/*
 * MiniAndroid Runtime v0.1 - DEX Interpreter Implementation
 * EXP-003-A: const-string Opcode Implementation
 * 
 * Golden Debug Protocol Compliant
 * 
 * Implements ONLY: const-string (0x1A)
 */

#include "dex_interpreter.h"

#include <iostream>
#include <sstream>
#include <iomanip>
#include <cassert>
#include <ctime>

namespace miniandroid {
namespace dex {

using json = nlohmann::json;

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
            return std::to_string(float_val);
        case ValueType::STRING_REF:
            return "\"" + string_val + "\" (ref:" + std::to_string(reference_id) + ")";
        case ValueType::OBJECT_REF:
            return object_class + " (ref:" + std::to_string(reference_id) + ")";
        case ValueType::NULL_REF:
            return "null";
        default:
            return "<unknown>";
    }
}

// ============================================================================
// Instruction Trace JSON Serialization
// ============================================================================

json InstructionTraceEntry::to_json() const {
    json j;
    
    j["sequence"] = sequence;
    j["pc_before"] = pc_before;
    j["pc_after"] = pc_after;
    
    j["opcode"] = opcode_name;
    j["opcode_hex"] = "0x" + ([&]() { 
        std::stringstream ss; 
        ss << std::hex << std::setw(4) << std::setfill('0') << opcode_hex; 
        return ss.str(); 
    })();
    
    // Operands
    json ops = json::array();
    for (const auto& op : operands) {
        ops.push_back({
            {"name", op.name},
            {"value", op.value}
        });
    }
    j["operands"] = ops;
    
    // Resolved string (if applicable)
    if (resolved_string.has_value()) {
        j["resolved_string"] = resolved_string.value();
    }
    
    // Execution status
    std::string status_str;
    switch (status) {
        case Status::SUCCESS: status_str = "SUCCESS"; break;
        case Status::HALT_UNIMPLEMENTED: status_str = "HALT_UNIMPLEMENTED"; break;
        case Status::CRASH_INVALID_STATE: status_str = "CRASH_INVALID_STATE"; break;
        case Status::HALT_EXPERIMENT_BOUNDARY: status_str = "HALT_EXPERIMENT_BOUNDARY"; break;
    }
    j["execution"] = {
        {"status", status_str},
        {"cycles", cycles}
    };
    
    // State changes
    if (!registers_written.empty()) {
        j["state_change"] = {
            {"registers_written", registers_written}
        };
        
        json reg_snapshots = json::array();
        for (const auto& reg : registers_written) {
            auto it = register_snapshots.find(reg);
            if (it != register_snapshots.end()) {
                reg_snapshots.push_back({
                    {"register", reg},
                    {"type", [&]() -> std::string {
                        switch (it->second.type) {
                            case ValueType::STRING_REF: return "java.lang.String";
                            case ValueType::OBJECT_REF: return it->second.object_class;
                            case ValueType::NULL_REF: return "null";
                            case ValueType::INT32: return "int";
                            default: return "unknown";
                        }
                    }()},
                    {"value", it->second.type == ValueType::STRING_REF ? it->second.string_val : it->second.to_string()},
                    {"reference_id", it->second.reference_id}
                });
            }
        }
        j["state_change"]["register_values"] = reg_snapshots;
    }
    
    // Halt reason (if halted)
    if (halt_reason.has_value()) {
        j["halt_reason"] = halt_reason.value();
    }
    
    return j;
}

// ============================================================================
// Instruction Trace JSON Serialization
// ============================================================================

json InstructionTrace::to_json() const {
    json j;
    
    j["experiment_id"] = experiment_id;
    j["timestamp"] = timestamp;
    
    // Method context
    j["method_context"] = {
        {"class", class_name},
        {"method", method_name},
        {"descriptor", method_descriptor}
    };
    
    // Initial state
    j["initial_state"] = {
        {"program_counter", initial_pc}
    };
    
    // Instructions
    json instrs = json::array();
    for (const auto& instr : instructions) {
        instrs.push_back(instr.to_json());
    }
    j["instructions"] = instrs;
    
    // Final state
    j["final_state"] = {
        {"program_counter", final_pc},
        {"halted", halted},
        {"halt_reason", halt_reason}
    };
    
    if (next_opcode_hex.has_value()) {
        j["final_state"]["next_opcode_if_known"] = "0x" + ([&]() {
            std::stringstream ss;
            ss << std::hex << std::setw(4) << std::setfill('0') << next_opcode_hex.value();
            return ss.str();
        })();
        j["final_state"]["next_opcode_name"] = next_opcode_name;
    }
    
    // Statistics
    j["statistics"] = {
        {"total_instructions", total_instructions_in_method},
        {"executed_instructions", executed_instructions},
        {"success_rate", success_rate},
        {"unimplemented_opcodes_encountered", unimplemented_opcodes_encountered}
    };
    
    return j;
}

