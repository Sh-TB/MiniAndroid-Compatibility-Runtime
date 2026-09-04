/*
 * MiniAndroid Runtime v0.2 - Enhanced DEX Interpreter
 * EXP-014: Real DEX Execution Core
 * 
 * Golden Debug Protocol Compliant
 * 
 * Implements critical opcodes for real execution path:
 * - P0: new-instance, invoke-direct, invoke-virtual, return-void
 * - P1: move-object, const/4, iget-object, iput-object, return-object
 * 
 * Key changes from EXP-003-A version:
 * 1. Object heap integration for new-instance
 * 2. Method resolution and dispatch for invoke-* 
 * 3. API registry integration for Android framework calls
 * 4. Register execution model with lifetime tracking
 */

#ifndef MINIANDROID_DEX_INTERPRETER_V2_H
#define MINIANDROID_DEX_INTERPRETER_V2_H

#include "dex_parser.h"
#include "class_resolver.h"
#include "../runtime/object_model.h"
#include <string>
#include <vector>
#include <map>
#include <optional>
#include <cstdint>
#include <functional>
#include <memory>
#include <chrono>

// Include JSON library
#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace dex {

using json = nlohmann::json;

// Forward declarations
namespace runtime {
    class EnhancedObjectHeap;
    class ActivityRuntimeObject;
    class ViewRuntimeObject;
    class TextViewRuntimeObject;
}

// ============================================================================
// Opcode Definitions (EXP-014 Extended Set)
// ============================================================================

namespace Opcodes {
    // Already implemented in EXP-003-A
    constexpr uint16_t CONST_STRING = 0x001A;  // const-string vAA, string@BBBB
    
    // NEW: Return opcodes (EXP-014)
    constexpr uint16_t RETURN_VOID = 0x0E;     // return-void
    constexpr uint16_t RETURN = 0x0F;          // return
    constexpr uint16_t RETURN_OBJECT = 0x11;   // return-object
    
    // NEW: Constant loading (EXP-014 P1)
    constexpr uint16_t CONST_4 = 0x12;         // const/4 vA, #+B
    constexpr uint16_t CONST_16 = 0x13;        // const/16 vAA, #+BBBB
    constexpr uint16_t CONST = 0x14;           // const vAA, #+BBBBBBBB
    constexpr uint16_t CONST_HIGH16 = 0x15;    // const/high16 vAA, #+BBBB0000
    
    // NEW: Move operations (EXP-014 P1)
    constexpr uint16_t MOVE = 0x01;            // move vA, vB
    constexpr uint16_t MOVE_FROM16 = 0x02;     // move/from16 vAA, vBBBB
    constexpr uint16_t MOVE_16 = 0x03;         // move/16 vAAA, vBBBB
    constexpr uint16_t MOVE_WIDE = 0x04;       // move-wide vA, vB
    constexpr uint16_t MOVE_OBJECT = 0x07;     // move-object vA, vB
    
    // NEW: Object operations (EXP-014 P0 CRITICAL)
    constexpr uint16_t NEW_INSTANCE = 0x22;    // new-instance vAA, type@BBBB
    constexpr uint16_t NEW_ARRAY = 0x23;       // new-array vAA, vB, type@CCCC
    
    // NEW: Instance field operations (EXP-014 P1)
    constexpr uint16_t IGET_OBJECT = 0x52;      // iget-object vAA, vBB, field@CCCC
    constexpr uint16_t IPUT_OBJECT = 0x59;      // iput-object vAA, vBB, field@CCCC
    
    // NEW: Method invocation (EXP-014 P0 CRITICAL)
    constexpr uint16_t INVOKE_VIRTUAL = 0x6E;   // invoke-virtual {vC, ...}, method@BBBB
    constexpr uint16_t INVOKE_SUPER = 0x6F;     // invoke-super {vC, ...}, method@BBBB
    constexpr uint16_t INVOKE_DIRECT = 0x70;    // invoke-direct {vC, ...}, method@BBBB
    constexpr uint16_t INVOKE_STATIC = 0x71;    // invoke-static {vC, ...}, method@BBBB
    constexpr uint16_t INVOKE_INTERFACE = 0x72; // invoke-interface {vC, ...}, method@BBBB
    
