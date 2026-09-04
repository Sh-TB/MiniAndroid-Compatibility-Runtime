/*
 * MiniAndroid Runtime v0.3 - EXP-018 Real Android Execution Core Batch
 * 
 * Enhanced DEX Interpreter with:
 * - Phase 1: Control Flow Engine (if-eqz/if-nez/if-eq/if-ne/goto)
 * - Phase 2: Return Value System (return/return-object/return-wide + move-result*)
 * - Phase 3: Static Dispatch (invoke-static)
 * - Phase 4: Interface Dispatch (invoke-interface)
 * 
 * Golden Debug Protocol Compliant
 * Data Source: database/api_priority.json, database/real_opcode_frequency.json
 */

#ifndef MINIANDROID_DEX_INTERPRETER_EXP018_H
#define MINIANDROID_DEX_INTERPRETER_EXP018_H

#include "dex_interpreter_v2.h"
#include <unordered_set>
#include <stack>
#include <limits>

namespace miniandroid {
namespace dex {

// ============================================================================
// EXP-018 New Opcode Definitions
// ============================================================================

namespace OpcodesExp018 {
    // Control Flow Opcodes (Phase 1) - P0 CRITICAL from real_opcode_frequency.json
    constexpr uint16_t IF_EQZ = 0x39;       // if-eqz vAA, +BBBB  (branch if vAA == 0)
    constexpr uint16_t IF_NEZ = 0x3A;       // if-nez vAA, +BBBB  (branch if vAA != 0)
    constexpr uint16_t IF_EQ = 0x33;        // if-eq vAA, vBB, +CCCC (branch if vAA == vBB)
    constexpr uint16_t IF_NE = 0x34;        // if-ne vAA, vBB, +CCCC (branch if vAA != vBB)
    constexpr uint16_t GOTO = 0x28;         // goto +AA           (unconditional jump)
    constexpr uint16_t GOTO_16 = 0x29;      // goto/16 +AAAA      (unconditional jump, 16-bit)
    constexpr uint16_t GOTO_32 = 0x2A;      // goto/32 +AAAAAAAA  (unconditional jump, 32-bit)
    
    // Extended conditional branches (P1_HIGH)
    constexpr uint16_t IF_LTZ = 0x3B;       // if-ltz vAA, +BBBB
    constexpr uint16_t IF_GEZ = 0x3C;       // if-gez vAA, +BBBB
    constexpr uint16_t IF_GTZ = 0x3D;       // if-gtz vAA, +BBBB
    constexpr uint16_t IF_LEZ = 0x3E;       // if-lez vAA, +BBBB
    constexpr uint16_t IF_LT = 0x35;        // if-lt vAA, vBB, +CCCC
    constexpr uint16_t IF_GE = 0x36;        // if-ge vAA, vBB, +CCCC
    constexpr uint16_t IF_GT = 0x37;        // if-gt vAA, vBB, +CCCC
    constexpr uint16_t IF_LE = 0x38;        // if-le vAA, vBB, +CCCC
    
    // Return Value System (Phase 2)
    constexpr uint16_t MOVE_RESULT = 0x0A;          // move-result vAA
    constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;   // move-result-object vAA
    constexpr uint16_t MOVE_RESULT_WIDE = 0x0B;     // move-result-wide vAA
    constexpr uint16_t RETURN_WIDE = 0x10;          // return-wide vAA
    
    // Static Dispatch (Phase 3) - P0_CRITICAL (485 occurrences in corpus)
    // INVOKE_STATIC = 0x67 already defined in V2
    
    // Interface Dispatch (Phase 4) - P1_HIGH (150 occurrences in corpus)
    // INVOKE_INTERFACE = 0x72 already defined in V2
    
