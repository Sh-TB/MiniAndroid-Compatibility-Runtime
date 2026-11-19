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

#include "dalvik_engine_impl.h"
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
bool DalvikExecutionEngine::execute_new_instance(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];
    
    // EXP-058: Use per-DEX type resolution instead of merged global types.
    // type_idx is relative to the current DEX file's type_ids table.
    std::string class_desc = resolve_type_for_dex(type_idx, current_dex_index_);
    if (class_desc == "<unknown>" && dex_report_ && type_idx < dex_report_->types.size()) {
        class_desc = dex_report_->types[type_idx];
    }
    
    // Allocate on heap
    uint32_t frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    uint32_t obj_id = heap_.allocate(class_desc, pc, frame_id);

    // ── S222-A F-023b (AOSP Configuration.setToDefaults + the F-149
    // device-density law): framework objects materialized via new-instance
    // start ZERO-FILLED on the heap. ART runs the framework class's own
    // field initializers (Configuration.<init> → setToDefaults:
    // fontScale=1.0, densityDpi from the device, locale non-null;
    // DisplayMetrics: density/densityDpi/scaledDensity/widthPixels/
    // heightPixels). Live face (dooz s222_baseline): the Compose
    // LocalDensity chain answered InlineDensity(density=2.625, fontScale=
    // 0.000000) — the Density wrapper read OUR heap Configuration whose
    // fontScale was still the raw 0.0 because that Configuration instance
    // was new-instance-materialized, never routed through the
    // get_or_create_singleton pre-populate (F-023 v1). The ONE device
    // identity law: every materialization path answers the same values.
    if (class_desc == "Landroid/content/res/Configuration;") {
        DalvikValue s222_fs;
        s222_fs.type = DalvikType::FLOAT32;
        s222_fs.float_val = 1.0f;  // AOSP Configuration.setToDefaults()
        heap_.set_object_field(obj_id, "fontScale", s222_fs);
        DalvikValue s222_dd;
        s222_dd.type = DalvikType::INT32;
        s222_dd.int_val = 420;  // the ONE device density (F-149/C9-22)
        heap_.set_object_field(obj_id, "densityDpi", s222_dd);
        DalvikValue s222_or;
        s222_or.type = DalvikType::INT32;
        s222_or.int_val = 1;  // ORIENTATION_PORTRAIT
        heap_.set_object_field(obj_id, "orientation", s222_or);
        DalvikValue s222_sl;
        s222_sl.type = DalvikType::INT32;
        s222_sl.int_val = 0x40;  // SCREENLAYOUT_SIZE_NORMAL
        heap_.set_object_field(obj_id, "screenLayout", s222_sl);
    } else if (class_desc == "Landroid/util/DisplayMetrics;") {
        DalvikValue s222_dm;
        s222_dm.type = DalvikType::FLOAT32;
        s222_dm.float_val = 2.625f;  // THE device-density law (F-149)
        heap_.set_object_field(obj_id, "density", s222_dm);
        DalvikValue s222_sd;
        s222_sd.type = DalvikType::FLOAT32;
        s222_sd.float_val = 2.625f;  // scaledDensity = density × fontScale 1.0
        heap_.set_object_field(obj_id, "scaledDensity", s222_sd);
        DalvikValue s222_ddm;
        s222_ddm.type = DalvikType::INT32;
        s222_ddm.int_val = 420;
        heap_.set_object_field(obj_id, "densityDpi", s222_ddm);
        DalvikValue s222_wp;
        s222_wp.type = DalvikType::INT32;
        s222_wp.int_val = 1080;
        heap_.set_object_field(obj_id, "widthPixels", s222_wp);
        DalvikValue s222_hp;
        s222_hp.type = DalvikType::INT32;
        s222_hp.int_val = 1920;
        heap_.set_object_field(obj_id, "heightPixels", s222_hp);
    }

    // CONT-38 (F-C4-545 evidence, DIAG-ONLY, env-gated): MINIANDROID_NEW_WATCH
    // = class-desc substring. Prints every new-instance of a watched class
    // with the allocating caller — answers "was the draw-block lambda EVER
    // constructed" without a fragile static scanner (the dooz board block
    // Lz6; never constructed = composition never reached the Canvas block).
    static thread_local const char* nw_env =
        std::getenv("MINIANDROID_NEW_WATCH");
    if (nw_env && nw_env[0] && !class_desc.empty() &&
        std::string(class_desc).find(nw_env) != std::string::npos) {
        static thread_local uint32_t nw_n = 0;
        if (nw_n++ < 200)
            std::cerr << "[NEW-WATCH] " << class_desc << " obj#" << obj_id
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc << std::endl;
    }
    // ── S222-A (DIAG-ONLY, env-gated MINIANDROID_S222_CACHE): the dooz
    // text-cache layout-result materialization probe. Ltw1; = the
    // TextLayoutResult holder (fields a=Lsw1; b=Lwu0; c:J=packed density;
    // the ONLY DEX constructor caller is Lex1;.q — the paragraph-layout
    // completion). If Ltw1; NEVER materializes, the MultiParagraphLayoutCache
    // textLayoutResult stays null and EVERY draw throws the upstream ISE
    // ("could not provide TextLayoutResult during the draw phase") — the
    // storm the S221 bridge could not close. This answers whether the
    // layout completion chain is EVER reached.
    if (class_desc == "Ltw1;") {
        static thread_local const bool s222_tw_on =
            diag_env("MINIANDROID_S222_CACHE");
        static thread_local uint32_t s222_tw_n = 0;
        if (s222_tw_on && s222_tw_n < 64)
            std::cerr << "[S222-TW1] Ltw1; obj#" << obj_id
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc << std::endl;
        ++s222_tw_n;
    }


    // DEMO-CLINIT (2026-09-04): per AOSP jvm.cc ClassLinker semantics,
    // new-instance is an ACTIVE USE of the class and must trigger
    // initialization (its <clinit>) before the instance is created.
    // Previously only sget/sput triggered initialization, so classes that
    // were first touched via new-instance ran with uninitialized statics.
    ensure_class_initialized(class_desc);
    // F-NEW-215: new-instance on an ERRONEOUS class raises
    // NoClassDefFoundError (JVMS 5.5 new-instance is active use).
    if (class_clinit_failed(class_desc) &&
        !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
        static std::atomic<uint64_t> f215_new_n{0};
        if (f215_new_n.fetch_add(1, std::memory_order_relaxed) < 8) {
            std::cerr << "[F-NEW-215] ACTIVE-USE new-instance class="
                      << class_desc << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
        throw_deferred("Ljava/lang/NoClassDefFoundError;",
                       class_desc + " <clinit> failed previously (erroneous class)",
                       "F-NEW-215");
        pc_ = pc + 2;
        return false;
    }

    // Store object reference in register
    set_register(dest_reg, DalvikValue::make_object(obj_id, class_desc));
    
    // EXP-061: Debug — trace new-instance for View/EditText/Button classes
    // to investigate why some views end up with object_id=0 in shadow dispatch.
    // EXP-089: Also trace LoginActivity creation (for Phase M1 verification).
    if (class_desc.find("EditText") != std::string::npos ||
        class_desc.find("TextView") != std::string::npos ||
        class_desc.find("Button") != std::string::npos ||
        class_desc.find("PhoneView") != std::string::npos ||
        class_desc.find("Keyboard") != std::string::npos ||
        class_desc.find("LoginActivity") != std::string::npos) {
        std::cerr << "[EXP061-NEW] new-instance " << class_desc
                  << " → v" << (int)dest_reg
                  << " obj_id=" << obj_id
                  << " pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << std::endl;
    }
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), class_desc});
    }
    trace.allocated_object_id = obj_id;
    
    // S157-B (CONT-42): the log() argument was built BEFORE the verbose
    // gate — concat + to_string heap churn per new-instance even when
    // verbose_ is false. Identical output when verbose, zero cost when not.
    if (verbose_) log("  ALLOCATED: " + class_desc + " -> obj#" + std::to_string(obj_id));
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_check_cast(uint32_t pc, InstructionTrace& trace) {
    // Format: 1c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix).
    std::string target_type = "<unknown>";
    target_type = resolve_type_for_dex(type_idx, current_dex_index_);

    // In full implementation, would check if register value is instance of target_type
    // For now, pass through (optimistic cast)
    DalvikValue val = get_register(reg);
    // If null or uninit, it's always ok
    if (val.type == DalvikType::NULL_REF || val.type == DalvikType::UNINITIALIZED ||
        val.type == DalvikType::REGISTER_UNSET) {
        // Null passes any check-cast
    }

    // F-090 (R-NEW-316): check-cast runtime-identity refinement.
    // ART law (dalvik bytecodes §check-cast / AOSP CheckCast.cc): the cast
    // ASSERTS the object is an instance of the target and the register's
    // static type is refined to the target; the OBJECT is untouched. This
    // engine carries a per-register class_desc that downstream identity
    // surfaces (Object.getClass F-088, Class.getAnnotation F-087 receiver,
    // EXP-059 runtime-type dispatch) read as the value's class. Without
    // refinement, the Kotlin idiom `map[key] as Navigator` left the register
    // poisoned with the container's declared type (Ljava/lang/Object; from
    // Map.get) — dooz addNavigator → nameForNavigator(read @Navigator.Name
    // off java.lang.Object) → IAE → MainActivity.onCreate died → blank Compose
    // frame. Refinement rule: the HEAP's runtime class is the identity
    // authority (EXP-059); use it when known, else refine to the cast target
    // (the verifier's static type). Optimistic pass retained (no ClassCast-
    // Exception yet — framework-side interface closure is not fully parsed;
    // a hard CCE here would wrongly reject valid framework casts).
    if (val.type == DalvikType::OBJECT_REF && val.object_id != 0) {
        // F-105 (S59, R-NEW-379): reconcile the register's creation-site
        // declaration with the heap record instead of letting the heap
        // record overwrite it unconditionally. The F-090 heap-authority
        // refinement poisoned view references whose id collides with an
        // unrelated heap object (activity-as-view: getParent result
        // declared Landroid/view/View; refined to heap#20's
        // MainActivity → the follow-up shadow dispatch lost the View
        // routing and the ViewTreeLifecycleOwner walk dead-ended).
        std::string runtime_desc =
            reconcile_class_decl(val.class_desc, val.object_id);
        std::string refined =
            !runtime_desc.empty() ? runtime_desc : target_type;
        if (!refined.empty() && refined != "<unknown>" &&
            refined != val.class_desc) {
            val.class_desc = refined;
            set_register(reg, val);
        }
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(reg), target_type});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_instance_of(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c [op vA vB] type@CCCC  — 2 code units
    // Encoding: cu[0] = BBBBAAAA_op (low byte = op, high nibble = vB, low nibble of high byte = vA)
    //           cu[1] = CCCC (type_idx)
    // EXP-092+ CRITICAL FIX: Previous code read dest/src from the wrong bit positions.
    //   dest = (instr >> 8) & 0xFF  → 0xc0 (full high byte) — WRONG, should be & 0x0F
    //   src  = instr & 0xFF         → 0x20 (the opcode!)   — WRONG, should be >> 12
    // This caused instance-of to read the wrong register and write to the wrong
    // register, producing garbage results. fillNextCodeParams' instance-of check
    // for TL_auth_sentCodeTypeFirebaseSms was returning true for ALL types
    // (including TL_auth_sentCodeTypeSms), causing the wrong page transition.
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0x0F;        // vA: low nibble of high byte
    uint8_t src = (instr >> 12) & 0x0F;        // vB: high nibble of high byte
    uint16_t type_idx = bytecode_[pc + 1];     // type@CCCC at pc+1 (not pc+2)

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix).
    std::string target_type = "<unknown>";
    target_type = resolve_type_for_dex(type_idx, current_dex_index_);

    // EXP-071: Use semantic superclass chain for instanceof check.
    // Previously this only did an EXACT class match (src_val.class_desc == target_type),
    // which failed for subclass checks like `obj instanceof Activity` when obj's
    // actual class is LaunchActivity (a subclass of Activity).
    // Now we use is_subclass_of() which walks the DEX superclass chain.
    DalvikValue src_val = get_register(src);
    bool is_instance = false;
    // F-105c (S59, R-NEW-379): INSTANCE-OF ON A CLASS TOKEN VALUE.
    // const-class (F-069/F-103) yields a CLASS_REF whose ref_id is the
    // heap-backed Ljava/lang/Class; token and whose class_desc is the
    // REFERENT descriptor (Lhb0; — the class the token represents, not
    // the token's own class). ART law: `X.class instanceof Y` classifies
    // the TOKEN — the token's runtime class IS java.lang.Class — so
    // `key instanceof Class` is TRUE for every class literal. Live face
    // (dooz v23): ViewModelProvider's ViewModelStore key guard
    // (Lwl0;.containsKey pc=0: instance-of key, Ljava/lang/Class; on the
    // KClass.java round-trip value stored via Ljj;->a) rejected the
    // CLASS_REF → IAE "Key must be a class" at depth 79 → APP BOUNDARY
    // unwind. Classify CLASS_REF values by the token's heap record.
    if (src_val.type == DalvikType::CLASS_REF) {
        // F-NEW-218 TOKEN-BACKING VALIDATION LAW (ART Object.getClass /
        // Class token identity): a Class token's runtime class IS
        // java.lang.Class — every CLASS_REF classifies as Ljava/lang/Class;
        // for the instanceof target, regardless of heap backing. The old
        // raw deref of ref_id adopted whatever heap record sat at that id
        // as the token's runtime class — but getClass answers tokens with
        // ref_id = instruction_sequence_ (an execution counter, NOT a heap
        // id) and the engine shares ONE integer id space (F-105's
        // premise), so the counter collides with live heap objects and the
        // token's classification became RANDOM (opencalculator vc53 face:
        // ArrayList.getClass() → `instanceof Class` FALSE → Gson
        // $Gson$Types.getRawType IAE "Expected a Class, ParameterizedType,
        // or GenericArrayType" at APP BOUNDARY → MainActivity.onCreate
        // aborted → empty frame). A heap record only backs a token when it
        // IS a Ljava/lang/Class; object — anything else at the shared id
        // belongs to a different entity (F-105 CONTRADICTION applied to
        // tokens). Detection is logged, bounded; classification stays
        // collision-proof.
        if (src_val.ref_id != 0 && heap_.has_object(src_val.ref_id)) {
            if (const auto* tok = heap_.get(src_val.ref_id);
                tok && !tok->class_descriptor.empty() &&
                tok->class_descriptor != "Ljava/lang/Class;") {
                static std::atomic<uint64_t> f218_n{0};
                if (f218_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                    std::cerr << "[F-NEW-218] TOKEN-BACKING-COLLISION ref_id="
                              << src_val.ref_id << " heap_desc="
                              << tok->class_descriptor
                              << " token_referent=" << src_val.class_desc
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
        is_instance = is_subclass_of("Ljava/lang/Class;", target_type);
    }
    else if (src_val.type == DalvikType::OBJECT_REF &&
             src_val.object_id == 0 && !src_val.class_desc.empty()) {
        // F-NEW-197 DESC-ONLY REFERENCE law: a reference with no heap
        // object carries only its creation-site declaration — that
        // declaration is the only type information (F-103's authority
        // law degenerates to the declaration). Classify by class_desc.
        is_instance = is_subclass_of(src_val.class_desc, target_type);
    }
    else if (src_val.type == DalvikType::STRING_REF) {
        // F-NEW-258 (CONT-7 W3): STRING-VALUE RUNTIME-TYPE LAW. An
        // in-register string value IS a java.lang.String instance — ART
        // instance-of and Class.isInstance agree on every non-null
        // string (OpenJDK: String.class.isInstance(s) == true, s != null).
        // The reflection path (F-103 isInstance law) already classifies
        // STRING_REF probes as Ljava/lang/String;; the bytecode path
        // fell through EVERY branch and answered FALSE. is_subclass_of
        // then composes the framework closure so the full ART truth
        // holds: String is-a CharSequence / Serializable / Comparable.
        // Live face (directive §4 contract row B-07): a String retrieved
        // from Bundle.get() answered getClass().getName()="java.lang.String"
        // (getClass handles STRING_REF) while `raw instanceof String`
        // answered FALSE — the two type paths disagreed on the same value.
        is_instance = is_subclass_of("Ljava/lang/String;", target_type);
    }
    else if (src_val.type == DalvikType::OBJECT_REF && src_val.object_id != 0) {
        // F-103 (S58, R-NEW-378) ART RUNTIME-TYPE LAW: the class of the
        // object a reference points to is the AUTHORITY for instance-of.
        // The register's cached class_desc can be empty or a degraded
        // generic tag ("Ljava/lang/Object;" after a shadow round-trip) —
        // in those cases the heap record is the only type information.
        //
        // F-105 (S59, R-NEW-379) — DECLARATION↔HEAP RECONCILIATION LAW.
        // The heap record is the authority ONLY when it does not
        // contradict the reference's creation-site declaration. The
        // engine intentionally shares ONE integer id space between
        // shadow entities and heap objects (F-023 activity-as-view: the
        // activity object's id IS the activity's view node id), so a
        // heap record at a referenced id may belong to a DIFFERENT
        // entity than the one the reference means. Live face (dooz
        // v23): ViewShadow.getParent returned the activity-as-view node
        // id 20 declared "Landroid/view/View;" while heap#20 is the
        // MainActivity → the F-103 heap-authority classified the parent
        // reference as MainActivity → `parent as? View`
        // (instance-of, Landroid/view/View; in the Lxd1;.g walk) was
        // FALSE → the ViewTreeLifecycleOwner walk dead-ended at the
        // first hop → WindowRecomposer ISE "ViewTreeLifecycleOwner not
        // found from Lho;@1074" (R-NEW-379 APP BOUNDARY unwind).
        // reconcile_class_decl implements the rules: generic declaration
        // → heap wins; consistent pair → the more specific wins;
        // CONTRADICTION → the creation-site declaration wins (the heap
        // record at the shared integer belongs to a different entity).
        std::string obj_class =
            reconcile_class_decl(src_val.class_desc, src_val.object_id);
        if (!obj_class.empty()) {
            // Check if obj_class is a subclass of target_type (or equal)
            is_instance = is_subclass_of(obj_class, target_type);
        }
    }
    // Also check if null — null instanceof anything is false (already handled by OBJECT_REF check)
    // F-072 diag (env-gated): interface-closure forensics for collection
    // checks on the dooz composition path.
    // R-NEW-337: extend the gate — every instance-of inside Loj0; (JobSupport)
    // is logged WITH the dex_report_ interface lookup result for the object
    // class. The d0 pc=0 check (state is Incomplete) returning FALSE on an
    // Lh20;(Empty) object is the suspected root of the first-composition
    // ISE "already complete or completing".
    if (std::getenv("MINIANDROID_INSTANCEOF_TRACE") &&
        (current_class_ == "Loj0;" || current_class_ == "Lkp1;" ||
         target_type == "Ljava/util/Set;" ||
         target_type == "[Ljava/lang/Object;" ||
         // CONT-7 W3 F-NEW-253: the SaveableStateRegistry canBeSaved
         // platform walk checks Bundle-storability via instance-of on
         // these platform types — log the authoritative classification
         // for every check in that family (bounded by the 200 cap).
         target_type == "Landroid/os/Bundle;" ||
         target_type == "Landroid/os/Parcelable;" ||
         target_type == "Ljava/io/Serializable;" ||
         target_type == "Ljava/lang/String;" ||
         target_type == "Ljava/lang/Number;" ||
         target_type == "Ljava/lang/Boolean;" ||
         target_type == "Ljava/lang/Character;" ||
         target_type == "Ljava/util/List;" ||
         target_type == "Ljava/util/Map;" ||
         target_type == "Landroid/util/SparseArray;" ||
         target_type == "Landroid/os/IBinder;" ||
         // S59 R-NEW-379: view-tree owner walks (Lxd1;.g) check
         // `parent as? View` after a static-wrapper getParent — log the
         // authoritative classification for View targets too.
         target_type == "Landroid/view/View;" ||
         target_type == "Landroid/view/ViewParent;" ||
         // S59 R-NEW-379 follow-up: Lwl0;.containsKey "Key must be a
         // class" at depth 79 — the Class-key guard classification.
         target_type == "Ljava/lang/Class;" ||
         // CONT-38: the composition-local provider-map identity gate
         // (Lku0;.get instance-of Lky0; — ProvidableCompositionLocal)
         // — a FALSE here short-circuits every local read to its default
         // (the LocalContentColor black face) before the trie lookup.
         target_type == "Lky0;")) {
        static thread_local uint64_t iof_n = 0;
        if (iof_n < 200) {
            ++iof_n;
            std::string oc = (src_val.type == DalvikType::OBJECT_REF)
                                 ? std::string(src_val.class_desc) : std::string("-");
            std::string hc;
            if (src_val.type == DalvikType::OBJECT_REF &&
                src_val.object_id != 0 && heap_.has_object(src_val.object_id)) {
                hc = heap_.get(src_val.object_id)->class_descriptor;
            }
            // S59 R-NEW-379 diag: the printed class must be the EFFECTIVE
            // authority (heap wins when non-empty) — register tag alone
            // mislabels the check.
            std::string eff = oc;
            if (!hc.empty()) eff = hc;
            fprintf(stderr,
                    "[INSTANCEOF-DIAG] %s.%s pc=%u target=%s obj=obj#%u class=%s heap=%s is_instance=%s\n",
                    current_class_.c_str(), current_method_.c_str(), pc,
                    target_type.c_str(),
                    src_val.type == DalvikType::OBJECT_REF ? src_val.object_id : 0u,
                    oc.c_str(), hc.c_str(), is_instance ? "TRUE" : "FALSE");
            // R-NEW-337 forensics: does dex_report_ actually know this class
            // and its implements-set? Empty closure / missing class def here
            // is exactly how `Lh20; instanceof Lmf0;` degrades to false.
            if (!oc.empty() && dex_report_) {
                bool found337 = false;
                for (const auto& cd : dex_report_->classes) {
                    if (cd.name != oc) continue;
                    found337 = true;
                    std::string ifs337;
                    for (const auto& ifc : cd.interfaces) ifs337 += ifc + " ";
                    fprintf(stderr,
                            "[INSTANCEOF-DIAG]   dex_report class=%s FOUND "
                            "ninterfaces=%zu [%s]\n",
                            cd.name.c_str(), cd.interfaces.size(),
                            ifs337.c_str());
                    break;
                }
                if (!found337)
                    fprintf(stderr,
                            "[INSTANCEOF-DIAG]   dex_report class=%s "
                            "MISSING (%zu classes scanned)\n",
                            oc.c_str(), dex_report_->classes.size());
            }
        }

    }
    // CONT-10 W6 (F-NEW-259 forensics): env-gated bounded trace of the
    // AUTHORITATIVE instanceof result for OBJECT_REF checks — generic
    // (no class gating): answers "which check dropped this element"
    // without per-app knowledge. Cap 1024 lines.
    if (std::getenv("MINIANDROID_F259_TRACE")) {
        static thread_local uint64_t f259_ins = 0;
        bool f259_dex_target =
            target_type.size() > 1 && target_type[0] == 'L' &&
            target_type.rfind("Ljava/", 0) != 0 &&
            target_type.rfind("Landroid/", 0) != 0;
        if (f259_dex_target && f259_ins++ < 65536) {
            std::string f259_oc = src_val.type == DalvikType::OBJECT_REF
                                      ? std::string(src_val.class_desc)
                                      : std::string("-");
            std::cerr << "[F259-INS] " << current_class_ << "."
                      << current_method_ << " target=" << target_type
                      << " obj=o" << src_val.object_id << " " << f259_oc
                      << " -> " << (is_instance ? "TRUE" : "FALSE")
                      << std::endl;
        }
    }
    set_register(dest, DalvikValue::make_bool(is_instance));

    // EXP-092+ PHASE 1: Trace instance-of in fillNextCodeParams AND lambda$onNextPressed$22
    // to verify the type field is correctly read and the response type check returns correct results.
    if (current_class_.find("LoginActivity") != std::string::npos &&
        (current_method_ == "fillNextCodeParams" ||
         current_method_.find("lambda$onNextPressed") == 0 ||
         current_method_.find("lambda$") == 0)) {
        std::cerr << "[EXP092-INSTANCEOF] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest
                  << " src=v" << (int)src
                  << " type_idx=" << type_idx
                  << " target_type=" << target_type
                  << " obj_class=" << (src_val.type == DalvikType::OBJECT_REF ? src_val.class_desc : "N/A")
                  << " obj_id=" << (src_val.type == DalvikType::OBJECT_REF ? src_val.object_id : 0)
                  << " is_instance=" << (is_instance ? "TRUE" : "FALSE")
                  << std::endl;
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    trace.operands.push_back({"type", target_type});
    }

    pc_ = pc + 2;  // EXP-037 Phase B (BLOCKER-017 FIX): 22c format is 2 code units (was pc + 3)
    return true;
}

// ============================================================================
// EXP-035: OPCODE IMPLEMENTATIONS — Field Operations
// ============================================================================

DalvikExecutionEngine::FieldResolution DalvikExecutionEngine::resolve_field(uint16_t field_idx) {
    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().resolve_field_ph, f107_t0);
    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().resolve_field_ph, f107_t0};
    // R-NEW-467 memo fast path: the resolved identity is run-invariant per
    // (dex, idx); the epoch guard re-derives on any hierarchy-table growth.
    if (field_memo_.size() == 65536) {
        const FieldMemo& m = field_memo_[field_idx];
        if (m.epoch == field_memo_epoch() && m.res.resolved)
            return m.res;
    }
    FieldResolution resolution;
    
    if (!dex_report_) {
        resolution.error_message = "No DexReport available (resolve_field)";
        return resolution;
    }

    // EXP-046: Per-DEX field resolution (same issue as BLOCKER-033 for methods).
    // The merged DexReport concatenates field_ids from all DEX files, so
    // field_idx from bytecode (which is per-DEX) points to the wrong field.
    if (is_multidex_ && current_dex_index_ < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[current_dex_index_];
        if (raw.size() >= sizeof(dex::DexHeader)) {
            dex::DexHeader hdr;
            std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));
            if (field_idx < hdr.field_ids_size) {
                size_t foff = hdr.field_ids_off + field_idx * 8;
                if (foff + 8 <= raw.size()) {
                    uint16_t class_idx, type_idx;
                    uint32_t name_idx;
                    std::memcpy(&class_idx, raw.data() + foff, 2);
                    std::memcpy(&type_idx, raw.data() + foff + 2, 2);
                    std::memcpy(&name_idx, raw.data() + foff + 4, 4);
                    if (class_idx < hdr.type_ids_size) {
                        uint32_t desc_str_idx;
                        std::memcpy(&desc_str_idx, raw.data() + hdr.type_ids_off + class_idx * 4, 4);
                        resolution.class_descriptor = read_dex_string_from_raw(raw, desc_str_idx, hdr);
                    }
                    resolution.field_name = read_dex_string_from_raw(raw, name_idx, hdr);
                    if (type_idx < hdr.type_ids_size) {
                        uint32_t type_str_idx;
                        std::memcpy(&type_str_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                        resolution.field_type = read_dex_string_from_raw(raw, type_str_idx, hdr);
                    }
                    if (!resolution.class_descriptor.empty() &&
                        !resolution.field_name.empty() &&
                        resolution.class_descriptor[0] == 'L') {
                        resolution.resolved = true;
                        // R-NEW-467: bank the memo for this (dex, idx).
                        if (field_memo_.size() == 65536) {
                            FieldMemo& m = field_memo_[field_idx];
                            m.res = resolution;
                            m.s134_valid = false;
                            m.epoch = field_memo_epoch();
                        }
                        return resolution;
                    }
                }
            }
        }
    }

    // Fallback: use merged DexReport
    resolution.class_descriptor = dex_report_->get_field_class(field_idx);
    resolution.field_name = dex_report_->get_field_name(field_idx);
    resolution.field_type = dex_report_->get_field_type(field_idx);

    if (resolution.class_descriptor.rfind("<bad_", 0) == 0 ||
        resolution.field_name.rfind("<bad_", 0) == 0 ||
        resolution.field_type.rfind("<bad_", 0) == 0) {
        resolution.error_message =
            "Field index " + std::to_string(field_idx) +
            " out of range or references invalid string/type";
        log("❌ FIELD RESOLUTION FAILED: " + resolution.error_message);
        return resolution;
    }

    resolution.resolved = true;
    // R-NEW-467: bank the memo for this (dex, idx).
    if (field_memo_.size() == 65536) {
        FieldMemo& m = field_memo_[field_idx];
        m.res = resolution;
        m.s134_valid = false;
        m.epoch = field_memo_epoch();
    }
    // Look up field offset from runtime metadata cache if available
    auto class_it = class_info_cache_.find(resolution.class_descriptor);
    if (class_it != class_info_cache_.end() && class_it->second) {
        const auto& class_info = *(class_it->second);
        for (const auto& inst_field : class_info.instance_fields) {
            if (inst_field.name == resolution.field_name) {
                resolution.field_offset = inst_field.byte_offset;
                break;
            }
        }
        resolution.is_static = false;
    } else {
        // Heuristic: if the field is from a framework class like
        // Landroid/* or Ljava/*, assume instance field for iget/iput and
        // static for sget/sput. The calling opcode handler will override
        // is_static as needed (sget/sput set it to true explicitly).
        resolution.is_static = false;
    }

    log("✅ FIELD RESOLVED: " + resolution.class_descriptor + "." + resolution.field_name +
        " type=" + resolution.field_type +
        " offset=" + std::to_string(resolution.field_offset));
    return resolution;
}

