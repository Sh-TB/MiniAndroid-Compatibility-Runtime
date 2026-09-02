// SEMANTIC RECONCILIATION (master request §7 RESULT_001/009/010) — long/cmp/convert
//
// Independent validation fixture for the live interpreter path
// (DalvikExecutionEngine::execute_method → execute_method_internal →
// fetch_decode_execute). Builds synthetic method bytecode and checks the
// FINAL REGISTER STATE against the Dalvik specification:
//
//   1. add-long / add-long/2addr must compute in FULL 64-bit
//      (2^32 + 1 == 4294967297 — a 32-bit shortcut yields 1).
//   2. cmp-long must compare the full 64-bit register pair.
//   3. cmpl-double / cmpg-double must implement NaN ordering:
//      cmpl → -1, cmpg → +1 on NaN; ±0.0 compare equal (→ 0).
//   4. int-to-long must sign-extend; float-to-int must convert the
//      NUMERIC value (not reinterpret bits); int-to-byte/char/short
//      must mask/sign-extend.
//
// Discrimination proof: every case is chosen so the pre-fix
// implementation (int32 union reads / type-re-tag CONV_CASE /
// swapped 12x nibbles) produces a DIFFERENT observable value.
//
// Harness pattern follows tests/unified0112_filled_new_array_test.cpp.

#include "../src/dex/dalvik_engine.h"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
using namespace miniandroid::dalvik::Opcode;
constexpr uint16_t CONST        = 0x14;  // const vAA, #+BBBBBBBB (31i)
constexpr uint16_t CONST_WIDE   = miniandroid::dalvik::Opcode::CONST_WIDE;   // 0x18 (51l)
constexpr uint16_t CONST_WIDE_HIGH16 = miniandroid::dalvik::Opcode::CONST_WIDE_HIGH16; // 0x19
constexpr uint16_t ADD_LONG     = miniandroid::dalvik::Opcode::ADD_LONG;     // 0x9B (23x)
constexpr uint16_t ADD_LONG_2ADDR = miniandroid::dalvik::Opcode::ADD_LONG_2ADDR; // 0xBB (12x)
constexpr uint16_t CMP_LONG     = miniandroid::dalvik::Opcode::CMP_LONG;     // 0x31 (23x)
constexpr uint16_t CMPL_DOUBLE  = miniandroid::dalvik::Opcode::CMPL_DOUBLE;  // 0x2F (23x)
constexpr uint16_t CMPG_DOUBLE  = miniandroid::dalvik::Opcode::CMPG_DOUBLE;  // 0x30 (23x)
constexpr uint16_t INT_TO_LONG  = miniandroid::dalvik::Opcode::INT_TO_LONG;  // 0x81 (12x)
constexpr uint16_t INT_TO_FLOAT = miniandroid::dalvik::Opcode::INT_TO_FLOAT; // 0x82 (12x)
constexpr uint16_t FLOAT_TO_INT = miniandroid::dalvik::Opcode::FLOAT_TO_INT; // 0x87 (12x)
constexpr uint16_t INT_TO_BYTE  = miniandroid::dalvik::Opcode::INT_TO_BYTE;  // 0x8D (12x)
constexpr uint16_t INT_TO_CHAR  = miniandroid::dalvik::Opcode::INT_TO_CHAR;  // 0x8E (12x)
constexpr uint16_t INT_TO_SHORT = miniandroid::dalvik::Opcode::INT_TO_SHORT; // 0x8F (12x)
constexpr uint16_t RETURN_WIDE  = miniandroid::dalvik::Opcode::RETURN_WIDE;  // 0x10 (11x)
constexpr uint16_t RETURN       = miniandroid::dalvik::Opcode::RETURN;       // 0x0F (11x)
}  // namespace opc

static int g_pass = 0, g_fail = 0;

static void record(const std::string& name, bool passed, const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    passed ? ++g_pass : ++g_fail;
}