    // Additional opcodes needed for real execution
    constexpr uint16_t CONST_16 = 0x13;       // const/16 vAA, #+BBBB
    constexpr uint16_t SGET_OBJECT = 0x62;   // sget-object vAA, field@BBBB
    constexpr uint16_t SPUT_OBJECT = 0x63;   // sput-object vAA, field@BBBB
    constexpr uint16_t CHECK_CAST = 0x1F;    // check-cast vAA, type@BBBB
    constexpr uint16_t INSTANCE_OF = 0x20;   // instance-of vA, vB, type@CCCC
}

// ============================================================================
// Branch Trace Entry (Phase 1 Evidence)
// ============================================================================

struct BranchTraceEntry {
    uint64_t sequence = 0;
    uint32_t pc_before = 0;
    uint32_t pc_after = 0;
    
    std::string opcode_name;
    std::string condition_description;
    
    // Condition evaluation
    struct {
        std::string register_a;
        std::string register_b;  // For two-register comparisons
        int32_t value_a = 0;
        int32_t value_b = 0;
        bool was_null_a = false;
        bool was_null_b = false;
        bool condition_result = false;
    } condition;
    
    // Branch decision
    bool taken = false;
    int32_t offset = 0;
    uint32_t target_pc = 0;
    uint32_t fallthrough_pc = 0;
    
    json to_json() const;
};

// ============================================================================
// Loop Detection Record (Phase 1)
// ============================================================================

struct LoopDetectionRecord {
    uint32_t loop_start_pc = 0;
    uint32_t loop_end_pc = 0;
    std::string loop_type;  // "for", "while", "do-while"
    
    uint32_t iteration_count = 0;
    uint32_t max_iterations_hit = false;
    bool is_infinite_loop_detected = false;
    
    // Back-edge information
    std::vector<uint32_t> back_edge_pcs;
    
    json to_json() const;
};

// ============================================================================
// Control Flow Statistics (Phase 1 Evidence)
// ============================================================================

struct ControlFlowStatistics {
    uint32_t total_branches_encountered = 0;
    uint32_t branches_taken = 0;
    uint32_t branches_not_taken = 0;
    uint32_t unconditional_jumps = 0;
    uint32_t loops_detected = 0;
    uint32_t infinite_loops_protected = 0;
    
    // Opcode breakdown
    std::map<std::string, uint32_t> opcode_counts;
    
    json to_json() const;
};

// ============================================================================
// Return Value Trace (Phase 2 Evidence)
// ============================================================================

struct ReturnTraceEntry {
    uint64_t sequence = 0;
    uint32_t pc = 0;
    std::string opcode_name;
    
    // What was returned
    Value returned_value;
    std::string returning_method;
    
    // Who captured it (move-result*)
    bool captured = false;
    uint32_t capture_pc = 0;
    uint8_t capture_register = 0;
    
    json to_json() const;
};

// ============================================================================
// Static Method Registry Entry (Phase 3)
// ============================================================================

struct StaticMethodEntry {
    std::string class_name;
    std::string method_name;
    std::string descriptor;
    
    enum class ImplementationType {
        NATIVE_CPP,     // Implemented in C++
        JDK_STUB,       // JDK method stub
        ANDROID_STUB,   // Android framework stub
        UNIMPLEMENTED
    } implementation_type;
    
    // Implementation function
    using StaticImplementationFn = std::function<Value(
        const std::vector<Value>& args,
        void* context
    )>;
    StaticImplementationFn implementation;
    
    // Metadata
    std::string added_in_experiment;
    uint32_t call_count = 0;  // Runtime statistics
    
    json to_json() const;
};

// ============================================================================
// Interface Dispatch Record (Phase 4 Evidence)
// ============================================================================

struct InterfaceDispatchRecord {
    uint64_t sequence = 0;
    uint32_t pc = 0;
    
    std::string interface_name;
    std::string method_name;
    std::string descriptor;
    
    // Object being dispatched on
    Value target_object;
    std::string actual_class;  // Runtime class of object
    
    // Resolution
    bool resolved = false;
    std::string resolved_method;
    Value result;
    
    // Common interfaces
    bool is_on_click_listener = false;
    
