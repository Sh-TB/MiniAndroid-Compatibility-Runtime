/*
 * MiniAndroid Runtime v0.1 - DEX Interpreter (EXP-003-BATCH)
 * 
 * Minimal DEX Execution Engine for Golden APK
 * 
 * Implements the complete onCreate() bytecode path:
 *   const-string → new-instance → invoke-direct → invoke-virtual → return-void
 * 
 * Golden Debug Protocol Compliant
 */

#ifndef MINIANDROID_DEX_INTERPRETER_BATCH_H
#define MINIANDROID_DEX_INTERPRETER_BATCH_H

#include "dex_parser.h"
#include "class_resolver.h"
#include "../api/android_stubs.h"
#include <string>
#include <vector>
#include <map>
#include <optional>
#include <cstdint>
#include <functional>
#include <memory>
#include <sstream>
#include <iomanip>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace dex {

using json = nlohmann::json;

// ============================================================================
// Opcode Definitions (EXP-003-BATCH Scope)
// ============================================================================

namespace Opcodes {
    // Implemented in EXP-003-A/BATCH
    constexpr uint16_t CONST_STRING = 0x001A;  // const-string vAA, string@BBBB
    constexpr uint16_t NEW_INSTANCE = 0x0022;  // new-instance vAA, type@BBBB
    constexpr uint16_t INVOKE_DIRECT = 0x0070; // invoke-direct {vC..}, method@BBBB
    constexpr uint16_t INVOKE_VIRTUAL = 0x006E;// invoke-virtual {vC..}, method@BBBB
    constexpr uint16_t RETURN_VOID = 0x000E;   // return-void
    
    // Not implemented in this scope
    constexpr uint16_t NOP = 0x0000;
}

// ============================================================================
// Value Types (Extended for BATCH)
// ============================================================================

enum class ValueType {
    UNINITIALIZED,
    INT32,
    FLOAT,
    LONG,
    DOUBLE,
    STRING_REF,      // Reference to string pool
    OBJECT_REF,     // Reference to heap object
    NULL_REF,       // Explicit null
    REGISTER_UNSET  // Register not yet written
};

// A value in a register or stack location
struct Value {
    ValueType type = ValueType::REGISTER_UNSET;
    
    union {
        int32_t int_val = 0;
        float float_val;
        int64_t long_val;
        double double_val;
    };
    
    std::string string_val;       // For STRING_REF
    std::string object_class;     // For OBJECT_REF - class descriptor
    uint32_t object_id = 0;       // For OBJECT_REF - heap object ID
    uint32_t reference_id = 0;    // Unique reference ID
    
    bool is_null = false;
    
    static Value make_string(const std::string& str, uint32_t ref_id) {
        Value v;
        v.type = ValueType::STRING_REF;
        v.string_val = str;
        v.reference_id = ref_id;
        return v;
    }
    
    static Value make_object(uint32_t obj_id, const std::string& cls) {
        Value v;
        v.type = ValueType::OBJECT_REF;
        v.object_id = obj_id;
        v.object_class = cls;
        return v;
    }
    
    static Value make_int(int32_t val) {
        Value v;
        v.type = ValueType::INT32;
        v.int_val = val;
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
    json to_json() const;
};

// ============================================================================
// Register File (Task #2)
// ============================================================================

struct RegisterFile {
    uint32_t size = 0;
    std::vector<Value> registers;
    
    void initialize(uint32_t count) {
        size = count;
        registers.clear();
        registers.resize(count, Value::make_uninitialized());
    }
    
    void write(uint8_t reg, const Value& value) {
        if (reg < size) {
            registers[reg] = value;
        }
    }
    
    Value read(uint8_t reg) const {
        if (reg < size) {
            return registers[reg];
        }
        return Value::make_uninitialized();
    }
    
    std::vector<uint8_t> get_written_registers() const {
        std::vector<uint8_t> written;
        for (uint8_t i = 0; i < size; ++i) {
            if (registers[i].type != ValueType::REGISTER_UNSET && 
                registers[i].type != ValueType::UNINITIALIZED) {
                written.push_back(i);
            }
        }
        return written;
    }
    
    json dump() const {
        json result;
        result["size"] = size;
        result["registers"] = json::array();
        
        for (uint8_t i = 0; i < size; ++i) {
            json reg_entry;
            reg_entry["register"] = "v" + std::to_string(i);
            reg_entry["value"] = registers[i].to_json();
            if (registers[i].type != ValueType::REGISTER_UNSET) {
                reg_entry["is_set"] = true;
            } else {
                reg_entry["is_set"] = false;
            }
            result["registers"].push_back(reg_entry);
        }
        
        return result;
    }
    
