/*
 * MiniAndroid Runtime v0.2 - Real Dalvik Execution Engine
 * EXP-030: Real Bytecode Execution
 * 
 * Complete Dalvik register machine implementation with:
 * - Full opcode execution (25+ opcodes)
 * - Method call stack (StackFrame)
 * - Object heap management
 * - API bridge integration
 * - Comprehensive evidence generation
 */

#ifndef MINIANDROID_REAL_DALVIK_ENGINE_H
#define MINIANDROID_REAL_DALVIK_ENGINE_H

#include "dex_parser.h"
#include "class_resolver.h"
#include "../runtime/runtime_metadata.h"
#include "../runtime/vtable_dispatch.h"
#include "../api/android_stubs.h"
#include <string>
#include <vector>
#include <map>
#include <stack>
#include <memory>
#include <cstdint>
#include <optional>
#include <functional>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <set>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace dalvik {

using json = nlohmann::json;
using Clock = std::chrono::high_resolution_clock;

// ============================================================================
// OPCODE DEFINITIONS — Complete Dalvik Instruction Set (EXP-030 Scope)
// ============================================================================

namespace Opcode {
    // Constants (10 opcodes)
    constexpr uint16_t NOP = 0x0000;
    constexpr uint16_t CONST_4 = 0x12;       // const/4 vAA, #+BBBB
    constexpr uint16_t CONST_16 = 0x13;      // const/16 vAA, #+BBBB
    constexpr uint16_t CONST = 0x14;         // const vAA, #+BBBBBBBB
    constexpr uint16_t CONST_HIGH16 = 0x15;  // const/high16 vAA, #+BBBB0000
    constexpr uint16_t CONST_WIDE = 0x16;    // const-wide vAA, #+BBBBBBBBBBBBBBBB
    constexpr uint16_t CONST_WIDE_16 = 0x18; // const-wide/16 vAA, #+BBBB
    constexpr uint16_t CONST_WIDE_32 = 0x19; // const-wide/32 vAA, #+BBBBBBBB
    constexpr uint16_t CONST_STRING = 0x1A;  // const-string vAA, string@BBBB
    constexpr uint16_t CONST_STRING_JUMBO = 0x1B; // const-string/jumbo vAA, string@BBBBBBBB
    constexpr uint16_t CONST_CLASS = 0x1C;   // const-class vAA, type@BBBB
    
    // Moves (11 opcodes)
    constexpr uint16_t MOVE = 0x01;          // move vA, vB
    constexpr uint16_t MOVE_FROM16 = 0x02;   // move/from16 vAA, vBBBB
    constexpr uint16_t MOVE_16 = 0x03;       // move/16 vAAAA, vBBBB
    constexpr uint16_t MOVE_WIDE = 0x04;     // move-wide vA, vB
    constexpr uint16_t MOVE_OBJECT = 0x07;   // move-object vA, vB
    constexpr uint16_t MOVE_OBJECT_FROM16 = 0x08; // move-object/from16 vAA, vBBBB
    constexpr uint16_t MOVE_OBJECT_16 = 0x09; // move-object/16 vAAAA, vBBBB
    constexpr uint16_t MOVE_RESULT = 0x0A;   // move-result vAA
    // EXP-037 Phase B (BLOCKER-021 FIX): Previous code had MOVE_RESULT_OBJECT
    // = 0x0B and MOVE_RESULT_WIDE = 0x0C — SWAPPED. Per AOSP:
    //   0x0a = move-result
    //   0x0b = move-result-wide
    //   0x0c = move-result-object
    // TinyMusicPlayer's onCreate hits 0x0c (move-result-object) at PC=6 and
    // was being dispatched to execute_move_result_wide handler (which doesn't
    // exist — falls through to "unimplemented").
    constexpr uint16_t MOVE_RESULT_WIDE = 0x0B;   // move-result-wide vAA
    constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C; // move-result-object vAA
    constexpr uint16_t MOVE_EXCEPTION = 0x0D; // move-exception vAA
    
    // Returns (4 opcodes)
    constexpr uint16_t RETURN_VOID = 0x0E;   // return-void {}
    constexpr uint16_t RETURN = 0x0F;        // return {} vAA
    constexpr uint16_t RETURN_WIDE = 0x10;   // return-wide {} vAA
    constexpr uint16_t RETURN_OBJECT = 0x11; // return-object {} vAA
    
    // Objects (3 opcodes)
    constexpr uint16_t INSTANCE_OF = 0x20;   // instance-of vA, vB, type@CCCC
    constexpr uint16_t CHECK_CAST = 0x1F;    // check-cast vAA, type@BBBB
    constexpr uint16_t NEW_INSTANCE = 0x22;  // new-instance vAA, type@BBBB
    constexpr uint16_t NEW_ARRAY = 0x23;     // new-array vA, vB, type@CCCC (EXP-038)
    constexpr uint16_t ARRAY_LENGTH = 0x21;  // array-length vA, vB

    // EXP-038 (BLOCKER-031): Array get/put opcodes (23x format)
    constexpr uint16_t AGET = 0x44;           // aget vAA, vBB, vCC
    constexpr uint16_t AGET_WIDE = 0x45;      // aget-wide vAA, vBB, vCC
    constexpr uint16_t AGET_OBJECT = 0x46;     // aget-object vAA, vBB, vCC
    constexpr uint16_t AGET_BOOLEAN = 0x47;    // aget-boolean vAA, vBB, vCC
    constexpr uint16_t AGET_BYTE = 0x48;      // aget-byte vAA, vBB, vCC
    constexpr uint16_t AGET_CHAR = 0x49;      // aget-char vAA, vBB, vCC
    constexpr uint16_t AGET_SHORT = 0x4A;     // aget-short vAA, vBB, vCC
    constexpr uint16_t APUT = 0x4B;           // aput vAA, vBB, vCC
    constexpr uint16_t APUT_WIDE = 0x4C;      // aput-wide vAA, vBB, vCC
    constexpr uint16_t APUT_OBJECT = 0x4D;    // aput-object vAA, vBB, vCC
    constexpr uint16_t APUT_BOOLEAN = 0x4E;   // aput-boolean vAA, vBB, vCC
    constexpr uint16_t APUT_BYTE = 0x4F;      // aput-byte vAA, vBB, vCC
    constexpr uint16_t APUT_CHAR = 0x50;      // aput-char vAA, vBB, vCC
    constexpr uint16_t APUT_SHORT = 0x51;     // aput-short vAA, vBB, vCC
    