    json to_json() const;
};

// ============================================================================
// Missing API Report Entry (Phase 5)
// ============================================================================

struct MissingApiEntry {
    std::string api_name;
    std::string priority;  // P0, P1, P2, P3
    double usage_percent = 0;
    uint32_t apps_blocked = 0;
    std::string blocking_reason;
    std::string suggested_fix;
    
    json to_json() const;
};

// ============================================================================
// EXP-018 Enhanced Configuration
// ============================================================================

struct Exp018Config : InterpreterConfigV2 {
    // Control flow settings
    uint32_t max_loop_iterations = 10000;  // Infinite loop protection
    bool enable_loop_detection = true;
    bool trace_all_branches = true;
    
    // Return value settings
    bool enable_return_tracking = true;
    
    // Static dispatch settings
    bool enable_static_dispatch = true;
    
    // Interface dispatch settings
    bool enable_interface_dispatch = true;
    
    // Strict mode (--strict-real)
    bool strict_real_mode = false;
    
    // API priority loading
    std::string api_priority_path = "run/database/api_priority.json";
    std::string opcode_frequency_path = "run/database/real_opcode_frequency.json";
    
    // Auto-loaded from database
    std::vector<MissingApiEntry> missing_apis;
};

// ============================================================================
// Main EXP-018 Interpreter Class
// ============================================================================

/**
 * EXP-018 Enhanced DEX Interpreter
 * 
 * Adds critical execution capabilities based on real corpus analysis:
 * 
 * Phase 1: Control Flow Engine
 *   - if-eqz/if-nez: Null checks and boolean conditions (blocks 67% apps without)
 *   - if-eq/if-ne: Register comparisons
 *   - goto: Loop support (blocks 92% apps without!)
 *   - Loop detection and infinite loop protection
 * 
 * Phase 2: Return Value System  
 *   - return-object: Methods can return objects
 *   - move-result-object: Capture return values
 *   - Enables method chaining: findViewById().setText()
 * 
 * Phase 3: Static Dispatch
 *   - invoke-static: Integer.parseInt(), Toast.makeText(), Log.d()
 *   - Static method registry with implementations
 * 
 * Phase 4: Interface Dispatch
 *   - invoke-interface: View.OnClickListener
 *   - Event listener support
 */
class DexInterpreterExp018 : public DexInterpreterV2 {
public:
    DexInterpreterExp018();
    ~DexInterpreterExp018();
    
    /**
     * Execute with EXP-018 enhancements
     */
    InstructionTrace execute_exp018(
        const MethodInfo& method,
        const std::vector<std::string>& strings,
        const Exp018Config& config = Exp018Config{}
    );
    
    // =========================================================================
    // Phase 1: Control Flow Accessors
    // =========================================================================
    
    const std::vector<BranchTraceEntry>& get_branch_trace() const { return branch_trace_; }
    const std::vector<LoopDetectionRecord>& get_loops_detected() const { return loops_detected_; }
    const ControlFlowStatistics& get_control_flow_stats() const { return cf_stats_; }
    
    // =========================================================================
    // Phase 2: Return Value Accessors
    // =========================================================================
    
    const std::vector<ReturnTraceEntry>& get_return_trace() const { return return_trace_; }
    Value get_pending_return_value() const { return pending_return_; }
    bool has_pending_return() const { return has_pending_return_; }
    
    // =========================================================================
    // Phase 3: Static Dispatch Accessors
    // =========================================================================
    
    const std::vector<StaticMethodEntry>& get_static_registry() const { return static_registry_; }
    void register_static_method(const StaticMethodEntry& entry);
    const std::vector<ApiCallRecord>& get_static_call_trace() const { return static_call_trace_; }
    
    // =========================================================================
    // Phase 4: Interface Dispatch Accessors
    // =========================================================================
    
    const std::vector<InterfaceDispatchRecord>& get_interface_trace() const { return interface_trace_; }
    void register_interface_implementation(
        const std::string& interface_name,
        const std::string& method_name,
        StaticMethodEntry::StaticImplementationFn impl
    );
    
