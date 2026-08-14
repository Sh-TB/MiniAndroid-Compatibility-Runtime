/**
 * @file execution_guard.cpp
 * @brief Implementation of ExecutionGuard - timeout and infinite loop protection
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#include "execution_guard.h"
#include <sstream>
#include <iostream>

namespace Guard {

// ============================================================================
// CONSTRUCTOR
// ============================================================================

ExecutionGuard::ExecutionGuard(
    const ExecutionLimits& limits,
    Observatory::ExecutionObservatory* observatory
)
    : limits_(limits)
    , observatory_(observatory)
    , current_depth_(0)
    , total_instructions_(0)
    , total_methods_(0)
    , violation_count_(0)
{
    method_instruction_counts_.reserve(64);  // Pre-allocate for common depths
}

// ============================================================================
// METHOD TRACKING
// ============================================================================

bool ExecutionGuard::enter_method(
    const std::string& class_name,
    const std::string& method_name,
    const std::string& signature
) {
    if (!limits_.enabled) {
        current_depth_++;
        method_instruction_counts_.push_back(0);
        return true;
    }
    
    // Check call depth limit
    bool ok = check_and_record(
        current_depth_ < limits_.max_call_depth,
        ExecutionLimitExceeded::LimitType::CALL_DEPTH,
        class_name + "->" + method_name + signature,
        current_depth_ + 1,
        limits_.max_call_depth
    );
    
    if (ok) {
        current_depth_++;
        method_instruction_counts_.push_back(0);
        
        // Check method count limit
        ok = increment_method_count();
    }
    
    return ok;
}

size_t ExecutionGuard::exit_method() {
    if (current_depth_ > 0) {
        if (!method_instruction_counts_.empty()) {
            method_instruction_counts_.pop_back();
        }
        current_depth_--;
    }
    return current_depth_;
}

// ============================================================================
// INSTRUCTION COUNTING
// ============================================================================

bool ExecutionGuard::check_instruction(
    uint32_t pc,
    uint16_t opcode,
    const std::string& opcode_name
) {
    if (!limits_.enabled) {
        total_instructions_++;
        if (in_method()) {
            method_instruction_counts_.back()++;
        }
        return true;
    }
    
    total_instructions_++;
    if (in_method()) {
        method_instruction_counts_.back()++;
    }
    
    size_t current_method_instructions = get_current_method_instruction_count();
    
    // Check per-method instruction limit
    bool ok = check_and_record(
        limits_.max_instructions_per_method == 0 || 
            current_method_instructions <= limits_.max_instructions_per_method,
        ExecutionLimitExceeded::LimitType::INSTRUCTIONS_PER_METHOD,
        in_method() ? "current method" : "global",
        current_method_instructions,
        limits_.max_instructions_per_method,
        pc,
        opcode,
        opcode_name
    );
    
    if (!ok) return false;
    
    // Check total instruction limit
    ok = check_and_record(
        limits_.max_total_instructions == 0 || 
            total_instructions_ <= limits_.max_total_instructions,
        ExecutionLimitExceeded::LimitType::TOTAL_INSTRUCTIONS,
        "session total",
        total_instructions_,
        limits_.max_total_instructions,
        pc,
        opcode,
        opcode_name
    );
    
    return ok;
}

// ============================================================================
// METHOD COUNTING
// ============================================================================

bool ExecutionGuard::increment_method_count() {
    total_methods_++;
    
    if (!limits_.enabled || limits_.max_methods == 0) {
        return true;
    }
    
    return check_and_record(
        total_methods_ <= limits_.max_methods,
        ExecutionLimitExceeded::LimitType::METHOD_COUNT,
        "session",
        total_methods_,
        limits_.max_methods
    );
}

// ============================================================================
// DIAGNOSTICS
// ============================================================================

std::string ExecutionGuard::get_last_violation_report() const {
    if (violation_count_ == 0) {
        return "No violations recorded";
    }
    
    std::ostringstream oss;
    oss << "================================================================\n";
    oss << "EXECUTION GUARD VIOLATION REPORT\n";
    oss << "================================================================\n\n";
    
    oss << "Violation #" << violation_count_ << "\n\n";
    
    oss << "Limit Type: " << last_violation_.type << "\n";
    oss << "  (" << ExecutionLimitExceeded(last_violation_.type, "", 0, 0).get_limit_type_string() << ")\n\n";
    
    oss << "Context: " << last_violation_.context << "\n\n";
    
    oss << "Values:\n";
    oss << "  Current:  " << last_violation_.current_value << "\n";
    oss << "  Maximum:  " << last_violation_.max_value << "\n";
    oss << "  Exceeded: " << (last_violation_.current_value - last_violation_.max_value) << "\n\n";
    
    if (last_violation_.last_pc > 0 || last_violation_.last_opcode > 0) {
        oss << "Last Instruction:\n";
        oss << "  PC:     0x" << std::hex << last_violation_.last_pc << "\n";
        oss << "  Opcode: 0x" << last_violation_.last_opcode << " (" 
            << last_violation_.last_opcode_name << ")\n\n";
    }
    
    oss << "Session Statistics:\n";
    oss << "  Total Instructions: " << std::dec << total_instructions_ << "\n";
    oss << "  Total Methods:      " << total_methods_ << "\n";
    oss << "  Current Depth:      " << current_depth_ << "\n";
    oss << "  Total Violations:   " << violation_count_ << "\n";
    
    oss << "\n================================================================\n";
    
    // Suspected reasons based on type
    oss << "\nSuspected Reasons:\n";
    switch (last_violation_.type) {
        case ExecutionLimitExceeded::LimitType::INSTRUCTIONS_PER_METHOD:
            oss << "  - Method contains infinite loop or very long execution path\n";
            oss << "  - Recursive calls without proper base case\n";
            oss << "  - Missing API implementation causing retry loops\n";
            break;
            
        case ExecutionLimitExceeded::LimitType::TOTAL_INSTRUCTIONS:
            oss << "  - APK has excessive initialization code\n";
            oss << "  - Multiple methods with long execution paths\n";
            oss << "  - Possible runaway execution across many methods\n";
            break;
            
        case ExecutionLimitExceeded::LimitType::CALL_DEPTH:
            oss << "  - Infinite recursion detected\n";
            oss << "  - Circular method invocation chain\n";
            oss << "  - Stack overflow would occur without this guard\n";
            break;
            
        case ExecutionLimitExceeded::LimitType::METHOD_COUNT:
            oss << "  - APK invokes too many methods\n";
            oss << "  - Possible initialization loop calling many methods\n";
            break;
            
        default:
            oss << "  - Unknown limit type exceeded\n";
    }
    
    oss << "\nRecommendations:\n";
    oss << "  1. Check the method at the reported location\n";
    oss << "  2. Look for missing API implementations causing retries\n";
    oss << "  3. Verify no circular dependencies in call graph\n";
    oss << "  4. Consider increasing limits if this is legitimate complex code\n";
    
    oss << "\n================================================================\n";
    
    return oss.str();
}

void ExecutionGuard::reset() {
    current_depth_ = 0;
    total_instructions_ = 0;
    total_methods_ = 0;
    method_instruction_counts_.clear();
    violation_count_ = 0;
    
    last_violation_.type = ExecutionLimitExceeded::LimitType::UNKNOWN;
    last_violation_.context = "";
    last_violation_.last_pc = 0;
    last_violation_.last_opcode = 0;
    last_violation_.last_opcode_name = "";
    last_violation_.current_value = 0;
    last_violation_.max_value = 0;
}

// ============================================================================
// INTERNAL HELPERS
// ============================================================================

bool ExecutionGuard::check_and_record(
    bool condition,
    ExecutionLimitExceeded::LimitType type,
    const std::string& context,
    size_t current,
    size_t max,
    uint32_t pc,
    uint16_t opcode,
    const std::string& opcode_name
) {
    if (condition) {
        return true;  // Limit not exceeded
    }
    
    // Record violation
    violation_count_++;
    
    last_violation_.type = type;
    last_violation_.context = context;
    last_violation_.last_pc = pc;
    last_violation_.last_opcode = opcode;
    last_violation_.last_opcode_name = opcode_name;
    last_violation_.current_value = current;
    last_violation_.max_value = max;
    
    // Log to console
    std::cerr << "[GUARD] LIMIT EXCEEDED: " 
              << ExecutionLimitExceeded(type, "", 0, 0).get_limit_type_string()
              << " in " << context
              << " (current=" << current << ", max=" << max << ")" << std::endl;
    
    // Record to observatory if available
    if (observatory_) {
        std::ostringstream reason;
        reason << ExecutionLimitExceeded(type, "", 0, 0).get_limit_type_string()
               << ": " << current << "/" << max;
        
        observatory_->record_timeout(
            context,  // Will be class->method format
            "",         // Method name (extract from context if needed)
            pc,
            opcode,
            opcode_name,
            current,
            max,
            reason.str()
        );
    }
    
    // Throw or return false based on configuration
    if (limits_.throw_on_limit) {
        std::ostringstream msg;
        msg << "Execution limit exceeded [" 
            << ExecutionLimitExceeded(type, "", 0, 0).get_limit_type_string()
            << "] in " << context 
            << ": current=" << current << ", max=" << max;
        
        throw ExecutionLimitExceeded(type, msg.str(), current, max);
    }
    
    return false;  // Limit hit, but not throwing
}

} // namespace Guard
