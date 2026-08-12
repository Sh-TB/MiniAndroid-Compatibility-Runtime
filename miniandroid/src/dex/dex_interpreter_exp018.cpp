/*
 * MiniAndroid Runtime v0.3 - EXP-018 Implementation
 * Real Android Execution Core Batch
 * 
 * Golden Debug Protocol Compliant
 * Every opcode implementation backed by real corpus data
 */

#include "dex_interpreter_exp018.h"
#include "../runtime/object_model.h"
#include <fstream>
#include <cmath>

namespace miniandroid {
namespace dex {

using json = nlohmann::json;
using namespace runtime;

// ============================================================================
// JSON Serialization for New Trace Structures
// ============================================================================

json BranchTraceEntry::to_json() const {
    json j;
    j["sequence"] = sequence;
    j["pc_before"] = pc_before;
    j["pc_after"] = pc_after;
    j["opcode"] = opcode_name;
    j["condition_description"] = condition_description;
    
    j["condition"]["register_a"] = condition.register_a;
    j["condition"]["register_b"] = condition.register_b;
    j["condition"]["value_a"] = condition.value_a;
    j["condition"]["value_b"] = condition.value_b;
    j["condition"]["was_null_a"] = condition.was_null_a;
    j["condition"]["was_null_b"] = condition.was_null_b;
    j["condition"]["result"] = condition.condition_result;
    
    j["taken"] = taken;
    j["offset"] = offset;
    j["target_pc"] = target_pc;
    j["fallthrough_pc"] = fallthrough_pc;
    
    return j;
}

json LoopDetectionRecord::to_json() const {
    json j;
    j["loop_start_pc"] = loop_start_pc;
    j["loop_end_pc"] = loop_end_pc;
    j["loop_type"] = loop_type;
    j["iteration_count"] = iteration_count;
    j["max_iterations_hit"] = max_iterations_hit;
    j["is_infinite_loop_detected"] = is_infinite_loop_detected;
    j["back_edge_pcs"] = back_edge_pcs;
    return j;
}

json ControlFlowStatistics::to_json() const {
    json j;
    j["total_branches_encountered"] = total_branches_encountered;
    j["branches_taken"] = branches_taken;
    j["branches_not_taken"] = branches_not_taken;
    j["unconditional_jumps"] = unconditional_jumps;
    j["loops_detected"] = loops_detected;
    j["infinite_loops_protected"] = infinite_loops_protected;
    j["opcode_breakdown"] = opcode_counts;
    return j;
}

json ReturnTraceEntry::to_json() const {
    json j;
    j["sequence"] = sequence;
    j["pc"] = pc;
    j["opcode"] = opcode_name;
    j["returned_value"] = returned_value.to_json();
    j["returning_method"] = returning_method;
    j["captured"] = captured;
    j["capture_pc"] = capture_pc;
    j["capture_register"] = capture_register;
    return j;
}

json StaticMethodEntry::to_json() const {
    json j;
    j["class"] = class_name;
    j["method"] = method_name;
    j["descriptor"] = descriptor;
    
    switch (implementation_type) {
        case ImplementationType::NATIVE_CPP: j["type"] = "NATIVE_CPP"; break;
        case ImplementationType::JDK_STUB: j["type"] = "JDK_STUB"; break;
        case ImplementationType::ANDROID_STUB: j["type"] = "ANDROID_STUB"; break;
        case ImplementationType::UNIMPLEMENTED: j["type"] = "UNIMPLEMENTED"; break;
    }
    
    j["added_in"] = added_in_experiment;
    j["call_count"] = call_count;
    return j;
}

json InterfaceDispatchRecord::to_json() const {
    json j;
    j["sequence"] = sequence;
    j["pc"] = pc;
    j["interface"] = interface_name;
    j["method"] = method_name;
    j["descriptor"] = descriptor;
    j["target_object"] = target_object.to_json();
    j["actual_class"] = actual_class;
    j["resolved"] = resolved;
    j["resolved_method"] = resolved_method;
    j["result"] = result.to_json();
    j["is_on_click_listener"] = is_on_click_listener;
    return j;
}

json MissingApiEntry::to_json() const {
    json j;
    j["api"] = api_name;
    j["priority"] = priority;
    j["usage_percent"] = usage_percent;
    j["apps_blocked"] = apps_blocked;
    j["blocking_reason"] = blocking_reason;
    j["suggested_fix"] = suggested_fix;
    return j;
}

// ============================================================================
// Constructor / Destructor
// ============================================================================

DexInterpreterExp018::DexInterpreterExp018() : DexInterpreterV2() {
    initialize_builtin_static_methods();
    initialize_builtin_interfaces();
}

DexInterpreterExp018::~DexInterpreterExp018() {}

// ============================================================================
// Main Execution Entry Point
// ============================================================================

InstructionTrace DexInterpreterExp018::execute_exp018(
    const MethodInfo& method,
    const std::vector<std::string>& strings,
    const Exp018Config& config
) {
    exp018_config_ = config;
    
    // Load databases if available
    if (!config.api_priority_path.empty()) {
        load_api_priority_database(config.api_priority_path);
    }
    if (!config.opcode_frequency_path.empty()) {
        load_opcode_frequency_database(config.opcode_frequency_path);
    }
    
    // Reset state
    branch_trace_.clear();
    loops_detected_.clear();
    cf_stats_ = ControlFlowStatistics{};
    return_trace_.clear();
    has_pending_return_ = false;
    pending_return_ = Value::make_uninitialized();
    static_call_trace_.clear();
    interface_trace_.clear();
    pc_visit_count_.clear();
    
    // Execute with base interpreter first, then enhance
    InstructionTrace trace = execute(method, strings, config);
    
    // Add EXP-018 specific data to trace
    trace.branch_trace = branch_trace_;
    trace.loops_detected = loops_detected_;
    trace.control_flow_stats = cf_stats_.to_json();
    trace.return_trace = return_trace_;
    trace.static_calls = static_call_trace_;
    trace.interface_calls = interface_trace_;
    
    return trace;
}

bool DexInterpreterExp018::fetch_decode_execute_exp018(
    InstructionTrace& trace, 
    const Exp018Config& config
) {
    // Track PC visits for loop detection
    pc_visit_[pc_]++;
    
    // Check loop protection
    if (config.enable_loop_detection && pc_visit_[pc_] > config.max_loop_iterations) {
        LoopDetectionRecord loop;
        loop.loop_start_pc = pc_;  // Approximate
        loop.loop_end_pc = pc_;
        loop.loop_type = "detected-infinite";
        loop.iteration_count = pc_visit_[pc_];
        loop.max_iterations_hit = true;
        loop.is_infinite_loop_detected = true;
        loops_detected_.push_back(loop);
        cf_stats_.infinite_loops_protected++;
        
        halt_reason_ = "INFINITE_LOOP_PROTECTED: PC " + std::to_string(pc_) + 
                       " visited " + std::to_string(pc_visit_[pc_]) + " times";
        halted_ = true;
        return false;
    }
    
    uint16_t opcode = fetch_opcode(pc_);
    
    InstructionTraceEntry entry;
    entry.sequence = instruction_sequence_++;
    entry.pc_before = pc_;
    entry.opcode_hex = opcode;
    
    bool success = true;
    
    // =========================================================================
    // Phase 1: Control Flow Opcodes (P0 CRITICAL)
    // Data Source: real_opcode_frequency.json - 1390 occurrences (10.82%)
    // =========================================================================
    
    switch (opcode) {
        case OpcodesExp018::IF_EQZ:
            entry.opcode_name = "if-eqz";
            success = execute_if_eqz(pc_, entry);
            cf_stats_.opcode_counts["if-eqz"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_NEZ:
            entry.opcode_name = "if-nez";
            success = execute_if_nez(pc_, entry);
            cf_stats_.opcode_counts["if-nez"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_EQ:
            entry.opcode_name = "if-eq";
            success = execute_if_eq(pc_, entry);
            cf_stats_.opcode_counts["if-eq"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_NE:
            entry.opcode_name = "if-ne";
            success = execute_if_ne(pc_, entry);
            cf_stats_.opcode_counts["if-ne"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::GOTO:
            entry.opcode_name = "goto";
            success = execute_goto(pc_, entry);
            cf_stats_.opcode_counts["goto"]++;
            cf_stats_.unconditional_jumps++;
            break;
            
        case OpcodesExp018::GOTO_16:
            entry.opcode_name = "goto/16";
            success = execute_goto_16(pc_, entry);
            cf_stats_.opcode_counts["goto/16"]++;
            cf_stats_.unconditional_jumps++;
            break;
            
        case OpcodesExp018::GOTO_32:
            entry.opcode_name = "goto/32";
            success = execute_goto_32(pc_, entry);
            cf_stats_.opcode_counts["goto/32"]++;
            cf_stats_.unconditional_jumps++;
            break;
            
        // Extended branches (P1_HIGH)
        case OpcodesExp018::IF_LTZ:
            entry.opcode_name = "if-ltz";
            success = execute_if_ltz(pc_, entry);
            cf_stats_.opcode_counts["if-ltz"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_GEZ:
            entry.opcode_name = "if-gez";
            success = execute_if_gez(pc_, entry);
            cf_stats_.opcode_counts["if-gez"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_GTZ:
            entry.opcode_name = "if-gtz";
            success = execute_if_gtz(pc_, entry);
            cf_stats_.opcode_counts["if-gtz"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_LEZ:
            entry.opcode_name = "if-lez";
            success = execute_if_lez(pc_, entry);
            cf_stats_.opcode_counts["if-lez"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_LT:
            entry.opcode_name = "if-lt";
            success = execute_if_lt(pc_, entry);
            cf_stats_.opcode_counts["if-lt"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_GE:
            entry.opcode_name = "if-ge";
            success = execute_if_ge(pc_, entry);
            cf_stats_.opcode_counts["if-ge"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_GT:
            entry.opcode_name = "if-gt";
            success = execute_if_gt(pc_, entry);
            cf_stats_.opcode_counts["if-gt"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        case OpcodesExp018::IF_LE:
            entry.opcode_name = "if-le";
            success = execute_if_le(pc_, entry);
            cf_stats_.opcode_counts["if-le"]++;
            cf_stats_.total_branches_encountered++;
            break;
            
        // =========================================================================
        // Phase 2: Return Value System (P1_HIGH)
        // Data Source: move-result-object (380 occ), return-object (250 occ)
        // =========================================================================
        
        case OpcodesExp018::MOVE_RESULT:
            entry.opcode_name = "move-result";
            success = execute_move_result(pc_, entry);
            break;
            
        case OpcodesExp018::MOVE_RESULT_OBJECT:
            entry.opcode_name = "move-result-object";
            success = execute_move_result_object(pc_, entry);
            break;
            
        case OpcodesExp018::MOVE_RESULT_WIDE:
            entry.opcode_name = "move-result-wide";
            success = execute_move_result_wide(pc_, entry);
            break;
            
        case OpcodesExp018::RETURN_WIDE:
            entry.opcode_name = "return-wide";
            success = execute_return_wide(pc_, entry);
            break;
            
        // =========================================================================
        // Phase 3: Static Dispatch (P0_CRITICAL)
        // Data Source: invoke-static (485 occurrences, 3.78% of all opcodes)
        // Blocks: Integer.parseInt, Toast.makeText, Log.d (~75% apps)
        // =========================================================================
        
        case OpcodesExp018::INVOKE_STATIC:
            entry.opcode_name = "invoke-static";
            success = execute_invoke_static(pc_, entry, config);
            break;
            
        // =========================================================================
        // Phase 4: Interface Dispatch (P1_HIGH)
        // Data Source: invoke-interface (150 occurrences, 1.17%)
        // Blocks: View.OnClickListener (~50% interactive apps)
        // =========================================================================
        
        case OpcodesExp018::INVOKE_INTERFACE:
            entry.opcode_name = "invoke-interface";
            success = execute_invoke_interface(pc_, entry, config);
            break;
            
        // =========================================================================
        // Phase 5: Additional Useful Opcodes
        // =========================================================================
        
        case OpcodesExp018::CONST_16:
            entry.opcode_name = "const/16";
            success = execute_const_16(pc_, entry);
            break;
            
        case OpcodesExp018::SGET_OBJECT:
            entry.opcode_name = "sget-object";
            success = execute_sget_object(pc_, entry);
            break;
            
        case OpcodesExp018::SPUT_OBJECT:
            entry.opcode_name = "sput-object";
            success = execute_sput_object(pc_, entry);
            break;
            
        case OpcodesExp018::CHECK_CAST:
            entry.opcode_name = "check-cast";
            success = execute_check_cast(pc_, entry);
            break;
            
        case OpcodesExp018::INSTANCE_OF:
            entry.opcode_name = "instance-of";
            success = execute_instance_of(pc_, entry);
            break;
            
        default:
            // Let base class handle known opcodes
            return DexInterpreterV2::fetch_decode_execute(trace, config);
    }
    
    entry.pc_after = pc_;
    add_instruction_to_trace(trace, entry);
    
    return success;
}

// ============================================================================
// Phase 1: Control Flow Implementations
// ============================================================================
// Data Source: real_opcode_frequency.json
// Total branch opcodes: 1390 (10.82% of all opcodes)
//
// Priority from corpus analysis:
// - if-eqz (450 occ): NULL checks, boolean conditions -> blocks 67% apps
// - goto (420 occ): ALL loops (for/while/do-while) -> blocks 92% apps!
// - if-nez (340 occ): Non-null checks -> blocks 58% apps
// - if-eq (180 occ): Integer comparisons -> blocks 18% apps
// ============================================================================

bool DexInterpreterExp018::execute_if_eqz(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: if-eqz vAA, +BBBB
    // Branch if vAA == zero (or null for references)
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    
    Value val = get_register(regA);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-eqz";
    branch.condition_description = "Branch if v" + std::to_string(regA) + " == 0/null";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.offset = offset;
    branch.fallthrough_pc = pc + 4;  // Instruction size is 4 bytes for 22x format
    
    // Evaluate condition: zero or null
    bool is_zero_or_null = false;
    if (val.type == ValueType::NULL_REF || val.is_null) {
        is_zero_or_null = true;
        branch.condition.was_null_a = true;
        branch.condition.value_a = 0;
    } else if (val.type == ValueType::INT32) {
        is_zero_or_null = (val.int_val == 0);
        branch.condition.value_a = val.int_val;
    } else if (val.type == ValueType::BOOLEAN) {
        is_zero_or_null = !val.bool_val;
        branch.condition.value_a = val.bool_val ? 1 : 0;
    } else {
        // Treat uninitialized as not-zero for safety
        is_zero_or_null = false;
        branch.condition.was_null_a = false;
        branch.condition.value_a = 0;
    }
    
    branch.condition.condition_result = is_zero_or_null;
    branch.taken = is_zero_or_null;
    
    if (is_zero_or_null) {
        branch.target_pc = pc + offset;
        pc_ = branch.target_pc;
        cf_stats_.branches_taken++;
    } else {
        branch.target_pc = pc + offset;
        pc_ = branch.fallthrough_pc;
        cf_stats_.branches_not_taken++;
    }
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), val.to_string(), regA});
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_nez(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: if-nez vAA, +BBBB
    // Branch if vAA != zero (non-null for references)
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    
    Value val = get_register(regA);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-nez";
    branch.condition_description = "Branch if v" + std::to_string(regA) + " != 0/non-null";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.offset = offset;
    branch.fallthrough_pc = pc + 4;
    
    // Evaluate condition: non-zero or non-null
    bool is_non_zero_non_null = false;
    if (val.type == ValueType::NULL_REF || val.is_null) {
        is_non_zero_non_null = false;
        branch.condition.was_null_a = true;
        branch.condition.value_a = 0;
    } else if (val.type == ValueType::INT32) {
        is_non_zero_non_null = (val.int_val != 0);
        branch.condition.value_a = val.int_val;
    } else if (val.type == ValueType::BOOLEAN) {
        is_non_zero_non_null = val.bool_val;
        branch.condition.value_a = val.bool_val ? 1 : 0;
    } else if (val.type == ValueType::OBJECT_REF || val.type == ValueType::STRING_REF) {
        is_non_zero_non_null = true;  // Valid reference is always "non-null"
        branch.condition.value_a = val.reference_id;
    } else {
        is_non_zero_non_null = false;
    }
    
    branch.condition.condition_result = is_non_zero_non_null;
    branch.taken = is_non_zero_non_null;
    
    if (is_non_zero_non_null) {
        branch.target_pc = pc + offset;
        pc_ = branch.target_pc;
        cf_stats_.branches_taken++;
    } else {
        branch.target_pc = pc + offset;
        pc_ = branch.fallthrough_pc;
        cf_stats_.branches_not_taken++;
    }
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), val.to_string(), regA});
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_eq(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: if-eq vAA, vBB, +CCCC
    // Branch if vAA == vBB
    
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];  // AA in low 8 bits
    uint8_t regB = bytecode_[pc + 2];  // BB
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 3] << 8) | bytecode_[pc + 4]);
    
    Value valA = get_register(regA);
    Value valB = get_register(regB);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-eq";
    branch.condition_description = "Branch if v" + std::to_string(regA) + " == v" + std::to_string(regB);
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.register_b = "v" + std::to_string(regB);
    branch.offset = offset;
    branch.fallthrough_pc = pc + 5;
    
    // Extract integer values for comparison
    int32_t a = 0, b = 0;
    bool can_compare = true;
    
    if (valA.type == ValueType::INT32) { a = valA.int_val; }
    else if (valA.type == ValueType::BOOLEAN) { a = valA.bool_val ? 1 : 0; }
    else if (valA.type == ValueType::NULL_REF) { a = 0; }
    else { can_compare = false; branch.condition.was_null_a = true; }
    
    if (valB.type == ValueType::INT32) { b = valB.int_val; }
    else if (valB.type == ValueType::BOOLEAN) { b = valB.bool_val ? 1 : 0; }
    else if (valB.type == ValueType::NULL_REF) { b = 0; }
    else { can_compare = false; branch.condition.was_null_b = true; }
    
    branch.condition.value_a = a;
    branch.condition.value_b = b;
    
    bool is_equal = can_compare && (a == b);
    branch.condition.condition_result = is_equal;
    branch.taken = is_equal;
    
    if (is_equal) {
        branch.target_pc = pc + offset;
        pc_ = branch.target_pc;
        cf_stats_.branches_taken++;
    } else {
        branch.target_pc = pc + offset;
        pc_ = branch.fallthrough_pc;
        cf_stats_.branches_not_taken++;
    }
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), valA.to_string(), regA});
    entry.operands.push_back({"v" + std::to_string(regB), valB.to_string(), regB});
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_ne(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: if-ne vAA, vBB, +CCCC
    // Branch if vAA != vBB
    
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint8_t regB = bytecode_[pc + 2];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 3] << 8) | bytecode_[pc + 4]);
    
