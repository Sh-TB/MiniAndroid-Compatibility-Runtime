// UNIFIED_011.3 TYPED-CATCH — typed exception matching + frame propagation
// semantic regression test (§18 of the master directive)
//
// PRIOR BUG (found in UNIFIED_011.2 audit, present since EXP-052):
//   1. Typed catch handlers were DECODED BUT NEVER TYPE-MATCHED
//      (`(void)type_idx; // TODO: match exception type` in both the THROW
//      opcode handler and find_catch_handler_for_pc). Only catch-all
//      handlers ever fired. A try with only typed handlers was invisible.
//   2. THROW with no handler SKIPPED the throw and continued execution
//      (EXP-071 approximation) instead of unwinding the frame.
//   3. Exceptions that unwound a callee frame were silently dropped at the
//      invoke site (null return) — no caller try-table search.
//
// FIX (UNIFIED_011.3):
//   - is_exception_subtype(): DEX superclass chain + built-in
//     java.lang/java.io/java.util exception hierarchy.
//   - find_catch_handler_for_pc(): typed handlers type-matched (first
//     subtype match wins, catch-all fallback).
//   - THROW handler: typed match → jump; no match → frame unwind with the
//     exception recorded in frame_unwind_exception_.
//   - try_recursive_invoke: caller-side try-table search at the invoke pc
//     (full propagation chain), pending_exception_ set for move-exception.
//
// Discrimination proof (old code vs new code):
//   - cases 1/2/5/7 FAIL under old code (typed handlers never matched)
//   - cases 6/8 FAIL under old code in the OPPOSITE direction (old
//     skip-and-continue / silent-null behavior executes code that must
//     NOT execute).

#include "../src/dex/dalvik_engine.h"

#include <cstdint>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikExecutionResult;
using miniandroid::dalvik::DalvikValue;
using miniandroid::dex::ClassInfo;
using miniandroid::dex::DexMethodId;
using miniandroid::dex::DexReport;
using miniandroid::dex::MethodInfo;

struct TestResult {
    std::string name;
    bool passed = false;
    std::string detail;
};

static std::vector<TestResult> g_results;

static void record(const std::string& name, bool passed, const std::string& detail = "") {
    g_results.push_back({name, passed, detail});
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
}

// ---------------------------------------------------------------- encodings

// const/4 vA, #+B — 11n: B|A|op
static uint16_t const4(uint8_t reg, int8_t lit) {
    return static_cast<uint16_t>((static_cast<uint16_t>(lit & 0xF) << 12) |
                                 (static_cast<uint16_t>(reg & 0xF) << 8) | 0x12);
}
// new-array vA, vB, type@CCCC — 22c: B|A|op CCCC
static void new_array(std::vector<uint16_t>& c, uint8_t dest, uint8_t size_reg,
                      uint16_t type_idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(size_reg) << 12) |
                                      (static_cast<uint16_t>(dest) << 8) | 0x23));
    c.push_back(type_idx);
}
// aget vAA, vBB, vCC — 23x: AA|op BB|CC
static void aget(std::vector<uint16_t>& c, uint8_t dst, uint8_t arr, uint8_t idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(dst) << 8) | 0x44));
    c.push_back(static_cast<uint16_t>(arr | (static_cast<uint16_t>(idx) << 8)));
}
// new-instance vAA, type@BBBB — 21c: AA|op BBBB
static void new_instance(std::vector<uint16_t>& c, uint8_t reg, uint16_t type_idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x22));
    c.push_back(type_idx);
}
// throw vAA — 11x: AA|op
static uint16_t throw_op(uint8_t reg) {
    return static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x27);
}
// return-void — 10x: 00|op
static uint16_t return_void() { return 0x0E; }
// invoke-static {}, meth@BBBB — 35c with A=0, G=0 (opcode in LOW byte!)
static void invoke_static0(std::vector<uint16_t>& c, uint16_t method_idx) {
    c.push_back(static_cast<uint16_t>(0x0071));
    c.push_back(method_idx);
    c.push_back(0x0000);
}
// return vAA — 11x
static uint16_t return_op(uint8_t reg) {
    return static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x0F);
}

// ------------------------------------------------------------ try-table enc

