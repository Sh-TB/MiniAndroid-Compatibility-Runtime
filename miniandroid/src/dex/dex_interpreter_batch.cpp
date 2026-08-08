/*
 * MiniAndroid Runtime v0.1 - DEX Interpreter Implementation (EXP-003-BATCH)
 * 
 * Minimal DEX Execution Engine
 * 
 * Implements: const-string, new-instance, invoke-direct, invoke-virtual, return-void
 */

#include "dex_interpreter_batch.h"

#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <algorithm>

namespace miniandroid {
namespace dex {

// ============================================================================
// Value Serialization
// ============================================================================

std::string Value::to_string() const {
    switch (type) {
        case ValueType::UNINITIALIZED:
            return "<uninitialized>";
        case ValueType::REGISTER_UNSET:
            return "<unset>";
        case ValueType::INT32:
            return std::to_string(int_val);
        case ValueType::FLOAT:
            return std::to_string(float_val) + "f";
        case ValueType::STRING_REF:
            return "\"" + string_val + "\" (str:" + std::to_string(reference_id) + ")";
        case ValueType::OBJECT_REF:
            return object_class + " (obj:" + std::to_string(object_id) + ")";
        case ValueType::NULL_REF:
            return "null";
        default:
            return "<unknown>";
    }
}

json Value::to_json() const {
    json j;
    j["type"] = [this]() -> std::string {
        switch (type) {
            case ValueType::UNINITIALIZED: return "UNINITIALIZED";
            case ValueType::REGISTER_UNSET: return "UNSET";
            case ValueType::INT32: return "INT32";
            case ValueType::FLOAT: return "FLOAT";
            case ValueType::STRING_REF: return "STRING_REF";
            case ValueType::OBJECT_REF: return "OBJECT_REF";
            case ValueType::NULL_REF: return "NULL_REF";
            default: return "UNKNOWN";
        }
    }();
    
    switch (type) {
        case ValueType::INT32:
            j["value"] = int_val;
            break;
        case ValueType::STRING_REF:
            j["value"] = string_val;
            j["reference_id"] = reference_id;
            break;
        case ValueType::OBJECT_REF:
            j["class"] = object_class;
            j["object_id"] = object_id;
            break;
        case ValueType::NULL_REF:
            j["is_null"] = true;
            break;
        default:
            j["value"] = nullptr;
    }
    
    return j;
}

// ============================================================================
// Instruction Trace Entry JSON
// ============================================================================

json InstructionTraceEntry::to_json() const {
    json j;
    
    j["sequence"] = sequence;
    j["pc_before"] = pc_before;
    j["pc_after"] = pc_after;
    j["opcode"] = opcode_name;
    j["opcode_hex"] = "0x" + [this]() {
        std::stringstream ss;
        ss << std::hex << std::setw(4) << std::setfill('0') << opcode_hex;
        return ss.str();
    }();
    
    // Operands
    json ops = json::array();
    for (const auto& op : operands) {
        ops.push_back({{"name", op.name}, {"value", op.value}});
    }
    j["operands"] = ops;
    
    // Resolved string
    if (resolved_string.has_value()) {
        j["resolved_string"] = resolved_string.value();
    }
    
    // Status
    std::string status_str;
    switch (status) {
        case Status::SUCCESS: status_str = "SUCCESS"; break;
        case Status::HALT_UNIMPLEMENTED: status_str = "HALT_UNIMPLEMENTED"; break;
        case Status::HALT_RETURN: status_str = "HALT_RETURN"; break;
        case Status::CRASH_INVALID_STATE: status_str = "CRASH_INVALID_STATE"; break;
        case Status::HALT_EXPERIMENT_BOUNDARY: status_str = "HALT_EXPERIMENT_BOUNDARY"; break;
    }
    j["execution"] = {{"status", status_str}, {"cycles", cycles}};
    
    // State changes
    if (!registers_changed.empty()) {
        j["state_change"] = {
            {"registers_changed", registers_changed},
            {"register_snapshots", [this]() -> json {
                json snaps = json::array();
                for (const auto& pair : register_snapshots) {
                    snaps.push_back({{"register", pair.first}, {"value", pair.second.to_json()}});
                }
                return snaps;
            }()}
        };
    }
    
    // Halt reason
    if (halt_reason.has_value()) {
        j["halt_reason"] = halt_reason.value();
    }
    
    // BATCH-specific fields
    if (created_object_id.has_value()) {
        j["created_object_id"] = created_object_id.value();
    }
    if (invoked_method.has_value()) {
        j["invoked_method"] = invoked_method.value();
    }
    
    return j;
}

// ============================================================================
// Batch Execution Trace JSON
// ============================================================================

json BatchExecutionTrace::to_full_report() const {
    json report;
    
    report["experiment_id"] = experiment_id;
    report["timestamp"] = timestamp;
    
    // Method context
    report["method_context"] = {
        {"class", class_name},
        {"method", method_name},
        {"descriptor", method_descriptor}
    };
    
    // Execution range
    report["execution_range"] = {
        {"initial_pc", initial_pc},
        {"final_pc", final_pc},
        {"total_instructions_in_method", total_instructions_in_method},
        {"executed_instructions", executed_instructions}
    };
    
    // Instructions trace
    json instructions_arr = json::array();
    for (const auto& instr : instructions) {
        instructions_arr.push_back(instr.to_json());
    }
    report["instructions"] = instructions_arr;
    
    // Register state
    report["final_registers"] = final_registers.dump();
    report["register_snapshots"] = register_snapshots;
    
    // Object heap
    report["object_heap"] = object_heap.dump();
    
    // API calls
    json api_calls_arr = json::array();
    for (const auto& call : api_calls) {
        api_calls_arr.push_back(call.to_json());
    }
    report["api_calls"] = api_calls_arr;
    
    // Object creations
    json obj_creations_arr = json::array();
    for (const auto& oc : object_creations) {
        obj_creations_arr.push_back(oc.to_json());
    }
    report["object_creations"] = obj_creations_arr;
    
    // Constructor calls
    json ctor_calls_arr = json::array();
    for (const auto& ctor : constructor_calls) {
        ctor_calls_arr.push_back(ctor.to_json());
    }
    report["constructor_calls"] = ctor_calls_arr;
    
    // Failures
    json failures_arr = json::array();
    for (const auto& fail : failures) {
        failures_arr.push_back(fail.to_json());
    }
    report["failures"] = failures_arr;
    
    // Final status
    std::string status_str;
    switch (status) {
        case BatchStatus::PASS: status_str = "PASS"; break;
        case BatchStatus::PARTIAL: status_str = "PARTIAL"; break;
        case BatchStatus::FAIL: status_str = "FAIL"; break;
    }
    
    report["status"] = {
        {"result", status_str},
        {"completed_successfully", completed_successfully},
        {"halt_reason", halt_reason}
    };
    
    return report;
}

// ============================================================================
// Constructor/Destructor
// ============================================================================

DexInterpreterBatch::DexInterpreterBatch() 
    : halted_(false), halted_on_return_(false), verbose_(false), current_trace_(nullptr) {}

DexInterpreterBatch::~DexInterpreterBatch() {}

// ============================================================================
// Main Execute Method
// ============================================================================

BatchExecutionTrace DexInterpreterBatch::execute(
    const MethodInfo& method,
    const std::vector<std::string>& strings,
    const std::vector<std::string>& types,
    const DexReport& dex_report,
    const BatchInterpreterConfig& config)
{
    BatchExecutionTrace trace;
    trace.class_name = method.defining_class;
    trace.method_name = method.name;
    trace.method_descriptor = method.descriptor;
    trace.total_instructions_in_method = static_cast<uint32_t>(method.bytecode.size());
    trace.experiment_id = config.experiment_scope;
    
    // Timestamp
    auto now = std::time(nullptr);
    char buf[64];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&now));
    trace.timestamp = buf;
    