    std::map<std::string, Value> get_snapshot() const {
        std::map<std::string, Value> snapshot;
        for (uint8_t i = 0; i < size; ++i) {
            snapshot["v" + std::to_string(i)] = registers[i];
        }
        return snapshot;
    }
};

// ============================================================================
// Object Heap (Task #3)
// ============================================================================

struct HeapObject {
    uint32_t object_id = 0;
    std::string class_descriptor;  // e.g., "Landroid/widget/TextView;"
    std::string readable_class;    // e.g., "android.widget.TextView"
    
    bool is_initialized = false;
    uint64_t creation_time = 0;    // Instruction sequence when created
    uint32_t creator_pc = 0;       // PC where new-instance was called
    
    // Reference to actual Android API stub (if applicable)
    std::shared_ptr<api::AndroidObject> api_object;
    
    json to_json() const {
        json obj;
        obj["object_id"] = object_id;
        obj["class_descriptor"] = class_descriptor;
        obj["readable_class"] = readable_class;
        obj["is_initialized"] = is_initialized;
        obj["creation_instruction"] = creation_time;
        obj["creator_pc"] = creator_pc;
        return obj;
    }
};

class ObjectHeap {
public:
    ObjectHeap() : next_object_id_(1) {}
    
    uint32_t allocate(const std::string& class_desc, uint32_t pc, uint64_t seq) {
        HeapObject obj;
        obj.object_id = next_object_id_++;
        obj.class_descriptor = class_desc;
        obj.readable_class = descriptor_to_readable(class_desc);
        obj.creation_time = seq;
        obj.creator_pc = pc;
        
        objects_[obj.object_id] = obj;
        return obj.object_id;
    }
    
    HeapObject* get(uint32_t object_id) {
        auto it = objects_.find(object_id);
        if (it != objects_.end()) {
            return &it->second;
        }
        return nullptr;
    }
    
    const HeapObject* get(uint32_t object_id) const {
        auto it = objects_.find(object_id);
        if (it != objects_.end()) {
            return &it->second;
        }
        return nullptr;
    }
    
    void set_api_object(uint32_t object_id, std::shared_ptr<api::AndroidObject> api_obj) {
        auto* obj = get(object_id);
        if (obj) {
            obj->api_object = api_obj;
        }
    }
    
    void mark_initialized(uint32_t object_id) {
        auto* obj = get(object_id);
        if (obj) {
            obj->is_initialized = true;
        }
    }
    
    size_t size() const { return objects_.size(); }
    
    json dump() const {
        json arr = json::array();
        for (const auto& pair : objects_) {
            arr.push_back(pair.second.to_json());
        }
        return arr;
    }
    
    std::vector<uint32_t> get_all_ids() const {
        std::vector<uint32_t> ids;
        for (const auto& pair : objects_) {
            ids.push_back(pair.first);
        }
        return ids;
    }

private:
    std::map<uint32_t, HeapObject> objects_;
    uint32_t next_object_id_;
    
    std::string descriptor_to_readable(const std::string& desc) const {
        if (desc.empty()) return desc;
        std::string result = desc;
        // Convert Landroid/widget/TextView; → android.widget.TextView
        if (result[0] == 'L' && result[result.size()-1] == ';') {
            result = result.substr(1, result.size() - 2);
        }
        // Replace / with .
        for (char& c : result) {
            if (c == '/') c = '.';
        }
        return result;
    }
};

// ============================================================================
// API Call Trace Entry (Task #7)
// ============================================================================

struct ApiCallTraceEntry {
    uint64_t sequence = 0;
    std::string api_class;         // e.g., "android.widget.TextView"
    std::string method;             // e.g., "setText"
    std::vector<std::string> arguments;
    std::string return_value;
    std::string status;             // "IMPLEMENTED", "STUBBED", "MISSING"
    uint32_t pc = 0;               // PC of invoking instruction
    
    json to_json() const {
        json entry;
        entry["sequence"] = sequence;
        entry["api"] = api_class + "." + method;
        entry["class"] = api_class;
        entry["method"] = method;
        entry["arguments"] = arguments;
        entry["return_value"] = return_value;
        entry["status"] = status;
        entry["pc"] = pc;
        return entry;
    }
};

// ============================================================================
// Object Creation Trace (Task #4)
// ============================================================================

struct ObjectCreationTraceEntry {
    uint64_t sequence = 0;
    std::string class_name;
    uint32_t object_id = 0;
    std::string status;             // "SUCCESS", "FAIL"
    uint32_t pc = 0;
    
