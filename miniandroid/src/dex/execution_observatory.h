/**
 * @file execution_observatory.h
 * @brief Complete execution trace system for MiniAndroid runtime
 * 
 * @description
 * Provides comprehensive observability into Dalvik bytecode execution.
 * Every operation produces structured evidence for debugging and validation.
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#ifndef EXECUTION_OBSERVATORY_H
#define EXECUTION_OBSERVATORY_H

#include <string>
#include <vector>
#include <map>
#include <chrono>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstdint>

/**
 * @namespace Observatory
 * @brief Execution tracing and observability components
 */
namespace Observatory {

// ============================================================================
// ENUMERATIONS
// ============================================================================

/**
 * @enum EventType
 * @brief Types of observable events during execution
 */
enum class EventType : uint8_t {
    // Method lifecycle
    METHOD_ENTER = 0,        ///< Method entry (before first instruction)
    METHOD_EXIT,             ///< Method exit (after return)
    
    // Instruction execution
    INSTRUCTION_START,       ///< Instruction about to execute
    INSTRUCTION_COMPLETE,    ///< Instruction finished executing
    
    // Exception handling
    EXCEPTION_THROWN,        ///< Exception thrown
    EXCEPTION_CAUGHT,        ///< Exception caught by handler
    
    // API calls
    API_CALL_ENTER,          ///< Android API call started
    API_CALL_EXIT,           ///< Android API call completed
    
    // Object operations
    OBJECT_ALLOCATED,        ///< New object created on heap
    OBJECT_ACCESSED,         ///< Field read/write on object
    
    // Execution control
    EXECUTION_TIMEOUT,       ///< Method exceeded instruction limit
    EXECUTION_ERROR,         ///< Fatal error during execution
    
    // Lifecycle markers
    APK_LOAD_START,          ///< APK loading began
    APK_LOAD_COMPLETE,       ///< APK loading finished
    DEX_PARSE_START,         ///< DEX parsing began
    DEX_PARSE_COMPLETE,      ///< DEX parsing finished
    CLASS_LOADING_START,     ///< Class loading began
    CLASS_LOADING_COMPLETE   ///< Class loading finished
};

/**
 * @enum ExecutionSource
 * @brief Source of execution (for evidence validation)
 */
enum class ExecutionSource : uint8_t {
    UNKNOWN = 0,
    REAL_DALVIK_INTERPRETER,  ///< Real Dalvik bytecode executed
    HOST_SHORTCUT,            ///< Host-side simulation (not real)
    STUB_IMPLEMENTATION,      ///< Stub/placeholder code
    ERROR_STATE               ///< Error or undefined state
};

/**
 * @enum ApiImplementationStatus
 * @brief Status of Android API implementation
 */
enum class ApiImplementationStatus : uint8_t {
    NOT_CALLED = 0,
    FOUND_AND_EXECUTED,       ///< Implemented and ran successfully
    FOUND_BUT_FAILED,         ///< Found but threw exception
    MISSING_STUB,             ///< No implementation, returned default
    MISSING_CRITICAL           ///< Missing implementation that caused failure
};

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * @struct RegisterState
 * @brief Snapshot of register file at a point in time
 */
struct RegisterState {
    uint16_t register_id;
    std::string value_string;
    std::string type_name;
    bool is_object_reference;
    uint32_t object_id;  // Valid if is_object_reference == true
    
    /**
     * @brief Convert to string representation
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "v" << std::setw(3) << std::setfill('0') << register_id 
            << " = " << (value_string.empty() ? "<empty>" : value_string);
        if (is_object_reference) {
            oss << " [obj:" << object_id << "]";
        }
        return oss.str();
    }
};

/**
 * @struct InstructionRecord
 * @brief Complete record of a single instruction execution
 */
struct InstructionRecord {
    // Location
    uint32_t pc;                    ///< Program counter
    uint16_t opcode;                ///< Opcode value
    std::string opcode_name;        ///< Human-readable opcode name
    
    // Operands
    std::vector<std::string> operands;  ///< Decoded operands
    
    // State before execution
    std::vector<RegisterState> registers_before;
    
    // State after execution
    std::vector<RegisterState> registers_after;
    
    // Result
    bool success;
    std::string error_message;
    
    // Timing
    std::chrono::microseconds duration;
    