    // Instance Field Operations (EXP-035: Field System Integration)
    constexpr uint16_t IGET = 0x52;          // iget vA, vB, field@CCCC
    constexpr uint16_t IGET_WIDE = 0x53;     // iget-wide vA, vB, field@CCCC
    constexpr uint16_t IGET_OBJECT = 0x54;   // iget-object vA, vB, field@CCCC
    constexpr uint16_t IGET_BOOLEAN = 0x55;  // iget-boolean vA, vB, field@CCCC
    constexpr uint16_t IGET_BYTE = 0x56;     // iget-byte vA, vB, field@CCCC
    constexpr uint16_t IGET_CHAR = 0x57;     // iget-char vA, vB, field@CCCC
    constexpr uint16_t IGET_SHORT = 0x58;    // iget-short vA, vB, field@CCCC
    constexpr uint16_t IPUT = 0x59;          // iput vA, vB, field@CCCC
    constexpr uint16_t IPUT_WIDE = 0x5A;     // iput-wide vA, vB, field@CCCC
    constexpr uint16_t IPUT_OBJECT = 0x5B;   // iput-object vA, vB, field@CCCC
    constexpr uint16_t IPUT_BOOLEAN = 0x5C;  // iput-boolean vA, vB, field@CCCC
    constexpr uint16_t IPUT_BYTE = 0x5D;     // iput-byte vA, vB, field@CCCC
    constexpr uint16_t IPUT_CHAR = 0x5E;     // iput-char vA, vB, field@CCCC
    constexpr uint16_t IPUT_SHORT = 0x5F;    // iput-short vA, vB, field@CCCC
    
    // Static Field Operations (EXP-035: Static Field Integration)
    constexpr uint16_t SGET = 0x60;          // sget vAA, field@BBBB
    constexpr uint16_t SGET_WIDE = 0x61;     // sget-wide vAA, field@BBBB
    constexpr uint16_t SGET_OBJECT = 0x62;   // sget-object vAA, field@BBBB
    constexpr uint16_t SGET_BOOLEAN = 0x63;  // sget-boolean vAA, field@BBBB
    constexpr uint16_t SGET_BYTE = 0x64;     // sget-byte vAA, field@BBBB
    constexpr uint16_t SGET_CHAR = 0x65;     // sget-char vAA, field@BBBB
    constexpr uint16_t SGET_SHORT = 0x66;    // sget-short vAA, field@BBBB
    constexpr uint16_t SPUT = 0x67;          // sput vAA, field@BBBB
    constexpr uint16_t SPUT_WIDE = 0x68;     // sput-wide vAA, field@BBBB
    constexpr uint16_t SPUT_OBJECT = 0x69;   // sput-object vAA, field@BBBB
    constexpr uint16_t SPUT_BOOLEAN = 0x6A;  // sput-boolean vAA, field@BBBB
    constexpr uint16_t SPUT_BYTE = 0x6B;     // sput-byte vAA, field@BBBB
    constexpr uint16_t SPUT_CHAR = 0x6C;     // sput-char vAA, field@BBBB
    constexpr uint16_t SPUT_SHORT = 0x6D;    // sput-short vAA, field@BBBB
    
    // Invokes (7 core opcodes)
    constexpr uint16_t INVOKE_VIRTUAL = 0x6E;    // invoke-virtual {vC..}, method@BBBB
    constexpr uint16_t INVOKE_SUPER = 0x6F;      // invoke-super {vC..}, method@BBBB
    constexpr uint16_t INVOKE_DIRECT = 0x70;     // invoke-direct {vC..}, method@BBBB
    constexpr uint16_t INVOKE_STATIC = 0x71;     // invoke-static {vC..}, method@BBBB
    constexpr uint16_t INVOKE_INTERFACE = 0x72;  // invoke-interface {vC..}, method@BBBB

    // EXP-038 (BLOCKER-030): invoke-*/range opcodes (3rc format)
    // These are used for method calls with many arguments (>5).
    constexpr uint16_t INVOKE_VIRTUAL_RANGE = 0x74;   // invoke-virtual/range {vCCCC..vNNNN}, meth@BBBB
    constexpr uint16_t INVOKE_SUPER_RANGE = 0x75;     // invoke-super/range
    constexpr uint16_t INVOKE_DIRECT_RANGE = 0x76;    // invoke-direct/range
    constexpr uint16_t INVOKE_STATIC_RANGE = 0x77;    // invoke-static/range
    constexpr uint16_t INVOKE_INTERFACE_RANGE = 0x78; // invoke-interface/range
    
    // Control flow (basic set)
    constexpr uint16_t GOTO = 0x28;           // goto +AA
    constexpr uint16_t GOTO_16 = 0x29;        // goto/16 +AAAA
    constexpr uint16_t GOTO_32 = 0x2A;        // goto/32 +AAAAAAAA
    // EXP-038 (BLOCKER-029): Fixed if-eqz/if-nez opcode values.
    // Per AOSP: if-eqz=0x38, if-nez=0x39, if-ltz=0x3a, if-gez=0x3b,
    // if-gtz=0x3c, if-lez=0x3d
    // Previous code had IF_EQZ=0x39 and IF_NEZ=0x3A — off by 1!
    constexpr uint16_t IF_EQZ = 0x38;         // if-eqz vAA, +BBBB
    constexpr uint16_t IF_NEZ = 0x39;         // if-nez vAA, +BBBB
    constexpr uint16_t IF_LTZ = 0x3A;         // if-ltz vAA, +BBBB
    constexpr uint16_t IF_GEZ = 0x3B;         // if-gez vAA, +BBBB
    constexpr uint16_t IF_GTZ = 0x3C;          // if-gtz vAA, +BBBB
    constexpr uint16_t IF_LEZ = 0x3D;          // if-lez vAA, +BBBB
    constexpr uint16_t IF_EQ = 0x32;          // if-eq vAA, vBB, +CCCC
    constexpr uint16_t IF_NE = 0x33;          // if-ne vAA, vBB, +CCCC
    // EXP-037 Phase B (BLOCKER-018): remaining if-* opcodes (22t format).
    // Without these, any code that does numeric comparison branching fails.
    constexpr uint16_t IF_LT = 0x34;          // if-lt vAA, vBB, +CCCC
    constexpr uint16_t IF_GE = 0x35;          // if-ge vAA, vBB, +CCCC
    constexpr uint16_t IF_GT = 0x36;          // if-gt vAA, vBB, +CCCC
    constexpr uint16_t IF_LE = 0x37;          // if-le vAA, vBB, +CCCC

