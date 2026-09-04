// SEMANTIC RECONCILIATION 2 (master request PHASE 4/8) — switch / neg-not / div-zero / parse
//
// Independent discriminating fixture for the live interpreter path
// (DalvikExecutionEngine::execute_method → execute_method_internal →
// fetch_decode_execute). Covers the four remaining NOT_DONE runtime gaps:
//
//   GROUP S (K-18): packed-switch (0x2B) / sparse-switch (0x2C) must
//        dispatch through their payload tables. Pre-fix: handle_unimplemented.
//   GROUP N (NOT_DONE #4 audit): neg-int/not-int/neg-long/not-long/neg-double
//        (0x7B..0x80) were ABSENT from the opcode table AND the dispatch.
//   GROUP D (K-29): div/rem-long (and div/rem-int) by zero must throw
//        java/lang/ArithmeticException (pre-fix: yielded 0 — and div-int/2addr
//        was an unguarded C++ UB division).
//   GROUP P (K-19/K-20): Integer.parseInt / Long.parseLong / Float.parseFloat /
//        Double.parseDouble / String.substring / String.concat must be
//        dispatched through bridge_to_api (pre-fix: NOT implemented — the
//        exp018 "NATIVE_CPP" claim was a plan, never code).
//
// Discrimination proof: every case is chosen so the pre-fix engine produces a
// DIFFERENT observable result (unimplemented halt, wrong value, or VOID).
//
// Harness pattern follows tests/semantic_long_cmp_conv_test.cpp and
// tests/unified0113_typed_catch_test.cpp.

#include "../src/dex/dalvik_engine.h"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

namespace opc {
using namespace miniandroid::dalvik::Opcode;
// Header-defined constants (exist before and after this campaign):
constexpr uint16_t CONST          = 0x14;  // 31i
constexpr uint16_t CONST_WIDE     = 0x18;  // 51l
constexpr uint16_t CONST_STRING   = 0x1A;  // 21c
constexpr uint16_t CONST_4        = 0x12;  // 11n
constexpr uint16_t MOVE_RESULT        = 0x0A;
constexpr uint16_t MOVE_RESULT_WIDE   = 0x0B;
constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C;
constexpr uint16_t RETURN         = 0x0F;
constexpr uint16_t RETURN_WIDE    = 0x10;
constexpr uint16_t RETURN_OBJECT  = 0x11;
constexpr uint16_t PACKED_SWITCH  = 0x2B;  // 31t
constexpr uint16_t SPARSE_SWITCH  = 0x2C;  // 31t
constexpr uint16_t DIV_INT        = 0x93;  // 23x
constexpr uint16_t INT_TO_DOUBLE  = 0x83;  // 12x
constexpr uint16_t DIV_LONG       = 0x9E;  // 23x
constexpr uint16_t REM_LONG       = 0x9F;  // 23x
constexpr uint16_t L_REM_INT_LIT8 = 0xDC;  // 22b — PASS-3: corrected to AOSP rem-int/lit8 (was 0xDF under the +3-shifted table)
constexpr uint16_t INVOKE_STATIC  = 0x71;  // 35c
constexpr uint16_t INVOKE_VIRTUAL = 0x6E;  // 35c
// Local constants for the neg/not family — deliberately NOT taken from the
// Opcode namespace so this fixture compiles BOTH against the pre-fix header
// (where 0x7B..0x80 are absent) and the post-fix header:
constexpr uint16_t L_NEG_INT    = 0x7B;  // 12x
constexpr uint16_t L_NOT_INT    = 0x7C;  // 12x
constexpr uint16_t L_NEG_LONG   = 0x7D;  // 12x
constexpr uint16_t L_NOT_LONG   = 0x7E;  // 12x
constexpr uint16_t L_NEG_DOUBLE = 0x80;  // 12x
constexpr uint16_t NOP          = 0x00;
}  // namespace opc

static int g_pass = 0, g_fail = 0;

static void record(const std::string& name, bool passed, const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    passed ? ++g_pass : ++g_fail;
}

