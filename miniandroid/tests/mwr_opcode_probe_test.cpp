// S211 KNOWLEDGE-TRANSFER PROBE — the two dispatcher ABSENCES + the 32x direction law
//
// Covers exactly the residue named by the S211 coverage-gap audit:
//
//   1. move-wide/16 (0x06, 32x) — reported by Coder-D (#529 D-P0-5), claimed
//      harness-tested in Coder-3's S180 batch (#530 "P0-5"), but NEVER landed
//      on main. Pre-fix the opcode falls to handle_unimplemented, which (with
//      the default stop_on_unimplemented=false, dalvik_engine.h:2395) silently
//      CONTINUES, leaving the destination register stale — silent-wrong,
//      the exact failure class CONSTITUTION_V2 §17 forbids.
//
//   2. rem-double/2addr (0xCF, 12x) — never reviewed by any session: the
//      Opcode constant exists (PASS-3 K-37 corrected 0xCF→rem-double/2addr)
//      but NO dispatch case exists in the main switch; same silent-continue
//      residue. The 23x rem-double (0xAF) and the sibling rem-float/2addr
//      (0xCA) ARE dispatched — the family hole is only the /2addr double.
//
//   3. 32x direction law — in-engine inconsistency proof: execute_move_object_16
//      reads unit1 = vAAAA = DEST (AOSP-correct), while the MOVE_16 case reads
//      unit1 = src (AOSP-reversed). AOSP instruction-formats: 32x is
//      "op vAAAA, vBBBB" with A = destination, B = source for the move family.
//      The S180 batch's C3-N1 "move/16 direction" fix (#530) also never landed.
//      This probe ASSERTS the AOSP direction for move-wide/16 (the new case
//      follows move-object/16's convention) and DOCUMENTS the MOVE_16 residue
//      with a discriminating snippet printed as an informational row.
//
// Discrimination proof: every numbered case produces a DIFFERENT observable
// value pre-fix (0 / stale) vs post-fix (exact AOSP semantics).
//
// Harness pattern follows tests/semantic_long_cmp_conv_test.cpp.

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
constexpr uint16_t CONST_WIDE = miniandroid::dalvik::Opcode::CONST_WIDE;          // 0x18 (51l)
constexpr uint16_t CONST_WIDE_HIGH16 = miniandroid::dalvik::Opcode::CONST_WIDE_HIGH16; // 0x19 (21h)
constexpr uint16_t CONST = miniandroid::dalvik::Opcode::CONST;                    // 0x14 (31i)
constexpr uint16_t MOVE_WIDE_16 = 0x06;                                           // 32x
constexpr uint16_t MOVE_16 = miniandroid::dalvik::Opcode::MOVE_16;                // 0x03 (32x)
constexpr uint16_t REM_DOUBLE_2ADDR = miniandroid::dalvik::Opcode::REM_DOUBLE_2ADDR; // 0xCF (12x)
constexpr uint16_t RETURN_WIDE = miniandroid::dalvik::Opcode::RETURN_WIDE;        // 0x10 (11x)
constexpr uint16_t RETURN = miniandroid::dalvik::Opcode::RETURN;                  // 0x0F (11x)
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
static uint16_t w12x(uint8_t vA, uint8_t vB, uint16_t op) { // B|A|op (AOSP 12x)
    return static_cast<uint16_t>((vB << 12) | (vA << 8) | op);
}
static void emit_const_wide(std::vector<uint16_t>& c, uint8_t reg, int64_t imm) { // 51l
    c.push_back(w11x(reg, opc::CONST_WIDE));
    uint64_t u = static_cast<uint64_t>(imm);
    for (int i = 0; i < 4; i++) c.push_back(static_cast<uint16_t>((u >> (i * 16)) & 0xFFFF));
}
static void emit_const_wide_high16(std::vector<uint16_t>& c, uint8_t reg, uint16_t hi) { // 21h
    c.push_back(w11x(reg, opc::CONST_WIDE_HIGH16));
    c.push_back(hi);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) { // 31i
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}
static void emit_32x(std::vector<uint16_t>& c, uint16_t op, uint16_t vaaaa, uint16_t vbbbb) {
    c.push_back(op);
    c.push_back(vaaaa);
    c.push_back(vbbbb);
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

static double as_double(const miniandroid::dalvik::DalvikValue& v) {
    using T = miniandroid::dalvik::DalvikType;
    switch (v.type) {
        case T::INT32:   return static_cast<double>(v.int_val);
        case T::INT64:   return static_cast<double>(v.long_val);
        case T::FLOAT32: return static_cast<double>(v.float_val);
        case T::FLOAT64: return v.double_val;
        case T::BOOLEAN: return v.bool_val ? 1.0 : 0.0;
        default:         return 0;
    }
}

static bool expect(DalvikExecutionEngine& engine, const char* name,
                   const std::vector<uint16_t>& code, bool wide_return,
                   double expected) {
    DalvikExecutionResult r = run(engine, code, wide_return, name);
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
    std::cout << "== mwr_opcode_probe_test — move-wide/16 + rem-double/2addr + 32x direction law ==\n";
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 2000;

    // ── 1. move-wide/16 copies the FULL 64-bit pair ────────────────────────
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 3, 4294967297LL);         // v3:v4 = 2^32 + 1
        emit_32x(c, opc::MOVE_WIDE_16, 1, 3);        // v1:v2 = v3:v4 (AOSP: A=dest, B=src)
        c.push_back(w11x(1, opc::RETURN_WIDE));
        expect(engine, "move_wide_16_copies_64bit_pair", c, true, 4294967297.0);
    }
    // Pre-fix observed (recorded in the S211 KT issue): the same snippet
    // died in the unimplemented-opcode handler at the 0x06 site — no return
    // trace, final_status=1 ([UNIMPL-DIAG] dump shows units [0006] 0001 0003).

    // ── 2. rem-double/2addr = IEEE fmod (result takes the DIVIDEND sign) ───
    {
        std::vector<uint16_t> c;
        emit_const_wide_high16(c, 2, 0x401E);        // v2:v3 = 7.5
        emit_const_wide_high16(c, 4, 0x4000);        // v4:v5 = 2.0
        c.push_back(w12x(2, 4, opc::REM_DOUBLE_2ADDR)); // v2 = fmod(7.5, 2.0) = 1.5
        c.push_back(w11x(2, opc::RETURN_WIDE));
        expect(engine, "rem_double_2addr_fmod_basic", c, true, 1.5);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide_high16(c, 2, 0xC01E);        // v2:v3 = -7.5
        emit_const_wide_high16(c, 4, 0x4000);        // v4:v5 = 2.0
        c.push_back(w12x(2, 4, opc::REM_DOUBLE_2ADDR));
        c.push_back(w11x(2, opc::RETURN_WIDE));
        expect(engine, "rem_double_2addr_sign_takes_dividend", c, true, -1.5);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide_high16(c, 2, 0x401E);        // v2:v3 = 7.5
        emit_const_wide_high16(c, 4, 0xC000);        // v4:v5 = -2.0
        c.push_back(w12x(2, 4, opc::REM_DOUBLE_2ADDR));
        c.push_back(w11x(2, opc::RETURN_WIDE));
        expect(engine, "rem_double_2addr_negative_divisor", c, true, 1.5);
    }

    // ── 3. 32x direction law (informational on the un-fixed MOVE_16) ───────
    //
    // AOSP: move/16 vAAAA, vBBBB copies B → A. The current MOVE_16 case reads
    // unit1 as src and unit2 as dest (reversed) while execute_move_object_16
    // follows AOSP — the in-engine inconsistency is the C3-N1 finding. With
    // distinct register contents the reversed law copies the WRONG value:
    //
    //   const v3 = 111; const v5 = 222; move/16 v5, v3 → AOSP returns v5 = 111;
    //   reversed returns v5 = 222 (v3 clobbered with 222 instead).
    {
        std::vector<uint16_t> c;
        emit_const(c, 3, 111);
        emit_const(c, 5, 222);
        emit_32x(c, opc::MOVE_16, 5, 3);             // AOSP: v5 = v3 = 111
        c.push_back(w11x(5, opc::RETURN));
        expect(engine, "move_16_direction_aosp_law", c, false, 111.0);
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