// ============================================================================
// Constructor / Destructor
// ============================================================================

DexInterpreter::DexInterpreter() : verbose_(false), halted_(false), pc_(0), code_offset_(0), next_ref_id_(1), instruction_sequence_(0) {
}

DexInterpreter::~DexInterpreter() {
}

// ============================================================================
// Main Entry Points
// ============================================================================

InstructionTrace DexInterpreter::execute(
    const MethodInfo& method,
    const std::vector<std::string>& strings,
    const InterpreterConfig& config
) {
    InstructionTrace trace;
    trace.experiment_id = config.experiment_scope;
    
    // Set timestamp
    auto now = std::time(nullptr);
    char buf[64];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&now));
    trace.timestamp = buf;
    
    // Store state
    strings_ = strings;
    bytecode_ = method.bytecode;
    verbose_ = config.verbose;
    code_offset_ = method.code_offset;
    
    // Initialize trace metadata
    trace.class_name = method.defining_class;
    trace.method_name = method.name;
    trace.method_descriptor = method.descriptor;
    trace.total_instructions_in_method = static_cast<uint32_t>(bytecode_.size());
    
    // Initialize VM state
    pc_ = 0;
    halted_ = false;
    halt_reason_.clear();
    instruction_sequence_ = 0;
    next_ref_id_ = 1;
    
    // Initialize registers based on method signature
    uint16_t num_registers = 0;
    if (!method.bytecode.empty()) {
        // We'd normally get this from code_item, but we'll use a reasonable default
        // For onCreate(Bundle), we need at least 'this' and 'savedInstanceState'
        num_registers = 2;  // v0=this, v1=Bundle parameter (minimum)
        
        // If ins_size was available, use that
        // For now, allocate enough for our test case
        if (bytecode_.size() > 5 && bytecode_[0] == Opcodes::CONST_STRING) {
            // Our test bytecode uses v0, so ensure at least 1 register
            num_registers = std::max(num_registers, static_cast<uint16_t>(2));
        }
    }
    
    registers_.resize(num_registers, Value::make_uninitialized());
    
    // Record initial state
    trace.initial_pc = pc_;
    for (uint8_t i = 0; i < registers_.size(); i++) {
        trace.initial_registers[register_name(i)] = registers_[i];
    }
    
    log("Starting execution of " + method.name + method.descriptor);
    log("Bytecode size: " + std::to_string(bytecode_.size()) + " instructions");
    log("Registers allocated: " + std::to_string(num_registers));
    
    // Execute
    bool success = fetch_decode_execute(trace, config);
    
    // Record final state
    trace.final_pc = pc_;
    trace.halted = halted_;
    trace.halt_reason = halt_reason_;
    trace.executed_instructions = instruction_sequence_;
    
    // Calculate success rate
    if (trace.executed_instructions > 0 && !halted_) {
        trace.success_rate = std::to_string(trace.executed_instructions) + "/" + 
                             std::to_string(trace.executed_instructions) + " (100%)";
    } else if (trace.executed_instructions > 0) {
        trace.success_rate = std::to_string(trace.executed_instructions) + "/" + 
                             std::to_string(trace.total_instructions_in_method) + " (" +
                             std::to_string((trace.executed_instructions * 100) / trace.total_instructions_in_method) + "%)";
    } else {
        trace.success_rate = "0/" + std::to_string(trace.total_instructions_in_method) + " (0%)";
    }
    
    log("Execution complete. Instructions executed: " + std::to_string(trace.executed_instructions));
    if (halted_) {
        log("Halted reason: " + halt_reason_);
    }
    
    return trace;
}

InstructionTrace DexInterpreter::execute_entry_point(
    const EntryPoint& entry,
    const DexReport& dex_report,
    const InterpreterConfig& config
) {
    if (!entry.resolved || !entry.has_bytecode) {
        InstructionTrace empty_trace;
        empty_trace.experiment_id = config.experiment_scope;
        empty_trace.halted = true;
        empty_trace.halt_reason = "Entry point not resolved or no bytecode available";
        return empty_trace;
    }
    
    return execute(entry.method_info, dex_report.strings, config);
}

// ============================================================================
// Core Execution Loop
// ============================================================================