    // Source tracking
    ExecutionSource source;
    
    /**
     * @brief Convert to JSON-like string for logging
     */
    std::string to_json() const {
        std::ostringstream oss;
        oss << "{\n";
        oss << "  \"pc\": 0x" << std::hex << pc << ",\n";
        oss << "  \"opcode\": 0x" << std::hex << opcode << ",\n";
        oss << "  \"opcode_name\": \"" << opcode_name << "\",\n";
        oss << "  \"success\": " << (success ? "true" : "false") << ",\n";
        oss << "  \"source\": " << static_cast<int>(source) << ",\n";
        oss << "  \"duration_us\": " << std::dec << duration.count() << "\n";
        oss << "}";
        return oss.str();
    }
};

/**
 * @struct MethodExecutionRecord
 * @brief Complete record of method entry to exit
 */
struct MethodExecutionRecord {
    // Identity
    std::string class_descriptor;
    std::string method_name;
    std::string method_signature;
    
    // Entry state
    uint64_t timestamp_enter_ns;
    uint32_t entry_pc;
    std::vector<RegisterState> argument_registers;
    
    // Exit state
    uint64_t timestamp_exit_ns;
    uint32_t exit_pc;
    std::string return_value;
    bool returned_normally;
    
    // Exception info (if thrown)
    bool exception_thrown;
    std::string exception_class;
    std::string exception_message;
    uint32_t exception_pc;
    
    // Statistics
    size_t total_instructions_executed;
    std::chrono::microseconds total_duration;
    
    // Instructions list
    std::vector<InstructionRecord> instructions;
    
    // Source tracking
    ExecutionSource source;
    
    // Call depth (for stack traces)
    int call_depth;
    
    /**
     * @brief Get method identifier string
     */
    std::string get_method_id() const {
        return class_descriptor + "->" + method_name + method_signature;
    }
    
    /**
     * @brief Check if execution was successful
     */
    bool is_successful() const {
        return source == ExecutionSource::REAL_DALVIK_INTERPRETER 
               && !exception_thrown 
               && total_instructions_executed > 0;
    }
    
    /**
     * @brief Convert summary to string
     */
    std::string summary() const {
        std::ostringstream oss;
        oss << "[METHOD] " << get_method_id() << "\n";
        oss << "  Instructions: " << total_instructions_executed << "\n";
        oss << "  Duration: " << total_duration.count() << "us\n";
        oss << "  Source: " << static_cast<int>(source) << "\n";
        oss << "  Success: " << (is_successful() ? "YES" : "NO") << "\n";
        if (exception_thrown) {
            oss << "  Exception: " << exception_class << ": " << exception_message << "\n";
            oss << "  At PC: 0x" << std::hex << exception_pc << "\n";
        }
        return oss.str();
    }
};

/**
 * @struct ApiCallRecord
 * @brief Record of an Android framework API call
 */
struct ApiCallRecord {
    // Target
    std::string api_class;
    std::string api_method;
    std::vector<std::string> arguments;
    
    // Resolution
    ApiImplementationStatus status;
    std::string resolver_type;  // "HOST_API_LAYER", "STUB", etc.
    
    // Execution
    std::string return_value;
    bool success;
    std::string error_message;
    
    // Timing
    std::chrono::microseconds duration;
    
    /**
     * @brief Get API call identifier
     */
    std::string get_api_id() const {
        return api_class + "." + api_method;
    }
    
    /**
     * @brief Convert to log format
     */
    std::string to_log_format() const {
        std::ostringstream oss;
        oss << "[API_CALL] " << get_api_id() << "(";
        for (size_t i = 0; i < arguments.size(); ++i) {
            if (i > 0) oss << ", ";
            oss << arguments[i];
        }
        oss << ") -> ";
        
        switch (status) {
            case ApiImplementationStatus::FOUND_AND_EXECUTED:
                oss << "SUCCESS"; break;
            case ApiImplementationStatus::FOUND_BUT_FAILED:
                oss << "FAILED"; break;
            case ApiImplementationStatus::MISSING_STUB:
                oss << "STUB"; break;
            case ApiImplementationStatus::MISSING_CRITICAL:
                oss << "MISSING_CRITICAL"; break;
            default:
                oss << "UNKNOWN"; break;
        }
        
        if (!return_value.empty()) {
            oss << " [" << return_value << "]";
        }
        
        return oss.str();
    }
};

/**
 * @struct TimeoutRecord
 * @brief Record of execution timeout event
 */
struct TimeoutRecord {
    std::string method_class;
    std::string method_name;
    uint32_t last_pc;
    uint16_t last_opcode;
    std::string last_opcode_name;
    size_t instructions_executed;
    size_t max_allowed;
    std::string suspected_reason;
    