    // Array operations (future)
    constexpr uint16_t AGET_OBJECT = 0x44;      // aget-object vAA, vBB, vCC
    constexpr uint16_t APUT_OBJECT = 0x4B;      // aput-object vAA, vBB, vCC
    
    // Type check operations (future)
    constexpr uint16_t INSTANCE_OF = 0x20;      // instance-of vA, vB, type@CCCC
    constexpr uint16_t CHECK_CAST = 0x1F;       // check-cast vAA, type@BBBB
}

// ============================================================================
// Enhanced Value Types (EXP-014)
// ============================================================================

enum class ValueType {
    UNINITIALIZED,
    INT32,
    FLOAT,
    LONG,
    DOUBLE,
    STRING_REF,      // Reference to string pool
    OBJECT_REF,     // Reference to object heap
    NULL_REF,       // Explicit null
    REGISTER_UNSET, // Register not yet written
    BOOLEAN,        // New: boolean type (stored as int32)
    BYTE,           // New: byte type
    SHORT,          // New: short type
    CHAR            // New: char type
};

std::string value_type_to_string(ValueType type);

// A value in a register or stack location (enhanced for EXP-014)
struct Value {
    ValueType type = ValueType::REGISTER_UNSET;
    
    union {
        int32_t int_val;
        float float_val;
        int64_t long_val;
        double double_val;
        bool bool_val;
        int8_t byte_val;
        int16_t short_val;
        char char_val;
    };
    
    std::string string_val;       // For STRING_REF
    std::string object_class;     // For OBJECT_REF - class name
    uint32_t reference_id = 0;    // Unique reference ID (object heap ID or string ref)
    
    bool is_null = false;
    
    // Register lifetime tracking (EXP-014 new)
    uint32_t defined_at_pc = 0;      // PC where this value was set
    uint32_t last_used_at_pc = 0;     // PC where this value was last read
    bool is_live = true;              // Liveness tracking
    
    // Factory methods
    static Value make_string(const std::string& str, uint32_t ref_id, uint32_t pc = 0);
    static Value make_object(const std::string& class_name, uint32_t obj_id, uint32_t pc = 0);
    static Value make_int(int32_t val, uint32_t pc = 0);
    static Value make_uninitialized();
    static Value make_null();
    static Value make_boolean(bool val, uint32_t pc = 0);
    
    std::string to_string() const;
    json to_json() const;
};

// ============================================================================
// API Dispatch Record (EXP-014 new)
// ============================================================================

enum class DispatchType {
    DIRECT,      // invoke-direct
    VIRTUAL,     // invoke-virtual
    STATIC,      // invoke-static
    SUPER,       // invoke-super
    INTERFACE,   // invoke-interface
    UNKNOWN
};

std::string dispatch_type_to_string(DispatchType type);

struct ApiCallRecord {
    uint64_t sequence = 0;
    std::string timestamp;
    
    // What was called
    std::string class_name;
    std::string method_name;
    std::string descriptor;
    DispatchType dispatch_type;
    
    // Call context
    std::string caller_method;
    std::string caller_class;
    uint32_t caller_pc = 0;
    
    // Arguments (simplified)
    std::vector<Value> arguments;
    
    // Result
    bool success = false;
    Value result_value;
    std::string result_summary;
    std::string error_message;
    
    // Source tracking
    bool was_dispatched_from_dex = false;  // KEY: Was this from real DEX?
    std::string dispatch_path;             // "DEX_INTERPRETER" or "CPP_FALLBACK"
    
    json to_json() const;
};

// ============================================================================
// Object Allocation Record (EXP-014 new)
// ============================================================================