// ── opcode encoders (Dalvik formats) ──────────────────────────────────────
static uint16_t w11x(uint8_t reg, uint16_t op) { return static_cast<uint16_t>((reg << 8) | op); }
static uint16_t w12x(uint8_t vA, uint8_t vB, uint16_t op) {  // B|A|op (AOSP 12x)
    // vA = dest = bits 8-11, vB = src = bits 12-15.
    // DEMO-12X-NIBBLE (2026-09-04): previously encoded the swapped
    // convention; both sides now follow AOSP. w12x(dest, src, op).
    return static_cast<uint16_t>((vB << 12) | (vA << 8) | op);
}
static uint16_t const4(uint8_t reg, int8_t lit) {  // 11n
    return static_cast<uint16_t>((static_cast<uint16_t>(lit & 0xF) << 12) |
                                 (static_cast<uint16_t>(reg) << 8) | opc::CONST_4);
}
static void emit_const(std::vector<uint16_t>& c, uint8_t reg, int32_t imm) {  // 31i
    c.push_back(w11x(reg, opc::CONST));
    uint32_t u = static_cast<uint32_t>(imm);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}
static void emit_const_wide(std::vector<uint16_t>& c, uint8_t reg, int64_t imm) {  // 51l
    c.push_back(w11x(reg, opc::CONST_WIDE));
    uint64_t u = static_cast<uint64_t>(imm);
    for (int i = 0; i < 4; i++) c.push_back(static_cast<uint16_t>((u >> (i * 16)) & 0xFFFF));
}
static void emit_23x(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, uint8_t vc) {
    c.push_back(w11x(va, op));
    c.push_back(static_cast<uint16_t>(vb | (vc << 8)));
}
static void emit_22b(std::vector<uint16_t>& c, uint16_t op, uint8_t va, uint8_t vb, int8_t lit) {
    c.push_back(w11x(va, op));
    c.push_back(static_cast<uint16_t>(vb | (static_cast<uint16_t>(static_cast<uint8_t>(lit)) << 8)));
}
static void push_i32(std::vector<uint16_t>& c, int32_t v) {
    uint32_t u = static_cast<uint32_t>(v);
    c.push_back(static_cast<uint16_t>(u & 0xFFFF));
    c.push_back(static_cast<uint16_t>(u >> 16));
}
static void emit_31t(std::vector<uint16_t>& c, uint16_t op, uint8_t reg, int32_t offset) {
    c.push_back(w11x(reg, op));
    push_i32(c, offset);
}
static void emit_invoke(std::vector<uint16_t>& c, uint16_t op, uint8_t argc,
                        const std::vector<uint8_t>& regs, uint16_t method_idx) {
    uint16_t word0 = static_cast<uint16_t>((argc << 12) | op);
    uint16_t word2 = 0;
    for (int i = 0; i < 4 && i < static_cast<int>(regs.size()); ++i)
        word2 |= static_cast<uint16_t>(regs[static_cast<size_t>(i)] << (4 * i));
    c.push_back(word0);
    c.push_back(method_idx);
    c.push_back(word2);
}

// ── observation helpers ───────────────────────────────────────────────────
static const miniandroid::dalvik::InstructionTrace* find_return(
        const DalvikExecutionResult& r) {
    for (const auto& t : r.instruction_traces)
        if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) return &t;
    return nullptr;
}
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

