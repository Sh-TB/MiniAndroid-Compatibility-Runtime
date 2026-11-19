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

// ── S71 ROOT LAW #1: ancestry dispatch helper ──────────────────────────────
// Walks the receiver's superclass chain — DEX chain via class_to_superclass_
// (populated from every loaded dex at :568/:718) plus the built-in AOSP
// platform hierarchy (framework supers are NOT in the APK's DEX) — and
// returns the nearest ancestor name that the substring dispatch guards can
// see (Context/Activity/Service/Application families), or "" when the
// receiver has no framework ancestor. Bounded: 12 DEX hops max; the
// platform table itself terminates at Context (terminal, not a key).
// Platform hierarchy source: AOSP Application/Service/Activity/ContextWrapper
// class declarations (docs/upstream/aosp/CONTEXT_STRING_LAW.md pin).
std::string DalvikExecutionEngine::framework_ancestor_for_dispatch(
    const std::string& cls) {
    static const char* kGuardFamilies[] = {"Context", "Activity", "Service",
                                           "Application"};
    auto matches_guard_family = [&](const std::string& c) {
        for (const char* f : kGuardFamilies)
            if (c.find(f) != std::string::npos) return true;
        return false;
    };
    // AOSP platform hierarchy (class → direct superclass).
    static const std::map<std::string, std::string> kPlatformSuper = {
        {"Landroid/app/Application;", "Landroid/content/Context;"},
        {"Landroid/app/Service;", "Landroid/content/Context;"},
        {"Landroid/app/Activity;", "Landroid/content/ContextThemeWrapper;"},
        {"Landroid/app/Dialog;", "Landroid/content/Context;"},
        {"Landroid/content/ContextThemeWrapper;", "Landroid/content/Context;"},
        {"Landroid/content/ContextWrapper;", "Landroid/content/Context;"},
    };
    std::string cur = cls;
    for (int hop = 0; hop < 12 && !cur.empty(); ++hop) {
        auto it = class_to_superclass_.find(cur);
        std::string sup = (it != class_to_superclass_.end()) ? it->second : "";
        if (sup.empty()) {
            auto pit = kPlatformSuper.find(cur);
            if (pit != kPlatformSuper.end()) sup = pit->second;
        }
        if (sup.empty()) break;
        if (matches_guard_family(sup)) return sup;
        cur = sup;
    }
    return "";
}

// F-150 (S72-W4): hierarchy-aware Thread receiver test. Ground truth:
// zhangman.github.snake @ b4968c39 — GameMainThread.run's unqualified
// sleep(1000/mSpeed) compiles to invoke-static
// Lzhangman/github/snake/SnakePanelView$GameMainThread;->sleep(J)V (javac
// emits the SUBCLASS descriptor for inherited static members), and
// reStartGame's new GameMainThread().start() compiles to invoke-virtual on
// the SUBCLASS. Literal `class_name == Thread` guards never saw those
// calls: the loop spun to the F-084 cap (silent wrongness, §038). The
// DEX superclass chain (class_to_superclass_, loaded from every dex)
// resolves the receiver to Thread; Object terminates the walk.
bool DalvikExecutionEngine::is_thread_receiver(const std::string& cls) {
    if (cls == "Ljava/lang/Thread;") return true;
    std::string cur = cls;
    for (int hop = 0; hop < 12 && !cur.empty(); ++hop) {
        auto it = class_to_superclass_.find(cur);
        if (it == class_to_superclass_.end()) return false;
        cur = it->second;
        if (cur == "Ljava/lang/Thread;") return true;
        if (cur == "Ljava/lang/Object;") return false;
    }
    return false;
}

