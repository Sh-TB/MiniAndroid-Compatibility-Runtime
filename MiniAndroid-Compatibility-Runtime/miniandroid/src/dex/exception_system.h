/**
 * @file exception_system.h
 * @brief Exception handling foundation for Dalvik execution
 * 
 * @description
 * Provides exception throwing, catching, and propagation mechanisms
 * that mirror Dalvik/ART behavior.
 * 
 * Key components:
 * - Exception state management
 * - Try/catch table parsing
 * - Exception propagation through call stack
 * - move-exception instruction support
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#ifndef EXCEPTION_SYSTEM_H
#define EXCEPTION_SYSTEM_H

#include <string>
#include <vector>
#include <memory>
#include <cstdint>
#include <stdexcept>
#include <map>
#include "execution_observatory.h"

/**
 * @namespace Exceptions
 * @brief Exception handling system components
 */
namespace Exceptions {

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * @enum DalvikExceptionType
 * @brief Standard Dalvik/Java exception types
 */
enum class DalvikExceptionType : uint8_t {
    NULL_POINTER,           ///< java.lang.NullPointerException
    ARRAY_INDEX_OUT_OF_BOUNDS,  ///< java.lang.ArrayIndexOutOfBoundsException
    ARITHMETIC,             ///< java.lang.ArithmeticException (divide by zero)
    CLASS_CAST,             ///< java.lang.ClassCastException
    NEGATIVE_ARRAY_SIZE,    ///< java.lang.NegativeArraySizeException
    ILLEGAL_ARGUMENT,       ///< java.lang.IllegalArgumentException
    ILLEGAL_STATE,          ///< java.lang.IllegalStateException
    NO_SUCH_METHOD,         ///< java.lang.NoSuchMethodError
    NO_SUCH_FIELD,          ///< java.lang.NoSuchFieldError
    ABSTRACT_METHOD,        ///< java.lang.AbstractMethodError
    UNSUPPORTED_OPERATION,  ///< java.lang.UnsupportedOperationException
    RUNTIME,               ///< java.lang.RuntimeException (generic)
    VIRTUAL_MACHINE_ERROR,  ///< java.lang.VirtualMachineError
    CUSTOM                  ///< User-defined or other exception
};

/**
 * @struct TryCatchEntry
 * @brief Single entry from DEX try/catch table
 */
struct TryCatchEntry {
    uint32_t try_start_pc;      ///< Start of try block (inclusive)
    uint32_t try_end_pc;        ///< End of try block (exclusive)
    uint32_t handler_pc;        ///< Handler code address
    std::string exception_type; ///< Exception class this handler catches
    bool catches_all;           ///< True if catches all exceptions
    
    /**
     * @brief Check if PC is within try block range
     */
    bool covers_pc(uint32_t pc) const {
        return pc >= try_start_pc && pc < try_end_pc;
    }
    
    /**
     * @brief Check if this handler can catch the given exception type
     */
    bool can_catch(const std::string& exc_type) const {
        if (catches_all) return true;
        // Simplified: exact match or superclass check would go here
        return exc_type == exception_type;
    }
};

/**
 * @struct TryCatchTable
 * @brief Complete try/catch table for a method
 */
struct TryCatchTable {
    std::vector<TryCatchEntry> entries;
    
    /**
     * @brief Find handler for exception at given PC
     * @param pc Program counter where exception occurred
     * @param exception_type Class name of thrown exception
     * @return Handler PC, or UINT32_MAX if no handler found
     */
    uint32_t find_handler(uint32_t pc, const std::string& exception_type) const {
        for (const auto& entry : entries) {
            if (entry.covers_pc(pc) && entry.can_catch(exception_type)) {
                return entry.handler_pc;
            }
        }
        return UINT32_MAX;  // No handler found
    }
    
    /**
     * @brief Check if there's any handler at given PC
     */
    bool has_handler_at(uint32_t pc) const {
        for (const auto& entry : entries) {
            if (entry.covers_pc(pc)) return true;
        }
        return false;
    }
    