    // EXP-038 (BLOCKER-028): Arithmetic 2addr opcodes (12x format)
    // These are heavily used in real Android bytecode for local variable math.
    constexpr uint16_t ADD_INT_2ADDR = 0xB0;    // add-int/2addr vA, vB
    constexpr uint16_t SUB_INT_2ADDR = 0xB1;    // sub-int/2addr vA, vB
    constexpr uint16_t MUL_INT_2ADDR = 0xB2;    // mul-int/2addr vA, vB
    constexpr uint16_t DIV_INT_2ADDR = 0xB3;    // div-int/2addr vA, vB
    constexpr uint16_t REM_INT_2ADDR = 0xB4;    // rem-int/2addr vA, vB
    constexpr uint16_t AND_INT_2ADDR = 0xB5;    // and-int/2addr vA, vB
    constexpr uint16_t OR_INT_2ADDR  = 0xB6;    // or-int/2addr vA, vB
    constexpr uint16_t XOR_INT_2ADDR = 0xB7;    // xor-int/2addr vA, vB
    constexpr uint16_t SHL_INT_2ADDR = 0xB8;    // shl-int/2addr vA, vB
    constexpr uint16_t SHR_INT_2ADDR = 0xB9;    // shr-int/2addr vA, vB
    constexpr uint16_t USHR_INT_2ADDR = 0xBA;   // ushr-int/2addr vA, vB

    // Arithmetic lit8 (22b format: AA|op BB|CC)
    constexpr uint16_t ADD_INT_LIT8 = 0xD8;     // add-int/lit8 vAA, vBB, #+CC
    constexpr uint16_t SUB_INT_LIT8 = 0xD9;     // sub-int/lit8 vAA, vBB, #+CC
    constexpr uint16_t MUL_INT_LIT8 = 0xDA;     // mul-int/lit8 vAA, vBB, #+CC
    constexpr uint16_t AND_INT_LIT8 = 0xDB;     // and-int/lit8 vAA, vBB, #+CC
    constexpr uint16_t OR_INT_LIT8  = 0xDC;     // or-int/lit8 vAA, vBB, #+CC
    constexpr uint16_t XOR_INT_LIT8 = 0xDD;     // xor-int/lit8 vAA, vBB, #+CC

    // Arithmetic lit16 (22s format: AA|op BBBB)
    constexpr uint16_t ADD_INT_LIT16 = 0xD0;    // add-int/lit16 vA, vB, #+BBBB
    constexpr uint16_t SUB_INT_LIT16 = 0xD1;     // rsub-int (reverse subtract)
    constexpr uint16_t MUL_INT_LIT16 = 0xD2;    // mul-int/lit16
    constexpr uint16_t DIV_INT_LIT16 = 0xD3;    // div-int/lit16
    constexpr uint16_t REM_INT_LIT16 = 0xD4;    // rem-int/lit16
    constexpr uint16_t AND_INT_LIT16 = 0xD5;    // and-int/lit16
    constexpr uint16_t OR_INT_LIT16  = 0xD6;    // or-int/lit16
    constexpr uint16_t XOR_INT_LIT16 = 0xD7;     // xor-int/lit16

    // Binary 23x format: AA|op BB|CC (3 registers)
    constexpr uint16_t ADD_INT = 0x90;          // add-int vAA, vBB, vCC
    constexpr uint16_t SUB_INT = 0x91;          // sub-int vAA, vBB, vCC
    constexpr uint16_t MUL_INT = 0x92;          // mul-int vAA, vBB, vCC
    constexpr uint16_t DIV_INT = 0x93;          // div-int vAA, vBB, vCC
    constexpr uint16_t REM_INT = 0x94;          // rem-int vAA, vBB, vCC
    constexpr uint16_t AND_INT = 0x95;          // and-int vAA, vBB, vCC
    constexpr uint16_t OR_INT  = 0x96;          // or-int vAA, vBB, vCC
    constexpr uint16_t XOR_INT = 0x97;          // xor-int vAA, vBB, vCC
}

// ============================================================================
// VALUE TYPES — Extended Register Value System
// ============================================================================

enum class DalvikType {
    UNINITIALIZED,
    INT32,
    INT64,      // Long
    FLOAT32,
    FLOAT64,    // Double
    STRING_REF,
    CLASS_REF,
    OBJECT_REF,
    NULL_REF,
    BOOLEAN,
    BYTE,
    SHORT,
    CHAR,
    VOID_,
    REGISTER_UNSET
};

struct DalvikValue {
    DalvikType type = DalvikType::REGISTER_UNSET;
    
    union {
        int32_t int_val = 0;
        int64_t long_val;
        float float_val;
        double double_val;
        bool bool_val;
        int8_t byte_val;
        int16_t short_val;
        char char_val;
    };
    
    // Reference types
    std::string string_val;       // For STRING_REF
    std::string class_desc;       // For CLASS_REF or OBJECT_REF
    uint32_t object_id = 0;       // For OBJECT_REF
    uint32_t ref_id = 0;          // Unique reference ID
    
    bool is_null = false;
    
    // Factory methods
    static DalvikValue make_int(int32_t val) {
        DalvikValue v; v.type = DalvikType::INT32; v.int_val = val; return v;
    }
    
    static DalvikValue make_long(int64_t val) {
        DalvikValue v; v.type = DalvikType::INT64; v.long_val = val; return v;
    }
    
