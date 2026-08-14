/**
 * @file exception_system.cpp
 * @brief Implementation of Exception handling foundation
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#include "exception_system.h"
#include <sstream>
#include <iostream>

namespace Exceptions {

// ============================================================================
// DALVIK EXCEPTION IMPLEMENTATION
// ============================================================================

DalvikException::DalvikException(DalvikExceptionType type)
    : type_(type)
    , class_name_(get_exception_class_name(type))
    , message_()
    , throw_pc_(0)
{
}

DalvikException::DalvikException(const std::string& class_name, const std::string& message)
    : type_(DalvikExceptionType::CUSTOM)
    , class_name_(class_name)
    , message_(message)
    , throw_pc_(0)
{
}

DalvikException::DalvikException(
    DalvikExceptionType type,
    const std::string& message,
    const std::string& throw_class,
    const std::string& throw_method,
    uint32_t throw_pc
)
    : type_(type)
    , class_name_(get_exception_class_name(type))
    , message_(message)
    , throw_location_class_(throw_class)
    , throw_location_method_(throw_method)
    , throw_pc_(throw_pc)
{
}

void DalvikException::add_stack_frame(const std::string& cls, const std::string& method, uint32_t pc) {
    StackFrame frame;
    frame.class_name = cls;
    frame.method_name = method;
    frame.pc = pc;
    stack_trace_.push_back(frame);
}

std::string DalvikException::get_stack_trace() const {
    std::ostringstream oss;
    
    oss << to_string() << "\n";
    
    // Print stack trace in reverse order (most recent first is actually last in vector)
    for (auto it = stack_trace_.rbegin(); it != stack_trace_.rend(); ++it) {
        oss << "    at " << it->class_name << "->" << it->method_name 
            << "(PC: 0x" << std::hex << it->pc << ")\n";
    }
    
    if (!stack_trace_.empty()) {
        oss << "    at " << throw_location_class_ << "->" << throw_location_method_ 
            << "(PC: 0x" << std::hex << throw_pc_ << ") [THROW]\n";
    }
    
    return oss.str();
}

std::string DalvikException::get_exception_class_name(DalvikExceptionType type) const {
    switch (type) {
        case DalvikExceptionType::NULL_POINTER:
            return "java.lang.NullPointerException";
        case DalvikExceptionType::ARRAY_INDEX_OUT_OF_BOUNDS:
            return "java.lang.ArrayIndexOutOfBoundsException";
        case DalvikExceptionType::ARITHMETIC:
            return "java.lang.ArithmeticException";
        case DalvikExceptionType::CLASS_CAST:
            return "java.lang.ClassCastException";
        case DalvikExceptionType::NEGATIVE_ARRAY_SIZE:
            return "java.lang.NegativeArraySizeException";
        case DalvikExceptionType::ILLEGAL_ARGUMENT:
            return "java.lang.IllegalArgumentException";
        case DalvikExceptionType::ILLEGAL_STATE:
            return "java.lang.IllegalStateException";
        case DalvikExceptionType::NO_SUCH_METHOD:
            return "java.lang.NoSuchMethodError";
        case DalvikExceptionType::NO_SUCH_FIELD:
            return "java.lang.NoSuchFieldError";
        case DalvikExceptionType::ABSTRACT_METHOD:
            return "java.lang.AbstractMethodError";
        case DalvikExceptionType::UNSUPPORTED_OPERATION:
            return "java.lang.UnsupportedOperationException";
        case DalvikExceptionType::RUNTIME:
            return "java.lang.RuntimeException";
        case DalvikExceptionType::VIRTUAL_MACHINE_ERROR:
            return "java.lang.VirtualMachineError";
        default:
            return "java.lang.Exception";
    }
}

// ============================================================================
// EXCEPTION MANAGER IMPLEMENTATION
// ============================================================================

ExceptionManager::ExceptionManager(Observatory::ExecutionObservatory* observatory)
    : state_(ExceptionState::NO_EXCEPTION)
    , current_exception_(nullptr)
    , has_try_catch_table_(false)
    , observatory_(observatory)
{
}

void ExceptionManager::throw_exception(
    DalvikExceptionType type,
    const std::string& message,
    const std::string& location_class,
    const std::string& location_method,
    uint32_t pc
) {
    current_exception_ = std::make_unique<DalvikException>(
        type, message, location_class, location_method, pc
    );
    
    state_ = ExceptionState::THROWN;
    
    // Record in observatory
    if (observatory_) {
        observatory_->record_exception_thrown(
            current_exception_->get_class_name(),
            current_exception_->get_message(),
            location_class,
            location_method,
            pc
        );
    }
    
    // Log to console
    std::cerr << "[EXCEPTION] Thrown: " << current_exception_->to_string()
              << " at " << location_class << "->" << location_method 
              << " [PC: 0x" << std::hex << pc << "]" << std::endl;
}

void ExceptionManager::throw_custom_exception(
    const std::string& class_name,
    const std::string& message,
    const std::string& location_class,
    const std::string& location_method,
    uint32_t pc
) {
    current_exception_ = std::make_unique<DalvikException>(class_name, message);
    current_exception_->add_stack_frame(location_class, location_method, pc);
    
    state_ = ExceptionState::THROWN;
    
    if (observatory_) {
        observatory_->record_exception_thrown(
            class_name, message, location_class, location_method, pc
        );
    }
}

void ExceptionManager::set_try_catch_table(const TryCatchTable& table) {
    current_try_catch_table_ = table;
    has_try_catch_table_ = true;
}

void ExceptionManager::clear_try_catch_table() {
    current_try_catch_table_ = TryCatchTable();
    has_try_catch_table_ = false;
}

uint32_t ExceptionManager::find_handler_for_pc(uint32_t pc) const {
    if (!has_pending_exception() || !has_try_catch_table_) {
        return UINT32_MAX;  // No exception or no table
    }
    
    uint32_t handler = current_try_catch_table_.find_handler(
        pc, 
        current_exception_->get_class_name()
    );
    
    return handler;
}

void ExceptionManager::enter_handler() {
    if (state_ == ExceptionState::THROWN) {
        state_ = ExceptionState::BEING_HANDLED;
        
        if (observatory_) {
            // Record that we're entering a handler - would need exception index
            // For now, just note the transition
        }
    }
}

void ExceptionManager::mark_handled() {
    state_ = ExceptionState::HANDLED;
}

void ExceptionManager::mark_unhandled() {
    state_ = ExceptionState::UNHANDLED;
    
    std::cerr << "[EXCEPTION] Unhandled: " 
              << (current_exception_ ? current_exception_->to_string() : "unknown")
              << " - will propagate to caller" << std::endl;
}

void ExceptionManager::clear_after_move() {
    if (state_ == ExceptionState::BEING_HANDLED) {
        state_ = ExceptionState::HANDLED;
        // Don't reset current_exception_ yet - it's still valid until handler exits
    }
}

bool ExceptionManager::prepare_propagation() {
    if (!has_pending_exception()) {
        return false;  // Nothing to propagate
    }
    
    // Add current method's info to stack trace before propagating
    // (caller should have added their frame already)
    
    state_ = ExceptionState::THROWN;  // Reset to thrown for caller to handle
    
    return true;  // Caller needs to handle this
}

void ExceptionManager::add_stack_frame(const std::string& cls, const std::string& method, uint32_t pc) {
    if (current_exception_) {
        current_exception_->add_stack_frame(cls, method, pc);
    }
}

} // namespace Exceptions