struct ObjectAllocationRecord {
    uint64_t sequence = 0;
    uint32_t pc = 0;
    std::string opcode;                    // "new-instance"
    
    // Type information
    std::string type_descriptor;          // e.g., "Landroid/widget/TextView;"
    std::string resolved_class_name;      // e.g., "android.widget.TextView"
    
    // Result
    uint32_t object_id = 0;               // Assigned object heap ID
    uint8_t destination_register = 0;     // Which register got the ref
    bool allocation_success = false;
    
    // Execution path verification
    bool allocated_via_interpreter = false;  // KEY: Real DEX allocation?
    std::string allocation_source;           // "DEX_NEW_INSTANCE" or "CPP_DIRECT"
    
    json to_json() const;
};

// ============================================================================
// Register Execution Trace (EXP-014 Task 1)
// ============================================================================

struct RegisterStateSnapshot {
    uint32_t pc = 0;
    uint32_t instruction_sequence = 0;
    std::map<uint8_t, Value> register_values;
    
    json to_json() const;
};

struct RegisterExecutionTrace {
    std::string experiment_id;
    std::string timestamp;
    std::string method_context;
    
    // Initial state
    RegisterStateSnapshot initial_state;
    
    // All state changes (after each instruction)
    std::vector<RegisterStateSnapshot> snapshots;
    
    // Final state
    RegisterStateSnapshot final_state;
    
    // Lifetime analysis
    struct RegisterLifetime {
        uint8_t register_num;
        ValueType final_type;
        uint32_t first_defined_pc;
        uint32_t last_used_pc;
        uint32_t write_count;
        uint32_t read_count;
        bool ever_live;
    };
    std::vector<RegisterLifetime> lifetimes;
    
    json to_json() const;
};

// ============================================================================
// Instruction Trace Entry (Enhanced for EXP-014)
// ============================================================================

struct InstructionTraceEntry {
    uint32_t sequence = 0;
    uint32_t pc_before = 0;
    uint32_t pc_after = 0;
    
    std::string opcode_name;
    uint16_t opcode_hex = 0;
    
    // Decoded operands
    struct Operand {
        std::string name;
        std::string value;
        int64_t numeric_value = 0;
    };
    std::vector<Operand> operands;
    
    // Resolved values
    std::optional<std::string> resolved_string;
    std::optional<std::string> resolved_type;
    
    // Execution result
    enum class Status {
        SUCCESS,
        HALT_UNIMPLEMENTED,
        CRASH_INVALID_STATE,
        HALT_EXPERIMENT_BOUNDARY,
        METHOD_RETURNED,      // EXP-014 new: normal method exit
        API_CALL_DISPATCHED    // EXP-014 new: API call made
    };
    Status status = Status::SUCCESS;
    uint32_t cycles = 1;
    
    // State changes
    std::vector<std::string> registers_written;
    std::map<std::string, Value> register_snapshots;
    
    // EXP-014 new fields
    std::optional<ObjectAllocationRecord> object_allocated;
    std::optional<ApiCallRecord> api_call_made;
    
    // Halt reason (if halted)
    std::optional<std::string> halt_reason;
    
    json to_json() const;
};

// ============================================================================
// Full Instruction Trace (Enhanced for EXP-014)
// ============================================================================

struct InstructionTrace {
    std::string experiment_id;
    std::string timestamp;
    
    // Method context
    std::string class_name;
    std::string method_name;
    std::string method_descriptor;
    
    // Initial state
    uint32_t initial_pc = 0;
    std::map<std::string, Value> initial_registers;
    
    // All executed instructions
    std::vector<InstructionTraceEntry> instructions;
    
    // Final state
    uint32_t final_pc = 0;
    bool halted = false;
    bool returned = false;         // EXP-014 new
    std::string halt_reason;
    std::optional<uint16_t> next_opcode_hex;
    std::string next_opcode_name;
    
