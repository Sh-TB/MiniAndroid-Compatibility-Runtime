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
static uint16_t w12x(uint8_t vA, uint8_t vB, uint16_t op) { // B|A|op (AOSP 12x)
    // vA = dest = bits 8-11, vB = src = bits 12-15.
    // DEMO-12X-NIBBLE (2026-09-04): previously encoded the swapped
    // convention (vA in bits 12-15), cancelling the interpreter's swapped
    // decoder inside this fixture while real DEX broke. Both sides now
    // follow AOSP; parameters keep their meaning: w12x(dest, src, op).
    return static_cast<uint16_t>((vB << 12) | (vA << 8) | op);
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
static void emit_invoke_static(std::vector<uint16_t>& c, uint16_t method_idx) {
    // 35c: AG|op BBBB FEDC — argc=2, regs {v2, v4} (two WIDE register pairs,
    // per the J J parameter list of Long.compare/compareUnsigned).
    c.push_back(static_cast<uint16_t>((2 << 12) | 0x71));
    c.push_back(method_idx);
    c.push_back(static_cast<uint16_t>(2 | (4 << 4)));
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
        case T::BOOLEAN: return v.bool_val ? 1.0 : 0.0;
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

    // ── F-086 (S57 R-NEW-344): java.lang.Long.compare/compareUnsigned ─────
    //
    // Bridge law (OpenJDK Long.java): compare is a SIGNED 64-bit compare
    // (-1/0/+1); compareUnsigned compares on the unsigned domain. The
    // discriminating case is the exact dooz v23 ScatterMap growth idiom
    // (R8-inlined Lbw0;.d): Long.compare(size*32 ^ Long.MIN_VALUE,
    // capacity*25 ^ Long.MIN_VALUE) must return +1 (448^MIN > 375^MIN);
    // the pre-fix bridge had NO Long.compare handler, so the STUBBED
    // typed-zero exit returned 0 → if-gtz fell through → cleanup instead
    // of resize → full-table probe spin → blank first frame (R-NEW-344).
    {
        auto cmp_snippet = [&](const char* name, int64_t a, int64_t b,
                               std::vector<std::string>& strings) {
            // find name index in strings (or append)
            uint16_t ni = 0;
            for (size_t i = 0; i < strings.size(); ++i)
                if (strings[i] == name) { ni = static_cast<uint16_t>(i); break; }
            if (ni == 0 && !(strings.size() && strings[0] == name)) {
                strings.push_back(name);
                ni = static_cast<uint16_t>(strings.size() - 1);
            }
            std::vector<uint16_t> c;
            emit_const_wide(c, 2, a);   // wide pair v2-v3
            emit_const_wide(c, 4, b);   // wide pair v4-v5
            emit_invoke_static(c, ni);  // invoke-static {v2, v4}, Long.name
            c.push_back(w11x(0, opc::MOVE_RESULT));
            c.push_back(w11x(0, opc::RETURN));
            return c;
        };

        // Build the report with method_ids for Long.compare/compareUnsigned.
        auto cmp_run = [&](const std::vector<uint16_t>& code,
                           const std::vector<std::string>& names,
                           const std::string& desc, const std::string& name) {
            MethodInfo mi;
            mi.name = name;
            mi.descriptor = desc;
            mi.defining_class = "LSemTest;";
            mi.registers_size = 16;
            mi.ins_size = 0;
            mi.outs_size = 5;
            mi.bytecode = code;

            DexReport report;
            report.strings = names;
            report.types.push_back("Ljava/lang/Long;");
            report.types.push_back("LSemTest;");
            report.method_ids.push_back({0, 0, 0});  // names[0] = "compare"
            if (names.size() > 1) report.method_ids.push_back({0, 0, 1});
            ClassInfo ci;
            ci.name = "LSemTest;";
            ci.superclass_name = "Ljava/lang/Object;";
            ci.direct_methods.push_back(mi);
            report.classes.push_back(ci);
            return engine.execute_method(ci.direct_methods[0], report, {}, false);
        };

        // The dooz23 growth idiom, bit-exact:
        //   compare(448 ^ LONG_MIN, 375 ^ LONG_MIN) == +1
        {
            std::vector<std::string> names{"compare"};
            auto c = cmp_snippet("compare",
                                 (int64_t)448 ^ (int64_t)0x8000000000000000ULL,
                                 (int64_t)375 ^ (int64_t)0x8000000000000000ULL,
                                 names);
            DalvikExecutionResult r = cmp_run(c, names, "()I", "f086_compare_scattermap_idiom");
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f086_long_compare_scattermap_growth_idiom", got == 1.0,
                   "expected +1 (resize decision), got " + std::to_string(got));
        }
        {   // plain signed: compare(5, 3) == 1
            std::vector<std::string> names{"compare"};
            auto c = cmp_snippet("compare", 5, 3, names);
            DalvikExecutionResult r = cmp_run(c, names, "()I", "f086_compare_pos");
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f086_long_compare_pos_gt", got == 1.0,
                   "expected +1, got " + std::to_string(got));
        }
        {   // negative-vs-positive: compare(-7, 3) == -1 (a 32-bit/unsigned
            // misread of the high word would give +1)
            std::vector<std::string> names{"compare"};
            auto c = cmp_snippet("compare", -7, 3, names);
            DalvikExecutionResult r = cmp_run(c, names, "()I", "f086_compare_neg");
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f086_long_compare_signed_neg", got == -1.0,
                   "expected -1, got " + std::to_string(got));
        }
        {   // LONG_MIN vs LONG_MAX == -1 (full-width discrimination)
            std::vector<std::string> names{"compare"};
            auto c = cmp_snippet("compare",
                                 (int64_t)0x8000000000000000ULL,
                                 (int64_t)0x7FFFFFFFFFFFFFFFULL, names);
            DalvikExecutionResult r = cmp_run(c, names, "()I", "f086_compare_minmax");
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f086_long_compare_min_max", got == -1.0,
                   "expected -1, got " + std::to_string(got));
        }
        {   // equal: compare(42, 42) == 0
            std::vector<std::string> names{"compare"};
            auto c = cmp_snippet("compare", 42, 42, names);
            DalvikExecutionResult r = cmp_run(c, names, "()I", "f086_compare_eq");
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f086_long_compare_equal", got == 0.0,
                   "expected 0, got " + std::to_string(got));
        }
        {   // unsigned domain: compareUnsigned(-1, 1) == +1 (signed would say -1)
            std::vector<std::string> names{"compare", "compareUnsigned"};
            auto c = cmp_snippet("compareUnsigned",
                                 (int64_t)-1, (int64_t)1, names);
            DalvikExecutionResult r = cmp_run(c, names, "()I", "f086_compare_unsigned");
            const miniandroid::dalvik::InstructionTrace* ret = nullptr;
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f086_long_compare_unsigned", got == 1.0,
                   "expected +1 (unsigned 2^64-1 > 1), got " + std::to_string(got));
        }
    }

    // ── F-102/F-103 (S58 R-NEW-376 + R-NEW-378) ──────────────────────────
    //
    // F-102 law: the 3rc invoke path must pass the call site's method PROTO
    // to try_recursive_invoke so the F-023 exact-(class, name, desc)
    // overload law selects the target. Pre-fix the range path dropped the
    // proto; the arity heuristic preferred the LARGER bytecode body —
    // re-selecting the CALLING ctor overload itself → same-receiver
    // self-recursion to the depth cap (dooz v18 Lj/j0; ×7 / v23 Lgz1; ×3 +
    // Lbp1; ×1 RECURSION-LIMIT drops, caller==callee).
    //
    // Discrimination: LSemA; carries <init>(I)V (NOP-padded, LARGER, sets
    // g:I) and <init>()V (SMALL, sets f:J = 127). The entry invokes
    // <init>()V via invoke-direct/range. Post-fix: exact descriptor match
    // → <init>()V runs → f == 127. Pre-fix: the heuristic picks the larger
    // <init>(I)V → f is never written → 0. (The fixture's proto fallback
    // resolves the call site to "()V" — the same non-empty-descriptor path
    // real APKs exercise.)
    {
        MethodInfo ctor_i;  // <init>(I)V — padded LARGE so the pre-fix
                            // "prefer larger bytecode" heuristic picks it
        ctor_i.name = "<init>";
        ctor_i.descriptor = "(I)V";
        ctor_i.defining_class = "LSemA;";
        ctor_i.registers_size = 6;   // v4 = this, v5 = p1 (I)
        ctor_i.ins_size = 2;
        ctor_i.outs_size = 2;
        {
            std::vector<uint16_t> c;
            for (int i = 0; i < 40; ++i) c.push_back(0x0000);  // nop padding
            // iput vA=5(src), vB=4(obj), g@field_idx1 (22c: B|A|op BBBB)
            c.push_back(static_cast<uint16_t>((4 << 12) | (5 << 8) | 0x59));
            c.push_back(static_cast<uint16_t>(1));
            c.push_back(w11x(0, 0x0E));  // return-void
            ctor_i.bytecode = c;
        }
        MethodInfo ctor_v;  // <init>()V — sets f = 127
        ctor_v.name = "<init>";
        ctor_v.descriptor = "()V";
        ctor_v.defining_class = "LSemA;";
        ctor_v.registers_size = 5;   // v4 = this
        ctor_v.ins_size = 1;
        ctor_v.outs_size = 2;
        {
            std::vector<uint16_t> c;
            // const-wide/16 v0, 127 (21s)
            c.push_back(w11x(0, 0x16));
            c.push_back(static_cast<uint16_t>(127));
            // iput-wide vA=0(src), vB=4(obj), f@field_idx0
            c.push_back(static_cast<uint16_t>((4 << 12) | (0 << 8) | 0x5A));
            c.push_back(static_cast<uint16_t>(0));
            c.push_back(w11x(0, 0x0E));  // return-void
            ctor_v.bytecode = c;
        }

        MethodInfo entry;
        entry.name = "f102_range_ctor_overload_exact";
        entry.descriptor = "()J";
        entry.defining_class = "LSemTest;";
        entry.registers_size = 6;
        entry.ins_size = 0;
        entry.outs_size = 3;
        {
            std::vector<uint16_t> c;
            // new-instance v2, LSemA; (type_idx 0)
            c.push_back(w11x(2, 0x22));
            c.push_back(0);
            // invoke-direct/range {v2}, LSemA;-><init>()V (3rc: AA|op BBBB CCCC)
            c.push_back(static_cast<uint16_t>((1 << 8) | 0x76));
            c.push_back(0);  // method_idx 0
            c.push_back(2);  // first_reg = v2
            // iget-wide vA=0(dest), vB=2(obj), f@field_idx0
            c.push_back(static_cast<uint16_t>((2 << 12) | (0 << 8) | 0x53));
            c.push_back(static_cast<uint16_t>(0));
            c.push_back(w11x(0, opc::RETURN_WIDE));
            entry.bytecode = c;
        }

        DexReport report;
        report.strings = {"f", "g", "<init>"};
        report.types = {"LSemA;", "LSemTest;", "J", "I"};
        report.field_ids.push_back({0, 2, 0});  // LSemA;.f : J
        report.field_ids.push_back({0, 3, 1});  // LSemA;.g : I
        report.method_ids.push_back({0, 0, 2});  // LSemA;.<init>
        ClassInfo ca;
        ca.name = "LSemA;";
        ca.superclass_name = "Ljava/lang/Object;";
        ca.direct_methods.push_back(ctor_i);
        ca.direct_methods.push_back(ctor_v);
        report.classes.push_back(ca);
        ClassInfo ct;
        ct.name = "LSemTest;";
        ct.superclass_name = "Ljava/lang/Object;";
        ct.direct_methods.push_back(entry);
        report.classes.push_back(ct);

        DalvikExecutionResult r = engine.execute_method(entry, report, {}, false);
        const miniandroid::dalvik::InstructionTrace* ret = nullptr;
        for (const auto& t : r.instruction_traces)
            if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN) ret = &t;
        double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
        record("f102_range_ctor_overload_exact_dispatch", got == 127.0,
               "expected 127 (the ()V overload stored it; larger (I)V body must "
               "NOT be selected), got " + std::to_string(got));
    }

    // ── F-103 (S58 R-NEW-378): java.lang.Class type-question laws ────────
    //
    // Law (OpenJDK Class.java): isInstance(obj) == isAssignableFrom(
    // obj.getClass()); both walk the real class hierarchy. Pre-fix there
    // was NO handler → STUBBED typed-zero 0 → the compose
    // DisposableSaveableStateRegistry ACCEPTABLE_CLASSES loop missed for
    // all 29 elements → rememberSaveable threw IAE "Can't put value with
    // type null into saved state" → APP BOUNDARY unwind (dooz v23
    // MainActivity.onCreate invoke_pc=317 → blank frame).
    //
    // Also pinned here: const-class HEAP-BACKED tokens (the token is a real
    // Ljava/lang/Class; heap object carrying __referent_desc, so §19
    // receiver-class resolution and shadow round-trips keep the token
    // identity) and the instance-of runtime-type authority walk.
    {
        // Shared report pieces: LSemBase; <- LSemSub; hierarchy.
        DexReport base_report;
        base_report.strings = {"<init>", "isInstance", "isAssignableFrom"};
        base_report.types = {"LSemBase;", "LSemSub;", "LSemTest;",
                             "Ljava/lang/String;", "Ljava/lang/Class;"};
        ClassInfo cb;
        cb.name = "LSemBase;";
        cb.superclass_name = "Ljava/lang/Object;";
        base_report.classes.push_back(cb);
        ClassInfo cs;
        cs.name = "LSemSub;";
        cs.superclass_name = "LSemBase;";
        base_report.classes.push_back(cs);
        ClassInfo ct2;
        ct2.name = "LSemTest;";
        ct2.superclass_name = "Ljava/lang/Object;";
        base_report.classes.push_back(ct2);

        auto class_law_run = [&](MethodInfo mi, DexReport report) {
            return engine.execute_method(mi, report, {}, false);
        };
        auto halt_return = [](DalvikExecutionResult& r)
            -> const miniandroid::dalvik::InstructionTrace* {
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN)
                    return &t;
            return nullptr;
        };

        {   // isInstance exact: String.class.isInstance("x") == true
            MethodInfo mi;
            mi.name = "f103_isInstance_string_exact";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8; mi.ins_size = 0; mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(3);   // const-class v2, String
            c.push_back(w11x(3, 0x1A)); c.push_back(3);   // const-string v3, strings[3]="x"
            // invoke-virtual {v2, v3}, Class.isInstance (method_ids slot 0)
            c.push_back(static_cast<uint16_t>((2 << 12) | 0x6E));
            c.push_back(0);
            c.push_back(static_cast<uint16_t>(2 | (3 << 4)));
            c.push_back(w11x(0, opc::MOVE_RESULT));
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DexReport rep = base_report;
            rep.strings.push_back("x");  // idx 3
            rep.method_ids.push_back({4, 0, 1});  // Class.isInstance
            DalvikExecutionResult r = class_law_run(mi, rep);
            const auto* ret = halt_return(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f103_class_isInstance_string_exact", got == 1.0,
                   "expected 1 (String token vs String value), got " + std::to_string(got));
        }
        {   // isAssignableFrom subclass walk: Base.isAssignableFrom(Sub)
            MethodInfo mi;
            mi.name = "f103_isAssignableFrom_subclass";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8; mi.ins_size = 0; mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(0);   // const-class v2, LSemBase;
            c.push_back(w11x(3, 0x1C)); c.push_back(1);   // const-class v3, LSemSub;
            // invoke-virtual {v2, v3}, Class.isAssignableFrom (method_ids slot 1)
            c.push_back(static_cast<uint16_t>((2 << 12) | 0x6E));
            c.push_back(1);
            c.push_back(static_cast<uint16_t>(2 | (3 << 4)));
            c.push_back(w11x(0, opc::MOVE_RESULT));
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DexReport rep = base_report;
            rep.method_ids.push_back({4, 0, 1});  // Class.isInstance
            rep.method_ids.push_back({4, 0, 2});  // Class.isAssignableFrom
            DalvikExecutionResult r = class_law_run(mi, rep);
            const auto* ret = halt_return(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f103_class_isAssignableFrom_subclass", got == 1.0,
                   "expected 1 (Sub is assignable to Base), got " + std::to_string(got));
        }
        {   // instance-of runtime-type authority: new LSemSub; instanceof LSemBase;
            MethodInfo mi;
            mi.name = "f103_instanceof_heap_subclass";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8; mi.ins_size = 0; mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x22)); c.push_back(1);   // new-instance v2, LSemSub;
            // instance-of v0, v2, LSemBase; (22c: dest vA=0 low nibble of high
            // byte, src vB=0? — canonical: (dest<<8)|op with src/type encoded
            // BB|CC — here: vA=0, vB=2, type@1)
            c.push_back(static_cast<uint16_t>((2 << 12) | (0 << 8) | 0x20));
            c.push_back(static_cast<uint16_t>(1));
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DalvikExecutionResult r = class_law_run(mi, base_report);
            const auto* ret = halt_return(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f103_instanceof_heap_subclass", got == 1.0,
                   "expected 1 (heap object of LSemSub; through the superclass "
                   "walk), got " + std::to_string(got));
        }
        {   // F-105c (S59 R-NEW-379): const-class token instanceof Class == true.
            // The const-class value is a CLASS_REF whose ref_id is the
            // heap-backed Ljava/lang/Class; token and whose class_desc is the
            // REFERENT (LSemBase;). ART law: X.class's runtime class IS
            // java.lang.Class, so `X.class instanceof Class` is TRUE for every
            // X. Pre-fix the guard `instance-of key, Ljava/lang/Class;` rejected
            // every CLASS_REF (type != OBJECT_REF) → ViewModelProvider's
            // ViewModelStore key check threw IAE "Key must be a class" (dooz
            // v23 Lwl0;.containsKey, depth 79, APP BOUNDARY unwind).
            MethodInfo mi;
            mi.name = "f105_instanceof_classtoken_is_class";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8; mi.ins_size = 0; mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(0);   // const-class v2, LSemBase;
            // instance-of v0, v2, Ljava/lang/Class; (type@4)
            c.push_back(static_cast<uint16_t>((2 << 12) | (0 << 8) | 0x20));
            c.push_back(static_cast<uint16_t>(4));
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DalvikExecutionResult r = class_law_run(mi, base_report);
            const auto* ret = halt_return(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f105_instanceof_classtoken_is_class", got == 1.0,
                   "expected 1 (the LSemBase; class token's runtime class is "
                   "java.lang.Class), got " + std::to_string(got));
        }
        {   // F-105c companion: the token is NOT the referent class.
            // `LSemBase.class instanceof LSemBase` must be FALSE on ART (the
            // token is a java.lang.Class object, not an LSemBase instance).
            MethodInfo mi;
            mi.name = "f105_instanceof_classtoken_not_referent";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8; mi.ins_size = 0; mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(0);   // const-class v2, LSemBase;
            // instance-of v0, v2, LSemBase; (type@0)
            c.push_back(static_cast<uint16_t>((2 << 12) | (0 << 8) | 0x20));
            c.push_back(static_cast<uint16_t>(0));
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DalvikExecutionResult r = class_law_run(mi, base_report);
            const auto* ret = halt_return(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f105_instanceof_classtoken_not_referent", got == 0.0,
                   "expected 0 (a Class token is not an instance of its own "
                   "referent class), got " + std::to_string(got));
        }
    }

    // ── F-106 (S60, R-NEW-380): reflection surface law family ────────────
    //
    // dooz v23 R-NEW-380: the androidx ViewModelProvider NewInstanceFactory
    // fallback (Leo;.n) executes
    //     ctor = modelClass.getDeclaredConstructor(null);
    //     if (!Modifier.isPublic(ctor.getModifiers()))
    //         throw new RuntimeException("Cannot create an instance of " + modelClass);
    //     return ctor.newInstance();
    // Pre-fix EVERY step typed-zero'd: the getDeclaredConstructor record
    // lost the referent identity (keyed "Ljava/lang/Class;"),
    // Constructor.getModifiers() and Modifier.isPublic(I) had NO handlers →
    // 0 → the THROW branch for every class (Leo;.n pc=53, depth 81), and
    // the message rendered an EMPTY class name (no Class.toString law).
    // Discrimination: pre-fix the full-chain fixture takes the not-public
    // branch (returns 0) and the NSM fixture returns normally; post-fix
    // the chain runs the real <init> (returns 127) and the missing-ctor
    // lookup throws NoSuchMethodException (uncaught, recorded).
    {
        DexReport f106;
        f106.strings = {"<init>", "getDeclaredConstructor", "getModifiers",
                        "isPublic", "newInstance", "toString", "g"};
        f106.types = {"LSemA;", "LSemB;", "LSemTest;", "Ljava/lang/Class;",
                      "Ljava/lang/reflect/Constructor;",
                      "Ljava/lang/reflect/Modifier;",
                      "Ljava/lang/Object;", "I", "Ljava/lang/Long;"};
        f106.method_ids.push_back({3, 0, 1});  // Class.getDeclaredConstructor
        f106.method_ids.push_back({4, 0, 2});  // Constructor.getModifiers
        f106.method_ids.push_back({5, 0, 3});  // Modifier.isPublic
        f106.method_ids.push_back({4, 0, 4});  // Constructor.newInstance
        f106.method_ids.push_back({3, 0, 5});  // Class.toString
        f106.method_ids.push_back({8, 0, 5});  // Long.toString
        f106.field_ids.push_back({0, 7, 6});   // LSemA;.g : I

        ClassInfo ca;
        ca.name = "LSemA;";
        ca.superclass_name = "Ljava/lang/Object;";
        MethodInfo ctor_v;  // public <init>()V — sets g = 127
        ctor_v.name = "<init>";
        ctor_v.descriptor = "()V";
        ctor_v.defining_class = "LSemA;";
        ctor_v.is_constructor = true;
        ctor_v.access_flags = 0x1;  // public
        ctor_v.registers_size = 5;
        ctor_v.ins_size = 1;
        ctor_v.outs_size = 2;
        {
            std::vector<uint16_t> c;
            c.push_back(w11x(0, 0x13));  // const/16 v0, 127
            c.push_back(static_cast<uint16_t>(127));
            c.push_back(static_cast<uint16_t>((4 << 12) | (0 << 8) | 0x59));
            c.push_back(static_cast<uint16_t>(0));  // iput v0, v4(this), g@0
            c.push_back(w11x(0, 0x0E));  // return-void
            ctor_v.bytecode = c;
        }
        MethodInfo ctor_i;  // <init>(I)V — exists but NOT the no-arg match
        ctor_i.name = "<init>";
        ctor_i.descriptor = "(I)V";
        ctor_i.defining_class = "LSemA;";
        ctor_i.is_constructor = true;
        ctor_i.access_flags = 0x1;
        ctor_i.parameters = {"I"};
        ctor_i.registers_size = 6;
        ctor_i.ins_size = 2;
        ctor_i.outs_size = 2;
        ctor_i.bytecode = {w11x(0, 0x0E)};  // return-void
        ca.direct_methods.push_back(ctor_v);
        ca.direct_methods.push_back(ctor_i);
        f106.classes.push_back(ca);

        ClassInfo cb;  // LSemB; — ONLY <init>(I)V: no no-arg ctor exists
        cb.name = "LSemB;";
        cb.superclass_name = "Ljava/lang/Object;";
        MethodInfo ctor_bi;
        ctor_bi.name = "<init>";
        ctor_bi.descriptor = "(I)V";
        ctor_bi.defining_class = "LSemB;";
        ctor_bi.is_constructor = true;
        ctor_bi.access_flags = 0x1;
        ctor_bi.parameters = {"I"};
        ctor_bi.registers_size = 6;
        ctor_bi.ins_size = 2;
        ctor_bi.outs_size = 2;
        ctor_bi.bytecode = {w11x(0, 0x0E)};
        cb.direct_methods.push_back(ctor_bi);
        f106.classes.push_back(cb);

        ClassInfo ct6;
        ct6.name = "LSemTest;";
        ct6.superclass_name = "Ljava/lang/Object;";
        f106.classes.push_back(ct6);

        auto f106_run = [&](MethodInfo mi) {
            return engine.execute_method(mi, f106, {}, false);
        };
        auto f106_ret = [](DalvikExecutionResult& r)
            -> const miniandroid::dalvik::InstructionTrace* {
            for (const auto& t : r.instruction_traces)
                if (t.status == miniandroid::dalvik::InstructionTrace::Status::HALT_RETURN)
                    return &t;
            return nullptr;
        };

        {   // full chain: const-class → getDeclaredConstructor(null) →
            // getModifiers → Modifier.isPublic → newInstance → real <init>.
            MethodInfo mi;
            mi.name = "f106_newinstancefactory_full_chain";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 12;
            mi.ins_size = 0;
            mi.outs_size = 3;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(0);   // const-class v2, LSemA;
            c.push_back((0 << 12) | (3 << 8) | 0x12);     // const/4 v3, null
            c.push_back((2 << 12) | 0x6E);                // invoke-virtual {v2,v3}
            c.push_back(0);                               //   getDeclaredConstructor
            c.push_back(2 | (3 << 4));
            c.push_back(w11x(4, 0x0C));                   // move-result-object v4
            c.push_back((1 << 12) | 0x6E);                // invoke-virtual {v4}
            c.push_back(1);                               //   getModifiers
            c.push_back(4);
            c.push_back(w11x(5, 0x0A));                   // move-result v5
            c.push_back((1 << 12) | 0x71);                // invoke-static {v5}
            c.push_back(2);                               //   Modifier.isPublic
            c.push_back(5);
            c.push_back(w11x(6, 0x0A));                   // move-result v6
            c.push_back((6 << 8) | 0x38);                 // if-eqz v6, +9 → not-public
            c.push_back(9);
            c.push_back((1 << 12) | 0x6E);                // invoke-virtual {v4}
            c.push_back(3);                               //   newInstance
            c.push_back(4);
            c.push_back(w11x(7, 0x0C));                   // move-result-object v7
            c.push_back((7 << 12) | (0 << 8) | 0x52);     // iget v0, v7, g@0
            c.push_back(static_cast<uint16_t>(0));
            c.push_back(w11x(0, opc::RETURN));            // return v0 (127)
            c.push_back((0 << 12) | (0 << 8) | 0x12);     // const/4 v0, 0
            c.push_back(w11x(0, opc::RETURN));            // return 0 (not-public)
            mi.bytecode = c;
            DalvikExecutionResult r = f106_run(mi);
            const auto* ret = f106_ret(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f106_newinstancefactory_full_chain", got == 127.0,
                   "expected 127 (the public no-arg ctor ran through "
                   "getDeclaredConstructor → getModifiers → isPublic → "
                   "newInstance), got " + std::to_string(got));
        }
        {   // missing constructor → NoSuchMethodException (uncaught: the
            // fixture has no catch; M3 FINDING-016 records the in-flight
            // exception). Pre-fix: no throw — the legacy record law
            // returned normally.
            MethodInfo mi;
            mi.name = "f106_getdeclaredconstructor_missing_throws_nsm";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8;
            mi.ins_size = 0;
            mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(1);   // const-class v2, LSemB;
            c.push_back((0 << 12) | (3 << 8) | 0x12);     // const/4 v3, null
            c.push_back((2 << 12) | 0x6E);                // invoke-virtual {v2,v3}
            c.push_back(0);                               //   getDeclaredConstructor
            c.push_back(2 | (3 << 4));
            c.push_back(w11x(0, opc::MOVE_RESULT));       // move-result v0
            c.push_back(w11x(0, opc::RETURN));            // return v0
            mi.bytecode = c;
            DalvikExecutionResult r = f106_run(mi);
            const auto* ret = f106_ret(r);
            // Post-fix: the deferred NoSuchMethodException unwinds the frame
            // (no catch in this fixture) → the method NEVER returns normally.
            // Pre-fix: the legacy record law returned a Constructor record
            // and the fixture completed with a normal return.
            record("f106_getdeclaredconstructor_missing_throws_nsm", ret == nullptr,
                   std::string(ret == nullptr
                                   ? "PASS: no normal return — the deferred "
                                     "NoSuchMethodException unwound the frame"
                                   : "FAIL: fixture returned normally — no "
                                     "NoSuchMethodException was raised"));
        }
        {   // Constructor.getModifiers() answers the DEX access flags (1).
            MethodInfo mi;
            mi.name = "f106_constructor_getmodifiers_public";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8;
            mi.ins_size = 0;
            mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(0);   // const-class v2, LSemA;
            c.push_back((0 << 12) | (3 << 8) | 0x12);     // const/4 v3, null
            c.push_back((2 << 12) | 0x6E);                // getDeclaredConstructor
            c.push_back(0);
            c.push_back(2 | (3 << 4));
            c.push_back(w11x(4, 0x0C));                   // move-result-object v4
            c.push_back((1 << 12) | 0x6E);                // getModifiers
            c.push_back(1);
            c.push_back(4);
            c.push_back(w11x(0, opc::MOVE_RESULT));       // move-result v0
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DalvikExecutionResult r = f106_run(mi);
            const auto* ret = f106_ret(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f106_constructor_getmodifiers_public", got == 1.0,
                   "expected 1 (ACC_PUBLIC of the declared no-arg ctor), got " +
                   std::to_string(got));
        }
        {   // Modifier.isPublic bit law: 0x10001 (public|constructor) → 1.
            MethodInfo mi;
            mi.name = "f106_modifier_ispublic_bitlaw";
            mi.descriptor = "()I";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8;
            mi.ins_size = 0;
            mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x14));                   // const v2, 0x10001
            c.push_back(static_cast<uint16_t>(0x0001));
            c.push_back(static_cast<uint16_t>(0x0001));
            c.push_back((1 << 12) | 0x71);                // invoke-static {v2}
            c.push_back(2);                               //   Modifier.isPublic
            c.push_back(2);
            c.push_back(w11x(0, opc::MOVE_RESULT));
            c.push_back(w11x(0, opc::RETURN));
            mi.bytecode = c;
            DalvikExecutionResult r = f106_run(mi);
            const auto* ret = f106_ret(r);
            double got = ret && ret->return_value ? as_double(*ret->return_value) : -999;
            record("f106_modifier_ispublic_bitlaw", got == 1.0,
                   "expected 1 (Modifier.isPublic(0x10001)), got " +
                   std::to_string(got));
        }
        {   // Class token toString: "class " + dotted name (OpenJDK law).
            MethodInfo mi;
            mi.name = "f106_class_tostring_token";
            mi.descriptor = "()Ljava/lang/String;";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8;
            mi.ins_size = 0;
            mi.outs_size = 2;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x1C)); c.push_back(0);   // const-class v2, LSemA;
            c.push_back((1 << 12) | 0x6E);                // invoke-virtual {v2}
            c.push_back(4);                               //   Class.toString
            c.push_back(2);
            c.push_back(w11x(0, 0x0C));                   // move-result-object v0
            c.push_back(w11x(0, 0x11));                   // return-object v0
            mi.bytecode = c;
            DalvikExecutionResult r = f106_run(mi);
            const auto* ret = f106_ret(r);
            std::string got = ret && ret->return_value &&
                                      ret->return_value->type ==
                                          miniandroid::dalvik::DalvikType::STRING_REF
                                  ? ret->return_value->string_val
                                  : std::string("<no-string>");
            record("f106_class_tostring_token",
                   got == "class SemA",
                   "expected \"class SemA\" (OpenJDK Class.toString of the "
                   "package-less LSemA;), got \"" + got + "\"");
        }
        {   // Long.toString(J, I) radix-36 — the Compose rememberSaveable
            // registry key (Lpm;.W: Long.toString(compositeKeyHash, 36)).
            // Pre-fix: NO handler → typed-zero "" → registerProvider("") →
            // IAE "Registered key is empty or blank" (dooz v23, Ldf1;.a).
            MethodInfo mi;
            mi.name = "f106_long_tostring_radix36";
            mi.descriptor = "()Ljava/lang/String;";
            mi.defining_class = "LSemTest;";
            mi.registers_size = 8;
            mi.ins_size = 0;
            mi.outs_size = 3;
            std::vector<uint16_t> c;
            c.push_back(w11x(2, 0x16));                   // const-wide/16 v2, 127
            c.push_back(static_cast<uint16_t>(127));
            c.push_back(w11x(4, 0x13));                   // const/16 v4, 36
            c.push_back(static_cast<uint16_t>(36));
            c.push_back((2 << 12) | 0x71);                // invoke-static {v2,v4}
            c.push_back(5);                               //   Long.toString(J I)
            c.push_back(2 | (4 << 4));                    // wide pair v2 + int v4
            c.push_back(w11x(0, 0x0C));                   // move-result-object v0
            c.push_back(w11x(0, 0x11));                   // return-object v0
            mi.bytecode = c;
            DalvikExecutionResult r = f106_run(mi);
            const auto* ret = f106_ret(r);
            std::string got2 = ret && ret->return_value &&
                                      ret->return_value->type ==
                                          miniandroid::dalvik::DalvikType::STRING_REF
                                  ? ret->return_value->string_val
                                  : std::string("<no-string>");
            record("f106_long_tostring_radix36",
                   got2 == "3j",
                   "expected \"3j\" (127 in base 36 — the rememberSaveable "
                   "key shape), got \"" + got2 + "\"");
        }
    }

    std::cout << "\nRESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
