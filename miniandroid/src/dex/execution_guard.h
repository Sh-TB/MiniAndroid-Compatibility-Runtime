/**
 * @file execution_guard.h
 * @brief Execution guard - timeout and infinite loop protection
 * 
 * @description
 * Prevents infinite loops and excessive execution during Dalvik interpretation.
 * Provides configurable limits with detailed diagnostics when limits are exceeded.
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#ifndef EXECUTION_GUARD_H
#define EXECUTION_GUARD_H

#include <string>
#include <cstdint>
#include <stdexcept>
#include <functional>
#include "execution_observatory.h"

/**
 * @namespace Guard
 * @brief Execution protection components
 */
namespace Guard {

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * @struct ExecutionLimits
 * @brief Configurable limits for execution protection
 */
struct ExecutionLimits {
    /**
     * @brief Maximum instructions per method before timeout
     * 
     * Most Android methods complete in <1000 instructions.
     * Complex methods (initializers) may use 10,000+.
     * Set to 0 to disable limit.
     */
    size_t max_instructions_per_method = 100000;
    
    /**
     * @brief Maximum total instructions for entire APK execution
     * 
     * Prevents runaway execution across multiple methods.
     * Set to 0 to disable limit.
     */
    size_t max_total_instructions = 1000000;
    
    /**
     * @brief Maximum method call depth
     * 
     * Prevents stack overflow from infinite recursion.
     * Android typically uses depth <100.
     */
    size_t max_call_depth = 256;
    
    /**
     * @brief Maximum methods to execute
     * 
     * Limits total number of method invocations.
     */
    size_t max_methods = 10000;
    
    /**
     * @brief Enable/disable guard
     */
    bool enabled = true;
    
    /**
     * @brief Throw exception vs return error on limit hit
     * 
     * If true, throws ExecutionLimitExceeded.
     * If false, returns error code from check functions.
     */
    bool throw_on_limit = false;
    
    /**
     * @brief Get default strict limits (for testing)
     */
    static ExecutionLimits strict() {
        ExecutionLimits limits;
        limits.max_instructions_per_method = 10000;
        limits.max_total_instructions = 100000;
        limits.max_call_depth = 50;
        limits.max_methods = 1000;
        return limits;
    }
    
    /**
     * @brief Get default lenient limits (for production)
     */
    static ExecutionLimits lenient() {
        ExecutionLimits limits;
        limits.max_instructions_per_method = 500000;
        limits.max_total_instructions = 5000000;
        limits.max_call_depth = 512;
        limits.max_methods = 50000;
        return limits;
    }
};

// ============================================================================
// EXCEPTIONS
// ============================================================================

/**
 * @class ExecutionLimitExceeded
 * @brief Thrown when execution exceeds configured limits
 */
class ExecutionLimitExceeded : public std::runtime_error {
public:
    /**
     * @enum LimitType
     * @brief Type of limit that was exceeded
     */
    enum class LimitType {
        INSTRUCTIONS_PER_METHOD,
        TOTAL_INSTRUCTIONS,
        CALL_DEPTH,
        METHOD_COUNT,
        UNKNOWN
    };
    
    ExecutionLimitExceeded(LimitType type, const std::string& message, size_t current, size_t maximum)
        : std::runtime_error(message)
        , limit_type_(type)
        , current_value_(current)
        , max_value_(maximum)
    {}
    
    LimitType get_limit_type() const { return limit_type_; }
    size_t get_current_value() const { return current_value_; }
    size_t get_max_value() const { return max_value_; }
    
    std::string get_limit_type_string() const {
        switch (limit_type_) {
            case LimitType::INSTRUCTIONS_PER_METHOD: return "INSTRUCTIONS_PER_METHOD";
            case LimitType::TOTAL_INSTRUCTIONS: return "TOTAL_INSTRUCTIONS";
            case LimitType::CALL_DEPTH: return "CALL_DEPTH";
            case LimitType::METHOD_COUNT: return "METHOD_COUNT";
            default: return "UNKNOWN";
        }
    }

private:
    LimitType limit_type_;
    size_t current_value_;
    size_t max_value_;
};

// ============================================================================
// GUARD CLASS
// ============================================================================

/**
 * @class ExecutionGuard
 * @brief Monitors and enforces execution limits
 * 
 * @description
 * Integrates with ExecutionObservatory to provide comprehensive
 * protection against infinite loops and resource exhaustion.
 * 
 * Usage:
 * @code
 * Guard::ExecutionGuard guard(limits, observatory);
 * 
 * // Before executing a method:
 * guard.enter_method("Activity", "onCreate", "()V");
 * 
 * // Before each instruction:
 * guard.check_instruction_limit(pc, opcode);
 * 
 * // After method completes:
 * guard.exit_method();
 * @endcode
 */
class ExecutionGuard {
public:
    /**
     * @brief Constructor
     * @param limits Configuration limits
     * @param observatory Observatory to record violations (can be null)
     */
    explicit ExecutionGuard(
        const ExecutionLimits& limits,
        Observatory::ExecutionObservatory* observatory = nullptr
    );
    