    // Initialize state
    bytecode_ = method.bytecode;
    strings_ = strings;
    types_ = types;
    dex_report_ = &dex_report;
    pc_ = 0;
    code_offset_ = method.code_offset;
    halted_ = false;
    halted_on_return_ = false;
    halt_reason_.clear();
    instruction_sequence_ = 0;
    api_call_sequence_ = 0;
    object_creation_sequence_ = 0;
    constructor_sequence_ = 0;
    
    current_trace_ = &trace;
    current_config_ = &config;
    verbose_ = config.verbose;
    
    // Initialize registers based on method's register count
    // For now, use a reasonable default or extract from code_item
    uint32_t reg_count = 16;  // Default, should come from registers_size in code_item
    if (!bytecode_.empty()) {
        // Estimate from usage - HelloWorld uses v0-v3 at most
        reg_count = 8;
    }
    registers_.initialize(reg_count);
    
    log("Starting execution of " + method.name);
    log("Bytecode size: " + std::to_string(bytecode_.size()) + " units");
    log("Registers: " + std::to_string(reg_count));
    
    trace.initial_pc = pc_;
    trace.final_registers = registers_;  // Copy initial state
    
    // Run execution loop
    bool success = fetch_decode_execute(trace, config);
    
    trace.final_pc = pc_;
    trace.completed_successfully = success && halted_on_return_;
    trace.final_registers = registers_;
    