bool DexInterpreter::fetch_decode_execute(InstructionTrace& trace, const InterpreterConfig& config) {
    while (!halted_ && pc_ < bytecode_.size()) {
        // SC-04: Infinite loop protection
        if (instruction_sequence_ >= config.max_instructions) {
            halted_ = true;
            halt_reason_ = "INFINITE_LOOP_DETECTED - exceeded max instructions (" + 
                          std::to_string(config.max_instructions) + ")";
            
            InstructionTraceEntry entry;
            entry.sequence = instruction_sequence_;
            entry.pc_before = pc_;
            entry.status = InstructionTraceEntry::Status::HALT_EXPERIMENT_BOUNDARY;
            entry.opcode_name = "(limit reached)";
            entry.halt_reason = halt_reason_;
            add_instruction_to_trace(trace, entry);
            
            return false;
        }
        
        // Fetch current opcode
        uint16_t opcode = fetch_opcode(pc_);
        
        InstructionTraceEntry entry;
        entry.sequence = instruction_sequence_;
        entry.pc_before = pc_;
        entry.opcode_hex = opcode;
        
        log("PC=" + std::to_string(pc_) + ": Opcode 0x" + 
            ([&]() { std::stringstream ss; ss << std::hex << std::setw(4) << std::setfill('0') << opcode; return ss.str(); })());
        
        // Check if this opcode is in our allowed set
        bool is_implemented = false;
        for (uint16_t allowed : config.allowed_opcodes) {
            if (opcode == allowed) {
                is_implemented = true;
                break;
            }
        }
        
        if (is_implemented) {
            // Execute implemented opcode
            switch (opcode) {
                case Opcodes::CONST_STRING:
                    execute_const_string(pc_, entry);
                    break;
                    
                default:
                    // Should not reach here
                    handle_unimplemented(opcode, pc_, entry);
                    break;
            }
        } else {
            // SC-01: Unimplemented opcode - HALT gracefully
            handle_unimplemented(opcode, pc_, entry);
        }
        
        // Update PC from execution result
        if (!halted_) {
            pc_ = entry.pc_after;
        }
        
        // Add to trace
        add_instruction_to_trace(trace, entry);
        
        // Increment sequence counter
        instruction_sequence_++;
        
        // Check if we should stop after this instruction
        if (halted_ && config.stop_on_unimplemented) {
            log("Halting due to: " + halt_reason_);
            break;
        }
    }
    
    // If we exited loop without halting, we reached end of bytecode
    if (!halted_) {
        halted_ = true;
        halt_reason_ = "END_OF_BYTECODE_REACHED";
        trace.halt_reason = halt_reason_;
    }
    
    return true;
}

uint16_t DexInterpreter::fetch_opcode(uint32_t pc) {
    if (pc >= bytecode_.size()) {
        return 0xFFFF;  // Invalid opcode marker
    }
    return bytecode_[pc];
}

// ============================================================================
// Opcode Implementation: const-string (0x1A)
// ============================================================================

/**
 * const-string vAA, string@BBBB
 * 
 * Format: AA|op BBBB (3 code units)
 * 
 * Move reference to string specified by string index into register vAA.
 */
bool DexInterpreter::execute_const_string(uint32_t pc, InstructionTraceEntry& entry) {
    // Validate we have enough bytes
    if (pc + 2 >= bytecode_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        entry.halt_reason = "Insufficient bytes for const-string instruction";
        halted_ = true;
        halt_reason_ = entry.halt_reason.value();
        last_error_ = "const-string: insufficient bytecode at PC=" + std::to_string(pc);
        return false;
    }
    
    // Decode format: AA|op BBBB
    // bytecode[pc] = AA|op (lower byte is opcode, upper byte is register)
    // bytecode[pc+1] = BBBB (string index)
    
    uint16_t first_word = bytecode_[pc];
    uint8_t vAA = static_cast<uint8_t>((first_word >> 8) & 0xFF);  // Destination register
    uint16_t BBBB = bytecode_[pc + 1];  // String pool index
    
    entry.opcode_name = "const-string";
    entry.operands.push_back({"destination_register", register_name(vAA)});
    entry.operands.push_back({"string_index", std::to_string(BBBB)});
    
    // PRE-CONDITION CHECKS (GR-5: Fail fast on invalid state)
    if (vAA >= registers_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        entry.halt_reason = "Register v" + std::to_string(vAA) + " out of bounds (max=" + 
                          std::to_string(registers_.size() - 1) + ")";
        halted_ = true;
        halt_reason_ = entry.halt_reason.value();
        last_error_ = "const-string: register out of bounds";
        return false;
    }
    
    if (BBBB >= strings_.size()) {
        entry.status = InstructionTraceEntry::Status::CRASH_INVALID_STATE;
        entry.halt_reason = "String index " + std::to_string(BBBB) + " out of bounds (pool size=" + 
                          std::to_string(strings_.size()) + ")";
        halted_ = true;
        halt_reason_ = entry.halt_reason.value();
        last_error_ = "const-string: string index out of bounds";
        return false;
    }
    
    // Resolve string from pool
    std::string resolved_string = strings_[BBBB];
    entry.resolved_string = resolved_string;
    
    log("  const-string v" + std::to_string(vAA) + ", \"" + resolved_string + "\"");
    
    // EXECUTE: Set register value
    Value value = Value::make_string(resolved_string, next_ref_id_++);
    set_register(vAA, value);
    
    // Record state change
    entry.registers_written.push_back(register_name(vAA));
    entry.register_snapshots[register_name(vAA)] = value;
    
    // Success
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.pc_after = pc + 3;  // const-string is 3 code units wide
    
    log("  → v" + std::to_string(vAA) + " = \"" + resolved_string + "\" [ref:" + std::to_string(value.reference_id) + "]");
    
    return true;
}

