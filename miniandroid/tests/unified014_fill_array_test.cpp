// UNIFIED_014b FILL-ARRAY-DATA — AOSP FillArrayData semantics regression test
//
// PRIOR BUGS (found in UNIFIED_014 cycle #2, same array-bounds chain):
//   1. fill-array-data silently OVERWROTE __array_length__ AND
//      __new_array_length__ with the payload count — real Dalvik NEVER
//      changes array length here (shrink/grow drift: count<len shrank the
//      array, count>len grew it).
//   2. No overflow check: payload count > array length must throw
//      ArrayIndexOutOfBoundsException.
//   3. No null check: fill into null array must throw NullPointerException.
//   4. Silent truncation: fills past 100 elements were silently capped.
//
// REFERENCE (upstream oracle, rule 4/7): AOSP art
// entrypoints/entrypoint_utils.cc FillArrayData()
// (refs/tags/android-14.0.0_r1 lines 176–195, fetched 2026-09-03):
//   - null → NPE "null array in FILL_ARRAY_DATA"
//   - element_count > length → AIOOBE
//     "failed FILL_ARRAY_DATA; length=%d, index=%d" (index=count)
//   - fills exactly element_count elements; length immutable
//
// Discrimination (old code vs new):
//   - case 1 old: length set to count (==len here, so PASSES old too —
//     regression guard)
//   - case 2 old: no throw, fallthrough marker created, length grew to 3 (FAIL)
//   - case 3 old: length SHRANK to 2 (FAIL)
//   - case 4 old: length set to 3 (==len, passes) — regression guard
//   - case 5 old: no throw, fallthrough marker created (FAIL)

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

struct TestResult { std::string name; bool passed = false; std::string detail; };
static std::vector<TestResult> g_results;
static void record(const std::string& name, bool passed, const std::string& detail = "") {
    g_results.push_back({name, passed, detail});
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
}

// ---------------------------------------------------------------- encodings

static uint16_t const4(uint8_t reg, int8_t lit) {
    return static_cast<uint16_t>((static_cast<uint16_t>(lit & 0xF) << 12) |
                                 (static_cast<uint16_t>(reg & 0xF) << 8) | 0x12);
}
static void new_array(std::vector<uint16_t>& c, uint8_t dest, uint8_t size_reg,
                      uint16_t type_idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(size_reg) << 12) |
                                      (static_cast<uint16_t>(dest) << 8) | 0x23));
    c.push_back(type_idx);
}
// fill-array-data vAA, +BBBBBBBB — 31t: AA|op BBBB BBBB (3 code units, op 0x26)
static void fill_array_data(std::vector<uint16_t>& c, uint8_t reg, int16_t offset) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x26));
    c.push_back(static_cast<uint16_t>(offset & 0xFFFF));
    c.push_back(static_cast<uint16_t>((offset >> 16) & 0xFFFF));
}
static void aget_object(std::vector<uint16_t>& c, uint8_t dst, uint8_t arr, uint8_t idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(dst) << 8) | 0x46));
    c.push_back(static_cast<uint16_t>(arr | (static_cast<uint16_t>(idx) << 8)));
}
static void new_instance(std::vector<uint16_t>& c, uint8_t reg, uint16_t type_idx) {
    c.push_back(static_cast<uint16_t>((static_cast<uint16_t>(reg) << 8) | 0x22));
    c.push_back(type_idx);
}
static uint16_t return_void() { return 0x0E; }

// fill-array-data-payload: ident 0x0300, width, count(2 units), raw bytes LE
static void append_payload(std::vector<uint16_t>& c, uint16_t width, uint32_t count,
                           const std::vector<uint8_t>& bytes) {
    c.push_back(0x0300);
    c.push_back(width);
    c.push_back(count & 0xFFFF);
    c.push_back((count >> 16) & 0xFFFF);
    for (size_t i = 0; i < bytes.size(); i += 2) {
        uint16_t w = bytes[i] | (i + 1 < bytes.size() ? static_cast<uint16_t>(bytes[i + 1] << 8) : 0);
        c.push_back(w);
    }
}

// ------------------------------------------------------------ try-table enc

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
    uint16_t handler_off = 1;
    auto push_u16 = [&](uint16_t x) { tries_data.push_back(x & 0xFF); tries_data.push_back((x >> 8) & 0xFF); };
    auto push_u32 = [&](uint32_t x) {
        tries_data.push_back(x & 0xFF); tries_data.push_back((x >> 8) & 0xFF);
        tries_data.push_back((x >> 16) & 0xFF); tries_data.push_back((x >> 24) & 0xFF);
    };
    push_u32(start); push_u16(insn_count); push_u16(handler_off);
    put_uleb(tries_data, 1);
    int32_t enc_size = catch_all_addr >= 0 ? -static_cast<int32_t>(typed.size()) - 1
                                           : static_cast<int32_t>(typed.size());
    put_sleb(tries_data, enc_size);
    for (const auto& [t, a] : typed) { put_uleb(tries_data, t); put_uleb(tries_data, a); }
    if (catch_all_addr >= 0) put_uleb(tries_data, static_cast<uint32_t>(catch_all_addr));
}