    size_t size() const { return entries.size(); }
};

// ============================================================================
// DALVIK EXCEPTION CLASS
// ============================================================================

/**
 * @class DalvikException
 * @brief Represents a Dalvik/Java-style exception
 */
class DalvikException {
public:
    /**
     * @brief Construct from type enum
     */
    explicit DalvikException(DalvikExceptionType type);
    
    /**
     * @brief Construct from custom class name and message
     */
    DalvikException(const std::string& class_name, const std::string& message = "");
    
    /**
     * @brief Construct with full context
     */
    DalvikException(
        DalvikExceptionType type,
        const std::string& message,
        const std::string& throw_class,
        const std::string& throw_method,
        uint32_t throw_pc
    );
    
    // Accessors
    DalvikExceptionType get_type() const { return type_; }
    std::string get_class_name() const { return class_name_; }
    std::string get_message() const { return message_; }
    std::string get_throw_location_class() const { return throw_location_class_; }
    std::string get_throw_location_method() const { return throw_location_method_; }
    uint32_t get_throw_pc() const { return throw_pc_; }
    
    /**
     * @brief Get full stack trace string
     */
    std::string get_stack_trace() const;
    
    /**
     * @brief Add stack frame to trace
     */
    void add_stack_frame(const std::string& cls, const std::string& method, uint32_t pc);
    
    /**
     * @brief Convert to string representation
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << class_name_;
        if (!message_.empty()) {
            oss << ": " << message_;
        }
        return oss.str();
    }

private:
    DalvikExceptionType type_;
    std::string class_name_;
    std::string message_;
    
    // Throw location
    std::string throw_location_class_;
    std::string throw_location_method_;
    uint32_t throw_pc_;
    
    // Stack trace
    struct StackFrame {
        std::string class_name;
        std::string method_name;
        uint32_t pc;
    };
    std::vector<StackFrame> stack_trace_;
};

// ============================================================================
// EXCEPTION STATE MACHINE
// ============================================================================

/**
 * @enum ExceptionState
 * @brief Current state of exception handling
 */
enum class ExceptionState : uint8_t {
    NO_EXCEPTION,           ///< Normal execution, no pending exception
    THROWN,                 ///< Exception thrown, looking for handler
    BEING_HANDLED,          ///< In exception handler (move-exception available)
    HANDLED,                ///< Exception handled, execution continuing
    UNHANDLED               ///< No handler found, will propagate up
};

/**
 * @class ExceptionManager
 * @brief Central exception state management
 * 
 * @description
 * Tracks current exception state across the entire execution.
 * Integrates with ExecutionObservatory for complete tracing.
 * 
 * Usage:
 * @code
 * Exceptions::ExceptionManager mgr(observatory);
 * 
 * // Throw an exception:
 * mgr.throw_exception(Exceptions::DalvikExceptionType::NULL_POINTER, "obj is null", ...);
 * 
 * // Check for pending exception:
 * if (mgr.has_pending_exception()) {
 *     uint32_t handler = mgr.find_handler(current_pc);
 *     if (handler != UINT32_MAX) {
 *         pc = handler;  // Jump to handler
 *         mgr.enter_handler();
 *     } else {
 *         // Propagate to caller
 *         mgr.mark_unhandled();
 *     }
 * }
 * 
 * // In handler, get exception object:
 * auto* exc = mgr.get_current_exception();
 * mgr.clear_after_move();  // After move-exception
 * @endcode
 */
class ExceptionManager {
public:
    /**
     * @brief Constructor
     * @param observatory Observatory for recording events (can be null)
     */
    explicit ExceptionManager(Observatory::ExecutionObservatory* observatory = nullptr);
    
    // =========================================================================
    // THROWING EXCEPTIONS
    // =========================================================================
    
    /**
     * @brief Throw a standard exception
     * @param type Exception type
     * @param message Human-readable message
     * @param location_class Class where thrown
     * @param location_method Method where thrown
     * @param pc Program counter where thrown
     */
    void throw_exception(
        DalvikExceptionType type,
        const std::string& message,
        const std::string& location_class,
        const std::string& location_method,
        uint32_t pc
    );
    
    /**
     * @brief Throw a custom exception
     */
    void throw_custom_exception(
        const std::string& class_name,
        const std::string& message,
        const std::string& location_class,
        const std::string& location_method,
        uint32_t pc
    );
    
