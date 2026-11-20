// w15_dalvik_lit_from16_law_test — #627 E-01/E-02 regression fence at the
// runtime level (raw-opcode probe, same harness pattern as the GP-582
// engine probe / S211 mwr_opcode_probe).
//
// Rows (each produces a DIFFERENT observable pre-fix vs post-fix):
//
//   E-02 lit-family — add-int/lit16 and mul-int/lit8 wrap (JLS 15.17.2 /
//   15.19 two's-complement semantics), and the INT32_MIN / -1 div/rem
//   edge is Java-defined (INT32_MIN, 0) instead of C++ UB (the old
//   b_val / lit with b_val=INT32_MIN, lit=-1 SIGFPE-traps on x86 — the
//   process died before any result existed).
//
//   E-01 /from16 family — move/from16 and move-wide/from16 carry a
//   16-BIT source register (22x AA|op BBBB, emitted for >255-register
//   methods). The pre-fix static_cast<uint8_t> aliased v256+ onto
//   v0..255; these rows place sentinels ABOVE v255 and assert they
//   arrive intact.
//
// Opcode encodings here follow the Dalvik formats table
// (source.android.com/docs/core/runtime/dalvik-bytecode): 22b lit8 =
// AA|op BB|CC, 22s lit16 = AA|op BBBBB, 22x from16 = AA|op BBBB,
// 21s const/16 = AA|op BBBBB.
#include "../src/dex/dalvik_engine_impl.h"

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
constexpr uint16_t CONST = miniandroid::dalvik::Opcode::CONST;              // 0x14 (31i)
constexpr uint16_t CONST_16 = 0x13;      // const/16 vAA, #+BBBB (21s)
constexpr uint16_t CONST_WIDE_16 = 0x16; // const-wide/16 vAA, #+BBBB (21s)
constexpr uint16_t CONST_HIGH16 = 0x15;  // const/high16 vAA, #+BBBB0000 (21h)
constexpr uint16_t MOVE_FROM16 = 0x02;   // move/from16 vAA, vBBBB (22x)
constexpr uint16_t MOVE_WIDE_FROM16 = 0x05; // move-wide/from16 (22x)
constexpr uint16_t RETURN = miniandroid::dalvik::Opcode::RETURN;            // 0x0F
constexpr uint16_t RETURN_WIDE = miniandroid::dalvik::Opcode::RETURN_WIDE;  // 0x10
constexpr uint16_t ADD_INT_LIT16 = 0xD0; // add-int/lit16 vAA, vBB, #+CCCC
constexpr uint16_t MUL_INT_LIT8 = 0xDA;  // mul-int/lit8 vAA, vBB, #+CC
constexpr uint16_t DIV_INT_LIT8 = 0xDB;  // div-int/lit8 vAA, vBB, #+CC
constexpr uint16_t REM_INT_LIT16 = 0xD4; // rem-int/lit16 vAA, vBB, #+CCCC
}  // namespace opc

static int g_pass = 0, g_fail = 0;

static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

static uint16_t w11x(uint8_t reg, uint16_t op) {
    return static_cast<uint16_t>((reg << 8) | op);
}

// 21h: AA|op / BBBB (const/high16).
static uint16_t w21h_lo(uint8_t reg, uint16_t op) {
    return static_cast<uint16_t>((reg << 8) | op);
}

// 22b/22s/22x all share the two-unit shape AA|op / operands.
static void emit_2u(std::vector<uint16_t>& c, uint16_t op, uint8_t vAA,
                    uint16_t operands) {
    c.push_back(static_cast<uint16_t>((vAA << 8) | op));
    c.push_back(operands);
}

static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) {
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}

// registers_size is a parameter: the /from16 rows need >256 registers.
static DalvikExecutionResult run(DalvikExecutionEngine& engine,
                                 const std::vector<uint16_t>& code,
                                 bool wide_return, const std::string& name,
                                 uint16_t registers_size,
                                 std::vector<DalvikValue> args = {},
                                 bool has_param = false) {
    MethodInfo mi;
    mi.name = name;
    // The /from16 rows take a WIDE PARAMETER: in a >255-register method the
    // only values that ever LIVE at v256+ are the incoming parameters (all
    // other A-format destinations are 8-bit by DEX format law) — the row
    // mirrors the real R8 shape.
    mi.descriptor = wide_return ? (has_param ? "(J)J" : "()J")
                                : (has_param ? "(I)I" : "()I");
    mi.defining_class = "LW15Test;";
    mi.registers_size = registers_size;
    mi.ins_size = has_param ? (wide_return ? 2 : 1) : 0;
    mi.outs_size = 5;
    mi.bytecode = code;

    DexReport report;
    report.strings.push_back(name);
    report.types.push_back("LW15Test;");
    ClassInfo ci;
    ci.name = "LW15Test;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    return engine.execute_method(ci.direct_methods[0], report, args, false);
}

