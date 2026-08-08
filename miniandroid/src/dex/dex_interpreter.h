/*
 * MiniAndroid Runtime v0.1 - DEX Interpreter
 * EXP-003-A: const-string Opcode Implementation
 * 
 * Golden Debug Protocol Compliant
 * 
 * Implements ONLY: const-string (0x1A)
 * Stops on any other opcode with PARTIAL_SUCCESS
 */

#ifndef MINIANDROID_DEX_INTERPRETER_H
#define MINIANDROID_DEX_INTERPRETER_H

#include "dex_parser.h"
#include "class_resolver.h"
#include <string>
#include <vector>
#include <map>
#include <optional>
#include <cstdint>
#include <functional>

// Include JSON library (needed for return types)
#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace dex {

// Convenience alias for JSON within our namespace
using json = nlohmann::json;

// ============================================================================
// Opcode Definitions (EXP-003-A: Only const-string)
// ============================================================================

namespace Opcodes {
    // Implemented in EXP-003-A
    constexpr uint16_t CONST_STRING = 0x001A;  // const-string vAA, string@BBBB
    
    // Future opcodes (NOT implemented yet)
    constexpr uint16_t CONST_STRING_JUMBO = 0x001B;
    constexpr uint16_t CONST_4 = 0x12;
    constexpr uint16_t CONST_16 = 0x13;
    constexpr uint16_t CONST = 0x14;
    constexpr uint16_t CONST_HIGH16 = 0x15;
    constexpr uint16_t NEW_INSTANCE = 0x22;
    constexpr uint16_t NEW_ARRAY = 0x23;
    constexpr uint16_t INVOKE_VIRTUAL = 0x6E;
    constexpr uint16_t INVOKE_SUPER = 0x6F;
    constexpr uint16_t INVOKE_DIRECT = 0x70;
    constexpr uint16_t INVOKE_STATIC = 0x71;
    constexpr uint16_t INVOKE_INTERFACE = 0x72;
    constexpr uint16_t RETURN_VOID = 0x0E;
    constexpr uint16_t RETURN = 0x0F;
    constexpr uint16_t RETURN_OBJECT = 0x11;
}

// ============================================================================
// VM State Types
// ============================================================================

// Value types in registers
enum class ValueType {
    UNINITIALIZED,
    INT32,
    FLOAT,
    LONG,
    DOUBLE,
    STRING_REF,      // Reference to string pool
    OBJECT_REF,     // Reference to object
    NULL_REF,       // Explicit null
    REGISTER_UNSET  // Register not yet written
};

// A value in a register or stack location
struct Value {
    ValueType type = ValueType::REGISTER_UNSET;
    
    union {
        int32_t int_val;
        float float_val;
        int64_t long_val;
        double double_val;
    };
    
    std::string string_val;       // For STRING_REF
    std::string object_class;     // For OBJECT_REF
    uint32_t reference_id = 0;    // Unique reference ID
    
    bool is_null = false;
    
    static Value make_string(const std::string& str, uint32_t ref_id) {
        Value v;
        v.type = ValueType::STRING_REF;
        v.string_val = str;
        v.reference_id = ref_id;
        return v;
    }
    
    static Value make_uninitialized() {
        Value v;
        v.type = ValueType::UNINITIALIZED;
        return v;
    }
    
    static Value make_null() {
        Value v;
        v.type = ValueType::NULL_REF;
        v.is_null = true;
        return v;
    }
    
    std::string to_string() const;
};

// Instruction-level trace entry (for instruction_trace.json)
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
    
    // Resolved values (if applicable)
    std::optional<std::string> resolved_string;
    
    // Execution result
    enum class Status {
        SUCCESS,
        HALT_UNIMPLEMENTED,
        CRASH_INVALID_STATE,
        HALT_EXPERIMENT_BOUNDARY
    };
    Status status = Status::SUCCESS;
    uint32_t cycles = 1;
    
    // State changes
    std::vector<std::string> registers_written;
    std::map<std::string, Value> register_snapshots;
    
    // Halt reason (if halted)
    std::optional<std::string> halt_reason;
    
    json to_json() const;
};

// Full instruction trace for experiment evidence
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
    std::string halt_reason;
    std::optional<uint16_t> next_opcode_hex;
    std::string next_opcode_name;
    
    // Statistics
    uint32_t total_instructions_in_method = 0;
    uint32_t executed_instructions = 0;
    std::string success_rate;
    uint32_t unimplemented_opcodes_encountered = 0;
    
    json to_json() const;
};

// Interpreter configuration
struct InterpreterConfig {
    bool verbose = false;
    bool debug_output = false;
    uint32_t max_instructions = 1000;  // SC-04: Infinite loop protection
    bool stop_on_unimplemented = true;  // SC-01 behavior
    bool generate_trace = true;
    
    // Experiment boundary
    std::string experiment_scope = "EXP-003-A";
    std::vector<uint16_t> allowed_opcodes = {Opcodes::CONST_STRING};
};

// ============================================================================
// Main DEX Interpreter Class
// ============================================================================

/**
 * DEX Bytecode Interpreter
 * 
 * EXP-003-A Scope: ONLY implements const-string (0x1A)
 * All other opcodes trigger graceful halt.
 */
class DexInterpreter {
public:
    DexInterpreter();
    ~DexInterpreter();
    
    /**
     * Execute method bytecode starting from entry point
     * 
     * @param method The method info from DEX parsing
     * @param strings String pool from DEX
     * @param config Interpreter configuration
     * @return Instruction trace as evidence
     */
    InstructionTrace execute(
        const MethodInfo& method,
        const std::vector<std::string>& strings,
        const InterpreterConfig& config = InterpreterConfig{}
    );
    
    /**
     * Execute with class resolver entry point
     */
    InstructionTrace execute_entry_point(
        const EntryPoint& entry,
        const DexReport& dex_report,
        const InterpreterConfig& config = InterpreterConfig{}
    );
    
    /**
     * Get last error message
     */
    std::string get_last_error() const { return last_error_; }
    
    /**
     * Check if interpreter halted early
     */
    bool was_halted() const { return halted_; }
    std::string halt_reason() const { return halt_reason_; }

private:
    // Core execution loop
    bool fetch_decode_execute(InstructionTrace& trace, const InterpreterConfig& config);
    uint16_t fetch_opcode(uint32_t pc);
    
    // Opcode implementations (EXP-003-A: Only const-string)
    bool execute_const_string(uint32_t pc, InstructionTraceEntry& entry);
    
    // Unimplemented opcode handler (SC-01)
    void handle_unimplemented(uint16_t opcode, uint32_t pc, InstructionTraceEntry& entry);
    
    // Register operations
    void set_register(uint8_t reg, const Value& value);
    Value get_register(uint8_t reg) const;
    std::string register_name(uint8_t reg) const;
    
    // Utility
    void log(const std::string& msg);
    void add_instruction_to_trace(InstructionTrace& trace, const InstructionTraceEntry& entry);
    
    // State
    std::vector<Value> registers_;
    std::vector<uint16_t> bytecode_;
    std::vector<std::string> strings_;
    uint32_t pc_ = 0;
    uint32_t code_offset_ = 0;
    
    uint32_t next_ref_id_ = 1;
    uint32_t instruction_sequence_ = 0;
    
    bool halted_ = false;
    std::string halt_reason_;
    std::string last_error_;
    
    bool verbose_ = false;
};

} // namespace dex
} // namespace miniandroid

#endif // MINIANDROID_DEX_INTERPRETER_H