    static DalvikValue make_string(const std::string& str, uint32_t id) {
        DalvikValue v; v.type = DalvikType::STRING_REF; 
        v.string_val = str; v.ref_id = id; return v;
    }
    
    static DalvikValue make_object(uint32_t obj_id, const std::string& cls) {
        DalvikValue v; v.type = DalvikType::OBJECT_REF;
        v.object_id = obj_id; v.class_desc = cls; return v;
    }
    
    static DalvikValue make_class(const std::string& desc, uint32_t id) {
        DalvikValue v; v.type = DalvikType::CLASS_REF;
        v.class_desc = desc; v.ref_id = id; return v;
    }
    
    static DalvikValue make_null() {
        DalvikValue v; v.type = DalvikType::NULL_REF; v.is_null = true; return v;
    }
    
    static DalvikValue make_uninit() {
        DalvikValue v; v.type = DalvikType::UNINITIALIZED; return v;
    }
    
    static DalvikValue make_void() {
        DalvikValue v; v.type = DalvikType::VOID_; return v;
    }
    
    static DalvikValue make_bool(bool b) {
        DalvikValue v; v.type = DalvikType::BOOLEAN; v.bool_val = b; return v;
    }
    
    std::string to_string() const;
    json to_json() const;
    
    bool is_integral() const {
        return type == DalvikType::INT32 || type == DalvikType::INT64 ||
               type == DalvikType::BOOLEAN || type == DalvikType::BYTE ||
               type == DalvikType::SHORT || type == DalvikType::CHAR;
    }
    
    bool is_reference() const {
        return type == DalvikType::STRING_REF || type == DalvikType::OBJECT_REF ||
               type == DalvikType::CLASS_REF || type == DalvikType::NULL_REF;
    }
};

// ============================================================================
// REGISTER FILE — Dalvik Virtual Machine Registers
// ============================================================================

class DexRegisterFile {
public:
    DexRegisterFile() : size_(0), pc_(0) {}
    
    void initialize(uint32_t count, uint32_t ins_count = 0) {
        size_ = count;
        ins_count_ = ins_count;
        registers_.clear();
        registers_.resize(count, DalvikValue::make_uninit());
        
        // Mark parameter registers (last N registers are 'p' registers)
        if (ins_count > 0 && ins_count < count) {
            param_start_ = count - ins_count;
        } else {
            param_start_ = count;
        }
    }
    
    void write_v(uint8_t reg, const DalvikValue& value) {
        if (reg < size_) {
            registers_[reg] = value;
            written_.insert(reg);
        }
    }
    
    void write_p(uint8_t param_idx, const DalvikValue& value) {
        uint8_t reg = param_start_ + param_idx;
        if (reg < size_) {
            registers_[reg] = value;
            written_.insert(reg);
        }
    }
    
    DalvikValue read_v(uint8_t reg) const {
        if (reg < size_) return registers_[reg];
        return DalvikValue::make_uninit();
    }
    
    DalvikValue read_p(uint8_t param_idx) const {
        uint8_t reg = param_start_ + param_idx;
        if (reg < size_) return registers_[reg];
        return DalvikValue::make_uninit();
    }
    
    void set_pc(uint32_t pc) { pc_ = pc; }
    uint32_t get_pc() const { return pc_; }
    
    uint32_t get_size() const { return size_; }
    uint32_t get_ins_count() const { return ins_count_; }
    
    std::vector<uint8_t> get_written_registers() const {
        return std::vector<uint8_t>(written_.begin(), written_.end());
    }
    
    json dump() const {
        json result;
        result["size"] = size_;
        result["ins_count"] = ins_count_;
        result["param_start"] = param_start_;
        result["pc"] = pc_;
        result["registers"] = json::array();
        
        for (uint8_t i = 0; i < size_; ++i) {
            json entry;
            bool is_param = (i >= param_start_);
            entry["name"] = is_param ? ("p" + std::to_string(i - param_start_)) 
                                     : ("v" + std::to_string(i));
            entry["index"] = i;
            entry["value"] = registers_[i].to_json();
            entry["written"] = (written_.count(i) > 0);
            result["registers"].push_back(entry);
        }
        return result;
    }
    
    std::map<std::string, DalvikValue> get_snapshot() const {
        std::map<std::string, DalvikValue> snap;
        for (uint8_t i = 0; i < size_; ++i) {
            bool is_param = (i >= param_start_);
            std::string name = is_param ? ("p" + std::to_string(i - param_start_)) 
                                       : ("v" + std::to_string(i));
            snap[name] = registers_[i];
        }
        return snap;
    }

private:
    uint32_t size_ = 0;
    uint32_t ins_count_ = 0;
    uint32_t param_start_ = 0;
    uint32_t pc_ = 0;
    std::vector<DalvikValue> registers_;
    std::set<uint8_t> written_;
};

// ============================================================================
// STACK FRAME — Method Call Context
// ============================================================================

struct StackFrame {
    uint32_t frame_id;
    std::string class_name;
    std::string method_name;
    std::string method_descriptor;
    std::string source_file;
    
    // Execution state
    uint32_t return_address = 0xFFFFFFFF;  // PC to return to
    uint32_t caller_pc = 0;                // PC of call instruction
    DalvikValue return_value;              // Return value register
    
    // Register file for this frame
    DexRegisterFile registers;
    
    // Method metadata
    uint32_t code_offset = 0;
    uint32_t bytecode_length = 0;
    uint32_t registers_size = 0;
    uint32_t ins_size = 0;
    uint32_t outs_size = 0;
    
    // Timing
    Clock::time_point enter_time;
    Clock::time_point exit_time;
    double duration_ms = 0;
    
    // Status
    enum class Status {
        ACTIVE,
        RETURNED,
        EXCEPTION_PENDING,
        HALTED
    } status = Status::ACTIVE;
    
    std::string halt_reason;
    