// Run a snippet as LSemTest;.name()I-style method with a plain DexReport.
static DalvikExecutionResult run_plain(DalvikExecutionEngine& engine,
                                       const std::vector<uint16_t>& code,
                                       const std::string& desc,
                                       const std::string& name) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = desc;
    mi.defining_class = "LSemTest;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;

    DexReport report;
    report.strings.push_back("LSemTest;");
    report.types.push_back("LSemTest;");
    ClassInfo ci;
    ci.name = "LSemTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    return engine.execute_method(ci.direct_methods[0], report, {}, false);
}
// Run with a try-table attached (tries_data / tries_size on MethodInfo).
static DalvikExecutionResult run_with_tries(DalvikExecutionEngine& engine,
                                            const std::vector<uint16_t>& code,
                                            const std::vector<uint8_t>& tries_data,
                                            const std::string& name) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = "()I";
    mi.defining_class = "LSemTest;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;
    mi.tries_data = tries_data;
    mi.tries_size = 1;

    DexReport report;
    report.strings.push_back("LSemTest;");
    report.types.push_back("LSemTest;");
    report.types.push_back("Ljava/lang/ArithmeticException;");
    ClassInfo ci;
    ci.name = "LSemTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    return engine.execute_method(ci.direct_methods[0], report, {}, false);
}
// Run with a method_ids[] table so invoke-* can resolve class/name and fall
// through to bridge_to_api (the class is deliberately NOT in report.classes).
static DalvikExecutionResult run_invoke(DalvikExecutionEngine& engine,
                                        const std::vector<uint16_t>& code,
                                        const std::string& desc,
                                        const std::vector<std::string>& strings,
                                        const std::vector<std::string>& types,
                                        const std::string& name) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = desc;
    mi.defining_class = "LSemTest;";
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 5;
    mi.bytecode = code;

    DexReport report;
    report.strings = strings;
    report.types = types;
    // method_idx 0 → {class_idx=1, proto_idx=0, name_idx=2}
    report.method_ids.push_back(DexMethodId{1, 0, 2});
    ClassInfo ci;
    ci.name = "LSemTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);

    return engine.execute_method(ci.direct_methods[0], report, {}, false);
}