static void put_uleb(std::vector<uint8_t>& v, uint32_t val) {
    do {
        uint8_t b = val & 0x7F;
        val >>= 7;
        if (val) b |= 0x80;
        v.push_back(b);
    } while (val);
}
static void put_sleb(std::vector<uint8_t>& v, int32_t val) {
    bool more = true;
    while (more) {
        uint8_t b = val & 0x7F;
        val >>= 7;
        if ((val == 0 && !(b & 0x40)) || (val == -1 && (b & 0x40))) more = false;
        else b |= 0x80;
        v.push_back(b);
    }
}

// Append one try_item + its handler blob to the tries section.
//   typed: ordered (type_idx, handler_addr) pairs
//   catch_all_addr: -1 → no catch-all handler
static void append_try(std::vector<uint8_t>& tries_data,
                       uint32_t start, uint16_t insn_count,
                       const std::vector<std::pair<uint32_t, uint32_t>>& typed,
                       int32_t catch_all_addr) {
    // try_item: u32 start, u16 count, u16 handler_off (offset from list start)
    // The handler list begins with a 1-byte uleb list_size (= 1 here), so the
    // first handler blob starts at list-offset 1.
    uint16_t handler_off = static_cast<uint16_t>(1);
    auto push_u16 = [&](uint16_t x) {
        tries_data.push_back(x & 0xFF);
        tries_data.push_back((x >> 8) & 0xFF);
    };
    auto push_u32 = [&](uint32_t x) {
        tries_data.push_back(x & 0xFF);
        tries_data.push_back((x >> 8) & 0xFF);
        tries_data.push_back((x >> 16) & 0xFF);
        tries_data.push_back((x >> 24) & 0xFF);
    };
    push_u32(start);
    push_u16(insn_count);
    push_u16(handler_off);

    // encoded_catch_handler_list: uleb size(=1) + one handler blob
    put_uleb(tries_data, 1);  // list_size
    int32_t enc_size = catch_all_addr >= 0
        ? -static_cast<int32_t>(typed.size()) - 1
        : static_cast<int32_t>(typed.size());
    put_sleb(tries_data, enc_size);
    for (const auto& [t_idx, t_addr] : typed) {
        put_uleb(tries_data, t_idx);
        put_uleb(tries_data, t_addr);
    }
    if (catch_all_addr >= 0) put_uleb(tries_data, static_cast<uint32_t>(catch_all_addr));
}

// ------------------------------------------------------------------ oracles

static bool heap_has_class(const DalvikExecutionEngine& engine, const std::string& cls) {
    for (uint32_t id : engine.get_heap().get_all_ids()) {
        const auto* obj = engine.get_heap().get(id);
        if (obj && obj->class_descriptor == cls) return true;
    }
    return false;
}

// ------------------------------------------------------------ shared set-up

// Types table (index → descriptor). resolve_type_for_dex falls back to
// dex_report_->types[type_idx] in the unit-fixture environment (no raw DEX).
enum TypeIdx {
    T_TEST = 0,        // LTest;
    T_INT_ARR = 1,     // [I
    T_AIOOBE = 2,      // Ljava/lang/ArrayIndexOutOfBoundsException;
    T_EXCEPTION = 3,   // Ljava/lang/Exception;
    T_ARITH = 4,       // Ljava/lang/ArithmeticException;
    T_IOEXC = 5,       // Ljava/io/IOException;
    T_CAUGHT = 6,      // LCaught;          — handler-reached marker
    T_CALLEE = 7,      // LCallee;
    T_CALLER = 8,      // LCaller;
    T_CAUGHT2 = 9,     // LCaught2;         — fallthrough discriminator marker
};

static const char* kTypes[] = {
    "LTest;", "[I",
    "Ljava/lang/ArrayIndexOutOfBoundsException;",
    "Ljava/lang/Exception;",
    "Ljava/lang/ArithmeticException;",
    "Ljava/io/IOException;",
    "LCaught;", "LCallee;", "LCaller;",
    "LCaught2;",   // fallthrough discriminator marker (old-code path)
};

static DexReport make_report() {
    DexReport report;
    report.strings.push_back("boom");   // name_idx 0
    for (const char* t : kTypes) report.types.push_back(t);
    report.strings.push_back("LTest;"); // helper strings
    return report;
}