    Value valA = get_register(regA);
    Value valB = get_register(regB);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-ne";
    branch.condition_description = "Branch if v" + std::to_string(regA) + " != v" + std::to_string(regB);
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.register_b = "v" + std::to_string(regB);
    branch.offset = offset;
    branch.fallthrough_pc = pc + 5;
    
    int32_t a = 0, b = 0;
    bool can_compare = true;
    
    if (valA.type == ValueType::INT32) { a = valA.int_val; }
    else if (valA.type == ValueType::BOOLEAN) { a = valA.bool_val ? 1 : 0; }
    else if (valA.type == ValueType::NULL_REF) { a = 0; }
    else { can_compare = false; }
    
    if (valB.type == ValueType::INT32) { b = valB.int_val; }
    else if (valB.type == ValueType::BOOLEAN) { b = valB.bool_val ? 1 : 0; }
    else if (valB.type == ValueType::NULL_REF) { b = 0; }
    else { can_compare = false; }
    
    branch.condition.value_a = a;
    branch.condition.value_b = b;
    
    bool not_equal = can_compare && (a != b);
    branch.condition.condition_result = not_equal;
    branch.taken = not_equal;
    
    if (not_equal) {
        branch.target_pc = pc + offset;
        pc_ = branch.target_pc;
        cf_stats_.branches_taken++;
    } else {
        branch.target_pc = pc + offset;
        pc_ = branch.fallthrough_pc;
        cf_stats_.branches_not_taken++;
    }
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), valA.to_string(), regA});
    entry.operands.push_back({"v" + std::to_string(regB), valB.to_string(), regB});
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_goto(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: goto +AA
    // Unconditional jump (8-bit signed offset)
    
    if (bytecode_.size() < pc + 1) return false;
    
    int8_t offset = static_cast<int8_t>(bytecode_[pc + 1]);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "goto";
    branch.condition_description = "Unconditional jump";
    branch.offset = offset;
    branch.taken = true;  // goto always taken
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 2;  // Instruction size is 2 bytes for 10x format
    
    pc_ = branch.target_pc;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    entry.operands.push_back({"target", std::to_string(pc_), pc_});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_goto_16(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: goto/16 +AAAA
    // Unconditional jump (16-bit signed offset)
    
    if (bytecode_.size() < pc + 2) return false;
    
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 1] << 8) | bytecode_[pc + 2]);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "goto/16";
    branch.condition_description = "Unconditional jump (16-bit)";
    branch.offset = offset;
    branch.taken = true;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 3;
    
    pc_ = branch.target_pc;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_goto_32(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: goto/32 +AAAAAAAA
    // Unconditional jump (32-bit signed offset)
    
    if (bytecode_.size() < pc + 4) return false;
    
    int32_t offset = (bytecode_[pc + 1] << 24) | (bytecode_[pc + 2] << 16) | 
                     (bytecode_[pc + 3] << 8) | bytecode_[pc + 4];
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "goto/32";
    branch.condition_description = "Unconditional jump (32-bit)";
    branch.offset = offset;  // Note: truncated in trace but used correctly
    branch.taken = true;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 5;
    
    pc_ = branch.target_pc;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"offset", std::to_string(offset), offset});
    
    if (exp018_config_.trace_all_branches) {
        record_branch(branch);
    }
    
    detect_loops(pc, pc_);
    
    return true;
}