    // =========================================================================
    // METHOD TRACKING
    // =========================================================================
    
    /**
     * @brief Enter a new method (increment depth)
     * @param class_name Class of method being entered
     * @param method_name Method name
     * @param signature Method signature
     * @throws ExecutionLimitExceeded if call depth exceeded
     * @return true if OK, false if limit hit (when not throwing)
     */
    bool enter_method(
        const std::string& class_name,
        const std::string& method_name,
        const std::string& signature
    );
    
    /**
     * @brief Exit current method (decrement depth)
     * @return Current depth after exit
     */
    size_t exit_method();
    
    /**
     * @brief Get current call depth
     */
    size_t get_current_depth() const { return current_depth_; }
    
    /**
     * @brief Check if we're in a method context
     */
    bool in_method() const { return current_depth_ > 0; }
    
    // =========================================================================
    // INSTRUCTION COUNTING
    // =========================================================================
    
    /**
     * @brief Record an instruction execution and check limits
     * @param pc Current program counter
     * @param opcode Current opcode value
     * @param opcode_name Human-readable opcode name
     * @throws ExecutionLimitExceeded if limit exceeded (if configured)
     * @return true if OK, false if limit hit
     */
    bool check_instruction(
        uint32_t pc,
        uint16_t opcode,
        const std::string& opcode_name
    );
    
    /**
     * @brief Get instruction count for current method
     */
    size_t get_current_method_instruction_count() const { 
        return in_method() ? method_instruction_counts_.back() : 0; 
    }
    
    /**
     * @brief Get total instruction count for session
     */
    size_t get_total_instruction_count() const { return total_instructions_; }
    
    // =========================================================================
    // METHOD COUNTING
    // =========================================================================
    
    /**
     * @brief Increment total method count and check limit
     */
    bool increment_method_count();
    
    /**
     * @brief Get total methods executed
     */
    size_t get_total_method_count() const { return total_methods_; }
    
    // =========================================================================
    // DIAGNOSTICS
    // =========================================================================
    
    /**
     * @brief Generate diagnostic report for last violation
     */
    std::string get_last_violation_report() const;
    
    /**
     * @brief Get number of limit violations recorded
     */
    size_t get_violation_count() const { return violation_count_; }
    
    /**
     * @brief Check if any violations occurred
     */
    bool had_violations() const { return violation_count_ > 0; }
    
    /**
     * @brief Reset all counters (for new session)
     */
    void reset();
    
    /**
     * @brief Update limits at runtime
     */
    void set_limits(const ExecutionLimits& limits) { limits_ = limits; }
    
    /**
     * @brief Get current limits
     */
    const ExecutionLimits& get_limits() const { return limits_; }

private:
    // Configuration
    ExecutionLimits limits_;
    
    // Observatory integration
    Observatory::ExecutionObservatory* observatory_;
    
    // Counters
    size_t current_depth_;
    size_t total_instructions_;
    size_t total_methods_;
    std::vector<size_t> method_instruction_counts_;
    
    // Violation tracking
    size_t violation_count_;
    
    // Last violation info (for diagnostics)
    struct LastViolation {
        ExecutionLimitExceeded::LimitType type;
        std::string context;
        uint32_t last_pc;
        uint16_t last_opcode;
        std::string last_opcode_name;
        size_t current_value;
        size_t max_value;
    } last_violation_;
    
    // Internal check helper
    bool check_and_record(
        bool condition,
        ExecutionLimitExceeded::LimitType type,
        const std::string& context,
        size_t current,
        size_t max,
        uint32_t pc = 0,
        uint16_t opcode = 0,
        const std::string& opcode_name = ""
    );
};

} // namespace Guard

#endif // EXECUTION_GUARD_H
