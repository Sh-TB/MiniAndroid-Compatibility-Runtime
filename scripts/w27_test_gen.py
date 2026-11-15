#!/usr/bin/env python3
"""Generate tests/s237_append_bounded_law_test.cpp — the W27 battery.

Rows (one per contract face of F-NEW-639):
  r1  the "777" face: append(acc,0,0).append("7").append(acc,1,1) -> "7"
      (pre-law: "777" — the issue #597 root cause)
  r2  the real slice: append("abcdef",2,4) -> "cd"; returns `this`
  r3  bounds: start<0, end>len -> deferred SIOOBE, value unchanged
  r4  bounds: start>end -> deferred SIOOBE, value unchanged
  r5  null sequence in-bounds -> "null" appended; out-of-bounds -> throw
"""
from pathlib import Path

T = r'''// s237_append_bounded_law_test — the W27 battery (issue #597).
//
// F-NEW-639: StringBuilder/StringBuffer.append(CharSequence|char[],
// int start, int end) appends the SLICE [start, end), with the OpenJDK
// bounds law (deferred StringIndexOutOfBoundsException) and the null
// -> "null" face. The generic append arm ignored args[2]/args[3]: both
// bounded appends of a Kotlin replace(String, transform) rebuild
// contributed the full accumulator — the OpenCalc one-tap "777" face.
// Bounds run on the stored UTF-8 BYTE length (the R24 approximation).

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"

#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using miniandroid::dalvik::DalvikExecutionEngine;
using miniandroid::dalvik::DalvikType;
using miniandroid::dalvik::DalvikValue;
namespace flw = miniandroid::framework;
using flw::CallResult;
using flw::ShadowRegistry;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

// Bridge helper: engine.bridge_to_api with a compact verdict.
static bool bridge(DalvikExecutionEngine& e, const std::string& cls,
                   const std::string& m, const std::vector<DalvikValue>& args,
                   DalvikValue& out) {
    miniandroid::dalvik::ApiCallTrace::Status st =
        miniandroid::dalvik::ApiCallTrace::Status::STUBBED;
    return e.bridge_to_api(cls, m, args, out, st, 0);
}

static uint32_t new_sb(DalvikExecutionEngine& engine, const std::string& v) {
    uint32_t sb = engine.get_heap_public().allocate(
        "Ljava/lang/StringBuilder;", 0, 0);
    engine.get_heap_public().set_object_field(
        sb, "sb_value", DalvikValue::make_string(v, 0));
    return sb;
}

static std::string sb_val(DalvikExecutionEngine& engine, uint32_t sb) {
    auto f = engine.get_heap_public().get_object_field(sb, "sb_value");
    return (f.has_value() &&
            f->type == DalvikType::STRING_REF)
               ? f->string_val
               : "<missing>";
}

int main(int argc, char** argv) {
    std::cout << "== s237_append_bounded — the #597 W27 battery ==\n";
    (void)argc; (void)argv;
    DalvikExecutionEngine engine;
    engine.config_.trace_cap = 4000;
    ShadowRegistry registry;
    flw::register_platform_shadows(registry);
    auto heap_adapter = std::make_unique<flw::DalvikHeapAdapter>(
        &engine.get_heap_public(), &engine);
    registry.set_heap(heap_adapter.get());
    engine.set_shadow_registry(&registry);

    // r1 — the "777" face, the EXACT Kotlin rebuild chain from the
    // issue: h("7") does acc="7", one match at pos=0:
    //   sb2.append(acc, 0, 0)   -> ""
    //   sb2.append(newValue "7")-> "7"
    //   sb2.append(acc, 1, 1)   -> ""
    // => "7" (the pre-law generic arm produced "777").
    {
        uint32_t sb = new_sb(engine, "");
        DalvikValue out;
        bool ok1 = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                          {DalvikValue::make_object(
                               sb, "Ljava/lang/StringBuilder;"),
                           DalvikValue::make_string("7", 0),
                           DalvikValue::make_int(0),
                           DalvikValue::make_int(0)},
                          out);
        bool ok2 = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                          {DalvikValue::make_object(
                               sb, "Ljava/lang/StringBuilder;"),
                           DalvikValue::make_string("7", 0)},
                          out);
        bool ok3 = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                          {DalvikValue::make_object(
                               sb, "Ljava/lang/StringBuilder;"),
                           DalvikValue::make_string("7", 0),
                           DalvikValue::make_int(1),
                           DalvikValue::make_int(1)},
                          out);
        record("r1_f639_777_face", ok1 && ok2 && ok3 &&
                                   sb_val(engine, sb) == "7",
               "value=\"" + sb_val(engine, sb) +
                   "\" (the one-tap face: one tap = one digit)");

        // r2 — the real slice + the chaining law (returns `this`).
        uint32_t sb2 = new_sb(engine, "x");
        DalvikValue out2;
        bool ok = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                         {DalvikValue::make_object(
                              sb2, "Ljava/lang/StringBuilder;"),
                          DalvikValue::make_string("abcdef", 0),
                          DalvikValue::make_int(2),
                          DalvikValue::make_int(4)},
                         out2);
        record("r2_f639_slice_chaining",
               ok && sb_val(engine, sb2) == "xcd" &&
                   out2.type == DalvikType::OBJECT_REF &&
                   out2.object_id == sb2,
               "value=\"" + sb_val(engine, sb2) + "\" ret=oid" +
                   std::to_string(out2.object_id) + " (slice [2,4)=\"cd\", "
                   "returns this)");
    }

    // r3 — the bounds law: start < 0 and end > length both defer the
    // StringIndexOutOfBoundsException and leave the buffer unchanged.
    {
        uint32_t sb = new_sb(engine, "ab");
        DalvikValue out;
        bool ok1 = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                          {DalvikValue::make_object(
                               sb, "Ljava/lang/StringBuilder;"),
                           DalvikValue::make_string("abc", 0),
                           DalvikValue::make_int(-1),
                           DalvikValue::make_int(2)},
                          out);
        bool v1 = sb_val(engine, sb) == "ab";
        bool ok2 = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                          {DalvikValue::make_object(
                               sb, "Ljava/lang/StringBuilder;"),
                           DalvikValue::make_string("abc", 0),
                           DalvikValue::make_int(2),
                           DalvikValue::make_int(9)},
                          out);
        bool v2 = sb_val(engine, sb) == "ab";
        record("r3_f639_bounds_throw_unchanged",
               ok1 && ok2 && out.object_id == 0 && v1 && v2,
               "obj#" + std::to_string(out.object_id) +
                   " (0 == the deferred SIOOBE; buffer stayed \"ab\")");
    }

    // r4 — start > end is the third bounds face.
    {
        uint32_t sb = new_sb(engine, "ab");
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                         {DalvikValue::make_object(
                              sb, "Ljava/lang/StringBuilder;"),
                          DalvikValue::make_string("abc", 0),
                          DalvikValue::make_int(2),
                          DalvikValue::make_int(1)},
                         out);
        record("r4_f639_start_gt_end_throw",
               ok && out.object_id == 0 && sb_val(engine, sb) == "ab",
               "obj#" + std::to_string(out.object_id) +
                   " (deferred SIOOBE, buffer unchanged)");
    }

    // r5 — the null-sequence face: append(null, start, end) uses the
    // "null" literal (length 4) for BOTH the slice and the bounds.
    {
        uint32_t sb = new_sb(engine, "");
        DalvikValue out;
        bool ok = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                         {DalvikValue::make_object(
                              sb, "Ljava/lang/StringBuilder;"),
                          DalvikValue::make_null(),
                          DalvikValue::make_int(0),
                          DalvikValue::make_int(4)},
                         out);
        std::string inbounds = sb_val(engine, sb);
        uint32_t sb2 = new_sb(engine, "");
        bool ok2 = bridge(engine, "Ljava/lang/StringBuilder;", "append",
                          {DalvikValue::make_object(
                               sb2, "Ljava/lang/StringBuilder;"),
                           DalvikValue::make_null(),
                           DalvikValue::make_int(0),
                           DalvikValue::make_int(5)},
                          out);
        record("r5_f639_null_sequence",
               ok && inbounds == "null" && ok2 && out.object_id == 0 &&
                   sb_val(engine, sb2) == "",
               "in-bounds=\"" + inbounds + "\" (the literal null); "
               "out-of-bounds obj#" + std::to_string(out.object_id) +
                   " (deferred SIOOBE on len 4)");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
'''

Path("/tmp/w27_int/miniandroid/tests/s237_append_bounded_law_test.cpp").write_text(T)
print("battery written (5 rows)")