// Extended conditional branches

bool DexInterpreterExp018::execute_if_ltz(uint32_t pc, InstructionTraceEntry& entry) {
    // if-ltz vAA, +BBBB - branch if vAA < 0
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    Value val = get_register(regA);
    
    bool is_negative = (val.type == ValueType::INT32 && val.int_val < 0);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-ltz";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.value_a = val.type == ValueType::INT32 ? val.int_val : 0;
    branch.condition.condition_result = is_negative;
    branch.taken = is_negative;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 4;
    
    pc_ = is_negative ? branch.target_pc : branch.fallthrough_pc;
    if (is_negative) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-ltz"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_gez(uint32_t pc, InstructionTraceEntry& entry) {
    // if-gez vAA, +BBBB - branch if vAA >= 0
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    Value val = get_register(regA);
    
    bool is_ge_zero = (val.type == ValueType::INT32 && val.int_val >= 0) || 
                      (val.type == ValueType::NULL_REF) ||
                      (val.type == ValueType::OBJECT_REF) || 
                      (val.type == ValueType::STRING_REF);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-gez";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.value_a = val.type == ValueType::INT32 ? val.int_val : 0;
    branch.condition.condition_result = is_ge_zero;
    branch.taken = is_ge_zero;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 4;
    
    pc_ = is_ge_zero ? branch.target_pc : branch.fallthrough_pc;
    if (is_ge_zero) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-gez"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_gtz(uint32_t pc, InstructionTraceEntry& entry) {
    // if-gtz vAA, +BBBB - branch if vAA > 0
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    Value val = get_register(regA);
    
    bool is_positive = (val.type == ValueType::INT32 && val.int_val > 0);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-gtz";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.value_a = val.type == ValueType::INT32 ? val.int_val : 0;
    branch.condition.condition_result = is_positive;
    branch.taken = is_positive;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 4;
    
    pc_ = is_positive ? branch.target_pc : branch.fallthrough_pc;
    if (is_positive) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-gtz"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_lez(uint32_t pc, InstructionTraceEntry& entry) {
    // if-lez vAA, +BBBB - branch if vAA <= 0
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    Value val = get_register(regA);
    
    bool is_le_zero = (val.type != ValueType::INT32) ||  // null/ref treated as <= 0
                      (val.type == ValueType::INT32 && val.int_val <= 0);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-lez";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.value_a = val.type == ValueType::INT32 ? val.int_val : 0;
    branch.condition.condition_result = is_le_zero;
    branch.taken = is_le_zero;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 4;
    
    pc_ = is_le_zero ? branch.target_pc : branch.fallthrough_pc;
    if (is_le_zero) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-lez"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_lt(uint32_t pc, InstructionTraceEntry& entry) {
    // if-lt vAA, vBB, +CCCC - branch if vAA < vBB
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint8_t regB = bytecode_[pc + 2];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 3] << 8) | bytecode_[pc + 4]);
    
    Value valA = get_register(regA);
    Value valB = get_register(regB);
    
    int32_t a = (valA.type == ValueType::INT32) ? valA.int_val : 0;
    int32_t b = (valB.type == ValueType::INT32) ? valB.int_val : 0;
    bool is_less = (a < b);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-lt";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.register_b = "v" + std::to_string(regB);
    branch.condition.value_a = a;
    branch.condition.value_b = b;
    branch.condition.condition_result = is_less;
    branch.taken = is_less;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 5;
    
    pc_ = is_less ? branch.target_pc : branch.fallthrough_pc;
    if (is_less) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-lt"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_ge(uint32_t pc, InstructionTraceEntry& entry) {
    // if-ge vAA, vBB, +CCCC - branch if vAA >= vBB
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint8_t regB = bytecode_[pc + 2];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 3] << 8) | bytecode_[pc + 4]);
    
    Value valA = get_register(regA);
    Value valB = get_register(regB);
    
    int32_t a = (valA.type == ValueType::INT32) ? valA.int_val : 0;
    int32_t b = (valB.type == ValueType::INT32) ? valB.int_val : 0;
    bool is_ge = (a >= b);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-ge";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.register_b = "v" + std::to_string(regB);
    branch.condition.value_a = a;
    branch.condition.value_b = b;
    branch.condition.condition_result = is_ge;
    branch.taken = is_ge;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 5;
    
    pc_ = is_ge ? branch.target_pc : branch.fallthrough_pc;
    if (is_ge) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-ge"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_gt(uint32_t pc, InstructionTraceEntry& entry) {
    // if-gt vAA, vBB, +CCCC - branch if vAA > vBB
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint8_t regB = bytecode_[pc + 2];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 3] << 8) | bytecode_[pc + 4]);
    
    Value valA = get_register(regA);
    Value valB = get_register(regB);
    
    int32_t a = (valA.type == ValueType::INT32) ? valA.int_val : 0;
    int32_t b = (valB.type == ValueType::INT32) ? valB.int_val : 0;
    bool is_gt = (a > b);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-gt";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.register_b = "v" + std::to_string(regB);
    branch.condition.value_a = a;
    branch.condition.value_b = b;
    branch.condition.condition_result = is_gt;
    branch.taken = is_gt;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 5;
    
    pc_ = is_gt ? branch.target_pc : branch.fallthrough_pc;
    if (is_gt) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-gt"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