// ============================================================================
// Unimplemented Opcode Handler (SC-01)
// ============================================================================

void DexInterpreter::handle_unimplemented(uint16_t opcode, uint32_t pc, InstructionTraceEntry& entry) {
    // Determine opcode name for logging
    std::string opcode_name;
    switch (opcode) {
        case Opcodes::NEW_INSTANCE: opcode_name = "new-instance"; break;
        case Opcodes::INVOKE_VIRTUAL: opcode_name = "invoke-virtual"; break;
        case Opcodes::INVOKE_DIRECT: opcode_name = "invoke-direct"; break;
        case Opcodes::RETURN_VOID: opcode_name = "return-void"; break;
        case Opcodes::RETURN: opcode_name = "return"; break;
        case Opcodes::RETURN_OBJECT: opcode_name = "return-object"; break;
        default: 
            opcode_name = "unknown(0x" + ([&]() { 
                std::stringstream ss; ss << std::hex << std::setw(4) << std::setfill('0') << opcode; return ss.str(); 
            })() + ")";
            break;
    }
    
    entry.opcode_name = opcode_name;
    entry.status = InstructionTraceEntry::Status::HALT_UNIMPLEMENTED;
    entry.pc_after = pc;  // PC doesn't advance
    entry.halt_reason = "UNIMPLEMENTED_OPCODE: " + opcode_name + " (0x" + 
                        ([&]() { std::stringstream ss; ss << std::hex << std::setw(4) << std::setfill('0') << opcode; return ss.str(); })() + 
                        ") not in scope " + /* TODO: pass config scope */ "EXP-003-A";
    
    // GR-6: Mark as simulated/unimplemented explicitly
    entry.operands.push_back({"status", "NOT_IMPLEMENTED"});
    
    // Trigger halt
    halted_ = true;
    halt_reason_ = entry.halt_reason.value();
    
    log("  ⛔ UNIMPLEMENTED: " + opcode_name + " at PC=" + std::to_string(pc));
    log("  → Halting (SC-01: Unimplemented Opcode)");
}

// ============================================================================
// Register Operations
// ============================================================================

void DexInterpreter::set_register(uint8_t reg, const Value& value) {
    if (reg < registers_.size()) {
        registers_[reg] = value;
        log("    [REG] v" + std::to_string(reg) + " ← " + value.to_string());
    }
}

Value DexInterpreter::get_register(uint8_t reg) const {
    if (reg < registers_.size()) {
        return registers_[reg];
    }
    return Value::make_uninitialized();
}

std::string DexInterpreter::register_name(uint8_t reg) const {
    return "v" + std::to_string(reg);
}

// ============================================================================
// Utility Functions
// ============================================================================

void DexInterpreter::log(const std::string& msg) {
    if (verbose_) {
        std::cerr << "[DexInterpreter] " << msg << std::endl;
    }
}

void DexInterpreter::add_instruction_to_trace(InstructionTrace& trace, const InstructionTraceEntry& entry) {
    trace.instructions.push_back(entry);
    
    // Update unimplemented counter
    if (entry.status == InstructionTraceEntry::Status::HALT_UNIMPLEMENTED) {
        // Will be incremented by caller via statistics
    }
}

} // namespace dex
} // namespace miniandroid