    json to_json() const {
        json frame;
        frame["frame_id"] = frame_id;
        frame["class"] = class_name;
        frame["method"] = method_name;
        frame["descriptor"] = method_descriptor;
        frame["return_address"] = std::string("0x") + 
            ([&]() { std::ostringstream o; o << std::hex << return_address; return o.str(); })();
        frame["caller_pc"] = caller_pc;
        frame["status"] = status == Status::ACTIVE ? "ACTIVE" :
                           status == Status::RETURNED ? "RETURNED" :
                           status == Status::EXCEPTION_PENDING ? "EXCEPTION" : "HALTED";
        frame["duration_ms"] = duration_ms;
        frame["registers"] = registers.dump();
        return frame;
    }
};

// ============================================================================
// HEAP OBJECT — Runtime Object Representation
// ============================================================================

struct HeapObject {
    uint32_t object_id = 0;
    std::string class_descriptor;   // Landroid/widget/TextView;
    std::string readable_class;     // android.widget.TextView
    
    bool initialized = false;
    uint64_t creation_sequence = 0;
    uint32_t creator_pc = 0;
    uint32_t creator_frame_id = 0;
    
    // Fields (simplified - would be full field table in production)
    std::map<std::string, DalvikValue> fields;
    
    // Bridge to Android API stub
    std::shared_ptr<api::AndroidObject> api_object;
    
    HeapObject() = default;
    
    HeapObject(uint32_t id, const std::string& desc, uint64_t seq, uint32_t pc, uint32_t frame)
        : object_id(id), class_descriptor(desc), creation_sequence(seq), 
          creator_pc(pc), creator_frame_id(frame) {
        readable_class = descriptor_to_readable(desc);
    }
    
    void set_field(const std::string& name, const DalvikValue& value) {
        fields[name] = value;
    }
    
    DalvikValue get_field(const std::string& name) const {
        auto it = fields.find(name);
        return (it != fields.end()) ? it->second : DalvikValue::make_uninit();
    }
    
    json to_json() const {
        json obj;
        obj["object_id"] = object_id;
        obj["class_descriptor"] = class_descriptor;
        obj["readable_class"] = readable_class;
        obj["initialized"] = initialized;
        obj["creation_sequence"] = creation_sequence;
        obj["creator_pc"] = creator_pc;
        obj["creator_frame_id"] = creator_frame_id;
        obj["field_count"] = fields.size();
        return obj;
    }

private:
    std::string descriptor_to_readable(const std::string& desc) const {
        if (desc.empty()) return desc;
        std::string result = desc;
        if (result[0] == 'L' && result.back() == ';') {
            result = result.substr(1, result.size() - 2);
        }
        for (char& c : result) { if (c == '/') c = '.'; }
        return result;
    }
};

// ============================================================================
// OBJECT HEAP — Dynamic Memory Management
// ============================================================================

class DalvikHeap {
public:
    DalvikHeap() : next_id_(1), alloc_sequence_(0) {}
    
    uint32_t allocate(const std::string& class_desc, uint32_t pc, uint32_t frame_id) {
        HeapObject obj(next_id_++, class_desc, alloc_sequence_++, pc, frame_id);
        objects_[obj.object_id] = obj;
        
        // Log allocation
        allocation_log_.push_back({
            {"object_id", obj.object_id},
            {"class", class_desc},
            {"pc", pc},
            {"frame_id", frame_id},
            {"sequence", alloc_sequence_ - 1}
        });
        
        return obj.object_id;
    }
    
    HeapObject* get(uint32_t id) {
        auto it = objects_.find(id);
        return (it != objects_.end()) ? &it->second : nullptr;
    }
    
    const HeapObject* get(uint32_t id) const {
        auto it = objects_.find(id);
        return (it != objects_.end()) ? &it->second : nullptr;
    }
    
    void mark_initialized(uint32_t id) {
        if (auto* obj = get(id)) obj->initialized = true;
    }
    
    void bind_api_object(uint32_t id, std::shared_ptr<api::AndroidObject> api_obj) {
        if (auto* obj = get(id)) obj->api_object = api_obj;
    }
    
    size_t size() const { return objects_.size(); }
    
    json dump() const {
        json arr = json::array();
        for (const auto& pair : objects_) {
            arr.push_back(pair.second.to_json());
        }
        return arr;
    }
    
    json get_allocation_log() const {
        return allocation_log_;
    }
    
    std::vector<uint32_t> get_all_ids() const {
        std::vector<uint32_t> ids;
        for (const auto& pair : objects_) ids.push_back(pair.first);
        return ids;
    }
    
    // EXP-035: Field access helpers
    bool has_object(uint32_t id) const {
        return objects_.find(id) != objects_.end();
    }
    
    std::optional<DalvikValue> get_object_field(uint32_t object_id, const std::string& field_name) const {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) {
            return std::nullopt;
        }
        
        DalvikValue val = it->second.get_field(field_name);
        if (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) {
            return std::nullopt;
        }
        return val;
    }
    
    bool set_object_field(uint32_t object_id, const std::string& field_name, const DalvikValue& value) {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) {
            return false;
        }
        it->second.set_field(field_name, value);
        return true;
    }

private:
    std::map<uint32_t, HeapObject> objects_;
    uint32_t next_id_;
    uint64_t alloc_sequence_;
    json allocation_log_;
};

// ============================================================================
// METHOD CALL STACK — Invocation Tracking
// ============================================================================

class CallStack {
public:
    CallStack() : next_frame_id_(1), max_depth_(0), current_depth_(0) {}
    
    void push_frame(StackFrame&& frame) {
        frame.frame_id = next_frame_id_++;
        frame.enter_time = Clock::now();
        
        stack_.push(std::move(frame));
        current_depth_ = stack_.size();
        if (current_depth_ > max_depth_) max_depth_ = current_depth_;
    }
    
    StackFrame pop_frame() {
        if (stack_.empty()) return StackFrame{};
        
        Frame frame = std::move(stack_.top());
        stack_.pop();
        
        frame.exit_time = Clock::now();
        frame.duration_ms = std::chrono::duration<double, std::milli>(
            frame.exit_time - frame.enter_time).count();
        frame.status = StackFrame::Status::RETURNED;
        
        completed_frames_.push_back(frame);
        current_depth_ = stack_.size();
        
        return frame;
    }
    
    StackFrame& top() { return stack_.top(); }
    const StackFrame& top() const { return stack_.top(); }
    