    std::string to_string() const {
        std::ostringstream oss;
        oss << "[TIMEOUT] " << method_class << "->" << method_name << "\n";
        oss << "  Last PC: 0x" << std::hex << last_pc << "\n";
        oss << "  Last Opcode: " << last_opcode_name << " (0x" << std::hex << last_opcode << ")\n";
        oss << "  Instructions: " << std::dec << instructions_executed << "/" << max_allowed << "\n";
        oss << "  Suspected: " << suspected_reason << "\n";
        return oss.str();
    }
};

/**
 * @struct ExceptionRecord
 * @brief Record of exception throw/catch event
 */
struct ExceptionRecord {
    std::string exception_class;
    std::string exception_message;
    std::string throw_location_class;
    std::string throw_location_method;
    uint32_t throw_pc;
    bool was_caught;
    std::string catch_location_class;
    std::string catch_location_method;
    uint32_t catch_pc;
    
    std::string to_string() const {
        std::ostringstream oss;
        oss << "[EXCEPTION] " << exception_class;
        if (!exception_message.empty()) {
            oss << ": " << exception_message;
        }
        oss << "\n";
        oss << "  Thrown at: " << throw_location_class << "->" << throw_location_method 
            << " [PC: 0x" << std::hex << throw_pc << "]\n";
        if (was_caught) {
            oss << "  Caught at: " << catch_location_class << "->" << catch_location_method 
                << " [PC: 0x" << std::hex << catch_pc << "]\n";
        } else {
            oss << "  NOT CAUGHT - unhandled exception\n";
        }
        return oss.str();
    }
};

// ============================================================================
// MAIN OBSERVATORY CLASS
// ============================================================================

/**
 * @class ExecutionObservatory
 * @brief Central observability system for capturing all execution events
 * 
 * @description
 * Thread-safe (single-threaded use assumed) observatory that records
 * every significant event during Dalvik execution.
 * 
 * Usage:
 * @code
 * Observatory::ExecutionObservatory obs("execution_trace");
 * obs.start_apk_load("app.apk");
 * // ... execute ...
 * obs.finish_and_save();
 * @endcode
 */
class ExecutionObservatory {
public:
    /**
     * @brief Constructor
     * @param session_id Unique identifier for this execution session
     */
    explicit ExecutionObservatory(const std::string& session_id = "default");
    
    /**
     * @brief Destructor - auto-saves if not saved
     */
    ~ExecutionObservatory();
    
    // =========================================================================
    // SESSION MANAGEMENT
    // =========================================================================
    
    /**
     * @brief Start new observation session
     * @param apk_path Path to APK being executed
     */
    void start_session(const std::string& apk_path);
    
    /**
     * @brief End current session and prepare report
     */
    void end_session();
    
    /**
     * @brief Save all collected data to files
     * @param output_dir Directory to write output files
     * @return true if save successful
     */
    bool save_to_directory(const std::string& output_dir);
    
    // =========================================================================
    // LIFECYCLE EVENTS
    // =========================================================================
    
    void record_apk_load_start(const std::string& apk_path);
    void record_apk_load_complete(bool success, size_t dex_count);
    void record_dex_parse_start(const std::string& dex_path);
    void record_dex_parse_complete(bool success, size_t class_count);
    void record_class_loading_start(const std::string& class_desc);
    void record_class_loading_complete(const std::string& class_desc, bool success);
    
    // =========================================================================
    // METHOD TRACKING
    // =========================================================================
    
    /**
     * @brief Record method entry
     * @param class_desc Class descriptor
     * @param method_name Method name
     * @param signature Method signature
     * @param entry_pc PC at method entry
     * @param args Argument register states
     * @return Handle for later updates
     */
    size_t record_method_enter(
        const std::string& class_desc,
        const std::string& method_name,
        const std::string& signature,
        uint32_t entry_pc,
        const std::vector<RegisterState>& args,
        int call_depth
    );
    