// EXP-042 Phase 4: Singleton cache helper.
// Returns an existing heap object for the given class descriptor, or allocates
// a fresh one. Cached in api_singletons_ so that getResources() always returns
// the same Resources object across the entire APK execution.
// ── S88 F-NEW-179 — keyed-by-path directory File law ────────────────
// AOSP ContextImpl.getFilesDir/getCacheDir/getExternalFilesDir(“none”)/
// getExternalCacheDir each return a STABLE File for that directory,
// carrying its own path. The previous class-keyed singleton answered the
// SAME pathless File for all four — File.getParentFile then computed no
// parent and answered null (microtimer single-instance guard NPE at
// h/f.v getParentFile).
DalvikValue DalvikExecutionEngine::get_or_create_dir_file(const std::string& path) {
    static const std::string kFileDesc = "Ljava/io/File;";
    // GATE A (issue #370): an application NEVER sees a host path (AOSP
    // ContextImpl law). Store-internal host backings map to their
    // ANDROID-LOGICAL spelling (/data/data/<pkg>/…, /data/app/<pkg>/…,
    // /storage/emulated/0/…, /system/fonts/…) BEFORE the File object is
    // minted; the physical mapping happens in resolve_android_path at
    // open time. Non-store paths (Environment statics, device nodes)
    // pass through unchanged.
    std::string visible = Storage::logical_android_path(path);
    if (visible.empty()) visible = path;
    auto it = dir_files_.find(visible);
    if (it != dir_files_.end() && heap_.has_object(it->second)) {
        DalvikValue v;
        v.type = DalvikType::OBJECT_REF;
        v.object_id = it->second;
        v.class_desc = kFileDesc;
        return v;
    }
    const uint32_t obj_id = heap_.allocate(
        kFileDesc, pc_, call_stack_.empty() ? 0 : call_stack_.top().frame_id);
    heap_.set_object_field(obj_id, "path", DalvikValue::make_string(visible, 0));
    dir_files_[visible] = obj_id;
    DalvikValue v;
    v.type = DalvikType::OBJECT_REF;
    v.object_id = obj_id;
    v.class_desc = kFileDesc;
    return v;
}

// ── S186h F-NEW-188c — obfuscated androidx FragmentManager REAL-INIT law ──
// Probe (tibarj.tranquilstopwatch #170, fresh store, real-dalvik trace):
//   FCV internal ctor (kept name — referenced from layout XML) calls the
//   R8-renamed FragmentManager body: `Lb1/t0;.A(I)Lb1/a0;` (=
//   findFragmentById) reads `Lb0/k;.a` (the fragment store) at its pc=2
//   and NPEs because the F-NEW-188 singleton was minted under the
//   CANONICAL name with an empty field set — the FM <init> never ran.
//   The existing F-NEW-188b findFragmentById intercept is name-keyed and
//   cannot fire on obfuscated method names (A/B/C…), so the real body
//   executed on empty state.
// LAW (generic, Rule 6 — semantics not names):
//   1. The app's REAL FragmentManager class is recoverable STRUCTURALLY:
//      FragmentContainerView's internal constructor signature is
//      (Context, AttributeSet, L<real-fm>;) — R8 can rename FragmentManager
//      but NOT FragmentContainerView (kept for XML) and NOT the signature.
//   2. Mint ONE object; alias BOTH the canonical key and the real class
//      key to it (identity law F-NEW-188 preserved).
//   3. Execute the real <init>()V of the real class on that object ONCE.
//      The store fields then hold genuine androidx state and ANY obfuscated
//      method body executes lawfully — an empty manager answers the
//      androidx @Nullable null contract from its own bytecode tail
//      (measured: b1/t0.A falls through to const/4 v6,0; return-object).
//      No synthetic null-return shim is added for the obfuscated path
//      (SQLITE Rule 1: vend the real behavior, don't rewrite it).
// NOTE: law state lives in function-local statics (NOT class members) —
//   adding members to DalvikExecutionEngine changes sizeof() and would ODR-
//   mismatch the other translation units' objects without a full rebuild
//   (measured S186h: mixed-layout relink crashed dooz golden in
//   std::string::_M_assign during APPLICATION_CREATE).
// F-C4-615b (W14): the INSTANCE-INDEPENDENT real-FM-class resolver.
// The engine object can be RECREATED between the provider phase and the
// activity phase (measured live, itsfrz: the S186h realinit bound
// api_singletons_["LU1/K;"]=obj#16 on the FIRST instance; the SECOND
// instance's map never got the binding because the realinit's static
// done-set still held oid 16 — function-local statics survive instances
// while member maps do not). This resolver runs off the DEX REPORT
// (instance-shared) with its own file-scope cache, so ANY instance can
// re-derive the class name.
static std::string g_w14_resolved_real_fm_class_;
static bool g_w14_resolved_real_fm_done_ = false;