    // Statistics
    uint32_t total_instructions_in_method = 0;
    uint32_t executed_instructions = 0;
    std::string success_rate;
    uint32_t unimplemented_opcodes_encountered = 0;
    
    // EXP-014 new statistics
    uint32_t objects_created = 0;
    uint32_t api_calls_dispatched = 0;
    uint32_t real_execution_percentage = 0;
    
    // Register trace (EXP-014 Task 1)
    RegisterExecutionTrace register_trace;
    
    // Allocation records
    std::vector<ObjectAllocationRecord> allocations;
    
    // API call records
    std::vector<ApiCallRecord> api_calls;
    
    json to_json() const;
};

// ============================================================================
// API Registry Entry (EXP-014 Phase 3)
// ============================================================================

enum class ApiImplementationStatus {
    IMPLEMENTED,      // Full C++ implementation exists
    STUBBED,          // Stub that logs but doesn't do real work
    SIMULATED,        // Simulated behavior (documented bypass)
    UNIMPLEMENTED,    // Not implemented at all
    NOT_NEEDED        // Internal/runtime method
};

std::string api_status_to_string(ApiImplementationStatus status);

struct ApiRegistryEntry {
    std::string class_name;
    std::string method_name;
    std::string descriptor;
    ApiImplementationStatus status;
    int priority;  // 0=highest
    
    // Implementation hook (function pointer or lambda)
    using ImplementationFn = std::function<Value(
        const std::vector<Value>& args,  // Arguments from registers
        void* context                     // Runtime context (object heap, etc.)
    )>;
    
    ImplementationFn implementation;
    
    // Metadata
    std::string added_in_experiment;
    std::string notes;
    
    json to_json() const;
};

// ============================================================================
// Interpreter Configuration (Enhanced for EXP-014)
// ============================================================================

struct InterpreterConfigV2 {
    // Basic settings
    bool verbose = false;
    bool debug_output = false;
    uint32_t max_instructions = 10000;  // Increased for real execution
    bool stop_on_unimplemented = false;  // Changed: don't stop, try to continue
    bool generate_trace = true;
    
    // Experiment scope
    std::string experiment_scope = "EXP-014";
    
    // EXP-014 new: Allowed opcodes (all implemented ones)
    std::vector<uint16_t> allowed_opcodes = {
        Opcodes::CONST_STRING,
        Opcodes::RETURN_VOID,
        Opcodes::RETURN_OBJECT,
        Opcodes::NEW_INSTANCE,
        Opcodes::INVOKE_DIRECT,
        Opcodes::INVOKE_VIRTUAL,
        Opcodes::MOVE_OBJECT,
        Opcodes::CONST_4,
        Opcodes::IGET_OBJECT,
        Opcodes::IPUT_OBJECT
    };
    
    // EXP-014 new: Strict mode
    bool strict_mode = false;  // FAIL on any simulation
    
    // EXP-014 new: Object heap reference
    runtime::EnhancedObjectHeap* object_heap = nullptr;
    
    // EXP-014 new: API registry reference
    std::shared_ptr<std::vector<ApiRegistryEntry>> api_registry;
    
    // EXP-014 new: Class resolver for method lookup
    ClassResolver* class_resolver = nullptr;
    
    // EXP-014 new: DEX report for type/method info
    const DexReport* dex_report = nullptr;
};

// ============================================================================
// Main DEX Interpreter Class V2 (EXP-014)
// ============================================================================

/**
 * Enhanced DEX Bytecode Interpreter
 * 
 * EXP-014 Scope: Implements critical opcodes for real execution:
 * - return-void, return-object (method completion)
 * - new-instance (object creation via DEX)
 * - invoke-direct (constructor calls)
 * - invoke-virtual (API method dispatch)
 * - move-object, const/4 (register manipulation)
 */
class DexInterpreterV2 {
public:
    DexInterpreterV2();
    ~DexInterpreterV2();
    