    json to_json() const {
        json entry;
        entry["sequence"] = sequence;
        entry["class"] = class_name;
        entry["object_id"] = object_id;
        entry["status"] = status;
        entry["pc"] = pc;
        return entry;
    }
};

// ============================================================================
// Constructor Invocation Trace (Task #5)
// ============================================================================

struct ConstructorTraceEntry {
    uint64_t sequence = 0;
    std::string class_name;
    std::string constructor;        // "<init>"
    uint32_t object_id = 0;
    std::string status;             // "SUCCESS", "FAIL", "NOT_FOUND"
    uint32_t pc = 0;
    
    json to_json() const {
        json entry;
        entry["sequence"] = sequence;
        entry["class"] = class_name;
        entry["constructor"] = constructor;
        entry["object_id"] = object_id;
        entry["status"] = status;
        entry["pc"] = pc;
        return entry;
    }
};

// ============================================================================
// Failure Report Entry (Task #8)
// ============================================================================

struct FailureReportEntry {
    std::string type;               // "UNIMPLEMENTED_OPCODE", "MISSING_METHOD", etc.
    std::string details;
    uint16_t opcode = 0;
    uint32_t pc = 0;
    std::string severity;           // "ERROR", "WARNING"
    
    json to_json() const {
        json entry;
        entry["type"] = type;
        entry["details"] = details;
        entry["opcode_hex"] = "0x" + [this]() {
            std::ostringstream oss;
            oss << std::hex << std::setw(4) << std::setfill('0') << opcode;
            return oss.str();
        }();
        entry["pc_hex"] = "0x" + [this]() {
            std::ostringstream oss;
            oss << std::hex << pc;
            return oss.str();
        }();
        entry["severity"] = severity;
        return entry;
    }
};

// ============================================================================
// Instruction Trace Entry (Enhanced for BATCH)
// ============================================================================

struct InstructionTraceEntry {
    uint32_t sequence = 0;
    uint32_t pc_before = 0;
    uint32_t pc_after = 0;
    
    std::string opcode_name;
    uint16_t opcode_hex = 0;
    
    struct Operand {
        std::string name;
        std::string value;
        int64_t numeric_value = 0;
    };
    std::vector<Operand> operands;
    
    std::optional<std::string> resolved_string;
    
    enum class Status {
        SUCCESS,
        HALT_UNIMPLEMENTED,
        HALT_RETURN,
        CRASH_INVALID_STATE,
        HALT_EXPERIMENT_BOUNDARY
    };
    Status status = Status::SUCCESS;
    uint32_t cycles = 1;
    
    std::vector<std::string> registers_changed;
    std::map<std::string, Value> register_snapshots;
    
    std::optional<std::string> halt_reason;
    
    // BATCH-specific fields
    std::optional<uint32_t> created_object_id;      // For new-instance
    std::optional<std::string> invoked_method;       // For invoke-* 
    
    json to_json() const;
};

// ============================================================================
// Complete Execution Trace (EXP-003-BATCH Evidence)
// ============================================================================

struct BatchExecutionTrace {
    std::string experiment_id = "EXP-003-BATCH";
    std::string timestamp;
    
    // Method context
    std::string class_name;
    std::string method_name;
    std::string method_descriptor;
    
    // Initial/Final state
    uint32_t initial_pc = 0;
    uint32_t final_pc = 0;
    
    // All executed instructions
    std::vector<InstructionTraceEntry> instructions;
    
    // Register trace
    RegisterFile final_registers;
    std::vector<json> register_snapshots;  // Snapshot after each instruction
    
    // Object heap
    ObjectHeap object_heap;
    
    // API calls made during execution
    std::vector<ApiCallTraceEntry> api_calls;
    
    // Object creation log
    std::vector<ObjectCreationTraceEntry> object_creations;
    
    // Constructor invocations
    std::vector<ConstructorTraceEntry> constructor_calls;
    
    // Failures/Issues encountered
    std::vector<FailureReportEntry> failures;
    
    // Execution statistics
    uint32_t total_instructions_in_method = 0;
    uint32_t executed_instructions = 0;
    bool completed_successfully = false;
    std::string halt_reason;
    
    // Status
    enum class BatchStatus {
        PASS,
        PARTIAL,
        FAIL
    };
    BatchStatus status = BatchStatus::PASS;
    
    json to_full_report() const;
};

// ============================================================================
// Interpreter Configuration (Updated for BATCH)
// ============================================================================

struct BatchInterpreterConfig {
    bool verbose = false;
    bool debug_output = false;
    uint32_t max_instructions = 1000;
    bool stop_on_unimplemented = true;
    bool generate_trace = true;
    