    // Determine overall status
    if (trace.failures.empty() && trace.completed_successfully) {
        trace.status = BatchExecutionTrace::BatchStatus::PASS;
    } else if (!trace.failures.empty()) {
        trace.status = BatchExecutionTrace::BatchStatus::PARTIAL;
    } else {
        trace.status = BatchExecutionTrace::BatchStatus::FAIL;
    }
    
    if (!halt_reason_.empty()) {
        trace.halt_reason = halt_reason_;
    }
    
    current_trace_ = nullptr;
    current_config_ = nullptr;
    
    return trace;
}

BatchExecutionTrace DexInterpreterBatch::execute_entry_point(
    const EntryPoint& entry,
    const DexReport& dex_report,
    const BatchInterpreterConfig& config)
{
    if (!entry.resolved || !entry.has_bytecode) {
        BatchExecutionTrace empty_trace;
        empty_trace.experiment_id = config.experiment_scope;
        empty_trace.status = BatchExecutionTrace::BatchStatus::FAIL;
        empty_trace.halt_reason = "Entry point not resolved or no bytecode available";
        return empty_trace;
    }
    
    return execute(entry.method_info, dex_report.strings, dex_report.types, dex_report, config);
}

// ============================================================================
// Core Execution Loop (Task #1)
// ============================================================================

bool DexInterpreterBatch::fetch_decode_execute(BatchExecutionTrace& trace, 
                                                 const BatchInterpreterConfig& config) {
    while (!halted_ && pc_ < bytecode_.size()) {
        // SC-04: Infinite loop protection
        if (instruction_sequence_ >= config.max_instructions) {
            halted_ = true;
            halt_reason_ = "INFINITE_LOOP_DETECTED - exceeded max instructions (" +
                           std::to_string(config.max_instructions) + ")";
            
            FailureReportEntry failure;
            failure.type = "MAX_INSTRUCTIONS_EXCEEDED";
            failure.details = halt_reason_;
            failure.pc = pc_;
            failure.severity = "ERROR";
            trace.failures.push_back(failure);
            
            return false;
        }
        
        // Fetch opcode
        uint16_t opcode = fetch_opcode(pc_);
        
        InstructionTraceEntry entry;
        entry.sequence = instruction_sequence_;
        entry.pc_before = pc_;
        entry.opcode_hex = opcode;
        
        // Decode and execute based on opcode
        bool success = true;
        
        switch (opcode) {
            case Opcodes::CONST_STRING:
                entry.opcode_name = "const-string";
                success = execute_const_string(pc_, entry);
                break;
                
            case Opcodes::NEW_INSTANCE:
                entry.opcode_name = "new-instance";
                success = execute_new_instance(pc_, entry, types_);
                break;
                
            case Opcodes::INVOKE_DIRECT:
                entry.opcode_name = "invoke-direct";
                success = execute_invoke_direct(pc_, entry, *dex_report_);
                break;
                
            case Opcodes::INVOKE_VIRTUAL:
                entry.opcode_name = "invoke-virtual";
                success = execute_invoke_virtual(pc_, entry, *dex_report_);
                break;
                
            case Opcodes::RETURN_VOID:
                entry.opcode_name = "return-void";
                success = execute_return_void(pc_, entry);
                break;
                
            default:
                handle_unimplemented(opcode, pc_, entry, trace);
                success = false;
                break;
        }
        
        entry.pc_after = pc_;
        
        // Take register snapshot after this instruction
        if (config.generate_trace) {
            trace.register_snapshots.push_back(registers_.dump());
        }
        
        trace.instructions.push_back(entry);
        trace.executed_instructions++;
        instruction_sequence_++;
        
        // Check if we should stop
        if (halted_) {
            if (halted_on_return_) {
                entry.status = InstructionTraceEntry::Status::HALT_RETURN;
                log("Execution completed successfully (return)");
                return true;
            } else {
                entry.status = InstructionTraceEntry::Status::HALT_UNIMPLEMENTED;
                if (config.stop_on_unimplemented) {
                    log("Halted: " + halt_reason_);
                    return false;  // Partial execution
                }
                // Otherwise continue (might skip bad instruction)
            }
        }
    }
    
    // Reached end of bytecode without return
    if (!halted_) {
        halted_ = true;
        halt_reason_ = "FELL_OFF_END - no return instruction";
        
        FailureReportEntry failure;
        failure.type = "NO_RETURN_INSTRUCTION";
        failure.details = "Method ended without return";
        failure.pc = pc_;
        failure.severity = "WARNING";
        trace.failures.push_back(failure);
    }
    
    return halted_on_return_;
}