    bool empty() const { return stack_.empty(); }
    size_t depth() const { return stack_.size(); }
    size_t max_depth() const { return max_depth_; }
    
    const std::vector<StackFrame>& get_completed_frames() const { 
        return completed_frames_; 
    }
    
    json dump_current_stack() const {
        json arr = json::array();
        
        // Copy stack to vector (can't iterate stack easily in reverse)
        std::vector<const Frame*> frames;
        auto temp = stack_;
        while (!temp.empty()) {
            frames.push_back(&temp.top());
            temp.pop();
        }
        
        for (auto it = frames.rbegin(); it != frames.rend(); ++it) {
            arr.push_back((*it)->to_json());
        }
        
        return arr;
    }
    
    json dump_all_calls() const {
        json result;
        result["max_depth"] = max_depth_;
        result["total_calls"] = completed_frames_.size() + stack_.size();
        result["current_stack"] = dump_current_stack();
        result["completed_calls"] = json::array();
        for (const auto& f : completed_frames_) {
            result["completed_calls"].push_back(f.to_json());
        }
        return result;
    }

private:
    using Frame = StackFrame;
    std::stack<Frame> stack_;
    std::vector<Frame> completed_frames_;
    uint32_t next_frame_id_;
    size_t max_depth_;
    size_t current_depth_;
};

// ============================================================================
// INSTRUCTION TRACE — Per-Instruction Evidence
// ============================================================================

struct InstructionTrace {
    uint64_t sequence = 0;
    uint32_t pc_before = 0;
    uint32_t pc_after = 0;
    
    std::string opcode_name;
    uint16_t opcode_hex = 0;
    
    struct Operand {
        std::string name;
        std::string value;
        int64_t numeric = 0;
    };
    std::vector<Operand> operands;
    
    enum class Status {
        SUCCESS,
        UNIMPLEMENTED,
        HALT_RETURN,
        CRASH_ERROR,
        BRANCH_TAKEN,
        BRANCH_NOT_TAKEN
    };
    Status status = Status::SUCCESS;
    
    // State changes
    std::map<std::string, DalvikValue> registers_before;
    std::map<std::string, DalvikValue> registers_after;
    std::vector<std::string> changed_registers;
    
    // Side effects
    std::optional<uint32_t> allocated_object_id;
    std::optional<std::string> invoked_method;
    std::optional<DalvikValue> return_value;
    
    // Error info
    std::optional<std::string> error_message;
    // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): halt_reason was referenced by
    // execute_iget/iput/sget/sput-object handlers in dalvik_engine.cpp but was
    // never declared on this struct, breaking the build. Treat it as a peer
    // of error_message (used by the trace consumer for halt diagnostics).
    std::string halt_reason;
    
    // Timing
    double execution_us = 0;
    
    json to_json() const {
        json trace;
        trace["sequence"] = sequence;
        trace["pc_before"] = pc_before;
        trace["pc_after"] = pc_after;
        trace["opcode"] = opcode_name;
        trace["opcode_hex"] = "0x" + [this]() {
            std::ostringstream o; o << std::hex << std::setw(4) << std::setfill('0') << opcode_hex; return o.str();
        }();
        trace["status"] = status == Status::SUCCESS ? "SUCCESS" :
                         status == Status::UNIMPLEMENTED ? "UNIMPLEMENTED" :
                         status == Status::HALT_RETURN ? "RETURN" :
                         status == Status::CRASH_ERROR ? "ERROR" :
                         status == Status::BRANCH_TAKEN ? "BRANCH_TAKEN" : "BRANCH_NOT_TAKEN";
        trace["operands"] = json::array();
        for (const auto& op : operands) {
            trace["operands"].push_back({{"name", op.name}, {"value", op.value}});
        }
        trace["changed_registers"] = changed_registers;
        if (allocated_object_id) trace["allocated_object"] = *allocated_object_id;
        if (invoked_method) trace["invoked"] = *invoked_method;
        if (return_value) trace["return_value"] = return_value->to_json();
        if (error_message) trace["error"] = *error_message;
        trace["execution_us"] = execution_us;
        return trace;
    }
};

// ============================================================================
// API CALL TRACE — Android API Invocation Evidence
// ============================================================================

struct ApiCallTrace {
    uint64_t sequence = 0;
    std::string api_class;      // android.widget.TextView
    std::string method;          // setText
    std::string descriptor;      // (Ljava/lang/CharSequence;)V
    std::vector<std::string> arguments;
    std::string return_value;
    
    enum class Status {
        IMPLEMENTED,
        STUBBED,
        MISSING,
        ERROR
    };
    Status status = Status::STUBBED;
    
    uint32_t pc = 0;
    uint32_t frame_id = 0;
    double execution_us = 0;
    
    json to_json() const {
        json call;
        call["sequence"] = sequence;
        call["api"] = api_class + "." + method;
        call["class"] = api_class;
        call["method"] = method;
        call["descriptor"] = descriptor;
        call["arguments"] = arguments;
        call["return_value"] = return_value;
        call["status"] = status == Status::IMPLEMENTED ? "IMPLEMENTED" :
                        status == Status::STUBBED ? "STUBBED" :
                        status == Status::MISSING ? "MISSING" : "ERROR";
        call["pc"] = pc;
        call["frame_id"] = frame_id;
        call["execution_us"] = execution_us;
        return call;
    }
};

// ============================================================================
// EXECUTION RESULT — Complete Run Evidence
// ============================================================================

struct DalvikExecutionResult {
    std::string experiment_id = "EXP-030";
    std::string timestamp;
    std::string apk_name;
    std::string apk_sha256;
    
    // DEX report reference (non-owning pointer for execution)
    const dex::DexReport* dex_report = nullptr;
    
    // Entry point
    std::string main_class;
    std::string main_method;
    
    // Final state
    enum class FinalStatus {
        COMPLETED_SUCCESS,
        COMPLETED_PARTIAL,
        HALTED_UNIMPLEMENTED_OPCODE,
        HALTED_MISSING_METHOD,
        HALTED_API_ERROR,
        HALTED_STACK_OVERFLOW,
        CRASH_EXCEPTION
    };
    FinalStatus final_status = FinalStatus::COMPLETED_SUCCESS;
    std::string halt_reason;
    
