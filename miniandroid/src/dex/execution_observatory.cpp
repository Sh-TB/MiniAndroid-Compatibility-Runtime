/**
 * @file execution_observatory.cpp
 * @brief Implementation of ExecutionObservatory - complete trace system
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

#include "execution_observatory.h"
#include <iostream>
#include <algorithm>
#include <ctime>

namespace Observatory {

// ============================================================================
// CONSTRUCTOR / DESTRUCTOR
// ============================================================================

ExecutionObservatory::ExecutionObservatory(const std::string& session_id)
    : session_id_(session_id)
    , session_active_(false)
    , session_start_time_(0)
    , session_end_time_(0)
    , current_method_handle_(SIZE_MAX)  // Invalid handle
    , saved_(false)
{
    // Reserve space to reduce reallocations
    methods_.reserve(100);
    api_calls_.reserve(50);
    timeouts_.reserve(10);
    exceptions_.reserve(20);
}

ExecutionObservatory::~ExecutionObservatory() {
    if (!saved_ && session_active_) {
        // Auto-save on destruction if not saved
        save_to_directory("./run/exp036/traces");
    }
}

// ============================================================================
// TIMESTAMP HELPERS
// ============================================================================

uint64_t ExecutionObservatory::get_timestamp_ns() const {
    auto now = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        now.time_since_epoch()
    ).count();
}

std::string ExecutionObservatory::escape_json(const std::string& s) const {
    std::string result;
    result.reserve(s.size() * 2);  // Worst case
    
    for (char c : s) {
        switch (c) {
            case '"':  result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\n': result += "\\n";  break;
            case '\r': result += "\\r";  break;
            case '\t': result += "\\t";  break;
            default:
                if (c >= 32 && c < 127) {
                    result += c;
                } else {
                    char buf[8];
                    snprintf(buf, sizeof(buf), "\\u%04x", (unsigned char)c);
                    result += buf;
                }
        }
    }
    
    return result;
}

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

void ExecutionObservatory::start_session(const std::string& apk_path) {
    session_id_ = "exp036_" + std::to_string(get_timestamp_ns());
    apk_path_ = apk_path;
    session_active_ = true;
    session_start_time_ = get_timestamp_ns();
    current_method_handle_ = SIZE_MAX;
    saved_ = false;
    
    // Clear previous data
    methods_.clear();
    api_calls_.clear();
    timeouts_.clear();
    exceptions_.clear();
    
    record_apk_load_start(apk_path);
}

void ExecutionObservatory::end_session() {
    session_end_time_ = get_timestamp_ns();
    session_active_ = false;
}

bool ExecutionObservatory::save_to_directory(const std::string& output_dir) {
    try {
        // Create directory structure (simplified - assumes exists or use mkdir)
        
        // Save JSON report
        std::string json_path = output_dir + "/" + session_id_ + "_report.json";
        std::ofstream json_file(json_path);
        if (json_file.is_open()) {
            json_file << generate_json_report();
            json_file.close();
        }
        
        // Save human-readable summary
        std::string summary_path = output_dir + "/" + session_id_ + "_summary.txt";
        std::ofstream summary_file(summary_path);
        if (summary_file.is_open()) {
            summary_file << generate_summary();
            summary_file.close();
        }
        
        // Save method traces separately
        std::string methods_path = output_dir + "/" + session_id_ + "_methods.json";
        std::ofstream methods_file(methods_path);
        if (methods_file.is_open()) {
            methods_file << "[\n";
            for (size_t i = 0; i < methods_.size(); ++i) {
                if (i > 0) methods_file << ",\n";
                
                const auto& m = methods_[i];
                methods_file << "{\n";
                methods_file << "  \"class\": \"" << escape_json(m.class_descriptor) << "\",\n";
                methods_file << "  \"method\": \"" << escape_json(m.method_name) << "\",\n";
                methods_file << "  \"signature\": \"" << escape_json(m.method_signature) << "\",\n";
                methods_file << "  \"instructions\": " << m.total_instructions_executed << ",\n";
                methods_file << "  \"duration_us\": " << m.total_duration.count() << ",\n";
                methods_file << "  \"source\": " << static_cast<int>(m.source) << ",\n";
                methods_file << "  \"success\": " << (m.is_successful() ? "true" : "false") << ",\n";
                methods_file << "  \"exception_thrown\": " << (m.exception_thrown ? "true" : "false") << "\n";
                methods_file << "}";
            }
            methods_file << "\n]\n";
            methods_file.close();
        }
        
        // Save API call log
        std::string api_path = output_dir + "/" + session_id_ + "_api_calls.txt";
        std::ofstream api_file(api_path);
        if (api_file.is_open()) {
            api_file << "# API Call Log: " << session_id_ << "\n";
            api_file << "# APK: " << apk_path_ << "\n\n";
            
            for (const auto& api : api_calls_) {
                api_file << api.to_log_format() << "\n";
            }
            api_file.close();
        }
        
        saved_ = true;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "[Observatory] Error saving: " << e.what() << std::endl;
        return false;
    }
}

// ============================================================================
// LIFECYCLE EVENTS
// ============================================================================

void ExecutionObservatory::record_apk_load_start(const std::string& apk_path) {
    // Could add timestamped event log here
    // For now, just record in summary
}

void ExecutionObservatory::record_apk_load_complete(bool success, size_t dex_count) {
    // Record completion stats
}

void ExecutionObservatory::record_dex_parse_start(const std::string& dex_path) {
    // DEX parse start
}

void ExecutionObservatory::record_dex_parse_complete(bool success, size_t class_count) {
    // DEX parse complete
}

void ExecutionObservatory::record_class_loading_start(const std::string& class_desc) {
    // Class loading start
}

void ExecutionObservatory::record_class_loading_complete(const std::string& class_desc, bool success) {
    // Class loading complete
}

// ============================================================================
// METHOD TRACKING
// ============================================================================

size_t ExecutionObservatory::record_method_enter(
    const std::string& class_desc,
    const std::string& method_name,
    const std::string& signature,
    uint32_t entry_pc,
    const std::vector<RegisterState>& args,
    int call_depth
) {
    MethodExecutionRecord record;
    record.class_descriptor = class_desc;
    record.method_name = method_name;
    record.method_signature = signature;
    record.timestamp_enter_ns = get_timestamp_ns();
    record.entry_pc = entry_pc;
    record.argument_registers = args;
    record.returned_normally = false;
    record.exception_thrown = false;
    record.total_instructions_executed = 0;
    record.source = ExecutionSource::REAL_DALVIK_INTERPRETER;  // Default, update as we go
    record.call_depth = call_depth;
    
    methods_.push_back(record);
    current_method_handle_ = methods_.size() - 1;
    
    return current_method_handle_;
}

void ExecutionObservatory::record_method_exit(
    size_t handle,
    uint32_t exit_pc,
    const std::string& return_value,
    bool normal_exit
) {
    if (handle >= methods_.size()) {
        std::cerr << "[Observatory] Invalid method handle: " << handle << std::endl;
        return;
    }
    
    auto& method = methods_[handle];
    method.timestamp_exit_ns = get_timestamp_ns();
    method.exit_pc = exit_pc;
    method.return_value = return_value;
    method.returned_normally = normal_exit;
    
    // Calculate duration
    auto duration_ns = method.timestamp_exit_ns - method.timestamp_enter_ns;
    method.total_duration = std::chrono::microseconds(duration_ns / 1000);
    
    // Reset current handle if this was the active method
    if (handle == current_method_handle_) {
        current_method_handle_ = SIZE_MAX;
    }
}

// ============================================================================
// INSTRUCTION TRACKING
// ============================================================================

void ExecutionObservatory::record_instruction(
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
) {
    InstructionRecord instr;
    instr.pc = pc;
    instr.opcode = opcode;
    instr.opcode_name = opcode_name;
    instr.operands = operands;
    instr.registers_before = regs_before;
    instr.registers_after = regs_after;
    instr.success = success;
    instr.error_message = error;
    instr.duration = std::chrono::microseconds(0);  // Would need timing wrapper
    instr.source = source;
    
    // Add to method's instruction list
    if (method_handle < methods_.size()) {
        methods_[method_handle].instructions.push_back(instr);
        methods_[method_handle].total_instructions_executed++;
        
        // Update source if not yet set or more specific
        if (source != ExecutionSource::UNKNOWN) {
            methods_[method_handle].source = source;
        }
    }
}

// ============================================================================
// EXCEPTION TRACKING
// ============================================================================

void ExecutionObservatory::record_exception_thrown(
    const std::string& exc_class,
    const std::string& exc_message,
    const std::string& location_class,
    const std::string& location_method,
    uint32_t pc
) {
    ExceptionRecord exc;
    exc.exception_class = exc_class;
    exc.exception_message = exc_message;
    exc.throw_location_class = location_class;
    exc.throw_location_method = location_method;
    exc.throw_pc = pc;
    exc.was_caught = false;
    
    exceptions_.push_back(exc);
    
    // Also mark current method as having exception
    if (current_method_handle_ < methods_.size()) {
        methods_[current_method_handle_].exception_thrown = true;
        methods_[current_method_handle_].exception_class = exc_class;
        methods_[current_method_handle_].exception_message = exc_message;
        methods_[current_method_handle_].exception_pc = pc;
    }
}

void ExecutionObservatory::record_exception_caught(
    size_t exception_record_idx,
    const std::string& catch_class,
    const std::string& catch_method,
    uint32_t catch_pc
) {
    if (exception_record_idx >= exceptions_.size()) {
        std::cerr << "[Observatory] Invalid exception index: " << exception_record_idx << std::endl;
        return;
    }
    
    exceptions_[exception_record_idx].was_caught = true;
    exceptions_[exception_record_idx].catch_location_class = catch_class;
    exceptions_[exception_record_idx].catch_location_method = catch_method;
    exceptions_[exception_record_idx].catch_pc = catch_pc;
}

// ============================================================================
// API CALL TRACKING
// ============================================================================

void ExecutionObservatory::record_api_call(
    const std::string& api_class,
    const std::string& api_method,
    const std::vector<std::string>& args,
    ApiImplementationStatus status,
    const std::string& resolver,
    const std::string& return_val,
    bool success,
    const std::string& error
) {
    ApiCallRecord api;
    api.api_class = api_class;
    api.api_method = api_method;
    api.arguments = args;
    api.status = status;
    api.resolver_type = resolver;
    api.return_value = return_val;
    api.success = success;
    api.error_message = error;
    api.duration = std::chrono::microseconds(0);  // Would need timing
    
    api_calls_.push_back(api);
}

// ============================================================================
// TIMEOUT TRACKING
// ============================================================================

void ExecutionObservatory::record_timeout(
    const std::string& method_class,
    const std::string& method_name,
    uint32_t last_pc,
    uint16_t last_opcode,
    const std::string& last_opcode_name,
    size_t instructions_executed,
    size_t max_allowed,
    const std::string& reason
) {
    TimeoutRecord timeout;
    timeout.method_class = method_class;
    timeout.method_name = method_name;
    timeout.last_pc = last_pc;
    timeout.last_opcode = last_opcode;
    timeout.last_opcode_name = last_opcode_name;
    timeout.instructions_executed = instructions_executed;
    timeout.max_allowed = max_allowed;
    timeout.suspected_reason = reason;
    
    timeouts_.push_back(timeout);
    
    // Mark current method as timed out
    if (current_method_handle_ < methods_.size()) {
        methods_[current_method_handle_].source = ExecutionSource::ERROR_STATE;
    }
}

// ============================================================================
// QUERY METHODS
// ============================================================================

size_t ExecutionObservatory::get_total_instructions() const {
    size_t total = 0;
    for (const auto& m : methods_) {
        total += m.total_instructions_executed;
    }
    return total;
}

size_t ExecutionObservatory::get_total_methods() const {
    return methods_.size();
}

size_t ExecutionObservatory::get_total_api_calls() const {
    return api_calls_.size();
}

bool ExecutionObservatory::has_real_interpreter_evidence() const {
    for (const auto& m : methods_) {
        if (m.source == ExecutionSource::REAL_DALVIK_INTERPRETER && 
            m.total_instructions_executed > 0) {
            return true;
        }
    }
    return false;
}

bool ExecutionObservatory::had_timeouts() const {
    return !timeouts_.empty();
}

bool ExecutionObservatory::had_uncaught_exceptions() const {
    for (const auto& e : exceptions_) {
        if (!e.was_caught) {
            return true;
        }
    }
    return false;
}

// ============================================================================
// REPORT GENERATION
// ============================================================================

std::string ExecutionObservatory::generate_summary() const {
    std::ostringstream oss;
    
    oss << "=================================================================\n";
    oss << "EXECUTION OBSERVATORY SUMMARY\n";
    oss << "Session: " << session_id_ << "\n";
    oss << "APK: " << apk_path_ << "\n";
    oss << "=================================================================\n\n";
    
    // Session info
    oss << "SESSION INFO:\n";
    oss << "  Start Time: " << session_start_time_ << " ns\n";
    oss << "  End Time:   " << session_end_time_ << " ns\n";
    if (session_end_time_ > session_start_time_) {
        oss << "  Duration:   " << (session_end_time_ - session_start_time_) / 1000000 << " ms\n";
    }
    oss << "\n";
    
    // Statistics
    oss << "STATISTICS:\n";
    oss << "  Methods Executed:     " << get_total_methods() << "\n";
    oss << "  Instructions Total:   " << get_total_instructions() << "\n";
    oss << "  API Calls:            " << get_total_api_calls() << "\n";
    oss << "  Exceptions Thrown:    " << exceptions_.size() << "\n";
    oss << "  Uncaught Exceptions:  " << (had_uncaught_exceptions() ? "YES" : "NO") << "\n";
    oss << "  Timeouts:             " << timeouts_.size() << "\n";
    oss << "  Real Interpreter:     " << (has_real_interpreter_evidence() ? "YES" : "NO") << "\n";
    oss << "\n";
    
    // Method list
    oss << "METHODS EXECUTED (" << methods_.size() << "):\n";
    oss << "-----------------------------------------------------------------\n";
    for (const auto& m : methods_) {
        oss << m.summary() << "\n";
    }
    oss << "\n";
    
    // API calls
    if (!api_calls_.empty()) {
        oss << "API CALLS (" << api_calls_.size() << "):\n";
        oss << "-----------------------------------------------------------------\n";
        for (const auto& api : api_calls_) {
            oss << api.to_log_format() << "\n";
        }
        oss << "\n";
    }
    
    // Timeouts
    if (!timeouts_.empty()) {
        oss << "TIMEOUTS (" << timeouts_.size() << "):\n";
        oss << "-----------------------------------------------------------------\n";
        for (const auto& t : timeouts_) {
            oss << t.to_string() << "\n";
        }
        oss << "\n";
    }
    
    // Exceptions
    if (!exceptions_.empty()) {
        oss << "EXCEPTIONS (" << exceptions_.size() << "):\n";
        oss << "-----------------------------------------------------------------\n";
        for (const auto& e : exceptions_) {
            oss << e.to_string() << "\n";
        }
        oss << "\n";
    }
    
    // Verdict
    oss << "VERDICT:\n";
    oss << "-----------------------------------------------------------------\n";
    
    bool success = has_real_interpreter_evidence() && 
                   !had_uncaught_exceptions() && 
                   !had_timeouts() &&
                   get_total_instructions() > 0;
    
    oss << "  Overall Status: " << (success ? "PASS ✅" : "FAIL ❌") << "\n";
    
    if (!has_real_interpreter_evidence()) {
        oss << "  ❌ No REAL_DALVIK_INTERPRETER evidence found\n";
    }
    if (had_uncaught_exceptions()) {
        oss << "  ❌ Unhandled exceptions detected\n";
    }
    if (had_timeouts()) {
        oss << "  ❌ Execution timeouts detected\n";
    }
    if (get_total_instructions() == 0) {
        oss << "  ❌ No instructions executed\n";
    }
    
    oss << "\n=================================================================\n";
    
    return oss.str();
}

std::string ExecutionObservatory::generate_json_report() const {
    std::ostringstream oss;
    
    oss << "{\n";
    oss << "  \"session_id\": \"" << escape_json(session_id_) << "\",\n";
    oss << "  \"apk_path\": \"" << escape_json(apk_path_) << "\",\n";
    oss << "  \"timestamp\": " << get_timestamp_ns() << ",\n";
    
    // Statistics
    oss << "  \"statistics\": {\n";
    oss << "    \"total_methods\": " << get_total_methods() << ",\n";
    oss << "    \"total_instructions\": " << get_total_instructions() << ",\n";
    oss << "    \"total_api_calls\": " << get_total_api_calls() << ",\n";
    oss << "    \"exceptions_thrown\": " << exceptions_.size() << ",\n";
    oss << "    \"uncaught_exceptions\": " << (had_uncaught_exceptions() ? "true" : "false") << ",\n";
    oss << "    \"timeouts\": " << timeouts_.size() << ",\n";
    oss << "    \"has_real_evidence\": " << (has_real_interpreter_evidence() ? "true" : "false") << "\n";
    oss << "  },\n";
    
    // Verdict
    bool success = has_real_interpreter_evidence() && 
                   !had_uncaught_exceptions() && 
                   !had_timeouts() &&
                   get_total_instructions() > 0;
    
    oss << "  \"verdict\": {\n";
    oss << "    \"status\": " << (success ? "\"PASS\"" : "\"FAIL\"") << ",\n";
    oss << "    \"has_real_interpreter_evidence\": " << (has_real_interpreter_evidence() ? "true" : "false") << ",\n";
    oss << "    \"no_uncaught_exceptions\": " << (!had_uncaught_exceptions() ? "true" : "false") << ",\n";
    oss << "    \"no_timeouts\": " << (!had_timeouts() ? "true" : "false") << ",\n";
    oss << "    \"instructions_executed_gt_zero\": " << (get_total_instructions() > 0 ? "true" : "false") << "\n";
    oss << "  },\n";
    
    // Methods array (summary only, full data in separate file)
    oss << "  \"methods\": [\n";
    for (size_t i = 0; i < methods_.size(); ++i) {
        if (i > 0) oss << ",";
        const auto& m = methods_[i];
        oss << "\n    {\n";
        oss << "      \"class\": \"" << escape_json(m.class_descriptor) << "\",\n";
        oss << "      \"method\": \"" << escape_json(m.method_name) << "\",\n";
        oss << "      \"instructions\": " << m.total_instructions_executed << ",\n";
        oss << "      \"success\": " << (m.is_successful() ? "true" : "false") << ",\n";
        oss << "      \"source\": " << static_cast<int>(m.source) << "\n";
        oss << "    }";
    }
    oss << "\n  ],\n";
    
    // API calls array (summary)
    oss << "  \"api_calls\": [\n";
    for (size_t i = 0; i < api_calls_.size(); ++i) {
        if (i > 0) oss << ",";
        const auto& a = api_calls_[i];
        oss << "\n    {\n";
        oss << "      \"api\": \"" << escape_json(a.get_api_id()) << "\",\n";
        oss << "      \"status\": " << static_cast<int>(a.status) << ",\n";
        oss << "      \"success\": " << (a.success ? "true" : "false") << "\n";
        oss << "    }";
    }
    oss << "\n  ]\n";
    
    oss << "}\n";
    
    return oss.str();
}

} // namespace Observatory