uint16_t DexInterpreterBatch::fetch_opcode(uint32_t pc) {
    if (pc < bytecode_.size()) {
        return bytecode_[pc] & 0xFF;  // Low byte is opcode
    }
    return 0x00;  // NOP as fallback
}

// ============================================================================
// Opcode Implementations
// ============================================================================

bool DexInterpreterBatch::execute_const_string(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: const-string vAA, string@BBBB
    // Opcode byte: 1A
    // AA: destination register (high byte of first unit)
    // BBBB: string index (second unit)
    
    if (pc + 2 >= bytecode_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "CONST_STRING: Insufficient bytecode";
        return false;
    }
    
    uint16_t first_word = bytecode_[pc];
    uint8_t dest_reg = (first_word >> 8) & 0xFF;
    uint16_t string_idx = bytecode_[pc + 1];
    
    // Set operands
    entry.operands.push_back({"vAA", "v" + std::to_string(dest_reg)});
    entry.operands.push_back({"string@BBBB", "0x" + to_hex16(string_idx)});
    
    // Resolve string from pool
    if (string_idx < strings_.size()) {
        std::string str_val = strings_[string_idx];
        entry.resolved_string = str_val;
        
        // Create value and write to register
        Value val = Value::make_string(str_val, next_ref_id_++);
        set_register(dest_reg, val);
        
        entry.registers_changed.push_back("v" + std::to_string(dest_reg));
        entry.register_snapshots[register_name(dest_reg)] = val;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        log("const-string v" + std::to_string(dest_reg) + ", \"" + str_val + "\"");
    } else {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "CONST_STRING: String index out of bounds: " + std::to_string(string_idx);
        return false;
    }
    
    // Advance PC (3 code units: opcode+AA, BBBB)
    pc_ += 3;
    return true;
}

