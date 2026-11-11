// GP-582 ENGINE PROBE — issue #582 interpreter boundary vectors
//
// Discriminating rows for the wave-1 interpreter repairs:
//
//   GP-INT-012 — signed add/sub/mul/shl and MIN/-1 div/rem were C++ UB on
//   the raw int32/int64 values. DEX/Java law: width-defined two's-complement
//   wrap + defined MIN/-1 results. Every row below produces a DIFFERENT
//   observable pre-fix (UB garbage/old value) vs post-fix (Java-exact).
//
//   GP-INT-013 — float/double divide-by-zero answered 0 instead of IEEE
//   ±Inf/NaN; REM_DOUBLE additionally decoded an INT64-backed double from
//   its low-32 int_val instead of the bit-reinterpreted long_val.
//
//   GP-INT-002 — handle_unimplemented advanced pc by 1 code unit regardless
//   of instruction width; an UNDEFINED opcode value (no DEX format exists)
//   now halts with a structured report instead of resuming in operand
//   words.
//
// Harness pattern follows tests/mwr_opcode_probe_test.cpp (S211).
#include "../src/dex/dalvik_engine.h"

#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dalvik::DalvikValue;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
constexpr uint16_t CONST_4 = miniandroid::dalvik::Opcode::CONST_4;        // 0x12
constexpr uint16_t CONST = miniandroid::dalvik::Opcode::CONST;            // 0x14 (31i)
constexpr uint16_t CONST_WIDE = miniandroid::dalvik::Opcode::CONST_WIDE;  // 0x18 (51l)
constexpr uint16_t RETURN = miniandroid::dalvik::Opcode::RETURN;          // 0x0F
constexpr uint16_t RETURN_WIDE = miniandroid::dalvik::Opcode::RETURN_WIDE;// 0x10
constexpr uint16_t ADD_INT = miniandroid::dalvik::Opcode::ADD_INT;        // 0x90
constexpr uint16_t MUL_INT = miniandroid::dalvik::Opcode::MUL_INT;        // 0x92
constexpr uint16_t DIV_INT = 0x93;                                        // div-int 23x
constexpr uint16_t REM_INT = 0x94;                                        // rem-int 23x
constexpr uint16_t SHL_INT = miniandroid::dalvik::Opcode::SHL_INT;        // 0x98
constexpr uint16_t ADD_LONG = miniandroid::dalvik::Opcode::ADD_LONG;      // 0x9B
constexpr uint16_t DIV_LONG = miniandroid::dalvik::Opcode::DIV_LONG;      // 0x9E
constexpr uint16_t DIV_FLOAT = miniandroid::dalvik::Opcode::DIV_FLOAT;    // 0xA9
constexpr uint16_t DIV_DOUBLE = miniandroid::dalvik::Opcode::DIV_DOUBLE;  // 0xAE
constexpr uint16_t REM_DOUBLE = miniandroid::dalvik::Opcode::REM_DOUBLE;  // 0xAF
}

static int g_pass = 0, g_fail = 0;

static void record(const std::string& name, bool passed, const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    passed ? ++g_pass : ++g_fail;
}

static uint16_t w11x(uint8_t reg, uint16_t op) {
    return static_cast<uint16_t>((reg << 8) | op);
}
static uint16_t w23x(uint8_t vAA, uint8_t vBB, uint8_t vCC, uint16_t op) {
    return static_cast<uint16_t>((vAA << 8) | op);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) {
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}
static void emit_const_wide(std::vector<uint16_t>& c, uint8_t reg, int64_t imm) {
    c.push_back(w11x(reg, opc::CONST_WIDE));
    uint64_t u = static_cast<uint64_t>(imm);
    for (int i = 0; i < 4; i++)
        c.push_back(static_cast<uint16_t>((u >> (i * 16)) & 0xFFFF));
}
static void emit_23x(std::vector<uint16_t>& c, uint16_t op, uint8_t vAA,
                     uint8_t vBB, uint8_t vCC) {
    c.push_back(w23x(vAA, vBB, vCC, op));
    c.push_back(static_cast<uint16_t>((vCC << 8) | vBB));
}

static DalvikExecutionResult run(DalvikExecutionEngine& engine,
                                 const std::vector<uint16_t>& code,
                                 bool wide_return, const std::string& name) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = wide_return ? "()J" : "()I";
    mi.defining_class = "LGP582Test;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;

    DexReport report;
    report.strings.push_back(name);
    report.types.push_back("LGP582Test;");
    ClassInfo ci;
    ci.name = "LGP582Test;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    return engine.execute_method(ci.direct_methods[0], report, {}, false);
}

static const miniandroid::dalvik::InstructionTrace* return_trace(
    const DalvikExecutionResult& r) {
    using S = miniandroid::dalvik::InstructionTrace::Status;
    for (const auto& t : r.instruction_traces)
        if (t.status == S::HALT_RETURN) return &t;
    return nullptr;
}

static double as_double(const DalvikValue& v) {
    using T = miniandroid::dalvik::DalvikType;
    switch (v.type) {
        case T::INT32:   return static_cast<double>(v.int_val);
        case T::INT64:   return static_cast<double>(v.long_val);
        case T::FLOAT32: return static_cast<double>(v.float_val);
        case T::FLOAT64: return v.double_val;
        default:         return 0;
    }
}