static bool expect_num(DalvikExecutionEngine& e, const char* name,
                       const std::vector<uint16_t>& code, const std::string& desc,
                       double expected) {
    DalvikExecutionResult r = run_plain(e, code, desc, name);
    const auto* ret = find_return(r);
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
static bool expect_num_invoke(DalvikExecutionEngine& e, const char* name,
                              const std::vector<uint16_t>& code, const std::string& desc,
                              const std::vector<std::string>& strings,
                              const std::vector<std::string>& types,
                              double expected) {
    DalvikExecutionResult r = run_invoke(e, code, desc, strings, types, name);
    const auto* ret = find_return(r);
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
static bool expect_str(DalvikExecutionEngine& e, const char* name,
                       const std::vector<uint16_t>& code,
                       const std::vector<std::string>& strings,
                       const std::vector<std::string>& types,
                       const std::string& expected) {
    DalvikExecutionResult r = run_invoke(e, code, "()Ljava/lang/String;", strings, types, name);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value (status=" +
               std::to_string(static_cast<int>(r.final_status)) + ")");
        return false;
    }
    std::string got = ret->return_value->string_val;
    bool ok = (got == expected);
    record(name, ok, "expected \"" + expected + "\", got \"" + got + "\"");
    return ok;
}

// try-table encoder (same encoding as tests/unified0113_typed_catch_test.cpp)
static void put_uleb(std::vector<uint8_t>& v, uint32_t val) {
    do { uint8_t b = val & 0x7F; val >>= 7; if (val) b |= 0x80; v.push_back(b); } while (val);
}
static void put_sleb(std::vector<uint8_t>& v, int32_t val) {
    bool more = true;
    while (more) {
        uint8_t b = val & 0x7F; val >>= 7;
        if ((val == 0 && !(b & 0x40)) || (val == -1 && (b & 0x40))) more = false;
        else b |= 0x80;
        v.push_back(b);
    }
}
static void append_try(std::vector<uint8_t>& tries_data, uint32_t start, uint16_t insn_count,
                       const std::vector<std::pair<uint32_t, uint32_t>>& typed,
                       int32_t catch_all_addr) {
    auto push_u16 = [&](uint16_t x) { tries_data.push_back(x & 0xFF); tries_data.push_back((x >> 8) & 0xFF); };
    auto push_u32 = [&](uint32_t x) { tries_data.push_back(x & 0xFF); tries_data.push_back((x >> 8) & 0xFF);
                                      tries_data.push_back((x >> 16) & 0xFF); tries_data.push_back((x >> 24) & 0xFF); };
    push_u32(start);
    push_u16(insn_count);
    push_u16(1);  // handler_off: list starts with the 1-byte uleb list_size
    put_uleb(tries_data, 1);
    int32_t enc_size = catch_all_addr >= 0 ? -static_cast<int32_t>(typed.size()) - 1
                                           : static_cast<int32_t>(typed.size());
    put_sleb(tries_data, enc_size);
    for (const auto& [t_idx, t_addr] : typed) { put_uleb(tries_data, t_idx); put_uleb(tries_data, t_addr); }
    if (catch_all_addr >= 0) put_uleb(tries_data, static_cast<uint32_t>(catch_all_addr));
}
// Typed-catch oracle: PASS only if the handler path produced `expected`.
static bool expect_caught(DalvikExecutionEngine& e, const char* name,
                          const std::vector<uint16_t>& code,
                          const std::vector<uint8_t>& tries_data, int expected) {
    DalvikExecutionResult r = run_with_tries(e, code, tries_data, name);
    const auto* ret = find_return(r);
    if (!ret || !ret->return_value) {
        record(name, false, "no return trace/value (status=" +
               std::to_string(static_cast<int>(r.final_status)) + ")");
        return false;
    }
    double got = as_double(*ret->return_value);
    bool ok = (got == static_cast<double>(expected));
    record(name, ok, "expected handler value " + std::to_string(expected) + ", got " + std::to_string(got));
    return ok;
}

int main() {
    std::cout << "== semantic_switch_parse_neg_test — switch / neg-not / div-zero / parse bridge ==\n";
    DalvikExecutionEngine engine;
    const int64_t TWO_POW_32 = 4294967296LL;
    const int T_ARITH = 1;  // type_idx for Ljava/lang/ArithmeticException; in run_with_tries

    // ── GROUP S (K-18): packed-switch ─────────────────────────────────────
    // pc0:  const/4 v0, X
    // pc1:  packed-switch v0, +19      (3 units → payload at pc20)
    // pc4:  const v1, 1009   (default) pc4-6
    // pc7:  return v1       (default exit)
    // pc8:  const v1, 1001   (key -2)  pc8-10
    // pc11: return v1
    // pc12: const v1, 1002   (key -1)  pc12-14
    // pc15: return v1
    // pc16: const v1, 1003   (key  0)  pc16-18
    // pc19: return v1
    // pc20: payload 0x0100, size=3, first_key=-2, targets={7,11,15} (rel pc1)
    auto packed_code = [](int8_t x) {
        std::vector<uint16_t> c;
        c.push_back(const4(0, x));
        emit_31t(c, opc::PACKED_SWITCH, 0, 19);
        emit_const(c, 1, 1009); c.push_back(w11x(1, opc::RETURN));   // default
        emit_const(c, 1, 1001); c.push_back(w11x(1, opc::RETURN));   // key -2
        emit_const(c, 1, 1002); c.push_back(w11x(1, opc::RETURN));   // key -1
        emit_const(c, 1, 1003); c.push_back(w11x(1, opc::RETURN));   // key  0
        c.push_back(0x0100);       // payload ident
        c.push_back(3);            // size
        push_i32(c, -2);           // first_key
        push_i32(c, 7);            // target for -2  → pc8
        push_i32(c, 11);           // target for -1  → pc12
        push_i32(c, 15);           // target for  0  → pc16
        return c;
    };
    expect_num(engine, "packed_switch_key0_hits_case",  packed_code(0),  "()I", 1003.0);
    expect_num(engine, "packed_switch_neg_key",         packed_code(-2), "()I", 1001.0);
    expect_num(engine, "packed_switch_default_falls",   packed_code(3),  "()I", 1009.0);

    // ── GROUP S (K-18): sparse-switch ─────────────────────────────────────
    // pc0:  const v0, X                (3 units)
    // pc3:  sparse-switch v0, +15      (3 units → payload at pc18)
    // pc6:  const v1, 2009   (default) pc6-8
    // pc9:  return v1
    // pc10: const v1, 2042   (key 42)  pc10-12
    // pc13: return v1
    // pc14: const v1, 2013   (key 900000) pc14-16
    // pc17: return v1
    // pc18: payload 0x0200, size=2, keys={42,900000}, targets={7,11} (rel pc3)
    auto sparse_code = [](int32_t x) {
        std::vector<uint16_t> c;
        emit_const(c, 0, x);
        emit_31t(c, opc::SPARSE_SWITCH, 0, 15);
        emit_const(c, 1, 2009); c.push_back(w11x(1, opc::RETURN));   // default
        emit_const(c, 1, 2042); c.push_back(w11x(1, opc::RETURN));   // key 42
        emit_const(c, 1, 2013); c.push_back(w11x(1, opc::RETURN));   // key 900000
        c.push_back(0x0200);
        c.push_back(2);
        push_i32(c, 42);
        push_i32(c, 900000);
        push_i32(c, 7);            // target for 42     → pc10
        push_i32(c, 11);           // target for 900000 → pc14
        return c;
    };
    expect_num(engine, "sparse_switch_key42",            sparse_code(42),       "()I", 2042.0);
    expect_num(engine, "sparse_switch_key_900000",       sparse_code(900000),   "()I", 2013.0);
    expect_num(engine, "sparse_switch_default_miss",     sparse_code(1),        "()I", 2009.0);
    expect_num(engine, "sparse_switch_default_negative", sparse_code(-1000000), "()I", 2009.0);

    // ── GROUP N: neg / not family (0x7B..0x80) ────────────────────────────
    {
        std::vector<uint16_t> c;
        c.push_back(const4(0, -7));
        c.push_back(w12x(1, 0, opc::L_NEG_INT));
        c.push_back(w11x(1, opc::RETURN));
        expect_num(engine, "neg_int_minus7", c, "()I", 7.0);
    }
    {
        std::vector<uint16_t> c;
        c.push_back(const4(0, 0));
        c.push_back(w12x(1, 0, opc::L_NOT_INT));
        c.push_back(w11x(1, opc::RETURN));
        expect_num(engine, "not_int_zero", c, "()I", -1.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, -2147483647 - 1);            // INT32_MIN
        c.push_back(w12x(1, 0, opc::L_NEG_INT));      // wraps to itself per JLS
        c.push_back(w11x(1, opc::RETURN));
        expect_num(engine, "neg_int_min_wraps", c, "()I", -2147483648.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, -5);
        c.push_back(w12x(2, 0, opc::L_NEG_LONG));
        c.push_back(w11x(2, opc::RETURN_WIDE));
        expect_num(engine, "neg_long_minus5", c, "()J", 5.0);
    }
    {
        std::vector<uint16_t> c;                       // not-long(2^32) — full 64-bit discriminator
        emit_const_wide(c, 0, TWO_POW_32);
        c.push_back(w12x(2, 0, opc::L_NOT_LONG));      // ~2^32 = 0xFFFFFFFF00000000 = -4294967297
        c.push_back(w11x(2, opc::RETURN_WIDE));
        expect_num(engine, "not_long_2p32", c, "()J", -4294967297.0);
    }
    {
        std::vector<uint16_t> c;
        emit_const(c, 0, 3);
        c.push_back(w12x(2, 0, opc::INT_TO_DOUBLE));   // v2 = 3.0 (FLOAT64)
        c.push_back(w12x(4, 2, opc::L_NEG_DOUBLE));    // v4 = -3.0
        c.push_back(w11x(4, opc::RETURN_WIDE));
        expect_num(engine, "neg_double_three", c, "()D", -3.0);
    }

    // ── GROUP D (K-29): division by zero → ArithmeticException ────────────
    // Layout (caught cases):
    //   pc0:  const-wide v0, 10        (5 units)
    //   pc5:  const-wide v2, 0         (5 units)
    //   pc10: div-long v4, v0, v2      (2 units)  ← try covers [10,12)
    //   pc12: const v1, 444            (fallthrough — the OLD buggy value)
    //   pc15: return v1
    //   pc16: const v1, 555            (handler — the CORRECT path)
    //   pc19: return v1
    auto div_long_code = [] {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 10);
        emit_const_wide(c, 2, 0);
        emit_23x(c, opc::DIV_LONG, 4, 0, 2);
        emit_const(c, 1, 444);
        c.push_back(w11x(1, opc::RETURN));
        emit_const(c, 1, 555);
        c.push_back(w11x(1, opc::RETURN));
        return c;
    };
    {
        std::vector<uint8_t> tries;
        append_try(tries, 10, 2, {{static_cast<uint32_t>(T_ARITH), 16}}, -1);
        expect_caught(engine, "div_long_zero_throws_typed", div_long_code(), tries, 555);
    }
    auto rem_long_code = [] {
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 10);
        emit_const_wide(c, 2, 0);
        emit_23x(c, opc::REM_LONG, 4, 0, 2);
        emit_const(c, 1, 445);
        c.push_back(w11x(1, opc::RETURN));
        emit_const(c, 1, 556);
        c.push_back(w11x(1, opc::RETURN));
        return c;
    };
    {
        std::vector<uint8_t> tries;
        append_try(tries, 10, 2, {{static_cast<uint32_t>(T_ARITH), 16}}, -1);
        expect_caught(engine, "rem_long_zero_throws_typed", rem_long_code(), tries, 556);
    }
    {
        std::vector<uint16_t> c;                       // div-int by zero (23x)
        emit_const(c, 0, 5);
        emit_const(c, 2, 0);
        emit_23x(c, opc::DIV_INT, 3, 0, 2);            // pc4-5
        emit_const(c, 1, 446);                         // pc6-8
        c.push_back(w11x(1, opc::RETURN));             // pc9
        emit_const(c, 1, 557);                         // pc10-12
        c.push_back(w11x(1, opc::RETURN));             // pc13
        std::vector<uint8_t> tries;
        append_try(tries, 6, 2, {{static_cast<uint32_t>(T_ARITH), 12}}, -1);
        expect_caught(engine, "div_int_zero_throws_typed", c, tries, 557);
    }
    {
        std::vector<uint16_t> c;                       // rem-int/lit8 with literal 0
        emit_const(c, 0, 5);                           // pc0-2
        emit_22b(c, opc::L_REM_INT_LIT8, 1, 0, 0);     // pc3-4  v1 = 5 rem 0
        emit_const(c, 1, 447);                         // pc5-7
        c.push_back(w11x(1, opc::RETURN));             // pc8
        emit_const(c, 1, 558);                         // pc9-11
        c.push_back(w11x(1, opc::RETURN));             // pc12
        std::vector<uint8_t> tries;
        append_try(tries, 3, 2, {{static_cast<uint32_t>(T_ARITH), 9}}, -1);
        expect_caught(engine, "rem_int_lit8_zero_throws_typed", c, tries, 558);
    }
    {
        // UNCAUGHT: no try table → div-long by zero must NOT return a value.
        // Pre-fix behavior: yields 0 and returns normally (777).
        std::vector<uint16_t> c;
        emit_const_wide(c, 0, 10);
        emit_const_wide(c, 2, 0);
        emit_23x(c, opc::DIV_LONG, 4, 0, 2);
        emit_const(c, 1, 777);
        c.push_back(w11x(1, opc::RETURN));
        DalvikExecutionResult r = run_plain(engine, c, "()I", "div_long_zero_uncaught");
        const auto* ret = find_return(r);
        bool returned_value = (ret && ret->return_value);
        record("div_long_zero_uncaught_unwinds", !returned_value,
               returned_value ? "method returned a value (old bug: no exception thrown)"
                              : "no normal return — frame unwound via ArithmeticException");
    }

    // ── GROUP P (K-19/K-20): parse* / substring / concat bridge ───────────
    {
        // Integer.parseInt("123") → 123
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);       // v0 = "123"
        emit_invoke(c, opc::INVOKE_STATIC, 1, {0}, 0);                 // parseInt(v0)
        c.push_back(w11x(1, opc::MOVE_RESULT));
        c.push_back(w11x(1, opc::RETURN));
        expect_num_invoke(engine, "integer_parseInt_123", c, "()I",
                          {"LSemTest;", "Ljava/lang/Integer;", "parseInt", "123"},
                          {"LSemTest;", "Ljava/lang/Integer;"}, 123.0);
    }
    {
        // Integer.parseInt("-45") → -45
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {0}, 0);
        c.push_back(w11x(1, opc::MOVE_RESULT));
        c.push_back(w11x(1, opc::RETURN));
        expect_num_invoke(engine, "integer_parseInt_negative", c, "()I",
                          {"LSemTest;", "Ljava/lang/Integer;", "parseInt", "-45"},
                          {"LSemTest;", "Ljava/lang/Integer;"}, -45.0);
    }
    {
        // Long.parseLong("4294967296") → 2^32 (64-bit discriminator)
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {0}, 0);
        c.push_back(w11x(1, opc::MOVE_RESULT_WIDE));
        c.push_back(w11x(1, opc::RETURN_WIDE));
        expect_num_invoke(engine, "long_parseLong_2p32", c, "()J",
                          {"LSemTest;", "Ljava/lang/Long;", "parseLong", "4294967296"},
                          {"LSemTest;", "Ljava/lang/Long;"}, 4294967296.0);
    }
    {
        // Float.parseFloat("2.5") → 2.5
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {0}, 0);
        c.push_back(w11x(1, opc::MOVE_RESULT));
        c.push_back(w11x(1, opc::RETURN));
        expect_num_invoke(engine, "float_parseFloat_2p5", c, "()F",
                          {"LSemTest;", "Ljava/lang/Float;", "parseFloat", "2.5"},
                          {"LSemTest;", "Ljava/lang/Float;"}, 2.5);
    }
    {
        // Double.parseDouble("1.5") → 1.5
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);
        emit_invoke(c, opc::INVOKE_STATIC, 1, {0}, 0);
        c.push_back(w11x(1, opc::MOVE_RESULT_WIDE));
        c.push_back(w11x(1, opc::RETURN_WIDE));
        expect_num_invoke(engine, "double_parseDouble_1p5", c, "()D",
                          {"LSemTest;", "Ljava/lang/Double;", "parseDouble", "1.5"},
                          {"LSemTest;", "Ljava/lang/Double;"}, 1.5);
    }
    {
        // "hello".substring(1, 3) → "el" (invoke-virtual with receiver)
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);       // v0 = "hello"
        c.push_back(const4(1, 1));                                     // v1 = 1
        c.push_back(const4(2, 3));                                     // v2 = 3
        emit_invoke(c, opc::INVOKE_VIRTUAL, 3, {0, 1, 2}, 0);          // v0.substring(v1, v2)
        c.push_back(w11x(3, opc::MOVE_RESULT_OBJECT));
        c.push_back(w11x(3, opc::RETURN_OBJECT));
        expect_str(engine, "string_substring_1_3", c,
                   {"LSemTest;", "Ljava/lang/String;", "substring", "hello"},
                   {"LSemTest;", "Ljava/lang/String;"}, "el");
    }
    {
        // "hello".concat("world") → "helloworld"
        std::vector<uint16_t> c;
        c.push_back(w11x(0, opc::CONST_STRING)); c.push_back(3);       // v0 = "hello"
        c.push_back(w11x(1, opc::CONST_STRING)); c.push_back(4);       // v1 = "world"
        emit_invoke(c, opc::INVOKE_VIRTUAL, 2, {0, 1}, 0);
        c.push_back(w11x(2, opc::MOVE_RESULT_OBJECT));
        c.push_back(w11x(2, opc::RETURN_OBJECT));
        expect_str(engine, "string_concat_hello_world", c,
                   {"LSemTest;", "Ljava/lang/String;", "concat", "hello", "world"},
                   {"LSemTest;", "Ljava/lang/String;"}, "helloworld");
    }

    std::cout << "\nRESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