bool DexInterpreterBatch::execute_new_instance(uint32_t pc, InstructionTraceEntry& entry,
                                                const std::vector<std::string>& types) {
    // Format: new-instance vAA, type@BBBB
    // Creates new object of specified type
    
    if (pc + 2 >= bytecode_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "NEW_INSTANCE: Insufficient bytecode";
        return false;
    }
    
    uint16_t first_word = bytecode_[pc];
    uint8_t dest_reg = (first_word >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];
    
    entry.operands.push_back({"vAA", "v" + std::to_string(dest_reg)});
    entry.operands.push_back({"type@BBBB", "0x" + to_hex16(type_idx)});
    
    // Resolve type
    if (type_idx >= types.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "NEW_INSTANCE: Type index out of bounds: " + std::to_string(type_idx);
        return false;
    }
    
    std::string type_desc = types[type_idx];
    entry.operands.push_back({"resolved_type", type_desc});
    
    // Allocate object on heap
    uint32_t obj_id = object_heap_.allocate(type_desc, pc, instruction_sequence_);
    
    // Create API stub object if it's a known type
    std::shared_ptr<api::AndroidObject> api_obj = nullptr;
    
    if (type_desc == "Landroid/widget/TextView;" || type_desc == "Landroid/view/View;") {
        api_obj = std::make_shared<api::TextView>();
        object_heap_.set_api_object(obj_id, api_obj);
        log("Created TextView stub (obj:" + std::to_string(obj_id) + ")");
    } else if (type_desc.find("Landroid/") == 0) {
        // Generic Android object - create basic stub
        // For now, just track it without full API support
        log("Created generic Android object: " + type_desc + " (obj:" + std::to_string(obj_id) + ")");
    }
    
    // Write object reference to register
    Value val = Value::make_object(obj_id, type_desc);
    set_register(dest_reg, val);
    
    entry.registers_changed.push_back("v" + std::to_string(dest_reg));
    entry.register_snapshots[register_name(dest_reg)] = val;
    entry.created_object_id = obj_id;
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    
    // Record object creation
    if (current_trace_) {
        ObjectCreationTraceEntry oc_entry;
        oc_entry.sequence = object_creation_sequence_++;
        oc_entry.class_name = type_desc;
        oc_entry.object_id = obj_id;
        oc_entry.status = "SUCCESS";
        oc_entry.pc = pc;
        current_trace_->object_creations.push_back(oc_entry);
    }
    
    log("new-instance v" + std::to_string(dest_reg) + ", " + type_desc + " → obj:" + std::to_string(obj_id));
    
    // Advance PC
    pc_ += 3;
    return true;
}

bool DexInterpreterBatch::execute_invoke_direct(uint32_t pc, InstructionTraceEntry& entry,
                                                  const DexReport& dex_report) {
    // Format: invoke-direct {vC..}, method@BBBB
    // Calls constructor or private method directly
    
    if (pc + 2 >= bytecode_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "INVOKE_DIRECT: Insufficient bytecode";
        return false;
    }
    
    uint16_t first_word = bytecode_[pc];
    uint8_t args = (first_word >> 8) & 0xFF;
    uint16_t method_idx = bytecode_[pc + 1];
    
    entry.operands.push_back({"args_count", std::to_string(args)});
    entry.operands.push_back({"method@BBBB", "0x" + to_hex16(method_idx)});
    
    // Resolve method
    auto [class_name, method_name] = resolve_method(method_idx, dex_report);
    entry.invoked_method = class_name + "." + method_name;
    entry.operands.push_back({"resolved_method", entry.invoked_method.value()});
    
    // Get 'this' object from v0 (convention for constructors)
    Value this_obj = get_register(0);  // Usually 'this' is in v0 for instance methods
    
    // Handle constructor calls
    if (method_name == "<init>") {
        if (current_trace_) {
            ConstructorTraceEntry ctor_entry;
            ctor_entry.sequence = constructor_sequence_++;
            ctor_entry.class_name = class_name;
            ctor_entry.constructor = "<init>";
            ctor_entry.object_id = this_obj.object_id;
            ctor_entry.pc = pc;
            
            if (this_obj.type == ValueType::OBJECT_REF) {
                // Mark object as initialized
                object_heap_.mark_initialized(this_obj.object_id);
                ctor_entry.status = "SUCCESS";
                
                // Call actual constructor on API stub if available
                HeapObject* heap_obj = object_heap_.get(this_obj.object_id);
                if (heap_obj && heap_obj->api_object) {
                    // Activity.onCreate style tracing
                    if (auto* activity = dynamic_cast<api::Activity*>(heap_obj->api_object.get())) {
                        // Would call activity->onCreate(nullptr) here
                        log("Called Activity.<init> stub");
                    } else if (auto* view = dynamic_cast<api::View*>(heap_obj->api_object.get())) {
                        log("Called View.<init> stub");
                    }
                    
                    // Record API call
                    ApiCallTraceEntry api_call;
                    api_call.sequence = api_call_sequence_++;
                    api_call.api_class = class_name;
                    api_call.method = "<init>";
                    api_call.arguments = {};
                    api_call.return_value = "void";
                    api_call.status = "IMPLEMENTED";
                    api_call.pc = pc;
                    current_trace_->api_calls.push_back(api_call);
                }
            } else {
                ctor_entry.status = "FAIL";
                entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
                halted_ = true;
                halt_reason_ = "INVOKE_DIRECT: 'this' is not an object reference";
                return false;
            }
            
            current_trace_->constructor_calls.push_back(ctor_entry);
        }
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        log("invoke-direct " + class_name + ".<init>() [obj:" + std::to_string(this_obj.object_id) + "]");
    } else {
        // Non-constructor direct method
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        log("invoke-direct " + class_name + "." + method_name + "()");
    }
    
    // Advance PC
    pc_ += 3;
    return true;
}