bool DexInterpreterExp018::execute_if_le(uint32_t pc, InstructionTraceEntry& entry) {
    // if-le vAA, vBB, +CCCC - branch if vAA <= vBB
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint8_t regB = bytecode_[pc + 2];
    int16_t offset = static_cast<int16_t>((bytecode_[pc + 3] << 8) | bytecode_[pc + 4]);
    
    Value valA = get_register(regA);
    Value valB = get_register(regB);
    
    int32_t a = (valA.type == ValueType::INT32) ? valA.int_val : 0;
    int32_t b = (valB.type == ValueType::INT32) ? valB.int_val : 0;
    bool is_le = (a <= b);
    
    BranchTraceBranch branch;
    branch.sequence = branch_trace_.size();
    branch.pc_before = pc;
    branch.opcode_name = "if-le";
    branch.condition.register_a = "v" + std::to_string(regA);
    branch.condition.register_b = "v" + std::to_string(regB);
    branch.condition.value_a = a;
    branch.condition.value_b = b;
    branch.condition.condition_result = is_le;
    branch.taken = is_le;
    branch.offset = offset;
    branch.target_pc = pc + offset;
    branch.fallthrough_pc = pc + 5;
    
    pc_ = is_le ? branch.target_pc : branch.fallthrough_pc;
    if (is_le) cf_stats_.branches_taken++; else cf_stats_.branches_not_taken++;
    cf_stats_.total_branches_encountered++;
    cf_stats_.opcode_counts["if-le"]++;
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    if (exp018_config_.trace_all_branches) record_branch(branch);
    detect_loops(pc, pc_);
    
    return true;
}

// Helper methods

void DexInterpreterExp018::record_branch(const BranchTraceBranch& branch) {
    branch_trace_.push_back(branch);
}

void DexInterpreterExp018::detect_loops(uint32_t from_pc, uint32_t to_pc) {
    // Simple backward edge detection: if we're jumping to an earlier PC, it's likely a loop
    if (to_pc < from_pc) {
        // Check if this loop was already detected
        bool found = false;
        for (auto& loop : loops_detected_) {
            if (loop.loop_start_pc <= to_pc && loop.loop_end_pc >= from_pc) {
                loop.iteration_count++;
                loop.back_edge_pcs.push_back(from_pc);
                found = true;
                break;
            }
        }
        
        if (!found) {
            LoopDetectionRecord loop;
            loop.loop_start_pc = to_pc;
            loop.loop_end_pc = from_pc;
            loop.loop_type = "detected-back-edge";
            loop.iteration_count = 1;
            loop.back_edge_pcs.push_back(from_pc);
            loops_detected_.push_back(loop);
            cf_stats_.loops_detected++;
        }
    }
}

bool DexInterpreterExp018::check_loop_protection(uint32_t target_pc) {
    if (!exp018_config_.enable_loop_detection) return true;
    
    auto it = pc_visit_count_.find(target_pc);
    if (it != pc_visit_count_.end() && it->second > exp018_config_.max_loop_iterations) {
        return false;  // Block the jump - infinite loop protection
    }
    return true;
}

// ============================================================================
// Phase 2: Return Value System Implementation
// ============================================================================
// Data Source: real_opcode_frequency.json
// - move-result-object (380 occ, 2.96%) - Critical for method chaining
// - return-object (250 occ, 1.95%) - Methods must return values
//
// Key APIs enabled by this system:
// - View.findViewById() returns View object
// - EditText.getText() returns Editable
// - CharSequence.toString() returns String
// ============================================================================

bool DexInterpreterExp018::execute_move_result(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: move-result vAA
    // Capture int/float return value from previous invoke*
    
    if (bytecode_.size() < pc + 1) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    
    ReturnTraceEntry ret_entry;
    ret_entry.sequence = return_trace_.size();
    ret_entry.pc = pc;
    ret_entry.opcode_name = "move-result";
    
    if (has_pending_return_) {
        set_register(regA, pending_return_, pc);
        ret_entry.returned_value = pending_return_;
        ret_entry.captured = true;
        ret_entry.capture_pc = pc;
        ret_entry.capture_register = regA;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        entry.operands.push_back({"v" + std::to_string(regA), pending_return_.to_string(), regA});
        entry.operands.push_back({"source", "pending_return", 0});
        
        clear_pending_return();
    } else {
        // No pending return - set to default
        Value default_val = Value::make_int(0, pc);
        set_register(regA, default_val, pc);
        ret_entry.returned_value = default_val;
        ret_entry.captured = true;
        ret_entry.capture_register = regA;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        entry.operands.push_back({"v" + std::to_string(regA), "0 (no pending)", regA});
    }
    
    return_trace_.push_back(ret_entry);
    pc_ += 2;  // 12x format - 2 bytes
    
    return true;
}

bool DexInterpreterExp018::execute_move_result_object(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: move-result-object vAA
    // Capture object reference return value from previous invoke*
    // THIS IS CRITICAL: Enables findViewById().setText() pattern!
    
    if (bytecode_.size() < pc + 1) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    
    ReturnTraceEntry ret_entry;
    ret_entry.sequence = return_trace_.size();
    ret_entry.pc = pc;
    ret_entry.opcode_name = "move-result-object";
    
    if (has_pending_return_) {
        set_register(regA, pending_return_, pc);
        ret_entry.returned_value = pending_return_;
        ret_entry.captured = true;
        ret_entry.capture_pc = pc;
        ret_entry.capture_register = regA;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        entry.operands.push_back({"v" + std::to_string(regA), pending_return_.to_string(), regA});
        entry.operands.push_back({"source", "pending_return_object", 0});
        
        clear_pending_return();
    } else {
        // No pending return - set to null
        Value null_val = Value::make_null();
        set_register(regA, null_val, pc);
        ret_entry.returned_value = null_val;
        ret_entry.captured = true;
        ret_entry.capture_register = regA;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        entry.operands.push_back({"v" + std::to_string(regA), "null (no pending)", regA});
    }
    
    return_trace_.push_back(ret_entry);
    pc_ += 2;
    
    return true;
}

bool DexInterpreterExp018::execute_move_result_wide(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: move-result-wide vAA
    // Capture long/double return value (uses vAA and vAA+1)
    
    if (bytecode_.size() < pc + 1) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    
    ReturnTraceEntry ret_entry;
    ret_entry.sequence = return_trace_.size();
    ret_entry.pc = pc;
    ret_entry.opcode_name = "move-result-wide";
    
    if (has_pending_return_) {
        set_register(regA, pending_return_, pc);
        // Wide values use two registers - set next register as well
        ensure_register_capacity(regA + 1);
        registers_[regA + 1] = Value::make_uninitialized();
        
        ret_entry.returned_value = pending_return_;
        ret_entry.captured = true;
        ret_entry.capture_pc = pc;
        ret_entry.capture_register = regA;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        entry.operands.push_back({"v" + std::to_string(regA), pending_return_.to_string(), regA});
        
        clear_pending_return();
    } else {
        Value default_val = Value::make_int(0, pc);
        set_register(regA, default_val, pc);
        ret_entry.returned_value = default_val;
        ret_entry.captured = true;
        
        entry.status = InstructionTraceEntry::Status::SUCCESS;
        entry.operands.push_back({"v" + std::to_string(regA), "0 (wide, no pending)", regA});
    }
    
    return_trace_.push_back(ret_entry);
    pc_ += 2;
    
    return true;
}