    // Statistics
    uint64_t total_instructions_executed = 0;
    uint64_t total_opcodes_decoded = 0;
    double total_execution_ms = 0;
    
    // Components
    CallStack call_stack;
    DalvikHeap heap;
    
    // Traces
    std::vector<InstructionTrace> instruction_traces;
    std::vector<ApiCallTrace> api_call_traces;
    
    // Final register state (from top frame if exists)
    json final_registers;
    
    // Output artifacts
    std::string screenshot_path;
    std::string report_path;
    
    json to_full_report() const;
};

// ============================================================================
// MAIN DALVIK EXECUTION ENGINE
// ============================================================================

/**
 * Real Dalvik Bytecode Execution Engine
 * 
 * EXP-030 Implementation:
 * - Executes actual DEX bytecode instructions
 * - Maintains real register state
 * - Allocates objects on heap
 * - Tracks method invocations via call stack
 * - Bridges to Android API stubs
 */
class DalvikExecutionEngine {
public:
    DalvikExecutionEngine();
    ~DalvikExecutionEngine();

    // EXP-038 (BLOCKER-033): Set per-DEX raw data for correct method_idx resolution.
    // Call this before execute_apk() to enable per-DEX method resolution.
    void set_per_dex_raw_data(std::vector<std::vector<uint8_t>> data) {
        per_dex_raw_data_ = std::move(data);
        is_multidex_ = (per_dex_raw_data_.size() > 1);
    }

    // EXP-038 (BLOCKER-033): Build class→DEX index map from DexReport.
    // Must be called after dex_report is set and before execution begins.
    void build_class_dex_index(const dex::DexReport& report);
    
    /**
     * Execute APK through real DEX bytecode interpretation
     */
    DalvikExecutionResult execute_apk(
        const std::string& apk_path,
        const dex::DexReport& dex_report,
        bool verbose = false
    );

    /**
     * EXP-037 Phase B (BLOCKER-019): Execute APK with explicit activity class
     * name from the AndroidManifest.xml. This bypasses the class-name-scan
     * heuristic in execute_apk() which fails for obfuscated APKs (e.g.
     * TinyMusicPlayer uses La/a;, La/b;, etc.).
     *
     * `activity_class_name` is the manifest's main_activity in DEX type
     * descriptor form, e.g. "Lcom/martinmimigames/tinymusicplayer/Launcher;".
     * If empty, falls back to the scan-based heuristic.
     */
    DalvikExecutionResult execute_apk_with_activity(
        const std::string& apk_path,
        const dex::DexReport& dex_report,
        const std::string& activity_class_name,
        bool verbose = false
    );
    
    /**
     * Execute specific method from DEX report
     */
    DalvikExecutionResult execute_method(
        const dex::MethodInfo& method,
        const dex::DexReport& dex_report,
        const std::vector<DalvikValue>& args = {},
        bool verbose = false
    );
    
    /**
     * Access post-execution state
     */
    const CallStack& get_call_stack() const { return call_stack_; }
    const DalvikHeap& get_heap() const { return heap_; }
    std::string get_last_error() const { return last_error_; }
    
    // Configuration
    struct Config {
        bool verbose = false;
        bool debug_output = false;
        uint64_t max_instructions = 100000;
        bool stop_on_unimplemented = true;
        bool generate_trace = true;
        bool enable_api_bridge = true;
    };

    // EXP-039: Public access to config for ApplicationRuntime
    Config config_;

private:
    // EXP-038 (BLOCKER-033): Per-DEX raw data for correct method_idx resolution.
    // Stored in DalvikExecutionEngine (NOT in DexReport) to avoid memory layout
    // issues that cause SEGV when DexReport struct is modified.
    // Each entry is the raw bytes of a DEX file, used to resolve method_idx
    // using the correct per-DEX method_ids[] table.
    std::vector<std::vector<uint8_t>> per_dex_raw_data_;
    bool is_multidex_ = false;

    // EXP-038 (BLOCKER-033): Map class descriptor → source DEX index.
    // Built during execute_apk() by scanning dex_report.classes.
    std::map<std::string, uint32_t> class_to_dex_index_;

    // Core execution loop
    bool execute_method_internal(
        const std::string& class_name,
        const std::string& method_name,
        const std::string& descriptor,
        const std::vector<uint16_t>& bytecode,
        uint32_t registers_size,
        uint32_t ins_size,
        uint32_t outs_size,
        const std::vector<DalvikValue>& args,
        DalvikExecutionResult& result
    );

    // EXP-038 (BLOCKER-034): Recursive DEX method invocation.
    // Given a declaring_class and method_name, search the DEX for a matching
    // method with bytecode. If found, recursively call execute_method_internal()
    // and return true (with result stored in return_val).
    // If not found (framework method), return false and let the caller bridge
    // to the API stub layer.
    bool try_recursive_invoke(
        const std::string& declaring_class,
        const std::string& method_name,
        const std::vector<DalvikValue>& args,
        DalvikValue& return_val,
        DalvikExecutionResult& result
    );
    
    bool fetch_decode_execute(DalvikExecutionResult& result);
    uint16_t fetch_opcode(uint32_t pc) const;
    
    // Opcode implementations — Constants
    bool execute_const_4(uint32_t pc, InstructionTrace& trace);
    bool execute_const_16(uint32_t pc, InstructionTrace& trace);
    bool execute_const(uint32_t pc, InstructionTrace& trace);
    bool execute_const_string(uint32_t pc, InstructionTrace& trace);
    bool execute_const_class(uint32_t pc, InstructionTrace& trace);
    
    // Opcode implementations — Moves
    bool execute_move(uint32_t pc, InstructionTrace& trace);
    bool execute_move_object(uint32_t pc, InstructionTrace& trace);
    // EXP-038 (BLOCKER-026): move-object/from16 (0x08, format 22x)
    // Required by Telegram's LaunchActivity.onCreate() at PC=1.
    bool execute_move_object_from16(uint32_t pc, InstructionTrace& trace);
    bool execute_move_result(uint32_t pc, InstructionTrace& trace);
    bool execute_move_result_object(uint32_t pc, InstructionTrace& trace);
    