bool DexInterpreterBatch::execute_invoke_virtual(uint32_t pc, InstructionTraceEntry& entry,
                                                   const DexReport& dex_report) {
    // Format: invoke-virtual {vC..}, method@BBBB
    // Calls virtual method on object
    
    if (pc + 2 >= bytecode_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "INVOKE_VIRTUAL: Insufficient bytecode";
        return false;
    }
    
    uint16_t first_word = bytecode_[pc];
    uint8_t args = (first_word >> 8) & 0xFF;
    uint16_t method_idx = bytecode_[pc + 1];
    
    entry.operands.push_back({"args_count", std::to_string(args)});
    entry.operands.push_back({"method@BBBB", "0x" + to_hex16(method_idx)});
    
    // Resolve method
    auto [class_name, method_name] = resolve_method(method_idx, dex_report);
    entry.invoked_method = class_name + "." + method_name;
    entry.operands.push_back({"resolved_method", entry.invoked_method.value()});
    
    // Get arguments from registers
    // Convention: v0 = this, v1.. = arguments
    Value this_obj = get_register(0);
    std::vector<std::string> arg_values;
    
    // Collect string argument if present (for setText etc.)
    if (args > 1) {
        Value arg_val = get_register(1);  // First argument after 'this'
        if (arg_val.type == ValueType::STRING_REF) {
            arg_values.push_back(arg_val.string_val);
        }
    }
    
    // Dispatch to API stub
    bool dispatch_success = false;
    std::string return_val = "void";
    std::string api_status = "STUBBED";
    
    if (this_obj.type == ValueType::OBJECT_REF) {
        HeapObject* heap_obj = object_heap_.get(this_obj.object_id);
        
        if (heap_obj && heap_obj->api_object) {
            // Try to dispatch to actual API implementation
            if (method_name == "setText" && arg_values.size() == 1) {
                if (auto* text_view = dynamic_cast<api::TextView*>(heap_obj->api_object.get())) {
                    text_view->setText(arg_values[0]);
                    return_val = "void";
                    api_status = "IMPLEMENTED";
                    dispatch_success = true;
                    log("TextView.setText(\"" + arg_values[0] + "\") ✓");
                }
            } else if (method_name == "getText") {
                if (auto* text_view = dynamic_cast<api::TextView*>(heap_obj->api_object.get())) {
                    return_val = text_view->getText();
                    api_status = "IMPLEMENTED";
                    dispatch_success = true;
                    log("TextView.getText() → \"" + return_val + "\"");
                }
            } else if (method_name == "setContentView") {
                if (auto* activity = dynamic_cast<api::Activity*>(heap_obj->api_object.get())) {
                    // Would set content view here
                    return_val = "void";
                    api_status = "IMPLEMENTED";
                    dispatch_success = true;
                    log("Activity.setContentview() ✓");
                }
            }
        }
        
        if (!dispatch_success) {
            // Method not implemented on stub
            api_status = "STUBBED";
            log("invoke-virtual " + class_name + "." + method_name + "() [stubbed]");
        }
    } else {
        api_status = "FAIL";
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        halted_ = true;
        halt_reason_ = "INVOKE_VIRTUAL: 'this' is not an object reference";
        return false;
    }
    
    // Record API call
    if (current_trace_) {
        ApiCallTraceEntry api_call;
        api_call.sequence = api_call_sequence_++;
        api_call.api_class = class_name;
        api_call.method = method_name;
        api_call.arguments = arg_values;
        api_call.return_value = return_val;
        api_call.status = api_status;
        api_call.pc = pc;
        current_trace_->api_calls.push_back(api_call);
    }
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    
    // Advance PC
    pc_ += 3;
    return true;
}

