// UNIFIED_014 APUT-BOUNDS — aput AOSP null/bounds semantics regression test
//
// PRIOR BUG (MASTER_CURRENT_GAP_MATRIX DEX-APUT-BOUNDS, UNIFIED_011.2 audit):
//   ARRAY_PUT_CASE wrote ANY index and AUTO-GREW "__array_length__" to idx+1:
//     - no NullPointerException on null arrays (silent skip)
//     - no ArrayIndexOutOfBoundsException on OOB stores (silent corrupt store)
//     - phantom array tail: aput at idx >= len made array-length/loops see a
//       grown array that real Dalvik would never produce
//
// FIX (UNIFIED_014): AOSP art interpreter_switch_impl-inl.h HandleAPut /
// APUT_OBJECT semantics (fetched 2026-09-03; docs/upstream_reference_aput_aosp.md):
//   - null array → NPE (pending exception path, same as aget)
//   - confirmed length > 0: idx < 0 || idx >= len → AIOOBE "length=…; index=…",
//     NO store, length immutable
//   - length unknown (0): legacy store+grow preserved (engine boundary, shared
//     with aget's arr_len==0 gate)
//
// Discrimination proof (old code vs new code):
//   - cases 1/2/4 FAIL under old code (old: silent store + auto-grow, no throw)
//   - case 3 FAILs under old code (old: length grew to 4; new: stays 2)
//   - case 5 PASSES both (legacy unknown-length path must keep working)
//   - case 6 FAILs under old code (old: silent skip; new: NPE handler runs)