// ── S134 (F-NEW-160) — DEX INSTANCE FIELD IDENTITY LAW ──────────────────
// A DEX instance field is identified by (declaring class, name, type) —
// NEVER by bare name. The heap's name-keyed field map makes two same-named
// fields of two different classes alias ONE storage slot (central §3
// hypothesis: two writers, one state). Measured face (solitaire 71,
// current HEAD): activity obj#16 read `iget-object e.m` (support
// AppCompatActivity delegate field) → the resolver answered the bare name
// "m" → the app's own `m` Handler field (b/b#30) leaked out as the
// "delegate" → e.onCreate invoked the delegate family on a HANDLER →
// g.a(Activity,f) got a Handler as its Activity arg → Window null →
// support/v7/app/h.<init> pc=11 NPE → APP-BOUNDARY unwind → blank
// two-color screen. ART law: fields occupy distinct slots per declaring
// class; a field of a superclass cannot alias a subclass field.
// Fix mechanics (no heap-storage refactor):
//   * NON-framework declaring class → key = "Lcls;->name" (qualified).
//     Reads answer the field DEFAULT (zero/null) when the qualified key
//     was never written — never another class's slot.
//   * FRAMEWORK declaring class (Landroid/*, Ljava/*, …) → bare name —
//     C++ shadow writers/readers keep their bare-key interop unchanged.
//   * DEX writes dual-write (qualified primary + bare legacy mirror) so
//     existing C++ bare-name readers of app fields stay fed.
// ─────────────────────────────────────────────────────────────────────────
std::string s134_dex_field_key(const std::string& cls,
                                      const std::string& name,
                                      bool dex_defined) {
    if (cls.empty() || name.empty()) return name;
    // S134 F-NEW-160: FRAMEWORK-OWNED classes (no DEX body - C++ shadows own
    // their fields) keep bare-name keys. DEX-defined classes (support lib /
    // androidx included, whatever their package prefix) use qualified
    // identity. Package-prefix heuristics are FORBIDDEN (S134 section 5):
    // the support library lives under Landroid/* and still collides.
    if (!dex_defined) return name;
    return cls + "->" + name;
}

// S134 F-NEW-160 implementation — see dalvik_engine.h declaration.
std::string DalvikExecutionEngine::resolved_field_declarer(
    const std::string& ref_cls, const std::string& name) const {
    if (ref_cls.empty() || name.empty()) return ref_cls;
    std::string walk = ref_cls;
    for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
        if (!is_dex_defined_class(walk)) break;  // framework ancestor: stop
        auto cit = class_info_index_.find(walk);
        if (cit != class_info_index_.end() && dex_report_ != nullptr) {
            const dex::ClassInfo& ci = dex_report_->classes[cit->second];
            for (const auto& f : ci.instance_fields)
                if (f.name == name) return walk;  // declarer found
        }
        auto sit = class_to_superclass_.find(walk);
        walk = (sit != class_to_superclass_.end()) ? sit->second : std::string();
    }
    return ref_cls;  // no DEX declarer found: keep the ref class as-is
}

// ── F-NEW-325 (CONT-53): the TRUE DEX declarer of an instance field ref.
// resolved_field_declarer returns ref_cls AS-IS when no DEX body on the
// chain declares the field — callers cannot distinguish "the ref class
// itself declares it" from "this field is declared by a FRAMEWORK
// ancestor" (solitaire: DrawerLayout$g [DEX] reads `width`, declared by
// the framework ViewGroup$LayoutParams; the DEX chain has NO declarer).
// Under the S134 law framework-owned fields keep ONE bare slot, but the
// iget/iput families keyed the read/write with the REF class
// (is_dex_defined_class(ref_cls)==true → qualified "LDrawerLayout$g;->width")
// while every non-interpreter writer (F-NEW-309's semantic write-back,
// the set_field_key_resolver) lands on the BARE slot → the interpreter
// read missed and answered the fabricated default (width=0 instead of the
// written WRAP_CONTENT -2 → DrawerLayout measured its drawer at 0x0).
// ART truth: field resolution walks the receiver's class chain; a field
// not declared by any DEX class lives in the framework superclass — one
// bare slot, whoever references it. This helper returns the ACTUAL DEX
// declarer (walking the chain, verifying the field body) or "" when the
// field is framework-owned — the key then stays bare.
std::string DalvikExecutionEngine::true_dex_field_declarer(
    const std::string& ref_cls, const std::string& name) const {
    if (ref_cls.empty() || name.empty()) return std::string();
    std::string walk = ref_cls;
    for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
        if (!is_dex_defined_class(walk)) break;  // framework ancestor: stop
        auto cit = class_info_index_.find(walk);
        if (cit != class_info_index_.end() && dex_report_ != nullptr) {
            const dex::ClassInfo& ci = dex_report_->classes[cit->second];
            for (const auto& f : ci.instance_fields)
                if (f.name == name) return walk;  // REAL declarer
        }
        auto sit = class_to_superclass_.find(walk);
        walk = (sit != class_to_superclass_.end()) ? sit->second : std::string();
    }
    return std::string();  // framework-owned field: no DEX declarer
}

// ── F-NEW-657 (#588 Games-g2): the STATIC-field declarer walker — the
// sput half of R-NEW-561. JVM static identity: an inherited static lives
// in the DECLARING class's ONE storage cell (javac/dx emit the access-site
// class for inherited statics, so a subclass <clinit> rebind keyed by the
// access-site lands in a cell the superclass query never reads — the
// lane's face: MyPuzzleProvider.<clinit> sput on ChessPuzzleProvider's
// sUriMatcher was invisible to the superclass query()). Mirrors
// true_dex_field_declarer over the DEX static_fields bodies; "" = not
// DEX-declared anywhere on the chain (engine-synthetic statics keep the
// ref-class key — every existing face preserved).
std::string DalvikExecutionEngine::static_field_declarer_of(
    const std::string& ref_cls, const std::string& name) const {
    if (ref_cls.empty() || name.empty()) return std::string();
    std::string walk = ref_cls;
    for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
        if (!is_dex_defined_class(walk)) break;  // framework ancestor: stop
        auto cit = class_info_index_.find(walk);
        if (cit != class_info_index_.end() && dex_report_ != nullptr) {
            const dex::ClassInfo& ci = dex_report_->classes[cit->second];
            for (const auto& f : ci.static_fields)
                if (f.name == name) return walk;  // the DECLARING class
        }
        auto sit = class_to_superclass_.find(walk);
        walk = (sit != class_to_superclass_.end()) ? sit->second : std::string();
    }
    return std::string();  // engine-synthetic static: keep the ref key
}

// ── CONT-29 W1 R-NEW-467: FIELD-RESOLUTION MEMOIZATION ──────────────────
// Epoch = the fingerprint of everything the resolution + declarer walk
// reads. Fixed after parse: nothing — BOTH hierarchy tables can grow
// mid-run (secondary-DEX class injection + [EXP095-HIER] superclass
// extension), and current_dex_index_ selects the multidex field table.
// All three are monotonically growing, so folding their sizes into the
// epoch makes ANY mid-run change invalidate every memo (re-derive once).
uint64_t DalvikExecutionEngine::field_memo_epoch() const {
    return (static_cast<uint64_t>(
                static_cast<uint32_t>(current_dex_index_))
            << 48)
         ^ (static_cast<uint64_t>(class_to_superclass_.size()) << 24)
         ^ static_cast<uint64_t>(class_info_index_.size());
}

const DalvikExecutionEngine::FieldMemo&
DalvikExecutionEngine::resolved_field_memo(uint16_t field_idx) {
    if (field_memo_.size() != 65536) field_memo_.resize(65536);
    FieldMemo& m = field_memo_[field_idx];
    const uint64_t ep = field_memo_epoch();
    // A hit requires BOTH the resolved identity AND the S134 parts: the
    // resolve_field-internal bank stores res-only entries (s134_valid=false,
    // empty fkey) — returning one of those would key every access with an
    // EMPTY string (the 851cc176→d602648e anchor collapse, first A/B).
    if (m.epoch == ep && m.res.resolved && m.s134_valid) return m;

    m.res = resolve_field(field_idx);
    m.s134_valid = false;
    m.epoch = ep;
    if (m.res.resolved) {
        m.s134_decl = true_dex_field_declarer(m.res.class_descriptor,
                                              m.res.field_name);
        m.s134_fkey = s134_dex_field_key(
            m.s134_decl, m.res.field_name, is_dex_defined_class(m.s134_decl));
        m.s134_valid = true;
    }
    return m;
}

static DalvikValue s134_field_default(const std::string& type_desc) {
    if (!type_desc.empty() && (type_desc[0] == 'L' || type_desc[0] == '['))
        return DalvikValue::make_null();
    switch (type_desc.empty() ? 'I' : type_desc[0]) {
        case 'J': return DalvikValue::make_long(0);
        case 'F': return DalvikValue::make_float(0.0f);
        case 'D': return DalvikValue::make_double(0.0);
        default: return DalvikValue::make_int(0);
    }
}