    // Opcode implementations — Objects
    bool execute_new_instance(uint32_t pc, InstructionTrace& trace);
    bool execute_check_cast(uint32_t pc, InstructionTrace& trace);
    bool execute_instance_of(uint32_t pc, InstructionTrace& trace);
    
    // EXP-035: Field System Integration - Instance Field Operations
    bool execute_iget(uint32_t pc, InstructionTrace& trace);
    bool execute_iget_object(uint32_t pc, InstructionTrace& trace);
    bool execute_iput(uint32_t pc, InstructionTrace& trace);
    bool execute_iput_object(uint32_t pc, InstructionTrace& trace);
    
    // EXP-035: Field System Integration - Static Field Operations  
    bool execute_sget(uint32_t pc, InstructionTrace& trace);
    bool execute_sget_object(uint32_t pc, InstructionTrace& trace);
    bool execute_sput(uint32_t pc, InstructionTrace& trace);
    bool execute_sput_object(uint32_t pc, InstructionTrace& trace);
    
    // EXP-035: Field resolution helper (connects to runtime_metadata.h)
    struct FieldResolution {
        std::string class_descriptor;
        std::string field_name;
        std::string field_type;
        uint32_t field_offset = 0;
        bool is_static = false;
        bool resolved = false;
        std::string error_message;
    };
    FieldResolution resolve_field(uint16_t field_idx);
    
    // Opcode implementations — Invokes
    bool execute_invoke_virtual(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    bool execute_invoke_direct(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    bool execute_invoke_static(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    bool execute_invoke_interface(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    // EXP-037 Phase B (BLOCKER-012): invoke-super — needed for super.onCreate()
    // calls. Real Android apps almost always call super.onCreate(bundle) as the
    // first instruction in their onCreate; without this handler, NO real app
    // can execute past its entry method's first instruction.
    bool execute_invoke_super(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    
    // Opcode implementations — Returns
    bool execute_return_void(uint32_t pc, InstructionTrace& trace);
    bool execute_return(uint32_t pc, InstructionTrace& trace);
    bool execute_return_object(uint32_t pc, InstructionTrace& trace);
    
    // Opcode implementations — Control flow
    bool execute_goto(uint32_t pc, InstructionTrace& trace);
    bool execute_if_eqz(uint32_t pc, InstructionTrace& trace);
    bool execute_if_nez(uint32_t pc, InstructionTrace& trace);
    // EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
    // (if-lt, if-ge, if-gt, if-le) — required for numeric comparisons.
    // Existing if-eq/if-ne are in a different file path (or unused).
    bool execute_if_lt(uint32_t pc, InstructionTrace& trace);
    bool execute_if_ge(uint32_t pc, InstructionTrace& trace);
    bool execute_if_gt(uint32_t pc, InstructionTrace& trace);
    bool execute_if_le(uint32_t pc, InstructionTrace& trace);
    // Also add if-eq/if-ne for completeness (22t format)
    bool execute_if_eq(uint32_t pc, InstructionTrace& trace);
    bool execute_if_ne(uint32_t pc, InstructionTrace& trace);
    
    // Unimplemented handler
    void handle_unimplemented(uint16_t opcode, uint32_t pc, InstructionTrace& trace);
    
    // Register access helpers
    void set_register(uint8_t reg, const DalvikValue& value);
    DalvikValue get_register(uint8_t reg) const;
    std::string register_name(uint8_t reg) const;
    
    // API bridge
    bool bridge_to_api(const std::string& class_name, const std::string& method,
                       const std::vector<DalvikValue>& args, DalvikValue& result,
                       ApiCallTrace::Status& status);
    
    // Utility
    void log(const std::string& msg);
    std::string to_hex(uint32_t val) const;
    std::string to_hex16(uint16_t val) const;
    int32_t read_signed_literal(uint16_t val) const;
    std::string get_timestamp() const;
    
    // State
    std::vector<uint16_t> bytecode_;
    const dex::DexReport* dex_report_ = nullptr;
    DexRegisterFile* current_registers_ = nullptr;
    CallStack call_stack_;
    DalvikHeap heap_;
    
    // EXP-035: Field System State
    // NOTE: DalvikValue is in miniandroid::dalvik (this namespace), not miniandroid::runtime.
    // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): corrected namespace reference; the
    // previous commit (3392b03 EXP-035) referenced runtime::DalvikValue which does
    // not exist, breaking the entire build since EXP-035.
    std::map<std::string, DalvikValue> static_field_storage_;  // key: "class_descriptor.field_name"
    std::map<std::string, std::shared_ptr<runtime::RuntimeClassInfo>> class_info_cache_;  // cached class metadata
    
    // EXP-035: VTable Dispatch State
    runtime::VirtualDispatcher vtable_dispatcher_;  // VTable-based method resolution
    
    uint32_t pc_ = 0;
    uint64_t instruction_sequence_ = 0;
    uint64_t api_call_sequence_ = 0;
    uint64_t object_sequence_ = 0;
    
    // EXP-035: Current execution context (for VTable evidence)
    std::string current_class_ = "<unknown>";
    std::string current_method_ = "<unknown>";
    // EXP-038 (BLOCKER-033): Current DEX index for per-DEX method resolution.
    uint32_t current_dex_index_ = 0;

    // EXP-038 (BLOCKER-033): Per-DEX method name resolution using raw DEX bytes.
    std::string resolve_method_name_for_dex(uint32_t method_idx, uint32_t dex_index) const;
    std::string resolve_method_class_for_dex(uint32_t method_idx, uint32_t dex_index) const;
    std::string read_dex_string_from_raw(const std::vector<uint8_t>& raw, uint32_t string_idx,
                                          const dex::DexHeader& hdr) const;
    
    bool halted_ = false;
    bool halted_on_return_ = false;
    std::string halt_reason_;
    std::string last_error_;
    
    DalvikExecutionResult* current_result_ = nullptr;
    // config_ moved to public section above
    
    bool verbose_ = false;
};

} // namespace dalvik
} // namespace miniandroid

#endif // MINIANDROID_REAL_DALVIK_ENGINE_H