    /**
     * Execute method bytecode starting from entry point
     */
    InstructionTrace execute(
        const MethodInfo& method,
        const std::vector<std::string>& strings,
        const InterpreterConfigV2& config = InterpreterConfigV2{}
    );
    
    /**
     * Execute with class resolver entry point
     */
    InstructionTrace execute_entry_point(
        const EntryPoint& entry,
        const DexReport& dex_report,
        const InterpreterConfigV2& config = InterpreterConfigV2{}
    );
    
    // State queries
    std::string get_last_error() const { return last_error_; }
    bool was_halted() const { return halted_; }
    std::string halt_reason() const { return halt_reason_; }
    bool did_return() const { return returned_; }
    
    // EXP-014 new: Access traces
    const std::vector<ObjectAllocationRecord>& get_allocations() const { return allocations_; }
    const std::vector<ApiCallRecord>& get_api_calls() const { return api_calls_; }
    const RegisterExecutionTrace& get_register_trace() const { return register_trace_; }

private:
    // Core execution loop
    bool fetch_decode_execute(InstructionTrace& trace, const InterpreterConfigV2& config);
    uint16_t fetch_opcode(uint32_t pc);
    
    // Opcode implementations (EXP-014 extended set)
    bool execute_const_string(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_return_void(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_return_object(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_new_instance(uint32_t pc, InstructionTraceEntry& entry, const InterpreterConfigV2& config);
    bool execute_invoke_direct(uint32_t pc, InstructionTraceEntry& entry, const InterpreterConfigV2& config);
    bool execute_invoke_virtual(uint32_t pc, InstructionTraceEntry& entry, const InterpreterConfigV2& config);
    bool execute_move_object(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_const_4(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_iget_object(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_iput_object(uint32_t pc, InstructionTraceEntry& entry);
    
    // Unimplemented opcode handler
    void handle_unimplemented(uint16_t opcode, uint32_t pc, InstructionTraceEntry& entry);
    
    // Register operations
    void set_register(uint8_t reg, const Value& value, uint32_t pc = 0);
    Value get_register(uint8_t reg) const;
    std::string register_name(uint8_t reg) const;
    void ensure_register_capacity(uint8_t reg);
    
    // EXP-014 new: Object heap operations
    uint32_t allocate_object(const std::string& type_descriptor, uint32_t pc);
    
    // EXP-014 new: Method resolution and dispatch
    ApiCallRecord* resolve_and_dispatch(
        const std::string& class_name,
        const std::string& method_name,
        const std::string& descriptor,
        DispatchType dispatch_type,
        const std::vector<uint8_t>& arg_registers,
        uint32_t pc,
        const InterpreterConfigV2& config
    );
    
    // EXP-014 new: Utility
    void log(const std::string& msg);
    void add_instruction_to_trace(InstructionTrace& trace, const InstructionTraceEntry& entry);
    void capture_register_snapshot(RegisterExecutionTrace& reg_trace, uint32_t pc);
    std::string get_timestamp() const;
    
    // State
    std::vector<Value> registers_;
    std::vector<uint16_t> bytecode_;
    std::vector<std::string> strings_;
    uint32_t pc_ = 0;
    uint32_t code_offset_ = 0;
    
    uint32_t next_ref_id_ = 1;
    uint32_t next_object_id_ = 100;  // Start object IDs at 100
    uint32_t instruction_sequence_ = 0;
    uint64_t api_call_sequence_ = 0;
    uint64_t allocation_sequence_ = 0;
    
    bool halted_ = false;
    bool returned_ = false;
    std::string halt_reason_;
    std::string last_error_;
    bool verbose_ = false;
    
    // EXP-014 new: Traces
    std::vector<ObjectAllocationRecord> allocations_;
    std::vector<ApiCallRecord> api_calls_;
    RegisterExecutionTrace register_trace_;
};

} // namespace dex
} // namespace miniandroid

#endif // MINIANDROID_DEX_INTERPRETER_V2_H