    /**
     * @brief Record method exit
     * @param handle Handle from record_method_enter
     * @param exit_pc PC at method exit
     * @param return_value Return value (if any)
     * @param normal_exit Whether exited normally (vs exception)
     */
    void record_method_exit(
        size_t handle,
        uint32_t exit_pc,
        const std::string& return_value,
        bool normal_exit
    );
    
    /**
     * @brief Get current method handle (top of stack)
     */
    size_t get_current_method_handle() const { return current_method_handle_; }
    
    // =========================================================================
    // INSTRUCTION TRACKING
    // =========================================================================
    
    /**
     * @brief Record single instruction execution
     * @param method_handle Parent method handle
     * @param pc Program counter
     * @param opcode Opcode value
     * @param opcode_name Human-readable name
     * @param operands Decoded operands
     * @param regs_before Register state before
     * @param regs_after Register state after
     * @param success Whether instruction succeeded
     * @param error Error message if failed
     * @param source Execution source
     */
    void record_instruction(
        size_t method_handle,
        uint32_t pc,
        uint16_t opcode,
        const std::string& opcode_name,
        const std::vector<std::string>& operands,
        const std::vector<RegisterState>& regs_before,
        const std::vector<RegisterState>& regs_after,
        bool success,
        const std::string& error,
        ExecutionSource source
    );
    
    // =========================================================================
    // EXCEPTION TRACKING
    // =========================================================================
    
    /**
     * @brief Record exception being thrown
     */
    void record_exception_thrown(
        const std::string& exc_class,
        const std::string& exc_message,
        const std::string& location_class,
        const std::string& location_method,
        uint32_t pc
    );
    
    /**
     * @brief Record exception being caught
     */
    void record_exception_caught(
        size_t exception_record_idx,
        const std::string& catch_class,
        const std::string& catch_method,
        uint32_t catch_pc
    );
    
    // =========================================================================
    // API CALL TRACKING
    // =========================================================================
    
    /**
     * @brief Record Android API call
     */
    void record_api_call(
        const std::string& api_class,
        const std::string& api_method,
        const std::vector<std::string>& args,
        ApiImplementationStatus status,
        const std::string& resolver,
        const std::string& return_val,
        bool success,
        const std::string& error
    );
    
    // =========================================================================
    // TIMEOUT TRACKING
    // =========================================================================
    
    /**
     * @brief Record execution timeout
     */
    void record_timeout(
        const std::string& method_class,
        const std::string& method_name,
        uint32_t last_pc,
        uint16_t last_opcode,
        const std::string& last_opcode_name,
        size_t instructions_executed,
        size_t max_allowed,
        const std::string& reason
    );
    
    // =========================================================================
    // QUERY METHODS
    // =========================================================================
    
    /**
     * @brief Get total instructions executed in session
     */
    size_t get_total_instructions() const;
    
    /**
     * @brief Get total methods executed in session
     */
    size_t get_total_methods() const;
    
    /**
     * @brief Get total API calls in session
     */
    size_t get_total_api_calls() const;
    
    /**
     * @brief Check if session has real Dalvik interpreter evidence
     */
    bool has_real_interpreter_evidence() const;
    
    /**
     * @brief Check if session had timeouts
     */
    bool had_timeouts() const;
    
    /**
     * @brief Check if session had uncaught exceptions
     */
    bool had_uncaught_exceptions() const;
    
    /**
     * @brief Generate execution summary
     */
    std::string generate_summary() const;
    
    /**
     * @brief Generate JSON report
     */
    std::string generate_json_report() const;

private:
    // Session identity
    std::string session_id_;
    std::string apk_path_;
    bool session_active_;
    uint64_t session_start_time_;
    uint64_t session_end_time_;
    
    // Collected data
    std::vector<MethodExecutionRecord> methods_;
    std::vector<ApiCallRecord> api_calls_;
    std::vector<TimeoutRecord> timeouts_;
    std::vector<ExceptionRecord> exceptions_;
    
    // Current state
    size_t current_method_handle_;
    bool saved_;
    
    // Helpers
    uint64_t get_timestamp_ns() const;
    std::string escape_json(const std::string& s) const;
};

} // namespace Observatory

#endif // EXECUTION_OBSERVATORY_H