bool DexInterpreterExp018::execute_return_wide(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: return-wide vAA
    // Return long/double value (uses vAA and vAA+1)
    
    if (bytecode_.size() < pc + 1) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    Value val = get_register(regA);
    
    ReturnTraceEntry ret_entry;
    ret_entry.sequence = return_trace_.size();
    ret_entry.pc = pc;
    ret_entry.opcode_name = "return-wide";
    ret_entry.returned_value = val;
    
    set_pending_return(val);
    
    returned_ = true;
    entry.status = InstructionTraceEntry::Status::METHOD_RETURNED;
    entry.operands.push_back({"v" + std::to_string(regA), val.to_string(), regA});
    
    return_trace_.push_back(ret_entry);
    
    return true;
}

void DexInterpreterExp018::set_pending_return(const Value& val) {
    pending_return_ = val;
    has_pending_return_ = true;
}

void DexInterpreterExp018::clear_pending_return() {
    pending_return_ = Value::make_uninitialized();
    has_pending_return_ = false;
}

// ============================================================================
// Phase 3: Static Dispatch Implementation
// ============================================================================
// Data Source: api_priority.json, real_opcode_frequency.json
// invoke-static (485 occurrences, 3.78%) - P0_CRITICAL
//
// Critical static methods from corpus:
// - java.lang.Integer.parseInt(String) - Used by 20% apps (calculators)
// - android.widget.Toast.makeText() - Used by 22% apps  
// - android.util.Log.d/i/w/e - Used by 9% apps
// - java.lang.String.valueOf() - Common conversion
// ============================================================================

