/*
 * MiniAndroid Runtime v0.2 - Real Dalvik Execution Engine Implementation
 * EXP-030: Real Bytecode Execution
 * 
 * Complete implementation of Dalvik register machine with:
 * - 25+ opcodes executed
 * - Real register state changes
 * - Object heap allocation
 * - Method call stack
 * - API bridge integration
 */

#include "dalvik_engine.h"
#include "dex_parser.h"
#include "mutf8.h"
#include <dlfcn.h>  // #371 PHASE B2: real dlopen/dlerror boundary diagnostics
#include <openssl/evp.h>  // #371 PHASE B2: sha16 file identity for loadLibrary law
#include <atomic>  // CONT-86 F-NEW-390 bounded diag counters
#include "../api/android_stubs.h"
#include "../api/http_client.h"  // S100 NET-001 (MG-247/248): real HTTP(S)
#include "../storage/data_root.h"
#include "../audio/audio_engine.h"  // CONT-65 F-NEW-356: real-decode media law
#include <filesystem>
#include <cstring>  // F-109c: strcmp arith dispatch (S62)
#include "../diagnostics/gfx_trace.h"  // CONT-83 WS-B frame correlation
#include "../diagnostics/mem_probe.h"
#include "../diagnostics/click_audit.h"  // UNIFIED_002 EXP-100: env-gated click audit (DIAGNOSTIC)
#include "../diagnostics/crash_forensics.h"  // S100 §3: last-op ring (issue #345)
#include "../diagnostics/gfx_provenance.h"  // S82-GFX §6: evidence-bit pixel chain
#include "../diagnostics/file_io_trace.h"   // IAPK: file-IO provenance (F-NEW-234 wave)
#include "../diagnostics/install_inspection.h"  // GATE A: zip_contains_entry (System.loadLibrary law)
#include "../jni/jni_bridge.h"
#include "../jni/dlopen_exec.h"  // #371 CLOSEOUT S-2: real native execution layer
#include "../fonts/text_shaper.h"  // F-NEW-344: getDesiredWidth via the SAME
                                   // shaper the drawText replay uses — the
                                   // single source of truth (box == pixels).
#include <nlohmann/json.hpp>  // F-NEW-243: org.json real laws (ordered_json)
// EXP-051: Shadow registry integration.
#include "../framework/shadow_registry.h"
#include <functional>
#include "../framework/android_shadows.h"
#include "../webview/webview_engine.h"
#include "../framework/choreographer_shadow.h"  // R-NEW-345 park-drain: vsync during park
#include "../framework/dialog_shadow.h"
#include "../framework/canvas_shadow.h"

// ─────────────────────────────────────────────────────────────────────────────
// CONT-121 W-01 (FIX-449 endgame): JVM String UTF-16 UNIT LAW helpers.
// Shared by both String.length sites and both String.charAt sites (the C97
// bridge-intrinsic entry and the F-090e deep site).
//
// ROOT (issue #364 F-NEW-449, S36-AOOB telegram play_billing n2.r):
// protobuf-lite's RawMessageInfo info-string decoder walks String.charAt
// under String.length() — both must address UTF-16 CODE UNITS (JVM/AOSP
// law). The engine answered length() as UTF-8 BYTE count and charAt by
// UTF-8 CODE-POINT index. The p3 info string is 40 UTF-16 units but 64
// UTF-8 bytes (12 chars in the Myanmar block are 3 bytes each, 1 unit),
// so the walk loop `i < length()` ran 24 phantom iterations past the real
// data, decoded garbage field descriptors, over-consumed the Object[11]
// entries array, and died at entries[11] (S36-AOOB len=11 idx=11). ASCII-
// only strings have bytes == units == code points, which is why every
// prior anchor stayed byte-identical.
// ─────────────────────────────────────────────────────────────────────────────
namespace {
int32_t str_utf16_unit_count(const std::string& s) {
    int32_t units = 0;
    for (size_t i = 0; i < s.size();) {
        unsigned char b0 = static_cast<unsigned char>(s[i]);
        size_t len = 1;
        if ((b0 & 0xE0) == 0xC0 && i + 1 < s.size()) len = 2;
        else if ((b0 & 0xF0) == 0xE0 && i + 2 < s.size()) len = 3;
        else if ((b0 & 0xF8) == 0xF0 && i + 3 < s.size()) len = 4;
        // 4-byte UTF-8 = supplementary code point = 2 UTF-16 units
        units += (len == 4) ? 2 : 1;
        i += len;
    }
    return units;
}
// Walks to UTF-16 unit `idx`; answers the unit's char value. Returns false
// when idx is outside [0, unit_count) — callers keep the honest-0 OOB rule
// (R-NEW-353 contract unchanged).
bool str_char_at_unit(const std::string& s, int32_t idx, int32_t& out) {
    if (idx < 0) return false;
    int32_t unit = 0;
    for (size_t i = 0; i < s.size();) {
        unsigned char b0 = static_cast<unsigned char>(s[i]);
        size_t len = 1;
        int32_t cp = b0;
        if ((b0 & 0xE0) == 0xC0 && i + 1 < s.size()) {
            len = 2;
            cp = ((b0 & 0x1F) << 6) |
                 (static_cast<unsigned char>(s[i + 1]) & 0x3F);
        } else if ((b0 & 0xF0) == 0xE0 && i + 2 < s.size()) {
            len = 3;
            cp = ((b0 & 0x0F) << 12) |
                 ((static_cast<unsigned char>(s[i + 1]) & 0x3F) << 6) |
                 (static_cast<unsigned char>(s[i + 2]) & 0x3F);
        } else if ((b0 & 0xF8) == 0xF0 && i + 3 < s.size()) {
            len = 4;
            cp = ((b0 & 0x07) << 18) |
                 ((static_cast<unsigned char>(s[i + 1]) & 0x3F) << 12) |
                 ((static_cast<unsigned char>(s[i + 2]) & 0x3F) << 6) |
                 (static_cast<unsigned char>(s[i + 3]) & 0x3F);
        }
        if (cp >= 0x10000) {
            cp -= 0x10000;
            if (unit == idx) {
                out = 0xD800 + (cp >> 10);
                return true;
            }
            if (unit + 1 == idx) {
                out = 0xDC00 + (cp & 0x3FF);
                return true;
            }
            unit += 2;
        } else {
            if (unit == idx) {
                out = cp;
                return true;
            }
            unit += 1;
        }
        i += len;
    }
    return false;
}
}  // namespace

#include "../framework/heap_adapter.h"
#include "../framework/bitmap_shadow.h"  // S109 ROOT-033: getDrawable raster decode
#include "../framework/view_ancestry.h"  // G12 FIX-G12-001: AOSP framework ancestry law
#include "../storage/sqlite_shadow.h"    // M3 F-ROOM-CHAIN: SQLite family shadow
#include "../resources/resource_runtime.h"  // G10 FIX-G10-002: early classifier wiring
#include "../resources/font_family.h"    // C9-16/C9-17 (CODER 9): font-family + weight law
#include "../resources/plurals.h"        // C9-20 (CODER 9): CLDR plural-category law
#include <png.h>                          // C9-7 (CODER 9): Bitmap.compress PNG encode
#include <setjmp.h>                       // C9-7: libpng error contract
#include <chrono>
#include <unordered_map>  // CONT-29 W1: METHOD-CENSUS (env-gated, read-only)
#include <x86intrin.h>  // S61 PERF: __rdtsc phase timers
#include <atomic>
#include <algorithm>
#include <iostream>
#include <malloc.h>
#include <fstream>
#include <regex>
#include <sstream>
#include <iomanip>
#include <cassert>
#include <cctype>    // EXP-071 Phase 6: std::toupper/std::tolower for String.toUpperCase/toLowerCase
#include <fcntl.h>   // LOADING-CAMPAIGN (R-2 FIX): real host fds for openFd/PFD
#include <unistd.h>  // LOADING-CAMPAIGN: ::open/::close/::dup
#include <unordered_set>
#include <set>            // F-023: default-interface-method dispatch visited set

// ────────────────────────────────────────────────────────────────────────
// CONT-96 W1 (F-074 throughput law): diagnostic env presence-checks used
// to call std::getenv() on EVERY interpreter instruction / method entry —
// an environ walk per opcode (measured as a real fraction of the ~310K
// ins/s interpreter wall on the 30s Telegram gate; see the 14530-site
// note for the single-site precedent). Diagnostic flags are
// process-constant: diag_env() caches the first-use answer keyed by the
// literal POINTER (every diagnostic call site passes a string literal;
// literals are stable for the process lifetime). Identical answers,
// identical stderr when a flag is set — only the per-op environ walk is
// gone. Value-using sites (find(getenv(...)), env[0]=='0') keep their
// raw getenv by design.
// ────────────────────────────────────────────────────────────────────────
static bool diag_env(const char* name) {
    struct Entry { const char* name; bool value; };
    static thread_local Entry table[96];
    static thread_local uint32_t count = 0;
    for (uint32_t i = 0; i < count; ++i)
        if (table[i].name == name) return table[i].value;
    const bool v = std::getenv(name) != nullptr;
    if (count < 96) {
        table[count].name = name;
        table[count].value = v;
        ++count;
    }
    return v;
}

#include "dex/dalvik_engine_internal.h"
namespace miniandroid {
namespace dalvik {
std::map<uint32_t, std::vector<CvFlat>>& g_content_values_mirror_ref() {
    static std::map<uint32_t, std::vector<CvFlat>> m;
    return m;
}
std::vector<CvFlat> content_values_flat_snapshot(uint32_t oid) {
    auto& m = g_content_values_mirror_ref();
    auto it = m.find(oid);
    return it == m.end() ? std::vector<CvFlat>{} : it->second;
}
bool field_trace_active(const char* field_name, const char* where,
                               const char* class_desc) {
    static thread_local const char* filter = std::getenv("MINIANDROID_FIELD_TRACE");
    if (!filter) return false;
    std::string f(filter);
    if (f != "1" && f != "all") {
        // CONT-9 W5: qualified "Lcls;.field" form — matches the field's
        // DECLARING class descriptor prefix AND the exact field name.
        // Generic diagnostic targeting (no engine-side R8 knowledge).
        // Qualified form "Lcls;.field": the class part ends at the FIRST
        // ";." boundary (R8 descriptors end with ';').
        size_t dot = f.find(";.");
        if (dot != std::string::npos && class_desc) {
            std::string cls = f.substr(0, dot + 1);
            std::string fld = f.substr(dot + 2);
            std::string cd = class_desc;
            std::string fn = field_name ? field_name : "";
            if (cd.rfind(cls, 0) != 0 || fn != fld) return false;
        } else {
            // R8 renames fields to single letters — match the FIELD NAME or
            // the CALLING METHOD signature so forensics can target e.g.
            // "MainActivity;.e".
            std::string fn = field_name ? field_name : "";
            std::string w = where ? where : "";
            if (fn.find(f) == std::string::npos && w.find(f) == std::string::npos)
                return false;
        }
    }
    static thread_local uint32_t budget = 2000;
    return budget-- > 0;
}
std::string dalvik_value_to_string(const DalvikValue& v) {
    switch (v.type) {
        case DalvikType::INT32:
        case DalvikType::BOOLEAN:
        case DalvikType::CHAR:
            return std::to_string(v.int_val);
        case DalvikType::INT64:
            return std::to_string(v.long_val);
        case DalvikType::FLOAT32:
            return std::to_string(v.float_val);
        case DalvikType::FLOAT64:
            return std::to_string(v.double_val);
        case DalvikType::STRING_REF:
            return "\"" + v.string_val + "\"";
        case DalvikType::OBJECT_REF:
            return "obj#" + std::to_string(v.object_id);
        default:
            return "<unset>";
    }
}

std::map<std::string, uint64_t> g_d7_read_census;
uint64_t g_d7_draws = 0;


// ============================================================================
// DalvikValue Serialization
// ISSUE-612 WAVE-3 PILOT EXTRACTION (the smallest independent family):
// these two pure member functions touch NO file-local state — only their
// own fields + nlohmann::json. Default (DALVIK_MODULAR=0, monolithic
// fallback): defined HERE. DALVIK_MODULAR=1: defined in
// dex/dalvik_value_glue.cpp instead. The paired #ifndef/#ifdef guards
// guarantee exactly one definition in every mode (no ODR duplication).
// ============================================================================
#ifndef MINIANDROID_DALVIK_MODULAR
std::string DalvikValue::to_string() const {
    switch (type) {
        case DalvikType::INT32: return std::to_string(int_val);
        case DalvikType::INT64: return std::to_string(long_val) + "L";
        case DalvikType::FLOAT32: return std::to_string(float_val) + "f";
        case DalvikType::FLOAT64: return std::to_string(double_val) + "d";
        case DalvikType::BOOLEAN: return bool_val ? "true" : "false";
        case DalvikType::STRING_REF: return "\"" + string_val + "\"";
        case DalvikType::OBJECT_REF: return class_desc + "#" + std::to_string(object_id);
        case DalvikType::CLASS_REF: return "[class] " + class_desc;
        case DalvikType::NULL_REF: return "null";
        case DalvikType::VOID_: return "void";
        case DalvikType::UNINITIALIZED:
        case DalvikType::REGISTER_UNSET: return "<uninit>";
        default: return "<???>";
    }
}
#endif  // MINIANDROID_DALVIK_MODULAR (fallback: body stays in the monolith)

#ifndef MINIANDROID_DALVIK_MODULAR
json DalvikValue::to_json() const {
    json j;
    j["type"] = [this]() -> std::string {
        switch (type) {
            case DalvikType::INT32: return "int32";
            case DalvikType::INT64: return "int64";
            case DalvikType::FLOAT32: return "float";
            case DalvikType::FLOAT64: return "double";
            case DalvikType::STRING_REF: return "string";
            case DalvikType::OBJECT_REF: return "object";
            case DalvikType::CLASS_REF: return "class";
            case DalvikType::NULL_REF: return "null";
            case DalvikType::BOOLEAN: return "boolean";
            case DalvikType::VOID_: return "void";
            default: return "uninit";
        }
    }();
    
    switch (type) {
        case DalvikType::INT32: j["value"] = int_val; break;
        case DalvikType::INT64: j["value"] = long_val; break;
        case DalvikType::FLOAT32: j["value"] = float_val; break;
        case DalvikType::FLOAT64: j["value"] = double_val; break;
        case DalvikType::BOOLEAN: j["value"] = bool_val; break;
        case DalvikType::STRING_REF: 
            j["value"] = string_val; 
            j["ref_id"] = ref_id;
            break;
        case DalvikType::OBJECT_REF:
            j["class"] = class_desc;
            j["object_id"] = object_id;
            break;
        case DalvikType::CLASS_REF:
            j["descriptor"] = class_desc;
            j["ref_id"] = ref_id;
            break;
        case DalvikType::NULL_REF: j["is_null"] = true; break;
        default: j["value"] = nullptr; break;
    }
    return j;
}
#endif  // MINIANDROID_DALVIK_MODULAR (fallback: body stays in the monolith)

// ============================================================================
// Constructor/Destructor
// ============================================================================

// ────────────────────────────────────────────────────────────────────────
// F-NEW-590 (W10) — the JNI engine-query hooks. The native-exec JNI layer
// (dlopen_exec.cpp) serves GetStatic<Prim>Field + GetDirectBufferAddress
// through these: the JNI TU cannot see the engine's static storage or the
// heap, so the ENGINE answers. Installed at construction (last engine
// wins — one engine per process in every observed run).
// Static-field law: name-keyed DEX static first (sorted-key determinism —
// the unordered map iterates arbitrarily; the FIRST sorted key wins so a
// repeat run answers identically), then the REAL display configuration
// for the four Flutter display statics. The display law reuses the
// engine's own constants: 1080x1920 software target (the measure spec the
// view tree runs under — [DEX-MEASURE] rows) + the device density 2.625
// (DensityContext law) + the AOSP 60fps software frame clock. This is NOT
// a fabricated value: it is the same configuration every other display
// consumer in the engine answers with — the single source of truth.
// ────────────────────────────────────────────────────────────────────────
static DalvikExecutionEngine* g_f590_engine = nullptr;

static bool f590_static_lookup(DalvikExecutionEngine* e,
                               const std::string& name, DalvikValue& out) {
    if (!e || name.empty()) return false;
    // name-keyed search over the static storage ("<class>.<name>" keys).
    const std::string suffix = "." + name;
    std::vector<std::pair<std::string, DalvikValue>> hits;
    e->f590_for_each_static([&](const std::string& key, const DalvikValue& v) {
        if (key.size() > suffix.size() &&
            key.compare(key.size() - suffix.size(), suffix.size(), suffix) == 0)
            hits.emplace_back(key, v);
    });
    if (hits.empty()) return false;
    std::sort(hits.begin(), hits.end(),
              [](const auto& a, const auto& b) { return a.first < b.first; });
    out = hits.front().second;
    static thread_local uint64_t n = 0;
    if (n++ < 8)
        std::cerr << "[F-NEW-590] static " << hits.front().first
                  << " -> DEX storage" << std::endl;
    return true;
}

bool DalvikExecutionEngine::f590_static_float(const std::string& name,
                                              float* out) {
    if (!out) return false;
    DalvikValue v;
    if (f590_static_lookup(this, name, v)) {
        if (v.type == DalvikType::FLOAT32) { *out = v.float_val; return true; }
        if (v.type == DalvikType::FLOAT64) { *out = (float)v.double_val; return true; }
        if (v.type == DalvikType::INT32)   { *out = (float)v.int_val; return true; }
    }
    // the REAL display configuration (single source of truth — see the
    // comment block above; 1080x1920 @ 2.625 density, 60fps clock).
    if (name == "refreshRateFPS") { *out = 60.0f; return true; }
    if (name == "displayWidth")   { *out = 1080.0f; return true; }
    if (name == "displayHeight")  { *out = 1920.0f; return true; }
    if (name == "displayDensity") { *out = 2.625f; return true; }
    return false;
}
bool DalvikExecutionEngine::f590_static_int(const std::string& name,
                                            int32_t* out) {
    if (!out) return false;
    DalvikValue v;
    if (f590_static_lookup(this, name, v)) {
        if (v.type == DalvikType::INT32) { *out = v.int_val; return true; }
        if (v.type == DalvikType::BOOLEAN) { *out = v.bool_val ? 1 : 0; return true; }
    }
    return false;
}
bool DalvikExecutionEngine::f590_static_long(const std::string& name,
                                             int64_t* out) {
    if (!out) return false;
    DalvikValue v;
    if (f590_static_lookup(this, name, v)) {
        if (v.type == DalvikType::INT64) { *out = v.long_val; return true; }
        if (v.type == DalvikType::INT32) { *out = v.int_val; return true; }
    }
    return false;
}
bool DalvikExecutionEngine::f590_static_bool(const std::string& name,
                                             uint8_t* out) {
    if (!out) return false;
    DalvikValue v;
    if (f590_static_lookup(this, name, v)) {
        if (v.type == DalvikType::BOOLEAN) { *out = v.bool_val ? 1 : 0; return true; }
        if (v.type == DalvikType::INT32)   { *out = v.int_val != 0; return true; }
    }
    return false;
}
bool DalvikExecutionEngine::f590_static_double(const std::string& name,
                                               double* out) {
    if (!out) return false;
    DalvikValue v;
    if (f590_static_lookup(this, name, v)) {
        if (v.type == DalvikType::FLOAT64) { *out = v.double_val; return true; }
        if (v.type == DalvikType::FLOAT32) { *out = v.float_val; return true; }
    }
    return false;
}

bool DalvikExecutionEngine::f590_direct_buffer_snapshot(uint32_t oid,
                                                        void** addr,
                                                        size_t* cap) {
    if (!addr || !cap || oid == 0) return false;
    DalvikHeap& heap = get_heap_public();
    if (!heap.has_object(oid)) return false;
    // ── S188-W18 F-NEW-605: the DIRECT fast path ─────────────────────────
    // A ByteBuffer minted from a native NewDirectByteBuffer (or carrying a
    // native pixel surface, Gdx2DPixmap.load) stores the REAL pointer in
    // __bb_addr__ — serve it verbatim (no snapshot copy: the pointer IS
    // the memory, and a copy would lie about the address identity).
    auto addr_v = heap.get_object_field(oid, "__bb_addr__");
    if (addr_v.has_value() && addr_v->type == DalvikType::INT64 &&
        addr_v->long_val != 0) {
        auto cap_v = heap.get_object_field(oid, "__bb_cap__");
        size_t bcap = (cap_v.has_value() && cap_v->type == DalvikType::INT32 &&
                       cap_v->int_val > 0)
                          ? (size_t)cap_v->int_val
                          : 0;
        *addr = (void*)(uintptr_t)addr_v->long_val;
        *cap = bcap;
        static thread_local uint64_t n = 0;
        if (n++ < 8)
            std::cerr << "[F-NEW-605] direct-buffer oid=" << oid
                      << " served REAL addr=" << *addr << " cap=" << bcap
                      << " (no copy)" << std::endl;
        // F-NEW-622: REAL identity — the caller must not copy
        miniandroid::nativeexec::f590_served_real_identity = true;
        return true;
    }
    // ── S196 F-NEW-582 (C3, S199 integration): the ENGINE-MINTED direct
    // fast path ─────────────────────────────────────────────────────────
    // allocateDirect/newDisposableByteBuffer minted a REAL calloc'd backing
    // and stored it in __bb_direct__ (+ __bb_direct_cap__). Serve the REAL
    // pointer verbatim — same identity law as the __bb_addr__ path above:
    // the put/get mirror laws, BufferUtils.copyJni and the FreeType natives
    // all read/write THIS memory, so a snapshot copy would hand GL a
    // different (stale/zero) buffer than the one the app filled. This is
    // the ONE shared registry on this line: C3's S196 engine-mint path and
    // the W18 native-mint path both answer through this hook (S195 audit
    // integration decision — no second registry).
    {
        auto dv = heap.get_object_field(oid, "__bb_direct__");
        if (dv.has_value() && dv->type == DalvikType::INT64 &&
            dv->long_val != 0) {
            auto cv2 = heap.get_object_field(oid, "__bb_direct_cap__");
            int32_t dcap = (cv2.has_value() && cv2->type == DalvikType::INT32)
                               ? cv2->int_val
                               : 0;
            if (dcap < 0) dcap = 0;
            if (dcap <= (16 << 20)) {
                *addr = (void*)(uintptr_t)dv->long_val;
                *cap = (size_t)dcap;
                static thread_local uint64_t n = 0;
                if (n++ < 8)
                    std::cerr << "[F-NEW-582] direct-buffer oid=" << oid
                              << " served REAL engine-mem addr=" << *addr
                              << " cap=" << dcap << " (no copy)" << std::endl;
                // F-NEW-622: REAL identity — the caller must not copy
                miniandroid::nativeexec::f590_served_real_identity = true;
                return true;
            }
            static thread_local uint64_t n2 = 0;
            if (n2++ < 4)
                std::cerr << "[F-NEW-582] direct-buffer oid=" << oid
                          << " cap=" << dcap << " exceeds the 16MB bound — "
                             "answering honestly (no buffer)" << std::endl;
            return false;
        }
    }
    // ── S199 W19a F-NEW-619 — TYPED-VIEW PARENT CHASE at the hook ───────
    // GetDirectBufferAddress(view) must answer the PARENT's real memory.
    // The pre-619 hook took the __bb_b{i}__ snapshot leg for a typed view
    // (fresh malloc of the view's own — empty — element fields): the real
    // libgdx.so AndroidGL20 natives (glVertexAttribPointer/glBufferData —
    // dispatched through the JNI table, NOT the GLES20 static bridge)
    // then bound zeroed snapshot pointers for the SHAPE mesh and the draw
    // rasterized nothing (tictactoe board lines missing). AOSP/ART law:
    // GetDirectBufferAddress on a view answers the view's effective base
    // = the parent's direct address (+ the view's own offset, 0 here);
    // the caller adds buffer.position() itself.
    {
        uint32_t cur = oid;
        for (int hop = 0; hop < 4 && cur != 0; ++hop) {
            if (!heap.has_object(cur)) break;
            auto pv = heap.get_object_field(cur, "__bb_parent__");
            if (!pv.has_value() || pv->type != DalvikType::OBJECT_REF ||
                pv->object_id == 0)
                break;
            cur = pv->object_id;
            auto pav = heap.get_object_field(cur, "__bb_addr__");
            if (pav.has_value() && pav->type == DalvikType::INT64 &&
                pav->long_val != 0) {
                auto pcv = heap.get_object_field(cur, "__bb_cap__");
                int32_t pcap = (pcv.has_value() &&
                                pcv->type == DalvikType::INT32)
                                   ? pcv->int_val
                                   : 0;
                *addr = (void*)(uintptr_t)pav->long_val;
                *cap = (size_t)(pcap > 0 ? pcap : 0);
                static thread_local uint64_t n = 0;
                if (n++ < 8)
                    std::cerr << "[F-NEW-619] view oid=" << oid
                              << " chased parent oid=" << cur
                              << " → REAL addr=" << *addr << " cap=" << *cap
                              << std::endl;
                // F-NEW-622: REAL identity — the caller must not copy
                miniandroid::nativeexec::f590_served_real_identity = true;
                return true;
            }
            auto pdv = heap.get_object_field(cur, "__bb_direct__");
            if (pdv.has_value() && pdv->type == DalvikType::INT64 &&
                pdv->long_val != 0) {
                auto pcv = heap.get_object_field(cur, "__bb_direct_cap__");
                int32_t pcap = (pcv.has_value() &&
                                pcv->type == DalvikType::INT32)
                                   ? pcv->int_val
                                   : 0;
                if (pcap > (16 << 20)) return false;  // honest bound
                *addr = (void*)(uintptr_t)pdv->long_val;
                *cap = (size_t)(pcap > 0 ? pcap : 0);
                static thread_local uint64_t n = 0;
                if (n++ < 8)
                    std::cerr << "[F-NEW-619] view oid=" << oid
                              << " chased parent oid=" << cur
                              << " → REAL engine-mem addr=" << *addr
                              << " cap=" << *cap << std::endl;
                // F-NEW-622: REAL identity — the caller must not copy
                miniandroid::nativeexec::f590_served_real_identity = true;
                return true;
            }
        }
    }
    auto cap_v = heap.get_object_field(oid, "__bb_cap__");
    int32_t bcap = (cap_v.has_value() && cap_v->type == DalvikType::INT32)
                       ? cap_v->int_val : 0;
    if (bcap < 0) bcap = 0;
    // bound: platform messages are small; a pathological cap (>16MB) fails
    // honestly instead of freezing the run on 4M field lookups.
    if (bcap > (16 << 20)) {
        static thread_local uint64_t n = 0;
        if (n++ < 4)
            std::cerr << "[F-NEW-590] direct-buffer oid=" << oid
                      << " cap=" << bcap << " exceeds the 16MB snapshot "
                         "bound — answering honestly (no buffer)" << std::endl;
        return false;
    }
    uint8_t* buf = (uint8_t*)malloc((size_t)bcap + 1);
    if (!buf) return false;
    memset(buf, 0, (size_t)bcap + 1);
    for (int32_t i = 0; i < bcap; ++i) {
        auto bv = heap.get_object_field(oid, "__bb_b" + std::to_string(i) + "__");
        if (bv.has_value() && bv->type == DalvikType::INT32)
            buf[i] = (uint8_t)(bv->int_val & 0xff);
    }
    *addr = buf;
    *cap = (size_t)bcap;
    static thread_local uint64_t n = 0;
    if (n++ < 8)
        std::cerr << "[F-NEW-590] direct-buffer oid=" << oid
                  << " snapshot cap=" << bcap << " (REAL malloc memory)"
                  << std::endl;
    // F-NEW-622: snapshot arm — NOT a real identity; the 609 persistent
    // copy path in the caller owns the stability of this malloc.
    miniandroid::nativeexec::f590_served_real_identity = false;
    return true;
}

// ── S188-W18 F-NEW-605: primitive-array critical family ────────────────
// The JNI criticals (slots 222/223) need byte-packed contiguous memory;
// the DEX heap stores arrays as name-keyed "array[i]" fields. Snapshot
// packs; write-back commits with per-element memcmp skip (the encodedData
// face is released unmodified) and per-element TYPE PRESERVATION (the
// F-028 law: float[] elements may sit as FLOAT32 values or INT32 raw
// bits — a committed element keeps the storage convention it had).
namespace {

// Byte-packed element size per array descriptor.
inline size_t w18_elem_bytes(const std::string& desc) {
    if (desc == "[J") return 8;
    if (desc == "[I" || desc == "[F") return 4;
    if (desc == "[S" || desc == "[C") return 2;
    return 1;  // [B and everything else honest-bounded
}

inline uint32_t w18_array_count(DalvikHeap& heap, uint32_t oid) {
    auto len_v = heap.get_object_field(oid, "__array_length__");
    if (len_v.has_value() && len_v->type == DalvikType::INT32 &&
        len_v->int_val >= 0)
        return (uint32_t)len_v->int_val;
    return 0;
}

}  // namespace

bool DalvikExecutionEngine::f590_primitive_array(uint32_t oid, void** addr,
                                                 size_t* byte_len) {
    if (!addr || !byte_len || oid == 0) return false;
    DalvikHeap& heap = get_heap_public();
    if (!heap.has_object(oid)) {
        static thread_local uint64_t n = 0;
        if (n++ < 6)
            std::cerr << "[F-NEW-606] critical oid=" << oid
                      << " rejected: not live on the DEX heap" << std::endl;
        return false;
    }
    std::string desc;
    if (!heap.get_object_class(oid, desc) || desc.empty() || desc[0] != '[') {
        static thread_local uint64_t n = 0;
        if (n++ < 6) {
            std::string d2;
            bool got = heap.get_object_class(oid, d2);
            std::cerr << "[F-NEW-606] critical oid=" << oid
                      << " rejected: not a primitive array (desc="
                      << (got ? d2 : std::string("<unrecorded>")) << ")"
                      << std::endl;
        }
        return false;
    }
    if (desc == "[L" || desc.size() > 1 && desc[1] == 'L') {
        static thread_local uint64_t n = 0;
        if (n++ < 6)
            std::cerr << "[F-NEW-606] critical oid=" << oid << " " << desc
                      << " rejected: object array (not a primitive critical)"
                      << std::endl;
        return false;  // object arrays are not primitive criticals
    }
    const uint32_t count = w18_array_count(heap, oid);
    if (count == 0) {
        static thread_local uint64_t n = 0;
        if (n++ < 6)
            std::cerr << "[F-NEW-606] critical oid=" << oid << " " << desc
                      << " rejected: no recorded length" << std::endl;
        return false;
    }
    const size_t eb = w18_elem_bytes(desc);
    const size_t total = (size_t)count * eb;
    // bound: pixmaps/asset buffers are ≤ a few MB; a pathological count
    // fails honestly instead of freezing the run on millions of lookups.
    if (total > (32u << 20)) {
        static thread_local uint64_t n = 0;
        if (n++ < 4)
            std::cerr << "[F-NEW-605] array oid=" << oid << " " << desc
                      << " total=" << total
                      << "B exceeds the 32MB critical bound — honest fail"
                      << std::endl;
        return false;
    }
    uint8_t* buf = (uint8_t*)malloc(total ? total : 1);
    if (!buf) return false;
    std::memset(buf, 0, total);
    // F-NEW-606 ELEMENT-TYPE-FAMILY law: a heap element of width N may
    // carry its value under ANY of the storage conventions the engine's
    // own producers use (aput-byte → BYTE/byte_val, aput-char → CHAR,
    // aput-short → SHORT, aput-boolean → BOOLEAN, InputStream.read →
    // make_byte, StreamTokenizer → make_char; aget's K-41 conversion
    // already reads this whole family). The pre-606 snapshot read ONLY
    // INT32/INT64/FLOAT32 — the 31435B icons.png snapshot arrived as
    // ZEROS, the real gdx2d_load failed, and the commit pass then WROTE
    // ZEROS back over the live PNG bytes (data destruction, caught by
    // the "commit 31435/31435 changed" tell). Snapshot now reads the
    // family; commit compares the family and writes the element back in
    // the array's descriptor-canonical make_* form (the same convention
    // aput/stream producers use) — no representation drift, no loss.
    for (uint32_t i = 0; i < count; ++i) {
        auto v = heap.get_object_field(oid, "array[" + std::to_string(i) + "]");
        uint8_t* dst = buf + (size_t)i * eb;
        if (!v.has_value()) continue;
        switch (eb) {
            case 8:
                if (v->type == DalvikType::INT64)
                    std::memcpy(dst, &v->long_val, 8);
                else if (v->type == DalvikType::FLOAT64)
                    std::memcpy(dst, &v->double_val, 8);
                else if (v->type == DalvikType::INT32) {
                    int64_t w = v->int_val;
                    std::memcpy(dst, &w, 8);
                }
                break;
            case 4:
                if (v->type == DalvikType::FLOAT32)
                    std::memcpy(dst, &v->float_val, 4);
                else if (v->type == DalvikType::INT32)
                    std::memcpy(dst, &v->int_val, 4);
                break;
            case 2: {
                int32_t x = 0;
                if (v->type == DalvikType::INT32) x = v->int_val;
                else if (v->type == DalvikType::SHORT) x = v->short_val;
                else if (v->type == DalvikType::CHAR) x = (int32_t)(uint8_t)v->char_val;
                uint16_t h = desc == "[C" ? (uint16_t)(uint32_t)x
                                          : (uint16_t)(int16_t)x;
                std::memcpy(dst, &h, 2);
                break;
            }
            case 1: {
                int32_t x = 0;
                if (v->type == DalvikType::INT32) x = v->int_val;
                else if (v->type == DalvikType::BYTE) x = v->byte_val;
                else if (v->type == DalvikType::BOOLEAN) x = v->bool_val ? 1 : 0;
                *dst = (uint8_t)x;
                break;
            }
        }
    }
    *addr = buf;
    *byte_len = total;
    static thread_local uint64_t n = 0;
    if (n++ < 12)
        std::cerr << "[F-NEW-605] array oid=" << oid << " " << desc
                  << " snapshot " << count << " elems (" << total
                  << "B, REAL malloc copy)" << std::endl;
    return true;
}

bool DalvikExecutionEngine::f590_primitive_array_write(uint32_t oid,
                                                       const void* data,
                                                       size_t byte_len) {
    if (!data || oid == 0 || byte_len == 0) return false;
    DalvikHeap& heap = get_heap_public();
    if (!heap.has_object(oid)) return false;
    std::string desc;
    if (!heap.get_object_class(oid, desc) || desc.empty() || desc[0] != '[' ||
        (desc.size() > 1 && desc[1] == 'L'))
        return false;
    const uint32_t count = w18_array_count(heap, oid);
    const size_t eb = w18_elem_bytes(desc);
    if (count == 0 || (size_t)count * eb > byte_len) return false;
    const uint8_t* src = (const uint8_t*)data;
    uint32_t committed = 0;
    for (uint32_t i = 0; i < count; ++i) {
        const std::string fname = "array[" + std::to_string(i) + "]";
        const uint8_t* s = src + (size_t)i * eb;
        auto cur = heap.get_object_field(oid, fname);
        // per-element skip: identical content → no map write. F-NEW-606:
        // the compare reads the FULL element-type family (BYTE/BOOLEAN
        // for [B, SHORT/CHAR for width-2, FLOAT64 for [D) — a typed
        // element that CONTENT-MATCHES must never count as "changed",
        // otherwise the commit pass rewrites live data (the 31435/31435
        // tell that preceded the type-family law).
        if (cur.has_value()) {
            bool same = false;
            switch (eb) {
                case 8:
                    same = (cur->type == DalvikType::INT64 &&
                            std::memcmp(&cur->long_val, s, 8) == 0) ||
                           (cur->type == DalvikType::FLOAT64 &&
                            std::memcmp(&cur->double_val, s, 8) == 0) ||
                           (cur->type == DalvikType::INT32 && [&] {
                                int64_t w = cur->int_val;
                                return std::memcmp(&w, s, 8) == 0;
                            }());
                    break;
                case 4:
                    same = (cur->type == DalvikType::FLOAT32 &&
                            std::memcmp(&cur->float_val, s, 4) == 0) ||
                           (cur->type == DalvikType::INT32 &&
                            std::memcmp(&cur->int_val, s, 4) == 0);
                    break;
                case 2: {
                    uint16_t h = (uint16_t)(*s | ((*(s + 1)) << 8));
                    int32_t x;
                    switch (cur->type) {
                        case DalvikType::INT32: x = cur->int_val; break;
                        case DalvikType::SHORT: x = cur->short_val; break;
                        case DalvikType::CHAR:
                            x = (int32_t)(uint8_t)cur->char_val;
                            break;
                        default: x = -1; break;
                    }
                    same = desc == "[C"
                               ? x == (int32_t)h
                               : x == (int32_t)(int16_t)h;
                    break;
                }
                case 1: {
                    int32_t x;
                    switch (cur->type) {
                        case DalvikType::INT32: x = cur->int_val; break;
                        case DalvikType::BYTE: x = cur->byte_val; break;
                        case DalvikType::BOOLEAN:
                            x = cur->bool_val ? 1 : 0;
                            break;
                        default: x = -1; break;
                    }
                    same = x == (int32_t)(int8_t)*s;
                    break;
                }
            }
            if (same) continue;
        }
        // F-NEW-606: the element goes back in the array's
        // descriptor-canonical make_* form — exactly the convention the
        // engine's own producers (aput-byte/char/short/boolean,
        // InputStream.read, STREAM-READ) store with, so aget's K-41
        // conversion keeps reading the array without type drift.
        switch (eb) {
            case 8: {
                if (desc == "[D") {
                    double d;
                    std::memcpy(&d, s, 8);
                    heap.set_object_field(oid, fname,
                                          DalvikValue::make_double(d));
                } else {
                    int64_t w;
                    std::memcpy(&w, s, 8);
                    heap.set_object_field(
                        oid, fname, DalvikValue::make_long(w));
                }
                break;
            }
            case 4: {
                if (desc == "[F") {
                    float f;
                    std::memcpy(&f, s, 4);
                    heap.set_object_field(oid, fname,
                                          DalvikValue::make_float(f));
                } else {
                    int32_t x;
                    std::memcpy(&x, s, 4);
                    heap.set_object_field(oid, fname,
                                          DalvikValue::make_int(x));
                }
                break;
            }
            case 2: {
                int16_t h;
                std::memcpy(&h, s, 2);
                if (desc == "[C")
                    heap.set_object_field(
                        oid, fname,
                        DalvikValue::make_char((char)(h & 0xFF)));
                else
                    heap.set_object_field(
                        oid, fname, DalvikValue::make_short(h));
                break;
            }
            case 1: {
                if (desc == "[Z")
                    heap.set_object_field(oid, fname,
                                          DalvikValue::make_bool(*s != 0));
                else
                    heap.set_object_field(
                        oid, fname,
                        DalvikValue::make_byte((int8_t)*s));
                break;
            }
        }
        ++committed;
    }
    static thread_local uint64_t n = 0;
    if (n++ < 12)
        std::cerr << "[F-NEW-605] array oid=" << oid << " " << desc
                  << " commit " << committed << "/" << count
                  << " changed elements" << std::endl;
    return true;
}

DalvikExecutionEngine::DalvikExecutionEngine()
    // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): VirtualDispatcher requires a
    // MethodResolver* in its constructor (no default ctor). The previous code
    // relied on a default ctor that never existed. We pass nullptr for now;
    // vtable_dispatcher_ is currently unused (the dispatch_virtual_call path
    // was removed because it referenced API surface that does not exist).
    // When BLOCKER-002 (method_ids parsing) and BLOCKER-003 (field_ids parsing)
    // land, a real MethodResolver will be wired in here.
    : vtable_dispatcher_(nullptr) {
    phase_clock().on = std::getenv("MINIANDROID_PERF_PHASES") != nullptr;  // S61 PERF
    if (phase_clock().on) {
        atexit([] {
            // S61 PERF: per-opcode histogram (the dtor never runs; print here).
            OpHistogram& h = op_hist();
            std::vector<std::pair<uint64_t, int>> tops;
            for (int o = 0; o < 256; ++o) {
                uint64_t v = h.ns[o].load();
                if (v > 0) tops.push_back({v, o});
            }
            std::sort(tops.begin(), tops.end(), std::greater<>());
            fprintf(stderr, "[PERF-OPS] top opcodes by ticks:\n");
            for (size_t k = 0; k < tops.size() && k < 12; ++k) {
                fprintf(stderr, "  op=0x%02x calls=%-9llu ticks=%-13llu est_ms=%llu\n",
                        tops[k].second, (unsigned long long)h.count[tops[k].second].load(),
                        (unsigned long long)tops[k].first,
                        (unsigned long long)(tops[k].first / 3000000ULL));
            }
            fflush(stderr);
            auto pr = [](const char* name, const PhaseClock::Phase& ph) {
                fprintf(stderr, "[PERF-PHASE] %-24s calls=%-10llu ticks=%-14llu\n",
                        name, (unsigned long long)ph.calls.load(),
                        (unsigned long long)ph.ns.load());
            };
            pr("execute_method_internal", phase_clock().invoke_internal);
            pr("try_recursive_invoke", phase_clock().recursive_invoke);
            pr("bridge_to_api", phase_clock().bridge);
            pr("fetch_decode_exec", phase_clock().fetch_exec);
            pr("is_subclass_of", phase_clock().subclass);
            pr("chain_overrides", phase_clock().overrides);
        pr("tri.resolve", phase_clock().invoke_resolve);
        pr("tri.execute", phase_clock().invoke_execute);
        pr("tri.native", phase_clock().invoke_native);
        pr("tri.bridge", phase_clock().invoke_bridge);
        pr("em.setup", phase_clock().em_setup);
        pr("em.fetch", phase_clock().em_fetch);
        pr("em.pop", phase_clock().em_pop);
        pr("resolve_field", phase_clock().resolve_field_ph);
        pr("class_init", phase_clock().class_init_ph);
        pr("sget.resolve", phase_clock().sget_resolve_ph);
        pr("sget.init", phase_clock().sget_init_ph);
        pr("sget.tail", phase_clock().sget_tail_ph);
        pr("insn.pre", phase_clock().insn_pre);
        pr("insn.sw_non", phase_clock().insn_sw_non);
        pr("insn.sw_inv", phase_clock().insn_sw_inv);
        pr("insn.post", phase_clock().insn_post);
        fprintf(stderr, "[PERF-CI] warm=%llu skipfw=%llu cold=%llu\n",
                (unsigned long long)phase_clock().ci_warm.load(),
                (unsigned long long)phase_clock().ci_skipfw.load(),
                (unsigned long long)(phase_clock().class_init_ph.calls.load()
                                     - phase_clock().ci_warm.load()
                                     - phase_clock().ci_skipfw.load()));
            fflush(stderr);
        });
    }
    log("DalvikExecutionEngine initialized");

    // F-NEW-590 (W10): install the JNI engine-query hooks (static-field
    // reads + direct-buffer snapshots) — the JNI TU calls back into THIS
    // engine's storage/heap. Last-constructed engine wins.
    g_f590_engine = this;
    {
        nativeexec::EngineHooks hooks;
        hooks.static_float = [](const char*, const char* name,
                                float* out) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_static_float(name ? name : "", out);
        };
        hooks.static_int = [](const char*, const char* name,
                              int32_t* out) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_static_int(name ? name : "", out);
        };
        hooks.static_long = [](const char*, const char* name,
                               int64_t* out) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_static_long(name ? name : "", out);
        };
        hooks.static_bool = [](const char*, const char* name,
                               uint8_t* out) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_static_bool(name ? name : "", out);
        };
        hooks.static_double = [](const char*, const char* name,
                                 double* out) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_static_double(name ? name : "", out);
        };
        hooks.direct_buffer = [](uint32_t oid, void** addr,
                                 size_t* cap) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_direct_buffer_snapshot(oid, addr, cap);
        };
        // S188-W18 F-NEW-605: the primitive-array critical family (JNI
        // slots 222/223) — Matrix4 + Gdx2DPixmap snapshot/commit.
        hooks.primitive_array = [](uint32_t oid, void** addr,
                                   size_t* byte_len) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_primitive_array(oid, addr, byte_len);
        };
        hooks.primitive_array_write = [](uint32_t oid, const void* data,
                                         size_t byte_len) -> bool {
            return g_f590_engine &&
                   g_f590_engine->f590_primitive_array_write(oid, data,
                                                             byte_len);
        };
        nativeexec::set_engine_hooks(hooks);
    }

    // ── F-NEW-251 (CONT-7 §13A): SHARED FIELD-IDENTITY RESOLVER ───────────
    // LAW: one logical instance field owns ONE storage slot across every
    // execution layer. The interpreter (iput/iget) and the Unsafe R337 path
    // address DEX-declared fields by the S134 F-NEW-160 qualified key
    // "<declarer>-><name>"; shadow-layer hooks (Atomic*FieldUpdater family
    // via the HeapAdapter, and any future bare-name consumer) address them
    // by bare name. Before this resolver the two shapes forked PARALLEL
    // slots for the same field — the dooz SemaphoreImpl._availablePermits
    // split-brain (bare slot stayed stale at 1 while the qualified slot
    // moved 1->0 under lock) desynchronized the kotlinx release() guard
    // and fired IllegalStateException "The number of released permits
    // cannot be greater than 1" on the FIRST unlock (Lek1;.b pc=268).
    // The heap applies the resolver centrally: bare-name writes land in the
    // qualified slot when the field is a DEX-declared instance field of the
    // receiver's class chain; bare-name reads fall back to it. Engine-
    // synthetic fields ("ordinal", "array[i]", "__*") and framework-owned
    // objects keep bare keys (S134 law: framework classes own their fields).
    heap_.set_field_key_resolver(
        [this](const std::string& cls, const std::string& name)
            -> std::string {
            if (!DalvikHeap::is_resolvable_bare_name(name)) return "";
            if (cls.empty() || cls[0] != 'L') return "";  // arrays/atoms
            if (!is_dex_defined_class(cls)) return "";    // framework-owned
            std::string decl = resolved_field_declarer(cls, name);
            if (decl.empty()) return "";
            // A declarer equal to the receiver class still proves nothing
            // unless the walk actually FOUND the field in a DEX body —
            // resolved_field_declarer returns the input class as-is when
            // nothing matched; distinguish by re-checking the chain.
            bool found = false;
            std::string walk = cls;
            for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
                if (!is_dex_defined_class(walk)) break;
                auto cit = class_info_index_.find(walk);
                if (cit != class_info_index_.end() && dex_report_ != nullptr) {
                    for (const auto& f :
                         dex_report_->classes[cit->second].instance_fields) {
                        if (f.name == name) { found = true; break; }
                    }
                }
                if (found) break;
                auto sit = class_to_superclass_.find(walk);
                walk = (sit != class_to_superclass_.end()) ? sit->second
                                                           : std::string();
            }
            if (!found) return "";  // not a DEX-declared field: keep bare
            return walk + "->" + name;  // `walk` = the DEX declarer
        });
}

DalvikExecutionEngine::~DalvikExecutionEngine() {
    log("DalvikExecutionEngine destroyed");
}

// EXP-039 (BLOCKER-035): Build class→DEX index map by searching each DEX's
// class_defs[] table for the class descriptor.
//
// For each DEX file's raw bytes, we parse the class_defs[] table and extract
// the class_idx → type descriptor. If the descriptor matches a class in the
// merged report, we record the DEX index.
//
// This is the CORRECT way to determine which DEX file owns a class.
void DalvikExecutionEngine::build_class_dex_index(const dex::DexReport& report) {
    class_to_dex_index_.clear();
    if (per_dex_raw_data_.empty()) {
        // Single DEX — all classes belong to DEX 0
        for (const auto& cls : report.classes) {
            class_to_dex_index_[cls.name] = 0;
        }
        log("Single DEX — mapped " + std::to_string(class_to_dex_index_.size()) + " classes to DEX 0");
        // UNIFIED_011.3 TYPED-CATCH: do NOT return early. Direct
        // execute_method callers (unit fixtures, tools) have empty
        // per_dex_raw_data_ and previously never reached the class→
        // superclass map (EXP-068) and class→ClassInfo index (EXP-045)
        // below — so try_recursive_invoke could never dispatch any DEX
        // method ("class not in index") and typed-catch hierarchy walks
        // had no superclass data. Fall through to the shared build.
    } else {

    // For each DEX file, parse its class_defs[] and build a set of class descriptors
    for (uint32_t di = 0; di < per_dex_raw_data_.size(); di++) {
        const auto& raw = per_dex_raw_data_[di];
        if (raw.size() < sizeof(dex::DexHeader)) continue;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        uint32_t cd_size = hdr.class_defs_size;
        uint32_t cd_off = hdr.class_defs_off;

        // Each DexClassDef is 32 bytes
        for (uint32_t ci = 0; ci < cd_size; ci++) {
            size_t cd_entry_off = cd_off + ci * 32;  // sizeof(DexClassDef) = 32
            if (cd_entry_off + 32 > raw.size()) break;

            // Read class_idx (first 4 bytes of DexClassDef)
            uint32_t class_idx;
            std::memcpy(&class_idx, raw.data() + cd_entry_off, 4);

            // Resolve class_idx → type_ids[class_idx] → descriptor string
            if (class_idx >= hdr.type_ids_size) continue;
            size_t tid_off = hdr.type_ids_off + class_idx * 4;  // type_ids are 4 bytes each
            if (tid_off + 4 > raw.size()) continue;

            uint32_t descriptor_idx;
            std::memcpy(&descriptor_idx, raw.data() + tid_off, 4);

            // Resolve descriptor string
            std::string descriptor = read_dex_string_from_raw(raw, descriptor_idx, hdr);

            if (!descriptor.empty() && descriptor[0] == 'L') {
                // Only assign if not already mapped (first DEX wins — but
                // classes shouldn't be duplicated across DEX files)
                if (class_to_dex_index_.find(descriptor) == class_to_dex_index_.end()) {
                    class_to_dex_index_[descriptor] = di;
                }
            }
        }
    }
    }  // else (per-DEX raw data present)

    // Assign DEX 0 to any remaining unmapped classes (safety fallback)
    uint32_t unmapped = 0;
    for (const auto& cls : report.classes) {
        if (class_to_dex_index_.find(cls.name) == class_to_dex_index_.end()) {
            class_to_dex_index_[cls.name] = 0;
            unmapped++;
        }
    }

    log("Built class→DEX index: " + std::to_string(class_to_dex_index_.size()) +
        " entries (" + std::to_string(unmapped) + " unmapped, assigned to DEX 0)");

    // EXP-068: Build class→superclass map from report.classes.
    // This enables semantic View inheritance queries (is_subclass_of).
    // NOTE: The APK's DEX only contains class_defs for classes DEFINED in the APK.
    // Framework classes (android.widget.LinearLayout, etc.) are referenced via
    // type_idx but their class_defs are not in the APK. So we pre-populate the
    // map with the known Android framework View hierarchy.
    class_to_superclass_.clear();
    // F-103 (S58, R-NEW-378): reset the declared-interfaces index alongside.
    class_to_interfaces_.clear();
    // Framework View hierarchy (from AOSP). F-107a: table above is
    // trivially destructible — no guard, no cleanup thunk.
    for (size_t fwv = 0; fwv < kNumFrameworkViews; ++fwv) {
        class_to_superclass_[kFrameworkViews[fwv].k] = kFrameworkViews[fwv].v;
    }
    // F-NEW-218 CLASS-TOKEN HIERARCHY LAW (OpenJDK Class.java declaration):
    // java.lang.Class extends Object and implements Type, AnnotatedElement,
    // GenericDeclaration, TypeVariable and Serializable. Every Class token
    // (const-class / getClass / forName result) must satisfy `token
    // instanceof Object/Type/AnnotatedElement/...` exactly like ART. The
    // Gson type-resolution family ($Gson$Types.getRawType → check-cast
    // Type / instanceof Type chains) walks these edges on every app that
    // serializes through Gson (opencalculator vc53 face).
    class_to_superclass_["Ljava/lang/Class;"] = "Ljava/lang/Object;";
    class_to_interfaces_["Ljava/lang/Class;"] = {
        "Ljava/lang/reflect/Type;",
        "Ljava/lang/reflect/AnnotatedElement;",
        "Ljava/lang/reflect/GenericDeclaration;",
        "Ljava/lang/reflect/TypeVariable;",
        "Ljava/io/Serializable;",
    };
    // Now add APK-defined classes from the DEX report.
    // F-NEW-224 (user campaign §B): the hierarchy map is keyed/stored in the
    // ONE canonical descriptor form — dotted or bare superclass spellings
    // from toolchain drift are normalized at INGESTION, not at every walk.
    int apk_class_count = 0;
    for (const auto& cls : report.classes) {
        if (!cls.superclass_name.empty()) {
            class_to_superclass_[framework::normalize_class_desc(cls.name)] =
                framework::normalize_class_desc(cls.superclass_name);
            apk_class_count++;
        }
        // F-087 (R-NEW-313): index runtime-visible class annotations for
        // the Class.getAnnotation bridge.
        if (!cls.class_annotations.empty()) {
            class_annotations_[cls.name] = cls.class_annotations;
        }
        // F-103 (S58, R-NEW-378): index declared interfaces for the
        // Class.isInstance/isAssignableFrom assignability walk.
        if (!cls.interfaces.empty()) {
            class_to_interfaces_[cls.name] = cls.interfaces;
        }
    }
    std::cerr << "[EXP068] Built class→superclass map: " << class_to_superclass_.size()
              << " entries (" << apk_class_count << " from APK + "
              << (class_to_superclass_.size() - apk_class_count) << " framework)"
              << " — LinearLayout present: "
              << (class_to_superclass_.count("Landroid/widget/LinearLayout;") ? "YES" : "NO")
              << std::endl;

    // G10 FIX-G10-002: wire the DEX-backed superclass classifier into the
    // resource inflater IMMEDIATELY (not only at render time) so the
    // inflate-time measure pass (setContentView) classifies custom and
    // framework containers by their REAL ancestors. Without this the first
    // measure of a ViewSwitcher/custom ViewGroup ran through the legacy
    // substring fallback (e.g. billthefarmer's FAB switcher measured 0x0
    // before the render-time re-measure corrected it).
    {
        auto& rt = resources::ResourceRuntime::instance();
        // M3 FIX-M3-001: register at the ResourceRuntime (process-wide
        // Factory law), NOT on the lazy default inflater instance —
        // ensure_loaded() recreates the inflater and the per-instance
        // hook was silently wiped (the classifier fell back to substring
        // matching for the AUTHORITATIVE window measure while the render
        // pass re-asserted the DEX classifier — cross-pass divergence).
        rt.set_is_a([this](const std::string& c, const std::string& a) {
            return is_subclass_of(c, a);
        });
    }

    // EXP-045 Phase 2: Build O(1) class→ClassInfo index for try_recursive_invoke().
    class_info_index_.clear();
    class_info_index_.reserve(report.classes.size());
    for (size_t i = 0; i < report.classes.size(); i++) {
        class_info_index_[report.classes[i].name] = i;
    }
    log("Built class→ClassInfo index: " + std::to_string(class_info_index_.size()) + " entries");
    // F-NEW-271 LAW DIAG (env-gated MINIANDROID_CLASS_FIELD_DUMP=<Ldesc;>,
    // one-shot, read-only): dump the ENGINE-PARSED declared field table of
    // one class — the authoritative view resolve_field_declarer and the
    // collapse-family audit reason over. Answers "does the engine's
    // class_data walk produce the same field list a spec-faithful walk
    // produces" without any app knowledge.
    if (const char* f271_cls = std::getenv("MINIANDROID_CLASS_FIELD_DUMP")) {
        std::string want(f271_cls);
        for (size_t i = 0; i < report.classes.size(); i++) {
            if (report.classes[i].name != want) continue;
            const auto& ci = report.classes[i];
            std::cerr << "[F271-CLASS] " << ci.name
                      << " super=" << ci.superclass_name
                      << " static=" << ci.static_fields.size()
                      << " instance=" << ci.instance_fields.size()
                      << std::endl;
            for (const auto& f : ci.instance_fields)
                std::cerr << "[F271-CLASS]   ifield " << f.name << " : "
                          << f.type << std::endl;
            break;
        }
    }
}

// EXP-088+ Phase 1.2: Inject ALL classes from secondary DEX files into
// the merged dex_report_->classes vector and update class_info_index_.
//
// Background:
//   stage_parse_dex() in execution_engine.cpp only parses classes.dex (DEX 0)
//   into result.dex_report. The other DEX files (classes2..classesN) are
//   loaded into per_dex_raw_data_ but their classes are NEVER merged into
//   dex_report.classes.
//   This means class_info_index_ only contains DEX 0 classes. Any class
//   defined in DEX 1+ (e.g. Telegram's UserConfig in classes3.dex) cannot
//   be found by try_recursive_invoke, which silently returns false and
//   the call is dropped (treated as "class not in index").
//
// This fix parses each secondary DEX file with DexParser, takes its classes,
// and injects them into dex_report_->classes (via const_cast — same pattern
// as the existing on-demand injection at line 826-855). We also update
// class_info_index_ for O(1) lookup.
//
// The original DEX 0 classes already in dex_report_->classes are preserved
// (we only append). Duplicates are detected via class_info_index_.
//
// This is the GENERIC fix for multi-DEX class resolution. It is NOT
// Telegram-specific — any multi-DEX APK benefits.
size_t DalvikExecutionEngine::inject_secondary_dex_classes() {
    if (!dex_report_) {
        log("inject_secondary_dex_classes: dex_report_ is null — skipping");
        return 0;
    }
    if (per_dex_raw_data_.size() <= 1) {
        // Single-DEX APK — nothing to inject.
        return 0;
    }

    // We modify dex_report_->classes via const_cast. The original DexReport
    // is owned by the caller (ExecutionEngine) which keeps it alive for the
    // full execution. The injected ClassInfo entries are read-only data
    // produced by DexParser::parse_data() — they're safe to retain.
    auto& mutable_classes = const_cast<std::vector<dex::ClassInfo>&>(dex_report_->classes);

    size_t injected_count = 0;
    size_t skipped_duplicate = 0;

    // Iterate over secondary DEX files (skip index 0 — that's DEX 0 which
    // is already parsed and present in dex_report_->classes).
    for (uint32_t di = 1; di < per_dex_raw_data_.size(); di++) {
        const auto& raw = per_dex_raw_data_[di];
        if (raw.empty()) continue;

        // Parse this DEX file with DexParser
        dex::DexParser parser;
        // Disable verbose logging for the secondary DEX parse to avoid
        // spamming the log (we may have many secondary DEX files).
        parser.set_verbose(false);
        auto single_report = parser.parse_data(raw, "DEX" + std::to_string(di));

        if (!single_report.is_valid) {
            log("inject_secondary_dex_classes: DEX " + std::to_string(di) +
                " parse failed — skipping (" + single_report.validation_error + ")");
            continue;
        }

        log("inject_secondary_dex_classes: DEX " + std::to_string(di) +
            " parsed — " + std::to_string(single_report.classes.size()) + " classes");

        // Append each class to dex_report_->classes and update index
        for (auto& cls : single_report.classes) {
            // Skip duplicates (a class might be defined in multiple DEX files
            // — rare, but R8/proguard can produce duplicates)
            if (class_info_index_.find(cls.name) != class_info_index_.end()) {
                skipped_duplicate++;
                continue;
            }
            mutable_classes.push_back(std::move(cls));
            size_t new_idx = mutable_classes.size() - 1;
            class_info_index_[mutable_classes.back().name] = new_idx;
            injected_count++;
        }
    }

    log("inject_secondary_dex_classes: injected " + std::to_string(injected_count) +
        " classes from " + std::to_string(per_dex_raw_data_.size() - 1) +
        " secondary DEX files (" + std::to_string(skipped_duplicate) + " duplicates skipped)");
    std::cerr << "[EXP088-MD-INJECT] Injected " << injected_count
              << " classes from secondary DEX files ("
              << skipped_duplicate << " duplicates skipped)"
              << " — total classes now: " << mutable_classes.size()
              << std::endl;

    // Update DEX report aggregate counts so they reflect the merged state
    const_cast<uint32_t&>(dex_report_->classes_count) = (uint32_t)mutable_classes.size();

    // EXP-095 (CM-019): Re-register ALL classes (original + injected) in the
    // superclass map. The map is built BEFORE multi-DEX injection runs, so
    // classes from secondary DEX files (e.g. SlideView → LinearLayout in
    // classes3.dex) were missing — breaking is_subclass_of for every
    // secondary-DEX class (layout detection, instanceof checks).
    {
        size_t added = 0;
        for (const auto& cls : mutable_classes) {
            if (!cls.superclass_name.empty()) {
                // F-NEW-224: same canonical-form ingestion as the primary map.
                const std::string key224 = framework::normalize_class_desc(cls.name);
                const std::string val224 = framework::normalize_class_desc(cls.superclass_name);
                if (class_to_superclass_.find(key224) == class_to_superclass_.end()) {
                    added++;
                }
                class_to_superclass_[key224] = val224;
            }
        }
        std::cerr << "[EXP095-HIER] superclass map extended by " << added
                  << " secondary-DEX classes (total "
                  << class_to_superclass_.size() << ")" << std::endl;
    }

    // ────────────────────────────────────────────────────────────────────
    // S102 LAW 1 — MULTIDEX-INTERFACE-CLOSURE (F-103 extension).
    //   Upstream: art::Class::IsAssignable walks the interface closure of
    //   the class regardless of WHICH classes.dex file defines it — a
    //   check-cast / instanceof against an interface must see the
    //   implements-set of every DEX in the APK.
    //   Root-gap evidence (mentalmath v?, fresh S102 run): the multidex
    //   injection patched the superclass map (EXP-095) but left the F-103
    //   declared-interfaces index DEX-0-only, so every class defined in
    //   classes2.dex+ answered FALSE for castability to its own declared
    //   interfaces. First hit: kotlinx.coroutines FastServiceLoader
    //   .loadMainDispatcherFactory — the dex declares
    //   Lkotlinx/coroutines/android/AndroidDispatcherFactory; implements
    //   Lkotlinx/coroutines/internal/MainDispatcherFactory; (verified by
    //   direct class_def walk) but Class.cast(Object) threw CCE
    //   "AndroidDispatcherFactory cannot be cast to MainDispatcherFactory"
    //   → the catch-all fell into the ServiceLoader fallback →
    //   "list(...) must not be null" NPE → Dispatchers.Main dead →
    //   lifecycleScope dead → MainActivity.onCreate dead [APP-BOUNDARY].
    //   Affected classes in this APK alone: 10,002 secondary-DEX classes
    //   (4,708 declaring interfaces). Every multidex APK with
    //   LifecycleOwner/Comparable/Runnable casts shares the family.
    // ────────────────────────────────────────────────────────────────────
    {
        size_t ifaces_added = 0;
        for (const auto& cls : mutable_classes) {
            if (!cls.interfaces.empty() &&
                class_to_interfaces_.find(cls.name) == class_to_interfaces_.end()) {
                class_to_interfaces_[cls.name] = cls.interfaces;
                ifaces_added++;
            }
        }
        std::cerr << "[S102-IFACE-CLOSURE] declared-interfaces index extended by "
                  << ifaces_added << " secondary-DEX classes (total "
                  << class_to_interfaces_.size() << ")" << std::endl;
    }

    // ────────────────────────────────────────────────────────────────────
    // F-087 MULTIDEX-ANNOTATION-CLOSURE (CONT-26; S102/EXP-095 family).
    //   Upstream: ART copies runtime-visible class annotations
    //   (annotations_directory_item, visibility=RUNTIME) into the Class
    //   object at load time REGARDLESS of which classesN.dex defines the
    //   class — Class.getAnnotation cannot see a DEX-file boundary
    //   (libcore Class.java: annotatedClasses resolved per loaded class).
    //   Root-gap evidence (CONT-26 oracle run, com.probe.oracle12 at
    //   e980887e39aee977): the F-087 class_annotations index was populated
    //   ONLY from DEX 0 (dalvik_engine.cpp primary ingestion loop), so
    //   every class defined in classes2.dex+ answered NULL for its own
    //   runtime annotations. First hit: navigation-compose
    //   NavigatorProvider.Companion.getNameForNavigator →
    //   Class.getAnnotation(@Navigator.Name) on NavGraphNavigator
    //   (classes2.dex, annotation verified present with vis=1
    //   value="navigation" by scripts/cont26_dex_ann_scan.py) → IAE
    //   "No @Navigator.Name annotation found for NavGraphNavigator" →
    //   rememberNavController dead → NavHost dead → composition never
    //   completes. Affected surface: EVERY multi-DEX APK's annotations
    //   (this oracle: all androidx classes live in classes2.dex).
    //   Fix is the third member of the EXP-095 (superclass) + S102
    //   (interfaces) closure family: same loop, same dedup law, no
    //   app/package/R8-name knowledge.
    // ────────────────────────────────────────────────────────────────────
    {
        size_t ann_added = 0;
        for (const auto& cls : mutable_classes) {
            if (!cls.class_annotations.empty() &&
                class_annotations_.find(cls.name) ==
                    class_annotations_.end()) {
                class_annotations_[cls.name] = cls.class_annotations;
                ann_added++;
            }
        }
        std::cerr << "[F087-MD-ANN] class-annotation index extended by "
                  << ann_added << " secondary-DEX classes (total "
                  << class_annotations_.size() << ")" << std::endl;
    }

    return injected_count;
}

// ============================================================================
// CODER7 WAVE-6 (issue #520; S185 SQLITE RULE #536): LoadedApk-lite —
// FOREIGN APK CODE INGESTION.
//
// AOSP law: frameworks/base/core/java/android/app/LoadedApk.java — every
// installed package owns a LoadedApk with its own ClassLoader, and
// ActivityThread.handleReceiver/handleCreateService deliver components
// cross-package by LOADING the target package's code and running the REAL
// component class. WAVE-5 resolved foreign components from the package
// index and honestly did not execute them (issue #520 W5.7 limitation #1:
// "the foreign dex is not loaded by this engine"). This method is the
// generic fix: it parses every store APK's DEX files and injects the
// classes into the SAME merged class index (class_info_index_ +
// superclass/interfaces/annotations closure maps) the running app uses —
// the exact mechanics of inject_secondary_dex_classes() above, generalized
// from per-APK to per-STORE (S185 LOAD-FIRST clause: milestone 0 = full
// load; the dispatch sites below then run real foreign bytecode).
//
// Dedup law (no-shadow): a class the RUNNING package defines wins — AOSP
// resolves through the app's own ClassLoader first; the store can never
// shadow it. Skipped duplicates are counted, never silent.
//
// Honesty laws: a missing store APK or a failed DEX parse records a loud
// C7-STORE-DEX ok=false row and leaves the dispatch fallback (the WAVE-5
// "resolved, not executed" rows) intact. No fabricated components.
// ============================================================================
size_t DalvikExecutionEngine::inject_foreign_apk_code(
    const std::vector<std::pair<std::string, std::string>>&
        apk_package_pairs) {
    if (!dex_report_ || apk_package_pairs.empty() ||
        c7_foreign_code_injected_)
        return 0;
    c7_foreign_code_injected_ = true;  // once-per-boot (AOSP LoadedApk model)

    auto& mutable_classes =
        const_cast<std::vector<dex::ClassInfo>&>(dex_report_->classes);
    size_t injected_total = 0;
    size_t skipped_dup = 0;
    miniandroid::apk::ApkParser c7_apk;

    // The AOSP multi-DEX naming law: classes.dex, classes2.dex .. classesN.dex.
    std::vector<std::string> c7_dex_names{"classes.dex"};
    for (int i = 2; i <= 32; ++i)
        c7_dex_names.push_back("classes" + std::to_string(i) + ".dex");

    for (const auto& c7_pair : apk_package_pairs) {
        const std::string& apk_path = c7_pair.first;
        const std::string& owner_pkg = c7_pair.second;
        if (apk_path.empty() || owner_pkg.empty()) continue;
        if (!std::filesystem::exists(apk_path)) {
            miniandroid::diagnostics::FileIoTrace::instance().record(
                "C7-STORE-DEX", owner_pkg, false,
                "store apk missing on disk: " + apk_path +
                    " — foreign code NOT loaded (honest)",
                "inject_foreign_apk_code");
            continue;
        }
        size_t per_apk = 0;
        for (const auto& c7_name : c7_dex_names) {
            auto c7_raw = c7_apk.extract_entry(apk_path, c7_name);
            if (c7_raw.empty()) continue;  // classes2.. absent — normal
            dex::DexParser c7_parser;
            c7_parser.set_verbose(false);
            auto c7_report = c7_parser.parse_data(c7_raw, "XPKG:" + c7_name);
            if (!c7_report.is_valid) {
                miniandroid::diagnostics::FileIoTrace::instance().record(
                    "C7-STORE-DEX", owner_pkg + "/" + c7_name, false,
                    "foreign dex parse failed: " + c7_report.validation_error,
                    "inject_foreign_apk_code");
                continue;
            }
            // ── EXP-038 per-DEX resolution law: the foreign dex joins
            // per_dex_raw_data_ and every foreign class maps to its slot
            // via class_to_dex_index_ — the SAME mechanism secondary-DEX
            // classes use. Without this, string/type/method IDX values
            // inside foreign bytecode resolve against the WRONG dex
            // tables (first live evidence: BrowserPingReceiver.onReceive
            // resolved its string idx to Landroid/content/pm/ActivityInfo
            // constants — garbage from dex 0's table).
            const uint32_t c7_dex_slot =
                (uint32_t)per_dex_raw_data_.size();
            per_dex_raw_data_.push_back(c7_raw);
            is_multidex_ = per_dex_raw_data_.size() > 1;
            for (auto& c7_cls : c7_report.classes) {
                if (class_info_index_.find(c7_cls.name) !=
                    class_info_index_.end()) {
                    skipped_dup++;
                    continue;
                }
                mutable_classes.push_back(std::move(c7_cls));
                size_t c7_new_idx = mutable_classes.size() - 1;
                class_info_index_[mutable_classes.back().name] = c7_new_idx;
                class_to_dex_index_[mutable_classes.back().name] =
                    c7_dex_slot;
                set_foreign_class_owner(mutable_classes.back().name,
                                        owner_pkg);
                per_apk++;
            }
        }
        injected_total += per_apk;
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "C7-STORE-DEX", owner_pkg, true,
            "foreign code ingested from " +
                apk_path.substr(apk_path.find_last_of("/\\") + 1) +
                ": classes=" + std::to_string(per_apk),
            "inject_foreign_apk_code");
        std::cerr << "[C7-W6] foreign code ingested: " << owner_pkg
                  << " classes=" << per_apk << std::endl;
    }

    if (injected_total == 0) {
        if (skipped_dup > 0)
            std::cerr << "[C7-W6] foreign injection: 0 new, " << skipped_dup
                      << " duplicates skipped (own-package definitions win)"
                      << std::endl;
        return 0;
    }

    // Aggregate count reflects the merged state (same law as the secondary
    // injection).
    const_cast<uint32_t&>(dex_report_->classes_count) =
        (uint32_t)mutable_classes.size();

    // ── Closure laws: the injected foreign classes must satisfy the SAME
    // structural indexes the multi-DEX injection maintains — EXP-095
    // (superclass map: a foreign BroadcastReceiver/Service subclass must
    // resolve is_subclass_of), S102 (declared-interfaces closure:
    // check-cast/instanceof), F-087 (runtime-annotation closure).
    // Same loops, same dedup law, zero package knowledge.
    {
        size_t c7_sup = 0, c7_ifc = 0, c7_ann = 0;
        for (const auto& c7_cls : mutable_classes) {
            if (!c7_cls.superclass_name.empty()) {
                const std::string c7_key =
                    framework::normalize_class_desc(c7_cls.name);
                const std::string c7_val = framework::normalize_class_desc(
                    c7_cls.superclass_name);
                if (class_to_superclass_.find(c7_key) ==
                    class_to_superclass_.end())
                    c7_sup++;
                class_to_superclass_[c7_key] = c7_val;
            }
            if (!c7_cls.interfaces.empty() &&
                class_to_interfaces_.find(c7_cls.name) ==
                    class_to_interfaces_.end()) {
                class_to_interfaces_[c7_cls.name] = c7_cls.interfaces;
                c7_ifc++;
            }
            if (!c7_cls.class_annotations.empty() &&
                class_annotations_.find(c7_cls.name) ==
                    class_annotations_.end()) {
                class_annotations_[c7_cls.name] = c7_cls.class_annotations;
                c7_ann++;
            }
        }
        std::cerr << "[C7-W6] foreign closure: superclass+" << c7_sup
                  << " interfaces+" << c7_ifc << " annotations+" << c7_ann
                  << " (dup skipped " << skipped_dup << ")" << std::endl;
    }
    return injected_total;
}

void DalvikExecutionEngine::set_foreign_class_owner(
    const std::string& class_desc, const std::string& package_name) {
    if (!class_desc.empty() && !package_name.empty())
        c7_foreign_class_owner_[class_desc] = package_name;
}

const std::string& DalvikExecutionEngine::foreign_owner_package(
    const std::string& class_desc) const {
    static const std::string c7_none;
    auto c7_it = c7_foreign_class_owner_.find(class_desc);
    return c7_it != c7_foreign_class_owner_.end() ? c7_it->second : c7_none;
}

// ── CODER7 WAVE-7: cross-package ACTIVITY launch laws ──────────────────────
// AOSP ActivityManagerService.checkComponentPermission + ActivityStarter:
// the launch of an activity component is gated on (a) the component being
// ENABLED (PackageItemInfo.isEnabled — a disabled component is not
// startable: android.content.ActivityNotFoundException) and (b) the
// component being EXPORTED to the caller's uid (a non-exported activity
// owned by a DIFFERENT package answers "Permission Denial": java.lang.
// SecurityException; same-uid starts are granted). The WAVE-5 store index
// is the single component table (register_own_package ingested the running
// package, so own and foreign targets share one lookup — no per-app
// special-casing). No store ⇒ "" (allowed; byte-identical pre-W7 runs).
std::string DalvikExecutionEngine::c7_activity_launch_gate(
    const std::string& dotted_cls) const {
    if (!c7_pkg_index_ || c7_pkg_index_->empty() || dotted_cls.empty())
        return std::string();
    for (const auto& c7_name : c7_pkg_index_->package_names()) {
        const C7IdxPackage* c7_pkg = c7_pkg_index_->find_package(c7_name);
        if (!c7_pkg) continue;
        for (const auto& c7_act : c7_pkg->activities) {
            if (c7_act.cls != dotted_cls) continue;
            if (!c7_act.enabled) {
                // AOSP Instrumentation.checkStartActivityResult:
                // "Unable to find explicit activity class" family — the
                // disabled component is UNRESOLVABLE for starts.
                return "ACTIVITY_NOT_FOUND: component disabled "
                       "(android:enabled=false): " + dotted_cls;
            }
            if (!c7_act.exported && !c7_pkg->package_name.empty() &&
                c7_pkg->package_name != package_name_) {
                // AOSP checkComponentPermission wording (ActivityStarter):
                // "Permission Denial: starting Intent ... not exported
                // from uid ..." — the cross-package non-exported start.
                return "SECURITY_EXCEPTION: Permission Denial: starting "
                       "activity " + dotted_cls + " from package " +
                       package_name_ + ": not exported from package " +
                       c7_pkg->package_name;
            }
            return std::string();  // enabled + (exported OR same package)
        }
    }
    // Not in any installed manifest: outside this gate's contract (the
    // pre-W7 drain path keeps handling unknown classes unchanged).
    return std::string();
}

std::string DalvikExecutionEngine::c7_resolve_activity_xpkg(
    const std::string& action, const std::vector<std::string>& cats,
    const std::string& mime, const std::string& scheme,
    const std::string& host, const std::string& path,
    bool default_only) const {
    if (!c7_pkg_index_ || c7_pkg_index_->empty() || action.empty())
        return std::string();
    // TEMP-W8-DEBUG (bounded): the resolution dims as received.
    {
        static thread_local const bool c7_dbg =
            std::getenv("MINIANDROID_C7_RESOLVE_DEBUG") != nullptr;
        static thread_local uint64_t c7_n = 0;
        if (c7_dbg && c7_n++ < 40)
            std::cerr << "[C7-RESOLVE-DBG] action=" << action
                      << " scheme=" << scheme << " host=" << host
                      << " path=" << path << " mime=" << mime
                      << " cats=" << cats.size() << std::endl;
    }
    std::vector<C7IdxMatch> c7_matches = c7_pkg_index_->query_activities(
        action, cats, mime, scheme, host, path, default_only);
    if (c7_matches.empty()) return std::string();
    // The index's ordering IS the best-match law (W5: priority desc, stable
    // ingest order) — AOSP resolveIntent answers the top candidate.
    return c7_matches[0].cls;
}

// ============================================================================
// EXP-038 (BLOCKER-033): Per-DEX method resolution using raw DEX bytes.
// ============================================================================

std::string DalvikExecutionEngine::read_dex_string_from_raw(
    const std::vector<uint8_t>& raw, uint32_t string_idx, const dex::DexHeader& hdr) const {

    uint32_t sids_off = hdr.string_ids_off;
    uint32_t sids_size = hdr.string_ids_size;

    if (string_idx >= sids_size) return "<bad_str_idx>";
    if (sids_off + (string_idx + 1) * 4 > raw.size()) return "<str_id_oob>";

    uint32_t string_data_off;
    std::memcpy(&string_data_off, raw.data() + sids_off + string_idx * 4, 4);

    if (string_data_off >= raw.size()) return "<str_data_oob>";

    // FIND-REUSE-001: delegate to the ONE shared MUTF-8 primitive.
    // Previously a third inline ULEB128 copy lived here with the same
    // utf16-size-as-byte-count truncation bug for non-ASCII strings.
    const auto r = miniandroid::dex::mutf8::decode_string_data(raw.data(), raw.size(), string_data_off);
    if (!r.stream_ok && r.utf8.empty()) return "<str_truncated>";  // structural failure, nothing decoded
    return r.utf8;
}

// EXP-065: Per-DEX string resolution.
// string_idx is relative to the current DEX file's string_ids table.
// In multi-DEX apps (Telegram has 5 DEX files), the merged dex_report_->strings
// is the CONCATENATION of all DEX files' string tables — so using the merged
// index causes const-string to fetch the WRONG string. For example,
// classes4.dex's string_idx=5975 is "+", but merged_strings[5975] is
// "FIELD_PREFERRED_AUDIO_LANGUAGES" from classes.dex (which has 56,182 strings
// before classes4.dex's strings start).
//
// This function reads the string directly from the per-DEX raw bytes.
std::string DalvikExecutionEngine::resolve_string_for_dex(
    uint32_t string_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (string_idx < hdr.string_ids_size) {
            return read_dex_string_from_raw(raw, string_idx, hdr);
        }
    }

fallback:
    // Single-DEX fallback: use the merged dex_report's strings.
    if (dex_report_ && string_idx < dex_report_->strings.size()) {
        return dex_report_->strings[string_idx];
    }
    return "<bad_str_idx:" + std::to_string(string_idx) + ">";
}

// ============================================================================
// EXP-068: Generic View inheritance queries.
// These walk the DEX superclass chain to determine if a class inherits from
// a known Android View type. This replaces class-name pattern matching with
// semantic superclass resolution.
// ============================================================================

bool DalvikExecutionEngine::is_subclass_of(const std::string& class_desc,
                                             const std::string& ancestor_desc) const {
    // R-NEW-530 (CONT-34): subclass-reachability memo. The walk in
    // is_subclass_of_impl is a PURE function of the class tables (DEX
    // superclass chains + the static framework ancestry table); the only
    // mutation is monotonic class-table growth, guarded by the same epoch
    // law as the R-NEW-467 field memo (size-compare, any growth invalidates
    // once). dooz 300s PERF evidence: 4,626,192 walks burning ~28% of the
    // interpreter's core budget — the compose placement pass re-derives the
    // SAME answers millions of times. Negative answers memoize too (most
    // instanceof probes walk to the root and answer false).
    struct R530Memo {
        size_t epoch = static_cast<size_t>(-1);
        std::unordered_map<std::string, bool> answers;
    };
    static thread_local R530Memo r530;
    size_t r530_epoch_now = class_to_superclass_.size();
    if (r530.epoch != r530_epoch_now) {
        r530.epoch = r530_epoch_now;
        r530.answers.clear();
    }
    std::string r530_key = framework::normalize_class_desc(class_desc);
    r530_key.push_back('\0');
    r530_key += framework::normalize_class_desc(ancestor_desc);
    auto r530_it = r530.answers.find(r530_key);
    if (r530_it != r530.answers.end()) return r530_it->second;
    bool r530_ans = is_subclass_of_impl(class_desc, ancestor_desc);
    r530.answers.emplace(std::move(r530_key), r530_ans);
    return r530_ans;
}

bool DalvikExecutionEngine::is_subclass_of_impl(const std::string& class_desc,
                                             const std::string& ancestor_desc) const {
    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().subclass, f107_t0);
    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().subclass, f107_t0};
    // G12 FIX-G12-001b (descriptor form law): the UI layer hands us
    // dot-form descriptors (Lfoo.bar.Baz; from AXML tags) while the
    // class_to_superclass_ map and the framework ancestry table are
    // slash-form (Lfoo/bar/Baz; from the DEX). Normalize once here.
    const std::string want =
        framework::normalize_class_desc(ancestor_desc);
    std::string current = framework::normalize_class_desc(class_desc);
    // M3-DIAG (temporary): trace app-class container classification
    // queries to expose cross-pass state divergence.
    // S138+ TRAIN-31 extension: also cover slash-LESS R8-renamed app
    // classes (Ltl0; etc.) — the old gate required a '/' so every
    // R8-short app class silently skipped the diag while the materialize
    // TYPE tests (target Lmo;) all answered FALSE (109x/0x TRUE at HEAD).
    static const bool m3_diag = std::getenv("MINIANDROID_M3_ANCESTRY_DIAG") != nullptr;
    std::string m3_path;
    if (m3_diag &&
        current.find("Landroid/") != 0 && current.find("Ljava/") != 0 &&
        current.find("Landroidx/") != 0 && current.find("Lkotlin/") != 0 &&
        current.find("Lcom/google/") != 0) {
        m3_path = current;
    }
    if (current == want) return true;
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-181 (WAVE C, FINAL CAMPAIGN phases 5/6 — ARRAY TYPE LAW).
    // ART/JVMS array classification: an array object's runtime type is its
    // descriptor. Rules implemented (AOSP Class.isAssignableFrom + JVMS
    // 4.4 assignability):
    //   • primitive arrays ([B [S [I [J [Z [C [F [D]) are FINAL types —
    //     instance-of another array type is FALSE (exact match above);
    //   • [LS; is an instance of [LT; iff S is assignable to T (covariant,
    //     store-checks guard writes at runtime — AOSP ArrayStoreException);
    //   • [[X; / any nested array is an instance of [Ljava/lang/Object;,
    //     [Ljava/lang/Cloneable;, [Ljava/io/Serializable; (and the plain
    //     Object/Cloneable/Serializable CLASS types);
    //   • a non-array object is NEVER an instance of an array type;
    //   • every array IS a java.lang.Object / Cloneable / Serializable.
    // The engine's synthetic "Larray;" marker (legacy shadow allocations)
    // is classified as an object array of unknown element: instance of
    // [Ljava/lang/Object; / Object / Cloneable / Serializable only.
    // Measured root face: guava RegularImmutableMap.create's duplicate-key
    // wrapper gate `instance-of v2, [Ljava/lang/Object;` answered FALSE on
    // a NEW_ARRAY'd wrapper stamped "Larray;" — the wrapper was stored AS
    // the hash table and the lawful get() probe looped (F-NEW-181 spin).
    // ────────────────────────────────────────────────────────────────────
    const auto is_prim_array_desc = [](const std::string& d) {
        return d.size() >= 2 && d[0] == '[' && d[1] != 'L' && d[1] != '[';
    };
    if (!want.empty() && want[0] == '[') {
        if (is_prim_array_desc(want)) return false;  // final: exact-only
        std::string Y = want.substr(2, want.size() - 3);  // [LY; → LY;
        if (current == "Larray;") return (Y == "Ljava/lang/Object;");
        if (current.size() > 2 && current[0] == '[') {
            std::string EC = current.substr(1);
            if (EC[0] == '[')
                return (Y == "Ljava/lang/Object;" ||
                        Y == "Ljava/lang/Cloneable;" ||
                        Y == "Ljava/io/Serializable;");
            if (EC.size() > 2 && EC[0] == 'L' && EC.back() == ';') {
                std::string elem = EC.substr(1, EC.size() - 2);
                if (elem == Y) return true;
                return is_subclass_of(elem, Y);
            }
            return false;  // primitive-element array vs object-array type
        }
        return false;  // non-array object vs array type
    }
    if (!current.empty() &&
        (current[0] == '[' || current == "Larray;")) {
        // array queried against a CLASS type
        return (want == "Ljava/lang/Object;" ||
                want == "Ljava/lang/Cloneable;" ||
                want == "Ljava/io/Serializable;");
    }
    if (want == "Ljava/lang/Object;" && !current.empty() &&
        (current[0] == 'L' || current[0] == '['))
        return true;  // every reference type is-a Object
    std::unordered_set<std::string> visited;  // cycle protection
    // ────────────────────────────────────────────────────────────────────
    // F-023 (DEX type-closure law — implements hierarchy): instance-of and
    // castability must consider the INTERFACE closure of the class, not
    // just the extends chain. A class C is an instance of interface I when
    // I is reachable through: C's direct interfaces, the interfaces of
    // every superclass, and the super-interfaces of those (transitive).
    // Evidence (dooz): ViewTreeLifecycleOwner.get stored the owner tag
    // (obj#8 = MainActivity) on the decor view; the walker lambda rejected
    // it because `tag as? LifecycleOwner` compiled to
    // instance-of tag, Landroidx/lifecycle/o; and the extends-only walk
    // returned FALSE (MainActivity → AppCompatActivity → … →
    // ComponentActivity IMPLEMENTS LifecycleOwner) → get() returned null →
    // WindowRecomposer_androidKt ISE "ViewTreeLifecycleOwner not found" →
    // Compose composition died before the first frame.
    // Framework-interface closure (android/* interfaces not parsed from the
    // APK dex) is out of scope here: the queried ancestor in real paths is
    // an app-bundled (androidx) type present in dex_report_.
    // ────────────────────────────────────────────────────────────────────
    auto interface_closure_contains = [&](const std::string& cls) -> bool {
        // ── F-NEW-236 (fairymahjong F-235 probe face): JDK FRAMEWORK
        // INTERFACE HIERARCHY. The DEX closure below can only see classes
        // parsed from the APK; every java.*/core collection class is a
        // framework type, so `instance-of Collection/List/Set/Map/Iterable`
        // on them answered FALSE and Kotlin's compiled toSet() (fairymahjong
        // Ls;.D) took the wrong branch → returned EmptySet for a 50-element
        // list → the game's dedup gate threw its own IAE. Law: the libcore
        // implements/interface-extends hierarchy (framework_class_interfaces
        // + framework_iface_supers) participates in EVERY classification,
        // app or framework, before and alongside the DEX closure.
        if (framework::framework_implements(cls, want)) return true;
        if (!dex_report_ || want.empty()) return false;
        std::vector<std::string> ifq;
        std::unordered_set<std::string> ifv;
        // F-107c (R-NEW-381, S61): O(log n) index lookup instead of a linear
        // scan of every dex_report_->classes entry. The classifier runs
        // millions of times per run (is_a wiring for measure/layout/instance-
        // of); each old collect() walked up to 3052 ClassInfo records — the
        // single largest profile cost after the static-churn fix. The
        // class_to_interfaces_ index (F-103) holds the SAME data keyed by
        // class descriptor and is rebuilt by build_class_dex_index.
        auto collect = [&](const std::string& c) {
            auto cit = class_to_interfaces_.find(c);
            if (cit == class_to_interfaces_.end()) return;
            for (const auto& ifc : cit->second) {
                if (!ifc.empty() && ifv.insert(ifc).second) {
                    ifq.push_back(framework::normalize_class_desc(ifc));
                }
            }
        };
        collect(cls);
        for (size_t qi = 0; qi < ifq.size() && qi < 128; ++qi) {
            if (ifq[qi] == want) return true;
            collect(ifq[qi]);
        }
        return false;
    };
    if (interface_closure_contains(current)) return true;
    for (int i = 0; i < 50; ++i) {  // max depth 50 to prevent infinite loops
        if (visited.count(current)) return false;  // cycle
        visited.insert(current);
        // G12 FIX-G12-001 (AOSP framework ancestry law): when the class is
        // a framework class (or the walk exits app code into one), the
        // AOSP `extends` hierarchy is the authority — TableRow/TableLayout
        // extend LinearLayout, ScrollView extends FrameLayout, Button
        // extends TextView. Without this layer the framework classes fell
        // to substring heuristics and TableRow classified as a leaf
        // (0x0 rows under 44px children — headingcalculator display grid).
        if (auto sup = framework::framework_superclass_of(current);
            !sup.empty()) {
            current = sup;
        } else {
            auto it = class_to_superclass_.find(current);
            if (it == class_to_superclass_.end()) {
                if (!m3_path.empty())
                    fprintf(stderr,
                            "[M3-ANCESTRY] query=%s want=%s MISSING-IN-MAP "
                            "map=%zu this=%p FALLBACK framework_is_subclass\n",
                            m3_path.c_str(), want.c_str(),
                            class_to_superclass_.size(), (const void*)this);
                // Unknown in BOTH layers: fall back to the framework walk
                // for the original descriptor (covers multi-hop app->
                // framework chains where the app entry point itself is
                // framework-relative).
                return framework::framework_is_subclass(current, want);
            }
            current = it->second;
            if (!m3_path.empty())
                m3_path += " -> " + current;
        }
        if (current == want) {
            if (!m3_path.empty())
                fprintf(stderr, "[M3-ANCESTRY] query=%s want=%s TRUE "
                                "this=%p\n", m3_path.c_str(), want.c_str(),
                        (const void*)this);
            return true;
        }
        // F-023: the current superclass may itself carry the interface
        // (e.g. androidx.activity.ComponentActivity implements
        // LifecycleOwner while MainActivity declares none directly).
        if (interface_closure_contains(current)) return true;
        if (current.empty() || current == "Ljava/lang/Object;") {
            if (!m3_path.empty())
                fprintf(stderr, "[M3-ANCESTRY] query=%s want=%s FALSE "
                                "this=%p\n", m3_path.c_str(), want.c_str(),
                        (const void*)this);
            return false;
        }
    }
    return false;
}

bool DalvikExecutionEngine::is_view_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/view/View;");
}

// ────────────────────────────────────────────────────────────────────────
// F-105 (S59, R-NEW-379) — DECLARATION↔HEAP CLASS RECONCILIATION.
// Shared by execute_instance_of and execute_check_cast. Resolves the
// runtime class of a reference from its creation-site declaration
// (register class_desc) and the heap record at the referenced id.
//
// The engine intentionally shares ONE integer id space between shadow
// entities and heap objects (F-023 activity-as-view: the activity
// object's id IS the activity's view node id), so the heap record at a
// referenced id may belong to a DIFFERENT entity than the one the
// reference means. Reconciliation rules (see the long law comment in
// execute_instance_of):
//   • declaration empty / Ljava/lang/Object; → heap record wins (F-103:
//     generic wrapper tags carry no runtime-type information).
//   • CONSISTENT pair (one assignable to the other) → the MORE SPECIFIC
//     side wins.
//   • CONTRADICTION (neither assignable) → the DECLARATION wins: the
//     reference means the entity its creator declared; the heap record
//     at the shared integer is a different entity.
// ────────────────────────────────────────────────────────────────────────
std::string DalvikExecutionEngine::reconcile_class_decl(
    const std::string& declared, uint32_t object_id) const {
    if (object_id == 0 || !heap_.has_object(object_id)) return declared;
    const auto* ho = heap_.get(object_id);
    if (!ho || ho->class_descriptor.empty()) return declared;
    const std::string& hc = ho->class_descriptor;
    const bool decl_generic =
        declared.empty() || declared == "Ljava/lang/Object;";
    if (decl_generic) return hc;                    // F-103 authority
    if (hc == declared) return declared;            // agreed
    if (is_subclass_of(hc, declared)) return hc;    // heap refines
    if (is_subclass_of(declared, hc)) return declared;  // decl sharper
    return declared;                                // CONTRADICTION (F-105)
}

// ============================================================================
// UNIFIED_011.3 TYPED-CATCH (§18): exception-type compatibility.
//
// Matching sources, in order:
//   1. exact descriptor equality
//   2. DEX superclass chain (class_to_superclass_, includes APK-defined
//      exception classes AND the seeded Android framework hierarchy)
//   3. built-in java.lang / java.io / java.util / org.json exception
//      hierarchy (framework exception classes whose class_defs are NOT in
//      the APK's DEX files — exactly like the View hierarchy seed above).
// `catch_desc` of Object/Throwable catches everything (Dalvik semantics).
// ============================================================================
bool DalvikExecutionEngine::is_exception_subtype(const std::string& exc_desc,
                                                 const std::string& catch_desc) const {
    if (exc_desc.empty() || catch_desc.empty()) return false;
    if (exc_desc == catch_desc) return true;
    if (catch_desc == "Ljava/lang/Object;" || catch_desc == "Ljava/lang/Throwable;") {
        return true;
    }

    // Built-in framework exception hierarchy (child → parent).
    static const miniandroid::dalvik::KvPair kBuiltinExcParent[] = {
    {"Ljava/lang/Exception;", "Ljava/lang/Throwable;"},
    {"Ljava/lang/RuntimeException;", "Ljava/lang/Exception;"},
    {"Ljava/lang/NullPointerException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/IndexOutOfBoundsException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/ArrayIndexOutOfBoundsException;", "Ljava/lang/IndexOutOfBoundsException;"},
    {"Ljava/lang/StringIndexOutOfBoundsException;", "Ljava/lang/IndexOutOfBoundsException;"},
    {"Ljava/lang/ArithmeticException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/IllegalArgumentException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/NumberFormatException;", "Ljava/lang/IllegalArgumentException;"},
    {"Ljava/lang/IllegalStateException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/ClassCastException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/UnsupportedOperationException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/NegativeArraySizeException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/ArrayStoreException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/util/ConcurrentModificationException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/SecurityException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/lang/InterruptedException;", "Ljava/lang/Exception;"},
    {"Ljava/lang/ClassNotFoundException;", "Ljava/lang/Exception;"},
    {"Ljava/lang/ReflectiveOperationException;", "Ljava/lang/Exception;"},
    // FIX-D12 (CONT-120): AOSP android.view.CalledFromWrongThreadException
    // extends RuntimeException (android.view hierarchy) — the companion
    // row for the ViewShadow.checkThread law so app catch(RuntimeException)
    // / catch(Exception) handlers can receive it.
    {"Landroid/view/CalledFromWrongThreadException;", "Ljava/lang/RuntimeException;"},
    // CODER7 WAVE-8 L2: android.app.PendingIntent$CanceledException
    // extends android.os.OperationCanceledException extends
    // java.lang.RuntimeException? — AOSP: OperationCanceledException
    // extends android.util.AndroidException extends java.lang.Exception.
    // The row (as Exception) lets app catch(Exception)/typed handlers
    // receive the ONE_SHOT re-send denial.
    {"Landroid/app/PendingIntent$CanceledException;", "Ljava/lang/Exception;"},
    // CODER7 WAVE-12: android.app.MissingForegroundServiceTypeException
    // extends java.lang.RuntimeException (AOSP API-34; the 3-arg
    // startForeground MANIFEST-sentinel law throws it when the manifest
    // declares no foregroundServiceType). The row lets app
    // catch(RuntimeException)/typed handlers receive it.
    {"Landroid/app/MissingForegroundServiceTypeException;",
     "Ljava/lang/RuntimeException;"},
    // FIX-D12-ADJACENT / unified0113 (CONT-120): the five reflective
    // NoSuch*/Illegal* families are OpenJDK java.lang facts of the SAME
    // kind as the ClassNotFoundException row above (java.lang §7 parent
    // chain) — they belonged in the unconditional table, not behind the
    // F-NEW-368 experiment gate. Without the NoSuchMethodException row a
    // typed catch(Exception) around Class.getDeclaredConstructor NEVER
    // matches and the deferred unwind aborts the whole DEX frame — the
    // memory app's CoordinatorLayout.getResolvedLayoutParams evidence
    // (F106-CTOR uncaught ×24, fan-out 24, the highest-count signature of
    // CONT-119). AOSP CoordinatorLayout.getResolvedLayoutParams wraps the
    // reflection in catch(NoSuchMethodException)/catch(Exception) and the
    // frame must survive it. The network / android rows below stay on the
    // gated table (F-NEW-368's per-container-trust experiment, unchanged).
    {"Ljava/lang/NoSuchMethodException;", "Ljava/lang/ReflectiveOperationException;"},
    {"Ljava/lang/NoSuchFieldException;", "Ljava/lang/ReflectiveOperationException;"},
    {"Ljava/lang/InstantiationException;", "Ljava/lang/ReflectiveOperationException;"},
    {"Ljava/lang/IllegalAccessException;", "Ljava/lang/ReflectiveOperationException;"},
    {"Ljava/lang/InvocationTargetException;", "Ljava/lang/ReflectiveOperationException;"},
    {"Ljava/io/IOException;", "Ljava/lang/Exception;"},
    {"Ljava/io/FileNotFoundException;", "Ljava/io/IOException;"},
    {"Ljava/io/EOFException;", "Ljava/io/IOException;"},
    {"Ljava/util/NoSuchElementException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/util/InputMismatchException;", "Ljava/util/NoSuchElementException;"},
    {"Lorg/json/JSONException;", "Ljava/lang/Exception;"},
    {"Lorg/xmlpull/v1/XmlPullParserException;", "Ljava/lang/Exception;"},
    {"Ljava/lang/Error;", "Ljava/lang/Throwable;"},
    {"Ljava/lang/OutOfMemoryError;", "Ljava/lang/VirtualMachineError;"},
    {"Ljava/lang/StackOverflowError;", "Ljava/lang/VirtualMachineError;"},
    {"Ljava/lang/VirtualMachineError;", "Ljava/lang/Error;"},
    {"Ljava/lang/AssertionError;", "Ljava/lang/Error;"},
    {"Ljava/lang/NoClassDefFoundError;", "Ljava/lang/LinkageError;"},
    {"Ljava/lang/LinkageError;", "Ljava/lang/Error;"},
    // F-NEW-518 (CONT-13, batch-3 census): the android.content PM family.
    // AOSP PackageManager.java: `public static class NameNotFoundException
    // extends AndroidException` (import android.util.AndroidException) and
    // AndroidException.java: `public class AndroidException extends Exception`.
    // Without these rows the platform-isPackageInstalled pattern —
    // `try { pm.getPackageInfo(pkg, 0); true } catch (e: Exception) { false }`
    // — could NEVER match its own handler: the DEX handler type is
    // java/lang/Exception, the thrown class has no DEX superclass (framework
    // class, not in class_to_superclass_), and the AndroidException row was
    // trapped behind the F-NEW-368 experiment gate. Live evidence (fossify
    // math/notes/clock/calendar ×4, batch-3 census): the handler at
    // Lo5/f;.U pc=17 (return false) decoded in the DEX try table, thrown
    // NameNotFoundException → is_exception_subtype false → deferred unwind →
    // APP BOUNDARY death at SplashActivity.onCreate. Same precedent as
    // FIX-D12-ADJACENT (CONT-120): platform exception chains are AOSP FACTS,
    // not experiment-gateable. No behavior flip under the gate (the gated
    // table's AndroidException row carries the identical parent).
    {"Landroid/content/pm/PackageManager$NameNotFoundException;", "Landroid/util/AndroidException;"},
    {"Landroid/content/pm/PackageManager$ApplicationNotFoundException;", "Landroid/util/AndroidException;"},
    {"Landroid/util/AndroidException;", "Ljava/lang/Exception;"},
};
static const size_t kBuiltinExcParent_N = sizeof(kBuiltinExcParent) / sizeof(kBuiltinExcParent[0]);

// F-NEW-368 extension table (CONT-71, env-gated MINIANDROID_F368_LAW): the
// java.net / java.util.concurrent / android exception families — every row
// an AOSP libcore documented parent. (CONT-120: the five REFLECTIVE rows
// moved to the unconditional kBuiltinExcParent above — unified0113/memory
// F106-CTOR evidence; java.lang §7 chains are not experiment-gateable.)
// Gated because the in-frame delivery it unlocks completes container DEX
// measure chains whose downstream emulation is still incomplete (the
// F-NEW-370 decode trail) — the default binary keeps the pre-wave
// behavior byte-for-byte; the flag activates the delivery for the
// per-container-trust experiment.
static const miniandroid::dalvik::KvPair kF368ExcParent[] = {
    {"Ljava/net/SocketException;", "Ljava/io/IOException;"},
    {"Ljava/net/ConnectException;", "Ljava/net/SocketException;"},
    {"Ljava/net/UnknownHostException;", "Ljava/io/IOException;"},
    {"Ljava/net/SocketTimeoutException;", "Ljava/io/InterruptedIOException;"},
    {"Ljava/io/InterruptedIOException;", "Ljava/io/IOException;"},
    {"Ljava/util/concurrent/ExecutionException;", "Ljava/lang/Exception;"},
    {"Ljava/util/concurrent/TimeoutException;", "Ljava/lang/Exception;"},
    {"Ljava/util/concurrent/CancellationException;", "Ljava/lang/IllegalStateException;"},
    {"Ljava/util/concurrent/RejectedExecutionException;", "Ljava/lang/RuntimeException;"},
    {"Ljava/util/concurrent/CompletionException;", "Ljava/lang/RuntimeException;"},
    {"Landroid/os/RemoteException;", "Landroid/os/AndroidException;"},
    {"Landroid/os/AndroidException;", "Ljava/lang/Exception;"},
    {"Landroid/util/AndroidException;", "Ljava/lang/Exception;"},
};
static const size_t kF368ExcParent_N = sizeof(kF368ExcParent) / sizeof(kF368ExcParent[0]);
static const bool f368_law_active = std::getenv("MINIANDROID_F368_LAW") != nullptr;
auto f368_builtin_parent = [&](const std::string& desc) -> const char* {
    if (f368_law_active) {
        const char* e = kv_table_find(kF368ExcParent, kF368ExcParent_N, desc);
        if (e) return e;
    }
    return kv_table_find(kBuiltinExcParent, kBuiltinExcParent_N, desc);
};


    // Walk both chains simultaneously (merged walk, cycle-safe).
    std::string via_dex = exc_desc;
    std::string via_builtin = exc_desc;
    std::unordered_set<std::string> visited;
    for (int depth = 0; depth < 50; ++depth) {
        if (via_dex == catch_desc || via_builtin == catch_desc) return true;
        if (via_dex == "Ljava/lang/Object;" && via_builtin == "Ljava/lang/Object;") break;
        size_t before = visited.size();
        visited.insert(via_dex);
        visited.insert(via_builtin);
        if (visited.size() == before) break;  // no progress → cycle

        // advance DEX chain
        auto dex_it = class_to_superclass_.find(via_dex);
        if (dex_it != class_to_superclass_.end()) {
            via_dex = dex_it->second;
        } else {
            // not DEX-defined: fall through to built-in chain for next step
            const char* b1 = f368_builtin_parent(via_dex);
            via_dex = b1 ? b1 : "Ljava/lang/Object;";
        }
        // advance built-in chain
        {
            const char* b2 = f368_builtin_parent(via_builtin);
            if (b2) {
                via_builtin = b2;
            } else {
                auto d_it = class_to_superclass_.find(via_builtin);
                via_builtin = (d_it != class_to_superclass_.end())
                        ? d_it->second : "Ljava/lang/Object;";
            }
        }
    }
    return false;
}

bool DalvikExecutionEngine::is_text_view_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/TextView;");
}

bool DalvikExecutionEngine::is_edit_text_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/EditText;");
}

bool DalvikExecutionEngine::is_image_view_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/ImageView;");
}

bool DalvikExecutionEngine::is_button_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/Button;");
}

bool DalvikExecutionEngine::is_view_group_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/view/ViewGroup;");
}

// MASTER CAMPAIGN FIX (F8 default-onMeasure law — View.java getDefaultSize):
// Walk the semantic superclass chain (class_to_superclass_ — DEX-derived for
// app classes, factual AOSP table for framework families) and report whether
// `method` is defined before the chain reaches a framework content class.
// Law (AOSP View.java): View.onMeasure default =
//   setMeasuredDimension(getDefaultSize(suggestedMinimumWidth, widthMeasureSpec), ...)
//   getDefaultSize: AT_MOST/EXACTLY -> specSize; UNSPECIFIED -> suggested size.
// It applies iff NO class in the chain overrides onMeasure. The runtime
// implements the CONTENT semantics of the framework measuring classes
// (TextView/ImageView/ProgressBar families) itself, so reaching one of those
// in the chain means CONTENT law (flag false). Reaching plain
// View/ViewGroup/SurfaceView etc. means the DEFAULT law applies (flag true).
bool DalvikExecutionEngine::class_chain_defines_method(
    const std::string& class_desc, const std::string& method) const {
    // Framework classes whose measure law is CONTENT-based (runtime
    // implements their onMeasure semantics directly). Factual AOSP
    // hierarchy (frameworks/base core/java/android/widget).
    static const miniandroid::dalvik::KvPair kContentMeasureClasses[] = {
    {"Landroid/widget/TextView;", ""},
    {"Landroid/widget/EditText;", ""},
    {"Landroid/widget/Button;", ""},
    {"Landroid/widget/CheckBox;", ""},
    {"Landroid/widget/RadioButton;", ""},
    {"Landroid/widget/ImageView;", ""},
    {"Landroid/widget/ProgressBar;", ""},
    {"Landroidx/appcompat/widget/AppCompatTextView;", ""},
    {"Landroidx/appcompat/widget/AppCompatEditText;", ""},
    {"Landroidx/appcompat/widget/AppCompatButton;", ""},
    {"Landroidx/appcompat/widget/AppCompatImageView;", ""},
    {"Landroidx/appcompat/widget/AppCompatCheckBox;", ""},
};
static const size_t kContentMeasureClasses_N = sizeof(kContentMeasureClasses) / sizeof(kContentMeasureClasses[0]);

    std::string cur = class_desc;
    int guard = 0;
    while (!cur.empty() && guard++ < 16) {
        auto cit = class_info_index_.find(cur);
        if (cit != class_info_index_.end() && dex_report_) {
            const auto& cls = dex_report_->classes[cit->second];
            // F-107c2: iterate without copying the method table.
            if (cls.find_method(method) != nullptr) return true;
        }
        if (kv_table_contains(kContentMeasureClasses, kContentMeasureClasses_N, cur)) return false;
        // MASTER-2 FIX-MEASURE-001 (override-query law): reaching a plain
        // framework View family means the APP chain does NOT define the
        // method — View.onMeasure is FRAMEWORK-OWNED. The query answers
        // "does the app chain DEFINE the method" (override semantics), so
        // the answer here is FALSE; the AOSP DEFAULT View.onMeasure
        // (getDefaultSize) law then applies via aosp_default_measure=true
        // at the flag sites. The previous `return true` conflated
        // "framework owns the method" with "the app chain defines it" and
        // inverted BOTH flags for every no-override View descendant:
        // org.billthefarmer.scope v140 Scope/Unit (no onMeasure in DEX,
        // verified) were flagged as overriders, the real-DEX measure hook
        // missed, and aosp_default_measure=false blocked the
        // getDefaultSize fallback → measured 0x0 (§3 reverse chain).
        if (cur == "Landroid/view/View;" || cur == "Landroid/view/SurfaceView;")
            return false;
        auto sup_it = class_to_superclass_.find(cur);
        if (sup_it == class_to_superclass_.end()) {
            // Unknown ancestor (framework class outside the seeded table):
            // conservative false (content model — prior behavior).
            return false;
        }
        cur = sup_it->second;
    }
    return false;
}

// M3 F-005 FIX-A (AG, 2026-09-08): AOSP law — TextView/Button/… OVERRIDE
// onMeasure with content semantics; an INSTANCE of these families measures
// content, never the raw View.getDefaultSize fallback. The prior bool
// answer conflated "the runtime models this family's content" (Button)
// with "the chain is a plain View descendant" (custom views) — both
// returned false, and the flag sites inverted false into
// aosp_default_measure=true, so every PROGRAMMATIC empty Button measured
// getDefaultSize(AT_MOST) = specSize (microtimer row buttons 1080x0,
// FINDING-005). Returns true when the ancestry reaches a runtime
// content-measure family — those nodes take the CONTENT measure and
// aosp_default_measure stays false at the flag sites.
bool DalvikExecutionEngine::runtime_content_measure_class(
    const std::string& class_desc) const {
    static const miniandroid::dalvik::KvPair kContentMeasureClasses1[] = {
    {"Landroid/widget/TextView;", ""},
    {"Landroid/widget/EditText;", ""},
    {"Landroid/widget/Button;", ""},
    {"Landroid/widget/CheckBox;", ""},
    {"Landroid/widget/RadioButton;", ""},
    {"Landroid/widget/ImageView;", ""},
    {"Landroid/widget/ProgressBar;", ""},
    {"Landroidx/appcompat/widget/AppCompatTextView;", ""},
    {"Landroidx/appcompat/widget/AppCompatEditText;", ""},
    {"Landroidx/appcompat/widget/AppCompatButton;", ""},
    {"Landroidx/appcompat/widget/AppCompatImageView;", ""},
    {"Landroidx/appcompat/widget/AppCompatCheckBox;", ""},
};
static const size_t kContentMeasureClasses1_N = sizeof(kContentMeasureClasses1) / sizeof(kContentMeasureClasses1[0]);

    std::string cur = class_desc;
    int guard = 0;
    while (!cur.empty() && guard++ < 16) {
        if (kv_table_contains(kContentMeasureClasses1, kContentMeasureClasses1_N, cur)) return true;
        auto cit = class_info_index_.find(cur);
        if (cit != class_info_index_.end() && dex_report_) return false;
        if (cur == "Landroid/view/View;" || cur == "Landroid/view/SurfaceView;")
            return false;
        auto sup_it = class_to_superclass_.find(cur);
        if (sup_it == class_to_superclass_.end()) {
            // Unknown ancestor (framework class outside the seeded table):
            // conservative TRUE (content model — the runtime's own content
            // measure remains the safer default for unresolvable chains).
            return true;
        }
        cur = sup_it->second;
    }
    return false;
}

// CONT-96 W3-B: memo fill + public cache-backed resolvers. The *_uncached
// bodies below are byte-identical to the original resolvers (renamed only).
DalvikExecutionEngine::MethodResolveCacheEntry&
DalvikExecutionEngine::method_resolve_entry(uint32_t dex_index,
                                            uint32_t method_idx) const {
    // Single-writer law: DEX execution runs on the interpreter thread; the
    // DEX tables are immutable after set_per_dex_raw_data_, so a filled
    // entry can never change. Entries fill once on first use.
    if (dex_index >= method_resolve_cache_.size())
        method_resolve_cache_.resize(dex_index + 1);
    auto& per = method_resolve_cache_[dex_index];
    if (method_idx >= per.size())
        per.resize(static_cast<size_t>(method_idx) + 1);
    auto& e = per[method_idx];
    if (e.filled) return e;
    e.name = resolve_method_name_uncached(method_idx, dex_index);
    e.cls = resolve_method_class_uncached(method_idx, dex_index);
    e.proto = resolve_method_proto_uncached(method_idx, dex_index);
    e.proto_params = parse_proto_param_types(e.proto);
    e.filled = true;
    return e;
}

std::string DalvikExecutionEngine::resolve_method_name_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {
    return method_resolve_entry(dex_index, method_idx).name;
}

std::string DalvikExecutionEngine::resolve_method_class_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {
    return method_resolve_entry(dex_index, method_idx).cls;
}

std::string DalvikExecutionEngine::resolve_method_proto_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {
    return method_resolve_entry(dex_index, method_idx).proto;
}

std::string DalvikExecutionEngine::resolve_method_name_uncached(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx < hdr.method_ids_size &&
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) <= raw.size()) {

            dex::DexMethodId mid;
            std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                        sizeof(dex::DexMethodId));
            return read_dex_string_from_raw(raw, mid.name_idx, hdr);
        }
    }

fallback:
    // Fallback to merged method_ids (works for classes.dex)
    if (dex_report_ && method_idx < dex_report_->method_ids.size()) {
        uint32_t name_idx = dex_report_->method_ids[method_idx].name_idx;
        if (name_idx < dex_report_->strings.size()) return dex_report_->strings[name_idx];
    }
    return "<bad_method_idx:" + std::to_string(method_idx) + ">";
}

std::string DalvikExecutionEngine::resolve_method_class_uncached(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx < hdr.method_ids_size &&
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) <= raw.size()) {

            dex::DexMethodId mid;
            std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                        sizeof(dex::DexMethodId));

            // Resolve class_idx → type descriptor
            uint16_t class_idx = mid.class_idx;
            if (class_idx < hdr.type_ids_size &&
                hdr.type_ids_off + (class_idx + 1) * 4 <= raw.size()) {

                uint32_t descriptor_idx;
                std::memcpy(&descriptor_idx, raw.data() + hdr.type_ids_off + class_idx * 4, 4);
                return read_dex_string_from_raw(raw, descriptor_idx, hdr);
            }
        }
    }

fallback:
    if (dex_report_ && method_idx < dex_report_->method_ids.size()) {
        uint16_t class_idx = dex_report_->method_ids[method_idx].class_idx;
        if (class_idx < dex_report_->types.size()) return dex_report_->types[class_idx];
    }
    return "<unknown>";
}

// EXP-058: Per-DEX type descriptor resolution.
// type_idx is relative to the current DEX file's type_ids table.
// The type_ids table maps type_idx → string_ids_idx → descriptor string.
// Previously, execute_new_instance used the MERGED global types vector,
// causing type_idx from one DEX to resolve to a type from a different DEX.
std::string DalvikExecutionEngine::resolve_type_for_dex(
    uint32_t type_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (type_idx < hdr.type_ids_size &&
            hdr.type_ids_off + (type_idx + 1) * 4 <= raw.size()) {

            // type_ids[type_idx] = string_ids_idx (descriptor string)
            uint32_t descriptor_idx;
            std::memcpy(&descriptor_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);

            return read_dex_string_from_raw(raw, descriptor_idx, hdr);
        }
    }

fallback:
    if (dex_report_ && type_idx < dex_report_->types.size()) {
        return dex_report_->types[type_idx];
    }
    return "<unknown>";
}

// EXP-071: Per-DEX proto (method descriptor) resolution.
// Reads the proto_ids table from raw DEX bytes to resolve method_idx →
// proto descriptor (e.g. "(Lorg/telegram/tgnet/TLRPC$TL_error;)V").
// This is the actual method descriptor; existing resolve_method_name_for_dex
// only returns the bare method NAME (e.g. "run"), which is not enough to
// decide whether wide register merging is needed for $r8$lambda methods.
//
// We resolve:
//   1. method_ids[method_idx].proto_idx → proto_ids index.
//   2. proto_ids[proto_idx].shorty_idx → shorty string (e.g. "VL")
//   3. proto_ids[proto_idx].return_type_idx → return type descriptor.
//   4. proto_ids[proto_idx].parameters_off → type_list of parameter types.
//   5. Assemble "(param_types)return_type" — full descriptor.
std::string DalvikExecutionEngine::resolve_method_proto_uncached(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx >= hdr.method_ids_size ||
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) > raw.size()) {
            goto fallback;
        }

        dex::DexMethodId mid;
        std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                    sizeof(dex::DexMethodId));

        uint32_t proto_idx = mid.proto_idx;
        if (proto_idx >= hdr.proto_ids_size ||
            hdr.proto_ids_off + (proto_idx + 1) * sizeof(dex::DexProtoId) > raw.size()) {
            goto fallback;
        }

        dex::DexProtoId pid;
        std::memcpy(&pid, raw.data() + hdr.proto_ids_off + proto_idx * sizeof(dex::DexProtoId),
                    sizeof(dex::DexProtoId));

        // Resolve return type descriptor.
        std::string return_type_desc = "<unknown>";
        if (pid.return_type_idx < hdr.type_ids_size &&
            hdr.type_ids_off + (pid.return_type_idx + 1) * 4 <= raw.size()) {
            uint32_t descriptor_idx;
            std::memcpy(&descriptor_idx,
                        raw.data() + hdr.type_ids_off + pid.return_type_idx * 4, 4);
            return_type_desc = read_dex_string_from_raw(raw, descriptor_idx, hdr);
        }

        // Resolve parameter types via the type_list at parameters_off.
        // EXP-088+ F4 CRITICAL FIX: type_list entries are 2 bytes each (ushort type_idx),
        // NOT 4 bytes. The DEX format specification says:
        //   type_list { uint size; type_item list[size]; }
        //   type_item { ushort type_idx; }  ← 2 bytes, not 4
        //
        // Previously this code read 4 bytes per entry, which caused:
        //   1. Wrong proto resolution (e.g. "(J)Z" instead of
        //      "(Lorg/telegram/ui/ActionBar/INavigationLayout;Lorg/telegram/ui/ActionBar/BaseFragment;)Z")
        //   2. Wrong wide-arg merging in invoke-static (fragment arg merged as long)
        //   3. args_size=1 instead of 2 for $default$addFragmentToStack
        //   4. Fragment lifecycle never starts → Phase M blocked
        //
        // This is a GENERIC fix — affects ALL multi-DEX APKs that use
        // desugered interface default methods with 2+ object parameters.
        std::string params_str;
        if (pid.parameters_off != 0 && pid.parameters_off + 4 <= raw.size()) {
            uint32_t list_size;
            std::memcpy(&list_size, raw.data() + pid.parameters_off, 4);
            // Bound check the list entries. Each entry is 2 bytes (ushort).
            size_t list_start = pid.parameters_off + 4;
            size_t list_bytes = static_cast<size_t>(list_size) * 2u;  // FIXED: 2 bytes per entry
            if (list_size <= 1024 && list_start + list_bytes <= raw.size()) {
                for (uint32_t i = 0; i < list_size; ++i) {
                    uint16_t type_idx;  // FIXED: uint16_t, not uint32_t
                    std::memcpy(&type_idx, raw.data() + list_start + i * 2, 2);  // FIXED: i * 2, reading 2 bytes
                    if (type_idx < hdr.type_ids_size &&
                        hdr.type_ids_off + (type_idx + 1) * 4 <= raw.size()) {
                        uint32_t desc_idx;
                        std::memcpy(&desc_idx,
                                    raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                        params_str += read_dex_string_from_raw(raw, desc_idx, hdr);
                    }
                }
            }
        }

        return "(" + params_str + ")" + return_type_desc;
    }

fallback:
    // Fallback: try the merged DexReport's method_ids + protos tables.
    if (dex_report_ && method_idx < dex_report_->method_ids.size()) {
        // ── A-R5 (S218, V2 fix — R25 matrix wave): CLASS-INFO PROTO
        // FALLBACK LAW. The old fallback returned the CONSTANT "()V" —
        // even though the method's TRUE descriptor is sitting in the
        // merged class-info tables (method_ids[method_idx] →
        // (class_idx, name_idx) → class_info_index_ → the class's
        // direct/virtual method entry). The constant leaked into every
        // descriptor-sensitive decision: the F-280 exact-(name, proto)
        // match (dalvik_engine.cpp, the F-280 block inside
        // try_recursive_invoke) compared "()V" against the real "()I"
        // and declared NO local match → its super-walk let an ANCESTOR's
        // lenient-selected same-name body outrank the receiver's own
        // declaration (the R25 dispatch-matrix probe's v_declared_super
        // row: new LSub; + invoke-virtual LBase.m answered 1, the base
        // body, instead of the override's 2 — the exact ART-law
        // violation §5 C3 demanded the matrix surface). First
        // observable: tests/r25_dispatch_matrix_test.cpp rows at
        // 14c4bf4e + /tmp dbg minimal repro (new-instance LSub; +
        // invoke-virtual (LSub.m) → LBase.m body ran).
        // Fix: consult the class-info method tables BEFORE the constant
        // default; first same-name non-empty descriptor wins (overload
        // ambiguity documented — best-available, strictly more accurate
        // than the constant; the raw-DEX path above is untouched so
        // real-APK proto_ids resolution is byte-identical).
        uint16_t class_idx = dex_report_->method_ids[method_idx].class_idx;
        uint32_t name_idx = dex_report_->method_ids[method_idx].name_idx;
        if (class_idx < dex_report_->types.size() &&
            name_idx < dex_report_->strings.size()) {
            const std::string& cname = dex_report_->types[class_idx];
            const std::string& mname = dex_report_->strings[name_idx];
            auto cit = class_info_index_.find(cname);
            if (!cname.empty() && !mname.empty() &&
                cit != class_info_index_.end()) {
                const dex::ClassInfo& ci =
                    dex_report_->classes[cit->second];
                for (const auto& mm : ci.direct_methods)
                    if (mm.name == mname && !mm.descriptor.empty())
                        return mm.descriptor;
                for (const auto& mm : ci.virtual_methods)
                    if (mm.name == mname && !mm.descriptor.empty())
                        return mm.descriptor;
            }
        }
        // (The raw proto_idx route stays the raw-DEX path above; the merged
        // protos vector cannot be used because multi-DEX merging shifts indices.)
        // because multi-DEX merging shifts indices. After the class-info
        // consult above, the "()V" constant remains only for methods that
        // exist in NO class-info table (merged-away classes).
    }
    return "()V";
}

// ============================================================================

DalvikExecutionResult DalvikExecutionEngine::execute_apk(
    const std::string& apk_path,
    const dex::DexReport& dex_report,
    bool verbose
) {
    // EXP-037 Phase B (BLOCKER-019): delegate to execute_apk_with_activity
    // with empty activity name (falls back to scan-based heuristic).
    return execute_apk_with_activity(apk_path, dex_report, std::string(), verbose);
}

DalvikExecutionResult DalvikExecutionEngine::execute_apk_with_activity(
    const std::string& apk_path,
    const dex::DexReport& dex_report,
    const std::string& activity_class_name,
    bool verbose
) {
    verbose_ = verbose;

    // M3 FINDING-016: per-run reset of the exception-honesty state + the
    // strict-mode env read (ART process-death law gate).
    uncaught_in_flight_count_ = 0;
    uncaught_in_flight_log_.clear();
    strict_uncaught_crash_ = false;
    strict_crash_reason_.clear();
    // F-NEW-200: per-run reset of the API status census (stub roll-up).
    api_status_implemented_ = 0;
    api_status_stubbed_ = 0;
    api_status_missing_ = 0;
    api_status_error_ = 0;
    {
        const char* es = std::getenv("MINIANDROID_EXC_STRICT");
        exc_strict_ = (es != nullptr && es[0] == '1');
    }

    // EXP-042 Phase 1: Gate debug cerr lines behind verbose. Previously these
    // always printed, generating enormous log volume during long runs (100 M
    // instructions × several cerr lines per recursive call = GB of stderr).
    if (verbose_) {
        std::cerr << "[EXP039] execute_apk_with_activity entered" << std::endl;
        std::cerr << "[EXP039] per_dex_raw_data_ size=" << per_dex_raw_data_.size() << std::endl;
        std::cerr << "[EXP039] class_to_dex_index_ size=" << class_to_dex_index_.size() << std::endl;
        std::cerr << "[EXP039] config_.max_instructions=" << config_.max_instructions << std::endl;
        std::cerr.flush();
    }
    // EXP-037 Phase B (BLOCKER-002 + BLOCKER-015 FIX):
    // Store the DexReport pointer so invoke-* / iget/iput/sget/sput handlers
    // can resolve method_idx and field_idx via DexReport::method_ids[] /
    // field_ids[]. Without this, every invoke-* handler sees dex_report_
    // as nullptr and falls back to "<method_idx:N>" placeholder strings,
    // which prevents the API bridge from routing framework calls.
    dex_report_ = &dex_report;
    // EXP-088+ Phase 1.2: Now that dex_report_ is set, inject ALL classes
    // from secondary DEX files (classes2.dex..classesN.dex) into the merged
    // dex_report_->classes vector and class_info_index_.
    //
    // Without this, only classes.dex (DEX 0) classes are available for
    // runtime dispatch. Any class defined in DEX 1+ (e.g. Telegram's
    // UserConfig in classes3.dex) cannot be found by try_recursive_invoke,
    // returning "class not in index" silently and dropping the call.
    //
    // The merged dex_report pointer (dex_report_) was just set above, so
    // this is the earliest point we can call inject_secondary_dex_classes().
    inject_secondary_dex_classes();

    // ── CODER7 WAVE-6: LoadedApk-lite — foreign store code injection ────
    // The S185 LOAD-FIRST law (#536): foreign components must EXECUTE, so
    // every store package's DEX classes are injected BEFORE any dispatch
    // can consult them (AOSP LoadedApk: the code is loaded before the
    // component is delivered). Runs only when a package store exists
    // (WAVE-5 MINIANDROID_PKG_STORE) — the no-store path is byte-identical.
    if (c7_pkg_index_ && !c7_pkg_index_->empty()) {
        std::vector<std::pair<std::string, std::string>> c7_xpairs;
        for (const auto& c7_pname : c7_pkg_index_->package_names()) {
            const auto* c7_pkg = c7_pkg_index_->find_package(c7_pname);
            if (c7_pkg && !c7_pkg->apk_path.empty() &&
                c7_pkg->apk_path != apk_path)
                c7_xpairs.emplace_back(c7_pkg->apk_path, c7_pname);
        }
        size_t c7_fx = inject_foreign_apk_code(c7_xpairs);
        if (c7_fx > 0)
            std::cerr << "[C7-W6] LoadedApk-lite: " << c7_fx
                      << " foreign classes loadable for cross-package "
                      << "component dispatch" << std::endl;
    }

    DalvikExecutionResult result;
    result.apk_name = apk_path.substr(apk_path.find_last_of("/\\") + 1);
    result.timestamp = get_timestamp();
    result.dex_report = &dex_report;

    // [R341-APP] AOSP handleBindApplication: bind the manifest Application
    // class RIGHT AFTER DEX infrastructure is ready and BEFORE any activity
    // work. App.onCreate (Dagger/Hilt component graphs, Koin start, etc.)
    // now executes with full method_idx resolution and multi-DEX classes.
    {
        uint32_t bound_app = bind_manifest_application(result);
        if (bound_app != 0) {
            std::cerr << "[R341-APP] bound application obj#" << bound_app
                      << " (" << application_class_desc_ << ")" << std::endl;
        }
    }

    auto start_time = Clock::now();
    
    log("Executing APK: " + apk_path);
    log("DEX classes: " + std::to_string(dex_report.classes_count));
    
    // ====================================================================
    // EXP-031.6 DEBUG: Trace complete DEX extraction pipeline
    // ====================================================================
    log("=== EXP-031.6 PIPELINE TRACE ===");
    
    int total_methods = 0;
    int methods_with_bytecode = 0;
    int methods_without_bytecode = 0;
    int total_instructions = 0;
    
    for (const auto& cls : dex_report.classes) {
        log("CLASS: " + cls.name + " (" + std::to_string(cls.all_methods().size()) + " methods)");
        
        for (const auto& method : cls.all_methods()) {
            total_methods++;
            
            bool has_code = !method.bytecode.empty();
            size_t insn_count = method.bytecode.size();
            
            if (has_code) {
                methods_with_bytecode++;
                total_instructions += insn_count;
                log("  METHOD [HAS CODE]: " + method.name + method.descriptor + 
                    " | code_off=0x" + std::to_string(method.code_offset) +
                    " | insns_size=" + std::to_string(insn_count) +
                    " | first_insn=0x" + (insn_count > 0 ? 
                        std::to_string(method.bytecode[0]) : "N/A"));
            } else {
                methods_without_bytecode++;
                log("  METHOD [NO CODE]:  " + method.name + method.descriptor +
                    " | code_off=0x" + std::to_string(method.code_offset) +
                    " | is_native=" + (method.is_native ? "Y" : "N") +
                    " | is_abstract=" + (method.is_abstract ? "Y" : "N"));
            }
        }
    }
    
    log("=== PIPELINE SUMMARY ===");
    log("Total methods: " + std::to_string(total_methods));
    log("With bytecode: " + std::to_string(methods_with_bytecode));
    log("Without bytecode: " + std::to_string(methods_without_bytecode));
    log("Total instructions: " + std::to_string(total_instructions));
    
    if (total_instructions == 0) {
        log("🔴 CRITICAL: ZERO INSTRUCTIONS EXTRACTED FROM DEX!");
        log("Root cause candidates:");
        log("  1. parse_code_item() not called (check class_data parsing)");
        log("  2. parse_code_item() called but insns_size=0");
        log("  3. parse_code_item() fails bounds check silently");
    }
    log("=== END EXP-031.6 TRACE ===");
    
    // Find main activity entry point
    if (!dex_report.classes.empty()) {
        log("🔍 Searching " + std::to_string(dex_report.classes.size()) + " classes for entry point...");

        // EXP-037 Phase B (BLOCKER-019 FIX): If the caller provided an explicit
        // activity_class_name from the AndroidManifest, look for that class
        // first. This bypasses the "Activity"/"Main"/"activity" name scan
        // which fails for obfuscated APKs (e.g. TinyMusicPlayer uses La/a;,
        // La/b;, etc.).
        //
        // The activity_class_name is expected to be in DEX type descriptor
        // form, e.g. "Lcom/martinmimigames/tinymusicplayer/Launcher;".
        // If the manifest gives it in dotted form ("com.foo.Launcher"),
        // the caller should convert it.
        if (!activity_class_name.empty()) {
            log("🎯 Manifest-provided activity class: " + activity_class_name);

            // EXP-086 Phase 1: Build the set of descriptor variants to try.
            // activity_class_name can be: dotted ("org.foo.Launcher") or
            // descriptor ("Lorg/foo/Launcher;"). We try both forms.
            std::vector<std::string> descriptor_variants;
            descriptor_variants.push_back(activity_class_name);  // as-is
            {
                std::string descriptor_form = "L" + activity_class_name + ";";
                descriptor_variants.push_back(descriptor_form);
            }
            {
                std::string converted = activity_class_name;
                for (auto& c : converted) if (c == '.') c = '/';
                std::string descriptor_form2 = "L" + converted + ";";
                descriptor_variants.push_back(descriptor_form2);
            }

            // First try: search dex_report.classes (single-DEX report from DEX 0).
            bool found = false;
            for (const auto& cls : dex_report.classes) {
                bool match = false;
                for (const auto& variant : descriptor_variants) {
                    if (cls.name == variant) {
                        match = true;
                        break;
                    }
                }
                if (match) {
                    log("  ✅ Found manifest activity class in DEX 0: " + cls.name);
                    result.main_class = cls.name;
                    found = true;

                    // EXP-043 Phase 4: Pre-populate static fields that Android's
                    // framework would have set before onCreate is called.
                    // Without this, ApplicationLoader.applicationContext is null
                    // and postInitApplication halts at PC=8.
                    //
                    // 1. Create the Application/Context singleton
                    // [R341-APP] When the AOSP bind law already attached the
                    // manifest Application class (bind_manifest_application,
                    // obj identity + real DEX lifecycle), REUSE that object —
                    // allocating a second plain Landroid/app/Application;
                    // here would fork the process application identity.
                    uint32_t app_ctx_id;
                    std::string app_ctx_desc;
                    if (application_object_id_ != 0 &&
                        heap_.has_object(application_object_id_)) {
                        app_ctx_id = application_object_id_;
                        app_ctx_desc = application_class_desc_.empty()
                                           ? "Landroid/app/Application;"
                                           : application_class_desc_;
                    } else {
                        app_ctx_id = heap_.allocate(
                            "Landroid/app/Application;",
                            0,  // pc=0 (pre-execution)
                            0   // frame_id=0 (pre-execution)
                        );
                        app_ctx_desc = "Landroid/app/Application;";
                    }
                    DalvikValue app_ctx_val;
                    app_ctx_val.type = DalvikType::OBJECT_REF;
                    app_ctx_val.object_id = app_ctx_id;
                    app_ctx_val.class_desc = app_ctx_desc;
                    // Store as ApplicationLoader.applicationContext static field
                    static_field_storage_["Lorg/telegram/messenger/ApplicationLoader;.applicationContext"]
                        = app_ctx_val;
                    // Also cache as the Context singleton so getResources() etc. work
                    api_singletons_["Landroid/content/Context;"] = app_ctx_id;

                    // EXP-046: Pre-populate NativeLoader.nativeLoaded = true.
                    DalvikValue native_loaded;
                    native_loaded.type = DalvikType::BOOLEAN;
                    native_loaded.bool_val = true;
                    native_loaded.int_val = 1;
                    static_field_storage_["Lorg/telegram/messenger/NativeLoader;.nativeLoaded"]
                        = native_loaded;

                    // 2. Create the Activity object (this) for onCreate
                    uint32_t activity_obj_id = heap_.allocate(
                        cls.name,  // "Lorg/telegram/ui/LaunchActivity;"
                        0,
                        0
                    );
                    DalvikValue activity_val;
                    activity_val.type = DalvikType::OBJECT_REF;
                    activity_val.object_id = activity_obj_id;
                    activity_val.class_desc = cls.name;

                    // AOSP fidelity: run the app's declared <init>()V so
                    // instance-field initializers are live before onCreate.
                    run_activity_default_init(cls.name, activity_obj_id, result);

                    // UNIFIED_011.3 FRAME-2 (§23): record the activity's heap
                    // object id so post-launch probes (click-test XML
                    // android:onClick dispatch) can pass the REAL activity
                    // instance as `this`. Without it, handlers executed with
                    // `this` = the clicked View object — every instance-field
                    // access (this.big, this.chrono, ...) hit the wrong heap
                    // object and the post-interaction re-render was unchanged.
                    if (shadow_registry_ != nullptr) {
                        auto* activity_shadow =
                            shadow_registry_->find_as<framework::ActivityShadow>();
                        if (activity_shadow != nullptr) {
                            activity_shadow->set_activity_heap_id(activity_obj_id);
                            std::cerr << "[U0113-ACTIVITY] activity heap object #"
                                      << activity_obj_id << " (" << cls.name
                                      << ") recorded for handler dispatch" << std::endl;
                        }
                    }
                    // F-NEW-396 (CONT-94) IDENTITY LAW — the DEX-0 launch path
                    // must record the activity singleton exactly like the
                    // multi-DEX and legacy-scan paths already do
                    // (api_singletons_[<activity descriptor>] = <heap id>).
                    // Evidence (Telegram official 12.10.5, run
                    // run/cont94/tg_official_diag3): this path printed
                    // [U0113-ACTIVITY] #694 but stored NO singleton entry, so
                    // the later getParentActivity() law's
                    // get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;")
                    // cache-MISSED and fabricated a fresh uninitialized
                    // LaunchActivity (#7307). The app's
                    // checkSystemBarColors did instanceof-LaunchActivity (TRUE —
                    // right class, wrong instance), invoked H(Z Z Z)V on the
                    // empty object, which read field p0 = null and called
                    // ActionBarLayout.w() on a null receiver — NPE ×3, three
                    // APP-BOUNDARY unwinds, login UI construction killed, the
                    // framebuffer stayed at 188/2073600 non-white pixels.
                    // AOSP law: Fragment.getParentActivity() answers THE
                    // activity hosting the fragment — one identity per process.
                    api_singletons_[cls.name] = activity_obj_id;
                    std::cerr << "[C94-SINGLETON] LAUNCH-STORE key='" << cls.name
                              << "' id=" << activity_obj_id << std::endl;

                    // Find onCreate method
                    // ── F-NEW-626 (S209): AOSP LAUNCH-ENTRY LAW — onCreate
                    // FIRST, classic-JVM main FALLBACK. AOSP
                    // ActivityThread.performLaunchActivity launches an
                    // Activity-derived class through onCreate(Bundle); a
                    // `main` method in an activity class is a NON-launch
                    // helper unless it is the classic JVM signature
                    // public static void main(String[]) — the shape the
                    // original heuristic targeted. Live defect (rttt
                    // org.kirkezz.rttt, SDL3 bootstrap): SDL 2.30.x declares
                    // `protected void main()V` — the SDL NATIVE-THREAD main
                    // invoked LATER by SDLMain.run (AOSP SDLActivity.java
                    // flow: onCreate → SDLThread → SDLMain.run → main() →
                    // nativeRunMain) — BEFORE onCreate in the dex method
                    // table; the old single-pass `onCreate || main` scan
                    // matched main()V first, onCreate never ran,
                    // mSingleton stayed null, SDLActivity.main pc=1 →
                    // getMainSharedObject on a null receiver → f141 NPE →
                    // APP BOUNDARY → white face 31ddd4d5b8e6d18e (baseline
                    // ×3 deterministic, binary 6da4574d2105529c). Two-pass
                    // law on BOTH launch paths (manifest launcher + legacy
                    // heuristic): Pass 1 picks onCreate when the class
                    // declares one; Pass 2 (only when NO onCreate exists)
                    // picks a STATIC main([Ljava/lang/String;)V — a bare
                    // main()V can never be a launch entry.
                    bool e626_has_oncreate = false;
                    bool e626_has_classic_main = false;
                    for (const auto& m626 : cls.all_methods()) {
                        if (m626.name == "onCreate") {
                            e626_has_oncreate = true;
                            break;
                        }
                    }
                    if (!e626_has_oncreate) {
                        for (const auto& m626 : cls.all_methods()) {
                            if (m626.name == "main" &&
                                m626.descriptor == "([Ljava/lang/String;)V" &&
                                (m626.access_flags & 0x0008)) {
                                e626_has_classic_main = true;
                                break;
                            }
                        }
                    }
                    for (const auto& method : cls.all_methods()) {
                        bool e626_pick;
                        if (e626_has_oncreate) {
                            e626_pick = (method.name == "onCreate");
                        } else {
                            e626_pick = (e626_has_classic_main &&
                                         method.name == "main" &&
                                         method.descriptor ==
                                             "([Ljava/lang/String;)V" &&
                                         (method.access_flags & 0x0008));
                        }
                        if (!e626_pick) {
                            continue;
                        }
                        result.main_method = method.name;
                        log("Found entry point: " + method.name + method.descriptor);
                        if (!method.bytecode.empty()) {
                                log("🎯 CALLING execute_method_internal() for " + method.name +
                                    " with " + std::to_string(method.bytecode.size()) + " instructions");

                                // ── CONT-68 (F-NEW-366): bind the effective
                                // ACTIVITY theme before onCreate (AOSP law: the
                                // theme is bound at Activity attach — before any
                                // content or AppCompat subdecor decision;
                                // ActivityInfo.getThemeResource: activity theme >
                                // application theme).
                                {
                                    uint32_t eff_theme =
                                        resources::ResourceRuntime::instance()
                                            .resolve_activity_theme(apk_path_, cls.name);
                                    resources::ResourceRuntime::instance()
                                        .set_activity_theme(eff_theme);
                                }

                                // EXP-043 Phase 4: Pass `this` (Activity) and Bundle
                                // as args. onCreate(Bundle) has ins=2: p0=this, p1=Bundle.
                                // The Bundle can be null (real Android passes null on
                                // first launch).
                                std::vector<DalvikValue> entry_args;
                                entry_args.push_back(activity_val);  // p0 = this (Activity)
                                entry_args.push_back(DalvikValue::make_null());  // p1 = Bundle (null)

                                // ── ROOT-062 (S115): AOSP CREATED-PHASE FAN-OUT ──
                                // Activity.performCreate law (API 29 pairing):
                                //   dispatchActivityPreCreated → onCreate →
                                //   dispatchActivityCreated → dispatchActivityPostCreated.
                                // The androidx ReportFragment$LifecycleCallbacks
                                // (registered DURING onCreate — ReportFragment
                                // injection) drive the LifecycleRegistry from these
                                // hooks: onActivityPostCreated → dispatch(ON_CREATE)
                                // moves the registry INITIALIZED → CREATED and gives
                                // every observer its first (ON_CREATE) event. Without
                                // this pairing the first registry sync is ON_START:
                                // androidx.savedstate.Recreator asserts
                                // "Next event must be ON_CREATE" and the launch
                                // dies at APP BOUNDARY (forkgram 12.10.8.0
                                // LaunchActivity.onCreate evidence + the S115 sweep
                                // family: secuso #86+#98, blockblast #86-class).
                                // The manifest-class block below (the dooz path)
                                // already fires this pairing — this site was the
                                // only onCreate dispatch that skipped it.
                                dispatch_activity_lifecycle_callbacks(
                                    "onActivityPreCreated", result);

                                execute_method_internal(
                                    cls.name,
                                    method.name,
                                    method.descriptor,
                                    method.bytecode,
                                    method.registers_size ? method.registers_size : 16,  // EXP-058: use actual
                                    method.ins_size ? method.ins_size : 2,  // EXP-058: use actual
                                    method.outs_size ? method.outs_size : 4,  // EXP-058: use actual
                                    entry_args,
                                    result,
                                    method.tries_size,
                                    method.tries_data.data(),
                                    method.tries_data.size()
                                );

                                if (method.name == "onCreate") {
                                    // ── F-NEW-304 (CONT-42): the CREATED-
                                    // stage fragment drain. AOSP: a commit()
                                    // inside onCreate enqueues the op; the
                                    // fragment reaches CREATED (onAttach →
                                    // onCreate) at the host's created window.
                                    // The queue the shadow committed is
                                    // consumed HERE — before the created
                                    // fan-out — so fragments that registered
                                    // preference state are ready before the
                                    // host reports ACTIVITY_CREATED.
                                    advance_fragments_to_created(result);
                                    dispatch_activity_lifecycle_callbacks(
                                        "onActivityCreated", result);
                                    // ── A93 (A1–A104 knowledge transfer,
                                    // Issue #382 audit): AOSP
                                    // ActivityThread.performLaunchActivity
                                    // dispatches Activity.onPostCreate(Bundle)
                                    // after callActivityOnCreate (+ restore)
                                    // and BEFORE the record is started
                                    // (handleStartActivity → onStart). Apps
                                    // that build content in onPostCreate
                                    // (e.g. minos GameView) need this hop;
                                    // non-overriders fall through to the
                                    // framework Activity stub. Same Bundle
                                    // shape as onCreate (null on cold launch).
                                    //
                                    // ── CONT-68 (F-NEW-366): the AOSP
                                    // handleStartActivity FINISH GATE —
                                    // `if (r.activity.mFinished) return;`
                                    // (fetched ActivityThread.java): an
                                    // activity that called finish() inside
                                    // onCreate is NEVER started — no
                                    // onPostCreate, no onStart, no onResume
                                    // (performResumeActivity carries the same
                                    // gate). Splash-style apps (Privacy
                                    // Friendly Memory/Notes: startActivity +
                                    // finish in onCreate, no setContentView)
                                    // hit this gate on every real device;
                                    // without it the engine drove
                                    // AppCompatDelegateImpl.onPostCreate →
                                    // ensureSubDecor → createSubDecor with the
                                    // platform SplashTheme and the REAL
                                    // appcompat DEX threw the
                                    // "Theme.AppCompat" ISE the device never
                                    // reaches. The shadow's pending_finish
                                    // flag IS the mFinished state at this
                                    // point (finish() recorded it during
                                    // onCreate; the G07 cascade consumes it
                                    // later, at the frame boundary).
                                    bool f366_finished_in_create = false;
                                    {
                                        auto* as_fin =
                                            shadow_registry_
                                                ? shadow_registry_->find_as<
                                                      framework::ActivityShadow>()
                                                : nullptr;
                                        f366_finished_in_create =
                                            as_fin && as_fin->pending_finish();
                                    }
                                    if (f366_finished_in_create) {
                                        log("[A93-POSTCREATE] skipped: activity "
                                            "finished during onCreate (AOSP "
                                            "handleStartActivity mFinished gate)");
                                    } else {
                                        DalvikValue postcreate_val;
                                        std::vector<DalvikValue> postcreate_args;
                                        postcreate_args.push_back(activity_val);  // p0 = this
                                        postcreate_args.push_back(
                                            DalvikValue::make_null());  // p1 = Bundle
                                        bool post_ok = try_recursive_invoke(
                                            cls.name,
                                            "onPostCreate",
                                            postcreate_args,
                                            postcreate_val,
                                            result,
                                            "(Landroid/os/Bundle;)V"
                                        );
                                        log(post_ok
                                                ? "[A93-POSTCREATE] Activity."
                                                  "onPostCreate dispatched"
                                                : "[A93-POSTCREATE] onPostCreate "
                                                  "not overridden (framework "
                                                  "stub fall-through)");
                                    }
                                    dispatch_activity_lifecycle_callbacks(
                                        "onActivityPostCreated", result);
                                }
                                log("✅ execute_method_internal() returned");
                            } else {
                                log("⚠️ Method " + method.name + " has EMPTY bytecode - skipping");
                            }
                            break;
                    }
                    // ── F-NEW-482 (CONT-155): INHERITED onCreate DISPATCH ──
                    // AOSP ActivityThread.performLaunchActivity law: the
                    // framework ALWAYS calls activity.onCreate(savedInstanceState)
                    // on the receiver's runtime class — regardless of WHICH
                    // superclass declares it. The same-class all_methods()
                    // scan above silently skipped launcher activities that
                    // declare only <init> and inherit onCreate from a base
                    // activity (Simple Mobile Tools SplashActivity -> Ll7/h;
                    // whose 219-insn onCreate never ran; cohort evidence: 7/17
                    // of the CONT-154 WINDOW_ROOT apps: flashlight,
                    // app.subster, voyager, how2vote, ricochlime,
                    // fdroid-privileged, fossify-contacts — all reached
                    // onStart/onResume with main_method EMPTY and zero
                    // setContentView). Fix: the try_recursive_invoke
                    // super-chain walk — the SAME resolution law the multi-DEX
                    // manifest path and the G07 onStart/onResume dispatch
                    // already use. Wrap mirrors the found-path above exactly:
                    // theme bind (CONT-68) -> onActivityPreCreated (F-058) ->
                    // onCreate -> fragments-to-created (F-NEW-304) ->
                    // onActivityCreated -> F-NEW-366 finish gate -> onPostCreate
                    // (A93) -> onActivityPostCreated.
                    if (result.main_method.empty()) {
                        log("🎯 F-NEW-482: launcher class declares no onCreate/main"
                            " — dispatching INHERITED onCreate via super-chain");
                        {
                            uint32_t eff_theme =
                                resources::ResourceRuntime::instance()
                                    .resolve_activity_theme(apk_path_, cls.name);
                            resources::ResourceRuntime::instance()
                                .set_activity_theme(eff_theme);
                        }
                        dispatch_activity_lifecycle_callbacks(
                            "onActivityPreCreated", result);
                        DalvikValue f482_ret;
                        std::vector<DalvikValue> f482_args;
                        f482_args.push_back(activity_val);              // p0 = this
                        f482_args.push_back(DalvikValue::make_null());  // p1 = Bundle
                        bool ok482 = try_recursive_invoke(
                            cls.name, "onCreate", f482_args, f482_ret, result,
                            "(Landroid/os/Bundle;)V");
                        if (ok482) {
                            result.main_method = "onCreate";
                            log("🎯 F-NEW-482: inherited onCreate dispatched"
                                " via super-chain");
                            advance_fragments_to_created(result);
                            dispatch_activity_lifecycle_callbacks(
                                "onActivityCreated", result);
                            bool f366_finished_in_create = false;
                            {
                                auto* as_fin =
                                    shadow_registry_
                                        ? shadow_registry_->find_as<
                                              framework::ActivityShadow>()
                                        : nullptr;
                                f366_finished_in_create =
                                    as_fin && as_fin->pending_finish();
                            }
                            if (f366_finished_in_create) {
                                log("[A93-POSTCREATE] skipped (F-NEW-482): activity"
                                    " finished during onCreate");
                            } else {
                                DalvikValue postcreate_val;
                                std::vector<DalvikValue> postcreate_args;
                                postcreate_args.push_back(activity_val);
                                postcreate_args.push_back(DalvikValue::make_null());
                                bool post_ok = try_recursive_invoke(
                                    cls.name, "onPostCreate", postcreate_args,
                                    postcreate_val, result,
                                    "(Landroid/os/Bundle;)V");
                                log(post_ok
                                        ? "[A93-POSTCREATE] onPostCreate dispatched"
                                          " (F-NEW-482 path)"
                                        : "[A93-POSTCREATE] onPostCreate not"
                                          " overridden (framework stub)");
                            }
                            dispatch_activity_lifecycle_callbacks(
                                "onActivityPostCreated", result);
                        } else {
                            log("⚠️ F-NEW-482: inherited onCreate also unresolved"
                                " — falling through to the legacy heuristic");
                        }
                    }
                    // Skip the legacy scan loop
                    goto entry_point_search_done;
                }
            }
            log("⚠️ Manifest activity class '" + activity_class_name + "' not found in dex_report.classes (DEX 0) — trying multi-DEX index");

            // EXP-086 Phase 1: Multi-DEX fallback.
            // dex_report.classes only contains classes from DEX 0 (the first
            // DEX file). The activity class may be in DEX 2/3/4 (e.g. Telegram
            // LaunchActivity is in classes3.dex). Use class_to_dex_index_
            // (built by build_class_dex_index) to check ALL DEX files.
            if (!found && !class_to_dex_index_.empty()) {
                for (const auto& variant : descriptor_variants) {
                    auto it = class_to_dex_index_.find(variant);
                    if (it != class_to_dex_index_.end()) {
                        uint32_t dex_idx = it->second;
                        log("  ✅ Found manifest activity class in DEX " + std::to_string(dex_idx) + ": " + variant);
                        result.main_class = variant;

                        // EXP-086 Phase 1: Load this class's full bytecode from
                        // per_dex_raw_data_[dex_idx] and inject it into
                        // dex_report_->classes so try_recursive_invoke can find
                        // it via class_info_index_. This is the GENERIC fix for
                        // multi-DEX entry-point resolution.
                        if (dex_report_ && dex_idx < per_dex_raw_data_.size()) {
                            log("  → Loading class bytecode from DEX " + std::to_string(dex_idx) + "...");
                            // Use DexParser to parse JUST this class from the
                            // per-DEX raw data.
                            dex::DexParser parser;
                            auto single_report = parser.parse_data(per_dex_raw_data_[dex_idx],
                                                                    "DEX" + std::to_string(dex_idx));
                            // Find the target class in the single-DEX report
                            // EXP-086 Phase 1: dex_report_ is `const dex::DexReport*`
                            // because execute_apk_with_activity takes a const&.
                            // We use const_cast to inject the class — this is
                            // safe because we own the lifetime of dex_report
                            // (it's passed by the caller who keeps the original
                            // alive). The injected class is read-only data.
                            //
                            // EXP-088+ F1 defense-in-depth: Check class_info_index_
                            // FIRST. If inject_secondary_dex_classes() already
                            // injected this class (which it should have, since it
                            // injects ALL classes from ALL secondary DEX files),
                            // skip the push_back. This prevents:
                            //   1. Duplicate entries in dex_report_->classes
                            //   2. Potential vector reallocation that could
                            //      invalidate ClassInfo& references held by
                            //      parent execution frames (the F1 finding)
                            //
                            // This on-demand path is now effectively dead code
                            // for multi-DEX APKs (inject_secondary_dex_classes
                            // handles everything), but it's kept as a fallback
                            // for single-DEX APKs that don't call the bulk
                            // injection.
                            auto it_existing = class_info_index_.find(variant);
                            if (it_existing != class_info_index_.end()) {
                                log("  ✅ " + variant + " already in class_info_index_"
                                    " (index " + std::to_string(it_existing->second) +
                                    ") — skipping on-demand injection (inject_secondary_dex_classes"
                                    " already handled it)");
                                found = true;
                            } else {
                                auto& mutable_classes = const_cast<std::vector<dex::ClassInfo>&>(dex_report_->classes);
                                for (auto& single_cls : single_report.classes) {
                                    if (single_cls.name == variant) {
                                        // Inject into dex_report_->classes and update index
                                        mutable_classes.push_back(single_cls);
                                        size_t new_idx = mutable_classes.size() - 1;
                                        class_info_index_[variant] = new_idx;
                                        log("  ✅ Injected " + variant + " into dex_report_->classes"
                                            " (index " + std::to_string(new_idx) + ", "
                                            + std::to_string(single_cls.direct_methods.size())
                                            + " direct + "
                                            + std::to_string(single_cls.virtual_methods.size())
                                            + " virtual methods)");
                                        found = true;
                                        break;
                                    }
                                }
                                if (!found) {
                                    log("  ⚠️ Class " + variant + " not found in DEX "
                                        + std::to_string(dex_idx) + " raw data");
                                }
                            }
                        }

                        if (found) {
                            // EXP-043 Phase 4: Pre-populate static fields
                            uint32_t app_ctx_id = heap_.allocate(
                                "Landroid/app/Application;",
                                0,  // pc=0 (pre-execution)
                                0   // frame_id=0 (pre-execution)
                            );
                            DalvikValue app_ctx_val;
                            app_ctx_val.type = DalvikType::OBJECT_REF;
                            app_ctx_val.object_id = app_ctx_id;
                            app_ctx_val.class_desc = "Landroid/app/Application;";
                            static_field_storage_["Lorg/telegram/messenger/ApplicationLoader;.applicationContext"]
                                = app_ctx_val;
                            // Set current_dex_index_ so per-DEX resolution uses the right DEX
                            current_dex_index_ = dex_idx;
                        }
                        break;
                    }
                }
            }

            if (!found) {
                log("⚠️ Manifest activity class '" + activity_class_name + "' not found in any DEX — falling back to scan");
            } else {
                // EXP-086 Phase 1: Skip the legacy Activity/Main scan when we
                // found the manifest activity class in the multi-DEX index.
                // try_recursive_invoke will resolve onCreate via per-DEX raw data.
                log("🎯 Skipping legacy scan — manifest activity class found in multi-DEX index");
                // DEMO-ACTIVITY-THIS (2026-09-04): pass the REAL activity
                // instance as p0 (this). Per AOSP ActivityThread.
                // performLaunchActivity -> activity.onCreate(savedInstanceState),
                // onCreate(Bundle) is an INSTANCE method: p0 = this (Activity),
                // p1 = Bundle. The previous code pushed ONLY the Bundle, so
                // write_p() loaded null into p0 and the bytecode's v_p0 (this)
                // read as null — every `iput-object v, p0, field` inside
                // onCreate silently wrote to heap object 0 and every
                // `iget-object` of an instance field read back null. First
                // observed with the miniandroid-demo APK where title/status/
                // stage fields were all lost (addView received null children).
                // This mirrors the proven legacy path below which allocates
                // the Activity heap object and passes [this, null].
                uint32_t activity_obj_id = heap_.allocate(result.main_class, 0, 0);
                DalvikValue activity_val = DalvikValue::make_object(
                    activity_obj_id, result.main_class);
                // AOSP fidelity: run the app's declared <init>()V so
                // instance-field initializers are live before onCreate.
                run_activity_default_init(result.main_class, activity_obj_id, result);
                // Record the activity instance so post-launch probes (click
                // dispatch, findViewById, getContentResolver) share the SAME
                // object, exactly like the legacy path (UNIFIED_011.3 FRAME-2).
                if (shadow_registry_ != nullptr) {
                    auto* activity_shadow =
                        shadow_registry_->find_as<framework::ActivityShadow>();
                    if (activity_shadow != nullptr) {
                        activity_shadow->set_activity_heap_id(activity_obj_id);
                        std::cerr << "[U0113-ACTIVITY] activity heap object #"
                                  << activity_obj_id << " (" << result.main_class
                                  << ") recorded for handler dispatch" << std::endl;
                    }
                }
                // Cache as the Context singleton so getResources() etc. on the
                // activity return a stable object across the whole run.
                api_singletons_[result.main_class] = activity_obj_id;
                // CONT-94 probe: identity of the activity-singleton key.
                std::cerr << "[C94-SINGLETON] LAUNCH-STORE key='" << result.main_class
                          << "' id=" << activity_obj_id << std::endl;

                std::vector<DalvikValue> entry_args;
                entry_args.push_back(activity_val);              // p0 = this (Activity)
                entry_args.push_back(DalvikValue::make_null());  // p1 = Bundle (null)
                // ── F-058 (R-NEW-279): AOSP pre-create fan-out ─────────
                // ActivityThread.performLaunchActivity: after newInstance
                // (the <init> above) and BEFORE onCreate, registered
                // Application.ActivityLifecycleCallbacks receive
                // onActivityPreCreated. dooz evidence: this is the hook
                // whose observer (androidx/lifecycle/v) registers the
                // ReportFragment inner callback (u$a.a → registerActivity
                // LifecycleCallbacks) — without it the LifecycleRegistry
                // never leaves INITIALIZED and WrappedComposition.setContent
                // never runs (0-pixel first frame).
                dispatch_activity_lifecycle_callbacks("onActivityPreCreated",
                                                      result);
                // ── CONT-68 (F-NEW-366): bind the effective ACTIVITY theme
                // before onCreate (same law as the manifest path above:
                // ActivityInfo.getThemeResource; theme bound at attach).
                {
                    uint32_t eff_theme =
                        resources::ResourceRuntime::instance()
                            .resolve_activity_theme(apk_path_,
                                                    result.main_class);
                    resources::ResourceRuntime::instance().set_activity_theme(
                        eff_theme);
                }
                DalvikValue return_val;  // onCreate returns void
                try {
                    log("🎯 Invoking onCreate via try_recursive_invoke (manifest class)");
                    bool ok = try_recursive_invoke(
                        result.main_class,
                        "onCreate",
                        entry_args,
                        return_val,
                        result,
                        "(Landroid/os/Bundle;)V"
                    );
                    if (ok) {
                        log("✅ onCreate invoked via try_recursive_invoke");
                        result.main_method = "onCreate";
                    } else {
                        log("⚠️ try_recursive_invoke returned false for onCreate");
                    }
                } catch (const std::exception& e) {
                    log("❌ try_recursive_invoke threw: " + std::string(e.what()));
                }
                // ── F-058 (R-NEW-279): AOSP post-create fan-out ────────
                // Activity.performCreate: after onCreate returns,
                // mApplication.dispatchActivityCreated → onActivityCreated,
                // then onActivityPostCreated (API 29 pre/post pairing).
                dispatch_activity_lifecycle_callbacks("onActivityCreated",
                                                      result);
                // ── A93 (A1–A104 knowledge transfer, Issue #382 audit) ──
                // AOSP ActivityThread.performLaunchActivity: after
                // callActivityOnCreate (+ onRestoreInstanceState when state
                // exists), Instrumentation.callActivityOnPostCreate dispatches
                // Activity.onPostCreate(Bundle) BEFORE the activity record is
                // started (handleStartActivity → onStart). Apps that build
                // their content view in onPostCreate (e.g. minos GameView)
                // never reach content creation without this hop; apps that do
                // not override it fall through to the framework Activity
                // stub — the super-class law. Bundle carries the same launch
                // state argument shape as onCreate (null on a cold launch).
                //
                // ── CONT-68 (F-NEW-366): the AOSP handleStartActivity
                // FINISH GATE — see the manifest-path dispatch above for the
                // full law citation (ActivityThread.java: `if
                // (r.activity.mFinished) return;`). Same skip here.
                bool f366_finished_in_create = false;
                {
                    auto* as_fin =
                        shadow_registry_
                            ? shadow_registry_->find_as<
                                  framework::ActivityShadow>()
                            : nullptr;
                    f366_finished_in_create =
                        as_fin && as_fin->pending_finish();
                }
                if (f366_finished_in_create) {
                    log("[A93-POSTCREATE] skipped: activity finished during "
                        "onCreate (AOSP handleStartActivity mFinished gate)");
                } else
                {
                    DalvikValue postcreate_val;
                    std::vector<DalvikValue> postcreate_args;
                    postcreate_args.push_back(activity_val);          // p0 = this
                    postcreate_args.push_back(DalvikValue::make_null());  // p1 = Bundle
                    bool post_ok = try_recursive_invoke(
                        result.main_class,
                        "onPostCreate",
                        postcreate_args,
                        postcreate_val,
                        result,
                        "(Landroid/os/Bundle;)V"
                    );
                    log(post_ok
                            ? "[A93-POSTCREATE] Activity.onPostCreate dispatched"
                            : "[A93-POSTCREATE] onPostCreate not overridden "
                              "(framework stub fall-through)");
                }
                dispatch_activity_lifecycle_callbacks("onActivityPostCreated",
                                                      result);
                goto entry_point_search_done;
            }
        }

        // Look for Activity-like classes (legacy heuristic)
        for (const auto& cls : dex_report.classes) {
            log("  Checking class: [" + cls.name + "] for Activity/Main/activity");

            if (cls.name.find("Activity") != std::string::npos ||
                cls.name.find("Main") != std::string::npos ||
                cls.name.find("activity") != std::string::npos) {

                result.main_class = cls.name;
                log("Found main class candidate: " + cls.name);

                // Find onCreate method
                // ── F-NEW-626 (S209): AOSP LAUNCH-ENTRY LAW — identical
                // two-pass shape on the legacy heuristic path (see the full
                // law comment at the manifest-launcher site above).
                bool e626_has_oncreate = false;
                bool e626_has_classic_main = false;
                for (const auto& m626 : cls.all_methods()) {
                    if (m626.name == "onCreate") {
                        e626_has_oncreate = true;
                        break;
                    }
                }
                if (!e626_has_oncreate) {
                    for (const auto& m626 : cls.all_methods()) {
                        if (m626.name == "main" &&
                            m626.descriptor == "([Ljava/lang/String;)V" &&
                            (m626.access_flags & 0x0008)) {
                            e626_has_classic_main = true;
                            break;
                        }
                    }
                }
                for (const auto& method : cls.all_methods()) {
                    bool e626_pick;
                    if (e626_has_oncreate) {
                        e626_pick = (method.name == "onCreate");
                    } else {
                        e626_pick = (e626_has_classic_main &&
                                     method.name == "main" &&
                                     method.descriptor ==
                                         "([Ljava/lang/String;)V" &&
                                     (method.access_flags & 0x0008));
                    }
                    if (!e626_pick) {
                        continue;
                    }
                    result.main_method = method.name;
                    log("Found entry point: " + method.name + method.descriptor);

                    // Execute this method
                    if (!method.bytecode.empty()) {
                            log("🎯 CALLING execute_method_internal() for " + method.name +
                                " with " + std::to_string(method.bytecode.size()) + " instructions");
                            // DEMO-ACTIVITY-THIS (2026-09-04): same fix as the
                            // manifest path above. The legacy heuristic path
                            // used to call onCreate with hardcoded regs=10,
                            // ins=1 and NO arguments — so `this` (p0) read as
                            // uninitialized and every instance-field write in
                            // onCreate was silently dropped. Per AOSP
                            // ActivityThread.performLaunchActivity we allocate
                            // the Activity heap object and pass [this, Bundle].
                            uint32_t activity_obj_id = heap_.allocate(cls.name, 0, 0);
                            DalvikValue activity_val = DalvikValue::make_object(
                                activity_obj_id, cls.name);
                            // AOSP fidelity: run the app's declared <init>()V so
                            // instance-field initializers are live before onCreate.
                            run_activity_default_init(cls.name, activity_obj_id, result);
                            if (shadow_registry_ != nullptr) {
                                auto* activity_shadow =
                                    shadow_registry_->find_as<framework::ActivityShadow>();
                                if (activity_shadow != nullptr) {
                                    activity_shadow->set_activity_heap_id(activity_obj_id);
                                    std::cerr << "[U0113-ACTIVITY] activity heap object #"
                                              << activity_obj_id << " (" << cls.name
                                              << ") recorded for handler dispatch" << std::endl;
                                }
                            }
                            api_singletons_[cls.name] = activity_obj_id;
                            // CONT-94 probe: identity of the activity-singleton key.
                            std::cerr << "[C94-SINGLETON] LEGACY-STORE key='" << cls.name
                                      << "' id=" << activity_obj_id << std::endl;
                            std::vector<DalvikValue> entry_args;
                            if (method.name == "onCreate") {
                                entry_args.push_back(activity_val);              // p0 = this
                                entry_args.push_back(DalvikValue::make_null());  // p1 = Bundle
                            }
                            execute_method_internal(
                                cls.name,
                                method.name,
                                method.descriptor,
                                method.bytecode,
                                method.registers_size ? method.registers_size : 16,
                                method.ins_size ? method.ins_size : 2,
                                method.outs_size ? method.outs_size : 4,
                                entry_args,
                                result,
                                method.tries_size,
                                method.tries_data.data(),
                                method.tries_data.size()
                            );
                            log("✅ execute_method_internal() returned");
                        } else {
                            log("⚠️ Method " + method.name + " has EMPTY bytecode - skipping");
                        }
                        break;
                }
                break;
            }
        }
        entry_point_search_done: ;

        // If no Activity found, try first class with methods
        log("🔍 main_method is " + (result.main_method.empty() ? "EMPTY" : result.main_method) + ", trying fallback...");
        if (result.main_method.empty()) {
            log("📋 Entering fallback mode - looking for any class with methods");
            for (const auto& cls : dex_report.classes) {
                log("  📋 Checking fallback class: [" + cls.name + "] with " + 
                    std::to_string(cls.all_methods().size()) + " methods");
                auto methods = cls.all_methods();
                log("  📋 all_methods() returned " + std::to_string(methods.size()) + " entries");
                if (!methods.empty()) {
                    result.main_class = cls.name;
                    const auto& method = methods[0];  // Use local copy
                    result.main_method = method.name;
                    
                    log("🎯 Using fallback entry: " + cls.name + "." + method.name);
                    log("🎯 Bytecode size: " + std::to_string(method.bytecode.size()));
                    
                    if (!method.bytecode.empty()) {
                        log("🚀 ABOUT TO CALL execute_method_internal() for fallback!");
                        try {
                            execute_method_internal(
                                cls.name, method.name, method.descriptor,
                                method.bytecode, 8, 0, 2, {}, result,
                                method.tries_size,
                                method.tries_data.data(),
                                method.tries_data.size()
                            );
                            log("✅ execute_method_internal() completed successfully");
                        } catch (const std::exception& e) {
                            log("❌ execute_method_internal() threw exception: " + std::string(e.what()));
                        }
                    } else {
                        log("⚠️ Fallback method has empty bytecode!");
                    }
                    break;
                }
            }
        }
    }
    
    auto end_time = Clock::now();
    result.total_execution_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
    result.final_registers = call_stack_.empty() ? json::object() : call_stack_.top().registers.dump();

    // M3 FINDING-016: surface the exception-honesty state on the result.
    // Default mode: count + bounded log (runtime engine downgrades plain
    // SUCCESS to PARTIAL_SUCCESS and records crash.log entries). Strict
    // mode: an app-boundary escape is the ART process-death law — CRASH.
    result.uncaught_in_flight_count = uncaught_in_flight_count_;
    result.uncaught_in_flight_log = uncaught_in_flight_log_;
    if (exc_strict_ && strict_uncaught_crash_) {
        result.final_status = DalvikExecutionResult::FinalStatus::CRASH_EXCEPTION;
        result.halt_reason = strict_crash_reason_;
    }

    log("Execution completed in " + std::to_string(result.total_execution_ms) + "ms");
    log("Instructions executed: " + std::to_string(result.total_instructions_executed));

    // CONT-42 THROUGHPUT LAW: the api_call_traces survivor ring ran O(1)
    // during execution; restore the exact chronological FIFO order once
    // before any consumer reads it (single O(cap) rotate — downstream
    // consumers keep reading chronological order exactly as before).
    ring_normalize_chrono(result.api_call_traces, result.api_call_ring_cursor);

    return result;
}

DalvikExecutionResult DalvikExecutionEngine::execute_method(
    const dex::MethodInfo& method,
    const dex::DexReport& dex_report,
    const std::vector<DalvikValue>& args,
    bool verbose
) {
    verbose_ = verbose;
    DalvikExecutionResult result;
    result.timestamp = get_timestamp();
    result.dex_report = &dex_report;
    result.main_class = method.defining_class;
    result.main_method = method.name;

    // UNIFIED_011.3 TYPED-CATCH: set dex_report_ on the unit entry point too.
    // Previously only execute_apk_with_activity set it (EXP-037 BLOCKER-002),
    // so direct execute_method callers had every resolve_*_for_dex fallback
    // return "<unknown>" — including the UNIFIED_011.3 typed-catch handler
    // type resolution (catch type descriptors are resolved per-DEX and fall
    // back to dex_report_->types).
    dex_report_ = &dex_report;
    // EXP-068 hierarchy map + EXP-045 class_info_index_ + EXP-088 dex index
    // are all built by build_class_dex_index(report) on the APK path; the
    // unit entry point needs them for invoke dispatch and type resolution.
    build_class_dex_index(dex_report);

    if (!method.bytecode.empty()) {
        execute_method_internal(
            method.defining_class,
            method.name,
            method.descriptor,
            method.bytecode,
            16,  // Default register count
            static_cast<uint32_t>(args.size()),
            4,   // Default outs
            args,
            result,
            method.tries_size,
            method.tries_data.data(),
            method.tries_data.size()
        );
    }

    // CONT-42: same chronological-restore law as execute_apk_with_activity.
    ring_normalize_chrono(result.api_call_traces, result.api_call_ring_cursor);

    return result;
}

// ============================================================================
// Core Execution Loop
// ============================================================================

// S56 frontier diagnostic: env-gated (MINIANDROID_LOOP_LOCALS_DIAG) frame
// locals dump at failure sites. READ-ONLY — pure get_register/heap reads;
// diagnostics must never change semantics (M3 law). Thread-local budget
// bounds the log volume. Prints: registers (int/long/obj), the receiver's
// heap fields, and the first elements of any array-typed field — enough to
// see probe/hash state (ScatterMap family: metadata longs + mask ints).
void DalvikExecutionEngine::dump_frame_locals_diag(const char* tag) {
    static thread_local const bool diag_on =
        std::getenv("MINIANDROID_LOOP_LOCALS_DIAG") != nullptr;
    if (!diag_on || !current_registers_) return;
    static thread_local uint32_t budget = 12;
    if (budget == 0) return;
    --budget;

    auto fmt_val = [this](const DalvikValue& v) -> std::string {
        std::ostringstream oss;
        switch (v.type) {
            case DalvikType::INT32: oss << "i=" << v.int_val; break;
            case DalvikType::INT64: oss << "j=" << v.long_val; break;
            case DalvikType::BOOLEAN: oss << "z=" << (v.bool_val ? 1 : 0); break;
            case DalvikType::FLOAT32: oss << "f=" << v.float_val; break;
            case DalvikType::FLOAT64: oss << "d=" << v.double_val; break;
            case DalvikType::OBJECT_REF:
            case DalvikType::STRING_REF: {
                oss << "(t=" << static_cast<int>(v.type) << ") o" << v.object_id
                    << " " << v.class_desc;
                if (v.type == DalvikType::STRING_REF && !v.is_null) {
                    std::string s = v.string_val.substr(0, 24);
                    oss << " \"" << s << "\"";
                }
                if (v.is_null) oss << " null";
                break;
            }
            case DalvikType::NULL_REF: oss << "null"; break;
            default: oss << "(t=" << static_cast<int>(v.type) << ")"; break;
        }
        return oss.str();
    };

    const uint32_t nregs = current_registers_->get_size();
    const uint32_t ins = current_registers_->get_ins_count();
    std::cerr << "[LOCALS-DIAG] " << tag << " " << current_class_ << "."
              << current_method_ << " regs=" << nregs << " ins=" << ins
              << " pc=" << pc_ << std::endl;
    for (uint32_t r = 0; r < nregs && r < 40; ++r) {
        DalvikValue v = get_register(static_cast<uint8_t>(r));
        std::cerr << "  v" << r << ": " << fmt_val(v) << std::endl;
    }
    if (nregs < ins) return;
    DalvikValue recv = get_register(static_cast<uint8_t>(nregs - ins));
    bool recv_obj =
        (recv.type == DalvikType::OBJECT_REF || recv.type == DalvikType::STRING_REF) &&
        !recv.is_null && heap_.has_object(recv.object_id);
    if (!recv_obj) return;
    const auto& objs = heap_.all_objects();
    auto it = objs.find(recv.object_id);
    if (it == objs.end()) return;
    std::cerr << "  this=o" << recv.object_id << " " << it->second.class_descriptor
              << " (" << it->second.fields.size() << " fields):" << std::endl;
    int fcount = 0;
    for (const auto& [fname, fval] : it->second.fields) {
        if (++fcount > 24) { std::cerr << "    ..." << std::endl; break; }
        std::cerr << "    " << fname << " = " << fmt_val(fval) << std::endl;
        // Array fields: dump length + first 12 elements (probe state).
        if (fval.type == DalvikType::OBJECT_REF && !fval.is_null &&
            heap_.has_object(fval.object_id)) {
            auto ait = objs.find(fval.object_id);
            if (ait == objs.end()) continue;
            std::string acl = ait->second.class_descriptor;
            // Arrays are heap objects; their desc may be "[J"-style or the
            // engine's synthetic "Larray;" marker — dump elements for both.
            bool is_array = (acl.size() > 1 && acl[0] == '[') || acl == "Larray;";
            if (is_array) {
                auto lf = ait->second.get_field("__array_length__");
                auto lnf = ait->second.get_field("__new_array_length__");
                int alen = -1;
                if (lf.type == DalvikType::INT32) alen = lf.int_val;
                else if (lnf.type == DalvikType::INT32) alen = lnf.int_val;
                std::cerr << "      len=" << alen << " elems:" << std::endl;
                for (int e = 0; e < alen && e < 12; ++e) {
                    auto ev = ait->second.get_field("array[" + std::to_string(e) + "]");
                    if (ev.type == DalvikType::UNINITIALIZED) { std::cerr << "        [" << e << "] <unset>" << std::endl; continue; }
                    std::cerr << "        [" << e << "] " << fmt_val(ev) << std::endl;
                }
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
// CONT-4 PHASE 1 — Lm2;.b solver ISE classification diagnostic.
// READ-ONLY (M3 law): pure get_register / heap / shadow-store reads.
//
// The frontier: fairymahjong throws IllegalStateException("Even face
// counts always permit a completion") from its own backtracking solver
// (Lm2;.b, guard pc=0x57f `if-lez v2 -> 0x5bb`). The engine cannot know a
// priori whether this is (a) an app bug — the game's parity claim is
// mathematically false for its own greedy strategy — or (b) a runtime
// root — our collection/array laws corrupted the solver's INPUT (face
// list) or STATE (counts/visited arrays) so the guard sees data the real
// ART would never produce. CONT-3 flagged residual [F-NEW-238-SET]
// POISON rows as the prime suspect.
//
// Decisive observation set (dumped at 4 pcs inside Lm2;.b):
//   * pc=0x51b / 0x525 / 0x531 — solver-section entry: every register,
//     full element dumps of register-held arrays ([I/[Z/[Ljava/lang/Object;
//     /Larray;) and the FULL CollectionShadow store of any register-held
//     ArrayList, with an INDEPENDENT per-face parity count (the game's own
//     invariant, recomputed from the store: kind-3 ints directly, kind-1
//     boxes via the Integer "value" field, kind-2 strings called out — a
//     string face in a numeric solver would itself be corruption).
//   * pc=0x57f — the guard visit: v2 plus the same array/collection dumps;
//     the FATAL visit (v2 <= 0) always dumps (it throws immediately after,
//     so this happens at most once per run); healthy visits budgeted.
//
// Bounded: fixed pc set + thread-local per-pc visit budgets (total < 12
// dumps per run). No semantics change: dump-only, and the lazy shadow
// state creation (get_or_create on an unseen id) yields the identical
// empty CollectionState the first real shadow op would create anyway.
// ─────────────────────────────────────────────────────────────────────────
void DalvikExecutionEngine::dump_cont4_solver_diag(uint32_t at_pc) {
    static thread_local const bool diag_on =
        std::getenv("MINIANDROID_CONT4_SOLVER_DIAG") != nullptr;
    if (!diag_on) return;

    // Solver chain targets: the Lm2;.b pcs plus the Kotlin-stdlib bridge
    // entries feeding its face-count Set (Lt;.r filter → Ls;.y limit →
    // Ls;.D toSet). Bridge dumps fire ONLY when Lm2;.b is on the call
    // chain (shared stdlib methods are called app-wide; unfiltered dumps
    // would both flood and catch the wrong invocation).
    const bool is_solver = (current_class_ == "Lm2;" && current_method_ == "b");
    const bool is_bridge =
        (current_class_ == "Ls;" &&
         (current_method_ == "D" || current_method_ == "y")) ||
        (current_class_ == "Lt;" && current_method_ == "r");
    if (is_bridge) {
        if (at_pc != 0x0 && at_pc != 0xFFFFFFFFu) return;
        bool in_chain = false;
        auto chain = call_stack_.snapshot_top_first();
        for (size_t fi = 0; fi < chain.size() && fi < 8; ++fi) {
            if (chain[fi].first == "Lm2;") { in_chain = true; break; }
        }
        if (!in_chain) return;
    } else if (!is_solver) {
        return;
    } else {
        if (!(at_pc == 0x0 || at_pc == 0x476 || at_pc == 0x47a ||
              at_pc == 0x480 || at_pc == 0x484 || at_pc == 0x4a1 ||
              at_pc == 0x51b || at_pc == 0x525 ||
              at_pc == 0x531 || at_pc == 0x57f)) return;
    }

    // Guard-operand short-circuit: only dump 0x57f when v2 <= 0 (the fatal
    // visit) or within the first two healthy visits (trajectory context).
    if (at_pc == 0x57f && current_registers_) {
        // 0x57f is `if-lez v2` — operand register v2 (8-bit form, low nibble
        // of the high byte is vAA; here v2 by disassembly).
        DalvikValue gv = get_register(2);
        int32_t gv_i = (gv.type == DalvikType::INT32) ? gv.int_val : 0;
        static thread_local uint32_t guard_healthy = 0;
        if (gv_i > 0 && guard_healthy >= 2) return;
        if (gv_i > 0) ++guard_healthy;
    }

    // Per-pc visit budgets (entry pcs dump only their first visits).
    static thread_local std::map<uint32_t, uint32_t> c4_visits;
    uint32_t& c4n = c4_visits[at_pc];
    const uint32_t c4_budget = (at_pc == 0x57f) ? 4u
                             : (is_bridge)      ? 8u
                             : (at_pc == 0x0)   ? 1u
                                                : 3u;
    if (c4n >= c4_budget) return;
    ++c4n;

    const char* c4_tag = is_bridge ? "BRIDGE" : "SOLVER";

    // Provenance helper: heap objects carry creator_pc (the allocating
    // pc) — one line answers "who minted this list/array".
    auto creator = [&](uint32_t id) -> std::string {
        const auto* ho = heap_.get(id);
        if (!ho) return "?";
        return "created@pc=0x" + [&] { std::ostringstream s; s << std::hex
            << ho->creator_pc << std::dec; return s.str(); }() +
            " frame#" + std::to_string(ho->creator_frame_id);
    };

    auto fmtv = [this](const DalvikValue& v) -> std::string {
        switch (v.type) {
            case DalvikType::INT32:  return "i" + std::to_string(v.int_val);
            case DalvikType::INT64:  return "j" + std::to_string(v.long_val);
            case DalvikType::BOOLEAN:return "z" + std::to_string(v.bool_val?1:0);
            case DalvikType::FLOAT32:return "f" + std::to_string(v.float_val);
            case DalvikType::FLOAT64:return "d" + std::to_string(v.double_val);
            case DalvikType::NULL_REF: return "null";
            case DalvikType::UNINITIALIZED: return "<unset>";
            case DalvikType::STRING_REF:
                if (v.is_null) return "str-null";
                return "str \"" + v.string_val.substr(0, 32) + "\"";
            case DalvikType::OBJECT_REF: {
                if (v.is_null || v.object_id == 0) return "o-null";
                std::string cls = v.class_desc;
                const auto* ho = heap_.get(v.object_id);
                if (ho && !ho->class_descriptor.empty())
                    cls = ho->class_descriptor;
                return "o#" + std::to_string(v.object_id) + " " + cls;
            }
            default: return "(t=" + std::to_string(static_cast<int>(v.type)) + ")";
        }
    };

    // Array element dump: heap arrays store length at __array_length__ and
    // elements at "array[i]" (kind-faithful DalvikValues).
    auto dump_array = [&](uint32_t arr_id) {
        const auto* ho = heap_.get(arr_id);
        if (!ho) return;
        auto lenf = ho->get_field("__array_length__");
        if (lenf.type != DalvikType::INT32) return;
        int32_t alen = lenf.int_val;
        std::cerr << "    array o#" << arr_id << " [" << ho->class_descriptor
                  << "] len=" << alen << " " << creator(arr_id) << " elems:";
        if (alen <= 0) { std::cerr << " (empty)" << std::endl; return; }
        int32_t show = alen < 160 ? alen : 160;
        for (int32_t e = 0; e < show; ++e) {
            auto ev = ho->get_field("array[" + std::to_string(e) + "]");
            std::cerr << " [" << e << "]" << fmtv(ev);
        }
        if (alen > show) std::cerr << " ...(" << (alen - show) << " more)";
        std::cerr << std::endl;
    };

    // Collection dump + independent parity count over the shadow store.
    auto dump_collection = [&](uint32_t obj_id) {
        framework::CollectionShadow* csh =
            shadow_registry_
                ? shadow_registry_->find_as<framework::CollectionShadow>()
                : nullptr;
        if (!csh) return;
        auto* st = csh->get_or_create(obj_id, false);
        if (!st) return;
        size_t n = st->elements.size();
        std::cerr << "    collection o#" << obj_id << " size=" << n
                  << " is_map=" << st->is_map << " " << creator(obj_id)
                  << " elems:";
        std::vector<int32_t> odd_faces;
        int32_t str_faces = 0, unset_faces = 0;
        // CONT-4: empty shadow store → the F-NEW-237b engine-array-backed
        // fallback serves get() from the object's own array[i] fields.
        // Dump the RAW backing slots (ref/string/int) — mixed kinds here
        // are the corruption signature (string slots where ints belong).
        if (n == 0 && heap_.has_object(obj_id)) {
            auto blenf = heap_.get_object_field(obj_id, "__array_length__");
            int32_t blen = (blenf && blenf->type == DalvikType::INT32)
                               ? blenf->int_val : 24;
            if (blen > 0) {
                std::cerr << " [backing len=" << blen << ":";
                int32_t bs = blen < 24 ? blen : 24;
                for (int32_t bi = 0; bi < bs; ++bi) {
                    std::string fn = "array[" + std::to_string(bi) + "]";
                    auto ev = heap_.get_object_field(obj_id, fn);
                    if (!ev) { std::cerr << " " << bi << ":<unset>"; continue; }
                    if (ev->type == DalvikType::STRING_REF)
                        std::cerr << " " << bi << ":str\"" << ev->string_val.substr(0,16) << "\"";
                    else if (ev->type == DalvikType::INT32)
                        std::cerr << " " << bi << ":i" << ev->int_val;
                    else if (ev->type == DalvikType::OBJECT_REF)
                        std::cerr << " " << bi << ":o#" << ev->object_id;
                    else
                        std::cerr << " " << bi << ":(t" << static_cast<int>(ev->type) << ")";
                }
                std::cerr << " ]" << std::endl;
            }
        }
        size_t show = n < 200 ? n : 200;
        std::map<int32_t, int32_t> face_counts;
        for (size_t i = 0; i < show; ++i) {
            uint8_t k = i < st->elem_kinds.size() ? st->elem_kinds[i] : 0;
            int32_t face = INT32_MIN;
            if (k == 3) {
                face = i < st->elem_ints.size() ? st->elem_ints[i] : INT32_MIN;
            } else if (k == 1) {
                uint32_t eid = st->elements[i];
                if (eid != 0 && heap_.has_object(eid)) {
                    auto bv = heap_.get_object_field(eid, "value");
                    if (bv && bv->type == DalvikType::INT32) face = bv->int_val;
                    else if (i < 8) {
                        std::string ecls;
                        const auto* eho = heap_.get(eid);
                        if (eho) ecls = eho->class_descriptor;
                        std::cerr << " [" << i << "]obj#" << eid << " " << ecls;
                    }
                } else {
                    if (i < 8) std::cerr << " [" << i << "]null-obj";
                }
            } else if (k == 2) {
                ++str_faces;  // string face in a numeric solver = corruption
                if (i < 24)
                    std::cerr << " [" << i << "]str\""
                              << (i < st->elem_strings.size()
                                      ? st->elem_strings[i].substr(0, 16)
                                      : "?")
                              << "\"";
            } else {
                ++unset_faces;
            }
            if (face != INT32_MIN) {
                if (i < 96) std::cerr << " " << face;
                auto fc = face_counts.find(face);
                if (fc == face_counts.end()) face_counts.emplace(face, 1);
                else ++fc->second;
            }
        }
        std::cerr << (n > show ? " ...(truncated)" : "") << std::endl;
        for (const auto& [face, cnt] : face_counts)
            if (cnt % 2 != 0) odd_faces.push_back(face);
        std::cerr << "    [CONT4-PARITY] distinct_faces="
                  << face_counts.size() << " odd_count_faces="
                  << odd_faces.size();
        for (size_t i = 0; i < odd_faces.size() && i < 12; ++i)
            std::cerr << " face" << odd_faces[i] << "x"
                      << face_counts[odd_faces[i]];
        std::cerr << " str_faces=" << str_faces
                  << " unset_faces=" << unset_faces << std::endl;
    };

    std::cerr << "[CONT4-" << c4_tag << "] " << current_class_ << "."
              << current_method_ << " pc=0x" << std::hex << at_pc
              << std::dec << " (visit " << c4n << ")"
              << " depth=" << call_stack_.depth() << " regs:";
    if (!current_registers_) { std::cerr << " none" << std::endl; return; }
    const uint32_t nregs = current_registers_->get_size();
    for (uint32_t r = 0; r < nregs && r < 31; ++r) {
        DalvikValue rv = get_register(static_cast<uint8_t>(r));
        if (rv.type == DalvikType::UNINITIALIZED) continue;
        std::cerr << " v" << r << "=" << fmtv(rv);
    }
    std::cerr << std::endl;
    // Deep dumps for every array/collection register (read-only).
    for (uint32_t r = 0; r < nregs && r < 31; ++r) {
        DalvikValue rv = get_register(static_cast<uint8_t>(r));
        if (rv.type != DalvikType::OBJECT_REF || rv.is_null ||
            rv.object_id == 0 || !heap_.has_object(rv.object_id))
            continue;
        const auto* ho = heap_.get(rv.object_id);
        if (!ho) continue;
        std::string cls = ho->class_descriptor;
        if (cls.size() > 1 && cls[0] == '[') dump_array(rv.object_id);
        else if (cls == "Larray;") dump_array(rv.object_id);
        else if (cls == "Ljava/util/ArrayList;" ||
                 cls == "Ljava/util/LinkedHashSet;" ||
                 cls == "Ljava/util/HashSet;" ||
                 cls == "Ljava/util/LinkedList;")
            dump_collection(rv.object_id);
        // Param-window provenance: at method entry, name every object
        // register's allocation site (the caller's minting pc).
        if (at_pc == 0x0)
            std::cerr << "    v" << r << " " << cls << " o#"
                      << rv.object_id << " " << creator(rv.object_id)
                      << std::endl;
    }
}

// ── CONT-47 D7 (DIAG-ONLY, env-gated): renderer read-side census state.
// D7a (MINIANDROID_D7_READCENSUS): while the draw window is open, count
// WHICH Lel0; (LayoutNode) fields the DEX draw walk reads — the A/n
// child-fold containers (order-bearing per D6) vs the single-ref q chain
// (last-inserted-wins). Counted in execute_iget/execute_iget_object,
// printed at draw-window close. Answers the OPDUMP bands 1-6 empty
// question with a read census instead of guesswork.
// D7c (MINIANDROID_D7_PLACECHECK): every insertAt (Lel0;.B) call records
// the inserted node + receiver ids (bounded); at draw-window close the
// walk prints each node's placement state (e:Z layout flag + q + A/n
// container array lens) — B touches NO placement per D6, so the chain
// may exist but sit unplaced behind the F-NEW-265 isPlaced draw gate.
namespace {
constexpr size_t D7_NODE_CAP = 512;
}  // namespace

// S224-TAPDRAIN: named (not anonymous) so the header externs bind — the
// tap-path drain reads the insertAt census + the once-per-node set.
std::set<uint32_t> g_d7_node_ids;
// S221: nodes the measure-bridge already serviced (once-per-node).
std::set<uint32_t> g_s221_bridged;

bool DalvikExecutionEngine::execute_method_internal(
    const std::string& class_name,
    const std::string& method_name,
    const std::string& descriptor,
    const std::vector<uint16_t>& bytecode,
    uint32_t registers_size,
    uint32_t ins_size,
    uint32_t outs_size,
    const std::vector<DalvikValue>& args,
    DalvikExecutionResult& result,
    uint16_t tries_size,
    const uint8_t* tries_data,
    size_t tries_data_size
) {
    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().invoke_internal, f107_t0);

    // F-NEW-282: CLASS_REF TOKEN MATERIALIZATION AT THE ARGUMENT BOUNDARY.
    // A CLASS_REF-typed register value (const-class / getOrCreateKotlinClass
    // token) is NOT a heap reference; the engine's frame machinery only
    // carries OBJECT_REF values intact across nested DEX calls, so a raw
    // CLASS_REF argument degrades to REGISTER_UNSET/zero by the time the
    // callee stores or compares it. Live face (real-Compose oracle):
    // ClassReference.<init>(Ljava/lang/Class;)V bound the token as
    // p1={t=CLASS_REF} at frame entry (PARAM-TRACE), yet the body's
    // iput-object v2, v1, jClass stored <unset> — every later consumer
    // (getJClass/equals/isInstance/getQualifiedName) then saw null and
    // ViewModelProvider.get(KClass) could not match its registered
    // initializer (IAE "No initializer set for given class null" → APP
    // BOUNDARY). ART law: a class literal IS a java.lang.Class instance —
    // one identity per (descriptor, loader). The F-103 law already mints
    // heap-backed Class tokens for const-class; materialize CLASS_REF
    // arguments to the SAME stable token object at the frame boundary so
    // the callee handles an ordinary reference. Identity per descriptor is
    // preserved (F-069 map), no app/package knowledge involved.
    // S156-P4 (CONT-42 zero-cost-gate law): the eager `= args` copy ran PER
    // INVOKE (heap alloc + per-element DalvikValue copy with COW string
    // refcount churn — the CowStr::release entries in the S156 RIP profile)
    // even when no argument is a CLASS_REF and the law would do nothing.
    // The vector is now built ONLY when a CLASS_REF argument exists; every
    // consumer keeps reading the same name through a reference.
    std::vector<DalvikValue> f282_storage;
    {
        const bool f282_diag = diag_env("MINIANDROID_F282_TRACE");
        bool f282_has_clsref = false;
        for (const auto& f282_scan : args) {
            if (f282_scan.type == DalvikType::CLASS_REF) {
                f282_has_clsref = true;
                break;
            }
        }
        if (f282_has_clsref) {
            f282_storage = args;
            for (auto& f282_a : f282_storage) {
                if (f282_a.type != DalvikType::CLASS_REF) continue;
                uint32_t f282_token = 0;
                auto f282_it = class_token_ids_.find(f282_a.class_desc);
                if (f282_it != class_token_ids_.end()) {
                    f282_token = f282_it->second;
                } else {
                    f282_token = heap_.allocate("Ljava/lang/Class;", pc_, 0);
                    heap_.set_object_field(f282_token, "__referent_desc",
                                           DalvikValue::make_string(f282_a.class_desc, 0));
                    class_token_ids_.emplace(f282_a.class_desc, f282_token);
                }
                if (f282_diag) {
                    static std::atomic<uint64_t> f282_n{0};
                    if (f282_n.fetch_add(1, std::memory_order_relaxed) < 24)
                        std::cerr << "[F282-TOKEN] arg CLASS_REF "
                                  << f282_a.class_desc
                                  << " → heap token obj#" << f282_token
                                  << " (callee " << class_name << "."
                                  << method_name << ")" << std::endl;
                }
                f282_a = DalvikValue::make_object(f282_token, "Ljava/lang/Class;");
            }
        }
    }
    const std::vector<DalvikValue>& f282_args =
        f282_storage.empty() ? args : f282_storage;

    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().invoke_internal, f107_t0};

    // ── TRAIN-67 (T67-ENTRY, DIAG-ONLY, env-gated MINIANDROID_T67_LABEL_TRACE):
    // the coroutine-machine lifecycle probe. Lss1;.q = the machine trampoline
    // (spill result + MIN_VALUE-mark the label + re-dispatch the suspend body);
    // Lbt1;.a = awaitPointerEventOrCancellation (the awaitEachGesture await).
    // Log every entry with THIS/args identity + the machine's live label so
    // the resume chain (who resumed whom, with what result) becomes evidence.
    {
        static const bool t67e_on = diag_env("MINIANDROID_T67_LABEL_TRACE");
        if (t67e_on && (class_name == "Lss1;" || class_name == "Lbt1;" ||
                        class_name == "Lxs1;" || class_name == "Lnr1;" ||
                        class_name == "Li6;" || class_name == "La00;")) {
            static thread_local uint64_t t67e_n = 0;
            if (t67e_n++ < 400) {
                std::string t67_dump;
                for (size_t t67i = 0;
                     t67i < f282_args.size() && t67i < 5; ++t67i) {
                    const DalvikValue& t67a = f282_args[t67i];
                    t67_dump += " a" + std::to_string(t67i) + "=";
                    if (t67a.type == DalvikType::OBJECT_REF)
                        t67_dump += t67a.class_desc + "#" +
                                    std::to_string(t67a.object_id);
                    else
                        t67_dump += dalvik_value_to_string(t67a);
                }
                uint32_t t67_this = (!f282_args.empty() &&
                                     f282_args[0].type == DalvikType::OBJECT_REF)
                                        ? f282_args[0].object_id : 0;
                std::string t67_lbl = "-";
                const char* t67_lf = (class_name == "Lss1;") ? "Lss1;.l"
                                     : (class_name == "Lxs1;") ? "Lxs1;.r"
                                     : nullptr;
                if (t67_lf && t67_this != 0 && heap_.has_object(t67_this)) {
                    auto t67_lv = heap_.get_object_field(t67_this, t67_lf);
                    if (t67_lv.has_value())
                        t67_lbl = dalvik_value_to_string(*t67_lv);
                    else
                        t67_lbl = "(unset)";
                }
                std::cerr << "[T67-ENTRY] " << class_name << "."
                          << method_name << " this=obj#" << t67_this
                          << " label=" << t67_lbl << t67_dump;
                if (!call_stack_.empty()) {
                    const StackFrame& t67cfr = call_stack_.top();
                    std::cerr << " caller=" << t67cfr.class_name << "."
                              << t67cfr.method_name;
                }
                std::cerr << std::endl;
            }
        }
    }
    // ── TRAIN-68 (T68-ENTRY, DIAG-ONLY, env-gated MINIANDROID_T68_NODE_TRACE):
    // the pointer-input NODE census probe. Lor1; = the SuspendingPointerInput
    // modifier node (M0/J = the dispatch arms, L0 = the lazy block LAUNCH,
    // <init> = node birth); Lj6; = the handler dispatcher; Lnc0;/Lk6; = dooz's
    // own scroll-board node family. Logs receiver identity per entry so the
    // hit-path census answers: HOW MANY nodes got the event, HOW MANY blocks
    // launched, and whether the clickable's detectTapAndPress node is in the
    // path at all (TRAIN-68 hypothesis (a) vs (b) decider).
    {
        static const bool t68_on = diag_env("MINIANDROID_T68_NODE_TRACE");
        // census only: node births + dispatch/launch arms + the handler
        // dispatcher — the draw/measure heat (Lnc0;.Q, Lk6;.i) is excluded.
        bool t68_want =
            (class_name == "Lor1;") ||
            (class_name == "Lj6;" && method_name == "invoke") ||
            (class_name == "Lxz1;" && method_name == "I") ||
            (class_name == "Lru;") ||
            // TRAIN-68 fold-arm census: the composed-factory inserts
            // (Ldr1;.c = the clickable-insert candidate, Ldr1;.d, Lkr1;.a =
            // the pointerInput insert, Ltl;.J) — which arms ran, which
            // silently dropped the clickable element.
            (class_name == "Ldr1;" &&
             (method_name == "c" || method_name == "d")) ||
            (class_name == "Lkr1;" && method_name == "a") ||
            (class_name == "Ltl;" && method_name == "J") ||
            // S152 TRAIN-70e measure-chain census: did the V re-fire arm
            // the bridge? DEX-truth: z is declared on Lkk; in the dooz v23
            // map (T24's Lt4;.z note predates the merge); Lzs0;.k = the
            // measure/layout perform; Las0;.w = the delegate measure arm.
            (class_name == "Lkk;" && method_name == "z") ||
            (class_name == "Lt4;" && method_name == "z") ||
            (class_name == "Lzs0;" && method_name == "k") ||
            (class_name == "Las0;" && method_name == "w") ||
            ((class_name == "Lnc0;" || class_name == "Lk6;") &&
             method_name == "<init>") ||
            // TRAIN-68 (T68-J): EVERY class's J(event,pass,bounds) dispatch
            // entry during touch — the full hit-path node census with
            // receiver classes (the clickable node should appear here).
            (method_name == "J" && touch_dispatch_active_ &&
             !f282_args.empty() && f282_args.size() >= 2 &&
             f282_args[0].type == DalvikType::OBJECT_REF &&
             f282_args[1].type == DalvikType::OBJECT_REF);
        if (t68_on && t68_want) {
            // per-class budgets (the old single 500-cap starved the tap
            // window: composition heat consumed it before the DOWN).
            static thread_local uint64_t t68n_1 = 0, t68n_2 = 0, t68n_3 = 0;
            uint64_t t68_cap = (class_name == "Lor1;") ? 200
                             : (class_name == "Lxz1;") ? 60
                             : (class_name == "Lru;")  ? 120
                             : 200;
            static thread_local uint64_t t68n_4 = 0, t68n_5 = 0;
            const bool t68_gen_j = !(class_name == "Lor1;") &&
                                   !(class_name == "Lxz1;") &&
                                   !(class_name == "Lru;") &&
                                   !(class_name == "Ldr1;") &&
                                   !(class_name == "Lkr1;") &&
                                   !(class_name == "Ltl;") &&
                                   method_name == "J";
            uint64_t& t68n = (class_name == "Lor1;") ? t68n_1
                           : (class_name == "Lxz1;") ? t68n_2
                           : (class_name == "Lru;")  ? t68n_3
                           : t68_gen_j               ? t68n_4
                           : t68n_5;
            if (t68n++ < t68_cap) {
                uint32_t t68_this = (!f282_args.empty() &&
                                     f282_args[0].type == DalvikType::OBJECT_REF)
                                        ? f282_args[0].object_id : 0;
                std::cerr << "[T68-ENTRY] " << class_name << "."
                          << method_name << " this=obj#" << t68_this;
                // node births + launches: dump the ctor/handler args so each
                // node's handler class becomes evidence.
                if (method_name == "<init>" || (class_name == "Lxz1;" && method_name == "I")) {
                    for (size_t t68i = 1;
                         t68i < f282_args.size() && t68i < 4; ++t68i) {
                        const DalvikValue& t68a = f282_args[t68i];
                        std::cerr << " a" << t68i << "=";
                        if (t68a.type == DalvikType::OBJECT_REF)
                            std::cerr << t68a.class_desc << "#"
                                      << t68a.object_id;
                        else
                            std::cerr << dalvik_value_to_string(t68a);
                    }
                }
                if (!call_stack_.empty()) {
                    const StackFrame& t68cfr = call_stack_.top();
                    std::cerr << " caller=" << t68cfr.class_name << "."
                              << t68cfr.method_name;
                }
                std::cerr << std::endl;
            }
        }
    }
    // ────────────────────────────────────────────────────────────────────
    // CONT-47 D7c node capture (unconditional, O(1) per insert): record
    // the insertAt receiver + inserted-node ids (bounded 512) so the
    // draw-window close can walk their placement state (D7c above).
    if (class_name == "Lel0;" && method_name == "B") {
        for (size_t d7ci = 0;
             d7ci < f282_args.size() && d7ci < 3; ++d7ci) {
            const DalvikValue& d7ca = f282_args[d7ci];
            if (d7ca.type == DalvikType::OBJECT_REF &&
                d7ca.object_id != 0 &&
                g_d7_node_ids.size() < D7_NODE_CAP)
                g_d7_node_ids.insert(d7ca.object_id);
        }
        // ── S155 (T21/#389 law, env-gated MINIANDROID_S155_APPLY=1):
        // "a node insert must schedule a modifier-chain rebuild + measure"
        // — the T21 census showed late-inserted compose nodes enter the
        // tree but their modifier pass (r1) never runs (P=NULL, D=0, zero
        // victory-region ops). DEX truth (androguard, dooz v23):
        // Lel0;.B(I,Lel0;)V = insertAt (args[2] = the inserted node); the
        // missed chain is Lel0;.N(Lpz0;)V (instance, public final, coded)
        // — the composition-scope-driven node update. Fire it on the
        // freshly-inserted node with the live Lpz0; scope (freshest heap
        // instance, refreshed every 16 fires). Bounded 64 fires/run;
        // default OFF — byte-inert, anchor-wall law.
        static const bool s155_apply_on =
            diag_env("MINIANDROID_S155_APPLY");
        static uint32_t s155_fires = 0;
        static uint32_t s155_scope = 0;
        if (s155_apply_on && s155_fires < 64 && f282_args.size() >= 3 &&
            f282_args[2].type == DalvikType::OBJECT_REF &&
            f282_args[2].object_id != 0) {
            const uint32_t s155_node = f282_args[2].object_id;
            if (s155_fires % 16 == 0 || !heap_.has_object(s155_scope)) {
                s155_scope = 0;
                for (uint32_t s155_oid : heap_.get_all_ids()) {
                    const auto* s155_obj = heap_.get(s155_oid);
                    if (s155_obj &&
                        s155_obj->class_descriptor == "Lpz0;")
                        s155_scope = s155_oid;  // keep the freshest
                }
            }
            if (s155_scope != 0) {
                ++s155_fires;
                DalvikValue s155_ret = DalvikValue::make_void();
                DalvikExecutionResult s155_res;
                const bool s155_ok = try_recursive_invoke(
                    "Lel0;", "N",
                    {DalvikValue::make_object(s155_node, "Lel0;"),
                     DalvikValue::make_object(s155_scope, "Lpz0;")},
                    s155_ret, s155_res, "(Lpz0;)V");
                std::cerr << "[S155-APPLY] node#" << s155_node
                          << " scope=o" << s155_scope
                          << " fire#" << s155_fires
                          << " N dispatched=" << (s155_ok ? "YES" : "NO")
                          << (s155_res.uncaught_in_flight_count ? " EXC"
                                                                : "")
                          << std::endl;
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────
    // CONT-47 D4 (F-NEW-567 evidence, DIAG-ONLY, env-gated): insertAt
    // context witness. D3 record: the 44 wave-2 Lel0;.B (insertAt) q-writes
    // form the chain 6464<-6440<-6416<-6392<-6367<-2113(ROOT) — the TOP of
    // the inserted chain attaches DIRECTLY to the root LayoutNode; the
    // divergence is at composition RECORD time (pass#2 composer node-stack
    // never descended into the destination content level). Witness: every
    // Lel0;.B entry dumps receiver id + its q (current parent) + raw args
    // + top-3 caller frames, so the D5 fix can name WHERE the applier's
    // current stayed at root. Read-only, bounded 96, inert by default.
    // ────────────────────────────────────────────────────────────────────
    {
        static thread_local const bool d4_on =
            diag_env("MINIANDROID_INSERT_TRACE");
        static thread_local uint64_t d4_n = 0;
        if (d4_on && class_name == "Lel0;" && method_name == "B" &&
            d4_n < 96) {
            ++d4_n;
            uint32_t d4_recv = (!f282_args.empty() &&
                                f282_args[0].type == DalvikType::OBJECT_REF)
                                   ? f282_args[0].object_id
                                   : 0;
            std::string d4_q = "ABSENT";
            if (d4_recv != 0) {
                auto d4_qv = heap_.get_object_field(d4_recv, "q");
                if (d4_qv.has_value() &&
                    d4_qv->type == DalvikType::OBJECT_REF)
                    d4_q = "#" + std::to_string(d4_qv->object_id);
            }
            std::cerr << "[D4-INSERT] B#" << d4_n << " recv=" << d4_recv
                      << " parent_q=" << d4_q;
            for (size_t d4_i = 1;
                 d4_i < f282_args.size() && d4_i < 4; ++d4_i) {
                const DalvikValue& d4_a = f282_args[d4_i];
                if (d4_a.type == DalvikType::INT32)
                    std::cerr << " a" << d4_i << "=" << d4_a.int_val;
                else if (d4_a.type == DalvikType::OBJECT_REF)
                    std::cerr << " a" << d4_i << "=o" << d4_a.object_id;
                else
                    std::cerr << " a" << d4_i << ":t" << (int)d4_a.type;
            }
            auto d4_frames = call_stack_.snapshot_top_first();
            for (size_t d4_fi = 0;
                 d4_fi < d4_frames.size() && d4_fi < 3; ++d4_fi)
                std::cerr << " <" << d4_frames[d4_fi].first << "."
                          << d4_frames[d4_fi].second << ">";
            std::cerr << std::endl;
        }
    }

    // F-NEW-344 probe (CONT-61): the AndroidParagraph (Lj7;) ctor args —
    // the zero-width root decode. The obtain width=0 chain ends here:
    // this ctor receives (delegate, I width, I height?, J constraints?);
    // printing the raw args answers WHERE the zero entered (the caller's
    // constraints decode).
    {
        static const bool f344_on =
            std::getenv("MINIANDROID_F344_TRACE") != nullptr;
        if (f344_on && class_name == "Lj7;" && method_name == "<init>") {
            std::cerr << "[F344-PCTOR] Lj7.<init> argc=" << f282_args.size();
            for (size_t f344_i = 0; f344_i < f282_args.size() && f344_i < 6;
                 ++f344_i) {
                const DalvikValue& f344_a = f282_args[f344_i];
                std::cerr << " a" << f344_i << ":t" << (int)f344_a.type;
                if (f344_a.type == DalvikType::INT32)
                    std::cerr << "=" << f344_a.int_val;
                else if (f344_a.type == DalvikType::INT64)
                    std::cerr << "=" << f344_a.long_val;
            }
            std::cerr << std::endl;
        }
    }
    uint64_t f107_su0 = 0; phase_clock().enter(phase_clock().em_setup, f107_su0);  // S61 setup
    current_result_ = &result;
    bytecode_ = bytecode;
    halted_ = false;
    halted_on_return_ = false;
    soft_stopped_no_return_ = false;  // CONT-132: per-frame exit discriminator
    instruction_sequence_ = 0;
    // G12 FIX-G12-003 (AOSP parent-delegation law, FIND-G09-ACF-001): the
    // boot classpath owns android.*/java.* classes — an app-bundled copy
    // (androidx shading, R8 stubs) must never shadow framework semantics.
    // The one choke point every <clinit> dispatch passes through is here:
    // a framework-namespace class's static initializer is NOT executed
    // from app DEX bytecode (muellerma stopwatch: bundled
    // android.app.AppComponentFactory.<clinit> threw NoClassDefFoundError
    // at boot and killed the app before the Activity inflated).
    if (method_name == "<clinit>") {
        const std::string norm = framework::normalize_class_desc(class_name);
        // M3 FINDING-013 (provenance law): mirror of the
        // ensure_class_initialized fix. The old blanket library-namespace
        // skip made ensure_class_initialized's real <clinit> invocation a
        // silent no-op ("result=OK" with zero sput writes — the i$b enum
        // stayed null and dooz's Lifecycle collapsed). LAW: only classes
        // ABSENT from the app DexReport are runtime stubs whose statics
        // are shadow-owned; app-bundled androidx/kotlin/j$/com.google
        // bytecode runs its own <clinit>. Landroid/* is an unconditional
        // skip (G12 parent-delegation — app-bundled platform copies must
        // never execute).
        bool clinit_in_app_dex =
            class_info_index_.find(class_name) != class_info_index_.end() ||
            class_info_index_.find(norm) != class_info_index_.end();
        // S123 (R-NEW-421c): the support/arch/databinding trees are
        // APP-BUNDLED LIBRARY bytecode (never platform) — same exemption as
        // ensure_class_initialized R-NEW-421. ContainerHelpers.<clinit>
        // evidence: the [platform-ns] skip here silently no-op'd the clinit
        // AFTER the ensure_class_initialized law fixed its gate, keeping
        // EMPTY_INTS/EMPTY_OBJECTS null and killing every SimpleArrayMap.
        bool is_app_library_ns =
            norm.rfind("Landroid/support/", 0) == 0 ||
            norm.rfind("Landroid/arch/", 0) == 0 ||
            norm.rfind("Landroid/databinding/", 0) == 0;
        bool is_platform_ns =
            (norm.rfind("Landroid/", 0) == 0) && !is_app_library_ns;
        bool is_library_ns =
            norm.rfind("Landroidx/", 0) == 0 ||
            norm.rfind("Ljava/", 0) == 0 ||
            norm.rfind("Lkotlin/", 0) == 0 ||
            norm.rfind("Lkotlinx/", 0) == 0 ||
            norm.rfind("Lcom/google/", 0) == 0 ||
            norm.rfind("Lj$/", 0) == 0;
        if (is_platform_ns || (is_library_ns && !clinit_in_app_dex)) {
            initialized_classes_.insert(norm);
            initialized_classes_.insert(class_name);
            std::cerr << "[G12-ACF] framework-namespace <clinit> skipped "
                      << "(parent-delegation): " << class_name
                      << (is_platform_ns ? " [platform-ns]"
                                         : " [stub — not in app dex]")
                      << std::endl;
            halted_ = false;
            return true;  // initialized; bytecode not executed
        }
    }
    halted_on_return_ = false;
    instruction_sequence_ = 0;
    // MASTER CAMPAIGN FIX (lifecycle-provenance law): record lifecycle
    // execution AT ENTRY — never inferred from the capacity-capped
    // api_call_traces ring (volume-dependent eviction flipped the
    // lifecycle-source validation between identical runs).
    if (method_name == "onCreate" || method_name == "onStart" ||
        method_name == "onResume") {
        lifecycle_from_dex_ = true;
    }
    // EXP-042 Phase 1: Per-frame loop detection counter. Reset on each new
    // method invocation so recursive calls do not pollute each other.
    // S157-B (CONT-42 throughput law): the three .assign() calls
    // REALLOCATED (destroy+alloc+memset) whenever consecutive frames have
    // different bytecode sizes — 3 heap alloc/free pairs + up to 16B/pc
    // memset PER METHOD INVOCATION. Byte-identical split: on resize, the
    // same assign; on same-size frames, a pure fill (no realloc). Same
    // bytes written, same semantics, zero behavior change.
    if (pc_visit_count_.size() != bytecode_.size()) {
        pc_visit_count_.assign(bytecode_.size(), 0u);   // CONT-96 W3-A: flat state
        pc_branch_sig_seen_.assign(bytecode_.size(), 0u);
        // F-NEW-084 closeout: reset the forward-progress signatures per frame.
        pc_branch_sig_.assign(bytecode_.size(), 0ull);
    } else {
        std::fill(pc_visit_count_.begin(), pc_visit_count_.end(), 0u);
        std::fill(pc_branch_sig_seen_.begin(), pc_branch_sig_seen_.end(), 0u);
        std::fill(pc_branch_sig_.begin(), pc_branch_sig_.end(), 0ull);
    }
    frame_progress_epoch_ = 0;
    pc_epoch_checkpoint_ = 0;
    // EXP-042 Phase 2: Set current_class_/current_method_ so loop-detector
    // halt messages and traces can identify the method that halted.
    current_class_ = class_name;
    current_method_ = method_name;
    // M5 scheduler-frontier diagnostic: dump incoming args of the Segment
    // CAS-retry method (LY1/j;.j) to expose caller-side register tags.
    // S22 frontier trace (env-gated MINIANDROID_S22_TRACE=1, capped 200,
    // read-only): every engine entry into the Recomposer runner lambda chain
    // (LF/F0 loop, LF/E0 recompositionRunner, LF/E0$a scope block) and the
    // MonotonicFrameClock withFrameNanos sites (LF/b0.u interface, K.u impl,
    // LF/d0.a accessor). Answers: did the runner body ever start, and did it
    // ever request a frame?
    if (diag_env("MINIANDROID_S22_TRACE")) {
        static thread_local uint64_t s22_n = 0;
        if (s22_n < 200) {
            bool s22_hit = false;
            if ((class_name == "LF/F0;" || class_name == "LF/E0;" ||
                 class_name == "LF/E0$a;" || class_name == "LF/b0;" ||
                 class_name == "Landroidx/compose/ui/platform/K;") &&
                (method_name == "t" || method_name == "j" || method_name == "u" ||
                 method_name == "a" || method_name == "o")) {
                s22_hit = true;
            }
            // F-077 probe: TrieNode node-slot accessor K/t.s and the
            // PersistentHashMap builder putAll (K/f) / merge (K/t.m) chain.
            if (class_name == "LK/t;" &&
                (method_name == "s" || method_name == "m" ||
                 method_name == "<init>")) {
                static thread_local uint64_t trienode_n = 0;
                if (trienode_n < 128) {
                    ++trienode_n;
                    std::cerr << "[TRIENODE] " << method_name << " recv="
                              << (args.empty() ? 0 : args[0].object_id) << " args(";
                    for (size_t ai = 1; ai < args.size() && ai < 5; ++ai) {
                        const auto& a = args[ai];
                        if (a.type == DalvikType::OBJECT_REF)
                            std::cerr << " obj=" << a.object_id;
                        else if (a.type == DalvikType::INT32)
                            std::cerr << " i=" << a.int_val;
                        else
                            std::cerr << " t" << (int)a.type;
                    }
                    std::cerr << ")";
                    // F-077 state dump: bitmaps (a,b), buffer length, null
                    // slot census — proves (or refutes) bitmap/buffer
                    // invariant violation on the receiver node. For <init>
                    // the node object already exists (heap-allocated before
                    // the ctor runs), so the same read works after stores.
                    uint32_t probe_id = 0;
                    if (method_name == "<init>") {
                        // the receiver is the NEW-INSTANCE object id = the
                        // engine's new-instance tracking; args[0] is p0 in
                        // non-static framing. Use current heap object of the
                        // receiver register: args[0].
                        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                            probe_id = args[0].object_id;
                    } else if (!args.empty() &&
                               args[0].type == DalvikType::OBJECT_REF) {
                        probe_id = args[0].object_id;
                    }
                    if (probe_id && heap_.has_object(probe_id)) {
                        auto rd = [&](const char* k) -> std::optional<DalvikValue> {
                            auto v = heap_.get_object_field(probe_id, k);
                            if (!v.has_value())
                                v = heap_.get_object_field(probe_id, std::string("LK/t;.") + k);
                            return v;
                        };
                        auto a_v = rd("a");
                        auto b_v = rd("b");
                        auto d_v = rd("d");
                        auto len_v = d_v.has_value() && d_v->type == DalvikType::OBJECT_REF
                                         ? heap_.get_object_field(d_v->object_id, "__array_length__")
                                         : std::optional<DalvikValue>{};
                        int nulls = -1;
                        if (len_v.has_value()) {
                            int L = len_v->int_val;
                            nulls = 0;
                            for (int k = 0; k < L; ++k) {
                                auto e = heap_.get_object_field(
                                    d_v->object_id, "array[" + std::to_string(k) + "]");
                                if (!e.has_value() || e->is_null) ++nulls;
                            }
                        }
                        std::cerr << " state{a=" << (a_v.has_value() ? a_v->int_val : -1)
                                  << " b=" << (b_v.has_value() ? b_v->int_val : -1)
                                  << " len=" << (len_v.has_value() ? len_v->int_val : -1)
                                  << " null_slots=" << nulls << "}";
                    }
                    std::cerr << std::endl;
                }
            }
            if (s22_hit) {
                ++s22_n;
                std::cerr << "[S22] entry#" << s22_n << " " << class_name << "."
                          << method_name << " args(" << args.size() << "):";
                for (size_t ai = 0; ai < args.size() && ai < 3; ++ai) {
                    const auto& a = args[ai];
                    if (a.type == DalvikType::OBJECT_REF)
                        std::cerr << " obj=" << a.object_id << "(" << a.class_desc << ")";
                    else if (a.is_null)
                        std::cerr << " NULL";
                    else
                        std::cerr << " v=" << a.int_val;
                }
                std::cerr << std::endl;
            }
        }
    }
    // Env-gated (MINIANDROID_J_ENTRY=1), capped; forensics only.
    if (diag_env("MINIANDROID_J_ENTRY") && class_name == "LY1/j;" &&
        method_name == "j") {
        static thread_local uint64_t j_entry_n = 0;
        if (j_entry_n < 8) {
            ++j_entry_n;
            std::cerr << "[J-ENTRY] call#" << j_entry_n << " args(" << args.size()
                      << "):";
            for (const auto& a : args) {
                std::cerr << " {t=" << (int)a.type;
                if (a.type == DalvikType::INT32) std::cerr << " i=" << a.int_val;
                else if (a.type == DalvikType::OBJECT_REF) std::cerr << " obj=" << a.object_id << " cls=" << a.class_desc;
                else if (a.is_null) std::cerr << " NULL";
                std::cerr << "}";
            }
            std::cerr << std::endl;
        }
    }
    // WAVE C (F-NEW-181) TABLESIZE FEED TRACE — env-gated, bounded.
    // Names the full feed chain into the map build: chooseTableSize's input,
    // createHashTable's (alternating, maxSize, tableSize, mask), and the
    // <init> store (table object identity + length + element provenance).
    // Evidence law: one instrumented run must NAME the divergence instead
    // of asserting it.
    if (diag_env("MINIANDROID_WAVEC_TRACE")) {
        static thread_local uint64_t wavec_n = 0;
        bool wavec_hit = false;
        const char* wavec_tag = "";
        if (class_name.find("RegularImmutableMap") != std::string::npos &&
            method_name == "createHashTable") {
            wavec_hit = true;
            wavec_tag = "CHT";
        } else if (class_name.find("RegularImmutableMap") != std::string::npos &&
                   method_name == "<init>") {
            wavec_hit = true;
            wavec_tag = "INIT";
        } else if (class_name.find("ImmutableSet") != std::string::npos &&
                   method_name == "chooseTableSize") {
            wavec_hit = true;
            wavec_tag = "CTS";
        }
        if (wavec_hit && wavec_n < 64) {
            ++wavec_n;
            std::cerr << "[WAVEC-" << wavec_tag << "] #" << wavec_n << " "
                      << class_name << "." << method_name;
            for (size_t ai = 0; ai < args.size() && ai < 5; ++ai) {
                const auto& a = args[ai];
                if (a.type == DalvikType::OBJECT_REF) {
                    std::cerr << " p" << ai << "=o" << a.object_id;
                    if (heap_.has_object(a.object_id)) {
                        const auto* ho = heap_.get(a.object_id);
                        if (ho) {
                            std::cerr << "<" << ho->class_descriptor << ">";
                            auto lf = heap_.get_object_field(
                                a.object_id, "__array_length__");
                            if (lf.has_value() && lf->type == DalvikType::INT32)
                                std::cerr << " len=" << lf->int_val;
                            auto et = heap_.get_object_field(
                                a.object_id, "__element_type__");
                            if (et.has_value() &&
                                et->type == DalvikType::STRING_REF)
                                std::cerr << " elem=" << et->string_val;
                        }
                    }
                } else if (a.type == DalvikType::INT32)
                    std::cerr << " p" << ai << "=" << a.int_val;
                else if (a.is_null)
                    std::cerr << " p" << ai << "=NULL";
                else
                    std::cerr << " p" << ai << "=t" << (int)a.type;
            }
            std::cerr << std::endl;
        }
    }
    // CHAR-PROBE campaign: keep the descriptor for signature-aware return
    // typing in execute_return (see current_method_descriptor_ declaration).
    current_method_descriptor_ = descriptor;
    // EXP-052: Save tries[] state for the THROW opcode handler.
    current_tries_size_ = tries_size;
    current_tries_data_ = tries_data;
    current_tries_data_size_ = tries_data_size;
    // S33 (R-NEW-332): depth-band trace — log method entries whose
    // recursion depth falls in the configured band (env-gated
    // MINIANDROID_DEPTHBAND=min:max, bounded 500). Exposes the app
    // composable's execution until its terminal point.
    {
        static thread_local const char* band_env =
            std::getenv("MINIANDROID_DEPTHBAND");
        if (band_env) {
            static thread_local int band_min = -1;
            static thread_local int band_max = -1;
            if (band_min < 0) {
                int mn = 0, mx = 0;
                if (sscanf(band_env, "%d:%d", &mn, &mx) == 2) {
                    band_min = mn;
                    band_max = mx;
                }
            }
            if (band_min >= 0 && recursion_depth_ >= band_min &&
                recursion_depth_ <= band_max &&
                class_name != "LM1/i;") {
                static thread_local uint64_t band_logged = 0;
                if (band_logged < 9000) {
                    ++band_logged;
                    std::cerr << "[DEPTHBAND d=" << recursion_depth_ << "] "
                              << class_name << "." << method_name << " "
                              << descriptor << std::endl;
                }
            }
        }
    }
    // S33 (R-NEW-332): composition-window trace — from the
    // AbstractComposeView.ensureCompositionCreated entry, log the next 800
    // method entries (env-gated, bounded) so the app content-lambda invoke
    // is directly visible in the composition pass.
    {
        static thread_local const bool compwin_on =
            diag_env("MINIANDROID_COMPWIN_TRACE");
        if (compwin_on) {
            static thread_local bool compwin_active = false;
            static thread_local uint64_t compwin_logged = 0;
            if (!compwin_active &&
                class_name == "Landroidx/compose/ui/platform/AbstractComposeView;" &&
                method_name == "ensureCompositionCreated") {
                compwin_active = true;
                std::cerr << "[COMPWIN-OPEN] " << class_name << "."
                          << method_name << " depth=" << recursion_depth_
                          << std::endl;
            }
            if (compwin_active && compwin_logged < 800) {
                ++compwin_logged;
                std::cerr << "[COMPWIN] " << class_name << "." << method_name
                          << " " << descriptor << " d=" << recursion_depth_
                          << std::endl;
                if (compwin_logged == 800)
                    std::cerr << "[COMPWIN-CLOSE] cap reached" << std::endl;
            }
        }
    }
    // S34 (R-NEW-333): compose-view pairing trace — same instance law.
    {
        static thread_local const bool cvpari_on =
            diag_env("MINIANDROID_CVPARI");
        if (cvpari_on) {
            const char* cv1_tag = nullptr;
            if (class_name == "Landroidx/compose/ui/platform/ComposeView;" &&
                method_name == "<init>") cv1_tag = "CV1-INIT";
            else if (class_name == "Landroidx/compose/ui/platform/ComposeView;" &&
                     method_name == "setContent") cv1_tag = "CV1-SETCONTENT";
            else if (class_name == "Landroidx/compose/ui/platform/AbstractComposeView;" &&
                     method_name == "c" && descriptor == "()V") cv1_tag = "CV1-CREATE";
            else if (class_name == "Landroidx/compose/ui/platform/ComposeView;" &&
                     method_name == "a" &&
                     descriptor == "(I LF/i;)V") cv1_tag = "CV1-CONTENT";
            else if (class_name == "Landroidx/compose/ui/platform/AbstractComposeView;" &&
                     method_name == "onAttachedToWindow") cv1_tag = "CV1-ATTACH";
            else if (class_name == "Landroidx/compose/ui/platform/AndroidComposeView;" &&
                     method_name == "<init>") cv1_tag = "CV1-ACV";
            else if (class_name == "Landroidx/compose/ui/platform/e1;" &&
                     method_name == "a") cv1_tag = "CV1-E1A";
            // [S34-PERTAG] per-tag bounded counters (shared counter was
            // suppressing late events — Content() runs AFTER startup churn).
            if (cv1_tag) {
                static thread_local uint64_t cv1_init_n = 0, cv1_setc_n = 0,
                    cv1_create_n = 0, cv1_content_n = 0, cv1_attach_n = 0,
                    cv1_acv_n = 0, cv1_e1a_n = 0;
                uint64_t* cnt = nullptr;
                if (cv1_tag[4] == 'I') cnt = &cv1_init_n;
                else if (cv1_tag[4] == 'S') cnt = &cv1_setc_n;
                else if (cv1_tag[4] == 'C' && cv1_tag[5] == 'R') cnt = &cv1_create_n;
                else if (cv1_tag[4] == 'C') cnt = &cv1_content_n;
                else if (cv1_tag[4] == 'A' && cv1_tag[5] == 'T') cnt = &cv1_attach_n;
                else if (cv1_tag[4] == 'A') cnt = &cv1_acv_n;
                else cnt = &cv1_e1a_n;
                if (*cnt < 80) {
                    ++*cnt;
                    std::cerr << "[" << cv1_tag << "] recv="
                              << (args.empty() ? 0 : args[0].object_id)
                              << " depth=" << recursion_depth_;
                    if (args.size() > 1)
                        std::cerr << " arg1=" << args[1].object_id
                                  << (args[1].is_null ? " NULL"
                                      : (args[1].type == DalvikType::OBJECT_REF
                                             ? (" " + args[1].class_desc) : ""));
                    if (!call_stack_.empty()) {
                        const StackFrame& cfr = call_stack_.top();
                        std::cerr << " caller=" << cfr.class_name << "."
                                  << cfr.method_name;
                    }
                    std::cerr << std::endl;
                }
            }
        }
    }
    // S34 (R-NEW-333): content-state write identity — receiver state id +
    // written value id (bounded, env-gated). Upstream: the app lambda
    // (ComposableLambdaImpl) and the Content() read must hit ONE state.
    {
        static thread_local const bool cvw_on =
            diag_env("MINIANDROID_CVPARI");
        if (cvw_on && class_name == "LF/V0;" &&
            (method_name == "setValue" || method_name == "getValue")) {
            static thread_local uint64_t cvw_n = 0;
            if (cvw_n < 90) {
                ++cvw_n;
                std::cerr << "[CV1-STATE-" << (method_name == "setValue" ? "W" : "R")
                          << "] state=" << (args.empty() ? 0 : args[0].object_id);
                if (method_name == "setValue" && args.size() > 1)
                    std::cerr << " val=" << args[1].object_id
                              << (args[1].is_null ? " NULL"
                                  : (args[1].type == DalvikType::OBJECT_REF
                                         ? (" " + args[1].class_desc) : ""));
                // [S34-CALLER] direct caller frame (callee frame not yet pushed)
                if (!call_stack_.empty()) {
                    const StackFrame& cfr = call_stack_.top();
                    std::cerr << " caller=" << cfr.class_name << "."
                              << cfr.method_name;
                }
                std::cerr << std::endl;
            }
        }
    }
    // S33 (R-NEW-332): LayoutNode census — count LayoutNode constructions
    // and draw dispatches; bounded, env-gated. Distinguishes "composition
    // created few nodes" from "nodes created but not linked into the tree".
    {
        static thread_local const bool census_on =
            diag_env("MINIANDROID_NODE_CENSUS");
        if (census_on) {
            static thread_local uint64_t ctor_count = 0;
            static thread_local uint64_t draw_count = 0;
            static thread_local uint64_t attach_count = 0;
            if (class_name == "Landroidx/compose/ui/node/e;" &&
                method_name == "<init>") {
                ++ctor_count;
                if (ctor_count <= 12) {
                    std::cerr << "[NODE-CENSUS] LayoutNode ctor #" << ctor_count
                              << " " << descriptor << " depth=" << recursion_depth_;
                    // [S34-CTORCALLER] direct caller of the LayoutNode ctor
                    if (!call_stack_.empty()) {
                        const StackFrame& cfr = call_stack_.top();
                        std::cerr << " caller=" << cfr.class_name << "."
                                  << cfr.method_name;
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" && method_name == "m" &&
                       descriptor == "(LL1/a;)V") {
                // [S34-NODEEMIT] ComposerImpl.m(factory) — node emission count
                static thread_local uint64_t emit_call_count = 0;
                ++emit_call_count;
                if (emit_call_count <= 24) {
                    std::cerr << "[S34-NODEEMIT] composer.m #" << emit_call_count
                              << " depth=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi) {
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "LN/a;" && method_name == "a" &&
                       descriptor == "(Ljava/lang/Object; LF/i; I)Ljava/lang/Object;") {
                static thread_local uint64_t naa_n = 0;
                ++naa_n;
                if (naa_n <= 10) {
                    std::cerr << "[S34-CHAINLINK] N/a.a #" << naa_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Lk0/s;" && method_name == "j") {
                static thread_local uint64_t ksj_n = 0;
                ++ksj_n;
                if (ksj_n <= 10) {
                    std::cerr << "[S34-CHAINLINK] k0/s.j #" << ksj_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LN/a;" && method_name == "j" &&
                       descriptor.size() > 20) {
                // [S34-CONTENT] content-lambda trampoline entries
                static thread_local uint64_t naj_n = 0;
                ++naj_n;
                if (naj_n <= 14) {
                    std::cerr << "[S34-CONTENT] LN/a.j #" << naj_n
                              << " d=" << recursion_depth_ << " " << descriptor;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LR/f;" && method_name == "a") {
                // [S34-CONTENT] R/f (content body) method entries
                static thread_local uint64_t rf_n = 0;
                ++rf_n;
                if (rf_n <= 14) {
                    std::cerr << "[S34-CONTENT] LR/f." << method_name << " #"
                              << rf_n << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LD/b;" && method_name == "f") {
                // [S34-DIVERGE] LD/b.f trampoline — ran? from where?
                static thread_local uint64_t dbf_n = 0;
                ++dbf_n;
                if (dbf_n <= 12) {
                    std::cerr << "[S34-DIVERGE] LD/b.f #" << dbf_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LB0/b;" && method_name == "c") {
                // [S34-DIVERGE] rememberNavController — caller chain
                static thread_local uint64_t b0c_n = 0;
                ++b0c_n;
                if (b0c_n <= 8) {
                    std::cerr << "[S34-DIVERGE] LB0/b.c #" << b0c_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 5; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Lh1/e;" && method_name == "<init>") {
                // [S34-DIVERGE] NavController ctor — caller chain
                static thread_local uint64_t nve_n = 0;
                ++nve_n;
                if (nve_n <= 8) {
                    std::cerr << "[S34-DIVERGE] NavController.<init> #" << nve_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 5; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Lb2/h;" && method_name == "a") {
                // [S34-CANCEL] cancellation-handler dispatch
                static thread_local uint64_t cx_n = 0;
                ++cx_n;
                if (cx_n <= 12) {
                    std::cerr << "[S34-CANCEL] b2/h.a #" << cx_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LW1/u0;" && method_name == "c") {
                // [S34-CANCEL] JobSupport.cancel(CancellationException)
                static thread_local uint64_t jc_n = 0;
                ++jc_n;
                if (jc_n <= 12) {
                    std::cerr << "[S34-CANCEL] JobSupport.c #" << jc_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LB0/b;" && method_name == "P") {
                // [S34-MODE] resume-mode table lookup returns
                static thread_local uint64_t mod_n = 0;
                ++mod_n;
                if (mod_n <= 20) {
                    std::cerr << "[S34-MODE] B0/b.P #" << mod_n
                              << " d=" << recursion_depth_
                              << " mode-arg=" << (args.size() > 1 ? args[1].int_val : -99)
                              << std::endl;
                }
            } else if (class_name == "LW1/N;" && method_name == "run") {
                // [S34-MODE] ResumeTask.run entries with mode field
                static thread_local uint64_t nrun_n = 0;
                ++nrun_n;
                if (nrun_n <= 20) {
                    uint32_t rid = args.empty() ? 0 : args[0].object_id;
                    auto mk = heap_.get_object_field(rid, "k");
                    std::cerr << "[S34-MODE] W1/N.run #" << nrun_n
                              << " d=" << recursion_depth_
                              << " mode=" << (mk ? mk->int_val : -1);
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/platform/WindowRecomposer_androidKt$createLifecycleAwareWindowRecomposer$2$b;" &&
                       (method_name == "t" || method_name == "q")) {
                // [S34-RUNNER] runner body segments (unbounded count, log 30)
                static thread_local uint64_t run_n = 0;
                ++run_n;
                if (run_n <= 30) {
                    std::cerr << "[S34-RUNNER] $2$b." << method_name << " #" << run_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LW1/g;" && method_name == "run") {
                // [S34-RUNNER] W1/g runnable (withContext machinery)
                static thread_local uint64_t wgn_n = 0;
                ++wgn_n;
                if (wgn_n <= 20) {
                    std::cerr << "[S34-RUNNER] W1/g.run #" << wgn_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/platform/K;" &&
                       method_name == "u") {
                // [S34-RUNNER] withFrameNanos impl
                static thread_local uint64_t ku_n = 0;
                ++ku_n;
                if (ku_n <= 10) {
                    std::cerr << "[S34-RUNNER] K.u (withFrameNanos) #" << ku_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/platform/WindowRecomposer_androidKt$createLifecycleAwareWindowRecomposer$2;" &&
                       method_name == "m") {
                // [S34-LIFEV] recomposer observer onStateChanged(owner, event)
                static thread_local uint64_t lev_n = 0;
                ++lev_n;
                if (lev_n <= 14) {
                    std::cerr << "[S34-LIFEV] onStateChanged #" << lev_n
                              << " d=" << recursion_depth_;
                    for (size_t ai = 0; ai < args.size() && ai < 3; ++ai)
                        std::cerr << " a" << ai << "=" << args[ai].object_id
                                  << (args[ai].is_null ? "(NULL)"
                                      : (args[ai].type == DalvikType::OBJECT_REF
                                             ? (" " + args[ai].class_desc) : ""));
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/platform/WindowRecomposer_androidKt$createLifecycleAwareWindowRecomposer$2$b;" &&
                       (method_name == "t" || method_name == "k")) {
                // [S34-LIFEV] recomposer lifecycle observer entries + event arg
                static thread_local uint64_t lev_n = 0;
                ++lev_n;
                if (lev_n <= 14) {
                    std::cerr << "[S34-LIFEV] observer." << method_name << " #"
                              << lev_n << " d=" << recursion_depth_;
                    for (size_t ai = 0; ai < args.size() && ai < 3; ++ai)
                        std::cerr << " a" << ai << "=" << args[ai].object_id
                                  << (args[ai].is_null ? "(NULL)"
                                      : (args[ai].type == DalvikType::OBJECT_REF
                                             ? (" " + args[ai].class_desc) : ""));
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/platform/J$c;" &&
                       (method_name == "run" || method_name == "doFrame")) {
                // [S34-JID] dispatcher-callback identity: outer J id + J.o size
                static thread_local uint64_t jid_n = 0;
                ++jid_n;
                if (jid_n <= 10) {
                    uint32_t cbid = args.empty() ? 0 : args[0].object_id;
                    std::cerr << "[S34-JID] J$c." << method_name << " #" << jid_n
                              << " cb=" << cbid;
                    auto v = heap_.get_object_field(cbid, "i");
                    if (v && v->type == DalvikType::OBJECT_REF) {
                        std::cerr << " outerJ=" << v->object_id;
                        auto o = heap_.get_object_field(v->object_id, "o");
                        if (o && o->type == DalvikType::OBJECT_REF)
                            std::cerr << " J.o-list=" << o->object_id;
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/platform/J;" &&
                       (method_name == "L" || method_name == "O")) {
                // [S34-UIDISP] AndroidUiDispatcher dispatch (L) / drain (O)
                static thread_local uint64_t jd_n = 0;
                ++jd_n;
                if (jd_n <= 20) {
                    std::cerr << "[S34-UIDISP] J." << method_name << " #" << jd_n
                              << " d=" << recursion_depth_ << " recv="
                              << (args.empty() ? 0 : args[0].object_id);
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/Y;" &&
                       (method_name == "j" || method_name == "d" || method_name == "l")) {
                // [S34-EFFECT] LaunchedEffectImpl lifecycle entries
                static thread_local uint64_t eff_n = 0;
                ++eff_n;
                if (eff_n <= 16) {
                    std::cerr << "[S34-EFFECT] LF/Y." << method_name << " #" << eff_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LW1/l0;" && method_name == "a") {
                // [S34-EFFECT] CoroutineScope.launch entry
                static thread_local uint64_t l0a_n = 0;
                ++l0a_n;
                if (l0a_n <= 16) {
                    std::cerr << "[S34-EFFECT] launch(W1/l0.a) #" << l0a_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e;" &&
                       method_name == "e" && descriptor == "(LF/z;)V") {
                // [S34-MLAW] LayoutNode.measure(constraints) entries
                static thread_local uint64_t meas_n = 0;
                ++meas_n;
                if (meas_n <= 24) {
                    std::cerr << "[S34-MLAW] LayoutNode.measure #" << meas_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" && method_name == "k" &&
                       descriptor == "()Z") {
                // [S34-SKIPLAW] skipping flag returns — fresh composition
                // must never skip content groups.
                static thread_local uint64_t skip_count = 0;
                ++skip_count;
                if (skip_count <= 80) {
                    std::cerr << "[S34-SKIPLAW] LF/l.k #" << skip_count
                              << " depth=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" &&
                       method_name == "j" && descriptor == "()V") {
                static thread_local uint64_t sn_count = 0;
                ++sn_count;
                if (sn_count <= 40)
                    std::cerr << "[S34-GROUPS] startNode #" << sn_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;" &&
                       method_name == "F" && descriptor == "()V") {
                static thread_local uint64_t un_count = 0;
                ++un_count;
                if (un_count <= 40)
                    std::cerr << "[S34-GROUPS] useNode #" << un_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;" &&
                       method_name == "m" && descriptor == "(LL1/a;)V") {
                static thread_local uint64_t cn_count = 0;
                ++cn_count;
                if (cn_count <= 40)
                    std::cerr << "[S34-GROUPS] createNode #" << cn_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;" && method_name == "r" &&
                       descriptor == "()V") {
                static thread_local uint64_t en_count = 0;
                ++en_count;
                if (en_count <= 40)
                    std::cerr << "[S34-GROUPS] r() #" << en_count
                              << " depth=" << recursion_depth_ << std::endl;
            } else if (class_name == "LF/l;") {
                // [S34-LALL] every ComposerImpl method entry, bounded
                static thread_local uint64_t lall_count = 0;
                ++lall_count;
                if (lall_count <= 2600) {
                    std::cerr << "[S34-LALL] #" << lall_count << " LF/l."
                              << method_name << descriptor
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" &&
                       ((method_name == "j" || method_name == "F" ||
                         method_name == "b" || method_name == "g" ||
                         method_name == "r" || method_name == "i") &&
                        descriptor == "()V")) {
                // [S34-STATEM2] ComposerImpl state machine with field values:
                // j=startNode, F=useNode, r/b/g/i=group end/skip variants.
                static thread_local uint64_t statem_count = 0;
                ++statem_count;
                if (statem_count <= 150) {
                    std::cerr << "[S34-STATEM] LF/l." << method_name
                              << " depth=" << recursion_depth_;
                    uint32_t recv = args.empty() ? 0 : args[0].object_id;
                    for (const char* fname : {"O", "q", "x"}) {
                        auto v = heap_.get_object_field(recv, fname);
                        if (!v)
                            v = heap_.get_object_field(
                                recv, std::string("LF/l;.") + fname);
                        if (v)
                            std::cerr << " " << fname << "=" << v->int_val;
                    }
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "LZ1/z;" && method_name == "getValue") {
                // [S34-LISTSZ] tracker reads with inner list size
                static thread_local uint64_t tz_n = 0;
                ++tz_n;
                if (tz_n <= 24) {
                    std::cerr << "[S34-LISTSZ] Z1/z.getValue #" << tz_n
                              << " d=" << recursion_depth_;
                    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        std::cerr << " tracker=o" << args[0].object_id;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " <" << frames[0].first << "."
                                  << frames[0].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Landroidx/navigation/compose/p$r;" &&
                        method_name == "getValue") ||
                       (class_name == "LF/w;" && method_name == "d") ||
                       (class_name == "LF/w;" && method_name == "b") ||
                       (class_name == "LF/f1;" && method_name == "getValue") ||
                       (class_name == "Lz1/r;" && method_name == "A") ||
                       (class_name == "LZ1/z;")) {
                // [S34-READSIDE] visibleEntries read side
                static thread_local std::map<std::string, uint64_t> rsd_n;
                std::string rsd_key = class_name + "." + method_name;
                uint64_t n = ++rsd_n[rsd_key];
                if (n <= 20) {
                    std::cerr << "[S34-READSIDE] " << rsd_key << " #" << n
                              << " d=" << recursion_depth_;
                    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        std::cerr << " recv=o" << args[0].object_id;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " <" << frames[0].first << "."
                                  << frames[0].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Lh1/t;") ||
                       (class_name == "Landroidx/navigation/c$a;")) {
                // [S34-NSPUSH] NavigatorState method dispatches
                static thread_local std::map<std::string, uint64_t> nsp_n;
                std::string nsp_key = class_name + "." + method_name;
                uint64_t n = ++nsp_n[nsp_key];
                if (n <= 10) {
                    std::cerr << "[S34-NSPUSH] " << nsp_key << " #" << n
                              << " d=" << recursion_depth_
                              << " argc=" << args.size();
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 2; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "LZ1/M;") &&
                       (method_name == "getValue" || method_name == "setValue")) {
                // [S34-FLOW] MutableStateFlow get/set
                static thread_local uint64_t flw_n = 0;
                ++flw_n;
                if (flw_n <= 40) {
                    std::cerr << "[S34-FLOW] Z1/M." << method_name << " #" << flw_n
                              << " d=" << recursion_depth_;
                    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        std::cerr << " recv=o" << args[0].object_id;
                    if (method_name == "setValue" && args.size() > 1 &&
                        args[1].type == DalvikType::OBJECT_REF)
                        std::cerr << " val=o" << args[1].object_id;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " <" << frames[0].first << "."
                                  << frames[0].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Lj/b;" && method_name == "b") ||
                       (class_name == "Lk/K;") ||
                       (class_name == "Landroidx/navigation/compose/p$f;" &&
                        method_name == "g") ||
                       (class_name == "Landroidx/navigation/compose/p$c;" &&
                        method_name == "o") ||
                       (class_name == "Landroidx/navigation/compose/p$p;" &&
                        method_name == "o") ||
                       (class_name == "Landroidx/navigation/compose/p$q;" &&
                        method_name == "o") ||
                       (class_name == "LF/M;" && method_name == "c")) {
                // [S34-ACBOUND] AnimatedContent boundary + p lambdas
                static thread_local std::map<std::string, uint64_t> acb_n;
                std::string acb_key = class_name + "." + method_name;
                uint64_t n = ++acb_n[acb_key];
                if (n <= 8) {
                    std::cerr << "[S34-ACBOUND] " << acb_key << " #" << n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Landroidx/navigation/compose/p$e;" &&
                        method_name == "g") ||
                       (class_name == "Landroidx/navigation/compose/l;" &&
                        method_name == "a") ||
                       (class_name == "LN/a;" && method_name == "g") ||
                       (class_name == "Ln1/q;" && method_name == "g") ||
                       (class_name == "Ln1/s;" && method_name == "g") ||
                       (class_name == "Ln1/t;" && method_name == "g")) {
                // [S34-DCHAIN] destination-content invoke chain
                static thread_local std::map<std::string, uint64_t> dch_n;
                std::string dch_key = class_name + "." + method_name;
                uint64_t n = ++dch_n[dch_key];
                if (n <= 8) {
                    std::cerr << "[S34-DCHAIN] " << dch_key << " #" << n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {
                // [S34-EMITCHAIN] node factory call — top-8 caller frames
                static thread_local uint64_t emit_count = 0;
                ++emit_count;
                if (emit_count <= 6) {
                    std::cerr << "[S34-EMITCHAIN] LayoutNode factory #" << emit_count
                              << " depth=" << recursion_depth_ << " chain:";
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 8; ++fi) {
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    }
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e;" &&
                       method_name == "n") {
                ++draw_count;
                if (draw_count <= 8) {
                    std::cerr << "[NODE-CENSUS] LayoutNode.draw #" << draw_count
                              << " " << descriptor
                              << " recv=" << (args.empty() ? 0 : args[0].object_id)
                              << std::endl;
                }
            } else if ((class_name == "Landroidx/compose/ui/node/e;" ||
                        class_name == "Lk0/T;") &&
                       (method_name == "attach" || method_name == "x0" ||
                        method_name == "N0" || method_name == "O0")) {
                ++attach_count;
                if (attach_count <= 12) {
                    std::cerr << "[NODE-CENSUS] link-candidate "
                              << class_name << "." << method_name
                              << " #" << attach_count
                              << " recv=" << (args.empty() ? 0 : args[0].object_id)
                              << " " << descriptor << std::endl;
                }
            }
        }
    }
    // EXP-053: Clear pending exception at method entry.
    pending_exception_ = DalvikValue::make_null();
    // EXP-042 Phase 4: Log the first 5000 method entries for diagnostic
    // visibility, then suppress to avoid log spam during long runs.
    // EXP-043 Phase 1: raised from 200 to 5000 to capture the full path
    // to the Intrinsics loop blocker.
    // EXP-053: raised to 100000 to capture <clinit> paths.
    // §24 TOOL-HYGIENE (MASTER-3 session 11): this is now ENV-GATED —
    // 100k unconditional stderr lines per run buried real signals
    // ([EXC-PROPAGATE], [SQLITE-SHADOW]) and slowed every run. Gate:
    // MINIANDROID_METHOD_TRACE=1 restores the old verbosity.
    static thread_local const bool method_trace_on =
        diag_env("MINIANDROID_METHOD_TRACE");
    static thread_local uint64_t method_entry_count = 0;
    // CONT-38: env-tunable cap (default 100000 unchanged) — composition
    // forensics on deep trees (dooz NavHost destination) run past the fixed
    // cutoff, hiding the exact ctor/install moments.
    static thread_local uint64_t method_trace_cap = [] {
        const char* c = std::getenv("MINIANDROID_METHOD_TRACE_CAP");
        return (c != nullptr) ? (uint64_t)strtoull(c, nullptr, 10) : 100000ULL;
    }();
    if (method_trace_on && method_entry_count < method_trace_cap) {
        std::cerr << "[METHOD-IN] " << class_name << "." << method_name
                  << " (bytecode_size=" << bytecode.size() << ")" << std::endl;
        method_entry_count++;
    }
    // S26 (R-NEW-328 evidence): every DEX method entry INSIDE the custom-view
    // draw window, env-gated + bounded — shows exactly which methods execute
    // during the compose draw dispatch and where the pipeline stops.
    static thread_local const bool drawwin_on =
        diag_env("MINIANDROID_DRAW_WINDOW_TRACE");
    static thread_local uint64_t drawwin_count = 0;
    // CONT-38: env-tunable cap (default 3000 unchanged) — the compose draw
    // cascade is deep (hundreds of method entries per dispatch); the fixed
    // cap died mid-walk before reaching the NavHost destination nodes.
    static thread_local uint64_t drawwin_cap = [] {
        const char* c = std::getenv("MINIANDROID_DRAW_WINDOW_TRACE_CAP");
        return (c != nullptr) ? (uint64_t)strtoull(c, nullptr, 10) : 3000ULL;
    }();
    if (drawwin_on && draw_window_active_ && drawwin_count < drawwin_cap) {
        std::cerr << "[DRAWWIN-IN] " << class_name << "." << method_name
                  << " " << descriptor << std::endl;
        drawwin_count++;
    }
    // CONT-38 (F-C4-544 evidence, DIAG-ONLY, env-gated): the compose draw
    // cascade reached Luc0;.g x205 / rc0.e x203 / rc0.c x971 in the C013
    // windows, yet the board draw block (Lz6;.i) NEVER dispatched. The
    // suspected skip: Lpz0;.L0's arm select — P (the InnerNodeCoordinator)
    // NULL -> the translate+children arm -> a childless node draws NOTHING.
    // This probe reads each Lpz0;.L0 receiver's P + D (coords) fields from
    // the heap at the invoke entry: which nodes draw, which are skipped,
    // and whether the board node's P is missing. Read-only, bounded.
    static thread_local const bool l0_trace_on =
        diag_env("MINIANDROID_L0_TRACE");
    static thread_local uint32_t l0_trace_count = 0;
    if (l0_trace_on && l0_trace_count < 400 &&
        class_name == "Lpz0;" && method_name == "L0" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        ++l0_trace_count;
        uint32_t p_id = 0, d_lo = 0, d_hi = 0;
        std::string p_cls;
        int m_flag = -1;  // T21: r1-ran witness (Lel0;.M written at r1 end)
        auto pf = heap_.get_object_field(args[0].object_id, "P");
        if (pf && pf->type == DalvikType::OBJECT_REF && pf->object_id != 0) {
            p_id = pf->object_id;
            if (const auto* po = heap_.get(pf->object_id))
                p_cls = po->class_descriptor;
        }
        // T21 witness: r1 writes the chain's M flag on EVERY exit path; if
        // it is still unset the modifier-update apply (r1) NEVER ran for
        // this node — a genuinely different root than "no draw content".
        auto sf = heap_.get_object_field(args[0].object_id, "s");
        if (sf && sf->type == DalvikType::OBJECT_REF && sf->object_id != 0) {
            auto mf = heap_.get_object_field(sf->object_id, "M");
            if (mf && (mf->type == DalvikType::BYTE ||
                       mf->type == DalvikType::INT32))
                m_flag = mf->int_val;
            else if (mf && (mf->type == DalvikType::INT64))
                m_flag = (int)mf->long_val;
        }
        auto df = heap_.get_object_field(args[0].object_id, "D");
        if (df && df->type == DalvikType::INT64) {
            d_lo = (uint32_t)(df->long_val & 0xffffffffULL);
            d_hi = (uint32_t)((df->long_val >> 32) & 0xffffffffULL);
        }
        // CONT-45 D1: measure-state witness — the layer's packed SIZE (the
        // l0(J) commit writes e/f ints; g:J = the packed timestamp) and the
        // owner presence. Distinguishes "measured but never placed" (e/f>0,
        // D=0) from "never measured" (e/f=0) at the L0 draw arm.
        int e_w = -1, f_h = -1;
        auto ef = heap_.get_object_field(args[0].object_id, "e");
        if (ef && ef->type == DalvikType::INT32) e_w = ef->int_val;
        auto ff = heap_.get_object_field(args[0].object_id, "f");
        if (ff && ff->type == DalvikType::INT32) f_h = ff->int_val;
        std::cerr << "[L0-TRACE] node#" << args[0].object_id
                  << " P=" << (p_id ? ("#" + std::to_string(p_id) + " " + p_cls)
                                    : std::string("NULL"))
                  << " r1ran=" << (m_flag < 0 ? "?" : (m_flag ? "Y" : "N"))
                  << " size=" << e_w << "x" << f_h
                  << " D=0x" << std::hex << d_hi << d_lo << std::dec
                  << " caller=" << current_class_ << "." << current_method_
                  << std::endl;
    }
    // ────────────────────────────────────────────────────────────────────
    // ────────────────────────────────────────────────────────────────────
    // CONT-44 T24 (F-NEW-567 evidence, DIAG-ONLY, env-gated): V→z bridge
    // watch. Runtime trace facts: Lel0;.V (compose invalidate-family)
    // RUNS after the destination-node insertion, but Lt4;.z (the owner
    // requestMeasure bridge → Lzs0;.r delegate.requestMeasure) NEVER
    // fires after the initial attach wave (z last@1140 vs V last@7053 in
    // the m2/m3 filtered traces), so the inserted nodes are never
    // measured (D=0, P=NULL → board region zero draw ops). V's body
    // guards the z call behind a field test. This probe dumps the V
    // receiver's OBJECT-REF fields (name → target id/class) at entry —
    // read-only, bounded 60 — to expose which reference is NULL/absent
    // on late-inserted nodes vs the initial attach-wave nodes.
    // ────────────────────────────────────────────────────────────────────
    static thread_local const bool v_trace_on =
        diag_env("MINIANDROID_V_TRACE");
    static thread_local uint32_t v_trace_count = 0;
    if (class_name == "Lel0;" && method_name == "V" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        uint32_t rid = args[0].object_id;
        // ── R-NEW-567 (CONT-44 T24, AOSP insertAt owner-propagation law):
        // a LayoutNode in an attached tree ALWAYS carries its owner
        // (LayoutNode.insertAt → node.owner = this.owner). The engine's
        // second-wave node materialization skips the h-writer, so late
        // nodes reach V with owner ABSENT and V's guard skips Lt4;.z —
        // the delegate measure scheduler is never armed (F-NEW-567 face:
        // board region zero draw ops). Repair: complete the propagation
        // with the recorded owner (exactly the value insertAt would have
        // written). Gate: only when an owner assignment was actually
        // observed (compose_owner_last_ != 0) and the receiver truly
        // lacks the field. Bounded evidence log.
        if (compose_owner_last_ != 0) {
            auto* ho = heap_.get(rid);
            auto rf = ho ? ho->get_field("r") : DalvikValue::make_uninit();
            auto qf = ho ? ho->get_field("Lel0;->r")
                         : DalvikValue::make_uninit();
            bool attached_absent =
                rf.type != DalvikType::OBJECT_REF &&
                qf.type != DalvikType::OBJECT_REF;
            static thread_local uint32_t r567_log = 0;
            // ── R-NEW-567 (CONT-44 T24, AOSP LayoutNode.attach law):
            // owner is the ATTACH MARKER — LayoutNode.attach(owner) checks
            // `check(owner == null)` and THEN stores it (the d-writer:
            // Lel0;.d(Ld31;)V — runs for the attach wave via Lt4;.<init>
            // and for first-wave inserts via B). Second-wave nodes reach V
            // with owner ABSENT because their insert path never executed
            // the attach law; V's guard (isAttached) then correctly skips
            // Lt4;.z and the measure scheduler is never armed (F-NEW-567
            // face: board region zero draw ops; V-TRACE evidence:
            // recv=9089..9329 r=ABSENT while first-wave nodes carry
            // r=#1547). THE FIX IS NOT a raw field write — that violates
            // the attach invariant (regression: compose's own attach law
            // threw ISE "Cannot attach Lel0;@6660 as it already is
            // attached"). The faithful repair = EXECUTE the real attach
            // law: try_recursive_invoke("Lel0;", "d", {this, owner}) —
            // the same method the B-insert path calls, running its real
            // body (owner store + modifier-chain attach side effects).
            // Env kill-switch: MINIANDROID_R567_DISABLE=1.
            // T24 status: the V-entry attach dispatch RACES compose's own
            // attach (node 6660: compose attaches it later via Lwo;.e and
            // throws ISE "already attached" → onCreate death). The repair
            // is therefore OPT-IN (MINIANDROID_R567_ATTACH=1) for A/B
            // forensics; default runs stay diagnostic-only. The faithful
            // fix point is the genuinely-never-attached node class
            // (V-TRACE: recv=9089..9329 r=ABSENT at draw time) — next
            // session: attach at first DRAW reach (Lpz0;.L0 entry) where
            // the onCreate attach race is over, or execute the skipped
            // applier-insert chain (B/d) for the second wave.
            if (attached_absent &&
                std::getenv("MINIANDROID_R567_DISABLE") == nullptr &&
                std::getenv("MINIANDROID_R567_ATTACH") != nullptr) {
                std::string own_cls = "Ljava/lang/Object;";
                if (const auto* oo = heap_.get(compose_owner_last_))
                    own_cls = oo->class_descriptor;
                DalvikValue ret = DalvikValue::make_void();
                DalvikExecutionResult res;
                bool ok = try_recursive_invoke(
                    "Lel0;", "d",
                    {DalvikValue::make_object(rid, "Lel0;"),
                     DalvikValue::make_object(compose_owner_last_, own_cls)},
                    ret, res);
                if (r567_log < 32) {
                    ++r567_log;
                    std::cerr << "[R-NEW-567-ATTACH] V recv=" << rid
                              << " owner=#" << compose_owner_last_
                              << " attach_dispatched=" << (ok ? "YES" : "NO")
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
        if (v_trace_on && v_trace_count < 60 &&
            !args.empty()) {
            uint32_t rid2 = args[0].object_id;
            std::string refs;
            if (const auto* ho = heap_.get(rid2)) {
                int n = 0, total_objrefs = 0;
                for (const auto& kv : ho->fields) {
                    if (kv.second.type == DalvikType::OBJECT_REF) {
                        ++total_objrefs;
                        if (n >= 14) continue;
                        std::string tcls = "-";
                        if (kv.second.object_id != 0) {
                            if (const auto* t = heap_.get(kv.second.object_id))
                                tcls = t->class_descriptor;
                        }
                        refs += " " + kv.first + "=#" +
                                std::to_string(kv.second.object_id) + "(" +
                                tcls + ")";
                        ++n;
                    }
                }
                auto rf = ho->get_field("r");
                std::string r_state = "ABSENT";
                if (rf.type == DalvikType::OBJECT_REF)
                    r_state = "#" + std::to_string(rf.object_id);
                std::cerr << "[V-TRACE] V#" << v_trace_count << " recv="
                          << rid2 << " caller=" << current_class_ << "."
                          << current_method_ << " objrefs_total="
                          << total_objrefs << " r=" << r_state
                          << " refs:" << refs << std::endl;
                // CONT-45 D2: compose-tree census — for the ROOT node
                // (first attach = recv 2113 in the dooz run; generic rule:
                // the node whose q parent field is ABSENT), resolve the
                // children containers (fields A/n, Lwg0; {e:I,f,g:Object})
                // and print their array targets so the wave-2 parent
                // structure is visible heap-side. Read-only, bounded 6.
                static thread_local uint32_t tree_dumps = 0;
                if (tree_dumps < 6 && rid2 != 0) {
                    auto qf = ho->get_field("q");
                    bool is_rootish =
                        qf.type != DalvikType::OBJECT_REF;
                    if (is_rootish) {
                        ++tree_dumps;
                        for (const char* cfld : {"A", "n", "N"}) {
                            auto ctf = ho->get_field(cfld);
                            if (ctf.type != DalvikType::OBJECT_REF ||
                                ctf.object_id == 0)
                                continue;
                            const auto* cw = heap_.get(ctf.object_id);
                            if (!cw)
                                continue;
                            std::string items;
                            int cnt = 0;
                            for (const char* hf : {"f", "g"}) {
                                auto hfr = cw->get_field(hf);
                                if (hfr.type == DalvikType::OBJECT_REF &&
                                    hfr.object_id != 0) {
                                    const auto* arr =
                                        heap_.get(hfr.object_id);
                                    if (arr) {
                                        auto al = arr->get_field(
                                            "__array_length__");
                                        int an = -1;
                                        if (al.type == DalvikType::INT32)
                                            an = al.int_val;
                                        items += std::string(" ") + hf +
                                                  "=arr#" +
                                                  std::to_string(
                                                      hfr.object_id) +
                                                  "[len=" +
                                                  std::to_string(an) + "]";
                                        for (int i = 0; i < an && i < 24;
                                             ++i) {
                                            auto ev = heap_.get_object_field(
                                                hfr.object_id,
                                                "array[" +
                                                    std::to_string(i) + "]");
                                            if (!ev.has_value())
                                                continue;
                                            if (ev->type ==
                                                DalvikType::OBJECT_REF) {
                                                items += " o" +
                                                    std::to_string(
                                                        ev->object_id);
                                                ++cnt;
                                            } else if (ev->type ==
                                                       DalvikType::INT32) {
                                                items += " i" +
                                                    std::to_string(
                                                        ev->int_val);
                                            }
                                        }
                                    }
                                } else if (hfr.type == DalvikType::INT32) {
                                    items += std::string(" ") + hf + "=i" +
                                             std::to_string(hfr.int_val);
                                }
                            }
                            (void)cnt;
                            std::cerr << "[TREE] root#" << rid2 << " "
                                      << cfld << "=#" << ctf.object_id
                                      << "(" << cw->class_descriptor
                                      << ")" << items << std::endl;
                        }
                    }
                }
                // CONT-45 D2b: one-shot deep dump of the root children
                // container (bounded, first 3 dumps only).
                static thread_local uint32_t deep_dumps = 0;
                if (deep_dumps < 40 && rid2 != 0 &&
                    ho->get_field("q").type != DalvikType::OBJECT_REF) {
                    ++deep_dumps;
                    for (const char* cfld : {"n", "A"}) {
                        auto ctf = ho->get_field(cfld);
                        if (ctf.type != DalvikType::OBJECT_REF ||
                            ctf.object_id == 0)
                            continue;
                        std::function<void(uint32_t, int, int)> walk =
                            [&](uint32_t oid, int depth, int budget) {
                            if (depth > 3 || budget <= 0)
                                return;
                            const auto* obj = heap_.get(oid);
                            if (!obj)
                                return;
                            std::string line;
                            int printed = 0;
                            for (const auto& kv : obj->fields) {
                                if (printed >= 10)
                                    break;
                                const auto& v = kv.second;
                                if (v.type == DalvikType::OBJECT_REF &&
                                    v.object_id != 0) {
                                    const auto* t = heap_.get(v.object_id);
                                    line += " " + kv.first + "=#" +
                                            std::to_string(v.object_id) +
                                            "(" + (t ? t->class_descriptor
                                                     : "?") + ")";
                                } else if (v.type == DalvikType::INT32) {
                                    line += " " + kv.first + "=i" +
                                            std::to_string(v.int_val);
                                } else if (v.type == DalvikType::INT64) {
                                    line += " " + kv.first + "=l" +
                                            std::to_string(v.long_val);
                                }
                                ++printed;
                            }
                            std::cerr << "[TREE2] d" << depth << " obj#"
                                      << oid << "(" << obj->class_descriptor
                                      << ")" << line << std::endl;
                            if (obj->class_descriptor.size() > 0 &&
                                obj->class_descriptor[0] == '[') {
                                auto alv = obj->get_field("__array_length__");
                                int an = alv.type == DalvikType::INT32
                                             ? alv.int_val : -1;
                                for (int i = 0; i < an && i < 16; ++i) {
                                    auto ev = heap_.get_object_field(
                                        oid, "array[" + std::to_string(i) +
                                                 "]");
                                    if (ev.has_value() &&
                                        ev->type == DalvikType::OBJECT_REF &&
                                        ev->object_id != 0) {
                                        std::cerr << "[TREE2]   arr[" << i
                                                  << "] -> o" << ev->object_id
                                                  << std::endl;
                                        walk(ev->object_id, depth + 1,
                                             budget - 1);
                                    }
                                }
                                return;
                            }
                            for (const auto& kv : obj->fields) {
                                if (kv.second.type ==
                                        DalvikType::OBJECT_REF &&
                                    kv.second.object_id != 0)
                                    walk(kv.second.object_id, depth + 1,
                                         budget - 1);
                            }
                        };
                        std::cerr << "[TREE2] root#" << rid2 << " via " << cfld
                                  << std::endl;
                        walk(ctf.object_id, 0, 24);
                    }
                }
            }
        }
    }
    // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): ATTACH watch. The Compose
    // text painter (Lte1/Lod1) draw body starts with `if (!this.r) return`
    // (Lok0.r = the attached flag, written ONLY by Lok0.u0/v0). Dispatch
    // reaches Lte1.I (UV-DISPATCH ×15) yet no Lg6 call ever runs → r is
    // false at draw time. Watch the attach/detach pair: receiver object id
    // + class, correlate with the dispatched painter ids. Env-gated,
    // bounded — zero behavior change.
    // ────────────────────────────────────────────────────────────────────
    {
        static thread_local const bool attw_on =
            diag_env("MINIANDROID_ATTACH_WATCH");
        if (attw_on && class_name == "Lok0;" &&
            (method_name == "u0" || method_name == "v0")) {
            static thread_local uint64_t attw_n = 0;
            if (attw_n++ < 400)
                std::cerr << "[ATTACH-WATCH] "
                          << (method_name == "u0" ? "u0(attach)" : "v0(detach)")
                          << " recv=" << (!args.empty() ? args[0].object_id : 0u)
                          << " cls=" << (!args.empty() ? args[0].class_desc : "?")
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
        }
    }
    // S33 (R-NEW-332): method entries inside the F-096 lifecycle dispatch
    // window (real-DEX onMeasure/onLayout) — shows the measure/layout
    // traversal the placement pass actually executes.
    static thread_local const bool lifewin_on =
        diag_env("MINIANDROID_LIFEWIN_TRACE");
    static thread_local uint64_t lifewin_count = 0;
    if (lifewin_on && lifecycle_window_active_ && lifewin_count < 4000) {
        std::cerr << "[LIFEWIN-IN] " << class_name << "." << method_name
                  << " " << descriptor
                  << " recv=" << (args.empty() ? 0 : args[0].object_id)
                  << (args.empty() ? "" : args[0].class_desc)
                  << std::endl;
        lifewin_count++;
    }

    // ────────────────────────────────────────────────────────────────────
    // CONT-9 W5 (F-NEW-256 first-divergence instrumentation, Phase 2 of the
    // directive): generic env-gated CALLER-FRAME trace for a caller-supplied
    // class-prefix list. MINIANDROID_CL_TRACE="Lnb0;,Lwo;,Lv02;,Ly11;"
    // (comma-separated class prefixes; the mechanism is app-agnostic — the
    // prefixes come from the RUN CONFIG, never hardcoded engine rules).
    // For each method entry whose declaring class starts with any prefix,
    // log stage/class.method, recursion depth, leading arg identities, and
    // the TOP-4 caller frames. Read-only; bounded at 4000 lines.
    // Answers: WHO drives the change-list apply while the content composable
    // is still executing (the F-NEW-256 mid-content-pass apply divergence).
    {
        static thread_local const bool cl_on =
            std::getenv("MINIANDROID_CL_TRACE") != nullptr;
        if (cl_on) {
            static thread_local const std::string cl_spec =
                std::getenv("MINIANDROID_CL_TRACE");
            static thread_local uint64_t cl_lines = 0;
            if (cl_lines < 8000) {
                size_t start = 0;
                while (start <= cl_spec.size()) {
                    size_t comma = cl_spec.find(',', start);
                    std::string pfx = cl_spec.substr(
                        start, comma == std::string::npos
                                   ? std::string::npos
                                   : comma - start);
                    // Token form "Lcls;.meth": match the class prefix AND
                    // the exact method name (R8-aware diagnostic targeting).
                    bool hit = false;
                    size_t semi_dot = pfx.find(";.");
                    if (semi_dot != std::string::npos) {
                        std::string cpfx = pfx.substr(0, semi_dot + 1);
                        std::string meth = pfx.substr(semi_dot + 2);
                        hit = (class_name.rfind(cpfx, 0) == 0 &&
                               method_name == meth);
                    } else {
                        hit = (!pfx.empty() &&
                               class_name.rfind(pfx, 0) == 0);
                    }
                    if (hit) {
                        ++cl_lines;
                        std::cerr << "[CL-TRACE] d=" << recursion_depth_
                                  << " " << class_name << "." << method_name;
                        for (size_t ai = 0;
                             ai < args.size() && ai < 3; ++ai) {
                            const auto& a = args[ai];
                            if (a.type == DalvikType::OBJECT_REF)
                                std::cerr << " a" << ai << "=o"
                                          << a.object_id << a.class_desc;
                            else if (a.type == DalvikType::INT32 ||
                                     a.type == DalvikType::BOOLEAN)
                                std::cerr << " a" << ai << "=i" << a.int_val;
                            else if (a.type == DalvikType::INT64)
                                std::cerr << " a" << ai << "=l" << a.long_val;
                        }
                        auto cl_frames = call_stack_.snapshot_top_first();
                        std::cerr << " CALLERS";
                        for (size_t fi = 0;
                             fi < cl_frames.size() && fi < 4; ++fi)
                            std::cerr << " <" << cl_frames[fi].first << "."
                                      << cl_frames[fi].second << ">";
                        std::cerr << std::endl;
                        break;
                    }
                    if (comma == std::string::npos) break;
                    start = comma + 1;
                }
            }
        }
    }

    // EXP-038 (BLOCKER-033): Set current_dex_index_ for per-DEX method resolution.
    // Look up which DEX file this class came from.
    auto it = class_to_dex_index_.find(class_name);
    if (it != class_to_dex_index_.end()) {
        current_dex_index_ = it->second;
    }

    log("Executing: " + class_name + "." + method_name + descriptor);
    log("Bytecode size: " + std::to_string(bytecode.size()) + " instructions");
    
    // Create stack frame
    StackFrame frame;
    frame.class_name = class_name;
    frame.method_name = method_name;
    frame.method_descriptor = descriptor;
    frame.code_offset = 0;
    frame.bytecode_length = bytecode.size();
    frame.registers_size = registers_size;
    frame.ins_size = ins_size;
    frame.outs_size = outs_size;
    frame.registers.initialize(registers_size, ins_size);
    
    // Load arguments into parameter registers.
    //
    // F-028c (M4 §A1) — PARAMETER REGISTER LAYOUT LAW: ART maps parameters
    // to the ins-region per the method proto; every J/D param occupies TWO
    // consecutive registers (value + high-word shadow), all others ONE.
    // The old loop wrote one register per arg, so after the first wide
    // param every later parameter landed early — a delegated
    // <init>(DDDDD) → <init>(DDDDDDD) chain in real Compose code
    // (dooz TransferFunction, LY/p;) read param 3 into param 2's slot and
    // zeros into the tail, tripping "transfer function must be increasing".
    // Layout authority = the method descriptor (parse_proto_param_types).
    {
        const std::vector<std::string> ptypes =
            parse_proto_param_types(descriptor);
        // args[] is RECEIVER-INCLUSIVE for instance calls while ptypes[]
        // lists declared params only. DEX verification guarantees
        // argc == declared_params (+1 for the receiver), so the shapes
        // below are exhaustive for well-formed calls; anything else falls
        // back to the legacy 1:1 layout.
        if (!ptypes.empty() &&
            (args.size() == ptypes.size() ||
             args.size() == ptypes.size() + 1)) {
            size_t ai = 0;
            uint8_t slot = 0;
            if (args.size() == ptypes.size() + 1) {
                // instance call: the receiver occupies slot 0
                frame.registers.write_p(0, f282_args[0]);
                ai = 1;
                slot = 1;
            }
            // S188-W18 STR PROBE: the sibling-family param binding.
            if (diag_env("MINIANDROID_W18_FT_TRACE") &&
                (class_name.find("FileHandle;") != std::string::npos ||
                 current_class_.find("FileHandle;") != std::string::npos)) {
                static thread_local uint64_t strbind_n = 0;
                if (strbind_n++ < 24) {
                    std::cerr << "[W18-BIND] " << class_name << "."
                              << method_name << " regs=" << registers_size
                              << " ins=" << ins_size
                              << " ptypes=" << ptypes.size()
                              << " args=" << args.size();
                    for (size_t bi = 0; bi < args.size() && bi < 3; ++bi)
                        std::cerr << " a" << bi << ":t"
                                  << static_cast<int>(f282_args[bi].type)
                                  << "/o" << f282_args[bi].object_id;
                    std::cerr << std::endl;
                }
            }
            for (size_t ti = 0; ti < ptypes.size() && ai < args.size();
                 ++ti, ++ai) {
                frame.registers.write_p(slot, f282_args[ai]);
                const std::string& t = ptypes[ti];
                if (t == "J" || t == "D") {
                    // Fill the shadow slot with the high 32-bit word so
                    // raw window reads observe ART's two-slot layout.
                    uint64_t bits = 0;
                    if (args[ai].type == DalvikType::INT64) {
                        bits = static_cast<uint64_t>(args[ai].long_val);
                    } else if (args[ai].type == DalvikType::FLOAT64) {
                        std::memcpy(&bits, &args[ai].double_val, sizeof(bits));
                    }
                    DalvikValue shadow;
                    shadow.type = DalvikType::INT32;
                    shadow.int_val =
                        static_cast<int32_t>(static_cast<uint32_t>(bits >> 32));
                    frame.registers.write_p(
                        static_cast<uint8_t>(slot + 1), shadow);
                    slot = static_cast<uint8_t>(slot + 2);
                } else {
                    slot = static_cast<uint8_t>(slot + 1);
                }
            }
        } else {
            // Proto unresolvable → legacy 1:1 fallback layout.
            for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
                frame.registers.write_p(static_cast<uint8_t>(i), f282_args[i]);
            }
        }
    }

    // S20 R-NEW-295 diagnostic: env-gated parameter-slot probe.
    // MINIANDROID_PARAM_TRACE=<class-substr>|<method-substr> prints, at each
    // matching method ENTRY, the raw args, proto param types, and a read-back
    // of the param registers (v[regs-ins .. regs-1]). Read-only — pure
    // get_register reads; diagnostics must never change semantics (M3 law).
    {
        static thread_local const char* pt_filter =
            std::getenv("MINIANDROID_PARAM_TRACE");
        static thread_local uint32_t pt_budget = 20000;
        if (pt_filter && pt_budget > 0) {
            std::string f(pt_filter);
            auto bar = f.find('|');
            std::string fcls = (bar == std::string::npos) ? f : f.substr(0, bar);
            std::string fmth = (bar == std::string::npos) ? "" : f.substr(bar + 1);
            if (class_name.find(fcls) != std::string::npos &&
                (fmth.empty() || method_name == fmth)) {
                pt_budget--;
                std::cerr << "[PARAM-TRACE] " << class_name << "." << method_name
                          << " regs=" << registers_size << " ins=" << ins_size
                          << " args=" << args.size();
                for (size_t i = 0; i < args.size() && i < 8; ++i) {
                    std::cerr << " a" << i << "={t=" << static_cast<int>(args[i].type);
                    if (args[i].type == DalvikType::OBJECT_REF ||
                        args[i].type == DalvikType::STRING_REF)
                        std::cerr << " obj=" << args[i].object_id
                                  << " cls=" << args[i].class_desc;
                    if (args[i].type == DalvikType::INT32)
                        std::cerr << " i=" << args[i].int_val;
                    std::cerr << "}";
                }
                std::cerr << std::endl;
                uint32_t pstart = (registers_size >= ins_size)
                                      ? registers_size - ins_size : 0;
                for (uint32_t r = pstart;
                     r < registers_size && r < pstart + 8; ++r) {
                    DalvikValue rv = frame.registers.read_v(
                        static_cast<uint8_t>(r));
                    std::cerr << "[PARAM-TRACE]   v" << r << "={t="
                              << static_cast<int>(rv.type);
                    if (rv.type == DalvikType::OBJECT_REF ||
                        rv.type == DalvikType::STRING_REF)
                        std::cerr << " obj=" << rv.object_id;
                    if (rv.type == DalvikType::INT32)
                        std::cerr << " i=" << rv.int_val;
                    std::cerr << "}" << std::endl;
                }
            }
        }
    }

    // EXP-062: Debug — trace parameter loading for PhoneView.<init>
    if (diag_env("MINIANDROID_EXP062_TRACE") && class_name.find("PhoneView") != std::string::npos &&
        method_name == "<init>") {
        std::cerr << "[EXP062-PARAM] PhoneView.<init> entering"
                  << " regs=" << registers_size << " ins=" << ins_size
                  << " param_start=" << (registers_size - ins_size)
                  << " args=" << args.size()
                  << std::endl;
        for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
            auto val = frame.registers.read_v(static_cast<uint8_t>(
                registers_size - ins_size + i));
            std::cerr << "  p" << i << " → v" << (registers_size - ins_size + i)
                      << " arg_type=" << static_cast<int>(args[i].type)
                      << " arg_obj=" << args[i].object_id
                      << " arg_class=" << args[i].class_desc
                      << " reg_type=" << static_cast<int>(val.type)
                      << " reg_obj=" << val.object_id
                      << std::endl;
        }
    }

    // EXP-063: Trace getString parameter passing (§24: env-gated —
    // MINIANDROID_APP_TRACE=1).
    static thread_local const bool app_trace_on =
        diag_env("MINIANDROID_APP_TRACE");
    if (app_trace_on && class_name.find("LocaleController") != std::string::npos &&
        method_name == "getString") {
        std::cerr << "[EXP063-GETSTRING] entering"
                  << " regs=" << registers_size << " ins=" << ins_size
                  << " param_start=" << (registers_size - ins_size)
                  << " args=" << args.size()
                  << std::endl;
        for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
            auto val = frame.registers.read_v(static_cast<uint8_t>(
                registers_size - ins_size + i));
            std::cerr << "  p" << i << " → v" << (registers_size - ins_size + i)
                      << " arg_type=" << static_cast<int>(args[i].type)
                      << " arg_int=" << args[i].int_val
                      << " arg_obj=" << args[i].object_id
                      << " reg_type=" << static_cast<int>(val.type)
                      << " reg_int=" << val.int_val
                      << std::endl;
        }
    }

    // EXP-058: Debug — verify parameter writes for addFragmentToStack.
    if (diag_env("MINIANDROID_EXP058_TRACE") && current_method_.find("addFragmentToStack") != std::string::npos ||
        method_name.find("addFragmentToStack") != std::string::npos) {
        for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
            auto val = frame.registers.read_v(static_cast<uint8_t>(
                registers_size - ins_size + i));
            // EXP-059: For INT32, print int_val (not object_id which is always 0).
            std::string arg_val_str;
            if (args[i].type == DalvikType::INT32) {
                arg_val_str = "int_val=" + std::to_string(args[i].int_val);
            } else if (args[i].type == DalvikType::OBJECT_REF) {
                arg_val_str = "obj_id=" + std::to_string(args[i].object_id) +
                              " class=" + args[i].class_desc;
            } else {
                arg_val_str = "obj=" + std::to_string(args[i].object_id);
            }
            std::cerr << "[EXP058-PARAM] p" << i
                      << " → v" << (registers_size - ins_size + i)
                      << " type=" << static_cast<int>(val.type)
                      << " obj=" << val.object_id
                      << " (from arg type=" << static_cast<int>(args[i].type)
                      << " " << arg_val_str << ")"
                      << std::endl;
        }
    }
    
    // Push frame onto call stack
    // R-NEW-339: capture the caller's invoke pc before it is overwritten —
    // pc_ still holds the invoke site in the CALLER frame here.
    call_stack_.set_last_invoke_pc(pc_);
    phase_clock().em_setup.ns.fetch_add(__rdtsc() - f107_su0);  // S61 setup ends
    // S100 §3 (issue #345): last-semantic-op ring for crash forensics.
    CrashForensics::note("DEX", "%s.%s recv=obj%s", class_name.c_str(),
                         method_name.c_str(),
                         (args.empty() ? "0" : std::to_string(args[0].object_id).c_str()));
    call_stack_.push_frame(std::move(frame));
    current_registers_ = &call_stack_.top().registers;
    pc_ = 0;
    
    // Execute until halt
    uint64_t f107_fe0 = 0; phase_clock().enter(phase_clock().em_fetch, f107_fe0);  // S61
    // CONT-29 W1 (generic, env-gated, read-only): per-method interpreter insn
    // census — names the throughput burn (draw-window wall) as evidence,
    // not guesswork. Accumulates per (class.method) insn deltas at method
    // exit; dumps the TOP-8 rows every ~2s wall clock (bounded 64 dumps).
    // Zero cost when MINIANDROID_METHOD_CENSUS is unset.
    static thread_local const bool mi_census_on_
        = std::getenv("MINIANDROID_METHOD_CENSUS") != nullptr;
    const uint64_t mi_census_entry = mi_census_on_ ? instruction_sequence_ : 0;
    bool success = fetch_decode_execute(result);
    phase_clock().exit(phase_clock().em_fetch, f107_fe0);
    if (mi_census_on_) {
        static thread_local std::unordered_map<std::string, uint64_t> mi_map;
        static thread_local std::unordered_map<std::string, uint64_t> mi_calls;
        static thread_local std::chrono::steady_clock::time_point mi_win;
        static thread_local bool mi_win_init = false;
        static thread_local uint32_t mi_dumps = 0;
        static thread_local uint64_t mi_last_seq = 0;
        const uint64_t mi_delta
            = instruction_sequence_ > mi_census_entry
                  ? instruction_sequence_ - mi_census_entry
                  : 0;
        std::string key = class_name + "." + method_name;
        mi_map[key] += mi_delta;
        mi_calls[key] += 1;
        if (!mi_win_init) {
            mi_win = std::chrono::steady_clock::now();
            mi_win_init = true;
            mi_last_seq = instruction_sequence_;
        }
        auto mi_el = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - mi_win).count();
        if (mi_el >= 2000 && mi_dumps < 64) {
            ++mi_dumps;
            mi_win = std::chrono::steady_clock::now();
            const uint64_t win_insns
                = instruction_sequence_ > mi_last_seq
                      ? instruction_sequence_ - mi_last_seq
                      : 0;
            mi_last_seq = instruction_sequence_;
            std::vector<std::pair<std::string, uint64_t>> rows(
                mi_map.begin(), mi_map.end());
            std::sort(rows.begin(), rows.end(),
                      [](const auto& a, const auto& b) {
                          return a.second > b.second;
                      });
            std::cerr << "[METHOD-CENSUS] window_insns=" << win_insns
                      << " total_methods=" << mi_map.size();
            for (size_t r = 0; r < rows.size() && r < 8; ++r)
                std::cerr << " | " << rows[r].first << "=" << rows[r].second
                          << " (n=" << mi_calls[rows[r].first] << ")";
            std::cerr << std::endl;
        }
    }
    uint64_t f107_pp0 = 0; phase_clock().enter(phase_clock().em_pop, f107_pp0);  // S61

    // EXP-042 Phase 1: memory probe after each method returns. This lets us
    // see whether memory grows linearly with recursive call count (a leak)
    // or stays flat (capped). Sampled once per method exit.
    {
        static thread_local uint64_t last_probe_seq = 0;
        if (instruction_sequence_ - last_probe_seq >= 10000 ||
            last_probe_seq == 0) {
            std::string tag = "method_exit: " + class_name + "." + method_name +
                              " insns=" + std::to_string(instruction_sequence_);
            miniandroid::probe::mark(tag.c_str());
            last_probe_seq = instruction_sequence_;
        }
    }
    
    // Pop frame (if not already done by return)
    if (!call_stack_.empty()) {
        call_stack_.pop_frame();
        current_registers_ = nullptr;
    }
    
    // Update result
    // F-110a (S62+, R-NEW-381 lever, MEASURED): result-snapshot deferral law.
    // The two assignments below deep-copy the ENTIRE heap (all objects × all
    // field maps of pair<string,DalvikValue>) and the ENTIRE call stack (all
    // frames × all registers) into `result`. execute_method_internal is
    // RECURSIVE: every nested invoke shares this same result sink
    // (try_recursive_invoke(..., *current_result_) at the class-init site and
    // the invoke handlers), so each of the N nested method exits performed a
    // full O(heap) copy that its parent exit immediately overwrote.
    // Measured (anuto 25s startup run, gprof): 387.6M pair<string,string>
    // vector element copies (__do_uninit_copy) — the dominant single cost of
    // the whole run; startup executed only 128K instructions in 25s of
    // user CPU. Outermost-only assignment preserves the EXACT final result
    // content (the outermost exit is the last write in every nesting chain)
    // while removing the O(N × heap_size) quadratic copying.
    if (call_stack_.empty()) {
        result.call_stack = call_stack_;
        result.heap = heap_;
    }
    
    if (halted_on_return_) {
        // F-NEW-395 UNWIND-HONESTY LAW (CONT-87, fixture-first): halted_on_
        // return_ is set BOTH by a normal return AND by an exception unwind
        // out of this frame (throw_deferred no-handler / mid-stack
        // keep-in-flight). Reporting COMPLETED_SUCCESS for an unwind was the
        // root of the clinit-result-OK-despite-throw honesty defect (live
        // pre-fix evidence run/cont87/clinit_pre.stderr: [CLASS_INIT]
        // result=OK recorded for a clinit whose deferred raise escaped, the
        // F-NEW-215 erroneous-class law never armed, and the raw exception
        // teleported to a LATER invoke site). The unwind case now records an
        // unambiguous marker — COMPLETED_PARTIAL + halt_reason="unwind <type>"
        // — which the <clinit> call site (ensure_class_initialized) reads to
        // route the class into the registered F-NEW-215 erroneous state.
        // Normal returns are byte-identical to before.
        if (frame_unwind_exception_valid_) {
            result.final_status =
                DalvikExecutionResult::FinalStatus::COMPLETED_PARTIAL;
            result.halt_reason = "unwind " +
                (std::string(frame_unwind_exception_.class_desc).empty()
                     ? std::string("Ljava/lang/RuntimeException;")
                     : std::string(frame_unwind_exception_.class_desc));
        } else {
            result.final_status =
                DalvikExecutionResult::FinalStatus::COMPLETED_SUCCESS;
            // F-NEW-395: a normal completion must not inherit a stale
            // "unwind ..." marker written by a nested run whose exception
            // THIS frame's own handler subsequently caught — the clinit
            // call site keys the erroneous-class routing on this exact
            // prefix, so SUCCESS is only SUCCESS with an empty marker.
            result.halt_reason.clear();
        }
    } else if (halted_) {
        result.final_status = DalvikExecutionResult::FinalStatus::HALTED_UNIMPLEMENTED_OPCODE;
        result.halt_reason = halt_reason_;
    } else {
        result.final_status = DalvikExecutionResult::FinalStatus::COMPLETED_PARTIAL;
    }
    
    // ── TRAIN-67 (T67-EXIT): the matching exit side — what the machine or
    // the await body RETURNED (SUSPENDED sentinel vs the real change object)
    // and how the frame ended (success vs unwind).
    {
        static const bool t67x_on = diag_env("MINIANDROID_T67_LABEL_TRACE");
        if (t67x_on && (class_name == "Lss1;" || class_name == "Lbt1;" ||
                        class_name == "Lxs1;" || class_name == "Lnr1;" ||
                        class_name == "Li6;" || class_name == "La00;")) {
            static thread_local uint64_t t67x_n = 0;
            if (t67x_n++ < 400) {
                const DalvikValue& t67rv = last_invoke_return_;
                std::string t67_r = "?";
                if (t67rv.type == DalvikType::OBJECT_REF)
                    t67_r = t67rv.class_desc + "#" +
                            std::to_string(t67rv.object_id);
                else
                    t67_r = dalvik_value_to_string(t67rv);
                std::cerr << "[T67-EXIT] " << class_name << "." << method_name
                          << " ret=" << t67_r << " status="
                          << (result.final_status ==
                                      DalvikExecutionResult::FinalStatus::
                                          COMPLETED_SUCCESS
                                  ? "SUCCESS"
                                  : (result.final_status ==
                                             DalvikExecutionResult::
                                                 FinalStatus::HALTED_UNIMPLEMENTED_OPCODE
                                         ? "HALTED"
                                         : "PARTIAL"))
                          << std::endl;
            }
        }
    }

    current_result_ = nullptr;
    return success;
}

// EXP-053: Ensure a class is initialized before accessing its static fields.
//
// Per JVM spec §2.17.4 (Initialization), a class is initialized the first
// time it is "actively used". Active use includes:
//   - new-instance on the class
//   - invoke-static on a method declared by the class
//   - sget/sput on a field declared by the class
//
// Initialization triggers <clinit> (the static initializer block, which
// may contain `const + sput` pairs that set the field values, plus other
// side-effecting code).
//
// We call this from the sget/sput handlers and from new-instance. The
// method is idempotent: a class already marked initialized is a no-op.
//
// CONT-48 F1 (AndResGuard drawable-binding gap): the R$ resid harvest used to
// live ONLY inside ensure_class_initialized — a LAZY law. The ARSC drawable
// census runs at startup BEFORE any app code touches R.drawable.*, so on
// resource-obfuscated APKs (telegram official: res/ paths renamed to res/ENE.png
// style garbage) field_name_by_resid_ had ZERO drawable entries and the
// ARSC-first binding pass bound 0/13206 paths. The harvest body is now a
// standalone helper, called BOTH lazily (class init) and EAGERLY (eager
// harvest over every R$ class in the DexReport, before the drawable census).
// Idempotent: the map overwrite is last-wins on identical resids.
void DalvikExecutionEngine::harvest_r_class_fields(
        const std::string& class_descriptor, const dex::ClassInfo& cls_ref) {
    if (class_descriptor.find("R$") == std::string::npos) return;
    // EXP-063: Build field_name_by_resid mapping for R classes.
    // This maps resource ID → field name, so we can resolve resources
    // by name when DEX IDs don't match ARSC entry indices.
    // EXP-093: Store ALL R$string values (including small D8-shrunk ordinals).
    // The D8 shrinker remaps resource IDs to small ordinals per R$subclass.
    // R$string.SentSmsCode=3 is different from R$anim.text_out_down=3.
    // By storing R$string values, we can resolve them via field_name_by_resid_.
    // R$bool / R$integer / R$color values >= 0x10000 are still stored (they
    // don't collide with R$string ordinals because they use the >= 0x10000 range).
    bool is_r_string = (class_descriptor.find("R$string") != std::string::npos);
    bool is_r_raw = (class_descriptor.find("R$raw") != std::string::npos);
    // EXP-098 (CM-027): R$raw also uses small D8-shrunk ordinals
    // (e.g. R.raw.default_pattern=3, R.raw.bot_webview_sheet_to_cross=3)
    // intermixed with large values (R.raw.chats_archiveavatar=917525).
    // Store ALL values so RLottieImageView.setAnimation(R.raw.X, w, h)
    // can resolve to the field name → resource_raw_paths_ lookup.
    bool store_all = is_r_string || is_r_raw;
    for (const auto& field : cls_ref.static_fields) {
        if (!field.has_default_value || field.default_value_is_string) continue;
        if (store_all) {
            // Store ALL values (including small ordinals like 0, 1, 2, 3).
            // Multiple R$subclasses can have value=3 — distinguished by
            // the calling class context (R$string.SentSmsCode vs
            // R$raw.bot_webview_sheet_to_cross). The caller resolves
            // via the right resource_raw_paths_/resource_string_values_.
            field_name_by_resid_[static_cast<int32_t>(field.default_int_value)] = field.name;
        } else {
            // For non-R$string/R$raw: only store values >= 0x10000
            if (field.default_int_value >= 0x10000) {
                field_name_by_resid_[static_cast<int32_t>(field.default_int_value)] = field.name;
            }
        }
    }
}

// CONT-48 F1: eager pass — harvest EVERY R$ class in the DexReport without
// executing any <clinit>. O(#classes) scan, no side effects beyond the resid
// map. Returns the number of R$ classes seen.
int DalvikExecutionEngine::eager_harvest_r_classes() {
    if (!dex_report_) return 0;
    int seen = 0;
    for (const auto& cls : dex_report_->classes) {
        if (cls.name.find("R$") == std::string::npos) continue;
        harvest_r_class_fields(cls.name, cls);
        seen++;
    }
    std::cerr << "[CONT48-F1] eager R$ harvest: " << seen << " classes, "
              << field_name_by_resid_.size() << " resids" << std::endl;
    return seen;
}

bool DalvikExecutionEngine::ensure_class_initialized(const std::string& class_descriptor) {
    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().class_init_ph, f107_t0);
    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().class_init_ph, f107_t0};
    // G12 FIX-G12-001b (descriptor form law): normalize BEFORE any prefix
    // test — the UI/init layer hands us dot-form descriptors
    // (Landroid.app.AppComponentFactory;) and the framework-namespace skip
    // below tests slash prefixes (Landroid/). Without normalization the
    // app-bundled android.* stub <clinit> executed and threw
    // NoClassDefFoundError at boot (muellerma stopwatch PARTIAL cluster,
    // FIND-G09-ACF-001): AOSP parent-delegation law — framework classes
    // resolve from the boot classpath, an app-bundled android.* copy must
    // never shadow framework semantics.
    const std::string normalized =
        framework::normalize_class_desc(class_descriptor);
    // F-NEW-215 CLASS-INIT HONESTY LAW: an ERRONEOUS class (its <clinit>
    // already ran and threw) stays erroneous — JVMS 5.5 forbids re-running
    // <clinit>, and the honest answer to "is it initialized?" is NO, not
    // the historical silent true. Active-use sites consult
    // class_clinit_failed() to raise NoClassDefFoundError; the earlier
    // evidence (08C.<clinit> FAILED while bookkeeping stayed OK, statics
    // missing far downstream) is exactly the silent-state-corruption
    // family this law closes.
    {
        auto f215_fit = failed_clinit_classes_.find(normalized);
        if (f215_fit == failed_clinit_classes_.end())
            f215_fit = failed_clinit_classes_.find(class_descriptor);
        if (f215_fit != failed_clinit_classes_.end()) {
            static std::atomic<uint64_t> f215_reuse_n{0};
            if (f215_reuse_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ERRONEOUS-REUSE class="
                          << class_descriptor
                          << " (clinit previously failed: " << f215_fit->second
                          << ")" << std::endl;
            }
            return false;
        }
    }
    // Already initialized?
    if (initialized_classes_.count(normalized) > 0 ||
        initialized_classes_.count(class_descriptor) > 0) {
        phase_clock().ci_warm.fetch_add(1, std::memory_order_relaxed);
        return true;
    }
    // ── R14 (A-R3 #580) SUPERCLASS-FIRST CLASS-INIT LAW (A-R3, S216) ──
    // JVMS 5.5 / AOSP ClassLinker::EnsureInitialized: initializing class C
    // requires C's DIRECT SUPERCLASS to be initialized FIRST (recursively).
    // The engine already builds class_to_superclass_ (EXP-068) and walks it
    // for semantic ancestry — but no init site ever walked it UPWARD (11
    // insert sites, 0 super-init calls at the R14 audit). Observable
    // divergence: a superclass whose <clinit> publishes state (registration
    // singletons, static tables consumed reflectively, counters) never ran
    // until the subclass actively referenced a superclass member — on ART
    // it runs at subclass-init time. One walk here covers all call sites.
    // Re-entrancy safe: the initialized_classes_ guard above (checked again
    // inside the recursive call) breaks cycles A→B→A before any <clinit>
    // re-runs, and the framework-namespace skip below is re-applied for the
    // superclass by the recursive call itself.
    if (!initialized_classes_.count(normalized)) {
        // A/B gate: MINIANDROID_R14_SUPER_INIT=0 disables (default ON —
        // the AOSP-faithful order; the 6-pin gate decides the final ship).
        static const bool r14_off =
            [] { const char* e = std::getenv("MINIANDROID_R14_SUPER_INIT");
                 return e && std::string(e) == "0"; }();
        auto sup_it = class_to_superclass_.find(normalized);
        if (sup_it == class_to_superclass_.end() || sup_it->second.empty())
            sup_it = class_to_superclass_.find(class_descriptor);
        if (!r14_off && sup_it != class_to_superclass_.end() &&
            !sup_it->second.empty()) {
            const std::string super_desc = sup_it->second;
            // App-DEX superclasses only: framework namespaces keep the
            // platform-skip (their statics ride the shadow/bridge layer).
            static const char* f_skip[] = {"Landroid/", "Ljava/", "Ljavax/"};
            bool fns = false;
            for (const char* p : f_skip)
                if (super_desc.compare(0, strlen(p), p) == 0) { fns = true; break; }
            if (!fns) {
                static thread_local int r14_depth = 0;
                if (r14_depth < 24) {  // bounded: never deeper than a real chain
                    r14_depth++;
                    ensure_class_initialized(super_desc);
                    r14_depth--;
                }
            }
        }
    }
    // Framework classes — skip <clinit> (they're stubbed).
    // The shadow registry / bridge_to_api handles their static fields.
    //
    // M3 FINDING-013 (provenance law, 2026-09-08): the OLD blanket skip of
    // Landroidx/ Lkotlin/ Lkotlinx/ Lcom/google/ Lj$/ was a NAMESPACE-based
    // decision. In a real R8-built APK those namespaces are APP-BUNDLED
    // REAL bytecode (androidx is a library shipped inside the APK — it is
    // NOT platform stubs). Consequence: every androidx enum/static read
    // via sget returned null — dooz's LifecycleRegistry.addObserver read
    // Lifecycle.State.DESTROYED/INITIALIZED as null, handed the null to
    // Kotlin Intrinsics.throwNpe, whose Thread.getStackTrace() skip-walk
    // then ran off the end of the synthetic trace array (aget AIOOBE),
    // and the swallowed exception cascade ended in the
    // "android:support:activity-result" IAE + a 100% white frame.
    // LAW (AOSP ClassLinker::EnsureInitialized): initialization is decided
    // by WHERE THE BYTECODE LIVES, not by package name — a class present
    // in the app DexReport runs its own <clinit>; only classes ABSENT from
    // it (resolved to runtime stubs/shadows) skip <clinit>.
    // Landroid/* stays an unconditional skip: app-bundled platform-namespace
    // copies must never shadow framework semantics (G12 parent-delegation
    // law, FIND-G09-ACF-001).
    // S123 (R-NEW-421) — APP-BUNDLED LIBRARY NAMESPACE EXCEPTION: the
    // Landroid/support/** and Landroid/arch/** trees are APP-BUNDLED
    // LIBRARY bytecode in every real APK (support-v4/v7/v13, architecture
    // components) — NOT platform stubs. The unconditional skip marked
    // them initialized without running their <clinit>, so support statics
    // (ContainerHelpers.EMPTY_INTS/EMPTY_OBJECTS — the backing arrays of
    // every SimpleArrayMap; ProcessMyEventKeeper log) read back null and
    // the first SimpleArrayMap.put died in System.arraycopy(null)
    // (flappycow Game.onCreate → BaseGameActivity.onCreate →
    // GoogleApiClient.Builder NPE evidence, view root never set). LAW
    // (AOSP ClassLinker, same as M3 FINDING-013): initialization is
    // decided by WHERE THE BYTECODE LIVES — when the class exists in the
    // app DexReport, run its own <clinit>; only ABSENT android.* classes
    // keep the platform-skip.
    const bool app_library_ns =
        normalized.rfind("Landroid/support/", 0) == 0 ||
        normalized.rfind("Landroid/arch/", 0) == 0 ||
        normalized.rfind("Landroid/databinding/", 0) == 0;
    {
        bool in_app_dex = class_info_index_.find(class_descriptor) !=
                              class_info_index_.end() ||
                          class_info_index_.find(normalized) !=
                              class_info_index_.end();
        if (!in_app_dex &&
            (normalized.rfind("Landroid/", 0) == 0 ||
             normalized.rfind("Landroidx/", 0) == 0 ||
             normalized.rfind("Ljava/", 0) == 0 ||
             normalized.rfind("Lkotlin/", 0) == 0 ||
             normalized.rfind("Lkotlinx/", 0) == 0 ||
             normalized.rfind("Lcom/google/", 0) == 0 ||
             normalized.rfind("Lj$/", 0) == 0)) {
            phase_clock().ci_skipfw.fetch_add(1, std::memory_order_relaxed);
            initialized_classes_.insert(normalized);
            initialized_classes_.insert(class_descriptor);
            return true;
        }
        if (normalized.rfind("Landroid/", 0) == 0 && !app_library_ns) {
            // Platform namespace is never initialized from app bytecode,
            // even when an app-bundled copy exists in the DexReport.
            initialized_classes_.insert(normalized);
            initialized_classes_.insert(class_descriptor);
            return true;
        }
        // S123 (R-NEW-421b): an app-library-namespace class that is NOT in
        // the app DEX (e.g. a support class that R8 stripped) keeps the
        // platform-skip semantics — mark and return without clinit.
        if (app_library_ns && !in_app_dex) {
            phase_clock().ci_skipfw.fetch_add(1, std::memory_order_relaxed);
            initialized_classes_.insert(normalized);
            initialized_classes_.insert(class_descriptor);
            return true;
        }
    }
    // DEMO-CLINIT (2026-09-04): run <clinit> for EVERY application class,
    // not only org.telegram/*. Per AOSP jvm.cc ClassLinker::EnsureInitialized
    // semantics, class initialization happens on first ACTIVE USE of any
    // class with a <clinit>. The old org.telegram-only gate (EXP-053/EXP-054)
    // left every other app's static fields uninitialized: static final
    // constants built in <clinit> (int[] palettes, string tables, singletons)
    // read back as null/0 and silently broke app logic (first observed with
    // the miniandroid-demo APK: COLORS[]/COLOR_NAMES[] were null because
    // com.miniandroid.demo.MainActivity.<clinit> never ran).
    // Deep-recursion protection remains:
    //   * framework/lib namespaces above are still skipped entirely,
    //   * the class is marked initialized BEFORE <clinit> runs (re-entrancy
    //     guard below prevents cycles A->B->A),
    //   * execution_guard still bounds interpreter steps per method.
    // Need DexReport to find the class.
    if (!dex_report_) {
        // CONT-38 decode diag (env-gated, bounded): which class got
        // POISON-marked initialized without its <clinit> running.
        {
            static thread_local const bool cpt_on =
                diag_env("MINIANDROID_CLINIT_PATH_TRACE");
            static thread_local uint64_t cpt_n = 0;
            if (cpt_on && cpt_n++ < 40)
                std::cerr << "[CLINIT-PATH] NO-DEX-REPORT poison class="
                          << class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
        }
        initialized_classes_.insert(class_descriptor);
        return false;
    }
    // Find the class in the DexReport.
    auto class_it = class_info_index_.find(class_descriptor);
    if (class_it == class_info_index_.end()) {
        // CONT-38 decode diag: the LOOKUP-MISS poison path.
        {
            static thread_local const bool cpt2_on =
                diag_env("MINIANDROID_CLINIT_PATH_TRACE");
            static thread_local uint64_t cpt2_n = 0;
            if (cpt2_on && cpt2_n++ < 40)
                std::cerr << "[CLINIT-PATH] LOOKUP-MISS poison class="
                          << class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
        }
        // EXP-062: Debug — trace R class lookups
        if (class_descriptor.find("R$") != std::string::npos) {
            std::cerr << "[EXP062-RLOOKUP] " << class_descriptor
                      << " NOT FOUND in class_info_index_ (size="
                      << class_info_index_.size() << ")"
                      << std::endl;
        }
        initialized_classes_.insert(class_descriptor);
        return false;
    }
    const dex::ClassInfo& cls_ref = dex_report_->classes[class_it->second];
    // Mark initialized BEFORE running <clinit> to prevent re-entrancy.
    initialized_classes_.insert(class_descriptor);
    struct F107InitDepth { ~F107InitDepth() { f107_init_depth().fetch_sub(1); } } f107_idg;
    f107_init_depth().fetch_add(1);

    // EXP-062: Count fields with defaults for this class
    {
        int with_defaults = 0;
        for (const auto& f : cls_ref.static_fields) {
            if (f.has_default_value) with_defaults++;
        }
        if (with_defaults > 0 || class_descriptor.find("R$") != std::string::npos) {
            std::cerr << "[EXP062-INIT] " << class_descriptor
                      << " static_fields=" << cls_ref.static_fields.size()
                      << " with_defaults=" << with_defaults
                      << std::endl;
        }
    }

    // EXP-063: R-class resid harvest (CONT-48 F1: extracted to the standalone
    // harvest_r_class_fields helper — also called EAGERLY from
    // eager_harvest_r_classes() before the ARSC drawable census).
    harvest_r_class_fields(class_descriptor, cls_ref);

    // EXP-062: Initialize static fields from DEX encoded_array_item
    // (default values). This is critical for R classes (R$drawable,
    // R$string, R$color) which have NO <clinit> — their field values
    // are baked into the DEX by the build system as default values.
    // EXP-063: Don't overwrite values already set by pre-population
    // (e.g., ApplicationLoader.applicationContext is set before execution).
    // But DO overwrite if the existing value is the default 0 (from a
    // previous SGET that found no stored value).
    for (const auto& field : cls_ref.static_fields) {
        if (!field.has_default_value) continue;
        std::string static_key = class_descriptor + "." + field.name;
        auto it = static_field_storage_.find(static_key);
        if (it != static_field_storage_.end()) {
            // Only skip if the value is non-zero (pre-populated)
            if (it->second.type == DalvikType::INT32 && it->second.int_val != 0) {
                continue;
            }
            if (it->second.type != DalvikType::INT32) {
                continue;  // Non-int values (objects, strings) — don't overwrite
            }
            // int_val == 0: this is a default, overwrite with DEX default
        }
        if (field.default_value_is_string) {
            DalvikValue sv = DalvikValue::make_string(field.default_string_value, 0);
            static_field_storage_[static_key] = sv;
        } else if (field.default_value_has_float_bits) {
            // F-028f: VALUE_FLOAT (right-zero-extended to 32 bits) and
            // VALUE_DOUBLE (right-zero-extended to 64 bits). The float
            // case keeps the width-nibble padding law: the stored value is
            // the low 32 bits reinterpreted as IEEE-754.
            DalvikValue fv;
            if (field.default_float_width == 8) {
                fv.type = DalvikType::FLOAT64;
                int64_t bits = field.default_float_bits;
                std::memcpy(&fv.double_val, &bits, sizeof(bits));
            } else {
                fv.type = DalvikType::FLOAT32;
                uint32_t fbits = static_cast<uint32_t>(
                    static_cast<uint64_t>(field.default_float_bits) & 0xffffffffu);
                std::memcpy(&fv.float_val, &fbits, sizeof(fbits));
            }
            static_field_storage_[static_key] = fv;
        } else if (field.type == "J") {
            // F-042 (MASTER-6 §C) — VALUE_LONG static-default law: a static
            // long field's default materializes as a FULL 64-bit INT64
            // value; the declared descriptor (J) decides the width, not the
            // encoded-value size nibble. Previously every long static
            // default was truncated to INT32 (the dooz/fixture ScatterMap
            // EMPTY marker 0x8080808080808080 read back 0x80808080).
            static_field_storage_[static_key] =
                DalvikValue::make_long(field.default_int_value);
        } else {
            static_field_storage_[static_key] = DalvikValue::make_int(
                static_cast<int32_t>(field.default_int_value));
        }
    }

    // Find the <clinit> method.
    for (const auto& m : cls_ref.direct_methods) {
        if (m.name != "<clinit>") continue;
        if (m.bytecode.empty()) continue;
        std::cerr << "[CLASS_INIT] class=" << class_descriptor
                  << " method=<clinit>"
                  << " bytecode_size=" << m.bytecode.size()
                  << std::endl;
        DalvikValue dummy_return;
        {
            DalvikExecutionResult diag_result;
            bool ok_diag = try_recursive_invoke(
                class_descriptor,
                "<clinit>",
                /*args=*/{},
                dummy_return,
                diag_result
            );
            // F-NEW-395 CLINIT-UNWIND HONESTY LAW (CONT-87, fixture-first):
            // try_recursive_invoke's post-invoke EXC-PROPAGATE consumes the
            // in-flight unwind and dispatches it at the active-use frame, and
            // its mid-stack propagation returns TRUE — correct for a normal
            // callee, but the <clinit> consumer must NEVER report success for
            // a run that ended with an exception unwinding OUT of the clinit
            // frame. The unwind now leaves an unambiguous diag marker (see
            // the F-NEW-395 UNWIND-HONESTY LAW at the execute_method_internal
            // finalization: COMPLETED_PARTIAL + halt_reason="unwind <type>").
            // Pre-fix live evidence (run/cont87/clinit_pre.stderr, binary
            // d22b36be55764348): a clinit whose deferred raise escaped
            // recorded [CLASS_INIT] result=OK, the class stayed poison-marked
            // initialized, the erroneous-class law (F-NEW-215) never armed,
            // and the raw exception "teleported" to a LATER invoke site
            // (AndStatus2048's CNFE surfaced inside MyMainActivity.onCreate
            // at a confusing pc instead of the class's first active use).
            // JVMS 5.5: a <clinit> that throws leaves the class ERRONEOUS.
            // The deferred-raise unwind now flows through the SAME registered
            // active-use law (F-NEW-215 NCDFE at sget/sput/new-instance/
            // forName) instead of bypassing it. Named residual (honest):
            // JVMS 5.5 wraps a non-Error clinit throw in
            // ExceptionInInitializerError on first use; this engine's
            // registered active-use answer is NoClassDefFoundError with the
            // original type preserved in the failure evidence.
            // ── CONT-125 (F-NEW-470): STALE-UNWIND CLINIT ATTRIBUTION LAW ──
            // JVMS 5.5 marks a class ERRONEOUS only when its OWN <clinit>
            // bytecode throws. An in-flight unwind that was already
            // propagating through an OUTER frame when the lazy init was
            // triggered belongs to that outer stack — it must not fail a
            // clinit whose own body completed. Snapshot the in-flight state
            // at entry and attribute the unwind to the clinit only when it
            // is NEW (entry had no in-flight unwind, or the exit unwind is a
            // different exception than the entry one).
            // Live face (tictactoe v3, binary 6bb7150a): SharedLibraryLoader
            // load faulted (GATEA-NATIVE FIX-TTT kept the runtime alive) and
            // libGDX wrapped it in GdxRuntimeException mid-unwind; the lazy
            // AndroidApplication.<clinit> (2-instruction body) was triggered
            // during that unwind; the stale marker flowed into diag_result,
            // F-NEW-395 CLINIT-UNWIND marked the class ERRONEOUS, the
            // invoke-super AndroidApplication.onCreate dispatch was refused,
            // Gdx.app stayed null, and AndroidLauncher.onCreate died on the
            // Gdx.app.log NPE (two APP-BOUNDARY unwinds). On ART the class
            // initializes fine — the app reaches initializeForView.
            const bool f470_unwind_valid_at_entry = frame_unwind_exception_valid_;
            const uint32_t f470_unwind_obj_at_entry =
                frame_unwind_exception_.object_id;
            if (ok_diag &&
                diag_result.halt_reason.rfind("unwind ", 0) == 0 &&
                (!f470_unwind_valid_at_entry ||
                 frame_unwind_exception_.object_id !=
                     f470_unwind_obj_at_entry)) {
                std::cerr << "[F-NEW-395] CLINIT-UNWIND class="
                          << class_descriptor
                          << " in-flight=" << diag_result.halt_reason
                          << " → erroneous (F-NEW-215 law)"
                          << std::endl;
                ok_diag = false;
            }
            // S123 CLINIT-DIAG: surface WHY a clinit failed (no silent aborts).
            std::cerr << "[CLASS_INIT] class=" << class_descriptor
                      << " method=<clinit>"
                      << " result=" << (ok_diag ? "OK" : "FAILED")
                      << " engine=" << (const void*)this
                      << " storage_size=" << static_field_storage_.size();
            if (!ok_diag) {
                std::cerr << " diag_final_status=" << static_cast<int>(diag_result.final_status)
                          << " diag_halt_reason=" << diag_result.halt_reason;
                if (!diag_result.uncaught_in_flight_log.empty()) {
                    std::cerr << " diag_uncaught0="
                              << diag_result.uncaught_in_flight_log.front();
                }
            }
            std::cerr << std::endl;
            if (!ok_diag) {
                // F-NEW-215 CLASS-INIT HONESTY LAW (JVMS 5.5 / AOSP
                // ClassLinker::EnsureInitialized): a <clinit> that threw
                // leaves the class ERRONEOUS — never silently INITIALIZED.
                // Record the first divergence and answer honestly; the
                // class is NOT erased from initialized_classes_ (erroneous
                // persists — <clinit> is never re-run), but every later
                // active use observes the failure via class_clinit_failed()
                // (NoClassDefFoundError at sget/sput/new-instance/forName).
                std::string f215_ev = diag_result.halt_reason;
                if (!diag_result.uncaught_in_flight_log.empty()) {
                    std::string f215_u0 =
                        diag_result.uncaught_in_flight_log.front();
                    if (f215_u0.size() > 120) f215_u0 = f215_u0.substr(0, 120);
                    f215_ev += " uncaught0=" + f215_u0;
                }
                if (f215_ev.size() > 200) f215_ev = f215_ev.substr(0, 200);
                // F-NEW-215 evidence honesty: distinguish "clinit THREW"
                // (failure evidence present) from "clinit never produced
                // evidence" (bridge bypass / lookup miss — the statics are
                // equally missing, but the forensics differ).
                if (diag_result.final_status ==
                        DalvikExecutionResult::FinalStatus::COMPLETED_SUCCESS &&
                    diag_result.halt_reason.empty() &&
                    diag_result.uncaught_in_flight_log.empty()) {
                    f215_ev = "clinit-not-run-no-evidence (bypass/lookup miss)";
                }
                failed_clinit_classes_[class_descriptor] = f215_ev;
                failed_clinit_classes_[normalized] = f215_ev;
                std::cerr << "[F-NEW-215] CLINIT-FAILED class="
                          << class_descriptor << " evidence=" << f215_ev
                          << std::endl;
                return false;
            }
        }
        break;
    }
    return true;
}

// ─── FINAL CANONICAL MASTER RECONCILIATION Pass-3 helpers (K-34/K-35) ──────
namespace {
// Basic XML entity unescape for the pull parser's TEXT/attribute values
// (the five predefined entities + small numeric character references).
std::string xml_unescape_pass3(const std::string& in) {
    std::string out;
    out.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        if (in[i] == '&') {
            size_t semi = in.find(';', i + 1);
            if (semi != std::string::npos && semi - i <= 10) {
                std::string ent = in.substr(i + 1, semi - i - 1);
                if (ent == "lt")  { out += '<';  i = semi; continue; }
                if (ent == "gt")  { out += '>';  i = semi; continue; }
                if (ent == "amp") { out += '&';  i = semi; continue; }
                if (ent == "quot"){ out += '"';  i = semi; continue; }
                if (ent == "apos"){ out += '\''; i = semi; continue; }
                if (!ent.empty() && ent[0] == '#' && ent.size() >= 2) {
                    bool hex = (ent[1] == 'x' || ent[1] == 'X');
                    long cp = strtol(ent.c_str() + (hex ? 2 : 1), nullptr, hex ? 16 : 10);
                    if (cp > 0 && cp < 128) { out += static_cast<char>(cp); i = semi; continue; }
                }
            }
        }
        out += in[i];
    }
    return out;
}
}  // namespace

// ASSETS-WITHOUT-ARSC LAW — shared asset entry/byte resolution.
// AOSP AssetManager (AssetManager2 + ApkAssets) opens asset paths from the
// APK ZIP directly; resources.arsc is a RESOURCE-table concern and its
// absence must not make assets/ unreachable. ResourceRuntime::ensure_loaded
// legitimately fails for arsc-less APKs ("no resources.arsc"), so every
// asset lookup goes through these helpers: the runtime's cached parser when
// available, a direct APK parse otherwise (generic — no package
// conditionals).
std::vector<std::string> DalvikExecutionEngine::asset_entry_names(
    const std::string& prefix) {
    std::vector<std::string> out;
    if (apk_path_.empty()) return out;
    if (resources::ResourceRuntime::instance().ensure_loaded(apk_path_)) {
        for (const auto& ze :
             resources::ResourceRuntime::instance().apk().list_entries_cached(prefix)) {
            out.push_back(ze.name);
        }
        return out;
    }
    miniandroid::apk::ApkParser fallback;
    for (const auto& ze : fallback.list_entries(apk_path_)) {
        out.push_back(ze.name);
    }
    return out;
}

std::vector<uint8_t> DalvikExecutionEngine::asset_entry_bytes(
    const std::string& entry) {
    if (apk_path_.empty()) return {};
    if (resources::ResourceRuntime::instance().ensure_loaded(apk_path_)) {
        return resources::ResourceRuntime::instance().apk().extract_entry_cached(entry);
    }
    miniandroid::apk::ApkParser fallback;
    return fallback.extract_entry(apk_path_, entry);
}

// Pass-3 (K-34): resolve an open asset stream chain to path + position.
// Same wrapper hops the readLine block always used (BufferedReader.in →
// InputStreamReader.source → InputStream), factored out so InputStream
// read()/available()/close() share ONE real implementation.
bool DalvikExecutionEngine::resolve_asset_stream(uint32_t start_id,
                                                 std::string& path,
                                                 size_t*& pos) {
    uint32_t lookup_id = start_id;
    for (int hop = 0; hop < 4 && lookup_id != 0; ++hop) {
        auto it = open_assets_.find(lookup_id);
        if (it != open_assets_.end()) {
            path = it->second.first;
            pos = &it->second.second;
            return true;
        }
        if (heap_.has_object(lookup_id)) {
            const auto* ho = heap_.get(lookup_id);
            if (!ho) return false;
            uint32_t next_id = 0;
            for (const char* fn : {"in", "source", "inputStream", "reader", "is"}) {
                auto fv = ho->get_field(fn);
                if (fv.type == DalvikType::OBJECT_REF) { next_id = fv.object_id; break; }
            }
            if (next_id == 0 || next_id == lookup_id) return false;
            lookup_id = next_id;
        } else {
            return false;
        }
    }
    return false;
}

// Pass-3 (K-34): asset bytes extracted once per path, then cached.
// F-104 (S58): "file:<abs>" keys serve SANDBOX file bytes (one disk read,
// cached; 4 MiB bound with an honest diagnostic on oversize) — the
// FileInputStream/FileReader ctor law registers those keys.
const std::string& DalvikExecutionEngine::cached_asset_bytes(const std::string& path) {
    // ── CODER7 WAVE-6: LIVE file: observability law ─────────────────────
    // AOSP FileInputStream semantics: every read() observes the file's
    // CURRENT bytes — content written by another stream in the same
    // process is fully visible once that stream closes (the WAVE-6 store
    // probe's handshake channel depends on it: the main app reads what
    // the foreign components' real bytecode appended AFTER the first
    // read primed the cache). APK/asset entries are runtime-immutable —
    // those keys keep the insert-once cache. The freshness check is
    // structural: (file size, mtime) changed ⇒ re-read.
    auto c7_it = asset_bytes_cache_.find(path);
    if (c7_it != asset_bytes_cache_.end()) {
        if (path.rfind("file:", 0) != 0) return c7_it->second;
        namespace lfs = std::filesystem;
        lfs::path c7_fp(path.substr(5));
        std::error_code c7_ec;
        auto c7_sz = lfs::file_size(c7_fp, c7_ec);
        auto c7_lt = lfs::last_write_time(c7_fp, c7_ec);
        auto c7_fit = asset_file_stamp_.find(path);
        bool c7_same = !c7_ec &&
                       c7_fit != asset_file_stamp_.end() &&
                       c7_fit->second.first == (long long)c7_sz &&
                       c7_fit->second.second ==
                           (long long)c7_lt.time_since_epoch().count();
        if (c7_same) return c7_it->second;
        asset_bytes_cache_.erase(c7_it);
        asset_file_stamp_.erase(path);
    }
    std::string content;
    if (path.rfind("file:", 0) == 0) {
        // LOADING-CAMPAIGN: the registered backing path is already the
        // path-law mapping (FileInputStream/openFileInput/openInputStream
        // resolved it) — read it REAL, whole. The old 4 MiB cap faked EOF
        // on larger app files (a silent fake-success); a 256 MiB honest
        // refusal replaces it (AOSP streams are uncapped; the refusal is
        // loud, never silent EOF).
        namespace lfs = std::filesystem;
        lfs::path fp(path.substr(5));
        std::error_code f104_ec;
        if (lfs::exists(fp, f104_ec) && !f104_ec) {
            static constexpr size_t kMaxHonestRead = 256u << 20;  // 256 MiB
            // LOADING-CAMPAIGN: character devices (AOSP exposes /dev/urandom
            // to apps — sepolicy appdomain urandom_device r_file_perms) have
            // no meaningful file_size; a bounded raw read serves them (an
            // infinite stream must never hang the assign() below).
            if (!lfs::is_regular_file(fp, f104_ec)) {
                std::ifstream in(fp, std::ios::binary);
                if (in) {
                    char devbuf[8192];
                    in.read(devbuf, sizeof(devbuf));
                    content.assign(devbuf, in.gcount());
                }
            } else {
            auto sz = lfs::file_size(fp, f104_ec);
            // R-NEW-549 (CONT-40): loud ledger for BIG honest reads — the
            // telegram +2.9GB envelope traced here (36 x malloc(120MB+1)
            // via bridge_to_api — the SAME file re-read 36x). One line per
            // assign >= 16MB: the path + the size, then the evidence chain
            // is complete.
            if (!f104_ec && sz >= (16u << 20)) {
                std::cerr << "[F104-BIGREAD] " << path << " size=" << sz
                          << " (bridge_to_api stream assign)" << std::endl;
            }
            if (!f104_ec && sz <= kMaxHonestRead) {
                std::ifstream in(fp, std::ios::binary);
                if (in)
                    content.assign(std::istreambuf_iterator<char>(in),
                                   std::istreambuf_iterator<char>());
            } else if (!f104_ec) {
                std::cerr << "[F104-READ] file exceeds " << kMaxHonestRead
                          << " bytes — read REFUSED (loud, not silent EOF): "
                          << path << std::endl;
            }
            }
        }
    } else if (!apk_path_.empty()) {
        // S102 LAW 2 (SERVICELOADER-APK-ENTRY): paths with the "apk-entry:"
        // prefix are ROOT ZIP entries (META-INF/services/…), NOT assets —
        // ServiceLoader/ClassLoader.getResources read the classpath, and
        // the classpath root of an APK is its own entry table (libcore:
        // ClassLoader.getResource walks the class path; for an APK that is
        // the APK's own entries). Without this prefix every META-INF
        // lookup wrongly hit "assets/META-INF/…" and answered empty.
        if (path.rfind("apk-entry:", 0) == 0) {
            const std::string entry = path.substr(strlen("apk-entry:"));
            auto bytes = asset_entry_bytes(entry);
            content.assign(bytes.begin(), bytes.end());
            if (content.empty()) {
                std::cerr << "[S102-APK-ENTRY] MISS " << entry
                          << " (honest empty — no fabrication)"
                          << std::endl;
            }
        } else if (path.rfind("apkfd:", 0) == 0) {
            // LOADING-CAMPAIGN (R-2 FIX): AssetFileDescriptor-backed stream —
            // key shape "apkfd:<offset>:<len>:<entry>"; serves the entry's
            // exact bytes (AOSP AFD over a stored entry reads offset/len
            // within base.apk; the extracted bytes are byte-identical).
            // Shape: apkfd:<offset>:<len>:<entry…>
            std::string spec = path.substr(strlen("apkfd:"));
            size_t c1 = spec.find(':');
            size_t c2 = (c1 == std::string::npos) ? std::string::npos
                                                  : spec.find(':', c1 + 1);
            if (c1 != std::string::npos && c2 != std::string::npos) {
                std::string entry = spec.substr(c2 + 1);
                auto bytes = asset_entry_bytes(entry);
                content.assign(bytes.begin(), bytes.end());
            }
        } else {
            // LOADING-CAMPAIGN (R-5 FIX): asset bytes are extracted from the
            // INSTALLED APK through the in-process ZIP parser — the
            // popen("unzip -p …") host-tool dependency (uncapped, injection-
            // prone, unprovenanced) is REMOVED. One byte source law: the
            // APK entry table.
            {
                auto bytes = asset_entry_bytes("assets/" + path);
                content.assign(bytes.begin(), bytes.end());
            }
        }
    }
    // CODER7 WAVE-6: record the (size, mtime) stamp for file: keys so the
    // next cached_asset_bytes call can detect a live change.
    if (path.rfind("file:", 0) == 0) {
        namespace lfs = std::filesystem;
        lfs::path c7_fp2(path.substr(5));
        std::error_code c7_ec2;
        auto c7_sz2 = lfs::file_size(c7_fp2, c7_ec2);
        auto c7_lt2 = lfs::last_write_time(c7_fp2, c7_ec2);
        if (!c7_ec2)
            asset_file_stamp_[path] = {(long long)c7_sz2,
                                       (long long)c7_lt2.time_since_epoch()
                                           .count()};
    }
    return asset_bytes_cache_.emplace(path, std::move(content)).first->second;
}

// LOADING-CAMPAIGN (ST-2 FIX): drain still-open write streams at run end.
// AOSP law: process death closes all streams; data written before death
// persists. Idempotent (called from the screenshot/finalize stage).
void DalvikExecutionEngine::flush_finalizers() {
    for (auto& [id, w] : open_writers_) {
        if (w.ever_opened && w.out.is_open()) {
            w.out.flush();
            w.out.close();
            w.ever_opened = false;
        }
    }
}

// 371-CLOSEOUT: binary-XML resource → text XML. The K-35 XmlPullParser
// event machine runs over TEXT; compiled @xml resources (res/xml/*.xml,
// e.g. androidx FileProvider's android.support.FILE_PROVIDER_PATHS paths
// file) are binary AXML. AOSP answers Resources.getXml(resid) with an
// XmlResourceParser over the DECODED document — this serializer is that
// decode hop: AXML chunk tree → escaped text XML, attribute order kept.
static std::string axml_attr_text(const resources::AxmlAttribute& a) {
    if (a.value.is_string()) return a.value.string_value;
    if (!a.raw_value.empty()) return a.raw_value;
    switch (a.value.type) {
        case resources::DataType::INT_BOOLEAN:
            return a.value.data != 0 ? "true" : "false";
        case resources::DataType::INT_DEC:
        case resources::DataType::INT_HEX:
        case resources::DataType::REFERENCE:
            return std::to_string(a.value.data);
        default:
            return std::to_string(a.value.data);
    }
}
static std::string xml_escape_text_371(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (char c : s) {
        switch (c) {
            case '&': out += "&amp;"; break;
            case '<': out += "&lt;"; break;
            case '>': out += "&gt;"; break;
            case '"': out += "&quot;"; break;
            default: out += c;
        }
    }
    return out;
}
static void axml_element_to_text(const resources::AxmlElement& el,
                                 std::string& out, int depth) {
    out.append(depth * 2, ' ');
    out += "<" + xml_escape_text_371(el.name);
    for (const auto& a : el.attributes) {
        out += "\n" + std::string((depth + 1) * 2, ' ') +
               xml_escape_text_371(a.name) + "=\"" +
               xml_escape_text_371(axml_attr_text(a)) + "\"";
    }
    if (el.children.empty() && el.cdata.empty()) {
        out += " />\n";
        return;
    }
    out += ">\n";
    if (!el.cdata.empty())
        out += xml_escape_text_371(el.cdata) + "\n";
    for (const auto& c : el.children) axml_element_to_text(c, out, depth + 1);
    out.append(depth * 2, ' ');
    out += "</" + xml_escape_text_371(el.name) + ">\n";
}
static std::string axml_bytes_to_text_371(const std::vector<uint8_t>& bytes) {
    resources::AxmlParser p;
    if (!p.parse(bytes) || !p.valid()) return std::string();
    std::string out;
    axml_element_to_text(p.root(), out, 0);
    return out;
}

// Pass-3 (K-35): REAL XmlPullParser event machine — one event per call.
// Progression: START_DOCUMENT → (misc-skip: whitespace/comments/PI/DOCTYPE)
// → START_TAG / TEXT / END_TAG … → END_DOCUMENT (terminal; next() after it
// throws XmlPullParserException at the call site). Self-closing tags queue
// exactly one END_TAG, mirroring KXml.
void DalvikExecutionEngine::xml_pull_advance(XmlPullState& st) {
    if (st.ended) return;
    const std::string& s = st.content;
    size_t i = st.pos;
    auto skip_misc = [&]() {
        for (;;) {
            while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
            if (i + 3 < s.size() && s.compare(i, 4, "<!--") == 0) {
                size_t e = s.find("-->", i + 4);
                i = (e == std::string::npos) ? s.size() : e + 3;
                continue;
            }
            if (i + 1 < s.size() && s[i] == '<' && s[i + 1] == '?') {
                size_t e = s.find("?>", i + 2);
                i = (e == std::string::npos) ? s.size() : e + 2;
                continue;
            }
            if (i + 8 < s.size() && s.compare(i, 9, "<![CDATA[") == 0) {
                size_t e = s.find("]]>", i + 9);
                i = (e == std::string::npos) ? s.size() : e + 3;
                continue;  // CDATA content is surfaced via nextToken(), skipped by next()
            }
            if (i + 1 < s.size() && s[i] == '<' && s[i + 1] == '!') {
                size_t e = s.find('>', i + 2);
                i = (e == std::string::npos) ? s.size() : e + 1;
                continue;
            }
            break;
        }
    };
    if (st.pending_end) {
        st.pending_end = false;
        st.event = 3;  // END_TAG
        st.cur_name = st.pending_end_name;
        st.cur_text.clear();
        st.attrs.clear();
        st.pos = i;
        return;
    }
    skip_misc();
    if (i >= s.size()) {
        st.event = 1;  // END_DOCUMENT
        st.ended = true;
        st.cur_name.clear();
        st.cur_text.clear();
        st.attrs.clear();
        st.pos = i;
        return;
    }
    if (s[i] == '<') {
        if (i + 1 < s.size() && s[i + 1] == '/') {
            size_t e = s.find('>', i);
            st.cur_name = (e == std::string::npos) ? s.substr(i + 2)
                                                    : s.substr(i + 2, e - i - 2);
            while (!st.cur_name.empty() &&
                   std::isspace(static_cast<unsigned char>(st.cur_name.back())))
                st.cur_name.pop_back();
            st.event = 3;  // END_TAG
            st.cur_text.clear();
            st.attrs.clear();
            i = (e == std::string::npos) ? s.size() : e + 1;
        } else {
            size_t e = s.find('>', i);
            if (e == std::string::npos) {
                st.event = 1;  // malformed document → terminate
                st.ended = true;
                st.pos = s.size();
                return;
            }
            std::string inner = s.substr(i + 1, e - i - 1);
            bool self_close = false;
            while (!inner.empty() && std::isspace(static_cast<unsigned char>(inner.back())))
                inner.pop_back();
            if (!inner.empty() && inner.back() == '/') { self_close = true; inner.pop_back(); }
            size_t k = 0;
            while (k < inner.size() && !std::isspace(static_cast<unsigned char>(inner[k])) &&
                   inner[k] != '=')
                ++k;
            st.cur_name = inner.substr(0, k);
            st.attrs.clear();
            while (k < inner.size()) {
                while (k < inner.size() && std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                size_t n0 = k;
                while (k < inner.size() && inner[k] != '=' &&
                       !std::isspace(static_cast<unsigned char>(inner[k])))
                    ++k;
                if (k == n0) break;
                std::string aname = inner.substr(n0, k - n0);
                while (k < inner.size() && std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                std::string aval;
                if (k < inner.size() && inner[k] == '=') {
                    ++k;
                    while (k < inner.size() && std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                    if (k < inner.size() && (inner[k] == '"' || inner[k] == '\'')) {
                        char q = inner[k++];
                        size_t v0 = k;
                        while (k < inner.size() && inner[k] != q) ++k;
                        aval = inner.substr(v0, k - v0);
                        if (k < inner.size()) ++k;
                    } else {
                        size_t v0 = k;
                        while (k < inner.size() && !std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                        aval = inner.substr(v0, k - v0);
                    }
                }
                st.attrs.emplace_back(aname, xml_unescape_pass3(aval));
            }
            st.event = 2;  // START_TAG
            // ── F-CSW-3 (S226; #376) Xml.asAttributeSet install hop ──────
            // Each START_TAG publishes the tag's TYPED attribute records
            // under the parser object id (document-order match: the text
            // events and the typed sequence derive from the same AXML
            // tree). Self-closing tags publish once here and queue their
            // END_TAG — identical consumption to KXml.
            if (st.owner_obj != 0 &&
                st.tag_attrs_pos < st.tag_attrs_seq.size()) {
                resources::AttributeSetStore::instance().install(
                    st.owner_obj, st.tag_attrs_seq[st.tag_attrs_pos]);
                ++st.tag_attrs_pos;
            }
            st.cur_text.clear();
            if (self_close) {
                st.pending_end = true;
                st.pending_end_name = st.cur_name;
            }
            i = e + 1;
        }
        st.pos = i;
        return;
    }
    // TEXT: characters up to the next '<' (or EOF).
    size_t e2 = s.find('<', i);
    std::string raw = (e2 == std::string::npos) ? s.substr(i) : s.substr(i, e2 - i);
    st.cur_text = xml_unescape_pass3(raw);
    st.cur_name.clear();
    st.attrs.clear();
    st.event = 4;  // TEXT
    st.pos = (e2 == std::string::npos) ? s.size() : e2;
}

// 371-CLOSEOUT: PackageManager.getXml(resid) / ProviderInfo.loadXmlMetaData
// shared hop (AOSP ResourcesImpl.getXml law): resource id → ARSC file
// selection → APK ZIP entry bytes → binary-XML decode → REAL K-35
// XmlPullParser over the decoded document. Returns false when the id does
// not resolve to an XML entry (call sites then answer their own AOSP
// failure shapes; never a silent fake parser).
bool DalvikExecutionEngine::xml_parser_for_resid(uint32_t resid,
                                                 DalvikValue& result) {
    auto& rt = resources::ResourceRuntime::instance();
    std::vector<uint8_t> bytes;
    std::string entry;
    if (rt.ensure_loaded(apk_path_)) {
        std::vector<std::string> apk_paths;
        for (const auto& ze : rt.apk().list_entries_cached("res/"))
            apk_paths.push_back(ze.name);
        auto sel_file = rt.arsc().select_file(resid, apk_paths,
                                              resources::device_config());
        if (sel_file) entry = sel_file->path;
        if (entry.empty()) {
            auto sel = rt.arsc().apk_path_for(resid, apk_paths);
            if (sel) entry = *sel;
        }
        if (!entry.empty() && entry.find("res/") != 0) entry = "res/" + entry;
        if (!entry.empty()) bytes = rt.apk().extract_entry(apk_path_, entry);
    }
    if (bytes.empty()) return false;
    std::string text = axml_bytes_to_text_371(bytes);
    if (text.empty()) {
        // Non-binary XML: serve the raw entry bytes as the document
        // (AOSP getXml also accepts plain-text XML resources).
        text.assign(bytes.begin(), bytes.end());
    }
    uint32_t frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    uint32_t obj_id = heap_.allocate("Lorg/xmlpull/v1/XmlPullParser;", pc_,
                                     frame_id);
    xml_parsers_[obj_id] = XmlPullState{};
    xml_parsers_[obj_id].content = text;
    xml_parsers_[obj_id].event = 0;  // START_DOCUMENT
    // ── F-CSW-3 (S226; #376) Xml.asAttributeSet — typed attr records ────
    // Decode the binary AXML ONCE here and keep every element's TYPED
    // attribute records in document order. The text serialization above
    // (axml_bytes_to_text_371) feeds the K-35 event machine but destroys
    // the TypedValue types (everything becomes a decimal string) — the
    // androidx vector parser's TypedArray reads need the RAW types. At
    // every START_TAG xml_pull_advance installs the matching record set
    // into the AttributeSetStore under the parser object id (the AOSP
    // law: the parser IS the AttributeSet — Xml.asAttributeSet), so
    // obtainStyledAttributes(parser, styleable[]) resolves the XML stage
    // exactly as the view-ctor path does.
    {
        resources::AxmlParser ax;
        if (ax.parse(bytes) && ax.valid()) {
            std::function<void(const resources::AxmlElement&,
                               std::vector<std::vector<resources::XmlAttrRecord>>&)>
                collect = [&](const resources::AxmlElement& el,
                              std::vector<std::vector<resources::XmlAttrRecord>>&
                                  seq) {
                    std::vector<resources::XmlAttrRecord> recs;
                    recs.reserve(el.attributes.size());
                    for (const auto& a : el.attributes) {
                        resources::XmlAttrRecord r;
                        r.resid = a.attr_resid;
                        r.type = a.value.type;
                        r.data = (int32_t)a.value.data;
                        r.ref_id = a.value.ref_id;
                        r.str = a.value.is_string() ? a.value.string_value
                                                    : a.raw_value;
                        recs.push_back(std::move(r));
                    }
                    seq.push_back(std::move(recs));
                    for (const auto& c : el.children) collect(c, seq);
                };
            collect(ax.root(), xml_parsers_[obj_id].tag_attrs_seq);
            xml_parsers_[obj_id].owner_obj = obj_id;
            std::cerr << "[F-CSW-3] getXml typed attr seq: "
                      << xml_parsers_[obj_id].tag_attrs_seq.size()
                      << " tags, obj#" << obj_id << std::endl;
        }
    }
    miniandroid::diagnostics::FileIoTrace::instance().record(
        "OPEN", "apk-entry:" + entry, true, "getXml/loadXmlMetaData",
        current_class_ + "." + current_method_);
    result = DalvikValue::make_object(obj_id, "Lorg/xmlpull/v1/XmlPullParser;");
    std::cerr << "[371-XML] xml_parser_for_resid resid=0x" << std::hex << resid
              << std::dec << " -> " << entry << " (" << text.size()
              << " text bytes) obj#" << obj_id << std::endl;
    return true;
}

// EXP-038 (BLOCKER-034): Recursive DEX method invocation.
// Search the DEX for a method matching declaring_class + method_name.
// If found with bytecode, recursively execute it.

// ────────────────────────────────────────────────────────────────────────
// F-NEW-236d (fairymahjong F-235 probe face): APP-DEFINED EQUALITY LAW.
// OpenJDK HashSet.add/contains and ArrayList.contains classify elements
// by the ELEMENT'S OWN equals(Object). CollectionShadow stores element
// object ids and cannot see DEX bytecode, so its pre-F-236d equality was
// identity + string content only. The engine installs a resolver at
// set_shadow_registry time and answers with the app's own law:
//   1. identity (same heap id) → true — Object.equals contract;
//   2. the receiver class (or a reachable app ancestor) declaring
//      equals(Ljava/lang/Object;)Z with real bytecode → the app's own
//      code runs via try_recursive_invoke (receiver identity preserved;
//      try_recursive_invoke_on_super covers inherited overrides);
//   3. no reachable override → identity (framework Object law).
// Reentrancy: this runs nested exactly like any invoke-virtual dispatch
// (the same execute_method_internal save/restore applies); recursion is
// bounded by the engine's existing depth machinery.
// ────────────────────────────────────────────────────────────────────────
void DalvikExecutionEngine::install_collection_equality_law() {
    if (!shadow_registry_) return;
    auto* cs = shadow_registry_->find_as<framework::CollectionShadow>();
    if (!cs) return;
    cs->app_equals_slot() = [this](uint32_t a, uint32_t b) -> bool {
        return this->app_object_equals(a, b);
    };
    // ── LAW-C/E/F (CONT-18): DEX CALLABLE INVOCATION CHANNEL INSTALL ────
    // The Java-8 collection default-method law (removeIf/sort/forEach/
    // merge/computeIfAbsent) and the stream filter stage receive their
    // functional arguments as D8-desugared lambda objects — real DEX code.
    // The shadow cannot execute DEX code, so the engine (the only layer
    // that can) installs this invoker: it resolves the callee's runtime
    // class from the heap, converts the shadow args to DalvikValues
    // (receiver = callee identity first), and runs try_recursive_invoke.
    // ok=false = no DEX body resolved → the shadow law declines loudly
    // (never a faked result).
    cs->dex_invoke_slot() =
        [this](uint32_t callee, const std::string& method,
               const std::vector<framework::CallContext::Arg>& cargs)
        -> framework::CollectionShadow::DexCallOutcome {
        if (callee == 0 || !heap_.has_object(callee))
            return framework::CollectionShadow::DexCallOutcome::fail();
        const auto* obj = heap_.get(callee);
        if (!obj || obj->class_descriptor.empty())
            return framework::CollectionShadow::DexCallOutcome::fail();
        const std::string cls = obj->class_descriptor;
        std::vector<DalvikValue> dargs;
        dargs.push_back(DalvikValue::make_object(callee, cls));
        for (const auto& a : cargs) {
            switch (a.kind) {
                case framework::CallContext::Arg::Kind::INT:
                    dargs.push_back(DalvikValue::make_int(a.int_val));
                    break;
                case framework::CallContext::Arg::Kind::LONG:
                    dargs.push_back(DalvikValue::make_long(a.long_val));
                    break;
                case framework::CallContext::Arg::Kind::FLOAT:
                    dargs.push_back(DalvikValue::make_float(a.float_val));
                    break;
                case framework::CallContext::Arg::Kind::DOUBLE:
                    dargs.push_back(DalvikValue::make_double(a.double_val));
                    break;
                case framework::CallContext::Arg::Kind::BOOL:
                    dargs.push_back(DalvikValue::make_bool(a.bool_val));
                    break;
                case framework::CallContext::Arg::Kind::STRING:
                    dargs.push_back(DalvikValue::make_string(a.string_val, 0));
                    break;
                case framework::CallContext::Arg::Kind::OBJECT:
                    dargs.push_back(DalvikValue::make_object(
                        a.object_id,
                        a.object_class.empty()
                            ? (heap_.has_object(a.object_id)
                                   ? heap_.get(a.object_id)->class_descriptor
                                   : "Ljava/lang/Object;")
                            : a.object_class));
                    break;
                case framework::CallContext::Arg::Kind::NULL_REF:
                default:
                    dargs.push_back(DalvikValue::make_null());
                    break;
            }
        }
        DalvikValue ret;
        DalvikExecutionResult sub;
        if (!try_recursive_invoke(cls, method, dargs, ret, sub)) {
            if (!try_recursive_invoke_on_super(cls, method, dargs, ret, sub,
                                               "")) {
                return framework::CollectionShadow::DexCallOutcome::fail();
            }
        }
        namespace f = framework;
        using Out = f::CollectionShadow::DexCallOutcome;
        switch (ret.type) {
            case DalvikType::BOOLEAN:
                return Out::of_bool(ret.int_val != 0);
            case DalvikType::INT32:
                return Out::of_int(ret.int_val);
            case DalvikType::INT64:
                return Out::of_int(static_cast<int32_t>(ret.long_val));
            case DalvikType::OBJECT_REF:
                if (ret.object_id == 0) return Out::of_null();
                return Out::of_obj(
                    ret.object_id,
                    heap_.has_object(ret.object_id)
                        ? heap_.get(ret.object_id)->class_descriptor
                        : std::string("Ljava/lang/Object;"));
            case DalvikType::STRING_REF:
                return Out::of_str(ret.string_val);
            case DalvikType::FLOAT32:
            case DalvikType::FLOAT64:
            default:
                return Out::of_null();
        }
    };
}

bool DalvikExecutionEngine::app_object_equals(uint32_t a, uint32_t b) {
    if (a == b) return true;   // Object.equals identity contract
    if (a == 0 || b == 0) return false;
    if (!heap_.has_object(a) || !heap_.has_object(b)) return false;
    const auto* oa = heap_.get(a);
    if (!oa) return false;
    std::string cls = framework::normalize_class_desc(oa->class_descriptor);
    if (cls.empty() || cls == "Ljava/lang/Object;") return false;
    DalvikExecutionResult sub;
    DalvikValue ret;
    std::vector<DalvikValue> args;
    args.push_back(DalvikValue::make_object(a, cls));
    args.push_back(DalvikValue::make_object(b, "Ljava/lang/Object;"));
    if (try_recursive_invoke(cls, "equals", args, ret, sub,
                             "(Ljava/lang/Object;)Z")) {
        return ret.type == DalvikType::BOOLEAN ? ret.int_val != 0 : false;
    }
    if (try_recursive_invoke_on_super(cls, "equals", args, ret, sub,
                                      "(Ljava/lang/Object;)Z")) {
        return ret.type == DalvikType::BOOLEAN ? ret.int_val != 0 : false;
    }
    // No app-declared equals anywhere in the chain → identity law.
    return false;
}

// AOSP ActivityThread.performLaunchActivity fidelity: run the activity's
// DECLARED no-arg <init>()V right after heap allocation. Instance-field
// initializers compiled into <init> (`boolean auto = true;`) must be live
// before onCreate — on real Android the constructor runs before any
// lifecycle callback. No-op when the class declares no no-arg <init>
// (framework classes never reach here with app bytecode).
void DalvikExecutionEngine::run_activity_default_init(const std::string& cls,
                                                      uint32_t activity_obj_id,
                                                      DalvikExecutionResult& result) {
    try {
        DalvikValue this_val = DalvikValue::make_object(activity_obj_id, cls);
        DalvikValue init_ret;
        std::vector<DalvikValue> init_args;
        init_args.push_back(this_val);  // p0 = this
        bool ok = try_recursive_invoke(cls, "<init>", init_args, init_ret,
                                       result, "()V");
        if (ok) {
            log("✅ activity <init>()V executed (instance field initializers live before onCreate)");
        }
    } catch (const std::exception& e) {
        log(std::string("⚠️ activity <init> dispatch skipped: ") + e.what());
    }
    // ── F-NEW-169 (FINAL CAMPAIGN PHASE 4 — activity attach law) ────────
    // AOSP ActivityThread.performLaunchActivity: after newInstance (the
    // <init> above) and BEFORE onCreate, activity.attach(...) drives
    // attachBaseContext(base) — the VIRTUAL dispatch lands on the app's
    // override when one exists. The app-level attachBaseContext is the
    // canonical attach-time state setup point:
    //   • WhatsApp LX/0IH override = the DI members-injector (stores the
    //     lattice providers via LX/00C;.A02(slotId) into A01/A0H/A03/A0I/
    //     A0F/A0B). Without the attach step the fields stay NULL and
    //     onCreate reads them → NPE 'Map.get on null object reference'
    //     (0IH.onCreate pc=14) → Main.onCreate catch-all rethrow BEFORE
    //     super.onCreate → the FragmentManager host is never attached →
    //     the onResume/onStart ISE family ('FragmentManager has not been
    //     attached to a host.' / 'No activity') — the FULL cascade.
    //   • Chains without an override resolve up to the framework boundary
    //     (ContextWrapper.attachBaseContext — the F-NEW-166 base-context
    //     law serves it, recording mBase) — identical observable outcome
    //     to the previous shadow-state seeding.
    // Ordering law: <init> → attachBaseContext → [pre-created fan-out] →
    // onCreate. try_recursive_invoke=false = no override in the DEX chain
    // (framework boundary serves the contract) — honest no-op, not an
    // error.
    {
        DalvikValue athis =
            DalvikValue::make_object(activity_obj_id, cls);
        DalvikValue aret;
        std::vector<DalvikValue> attach_args;
        attach_args.push_back(athis);
        // F-NEW-184 base-context law: the engine's Context identity is the
        // bound object itself (the same convention the Application bind
        // uses) — never null.
        attach_args.push_back(athis);
        try {
            bool aok = try_recursive_invoke(cls, "attachBaseContext",
                                            attach_args, aret, result);
            if (!aok)
                aok = try_recursive_invoke_on_super(
                    cls, "attachBaseContext", attach_args, aret, result, "");
            // F-NEW-169 evidence: if the attach override was not reached,
            // dump the DEX superclass chain the climb walked (bounded 16)
            // so the resolution gap is NAMED, not guessed.
            if (!aok && diag_env("MINIANDROID_WAVEC_TRACE")) {
                std::cerr << "[WAVEC-ATTACH-CHAIN] " << cls << ":";
                std::string walk = cls;
                for (int hop = 0; hop < 16; ++hop) {
                    auto sit = class_to_superclass_.find(walk);
                    if (sit == class_to_superclass_.end()) {
                        std::cerr << " (no-super-for=" << walk << ")";
                        break;
                    }
                    walk = sit->second;
                    std::cerr << " -> " << walk;
                    if (walk.empty() || walk == "Ljava/lang/Object;") break;
                }
                std::cerr << std::endl;
            }
            // F-NEW-169 decisive evidence: read the DI fields the override
            // must have stored. If A0B is still null after a successful
            // dispatch, the attach died partway (its NPE is deferred).
            if (diag_env("MINIANDROID_WAVEC_TRACE")) {
                for (const char* fn : {"A0B", "A03", "A05"}) {
                    auto fv = heap_.get_object_field(activity_obj_id, fn);
                    std::cerr << "[WAVEC-ATTACH-FIELD] " << cls << " obj#"
                              << activity_obj_id << " " << fn << " = "
                              << (fv.has_value() ? dalvik_value_to_string(*fv)
                                                 : "<no-field>")
                              << std::endl;
                }
            }
            log(std::string("✅ F-NEW-169 activity attachBaseContext ") +
                (aok ? "executed (app override ran)"
                     : "not declared in DEX chain (framework boundary serves)"));
        } catch (const std::exception& e) {
            log(std::string("⚠️ activity attachBaseContext dispatch skipped: ") +
                e.what());
        }
    }
}

// ── R-NEW-341 (S40): AOSP handleBindApplication law ──────────────────────
// ActivityThread.handleBindApplication → LoadedApk.makeApplication →
//   instrumentation.newApplication(appClass) → app.<init>() →
//   app.attachBaseContext(appContext) → Instrumentation
//   .callApplicationOnCreate(app) → app.onCreate()
// ALL of it happens BEFORE any activity instantiation, and the resulting
// object is THE application identity for the whole process:
//   - Activity.getApplication() / getApplicationContext() return it,
//   - DI frameworks type-check it (Hilt: instanceof Application, then
// ── S-1 FIX (LOADING-CAMPAIGN) — installContentProviders stage ──────────
// AOSP ActivityThread.handleBindApplication order: providers are installed
// BEFORE Application.onCreate; androidx.startup.InitializationProvider,
// WorkManager/ProcessLifecycleOwner/Emoji2 initialize in that window.
// Law: instantiate each manifest <provider> class, run its onCreate()
// with REAL DEX execution; a class absent from the DEX is recorded and
// skipped loudly (honest platform-skip, never a fake provider); a throwing
// provider propagates exactly like app onCreate (AOSP kills the process;
// the engine records + continues, evidence honest).
void DalvikExecutionEngine::install_content_providers(
    DalvikExecutionResult& result) {
    if (manifest_providers_.empty()) return;
    for (const std::string& pcls : manifest_providers_) {
        // DEX-presence gate: normalized dotted → descriptor.
        std::string desc = pcls;
        if (!desc.empty() && desc[0] != 'L') {
            std::replace(desc.begin(), desc.end(), '.', '/');
            desc = "L" + desc + ";";
        }
        bool in_dex = class_to_superclass_.find(desc) != class_to_superclass_.end();
        if (!in_dex && dex_report_ != nullptr) {
            for (const auto& cd : dex_report_->classes) {
                if (cd.name == desc) { in_dex = true; break; }
            }
        }
        if (!in_dex) {
            std::cerr << "[S1-PROVIDER] SKIP " << pcls
                      << " (class absent from DEX — honest platform-skip)"
                      << std::endl;
            continue;
        }
        try {
            const uint32_t pid = heap_.allocate(desc, pc_, 0);
            if (pid == 0) continue;
            // CODER7 WAVE-8 L1: the OWN provider's read/write permission
            // identity (manifest android:readPermission/writePermission;
            // same-app access is exempt at the gate — AOSP same-uid law).
            for (const auto& c7_pp : manifest_provider_perms_)
                if (std::get<0>(c7_pp) == pcls) {
                    c7_set_provider_perms(pid, std::get<1>(c7_pp),
                                          std::get<2>(c7_pp), package_name_);
                    break;
                }
            DalvikValue pobj = DalvikValue::make_object(pid, desc);
            DalvikValue ret;
            std::vector<DalvikValue> pinit;
            pinit.push_back(pobj);
            try_recursive_invoke(desc, "<init>", pinit, ret, result, "()V");
            // GATE A (issue #370): AOSP ActivityThread.installProvider law —
            // attachInfo(context, info) runs BEFORE onCreate and binds
            // mContext + mInfo. The engine mirrors it: build a ProviderInfo
            // heap object (name + authority identity from the manifest) and
            // invoke the provider's attachInfo override (or the framework
            // default) with the bound application context.
            {
                uint32_t pinfo_id = heap_.allocate(
                    "Landroid/content/pm/ProviderInfo;", pc_, 0);
                heap_.set_object_field(pinfo_id, "name",
                                       DalvikValue::make_string(desc, 1));
                std::string auth;
                for (const auto& [pname, pauth] : manifest_provider_identity_) {
                    if (pname == pcls) { auth = pauth; break; }
                }
                heap_.set_object_field(pinfo_id, "authority",
                                       DalvikValue::make_string(auth, 1));
                heap_.set_object_field(pinfo_id, "authorities",
                                       DalvikValue::make_string(auth, 1));
                // #371: ProviderInfo.grantUriPermissions (AOSP
                // PackageParser law). androidx FileProvider.attachInfo
                // throws SecurityException when this is false — the seed
                // must reflect the REAL manifest value.
                bool grant_up = false;
                for (const auto& [gname, gval] : manifest_provider_grants_) {
                    if (gname == pcls) { grant_up = gval; break; }
                }
                heap_.set_object_field(pinfo_id, "grantUriPermissions",
                                       DalvikValue::make_bool(grant_up));
                // F-NEW-525: exported + multiprocess (AOSP PackageParser
                // ProviderInfo law — defaults FALSE, manifest value wins;
                // ShizukuProvider.attachInfo enforces exported=true /
                // multiprocess=false at attach). Unset previously read
                // 0 for exported too — the seed is drift-free for every
                // manifest that does not declare exported=true.
                for (const auto& [ename, eval] : manifest_provider_exported_) {
                    if (ename == pcls) {
                        heap_.set_object_field(
                            pinfo_id, "exported",
                            DalvikValue::make_bool(eval));
                        break;
                    }
                }
                heap_.set_object_field(
                    pinfo_id, "multiprocess",
                    DalvikValue::make_bool(false));
                // 371-CLOSEOUT: ProviderInfo.metaData (AOSP PackageParser
                // law — component <meta-data> children become the Bundle;
                // android:resource refs land as the RESOLVED resource id
                // int, value entries as typed ints/strings). androidx
                // FileProvider.attachInfo → parsePathStrategy reads
                // metaData.getInt("android.support.FILE_PROVIDER_PATHS")
                // via loadXmlMetaData; a missing metaData bundle answers
                // null there and every FileProvider app died at install.
                auto md_it = component_meta_data_.find(pcls);
                if (md_it == component_meta_data_.end() && !pcls.empty()) {
                    // descriptor→dotted fallback (manifest keys are dotted).
                    std::string bare = pcls;
                    std::replace(bare.begin(), bare.end(), '/', '.');
                    if (bare.size() > 2 && bare.front() == 'L' && bare.back() == ';')
                        bare = bare.substr(1, bare.size() - 2);
                    md_it = component_meta_data_.find(bare);
                }
                if (md_it != component_meta_data_.end() && !md_it->second.empty()) {
                    uint32_t md_bundle = heap_.allocate("Landroid/os/Bundle;",
                                                        pc_, 0);
                    static const std::string kDigits = "0123456789";
                    for (const auto& mde : md_it->second) {
                        if (mde.has_resource && mde.resource_id != 0) {
                            heap_.set_object_field(
                                md_bundle, "bundle:" + mde.name,
                                DalvikValue::make_int(
                                    static_cast<int32_t>(mde.resource_id)));
                        } else if (!mde.value.empty() &&
                                   mde.value.find_first_not_of(kDigits) ==
                                       std::string::npos) {
                            heap_.set_object_field(
                                md_bundle, "bundle:" + mde.name,
                                DalvikValue::make_int(std::stoi(mde.value)));
                        } else if (!mde.value.empty()) {
                            heap_.set_object_field(
                                md_bundle, "bundle:" + mde.name,
                                DalvikValue::make_string(mde.value, 0));
                        }
                    }
                    heap_.set_object_field(
                        pinfo_id, "metaData",
                        DalvikValue::make_object(md_bundle,
                                                 "Landroid/os/Bundle;"));
                    std::cerr << "[371-MD] ProviderInfo " << pcls
                              << " metaData entries="
                              << md_it->second.size() << std::endl;
                }
                DalvikValue pinfo;
                pinfo.type = DalvikType::OBJECT_REF;
                pinfo.object_id = pinfo_id;
                pinfo.class_desc = "Landroid/content/pm/ProviderInfo;";
                uint32_t ctx_id = application_object_id_;
                DalvikValue ctx_obj;
                if (ctx_id != 0 && heap_.has_object(ctx_id)) {
                    ctx_obj.type = DalvikType::OBJECT_REF;
                    ctx_obj.object_id = ctx_id;
                    ctx_obj.class_desc = application_class_desc_.empty()
                                             ? "Landroid/app/Application;"
                                             : application_class_desc_;
                } else {
                    ctx_obj = get_or_create_singleton("Landroid/content/Context;");
                }
                std::vector<DalvikValue> pattach{pobj, ctx_obj, pinfo};
                try_recursive_invoke(desc, "attachInfo", pattach, ret, result,
                                     "(Landroid/content/Context;"
                                     "Landroid/content/pm/ProviderInfo;)V");
                provider_context_[pid] = ctx_obj.object_id;
                // ── #371 PHASE B1: authority→provider dispatch map ──
                // AOSP law: ContentResolver.acquireProvider resolves a
                // content URI authority through the PMS provider map that
                // installContentProviders populates. Authorities are
                // ';'-joined in ProviderInfo — each spelling maps to the
                // SAME installed provider instance.
                for (const auto& [pname, pauth] : manifest_provider_identity_) {
                    if (pname != pcls) continue;
                    const std::string& auth_all = pauth;
                    size_t start = 0;
                    while (start <= auth_all.size()) {
                        size_t semi = auth_all.find(';', start);
                        std::string one = auth_all.substr(
                            start, semi == std::string::npos
                                       ? std::string::npos
                                       : semi - start);
                        if (!one.empty()) {
                            provider_by_authority_[one] = pid;
                            provider_class_by_oid_[pid] = pcls;
                        }
                        if (semi == std::string::npos) break;
                        start = semi + 1;
                    }
                    break;
                }
            }
            // ContentProvider.onCreate() — the init hook (attachInfo is
            // framework-internal in AOSP; onCreate carries the app init).
            std::vector<DalvikValue> pcreate;
            pcreate.push_back(pobj);
            bool ok = try_recursive_invoke(desc, "onCreate", pcreate, ret,
                                           result, "()Z");
            std::cerr << "[S1-PROVIDER] installed " << pcls
                      << " obj#" << pid << " attachInfo+onCreate "
                      << (ok ? "OK" : "SKIPPED") << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[S1-PROVIDER] " << pcls
                      << " threw (recorded, install continues): "
                      << e.what() << std::endl;
        }
    }
}

// ────────────────────────────────────────────────────────────────────────
// #371 PHASE B1/B5 helpers: content-URI parsing, provider resolution,
// provider/lifecycle invocation, Uri object construction.
// ────────────────────────────────────────────────────────────────────────
bool DalvikExecutionEngine::parse_content_uri(const std::string& raw,
                                              std::string& scheme,
                                              std::string& authority,
                                              std::string& path,
                                              std::string& query) {
    // AOSP Uri law: "content://authority/path?query" — hierarchical form;
    // fragment splits first, then scheme, then authority up to '/' or '?'.
    std::string body = raw;
    auto hash = body.find('#');
    if (hash != std::string::npos) body = body.substr(0, hash);
    size_t colon = body.find(':');
    if (colon == std::string::npos) return false;
    scheme = body.substr(0, colon);
    if (scheme != "content") return false;
    body = body.substr(colon + 1);
    // "//authority..." — authority ends at '/', '?' or end.
    if (body.size() >= 2 && body[0] == '/' && body[1] == '/')
        body = body.substr(2);
    else
        return false;  // AOSP: hierarchical URIs need "//<authority>"
    auto slash = body.find('/');
    auto qm = body.find('?');
    size_t auth_end = std::min(slash, qm);
    authority = body.substr(0, auth_end == std::string::npos ? body.size()
                                                             : auth_end);
    if (authority.empty()) return false;
    if (slash != std::string::npos && (qm == std::string::npos || slash < qm)) {
        size_t path_end = (qm == std::string::npos) ? body.size() : qm;
        path = body.substr(slash, path_end - slash);
    }
    if (qm != std::string::npos) query = body.substr(qm + 1);
    return true;
}

// ── CODER7 WAVE-8 L2: PendingIntent.send dispatch (the AOSP sendInner
// law). The shadow owns the RECORD laws (ONE_SHOT / IMMUTABLE /
// CanceledException); this method IS the dispatch channel — the frozen
// intent re-enters the exact bridge law the app-context calls use. No
// duplicated broadcast/service/activity resolution exists here by design
// (S185 VEND/DON'T-REWRITE: one component table, one pipeline).
bool DalvikExecutionEngine::c7_send_pending_intent(const std::string& kind,
                                                   uint32_t intent_oid,
                                                   std::string& err) {
    if (intent_oid == 0 || !heap_.has_object(intent_oid)) {
        err = "frozen intent object missing from heap";
        return false;
    }
    DalvikValue c7_ctx =
        (application_object_id_ != 0 &&
         heap_.has_object(application_object_id_))
            ? DalvikValue::make_object(
                  application_object_id_,
                  application_class_desc_.empty()
                      ? "Landroid/app/Application;"
                      : application_class_desc_)
            : get_or_create_singleton("Landroid/content/Context;");
    DalvikValue c7_iv =
        DalvikValue::make_object(intent_oid, "Landroid/content/Intent;");
    if (kind == "BROADCAST") {
        // ContextImpl.sendBroadcast — the full gated law (own + xpkg
        // resolution, exported/permission gates, sticky/category laws)
        // runs unmodified; its evidence rows are the dispatch proof.
        DalvikValue c7_ret;
        ApiCallTrace::Status c7_st;
        std::vector<DalvikValue> c7_args{c7_ctx, c7_iv};
        bridge_to_api("Landroid/content/ContextWrapper;", "sendBroadcast",
                      c7_args, c7_ret, c7_st, 0);
        return true;
    }
    if (kind == "SERVICE") {
        DalvikValue c7_ret;
        ApiCallTrace::Status c7_st;
        std::vector<DalvikValue> c7_args{c7_ctx, c7_iv};
        bridge_to_api("Landroid/content/ContextWrapper;", "startService",
                      c7_args, c7_ret, c7_st, 0);
        return true;
    }
    if (kind == "ACTIVITY") {
        // AOSP sendInner → AMS.startActivityAsUser: the ContextImpl
        // NEW_TASK gate does NOT apply to a PendingIntent send; the
        // WAVE-7 resolve + SYNCHRONOUS gate + queue law DOES.
        auto* c7_ish = shadow_registry_
                           ? shadow_registry_->find_as<
                                 framework::IntentShadow>()
                           : nullptr;
        if (!c7_ish) {
            err = "no IntentShadow wired";
            return false;
        }
        auto c7_pi = c7_ish->get_or_create_intent(intent_oid);
        if (!c7_pi) {
            err = "no intent record for the frozen intent";
            return false;
        }
        c7_pi->intent_object_id = intent_oid;
        if (c7_pi->component_class.empty() && !c7_pi->action.empty()) {
            std::string c7_res = c7_ish->resolve_action_target(c7_pi->action);
            if (!c7_res.empty()) c7_pi->component_class = c7_res;
            if (c7_pi->component_class.empty()) {
                std::string c7_x = c7_resolve_activity_xpkg(
                    c7_pi->action, c7_pi->categories, c7_pi->type,
                    c7_pi->data_scheme, c7_pi->data_host, c7_pi->data_path,
                    /*default_only=*/true);
                if (!c7_x.empty()) {
                    c7_pi->component_class = c7_x;
                    miniandroid::diagnostics::FileIoTrace::instance().record(
                        "ACT-XPKG-RESOLVE", c7_x, true,
                        "PendingIntent send implicit resolution via store "
                        "index (action=" +
                            c7_pi->action + ")",
                        "DalvikExecutionEngine.c7_send_pending_intent");
                }
            }
        }
        if (!c7_pi->component_class.empty()) {
            std::string c7_gerr =
                c7_activity_launch_gate(c7_pi->component_class);
            if (!c7_gerr.empty()) {
                // The gate refusal is a REAL exception in the caller's
                // frame (AOSP sendInner rethrows before dispatch).
                if (c7_gerr.rfind("SECURITY_EXCEPTION:", 0) == 0)
                    throw_deferred("Ljava/lang/SecurityException;",
                                   c7_gerr.substr(18), "PI-SEND");
                else
                    throw_deferred(
                        "Landroid/content/ActivityNotFoundException;",
                        c7_gerr.substr(c7_gerr.find(':') + 1), "PI-SEND");
                err = c7_gerr;
                return false;
            }
        }
        c7_ish->enqueue_pending(c7_pi);
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "PI-SEND", "ACTIVITY", true,
            "launch queued (component=" + c7_pi->component_class +
                "; drain applies the task/launchMode laws)",
            "DalvikExecutionEngine.c7_send_pending_intent");
        return true;
    }
    err = "unknown PendingIntent kind " + kind;
    return false;
}

// ── CODER7 WAVE-12: the manifest FGS-type lookup ─────────────────────────
// AOSP PackageManagerService.generatePackageInfo: ServiceInfo
// .foregroundServiceType is served from the parsed manifest
// android:foregroundServiceType bitmask on EVERY ServiceInfo the PM
// generates (getServiceInfo, getPackageInfo GET_SERVICES). The running
// package's table is manifest_service_filters_ (the stage-load transfer
// carries fgs_type per service row).
int DalvikExecutionEngine::manifest_service_fgs_type(
    const std::string& dotted_cls) const {
    // Name-form normalization: callers pass the dotted absolute name OR
    // the descriptor form ("Lc7/w12/W12Service;" — the ServiceInstance
    // cls and the engine dispatch class_name are descriptors); the
    // transfer table stores the dotted absolute name. Descriptor →
    // dotted: trim the L...; wrapper, slashes → dots (the F116 law).
    std::string key = dotted_cls;
    if (key.size() >= 2 && key.front() == 'L' && key.back() == ';')
        key = key.substr(1, key.size() - 2);
    for (auto& ch : key)
        if (ch == '/') ch = '.';
    for (const auto& st : manifest_service_filters_) {
        if (st.cls == key) return st.fgs_type;
    }
    return 0;
}

// ── CODER7 WAVE-12: the parent-chain resolver ────────────────────────────
// AOSP TaskStackBuilder.addParentStack(ComponentName) walks
// ActivityInfo.parentActivityName through PackageManager.getActivityInfo.
// One law, two sources: the RUNNING package answers from the manifest
// transfer (manifest_activity_parent_); store packages answer from the
// C7 package index (C7IdxActivity.parent_activity_name — the SQLite
// cache payload carries it). "" = no parent (the walk terminates).
std::string DalvikExecutionEngine::c7_activity_parent_of(
    const std::string& pkg, const std::string& cls) const {
    if (pkg == package_name_ || pkg.empty()) {
        auto it = manifest_activity_parent_.find(cls);
        if (it != manifest_activity_parent_.end()) return it->second;
        return "";
    }
    if (c7_pkg_index_) {
        if (const C7IdxPackage* fp = c7_pkg_index_->find_package(pkg)) {
            for (const auto& a : fp->activities) {
                if (a.cls == cls) return a.parent_activity_name;
            }
        }
    }
    return "";
}

// ── CODER7 WAVE-12: the TaskStackBuilder.startActivities dispatch ────────
// AOSP TaskStackBuilder.startActivities() delegates to
// Context.startActivities(mIntents): the RAW intents (NO flag copies —
// the flag-carrying copies are the getIntents() law), drained in order.
// The bridge re-enters the ONE W3 startActivities law (implicit
// resolution + the synchronous launch gate + the FIFO pending queue) —
// the S185 VEND/DON'T-REWRITE rule (one pipeline, no duplicated
// launch path). The receiver is the application context (the same
// identity law c7_send_pending_intent uses).
bool DalvikExecutionEngine::c7_tsb_start_dispatch(
    const std::vector<uint32_t>& oids, std::string& err) {
    if (oids.empty()) {
        err = "startActivities on an empty TaskStackBuilder";
        return false;
    }
    uint32_t c7_arr =
        heap_.allocate("[Landroid/content/Intent;", pc_, 0);
    heap_.set_object_field(c7_arr, "__array_length__",
                           DalvikValue::make_int((int)oids.size()));
    for (size_t i = 0; i < oids.size(); ++i) {
        if (!heap_.has_object(oids[i])) {
            err = "stack intent missing from heap (oid " +
                  std::to_string(oids[i]) + ")";
            return false;
        }
        DalvikValue ev;
        ev.type = DalvikType::OBJECT_REF;
        ev.object_id = oids[i];
        ev.class_desc = "Landroid/content/Intent;";
        ev.int_val = (int64_t)oids.size();
        heap_.set_object_field(c7_arr,
                               "array[" + std::to_string(i) + "]", ev);
    }
    DalvikValue c7_ctx =
        (application_object_id_ != 0 &&
         heap_.has_object(application_object_id_))
            ? DalvikValue::make_object(
                  application_object_id_,
                  application_class_desc_.empty()
                      ? "Landroid/app/Application;"
                      : application_class_desc_)
            : get_or_create_singleton("Landroid/content/Context;");
    DalvikValue c7_av;
    c7_av.type = DalvikType::OBJECT_REF;
    c7_av.object_id = c7_arr;
    c7_av.class_desc = "[Landroid/content/Intent;";
    c7_av.int_val = (int64_t)oids.size();
    DalvikValue c7_ret;
    ApiCallTrace::Status c7_st;
    std::vector<DalvikValue> c7_args{c7_ctx, c7_av};
    bridge_to_api("Landroid/content/ContextWrapper;", "startActivities",
                  c7_args, c7_ret, c7_st, 0);
    return true;
}

uint32_t DalvikExecutionEngine::resolve_provider_for_authority(
    const std::string& authority, std::string& provider_cls) {
    auto it = provider_by_authority_.find(authority);
    if (it == provider_by_authority_.end()) {
        // ── CODER7 WAVE-6: foreign provider acquisition (LoadedApk-lite) ──
        // AOSP ActivityThread.acquireProvider: the authority is resolved
        // through the PMS provider map across ALL packages; when the
        // provider lives in ANOTHER package, its process is started, the
        // REAL ContentProvider class is INSTALLED (attachInfo + onCreate)
        // and the binder returned. The engine mirrors that: on an
        // own-provider miss, install the foreign provider from the WAVE-5
        // index (its dex classes were ingested by inject_foreign_apk_code
        // — the S185 LOAD-FIRST law) and let the unmodified CRUD dispatch
        // run the foreign query/insert/update/delete/openFile bytecode.
        // Gates (AOSP checkComponentPermission + ProviderUriPermissions):
        // enabled (the index only publishes enabled providers), exported
        // (running package is a foreign caller), grantUriPermissions OR
        // exported grants access — non-exported + no grant ⇒ deny row.
        // Re-resolve after install; a failure falls through to the honest
        // unknown-authority path (never a fabricated provider).
        if (c7_pkg_index_ && !c7_pkg_index_->empty()) {
            auto c7_fprov = c7_pkg_index_->providers_for_authority(authority);
            for (const auto& c7_pr : c7_fprov) {
                if (c7_pr.package_name == package_name_) continue;
                if (!c7_pr.exported && !c7_pr.grant_uri_permissions) {
                    miniandroid::diagnostics::FileIoTrace::instance().record(
                        "PROV-XPKG-DENY",
                        c7_pr.package_name + "/" + c7_pr.cls, false,
                        "foreign provider not exported and grantUri"
                        "Permissions=false (AOSP checkComponentPermission)",
                        current_class_ + "." + current_method_);
                    continue;
                }
                std::string c7_fdesc = c7_pr.cls;
                if (!c7_fdesc.empty() && c7_fdesc[0] != 'L') {
                    std::replace(c7_fdesc.begin(), c7_fdesc.end(), '.', '/');
                    c7_fdesc = "L" + c7_fdesc + ";";
                }
                if (c7_fdesc.empty() || class_to_superclass_.find(c7_fdesc) ==
                                            class_to_superclass_.end()) {
                    miniandroid::diagnostics::FileIoTrace::instance().record(
                        "PROV-XPKG", c7_pr.package_name + "/" + c7_pr.cls,
                        false,
                        "foreign provider RESOLVED but class not loaded — "
                        "honest miss (no fabrication)",
                        current_class_ + "." + current_method_);
                    continue;
                }
                // ── Install (mirror of install_content_providers GATE-A):
                // allocate → <init>()V → ProviderInfo(identity from the
                // index) → attachInfo(context, info) → onCreate → publish
                // every declared authority.
                uint32_t c7_fpid = heap_.allocate(c7_fdesc, pc_, 0);
                if (c7_fpid == 0) continue;
                DalvikValue c7_fpobj =
                    DalvikValue::make_object(c7_fpid, c7_fdesc);
                DalvikValue c7_fret;
                DalvikExecutionResult c7_ftmp;
                std::vector<DalvikValue> c7_finit{c7_fpobj};
                try_recursive_invoke(c7_fdesc, "<init>", c7_finit, c7_fret,
                                     c7_ftmp, "()V");
                {
                    uint32_t c7_finfo_id = heap_.allocate(
                        "Landroid/content/pm/ProviderInfo;", pc_, 0);
                    heap_.set_object_field(
                        c7_finfo_id, "name",
                        DalvikValue::make_string(c7_fdesc, 1));
                    heap_.set_object_field(
                        c7_finfo_id, "authority",
                        DalvikValue::make_string(c7_pr.authorities, 1));
                    heap_.set_object_field(
                        c7_finfo_id, "authorities",
                        DalvikValue::make_string(c7_pr.authorities, 1));
                    heap_.set_object_field(
                        c7_finfo_id, "grantUriPermissions",
                        DalvikValue::make_bool(
                            c7_pr.grant_uri_permissions));
                    heap_.set_object_field(
                        c7_finfo_id, "exported",
                        DalvikValue::make_bool(c7_pr.exported));
                    heap_.set_object_field(
                        c7_finfo_id, "multiprocess",
                        DalvikValue::make_bool(false));
                    DalvikValue c7_finfo;
                    c7_finfo.type = DalvikType::OBJECT_REF;
                    c7_finfo.object_id = c7_finfo_id;
                    c7_finfo.class_desc =
                        "Landroid/content/pm/ProviderInfo;";
                    DalvikValue c7_fctx;
                    if (application_object_id_ != 0 &&
                        heap_.has_object(application_object_id_)) {
                        c7_fctx.type = DalvikType::OBJECT_REF;
                        c7_fctx.object_id = application_object_id_;
                        c7_fctx.class_desc =
                            application_class_desc_.empty()
                                ? "Landroid/app/Application;"
                                : application_class_desc_;
                    } else {
                        c7_fctx = get_or_create_singleton(
                            "Landroid/content/Context;");
                    }
                    std::vector<DalvikValue> c7_fattach{c7_fpobj, c7_fctx,
                                                        c7_finfo};
                    try_recursive_invoke(
                        c7_fdesc, "attachInfo", c7_fattach, c7_fret, c7_ftmp,
                        "(Landroid/content/Context;"
                        "Landroid/content/pm/ProviderInfo;)V");
                    provider_context_[c7_fpid] = c7_fctx.object_id;
                    // Publish EVERY ';'-joined authority (AOSP
                    // installContentProviders map law).
                    const std::string& c7_auth_all = c7_pr.authorities;
                    size_t c7_start = 0;
                    while (c7_start <= c7_auth_all.size()) {
                        size_t c7_semi = c7_auth_all.find(';', c7_start);
                        std::string c7_one = c7_auth_all.substr(
                            c7_start,
                            c7_semi == std::string::npos
                                ? std::string::npos
                                : c7_semi - c7_start);
                        if (!c7_one.empty()) {
                            provider_by_authority_[c7_one] = c7_fpid;
                            provider_class_by_oid_[c7_fpid] = c7_pr.cls;
                            // CODER7 WAVE-8 L1: the foreign provider's
                            // read/write permission identity rides the
                            // store index (checkContentProviderAccess law).
                            c7_set_provider_perms(
                                c7_fpid, c7_pr.read_permission,
                                c7_pr.write_permission, c7_pr.package_name);
                        }
                        if (c7_semi == std::string::npos) break;
                        c7_start = c7_semi + 1;
                    }
                }
                std::vector<DalvikValue> c7_fcreate;
                c7_fcreate.push_back(c7_fpobj);
                bool c7_fok = try_recursive_invoke(c7_fdesc, "onCreate",
                                                   c7_fcreate, c7_fret,
                                                   c7_ftmp, "()Z");
                miniandroid::diagnostics::FileIoTrace::instance().record(
                    "PROV-XPKG-EXEC", c7_pr.package_name + "/" + c7_pr.cls,
                    c7_fok,
                    "foreign provider INSTALLED from store (authority=" +
                        authority + ") attachInfo+onCreate " +
                        (c7_fok ? "OK" : "SKIPPED") +
                        " — REAL CRUD dispatch follows",
                    current_class_ + "." + current_method_);
                std::cerr << "[C7-W6] foreign provider installed: "
                          << c7_pr.package_name << "/" << c7_pr.cls
                          << " auth=" << authority << std::endl;
                it = provider_by_authority_.find(authority);
                break;
            }
        }
        if (it == provider_by_authority_.end()) return 0;
    }
    provider_cls.clear();
    auto cls_it = provider_class_by_oid_.find(it->second);
    if (cls_it != provider_class_by_oid_.end()) {
        provider_cls = cls_it->second;
        // CODER7 WAVE-3: a DISABLED provider is not published (AOSP
        // PackageItemInfo.isEnabled) — the authority miss law applies.
        if (!c7_provider_enabled(provider_cls)) {
            provider_cls.clear();
            return 0;
        }
    }
    return it->second;
}

bool DalvikExecutionEngine::invoke_provider_method(
    uint32_t provider_oid, const std::string& provider_cls,
    const std::string& method, std::vector<DalvikValue> args, DalvikValue& ret,
    std::string& err) {
    DalvikExecutionResult tmp;
    std::vector<DalvikValue> full;
    DalvikValue recv = DalvikValue::make_object(provider_oid, provider_cls);
    full.push_back(recv);
    for (auto& a : args) full.push_back(a);
    bool ok = try_recursive_invoke(provider_cls, method, full, ret, tmp, "");
    if (!ok) err = "provider method not found: " + provider_cls + "." + method;
    return ok;
}

uint32_t DalvikExecutionEngine::make_uri_object(const std::string& raw) {
    // The Uri.parse law path (bridge handler above) is the canonical
    // constructor of Uri heap objects; reuse its field layout here.
    uint32_t uri_id = heap_.allocate("Landroid/net/Uri;", pc_, 0);
    auto put = [&](const char* k, const std::string& v) {
        heap_.set_object_field(uri_id, k, DalvikValue::make_string(v, 0));
    };
    put("uri_raw", raw);
    std::string scheme, authority, path, query;
    if (parse_content_uri(raw, scheme, authority, path, query)) {
        put("scheme", scheme);
        put("path", path);
        if (!query.empty()) put("query", query);
    } else {
        // Non-content form: keep the raw string reachable (longest-string
        // field law serves getPath/getLastPathSegment honestly).
        put("path", raw);
    }
    put("ssp", raw);
    return uri_id;
}

bool DalvikExecutionEngine::invoke_lifecycle_method(
    uint32_t oid, const std::string& cls, const std::string& method,
    std::vector<DalvikValue> args, DalvikValue& ret) {
    DalvikExecutionResult tmp;
    std::vector<DalvikValue> full;
    full.push_back(DalvikValue::make_object(oid, cls));
    for (auto& a : args) full.push_back(a);
    return try_recursive_invoke(cls, method, full, ret, tmp, "");
}

// ── CODER7 WAVE-9: the system-signal dispatch laws ────────────────────
// AOSP ActivityThread.handleTrimMemory: "the Application's callbacks run
// BEFORE the component's" — dispatch order app → activity. AOSP
// Application.onLowMemory: fired at TRIM_MEMORY_COMPLETE (the legacy
// ComponentCallbacks alias; android-14 ActivityThread keeps the
// onLowMemory() leg for level == TRIM_MEMORY_COMPLETE). AOSP
// handleConfigurationChanged: the Configuration object reaches BOTH the
// Application and the Activity overrides; the ORIENTATION constant the
// engine carries for the rotate signal is ORIENTATION_LANDSCAPE (2).
void DalvikExecutionEngine::dispatch_memory_and_config_signals(
    int trim_level, bool rotate) {
    // The live activity identity (ActivityShadow::current_activity_id —
    // the same identity performLaunchActivity recorded).
    uint32_t act_oid = 0;
    std::string act_cls;
    if (shadow_registry_ != nullptr) {
        if (auto* act =
                shadow_registry_->find_as<framework::ActivityShadow>()) {
            act_oid = act->current_activity_id();
            if (act_oid != 0 && heap_.has_object(act_oid))
                act_cls = heap_.get(act_oid)->class_descriptor;
        }
    }
    const bool app_live = application_object_id_ != 0 &&
                          heap_.has_object(application_object_id_) &&
                          !application_class_desc_.empty();

    if (trim_level > 0) {
        int app_done = 0, act_done = 0, low_done = 0;
        if (app_live) {
            DalvikValue ret;
            if (invoke_lifecycle_method(
                    application_object_id_, application_class_desc_,
                    "onTrimMemory", {DalvikValue::make_int(trim_level)}, ret))
                app_done++;
            // AOSP: onLowMemory is the TRIM_MEMORY_COMPLETE alias.
            if (trim_level == 15 /*TRIM_MEMORY_COMPLETE*/) {
                DalvikValue lret;
                if (invoke_lifecycle_method(
                        application_object_id_, application_class_desc_,
                        "onLowMemory", {}, lret))
                    low_done++;
            }
        }
        if (act_oid != 0 && !act_cls.empty()) {
            DalvikValue ret;
            if (invoke_lifecycle_method(act_oid, act_cls, "onTrimMemory",
                                        {DalvikValue::make_int(trim_level)},
                                        ret))
                act_done++;
        }
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "C7-TRIM", "level=" + std::to_string(trim_level), true,
            "app=" + std::to_string(app_done) +
                " act=" + std::to_string(act_done) +
                " lowmem=" + std::to_string(low_done) +
                " (AOSP app-before-activity)",
            "DispatchMemoryAndConfigSignals");
        std::cerr << "[C7-TRIM] level=" << trim_level
                  << " app=" << app_done << " act=" << act_done
                  << " lowmem=" << low_done << std::endl;
    }

    if (rotate) {
        uint32_t cfg_id = heap_.allocate(
            "Landroid/content/res/Configuration;", pc_, 0);
        heap_.set_object_field(
            cfg_id, "orientation", DalvikValue::make_int(2)  // LANDSCAPE
        );
        heap_.set_object_field(
            cfg_id, "densityDpi", DalvikValue::make_int(160));
        DalvikValue cfg =
            DalvikValue::make_object(cfg_id,
                                     "Landroid/content/res/Configuration;");
        int app_done = 0, act_done = 0;
        if (app_live) {
            DalvikValue ret;
            if (invoke_lifecycle_method(
                    application_object_id_, application_class_desc_,
                    "onConfigurationChanged", {cfg}, ret))
                app_done++;
        }
        if (act_oid != 0 && !act_cls.empty()) {
            DalvikValue ret;
            if (invoke_lifecycle_method(act_oid, act_cls,
                                        "onConfigurationChanged", {cfg},
                                        ret))
                act_done++;
        }
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "C7-CFGCHG", "orientation=2", true,
            "app=" + std::to_string(app_done) +
                " act=" + std::to_string(act_done) +
                " (AOSP app-before-activity)",
            "DispatchMemoryAndConfigSignals");
        std::cerr << "[C7-CFGCHG] orientation=2 app=" << app_done
                  << " act=" << act_done << std::endl;
    }

    // ── CODER7 WAVE-11: the SERVICE system-signal stand-ins (the same
    // honest harness pattern the W9 trim/config dispatch uses — the env
    // carries the deterministic system signal; empty ⇒ no dispatch).
    //   MINIANDROID_TASK_REMOVED=<root-intent action or "1">  → AOSP
    //       ActiveServices.killServicesLocked → onTaskRemoved(rootIntent)
    //       delivered to every STARTED live service when the launching
    //       task is removed.
    //   MINIANDROID_SVC_TIMEOUT="1" → AOSP Service.onTimeout(int startId)
    //       (API 34 shortService FGS budget exhaustion): delivered to
    //       every STARTED live service with ITS OWN lastStartId; the
    //       timeout-kill contract (stopSelf or the system kills) is the
    //       app's obligation — tracked, never faked.
    static const bool c7_task_removed = [] {
        const char* e = std::getenv("MINIANDROID_TASK_REMOVED");
        return e && e[0];
    }();
    static const bool c7_svc_timeout = [] {
        const char* e = std::getenv("MINIANDROID_SVC_TIMEOUT");
        return e && e[0] == '1';
    }();
    if (c7_task_removed || c7_svc_timeout) {
        static const std::string c7_root_action = [] {
            const char* e = std::getenv("MINIANDROID_TASK_REMOVED");
            if (!e || !e[0] || std::string(e) == "1") return std::string();
            return std::string(e);
        }();
        uint32_t root_oid = 0;
        if (c7_task_removed) {
            root_oid = heap_.allocate("Landroid/content/Intent;", pc_, 0);
            if (shadow_registry_ != nullptr) {
                auto* tish =
                    shadow_registry_->find_as<framework::IntentShadow>();
                if (tish) {
                    auto tpi = tish->get_or_create_intent(root_oid);
                    if (tpi)
                        tpi->action = c7_root_action.empty()
                                          ? "android.intent.action.MAIN"
                                          : c7_root_action;
                }
            }
        }
        int tr_done = 0, to_done = 0;
        for (auto& [tsvc_cls, tsvc] : live_services_) {
            if (!tsvc.started || tsvc.destroyed || !tsvc.created) continue;
            if (c7_task_removed && root_oid != 0) {
                DalvikValue tret;
                DalvikValue tint =
                    DalvikValue::make_object(root_oid,
                                             "Landroid/content/Intent;");
                if (invoke_lifecycle_method(tsvc.oid, tsvc.cls,
                                            "onTaskRemoved", {tint}, tret))
                    tr_done++;
            }
            if (c7_svc_timeout) {
                DalvikValue tret;
                if (invoke_lifecycle_method(
                        tsvc.oid, tsvc.cls, "onTimeout",
                        {DalvikValue::make_int(tsvc.last_start_id)}, tret))
                    to_done++;
            }
        }
        if (c7_task_removed)
            miniandroid::diagnostics::FileIoTrace::instance().record(
                "SVC-TASKREMOVED",
                c7_root_action.empty() ? "MAIN" : c7_root_action, true,
                "onTaskRemoved delivered=" + std::to_string(tr_done) +
                    " (ActiveServices task-removal law, env stand-in)",
                "DispatchMemoryAndConfigSignals");
        if (c7_svc_timeout)
            miniandroid::diagnostics::FileIoTrace::instance().record(
                "SVC-TIMEOUT", "shortService", true,
                "onTimeout delivered=" + std::to_string(to_done) +
                    " (API 34 FGS budget law, env stand-in)",
                "DispatchMemoryAndConfigSignals");
    }
}

// ── F-NEW-304 (CONT-42): platform Fragment lifecycle drain ─────────────
// AOSP FragmentController/FragmentManagerImpl laws, driven from the HOST
// lifecycle boundaries. Evidence chain: tananaev calculator v1.10
// MainActivity.onCreate → getFragmentManager().beginTransaction()
// .replace(16908290, new PrefsFragment()).commit() — the old law dropped
// every op (fluent THIS) and commit answered 0, so the platform
// PreferenceFragment NEVER materialized: ContentFrameLayout stayed at
// children=0, first_missing_stage=APP_DRAW_OPS, verdict
// DEFAULT_BACKGROUND_ONLY (the recorded PARTIAL face).
// Stage model (AOSP Fragment.mState ladder):
//   0 queued → 1 CREATED (onAttach+onCreate) → 3 STARTED (onCreateView →
//   onViewCreated → onActivityCreated → onStart) → 4 RESUMED (onResume).
// (2 = the VIEW_CREATED hop; folded into the started transition — the
// platform dispatches view creation and start within one host event.)
// The stage lives on the fragment heap object (__frag_stage__) — the same
// field the shadow getters (isAdded/getView/getTag) answer from.

static int32_t frag_stage_of(DalvikHeap& heap, uint32_t oid) {
    auto v = heap.get_object_field(oid, "__frag_stage__");
    if (v && v->type == DalvikType::INT32) return v->int_val;
    return 0;
}


// ── F-NEW-383 (CONT-82): ColorStateList wrap helper ─────────────────────
// AOSP ColorStateList.valueOf(int color): a single default-state spec whose
// getDefaultColor() answers the color for ANY state set. Heap convention:
// __default_color__ (INT32 ARGB) + __csl_single__ (INT32 1) — the reader
// law answers deterministically from these fields; full state-spec arrays
// remain a named deeper frontier (no state-dependent colors invented).
uint32_t csl_wrap_single(DalvikHeap& heap, uint32_t pc, int32_t argb,
                                uint32_t frame_id) {
    uint32_t id = heap.allocate("Landroid/content/res/ColorStateList;", pc,
                                frame_id);
    heap.set_object_field(id, "__default_color__",
                          DalvikValue::make_int(argb));
    heap.set_object_field(id, "__csl_single__", DalvikValue::make_int(1));
    return id;
}

bool DalvikExecutionEngine::advance_fragments_to_created(
    DalvikExecutionResult& result) {
    (void)result;
    auto* fm = shadow_registry_
                   ? shadow_registry_->find_as<framework::FragmentManagerShadow>()
                   : nullptr;
    if (!fm) return false;
    (void)fm->take_drain_requested();  // executePendingTransactions: same window
    std::vector<framework::FragmentManagerShadow::PendingTx> txs;
    if (!fm->take_committed(txs)) return false;
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    uint32_t host_id = as ? as->current_activity_id() : 0;
    static int fnew304_created_diag = 0;
    bool advanced = false;
    for (auto& tx : txs) {
        for (auto& op : tx.ops) {
            if (op.frag == 0) continue;
            if (op.type == 0 || op.type == 1) {  // add / replace
                if (frag_stage_of(heap_, op.frag) >= 1) continue;
                std::string frag_cls;
                heap_.get_object_class(op.frag, frag_cls);
                // AOSP replace: the container's current fragment leaves
                // before the new one attaches — its view detaches from
                // the tree (single-active-content law).
                if (op.type == 1 && op.container != 0) {
                    if (auto* vs = shadow_registry_
                                       ? shadow_registry_->find_as<
                                             framework::ViewShadow>()
                                       : nullptr) {
                        for (auto& r : fm->fragments()) {
                            if (r.frag != op.frag &&
                                r.container == op.container && r.view != 0) {
                                vs->detach_from_parent(r.view);
                            }
                        }
                    }
                }
                DalvikValue ret;
                // onAttach(Context) — the host activity IS the Context the
                // fragment stores (AOSP Fragment.mHost context). Skipped
                // silently when not overridden (platform default no-op).
                if (host_id != 0) {
                    invoke_lifecycle_method(
                        op.frag, frag_cls, "onAttach",
                        {DalvikValue::make_object(host_id,
                                                  "Landroid/app/Activity;")},
                        ret);
                }
                // onCreate(Bundle=null) — the app's addPreferencesFrom-
                // Resource call fires HERE through the real DEX.
                invoke_lifecycle_method(op.frag, frag_cls, "onCreate",
                                        {DalvikValue::make_null()}, ret);
                heap_.set_object_field(op.frag, "__frag_stage__",
                                       DalvikValue::make_int(1));
                heap_.set_object_field(op.frag, "__frag_host__",
                                       DalvikValue::make_object(
                                           host_id, "Landroid/app/Activity;"));
                advanced = true;
                if (fnew304_created_diag < 24) {
                    ++fnew304_created_diag;
                    std::cerr << "[F-NEW-304] created drain: " << frag_cls
                              << " obj#" << op.frag << " container=0x" << std::hex
                              << op.container << std::dec
                              << (op.tag.empty() ? "" : " tag=" + op.tag)
                              << std::endl;
                }
            } else if (op.type == 2) {  // remove
                if (auto* vs = shadow_registry_
                                   ? shadow_registry_->find_as<
                                         framework::ViewShadow>()
                                   : nullptr) {
                    uint32_t v = 0;
                    auto fv = heap_.get_object_field(op.frag, "__frag_view__");
                    if (fv && fv->type == DalvikType::OBJECT_REF)
                        v = fv->object_id;
                    if (v != 0) vs->detach_from_parent(v);
                }
                heap_.set_object_field(op.frag, "__frag_stage__",
                                       DalvikValue::make_int(0));
            }
            // hide/show/detach/attach: view-visibility hops — no observable
            // content change in this runtime's single-window model yet;
            // recorded as the honest scope boundary (next-wave candidate).
        }
    }
    return advanced;
}

// ── F-NEW-339 (CONT-59): XML <fragment> tag instantiation law ───────────
bool DalvikExecutionEngine::instantiate_fragment_tag(
        uint32_t container_view_id, const std::string& frag_class_desc,
        const std::string& tag, int32_t xml_id,
        const std::vector<resources::XmlAttrRecord>& xml_attrs) {
    (void)container_view_id;
    auto* fm = shadow_registry_
                   ? shadow_registry_->find_as<framework::FragmentManagerShadow>()
                   : nullptr;
    if (!fm) return false;
    if (!is_dex_defined_class(frag_class_desc)) {
        std::cerr << "[F-NEW-339] <fragment> name not in DEX: "
                  << frag_class_desc << " — honest miss" << std::endl;
        return false;
    }
    // AOSP FragmentFactory.instantiate law: the NO-ARG constructor.
    uint32_t frag = heap_.allocate(frag_class_desc, 0, 0);
    DalvikValue ctor_ret;
    DalvikExecutionResult ctor_result;
    try_recursive_invoke(frag_class_desc, "<init>", {}, ctor_ret,
                         ctor_result, "()V");
    // Host linkage (the F-NEW-304 laws read __frag_host__ at dispatch).
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    uint32_t host_id = as ? as->current_activity_id() : 0;
    if (host_id != 0)
        heap_.set_object_field(
            frag, "__frag_host__",
            DalvikValue::make_object(host_id, "Landroid/app/Activity;"));

    // ── F-C4-617 (W15): the onInflate DISPATCH law ─────────────────────
    // AOSP FragmentLayoutInflaterFactory / FragmentContainerView internal
    // ctor (fragment-1.8.5, decoded from itsfrz 5 this wave):
    //     containerFragment.onInflate(context, attrs, null);
    // BEFORE the transaction commits. The method reads app:navGraph into
    // mGraphId (NavHostFragment.onInflate → obtainStyledAttributes →
    // TypedArray.getResourceId(0,0)) and app:defaultNavHost — the values
    // every later NavController wire needs. R8 renames the method (itsfrz
    // NavHostFragment.y) — the structural resolve is the EXACT descriptor
    // (Landroid/content/Context;Landroid/util/AttributeSet;
    //  Landroid/os/Bundle;)V with name "onInflate" preferred, ANY
    // single-method name with that descriptor accepted (the signature is
    // unique on a Fragment subclass). The element's XML attrs ride the
    // AttributeSetStore (F-NEW-197) so the real obtainStyledAttributes
    // (F-NEW-327) reads them. Honest miss: no matching method → skipped
    // silently (the F-NEW-304 lifecycle drain proceeds as before).
    {
        const std::string kOnInflateDesc =
            "(Landroid/content/Context;Landroid/util/AttributeSet;"
            "Landroid/os/Bundle;)V";
        const dex::ClassInfo* frag_ci = nullptr;
        {
            auto cit = class_info_index_.find(frag_class_desc);
            if (cit != class_info_index_.end())
                frag_ci = &dex_report_->classes[cit->second];
        }
        std::string oninflate_name;
        if (frag_ci != nullptr) {
            int desc_matches = 0;
            std::string only_name;
            for (const auto* ml :
                 {&frag_ci->direct_methods, &frag_ci->virtual_methods}) {
                for (const auto& mm : *ml) {
                    if (mm.descriptor != kOnInflateDesc) continue;
                    if (mm.is_abstract || mm.is_native ||
                        mm.bytecode.empty())
                        continue;
                    ++desc_matches;
                    only_name = mm.name;
                    if (mm.name == "onInflate") {
                        oninflate_name = mm.name;  // canonical wins
                        break;
                    }
                }
                if (!oninflate_name.empty()) break;
            }
            // R8-renamed shape: exactly ONE method with the descriptor.
            if (oninflate_name.empty() && desc_matches == 1)
                oninflate_name = only_name;
        }
        if (!oninflate_name.empty()) {
            uint32_t ctx617 = host_id;
            if (ctx617 == 0)
                ctx617 = heap_.allocate("Landroid/content/Context;", 0, 0);
            uint32_t attrs617 =
                heap_.allocate("Landroid/util/AttributeSet;", 0, 0);
            if (!xml_attrs.empty()) {
                resources::AttributeSetStore::instance().install(
                    attrs617, xml_attrs);
            }
            std::vector<DalvikValue> oargs;
            oargs.push_back(
                DalvikValue::make_object(frag, frag_class_desc));
            oargs.push_back(DalvikValue::make_object(
                ctx617, "Landroid/content/Context;"));
            oargs.push_back(DalvikValue::make_object(
                attrs617, "Landroid/util/AttributeSet;"));
            oargs.push_back(DalvikValue::make_null());  // Bundle (null)
            DalvikValue oret = DalvikValue::make_void();
            DalvikExecutionResult ores;
            bool ook = try_recursive_invoke(
                frag_class_desc, oninflate_name, oargs, oret, ores,
                kOnInflateDesc);
            static thread_local int f617_n = 0;
            if (f617_n < 8) {
                ++f617_n;
                std::cerr << "[F-C4-617] onInflate " << oninflate_name
                          << " on " << frag_class_desc << " obj#" << frag
                          << " ok=" << (ook ? 1 : 0) << " attrs="
                          << xml_attrs.size() << std::endl;
            }
        }
    }
    // Synthetic BackStackRecord: add(frag, container=xml_id, tag) — the
    // SAME committed queue the DEX commit path feeds; the F-NEW-304
    // drains run onAttach/onCreate/onCreateView and attach the fragment
    // view into the container node (find_by_android_id(xml_id)).
    framework::FragmentManagerShadow::PendingOp op;
    op.type = 0;
    op.container = (uint32_t)xml_id;
    op.frag = frag;
    op.tag = tag;
    framework::FragmentManagerShadow::PendingTx tx;
    tx.ops.push_back(op);
    fm->enqueue_committed(tx);
    fm->record_fragment({frag, (uint32_t)xml_id, tag, 0});
    std::cerr << "[F-NEW-339] <fragment> " << frag_class_desc << " obj#"
              << frag << " container=" << xml_id
              << (tag.empty() ? "" : " tag=" + tag)
              << " → synthetic add committed" << std::endl;
    return true;
}

bool DalvikExecutionEngine::advance_fragments_to_started(
    DalvikExecutionResult& result) {
    (void)result;
    auto* fm = shadow_registry_
                   ? shadow_registry_->find_as<framework::FragmentManagerShadow>()
                   : nullptr;
    if (!fm) return false;
    auto* vs = shadow_registry_
                   ? shadow_registry_->find_as<framework::ViewShadow>()
                   : nullptr;
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    static int fnew304_start_diag = 0;
    bool advanced = false;
    for (auto& r : fm->fragments()) {
        if (r.frag == 0) continue;
        int32_t stage = frag_stage_of(heap_, r.frag);
        if (stage < 1 || stage >= 3) continue;
        std::string frag_cls;
        heap_.get_object_class(r.frag, frag_cls);
        // Container node: the transaction's android:id view within the
        // activity content tree (android.R.id.content may be the root).
        uint32_t container_node = 0;
        if (vs && as && as->content_view_id() != 0 && r.container != 0) {
            container_node = vs->find_by_android_id(as->content_view_id(),
                                                    (int32_t)r.container);
            if (container_node == 0 &&
                as->content_view_id() == r.container) {
                container_node = as->content_view_id();
            }
        }
        // onCreateView — the app override executes REAL DEX (inflater
        // contract included); a platform PreferenceFragment subclass
        // without an override gets the platform list-container law.
        uint32_t view = 0;
        {
            DalvikValue cret;
            std::vector<DalvikValue> cargs;
            cargs.push_back(
                DalvikValue::make_object(r.frag, frag_cls));  // this
            uint32_t inflater_id = 0;
            {
                DalvikValue inflater_val =
                    get_or_create_singleton("Landroid/view/LayoutInflater;");
                inflater_id = inflater_val.object_id;
            }
            cargs.push_back(DalvikValue::make_object(
                inflater_id, "Landroid/view/LayoutInflater;"));
            if (container_node != 0) {
                cargs.push_back(DalvikValue::make_object(
                    container_node, "Landroid/view/ViewGroup;"));
            } else {
                cargs.push_back(DalvikValue::make_null());
            }
            cargs.push_back(DalvikValue::make_null());  // savedInstanceState
            DalvikExecutionResult ctmp;
            const std::string cdesc =
                "(Landroid/view/LayoutInflater;Landroid/view/ViewGroup;"
                "Landroid/os/Bundle;)Landroid/view/View;";
            bool ok = try_recursive_invoke(frag_cls, "onCreateView", cargs,
                                           cret, ctmp, cdesc);
            if (ok && cret.type == DalvikType::OBJECT_REF &&
                !cret.is_null && cret.object_id != 0) {
                view = cret.object_id;
            } else if (!ok && is_subclass_of(
                                  frag_cls,
                                  "Landroid/preference/PreferenceFragment;")) {
                view = frag_build_preference_list_view(r.frag);
            }
        }
        if (view != 0 && container_node != 0 && vs) {
            vs->add_child(container_node, view);
            heap_.set_object_field(
                r.frag, "__frag_view__",
                DalvikValue::make_object(view, "Landroid/view/View;"));
            r.view = view;
            fm->record_fragment(r);
        }
        DalvikValue vret;
        if (view != 0) {
            // onViewCreated(View, Bundle) — platform Fragment API 23+;
            // non-overriders fall through (platform stub is a no-op).
            invoke_lifecycle_method(
                r.frag, frag_cls, "onViewCreated",
                {DalvikValue::make_object(view, "Landroid/view/View;"),
                 DalvikValue::make_null()},
                vret);
        }
        // onActivityCreated(Bundle) — the AOSP CREATED→VIEW_CREATED hop.
        invoke_lifecycle_method(r.frag, frag_cls, "onActivityCreated",
                                {DalvikValue::make_null()}, vret);
        // onStart() — the fragment reaches STARTED with its host.
        invoke_lifecycle_method(r.frag, frag_cls, "onStart", {}, vret);
        heap_.set_object_field(r.frag, "__frag_stage__",
                               DalvikValue::make_int(3));
        advanced = true;
        if (fnew304_start_diag < 24) {
            ++fnew304_start_diag;
            std::cerr << "[F-NEW-304] started drain: " << frag_cls
                      << " obj#" << r.frag << " view#" << view
                      << " container#" << container_node << std::endl;
        }
    }
    return advanced;
}

bool DalvikExecutionEngine::advance_fragments_to_resumed(
    DalvikExecutionResult& result) {
    (void)result;
    auto* fm = shadow_registry_
                   ? shadow_registry_->find_as<framework::FragmentManagerShadow>()
                   : nullptr;
    if (!fm) return false;
    static int fnew304_resume_diag = 0;
    bool advanced = false;
    for (auto& r : fm->fragments()) {
        if (r.frag == 0) continue;
        if (frag_stage_of(heap_, r.frag) != 3) continue;
        std::string frag_cls;
        heap_.get_object_class(r.frag, frag_cls);
        DalvikValue ret;
        invoke_lifecycle_method(r.frag, frag_cls, "onResume", {}, ret);
        heap_.set_object_field(r.frag, "__frag_stage__",
                               DalvikValue::make_int(4));
        advanced = true;
        if (fnew304_resume_diag < 24) {
            ++fnew304_resume_diag;
            std::cerr << "[F-NEW-304] resumed: " << frag_cls << " obj#"
                      << r.frag << std::endl;
        }
    }
    return advanced;
}

// Platform PreferenceFragment.onCreateView law — the AOSP internal
// preference_list_fragment contract reduced to this runtime's REAL view
// semantics: a vertical LinearLayout container whose rows are REAL
// LinearLayout/TextView nodes (title + optional summary), measured by
// the canonical measure laws like every XML-inflated tree. NO fixed
// geometry: widths/heights are MATCH_PARENT/WRAP_CONTENT and the render
// pass owns every pixel. Rows come from the parsed screen state the
// addPreferencesFromResource law stored on the fragment object.
uint32_t DalvikExecutionEngine::frag_build_preference_list_view(
    uint32_t frag_oid) {
    auto* vs = shadow_registry_
                   ? shadow_registry_->find_as<framework::ViewShadow>()
                   : nullptr;
    if (!vs) return 0;
    auto nfield = heap_.get_object_field(frag_oid, "__pref_n__");
    int n = (nfield && nfield->type == DalvikType::INT32) ? nfield->int_val : 0;
    if (n <= 0) return 0;
    uint32_t root = vs->create_view("Landroid/widget/LinearLayout;");
    auto* rn = vs->get_or_create_node(root, "Landroid/widget/LinearLayout;");
    if (!rn) return 0;
    rn->width = -1;   // MATCH_PARENT
    rn->height = -2;  // WRAP_CONTENT
    // The measure law derives child specs from lp_width/lp_height (the
    // layout-params record the inflater fills from XML) — an engine-built
    // node must fill them too or the spec derivation falls back to the
    // parent's EXACTLY (live face: every row measured 1080x1920).
    rn->lp_width = -1;
    rn->lp_height = -2;
    // AOSP LinearLayout.java: the orientation field defaults to HORIZONTAL —
    // the preference list is VERTICAL (the platform
    // preference_list_fragment ListView law). Without this the rows laid
    // out at x=i*width, every row off-screen right (live tananaev face:
    // rows at pos=(1080/2160/3240/4320,0) on a 1080-wide screen).
    rn->orientation = 1;  // VERTICAL
    static int fnew304_pref_diag = 0;
    for (int i = 0; i < n && i < 128; ++i) {
        const std::string p = "__pref_" + std::to_string(i) + "_";
        uint32_t row = vs->create_view("Landroid/widget/LinearLayout;");
        auto* rown = vs->get_or_create_node(row, "Landroid/widget/LinearLayout;");
        if (!rown) continue;
        rown->width = -1;
        rown->height = -2;
        rown->lp_width = -1;
        rown->lp_height = -2;
        rown->orientation = 1;  // VERTICAL (title stacked over summary)
        vs->add_child(root, row);
        auto tfield = heap_.get_object_field(frag_oid, p + "title");
        std::string title =
            (tfield && tfield->type == DalvikType::STRING_REF && !tfield->is_null)
                ? std::string(tfield->string_val)
                : std::string();
        auto sfield = heap_.get_object_field(frag_oid, p + "summary");
        std::string summary =
            (sfield && sfield->type == DalvikType::STRING_REF && !sfield->is_null)
                ? std::string(sfield->string_val)
                : std::string();
        if (!title.empty()) {
            uint32_t tv = vs->create_view("Landroid/widget/TextView;");
            auto* tvn = vs->get_or_create_node(tv, "Landroid/widget/TextView;");
            if (tvn) {
                tvn->text = title;
                tvn->width = -1;
                tvn->height = -2;
                tvn->lp_width = -1;
                tvn->lp_height = -2;
                vs->add_child(row, tv);
            }
        }
        if (!summary.empty()) {
            uint32_t sv = vs->create_view("Landroid/widget/TextView;");
            auto* svn = vs->get_or_create_node(sv, "Landroid/widget/TextView;");
            if (svn) {
                svn->text = summary;
                svn->width = -1;
                svn->height = -2;
                svn->lp_width = -1;
                svn->lp_height = -2;
                vs->add_child(row, sv);
            }
        }
        if (fnew304_pref_diag < 12) {
            ++fnew304_pref_diag;
            std::cerr << "[F-NEW-304] pref row " << i << " title=\"" << title
                      << "\" summary=\"" << summary << "\"" << std::endl;
        }
    }
    return root;
}

//     Lxb0;.d() unwrap → Dagger component — dooz23 Lk2;.b evidence).
// The runtime hands the manifest android:name class via
// set_application_class_hint(); self-discovery (single DEX class whose
// direct superclass is Landroid/app/Application;) covers callers that
// never parsed a manifest. Runs INSIDE execute_apk_with_activity after
// dex_report_ + secondary-DEX injection, so App.onCreate executes with
// full DEX infrastructure (the old runtime-side bind ran with
// dex_report=NULL — [TRY-ENTRY] dex_report=NULL evidence in run r340 —
// and dooz23's App.onCreate Dagger-component build silently degraded).
uint32_t DalvikExecutionEngine::bind_manifest_application(
    DalvikExecutionResult& result) {
    // F-C4-562 (4APP4 W3, Coder-4): installContentProviders NO LONGER runs
    // at bind entry. AOSP ActivityThread.handleBindApplication order is
    //   1. app = data.info.makeApplication(false, mInstrumentation)  // <init> + attach
    //   2. mInstrumentation.installContentProviders(app, data.providers)
    //   3. mInstrumentation.callApplicationOnCreate(app)
    // so the provider stage now runs on BOTH paths AFTER the Application
    // instance exists (see the install calls below), and providers get the
    // constructed app object as their Context — never a bare Context
    // singleton. (The old comment claimed this call covered the early
    // returns; it ran before them, inverting the AOSP order.)
    std::string app_class = application_class_hint_;
    if (!app_class.empty()) {
        // Normalize dotted/hint forms to descriptor form.
        if (app_class[0] != 'L') {
            std::replace(app_class.begin(), app_class.end(), '.', '/');
            if (app_class[0] != 'L') app_class = "L" + app_class;
            if (app_class.back() != ';') app_class += ";";
        }
    } else if (dex_report_ != nullptr) {
        // Self-discovery: exactly one app-bundled Application subclass.
        size_t hits = 0;
        for (const auto& cd : dex_report_->classes) {
            if (cd.superclass_name == "Landroid/app/Application;") {
                app_class = cd.name;
                ++hits;
            }
        }
        if (hits > 1) {
            std::cerr << "[R341-APP] ambiguous Application subclass set ("
                      << hits << " hits) — refusing to guess" << std::endl;
            app_class.clear();
        }
    }
    if (app_class.empty()) {
        // No custom Application class — AOSP default android.app.Application.
        DalvikValue app_singleton =
            get_or_create_singleton("Landroid/app/Application;");
        application_object_id_ = app_singleton.object_id;
        application_class_desc_ = "Landroid/app/Application;";
        std::cerr << "[R341-APP] default Application bound: obj#"
                  << application_object_id_ << std::endl;
        // F-C4-562 (4APP4 W3, Coder-4): AOSP handleBindApplication ORDER —
        // makeApplication(false) constructs the Application INSTANCE
        // BEFORE installContentProviders(app, providers); providers receive
        // the constructed app object as their Context (dagger.android
        // walks it for HasAndroidInjector; engine evidence: Nextcloud 35
        // FileContentProvider.onCreate → AndroidInjection.inject walked a
        // bare android.content.Context singleton because providers ran
        // before the app object existed → RuntimeException "android.content
        // Context does not implement dagger.android.HasAndroidInjector"
        // ×4 uncaught). Providers still run BEFORE app.onCreate (AOSP).
        install_content_providers(result);
        return application_object_id_;
    }
    if (class_to_superclass_.find(app_class) == class_to_superclass_.end()) {
        std::cerr << "[R341-APP] hint class " << app_class
                  << " not present in DEX — default Application fallback"
                  << std::endl;
        DalvikValue app_singleton =
            get_or_create_singleton("Landroid/app/Application;");
        application_object_id_ = app_singleton.object_id;
        application_class_desc_ = "Landroid/app/Application;";
        // F-C4-562: same AOSP order law as above (instance first, then
        // providers, then onCreate) on the fallback path.
        install_content_providers(result);
        return application_object_id_;
    }

    uint32_t app_obj_id = heap_.allocate(app_class, 0, 0);
    if (app_obj_id == 0) {
        std::cerr << "[R341-APP] heap allocation failed for " << app_class
                  << std::endl;
        return 0;
    }
    std::cerr << "[R341-APP] instantiating Application " << app_class
              << " obj#" << app_obj_id << " (post-DEX-inject, AOSP order)"
              << std::endl;

    application_object_id_ = app_obj_id;
    application_class_desc_ = app_class;

    // <init>()V — instance-field initializers (dooz App: flag e=false +
    // Lpc; lazy Dagger-holder construction).
    try {
        DalvikValue this_val = DalvikValue::make_object(app_obj_id, app_class);
        DalvikValue ret;
        std::vector<DalvikValue> init_args;
        init_args.push_back(this_val);
        bool ok = try_recursive_invoke(app_class, "<init>", init_args, ret,
                                       result, "()V");
        std::cerr << "[R341-APP] <init> " << (ok ? "OK" : "SKIPPED")
                  << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "[R341-APP] <init> threw (recorded, bind continues): "
                  << e.what() << std::endl;
    }
    // attachBaseContext(Context) — AOSP binds the app context here.
    // S89 F-NEW-184: the base context is NEVER null — AOSP LoadedApk calls
    //   app.attachBaseContext(context) (Instrumentation.newApplication's
    // context) BEFORE any app code runs, and ContextWrapper stores it as
    // mBase. The previous behavior pushed DalvikValue::make_null() —
    // fine when apps never override attachBaseContext (REC-MISS no-op),
    // but Kotlin apps that DO override it run their compiler-inserted
    // `context.checkNotNullParameter("context")` FIRST (R8 inlines
    // Intrinsics into androidx.multidex.ZipUtil) → immediate
    //   NPE "Parameter specified as non-null is null: ... attachBaseContext,
    // parameter context"
    // at APP BOUNDARY (secuso pfacore torchlight: whole app died before
    // onCreate). LAW: bind the engine's application context object (the
    // R341-APP instance doubles as the engine's Context — the same object
    // getApplicationContext() serves), preserving AOSP ordering.
    try {
        DalvikValue this_val = DalvikValue::make_object(app_obj_id, app_class);
        DalvikValue ret;
        std::vector<DalvikValue> attach_args;
        attach_args.push_back(this_val);
        attach_args.push_back(this_val);  // F-NEW-184: the REAL base context
        try_recursive_invoke(app_class, "attachBaseContext", attach_args, ret,
                             result);
    } catch (const std::exception&) {
        // no-op — not every app class declares it
    }
    // S-1 FIX (LOADING-CAMPAIGN): the provider stage moved to
    // install_content_providers(), called AFTER the Application <init> +
    // attachBaseContext and BEFORE Application.onCreate below — the AOSP
    // handleBindApplication order (makeApplication → installContentProviders
    // → callApplicationOnCreate). F-C4-562 (4APP4 W3, Coder-4) fixed the
    // inversion: providers used to install at bind ENTRY, before the app
    // object existed, so attachInfo handed every provider the bare Context
    // singleton (Nextcloud AndroidInjection evidence above).
    install_content_providers(result);

    // onCreate() — the REAL component build runs here (dooz: flag guard +
    // Lpc;.d() → Dagger SingletonComponent Lps; graph).
    try {
        DalvikValue this_val = DalvikValue::make_object(app_obj_id, app_class);
        DalvikValue ret;
        std::vector<DalvikValue> create_args;
        create_args.push_back(this_val);
        size_t before = result.total_instructions_executed;
        bool ok = try_recursive_invoke(app_class, "onCreate", create_args, ret,
                                       result);
        std::cerr << "[R341-APP] onCreate "
                  << (ok ? "OK" : "SKIPPED") << " ins="
                  << (result.total_instructions_executed - before) << std::endl;
    } catch (const std::exception& e) {
        // AOSP would kill the process; the engine degrades gracefully and
        // keeps the evidence honest in the log.
        std::cerr << "[R341-APP] onCreate threw (recorded, bind continues): "
                  << e.what() << std::endl;
    }

    // Telegram contract (EXP-043): ApplicationLoader.applicationContext
    // static field carries the REAL bound application object now.
    static_field_storage_["Lorg/telegram/messenger/ApplicationLoader;.applicationContext"] =
        DalvikValue::make_object(app_obj_id, app_class);

    // Publish the identity to the Activity shadow so the shadow-side
    // getApplicationContext() serves the SAME object (dual-dispatch law:
    // engine P0.7 and shadows must never disagree on object identity).
    if (shadow_registry_ != nullptr) {
        auto* activity_shadow =
            shadow_registry_->find_as<framework::ActivityShadow>();
        if (activity_shadow != nullptr) {
            activity_shadow->set_application_heap_identity(app_obj_id,
                                                           app_class);
            std::cerr << "[R341-APP] identity published to ActivityShadow"
                      << std::endl;
        }
    }
    return app_obj_id;
}

// ── F-058 (R-NEW-279): Application.dispatchActivity* fan-out ────────────
// AOSP ActivityThread law: each activity lifecycle transition is reported
// to every registered Application.ActivityLifecycleCallbacks, in
// registration order. The observer receives (this, activity[, bundle]).
// Signature law (Application$ActivityLifecycleCallbacks, API 34):
//   onActivityPreCreated(Activity, Bundle) / onActivityCreated(Activity, Bundle)
//   onActivityPostCreated(Activity, Bundle)
//   onActivityPreStarted/Started/PostStarted(Activity)
//   onActivityPreResumed/Resumed/PostResumed(Activity)   [+ Paused/Stopped/
//   SaveInstanceState(Bundle)/Destroyed pairs]
// try_recursive_invoke returning false = observer lacks that method =
// AOSP default no-op — skipped, never an error. Exceptions inside one
// observer must not starve the others (AOSP dispatches sequentially; an
// observer throw propagates to the app — here it is recorded and the
// fan-out continues, the failure-honesty record keeps the evidence).
size_t DalvikExecutionEngine::dispatch_activity_lifecycle_callbacks(
    const std::string& event, DalvikExecutionResult& result) {
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    if (!as) return 0;
    const auto& cbs = as->lifecycle_callbacks();
    if (cbs.empty()) return 0;
    // The event's activity argument is the CURRENT activity (AOSP: the
    // activity whose lifecycle is transitioning).
    uint32_t act_id = as->current_activity_id();
    const std::string& act_cls = as->current_activity_class();
    if (act_id == 0 || !heap_.has_object(act_id)) return 0;
    // Bundle argument: non-null only for the Created/SaveInstanceState
    // families (AOSP passes the saved-state Bundle there, the hot path
    // (re)launch passes the intent extras bundle; the interpreter's shadow
    // Bundle answers — a null Bundle is the documented first-launch case).
    const bool wants_bundle =
        event == "onActivityPreCreated" || event == "onActivityCreated" ||
        event == "onActivityPostCreated" ||
        event == "onActivitySaveInstanceState" ||
        event == "onActivityPreDestroyed" || event == "onActivityDestroyed" ||
        event == "onActivityPostDestroyed";
    size_t dispatched = 0;
    for (const auto& cb : cbs) {
        if (!heap_.has_object(cb.oid)) continue;  // GC'd observer — skip
        std::vector<DalvikValue> args;
        args.push_back(DalvikValue::make_object(cb.oid, cb.cls));   // p0 = this
        args.push_back(DalvikValue::make_object(act_id, act_cls));  // p1 = activity
        if (wants_bundle) args.push_back(DalvikValue::make_null()); // p2 = Bundle
        DalvikValue ret;
        size_t before = result.total_instructions_executed;
        bool ok = false;
        try {
            ok = try_recursive_invoke(cb.cls, event, args, ret, result);
        } catch (const std::exception& e) {
            std::cerr << "[F058] observer threw during " << event << " obs="
                      << cb.oid << " cls=" << cb.cls << " err=" << e.what()
                      << std::endl;
            continue;
        }
        if (ok) {
            dispatched++;
            std::cerr << "[F058-DISPATCH] " << event << " -> " << cb.cls
                      << " obs=" << cb.oid
                      << " ins=" << (result.total_instructions_executed - before)
                      << std::endl;
        }
    }
    if (dispatched > 0) {
        std::cerr << "[F058] " << event << " fan-out: " << dispatched << "/"
                  << cbs.size() << " observers executed" << std::endl;
    }
    return dispatched;
}

// F-074 (S21) — ART virtual-dispatch law for engine-level invokes.
// See dalvik_engine.h for the root-cause evidence chain. Walks the DEX
// superclass chain and retries try_recursive_invoke on the first ancestor
// that declares the method with bytecode. The receiver (args[0]) keeps its
// ORIGINAL object identity — an inherited method executes with the runtime
// receiver, exactly as ART resolves invokevirtual/interface invokes.
bool DalvikExecutionEngine::try_recursive_invoke_on_super(
    const std::string& declaring_class,
    const std::string& method_name,
    const std::vector<DalvikValue>& args,
    DalvikValue& return_val,
    DalvikExecutionResult& result,
    const std::string& method_descriptor
) {
    if (!dex_report_) return false;
    // Bounded climb: real chains are shallow (DispatchedContinuation →
    // DispatchedTask → Task → Object = 3 hops); 16 covers any sane hierarchy
    // while a corrupted-DEX cycle cannot loop forever.
    static constexpr int kMaxSuperHops = 16;
    std::string walk = declaring_class;
    for (int hop = 0; hop < kMaxSuperHops; ++hop) {
        auto sup_it = class_to_superclass_.find(walk);
        if (sup_it == class_to_superclass_.end()) return false;
        const std::string sup = sup_it->second;  // copy: map may rehash on retry
        if (sup.empty() || sup == "Ljava/lang/Object;") return false;
        auto cit = class_info_index_.find(sup);
        if (cit != class_info_index_.end()) {
            const dex::ClassInfo& sup_cls = dex_report_->classes[cit->second];
            // F-107c2: iterate direct+virtual tables in place (no copy) —
            // same order and same empty-bytecode skip as the old
            // all_methods() loop, zero MethodInfo copies.
            const auto f107c2_iter = [&](auto&& body) {
                for (const auto& m : sup_cls.direct_methods) {
                    if (m.name != method_name || m.bytecode.empty()) continue;
                    if (body(m)) return true;
                }
                for (const auto& m : sup_cls.virtual_methods) {
                    if (m.name != method_name || m.bytecode.empty()) continue;
                    if (body(m)) return true;
                }
                return false;
            };
            bool dispatched_f107c2 = f107c2_iter([&](const auto& m) {
                // S55: the F-074 forensic trace used to be ALWAYS-ON
                // stderr — including a heap message lookup per dispatch.
                // Compose-heavy apps make MILLIONS of inherited calls;
                // the trace throttled them to ~1.6K instr/s (Dooz v18
                // could not reach its first frame inside 10 minutes).
                // The LAW (receiver-identity super dispatch) is the code
                // below; the TRACE is now env-gated (MINIANDROID_F074_TRACE).
                static const bool f074_trace =
                    diag_env("MINIANDROID_F074_TRACE");
                if (!f074_trace) {
                    return try_recursive_invoke(sup, method_name, args,
                                                return_val, result,
                                                method_descriptor);
                }
                std::cerr << "[F074-SUPER-DISPATCH] " << declaring_class << "."
                          << method_name << " not declared locally → ancestor "
                          << sup << "." << m.name << m.descriptor
                          << " (receiver identity preserved)";
                // S21 forensics: exception-object arguments (handleFatal-
                // Exception family) carry the thrown Throwable in args —
                // surface its message so the fatal cause is visible without
                // a DEX re-disassembly. Read-only; heap lookups only.
                for (size_t ai = 0; ai < args.size(); ++ai) {
                    const DalvikValue& a = args[ai];
                    if (a.type != DalvikType::OBJECT_REF || a.object_id == 0)
                        continue;
                    std::cerr << " a" << ai << "=o" << a.object_id;
                    if (!a.class_desc.empty())
                        std::cerr << "(" << a.class_desc << ")";
                    auto mv = heap_.get_object_field(a.object_id, "message");
                    if (mv.has_value() && mv->type == DalvikType::STRING_REF &&
                        !mv->string_val.empty())
                        std::cerr << "=\"" << mv->string_val.substr(0, 120)
                                  << "\"";
                }
                std::cerr << std::endl;
                return try_recursive_invoke(sup, method_name, args, return_val,
                                            result, method_descriptor);
            });
            if (dispatched_f107c2) return true;
        }
        walk = sup;  // method not on this ancestor — keep climbing
    }
    return false;
}

// ─────────────────────────────────────────────────────────────────────────────
// CONT-12 F-NEW-266 — invoke-virtual TRANSITIVE INTERFACE-DEFAULT dispatch.
// ART/JVMS 5.4.5 resolution law: when the receiver's class chain declares no
// implementation, the resolution continues into every transitively
// implemented interface; the first code-bearing (default) method with the
// exact descriptor executes. The invoke-interface path already implements
// this (F-023, see execute_invoke_interface); invoke-virtual historically
// fell through to the API bridge, whose stub silently returned NULL — the
// null then fed the next instruction (dooz-native evidence: none; external
// un-renamed Compose 1.11.4 oracle: AndroidComposeView$root$1$1.then(other)
// → interface Modifier.then default body → null receiver → NPE ×172 →
// setContent dead). Generic: no app, package, or R8-name knowledge.
// Bounded: 12-hop extends chain, 64-interface closure, memoized results.
// ─────────────────────────────────────────────────────────────────────────────
bool DalvikExecutionEngine::try_interface_default_invoke(
    const std::string& receiver_class,
    const std::string& method_name,
    const std::string& method_descriptor,
    const std::vector<DalvikValue>& args,
    DalvikValue& return_val,
    DalvikExecutionResult& result,
    std::string* dispatched_out) {
    if (!dex_report_) return false;
    if (method_descriptor.empty()) return false;

    // ── F-NEW-266a (CONT-16): ART NULL-RECEIVER LAW on the default-method
    // route. A typed-null receiver must throw NullPointerException AT THE
    // CALL SITE, before ANY callee body runs (ART interpreter law — the
    // same F-141 gate the generic invoke-interface path enforces before
    // its dispatch walk). The default-method route bypassed that gate: the
    // resolution/memo machinery below is a property of the METHOD REF, so
    // it dispatched the default body for a null receiver (probe face:
    // fixtures/f266_probe row D — OtherDefI.other() on a typed null
    // answered without NPE). The gate must precede the memo lookup: NPE is
    // a receiver property, not a resolution property.
    if (!args.empty() && f141_is_null_receiver(args[0])) {
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke interface method '" + receiver_class +
                           "." + method_name + "' on a null object reference",
                       "f266a-null-recv");
        return true;
    }

    // Memo key: method ref identity (class.name + proto). The receiver's
    // runtime class does NOT participate: the resolution result is a
    // property of the method ref and the implementing interface, and the
    // default body executes with the ORIGINAL receiver either way.
    const std::string memo_key =
        receiver_class + "." + method_name + method_descriptor;
    {
        auto it = iface_default_memo_.find(memo_key);
        if (it != iface_default_memo_.end()) {
            if (it->second.first.empty()) return false;  // negative memo
            return try_recursive_invoke(it->second.first, it->second.second,
                                        args, return_val, result,
                                        method_descriptor);
        }
    }

    // Resolution gate: only for app-bundled (DEX-defined) method refs —
    // framework refs (Landroid/*, Ljava/*) belong to the API bridge and
    // must not pay the closure scan.
    if (class_info_index_.find(receiver_class) == class_info_index_.end()) {
        iface_default_memo_[memo_key] = {"", ""};  // negative memo
        return false;
    }

    // 1. Receiver extends chain (bounded, mirrors F-023).
    std::vector<std::string> cls_chain;
    std::string cc = receiver_class;
    for (int hop = 0; hop < 12 && !cc.empty() &&
                      cc != "Ljava/lang/Object;"; ++hop) {
        cls_chain.push_back(cc);
        auto sit = class_to_superclass_.find(cc);
        if (sit == class_to_superclass_.end()) break;
        cc = sit->second;
    }

    // 2. Transitive interface closure (declared interfaces of every class
    //    in the chain, closed over super-interfaces, bounded at 64).
    std::vector<std::string> ifq;
    std::set<std::string> visited;
    auto enqueue_ifaces = [&](const std::string& cls) {
        for (const auto& cd : dex_report_->classes) {
            if (cd.name != cls) continue;
            for (const auto& ifc : cd.interfaces) {
                if (!ifc.empty() && visited.insert(ifc).second)
                    ifq.push_back(ifc);
            }
            break;
        }
    };
    for (const auto& k : cls_chain) enqueue_ifaces(k);
    for (size_t qi = 0; qi < ifq.size() && qi < 64; ++qi)
        enqueue_ifaces(ifq[qi]);

    // 3. Dispatch the first code-bearing method with the exact descriptor.
    //    Exact-descriptor match keeps overloaded defaults unambiguous, and
    //    the class-def linear scan matches the F-023 cost envelope.
    for (const auto& ifc : ifq) {
        for (const auto& cd : dex_report_->classes) {
            if (cd.name != ifc) continue;
            for (const auto& mi : cd.all_methods()) {
                if (mi.code_offset == 0 || mi.is_abstract) continue;
                if (mi.descriptor != method_descriptor) continue;
                if (mi.name != method_name) continue;
                if (try_recursive_invoke(ifc, mi.name, args, return_val,
                                         result, method_descriptor)) {
                    iface_default_memo_[memo_key] = {ifc, mi.name};
                    if (dispatched_out)
                        *dispatched_out = ifc + "." + mi.name;
                    static std::atomic<uint64_t> f266_n{0};
                    if (f266_n.fetch_add(1, std::memory_order_relaxed) < 24) {
                        std::cerr << "[INTERFACE-DEFAULT-V] " << ifc << "."
                                  << mi.name << method_descriptor
                                  << " (invoke-virtual default-method dispatch"
                                  << ", receiver " << receiver_class << ")"
                                  << std::endl;
                    }
                    return true;
                }
            }
            break;
        }
    }
    if (iface_default_memo_.size() < 4096)
        iface_default_memo_[memo_key] = {"", ""};  // negative memo
    return false;
}

} // namespace dalvik
} // namespace miniandroid