bool DalvikExecutionEngine::execute_iget(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iget vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: same advance-pc-on-failure strategy as iget-object.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    uint64_t f107_sr0 = 0; phase_clock().enter(phase_clock().sget_resolve_ph, f107_sr0);
    // R-NEW-467: memoized resolution + S134 identity (same value the fresh
    // walk answers; epoch-guarded on the mid-run-mutable hierarchy inputs).
    const DalvikExecutionEngine::FieldMemo& field_memo
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo.res;
    phase_clock().exit(phase_clock().sget_resolve_ph, f107_sr0);
    uint64_t f107_si0 = 0; phase_clock().enter(phase_clock().sget_init_ph, f107_si0);
    DalvikValue result_value;
    result_value.type = DalvikType::INT32;
    result_value.int_val = 0;
    
    if (field_res.resolved) {
        DalvikValue obj_ref = get_register(obj_reg);
        /* F-NEW-268d (CONT-18g): ART iget null-receiver law — iget on a null
         * receiver throws NullPointerException at the access (ART resolves
         * the field first, then null-checks — same order here; the silent
         * default-value answer hid the first divergence, issue #381 face d).
         * f141_is_null_receiver covers NULL_REF / OBJECT_REF-id-0 / INT32-0
         * typed null (F-141 + F-266a untyped-register law). */
        if (f141_is_null_receiver(obj_ref)) {
            raise_synthetic_exception(
                "Ljava/lang/NullPointerException;",
                "Attempt to read from field '" + field_res.class_descriptor +
                    "." + field_res.field_name +
                    "' on a null object reference",
                "iget-null-recv");
            return true;  /* pc_ set by raise (catch handler) or frame unwind */
        }
        // CONT-47 D7a: draw-window LayoutNode read census (env-gated,
        // bounded 64 distinct fields). Which Lel0; fields does the DEX
        // draw walk read — A/n folds vs q chain (D6 verdicts)?
        static const bool d7a_on_iget =
            diag_env("MINIANDROID_D7_READCENSUS");
        if (d7a_on_iget && draw_window_active_ &&
            field_res.class_descriptor == "Lel0;" &&
            g_d7_read_census.size() < 64)
            ++g_d7_read_census[field_res.field_name];
        if (obj_ref.type == DalvikType::OBJECT_REF && heap_.has_object(obj_ref.object_id)) {
            // S134 F-NEW-160: qualified field identity (declaring class + name).
            // F-NEW-325: a framework-owned field (no DEX declarer on the
            // chain — DrawerLayout$g -> width, declared by the framework
            // MarginLayoutParams) keeps ONE bare slot even when the REF
            // class is DEX-defined; the ref-class key fabricated a second
            // identity and the read answered a fabricated default.
            const std::string& s134_fkey = field_memo.s134_fkey;
            const bool s134_decl_is_dex = field_memo.s134_valid
                && is_dex_defined_class(field_memo.s134_decl);
            auto field_val = heap_.get_object_field(obj_ref.object_id, s134_fkey);
            // ── TRAIN-67 (T67, DIAG-ONLY, env-gated MINIANDROID_T67_LABEL_TRACE):
            // suspend-lambda STATE-MACHINE label-persistence probe. Lss1; = the
            // awaitEachGesture-level machine (R8): field l:I = the Kotlin
            // state-machine label, k:Ljava/lang/Object; = the L$0 spill. The
            // S146 death: on resume the machine re-awaits from label 0 — log
            // every read of these fields with the RECEIVER IDENTITY so the
            // iput-before-suspend vs iget-on-resume split becomes evidence.
            {
                static const bool t67_on = diag_env("MINIANDROID_T67_LABEL_TRACE");
                if (t67_on && (field_res.class_descriptor == "Lss1;" ||
                               field_res.class_descriptor == "Lxs1;" ||
                               field_res.class_descriptor == "Li6;")) {
                    static thread_local uint64_t t67_n = 0;
                    if (t67_n++ < 600) {
                        std::cerr << "[T67-IGET] Lss1;." << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val="
                                  << (field_val.has_value()
                                          ? dalvik_value_to_string(*field_val)
                                          : std::string("(none)"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc << std::endl;
                    }
                }
            }
            // ── S211 (DIAG-ONLY, env-gated MINIANDROID_S211_SEGTRACE):
            // dooz post-nav zombie probe — every iget of a Lbw0; (kotlinx
            // Segment family) INT field logs (obj#, field, value, caller,
            // pc). Answers: what did the .e scanner's mask register
            // (this.c) actually read at the divergence — 7 or garbage?
            {
                static const bool s211_on = diag_env("MINIANDROID_S211_SEGTRACE");
                if (s211_on && field_res.class_descriptor == "Lbw0;" &&
                    field_res.field_name == "c") {
                    static thread_local uint64_t s211_n = 0;
                    if (s211_n++ < 400) {
                        std::cerr << "[S211-IGET] Lbw0;." << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val="
                                  << (field_val.has_value()
                                          ? dalvik_value_to_string(*field_val)
                                          : std::string("(none)"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc << std::endl;
                    }
                }
            }
            // ── S221 (DIAG-ONLY, env-gated MINIANDROID_S221_DENSTRACE):
            // dooz post-NewGame text-cache ISE storm probe. The app-side
            // MultiParagraphLayoutCache flips density (2.625 real <-> 0.0
            // Unspecified) between layout and draw — each flip markDirty()s
            // the cache so EVERY draw throws the "could not provide
            // TextLayoutResult" ISE and one escapes MainActivity.onCreate
            // (ART process-death; the transition freezes half-slid).
            // Upstream law (TextStringSimpleNode.kt header): "the density
            // should not change between layout and draw phases". Every
            // float iget answering 0.0 INSIDE a draw window logs (field,
            // receiver, caller chain top 6) — the 0.0 delivery site becomes
            // evidence instead of a guess.
            {
                static const bool s221_on = diag_env("MINIANDROID_S221_DENSTRACE");
                if (s221_on && draw_window_active_ && field_val.has_value() &&
                    field_val->type == DalvikType::FLOAT32 &&
                    field_val->float_val == 0.0f) {
                    static thread_local uint64_t s221_n = 0;
                    if (s221_n++ < 40) {
                        std::cerr << "[S221-ZERODENS] "
                                  << field_res.class_descriptor << "."
                                  << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc;
                        auto s221_frames = call_stack_.snapshot_top_first();
                        for (size_t fi = 0;
                             fi < s221_frames.size() && fi < 6; ++fi)
                            std::cerr << " <" << s221_frames[fi].first << "."
                                      << s221_frames[fi].second << ">";
                        std::cerr << std::endl;
                    }
                }
            }
            // ── TRAIN-68 (T68-JOBGET): the pointerInputJob null-check reads.
            // Lor1;.v:Lkp1; = the lazy coroutine job — every node reads it on
            // the first event (if-null-launch). Log the READ + the value with
            // receiver identity so the skipped-launch nodes (#6571/#14049)
            // become evidence: was v non-null, or did the read fail?
            {
                static const bool t68g_on = diag_env("MINIANDROID_T68_NODE_TRACE");
                if (t68g_on && field_res.class_descriptor == "Lor1;" &&
                    field_res.field_name == "v") {
                    static thread_local uint64_t t68g_n = 0;
                    if (t68g_n++ < 120)
                        std::cerr << "[T68-JOBGET] Lor1;.v obj#"
                                  << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val="
                                  << (field_val.has_value()
                                          ? dalvik_value_to_string(*field_val)
                                          : std::string("(none)"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                }
            }
            if (!field_val.has_value() && s134_decl_is_dex) {
                // AOSP law: an instance field never written answers its
                // DEFAULT value — never another class's same-named slot.
                // FINAL-CAMPAIGN PHASE 3 diag (SGET-MISS probe precedent):
                // a DEX-defined qualified read that misses means the writer
                // used a different identity — dump the asked key + the
                // object's actual keys (throttled) so the mismatch is
                // EVIDENCE, not a guess.
                static thread_local uint64_t iget_miss_diag_n = 0;
                if (iget_miss_diag_n < 16) {
                    ++iget_miss_diag_n;
                    const auto* hobj = heap_.get(obj_ref.object_id);
                    std::string have;
                    if (hobj) {
                        int cnt = 0;
                        for (const auto& kv : hobj->fields) {
                            if (cnt++ >= 6) break;
                            have += " " + kv.first;
                        }
                    }
                    std::cerr << "[IGET-MISS-DIAG] asked=\"" << s134_fkey
                              << "\" obj#" << obj_ref.object_id
                              << " cls="
                              << (hobj ? hobj->class_descriptor : std::string("<no-heap-obj>"))
                              << " keys:" << (have.empty() ? " <none>" : have)
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
                field_val = s134_field_default(field_res.field_type);
            }
            if (field_val.has_value()) {
                result_value = field_val.value();
            }
        }
    }
    // M3 FIELD-TRACE (AG diagnostic): env-gated field-access value trace.
    {
        DalvikValue tgt = get_register(obj_reg);
        if (field_trace_filter_set() &&
            field_trace_active(field_res.field_name.c_str(),
                               (current_class_ + "." + current_method_).c_str(),
                               field_res.class_descriptor.c_str())) {
            std::cerr << "[FIELD-TRACE] get " << current_class_ << "." << current_method_
                      << " " << field_res.class_descriptor << "." << field_res.field_name
                      << " obj#" << (tgt.type == DalvikType::OBJECT_REF ? tgt.object_id : 0)
                      << " value=" << dalvik_value_to_string(result_value)
                      << std::endl;
        }
        // F-NEW-267 (CONT-64 W1) HIT-TEST WIDE-READ probe — env-gated
        // MINIANDROID_TOUCH_FIELD_TRACE=1, bounded, ACTIVE ONLY during the
        // touch dispatch. Logs every iget-wide (64-bit = the packed
        // IntOffset/IntSize/Constraints value-class reads) on the compose
        // node-tree classes so the decode sees EXACTLY what bounds the
        // pure-DEX hit-test walk consumes.
        static thread_local const bool htft_on =
            std::getenv("MINIANDROID_TOUCH_FIELD_TRACE") != nullptr;
        if (htft_on && touch_dispatch_active_ &&
            result_value.type == DalvikType::INT64) {
            static const char* htft_classes[] = {
                "Lel0;", "Lkz0;", "Lug0;", "Lpz0;", "Lil0;", "Lzs0;",
                "Lbt0;", "Ld61;", "Las0;", "Lkc;", "Loh;", "Lg5;"};
            const std::string& cd = field_res.class_descriptor;
            for (const char* hc : htft_classes) {
                if (cd == hc) {
                    static thread_local uint64_t htft_n = 0;
                    if (htft_n++ < 240) {
                        DalvikValue tgt2 = get_register(obj_reg);
                        std::cerr << "[HT-WIDE] " << cd << "."
                                  << field_res.field_name
                                  << " obj#" << (tgt2.type == DalvikType::OBJECT_REF
                                                     ? tgt2.object_id : 0)
                                  << " = " << result_value.long_val
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    }
                    break;
                }
            }
        }
        // ── TRAIN-64 (T64, DIAG-ONLY, env-gated MINIANDROID_T64_CHANGE_TRACE):
        // pointer-change field READ law. Lu71; = PointerInputChange (R8):
        // d=pressed, h=previousPressed, o=isConsumed, p. The tap state
        // machine (waitForUpOrCancellation: fastAll{changedToUp} =
        // !pressed && previousPressed; fastAny{isConsumed}) reads these
        // fields INLINE (R8), so no invoke probe can see them. Log every
        // boolean read during the touch dispatch — answers WHY the dooz
        // cell tap never fires onTap (changedToUp false? consumed?).
        static thread_local const bool t64r_on =
            std::getenv("MINIANDROID_T64_CHANGE_TRACE") != nullptr;
        if (t64r_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lu71;") {
            static const char* t64_bools[] = {"d", "h", "o", "p"};
            for (const char* t64b : t64_bools) {
                if (field_res.field_name == t64b) {
                    static thread_local uint64_t t64r_n = 0;
                    if (t64r_n++ < 400) {
                        DalvikValue t64_t = get_register(obj_reg);
                        std::cerr << "[T64-R] Lu71;." << field_res.field_name
                                  << " obj#"
                                  << (t64_t.type == DalvikType::OBJECT_REF
                                          ? t64_t.object_id : 0)
                                  << " = "
                                  << dalvik_value_to_string(result_value)
                                  << " dst=v" << static_cast<int>(dest_reg)
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    }
                    break;
                }
            }
            // T64-Q: the q-chain read (b()Z recurses into q when non-null —
            // a self/loop in q makes isConsumed answer from the WRONG change).
            if (field_res.field_name == "q") {
                static thread_local uint64_t t64q_n = 0;
                if (t64q_n++ < 200) {
                    DalvikValue t64_t3 = get_register(obj_reg);
                    std::cerr << "[T64-Q] Lu71;.q obj#"
                              << (t64_t3.type == DalvikType::OBJECT_REF
                                      ? t64_t3.object_id : 0)
                              << " -> "
                              << dalvik_value_to_string(result_value)
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
            // T64b: the isOutOfBounds arm reads the packed position
            // (j = position, g = previousPosition) as iget-wide — log those
            // during the touch dispatch (bounds: size + extendedTouchPadding
            // decide the cancel).
            if (field_res.field_name == "j" || field_res.field_name == "g") {
                static thread_local uint64_t t64p_n = 0;
                if (t64p_n++ < 200 && result_value.type == DalvikType::INT64) {
                    DalvikValue t64_t2 = get_register(obj_reg);
                    std::cerr << "[T64-POS] Lu71;." << field_res.field_name
                              << " obj#"
                              << (t64_t2.type == DalvikType::OBJECT_REF
                                      ? t64_t2.object_id : 0)
                              << " = " << result_value.long_val
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
    }
    // EXP-042 Phase 2: on any failure path, fall through with default 0 and
    // advance pc_ — never return false (which would cause an infinite loop).
    
    set_register(dest_reg, result_value);
    // S157-B (CONT-42 zero-cost-gate law): the operand block below builds
    // concat/to_string heap strings per executed iget — with trace_cap == 0
    // the trace is destroyed unread (phase-A recording-block proof), so the
    // block is pure waste. Gated; content identical when consumed.
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }
    
    pc_ = pc + 2;
    return true;
}

// ── S122 (R-NEW-414) — instance field-initializer defaults ──────────────
// javac compiles `final Rect m = new Rect();` (and every other inline
// instance-field initializer) into the constructor body: new-instance T vN
// → invoke-direct T.<init> vN → iput-object vN → F. ART therefore
// guarantees such fields are NON-NULL on any constructed object. This
// runtime materializes view/heap objects for DEX-defined classes WITHOUT
// running the class's <init> (the subdecor ContentFrameLayout path), so
// iget-object on those fields answered null and apps died on the first
// method call (chess 10.6.0: ContentFrameLayout field l — the AOSP
// `mDecorPadding` Rect — read null in the measure path → Rect.set NPE →
// onCreate unwound → blank screen).
// LAW: a field whose constructor initializer is `new T` is materialized
// as an empty T on a heap read that would otherwise answer null. Generic
// across every DEX class; zero package checks.
// S122: DEX instruction sizes (in 16-bit code units) for the R-NEW-414
// initializer scan — standard format widths from the DEX spec tables.
static size_t r414_opcode_size(uint8_t op) {
    static const uint8_t k1[12] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06,
                                   0x07, 0x08, 0x09, 0x0a, 0x0b};
    static const uint8_t k1b[16] = {0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12,
                                    0x1d, 0x1e, 0x27, 0x28, 0x7b, 0x7c, 0x7d,
                                    0x7e, 0x27};
    static const uint8_t k1c[8] = {0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6,
                                   0xb7};
    if (op == 0x13 || op == 0x15 || op == 0x16 || op == 0x19 || op == 0x1c ||
        op == 0x1f || op == 0x20 || op == 0x21 || op == 0x22 || op == 0x23)
        return 2;
    if (op == 0x14 || op == 0x17 || op == 0x18) return 3;
    if (op == 0x1a) return 2;
    if (op == 0x1b) return 3;
    if (op == 0x29) return 2;
    if (op == 0x2a || op == 0x2b || op == 0x2c) return 3;
    if (op == 0x24 || op == 0x25 || op == 0x26) return 3;
    if ((op >= 0x2d && op <= 0x31) || (op >= 0x44 && op <= 0x6d)) return 2;
    if ((op >= 0x32 && op <= 0x3d)) return 2;
    if ((op >= 0x3e && op <= 0x43)) return 2;  // unused range (nop-width)
    if ((op >= 0x6e && op <= 0x72) || (op >= 0x74 && op <= 0x78)) return 3;
    if (op >= 0x7f && op <= 0xaf) return 2;
    for (uint8_t k : k1) if (op == k) return 1;
    for (uint8_t k : k1b) if (op == k) return 1;
    for (uint8_t k : k1c) if (op == k) return 1;
    if (op >= 0xb8 && op <= 0xcf) return 1;
    if (op >= 0xd0 && op <= 0xe2) return 2;
    return 1;  // unknown: conservative 1-unit stride
}

void DalvikExecutionEngine::scan_init_field_defaults(const std::string& cls) {
    if (init_defaults_scanned_.count(cls) > 0) return;
    init_defaults_scanned_.insert(cls);
    if (!dex_report_) return;
    auto class_it = class_info_index_.find(cls);
    if (class_it == class_info_index_.end()) return;
    const dex::ClassInfo& info = dex_report_->classes[class_it->second];
    uint32_t dex_idx = 0;
    if (auto dit = class_to_dex_index_.find(cls); dit != class_to_dex_index_.end())
        dex_idx = dit->second;
    auto& field_map = init_field_defaults_[cls];
    // S156-P4 (CONT-42 zero-cost-gate law): static-cached — one-time env read.
    static const bool r414_trace = std::getenv("MINIANDROID_R414_TRACE") != nullptr;
    for (const auto* list : {&info.direct_methods, &info.virtual_methods}) {
        for (const auto& m : *list) {
            if (m.name != "<init>" || m.bytecode.empty()) continue;
            // reg → newest new-instance type (javac initializers store the
            // freshly constructed object almost immediately)
            std::map<uint16_t, std::string> reg_types;
            const std::vector<uint16_t>& bc = m.bytecode;
            size_t pc2 = 0;
            while (pc2 + 1 < bc.size()) {
                uint16_t unit = bc[pc2];
                uint8_t op = unit & 0xFF;
                uint8_t hi = (unit >> 8) & 0xFF;
                if (op == 0x00) {
                    // nop; skip pseudo-data payloads so the scan stays aligned
                    if (hi == 0x01) {  // packed-switch-payload
                        if (pc2 + 3 >= bc.size()) break;
                        uint32_t sz = (uint32_t)bc[pc2 + 1] |
                                      ((uint32_t)bc[pc2 + 2] << 16);
                        pc2 += 4 + sz * 2;
                        continue;
                    }
                    if (hi == 0x02) {  // sparse-switch-payload
                        if (pc2 + 3 >= bc.size()) break;
                        uint32_t sz = (uint32_t)bc[pc2 + 1] |
                                      ((uint32_t)bc[pc2 + 2] << 16);
                        pc2 += 2 + sz * 4;
                        continue;
                    }
                    if (hi == 0x03) {  // fill-array-data-payload
                        if (pc2 + 5 >= bc.size()) break;
                        uint16_t ew = bc[pc2 + 1];
                        uint32_t sz = (uint32_t)bc[pc2 + 2] |
                                      ((uint32_t)bc[pc2 + 3] << 16);
                        pc2 += 4 + (size_t)((uint64_t)sz * ew + 1) / 2;
                        continue;
                    }
                    pc2 += 1;
                    continue;
                }
                if (op == 0x22 && pc2 + 1 < bc.size()) {  // new-instance
                    uint16_t reg = hi;
                    uint16_t tidx = bc[pc2 + 1];
                    reg_types[reg] = resolve_type_for_dex(tidx, dex_idx);
                    pc2 += r414_opcode_size(op);
                    continue;
                }
                if (op == 0x5B && pc2 + 1 < bc.size()) {  // iput-object
                    uint8_t src = (unit >> 8) & 0xF;
                    uint16_t fidx = bc[pc2 + 1];
                    auto rt = reg_types.find(src);
                    if (rt != reg_types.end()) {
                        FieldResolution fr = resolve_field((uint16_t)fidx);
                        if (fr.resolved && fr.field_type == rt->second) {
                            field_map[fr.field_name] = rt->second;
                        }
                    }
                    pc2 += r414_opcode_size(op);
                    continue;
                }
                pc2 += r414_opcode_size(op);  // spec-width stride keeps the scan aligned
            }
            if (r414_trace && !field_map.empty()) {
                std::cerr << "[R414-SCAN] " << cls << " initializers:";
                for (auto& kv : field_map)
                    std::cerr << " " << kv.first << "->" << kv.second;
                std::cerr << std::endl;
            }
        }
    }
}

DalvikValue DalvikExecutionEngine::materialize_init_default(
    const std::string& type_desc) {
    if (type_desc.empty() || type_desc[0] != 'L') return DalvikValue::make_null();
    uint32_t oid = heap_.allocate(type_desc, 0, 0);
    if (type_desc == "Landroid/graphics/Rect;" ||
        type_desc == "Landroid/graphics/Point;" ||
        type_desc == "Landroid/graphics/PointF;") {
        for (const char* f : {"left", "top", "right", "bottom", "x", "y"})
            heap_.set_object_field(oid, f, DalvikValue::make_int(0));
    } else if (type_desc == "Landroid/util/TypedValue;") {
        heap_.set_object_field(oid, "type", DalvikValue::make_int(0));
    } else if (type_desc == "Ljava/lang/StringBuilder;" ||
               type_desc == "Ljava/lang/StringBuffer;") {
        // leave empty shell; string methods are shadow-dispatched
    }
    // F-NEW-464 (CONT-114): EXECUTE the ()V constructor of a DEX-defined
    // initializer type. ART law (completed by this change): a field never
    // written reads null; an initializer-default object exists only after
    // its constructing <init> ran. F-NEW-274 already gates on the ()V
    // ctor's EXISTENCE, but the materializer only allocated — every
    // DEX-defined zero-state stayed a bare shell (tower3d: libGDX
    // DirectionalLightsAttribute.lights materialized as Array obj#393 with
    // ZERO fields; Array.add then read size off nothing -> ARR-LEN-NULL NPE
    // -> AndroidLauncher.onCreate death). Running the real ()V ctor gives
    // the object its true zero-state (Array: items/ordered/size). Framework
    // shells (Rect/Point/TypedValue above) keep their seeded zero-state.
    // Re-entrancy guard: a ctor whose body reads the SAME missing field
    // must not recurse forever — nested same-type materialization returns
    // the bare shell (documented honest frontier).
    static thread_local std::string f464_in_flight;
    if (f464_in_flight == type_desc) {
        return DalvikValue::make_object(oid, type_desc);
    }
    // F-NEW-464/465 (CONT-114 + CONT-116 correction): EXECUTE the ()V
    // constructor of a DEX-defined initializer type. CONT-116 found the
    // dispatch condition INVERTED: `!class_has_no_arg_ctor` ran the ()V
    // body only for classes WITHOUT one (a ctor that does not exist) and
    // skipped every class that HAS one — libGDX Array's ()V never ran, so
    // every R-NEW-414-materialized Array stayed a bare shell (tower3d
    // obj#393: zero fields → Array.add pc=4 ARR-LEN-NULL NPE →
    // AndroidLauncher.onCreate APP-BOUNDARY death). ART law: run the ()V
    // ctor exactly when it EXISTS; the F-NEW-274 gate upstream already
    // refuses fabrication for ctor-less classes (honest null path).
    if (class_info_index_.find(type_desc) != class_info_index_.end() &&
        dex_report_ && class_has_no_arg_ctor(type_desc)) {
        f464_in_flight = type_desc;
        DalvikValue recv = DalvikValue::make_object(oid, type_desc);
        DalvikValue ret = DalvikValue::make_void();
        DalvikExecutionResult res;
        // F-NEW-501 (CONT-159): pass the EXACT "()V" descriptor. The
        // materializer must run THE no-arg constructor — ART's default-
        // initialization contract. With the descriptor left empty, the
        // lenient overload selection (EXP-078 largest-bytecode law) picked
        // whichever same-name <init> had the biggest body: for libgdx Array
        // that was the COPY ctor (Array;(Array;)V, 30 units > 7) — it then
        // read the fresh shell's ABSENT items field → getClass() on null →
        // NPE → AndroidLauncher.onCreate death (tower3d uniform-black face).
        // The F-NEW-274 gate above already verified a local ()V exists, so
        // the exact-match law resolves it deterministically.
        bool ran = try_recursive_invoke(type_desc, "<init>", {recv}, ret, res,
                                        "()V");
        f464_in_flight.clear();
        if (ran) heap_.mark_initialized(oid);
        // ran == false: keep the seeded shell (honest — ctor not found in
        // the DEX chain after all); the read still answers a valid object.
    }
    DalvikValue v = DalvikValue::make_object(oid, type_desc);
    return v;
}

// F-NEW-274 (CONT-22) — ART constructor-contract gate for R-NEW-414
// initializer materialization (see header for the law). Live face (dooz,
// run/cont21/after/dooz_r3 + fresh CONT-22 runs): Lgf1;.g's initializer is
// `new Lwg0;(Lrf1;, I)` — an R8 merged-lambda class whose ONLY constructors
// take captured arguments; R414 fabricated a zero Lwg0; whose capture field
// .f stayed null, the caller's own `if-eqz` null-guard at the read site
// (Lg8;.a:  iget g; if-eqz; …invoke .y) then saw a NON-null broken object,
// invoked the save-lambda body, and died at `iget Lrf1;.f` on the null
// capture (SavedStateRegistry.performSave neighborhood). ART law: a field
// never written reads null; an initializer-default object exists only after
// its constructing <init> ran, so a class with no ()V ctor cannot have a
// legal zero-state instance. DEX-defined classes are inspected for a ()V
// <init>; non-DEX classes (framework Rect/Point/TypedValue shells the
// materializer seeds itself) keep the old behavior.
bool DalvikExecutionEngine::class_has_no_arg_ctor(const std::string& type_desc) {
    if (type_desc.empty() || type_desc[0] != 'L') return false;
    auto cit = class_info_index_.find(type_desc);
    if (cit == class_info_index_.end() ||
        cit->second >= dex_report_->classes.size()) {
        // Framework-owned type: materialize_init_default's seed block
        // defines its zero-state contract (Rect/Point/PointF/TypedValue).
        return true;
    }
    const auto& cls = dex_report_->classes[cit->second];
    for (const auto& m : cls.direct_methods) {
        if (m.name == "<init>" && m.descriptor == "()V") return true;
    }
    return false;
}

bool DalvikExecutionEngine::execute_iget_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iget-object vA, vB, field@CCCC
    // Read object field from object and place reference in destination register
    // EXP-042 Phase 2 FIX: Previously, every error path returned false WITHOUT
    // advancing pc_. The caller then re-fetched the same opcode, hit the same
    // error, and looped forever — the loop detector eventually halted the
    // method, but only after 50 001 wasted iterations. Now all error paths
    // advance pc_ by 2 (22c format is 2 code units) and return true so the
    // caller can continue with a sensible default (null/0).
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;    // vA - 4-bit destination reg
    uint8_t obj_reg = (instr >> 12) & 0xF;    // vB - 4-bit object reg
    uint16_t field_idx = bytecode_[pc + 1];   // CCCC - field index
    
    // Resolve field from DEX (R-NEW-467 memoized)
    const DalvikExecutionEngine::FieldMemo& field_memo
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo.res;
    if (!field_res.resolved) {
        trace.error_message = "Failed to resolve field index " + std::to_string(field_idx);
        trace.status = InstructionTrace::Status::CRASH_ERROR;
        // EXP-042 Phase 2: advance pc_ and continue rather than spin.
        set_register(dest_reg, DalvikValue::make_null());
        // S88 DIAG: unresolved-field silent-null route — count and name it.
        {
            static thread_local uint64_t s88_uf_n = 0;
            if (s88_uf_n < 40) {
                ++s88_uf_n;
                std::cerr << "[S88-UNRESOLVED-FIELD] idx=" << field_idx
                          << " caller=" << current_class_ << "." << current_method_
                          << " pc=" << pc << std::endl;
            }
        }
        pc_ = pc + 2;
        return true;
    }
    
    // Get object reference from register
    DalvikValue obj_ref = get_register(obj_reg);

    /* F-NEW-268d (CONT-18g): ART iget-object null-receiver law — mirror of
     * the iget arm (field resolved first, then the null check; issue #381
     * face d). The old path answered a silent null default. */
    if (f141_is_null_receiver(obj_ref)) {
        raise_synthetic_exception(
            "Ljava/lang/NullPointerException;",
            "Attempt to read from field '" + field_res.class_descriptor +
                "." + field_res.field_name +
                "' on a null object reference",
            "iget-null-recv");
        return true;  /* pc_ set by raise (catch handler) or frame unwind */
    }

    // CONT-47 D7a: draw-window LayoutNode read census (env-gated,
    // bounded 64 distinct fields) — same law as the iget arm.
    static const bool d7a_on_igeto =
        diag_env("MINIANDROID_D7_READCENSUS");
    if (d7a_on_igeto && draw_window_active_ &&
        field_res.class_descriptor == "Lel0;" &&
        g_d7_read_census.size() < 64)
        ++g_d7_read_census[field_res.field_name];

    // S88 DIAG (bounded, env-gated): MiniFont$Glyph field reads — tweakWidth
    // NPE "Path.transform on null" while iput traces show the path field
    // stored. This probe exposes resolved/has_object/result for every
    // Glyph iget-object.
    // S156-P4 (CONT-42 zero-cost-gate law): the raw std::getenv ran PER
    // iget-object call (7.06M calls on the dooz record phase = a linear
    // environ scan per op, ~hundreds of ns each). Static-cached: the env
    // is read once, the gate costs one branch.
    static const bool s88_glyph_diag = std::getenv("MINIANDROID_S88_GLYPH") != nullptr;
    if (s88_glyph_diag &&
        field_res.class_descriptor.find("MiniFont$Glyph") != std::string::npos) {
        std::cerr << "[S88-IGET] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " resolved=" << field_res.resolved
                  << " field=" << field_res.field_name
                  << " recv_type=" << static_cast<int>(obj_ref.type)
                  << " recv_id=" << obj_ref.object_id
                  << " in_heap=" << (heap_.has_object(obj_ref.object_id) ? "Y" : "N")
                  << std::endl;
    }

    // ── TRAIN-68 (T68-JOBGET-OBJ): the pointerInputJob null-check read is an
    // IGET-OBJECT (Lor1;.v:Lkp1;) — this arm, not the int iget arm. Log the
    // read with receiver identity: hit + value for every launch-gate check.
    {
        static const bool t68o_on = diag_env("MINIANDROID_T68_NODE_TRACE");
        if (t68o_on && field_res.class_descriptor == "Lor1;" &&
            field_res.field_name == "v") {
            static thread_local uint64_t t68o_n = 0;
            if (t68o_n++ < 120)
                std::cerr << "[T68-JOBGET-OBJ] Lor1;.v obj#"
                          << (obj_ref.type == DalvikType::OBJECT_REF
                                  ? obj_ref.object_id : 0)
                          << " in_heap="
                          << (heap_.has_object(obj_ref.object_id) ? "Y" : "N")
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
    }

    DalvikValue result_value;
    result_value.type = DalvikType::NULL_REF;
    result_value.object_id = 0;
    
    if (obj_ref.type == DalvikType::OBJECT_REF) {
        // Look up object field from heap
        if (heap_.has_object(obj_ref.object_id)) {
            if (field_trace_filter_set() &&
                field_trace_active(field_res.field_name.c_str(),
                                   (current_class_ + "." + current_method_).c_str(),
                                   field_res.class_descriptor.c_str())) {
                DalvikValue tgt = get_register(obj_reg);
                std::cerr << "[FIELD-TRACE] get-obj " << current_class_ << "."
                          << current_method_ << " "
                          << field_res.class_descriptor << "." << field_res.field_name
                          << " obj#" << (tgt.type == DalvikType::OBJECT_REF ? tgt.object_id : 0)
                          << std::endl;
            }
            // F-NEW-325: true-declarer keying (see execute_iget).
            // R-NEW-467: the declarer walk + key concat are memoized.
            const std::string& s134_fkey = field_memo.s134_fkey;
            auto field_val = heap_.get_object_field(obj_ref.object_id,
                s134_fkey);
            // W5 (Coder-4) DIAG: Koin Module.includedModules read forensics.
            {
                static const bool f566f_on =
                    diag_env("MINIANDROID_F566_FIELD_DIAG");
                static thread_local uint64_t f566f_n = 0;
                if (f566f_on && field_res.resolved &&
                    (field_res.field_name == "includedModules" ||
                     field_res.field_name == "includes") &&
                    f566f_n++ < 60) {
                    std::cerr << "[F566-IGET] " << field_res.field_name << " obj#"
                              << obj_ref.object_id << " key=\"" << s134_fkey
                              << "\" hit="
                              << (field_val.has_value() ? 1 : 0) << " val=";
                    if (field_val.has_value())
                        std::cerr << dalvik_value_to_string(*field_val);
                    else
                        std::cerr << "(none=default-null)";
                    std::cerr << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                    // W6 (Coder-4): when loadModules reads the includes
                    // list, dump the value object's STORE SHAPE (class,
                    // heap array length, first elements) — the flatten
                    // drop forensics (F-C4-570 root-pinning).
                    if (field_val.has_value() &&
                        field_val->type == DalvikType::OBJECT_REF &&
                        field_val->object_id != 0 &&
                        current_class_ == "Lorg/koin/core/Koin;") {
                        uint32_t fv = field_val->object_id;
                        const auto* fvo = heap_.has_object(fv)
                            ? heap_.get(fv) : nullptr;
                        std::cerr << "[W6-INCL] list obj#" << fv << " class="
                                  << (fvo ? fvo->class_descriptor
                                          : std::string("?"));
                        int32_t w6_alen = -1;
                        {
                            auto w6_al =
                                heap_.get_object_field(fv, "__array_length__");
                            if (w6_al.has_value() &&
                                w6_al->type == DalvikType::INT32)
                                w6_alen = w6_al->int_val;
                            std::cerr << " __array_length__="
                                      << (w6_al.has_value()
                                              ? std::to_string(w6_alen)
                                              : std::string("ABSENT"));
                        }
                        if (fvo) {
                            std::cerr << " fields=";
                            size_t shown = 0;
                            for (const auto& w6f : fvo->fields) {
                                if (shown++ >= 6) { std::cerr << "…"; break; }
                                std::cerr << w6f.first << "("
                                          << static_cast<int>(w6f.second.type)
                                          << ",o" << w6f.second.object_id
                                          << ") ";
                            }
                        }
                        // first two array slots if present
                        for (int32_t w6_i = 0; w6_i < 2; ++w6_i) {
                            auto w6_ev = heap_.get_object_field(
                                fv, "array[" + std::to_string(w6_i) + "]");
                            if (w6_ev.has_value())
                                std::cerr << " arr[" << w6_i << "]=o"
                                          << w6_ev->object_id;
                        }
                        std::cerr << std::endl;
                    }
                }
            }
            // ── TRAIN-68 (T68-JOBGET-VAL): the pointerInputJob read VALUE.
            // The DOWN-window evidence: nodes #6571/#14049 jumped pc=8 -> 29
            // with the launch block skipped — this prints the exact value the
            // null-check saw (stale slot vs default-null vs wrong key).
            {
                static const bool t68v_on = diag_env("MINIANDROID_T68_NODE_TRACE");
                if (t68v_on && field_res.class_descriptor == "Lor1;" &&
                    field_res.field_name == "v") {
                    static thread_local uint64_t t68v_n = 0;
                    if (t68v_n++ < 120) {
                        std::cerr << "[T68-JOBGET-VAL] Lor1;.v obj#"
                                  << obj_ref.object_id << " key=\"" << s134_fkey
                                  << "\" hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val=";
                        if (field_val.has_value())
                            std::cerr << dalvik_value_to_string(*field_val);
                        else
                            std::cerr << "(none=default-null)";
                        std::cerr << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                    }
                }
            }
            // S134 F-NEW-160 probe: qualified-read hit/miss visibility.
            {
                static thread_local const bool s134_qprobe =
                    std::getenv("MINIANDROID_S134_QPROBE") != nullptr;
                if (s134_qprobe) {
                    static thread_local uint64_t s134_qn = 0;
                    // S49 convention: budget env-configurable
                    // (MINIANDROID_S134_QGET_BUDGET) so deep-boot forensics
                    // can capture beyond the default 60 rows.
                    static thread_local uint64_t s134_qcap = [] {
                        const char* b = std::getenv("MINIANDROID_S134_QGET_BUDGET");
                        return (b != nullptr) ? static_cast<uint64_t>(atoi(b)) : 60ull;
                    }();
                    if (s134_qn < s134_qcap) {
                        ++s134_qn;
                        std::cerr << "[S134-QGET] key="
                                  << s134_dex_field_key(field_res.class_descriptor,
                                                        field_res.field_name,
                                                        is_dex_defined_class(
                                                            field_res.class_descriptor))
                                  << " obj#" << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? "Y" : "N")
                                  << (field_val.has_value()
                                          ? " val=" + field_val->to_string()
                                          : "")
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                    }
                }
            }
            // S134 F-NEW-160: qualified identity read (declaring class + name);
            // non-framework miss answers the field DEFAULT (null for refs —
            // the R-NEW-414 initializer materialization below still applies
            // on top of the honest default).
            // S122 (R-NEW-414): field-initializer default. A field whose
            // constructor initializer is `new T` is NON-NULL on any real
            // instance. When the heap object (materialized for a DEX-defined
            // class, e.g. a view node whose <init> the inflater did not run)
            // has NO entry — or a null/zero entry — for the field, materialize
            // the initializer type instead of answering a manufactured null
            // (chess: ContentFrameLayout.mDecorPadding Rect read null ->
            // Rect.set NPE -> onCreate dead). The value is STORED so identity
            // stays stable.
            {
                // F-NEW-252 (explicit-null beats initializer law): a heap
                // ENTRY holding NULL_REF is a NULL that executed bytecode
                // WROTE (iput-object with a null source — dooz draw path:
                // Lpz0;.L0 stores its null p2 into Lkc;.c, and Lyl;.z's
                // `if-eqz v2` null-guard then skips the tracker block, which
                // is the real-ART behavior). Fabricating the initializer
                // default over an explicit null turned the app's legal null
                // into a fake `new Object`, forced the tracker read, and
                // crashed dispatchDraw with the app's own
                // "Only add dependencies during a tracking block" IAE.
                // Absent entries (no value at all) and dangling refs stay
                // missing — the chess ContentFrameLayout.mDecorPadding case
                // (inflater-materialized object whose <init> never ran) is
                // unchanged: its fields have NO entries.
                bool r414_missing = !field_val.has_value();
                if (!r414_missing) {
                    const DalvikValue& fv = field_val.value();
                    r414_missing =
                        (fv.type == DalvikType::OBJECT_REF &&
                         fv.object_id == 0) ||
                        (fv.type == DalvikType::OBJECT_REF &&
                         !heap_.has_object(fv.object_id));
                }
                if (r414_missing) {
                    const HeapObject* r414_hobj = heap_.get(obj_ref.object_id);
                    std::string r414_cls =
                        r414_hobj ? r414_hobj->class_descriptor
                                  : field_res.class_descriptor;
                    if (std::getenv("MINIANDROID_R414_TRACE") != nullptr) {
                        static thread_local uint64_t r414_dbg_n = 0;
                        if (r414_dbg_n < 40) {
                            ++r414_dbg_n;
                            std::cerr << "[R414-PROBE] field "
                                      << field_res.class_descriptor << "."
                                      << field_res.field_name << " recv_cls="
                                      << r414_cls << " dex_defined="
                                      << (class_info_index_.count(r414_cls) > 0)
                                      << " caller=" << current_class_ << "."
                                      << current_method_ << " pc=" << pc
                                      << std::endl;
                        }
                    }
                    // S134 F-NEW-160 LAW FIX: the initializer scan must read
                    // the FIELD'S DECLARING CLASS only, and the initializer
                    // type must MATCH the declared field type. The previous
                    // receiver-chain walk matched by NAME alone, so an
                    // unrelated same-named field of a superclass leaked its
                    // initializer into this read (solitaire 71: `e.m`
                    // (delegate, no initializer) picked up classes.c's
                    // `m = new b.b()` Handler → the Handler answered as the
                    // AppCompat delegate → Window null → boot death — the
                    // exact name-aliasing family this law closes).
                    // ART law: a field initializer belongs to the class that
                    // DECLARES the field; identity is (class, name, type).
                    if (!field_res.class_descriptor.empty() &&
                        field_res.class_descriptor[0] == 'L' &&
                        !field_res.field_name.empty()) {
                    {
                        std::string walk = field_res.class_descriptor;
                        scan_init_field_defaults(walk);
                        auto fm = init_field_defaults_.find(walk);
                        if (fm != init_field_defaults_.end()) {
                            auto ft = fm->second.find(field_res.field_name);
                            if (ft != fm->second.end() && !ft->second.empty() &&
                                ft->second == field_res.field_type) {
                                // F-NEW-274 constructor-contract gate: fabricate
                                // ONLY when the initializer type has a ()V ctor
                                // (or is framework-owned). Otherwise the honest
                                // ART default (null) flows and the app's own
                                // null-handling runs.
                                if (!class_has_no_arg_ctor(ft->second)) {
                                    // ── [S188-W4] INNER-CLASS INITIALIZER
                                    // CAPTURE LAW ─────────────────────────
                                    // F274 honest-null fired for
                                    // Material/RecyclerView
                                    // RecyclerViewAccessibilityDelegate
                                    // (tranquilstopwatch + solitaire census):
                                    // field Ls1/m1;.e : Ls1/l1; — l1 is the
                                    // INNER class whose ONLY ctor is
                                    // <init>(Ls1/m1;)V (outer-this capture,
                                    // javac lowers `this.new Inner()` to
                                    // exactly that). ART runs the REAL ctor
                                    // with the receiver as the outer
                                    // argument. Fabricate the same way: run
                                    // the REAL DEX ctor; fall back to honest
                                    // null only when no such capture-ctor
                                    // exists or it fails.
                                    bool inner_made = false;
                                    DalvikValue inner_dv;
                                    if (ft->second.size() > 2 &&
                                        ft->second.front() == 'L') {
                                        auto ccit =
                                            class_info_index_.find(ft->second);
                                        if (ccit != class_info_index_.end() &&
                                            ccit->second <
                                                dex_report_->classes.size()) {
                                            const auto& ccls =
                                                dex_report_->classes
                                                    [ccit->second];
                                            for (const auto& m :
                                                 ccls.direct_methods) {
                                                if (m.name != "<init>" ||
                                                    m.descriptor.empty() ||
                                                    m.descriptor.front() !=
                                                        '(')
                                                    continue;
                                                // capture-ctor shape:
                                                // (L<declaring>;)V where
                                                // declaring == walk
                                                std::string want =
                                                    "(L" + walk.substr(1);
                                                if (m.descriptor != want + ")V")
                                                    continue;
                                                uint32_t oid = heap_.allocate(
                                                    ft->second, pc, 0);
                                                if (oid == 0) break;
                                                DalvikValue self_v =
                                                    DalvikValue::make_object(
                                                        oid, ft->second);
                                                DalvikValue outer_v =
                                                    obj_ref;  // receiver IS
                                                              // the outer
                                                              // this
                                                DalvikValue ctor_ret;
                                                DalvikExecutionResult ctor_res;
                                                std::vector<DalvikValue>
                                                    ctor_args{self_v, outer_v};
                                                inner_made =
                                                    try_recursive_invoke(
                                                        ft->second, "<init>",
                                                        ctor_args, ctor_ret,
                                                        ctor_res,
                                                        m.descriptor);
                                                if (inner_made) {
                                                    inner_dv = self_v;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                    if (inner_made) {
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            s134_dex_field_key(
                                                resolved_field_declarer(
                                                    field_res.class_descriptor,
                                                    field_res.field_name),
                                                field_res.field_name, true),
                                            inner_dv);
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            field_res.field_name, inner_dv);
                                        std::cerr << "[S188-W4-INNER-INIT] "
                                                  << walk << "."
                                                  << field_res.field_name
                                                  << " = new " << ft->second
                                                  << "(this) REAL ctor obj#"
                                                  << inner_dv.object_id
                                                  << " caller="
                                                  << current_class_ << "."
                                                  << current_method_
                                                  << " pc=" << pc << std::endl;
                                        result_value = inner_dv;
                                        field_val = inner_dv;
                                    } else {
                                    static thread_local uint64_t f274_n = 0;
                                    if (f274_n < 16) {
                                        ++f274_n;
                                        std::cerr << "[F274-CTORGATE] "
                                                  << walk << "."
                                                  << field_res.field_name
                                                  << " initializer type "
                                                  << ft->second
                                                  << " has no ()V ctor -> honest null (recv="
                                                  << r414_cls << " caller="
                                                  << current_class_ << "."
                                                  << current_method_
                                                  << " pc=" << pc << ")"
                                                  << std::endl;
                                    }
                                    }
                                } else {
                                    DalvikValue dv =
                                        materialize_init_default(ft->second);
                                    if (dv.type == DalvikType::OBJECT_REF &&
                                        dv.object_id != 0) {
                                        // S134 F-NEW-160: store under the
                                        // QUALIFIED identity (declaring class
                                        // + name) so the next qualified read
                                        // re-hits the SAME object (identity
                                        // stability); bare mirror for legacy
                                        // C++ readers.
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            s134_dex_field_key(
                                                resolved_field_declarer(
                                                    field_res.class_descriptor,
                                                    field_res.field_name),
                                                field_res.field_name, true),
                                            dv);
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            field_res.field_name, dv);
                                        static thread_local uint64_t r414_n = 0;
                                        if (r414_n < 24) {
                                            ++r414_n;
                                            std::cerr << "[R414-INIT-DEFAULT] "
                                                      << walk << "."
                                                      << field_res.field_name
                                                      << " obj#"
                                                      << obj_ref.object_id
                                                      << " = new " << ft->second
                                                      << " (recv=" << r414_cls
                                                      << " caller="
                                                      << current_class_ << "."
                                                      << current_method_
                                                      << " pc=" << pc << ")"
                                                      << std::endl;
                                        }
                                        result_value = dv;
                                        field_val = dv;
                                    }
                                }
                            }
                        }
                    }
                    }
                }
            }
            // ── [S188-W4] FRAMEWORK OBSERVABLE INVARIANT LAW ──────────────
            // AOSP android.database.Observable: field initializer
            // `mObservers = new ArrayList<Object>()` runs for EVERY subclass
            // instance (javac inlines it into the default ctor the subclass
            // super() chain calls). Engine gap: framework superclasses have
            // no DEX body, so a Material Observable subclass (Ls1/o0; —
            // tranquilstopwatch + solitaire NavigationView chain) reached
            // `mObservers.isEmpty()` with a null list → NPE →
            // NavigationView.<init> died → app blank. AOSP invariant:
            // mObservers is NEVER null on a constructed Observable.
            if (!field_val.has_value() &&
                field_res.class_descriptor == "Landroid/database/Observable;" &&
                field_res.field_name == "mObservers" &&
                obj_ref.object_id != 0) {
                uint32_t list_oid =
                    heap_.allocate("Ljava/util/ArrayList;", pc, 0);
                if (list_oid != 0) {
                    DalvikValue dv =
                        DalvikValue::make_object(list_oid,
                                                 "Ljava/util/ArrayList;");
                    heap_.set_object_field(
                        obj_ref.object_id,
                        s134_dex_field_key(
                            resolved_field_declarer(field_res.class_descriptor,
                                                    field_res.field_name),
                            field_res.field_name, true),
                        dv);
                    heap_.set_object_field(obj_ref.object_id,
                                           field_res.field_name, dv);
                    std::cerr << "[S188-W4-OBSERVABLE] mObservers invariant "
                              << "obj#" << obj_ref.object_id
                              << " = ArrayList#" << list_oid
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                    field_val = dv;
                }
            }
            // S72 null-field probe (env-gated, bounded, read-only): a read
            // where the heap object has NO ENTRY for the field means the
            // iput never ran (silent-lost write or skipped <init>) — the
            // engine then answers null-with-empty-desc downstream, which is
            // how dooz's trie nodes reached arraycopy(null).
            if (!field_val.has_value()) {
                static thread_local const char* nf_filter =
                    std::getenv("MINIANDROID_NULLFIELD_TRACE");
                static thread_local uint64_t nf_n = 0;
                if (nf_filter && nf_n < 30) {
                    if (std::string(nf_filter) == "*" ||
                        field_res.field_name == nf_filter) {
                        ++nf_n;
                        const HeapObject* hobj = heap_.get(obj_ref.object_id);
                        std::cerr << "[NULLFIELD] "
                                  << (hobj ? hobj->class_descriptor
                                           : field_res.class_descriptor)
                                  << "->" << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " UNSET (iput never ran)"
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                    }
                }
            }
            if (field_val.has_value()) {
                result_value = field_val.value();
                // ── F-065 (R-NEW-289): const-class FIELD ROUND-TRIP law ────
                // ART: java.lang.Class instances are real objects with
                // identity — a Class reference stored with iput-object and
                // read back with iget-object is the SAME reference, and is
                // NON-NULL. The engine's Class representation is CLASS_REF
                // (class_desc = referred type descriptor — the bridge law
                // FIX-M3-012 serves Class.getName/forName/getPackage on
                // exactly that form). The old blanket retag below rewrote a
                // stored CLASS_REF to OBJECT_REF while keeping object_id=0
                // (make_class stores the token in ref_id, not object_id) —
                // a pseudo-null by the is-zero law (OBJECT_REF && oid==0).
                // Every Kotlin `T::class.java` round-trip through a field
                // then failed Intrinsics.checkNotNull — real-APK hit: dooz
                // SavedStateHandlesVM creation (y.c → M1/u.a → new
                // LM1/d(jClass) → LM1/d;.a reads field a → OBJECT_REF{0}
                // → M1/i.d NPE "null cannot be cast to non-null type
                // java.lang.Class<...get-java>" → first frame died).
                // CLASS_REF now round-trips identity-verbatim like
                // OBJECT_REF/STRING_REF. No app special-casing: every
                // const-class field round-trip in every APK benefits.
                if (result_value.type != DalvikType::OBJECT_REF &&
                    result_value.type != DalvikType::NULL_REF &&
                    result_value.type != DalvikType::STRING_REF &&
                    result_value.type != DalvikType::CLASS_REF) {
                    result_value.type = DalvikType::OBJECT_REF;
                }
            }
        }
    }
    // S122 (R-NEW-414b): receiver NOT heap-backed — the in-heap law above
    // never ran. The receiver id is a VIEW NODE (e.g. the android.R.id.content
    // ContentFrameLayout node, id 800100 — chess evidence: Lg/c0;.y pc=454
    // reads the AOSP mDecorPadding Rect, gets a manufactured null, and the
    // following Rect.set NPE unwinds onCreate -> blank screen). Same honest
    // initializer default, answered from the field's DECLARING class and
    // cached per (node id, field) so identity stays stable across reads.
    if (result_value.type == DalvikType::NULL_REF &&
        obj_ref.type == DalvikType::OBJECT_REF && obj_ref.object_id != 0 &&
        !heap_.has_object(obj_ref.object_id) && !field_res.field_name.empty() &&
        !field_res.class_descriptor.empty() &&
        field_res.class_descriptor[0] == 'L') {
        auto nfkey = std::make_pair(obj_ref.object_id, field_res.field_name);
        auto cached = node_field_defaults_.find(nfkey);
        if (cached != node_field_defaults_.end()) {
            result_value =
                DalvikValue::make_object(cached->second, field_res.class_descriptor);
        } else {
            std::string walk = field_res.class_descriptor;
            for (int hop = 0; hop < 8 && !walk.empty(); ++hop) {
                scan_init_field_defaults(walk);
                auto fm = init_field_defaults_.find(walk);
                if (fm != init_field_defaults_.end()) {
                    auto ft = fm->second.find(field_res.field_name);
                    if (ft != fm->second.end() && !ft->second.empty()) {
                        // F-NEW-274 constructor-contract gate (same law as the
                        // in-heap arm): a class with no ()V constructor has no
                        // legal zero-state instance — answer the honest ART
                        // default (null) instead of a fabricated object.
                        if (!class_has_no_arg_ctor(ft->second)) {
                            static thread_local uint64_t f274b_n = 0;
                            if (f274b_n < 16) {
                                ++f274b_n;
                                std::cerr << "[F274-CTORGATE-B] field "
                                          << field_res.class_descriptor << "."
                                          << field_res.field_name
                                          << " initializer type " << ft->second
                                          << " has no ()V ctor -> honest null"
                                          << std::endl;
                            }
                            break;
                        }
                        DalvikValue dv = materialize_init_default(ft->second);
                        if (dv.type == DalvikType::OBJECT_REF &&
                            dv.object_id != 0) {
                            node_field_defaults_[nfkey] = dv.object_id;
                            static thread_local uint64_t r414b_n = 0;
                            if (r414b_n < 16) {
                                ++r414b_n;
                                std::cerr << "[R414B-NOHEAP] field "
                                          << field_res.class_descriptor << "."
                                          << field_res.field_name
                                          << " node#" << obj_ref.object_id
                                          << " = new " << ft->second
                                          << " (caller=" << current_class_
                                          << "." << current_method_
                                          << " pc=" << pc << ")"
                                          << std::endl;
                            }
                            result_value = dv;
                        }
                        break;
                    }
                }
                auto sit = class_to_superclass_.find(walk);
                walk = (sit != class_to_superclass_.end()) ? sit->second : "";
            }
        }
    }
    // ── F-NEW-271 LAW DIAG (read-side twin, env-gated MINIANDROID_FIELD_LAW_DIAG,
    // bounded, read-only). A field read answering a STRING_REF while the
    // field's declared type (from field_ids) is NOT Ljava/lang/String is an
    // alien-typed value — the exact face F-271 recorded on Lnb0.j (STRING_REF
    // in a :Lqb0 slot). Dump the read-key identity (qualified vs bare via the
    // resolved declarer), the receiver's heap class, and the receiver's FULL
    // field map (all slots, keys, types, bounded contents) so the polluted
    // slot and the value's origin are both visible. The write-side twin lives
    // in execute_iput_object and catches the alien store in the act.
    // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
    // std::getenv per read.
    static const bool f271_law_diag = std::getenv("MINIANDROID_FIELD_LAW_DIAG") != nullptr;
    if (f271_law_diag &&
        result_value.type == DalvikType::STRING_REF &&
        field_res.field_type != "Ljava/lang/String;") {
        static thread_local uint64_t f271_rn = 0;
        if (f271_rn < 40) {
            ++f271_rn;
            std::cerr << "[F271-READ] " << current_class_ << "."
                      << current_method_ << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name << " : " << field_res.field_type
                      << " answered STRING_REF len="
                      << result_value.string_val.size()
                      << " str=\"" << result_value.string_val.substr(0, 48)
                      << "\"";
            if (obj_ref.type == DalvikType::OBJECT_REF) {
                const std::string f271_decl = resolved_field_declarer(
                    field_res.class_descriptor, field_res.field_name);
                std::cerr << " recv#" << obj_ref.object_id
                          << " recv_reg_cls=" << obj_ref.class_desc
                          << " declarer=" << f271_decl
                          << " dex_defined="
                          << (is_dex_defined_class(f271_decl) ? 1 : 0)
                          << " readkey="
                          << s134_dex_field_key(
                                 f271_decl, field_res.field_name,
                                 is_dex_defined_class(f271_decl));
                if (heap_.has_object(obj_ref.object_id)) {
                    const HeapObject* f271_ho = heap_.get(obj_ref.object_id);
                    if (f271_ho) {
                        std::cerr << " heap_cls=" << f271_ho->class_descriptor
                                  << " fields[" << f271_ho->fields.size()
                                  << "]:";
                        int f271_nf = 0;
                        for (const auto& [fk, fv] : f271_ho->fields) {
                            if (f271_nf++ >= 20) {
                                std::cerr << " ...";
                                break;
                            }
                            std::cerr << " " << fk << "=t"
                                      << static_cast<int>(fv.type) << "/o"
                                      << fv.object_id;
                            if (fv.type == DalvikType::STRING_REF)
                                std::cerr << "(\""
                                          << fv.string_val.substr(0, 32)
                                          << "\")";
                        }
                    }
                } else {
                    std::cerr << " recv-not-in-heap";
                }
            }
            std::cerr << std::endl;
        }
    }
    // EXP-042 Phase 2: if obj_ref is not OBJECT_REF (uninit, null, primitive),
    // just return null. Previously this returned false and caused infinite
    // loops in ComponentActivity.onCreate, UserConfig.isClientActivated,
    // FragmentActivity.onCreate, etc.

    // EXP-055: Debug — log iget-object result for isClientActivated investigation.
    // R-NEW-539 (CONT-36): env-gated behind MINIANDROID_TG_DEBUG (the
    // telegram hot-path iget stream; ungated fprintf burn, bounded-logging
    // law). Identical output when the flag is set.
    {
        static thread_local const bool tg_dbg2 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg2 &&
        current_class_.find("UserConfig") != std::string::npos &&
        (current_method_ == "isClientActivated" || current_method_ == "getCurrentUser")) {
        std::cerr << "[IGET-OBJ-DBG] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_reg_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }
    }

    // EXP-071 Phase 6 debug: Trace iget-object for TL_nearestDc.country
    // to understand why setCountry receives null for the country argument.
    // R-NEW-539 (CONT-36): env-gated (MINIANDROID_TG_DEBUG) — bounded-logging
    // law; the country-field stream is telegram hot-path.
    {
        static thread_local const bool tg_dbg4 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg4 &&
        field_res.field_name == "country" &&
        field_res.class_descriptor.find("nearestDc") != std::string::npos) {
        std::cerr << "[EXP071-IGET-COUNTRY] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_reg_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type);
        if (result_value.type == DalvikType::STRING_REF) {
            std::cerr << " str=\"" << result_value.string_val << "\"";
        }
        std::cerr << std::endl;
    }
    }

    // EXP-059: Debug — log iget-object in addFragmentToStack
    // R-NEW-539 (CONT-36): env-gated (MINIANDROID_TG_DEBUG).
    {
        static thread_local const bool tg_dbg5 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg5 && current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IGET] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest_reg
                  << " obj=v" << (int)obj_reg
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }
    }

    // EXP-060: Debug — log iget-object for parentLayout in presentFragment
    // R-NEW-539 (CONT-36): env-gated (MINIANDROID_TG_DEBUG).
    {
        static thread_local const bool tg_dbg6 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg6 && field_res.resolved &&
        field_res.field_name == "parentLayout" &&
        current_method_ == "presentFragment") {
        std::cerr << "[EXP060-IGET] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " obj=v" << (int)obj_reg
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }
    }

    set_register(dest_reg, result_value);
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }
    
    pc_ = pc + 2;  // 22c format = 2 code units
    return true;
}

bool DalvikExecutionEngine::execute_iput(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iput vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: never return false — always advance pc_.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];

    // R-NEW-467: memoized resolution (same value the fresh walk answers).
    const DalvikExecutionEngine::FieldMemo& field_memo_iput
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo_iput.res;
    DalvikValue src_val = get_register(src_reg);
    DalvikValue obj_ref = get_register(obj_reg);

    // S135 F-NEW-365 (S57 wave, merge complement): ART null-receiver FIELD
    // law for the WRITE forms. F-NEW-268d (CONT-18g) closed iget/iget-object;
    // the iput family kept the EXP-042 silent-drop — a null receiver wrote
    // nowhere and the body kept running with this=NULL (same disease family
    // F-141/F-268d eliminated for reads). ART throws NPE at the write site
    // ("Attempt to write to field ... on a null object reference").
    if (field_res.resolved && f141_is_null_receiver(obj_ref)) {
        raise_synthetic_exception(
            "Ljava/lang/NullPointerException;",
            "Attempt to write to field '" + field_res.class_descriptor + "." +
                field_res.field_name + ":" + field_res.field_type +
                "' on a null object reference",
            "iput-null-recv");
        return true;  /* pc_ set by raise (catch handler) or frame unwind */
    }

    // ── S211 (DIAG-ONLY, env-gated MINIANDROID_S211_SEGTRACE): dooz zombie
    // probe — every iput into a Lbw0; (kotlinx Segment family) field logs
    // (obj#, field, written value, caller, pc). The initializer `.f` writes
    // the mask `c` — the writer identity + value answers whether c is
    // capacity-consistent (7 -> Object[7]) or garbage-sourced.
    {
        static const bool s211w_on = diag_env("MINIANDROID_S211_SEGTRACE");
        if (s211w_on && field_res.resolved &&
            field_res.class_descriptor == "Lbw0;") {
            static thread_local uint64_t s211_wn = 0;
            if (s211_wn++ < 400) {
                uint32_t s211_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[S211-IPUT] Lbw0;." << field_res.field_name
                          << " obj#" << s211_recv
                          << " val=" << dalvik_value_to_string(src_val)
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
            }
        }
    }

    // ── S221b (DIAG-ONLY, env-gated MINIANDROID_S221_DENSTRACE): the WRITE
    // twin of S221-ZERODENS — every iput of 0.0f into Lmb1; fields (the
    // InlineDensity value class: a=density b=fontScale) logs the WRITER
    // chain. Upstream constructs Unspecified ONLY from the cache density
    // setter's null path (`value?.let{...} ?: InlineDensity.Unspecified`);
    // the writer identity decides the fix surface (runtime delivery vs
    // app-side substitution-null propagation).
    {
        static const bool s221w_on = diag_env("MINIANDROID_S221_DENSTRACE");
        if (s221w_on && field_res.resolved &&
            field_res.class_descriptor == "Lmb1;" &&
            src_val.type == DalvikType::FLOAT32 &&
            src_val.float_val == 0.0f) {
            static thread_local uint64_t s221w_n = 0;
            if (s221w_n++ < 40) {
                uint32_t s221w_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[S221b-ZEROW] Lmb1;." << field_res.field_name
                          << " obj#" << s221w_recv
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc;
                auto s221w_frames = call_stack_.snapshot_top_first();
                for (size_t fi = 0;
                     fi < s221w_frames.size() && fi < 6; ++fi)
                    std::cerr << " <" << s221w_frames[fi].first << "."
                              << s221w_frames[fi].second << ">";
                std::cerr << std::endl;
            }
        }
    }

    // ── CONT-47 D8 (DIAG-ONLY, env-gated): place-descent witness — every
    // write to Lel0;.e (the D7 placecheck showed e=F on all 44 inserted
    // chain nodes at draw: whatever sets e=T = the place walk). Print
    // receiver + written value + caller so the descent's reach is visible.
    {
        static const bool d8_on = diag_env("MINIANDROID_D8_EWRITE");
        if (d8_on && field_res.resolved &&
            field_res.class_descriptor == "Lel0;" &&
            field_res.field_name == "e") {
            static thread_local uint64_t d8_wn = 0;
            if (d8_wn < 64) {
                ++d8_wn;
                uint32_t d8_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::string d8_v = "?";
                if (src_val.type == DalvikType::BOOLEAN)
                    d8_v = src_val.bool_val ? "T" : "F";
                else if (src_val.type == DalvikType::INT32)
                    d8_v = src_val.int_val ? "T" : "F";
                std::cerr << "[D8-EWRITE] w#" << d8_wn
                          << " recv=o" << d8_recv << " e=" << d8_v
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }

    // ── TRAIN-64 (T64, DIAG-ONLY, env-gated MINIANDROID_T64_CHANGE_TRACE):
    // pointer-change field WRITE law. Lu71; = PointerInputChange (R8):
    // d=pressed, h=previousPressed, o=isConsumed. The MotionEvent→
    // PointerInputChange adapter writes these during the touch dispatch;
    // waitForUpOrCancellation's fastAll{changedToUp} (= !d && h) dies when
    // the UP change never gets h=true. Log every boolean write — pairs
    // with the [T64-R] read probe to pin the exact wrong field.
    {
        static const bool t64w_on = diag_env("MINIANDROID_T64_CHANGE_TRACE");
        if (t64w_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lu71;") {
            static const char* t64w_bools[] = {"d", "h", "o", "p"};
            for (const char* t64wb : t64w_bools) {
                if (field_res.field_name == t64wb) {
                    static thread_local uint64_t t64w_n = 0;
                    if (t64w_n++ < 400) {
                        uint32_t t64w_recv =
                            (obj_ref.type == DalvikType::OBJECT_REF)
                                ? obj_ref.object_id : 0;
                        std::cerr << "[T64-W] Lu71;." << field_res.field_name
                                  << " obj#" << t64w_recv << " = "
                                  << dalvik_value_to_string(src_val)
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    }
                    break;
                }
            }
        }
        // T64-QW: the q-chain write (who links a change to another).
        if (t64w_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lu71;" &&
            field_res.field_name == "q") {
            static thread_local uint64_t t64qw_n = 0;
            if (t64qw_n++ < 64) {
                uint32_t t64qw_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[T64-QW] Lu71;.q obj#" << t64qw_recv << " = "
                          << dalvik_value_to_string(src_val)
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
        // T64-C2: the RAW PointerInputEventData isInitiallyConsumed write
        // (Lw71;.g) — feeds Las0;.t's change ctor slot 14; the DOWN was
        // born with 1 (should be 0) which kills awaitFirstDown's
        // changedToDown() (!isConsumed) — log the writer and the value.
        if (t64w_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lw71;" &&
            field_res.field_name == "g") {
            static thread_local uint64_t t64g_n = 0;
            if (t64g_n++ < 64) {
                uint32_t t64g_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[T64-G] Lw71;.g obj#" << t64g_recv << " = "
                          << dalvik_value_to_string(src_val)
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }

    // ── F-NEW-406 (CONT-99 T1): DEX float-bit register law at the FIELD-
    // STORE boundary. DEX float registers carry raw IEEE-754 BITS in int
    // registers — `const/high16 v0, 0x3f800000` IS the literal float 1.0f
    // and no conversion instruction runs along that path (int-to-float is
    // only emitted when the source was a genuine int). A store into a
    // declared-float field must therefore BIT-CAST the register bits into
    // the FLOAT32 value; the old raw store left the field as INT32 bits,
    // and every float reader saw the bit pattern VALUE-cast (c99lay probe:
    // LinearLayout.LayoutParams.weight read 1.06535e9 instead of 1.0f —
    // the 0px+weight children collapsed to width 0 / full-width garbage).
    // Symmetric law for declared-double fields (wide register = INT64
    // bits). Genuine-int stores into float fields do not exist in DEX
    // (the verifier requires float registers for F fields).
    if (field_res.resolved && field_res.field_type == "F" &&
        src_val.type == DalvikType::INT32) {
        float fbits = 0.0f;
        std::memcpy(&fbits, &src_val.int_val, sizeof(fbits));
        src_val.type = DalvikType::FLOAT32;
        src_val.float_val = fbits;
    } else if (field_res.resolved && field_res.field_type == "D" &&
               src_val.type == DalvikType::INT64) {
        double dbits = 0.0;
        std::memcpy(&dbits, &src_val.long_val, sizeof(dbits));
        src_val.type = DalvikType::FLOAT64;
        src_val.double_val = dbits;
    }
    if (field_res.resolved && obj_ref.type == DalvikType::OBJECT_REF &&
        heap_.has_object(obj_ref.object_id)) {
        // S134 F-NEW-160: dual write — qualified primary key (declaring
        // class + name) + bare legacy mirror (C++ shadow readers).
        // F-NEW-321 (CONT-50): the mirror write is RAW (exact bare key, no
        // F-NEW-251 redirect) — the redirect re-resolves the bare name
        // against the receiver's most-derived declarer, so a SUPERCLASS
        // write's mirror landed in the SUBCLASS's shadowed qualified slot
        // (solitaire 71: ay$a.<init> mObservable mirror clobbered c$b.a =
        // the outer presenter; probe fnew320 N2 PRE face). The mirror is a
        // legacy channel, not a second identity resolution.
        {
            // F-NEW-325: true-declarer keying — a framework-owned field
            // (no DEX declarer; the bare/raw mirror IS the slot) stays
            // bare even when the REF class is DEX-defined; a real DEX
            // declarer keeps the qualified slot + the raw bare mirror
            // (F-NEW-321 law unchanged).
            const std::string& s134_decl = field_memo_iput.s134_decl;
            if (!is_dex_defined_class(s134_decl)) {
                heap_.set_object_field(obj_ref.object_id, field_res.field_name,
                                       src_val);
            } else {
                heap_.set_object_field(obj_ref.object_id,
                    s134_dex_field_key(s134_decl, field_res.field_name, true),
                    src_val);
                heap_.set_object_field_raw(obj_ref.object_id,
                                           field_res.field_name, src_val);
            }
        }
        // ── TRAIN-68 (T68-JOBPUT): the pointerInputJob WRITE side — the lazy
        // launch stores the Job; log every write with receiver identity.
        {
            static const bool t68p_on = diag_env("MINIANDROID_T68_NODE_TRACE");
            if (t68p_on && field_res.class_descriptor == "Lor1;" &&
                field_res.field_name == "v") {
                static thread_local uint64_t t68p_n = 0;
                if (t68p_n++ < 120) {
                    std::cerr << "[T68-JOBPUT] Lor1;.v obj#"
                              << obj_ref.object_id << " val="
                              << dalvik_value_to_string(src_val)
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc_ << std::endl;
                }
            }
        }
        // ── TRAIN-67 (T67-IPUT): the label WRITE side — the iput before the
        // suspend must land on the SAME object the resume reads. Log writes
        // to the machine's label (l) and spill (k) slots with obj identity.
        {
            static const bool t67w_on = diag_env("MINIANDROID_T67_LABEL_TRACE");
            if (t67w_on && (field_res.class_descriptor == "Lss1;" ||
                            field_res.class_descriptor == "Lxs1;" ||
                            field_res.class_descriptor == "Li6;")) {
                static thread_local uint64_t t67w_n = 0;
                if (t67w_n++ < 600) {
                    std::cerr << "[T67-IPUT] Lss1;." << field_res.field_name
                              << " obj#" << obj_ref.object_id
                              << " val=" << dalvik_value_to_string(src_val)
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                }
            }
        }
        // M3 FIELD-TRACE (AG diagnostic): env-gated field-store value trace.
        // NOTE: render via dalvik_value_to_string — printing .long_val on an
        // INT32 union read shows stale upper bytes as false corruption.
        if (field_trace_filter_set() &&
            field_trace_active(field_res.field_name.c_str(),
                               (current_class_ + "." + current_method_).c_str(),
                               field_res.class_descriptor.c_str())) {
            std::cerr << "[FIELD-TRACE] put " << current_class_ << "."
                      << current_method_ << " "
                      << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " obj#" << obj_ref.object_id
                      << " value=" << dalvik_value_to_string(src_val) << std::endl;
        }
        // M3-DIAG (temporary): long field writes — Alarm expiresMs math.
        static thread_local uint64_t m3w = 0;
        if (src_val.type == DalvikType::INT64 && m3w < 30) {
            m3w++;
            std::cerr << "[M3-LONG-PUT] field="
                      << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " caller=" << current_class_ << "." << current_method_
                      << " value=" << src_val.long_val << std::endl;
        }
    }
    // EXP-042 Phase 2: on any failure path, just advance pc_ — never spin.

    // EXP-092+ INSTRUMENTATION: Log every write to PhoneView.countryState
    // to trace the root cause of the onNextPressed needShowAlert branch.
    // The field is field@33152 in classes4.dex, declared on
    // Lorg/telegram/ui/LoginActivity$PhoneView; as `int countryState`.
    // Values observed:
    //   0 = set by setCountry (after auto-detection from getNearestDc response)
    //   1 = set by <init> and afterTextChanged (default / user-typed-but-no-match)
    //   2 = set by afterTextChanged when country code matches (COUNTRY_SELECTED)
    if (field_res.resolved &&
        field_res.field_name == "countryState" &&
        field_res.class_descriptor.find("PhoneView") != std::string::npos) {
        int32_t new_val = 0;
        if (src_val.type == DalvikType::INT32 || src_val.type == DalvikType::BOOLEAN) {
            new_val = src_val.int_val;
        }
        std::cerr << "[EXP092-COUNTRYSTATE-WRITE] pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << " obj_id=" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                  << " new_value=" << new_val
                  << " src_type=" << static_cast<int>(src_val.type)
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log every write to LoginActivity.currentViewNum
    // (field@33189) to trace the page transition. This is the field that
    // tracks which page (PhoneView, SmsView, etc.) is currently active.
    if (field_res.resolved &&
        field_res.field_name == "currentViewNum" &&
        field_res.class_descriptor.find("LoginActivity;") != std::string::npos &&
        field_res.class_descriptor.find("PhoneView") == std::string::npos) {
        int32_t new_val = 0;
        if (src_val.type == DalvikType::INT32 || src_val.type == DalvikType::BOOLEAN) {
            new_val = src_val.int_val;
        }
        std::cerr << "[EXP092-CURRENTVIEWNUM-WRITE] pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << " obj_id=" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                  << " new_value=" << new_val
                  << " src_type=" << static_cast<int>(src_val.type)
                  << std::endl;
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_iput_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iput-object vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: never return false — always advance pc_.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    // F-NEW-282 (store side): a CLASS_REF source value written through
    // iput-object must land as its heap-backed Class token (F-103 identity
    // map), not as a raw class-typed register value — raw CLASS_REF does
    // not survive the frame machinery (see the F-NEW-282 law comment in
    // execute_method_internal) and consumers read the field back as
    // null/unset (oracle: ClassReference.jClass → getJClass/equals/
    // isInstance/getQualifiedName all null). Same generic law as the
    // argument-boundary materialization; no app knowledge.

    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];

    // R-NEW-467: memoized resolution (same value the fresh walk answers).
    const DalvikExecutionEngine::FieldMemo& field_memo_iputo
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo_iputo.res;
    DalvikValue src_val = get_register(src_reg);
    // F-NEW-282 (store side) — materialize now that src_val is bound.
    if (src_val.type == DalvikType::CLASS_REF && !src_val.class_desc.empty()) {
        auto f282_it = class_token_ids_.find(src_val.class_desc);
        uint32_t f282_token = 0;
        if (f282_it != class_token_ids_.end()) {
            f282_token = f282_it->second;
        } else {
            f282_token = heap_.allocate("Ljava/lang/Class;", pc_, 0);
            heap_.set_object_field(f282_token, "__referent_desc",
                                   DalvikValue::make_string(src_val.class_desc, 0));
            class_token_ids_.emplace(src_val.class_desc, f282_token);
        }
        src_val = DalvikValue::make_object(f282_token, "Ljava/lang/Class;");
    }
    DalvikValue obj_ref = get_register(obj_reg);
    // ── TRAIN-68 (T68-JOBPUT-OBJ): the pointerInputJob store is an
    // IPUT-OBJECT (Lor1;.v:Lkp1;) — log the write with receiver identity.
    {
        static const bool t68po_on = diag_env("MINIANDROID_T68_NODE_TRACE");
        if (t68po_on && field_res.class_descriptor == "Lor1;" &&
            field_res.field_name == "v") {
            static thread_local uint64_t t68po_n = 0;
            if (t68po_n++ < 120)
                std::cerr << "[T68-JOBPUT-OBJ] Lor1;.v obj#"
                          << (obj_ref.type == DalvikType::OBJECT_REF
                                  ? obj_ref.object_id : 0)
                          << " val="
                          << (src_val.type == DalvikType::OBJECT_REF
                                  ? ("obj#" + std::to_string(src_val.object_id))
                                  : dalvik_value_to_string(src_val))
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
        // W5 (Coder-4) DIAG: Koin Module.includedModules store forensics.
        static const bool f566f_on =
            diag_env("MINIANDROID_F566_FIELD_DIAG");
        if (f566f_on && field_res.resolved &&
            (field_res.field_name == "includedModules" ||
             field_res.field_name == "includes")) {
            static thread_local uint64_t f566f_n = 0;
            if (f566f_n++ < 60)
                std::cerr << "[F566-IPUT] " << field_res.field_name << " obj#"
                          << (obj_ref.type == DalvikType::OBJECT_REF
                                  ? obj_ref.object_id : 0)
                          << " <- "
                          << (src_val.type == DalvikType::OBJECT_REF
                                  ? ("obj#" + std::to_string(src_val.object_id))
                                  : dalvik_value_to_string(src_val))
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
    }
    // S135 F-NEW-365 (S57 wave, merge complement): ART null-receiver FIELD
    // law, iput-object form — same family as the execute_iput law above
    // (F-NEW-268d closed the reads; the writes stayed silent until now).
    if (field_res.resolved && f141_is_null_receiver(obj_ref)) {
        raise_synthetic_exception(
            "Ljava/lang/NullPointerException;",
            "Attempt to write to field '" + field_res.class_descriptor + "." +
                field_res.field_name + ":" + field_res.field_type +
                "' on a null object reference",
            "iput-null-recv");
        return true;  /* pc_ set by raise (catch handler) or frame unwind */
    }
    if (field_res.resolved && field_res.field_name == "actionBarLayout") {
        std::cerr << "[EXP058-IPUT] iput-object actionBarLayout"
                  << " src_reg=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj_reg=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " pc=" << pc
                  << " field_class=" << field_res.class_descriptor
                  << std::endl;
    }

    // EXP-060: Debug — log iput-object for parentLayout field.
    if (field_res.resolved && field_res.field_name == "parentLayout") {
        std::cerr << "[EXP060-IPUT] iput-object parentLayout"
                  << " src_reg=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj_reg=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " pc=" << pc
                  << " field_class=" << field_res.class_descriptor
                  << std::endl;
    }

    // EXP-062: Debug — log ALL iput-object in PhoneView.<init>
    if (field_res.resolved &&
        current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        std::cerr << "[EXP062-IPUT] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " src=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " obj_class=" << obj_ref.class_desc
                  << " stored=" << (obj_ref.type == DalvikType::OBJECT_REF && heap_.has_object(obj_ref.object_id) ? "YES" : "NO")
                  << std::endl;
    }

    // S24 frontier probe (env-gated, bounded): Navigator.state injection —
    // the single DEX writer is navigation/compose/p.a (iput l.a). If this
    // never fires (or fires on a different receiver than the one that later
    // reads getState()), the Compose NavHost chain dies with "You cannot
    // access the Navigator's state until the Navigator is attached".
    if (field_res.resolved && field_res.field_name == "a" &&
        field_res.class_descriptor == "Landroidx/navigation/l;" &&
        std::getenv("MINIANDROID_S24_TRACE") != nullptr) {
        static thread_local uint64_t s24_nav_iput = 0;
        if (s24_nav_iput < 24) {
            ++s24_nav_iput;
            std::cerr << "[S24-NAV-STATE-IPUT] pc=" << pc
                      << " recv_oid="
                      << (obj_ref.type == DalvikType::OBJECT_REF
                              ? obj_ref.object_id : 0)
                      << " recv_cls=" << obj_ref.class_desc
                      << " value_oid="
                      << (src_val.type == DalvikType::OBJECT_REF
                              ? src_val.object_id : 0)
                      << " heap_has_recv="
                      << (obj_ref.type == DalvikType::OBJECT_REF &&
                          heap_.has_object(obj_ref.object_id) ? 1 : 0)
                      << std::endl;
        }
    }

    if (field_res.resolved && obj_ref.type == DalvikType::OBJECT_REF &&
        heap_.has_object(obj_ref.object_id)) {
        // ── F-NEW-271 LAW DIAG (write-side twin, env-gated
        // MINIANDROID_FIELD_LAW_DIAG, bounded, read-only): an iput-object
        // storing a STRING_REF into a field whose declared type is not
        // Ljava/lang/String is the alien-typed store family — catch it in
        // the act with caller identity, both store keys, the receiver's
        // runtime class, and its pre-store field map.
        // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
        // std::getenv per iput-object.
        static const bool f271_law_diag_w = std::getenv("MINIANDROID_FIELD_LAW_DIAG") != nullptr;
        if (f271_law_diag_w &&
            src_val.type == DalvikType::STRING_REF &&
            (field_res.field_type != "Ljava/lang/String;" ||
             src_val.string_val.empty())) {
            static thread_local uint64_t f271_wn = 0;
            if (f271_wn < 40) {
                ++f271_wn;
                std::cerr << "[F271-WRITE] " << current_class_ << "."
                          << current_method_ << " pc=" << pc
                          << " field=" << field_res.class_descriptor << "."
                          << field_res.field_name << " : "
                          << field_res.field_type
                          << " <- STRING_REF len=" << src_val.string_val.size()
                          << " str=\"" << src_val.string_val.substr(0, 48)
                          << "\" recv#" << obj_ref.object_id
                          << " recv_reg_cls=" << obj_ref.class_desc;
                {
                    const std::string f271_wdecl = resolved_field_declarer(
                        field_res.class_descriptor, field_res.field_name);
                    std::cerr << " declarer=" << f271_wdecl
                              << " qkey="
                              << s134_dex_field_key(
                                     f271_wdecl, field_res.field_name,
                                     is_dex_defined_class(f271_wdecl));
                }
                const HeapObject* f271_who = heap_.get(obj_ref.object_id);
                if (f271_who) {
                    std::cerr << " heap_cls=" << f271_who->class_descriptor
                              << " pre-fields["
                              << f271_who->fields.size() << "]:";
                    int f271_wnf = 0;
                    for (const auto& [fk, fv] : f271_who->fields) {
                        if (f271_wnf++ >= 12) {
                            std::cerr << " ...";
                            break;
                        }
                        std::cerr << " " << fk << "=t"
                                  << static_cast<int>(fv.type) << "/o"
                                  << fv.object_id;
                        if (fv.type == DalvikType::STRING_REF)
                            std::cerr << "(\""
                                      << fv.string_val.substr(0, 24)
                                      << "\")";
                    }
                }
                std::cerr << std::endl;
            }
        }
        // S134 F-NEW-160: dual write (qualified primary + bare legacy mirror).
        // F-NEW-321 (CONT-50): the mirror write is RAW — see the execute_iput
        // site for the law (a superclass write's mirror must not re-resolve
        // onto the subclass's shadowed slot; solitaire c$b.a face).
        {
            // F-NEW-325: true-declarer keying — a framework-owned field
            // (no DEX declarer; the bare/raw mirror IS the slot) stays
            // bare even when the REF class is DEX-defined; a real DEX
            // declarer keeps the qualified slot + the raw bare mirror
            // (F-NEW-321 law unchanged).
            const std::string& s134_decl = field_memo_iputo.s134_decl;
            if (!is_dex_defined_class(s134_decl)) {
                heap_.set_object_field(obj_ref.object_id, field_res.field_name,
                                       src_val);
            } else {
                heap_.set_object_field(obj_ref.object_id,
                    s134_dex_field_key(s134_decl, field_res.field_name, true),
                    src_val);
                heap_.set_object_field_raw(obj_ref.object_id,
                                           field_res.field_name, src_val);
            }
            // CONT-44 T24 (F-NEW-567 root evidence): record the compose
            // LayoutNode owner assignment. AOSP LayoutNode.insertAt
            // propagates Owner (Lel0;.r) to every inserted node via the
            // d/h writers; the second-wave insert never executes the h
            // path (runtime: Q/M/h ZERO runs), so late nodes carry NO
            // owner and V's guard skips Lt4;.z — the measure scheduler
            // (Lzs0;.r delegate.requestMeasure) is never re-armed and the
            // nodes stay unpositioned (dooz board region zero draw ops).
            // Record the most recent owner value; the V-entry repair
            // completes the propagation with exactly the value insertAt
            // would have written.
            if (field_res.class_descriptor == "Lel0;" &&
                field_res.field_name == "r" &&
                src_val.type == DalvikType::OBJECT_REF) {
                compose_owner_last_ = src_val.object_id;
            }
        }
        if (field_trace_filter_set() &&
            field_trace_active(field_res.field_name.c_str(),
                               (current_class_ + "." + current_method_).c_str(),
                               field_res.class_descriptor.c_str())) {
            std::cerr << "[FIELD-TRACE] put-obj " << current_class_ << "."
                      << current_method_ << " "
                      << field_res.class_descriptor << "." << field_res.field_name
                      << " obj#" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                      << " value=" << dalvik_value_to_string(src_val) << std::endl;
        }

    } else if (field_res.resolved) {
        // S72 silent-lost-write probe (env-gated, bounded): the iput fell
        // into the legacy drop path — the write VANISHES and the field
        // later reads back as null-with-empty-desc. This is the write-side
        // twin of the [NULLFIELD] read probe (dooz trie-node evidence).
        {
            static thread_local const char* nf_filter =
                std::getenv("MINIANDROID_NULLFIELD_TRACE");
            static thread_local uint64_t nd_n = 0;
            if (nf_filter && nd_n < 30) {
                if (std::string(nf_filter) == "*" ||
                    field_res.field_name == nf_filter) {
                    ++nd_n;
                    std::cerr << "[IPUT-DROP] "
                              << field_res.class_descriptor << "."
                              << field_res.field_name
                              << " value_oid="
                              << (src_val.type == DalvikType::OBJECT_REF
                                      ? src_val.object_id : 0)
                              << " recv_type=" << static_cast<int>(obj_ref.type)
                              << " recv_oid=" << obj_ref.object_id
                              << " recv_desc=" << obj_ref.class_desc
                              << " heap_has="
                              << (obj_ref.type == DalvikType::OBJECT_REF &&
                                  heap_.has_object(obj_ref.object_id) ? 1 : 0)
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc
                              << std::endl;
                }
            }
        }
    }
    // EXP-042 Phase 2: never return false; just advance pc_.

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "target"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

// EXP-035: Static Field Operations

bool DalvikExecutionEngine::execute_sget(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sget vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false on field resolution failure —
    // advance pc_ by 2 and return default 0.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];

    FieldResolution field_res = resolve_field(field_idx);
    // CONT-126: FIELD-TRACE statics coverage (sget family) — the trace tool
    // previously covered ONLY instance iget/iput, so static-field decode
    // (e.g. tictactoe's Gdx.app putstatic hunt) had no visibility. Same
    // env gate + qualified "Lcls;.field" filter semantics as the instance
    // paths. Read-only diagnostics: zero semantic change by construction.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] get-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << std::endl;
    }
    // CONT-38 decode diag (env-gated, bounded): UNRESOLVED static-field
    // reads answer 0 silently — the theme-defaults zero face.
    if (!field_res.resolved) {
        static thread_local const bool ufs_on =
            std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr;
        static thread_local uint64_t ufs_n = 0;
        if (ufs_on && ufs_n++ < 40)
            std::cerr << "[SGET-UNRESOLVED] field_idx=" << field_idx
                      << " caller=" << current_class_ << "."
                      << current_method_ << " pc=" << pc << std::endl;
    }

    // EXP-053: Ensure the class is initialized before reading its static field.
    // F-NEW-215: active use (sget) of an ERRONEOUS class raises
    // NoClassDefFoundError instead of silently reading a missing static.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sget_n{0};
            if (f215_sget_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sget class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }

    DalvikValue result_value;
    result_value.type = DalvikType::INT32;
    result_value.int_val = 0;

    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        auto it = static_field_storage_.find(static_key);
        // R-NEW-561 (TRAIN 8): declarer-chain retry (same law as the
        // sget-object path above) — inherited statics resolve to the
        // declarer; the requesting-class key may miss while the write
        // landed under a declarer identity. On hit: answer + alias.
        if (it == static_field_storage_.end()) {
            std::string walk_cls = field_res.class_descriptor;
            for (int r561_hop = 0; r561_hop < 32; ++r561_hop) {
                auto sit = class_to_superclass_.find(walk_cls);
                if (sit == class_to_superclass_.end() || sit->second.empty())
                    break;
                walk_cls = sit->second;
                auto dit = static_field_storage_.find(
                    walk_cls + "." + field_res.field_name);
                if (dit != static_field_storage_.end()) {
                    static_field_storage_[static_key] = dit->second;
                    it = static_field_storage_.find(static_key);
                    break;
                }
            }
        }
        // CONT-38 decode diag (env-gated, bounded): the sget-WIDE color
        // statics — the actual path the painter takeOrElse chain reads.
        // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
        // std::getenv per sget-wide.
        static thread_local const bool c38w_on =
            std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr;
        if (c38w_on &&
            (field_res.class_descriptor == "Lzh;" ||
             field_res.class_descriptor == "Lai;" ||
             field_res.class_descriptor == "Lts0;" ||
             field_res.class_descriptor == "Lci;")) {
            static thread_local uint64_t c38s_n = 0;
            if (c38s_n++ < 8000)
                {
                    auto vit = static_field_storage_.find(static_key);
                    long long vhex = (vit != static_field_storage_.end() &&
                                      vit->second.type == DalvikType::INT64)
                                         ? vit->second.long_val : -1;
                    std::cerr << "[COLOR-SGET-W] " << static_key
                              << " hit=" << (vit != static_field_storage_.end())
                              << " val=0x" << std::hex << vhex << std::dec
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                }
        }
        if (it != static_field_storage_.end()) {
            result_value = it->second;
        } else if (field_res.class_descriptor ==
                       "Landroid/view/View$MeasureSpec;" &&
                   (field_res.field_name == "EXACTLY" ||
                    field_res.field_name == "AT_MOST" ||
                    field_res.field_name == "UNSPECIFIED")) {
            // R500 (ROOT-VIEW-FRAME family): AOSP View$MeasureSpec mode
            // constants (EXACTLY = 0x40000000, AT_MOST = 0x80000000,
            // UNSPECIFIED = 0) are JVM-stable compile-time ints consumed
            // by every programmatic measure chain. The int sget path has
            // no constant synthesis — seed them BEFORE the typed-default
            // law answers 0 (probe evidence: makeMeasureSpec(200, EXACTLY)
            // returned the mode-less 0xc8 → default onMeasure -> 0x0).
            if (field_res.field_name == "EXACTLY") {
                result_value = DalvikValue::make_int(0x40000000);
            } else if (field_res.field_name == "AT_MOST") {
                result_value = DalvikValue::make_int((int32_t)0x80000000u);
            } else {
                result_value = DalvikValue::make_int(0);
            }
            static_field_storage_[static_key] = result_value;
        } else {
            static_field_storage_[static_key] = result_value;
        }
    }

    // ── F-062: capture the APK's compose_view_saveable_id_tag key ──────
    // Name-based capture (no hardcoded resource id): the androidx
    // saved-state migration reads this key on EVERY ancestor hop; the
    // ViewShadow decor-anchor law (getTag) needs the same int to answer
    // the terminating String at the window root. Evidence: dooz live run
    // walk 477→102→8→101 dead-ended at the unanchored root and the
    // `parent as View` unwrap NPE'd mid-composition (0-pixel first frame).
    if (field_res.resolved &&
        field_res.field_name == "compose_view_saveable_id_tag" &&
        result_value.type == DalvikType::INT32 && result_value.int_val != 0) {
        framework::ViewShadow::record_compose_saveable_id_key(
            result_value.int_val);
    }

    // EXP-053: Trace every sget (for resource ID investigation).
    // Throttled to first 100 to avoid log explosion.
    // EXP-063: Also trace R$string and R$drawable specifically.
    if (field_res.resolved) {
        static thread_local uint64_t sget_log_count = 0;
        static thread_local std::string last_method = "";
        static thread_local uint64_t method_sget_count = 0;
        if (current_method_ != last_method) {
            last_method = current_method_;
            method_sget_count = 0;
        }
        bool should_log = (sget_log_count < 100 && method_sget_count < 5);
        // EXP-063: Always log R$ fields
        bool is_r_field = (field_res.class_descriptor.find("R$") != std::string::npos);
        should_log = should_log || is_r_field;
        if (should_log) {
            sget_log_count++;
            method_sget_count++;
            std::cerr << "[SGET] class=" << current_class_
                      << " method=" << current_method_
                      << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " value=" << result_value.int_val
                      << std::endl;
        }
    }

    set_register(dest_reg, result_value);
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sget_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sget-object vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];

    uint64_t f107_sr0 = 0; phase_clock().enter(phase_clock().sget_resolve_ph, f107_sr0);
    FieldResolution field_res = resolve_field(field_idx);
    phase_clock().exit(phase_clock().sget_resolve_ph, f107_sr0);
    uint64_t f107_si0 = 0; phase_clock().enter(phase_clock().sget_init_ph, f107_si0);

    // CONT-126: FIELD-TRACE statics coverage (sget-object family) — same
    // law and same env gate as the sget hook; read-only diagnostics.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] get-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << std::endl;
    }

    // EXP-053: Ensure the class is initialized before reading its static field.
    // F-NEW-215: active use (sget-object family) of an ERRONEOUS class
    // raises NoClassDefFoundError instead of answering null.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sgeto_n{0};
            if (f215_sgeto_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sget-object class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }

    phase_clock().exit(phase_clock().sget_init_ph, f107_si0);
    uint64_t f107_st0 = 0; phase_clock().enter(phase_clock().sget_tail_ph, f107_st0);
    struct F107TailGuard { PhaseClock::Phase& ph; uint64_t t0; ~F107TailGuard(){ phase_clock().exit(ph, t0);} } f107_tailguard{phase_clock().sget_tail_ph, f107_st0};
    DalvikValue result_value;
    result_value.type = DalvikType::NULL_REF;
    result_value.object_id = 0;

    // S24 probe (env-gated, bounded): the Kotlin EmptyList singleton
    // (z1/t.i) feeds NavController.navigate's List param; a null answer
    // nulls z1/r.D's receiver and NPEs addAll ("parameter elements").
    if (field_res.resolved &&
        field_res.class_descriptor == "Lz1/t;" &&
        field_res.field_name == "i" &&
        std::getenv("MINIANDROID_S24_TRACE") != nullptr) {
        static thread_local uint64_t s24_emptylist = 0;
        if (s24_emptylist < 12) {
            ++s24_emptylist;
            auto probe = static_field_storage_.find("Lz1/t;.i");
            std::cerr << "[S24-EMPTYLIST] sget-object z1/t.i pc=" << pc
                      << " storage_hit=" << (probe != static_field_storage_.end())
                      << " oid="
                      << (probe != static_field_storage_.end()
                              ? probe->second.object_id : 0)
                      << " type="
                      << (probe != static_field_storage_.end()
                              ? static_cast<int>(probe->second.type) : -1)
                      << std::endl;
        }
    }

    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        auto it = static_field_storage_.find(static_key);
        // ── TRAIN-68 (T68-START): the CoroutineStart (Lyr;) enum static
        // reads — the node's lazy launch branches on the start constant;
        // log every Lyr; sget-object with field + loaded object id so the
        // inline-vs-deferred divergence per node becomes evidence.
        if (field_res.class_descriptor == "Lyr;" && touch_dispatch_active_) {
            static const bool t68s_on = diag_env("MINIANDROID_T68_NODE_TRACE");
            if (t68s_on) {
                static thread_local uint64_t t68s_n = 0;
                if (t68s_n++ < 80)
                    std::cerr << "[T68-START] sget Lyr;."
                              << field_res.field_name
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc
                              << " storage_hit="
                              << (it != static_field_storage_.end() ? 1 : 0)
                              << " oid="
                              << (it != static_field_storage_.end()
                                      ? it->second.object_id : 0)
                              << std::endl;
            }
        }
        // R-NEW-561 (CONT-42 TRAIN 8): JVM static-field resolution law —
        // the static lives on its DECLARER (JVM sget resolution walks the
        // superclass chain). [SGET-MISS] evidence (this wave): the read key
        // (a requesting/alias class identity, e.g. telegram's Ljr;.b0)
        // missed while the write had landed under a DIFFERENT identity of
        // the SAME logical static (the declarer class, e.g.
        // Lcom/google/firebase/messaging/f;.b0). Walk the superclass chain
        // (bounded 32) and answer the first ancestor key that holds the
        // field; alias the requesting key so identity (==) holds from here
        // on. No ancestor hit = the ladder below answers as before.
        if (it == static_field_storage_.end()) {
            std::string walk_cls = field_res.class_descriptor;
            for (int r561_hop = 0; r561_hop < 32; ++r561_hop) {
                auto sit = class_to_superclass_.find(walk_cls);
                if (sit == class_to_superclass_.end() || sit->second.empty())
                    break;
                walk_cls = sit->second;
                auto dit = static_field_storage_.find(
                    walk_cls + "." + field_res.field_name);
                if (dit != static_field_storage_.end()) {
                    static_field_storage_[static_key] = dit->second;
                    it = static_field_storage_.find(static_key);
                    static thread_local uint64_t r561_hits = 0;
                    if (r561_hits++ < 12)
                        std::cerr << "[R561-DECLARER] sget-object "
                                  << static_key << " <- " << walk_cls << "."
                                  << field_res.field_name << std::endl;
                    break;
                }
            }
        }
        // CONT-38 decode diag (env-gated, bounded): the theme-defaults
        // color statics — who reads them and what the storage answers.
        // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
        // std::getenv per sget.
        static thread_local const bool c38_on =
            std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr;
        if (c38_on &&
            (field_res.class_descriptor == "Lzh;" ||
             field_res.class_descriptor == "Lai;" ||
             field_res.class_descriptor == "Lts0;")) {
            static thread_local uint64_t c38_n = 0;
            if (c38_n++ < 300)
                std::cerr << "[COLOR-SGET] " << static_key
                          << " hit=" << (it != static_field_storage_.end())
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
        if (it != static_field_storage_.end()) {
            result_value = it->second;
        } else {
            // CYCLE-E: framework enum constant synthesis. android.* classes
            // are not defined in app DEX files, so their enum <clinit> never
            // runs and every sget-object of e.g. Paint$Style.STROKE produced
            // NULL — Paint.setStyle / Path.setFillType / PorterDuff modes
            // silently degraded for every real drawing call. Materialize the
            // constant as a real object carrying its AOSP ordinal, cached per
            // static_key so identity (==) comparisons hold.
            const int ordinal = framework_enum_ordinal(
                field_res.class_descriptor, field_res.field_name);
            if (field_res.class_descriptor ==
                           "Landroid/content/Context;" &&
                       field_res.field_name.size() > 8 &&
                       field_res.field_name.rfind("_SERVICE") ==
                           field_res.field_name.size() - 8) {
                // ── F-NEW-639 (S235-1, #588 Wave-5 lane): AOSP Context
                // .*_SERVICE string-constant law — the lane's F-NEW-637 face
                // (conversations POWER_SERVICE → silent null service): the
                // engine had NO framework static STRING table, so every
                // Context.POWER_SERVICE / TELEPHONY_SERVICE sget-object
                // answered null → getSystemService(null) → null manager →
                // the app dies at the cast/NPE boundary. AOSP Context.java:
                // every service constant is a public static final String
                // whose VALUE is the service-registry key ("power",
                // "phone", ...). Served from the table below (the AOSP
                // Context.java string truth), cached per static_key like
                // the Locale law.
                static const miniandroid::dalvik::KvPair t_ctx_services[] = {
                    {"POWER_SERVICE", "power"},
                    {"WINDOW_SERVICE", "window"},
                    {"LAYOUT_INFLATER_SERVICE", "layout_inflater"},
                    {"ACTIVITY_SERVICE", "activity"},
                    {"INPUT_METHOD_SERVICE", "input_method"},
                    {"ALARM_SERVICE", "alarm"},
                    {"KEYGUARD_SERVICE", "keyguard"},
                    {"LOCATION_SERVICE", "location"},
                    {"SEARCH_SERVICE", "search"},
                    {"NOTIFICATION_SERVICE", "notification"},
                    {"ACCESSIBILITY_SERVICE", "accessibility"},
                    {"DEVICE_POLICY_SERVICE", "device_policy"},
                    {"UI_MODE_SERVICE", "uimode"},
                    {"DOWNLOAD_SERVICE", "download"},
                    {"STORAGE_SERVICE", "storage"},
                    {"AUDIO_SERVICE", "audio"},
                    {"VIBRATOR_SERVICE", "vibrator"},
                    {"CONNECTIVITY_SERVICE", "connectivity"},
                    {"WIFI_SERVICE", "wifi"},
                    {"BATTERY_SERVICE", "battery"},
                    {"CLIPBOARD_SERVICE", "clipboard"},
                    {"INPUT_SERVICE", "input"},
                    {"DISPLAY_SERVICE", "display"},
                    {"SENSOR_SERVICE", "sensor"},
                    {"BLUETOOTH_SERVICE", "bluetooth"},
                    {"NSD_SERVICE", "nsd"},
                    {"MEDIA_ROUTER_SERVICE", "media_router"},
                    {"TELEPHONY_SERVICE", "phone"},
                    {"TELEPHONY_SUBSCRIPTION_SERVICE", "isub"},
                    {"CARRIER_CONFIG_SERVICE", "carrier_config"},
                    {"TELECOM_SERVICE", "telecom"},
                    {"APPWIDGET_SERVICE", "appwidget"},
                    {"WALLPAPER_SERVICE", "wallpaper"},
                    {"RESTRICTIONS_SERVICE", "restrictions"},
                    {"PRINT_SERVICE", "print"},
                    {"ACCOUNT_SERVICE", "account"},
                    {"JOB_SCHEDULER_SERVICE", "jobscheduler"},
                    {"MEDIA_SESSION_SERVICE", "media_session"},
                    {"DROPBOX_SERVICE", "dropbox"},
                    {"NETWORK_STATS_SERVICE", "networkstats"},
                    {"USB_SERVICE", "usb"},
                    {"VIBRATOR_MANAGER_SERVICE", "vibrator_manager"},
                    {"APP_OPS_SERVICE", "appops"},
                    {"CAMERA_SERVICE", "camera"},
                    {"USER_SERVICE", "user"},
                };
                if (const char* svc = kv_table_find(
                        t_ctx_services,
                        sizeof(t_ctx_services) /
                            sizeof(t_ctx_services[0]),
                        field_res.field_name)) {
                    result_value = DalvikValue::make_string(svc, pc);
                    static_field_storage_[static_key] = result_value;
                    static thread_local uint64_t f639_const_n = 0;
                    if (f639_const_n++ < 8)
                        std::cerr << "[F-NEW-639] Context."
                                  << field_res.field_name << " -> \"" << svc
                                  << "\" caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                } else {
                    static_field_storage_[static_key] = result_value;
                }
            } else if (ordinal >= 0) {
                uint32_t enum_id = heap_.allocate(field_res.class_descriptor, pc, 0);
                heap_.set_object_field(enum_id, "ordinal",
                                       DalvikValue::make_int(ordinal));
                heap_.set_object_field(enum_id, "enum_name",
                                       DalvikValue::make_string(field_res.field_name, 0));
                result_value = DalvikValue::make_object(enum_id,
                                                        field_res.class_descriptor);
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Lkotlin/Unit;" &&
                       field_res.field_name == "INSTANCE") {
                // ── A-R6 R30 — KOTLIN UNIT OBJECT-DECLARATION LAW ──────
                // (roadmap §8 F1, the kotlin_family_probe census at
                // 1a0fa259: the unresolved-static world answered NULL for
                // Lkotlin/Unit;.INSTANCE — every Unit-typed expression in
                // a host-boundary report read null, and the null identity
                // propagated through static stores). Kotlin law
                // (Tier 1, kotlin/Unit): an object declaration holds
                // exactly ONE instance per runtime, loaded from the static
                // INSTANCE field. get_or_create_singleton mints it once
                // per engine — identity (===) across reads and
                // static-field roundtrips holds by construction, and the
                // a1/a2 probe rows are the executable proof.
                result_value = get_or_create_singleton("Lkotlin/Unit;");
                static_field_storage_[static_key] = result_value;
                static thread_local uint64_t r30_unit_n{0};
                if (r30_unit_n++ < 8)
                    std::cerr << "[R30-UNIT] sget-object Lkotlin/Unit;.INSTANCE -> o"
                              << result_value.object_id << " caller="
                              << current_class_ << "." << current_method_
                              << std::endl;
            } else if (field_res.class_descriptor == "Ljava/lang/Boolean;" &&
                       (field_res.field_name == "TRUE" ||
                        field_res.field_name == "FALSE")) {
                // F-050d: java.lang.Boolean static constant synthesis.
                // OpenJDK law (Boolean.java): public static final Boolean
                // TRUE = new Boolean(true); FALSE = new Boolean(false); —
                // and R8 rewrites Boolean.valueOf(true) INTO the sget of
                // TRUE. Live evidence (dooz v18): the Recomposer's channel
                // iterator resumed hasNext() with a boxed Boolean; the
                // resume path hit sget-object Boolean.TRUE, got NULL, the
                // unboxed result read false, the consume loop exited as if
                // the channel was exhausted, and cancelConsumed cancelled
                // the Recomposer's awaitWork channel mid-run — the frame
                // await never resumed (CancellationException "Channel was
                // cancelled"). Cached per static_key so identity (===)
                // comparisons against the canonical singleton hold.
                const bool bool_val = (field_res.field_name == "TRUE");
                uint32_t box_id = heap_.allocate("Ljava/lang/Boolean;", pc, 0);
                heap_.set_object_field(box_id, "value",
                                       DalvikValue::make_bool(bool_val));
                result_value = DalvikValue::make_object(box_id,
                                                        "Ljava/lang/Boolean;");
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/lang/System;" &&
                       (field_res.field_name == "out" ||
                        field_res.field_name == "err")) {
                // F-NEW-245 (CONT-5): java.lang.System.out / System.err —
                // NEVER NULL. OpenJDK System.java: out/err are final
                // PrintStreams over FileDescriptor.out/err, initialized in
                // System.<clinit> before any app code runs. Pre-fix: no
                // static synthesis → sget-object answered NULL → the very
                // first System.out.println NPE'd ("PrintStream.println on
                // a null object reference") and killed the app at APP
                // BOUNDARY (raumballer JGEngine.initActivity pc=81, x3
                // deterministic; fan-out: every library/game that logs
                // via System.out). Cached per static_key so identity
                // (System.out == System.out) holds; __fd__ = 1|2 routes
                // println/print/write/flush to real stdout/stderr
                // (the PrintStream bridge law near the PrintWriter law).
                uint32_t ps_id = heap_.allocate("Ljava/io/PrintStream;", pc, 0);
                heap_.set_object_field(
                    ps_id, "__fd__",
                    DalvikValue::make_int(field_res.field_name == "out" ? 1
                                                                        : 2));
                result_value = DalvikValue::make_object(
                    ps_id, "Ljava/io/PrintStream;");
                static_field_storage_[static_key] = result_value;
            } else if (const int static_int_val = framework_static_int(
                           field_res.class_descriptor, field_res.field_name);
                       static_int_val >= 0) {
                // F-110e (S62+): framework static INT constant synthesis.
                // Cached per static_key like the enum law above so identity
                // semantics hold for later sgets of the same constant.
                result_value = DalvikValue::make_int(static_int_val);
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/util/Locale;") {
                // M3 F-ROOM-CHAIN: java.util.Locale constant synthesis.
                // microtimer v8 Room init reads Locale.US inside the R8-inlined
                // Kotlin Intrinsics path (Le/o;.<init> — "(this as
                // java.lang.String).toLowerCase(locale)" expression check); a
                // NULL Locale.US produced "US must not be null" NPEs that the
                // uncaught-tail compatibility policy swallowed, breaking the
                // Room open chain. AOSP law: Locale.* constants are non-null
                // static objects; materialize them (cached per static_key so
                // identity comparisons hold) with __locale_tag__ carrying the
                // AOSP tag for String-case/Locale-sensitive bridges.
                static const miniandroid::dalvik::KvPair t_kLocaleConsts[] = {
    {"CANADA", "en_CA"},
    {"CANADA_FRENCH", "fr_CA"},
    {"CHINA", "zh_CN"},
    {"CHINESE", "zh"},
    {"ENGLISH", "en"},
    {"FRANCE", "fr_FR"},
    {"FRENCH", "fr"},
    {"GERMAN", "de"},
    {"GERMANY", "de_DE"},
    {"ITALIAN", "it"},
    {"ITALY", "it_IT"},
    {"JAPAN", "ja_JP"},
    {"JAPANESE", "ja"},
    {"KOREA", "ko_KR"},
    {"KOREAN", "ko"},
    {"PRC", "zh_CN"},
    {"SIMPLIFIED_CHINESE", "zh_CN"},
    {"TAIWAN", "zh_TW"},
    {"TRADITIONAL_CHINESE", "zh_TW"},
    {"UK", "en_GB"},
    {"US", "en_US"},
};
                const char* lv = kv_table_find(t_kLocaleConsts,
                        sizeof(t_kLocaleConsts) / sizeof(t_kLocaleConsts[0]),
                        field_res.field_name);
                if (lv) {
                    uint32_t loc_id = heap_.allocate("Ljava/util/Locale;", pc, 0);
                    heap_.set_object_field(loc_id, "__locale_tag__",
                                           DalvikValue::make_string(lv, 0));
                    heap_.set_object_field(loc_id, "__locale_name__",
                                           DalvikValue::make_string(field_res.field_name, 0));
                    result_value = DalvikValue::make_object(loc_id,
                                                            "Ljava/util/Locale;");
                    static_field_storage_[static_key] = result_value;
                    std::cerr << "[LOCALE-CONST] synthesized Locale."
                              << field_res.field_name << " tag=\"" << lv
                              << "\" oid=" << loc_id << std::endl;
                } else {
                    static_field_storage_[static_key] = result_value;
                }
            } else if (field_res.class_descriptor ==
                           "Ljava/nio/ByteOrder;" &&
                       (field_res.field_name == "LITTLE_ENDIAN" ||
                        field_res.field_name == "BIG_ENDIAN")) {
                // F-NEW-393 (CONT-86): AOSP ByteOrder law — LITTLE_ENDIAN /
                // BIG_ENDIAN are non-null singletons (OpenJDK ByteOrder.java);
                // org.andstatus.game2048's Lb8;.<init> reads both to build
                // its endian views. Materialize with ordinal 0/1 (cached per
                // static_key; nativeOrder() answers the LITTLE_ENDIAN one on
                // this aarch64 device model).
                const int bo_ord =
                    field_res.field_name == "LITTLE_ENDIAN" ? 0 : 1;
                uint32_t bo_id = heap_.allocate("Ljava/nio/ByteOrder;", pc, 0);
                heap_.set_object_field(bo_id, "ordinal",
                                       DalvikValue::make_int(bo_ord));
                heap_.set_object_field(bo_id, "__byteorder_name__",
                                       DalvikValue::make_string(
                                           field_res.field_name, 0));
                result_value = DalvikValue::make_object(
                    bo_id, "Ljava/nio/ByteOrder;");
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Landroid/os/Environment;" &&
                       (field_res.field_name == "MEDIA_MOUNTED" ||
                        field_res.field_name == "MEDIA_MOUNTED_READ_ONLY" ||
                        field_res.field_name == "MEDIA_REMOVED" ||
                        field_res.field_name == "MEDIA_UNMOUNTED" ||
                        field_res.field_name == "MEDIA_BAD_REMOVAL" ||
                        field_res.field_name == "MEDIA_CHECKING" ||
                        field_res.field_name == "MEDIA_NOFS" ||
                        field_res.field_name == "MEDIA_SHARED" ||
                        field_res.field_name == "MEDIA_UNKNOWN" ||
                        field_res.field_name == "MEDIA_EJECTING")) {
                // F-NEW-223 (user campaign §H): Environment storage-state
                // String constants. AOSP Environment.java — apps gate their
                // storage paths on `state.equals(Environment.MEDIA_MOUNTED)`;
                // with no seed the sget answered null and String.equals(null)
                // returned false → the app concluded "no external storage" →
                // onCreate died. Values are the AOSP constant strings.
                const char* s223 =
                    field_res.field_name == "MEDIA_MOUNTED"            ? "mounted"
                    : field_res.field_name == "MEDIA_MOUNTED_READ_ONLY" ? "mounted_ro"
                    : field_res.field_name == "MEDIA_REMOVED"           ? "removed"
                    : field_res.field_name == "MEDIA_UNMOUNTED"         ? "unmounted"
                    : field_res.field_name == "MEDIA_BAD_REMOVAL"       ? "bad_removal"
                    : field_res.field_name == "MEDIA_CHECKING"          ? "checking"
                    : field_res.field_name == "MEDIA_NOFS"              ? "nofs"
                    : field_res.field_name == "MEDIA_SHARED"            ? "shared"
                    : field_res.field_name == "MEDIA_EJECTING"          ? "ejecting"
                                                                        : "unknown";
                result_value = DalvikValue::make_string(s223, 0);
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/util/Collections;" &&
                       (field_res.field_name == "EMPTY_SET" ||
                        field_res.field_name == "EMPTY_LIST" ||
                        field_res.field_name == "EMPTY_MAP")) {
                // R-NEW-397 (S78, F-154): java.util.Collections empty-singleton
                // static-final law. OpenJDK Collections.java:
                //   public static final Set  EMPTY_SET  = new EmptySet<>();
                //   public static final List EMPTY_LIST = new EmptyList<>();
                //   public static final Map  EMPTY_MAP  = new EmptyMap<>();
                // JVM-injected-at-clinit constants — never null. Evidence:
                // dooz DataStore first-launch parse — Ljs0;.entrySet (REAL dex
                // bytecode) sgets Collections.EMPTY_SET; with no seed the
                // sget answered typed-zero NULL → Set.iterator() NPE at
                // Lh3;.h pc=36 → uncaught past all app frames (run/
                // s78_f152_postfix2). Materialized as heap-backed EMPTY
                // singletons ("__array_length__"=0) so the F-036 iterator
                // machinery + the R-NEW-397 Empty-family dispatch below
                // answer every read. Cached per static_key — identity holds.
                const char* empty_cls = nullptr;
                if (field_res.field_name == "EMPTY_SET")
                    empty_cls = "Ljava/util/Collections$EmptySet;";
                else if (field_res.field_name == "EMPTY_LIST")
                    empty_cls = "Ljava/util/Collections$EmptyList;";
                else
                    empty_cls = "Ljava/util/Collections$EmptyMap;";
                uint32_t e_id = heap_.allocate(empty_cls, pc, 0);
                heap_.set_object_field(e_id, "__array_length__",
                                       DalvikValue::make_int(0));
                heap_.set_object_field(e_id, "__iterator_pos__",
                                       DalvikValue::make_int(0));
                result_value = DalvikValue::make_object(e_id, empty_cls);
                static_field_storage_[static_key] = result_value;
                std::cerr << "[R-NEW-397] synthesized Collections."
                          << field_res.field_name << " obj#" << e_id
                          << std::endl;
            } else if (field_res.class_descriptor ==
                           "Landroid/graphics/Typeface;" &&
                       (field_res.field_name == "DEFAULT" ||
                        field_res.field_name == "DEFAULT_BOLD" ||
                        field_res.field_name == "SANS_SERIF" ||
                        field_res.field_name == "SERIF" ||
                        field_res.field_name == "MONOSPACE")) {
                // F-NEW-294 (CONT-35): AOSP Typeface static-constant law.
                // frameworks/base/graphics/java/android/graphics/Typeface.java
                // declares the family constants as static finals built by
                // create() inside <clinit>:
                //   DEFAULT       = create((String) null, NORMAL)
                //   DEFAULT_BOLD  = create((String) null, BOLD)
                //   SANS_SERIF    = create("sans-serif", NORMAL)
                //   SERIF         = create("serif", NORMAL)
                //   MONOSPACE     = create("monospace", NORMAL)
                // A live ART <clinit> ALWAYS completes — the constants are
                // NEVER null (same platform-constant law family as the
                // Boolean/Locale/StandardCharsets arms above). The engine
                // runs no framework <clinit> for the platform class, so the
                // sget hit [SGET-MISS] and answered NULL; the R8-inlined
                // Compose font resolver (FontListFontFamilyTypefaceAdapter
                // .resolve → TypefaceResult(value, immediate)) then handed
                // the null value to the consumer's Kotlin platform-type
                // `!!` check — compiled as invoke-virtual getClass() BEFORE
                // the check-cast — and composeStopwatch's
                // AndroidParagraphIntrinsics (Lk6;.<init> pc=409) NPE'd
                // once per run ("getClass on a null object reference"),
                // aborting the text pass and leaving the Compose stopwatch
                // view (Lh4;) at onDraw ops=0. Materialize each constant as
                // a REAL heap Typeface object carrying its family/style
                // (__typeface_family__/__typeface_style__), cached per
                // static_key so identity comparisons hold — the same shape
                // the bridge_to_api create/defaultFromStyle law answers.
                const char* fam = "sans-serif";
                int st = 0;
                if (field_res.field_name == "DEFAULT_BOLD") {
                    fam = "sans-serif"; st = 1;
                } else if (field_res.field_name == "SANS_SERIF") {
                    fam = "sans-serif"; st = 0;
                } else if (field_res.field_name == "SERIF") {
                    fam = "serif"; st = 0;
                } else if (field_res.field_name == "MONOSPACE") {
                    fam = "monospace"; st = 0;
                } else {
                    fam = "sans-serif"; st = 0;   // DEFAULT
                }
                uint32_t tf_id = heap_.allocate("Landroid/graphics/Typeface;",
                                                pc, 0);
                heap_.set_object_field(tf_id, "__typeface_family__",
                                       DalvikValue::make_string(fam, 0));
                heap_.set_object_field(tf_id, "__typeface_style__",
                                       DalvikValue::make_int(st));
                result_value = DalvikValue::make_object(
                    tf_id, "Landroid/graphics/Typeface;");
                static_field_storage_[static_key] = result_value;
                std::cerr << "[F-NEW-294] synthesized Typeface."
                          << field_res.field_name << " family=" << fam
                          << " style=" << st << " oid=" << tf_id
                          << std::endl;
            } else if (field_res.class_descriptor ==
                           "Landroid/view/View$MeasureSpec;" &&
                       (field_res.field_name == "EXACTLY" ||
                        field_res.field_name == "AT_MOST" ||
                        field_res.field_name == "UNSPECIFIED")) {
                // R500 (ROOT-VIEW-FRAME family): AOSP View.java MeasureSpec
                // mode constants are JVM-stable compile-time ints —
                //   UNSPECIFIED = 0, EXACTLY = 1 << 30 (0x40000000),
                //   AT_MOST = 2 << 30 (0x80000000)
                // — and the DEX measure chains (F-096b in-place getMode
                // law) compare them DIRECTLY. With no seed the sget
                // answered typed-default 0 for EXACTLY/AT_MOST, so every
                // programmatic makeMeasureSpec(size, EXACTLY) produced a
                // mode-less spec (probe evidence: makeMeasureSpec(200,
                // EXACTLY) -> 0xc8; default onMeasure then answered 0x0).
                if (field_res.field_name == "EXACTLY") {
                    result_value = DalvikValue::make_int(0x40000000);
                } else if (field_res.field_name == "AT_MOST") {
                    result_value = DalvikValue::make_int((int32_t)0x80000000u);
                } else {
                    result_value = DalvikValue::make_int(0);
                }
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/io/File;" &&
                       (field_res.field_name == "separator" ||
                        field_res.field_name == "separatorChar" ||
                        field_res.field_name == "pathSeparator" ||
                        field_res.field_name == "pathSeparatorChar")) {
                // F-079 (R-NEW-305): java.io.File path-separator constant law.
                // OpenJDK/AOSP (ojluni File.java): the four static constants
                // are initialized from the platform FileSystem:
                //   separator      = fs.getSeparator()    → "/" on Linux/Android
                //   separatorChar  = separator.charAt(0)  → '/'
                //   pathSeparator  = fs.getPathSeparator() → ":" on Linux/Android
                //   pathSeparatorChar = pathSeparator.charAt(0) → ':'
                // They are compile-time-stable platform constants — never
                // null. Live evidence (dooz v18, post F-078): the Kotlin
                // stdlib FilePathString companion (<clinit> Lg2/m;) reads
                // File.separator via sget-object; with no seed the SGET
                // returned null and the companion's Intrinsics null-check
                // threw NPE "separator must not be null" DURING <clinit> —
                // the failing class-init killed the Recomposer's first
                // composition at the F/A0.a unwind.
                // Cached per static_key (same policy as Locale/Boolean).
                if (field_res.field_name == "separator") {
                    result_value = DalvikValue::make_string("/", 0);
                } else if (field_res.field_name == "pathSeparator") {
                    result_value = DalvikValue::make_string(":", 0);
                } else if (field_res.field_name == "separatorChar") {
                    result_value = DalvikValue::make_char('/');
                } else {
                    result_value = DalvikValue::make_char(':');
                }
                static_field_storage_[static_key] = result_value;
            } else if (
                // S123-CLINIT-MAT: shared-geometry static materialization
                // after a FAILED <clinit>. AOSP law: a class's <clinit> runs
                // before any static read; inline-initialized statics like
                // `public static final RectF rectTmp = new RectF()` are
                // therefore NEVER null at first use. If the class's clinit
                // aborted partway (unmodeled API mid-<clinit>), every static
                // declared AFTER the abort point reads back null and the app
                // draw code NPEs on the first geometry call (live evidence:
                // forkgram he1$d.onDraw pc=16 — sget-object
                // AndroidUtilities.rectTmp → null → RectF.set NPE ×65
                // APP-BOUNDARY unwinds; the "StartMessaging" text was already
                // measured on the login view). The class IS marked
                // initialized (attempted), so re-running clinit is not
                // possible; materialize the AOSP no-arg-ctor state (zero
                // geometry) for the shared graphics primitives, cached per
                // static_key so identity (==) holds across the app.
                field_res.field_type == "Landroid/graphics/RectF;" ||
                field_res.field_type == "Landroid/graphics/Rect;" ||
                field_res.field_type == "Landroid/graphics/Point;" ||
                field_res.field_type == "Landroid/graphics/Paint;") {
                const bool attempted =
                    initialized_classes_.find(field_res.class_descriptor) !=
                    initialized_classes_.end();
                auto null_probe = static_field_storage_.find(static_key);
                const bool stored_null =
                    null_probe != static_field_storage_.end() &&
                    null_probe->second.type == DalvikType::NULL_REF;
                // F-NEW-446 (CONT-106, fixture-first): S123 fires ONLY for a
                // genuinely FAILED <clinit> (the F-NEW-215 evidence map).
                // AOSP law: a COMPLETED clinit that leaves a static object
                // field null means the app's own lazy factory owns the first
                // assignment — sget MUST return that null faithfully so the
                // app's null-sentinel guards keep working. The old
                // `attempted || stored_null` gate materialized Paint/RectF
                // statics of HEALTHY classes, converting guarded early-return
                // paths into deep paths that read unrelated lazy singletons.
                // Live PRE evidence (run/cont105/tg_pre.log + probe
                // fixtures/cont106_clinitsentinel PRE, binary
                // afaad5bd4f56f9d3): o6.<clinit> result=OK (1736 sputs, no
                // k0/m0/u1 assignment — telegram's o6.P(Context) factory owns
                // them; single u1 writer, callers o6.R / r4.<init> /
                // CheckBoxSquare.<init>) → [S123-CLINIT-MAT] materialized
                // o6.k0/m0 on first sget → o6.k's `if-nez k0 → return-void`
                // guard (classes3.dex 0x0..0x8) fell through → iput-boolean
                // xj0.Y:Z on the never-factory u1 → uncaught NPE @o6.k pc=46.
                // Probe faces: [C106-SENTINEL] guardEscaped=true (AOSP false)
                // and [C106-INVOKE2] result=NO-EXC (AOSP NPE).
                // The original S123 evidence (forkgram he1$d →
                // AndroidUtilities.rectTmp, clinit ABORTED mid-way on an
                // unmodeled API) is exactly a failed_clinit_classes_ member —
                // preserved by this gate. POST faces: guardEscaped=false,
                // INVOKE2=NPE, failed-clinit materialization retained.
                const bool clinit_failed =
                    failed_clinit_classes_.find(field_res.class_descriptor) !=
                    failed_clinit_classes_.end();
                if (clinit_failed) {
                    uint32_t geo_id = heap_.allocate(field_res.field_type,
                                                     pc, 0);
                    // AOSP no-arg ctor state: zero geometry fields.
                    if (field_res.field_type == "Landroid/graphics/RectF;") {
                        heap_.set_object_field(geo_id, "left",
                                               DalvikValue::make_float(0.0f));
                        heap_.set_object_field(geo_id, "top",
                                               DalvikValue::make_float(0.0f));
                        heap_.set_object_field(geo_id, "right",
                                               DalvikValue::make_float(0.0f));
                        heap_.set_object_field(geo_id, "bottom",
                                               DalvikValue::make_float(0.0f));
                    } else if (field_res.field_type ==
                               "Landroid/graphics/Rect;") {
                        heap_.set_object_field(geo_id, "left",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "top",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "right",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "bottom",
                                               DalvikValue::make_int(0));
                    } else if (field_res.field_type ==
                               "Landroid/graphics/Point;") {
                        heap_.set_object_field(geo_id, "x",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "y",
                                               DalvikValue::make_int(0));
                    } else {
                        // Landroid/graphics/Paint; — AOSP default paint:
                        // FILL style, BLACK color, anti-alias off.
                        heap_.set_object_field(geo_id, "color",
                                               DalvikValue::make_int(
                                                   0xFF000000));
                    }
                    result_value = DalvikValue::make_object(
                        geo_id, field_res.field_type);
                    static_field_storage_[static_key] = result_value;
                    std::cerr << "[S123-CLINIT-MAT] materialized "
                              << field_res.class_descriptor << "."
                              << field_res.field_name
                              << " type=" << field_res.field_type
                              << " oid=" << geo_id
                              << " (clinit_failed="
                              << (clinit_failed ? "true" : "false")
                              << " attempted="
                              << (attempted ? "true" : "false")
                              << " stored_null="
                              << (stored_null ? "true" : "false") << ")"
                              << std::endl;
                } else {
                    result_value.type = DalvikType::NULL_REF;
                    result_value.object_id = 0;
                }
            } else {
                // OpenJDK Integer.java: `public static final Class<Integer>
                // TYPE = int.class;` (and the same for the other boxes) —
                // the primitive Class constants are JVM-injected, never
                // written by <clinit>. With no seed the sget-object answered
                // typed-zero NULL and Array.newInstance(Integer.TYPE, dims)
                // produced a null matrix (FishRingsForAndroid Rings.<init>
                // evidence: int[12][3] board → aput-null NPE in Rings.init).
                // Descriptor: the primitive letters (JLS/DEX spec) — mirrored
                // by the Array.newInstance primitive-component arm below.
                static const std::map<std::string, std::string>
                    k_primitive_type_desc = {
                        {"Ljava/lang/Integer;", "I"},
                        {"Ljava/lang/Boolean;", "Z"},
                        {"Ljava/lang/Byte;", "B"},
                        {"Ljava/lang/Character;", "C"},
                        {"Ljava/lang/Short;", "S"},
                        {"Ljava/lang/Long;", "J"},
                        {"Ljava/lang/Float;", "F"},
                        {"Ljava/lang/Double;", "D"},
                        {"Ljava/lang/Void;", "V"},
                    };
                auto prim = k_primitive_type_desc.find(
                    field_res.class_descriptor);
                if (prim != k_primitive_type_desc.end() &&
                    field_res.field_name == "TYPE") {
                    result_value = DalvikValue::make_class(
                        prim->second, instruction_sequence_);
                    static_field_storage_[static_key] = result_value;
                } else if (field_res.class_descriptor ==
                           "Lorg/json/JSONObject;") {
                // ── F-JSON-NULL (S226; #508 Vector-Pinball chain): the AOSP
                // JSONObject.NULL SENTINEL ────────────────────────────────
                // OpenJDK/Android org.json JSONObject: `public static final
                // Object NULL = new Object()` — the sentinel is a REAL
                // identity object (the docs' "a value equal to Java null"),
                // never Java null itself. The engine ran no framework
                // <clinit> for org.json, so the sget answered typed-zero
                // NULL — and bouncy v43's JSONUtils.objectFromJSONItem
                // (REAL bytecode, disassembled):
                //   0x0000 sget-object v0, Lorg/json/JSONObject;->NULL
                //   0x0004 if-ne v1, v0, +004h        ← != sentinel?
                //   0x0008 const/4 v1, 0             ← null the value
                //   0x000a return-object v1
                // compared every STRING_REF leaf against the null token —
                // the mixed compare saw "no object == no object" and nulled
                // EVERY leaf value before Map.put (MAPPUT val_kind=7 rows,
                // live run) → params.get("class") NPE at
                // FieldElement.createFromParameters pc=16 → onCreate APP
                // BOUNDARY unwind → no table render. Law: the sentinel is
                // minted ONCE (a heap Lorg/json/JSONObject; with
                // json_value="null" — the AOSP identity face) and cached;
                // identity comparisons against it now behave per ART.
                if (field_res.field_name == "NULL") {
                    auto nullit = static_field_storage_.find(static_key);
                    if (nullit == static_field_storage_.end() ||
                        nullit->second.type != DalvikType::OBJECT_REF ||
                        nullit->second.object_id == 0) {
                        uint32_t sid =
                            heap_.allocate("Lorg/json/JSONObject;", pc_, 0);
                        heap_.set_object_field(
                            sid, "json_value",
                            DalvikValue::make_string("null", 0));
                        result_value =
                            DalvikValue::make_object(sid,
                                                     "Lorg/json/JSONObject;");
                        static_field_storage_[static_key] = result_value;
                        static thread_local uint64_t fjsonnull_n = 0;
                        if (fjsonnull_n++ < 4)
                            std::cerr << "[F-JSON-NULL] JSONObject.NULL "
                                         "sentinel minted o"
                                      << sid
                                      << " (AOSP identity object law)"
                                      << std::endl;
                    }
                }
                } else if (field_res.class_descriptor ==
                           "Ljava/nio/charset/StandardCharsets;") {
                // FINAL-CAMPAIGN PHASE 3 (F-NEW-169 face-1):
                // java.nio.charset.StandardCharsets is a JDK platform-constant
                // holder — OpenJDK StandardCharsets.java defines the six
                // charset constants as static finals initialized in
                // <clinit>, which on a live JVM ALWAYS completes. The engine
                // runs no such <clinit> (framework class, no DEX body), so
                // the sget answered null and the first consumer (WhatsApp
                // 08D.<clinit> → Charset.name()) NPE'd → the requesting
                // clinit died leaving its statics unwritten (SGET-MISS →
                // null) → app-baked null-check NPE chain → white screen.
                // Object identity: the SAME heap Charset convention the
                // Charset.forName law uses (__charset_name__ field).
                static const std::map<std::string, std::string>
                    k_standard_charsets = {
                        {"UTF_8", "UTF-8"},
                        {"ISO_8859_1", "ISO-8859-1"},
                        {"US_ASCII", "US-ASCII"},
                        {"UTF_16", "UTF-16"},
                        {"UTF_16BE", "UTF-16BE"},
                        {"UTF_16LE", "UTF-16LE"},
                    };
                auto sc = k_standard_charsets.find(field_res.field_name);
                if (sc != k_standard_charsets.end()) {
                    uint32_t cs_id =
                        heap_.allocate("Ljava/nio/charset/Charset;", pc_, 0);
                    heap_.set_object_field(
                        cs_id, "__charset_name__",
                        DalvikValue::make_string(sc->second, 0));
                    result_value = DalvikValue::make_object(
                        cs_id, "Ljava/nio/charset/Charset;");
                    static_field_storage_[static_key] = result_value;
                }
                } else {
                // M3 FINDING-013 miss-probe: print the missing key and the
                // presence of ANY same-class keys in storage — a clinit that
                // ran but whose writes are invisible here means the two
                // paths disagree on the storage KEY (or engine instance).
                static thread_local uint64_t sget_miss_probe = 0;
                if (sget_miss_probe < 24) {
                    sget_miss_probe++;
                    size_t same_class = 0;
                    std::string sample;
                    for (const auto& [k, v] : static_field_storage_) {
                        if (k.rfind(field_res.class_descriptor + ".", 0) == 0) {
                            same_class++;
                            if (sample.empty()) sample = k;
                        }
                    }
                    std::cerr << "[SGET-MISS] key=" << static_key
                              << " storage_size=" << static_field_storage_.size()
                              << " same_class_keys=" << same_class
                              << " engine=" << (const void*)this
                              << (sample.empty() ? "" : " first=" + sample)
                              << std::endl;
                    // Where did a write with THIS field name land?
                    for (const auto& [k, v] : static_field_storage_) {
                        if (k.find("." + field_res.field_name) !=
                            std::string::npos) {
                            std::cerr << "[SGET-MISS]   landed: " << k
                                      << std::endl;
                        }
                    }
                }
                static_field_storage_[static_key] = result_value;
                }
            }
        }
    }

    // EXP-053: Trace sget-object (for singleton cache observation).
    if (field_res.resolved) {
        static thread_local uint64_t sget_obj_log_count = 0;
        if (sget_obj_log_count < 100) {
            sget_obj_log_count++;
            std::cerr << "[SGET] class=" << current_class_
                      << " method=" << current_method_
                      << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " obj_id=" << result_value.object_id
                      << std::endl;
        }
    }

    set_register(dest_reg, result_value);
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sput(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sput vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    // CONT-126: FIELD-TRACE statics coverage (sput family) — same law and
    // same env gate as the sget hook; read-only diagnostics.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] put-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << " reg=v"
                  << (int)src_reg << std::endl;
    }
    
    // F-NEW-215: sput is ACTIVE USE (JVMS 5.5) — the write must trigger
    // class initialization exactly like sget, and an ERRONEOUS class must
    // raise NoClassDefFoundError instead of silently writing a static the
    // class's own <clinit> never got to build.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sput_n{0};
            if (f215_sput_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sput class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }
    
    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        // F-NEW-657 (#588 Games-g2): the sput half of R-NEW-561 — the
        // write lands in the DECLARING class's ONE storage cell. A
        // subclass <clinit> rebind of an inherited static keyed by the
        // access-site class was invisible to the superclass query()'s
        // cell (the chess provider face); key the write at the DEX
        // declarer when the chain declares the static. Engine-synthetic
        // statics (no DEX declarer) keep the ref-class key unchanged.
        std::string f657_decl = static_field_declarer_of(
            field_res.class_descriptor, field_res.field_name);
        if (!f657_decl.empty() && f657_decl != field_res.class_descriptor) {
            static thread_local uint64_t f657_writes = 0;
            if (f657_writes++ < 8)
                std::cerr << "[F-NEW-657] sput declarer-key "
                          << field_res.class_descriptor << "."
                          << field_res.field_name << " -> " << f657_decl
                          << " (caller " << current_class_ << "."
                          << current_method_ << ")" << std::endl;
            static_key = f657_decl + "." + field_res.field_name;
        }
        static_field_storage_[static_key] = src_val;
    }
    
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sput_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sput-object vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    // CONT-126: FIELD-TRACE statics coverage (sput-object family) — same
    // law and same env gate as the sget hook; read-only diagnostics.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] put-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << " reg=v"
                  << (int)src_reg << std::endl;
    }
    
    // F-NEW-215: sput-object is ACTIVE USE — same law as sput (init
    // trigger + NoClassDefFoundError on an erroneous class).
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sputo_n{0};
            if (f215_sputo_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sput-object class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }
    
    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        // F-NEW-657: the sput-object declarer-key law — same as the
        // sput scalar half (the sUriMatcher face is an OBJECT static).
        std::string f657_decl = static_field_declarer_of(
            field_res.class_descriptor, field_res.field_name);
        if (!f657_decl.empty() && f657_decl != field_res.class_descriptor) {
            static thread_local uint64_t f657_owrites = 0;
            if (f657_owrites++ < 8)
                std::cerr << "[F-NEW-657] sput-object declarer-key "
                          << field_res.class_descriptor << "."
                          << field_res.field_name << " -> " << f657_decl
                          << " (caller " << current_class_ << "."
                          << current_method_ << ")" << std::endl;
            static_key = f657_decl + "." + field_res.field_name;
        }
        static_field_storage_[static_key] = src_val;
        // S123 DIAG (bounded): where do ContainerHelpers' static writes land?
        if (current_method_ == "<clinit>" &&
            static_key.find("ContainerHelpers") != std::string::npos) {
            std::cerr << "[S123-SPUT-CH] key=" << static_key
                      << " val_type=" << static_cast<int>(src_val.type)
                      << " obj=" << src_val.object_id
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
        }
    } else {
        // M3 FINDING-013 diag: an UNRESOLVED sput-object silently vanishes —
        // exactly the invisible-state-loss class that cost dooz its
        // Lifecycle.State enum. Cap-limited visibility, semantics unchanged.
        static thread_local uint64_t sput_miss_count = 0;
        if (sput_miss_count < 40) {
            sput_miss_count++;
            std::cerr << "[SPUT-UNRESOLVED] field_idx=" << field_idx
                      << " src_class=" << src_val.class_desc
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
    }
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }
    
    pc_ = pc + 2;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Invokes
// ============================================================================

// ────────────────────────────────────────────────────────────────────────
// F-NEW-249 (CONT-6): STABLE CLASS-TOKEN IDENTITY LAW (Object.getClass).
// ART ClassLinker mints ONE java.lang.Class instance per runtime class —
// identity is observable (==, HashSet<Class>, synchronized(Class), and
// androidx's NavigatorProvider name cache keyed by Class). The engine's
// const-class opcode already honors this via the F-069 class_token_ids_
// map; getClass stamped ref_id = instruction_sequence_, producing a
// DIFFERENT token per call site for the same class. This helper returns
// the stable per-descriptor token: first call allocates the backing heap
// object ("Ljava/lang/Class;" with __referent_desc) exactly like
// const-class, later calls reuse it. Type stays CLASS_REF with
// class_desc = the REFERRED descriptor (existing consumer contract).
// ────────────────────────────────────────────────────────────────────────
DalvikValue DalvikExecutionEngine::make_stable_class_token(
    const std::string& type_desc) {
    if (type_desc.empty())
        return DalvikValue::make_class("Ljava/lang/Class;",
                                       instruction_sequence_);
    uint32_t token = 0;
    auto tok_it = class_token_ids_.find(type_desc);
    if (tok_it != class_token_ids_.end()) {
        token = tok_it->second;
    } else {
        token = heap_.allocate("Ljava/lang/Class;", pc_, 0);
        heap_.set_object_field(token, "__referent_desc",
                               DalvikValue::make_string(type_desc, 0));
        class_token_ids_.emplace(type_desc, token);
    }
    return DalvikValue::make_class(type_desc, token);
}

} // namespace dalvik
} // namespace miniandroid
// W23-BENCH op=D run=1 t=1795118402
// W23-BENCH op=D run=2 t=1795118414
// W23-BENCH op=D run=3 t=1795118427
// W23-BENCH op=D run=1 t=1795120065
// W23-BENCH op=D run=2 t=1795120074
// W23-BENCH op=D run=3 t=1795120083