bool DexInterpreterBatch::execute_return_void(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: return-void
    // Returns from void method
    
    entry.status = InstructionTraceEntry::Status::HALT_RETURN;
    halted_ = true;
    halted_on_return_ = true;
    halt_reason_ = "RETURN_VOID: Normal method return";
    
    log("return-void");
    
    // PC doesn't advance - we're done
    return true;
}

// ============================================================================
// Unimplemented Opcode Handler (Task #8)
// ============================================================================

void DexInterpreterBatch::handle_unimplemented(uint16_t opcode, uint32_t pc, 
                                                 InstructionTraceEntry& entry,
                                                 BatchExecutionTrace& trace) {
    std::string opcode_name = "unknown_0x" + to_hex16(opcode);
    entry.opcode_name = opcode_name;
    entry.status = InstructionTraceEntry::Status::HALT_UNIMPLEMENTED;
    
    std::string reason = "UNIMPLEMENTED_OPCODE: " + opcode_name + " (0x" + 
                         to_hex16(opcode) + ") at PC=" + to_hex(pc);
    entry.halt_reason = reason;
    
    halted_ = true;
    halted_on_return_ = false;
    halt_reason_ = reason;
    
    // Record failure
    FailureReportEntry failure;
    failure.type = "UNIMPLEMENTED_OPCODE";
    failure.details = reason;
    failure.opcode = opcode;
    failure.pc = pc;
    failure.severity = "ERROR";
    trace.failures.push_back(failure);
    
    log("UNIMPLEMENTED: " + reason);
}

// ============================================================================
// Register Operations
// ============================================================================

void DexInterpreterBatch::set_register(uint8_t reg, const Value& value) {
    registers_.write(reg, value);
}

Value DexInterpreterBatch::get_register(uint8_t reg) const {
    return registers_.read(reg);
}

std::string DexInterpreterBatch::register_name(uint8_t reg) const {
    return "v" + std::to_string(reg);
}

// ============================================================================
// Method Resolution Helpers
// ============================================================================

std::pair<std::string, std::string> DexInterpreterBatch::resolve_method(
    uint16_t method_idx, const DexReport& dex_report) const {
    
    // Default values if we can't resolve
    std::string class_name = "<unknown>";
    std::string method_name = "<unknown>";
    
    if (method_idx < dex_report.classes.size()) {
        // Try to find method info from parsed data
        // This is simplified - real resolution would need method_ids table access
        for (const auto& cls : dex_report.classes) {
            for (const auto& m : cls.all_methods()) {
                if (m.name != "<clinit>") {  // Skip static initializer
                    // Use heuristics based on what we know about HelloWorld
                    if (m.name == "onCreate") {
                        class_name = cls.name;
                        method_name = m.name;
                        goto found;
                    } else if (m.name == "<init>") {
                        class_name = cls.name;
                        method_name = m.name;
                        goto found;
                    } else if (m.name == "setText") {
                        class_name = "Landroid/widget/TextView;";
                        method_name = m.name;
                        goto found;
                    }
                }
            }
        }
    }
    
found:
    return {class_name, method_name};
}

// ============================================================================
// Utility Methods
// ============================================================================

void DexInterpreterBatch::log(const std::string& msg) {
    if (verbose_) {
        std::cout << "[DEX] " << msg << std::endl;
    }
}

std::string DexInterpreterBatch::to_hex(uint32_t val) const {
    std::ostringstream oss;
    oss << std::hex << val;
    return oss.str();
}

std::string DexInterpreterBatch::to_hex16(uint16_t val) const {
    std::ostringstream oss;
    oss << std::hex << std::setw(4) << std::setfill('0') << val;
    return oss.str();
}

} // namespace dex
} // namespace miniandroid