static const miniandroid::dalvik::InstructionTrace* return_trace(
    const DalvikExecutionResult& r) {
    using S = miniandroid::dalvik::InstructionTrace::Status;
    for (const auto& t : r.instruction_traces)
        if (t.status == S::HALT_RETURN) return &t;
    return nullptr;
}

static void expect_int(DalvikExecutionEngine& engine, const char* name,
                       const std::vector<uint16_t>& code, int32_t expected,
                       uint16_t registers_size = 16,
                       std::vector<DalvikValue> args = {},
                       bool has_param = false) {
    DalvikExecutionResult r =
        run(engine, code, false, name, registers_size, args, has_param);
    const auto* ret = return_trace(r);
    if (!ret || !ret->return_value) {
        record(name, false,
               "no return trace/value (final_status=" +
                   std::to_string(static_cast<int>(r.final_status)) + ")");
        return;
    }
    int32_t got = ret->return_value->int_val;
    record(name, got == expected,
           "expected " + std::to_string(expected) + ", got " +
               std::to_string(got));
    if (got != expected) {
        for (const auto& t : r.instruction_traces)
            std::cout << "    trace: " << t.opcode_name << "\n";
    }
}

int main() {
    std::cout << "== w15_dalvik_lit_from16_law_test — #627 E-01/E-02 ==\n";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;

    // ── E-02: lit8/lit16 arithmetic (JLS-defined, UB pre-fix) ───────────
    // div-int/lit8 INT32_MIN / -1 = INT32_MIN (Java-defined; pre-fix the
    // raw C++ division SIGFPE-traps the process on x86).
    {
        std::vector<uint16_t> c;
        emit_const(c, 1, static_cast<int32_t>(0x80000000u));
        emit_2u(c, opc::DIV_INT_LIT8, 0,
                static_cast<uint16_t>((0xFF << 8) | 1));  // vBB=1, CC=-1
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "lit8_div_int32min_by_minus1_is_int32min", c,
                   static_cast<int32_t>(0x80000000u));
    }
    // rem-int/lit16 INT32_MIN % -1 = 0 (Java-defined; pre-fix UB).
    // 22s is the NIBBLE form B|A|op CCCC: vA (dest) = bits 8-11, vB
    // (src) = bits 12-15 — the encoding mirrors the 12x family rows.
    {
        std::vector<uint16_t> c;
        emit_const(c, 1, static_cast<int32_t>(0x80000000u));
        // rem-int/lit16 v2, v1, #-1  → (B=1)<<12 | (A=2)<<8 | 0xD4
        c.push_back(static_cast<uint16_t>((1u << 12) | (2u << 8) | 0xD4));
        c.push_back(static_cast<uint16_t>(0xFFFF));
        c.push_back(w11x(2, opc::RETURN));
        expect_int(engine, "lit16_rem_int32min_by_minus1_is_zero", c, 0);
    }
    // add-int/lit16 INT32_MAX + 1 wraps to INT32_MIN (two's-complement;
    // pre-fix signed-overflow UB). Nibble form: v2 = v1 + #+1.
    {
        std::vector<uint16_t> c;
        emit_const(c, 1, static_cast<int32_t>(0x7FFFFFFFu));
        c.push_back(static_cast<uint16_t>((1u << 12) | (2u << 8) | 0xD0));
        c.push_back(static_cast<uint16_t>(0x0001));
        c.push_back(w11x(2, opc::RETURN));
        expect_int(engine, "lit16_add_int32max_plus1_wraps_to_min", c,
                   static_cast<int32_t>(0x80000000u));
    }
    // mul-int/lit8 0x40000000 * 2 wraps to INT32_MIN (the mathematical
    // product 2^31 overflows; pre-fix C++ UB — gcc codegen happened to
    // produce the same bit pattern, but the behavior is now width-defined).
    {
        std::vector<uint16_t> c;
        emit_const(c, 1, static_cast<int32_t>(0x40000000u));
        emit_2u(c, opc::MUL_INT_LIT8, 0,
                static_cast<uint16_t>((0x02 << 8) | 1));  // vBB=1, CC=+2
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "lit8_mul_2_to_the_31_wraps_to_min", c,
                   static_cast<int32_t>(0x80000000u));
    }

    // ── W22 #627 E-05: const/high16 unsigned-width shift ────────────────
    // 21h law: vAA = (int32_t)((uint32_t)BBBB << 16). Pre-fix the shift ran
    // in signed width (BBBB >= 0x8000 is a negative int16 → C++17 UB, the
    // same family 19ee074a fixed for lit8/lit16 shl). Bit-pattern rows pin
    // both the sign-bit and the non-sign-bit cases (the old form usually
    // produced the right bits by accident — these rows keep it defined).
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0x8000));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_8000_is_0x80000000", c,
                   static_cast<int32_t>(0x80000000u));
    }
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0xABCD));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_abcd_is_0xabcd0000", c,
                   static_cast<int32_t>(0xABCD0000u));
    }
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0x7FFF));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_7fff_is_0x7fff0000", c,
                   static_cast<int32_t>(0x7FFF0000u));
    }
    // AUD-47 (#627 E-05 verification): the hub's "7/7 bit-exact" claim was
    // never published as named tests (only 3 vectors illustrated); these 4
    // rows complete the audit's reconstruction to a 7-vector engine-tested
    // set — both boundaries (0x0000/0x0001/0x7FFF below the sign bit,
    // 0x8000/0x8001/0xFFFF above it) plus the 0xABCD mid-range row above.
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0x0000));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_0000_is_0x00000000", c,
                   static_cast<int32_t>(0x00000000u));
    }
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0x0001));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_0001_is_0x00010000", c,
                   static_cast<int32_t>(0x00010000u));
    }
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0x8001));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_8001_is_0x80010000", c,
                   static_cast<int32_t>(0x80010000u));
    }
    {
        std::vector<uint16_t> c;
        c.push_back(w21h_lo(0, opc::CONST_HIGH16));
        c.push_back(static_cast<uint16_t>(0xFFFF));
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "const_high16_ffff_is_0xffff0000", c,
                   static_cast<int32_t>(0xFFFF0000u));
    }

    // ── E-01: /from16 16-bit source registers (>255-register methods) ──
    // AOSP-faithful shape: in a >255-register method the only values that
    // LIVE at v256+ are the incoming parameters (every other A-format
    // destination register field is 8 bits wide — const/16 v300 is not
    // encodable). The sentinel therefore rides the (I)I parameter, which
    // execute_method loads at v301 (registers_size 302, ins 1); the row
    // then brings it down with move/from16 — the exact R8 pattern the
    // pre-fix uint8_t cast broke (v301 aliased onto v45).
    {
        std::vector<uint16_t> c;
        // move/from16 v0, v301
        emit_2u(c, opc::MOVE_FROM16, 0, 301);
        c.push_back(w11x(0, opc::RETURN));
        expect_int(engine, "move_from16_reads_param_v301", c, 777,
                   /*registers_size=*/302, {DalvikValue::make_int(777)},
                   /*has_param=*/true);
    }
    // move-wide/from16: a (J)J method carries its wide parameter at
    // v300+v301; the row widens it down to v0/v1 and returns it.
    {
        std::vector<uint16_t> c;
        // move-wide/from16 v0, v300
        emit_2u(c, opc::MOVE_WIDE_FROM16, 0, 300);
        c.push_back(w11x(0, opc::RETURN_WIDE));
        DalvikExecutionResult r =
            run(engine, c, true, "move_wide_from16_reads_param_v300", 302,
                {DalvikValue::make_long(1234)}, /*has_param=*/true);
        const auto* ret = return_trace(r);
        if (!ret || !ret->return_value) {
            std::string tn;
            for (const auto& t : r.instruction_traces)
                tn += " " + t.opcode_name;
            record("move_wide_from16_reads_param_v300", false,
                   "no return trace/value (final_status=" +
                       std::to_string(static_cast<int>(r.final_status)) + ")"
                       + tn);
        } else {
            int64_t got = ret->return_value->type ==
                                  miniandroid::dalvik::DalvikType::INT64
                              ? ret->return_value->long_val
                              : ret->return_value->int_val;
            record("move_wide_from16_reads_param_v300", got == 1234,
                   "expected 1234, got " + std::to_string(got));
        }
    }

    std::cout << "  summary: " << g_pass << " passed, " << g_fail
              << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