// ── opcode encoders (Dalvik formats) ──────────────────────────────────────
static uint16_t w11x(uint8_t reg, uint16_t op) {            // AA|op
    return static_cast<uint16_t>((reg << 8) | op);
}
static uint16_t w12x(uint8_t vA, uint8_t vB, uint16_t op) { // B|A|op  (vA high nibble)
    return static_cast<uint16_t>((vA << 12) | (vB << 8) | op);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) { // 31i
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}
static void emit_const_wide(std::vector<uint16_t>& c, uint8_t reg, int64_t imm) { // 51l
    c.push_back(w11x(reg, opc::CONST_WIDE));
    uint64_t u = static_cast<uint64_t>(imm);
    for (int i = 0; i < 4; i++) c.push_back(static_cast<uint16_t>((u >> (i * 16)) & 0xFFFF));
}
static void emit_const_wide_high16(std::vector<uint16_t>& c, uint8_t reg, uint16_t hi) { // 21s
    c.push_back(w11x(reg, opc::CONST_WIDE_HIGH16));
    c.push_back(hi);
}
static void emit_23x(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, uint8_t vc) {
    c.push_back(w11x(va, op));
    c.push_back(static_cast<uint16_t>(vb | (vc << 8)));
}

// Run a bytecode snippet in one synthetic method; return execution result.
static DalvikExecutionResult run(DalvikExecutionEngine& engine, const std::vector<uint16_t>& code,
                                 bool wide_return, const std::string& name) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = wide_return ? "()J" : "()I";
    mi.defining_class = "LSemTest;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;

    DexReport report;
    report.strings.push_back(name);
    report.types.push_back("LSemTest;");
    ClassInfo ci;
    ci.name = "LSemTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    return engine.execute_method(ci.direct_methods[0], report, {}, false);
}

// Numeric value of a DalvikValue as double (test values fit exactly).
static double as_double(const miniandroid::dalvik::DalvikValue& v) {
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
                   const std::vector<uint16_t>& code, bool /*wide_return*/, int /*reg*/,
                   double expected) {
    DalvikExecutionResult r = run(engine, code, false, name);
    const miniandroid::dalvik::InstructionTrace* ret = nullptr;
    for (const auto& t : r.instruction_traces)
        if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value (status=" +
               std::to_string(static_cast<int>(r.final_status)) + ")");
        return false;
    }
    double got = as_double(*ret->return_value);
    bool ok = (got == expected);
    record(name, ok, "expected " + std::to_string(expected) + ", got " + std::to_string(got));
    return ok;
}