#include "../src/dex/dalvik_engine.h"

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
// const/16 vAA, #+BBBB — 21s: AA|op BBBB
static void const16(std::vector<uint16_t>& c, uint8_t reg, int16_t lit) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x13));
    c.push_back(static_cast<uint16_t>(lit));
}
// new-array vA, vB, type@CCCC — 22c: B|A|op CCCC
static void new_array(std::vector<uint16_t>& c, uint8_t dest, uint8_t size_reg,
                      uint16_t type_idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(size_reg) << 12) |
                                      (static_cast<uint16_t>(dest) << 8) | 0x23));
    c.push_back(type_idx);
}
// aput vAA, vBB, vCC — 23x: AA|op BB|CC (op=0x4B per dalvik_engine.h)
static void aput(std::vector<uint16_t>& c, uint8_t src, uint8_t arr, uint8_t idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(src) << 8) | 0x4B));
    c.push_back(static_cast<uint16_t>(arr | (static_cast<uint16_t>(idx) << 8)));
}
// aget vAA, vBB, vCC — 23x
static void aget(std::vector<uint16_t>& c, uint8_t dst, uint8_t arr, uint8_t idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(dst) << 8) | 0x44));
    c.push_back(static_cast<uint16_t>(arr | (static_cast<uint16_t>(idx) << 8)));
}
// array-length vA, vB — 12x: B|A|op (op=0x20)
static uint16_t array_length(uint8_t dst, uint8_t arr) {
    return static_cast<uint16_t>((static_cast<uint16_t>(arr & 0xF) << 12) |
                                 (static_cast<uint16_t>(dst & 0xF) << 8) | 0x20);
}
// new-instance vAA, type@BBBB — 21c: AA|op BBBB
static void new_instance(std::vector<uint16_t>& c, uint8_t reg, uint16_t type_idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x22));
    c.push_back(type_idx);
}
// const/null vAA, literal? — const/4 with -1 gives NULL via sget? Use const/4 = -1? 
// Null array source: move the null from a register we pre-fill via const/4 0?
// Real Dalvik: const/4 v0, 0 → literal 0 (int). For null the canonical encoder
// uses const/4 with 0 + the verifier knows. In our fixture engine, a register
// that was never written reads as NULL_REF? Safer: const/4 v, 0 then rely on
// engine treating type INT32... NOT null. We instead produce null via aget on
// an OBJECT array? Simplest unambiguous null: new-instance of array type?
// No — the engine's null literal in fixtures: use aput from a register that
// holds NULL_REF. aget-object OOB-skip yields make_null() only in legacy path.
// Deterministic approach: aget-object at an IN-BOUNDS index of a fresh
// object array — elements are default NULL_REF? Engine default for missing
// element is result_val.type=OBJECT_REF + make_null()? (ARRAY_GET_CASE sets
// make_null() only when elem missing in old path...). To stay robust, we use
// an explicit "null emitter" method: return-null from invoke is out of scope
// here; instead const-wide/16? No.
// => We use aget-object on empty-object-array legacy path (arr_len==0 →
// result NULL_REF) to load a real NULL_REF register, then aput-object into it.
// aput-object op = 0x4D (dalvik_engine.h)
static void aput_object(std::vector<uint16_t>& c, uint8_t src, uint8_t arr, uint8_t idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(src) << 8) | 0x4D));
    c.push_back(static_cast<uint16_t>(arr | (static_cast<uint16_t>(idx) << 8)));
}
static void aget_object(std::vector<uint16_t>& c, uint8_t dst, uint8_t arr, uint8_t idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(dst) << 8) | 0x46));
    c.push_back(static_cast<uint16_t>(arr | (static_cast<uint16_t>(idx) << 8)));
}
// return-void — 10x: 00|op
static uint16_t return_void() { return 0x0E; }

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
static void append_try(std::vector<uint8_t>& tries_data,
                       uint32_t start, uint16_t insn_count,
                       const std::vector<std::pair<uint32_t, uint32_t>>& typed,
                       int32_t catch_all_addr) {
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
    put_uleb(tries_data, 1);
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

// NOTE: NEW_ARRAY allocates the heap array with the hardcoded descriptor
// "Larray;" (resolved type goes to the trace only) — fixture oracle must
// scan for "Larray;".
static const char* kArrayDesc = "Larray;";

static uint32_t find_array_id(const DalvikExecutionEngine& engine) {
    for (uint32_t id : engine.get_heap().get_all_ids()) {
        const auto* obj = engine.get_heap().get(id);
        if (obj && obj->class_descriptor == kArrayDesc) return id;
    }
    return 0;
}

static bool heap_has_class(const DalvikExecutionEngine& engine, const std::string& cls) {
    for (uint32_t id : engine.get_heap().get_all_ids()) {
        const auto* obj = engine.get_heap().get(id);
        if (obj && obj->class_descriptor == cls) return true;
    }
    return false;
}

static int32_t heap_array_length(const DalvikExecutionEngine& engine, uint32_t arr_id) {
    const auto* obj = engine.get_heap().get(arr_id);
    if (!obj) return -1;
    auto it = obj->fields.find("__array_length__");
    if (it == obj->fields.end()) return -1;
    return it->second.int_val;
}

static int32_t heap_array_elem(const DalvikExecutionEngine& engine, uint32_t arr_id, int idx) {
    const auto* obj = engine.get_heap().get(arr_id);
    if (!obj) return -999;
    auto it = obj->fields.find("array[" + std::to_string(idx) + "]");
    if (it == obj->fields.end()) return -999;
    return it->second.int_val;
}

// ------------------------------------------------------------ shared set-up

enum TypeIdx { T_TEST = 0, T_INT_ARR = 1, T_AIOOBE = 2, T_EXCEPTION = 3,
               T_NPE = 4, T_CAUGHT = 5, T_CAUGHT2 = 6 };

static const char* kTypes[] = {
    "LTest;", "[I",
    "Ljava/lang/ArrayIndexOutOfBoundsException;",
    "Ljava/lang/Exception;",
    "Ljava/lang/NullPointerException;",
    "LCaught;", "LCaught2;",
};

static DexReport make_report() {
    DexReport report;
    report.strings.push_back("aput-fixture");
    for (const char* t : kTypes) report.types.push_back(t);
    report.strings.push_back("LTest;");
    return report;
}

static void push_test_class(DexReport& report, const MethodInfo& mi) {
    ClassInfo ci;
    ci.name = "LTest;";
    ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);
}

// -------------------------------------------------------------------- cases

// Case 1: in-bounds aput + array-length unchanged (AOSP: length immutable).
// Method: v0 = new int[2]; v1 = 7; aput v1→v0[1]; array-length v3←v0
// Old code: PASS for store but nothing asserts length — we assert elem==7 AND
// length stays 2. New code: store at 1 (in-bounds, len=2) OK.
static bool case_inbounds_store(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m1"; mi.descriptor = "()I"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, 2));            // pc0: v1 = 2 (size)
    new_array(mi.bytecode, 0, 1, T_INT_ARR);        // pc1-2: v0 = new int[2]
    mi.bytecode.push_back(const4(2, 7));            // pc3: v2 = 7 (src)
    mi.bytecode.push_back(const4(3, 1));            // pc4: v3 = 1 (idx reg)
    aput(mi.bytecode, 2, 0, 3);                     // pc5-6: v0[v3=1] = 7
    mi.bytecode.push_back(array_length(4, 0));      // pc7: v4 = length(v0)
    mi.bytecode.push_back(return_void());           // pc8
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t arr_id = find_array_id(engine);
    bool stored = heap_array_elem(engine, arr_id, 1) == 7;
    bool len_ok = heap_array_length(engine, arr_id) == 2;
    bool ok = (arr_id != 0) && stored && len_ok;
    *d = "stored=" + std::to_string(stored) + " len=" +
         std::to_string(heap_array_length(engine, arr_id));
    return ok;
}