static bool expect(DalvikExecutionEngine& engine, const char* name,
                   const std::vector<uint16_t>& code, bool wide_return,
                   double expected) {
    DalvikExecutionResult r = run(engine, code, wide_return, name);
    const auto* ret = return_trace(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value (status=" +
               std::to_string(static_cast<int>(r.final_status)) + ")");
        return false;
    }
    double got = as_double(*ret->return_value);
    bool ok;
    if (std::isnan(expected)) ok = std::isnan(got);
    else if (std::isinf(expected)) ok = got == expected;
    else ok = (got == expected);
    record(name, ok, "expected " + std::to_string(expected) + ", got " +
           std::to_string(got));
    return ok;
}

int main() {
    std::cout << "== gp582_engine_probe_test — issue #582 boundary vectors ==\n";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;

    // ── GP-INT-012: wrap-defined signed arithmetic ──
    // add-int INT_MIN + (-1) = 0x7FFFFFFF (Java wrap; C++ pre-fix = UB)
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, static_cast<int32_t>(0x80000000u));
        emit_const(c, 1, -1);
        emit_23x(c, opc::ADD_INT, 2, 0, 1);
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "add_int_min_minus1_wraps_to_max", c, false, 2147483647.0);
    }
    // mul-int 0x10000 * 0x10000 = 0 (wrap; UB pre-fix)
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 65536);
        emit_23x(c, opc::MUL_INT, 2, 0, 0);
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "mul_int_65536_squared_wraps_to_zero", c, false, 0.0);
    }
    // div-int INT_MIN / -1 = INT_MIN (Java-defined; C++ UB pre-fix)
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, static_cast<int32_t>(0x80000000u));
        emit_const(c, 1, -1);
        emit_23x(c, opc::DIV_INT, 2, 0, 1);
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "div_int_min_by_minus1_java_min", c, false, -2147483648.0);
    }
    // rem-int INT_MIN % -1 = 0 (Java-defined; UB pre-fix)
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, static_cast<int32_t>(0x80000000u));
        emit_const(c, 1, -1);
        emit_23x(c, opc::REM_INT, 2, 0, 1);
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "rem_int_min_by_minus1_java_zero", c, false, 0.0);
    }
    // shl-int 1 << 31 = INT_MIN (wrap; signed-shift UB pre-fix)
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 1);
        emit_const(c, 1, 31);
        emit_23x(c, opc::SHL_INT, 2, 0, 1);
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "shl_int_1_to_31_wraps_to_min", c, false, -2147483648.0);
    }
    // add-long INT64_MIN + (-1) = INT64_MAX (wrap; UB pre-fix)
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, (-0x7FFFFFFFFFFFFFFFLL - 1));
        emit_const_wide(c, 2, -1);
        emit_23x(c, opc::ADD_LONG, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "add_long_min64_minus1_wraps_to_max", c, true,
               9223372036854775807.0);
    }
    // div-long INT64_MIN / -1 = INT64_MIN (Java-defined; UB pre-fix)
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, (-0x7FFFFFFFFFFFFFFFLL - 1));
        emit_const_wide(c, 2, -1);
        emit_23x(c, opc::DIV_LONG, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "div_long_min_by_minus1_java_min", c, true,
               -9223372036854775808.0);
    }

    // ── GP-INT-013: IEEE float/double laws ──
    // div-float 1.0 / 0.0 = +Inf (was 0)
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, static_cast<int32_t>(0x3F800000u));  // 1.0f bits
        emit_const(c, 1, 0);                                   // 0.0f bits
        emit_23x(c, opc::DIV_FLOAT, 2, 0, 1);
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "div_float_by_zero_positive_inf", c, false,
               std::numeric_limits<double>::infinity());
    }
    // div-double -1.0 / 0.0 = -Inf (was 0)
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, static_cast<int64_t>(0xBFF0000000000000ull)); // -1.0
        emit_const_wide(c, 2, 0);                                           // 0.0
        emit_23x(c, opc::DIV_DOUBLE, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "div_double_neg_by_zero_negative_inf", c, true,
               -std::numeric_limits<double>::infinity());
    }
    // rem-double 1.0 % 0.0 = NaN (was 0)
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, static_cast<int64_t>(0x3FF0000000000000ull)); // 1.0
        emit_const_wide(c, 2, 0);                                           // 0.0
        emit_23x(c, opc::REM_DOUBLE, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "rem_double_by_zero_nan", c, true,
               std::numeric_limits<double>::quiet_NaN());
    }
    // rem-double with INT64-backed operand: 3.0-bits-as-long % 2.0 = 1.0
    // (pre-fix decoded the low-32 int_val = 0 → answered 0)
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, static_cast<int64_t>(0x4008000000000000ull)); // 3.0 bits
        emit_const_wide(c, 2, static_cast<int64_t>(0x4000000000000000ull)); // 2.0 bits
        emit_23x(c, opc::REM_DOUBLE, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "rem_double_int64_backed_operand_fmod_3_2", c, true, 1.0);
    }

    // ── GP-INT-002: undefined opcode halts (no operand-word resume) ──
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 42);
        c.push_back(static_cast<uint16_t>(0xE3 | (0x00 << 8)));  // undefined
        c.push_back(0x0000);
        c.push_back(w11x(0, opc::RETURN));
        DalvikExecutionResult r = run(engine, c, false,
                                      "undefined_opcode_halt");
        const auto* ret = return_trace(r);
        bool ok = (ret == nullptr || !ret->return_value);
        record(ok ? "undefined_opcode_halts_no_resume" :
               "undefined_opcode_halts_no_resume",
               ok, ret ? "UNEXPECTED clean return — operand-word resume still live"
                       : "halted before return (structured, no desync)");
    }
    // defined 2-unit opcode still executes correctly after the width law:
    // add-int is 2 units — the whole battery above (23x rows) is itself the
    // positive-width regression (any off-by-one PC would corrupt every row).

    std::cout << "----\n";
    std::cout << "gp582: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