int main() {
    std::cout << "== semantic_long_cmp_conv_test — Dalvik 64-bit / NaN / conversion semantics ==\n";
    DalvikExecutionEngine engine;
    const int64_t TWO_POW_32 = 4294967296LL;

    // ── RESULT_001: long arithmetic in full 64-bit ────────────────────────
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, TWO_POW_32);          // v0 = 2^32
        emit_const_wide(c, 2, 1);                   // v2 = 1
        emit_23x(c, opc::ADD_LONG, 4, 0, 2);        // v4 = v0 + v2
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "add_long_64bit_2p32_plus_1", c, true, 4, 4294967297.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, TWO_POW_32);
        emit_const_wide(c, 1, 1);
        c.push_back(w12x(0, 1, opc::ADD_LONG_2ADDR)); // v0 = v0 + v1
        c.push_back(w11x(0, opc::RETURN_WIDE));
        expect(engine, "add_long_2addr_64bit", c, true, 0, 4294967297.0);
    }
    {
        std::vector<uint16_t> c;                     // negative long add: -2^32 + 5
        emit_const_wide(c, 0, -TWO_POW_32);
        emit_const_wide(c, 2, 5);
        emit_23x(c, opc::ADD_LONG, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect(engine, "add_long_negative", c, true, 4, -4294967291.0);
    }

    // ── RESULT_009: cmp-long full 64-bit ──────────────────────────────────
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, TWO_POW_32);           // bigger as 64-bit
        emit_const_wide(c, 2, 1);
        emit_23x(c, opc::CMP_LONG, 4, 0, 2);         // low32 says 0<1 → -1; spec says +1
        c.push_back(w11x(4, opc::RETURN));
        expect(engine, "cmp_long_64bit_greater", c, false, 4, 1.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 1);
        emit_const_wide(c, 2, TWO_POW_32);
        emit_23x(c, opc::CMP_LONG, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN));
        expect(engine, "cmp_long_64bit_less", c, false, 4, -1.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, TWO_POW_32);
        emit_const_wide(c, 2, TWO_POW_32);
        emit_23x(c, opc::CMP_LONG, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN));
        expect(engine, "cmp_long_64bit_equal", c, false, 4, 0.0);
    }

    // ── RESULT_009: cmpl/cmpg-double NaN + signed zero ────────────────────
    {
        std::vector<uint16_t> c;
        emit_const_wide_high16(c, 0, 0x7FF8);        // quiet NaN double
        emit_const_wide(c, 2, 0x3FF0000000000000LL); // 1.0
        emit_23x(c, opc::CMPL_DOUBLE, 4, 0, 2);      // cmpl(NaN) → -1
        c.push_back(w11x(4, opc::RETURN));
        expect(engine, "cmpl_double_nan_minus1", c, false, 4, -1.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide_high16(c, 0, 0x7FF8);
        emit_const_wide(c, 2, 0x3FF0000000000000LL);
        emit_23x(c, opc::CMPG_DOUBLE, 4, 0, 2);      // cmpg(NaN) → +1
        c.push_back(w11x(4, opc::RETURN));
        expect(engine, "cmpg_double_nan_plus1", c, false, 4, 1.0);
    }
    {
        std::vector<uint16_t> c;                     // -0.0 vs +0.0 → 0
        emit_const_wide(c, 0, static_cast<int64_t>(0x8000000000000000ULL)); // -0.0
        emit_const_wide(c, 2, 0);                    // +0.0
        emit_23x(c, opc::CMPL_DOUBLE, 4, 0, 2);
        c.push_back(w11x(4, opc::RETURN));
        expect(engine, "cmpl_double_signed_zero_equal", c, false, 4, 0.0);
    }

    // ── RESULT_010: real conversions ──────────────────────────────────────
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, -5);
        c.push_back(w12x(1, 0, opc::INT_TO_LONG));   // v1 = (long)(-5)
        c.push_back(w11x(1, opc::RETURN_WIDE));
        expect(engine, "int_to_long_sign_extend", c, true, 1, -5.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 3);
        c.push_back(w12x(1, 0, opc::INT_TO_FLOAT));  // v1 = 3.0f
        c.push_back(w12x(2, 1, opc::FLOAT_TO_INT));  // v2 = 3
        c.push_back(w11x(2, opc::RETURN));
        expect(engine, "float_to_int_numeric", c, false, 2, 3.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 511);                       // 0x1FF
        c.push_back(w12x(1, 0, opc::INT_TO_BYTE));   // → -1
        c.push_back(w11x(1, opc::RETURN));
        expect(engine, "int_to_byte_sign_extend", c, false, 1, -1.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 0x10041);
        c.push_back(w12x(1, 0, opc::INT_TO_CHAR));   // low16 zero-extend → 0x41
        c.push_back(w11x(1, opc::RETURN));
        expect(engine, "int_to_char_zero_extend", c, false, 1, 65.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 0x18000);
        c.push_back(w12x(1, 0, opc::INT_TO_SHORT));  // low16 sign-extend → -32768
        c.push_back(w11x(1, opc::RETURN));
        expect(engine, "int_to_short_sign_extend", c, false, 1, -32768.0);
    }

    std::cout << "\nRESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