const std::string& w14_resolve_real_fm_class(
    const dex::DexReport* dex_report) {
    if (!g_w14_resolved_real_fm_done_) {
        g_w14_resolved_real_fm_done_ = true;
        if (dex_report != nullptr) {
            const std::string fcv =
                "Landroidx/fragment/app/FragmentContainerView;";
            for (const auto& cls : dex_report->classes) {
                if (cls.name != fcv) continue;
                for (const auto& m : cls.direct_methods) {
                    if (!m.is_constructor) continue;
                    // Internal ctor = 3 params: (Context, AttributeSet, FM)
                    if (m.parameters.size() != 3) continue;
                    const std::string& third = m.parameters[2];
                    if (third.size() > 2 && third[0] == 'L' &&
                        third != fcv &&
                        third != "Landroidx/fragment/app/FragmentManager;") {
                        g_w14_resolved_real_fm_class_ = third;
                    }
                }
                break;
            }
        }
        if (!g_w14_resolved_real_fm_class_.empty()) {
            std::cerr << "[F-NEW-188c/W14] resolved real FM class = "
                      << g_w14_resolved_real_fm_class_ << std::endl;
        }
    }
    return g_w14_resolved_real_fm_class_;
}

void DalvikExecutionEngine::realinit_fragment_manager_singleton(uint32_t fm_oid) {
    static std::set<uint32_t>& done = *new std::set<uint32_t>();
    static std::string resolved_real_fm_class_;
    static bool real_fm_class_resolved_ = false;

    if (fm_oid == 0 || done.count(fm_oid)) return;

    if (!real_fm_class_resolved_) {
        real_fm_class_resolved_ = true;
        resolved_real_fm_class_ = w14_resolve_real_fm_class(dex_report_);
        if (!resolved_real_fm_class_.empty()) {
            std::cerr << "[F-NEW-188c] resolved real FM class = "
                      << resolved_real_fm_class_ << std::endl;
        } else {
            std::cerr << "[F-NEW-188c] no obfuscated FM signature found "
                         "(canonical androidx layout) — real-init skipped"
                      << std::endl;
        }
    }

    const std::string& real_fm = resolved_real_fm_class_;
    if (real_fm.empty()) return;

    // Identity law: ONE object, TWO keys (canonical + real class).
    auto it = api_singletons_.find(real_fm);
    if (it != api_singletons_.end() && it->second != fm_oid) {
        std::cerr << "[F-NEW-188c] WARNING real-FM key already bound to obj#"
                  << it->second << " (kept existing binding)" << std::endl;
        return;
    }
    api_singletons_[real_fm] = fm_oid;

    // Run the real <init>()V ONCE on the shared object.
    done.insert(fm_oid);
    DalvikValue rv;
    DalvikExecutionResult res;
    std::vector<DalvikValue> args;
    args.push_back(DalvikValue::make_object(fm_oid, real_fm));
    bool ok = try_recursive_invoke(real_fm, "<init>", args, rv, res);
    std::cerr << "[F-NEW-188c] real-init " << real_fm << " obj#" << fm_oid
              << " ok=" << (ok ? 1 : 0) << std::endl;
}