// ------------------------------------------------------------------ oracles

static const char* kArrayDesc = "Larray;";  // NEW_ARRAY hardcodes this descriptor

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
static int32_t heap_len(const DalvikExecutionEngine& engine, uint32_t arr_id) {
    const auto* obj = engine.get_heap().get(arr_id);
    if (!obj) return -1;
    auto it = obj->fields.find("__array_length__");
    return it == obj->fields.end() ? -1 : it->second.int_val;
}
static int32_t heap_elem_int(const DalvikExecutionEngine& engine, uint32_t arr_id, int idx) {
    const auto* obj = engine.get_heap().get(arr_id);
    if (!obj) return -999;
    auto it = obj->fields.find("array[" + std::to_string(idx) + "]");
    return it == obj->fields.end() ? -999 : it->second.int_val;
}
static int32_t heap_elem_bool(const DalvikExecutionEngine& engine, uint32_t arr_id, int idx) {
    const auto* obj = engine.get_heap().get(arr_id);
    if (!obj) return -999;
    auto it = obj->fields.find("array[" + std::to_string(idx) + "]");
    if (it == obj->fields.end()) return -999;
    if (it->second.type == miniandroid::dalvik::DalvikType::BOOLEAN) return it->second.bool_val ? 1 : 0;
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
    report.strings.push_back("fill-fixture");
    for (const char* t : kTypes) report.types.push_back(t);
    report.strings.push_back("LTest;");
    return report;
}
static void push_test_class(DexReport& report, const MethodInfo& mi) {
    ClassInfo ci; ci.name = "LTest;"; ci.superclass_name = "Ljava/lang/Object;";
    ci.direct_methods.push_back(mi);
    report.classes.push_back(ci);
}
static MethodInfo base_method(const std::string& name, uint8_t size_lit) {
    MethodInfo mi;
    mi.name = name; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, static_cast<int8_t>(size_lit)));  // pc0: v1 = size
    new_array(mi.bytecode, 0, 1, T_INT_ARR);                          // pc1-2: v0 = new int[size]
    return mi;
}

// -------------------------------------------------------------------- cases

// Case 1: exact fill (count == len, width 4) — elements stored, length kept.
static bool case_exact_fill(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = base_method("m1", 3);
    fill_array_data(mi.bytecode, 0, 4);              // pc3-5, payload at pc7
    mi.bytecode.push_back(return_void());            // pc6
    append_payload(mi.bytecode, 4, 3, {11,0,0,0, 22,0,0,0, 33,0,0,0});
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t a = find_array_id(engine);
    bool ok = heap_elem_int(engine, a, 0) == 11 && heap_elem_int(engine, a, 1) == 22 &&
              heap_elem_int(engine, a, 2) == 33 && heap_len(engine, a) == 3;
    *d = "e0=" + std::to_string(heap_elem_int(engine, a, 0)) +
         " e1=" + std::to_string(heap_elem_int(engine, a, 1)) +
         " e2=" + std::to_string(heap_elem_int(engine, a, 2)) +
         " len=" + std::to_string(heap_len(engine, a));
    return ok;
}