    // =========================================================================
    // Phase 5: API Database Integration
    // =========================================================================
    
    bool load_api_priority_database(const std::string& path);
    bool load_opcode_frequency_database(const std::string& path);
    const std::vector<MissingApiEntry>& get_missing_apis() const { return exp018_config_.missing_apis; }
    
    /**
     * Generate runtime missing API report
     */
    json generate_missing_api_report() const;
    
protected:
    // Override fetch-decode-execute to add new opcodes
    bool fetch_decode_execute_exp018(InstructionTrace& trace, const Exp018Config& config);
    
private:
    // =========================================================================
    // Phase 1: Control Flow Implementations
    // =========================================================================
    
    bool execute_if_eqz(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_nez(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_eq(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_ne(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_goto(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_goto_16(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_goto_32(uint32_t pc, InstructionTraceEntry& entry);
    
    // Extended branches
    bool execute_if_ltz(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_gez(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_gtz(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_lez(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_lt(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_ge(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_gt(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_if_le(uint32_t pc, InstructionTraceEntry& entry);
    
    // Branch helper
    bool evaluate_condition(int32_t a, int32_t b, const std::string& op);
    void record_branch(const BranchTraceEntry& branch);
    void detect_loops(uint32_t from_pc, uint32_t to_pc);
    bool check_loop_protection(uint32_t target_pc);
    
    // =========================================================================
    // Phase 2: Return Value Implementations
    // =========================================================================
    
    bool execute_move_result(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_move_result_object(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_move_result_wide(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_return_wide(uint32_t pc, InstructionTraceEntry& entry);
    
    void set_pending_return(const Value& val);
    void clear_pending_return();
    
    // =========================================================================
    // Phase 3: Static Dispatch Implementation
    // =========================================================================
    
    bool execute_invoke_static(uint32_t pc, InstructionTraceEntry& entry, const Exp018Config& config);
    StaticMethodEntry* lookup_static_method(
        const std::string& class_name,
        const std::string& method_name,
        const std::string& descriptor
    );
    void initialize_builtin_static_methods();
    
    // =========================================================================
    // Phase 4: Interface Dispatch Implementation
    // =========================================================================
    
    bool execute_invoke_interface(uint32_t pc, InstructionTraceEntry& entry, const Exp018Config& config);
    InterfaceDispatchRecord* resolve_interface_method(
        const Value& object,
        const std::string& interface_name,
        const std::string& method_name,
        const std::string& descriptor
    );
    void initialize_builtin_interfaces();
    
    // =========================================================================
    // Phase 5: Additional Opcode Implementations
    // =========================================================================
    
    bool execute_const_16(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_sget_object(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_sput_object(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_check_cast(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_instance_of(uint32_t pc, InstructionTraceEntry& entry);
    
    // =========================================================================
    // State
    // =========================================================================
    
    Exp018Config exp018_config_;
    
    // Phase 1: Control flow state
    std::vector<BranchTraceEntry> branch_trace_;
    std::vector<LoopDetectionRecord> loops_detected_;
    ControlFlowStatistics cf_stats_;
    std::map<uint32_t, uint32_t> pc_visit_count_;  // For loop detection
    std::stack<uint32_t> call_stack_;               // For return address tracking
    
    // Phase 2: Return value state
    std::vector<ReturnTraceEntry> return_trace_;
    Value pending_return_;
    bool has_pending_return_ = false;
    
    // Phase 3: Static dispatch state
    std::vector<StaticMethodEntry> static_registry_;
    std::vector<ApiCallRecord> static_call_trace_;
    
    // Phase 4: Interface dispatch state
    std::vector<InterfaceDispatchRecord> interface_trace_;
    std::map<std::string, std::map<std::string, StaticMethodEntry::StaticImplementationFn>> interface_implementations_;
    
    // Phase 5: Database state
    json api_priority_db_;
    json opcode_frequency_db_;
};

} // namespace dex
} // namespace miniandroid

#endif // MINIANDROID_DEX_INTERPRETER_EXP018_H