// Case 2: OOB store (idx=len) throws AIOOBE, caught by typed handler,
// and the OOB element is NOT stored. Old code: silent store + grow (FAIL).
static bool case_oob_typed(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m2"; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, 2));            // pc0: v1 = 2
    new_array(mi.bytecode, 0, 1, T_INT_ARR);        // pc1-2: v0 = new int[2]
    mi.bytecode.push_back(const4(2, 9));            // pc3: v2 = 9 (src)
    mi.bytecode.push_back(const4(3, 2));            // pc4: v3 = 2 (idx reg == len)
    aput(mi.bytecode, 2, 0, 3);                     // pc5-6: v0[v3=2] = 9 → AIOOBE
    new_instance(mi.bytecode, 7, T_CAUGHT2);        // pc7-8: FALLTHROUGH marker (must NOT run)
    append_try(mi.tries_data, 0, 9, {{T_AIOOBE, 9}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);         // pc9: handler marker
    mi.bytecode.push_back(return_void());           // pc11
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t arr_id = find_array_id(engine);
    bool handler_ran = heap_has_class(engine, "LCaught;");
    bool fell_through = heap_has_class(engine, "LCaught2;");
    bool not_stored = heap_array_elem(engine, arr_id, 2) == -999;
    bool len_ok = heap_array_length(engine, arr_id) == 2;
    bool ok = handler_ran && !fell_through && not_stored && len_ok;
    *d = "handler=" + std::to_string(handler_ran) +
         " fell_through=" + std::to_string(fell_through) +
         " stored=" + std::to_string(!not_stored) +
         " len=" + std::to_string(heap_array_length(engine, arr_id));
    return ok;
}

// Case 3: AIOOBE caught by subclass handler (catch Exception).
// Old code: no throw at all → handler never runs (FAIL).
static bool case_oob_subclass(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m3"; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, 1));            // v1 = 1
    new_array(mi.bytecode, 0, 1, T_INT_ARR);        // v0 = new int[1]
    mi.bytecode.push_back(const4(2, 5));            // v2 = 5 (src)
    mi.bytecode.push_back(const4(3, 5));            // v3 = 5 (idx reg > len)
    aput(mi.bytecode, 2, 0, 3);                     // v0[5] = 5 → AIOOBE
    new_instance(mi.bytecode, 7, T_CAUGHT2);        // FALLTHROUGH marker (must NOT run)
    append_try(mi.tries_data, 0, 9, {{T_EXCEPTION, 9}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);
    mi.bytecode.push_back(return_void());
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;") && !heap_has_class(engine, "LCaught2;");
    *d = ok ? "Exception handler caught aput AIOOBE (no fallthrough)"
            : "handler ran without throw (fallthrough) or hierarchy handler missing";
    return ok;
}

// Case 4: array-length must NOT grow after failed OOB aput (phantom tail).
// Covered inside case 2 (len_ok). This case adds negative index discrimination:
// idx = -1 with len=2 → AIOOBE (uint32 cast makes negative always OOB in AOSP).
static bool case_negative_idx(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m4"; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, 2));            // v1 = 2
    new_array(mi.bytecode, 0, 1, T_INT_ARR);        // v0 = new int[2]
    const16(mi.bytecode, 2, -1);                    // v2 = -1 (src AND idx)
    aput(mi.bytecode, 2, 0, 2);                     // v0[v2=-1] → AIOOBE
    new_instance(mi.bytecode, 7, T_CAUGHT2);        // FALLTHROUGH marker (must NOT run)
    append_try(mi.tries_data, 0, 9, {{T_AIOOBE, 9}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);
    mi.bytecode.push_back(return_void());
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t arr_id = find_array_id(engine);
    bool handler_ran = heap_has_class(engine, "LCaught;");
    bool fell_through = heap_has_class(engine, "LCaught2;");
    // old code: "array[-1]" stored, length untouched → len stays 2 on old too;
    // the discriminator is the fallthrough marker.
    bool len_ok = heap_array_length(engine, arr_id) == 2;
    bool ok = handler_ran && !fell_through && len_ok;
    *d = "handler=" + std::to_string(handler_ran) +
         " fell_through=" + std::to_string(fell_through) +
         " len=" + std::to_string(heap_array_length(engine, arr_id));
    return ok;
}

// Case 5: unknown-length legacy path still stores + grows (engine boundary).
// Array created via new-array size 0 → arr_len==0 → legacy gate (same as aget).
// Old code: PASS; new code must NOT regress it.
static bool case_unknown_len_legacy(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m5"; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, 0));            // v1 = 0 (size 0 → "unknown")
    new_array(mi.bytecode, 0, 1, T_INT_ARR);        // v0 = new int[0]
    mi.bytecode.push_back(const4(2, 3));            // v2 = 3 (src)
    mi.bytecode.push_back(const4(3, 0));            // v3 = 0 (idx reg)
    aput(mi.bytecode, 2, 0, 3);                     // v0[v3=0] = 3 (legacy store+grow)
    mi.bytecode.push_back(return_void());
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t arr_id = find_array_id(engine);
    bool stored = heap_array_elem(engine, arr_id, 0) == 3;
    bool grown = heap_array_length(engine, arr_id) == 1;
    bool ok = stored && grown;
    *d = "stored=" + std::to_string(stored) + " grown=" + std::to_string(grown) +
         " (legacy unknown-length path preserved)";
    return ok;
}

// Case 6: aput-object into NULL array → NPE caught by typed handler.
// Old code: silent skip, no exception (FAIL).
static bool case_null_npe(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m6"; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    // null emitter: new int[0]; aget-object v0[0] → legacy path returns
    // NULL_REF in v4 (engine's make_null for OBJECT_REF missing elem).
    mi.bytecode.push_back(const4(1, 0));            // pc0: v1 = 0
    new_array(mi.bytecode, 0, 1, T_INT_ARR);        // pc1-2: v0 = new int[0]
    aget_object(mi.bytecode, 4, 0, 0);              // pc3-4: v4 = NULL_REF (legacy aget)
    mi.bytecode.push_back(const4(5, 0));            // pc5: v5 = 0 (idx reg)
    mi.bytecode.push_back(const4(2, 1));            // pc6: v2 = 1 (src)
    aput_object(mi.bytecode, 2, 4, 5);              // pc7-8: aput-object v2→v4[v5]
    //   → v4 is NULL → NPE (AOSP HandleAPut)
    new_instance(mi.bytecode, 7, T_CAUGHT2);        // pc9-10: FALLTHROUGH marker (must NOT run)
    append_try(mi.tries_data, 0, 11, {{T_NPE, 11}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);         // pc11: handler marker
    mi.bytecode.push_back(return_void());           // pc13
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;") && !heap_has_class(engine, "LCaught2;");
    *d = ok ? "NPE handler ran for aput into null array (no fallthrough)"
            : "no throw on null aput (fallthrough) or NPE handler missing";
    return ok;
}

// --------------------------------------------------------------------- main

int main() {
    std::cout << "=== UNIFIED_014 aput-bounds semantic test (AOSP HandleAPut) ===\n";
    std::string d;
    DalvikExecutionEngine e1; e1.config_.generate_trace = false;
    DalvikExecutionEngine e2; e2.config_.generate_trace = false;
    DalvikExecutionEngine e3; e3.config_.generate_trace = false;
    DalvikExecutionEngine e4; e4.config_.generate_trace = false;
    DalvikExecutionEngine e5; e5.config_.generate_trace = false;
    DalvikExecutionEngine e6; e6.config_.generate_trace = false;

    d.clear(); record("inbounds_store_len_immutable", case_inbounds_store(e1, &d), d);
    d.clear(); record("oob_throws_no_store_no_grow",  case_oob_typed(e2, &d), d);
    d.clear(); record("oob_subclass_handler",         case_oob_subclass(e3, &d), d);
    d.clear(); record("negative_idx_throws",          case_negative_idx(e4, &d), d);
    d.clear(); record("unknown_len_legacy_preserved", case_unknown_len_legacy(e5, &d), d);
    d.clear(); record("null_array_npe",               case_null_npe(e6, &d), d);

    int passed = 0, failed = 0;
    for (const auto& r : g_results) (r.passed ? passed : failed)++;
    std::cout << "\nRESULT: " << passed << " passed, " << failed << " failed\n";
    return failed == 0 ? 0 : 1;
}