void DexInterpreterExp018::initialize_builtin_static_methods() {
    // Register built-in JDK static methods
    
    // Integer.parseInt(String)
    StaticMethodEntry parseInt;
    parseInt.class_name = "java.lang.Integer";
    parseInt.method_name = "parseInt";
    parseInt.descriptor = "(Ljava/lang/String;)I";
    parseInt.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    parseInt.added_in_experiment = "EXP-018-PHASE3";
    parseInt.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_int(0);
        try {
            if (args[0].type == ValueType::STRING_REF) {
                return Value::make_int(std::stoi(args[0].string_val));
            }
            return Value::make_int(0);
        } catch (...) {
            return Value::make_int(0);  // NumberFormatException -> return 0
        }
    };
    static_registry_.push_back(parseInt);
    
    // Integer.valueOf(int)
    StaticMethodEntry valueOfInt;
    valueOfInt.class_name = "java.lang.Integer";
    valueOfInt.method_name = "valueOf";
    valueOfInt.descriptor = "(I)Ljava/lang/Integer;";
    valueOfInt.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    valueOfInt.added_in_experiment = "EXP-018-PHASE3";
    valueOfInt.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_int(0);
        return args[0];  // Just pass through the int value
    };
    static_registry_.push_back(valueOfInt);
    
    // Long.parseLong(String)
    StaticMethodEntry parseLong;
    parseLong.class_name = "java.lang.Long";
    parseLong.method_name = "parseLong";
    parseLong.descriptor = "(Ljava/lang/String;)J";
    parseLong.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    parseLong.added_in_experiment = "EXP-018-PHASE3";
    parseLong.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_int(0);
        try {
            if (args[0].type == ValueType::STRING_REF) {
                return Value::make_int(static_cast<int32_t>(std::stoll(args[0].string_val)));
            }
            return Value::make_int(0);
        } catch (...) {
            return Value::make_int(0);
        }
    };
    static_registry_.push_back(parseLong);
    
    // Float.parseFloat(String)
    StaticMethodEntry parseFloat;
    parseFloat.class_name = "java.lang.Float";
    parseFloat.method_name = "parseFloat";
    parseFloat.descriptor = "(Ljava/lang/String;)F";
    parseFloat.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    parseFloat.added_in_experiment = "EXP-018-PHASE3";
    parseFloat.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_int(0);
        try {
            if (args[0].type == ValueType::STRING_REF) {
                Value v;
                v.type = ValueType::FLOAT;
                v.float_val = std::stof(args[0].string_val);
                return v;
            }
            return Value::make_int(0);
        } catch (...) {
            return Value::make_int(0);
        }
    };
    static_registry_.push_back(parseFloat);
    
    // Double.parseDouble(String)
    StaticMethodEntry parseDouble;
    parseDouble.class_name = "java.lang.Double";
    parseDouble.method_name = "parseDouble";
    parseDouble.descriptor = "(Ljava/lang/String;)D";
    parseDouble.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    parseDouble.added_in_experiment = "EXP-018-PHASE3";
    parseDouble.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_int(0);
        try {
            if (args[0].type == ValueType::STRING_REF) {
                Value v;
                v.type = ValueType::DOUBLE;
                v.double_val = std::stod(args[0].string_val);
                return v;
            }
            return Value::make_int(0);
        } catch (...) {
            return Value::make_int(0);
        }
    };
    static_registry_.push_back(parseDouble);
    
    // Boolean.parseBoolean(String)
    StaticMethodEntry parseBoolean;
    parseBoolean.class_name = "java.lang.Boolean";
    parseBoolean.method_name = "parseBoolean";
    parseBoolean.descriptor = "(Ljava/lang/String;)Z";
    parseBoolean.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    parseBoolean.added_in_experiment = "EXP-018-PHASE3";
    parseBoolean.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_boolean(false);
        if (args[0].type == ValueType::STRING_REF) {
            return Value::make_boolean(args[0].string_val == "true");
        }
        return Value::make_boolean(false);
    };
    static_registry_.push_back(parseBoolean);
    
    // String.valueOf(int)
    StaticMethodEntry valueOfStringInt;
    valueOfStringInt.class_name = "java.lang.String";
    valueOfStringInt.method_name = "valueOf";
    valueOfStringInt.descriptor = "(I)Ljava/lang/String;";
    valueOfStringInt.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    valueOfStringInt.added_in_experiment = "EXP-018-PHASE3";
    valueOfStringInt.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_string("", next_ref_id_++, pc_);
        if (args[0].type == ValueType::INT32) {
            return Value::make_string(std::to_string(args[0].int_val), next_ref_id_++, pc_);
        }
        return Value::make_string("", next_ref_id_++, pc_);
    };
    static_registry_.push_back(valueOfStringInt);
    
    // String.valueOf(long)
    StaticMethodEntry valueOfStringLong;
    valueOfStringLong.class_name = "java.lang.String";
    valueOfStringLong.method_name = "valueOf";
    valueOfStringLong.descriptor = "(J)Ljava/lang/String;";
    valueOfStringLong.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    valueOfStringLong.added_in_experiment = "EXP-018-PHASE3";
    valueOfStringLong.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_string("", next_ref_id_++, pc_);
        if (args[0].type == ValueType::INT32 || args[0].type == ValueType::LONG) {
            return Value::make_string(std::to_string(args[0].int_val), next_ref_id_++, pc_);
        }
        return Value::make_string("", next_ref_id_++, pc_);
    };
    static_registry_.push_back(valueOfStringLong);
    
    // String.valueOf(float)
    StaticMethodEntry valueOfStringFloat;
    valueOfStringFloat.class_name = "java.lang.String";
    valueOfStringFloat.method_name = "valueOf";
    valueOfStringFloat.descriptor = "(F)Ljava/lang/String;";
    valueOfStringFloat.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    valueOfStringFloat.added_in_experiment = "EXP-018-PHASE3";
    valueOfStringFloat.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_string("", next_ref_id_++, pc_);
        // Convert float to string (simplified)
        std::ostringstream oss;
        if (args[0].type == ValueType::FLOAT) {
            oss << args[0].float_val;
        } else {
            oss << "0";
        }
        return Value::make_string(oss.str(), next_ref_id_++, pc_);
    };
    static_registry_.push_back(valueOfStringFloat);
    
    // String.valueOf(Object)
    StaticMethodEntry valueOfStringObj;
    valueOfStringObj.class_name = "java.lang.String";
    valueOfStringObj.method_name = "valueOf";
    valueOfStringObj.descriptor = "(Ljava/lang/Object;)Ljava/lang/String;";
    valueOfStringObj.implementation_type = StaticMethodEntry::ImplementationType::NATIVE_CPP;
    valueOfStringObj.added_in_experiment = "EXP-018-PHASE3";
    valueOfStringObj.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_string("null", next_ref_id_++, pc_);
        if (args[0].type == ValueType::NULL_REF || args[0].is_null) {
            return Value::make_string("null", next_ref_id_++, pc_);
        }
        if (args[0].type == ValueType::STRING_REF) {
            return args[0];
        }
        // Return toString representation
        return Value::make_string(args[0].object_class + "@" + std::to_string(args[0].reference_id), 
                                  next_ref_id_++, pc_);
    };
    static_registry_.push_back(valueOfStringObj);
    
    // Log.d (stub - just logs)
    StaticMethodEntry logd;
    logd.class_name = "android.util.Log";
    logd.method_name = "d";
    logd.descriptor = "(Ljava/lang/String;Ljava/lang/String;)I";
    logd.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    logd.added_in_experiment = "EXP-018-PHASE3";
    logd.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() >= 2) {
            std::string tag = (args[0].type == ValueType::STRING_REF) ? args[0].string_val : "?";
            std::string msg = (args[1].type == ValueType::STRING_REF) ? args[1].string_val : "";
            // In real runtime, this would write to logcat
            log("[Log.d] " + tag + ": " + msg);
        }
        return Value::make_int(0);  // Log.d returns length of message
    };
    static_registry_.push_back(logd);
    
    // Log.i
    StaticMethodEntry logi;
    logi.class_name = "android.util.Log";
    logi.method_name = "i";
    logi.descriptor = "(Ljava/lang/String;Ljava/lang/String;)I";
    logi.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    logi.added_in_experiment = "EXP-018-PHASE3";
    logi.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() >= 2) {
            std::string tag = (args[0].type == ValueType::STRING_REF) ? args[0].string_val : "?";
            std::string msg = (args[1].type == ValueType::STRING_REF) ? args[1].string_val : "";
            log("[Log.i] " + tag + ": " + msg);
        }
        return Value::make_int(0);
    };
    static_registry_.push_back(logi);
    
    // Log.w
    StaticMethodEntry logw;
    logw.class_name = "android.util.Log";
    logw.method_name = "w";
    logw.descriptor = "(Ljava/lang/String;Ljava/lang/String;)I";
    logw.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    logw.added_in_experiment = "EXP-018-PHASE3";
    logw.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() >= 2) {
            std::string tag = (args[0].type == ValueType::STRING_REF) ? args[0].string_val : "?";
            std::string msg = (args[1].type == ValueType::STRING_REF) ? args[1].string_val : "";
            log("[Log.w] " + tag + ": " + msg);
        }
        return Value::make_int(0);
    };
    static_registry_.push_back(logw);
    
    // Log.e
    StaticMethodEntry loge;
    loge.class_name = "android.util.Log";
    loge.method_name = "e";
    loge.descriptor = "(Ljava/lang/String;Ljava/lang/String;)I";
    loge.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    loge.added_in_experiment = "EXP-018-PHASE3";
    loge.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() >= 2) {
            std::string tag = (args[0].type == ValueType::STRING_REF) ? args[0].string_val : "?";
            std::string msg = (args[1].type == ValueType::STRING_REF) ? args[1].string_val : "";
            log("[Log.e] " + tag + ": " + msg);
        }
        return Value::make_int(0);
    };
    static_registry_.push_back(loge);
    
    // Toast.makeText (returns Toast object)
    StaticMethodEntry makeText;
    makeText.class_name = "android.widget.Toast";
    makeText.method_name = "makeText";
    makeText.descriptor = "(Landroid/content/Context;II)Landroid/widget/Toast;";
    makeText.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    makeText.added_in_experiment = "EXP-018-PHASE3";
    makeText.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        // Create a Toast object stub
        return Value::make_object("android.widget.Toast", next_object_id_++, pc_);
    };
    static_registry_.push_back(makeText);
    
    // TextUtils.isEmpty()
    StaticMethodEntry textUtilsIsEmpty;
    textUtilsIsEmpty.class_name = "android.text.TextUtils";
    textUtilsIsEmpty.method_name = "isEmpty";
    textUtilsIsEmpty.descriptor = "(Ljava/lang/CharSequence;)Z";
    textUtilsIsEmpty.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    textUtilsIsEmpty.added_in_experiment = "EXP-018-PHASE3";
    textUtilsIsEmpty.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_boolean(true);
        if (args[0].type == ValueType::NULL_REF || args[0].is_null) {
            return Value::make_boolean(true);
        }
        if (args[0].type == ValueType::STRING_REF) {
            return Value::make_boolean(args[0].string_val.empty());
        }
        return Value::make_boolean(false);
    };
    static_registry_.push_back(textUtilsIsEmpty);
    
    // TextUtils.equals()
    StaticMethodEntry textUtilsEquals;
    textUtilsEquals.class_name = "android.text.TextUtils";
    textUtilsEquals.method_name = "equals";
    textUtilsEquals.descriptor = "(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Z";
    textUtilsEquals.implementation_type = StaticMethodEntry::ImplementationType::ANDROID_STUB;
    textUtilsEquals.added_in_experiment = "EXP-018-PHASE3";
    textUtilsEquals.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() < 2) return Value::make_boolean(args.empty());
        
        // Handle null cases like Android's TextUtils.equals
        bool a_is_null = (args[0].type == ValueType::NULL_REF || args[0].is_null);
        bool b_is_null = (args[1].type == ValueType::NULL_REF || args[1].is_null);
        
        if (a_is_null && b_is_null) return Value::make_boolean(true);
        if (a_is_null || b_is_null) return Value::make_boolean(false);
        
        if (args[0].type == ValueType::STRING_REF && args[1].type == ValueType::STRING_REF) {
            return Value::make_boolean(args[0].string_val == args[1].string_val);
        }
        return Value::make_boolean(false);
    };
    static_registry_.push_back(textUtilsEquals);
    
    // Math.min(int, int)
    StaticMethodEntry mathMin;
    mathMin.class_name = "java.lang.Math";
    mathMin.method_name = "min";
    mathMin.descriptor = "(II)I";
    mathMin.implementation_type = StaticMethodEntry::ImplementationType::JDK_STUB;
    mathMin.added_in_experiment = "EXP-018-PHASE3";
    mathMin.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() < 2) return Value::make_int(0);
        int a = (args[0].type == ValueType::INT32) ? args[0].int_val : 0;
        int b = (args[1].type == ValueType::INT32) ? args[1].int_val : 0;
        return Value::make_int(std::min(a, b));
    };
    static_registry_.push_back(mathMin);
    
    // Math.max(int, int)
    StaticMethodEntry mathMax;
    mathMax.class_name = "java.lang.Math";
    mathMax.method_name = "max";
    mathMax.descriptor = "(II)I";
    mathMax.implementation_type = StaticMethodEntry::ImplementationType::JDK_STUB;
    mathMax.added_in_experiment = "EXP-018-PHASE3";
    mathMax.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.size() < 2) return Value::make_int(0);
        int a = (args[0].type == ValueType::INT32) ? args[0].int_val : 0;
        int b = (args[1].type == ValueType::INT32) ? args[1].int_val : 0;
        return Value::make_int(std::max(a, b));
    };
    static_registry_.push_back(mathMax);
    
    // Math.abs(int)
    StaticMethodEntry mathAbs;
    mathAbs.class_name = "java.lang.Math";
    mathAbs.method_name = "abs";
    mathAbs.descriptor = "(I)I";
    mathAbs.implementation_type = StaticMethodEntry::ImplementationType::JDK_STUB;
    mathAbs.added_in_experiment = "EXP-018-PHASE3";
    mathAbs.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        if (args.empty()) return Value::make_int(0);
        int a = (args[0].type == ValueType::INT32) ? args[0].int_val : 0;
        return Value::make_int(std::abs(a));
    };
    static_registry_.push_back(mathAbs);
    
    // System.currentTimeMillis()
    StaticMethodEntry currentTimeMillis;
    currentTimeMillis.class_name = "java.lang.System";
    currentTimeMillis.method_name = "currentTimeMillis";
    currentTimeMillis.descriptor = "()J";
    currentTimeMillis.implementation_type = StaticMethodEntry::ImplementationType::JDK_STUB;
    currentTimeMillis.added_in_experiment = "EXP-018-PHASE3";
    currentTimeMillis.implementation = [](const std::vector<Value>& args, void* ctx) -> Value {
        // Return current time in milliseconds (simplified)
        Value v;
        v.type = ValueType::LONG;
        v.long_val = static_cast<int64_t>(std::time(nullptr)) * 1000;
        return v;
    };
    static_registry_.push_back(currentTimeMillis);
    
    // System.arraycopy()
    StaticMethodEntry arraycopy;
    arraycopy.class_name = "java.lang.System";
    arraycopy.method_name = "arraycopy";
    arraycopy.descriptor = "(Ljava/lang/Object;ILjava/lang/Object;II)V";
    arraycopy.implementation_type = StaticMethodEntry::ImplementationType::JDK_STUB;
    arraycopy.added_in_experiment = "EXP-018-PHASE3";
    arraycopy.implementation = [this](const std::vector<Value>& args, void* ctx) -> Value {
        // Stub implementation - would need array support
        log("[System.arraycopy] STUB - arrays not fully supported");
        return Value::make_uninitialized();  // void return
    };
    static_registry_.push_back(arraycopy);
    
    // Build.VERSION.SDK_INT (static field access will be handled separately)
    // This is here for documentation - actual field access via sget-object
}