DalvikValue DalvikExecutionEngine::get_or_create_singleton(const std::string& class_desc) {
    auto it = api_singletons_.find(class_desc);
    if (it != api_singletons_.end()) {
        // Verify the object still exists in the heap
        if (heap_.has_object(it->second)) {
            DalvikValue v;
            v.type = DalvikType::OBJECT_REF;
            v.object_id = it->second;
            v.class_desc = class_desc;
            return v;
        }
        // CONT-94 probe (bounded): a cached singleton whose heap object is
        // gone is an identity break — log it instead of silently reallocating.
        static thread_local uint64_t c94_stale = 0;
        if (class_desc.find("LaunchActivity") != std::string::npos &&
            c94_stale < 8) {
            ++c94_stale;
            std::cerr << "[C94-SINGLETON] STALE cached " << class_desc
                      << " id=" << it->second << " (heap object missing)"
                      << std::endl;
        }
    }
    // CONT-94 probe (bounded): which key missed, and what we allocate.
    static thread_local uint64_t c94_miss = 0;
    bool c94_probe = class_desc.find("LaunchActivity") != std::string::npos;
    if (c94_probe && c94_miss < 8) {
        ++c94_miss;
        std::cerr << "[C94-SINGLETON] MISS " << class_desc
                  << " (no cache entry) -> allocating new" << std::endl;
    }
    uint32_t obj_id = heap_.allocate(class_desc, pc_,
                                    call_stack_.empty() ? 0 : call_stack_.top().frame_id);
    api_singletons_[class_desc] = obj_id;
    if (c94_probe && c94_miss <= 8) {
        std::cerr << "[C94-SINGLETON] allocated " << class_desc
                  << " obj#" << obj_id << std::endl;
    }
    // Pre-populate known fields for some singletons
    if (class_desc == "Landroid/util/DisplayMetrics;") {
        DalvikValue density;
        density.type = DalvikType::FLOAT32;
        density.float_val = 2.625f;  // THE device-density law (F-149: was
                                     // 1.0 — silently diverged from the
                                     // inflater DeviceMetrics authority)
        heap_.set_object_field(obj_id, "density", density);
        DalvikValue density_dpi;
        density_dpi.type = DalvikType::INT32;
        density_dpi.int_val = 420;  // DENSITY_420 — matches 2.625 density
        heap_.set_object_field(obj_id, "densityDpi", density_dpi);
        DalvikValue scaled_d;
        scaled_d.type = DalvikType::FLOAT32;
        scaled_d.float_val = 2.625f;  // fontScale 1.0 (F-023 default)
        heap_.set_object_field(obj_id, "scaledDensity", scaled_d);
        DalvikValue width_px;
        width_px.type = DalvikType::INT32;
        width_px.int_val = 1080;
        heap_.set_object_field(obj_id, "widthPixels", width_px);
        DalvikValue height_px;
        height_px.type = DalvikType::INT32;
        height_px.int_val = 1920;
        heap_.set_object_field(obj_id, "heightPixels", height_px);
    } else if (class_desc == "Landroid/content/res/Configuration;") {
        DalvikValue screen_layout;
        screen_layout.type = DalvikType::INT32;
        screen_layout.int_val = 0x40;  // SCREENLAYOUT_SIZE_NORMAL
        heap_.set_object_field(obj_id, "screenLayout", screen_layout);
        DalvikValue orientation;
        orientation.type = DalvikType::INT32;
        orientation.int_val = 1;  // ORIENTATION_PORTRAIT
        heap_.set_object_field(obj_id, "orientation", orientation);
        // F-023 (AOSP Configuration.setToDefaults law): fontScale defaults
        // to 1.0f on a fresh Configuration. Material3's non-linear font
        // scaling path check()s "fontScale > 1" when the app opts into
        // non-linear scaling — with an unset (0.0) fontScale the check
        // throws "You should only apply non-linear scaling to font scales
        // > 1" during the FIRST composition (dooz M1/i.f chain, Material3
        // Typography init). Real devices report the user's fontScale
        // (default 1.0 = no scaling).
        DalvikValue font_scale;
        font_scale.type = DalvikType::FLOAT32;
        font_scale.float_val = 1.0f;  // AOSP Configuration.setToDefaults()
        heap_.set_object_field(obj_id, "fontScale", font_scale);
    } else if (class_desc == "Ljava/io/File;") {
        DalvikValue path;
        path.type = DalvikType::STRING_REF;
        path.string_val = "/tmp/miniandroid/files";
        path.ref_id = 0;
        heap_.set_object_field(obj_id, "path", path);
    }
    DalvikValue v;
    v.type = DalvikType::OBJECT_REF;
    v.object_id = obj_id;
    v.class_desc = class_desc;
    return v;
}