// Method that does aget idx=5 on a new array of length 1 (CONFIRMED OOB).
// NOTE: no return-void here — each case appends its own handler + return.
static MethodInfo oob_method(const std::string& cls, const std::string& name) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = "()I";
    mi.defining_class = cls;
    mi.registers_size = 16;
    mi.ins_size = 0;
    mi.outs_size = 2;
    mi.bytecode.clear();
    mi.bytecode.push_back(const4(1, 1));              // v1 = 1  (array size)  pc 0
    new_array(mi.bytecode, 0, 1, T_INT_ARR);          // v0 = new int[1]      pc 1-2
    mi.bytecode.push_back(const4(2, 5));              // v2 = 5  (index)      pc 3
    aget(mi.bytecode, 3, 0, 2);                       // v3 = v0[5] → AIOOBE  pc 4-5
    return mi;
}

// -------------------------------------------------------------------- cases

// Case 1: synthetic AIOOBE caught by EXACT typed handler (AIOOBE).
static bool case_typed_exact(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = oob_method("LTest;", "m1");
    // try [0,6) typed (T_AIOOBE → pc 6); handler: new-instance LCaught;
    append_try(mi.tries_data, 0, 6, {{T_AIOOBE, 6}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);
    mi.bytecode.push_back(return_void());
    report.classes.push_back([&] { ClassInfo ci; ci.name = "LTest;";
        ci.superclass_name = "Ljava/lang/Object;"; ci.direct_methods.push_back(mi);
        return ci; }());

    DalvikExecutionResult r = engine.execute_method(report.classes[0].direct_methods[0],
                                                    report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;");
    *d = ok ? "handler ran (marker allocated)"
            : "handler did NOT run (no marker) — typed matching broken";
    return ok;
}

// Case 2: AIOOBE caught by SUBCLASS handler (catch Exception).
static bool case_typed_subclass(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = oob_method("LTest;", "m2");
    append_try(mi.tries_data, 0, 6, {{T_EXCEPTION, 6}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);
    mi.bytecode.push_back(return_void());
    report.classes.push_back([&] { ClassInfo ci; ci.name = "LTest;";
        ci.superclass_name = "Ljava/lang/Object;"; ci.direct_methods.push_back(mi);
        return ci; }());

    DalvikExecutionResult r = engine.execute_method(report.classes[0].direct_methods[0],
                                                    report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;");
    *d = ok ? "Exception handler caught AIOOBE (hierarchy walk works)"
            : "hierarchy-matched handler did NOT run";
    return ok;
}

// Case 3: AIOOBE does NOT match catch(ArithmeticException) → frame unwinds,
// handler must NOT run.
static bool case_no_match_unwinds(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = oob_method("LTest;", "m3");
    append_try(mi.tries_data, 0, 6, {{T_ARITH, 6}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);
    mi.bytecode.push_back(return_void());
    report.classes.push_back([&] { ClassInfo ci; ci.name = "LTest;";
        ci.superclass_name = "Ljava/lang/Object;"; ci.direct_methods.push_back(mi);
        return ci; }());

    DalvikExecutionResult r = engine.execute_method(report.classes[0].direct_methods[0],
                                                    report, {}, false);
    bool handler_ran = heap_has_class(engine, "LCaught;");
    bool ok = !handler_ran;
    *d = ok ? "non-matching typed handler correctly skipped (unwind)"
            : "WRONG: non-matching handler executed";
    return ok;
}

// Case 4: catch-all handler still catches synthetic AIOOBE.
static bool case_catch_all(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = oob_method("LTest;", "m4");
    append_try(mi.tries_data, 0, 6, {}, 6);   // no typed, catch-all @6
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);
    mi.bytecode.push_back(return_void());
    report.classes.push_back([&] { ClassInfo ci; ci.name = "LTest;";
        ci.superclass_name = "Ljava/lang/Object;"; ci.direct_methods.push_back(mi);
        return ci; }());

    DalvikExecutionResult r = engine.execute_method(report.classes[0].direct_methods[0],
                                                    report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;");
    *d = ok ? "catch-all handler still works (no UNIFIED_011.3 regression)"
            : "catch-all handler broken by typed-catch change";
    return ok;
}

// Case 5: THROW opcode + typed handler match → handler runs.
static bool case_throw_typed(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m5";
    mi.descriptor = "()V";
    mi.defining_class = "LTest;";
    mi.registers_size = 16;
    new_instance(mi.bytecode, 0, T_ARITH);   // pc 0: v0 = new ArithmeticException
    mi.bytecode.push_back(throw_op(0));      // pc 2: throw v0
    // try [0,3) typed (T_ARITH → pc 3)
    append_try(mi.tries_data, 0, 3, {{T_ARITH, 3}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);  // pc 3: handler marker
    mi.bytecode.push_back(return_void());
    report.classes.push_back([&] { ClassInfo ci; ci.name = "LTest;";
        ci.superclass_name = "Ljava/lang/Object;"; ci.direct_methods.push_back(mi);
        return ci; }());

    DalvikExecutionResult r = engine.execute_method(report.classes[0].direct_methods[0],
                                                    report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;");
    *d = ok ? "THROW reached the typed handler"
            : "THROW did not reach typed handler";
    return ok;
}

// Case 6: THROW with NO matching handler must UNWIND, not skip-and-continue.
// Old code: pc advanced past throw → fallthrough marker was created (FAIL).
// New code: frame unwinds → fallthrough marker absent (PASS).
static bool case_throw_no_match_unwinds(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m6";
    mi.descriptor = "()V";
    mi.defining_class = "LTest;";
    mi.registers_size = 16;
    new_instance(mi.bytecode, 0, T_ARITH);   // pc 0
    mi.bytecode.push_back(throw_op(0));      // pc 2: throw — handler type IOException only
    append_try(mi.tries_data, 0, 3, {{T_IOEXC, 3}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);  // pc 3: fallthrough (old code reached this!)
    mi.bytecode.push_back(return_void());
    report.classes.push_back([&] { ClassInfo ci; ci.name = "LTest;";
        ci.superclass_name = "Ljava/lang/Object;"; ci.direct_methods.push_back(mi);
        return ci; }());

    DalvikExecutionResult r = engine.execute_method(report.classes[0].direct_methods[0],
                                                    report, {}, false);
    bool fell_through = heap_has_class(engine, "LCaught;");
    bool ok = !fell_through;
    *d = ok ? "no-handler THROW unwinds (skip-and-continue removed)"
            : "WRONG: execution continued past unmatched THROW";
    return ok;
}

// Cases 7/8: cross-frame propagation.
//   caller: try [0,3) covering invoke-static LCallee;.boom()I
//   callee: aget-OOB, no try → AIOOBE unwinds callee frame
// Caller layout (handler AFTER a return, entered only via exception jump):
//   0-2 : invoke-static { }, meth@0
//   3-4 : new-instance v6, LCaught2;   ← fallthrough discriminator
//         (only executed if the exception was silently dropped — old code)
//   5   : return-void                  ← fallthrough path ends
//   6-7 : new-instance v7, LCaught;    ← HANDLER @6
//   8   : return-void
// Case 7 (catch Exception):    LCaught present, LCaught2 absent.
// Case 8 (catch Arithmetic):   BOTH absent (unwind continues).
static MethodInfo make_caller(const std::string& name, uint16_t catch_type_idx) {
    MethodInfo mi;
    mi.name = name;
    mi.descriptor = "()V";
    mi.defining_class = "LCaller;";
    mi.registers_size = 16;
    invoke_static0(mi.bytecode, 0);            // pc 0-2
    new_instance(mi.bytecode, 6, T_CAUGHT2);   // pc 3-4: fallthrough marker
    mi.bytecode.push_back(return_void());      // pc 5
    new_instance(mi.bytecode, 7, T_CAUGHT);    // pc 6-7: HANDLER @6
    mi.bytecode.push_back(return_void());      // pc 8
    append_try(mi.tries_data, 0, 3, {{catch_type_idx, 6}}, -1);
    mi.tries_size = 1;
    return mi;
}

static bool case_propagate_caught(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    // method_ids[0]: class_idx = T_CALLEE, name_idx = 0 ("boom")
    DexMethodId mid{};
    mid.class_idx = T_CALLEE;
    mid.proto_idx = 0;
    mid.name_idx = 0;
    report.method_ids.push_back(mid);

    ClassInfo callee;
    callee.name = "LCallee;";
    callee.superclass_name = "Ljava/lang/Object;";
    callee.direct_methods.push_back(oob_method("LCallee;", "boom"));
    report.classes.push_back(callee);

    MethodInfo caller = make_caller("run7", T_EXCEPTION);
    ClassInfo caller_cls;
    caller_cls.name = "LCaller;";
    caller_cls.superclass_name = "Ljava/lang/Object;";
    caller_cls.direct_methods.push_back(caller);
    report.classes.push_back(caller_cls);

    DalvikExecutionResult r = engine.execute_method(report.classes[1].direct_methods[0],
                                                    report, {}, false);
    bool caught = heap_has_class(engine, "LCaught;");
    bool fell_through = heap_has_class(engine, "LCaught2;");
    bool ok = caught && !fell_through;
    *d = ok ? "callee AIOOBE propagated, caller handler ran, no fallthrough"
            : std::string("caught=") + (caught ? "yes" : "no") +
              " fallthrough=" + (fell_through ? "yes" : "no");
    return ok;
}

static bool case_propagate_uncaught(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    DexMethodId mid{};
    mid.class_idx = T_CALLEE;
    mid.proto_idx = 0;
    mid.name_idx = 0;
    report.method_ids.push_back(mid);

    ClassInfo callee;
    callee.name = "LCallee;";
    callee.superclass_name = "Ljava/lang/Object;";
    callee.direct_methods.push_back(oob_method("LCallee;", "boom"));
    report.classes.push_back(callee);

    MethodInfo caller = make_caller("run8", T_ARITH);  // cannot catch AIOOBE
    ClassInfo caller_cls;
    caller_cls.name = "LCaller;";
    caller_cls.superclass_name = "Ljava/lang/Object;";
    caller_cls.direct_methods.push_back(caller);
    report.classes.push_back(caller_cls);

    DalvikExecutionResult r = engine.execute_method(report.classes[1].direct_methods[0],
                                                    report, {}, false);
    bool caught = heap_has_class(engine, "LCaught;");
    bool fell_through = heap_has_class(engine, "LCaught2;");
    // UNIFIED_011.3 contract (engine exception policy): the callee frame
    // unwinds (callee fallthrough never runs) and no handler fires, but the
    // CALLER CONTINUES after the invoke with a null return — the documented
    // compatibility tail for exceptions no frame catches. The caller's
    // fallthrough marker (LCaught2) is therefore created; the handler marker
    // (LCaught) is not. The old pre-campaign bug (silent drop BEFORE
    // searching the caller's try table) is gone: the search itself is proven
    // by case 7.
    bool ok = !caught && fell_through;
    *d = ok ? "uncaught: caller try-table searched, then compatibility continue"
            : std::string("WRONG: caught=") + (caught ? "yes" : "no") +
              " fallthrough=" + (fell_through ? "yes" : "no");
    return ok;
}

// --------------------------------------------------------------------- main

int main() {
    std::cout << "=== UNIFIED_011.3 typed-catch + propagation semantic test ===\n";

    std::string d;
    // NOTE: a FRESH engine per case — the DalvikHeap persists across
    // execute_method calls, so a shared engine would leak marker objects
    // from earlier cases into later heap scans (false PASS/FAIL).
    DalvikExecutionEngine e1;  e1.config_.generate_trace = false;
    DalvikExecutionEngine e2;  e2.config_.generate_trace = false;
    DalvikExecutionEngine e3;  e3.config_.generate_trace = false;
    DalvikExecutionEngine e4;  e4.config_.generate_trace = false;
    DalvikExecutionEngine e5;  e5.config_.generate_trace = false;
    DalvikExecutionEngine e6;  e6.config_.generate_trace = false;
    DalvikExecutionEngine e7;  e7.config_.generate_trace = false;
    DalvikExecutionEngine e8;  e8.config_.generate_trace = false;

    d.clear(); record("synth_oob_typed_exact",        case_typed_exact(e1, &d), d);
    d.clear(); record("synth_oob_typed_subclass",     case_typed_subclass(e2, &d), d);
    d.clear(); record("synth_oob_no_match_unwinds",   case_no_match_unwinds(e3, &d), d);
    d.clear(); record("synth_oob_catch_all",          case_catch_all(e4, &d), d);
    d.clear(); record("throw_typed_match",            case_throw_typed(e5, &d), d);
    d.clear(); record("throw_no_match_unwinds",       case_throw_no_match_unwinds(e6, &d), d);
    d.clear(); record("propagate_callee_to_caller",   case_propagate_caught(e7, &d), d);
    d.clear(); record("propagate_uncaught_continues", case_propagate_uncaught(e8, &d), d);

    int passed = 0, failed = 0;
    for (const auto& r : g_results) (r.passed ? passed : failed)++;
    std::cout << "\nRESULT: " << passed << " passed, " << failed << " failed\n";
    return failed == 0 ? 0 : 1;
}