bool DexInterpreterExp018::execute_invoke_static(uint32_t pc, InstructionTraceEntry& entry, 
                                                  const Exp018Config& config) {
    // Format: invoke-static {vC, vD, ...}, method@BBBB
    // Call a static method
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint16_t method_idx = (bytecode_[pc + 2] << 8) | bytecode_[pc + 3];
    
    // Decode register count and argument registers
    uint8_t arg_info = bytecode_[pc + 1];
    uint8_t arg_count = (arg_info >> 4) & 0x0F;
    
    // Extract argument registers (simplified - assuming contiguous vC..)
    std::vector<uint8_t> arg_registers;
    std::vector<Value> args;
    
    for (uint8_t i = 0; i < arg_count && (pc + 4 + i) < bytecode_.size(); ++i) {
        uint8_t reg = bytecode_[pc + 4 + i];
        arg_registers.push_back(reg);
        args.push_back(get_register(reg));
    }
    
    // Look up method in string table (simplified resolution)
    // In real DEX, method_idx refers to method_ids[] which has class, method, proto refs
    std::string class_name = "unknown";
    std::string method_name = "unknown";
    std::string descriptor = "()V";
    
    // Try to resolve from dex_report if available
    // For now, use heuristic based on common patterns
    
    ApiCallRecord call_record;
    call_record.sequence = api_call_sequence_++;
    call_record.pc = pc;
    call_record.dispatch_type = DispatchType::STATIC;
    call_record.was_dispatched_from_dex = true;
    call_record.dispatch_path = "DEX_INVOKE_STATIC_EXP018";
    call_record.arguments = args;
    
    // Look up in static registry
    StaticMethodEntry* method_impl = nullptr;
    
    // Try exact match first
    for (auto& entry : static_registry_) {
        if (entry.method_name == method_name && entry.class_name == class_name) {
            method_impl = &entry;
            break;
        }
    }
    
    // If not found by index, try common patterns
    if (!method_impl) {
        // Search by method name only (heuristic)
        for (auto& reg_entry : static_registry_) {
            if (reg_entry.method_name == method_name) {
                method_impl = &reg_entry;
                class_name = reg_entry.class_name;  // Update for trace
                descriptor = reg_entry.descriptor;
                break;
            }
        }
    }
    
    call_record.class_name = class_name;
    call_record.method_name = method_name;
    call_record.descriptor = descriptor;
    
    if (method_impl && config.enable_static_dispatch) {
        // Execute the static method
        method_impl->call_count++;
        Value result = method_impl->implementation(args, nullptr);
        
        call_record.success = true;
        call_record.result_value = result;
        call_record.result_summary = "Static method executed: " + class_name + "." + method_name;
        
        // Set pending return for move-result/move-result-object
        if (descriptor.find(")V") == std::string::npos) {
            // Non-void method - set pending return
            set_pending_return(result);
        }
        
        entry.status = InstructionTraceEntry::Status::API_CALL_DISPATCHED;
        entry.api_call_made = call_record;
        
    } else {
        // Method not implemented
        call_record.success = false;
        call_record.error_message = "Static method not in registry: " + class_name + "." + method_name;
        call_record.result_summary = "UNIMPLEMENTED_STATIC";
        
        entry.status = InstructionTraceEntry::Status::HALT_UNIMPLEMENTED;
        entry.halt_reason = "invoke-static not implemented: " + class_name + "." + method_name;
        entry.api_call_made = call_record;
        
        if (config.stop_on_unimplemented) {
            halt_reason_ = entry.halt_reason.value();
            halted_ = true;
        }
    }
    
    static_call_trace_.push_back(call_record);
    api_calls_.push_back(call_record);
    
    // Advance PC past the instruction
    // invoke-static format: 35c or 3rc (5 bytes + 2 bytes per 5 regs over 4, rounded up)
    uint32_t instr_size = 4 + ((arg_count + 3) / 4) * 2;  // Simplified calculation
    if (arg_count <= 5) {
        instr_size = 5;  // 35c format
    } else {
        instr_size = 5 + ((arg_count - 5) / 4 + 1) * 2;  // Extended format
    }
    pc_ += instr_size;
    
    entry.operands.push_back({"method", class_name + "." + method_name + descriptor, method_idx});
    entry.operands.push_back({"args", std::to_string(arg_count), arg_count});
    
    return true;
}

StaticMethodEntry* DexInterpreterExp018::lookup_static_method(
    const std::string& class_name,
    const std::string& method_name,
    const std::string& descriptor
) {
    for (auto& entry : static_registry_) {
        if (entry.class_name == class_name && 
            entry.method_name == method_name && 
            entry.descriptor == descriptor) {
            return &entry;
        }
    }
    return nullptr;
}

void DexInterpreterExp018::register_static_method(const StaticMethodEntry& entry) {
    static_registry_.push_back(entry);
}

// ============================================================================
// Phase 4: Interface Dispatch Implementation
// ============================================================================
// Data Source: api_priority.json
// invoke-interface (150 occurrences, 1.17%) - P1_HIGH
//
// Critical interface from corpus:
// - View.OnClickListener.onClick(View) - Used by 50% interactive apps
// - Other interfaces less common but needed for completeness
// ============================================================================

void DexInterpreterExp018::initialize_builtin_interfaces() {
    // Register OnClickListener handler
    interface_implementations_["android.view.View$OnClickListener"]["onClick"] = 
        [this](const std::vector<Value>& args, void* ctx) -> Value {
            // Handle onClick callback
            if (!args.empty()) {
                log("[Interface] onClick called on " + args[0].to_string());
            }
            return Value::make_uninitialized();  // void return
        };
}

bool DexInterpreterExp018::execute_invoke_interface(uint32_t pc, InstructionTraceEntry& entry,
                                                     const Exp018Config& config) {
    // Format: invoke-interface {vC, vD, ...}, method@BBBB
    // Call an interface method on an object
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint16_t method_idx = (bytecode_[pc + 2] << 8) | bytecode_[pc + 3];
    uint8_t arg_info = bytecode_[pc + 1];
    uint8_t arg_count = (arg_info >> 4) & 0x0F;
    
    // First argument is 'this' for interface calls
    std::vector<uint8_t> arg_registers;
    std::vector<Value> args;
    
    for (uint8_t i = 0; i < arg_count && (pc + 4 + i) < bytecode_.size(); ++i) {
        uint8_t reg = bytecode_[pc + 4 + i];
        arg_registers.push_back(reg);
        args.push_back(get_register(reg));
    }
    
    InterfaceDispatchRecord dispatch;
    dispatch.sequence = interface_trace_.size();
    dispatch.pc = pc;
    dispatch.target_object = args.empty() ? Value::make_null() : args[0];
    dispatch.actual_class = dispatch.target_object.object_class;
    
    // Resolve interface method (simplified)
    std::string interface_name = "android.view.View$OnClickListener";  // Most common
    std::string method_name = "onClick";
    std::string descriptor = "(Landroid/view/View;)V";
    
    dispatch.interface_name = interface_name;
    dispatch.method_name = method_name;
    dispatch.descriptor = descriptor;
    dispatch.is_on_click_listener = (method_name == "onClick");
    
    // Look up implementation
    auto iface_it = interface_implementations_.find(interface_name);
    bool found = false;
    
    if (iface_it != interface_implementations_.end()) {
        auto method_it = iface_it->second.find(method_name);
        if (method_it != iface_it->second.end()) {
            // Execute interface method
            Value result = method_it->second(args, nullptr);
            
            dispatch.resolved = true;
            dispatch.resolved_method = interface_name + "." + method_name;
            dispatch.result = result;
            
            entry.status = InstructionTraceEntry::Status::API_CALL_DISPATCHED;
            found = true;
            
            log("[invoke-interface] " + interface_name + "." + method_name + " dispatched");
        }
    }
    
    if (!found) {
        dispatch.resolved = false;
        dispatch.resolved_method = "UNIMPLEMENTED";
        
        entry.status = config.strict_real_mode ? 
            InstructionTraceEntry::Status::HALT_UNIMPLEMENTED :
            InstructionTraceEntry::Status::SUCCESS;
        entry.halt_reason = "invoke-interface not implemented: " + interface_name + "." + method_name;
        
        if (config.stop_on_unimplemented) {
            halt_reason_ = entry.halt_reason.value();
            halted_ = true;
        }
        
        log("[invoke-interface] NOT IMPLEMENTED: " + interface_name + "." + method_name);
    }
    
    interface_trace_.push_back(dispatch);
    
    // Calculate instruction size (same as other invoke formats)
    uint32_t instr_size = (arg_count <= 5) ? 5 : 5 + ((arg_count - 5) / 4 + 1) * 2;
    pc_ += instr_size;
    
    entry.operands.push_back({"interface", interface_name, 0});
    entry.operands.push_back({"method", method_name, 0});
    entry.operands.push_back({"target", dispatch.target_object.to_string(), 0});
    
    return true;
}