    // =========================================================================
    // STATE QUERIES
    // =========================================================================
    
    /**
     * @brief Check if there's a pending exception
     */
    bool has_pending_exception() const { 
        return state_ == ExceptionState::THROWN || state_ == ExceptionState::UNHANDLED; 
    }
    
    /**
     * @brief Check if we're in a handler (move-exception valid)
     */
    bool in_handler() const { return state_ == ExceptionState::BEING_HANDLED; }
    
    /**
     * @brief Get current exception state
     */
    ExceptionState get_state() const { return state_; }
    
    /**
     * @brief Get current exception (null if none pending)
     */
    const DalvikException* get_current_exception() const { 
        return current_exception_.get(); 
    }
    
    // =========================================================================
    // HANDLER LOOKUP
    // =========================================================================
    
    /**
     * @brief Set try/catch table for current method
     */
    void set_try_catch_table(const TryCatchTable& table);
    
    /**
     * @brief Clear try/catch table (method exit)
     */
    void clear_try_catch_table();
    
    /**
     * @brief Find handler for current exception at given PC
     * @return Handler PC, or UINT32_MAX if not found
     */
    uint32_t find_handler_for_pc(uint32_t pc) const;
    
    /**
     * @brief Enter exception handler (after jump)
     */
    void enter_handler();
    
    /**
     * @brief Mark exception as handled (handler completed normally)
     */
    void mark_handled();
    
    /**
     * @brief Mark exception as unhandled (no handler found)
     */
    void mark_unhandled();
    
    /**
     * @brief Clear exception after move-exception executed
     */
    void clear_after_move();
    
    // =========================================================================
    // PROPAGATION
    // =========================================================================
    
    /**
     * @brief Prepare exception for propagation to caller
     * @return true if caller should handle it, false if fatal
     */
    bool prepare_propagation();
    
    /**
     * @brief Add stack frame to current exception's trace
     */
    void add_stack_frame(const std::string& cls, const std::string& method, uint32_t pc);

private:
    // State
    ExceptionState state_;
    std::unique_ptr<DalvikException> current_exception_;
    
    // Current method's try/catch table
    TryCatchTable current_try_catch_table_;
    bool has_try_catch_table_;
    
    // Observatory integration
    Observatory::ExecutionObservatory* observatory_;
    
    // Internal helpers
    void record_exception_event(bool caught);
    std::string get_exception_class_name(DalvikExceptionType type) const;
};

// ============================================================================
// FACTORY FUNCTIONS
// ============================================================================

/**
 * @brief Create common Dalvik exceptions
 */
namespace Factory {

inline DalvikException null_pointer(
    const std::string& msg = "Attempt to invoke virtual method on null object reference",
    const std::string& cls = "",
    const std::string& method = "",
    uint32_t pc = 0
) {
    return DalvikException(DalvikExceptionType::NULL_POINTER, msg, cls, method, pc);
}

inline DalvikException array_index_oob(
    const std::string& msg,
    size_t index,
    size_t size,
    const std::string& cls = "",
    const std::string& method = "",
    uint32_t pc = 0
) {
    std::ostringstream oss;
    oss << msg << "; index=" << index << ", length=" << size;
    return DalvikException(DalvikExceptionType::ARRAY_INDEX_OUT_OF_BOUNDS, oss.str(), cls, method, pc);
}

inline DalvikException arithmetic_div_zero(
    const std::string& cls = "",
    const std::string& method = "",
    uint32_t pc = 0
) {
    return DalvikException(DalvikExceptionType::ARITHMETIC, "divide by zero", cls, method, pc);
}

inline DalvikException class_cast(
    const std::string& from,
    const std::string& to,
    const std::string& cls = "",
    const std::string& method = "",
    uint32_t pc = 0
) {
    std::ostringstream oss;
    oss << "Cannot cast " << from << " to " << to;
    return DalvikException(DalvikExceptionType::CLASS_CAST, oss.str(), cls, method, pc);
}

} // namespace Factory

} // namespace Exceptions

#endif // EXCEPTION_SYSTEM_H