    std::string experiment_scope = "EXP-003-BATCH";
    
    // Allowed opcodes for this batch
    std::vector<uint16_t> allowed_opcodes = {
        Opcodes::CONST_STRING,
        Opcodes::NEW_INSTANCE,
        Opcodes::INVOKE_DIRECT,
        Opcodes::INVOKE_VIRTUAL,
        Opcodes::RETURN_VOID
    };
    
    // API stub integration
    miniandroid::api::ApiRegistry* api_registry = nullptr;
};

// ============================================================================
// Main DEX Interpreter Class (EXP-003-BATCH)
// ============================================================================

/**
 * DEX Bytecode Interpreter - Minimal Execution Engine
 * 
 * EXP-003-BATCH Scope:
 *   - const-string (0x1A): Load string reference into register
 *   - new-instance (0x22): Create object on heap
 *   - invoke-direct (0x70): Call constructor directly
 *   - invoke-virtual (0x6E): Call virtual method
 *   - return-void (0x0E): Return from void method
 */
class DexInterpreterBatch {
public:
    DexInterpreterBatch();
    ~DexInterpreterBatch();
    
    /**
     * Execute method bytecode completely
     */
    BatchExecutionTrace execute(
        const MethodInfo& method,
        const std::vector<std::string>& strings,
        const std::vector<std::string>& types,
        const DexReport& dex_report,
        const BatchInterpreterConfig& config = BatchInterpreterConfig{}
    );
    
    /**
     * Execute with class resolver entry point
     */
    BatchExecutionTrace execute_entry_point(
        const EntryPoint& entry,
        const DexReport& dex_report,
        const BatchInterpreterConfig& config = BatchInterpreterConfig{}
    );
    
    // Accessors for post-execution analysis
    const RegisterFile& get_registers() const { return registers_; }
    const ObjectHeap& get_heap() const { return object_heap_; }
    std::string get_last_error() const { return last_error_; }
    bool was_successful() const { return !halted_ || halted_on_return_; }

private:
    // Core execution loop
    bool fetch_decode_execute(BatchExecutionTrace& trace, const BatchInterpreterConfig& config);
    uint16_t fetch_opcode(uint32_t pc);
    
    // Opcode implementations
    bool execute_const_string(uint32_t pc, InstructionTraceEntry& entry);
    bool execute_new_instance(uint32_t pc, InstructionTraceEntry& entry, 
                              const std::vector<std::string>& types);
    bool execute_invoke_direct(uint32_t pc, InstructionTraceEntry& entry,
                                const DexReport& dex_report);
    bool execute_invoke_virtual(uint32_t pc, InstructionTraceEntry& entry,
                                 const DexReport& dex_report);
    bool execute_return_void(uint32_t pc, InstructionTraceEntry& entry);
    
    // Unimplemented handler
    void handle_unimplemented(uint16_t opcode, uint32_t pc, InstructionTraceEntry& entry,
                               BatchExecutionTrace& trace);
    
    // Register operations (delegates to RegisterFile)
    void set_register(uint8_t reg, const Value& value);
    Value get_register(uint8_t reg) const;
    std::string register_name(uint8_t reg) const;
    
    // Method resolution helpers
    std::pair<std::string, std::string> resolve_method(uint16_t method_idx, 
                                                         const DexReport& dex_report) const;
    
    // Utility
    void log(const std::string& msg);
    std::string to_hex(uint32_t val) const;
    std::string to_hex16(uint16_t val) const;
    
    // State
    RegisterFile registers_;
    ObjectHeap object_heap_;
    std::vector<uint16_t> bytecode_;
    std::vector<std::string> strings_;
    std::vector<std::string> types_;  // Type descriptors for new-instance
    const DexReport* dex_report_ = nullptr;  // Current DEX report for method resolution
    uint32_t pc_ = 0;
    uint32_t code_offset_ = 0;
    
    uint32_t next_ref_id_ = 1;
    uint64_t instruction_sequence_ = 0;
    uint64_t api_call_sequence_ = 0;
    uint64_t object_creation_sequence_ = 0;
    uint64_t constructor_sequence_ = 0;
    
    bool halted_ = false;
    bool halted_on_return_ = false;
    std::string halt_reason_;
    std::string last_error_;
    
    // Current trace being built
    BatchExecutionTrace* current_trace_ = nullptr;
    const BatchInterpreterConfig* current_config_ = nullptr;
    
    bool verbose_ = false;
};

} // namespace dex
} // namespace miniandroid

#endif // MINIANDROID_DEX_INTERPRETER_BATCH_H