// ============================================================================
// Utility Methods
// ============================================================================

void DalvikExecutionEngine::log(const std::string& msg) {
    if (verbose_) {
        std::cerr << "[DalvikEngine] " << msg << std::endl;
    }
}

std::string DalvikExecutionEngine::to_hex(uint32_t val) const {
    std::ostringstream o;
    o << "0x" << std::hex << val;
    return o.str();
}

std::string DalvikExecutionEngine::to_hex16(uint16_t val) const {
    std::ostringstream o;
    o << "0x" << std::hex << std::setw(4) << std::setfill('0') << val;
    return o.str();
}

int32_t DalvikExecutionEngine::read_signed_literal(uint16_t val) const {
    // Sign-extend 16-bit to 32-bit
    return static_cast<int32_t>(static_cast<int16_t>(val));
}

std::string DalvikExecutionEngine::get_timestamp() const {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::ostringstream ss;
    ss << std::put_time(std::gmtime(&time_t), "%Y-%m-%dT%H:%M:%SZ");
    return ss.str();
}

// ============================================================================
// Execution Result Serialization
// ============================================================================

json DalvikExecutionResult::to_full_report() const {
    json report;
    report["experiment"] = experiment_id;
    report["timestamp"] = timestamp;
    report["apk"] = apk_name;
    report["sha256"] = apk_sha256;
    
    report["entry_point"] = {
        {"class", main_class},
        {"method", main_method}
    };
    
    report["final_status"] = [this]() -> std::string {
        switch (final_status) {
            case FinalStatus::COMPLETED_SUCCESS: return "SUCCESS";
            case FinalStatus::COMPLETED_PARTIAL: return "PARTIAL";
            case FinalStatus::HALTED_UNIMPLEMENTED_OPCODE: return "HALTED_OPCODE";
            case FinalStatus::HALTED_MISSING_METHOD: return "HALTED_METHOD";
            case FinalStatus::HALTED_API_ERROR: return "HALTED_API";
            case FinalStatus::HALTED_STACK_OVERFLOW: return "HALTED_STACK";
            case FinalStatus::CRASH_EXCEPTION: return "CRASH";
            default: return "UNKNOWN";
        }
    }();
    
    report["halt_reason"] = halt_reason;
    
    report["statistics"] = {
        {"instructions_executed", total_instructions_executed},
        {"opcodes_decoded", total_opcodes_decoded},
        {"execution_ms", total_execution_ms},
        {"heap_objects", heap.size()},
        {"max_call_depth", call_stack.max_depth()},
        {"total_calls", call_stack.get_completed_frames().size()}
    };
    
    report["call_stack"] = call_stack.dump_all_calls();
    report["heap"] = heap.dump();
    
    report["instruction_traces"] = json::array();
    for (const auto& t : instruction_traces) {
        report["instruction_traces"].push_back(t.to_json());
    }
    
    report["api_calls"] = json::array();
    for (const auto& c : api_call_traces) {
        report["api_calls"].push_back(c.to_json());
    }
    
    report["final_registers"] = final_registers;
    
    return report;
}

} // namespace dalvik
} // namespace miniandroid