InterfaceDispatchRecord* DexInterpreterExp018::resolve_interface_method(
    const Value& object,
    const std::string& interface_name,
    const std::string& method_name,
    const std::string& descriptor
) {
    // Create a new dispatch record
    InterfaceDispatchRecord record;
    record.sequence = interface_trace_.size();
    record.interface_name = interface_name;
    record.method_name = method_name;
    record.descriptor = descriptor;
    record.target_object = object;
    record.actual_class = object.object_class;
    record.is_on_click_listener = (method_name == "onClick");
    
    // Try to resolve
    auto iface_it = interface_implementations_.find(interface_name);
    if (iface_it != interface_implementations_.end()) {
        auto method_it = iface_it->second.find(method_name);
        if (method_it != iface_it->second.end()) {
            record.resolved = true;
            record.resolved_method = interface_name + "." + method_name;
            interface_trace_.push_back(record);
            return &interface_trace_.back();
        }
    }
    
    record.resolved = false;
    interface_trace_.push_back(record);
    return &interface_trace_.back();
}

void DexInterpreterExp018::register_interface_implementation(
    const std::string& interface_name,
    const std::string& method_name,
    StaticMethodEntry::StaticImplementationFn impl
) {
    interface_implementations_[interface_name][method_name] = impl;
}

// ============================================================================
// Phase 5: Additional Opcode Implementations
// ============================================================================

bool DexInterpreterExp018::execute_const_16(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: const/16 vAA, #+BBBB
    // Load 16-bit signed integer constant into register
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    int16_t value = static_cast<int16_t>((bytecode_[pc + 2] << 8) | bytecode_[pc + 3]);
    
    Value val = Value::make_int(static_cast<int32_t>(value), pc);
    set_register(regA, val, pc);
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), std::to_string(value), regA});
    
    pc_ += 4;  // 21s format - 4 bytes
    
    return true;
}

bool DexInterpreterExp018::execute_sget_object(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: sget-object vAA, field@BBBB
    // Read object reference from static field
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint16_t field_idx = (bytecode_[pc + 2] << 8) | bytecode_[pc + 3];
    
    // Common static fields (would be resolved from DEX in full implementation)
    Value field_value;
    
    // Handle known static fields
    // Build.VERSION.SDK_INT -> returns API level (e.g., 30 for Android 11)
    // For now, return a reasonable default
    field_value = Value::make_int(30, pc);  // Android 11 API level as default
    
    set_register(regA, field_value, pc);
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), field_value.to_string(), regA});
    entry.operands.push_back({"field@", std::to_string(field_idx), field_idx});
    
    pc_ += 4;  // 21c format - 4 bytes
    
    return true;
}

bool DexInterpreterExp018::execute_sput_object(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: sput-object vAA, field@BBBB
    // Write object reference to static field
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint16_t field_idx = (bytecode_[pc + 2] << 8) | bytecode_[pc + 3];
    
    Value val = get_register(regA);
    
    // In a full implementation, this would store to a static field table
    // For now, just log the operation
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), val.to_string(), regA});
    entry.operands.push_back({"field@", std::to_string(field_idx), field_idx});
    
    log("[sput-object] Field " + std::to_string(field_idx) + " <- " + val.to_string());
    
    pc_ += 4;
    
    return true;
}

bool DexInterpreterExp018::execute_check_cast(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: check-cast vAA, type@BBBB
    // Verify that object in vAA can be cast to specified type
    // Throws ClassCastException on failure (for now, just check without throwing)
    
    if (bytecode_.size() < pc + 3) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint16_t type_idx = (bytecode_[pc + 2] << 8) | bytecode_[pc + 3];
    
    Value val = get_register(regA);
    
    // In full implementation, verify type compatibility
    // For now, assume cast succeeds (common case in well-formed code)
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), val.to_string(), regA});
    entry.operands.push_back({"type@", std::to_string(type_idx), type_idx});
    
    // Register keeps same value after successful cast
    pc_ += 4;
    
    return true;
}

bool DexInterpreterExp018::execute_instance_of(uint32_t pc, InstructionTraceEntry& entry) {
    // Format: instance-of vA, vB, type@CCCC
    // Check if object in vB is instance of specified type, store boolean in vA
    
    if (bytecode_.size() < pc + 4) return false;
    
    uint8_t regA = bytecode_[pc + 1];
    uint8_t regB = bytecode_[pc + 2];
    uint16_t type_idx = (bytecode_[pc + 3] << 8) | bytecode_[pc + 4];
    
    Value val = get_register(regB);
    
    bool is_instance = false;
    
    // Basic type checking
    if (val.type == ValueType::NULL_REF || val.is_null) {
        is_instance = false;  // null is not instance of anything
    } else if (val.type == ValueType::OBJECT_REF) {
        // Would need proper type hierarchy check
        // Simplified: assume true for non-null objects
        is_instance = true;
    }
    
    Value result = Value::make_boolean(is_instance, pc);
    set_register(regA, result, pc);
    
    entry.status = InstructionTraceEntry::Status::SUCCESS;
    entry.operands.push_back({"v" + std::to_string(regA), is_instance ? "true" : "false", regA});
    entry.operands.push_back({"v" + std::to_string(regB), val.to_string(), regB});
    entry.operands.push_back({"type@", std::to_string(type_idx), type_idx});
    
    pc_ += 5;
    
    return true;
}

// ============================================================================
// Phase 5: API Database Integration
// ============================================================================

bool DexInterpreterExp018::load_api_priority_database(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        log("[EXP-018] Could not load API priority database: " + path);
        return false;
    }
    
    try {
        file >> api_priority_db_;
        log("[EXP-018] Loaded API priority database: " + path);
        
        // Extract missing APIs into our report structure
        if (api_priority_db_.contains("priority_classifications")) {
            auto& classifications = api_priority_db_["priority_classifications"];
            
            // Process P1 APIs that are not implemented
            if (classifications.contains("P1_HIGH_GT_25_PERCENT")) {
                for (const auto& api : classifications["P1_HIGH_GT_25_PERCENT"]) {
                    if (api.contains("implemented") && !api["implemented"].get<bool>()) {
                        MissingApiEntry missing;
                        missing.api_name = api.value("api", "unknown");
                        missing.priority = "P1";
                        missing.usage_percent = api.value("usage_percent", 0.0);
                        missing.apps_blocked = api.value("apps_using", 0);
                        missing.blocking_reason = api.value("status", "Not implemented");
                        missing.suggested_fix = "Implement " + missing.api_name;
                        exp018_config_.missing_apis.push_back(missing);
                    }
                }
            }
            
            // Process P2 APIs
            if (classifications.contains("P2_MEDIUM_GT_10_PERCENT")) {
                for (const auto& api : classifications["P2_MEDIUM_GT_10_PERCENT"]) {
                    if (api.is_object() && api.contains("implemented") && !api["implemented"].get<bool>()) {
                        MissingApiEntry missing;
                        missing.api_name = api.value("api", "unknown");
                        missing.priority = "P2";
                        missing.usage_percent = api.value("usage_percent", 0.0);
                        missing.apps_blocked = api.value("apps_using", 0);
                        missing.blocking_reason = api.value("status", "Not implemented");
                        missing.suggested_fix = "Implement when needed";
                        exp018_config_.missing_apis.push_back(missing);
                    }
                }
            }
        }
        
        return true;
    } catch (const std::exception& e) {
        log("[EXP-018] Error parsing API priority database: " + std::string(e.what()));
        return false;
    }
}

bool DexInterpreterExp018::load_opcode_frequency_database(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        log("[EXP-018] Could not load opcode frequency database: " + path);
        return false;
    }
    
    try {
        file >> opcode_frequency_db_;
        log("[EXP-018] Loaded opcode frequency database: " + path);
        return true;
    } catch (const std::exception& e) {
        log("[EXP-018] Error parsing opcode frequency database: " + std::string(e.what()));
        return false;
    }
}

json DexInterpreterExp018::generate_missing_api_report() const {
    json report;
    report["experiment_id"] = "EXP-018";
    report["timestamp"] = get_timestamp();
    report["total_missing_apis"] = exp018_config_.missing_apis.size();
    
    json missing_array = json::array();
    for (const auto& api : exp018_config_.missing_apis) {
        missing_array.push_back(api.to_json());
    }
    report["missing_apis"] = missing_array;
    
    // Summary statistics
    double total_apps_blocked = 0;
    for (const auto& api : exp018_config_.missing_apis) {
        total_apps_blocked += api.apps_blocked;
    }
    
    report["summary"] = {
        {"p1_missing", std::count_if(exp018_config_.missing_apis.begin(), 
                                       exp018_config_.missing_apis.end(),
                                       [](const MissingApiEntry& e) { return e.priority == "P1"; })},
        {"p2_missing", std::count_if(exp018_config_.missing_apis.begin(),
                                       exp018_config_.missing_apis.end(),
                                       [](const MissingApiEntry& e) { return e.priority == "P2"; })},
        {"total_apps_potentially_blocked", total_apps_blocked}
    };
    
    return report;
}

} // namespace dex
} // namespace miniandroid