// Case 2: overflow (count 3 > len 2) → AIOOBE, length stays 2, no fallthrough.
static bool case_overflow(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = base_method("m2", 2);
    fill_array_data(mi.bytecode, 0, 8);              // pc3-5, payload at pc11
    new_instance(mi.bytecode, 7, T_CAUGHT2);         // pc6-7: fallthrough marker
    append_try(mi.tries_data, 0, 8, {{T_AIOOBE, 8}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);          // pc8-9: handler
    mi.bytecode.push_back(return_void());            // pc10
    append_payload(mi.bytecode, 4, 3, {1,0,0,0, 2,0,0,0, 3,0,0,0});
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t a = find_array_id(engine);
    bool ok = heap_has_class(engine, "LCaught;") && !heap_has_class(engine, "LCaught2;") &&
              heap_len(engine, a) == 2 && heap_elem_int(engine, a, 0) == -999;
    *d = "handler=" + std::to_string(heap_has_class(engine, "LCaught;")) +
         " fell=" + std::to_string(heap_has_class(engine, "LCaught2;")) +
         " len=" + std::to_string(heap_len(engine, a)) +
         " e0=" + std::to_string(heap_elem_int(engine, a, 0));
    return ok;
}

// Case 3: underfill (count 2 < len 4) — 2 elements stored, length STAYS 4.
static bool case_underfill(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = base_method("m3", 4);
    fill_array_data(mi.bytecode, 0, 4);              // pc3-5, payload at pc7
    mi.bytecode.push_back(return_void());            // pc6
    append_payload(mi.bytecode, 4, 2, {7,0,0,0, 8,0,0,0});
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t a = find_array_id(engine);
    bool ok = heap_elem_int(engine, a, 0) == 7 && heap_elem_int(engine, a, 1) == 8 &&
              heap_elem_int(engine, a, 2) == -999 && heap_len(engine, a) == 4;
    *d = "e0=" + std::to_string(heap_elem_int(engine, a, 0)) +
         " e1=" + std::to_string(heap_elem_int(engine, a, 1)) +
         " e2=" + std::to_string(heap_elem_int(engine, a, 2)) +
         " len=" + std::to_string(heap_len(engine, a)) + " (old shrank to 2)";
    return ok;
}

// Case 4: width-1 boolean payload — byte unpack order (lo byte first).
static bool case_width1_bool(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi = base_method("m4", 3);
    fill_array_data(mi.bytecode, 0, 4);              // pc3-5, payload at pc7
    mi.bytecode.push_back(return_void());            // pc6
    append_payload(mi.bytecode, 1, 3, {1, 0, 1});    // bytes: true,false,true
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    uint32_t a = find_array_id(engine);
    bool ok = heap_elem_bool(engine, a, 0) == 1 && heap_elem_bool(engine, a, 1) == 0 &&
              heap_elem_bool(engine, a, 2) == 1 && heap_len(engine, a) == 3;
    *d = "b0=" + std::to_string(heap_elem_bool(engine, a, 0)) +
         " b1=" + std::to_string(heap_elem_bool(engine, a, 1)) +
         " b2=" + std::to_string(heap_elem_bool(engine, a, 2)) +
         " len=" + std::to_string(heap_len(engine, a));
    return ok;
}

// Case 5: fill into null array → NPE, no fallthrough.
static bool case_null_npe(DalvikExecutionEngine& engine, std::string* d) {
    DexReport report = make_report();
    MethodInfo mi;
    mi.name = "m5"; mi.descriptor = "()V"; mi.defining_class = "LTest;";
    mi.registers_size = 16; mi.ins_size = 0; mi.outs_size = 2;
    mi.bytecode.push_back(const4(1, 0));             // pc0: v1 = 0
    new_array(mi.bytecode, 0, 1, T_INT_ARR);         // pc1-2: v0 = new int[0]
    aget_object(mi.bytecode, 4, 0, 0);               // pc3-4: v4 = NULL_REF (legacy aget)
    fill_array_data(mi.bytecode, 4, 8);              // pc5-7: fill v4 → NPE, payload pc13
    new_instance(mi.bytecode, 7, T_CAUGHT2);         // pc8-9: fallthrough marker
    append_try(mi.tries_data, 0, 10, {{T_NPE, 10}}, -1);
    mi.tries_size = 1;
    new_instance(mi.bytecode, 6, T_CAUGHT);          // pc10-11: handler
    mi.bytecode.push_back(return_void());            // pc12
    append_payload(mi.bytecode, 4, 1, {9,0,0,0});
    push_test_class(report, mi);
    auto r = engine.execute_method(report.classes[0].direct_methods[0], report, {}, false);
    bool ok = heap_has_class(engine, "LCaught;") && !heap_has_class(engine, "LCaught2;");
    *d = ok ? "NPE handler ran (null fill), no fallthrough"
            : "no throw on null fill (fallthrough) or handler missing";
    return ok;
}

// --------------------------------------------------------------------- main

int main() {
    std::cout << "=== UNIFIED_014b fill-array-data semantic test (AOSP FillArrayData) ===\n";
    std::string d;
    DalvikExecutionEngine e1; e1.config_.generate_trace = false;
    DalvikExecutionEngine e2; e2.config_.generate_trace = false;
    DalvikExecutionEngine e3; e3.config_.generate_trace = false;
    DalvikExecutionEngine e4; e4.config_.generate_trace = false;
    DalvikExecutionEngine e5; e5.config_.generate_trace = false;

    d.clear(); record("exact_fill_len_immutable", case_exact_fill(e1, &d), d);
    d.clear(); record("overflow_aioobe_no_fallthrough", case_overflow(e2, &d), d);
    d.clear(); record("underfill_keeps_length", case_underfill(e3, &d), d);
    d.clear(); record("width1_bool_unpack", case_width1_bool(e4, &d), d);
    d.clear(); record("null_fill_npe", case_null_npe(e5, &d), d);

    int passed = 0, failed = 0;
    for (const auto& r : g_results) (r.passed ? passed : failed)++;
    std::cout << "\nRESULT: " << passed << " passed, " << failed << " failed\n";
    return failed == 0 ? 0 : 1;
}
