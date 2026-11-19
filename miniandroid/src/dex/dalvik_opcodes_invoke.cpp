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
bool DalvikExecutionEngine::execute_invoke_virtual(uint32_t pc, InstructionTrace& trace,
                                                  DalvikExecutionResult& result) {
    // Format: 35c [op] {vC..}, method@BBBB
    // EXP-035: Now uses VTable dispatch for proper polymorphic method resolution
    if (pc + 2 >= bytecode_.size()) return false;

    // S24 flow probe (env-gated, bounded): trace p.a (NavHost/NavController
    // R8-merged method) instruction flow — the navigator-attach block
    // (pc ~1240-1404) never executed its state iput while the graph build
    // (pc ~2546 c.h) did; this reveals the actual pc path.
    {
        static thread_local uint64_t s24_flow = 0;
        if (diag_env("MINIANDROID_S24_TRACE") &&
            current_class_ == "Landroidx/navigation/compose/p;" &&
            s24_flow < 120) {
            ++s24_flow;
            std::cerr << "[S24-PA-FLOW] virtual pc=" << pc << std::endl;
        }
    }

    // S58 R-NEW-378 probe (env-gated, bounded): every invoke-virtual from
    // the compose SaveableStateProvider init frame — reveals the
    // ACCEPTABLE_CLASSES loop traffic (isEmpty/size/get/isInstance) and
    // where each dispatch actually landed.
    {
        static thread_local uint64_t je_flow = 0;
        if (diag_env("MINIANDROID_CLASS_LAW_TRACE") &&
            current_class_ == "Lje;" && current_method_ == "<init>" &&
            je_flow < 40) {
            ++je_flow;
            uint16_t je_mi = bytecode_[pc + 1];
            std::cerr << "[JE-FLOW] virtual pc=" << pc
                      << " method_idx=" << je_mi
                      << " -> "
                      << (dex_report_ ? resolve_method_class_for_dex(je_mi, current_dex_index_) : "?")
                      << "."
                      << (dex_report_ ? resolve_method_name_for_dex(je_mi, current_dex_index_) : "?")
                      << std::endl;
        }
    }

    // EXP-071 Phase 7: Save and reset current_invoke_is_static_ to false
    // for invoke-virtual calls. This ensures try_shadow_dispatch correctly
    // treats args[0] as `this` (instance method, not static).
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;

    // EXP-062: Debug — trace ALL invoke-virtual entry in PhoneView.<init>
    if (diag_env("MINIANDROID_EXP062_TRACE") && current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        auto v1 = get_register(1);
        std::cerr << "[EXP062-ENTRY] invoke-virtual entry pc=" << pc
                  << " v1_type=" << static_cast<int>(v1.type)
                  << " v1_obj=" << v1.object_id
                  << std::endl;
    }

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): Per AOSP dalvik-bytecode.html,
    // 35c format is "AA|op BBBB FEDC" where:
    //   code[pc+0] = AA|op (arg_count + 5th_reg in high byte, opcode in low byte)
    //   code[pc+1] = BBBB (method_idx, 16-bit)
    //   code[pc+2] = FEDC (register list, 4 nibbles packed)
    // The previous code read method_idx from code[pc+2] and regs from code[pc+1],
    // which is REVERSED. This caused every invoke-* to read the register list
    // as the method_idx (often out-of-bounds) and the method_idx as the
    // register list (corrupted register values).
    uint16_t method_idx = bytecode_[pc + 1];  // method reference (was pc+2)
    uint16_t regs_word = bytecode_[pc + 2];    // register list (was pc+1)
    std::vector<DalvikValue> args;
    std::vector<std::string> arg_names;
    
    // Extract 5 register args (vG, vH, vI, vJ, vK) from 35c encoding
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg (low nibble of AA) — was (instr >> 4) & 0xF
    };
    
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    for (int i = 0; i < argc && i < 5; ++i) {
        DalvikValue val = get_register(regs[i]);
        args.push_back(val);
        arg_names.push_back(register_name(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for 35c instance calls.
    // 'F' params hold raw IEEE bits in INT32 registers (const is untyped);
    // 'J'/'D' params occupy TWO registers and must merge into one value.
    // Without this, literal float args (drawText x/y, drawRect edges,
    // drawCircle radius, drawOval/drawArc rects…) reached shadows and
    // callees as huge raw-bit integers and wide args arrived split.
    // F-090i (R-NEW-322): the proto is ALSO the callee's exact descriptor —
    // hoisted so every try_recursive_invoke below passes it (the F-023
    // exact-descriptor overload law can only fire when the descriptor is
    // supplied). Live evidence (dooz): c.a invoked the 1-arg
    // z1/i.addAll(Collection); with no descriptor the arity heuristic
    // executed the 2-arg addAll(I, Collection) body whose elements
    // register stayed unwritten → M1/i.f NPE "parameter elements is
    // null" → NavHost graph build died → Compose never composed.
    std::string invoke_descriptor_35c;
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        invoke_descriptor_35c = mre.proto;
        if (invoke_descriptor_35c != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        } else {
            invoke_descriptor_35c.clear();
        }
    }
    
    // EXP-035: VTable-based method resolution
    std::string static_type = "<unknown>";      // Declared type in bytecode
    std::string runtime_type = "<unknown>";     // Actual type of object
    std::string resolved_method = "<unresolved>";

    // EXP-037 Phase B (BLOCKER-002 FIX): Now that DexReport exposes
    // method_ids[], we can resolve method_idx → method name + declaring class.
    std::string method_name_from_dex = "<method_idx:" + std::to_string(method_idx) + ">";
    std::string declaring_class = "<unknown>";
    if (dex_report_) {
        method_name_from_dex = resolve_method_name_for_dex(method_idx, current_dex_index_);
        declaring_class = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // S24 probe: c.a's addAll receives a null collection — print the arg.
    if (diag_env("MINIANDROID_S24_TRACE") &&
        method_name_from_dex == "addAll" &&
        current_class_ == "Landroidx/navigation/c;") {
        static thread_local uint64_t s24_addall = 0;
        if (s24_addall < 8) {
            ++s24_addall;
            std::cerr << "[S24-ADDALL] caller pc=" << pc
                      << " argc=" << args.size()
                      << " recv_oid="
                      << (args.empty() ? 0 : args[0].object_id)
                      << " elements_type="
                      << (args.size() > 1 ? static_cast<int>(args[1].type)
                                          : static_cast<int>(args[0].type))
                      << " elements_oid="
                      << (args.size() > 1 ? args[1].object_id
                                          : args[0].object_id)
                      << " elements_cls="
                      << (args.size() > 1 ? args[1].class_desc
                                          : args[0].class_desc)
                      << std::endl;
        }
    }
    // ── S173 NDFE probe (env-gated, bounded 96, zero behavior) ──────────
    // Koin 4.x keeps its definition index in a DESUGARED
    // j$/util/concurrent/ConcurrentHashMap (resolveDefinition$koin_core,
    // R8-merged into Lorg/slf4j/event/EventRecodingLogger;, reads it via
    // the merged field slot). The S172 residual NoDefinitionFoundException
    // is ONE index miss for the ':local:'-qualified
    // BaseCatalogFeatureFlagProvider. The index ops never reach
    // bridge_to_api (the CHM lives in the app dex and executes its real
    // bytecode per the F-C4-566 law), so this interpreter-level probe is
    // the only visibility: log the RAW get/put keys for the CHM surface.
    if (diag_env("MINIANDROID_S173_PROBE") &&
        declaring_class.find("ConcurrentHashMap") != std::string::npos &&
        // Only RESOLUTION-time lookups: resolveDefinition$koin_core is
        // R8-merged into EventRecodingLogger. The loadModules put/get
        // churn is already proven (BaseCatalog ':local:' put lands).
        (current_method_.find("resolveDefinition") != std::string::npos ||
         current_class_ == "Lorg/slf4j/event/EventRecodingLogger;")) {
        static thread_local uint64_t s173_chm = 0;
        if (s173_chm < 200 && args.size() >= 2 &&
            args[1].type == DalvikType::STRING_REF) {
            ++s173_chm;
            const std::string& keydesc = args[1].string_val;
            std::cerr << "[S173-CHM-V] " << method_name_from_dex
                      << " argc=" << args.size()
                      << " key=\"" << keydesc << "\""
                      << " caller=" << current_class_ << "."
                      << current_method_ << " pc=" << pc << std::endl;
        }
    }
    
    // ────────────────────────────────────────────────────────────────────
    // F-141 (S72-W3): ART NULL-RECEIVER INVOKE LAW. ART's interpreter
    // throws NullPointerException at the invoke site — BEFORE the callee
    // body executes — when an instance invoke's receiver is null
    // ("Attempt to invoke virtual method '<sig>' on a null object
    // reference"). The old path logged "would be NullPointerException"
    // and dispatched anyway: the callee ran with this=NULL, state
    // corruption compounded silently (dooz PersistentHashMapBuilder
    // putAll trie walk, entry #49 this=NULL → arraycopy(null) NPE at the
    // wrong site — first divergence hidden behind the last symptom,
    // constitution §030/§039/§177).
    // Covers NULL_REF and OBJECT_REF/object_id==0 (engine-wide null).
    // ────────────────────────────────────────────────────────────────────
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        // S113 ROOT-059 law: shadow-claimed platform classes route null
        // receivers to the shadow's materialization law instead of the ART
        // NPE — androidx's insets chain (Builder→Impl30→consume*) was built
        // on non-null WindowInsets objects everywhere, and the runtime's
        // platform law provides them. Unclaimed classes keep the
        // ART-faithful throw below.
        // F-NEW-270 (CONT-18h) ROUTE DOMAIN LAW: the route is lawful for
        // FRAMEWORK classes only. ViewShadow's EXP-060 heuristic claims
        // every non-framework class ("could be a View subclass"), so an
        // ungated claims_class() check also captured R8-obfuscated app
        // classes and let their real DEX bodies run with this=null — the
        // wrong-site-exception disease F-141 eliminated (live face: dooz
        // Lhv0;.h→Lhv0;.d iget NPE at pc=17 inside the callee + silent
        // h() swallow). Non-framework classes keep the ART throw.
        // F-NEW-447 (CONT-107): CALLER-DOMAIN GATE on the ROOT-059 route.
        // The routing crutch exists to bridge engine gaps INSIDE framework
        // chains (androidx insets: Builder→Impl30→consume*) — those callers
        // are framework classes. When the CALLER is app DEX code (probe face:
        // Lcom/probe/c106a/MainActivity;.onCreate invoking
        // Landroid/graphics/Paint;.setStrokeWidth on a null never-assigned
        // static Paint), ART throws NPE at the invoke site; the silent
        // shadow route let app code proceed with the null static
        // ([C106-INVOKE2] NO-EXC vs ART NPE — F-NEW-447). Law: route only
        // when the current frame is framework-owned; app-caller sites get
        // the ART-faithful throw below. Unknown caller frames (engine-
        // internal invokes) keep the legacy route.
        const bool f447_caller_is_framework =
            current_class_.empty() || f141_is_framework_class(current_class_);
        if (shadow_registry_ && f141_is_framework_class(declaring_class) &&
            shadow_registry_->claims_class(declaring_class) &&
            f447_caller_is_framework) {
            std::cerr << "[ROOT-059] null-recv routed to shadow law: " << declaring_class
                      << "." << method_name_from_dex
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
            static_type = declaring_class;
            runtime_type = declaring_class;
            resolved_method = declaring_class + "." + method_name_from_dex;
        } else {
        // F-NEW-447 bounded marker: this invoke USED to route to the shadow
        // (ROOT-059); the caller-domain gate keeps ART NPE parity here.
        if (shadow_registry_ && f141_is_framework_class(declaring_class) &&
            shadow_registry_->claims_class(declaring_class) &&
            !f447_caller_is_framework) {
            static thread_local uint64_t f447_npe_n = 0;
            if (f447_npe_n++ < 16)
                std::cerr << "[F447-NPE] app-caller null-recv NPE parity: "
                          << declaring_class << "." << method_name_from_dex
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
        }
        // F-141 DIAG (env-gated, bounded, remove after root closure §112-114):
        // dump the receiver value identity + current frame register window —
        // answers "which register carried the null receiver".
        if (diag_env("MINIANDROID_F141_DIAG") && current_registers_) {
            std::cerr << "[F141-DIAG] " << current_class_ << "."
                      << current_method_ << " pc=" << pc_
                      << " recv_type=" << static_cast<int>(args[0].type)
                      << " recv_oid=" << args[0].object_id
                      << " recv_cls=" << args[0].class_desc
                      << " bytecode_pc_range=[";
            for (uint32_t d = 0; d < 12 && pc_ + d < bytecode_.size(); ++d)
                std::cerr << std::hex << bytecode_[pc_ + d] << std::dec << " ";
            std::cerr << "] regs:";
            int dumped = 0;
            for (const auto& [rid, val] : current_registers_->get_snapshot()) {
                if (dumped++ >= 24) break;
                std::cerr << " " << rid << ":t" << static_cast<int>(val.type)
                          << "/o" << val.object_id;
            }
            std::cerr << std::endl;
        }
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke virtual method '" +
                           declaring_class + "." + method_name_from_dex +
                           "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
        }
    }

    // Get the object reference (first arg is 'this' for virtual calls)
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
        !(args[0].object_id == 0)) {
        DalvikValue this_obj = args[0];
        static_type = this_obj.class_desc;

        // Look up actual object class from heap
        if (auto* heap_obj = heap_.get(this_obj.object_id)) {
            runtime_type = heap_obj->class_descriptor;
            resolved_method = runtime_type + "." + method_name_from_dex;
        } else {
            // Object not in heap - use static type as fallback
            runtime_type = static_type;
            resolved_method = static_type + "." + method_name_from_dex;
            log("⚠️ INVOKE-VIRTUAL: Object not found in heap, using static type");
        }

        // EXP-061: Debug — trace addView calls to find why child=0
        if (method_name_from_dex == "addView" && args.size() >= 2) {
            std::cerr << "[EXP062-ADDVIEW-TRACE] invoke-virtual addView"
                      << " argc=" << args.size()
                      << " this_id=" << args[0].object_id
                      << " this_class=" << runtime_type
                      << " child_type=" << static_cast<int>(args[1].type)
                      << " child_id=" << args[1].object_id
                      << " child_class=" << args[1].class_desc;
            for (size_t ai = 2; ai < args.size(); ++ai)
                std::cerr << " a" << ai << "=t" << static_cast<int>(args[ai].type)
                          << "/v" << (args[ai].type == DalvikType::OBJECT_REF
                                          ? args[ai].object_id
                                          : (int64_t)args[ai].int_val);
            std::cerr << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc
                      << std::endl;
        }

        // R-NEW-347 (S42) diagnostic: where does the DEX-driven
        // View.measure(wSpec, hSpec) call go? Bounded probe (8 hits) —
        // remove after the measure chain is proven.
        if (method_name_from_dex == "measure") {
            static thread_local uint64_t r347_mprobe = 0;
            if (r347_mprobe < 8) {
                ++r347_mprobe;
                std::cerr << "[R347-MPROBE] invoke-virtual measure"
                          << " runtime=" << runtime_type
                          << " declaring=" << declaring_class
                          << " argc=" << args.size()
                          << " recv=" << (args.empty() ? 0 : args[0].object_id)
                          << " a1t=" << (args.size() > 1 ? static_cast<int>(args[1].type) : -1)
                          << " a2t=" << (args.size() > 2 ? static_cast<int>(args[2].type) : -1)
                          << " caller=" << current_class_ << "." << current_method_
                          << std::endl;
            }
        }

        // EXP-062: Debug — trace v1 in PhoneView.<init> after each invoke-virtual
        // EXP-063: Also trace getResourceEntryName
        if (method_name_from_dex == "getResourceEntryName" && args.size() >= 2) {
            std::cerr << "[EXP063-RES-ARGS] getResourceEntryName"
                      << " this_id=" << args[0].object_id
                      << " this_type=" << static_cast<int>(args[0].type)
                      << " resid_type=" << static_cast<int>(args[1].type)
                      << " resid=" << args[1].int_val
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc
                      << std::endl;
        }
        if (current_class_.find("PhoneView") != std::string::npos &&
            current_method_ == "<init>" && !args.empty()) {
            auto v1 = get_register(1);
            std::cerr << "[EXP062-V1] invoke-virtual " << method_name_from_dex
                      << " pc=" << pc
                      << " v1_type=" << static_cast<int>(v1.type)
                      << " v1_obj=" << v1.object_id
                      << " this_type=" << static_cast<int>(args[0].type)
                      << " this_obj=" << args[0].object_id
                      << std::endl;
        }
    } else {
        // No object reference or null - can't do virtual dispatch
        if (args.empty()) {
            log("❌ INVOKE-VIRTUAL: No arguments provided");
        } else if (args[0].type == DalvikType::NULL_REF) {
            log("⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerException)");
        }
        resolved_method = (declaring_class.empty() ? static_type : declaring_class) +
                          "." + method_name_from_dex;
    }
    
    // S109 forensics: trace setFragmentStack dispatch end-to-end.
    if (method_name_from_dex == "setFragmentStack") {
        static thread_local uint64_t sfs_n = 0;
        if (sfs_n < 10) {
            ++sfs_n;
            std::cerr << "[S109-SFS] invoke-virtual entry pc=" << pc
                      << " declaring=" << declaring_class
                      << " runtime=" << runtime_type
                      << " argc=" << args.size()
                      << " a0=" << (args.empty() ? -1 : (int)args[0].type)
                      << " o0=" << (args.empty() ? 0 : args[0].object_id)
                      << " a1=" << (args.size() > 1 ? (int)args[1].type : -1)
                      << " o1=" << (args.size() > 1 ? args[1].object_id : 0)
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
        }
    }
    // Try API bridge with resolved method info
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status api_status = ApiCallTrace::Status::STUBBED;

    // EXP-079: Debug — trace onNextPressed dispatch specifically
    if (method_name_from_dex == "onNextPressed" || method_name_from_dex == "onDoneButtonPressed") {
        std::cerr << "[EXP079-DISPATCH] method=" << method_name_from_dex
                  << " declaring_class=" << declaring_class
                  << " runtime_type=" << runtime_type
                  << " static_type=" << static_type
                  << " args[0]_type=" << (args.empty() ? -1 : (int)args[0].type)
                  << " args[0]_obj=" << (args.empty() ? 0 : args[0].object_id)
                  << " args[0]_class=" << (args.empty() ? "" : args[0].class_desc)
                  << std::endl;
    }

    // [S34-TSTATE] NavigatorState.createBackStackEntry dispatch forensics
    if (declaring_class == "Lh1/t;" && method_name_from_dex == "a") {
        static thread_local uint64_t tstate_n = 0;
        ++tstate_n;
        if (tstate_n <= 12) {
            std::cerr << "[S34-TSTATE] h1/t.a entry #" << tstate_n
                      << " runtime_type=" << runtime_type
                      << " recv=o" << (args.empty() ? 0 : args[0].object_id)
                      << " cls=" << (args.empty() ? "?" : args[0].class_desc);
            for (size_t ai = 1; ai < args.size() && ai < 3; ++ai)
                std::cerr << " a" << ai << "=o" << args[ai].object_id
                          << (args[ai].is_null ? "(NULL)" : "");
            std::cerr << std::endl;
        }
    }
    // EXP-038 (BLOCKER-034): Try recursive DEX method invocation first.
    // If the target method exists in DEX with bytecode, execute it recursively
    // instead of bridging to the API stub layer. This enables real execution
    // of helper methods (e.g., ApplicationLoader.init, AndroidUtilities, etc.)
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        // EXP-059: Polymorphism fix — invoke-virtual must dispatch using the
        // receiver's RUNTIME type, not the static declaring class from the
        // method_idx. Otherwise `BaseFragment.createView` (declared in the
        // base class) would be called instead of `MainTabsActivity.createView`
        // (the override that actually builds the UI).
        //
        // Strategy:
        //   1. If runtime_type is a known subclass of declaring_class, try
        //      the runtime_type FIRST. If it has the method, dispatch there.
        //   2. If the runtime_type doesn't have the method (or fails), fall
        //      back to the declaring_class (which is what the bytecode
        //      reference points to).
        bool tried_runtime_type = false;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            runtime_type != "<unknown>" && runtime_type != declaring_class) {
            // Try the runtime type first — this is the polymorphic dispatch.
            if (try_recursive_invoke(runtime_type, method_name_from_dex,
                                     args, return_val, result,
                                     invoke_descriptor_35c)) {
                recursively_invoked = true;
                tried_runtime_type = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                last_invoke_return_ = return_val;
            }
        }
        // M3 F-020 ROOT FIX (§ ART vtable law — most-derived override):
        // after the runtime type misses, ART walks the RECEIVER's class
        // hierarchy IN ORDER (LP/a → LP/b → LP/g): the first level that
        // declares the method wins. The previous code jumped straight to
        // the STATIC declaring class, skipping intermediate overrides —
        // so Snapshot.s(I) (setWriteCount, overridden by MutableSnapshot
        // LP/b to store the count) executed the base LP/g.s which always
        // throws "Updating write count is not supported" → dooz ISE inside
        // setValue. Walk the chain via class_to_superclass_ (C013 map),
        // stopping at the declaring class; the declaring-class fallback
        // below remains the last resort for receivers whose hierarchy is
        // unknown (pure framework receivers).
        if (!recursively_invoked && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF &&
            runtime_type != "<unknown>" && runtime_type != declaring_class) {
            std::string f020_cur = runtime_type;
            int f020_guard = 0;
            while (!f020_cur.empty() && f020_guard++ < 12 &&
                   f020_cur != declaring_class &&
                   f020_cur != "Ljava/lang/Object;") {
                auto sup_it = class_to_superclass_.find(f020_cur);
                if (sup_it == class_to_superclass_.end()) break;
                const std::string& sup = sup_it->second;
                if (sup.empty() || sup == f020_cur) break;
                f020_cur = sup;
                if (f020_cur == "Ljava/lang/Object;") break;
                if (try_recursive_invoke(f020_cur, method_name_from_dex,
                                         args, return_val, result,
                                         invoke_descriptor_35c)) {
                    recursively_invoked = true;
                    api_status = ApiCallTrace::Status::IMPLEMENTED;
                    last_invoke_return_ = return_val;
                    break;
                }
            }
        }
        if (!tried_runtime_type && !recursively_invoked) {
            // M3 F-020: also gate on !recursively_invoked — a successful
            // hierarchy-walk dispatch above (most-derived override law)
            // must not be overwritten by the static declaring-class body.
            // Use declaring_class from method_ids[] for lookup
            if (try_recursive_invoke(declaring_class, method_name_from_dex,
                                     args, return_val, result,
                                     invoke_descriptor_35c)) {
                recursively_invoked = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                // EXP-057: CRITICAL FIX — must update last_invoke_return_ after
                // recursive invoke so move-result/move-result-object can read it.
                // try_recursive_invoke restores last_invoke_return_ to the saved
                // value internally, so we must re-set it from return_val here.
                // Without this, move-result-object reads stale VOID_ from a
                // previous method's return-void.
                last_invoke_return_ = return_val;
            }
        }
        // ── CONT-12 F-NEW-266 ─────────────────────────────────────────────
        // ART/JVMS 5.4.5: after the class chain misses, virtual resolution
        // continues into the receiver's TRANSITIVELY IMPLEMENTED INTERFACES
        // (default methods). The pre-266 path fell to the API bridge whose
        // stub silently returned null — the null fed the next instruction
        // (un-renamed Compose 1.11.4 oracle face: root$1$1.then(other) →
        // interface Modifier.then default body → null → chained
        // invoke-interface receiver NPE ×172 → setContent dead).
        if (!recursively_invoked && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF &&
            !runtime_type.empty() && runtime_type != "<unknown>") {
            std::string f266_dispatched;
            if (try_interface_default_invoke(
                    runtime_type, method_name_from_dex, invoke_descriptor_35c,
                    args, return_val, result, &f266_dispatched)) {
                recursively_invoked = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                last_invoke_return_ = return_val;
                // S157-B: trace_cap==0 gate (never-read trace).
                if (config_.trace_cap > 0) {
                trace.invoked_method = f266_dispatched +
                    " [default-method " + invoke_descriptor_35c + "]";
                }
            }
        }
    }

    if (declaring_class == "Lh1/t;" && method_name_from_dex == "a") {
        static thread_local uint64_t tstate_r = 0;
        ++tstate_r;
        if (tstate_r <= 12) {
            std::cerr << "[S34-TSTATE-RES] h1/t.a #" << tstate_r
                      << " recursively_invoked=" << (recursively_invoked ? 1 : 0)
                      << " runtime=" << runtime_type
                      << " status=" << (int)api_status;
            if (return_val.type == DalvikType::OBJECT_REF)
                std::cerr << " ret=o" << return_val.object_id;
            std::cerr << std::endl;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // Use declaring_class (the static type from method_ids[]) if
        // runtime_type is unknown — this lets us route framework calls like
        // android.app.Activity.onCreate to the API stub layer.
        std::string api_class = (runtime_type != "<unknown>") ? runtime_type : declaring_class;
        // M3 FINDING-011 diag (bounded): does the View tag bridge entry fire?
        if (method_name_from_dex == "setTag" || method_name_from_dex == "getTag" ||
            method_name_from_dex == "obtainStyledAttributes") {
            static thread_local uint64_t tag_entry = 0;
            if (tag_entry < 16) {
                tag_entry++;
                std::cerr << "[TAG-ENTRY] bridge_to_api " << api_class << "."
                          << method_name_from_dex << " argc=" << args.size()
                          << " caller=" << current_class_ << "." << current_method_
                          << std::endl;
            }
        }
        bridge_to_api(api_class, method_name_from_dex, args, return_val, api_status, method_idx); last_invoke_return_ = return_val;
        // ── F-NEW-271 LAW DIAG (collection add/remove channel, env-gated
        // MINIANDROID_F271_COLL_TRACE, bounded, read-only). The F271-WRITE
        // face (dooz Lnb0.p pc=1553 storing STRING_REF "" into Lnb0.j:Lqb0)
        // is served by the CollectionShadow remove(int) channel: a slot that
        // stored a NULL/zero-ref element (kind-2 + "" null-element
        // representation) is served back as handled_string("") → STRING_REF/0
        // — an alien type ART would never produce (ArrayList.remove of a null
        // element returns typed null). This trace records BOTH directions of
        // the channel with the live arg kinds and the served value so the
        // first incorrect state (a legal add(null) vs a zero-ref OBJECT arg
        // fed by an upstream conversion defect) is evidence, not guesswork.
        if (diag_env("MINIANDROID_F271_COLL_TRACE") &&
            (method_name_from_dex == "add" || method_name_from_dex == "remove" ||
             method_name_from_dex == "removeAt" || method_name_from_dex == "removeFirst" ||
             method_name_from_dex == "removeLast" || method_name_from_dex == "pop" ||
             method_name_from_dex == "poll" || method_name_from_dex == "pollLast") &&
            (api_class.find("Ljava/util/ArrayList;") != std::string::npos ||
             api_class.find("Ljava/util/ArrayDeque;") != std::string::npos ||
             api_class.find("Ljava/util/LinkedList;") != std::string::npos)) {
            static thread_local uint64_t f271_coll_n = 0;
            if (f271_coll_n < 100) {
                ++f271_coll_n;
                std::cerr << "[F271-COLL] " << method_name_from_dex
                          << " recv=" << api_class
                          << " recv_id=" << (!args.empty() ? args[0].object_id : 0)
                          << " argc=" << args.size();
                for (size_t fci = 1; fci < args.size() && fci <= 3; ++fci) {
                    std::cerr << " a" << fci << ":t"
                              << static_cast<int>(args[fci].type) << "/o"
                              << args[fci].object_id;
                    if (args[fci].type == DalvikType::STRING_REF)
                        std::cerr << "(\"" << args[fci].string_val.substr(0, 24) << "\")";
                }
                std::cerr << " -> served t"
                          << static_cast<int>(return_val.type) << "/o"
                          << return_val.object_id;
                if (return_val.type == DalvikType::STRING_REF)
                    std::cerr << "(\"" << return_val.string_val.substr(0, 24) << "\")";
                std::cerr << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
            }
        }
    }

    // EXP-094 (CM-018): Record the receiver of a successful "setParams" call.
    // Multi-page apps instantiate several same-class page views; the one the
    // app actively configures via setParams IS the current page. The render
    // stage uses this to pick the correct render root (see stage_render_frame).
    if (method_name_from_dex == "setParams" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        last_set_params_view_ = args[0].object_id;
        std::cerr << "[EXP094-SETPARAMS] active page view = obj#" << last_set_params_view_
                  << " class=" << args[0].class_desc << std::endl;
    }
    
    // Create API call trace with VTable information
    // GP S223 CALL-004 (issue #582): the 35c trace now carries the EXACT
    // descriptor (already resolved above for the F-023 overload law —
    // invoke_descriptor_35c) and the call's execution time; caller method
    // and PC were already present.
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = runtime_type;  // Use runtime type for accuracy
    api_trace.method = method_name_from_dex;
    api_trace.descriptor = invoke_descriptor_35c;   // CALL-004
    api_trace.arguments = arg_names;
    api_trace.return_value = return_val.to_string();
    api_trace.status = api_status;
    api_trace.pc = pc;
    api_trace.frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    note_api_status(api_trace);  // F-NEW-200 census
    
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));
    
    // EXP-035: Evidence trace with VTable dispatch information
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = resolved_method;
    trace.operands.push_back({"args", std::to_string(arg_names.size())});
    trace.operands.push_back({"method_idx", std::to_string(method_idx)});
    trace.operands.push_back({"method_name", method_name_from_dex});
    trace.operands.push_back({"static_type", static_type});       // CRITICAL EVIDENCE
    trace.operands.push_back({"runtime_type", runtime_type});     // CRITICAL EVIDENCE
    trace.operands.push_back({"resolved_method", resolved_method}); // CRITICAL EVIDENCE
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});  // MANDATORY TAG
    }

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

// EXP-037 Phase B (BLOCKER-012): invoke-super
// Format: 35c [op {vC..vG, vF}], method@BBBB
//   instr_word[0] = opcode | (arg_count << 4)
//   instr_word[1] = packed register args (4 nibbles)
//   instr_word[2] = method_idx
//
// Semantics (per AOSP dexlib2):
//   invoke-super dispatches a virtual method starting from the SUPERCLASS
//   of the static type of `this`, NOT the runtime type. This is critical
//   for `super.onCreate(bundle)` calls — the call site declares the parent
//   class explicitly so the runtime must walk to that class's vtable slot
//   rather than using the runtime-type vtable.
//
//   Without this opcode, NO real Android app can execute past PC=0 of its
//   onCreate method, because `super.onCreate(bundle)` is always the first
//   instruction in user onCreate() implementations.
//
// Implementation:
//   Since BLOCKER-002 (method_ids[] parsing) is still open, we cannot yet
//   resolve method_idx → method name from the DEX. We degrade gracefully:
//   1. Log the invoke-super attempt with method_idx.
//   2. Bridge to API layer (which currently has stub onCreate handler).
//   3. Advance PC by 3 (35c format = 3 code units).
//   4. Do NOT halt — let execution continue to the next instruction.
//
// When BLOCKER-002 lands, this method should be rewritten to:
//   1. Look up method_idx in DexReport::method_ids[] to get the
//      declaring class + method name + descriptor.
//   2. Resolve the parent class of `this`'s static type.
//   3. Walk the parent's virtual_methods[] to find the matching method.
//   4. Recursively invoke execute_method_internal() on that method.
bool DalvikExecutionEngine::execute_invoke_super(uint32_t pc, InstructionTrace& trace,
                                                  DalvikExecutionResult& result) {
    // Format: 35c — 3 code units (6 bytes)
    if (pc + 2 >= bytecode_.size()) {
        log("❌ INVOKE-SUPER: PC out of bounds");
        return false;
    }

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1

    // 35c register encoding: 5 nibbles packed
    //   vA = high nibble of opcode word = arg count (typically 1 or 2)
    //   vG = low nibble of opcode word = 5th register (or 0 if vA < 5)
    //   vC..vF = 4 nibbles of regs_word
    // EXP-037 Phase B (BLOCKER-016 FIX): 35c format AA|op where AA = high byte.
// arg_count = HIGH NIBBLE of AA = (instr >> 12) & 0xF (was (instr >> 4) & 0xF — wrong)
// 5th_reg   = LOW NIBBLE of AA  = (instr >> 8) & 0xF (was (instr >> 4) & 0xF — wrong)
uint8_t arg_count = static_cast<uint8_t>((instr >> 12) & 0xF);
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg (low nibble of AA) — was (instr >> 4) & 0xF
    };

    // Read up to arg_count registers (cap at 5 for 35c format)
    std::vector<DalvikValue> args;
    std::vector<std::string> arg_names;
    uint8_t n_args = std::min<uint8_t>(arg_count, 5);
    for (uint8_t i = 0; i < n_args; ++i) {
        DalvikValue val = get_register(regs[i]);
        args.push_back(val);
        arg_names.push_back(register_name(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for 35c instance calls
    // (super). See execute_invoke_virtual for the full rationale.
    // F-NEW-284: proto_35c is declared at dispatch scope (not inside the
    // dex_report_ guard) so the super-dispatch arm can pass it to
    // try_recursive_invoke as the F-023 exact-descriptor authority. Empty
    // when the proto is unresolvable — legacy behavior preserved.
    std::string proto_35c;
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        proto_35c = mre.proto;
        if (proto_35c != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        } else {
            proto_35c.clear();
        }
    }

    // EXP-037 Phase B (BLOCKER-002 + BLOCKER-012): Now that DexReport exposes
    // method_ids[], we can resolve method_idx → method name + declaring class.
    std::string method_name = "<method_idx:" + std::to_string(method_idx) + ">";
    std::string declaring_class = "<unknown>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        declaring_class = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // Identify `this` (first arg) for diagnostic logging
    std::string runtime_type = "<unknown>";
    std::string static_type = "<unknown>";
    std::string resolved_method = declaring_class + "." + method_name + " (super)";

    // F-141 (S72-W3): ART null-receiver law — invoke-super with a null
    // receiver throws NPE at the call site before the ancestor body runs
    // (ART DoInvoke → ThrowNullPointerExceptionFromInterpreter). Old
    // behavior logged "would be NullPointerException on real Android"
    // and dispatched with this=NULL.
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke super method '" + declaring_class +
                           "." + method_name + "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
    }

    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        const DalvikValue& this_obj = args[0];
        static_type = this_obj.class_desc;
        if (auto* heap_obj = heap_.get(this_obj.object_id)) {
            runtime_type = heap_obj->class_descriptor;
        } else {
            runtime_type = static_type;
        }
    } else if (!args.empty() && args[0].type == DalvikType::NULL_REF) {
        log("⚠️ INVOKE-SUPER: Null `this` reference (would be NullPointerException on real Android)");
        runtime_type = "<null>";
    } else {
        log("⚠️ INVOKE-SUPER: First argument is not an object reference (arg_count=" +
            std::to_string(arg_count) + ", arg[0].type=" +
            std::to_string(static_cast<int>(args.empty() ? DalvikType::UNINITIALIZED : args[0].type)) + ")");
    }

    log("📞 INVOKE-SUPER: " + declaring_class + "." + method_name +
        " (method_idx=" + std::to_string(method_idx) +
        ", arg_count=" + std::to_string(arg_count) +
        ", static_type=" + static_type +
        ", runtime_type=" + runtime_type + ")");

    // Bridge to API layer — for super.onCreate(), the API layer provides
    // the framework's Activity.onCreate implementation (window setup, etc.).
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status api_status = ApiCallTrace::Status::STUBBED;

    // EXP-038 (BLOCKER-034): Try recursive invocation for super calls too.
    bool recursively_invoked = false;
    // F-NEW-284 (CONT-28): the call-site proto is the F-023 overload law's
    // AUTHORITY here too — the proto was already resolved above for the
    // EXP-095 arg conversion but was NOT passed to the dispatcher, so every
    // super-dispatch selected overloads by SHAPE. Real-Compose oracle proof
    // (proto-free selection, JVMS 5.4.5): NodeCoordinator declares TWO
    // same-name 32-unit overloads placeAt-f8xVGno(JF, GraphicsLayer)V and
    // placeAt-f8xVGno(JF, Function1)V; LayoutModifierNodeCoordinator.
    // placeAt(JF, Function1)V invoke-super'd without a descriptor, the
    // loose shape loop hit the GraphicsLayer body first, its `layer` param
    // register received the Function1 lambda, placeSelf carried the lambda
    // into the explicitLayer slot, and GraphicsLayerOwnerLayer ended up
    // with a lambda where its GraphicsLayer belongs — every later
    // GraphicsLayer.setPosition/record died f141-null-recv on the missing
    // impl field (the draw-pipeline APP BOUNDARY). The proto restores
    // exact-descriptor selection; without one the legacy behavior is
    // byte-identical (descriptor=="" keeps the old path).
    if (config_.enable_api_bridge) {
        if (try_recursive_invoke(declaring_class, method_name, args, return_val, result,
                                 proto_35c)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            api_status = ApiCallTrace::Status::IMPLEMENTED;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // ── CONT-130 (F-NEW-471 SLICE 2): SUPERCLASS-CHAIN SUPER RESOLUTION ─
        // Byte-level ground truth (scripts/cont130_dex_truth.py, tictactoe v3
        // classes.dex, class_def[1563] @ class_data_off 0x3185fe): the
        // engine's class_data walk is BYTE-EXACT (DM diffs 1135/1/38 =
        // <clinit>/<init>/init; 49 VM diffs resolving 1137..1196 with 1184
        // SKIPPED by the encoded diff stream — the dex genuinely does NOT
        // declare AndroidApplication.onCreate while method_ids[1184]
        // references it for the invoke-super in AndroidLauncher.onCreate).
        // That is a NORMAL dex shape: a method_ids entry is a REFERENCE
        // pool slot, not a declaration; ART resolves the super-call by
        // walking the superclass chain (JVMS 5.4.3.3) — an app-parsed
        // ancestor's body if one declares it, else the first framework
        // ancestor (the F-NEW-324 boundary, already landed). The engine's
        // super path only tried the EXACT declaring class, so a
        // declared-ancestor super-call silently shadow-fallbacked.
        // LAW: after the exact-class miss, walk the app-parsed superclass
        // chain (the F-074/S21 walker, receiver identity preserved,
        // 16-hop cap) BEFORE the shadow bridge. Strictly closer to ART:
        // only reachable when the exact class missed, and a chain hit is
        // a real DEX body the old path never ran. Framework-bottomed
        // chains (tictactoe AndroidApplication→Activity) still resolve
        // through the F-NEW-324 boundary law — unchanged byte path.
        if (try_recursive_invoke_on_super(declaring_class, method_name, args,
                                          return_val, result, proto_35c)) {
            last_invoke_return_ = return_val;
            recursively_invoked = true;
            api_status = ApiCallTrace::Status::IMPLEMENTED;
            static std::atomic<uint64_t> f471_chain_n{0};
            if (f471_chain_n.fetch_add(1, std::memory_order_relaxed) < 40) {
                std::cerr << "[F-NEW-471-SUPER-CHAIN] super-call "
                          << declaring_class << "." << method_name
                          << " not declared locally; dispatched via"
                          << " app-parsed superclass chain (ART 5.4.3.3)"
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // ── CONT-127 (F-NEW-471 SLICE 1) + CONT-130 RECLASSIFICATION ────────
        // Byte truth (cont130_dex_truth.py): method_ids is a REFERENCE pool,
        // not a declaration table — a reference whose class declares no such
        // method in class_data is a NORMAL dex shape resolved by superclass
        // resolution, NOT evidence of a parse desync. The engine's
        // class_data walk was re-verified byte-exact for tictactoe v3
        // (class_def[1563]: 3 DM + 49 VM, diffs self-consistent, names
        // addAndroidEventListener..useImmersiveMode — onCreate omitted by
        // the dex itself). After SLICE 2's chain walk, reaching this point
        // means the whole app-parsed chain lacks a body: the call resolves
        // onto the first FRAMEWORK ancestor (F-NEW-324 boundary law below)
        // — the ART-equivalent shadow target. This log now DOCUMENTS that
        // resolution (bounded); it no longer claims a parse gap.
        if (dex_report_) {
            const auto& mre = method_resolve_entry(current_dex_index_,
                                                   method_idx);
            if (mre.cls == declaring_class && mre.name == method_name) {
                static std::atomic<uint64_t> f471_gap_n{0};
                if (f471_gap_n.fetch_add(1, std::memory_order_relaxed) < 40) {
                    std::cerr << "[F-NEW-471-RES-GAP] super-call "
                              << declaring_class << "." << method_name
                              << " method_id=" << method_idx
                              << " has no declaration in class_data or any"
                              << " app-parsed superclass (reference-only"
                              << " method_ids slot) — framework-boundary"
                              << " shadow dispatch (ART-equivalent)"
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
        // R-NEW-345 SUPER-DISPATCH IDENTITY LAW: pass the CLEAN declaring
        // class into the bridge. ART super-dispatch resolves the SAME
        // receiver/method identity as virtual dispatch; the old "<super>"
        // marker leaked into dispatch identity, so every framework-ancestor
        // super call silently missed its shadow — kotlinx scheduler
        // Worker.start() { super.start() } → Thread.start() never reached
        // ThreadShadow (no worker ever ran: runBlocking/BlockingCoroutine
        // spun forever in joinBlocking). Marker kept in the api_trace log
        // line below only.
        //
        // ── F-NEW-324 (CONT-52): the super-dispatch BOUNDARY law. When the
        // declaring class is a DEX-defined INTERMEDIATE that does not
        // define the method (NavigationView.onMeasure does invoke-super
        // f.onMeasure where f = ScrimInsetsFrameLayout is a DEX class with
        // NO onMeasure whose super is the FrameLayout boundary), ART
        // resolution continues PAST the DEX chain onto the FIRST framework
        // ancestor — the bridge must see THAT boundary class, not the DEX
        // declaring class, or every shadow keyed by a framework name
        // silently misses: the FrameLayout.onMeasure measure law never
        // ran, setMeasuredDimension was never reached, and the engine
        // recorded [DEX-MEASURE] NavigationView.onMeasure
        // "FAILED(no write-back)" on every pass → the whole drawer menu
        // measured 0x0 and the NavigationView node never entered the
        // render tree. Walk the DEX superclass chain up from the declaring
        // class; the first NON-DEX ancestor is the boundary. Declaring
        // classes that are already framework classes (the R-NEW-345 case,
        // e.g. RecyclerView.onMeasure's super → ViewGroup) are untouched —
        // probe fnew324 P2 pins that control face.
        std::string bridge_cls = declaring_class;
        if (dex_report_ && is_dex_defined_class(declaring_class)) {
            std::string boundary = superclass_of(declaring_class);
            while (!boundary.empty() && is_dex_defined_class(boundary)) {
                boundary = superclass_of(boundary);
            }
            if (!boundary.empty()) bridge_cls = boundary;
        }
        bridge_to_api(bridge_cls, method_name,
                      args, return_val, api_status, method_idx);
        last_invoke_return_ = return_val;
    }

    // Record an API call trace entry so this call shows up in evidence
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = declaring_class + "<super>";
    api_trace.method = method_name;
    api_trace.arguments = arg_names;
    api_trace.return_value = return_val.to_string();
    api_trace.status = api_status;
    api_trace.pc = pc;
    api_trace.frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));

    // Trace evidence
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = resolved_method;
    trace.operands.push_back({"invoke_kind", "super"});
    trace.operands.push_back({"method_idx", std::to_string(method_idx)});
    trace.operands.push_back({"method_name", method_name});
    trace.operands.push_back({"declaring_class", declaring_class});
    trace.operands.push_back({"arg_count", std::to_string(arg_count)});
    trace.operands.push_back({"args", std::to_string(arg_names.size())});
    trace.operands.push_back({"static_type", static_type});
    trace.operands.push_back({"runtime_type", runtime_type});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    // Advance PC past the 35c instruction (3 code units = 6 bytes)
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_direct(uint32_t pc, InstructionTrace& trace,
                                                 DalvikExecutionResult& result) {
    // Similar to invoke-virtual but for constructors and private methods
    if (pc + 2 >= bytecode_.size()) return false;

    // EXP-071 Phase 7: Save and reset current_invoke_is_static_ to false
    // for invoke-direct calls (instance methods).
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;
    
    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1
    
    // Extract registers
    // EXP-037 Phase B (BLOCKER-016 FIX): 5th reg is low nibble of AA (high byte
    // of opcode word), so it's (instr >> 8) & 0xF, not (instr >> 4) & 0xF.
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg — was (instr >> 4) & 0xF
    };
    
    std::vector<DalvikValue> args;
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    for (int i = 0; i < argc && i < 5; ++i) {
        args.push_back(get_register(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for invoke-direct (35c).
    // Constructors like Paint.<init>(int) are unaffected, but any direct
    // call with literal floats/wides (e.g. custom View ctors) needs the
    // same proto-guided reinterpretation as virtual calls.
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        const std::string& proto_35c = mre.proto;
        if (proto_35c != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        }
    }
    
    // Resolve as constructor (<init>) or direct method
    // EXP-037 Phase B (BLOCKER-002 FIX): use DexReport::method_ids to resolve
    // method_idx → real method name + declaring class.
    std::string method_name = "<init>";  // fallback for legacy code paths
    std::string class_name = "<unknown>";
    std::string method_desc_081;
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
        method_desc_081 = resolve_method_proto_for_dex(method_idx, current_dex_index_);
        // S55 R-NEW-376 (env-gated): direct evidence for the j0.<init>
        // self-recursion — print EVERY invoke-direct dispatched from a
        // j0/t0/E0 constructor frame with the resolved (class, name, desc).
        static const bool r376_direct =
            diag_env("MINIANDROID_F040_DIAG");
        if (r376_direct && current_method_ == "<init>" &&
            (current_class_ == "Lj/j0;" || current_class_ == "Lt0/t;" ||
             current_class_ == "LE0/c;")) {
            static thread_local uint64_t r376_n = 0;
            if (r376_n < 60000) {
                r376_n++;
                std::cerr << "[R376-DIRECT] from=" << current_class_
                          << ".<init> depth=" << recursion_depth_
                          << " method_idx=" << method_idx
                          << " dex=" << current_dex_index_
                          << " resolved=" << class_name << "."
                          << method_name << method_desc_081
                          << " argc=" << args.size() << std::endl;
            }
        }
        // EXP-081: Debug trace
        if (diag_env("MINIANDROID_EXP081_TRACE") && (method_name.find("lambda") != std::string::npos || method_name.find("createView") != std::string::npos)) {
            std::cerr << "[EXP081-DESC] method=" << method_name
                      << " method_idx=" << method_idx
                      << " dex=" << current_dex_index_
                      << " desc=" << method_desc_081
                      << std::endl;
        }
    }

    // EXP-061: Debug — trace invoke-direct inside PhoneView.<init>
    if (diag_env("MINIANDROID_EXP061_TRACE") && current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        std::cerr << "[EXP061-INVOKE-DIRECT] caller=PhoneView.<init>"
                  << " method_idx=" << method_idx
                  << " dex_index=" << current_dex_index_
                  << " → class=" << class_name
                  << " method=" << method_name
                  << " argc=" << (int)argc
                  << std::endl;
    }
    
    // F-141 (S72-W3): ART null-receiver law extends to invoke-direct
    // (constructors/private methods): NPE at the call site before the
    // callee body executes. Previously invoke-direct had NO null check —
    // the body ran with this=NULL (silent wrongness, §039/§177).
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke direct method '" + class_name +
                           "." + method_name + "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
    }

    // MASTER CAMPAIGN FIX (F2 constructor-direct law): java.lang.Object.<init>
    // is the compiler-mandated empty constructor (AOSP/ART: Object has no
    // constructor logic; javac/d8 emit invoke-direct Object;-><init>()V as
    // the first instruction of EVERY constructor). It must be a no-op at the
    // engine level. Letting it fall through to the shadow layer let the
    // C013 ancestor walk + ViewShadow's user-class catch-all claim it
    // (evidence: fr.neamar.kiss v224, R8 horizontal class merging — 24
    // classes extend the merged target Lfr/neamar/kiss/db/DBHelper;, every
    // merged constructor's Object.<init> super call walked
    // ArchTaskExecutor->DBHelper and ViewShadow allocated bogus view nodes).
    if (method_name == "<init>" && class_name == "Ljava/lang/Object;") {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            if (auto* obj = heap_.get(args[0].object_id)) {
                heap_.mark_initialized(args[0].object_id);
            }
        }
        // S157-B: trace_cap==0 gate (never-read trace — see iget block).
        if (config_.trace_cap > 0) {
        trace.invoked_method = "Ljava/lang/Object;.<init> (no-op law)";
        trace.operands.push_back({"method", std::to_string(method_idx)});
        }
        current_invoke_is_static_ = saved_is_static;
        pc_ = pc + 3;
        return true;
    }

    // Check if first arg is an object we allocated
    // EXP-061 FIX: Do NOT overwrite class_name with the runtime class for
    // invoke-direct. invoke-direct uses the DECLARING class (from method_ids[]),
    // not the runtime class. Overwriting it causes try_recursive_invoke to
    // search for <init> in the SUBCLASS (e.g. PhoneView) instead of the
    // SUPERCLASS (e.g. SlideView), leading to infinite recursion detection
    // or wrong method selection. Only invoke-virtual should use the runtime
    // class for polymorphic dispatch.
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        if (auto* obj = heap_.get(args[0].object_id)) {
            // Mark as initialized (constructor called)
            if (method_name == "<init>") {
                heap_.mark_initialized(args[0].object_id);
            }
            // S157-B: gate the argument build on verbose_ (log() checks too late).
            if (verbose_) log("  INVOKE-DIRECT: " + class_name + "." + method_name +
                "() on obj#" + std::to_string(args[0].object_id));
        }
    }
    
    // API bridge
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

    // ── #371 CLOSEOUT: JVMS 5.5 / AOSP ClassLinker::EnsureInitialized law
    // ── the first ACTIVE USE of a class triggers initialization, and
    // invoke-static IS an active use. sget/sput/new-instance already
    // ensured this; a class first touched via static-method invocation ran
    // uninitialized (S-2 evidence: NativeProbe.<clinit> — the canonical
    // System.loadLibrary-in-static-init pattern — never executed, so the
    // native library never loaded and every native call failed softly 0).
    // ensure_class_initialized early-exits on the already-initialized set,
    // so the per-call cost is one hash lookup.
    if (!class_name.empty() && class_name[0] == 'L')
        ensure_class_initialized(class_name);

    // EXP-038 (BLOCKER-034): Try recursive invocation.
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        // EXP-079: Debug trace for lambda$createView$1 dispatch
        // EXP-089: Also trace lambda$new$0 (ActionBar back button handler)
        // and any method containing "presentFragment" or "swapToFragment"
        if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||
            method_name.find("onDoneButton") != std::string::npos ||
            method_name.find("onNextPressed") != std::string::npos ||
            method_name.find("lambda$new") != std::string::npos ||
            method_name.find("presentFragment") != std::string::npos ||
            method_name.find("swapToFragment") != std::string::npos ||
            method_name.find("onBackPressed") != std::string::npos)) {
            std::cerr << "[EXP079-DIRECT] invoke-direct: class=" << class_name
                      << " method=" << method_name
                      << " method_idx=" << method_idx
                      << " dex_index=" << current_dex_index_
                      << " args=" << args.size()
                      << std::endl;
        }
        if (class_name == "LE1/c;" && diag_env("MINIANDROID_E1_DIAG")) {
            std::cerr << "[E1-DIAG] inner direct: desc=" << method_desc_081
                      << " args=" << args.size() << std::endl;
        }
        if (try_recursive_invoke(class_name, method_name, args, return_val, result, method_desc_081)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
            // EXP-079: Debug trace
            if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||
                method_name.find("lambda$new") != std::string::npos ||
                method_name.find("presentFragment") != std::string::npos)) {
                std::cerr << "[EXP079-DIRECT] try_recursive_invoke SUCCEEDED for " << method_name << std::endl;
            }
        } else {
            // EXP-079: Debug trace
            if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||
                method_name.find("lambda$new") != std::string::npos ||
                method_name.find("presentFragment") != std::string::npos)) {
                std::cerr << "[EXP079-DIRECT] try_recursive_invoke FAILED for " << method_name << std::endl;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
    }
    
    // Trace
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = class_name + "." + method_name;
    trace.operands.push_back({"method", std::to_string(method_idx)});
    }

    // MASTER CAMPAIGN FIX (F8 default-onMeasure law): at constructor
    // completion, record whether the AOSP DEFAULT View.onMeasure applies to
    // this node (no onMeasure override anywhere in the semantic chain below
    // a framework content class). The measure pass consumes this for leaf
    // nodes with no content source (View.getDefaultSize: AT_MOST/EXACTLY →
    // specSize). Evidence: org.billthefarmer.scope v140 custom views
    // measured 0x0 (content model) where AOSP measures them at the
    // parent-available size.
    if (method_name == "<init>" && shadow_registry_ && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow) {
            auto* node = view_shadow->find_node(args[0].object_id);
            if (node) {
                const std::string& cls = !std::string(args[0].class_desc).empty()
                                             ? std::string(args[0].class_desc) : class_name;
                bool overrides = class_chain_defines_method(cls, "onMeasure");
                // M3 F-005 FIX-A: content families never take the
                // getDefaultSize fallback (see the constructor-time site).
                node->aosp_default_measure =
                    !overrides && !runtime_content_measure_class(cls);
                // R-NEW-347 (S42): programmatic views (new-instance +
                // invoke-direct — compose's AndroidComposeView from
                // La72;.a, app-built custom views) must carry the SAME
                // overrides_on_measure flag the inflate-time constructor
                // path records (run_custom_view_constructor site). Without
                // it the F10 real-DEX onMeasure hook never fires for
                // programmatically-built views and the measure pass
                // answers from the native content model instead of the
                // APK's own onMeasure bytecode.
                node->overrides_on_measure = overrides;
                // S122 (R-NEW-417): same capture for the touch gate.
                node->overrides_touch_event =
                    class_chain_defines_method(cls, "onTouchEvent");
                // S128 (R-NEW-424, CAP-INPUT-100): intercept-gate capture.
                node->overrides_intercept_touch_event =
                    class_chain_defines_method(cls, "onInterceptTouchEvent");
                // S123 (R-NEW-419): same capture for the onSizeChanged law.
                node->overrides_on_size_changed =
                    class_chain_defines_method(cls, "onSizeChanged");
            }
        }
    }

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_static(uint32_t pc, InstructionTrace& trace,
                                                 DalvikExecutionResult& result) {
    // Format similar to invoke-virtual but for static methods
    if (pc + 2 >= bytecode_.size()) return false;
    // S55 R-NEW-361: entry-level probe — was the function even reached?
    if (diag_env("MINIANDROID_F040_DIAG")) {
        static thread_local uint64_t eis_entry = 0;
        if (eis_entry < 200000) {
            eis_entry++;
            auto mn = resolve_method_name_for_dex(
                bytecode_[pc + 1], current_dex_index_);
            if (mn == "fill" || mn == "r") {
                std::cerr << "[EIS-ENTRY] pc=" << pc
                          << " method=" << mn
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }

    // EXP-071 Phase 8: Mark this call as static so try_shadow_dispatch
    // doesn't treat args[0] as `this`. See header comment for details.
    //
    // EXP-071 Phase 7 FIX: The flag stays true during the entire
    // execute_invoke_static call. execute_invoke_virtual and
    // execute_invoke_direct SAVE and RESET the flag to false at their
    // entry, and RESTORE it at their exit. This ensures that:
    //   - bridge_to_api → try_shadow_dispatch at THIS level sees true (static)
    //   - bridge_to_api → try_shadow_dispatch inside callees sees false (instance)
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = true;

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1
    // ── S222-A (DIAG-ONLY, env-gated MINIANDROID_S222_CACHE): the dooz
    // text-cache density PACKER probe (invoke-static face). Lsg0;.a(FF)J
    // packs (density, fontScale) into the InlineDensity long the
    // MultiParagraphLayoutCache stores. Logging the caller names the
    // producer of the (2.625, 0.0) fontScale-zero face — the flip driver
    // the S221 decode left open ("null vs a real (0,0) Density object").
    {
        static thread_local const bool s222_pack_on =
            diag_env("MINIANDROID_S222_CACHE");
        if (s222_pack_on) {
            std::string s222_pmn =
                resolve_method_name_for_dex(method_idx, current_dex_index_);
            if (s222_pmn == "a" && dex_report_) {
                std::string s222_pcls =
                    dex_report_->get_method_class(method_idx);
                if (s222_pcls == "Lsg0;") {
                    static thread_local uint64_t s222_pn = 0;
                    if (s222_pn < 48) {
                        ++s222_pn;
                        std::cerr << "[S222-PACK-S] Lsg0;.a(FF)J caller="
                                  << current_class_ << "." << current_method_
                                  << " pc=" << pc << std::endl;
                    }
                }
            }
        }
    }
    // ────────────────────────────────────────────────────────────────────
    // R-NEW-350 probe (S43, env-gated read-only): the 3-arg
    // Class.forName(String,boolean,ClassLoader) from protobuf's
    // GeneratedMessageLite.getDefaultInstance produced ZERO bridge logs —
    // trace every static forName dispatch AT THE INTERPRETER LEVEL (method
    // idx + resolved name + class) so the exact route (cycle guard /
    // super-dispatch / bridge miss) becomes visible in one run.
    // ────────────────────────────────────────────────────────────────────
    if (dex_report_) {
        static thread_local const bool r350fn2 =
            diag_env("MINIANDROID_R350_TRACE");
        if (r350fn2) {
            std::string fn_name =
                resolve_method_name_for_dex(method_idx, current_dex_index_);
            if (fn_name == "forName") {
                std::string fn_cls =
                    resolve_method_class_for_dex(method_idx, current_dex_index_);
                std::cerr << "[R350-FN2] static forName dispatch idx="
                          << method_idx << " class=" << fn_cls
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc_units=" << pc
                          << std::endl;
            }
        }
    }

    // Extract argument registers
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg — was (instr >> 4) & 0xF
    };

    std::vector<DalvikValue> args;
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;

    // F-044 DIAG (env-gated): did the version-scan's identityHashCode call
    // reach the invoke handler at all?
    {
        static thread_local const bool f044p = std::getenv("MINIANDROID_F044_DIAG") != nullptr;
        if (f044p) {
            std::string mh = resolve_method_name_for_dex(method_idx, current_dex_index_);
            std::string mc = resolve_method_class_for_dex(method_idx, current_dex_index_);
            if (mc == "Ljava/lang/System;" && mh == "identityHashCode") {
                std::cerr << "[F044-DIAG] invoke-static System.identityHashCode reached execute_invoke_static" << std::endl;
            }
        }
    }

    // EXP-071 Phase 8: Resolve method name and proto EARLY so we can use them
    // for debug tracing in the wide-merge code below. The original code only
    // resolved method_name AFTER the args were built, which meant our debug
    // trace couldn't reference method_name.
    std::string method_name = "<static_method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<static_class>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // ── S188-W18 FT PROBE (entry) — trace the FreeType static dispatch.
    static thread_local const bool w18ft_in_on =
        std::getenv("MINIANDROID_W18_FT_TRACE") != nullptr;
    if (w18ft_in_on &&
        class_name.find("freetype/FreeType") != std::string::npos) {
        static thread_local uint64_t w18ft_in_n = 0;
        if (w18ft_in_n++ < 60)
            std::cerr << "[W18-FT-STATIC] entry " << class_name << "."
                      << method_name << " method_idx=" << method_idx
                      << " dex=" << current_dex_index_
                      << " proto="
                      << (dex_report_
                              ? resolve_method_proto_for_dex(method_idx,
                                                             current_dex_index_)
                              : std::string("<no-report>"))
                      << std::endl;
    }

    // EXP-071 Phase 8: Wide register merging.
    //
    // For methods with wide arguments (J = long, D = double), each wide arg
    // occupies TWO consecutive register slots in the Dalvik register file.
    // Without merging, `invoke-static {v3, v0, v1}, runOnUIThread(Runnable, J)`
    // would push 3 args (v3=Runnable, v0=low32, v1=high32) instead of 2
    // (Runnable, long). This breaks HandlerShadow's delay extraction
    // because args[1] is a low-half INT32 instead of an INT64 long.
    //
    // Fix: parse the method descriptor and merge wide register pairs into
    // single INT64/FLOAT64 DalvikValues. The descriptor is the (Ljava/lang/Runnable;J)V
    // string from the DEX method_id table; we walk the parameter types left
    // to right, consuming registers from the regs[] array in order.
    std::string method_proto = "<unknown>";
    if (dex_report_) {
        method_proto = resolve_method_proto_for_dex(method_idx, current_dex_index_);
    }
    // EXP-082: Debug trace for $r8$lambda invoke-static
    if (diag_env("MINIANDROID_EXP082_TRACE") && (method_name.find("$r8$lambda") != std::string::npos || method_name.find("createView") != std::string::npos)) {
        std::cerr << "[EXP082-STATIC] method=" << method_name
                  << " method_idx=" << method_idx
                  << " dex=" << current_dex_index_
                  << " proto=" << method_proto
                  << " argc=" << (int)argc
                  << std::endl;
    }

    // Parse the parameter list inside the parens.
    // Format: "(Ljava/lang/Runnable;J)V" → params = ["Ljava/lang/Runnable;", "J"]
    std::vector<std::string> param_types;
    if (method_proto != "<unknown>") {
        size_t lp = method_proto.find('(');
        size_t rp = method_proto.find(')');
        if (lp != std::string::npos && rp != std::string::npos && rp > lp) {
            std::string params = method_proto.substr(lp + 1, rp - lp - 1);
            size_t i = 0;
            while (i < params.size()) {
                char c = params[i];
                if (c == 'L') {
                    size_t semi = params.find(';', i);
                    if (semi == std::string::npos) break;
                    param_types.push_back(params.substr(i, semi - i + 1));
                    i = semi + 1;
                } else if (c == '[') {
                    // Array — keep eating [ until non-[
                    size_t start = i;
                    while (i < params.size() && params[i] == '[') i++;
                    if (i < params.size() && params[i] == 'L') {
                        size_t semi = params.find(';', i);
                        if (semi == std::string::npos) break;
                        param_types.push_back(params.substr(start, semi - start + 1));
                        i = semi + 1;
                    } else {
                        param_types.push_back(params.substr(start, i - start + 1));
                        i += 1;
                    }
                } else {
                    // Primitive — single char (B C D F I J S Z V)
                    param_types.push_back(std::string(1, c));
                    i += 1;
                }
            }
        }
    }

    // Walk params, consuming registers from regs[]. Each wide param (J or D)
    // consumes TWO register slots; otherwise one.
    size_t reg_idx = 0;
    for (size_t p = 0; p < param_types.size() && reg_idx < 5 && (int)reg_idx < argc; ++p) {
        const std::string& pt = param_types[p];
        if (pt == "J" || pt == "D") {
            // Wide: this register pair holds a 64-bit value.
            DalvikValue lo = get_register(regs[reg_idx]);
            if (lo.type == DalvikType::INT64) {
                // Case 1: low register already holds the full INT64 (set by const-wide/*).
                if (pt == "J") {
                    args.push_back(lo);
                } else {
                    double d;
                    int64_t bits = lo.long_val;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                }
            } else if (lo.type == DalvikType::FLOAT64) {
                args.push_back(lo);
            } else if (reg_idx + 1 < 5) {
                // Case 2: merge two registers (split wide value).
                DalvikValue hi = get_register(regs[reg_idx + 1]);
                int64_t combined = (static_cast<int64_t>(hi.int_val) << 32) |
                                   (static_cast<uint32_t>(lo.int_val));
                if (pt == "J") {
                    args.push_back(DalvikValue::make_long(combined));
                } else {
                    double d;
                    int64_t bits = combined;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                }
            } else {
                // GP-INT-001 (issue #582): a wide param starting at the 5th
                // 35c slot cannot have a second encoded word (regs is the
                // 5-slot local array; the pre-fix code read regs[5] — one
                // past the end, stack garbage). Verifier-valid DEX cannot
                // encode it (the pair needs 6 registers); treat as a
                // malformed-invoke face: loud, hi = 0, no OOB.
                static thread_local uint64_t gp_int001_n = 0;
                if (gp_int001_n++ < 8)
                    std::cerr << "[GP-INT-001] invoke-static wide param at "
                                 "slot 4 has no second encoded register — "
                                 "malformed 35c args (hi=0)"
                              << std::endl;
                if (pt == "J") {
                    args.push_back(DalvikValue::make_long(
                        static_cast<int64_t>(static_cast<uint32_t>(
                            get_register(regs[reg_idx]).int_val))));
                } else {
                    args.push_back(DalvikValue::make_double(0.0));
                }
            }
            reg_idx += 2;
        } else {
            DalvikValue v = get_register(regs[reg_idx]);
            // EXP-095 (CM-019): signature-aware FLOAT conversion.
            // For 'F' params the register holds raw float BITS as INT32
            // (e.g. const/high16 v1, 0x42400000 loads 48.0f as raw bits —
            // const opcodes are not float-typed). Per the method signature
            // we reinterpret: LayoutHelper.createFrame(IF) previously
            // delivered height=0x42400000=1111490560 instead of 48.
            if (pt == "F" && v.type == DalvikType::INT32) {
                float f;
                int32_t bits = v.int_val;
                std::memcpy(&f, &bits, sizeof(f));
                args.push_back(DalvikValue::make_float(f));
            } else if (v.type == DalvikType::INT32) {
                // ROOT-1 (GAME-185 #608) — signature-aware primitive retyping
                // in the INLINE packer: DEX registers are untyped; the proto's
                // param char is the only authority. The shared build_invoke_args
                // carries this law (CHAR-PROBE campaign), but this inline packer
                // handled only 'F' — so kotlin's split(delimiter: Char) lowered
                // to invoke-static String.valueOf(char) received INT32 44 and
                // produced "44" instead of ",". dk.cocode.chess: 0 of 9,000 CSV
                // rows ever split; every parseLine collapsed to one column and
                // the puzzle repository stayed empty ("No puzzles available").
                // Same register word, proto-char authority: C→CHAR, Z→BOOLEAN,
                // B→BYTE, S→SHORT.
                switch (pt.empty() ? 'I' : pt[0]) {
                    case 'C': {
                        DalvikValue c = v;
                        c.type = DalvikType::CHAR;
                        c.int_val &= 0xFFFF;
                        args.push_back(c);
                        break;
                    }
                    case 'Z':
                        args.push_back(DalvikValue::make_bool(v.int_val != 0));
                        break;
                    case 'B': {
                        DalvikValue b = v;
                        b.type = DalvikType::BYTE;
                        b.int_val = static_cast<int8_t>(v.int_val & 0xFF);
                        args.push_back(b);
                        break;
                    }
                    case 'S': {
                        DalvikValue s = v;
                        s.type = DalvikType::SHORT;
                        s.int_val = static_cast<int16_t>(v.int_val & 0xFFFF);
                        args.push_back(s);
                        break;
                    }
                    default:
                        args.push_back(v);
                        break;
                }
            } else {
                args.push_back(v);
            }
            reg_idx += 1;
        }
    }
    // If we couldn't parse params (proto unavailable), fall back to old behavior.
    if (param_types.empty() && args.empty()) {
        for (int i = 0; i < argc && i < 5; ++i) {
            args.push_back(get_register(regs[i]));
        }
    }

    // EXP-088+ F4: Trace invoke-static for $default$ methods (desugared interface defaults)
    // to verify overload resolution and arg count correctness.
    if (diag_env("MINIANDROID_EXP088_TRACE") && method_name.find("$default$") != std::string::npos) {
        std::cerr << "[EXP088-F4-STATIC] method=" << method_name
                  << " class=" << class_name
                  << " proto=" << method_proto
                  << " method_idx=" << method_idx
                  << " current_dex=" << current_dex_index_
                  << " argc=" << (int)argc
                  << " args_size=" << args.size()
                  << " caller=" << current_class_ << "." << current_method_
                  << " pc=" << pc;
        for (size_t i = 0; i < args.size() && i < 4; ++i) {
            std::cerr << " arg[" << i << "]=" << (int)args[i].type;
            if (args[i].type == DalvikType::OBJECT_REF) std::cerr << "/obj=" << args[i].object_id;
        }
        // Also try resolving with ALL DEX files to find the correct proto
        for (uint32_t di = 0; di < per_dex_raw_data_.size(); di++) {
            std::string alt_proto = resolve_method_proto_for_dex(method_idx, di);
            if (alt_proto != "<unknown>" && alt_proto != method_proto) {
                std::cerr << " alt_proto[DEX" << di << "]=" << alt_proto;
            }
        }
        std::cerr << std::endl;
    }

    // EXP-063: Trace invoke-static for getString
    if (dex_report_) {
        std::string mn = resolve_method_name_for_dex(method_idx, current_dex_index_);
        if (mn == "getString") {
            std::string cn = resolve_method_class_for_dex(method_idx, current_dex_index_);
            std::cerr << "[EXP063-ISTATIC] getString"
                      << " instr=0x" << std::hex << instr << std::dec
                      << " argc=" << (int)argc
                      << " regs[0]=" << (int)regs[0]
                      << " class=" << cn
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc;
            if (!args.empty()) {
                std::cerr << " arg0=" << args[0].int_val;
            } else {
                std::cerr << " NO_ARGS";
            }
            std::cerr << std::endl;
        }
    }

    // EXP-071 Phase 8: Trace runOnUIThread specifically to verify wide-arg merging.
    if (method_name == "runOnUIThread" || method_name == "executeOnUIThread") {
        std::cerr << "[EXP071-RUNONUI] class=" << class_name
                  << " method=" << method_name
                  << " argc=" << (int)argc
                  << " args_count=" << args.size()
                  << " proto=" << method_proto;
        for (size_t i = 0; i < args.size(); ++i) {
            std::cerr << " arg[" << i << "]=";
            switch (args[i].type) {
                case DalvikType::OBJECT_REF:
                    std::cerr << "obj#" << args[i].object_id
                              << "(" << args[i].class_desc << ")";
                    break;
                case DalvikType::INT64:
                    std::cerr << "long=" << args[i].long_val;
                    break;
                case DalvikType::INT32:
                    std::cerr << "int=" << args[i].int_val;
                    break;
                default:
                    std::cerr << "<other>";
                    break;
            }
        }
        std::cerr << std::endl;
    }
    
    // Common static methods we might recognize (legacy hint — now used only
    // for routing hints when the API bridge falls through).
    if (class_name.find("Log") != std::string::npos) {
        if (args.size() > 0 && args[0].type == DalvikType::INT32) {
            // args[0].int_val is the Log level: 5=warn, 6=error, etc.
            // (Just a hint; method_name from DEX is authoritative.)
        }
    }

    // API bridge
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

    // ────────────────────────────────────────────────────────────────────
    // R-NEW-350 (S43) — java.lang.Class.forName OVERLOAD LAW (host-class
    // dispatch at the interpreter level, BEFORE the recursive-invoke /
    // bridge layers — same pre-emption pattern as the R-NEW-347
    // View.measure law, which had to be placed before a silent-void
    // shadow handler).
    //
    // OpenJDK/AOSP law (java.lang.Class, java.lang.ClassLoader):
    //   forName(String name)
    //   forName(String name, boolean initialize, ClassLoader loader)
    //   → resolves `name` against the CALLER'S classloader domain and,
    //     when initialize=true, RUNS the class <clinit> before returning
    //     the Class object. Unknown name → ClassNotFoundException.
    //
    // Engine mapping: our authoritative classloader domain is the APK DEX
    // (class_info_index_ over dex_report_->classes); the dotted binary
    // name maps to the L-descriptor form; make_class returns the CLASS_REF
    // whose referent_desc every downstream const-class law reads.
    //
    // Real demand (dooz23, PRIORITY-1): protobuf-javalite
    // GeneratedMessageLite.getDefaultInstance(Class) — DEX Lbc0;.d — does
    //   defaultInstanceMap.get(clazz) == null
    //   → Class.forName(clazz.getName(), true, clazz.getClassLoader())
    //   → defaultInstanceMap.get(clazz)   // now registered by <clinit>
    // The 3-arg call was swallowed BEFORE the bridge (zero bridge logs,
    // zero CNFE, silent void) so the <clinit> never ran, the second get
    // stayed null, dynamicMethod(GET_DEFAULT_INSTANCE) answered null and
    // the bare IllegalStateException killed the DataStore theme read →
    // RuntimeException "Unable to get message info for y81" →
    // MainActivity.onCreate died before composition (S43 baseline,
    // crash.log chain 1; R350-FN2 trace proved interpreter dispatch at
    // idx=6825 with no bridge arrival).
    // ────────────────────────────────────────────────────────────────────
    // ENABLING GATE (S43 evidence-driven): with this law unconditionally
    // ON, microtimer's Room initDb loop (MainActivity.onCreate re-visited
    // the SAME forName invoke 50k×, HALT-LOOP guard) starved the run
    // budget → white frame + battery corpus-stage regression (A/B-proven:
    // stash→rebuild→run restored microtimer's 1,042,368-nonwhite render;
    // unstash→re-run reproduced the blank). The dooz23 protobuf chain
    // REQUIRES the law (UOE → asSubclass chain). Resolution: the law is
    // DEFAULT-OFF (S42 bridge behavior for every app); evidence runs
    // enable it explicitly with MINIANDROID_R350_LAW=1. Next-session
    // root: why microtimer's getGeneratedImplementation retries under
    // interpreter-level resolution but proceeded under bridge-level.
    // ────────────────────────────────────────────────────────────────────
    // R-NEW-354 (S44) — FRAMEWORK-CLASS REGISTRY LAW (Class.forName
    // fallthrough to the engine's own framework surface).
    //
    // AOSP law (java.lang.Class, java.lang.ClassLoader): forName resolves
    // against the FULL classpath — the boot classpath (framework classes)
    // FIRST, then the app classloader. A mini-Android owns a framework
    // surface; a name absent from the app DEX but present in that surface
    // must answer a Class object, not a ClassNotFoundException.
    //
    // Real demand (dooz23, PRIORITY-1, S44 evidence): compose-ui 1.11.4
    // AndroidComposeView.onAttachedToWindow (DEX Lt4;, pc 84-198) runs the
    // AOSP StrictMode block: StrictMode.getVmPolicy → Class.forName(
    // "android.os.SystemProperties") → getDeclaredMethod("addChangeCallback")
    // → invoke + setVmPolicy round-trip. On the engine the forName threw a
    // deferred CNFE, the attach method derailed, the deferred compose
    // request (Lt4;->n0, stored by setOnReadyForComposition) was never
    // consumed (pc 640-662), the composition never bootstrapped
    // (Lf90;.i never dispatched), AndroidComposeView measured 0x0 with
    // zero children, and the frame stayed blank AFTER R-NEW-353 had
    // already unblocked the protobuf schema build.
    //
    // GENERIC (zero class hacks): the registry holds framework classes the
    // engine's shadow surface genuinely models. Reflection into them rides
    // the M4 F-029 record laws: getDeclaredMethod mints a Method record for
    // any name, invoke dispatches back through the bridge (an unanswered
    // shadow method yields null — the callback simply never fires, which is
    // AOSP-exact for a runtime with no property daemon). Registry answers
    // are deterministic (no app-DEX retry interaction → no R-NEW-352-class
    // HALT-LOOP risk) so the law is DEFAULT-ON, independent of the
    // MINIANDROID_R350_LAW gate that guards APP-class resolution.
    // ────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/lang/Class;" &&
        method_name == "forName" &&
        !args.empty() && args[0].type == DalvikType::STRING_REF) {
        static const char* kFrameworkClasses[] = {
            "android.os.SystemProperties",
            // F-NEW-526: hidden-but-real framework class —
            // shizuku-style reflective service holders probe it
            // in <clinit> (py7.a evidence: forName CNF swallowed
            // by the clinit catch left getService Method null ->
            // NPE at the later getService.invoke). AOSP: forName
            // succeeds on every device.
            "android.os.ServiceManager",
        };
        const std::string& fw_name = args[0].string_val;
        for (const char* fw : kFrameworkClasses) {
            if (fw_name == fw) {
                std::string fw_desc = fw;
                for (char& c : fw_desc)
                    if (c == '.') c = '/';
                fw_desc = "L" + fw_desc + ";";
                std::cerr << "[R354-FORNAME] \"" << fw_name
                          << "\" -> framework registry " << fw_desc
                          << std::endl;
                return_val = DalvikValue::make_class(fw_desc,
                                                     instruction_sequence_);
                last_invoke_return_ = return_val;
                status = ApiCallTrace::Status::IMPLEMENTED;
                // R-NEW-355: pc-advance contract — 35c invoke = 3 units.
                pc_ = pc + 3;
                return true;
            }
        }
    }

    // S58 (R-NEW-352 CLOSED): DEFAULT-ON. The recorded blocker — microtimer's
    // Room initDb loop re-visiting the SAME forName invoke 50k× and starving
    // the run budget (A/B-proven S43) — was the MISSING PC-ADVANCE CONTRACT,
    // root-caused and fixed at S44 (R-NEW-355): every forName exit below now
    // advances pc_ past the 35c invoke before returning. S58 A/B re-proof at
    // the fixed HEAD: microtimer law-ON vs law-OFF are PIXEL-IDENTICAL
    // (1,041,437 non-white both; rc=0; HALT-LOOP 0; exactly 2 forName
    // resolutions — no retry storm; run/s58_r352_lawON vs s58_r352_lawOFF).
    // MINIANDROID_R350_LAW=0 is preserved as an explicit opt-out for A/B
    // hygiene runs.
    static thread_local const bool r350_law_off =
        std::getenv("MINIANDROID_R350_LAW") != nullptr &&
        std::getenv("MINIANDROID_R350_LAW")[0] == '0';
    static thread_local const bool r350_law_on = !r350_law_off;
    if (r350_law_on && class_name == "Ljava/lang/Class;" &&
        method_name == "forName") {
        // R-NEW-350 diagnostic: the 3-arg call's name argument may arrive
        // in a non-STRING_REF register shape — log every forName arg
        // vector (env-gated) so the shape is on record.
        {
            static thread_local const bool r350shape =
                diag_env("MINIANDROID_R350_TRACE");
            static thread_local uint64_t r350shape_n = 0;
            if (r350shape && r350shape_n < 40) {
                ++r350shape_n;
                std::cerr << "[R350-SHAPE] forName argc=" << args.size();
                for (size_t si = 0; si < args.size() && si < 3; ++si)
                    std::cerr << " a" << si << "k" << (int)args[si].type;
                std::cerr << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }
    if (r350_law_on && class_name == "Ljava/lang/Class;" &&
        method_name == "forName" &&
        !args.empty() && args[0].type == DalvikType::STRING_REF) {
        // dotted binary name → L-descriptor (ordinary classes only; the
        // deterministic subset documented in FIX-M3-012b).
        const std::string& want_name = args[0].string_val;
        std::string want_desc;
        if (!want_name.empty() && want_name[0] != '[') {
            bool r350_ordinary = true;
            for (char c : want_name) {
                if (!(c == '.' || c == '/' ||
                      (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                      (c >= '0' && c <= '9') || c == '_' || c == '$')) {
                    r350_ordinary = false;
                    break;
                }
            }
            if (r350_ordinary) {
                want_desc = want_name;
                for (char& c : want_desc)
                    if (c == '.') c = '/';
                want_desc = "L" + want_desc + ";";
            }
        }
        auto r350_cit =
            want_desc.empty()
                ? class_info_index_.end()
                : class_info_index_.find(want_desc);
        if (r350_cit == class_info_index_.end()) {
            // S84 (F-NEW-160): framework-class bridge. On a real device
            // Class.forName NEVER throws ClassNotFoundException for a
            // framework/OpenJDK class the platform ships (AOSP
            // Class.forName → BootClassLoader lookup). MiniAndroid's DEX
            // class_info_index_ only covers APK classes, so framework
            // names (android.os.Build$VERSION — hit by 9/50 S84 titles)
            // fell through to CNFE although the engine models their
            // statics (seed table). A/B law (S84, foehnix.widget):
            // bridge ONLY pure-data holder classes — instantiable engine
            // artifacts (dalvik.system.CloseGuard) returned as Class
            // objects pushed apps into Class.getMethod/Method.invoke
            // recursion storms (RECURSION-LIMIT frame-drop cascade,
            // L2→L0 regression), so they STAY on the CNFE path that real
            // app catches handle gracefully. Members later ride the
            // normal shadow / unknown-API paths.
            static const std::array<const char*, 4> r350_fw_classes = {
                "Landroid/os/Build;",
                "Landroid/os/Build$VERSION;",
                "Landroid/os/Build$VERSION_CODES;",
                "Ljava/lang/Thread;",
            };
            bool r350_is_fw =
                std::find_if(r350_fw_classes.begin(), r350_fw_classes.end(),
                             [&](const char* c) { return want_desc == c; }) !=
                r350_fw_classes.end();
            if (r350_is_fw) {
                return_val = DalvikValue::make_class(want_desc,
                                                     instruction_sequence_);
                last_invoke_return_ = return_val;
                status = ApiCallTrace::Status::IMPLEMENTED;
                pc_ = pc + 3;  // R-NEW-355 pc-advance contract
                return true;
            }
            // ── R350-DEXPATH (NOTEPAD-GAP wave 4): ART's forName resolves
            // against the FULL classpath — the APK's OWN shipped classes
            // included. The old law answered CNFE for every non-whitelisted
            // name, so androidx DataStore's protobuf-lite schema factory
            // (Class.forName("…protobuf.ExtensionSchemaFull") family —
            // reflective schema lookup by design, NOT strippable by R8)
            // failed every read, NotepadActivity's preference-gated
            // setContentView never ran, and the window captured a blank
            // theme background. Law: a forName whose L-descriptor exists in
            // the loaded DEX class index answers a REAL class token,
            // initialized per the 3-arg initialize flag (ART semantics).
            if (!class_info_index_.empty() &&
                class_info_index_.find(want_desc) != class_info_index_.end()) {
                const bool r350_dx_init =
                    args.size() >= 2 && args[1].type == DalvikType::INT32 &&
                    args[1].int_val != 0;
                if (r350_dx_init) ensure_class_initialized(want_desc);
                std::cerr << "[R351-FORNAME-DEX] \"" << want_name
                          << "\" → APK classpath class token" << std::endl;
                return_val = DalvikValue::make_class(want_desc,
                                                     instruction_sequence_);
                last_invoke_return_ = return_val;
                status = ApiCallTrace::Status::IMPLEMENTED;
                pc_ = pc + 3;
                return true;
            }
            // Real law: unknown class → ClassNotFoundException (deferred —
            // the DEX catch at the call site must observe it).
            // ISSUE-617-FORNAME-BOOTSTRAP (Minos wave): ART's forName NEVER
            // throws for a BOOTSTRAP-CLASSPATH class — android.util.Log,
            // android.view.*, org.json.*, etc. are always present on
            // device. The old law answered CNFE for every non-whitelisted
            // framework name; live face (de.tcrass.minos): greenrobot
            // EventBus's AndroidLogger.<clinit> probes
            // Class.forName("android.util.Log") to select the log backend
            // and got a deferred CNFE (R350-FORNAME) instead of a class
            // token. Law: any name in a bootstrap namespace (android.,
            // androidx., dalvik., java., javax.) answers a REAL class
            // token (3-arg initialize flag honored, R-NEW-355 pc-advance
            // kept) — member access later rides the normal shadow /
            // unknown-API paths, exactly like the whitelist above.
            {
                const bool r350_bootstrap_ns =
                    want_name.rfind("android.", 0) == 0 ||
                    want_name.rfind("androidx.", 0) == 0 ||
                    want_name.rfind("dalvik.", 0) == 0 ||
                    want_name.rfind("java.", 0) == 0 ||
                    want_name.rfind("javax.", 0) == 0;
                if (r350_bootstrap_ns) {
                    const bool r350_bs_init =
                        args.size() >= 2 && args[1].type == DalvikType::INT32 &&
                        args[1].int_val != 0;
                    if (r350_bs_init) ensure_class_initialized(want_desc);
                    static thread_local uint64_t r350_bs_n = 0;
                    if (r350_bs_n < 16) {
                        ++r350_bs_n;
                        std::cerr << "[R350-FORNAME-BOOTSTRAP] \"" << want_name
                                  << "\" → framework classpath class token"
                                  << std::endl;
                    }
                    return_val = DalvikValue::make_class(
                        want_desc, instruction_sequence_);
                    last_invoke_return_ = return_val;
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    pc_ = pc + 3;
                    return true;
                }
            }
            std::cerr << "[R350-FORNAME] \"" << want_name
                      << "\" → ClassNotFoundException" << std::endl;
            throw_deferred("Ljava/lang/ClassNotFoundException;",
                           want_name, "R350-FORNAME");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return_val = DalvikValue::make_null();
            last_invoke_return_ = return_val;
            // R-NEW-355 (S44): INVOKE PC-ADVANCE CONTRACT — every early
            // return from execute_invoke_static must advance pc_ past the
            // 35c invoke (3 code units). The missing advance re-executed
            // the SAME forName invoke forever: the S43 "R-NEW-352 retry
            // loop" (microtimer 50001 re-visits → HALT-LOOP) and the S44
            // SystemProperties loop (50001 re-visits → HALT-LOOP) were
            // THIS contract violation, not app-level retries. The normal
            // path at the function tail already does pc_ = pc + 3.
            pc_ = pc + 3;
            return true;
        }
        // initialize flag: 2-arg and 3-arg overloads both carry it in
        // args[1] (boolean shares the INT32 register slot).
        const bool r350_init =
            args.size() >= 2 && args[1].type == DalvikType::INT32 &&
            args[1].int_val != 0;
        if (r350_init) {
            ensure_class_initialized(want_desc);
        }
        // The returned Class object rides the invoke return path
        // (return_val → move-result-object at the call site).
        // W8 (F-NEW-511a): STABLE CLASS-TOKEN IDENTITY LAW for Class.forName
        // (same defect F-NEW-249 fixed for Object.getClass): make_class
        // stamped ref_id = instruction_sequence_ — a monotonic COUNTER,
        // not a heap id — and the CLASS_REF→shadow-arg conversion carries
        // that counter as object_id, ALIASING an arbitrary live heap object.
        // Live face (W8 survivalmanual): forName tokens aliased heap ids 24/
        // 45/66/87 (PackageManager owned 24) → the androidx.startup HashSet
        // stored "Class<KotprefInitializer>" backed by a foreign object.
        return_val = make_stable_class_token(want_desc);
        last_invoke_return_ = return_val;
        status = ApiCallTrace::Status::IMPLEMENTED;
        // R-NEW-350 log cap: microtimer's Room init calls Class.forName
        // ~50k times (Database_Impl reflection loop); an unbounded log
        // line per call turned the law into an I/O bottleneck that
        // starved the run budget (S43 sweep evidence). Log the first 16
        // resolutions only — the law itself always executes.
        {
            static thread_local uint64_t r350_ok_n = 0;
            if (r350_ok_n < 16) {
                ++r350_ok_n;
                std::cerr << "[R350-FORNAME] \"" << want_name << "\" -> "
                          << want_desc << " (initialized=" << r350_init
                          << ")" << std::endl;
            }
        }
        // R-NEW-355: pc-advance contract (see the CNFE exit above) — the
        // missing advance made every gated forName an in-place spin.
        pc_ = pc + 3;
        return true;
    }

    // ── #371 CLOSEOUT: JVMS 5.5 / AOSP ClassLinker::EnsureInitialized law
    // ── the first ACTIVE USE of a class triggers initialization, and
    // invoke-static IS an active use. sget/sput/new-instance already
    // ensured this; a class first touched via static-method invocation ran
    // uninitialized (S-2 evidence: NativeProbe.<clinit> — the canonical
    // System.loadLibrary-in-static-init pattern — never executed, so the
    // native library never loaded and every native call failed softly 0).
    // ensure_class_initialized early-exits on the already-initialized set,
    // so the per-call cost is one hash lookup.
    if (!class_name.empty() && class_name[0] == 'L')
        ensure_class_initialized(class_name);

    // EXP-038 (BLOCKER-034): Try recursive invocation.
    bool recursively_invoked = false;
    // EXP-063: Intercept getString(String, int) before recursive invoke.
    if (config_.enable_api_bridge &&
        method_name == "getString" &&
        class_name.find("LocaleController") != std::string::npos &&
        args.size() >= 1 && args[0].type == DalvikType::STRING_REF) {
        std::string res_name = args[0].string_val;
        if (!res_name.empty()) {
            auto it = resource_string_values_.find(res_name);
            if (it != resource_string_values_.end()) {
                std::cerr << "[RES] getString name=" << res_name << " val=" << it->second << std::endl;
                return_val = DalvikValue::make_string(it->second, 0);
                last_invoke_return_ = return_val;
                recursively_invoked = true;
                status = ApiCallTrace::Status::IMPLEMENTED;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is already false (reset above).
        // S188-W18 FT PROBE: FreeType-family static dispatch — did
        // try_recursive_invoke claim it, and as what?
        static thread_local const bool w18ft_d_on =
            std::getenv("MINIANDROID_W18_FT_TRACE") != nullptr;
        bool w18ft_probe = w18ft_d_on &&
            class_name.find("freetype/FreeType") != std::string::npos;
        static thread_local uint64_t w18ft_d_n = 0;
        if (w18ft_probe && w18ft_d_n++ < 200)
            std::cerr << "[W18-FT-DISP] pre-RI " << class_name << "."
                      << method_name << " proto=" << method_proto << std::endl;
        if (try_recursive_invoke(class_name, method_name, args, return_val, result, method_proto)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
            if (w18ft_probe && w18ft_d_n < 220)
                std::cerr << "[W18-FT-DISP] RI-claimed ret_type="
                          << static_cast<int>(return_val.type)
                          << " val=" << (return_val.type == DalvikType::INT64
                                             ? (long long)return_val.long_val
                                             : (long long)return_val.int_val)
                          << std::endl;
        } else if (w18ft_probe && w18ft_d_n < 220) {
            std::cerr << "[W18-FT-DISP] RI-miss -> bridge" << std::endl;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is still true (set at top of execute_invoke_static).
        // try_shadow_dispatch inside bridge_to_api will see it and correctly
        // treat args[0] as the first parameter (not `this`).
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
        // ────────────────────────────────────────────────────────────────
        // F-NEW-326 (CONT-54): the framework-boundary static resolution
        // law. ART invoke-static resolution walks the FULL superclass
        // chain — INCLUDING past the DEX boundary into the framework — to
        // the class that actually declares the method (Dalvik spec: the
        // method must be declared in the referenced class or one of its
        // superclasses). Byte-level evidence (solitaire classes.dex):
        // five support-lib classes (DrawerLayout m@5133, NestedScrollView
        // m@5251, ActionMenuView m@7364, Toolbar m@8216, ar m@8737) carry
        // method_ids naming THEIR OWN class as the owner of
        // getChildMeasureSpec(III)I while NO class in the DEX declares it
        // (DrawerLayout's class_data jumps m@5124 -> m@5143 — the id is
        // undeclared); on a real device every such invoke resolves to the
        // framework ViewGroup.getChildMeasureSpec law. try_recursive_invoke
        // (exact local match + F-074/F-280 super-walk) only walks DEX
        // ancestors, and the first bridge dispatch keyed on the APP class
        // identity — a STUBBED typed-default answer with NO handler run.
        // Law: when (a) the named class IS a DEX class and (b) the first
        // dispatch ended STUBBED (the typed-default tail — side-effect-
        // free, so a retry cannot double-fire any handler), walk the
        // superclass chain past the DEX boundary (nearest framework
        // ancestor first, bounded 16 hops) and accept the first
        // IMPLEMENTED framework law. Otherwise the original STUBBED
        // answer stands — byte-identical to the pre-law behavior.
        // ────────────────────────────────────────────────────────────────
        if (status == ApiCallTrace::Status::STUBBED &&
            class_info_index_.find(class_name) != class_info_index_.end()) {
            std::string walk = class_name;
            for (int hop = 0; hop < 16; ++hop) {
                auto sup_it = class_to_superclass_.find(walk);
                if (sup_it == class_to_superclass_.end()) break;
                std::string sup = sup_it->second;
                if (sup.empty() || sup == "Ljava/lang/Object;") break;
                walk = sup;
                // DEX ancestors were already covered by the resolver's
                // own walk — the retry is for the FRAMEWORK boundary.
                if (class_info_index_.find(sup) != class_info_index_.end())
                    continue;
                ApiCallTrace::Status f326_st = ApiCallTrace::Status::STUBBED;
                DalvikValue f326_rv = DalvikValue::make_void();
                bridge_to_api(sup, method_name, args, f326_rv, f326_st,
                              method_idx);
                if (f326_st == ApiCallTrace::Status::IMPLEMENTED) {
                    static thread_local uint64_t f326_redispatch_n = 0;
                    if (f326_redispatch_n < 40) {
                        ++f326_redispatch_n;
                        std::cerr << "[F-NEW-326] static re-dispatch "
                                  << class_name << "." << method_name
                                  << " as " << sup
                                  << " (framework boundary)" << std::endl;
                    }
                    return_val = f326_rv;
                    last_invoke_return_ = f326_rv;
                    status = f326_st;
                    break;
                }
            }
        }
    }

    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = class_name + "." + method_name;
    }

    // R-NEW-339 temp probe: every invoke-static dispatched from
    // Lt4;.<init> (AndroidComposeView ctor) — trace which call yields a
    // null/void where an object was expected around the autofill fetch.
    if (current_class_ == "Lt4;" && current_method_ == "<init>") {
        static thread_local uint64_t t4probe = 0;
        if (t4probe < 120) {
            ++t4probe;
            std::cerr << "[T4PROBE] invoke-static " << class_name << "."
                      << method_name << " pc=" << pc
                      << " ret_type=" << static_cast<int>(return_val.type)
                      << " ret_oid=" << return_val.object_id
                      << " ret_cls=" << return_val.class_desc
                      << std::endl;
        }
    }

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_interface(uint32_t pc, InstructionTrace& trace,
                                                   DalvikExecutionResult& result) {
    // Similar to other invokes but for interface dispatch
    if (pc + 2 >= bytecode_.size()) return false;

    // ────────────────────────────────────────────────────────────────────
    // F-023 (EXP-071 Phase 7 completion — invoke-interface INSTANCE law):
    // execute_invoke_static/virtual/direct each SAVE + RESET + RESTORE
    // current_invoke_is_static_ at their boundary. invoke-interface is an
    // INSTANCE call form but was forgotten, so any ancestor window that had
    // left the flag true (e.g. a static-dispatched entry frame) leaked into
    // try_recursive_invoke's M3-19/F-017 active-cycle key construction —
    // the receiver's #object_id suffix was skipped for ALL
    // interface-dispatched methods. Same-class re-entrancy across different
    // instances (CombinedContext.get recursing over a CoroutineContext
    // chain) then collided into ONE key and was stubbed null mid-fold; the
    // null fed kotlin.coroutines plus → CombinedContext.<init>
    // checkNotNullParameter → the NPE that killed Compose composition
    // before the first frame (dooz M1/i.f).
    // Scope-guard restore covers every return path below.
    // ────────────────────────────────────────────────────────────────────
    const bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;
    struct IsStaticRestore {
        bool& flag; bool saved;
        ~IsStaticRestore() { flag = saved; }
    } is_static_restore{current_invoke_is_static_, saved_is_static};

    uint16_t instr = bytecode_[pc];
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    uint16_t method_idx = bytecode_[pc + 1];
    uint16_t regs_word = bytecode_[pc + 2];

    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)
    };

    std::vector<DalvikValue> args;
    for (int i = 0; i < argc && i < 5; ++i) {
        args.push_back(get_register(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for invoke-interface (35c).
    // See execute_invoke_virtual for the full rationale.
    // F-090i (R-NEW-322): hoisted proto — also the callee's exact descriptor
    // for the F-023 overload law at every DEX dispatch site below.
    std::string iface_proto;
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        iface_proto = mre.proto;
        if (iface_proto != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        } else {
            iface_proto.clear();
        }
    }

    // EXP-037 Phase B (BLOCKER-002 FIX): resolve method_idx via DexReport.
    std::string method_name = "<interface_method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<interface>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // ────────────────────────────────────────────────────────────────────────
    // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): UV-DISPATCH watch. The Compose
    // text painter (Lte1/Lod1) reaches the canvas ONLY as a Luv draw block
    // through Loc0.c — this is the APK's SINGLE Luv;->I dispatch site. Log
    // the receiver's runtime class per dispatch: answers WHICH draw blocks
    // actually run per frame (observed: only 20 of 82 D0 walk nodes reach
    // here; the text painter's I never fires). Env-gated, bounded — zero
    // behavior change.
    // ────────────────────────────────────────────────────────────────────────
    {
        static thread_local const bool uvw_on =
            diag_env("MINIANDROID_UV_WATCH");
        if (uvw_on && class_name == "Luv;" && method_name == "I") {
            static thread_local uint64_t uvw_n = 0;
            if (uvw_n++ < 400) {
                const char* uvw_t = "(noargs)";
                if (!args.empty()) {
                    if (args[0].type == DalvikType::OBJECT_REF)
                        uvw_t = args[0].class_desc.c_str();
                    else if (args[0].type == DalvikType::NULL_REF)
                        uvw_t = "NULL";
                    else
                        uvw_t = "other";
                }
                std::cerr << "[UV-DISPATCH] recv-cls=" << uvw_t
                          << " obj=" << (args.empty() ? 0u : args[0].object_id)
                          << " caller=" << current_class_ << "."
                          << current_method_;
                // CONT-37: dump the receiver's attached flag (Lok0.r) — the
                // painter body's first gate — plus the coordinator field (l)
                // identity, to answer whether attach state survived to draw.
                if (!args.empty() &&
                    args[0].type == DalvikType::OBJECT_REF) {
                    auto rf = heap_.get_object_field(args[0].object_id, "r");
                    auto lf = heap_.get_object_field(args[0].object_id, "l");
                    std::cerr << " r="
                              << (rf ? std::to_string(rf->bool_val)
                                     : std::string("?"))
                              << " l="
                              << (lf ? std::to_string(lf->object_id)
                                     : std::string("?"));
                }
                std::cerr << std::endl;
            }
        }
    }

    // ── S173 NDFE probe (interface path, env-gated, bounded 96) ─────────
    // Same evidence as the [S173-CHM-V] block in execute_invoke_virtual:
    // the Koin index (desugared j$ ConcurrentHashMap) may be reached
    // through an interface-typed slot (invoke-interface on Lj$/util/Map;).
    if (diag_env("MINIANDROID_S173_PROBE") &&
        class_name.find("ConcurrentHashMap") != std::string::npos &&
        (current_method_.find("resolveDefinition") != std::string::npos ||
         current_class_ == "Lorg/slf4j/event/EventRecodingLogger;")) {
        static thread_local uint64_t s173_chm_i = 0;
        if (s173_chm_i < 200 && args.size() >= 2 &&
            args[1].type == DalvikType::STRING_REF) {
            ++s173_chm_i;
            const std::string& keydesc = args[1].string_val;
            std::cerr << "[S173-CHM-I] " << method_name
                      << " argc=" << args.size()
                      << " key=\"" << keydesc << "\""
                      << " caller=" << current_class_ << "."
                      << current_method_ << " pc=" << pc << std::endl;
        }
    }

    // ── F-068 (R-NEW-292): RUNTIME-CLASS-FIRST interface dispatch law ─────
    // DEX invoke-interface dispatch: ART resolves the target against the
    // RECEIVER'S RUNTIME CLASS — the most specific implementation among
    // the class hierarchy and the interfaces it implements. The declared
    // interface in the method ref supplies only the SIGNATURE; a default
    // method body living on the declared interface executes ONLY when the
    // runtime class does not override it.
    // The old order tried the DECLARED interface first. For interfaces
    // WITH default bodies that shadows the receiver's real override:
    // androidx F$b (ViewModelProvider.Factory, R8) has a default
    // b(Class, CreationExtras) that delegates to a throwing a(Class)
    // ("Factory.create(String) is unsupported…"), while the actual
    // factory Lf1/b (the viewModelFactory{} initializer-lambda SAM)
    // overrides b(Class, extras). Dooz SavedStateHandlesVM.create went
    // through the throwing default → UnsupportedOperationException →
    // MainActivity.onCreate died at invoke_pc=109 → first frame died.
    // Runtime-first also honors the simple case: abstract interfaces miss
    // on the runtime class and fall through unchanged.
    DalvikValue return_val = DalvikValue::make_void();
    // F-141 (S72-W3): ART null-receiver law — invoke-interface with a null
    // receiver throws NPE at the call site (ART: "Attempt to invoke
    // interface method '<sig>' on a null object reference"). Previously
    // the dispatch walk ran with heap_obj = nullptr and silent null
    // semantics.
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke interface method '" + class_name +
                           "." + method_name + "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
    }
    // Resolve the receiver's heap object once for the whole dispatch walk.
    const auto* heap_obj =
        (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
         heap_.has_object(args[0].object_id))
            ? heap_.get(args[0].object_id)
            : nullptr;
    // ── F-068 (R-NEW-292): RUNTIME-CLASS-FIRST interface dispatch law ─────
    // DEX invoke-interface dispatch: ART resolves the target against the
    // RECEIVER'S RUNTIME CLASS — the most specific implementation among
    // the class hierarchy and the interfaces it implements. The declared
    // interface in the method ref supplies only the SIGNATURE; a default
    // method body living on the declared interface executes ONLY when the
    // runtime class does not override it.
    // The old order tried the DECLARED interface first. For interfaces
    // WITH default bodies that shadows the receiver's real override:
    // androidx F$b (ViewModelProvider.Factory, R8) has a default
    // b(Class, CreationExtras) that delegates to a throwing a(Class)
    // ("Factory.create(String) is unsupported…"), while the actual
    // factory Lf1/b (the viewModelFactory{} initializer-lambda SAM)
    // overrides b(Class, extras). Dooz SavedStateHandlesVM.create went
    // through the throwing default → UnsupportedOperationException →
    // MainActivity.onCreate died at invoke_pc=109 → first frame died.
    if (heap_obj && !heap_obj->class_descriptor.empty() &&
        heap_obj->class_descriptor != class_name) {
        // F-NEW-281c: EXACT (name, descriptor) gate on the runtime-class-
        // first arm. JVMS 5.4.3.4: a same-name different-proto method is
        // NEVER a candidate for an interface invoke. With a concrete call-
        // site proto, this arm may dispatch via try_recursive_invoke's
        // legacy lenient (name-only) selection — which let a same-name
        // WRONG-shape overload win BEFORE the interface-default search
        // could run. Live face (real-Compose oracle): Factory.create(
        // KClass, extras) dispatched InitializerViewModelFactory.create(
        // Class, extras) — the KClass flowed into the Class slot,
        // getKotlinClass re-wrapped it, and the initializer match failed
        // with IAE "No initializer set for given class null" → APP
        // BOUNDARY. Gate: when the proto is resolvable, the runtime class
        // chain must declare an EXACT (name, proto) non-abstract method
        // for this arm to fire; otherwise control proceeds to the
        // declared-interface and interface-hierarchy default search
        // (F-023 / F-NEW-281), which find the TRUE candidate. Empty proto
        // keeps the legacy behavior unchanged.
        bool f281c_exact = false;
        if (!iface_proto.empty() && dex_report_) {
            std::string f281c_cls = heap_obj->class_descriptor;
            for (int f281c_hop = 0;
                 f281c_hop < 8 && !f281c_cls.empty() && !f281c_exact;
                 ++f281c_hop) {
                for (const auto& cls : dex_report_->classes) {
                    if (cls.name != f281c_cls) continue;
                    for (const auto& mi : cls.all_methods()) {
                        // S188-W17 (F-NEW-601) native-exact law: an
                        // ACC_NATIVE method has code_offset==0 and is NOT
                        // abstract — it is a REAL dispatch target (AOSP
                        // art_method: entry points, not "no method").
                        // Live evidence (p9, /tmp/p9probe.log): the
                        // interface call GL20.glCreateShader(I)I on the
                        // AndroidGL20 receiver skipped this walk entirely
                        // (native skipped by code_offset==0) →
                        // S186I-STUB answered 0 → ShaderProgram
                        // isCompiled=false → IllegalArgumentException
                        // "Error compiling shader" → APP BOUNDARY unwind
                        // before the first frame. An interface call whose
                        // runtime class declares a native with the EXACT
                        // name+descriptor is an EXACT hit; the native
                        // block in try_recursive_invoke runs it.
                        if (mi.is_abstract) continue;
                        if (mi.code_offset == 0 &&
                            !(mi.access_flags & 0x100))
                            continue;
                        if (mi.name != method_name) continue;
                        if (mi.descriptor == iface_proto) {
                            f281c_exact = true;
                            break;
                        }
                    }
                    break;  // found the class def
                }
                if (f281c_exact) break;
                auto f281c_sup = class_to_superclass_.find(f281c_cls);
                if (f281c_sup == class_to_superclass_.end()) break;
                f281c_cls = f281c_sup->second;
                if (f281c_cls == "Ljava/lang/Object;") break;
            }
        }
        // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): log the f281c gate result
        // for the draw-block dispatch (Luv;.I) — if the exact walk misses a
        // method that exists, the runtime-first arm is skipped and the
        // dispatch falls to the deeper fallbacks (observed: painter paint
        // dispatch never reaches the body).
        if (diag_env("MINIANDROID_UV_WATCH") && class_name == "Luv;" &&
            method_name == "I" &&
            (heap_obj->class_descriptor == "Lte1;" ||
             heap_obj->class_descriptor == "Lod1;")) {
            static thread_local uint64_t uvf_n = 0;
            if (uvf_n++ < 60)
                std::cerr << "[UV-F281C] recv=" << heap_obj->class_descriptor
                          << " obj=" << (args.empty() ? 0u : args[0].object_id)
                          << " proto=" << iface_proto
                          << " exact=" << (f281c_exact ? 1 : 0)
                          << std::endl;
        }
        if (f281c_exact || iface_proto.empty())
        // F-090i (R-NEW-322): pass the interface proto as the exact
        // descriptor so the F-023 overload law resolves same-name
        // overloads on the runtime class correctly.
        if (try_recursive_invoke(heap_obj->class_descriptor, method_name,
                                 args, return_val, result, iface_proto)) {
            // S59 R-NEW-379 DIAG: the runtime-first dispatch claims success
            // — surface the resolved class/method and the return shape so
            // silent typed-zero/void returns become visible.
            if (diag_env("MINIANDROID_IFACE_FAIL_TRACE")) {
                fprintf(stderr,
                        "[IFACE-RT] %s.%s%s via runtime %s (recv obj#%u) "
                        "ret_type=%d ret_id=%u ret_int=%d\n",
                        class_name.c_str(), method_name.c_str(),
                        iface_proto.c_str(),
                        heap_obj->class_descriptor.c_str(),
                        args.empty() ? 0u : args[0].object_id,
                        static_cast<int>(return_val.type), return_val.object_id,
                        return_val.type == DalvikType::INT32 ? return_val.int_val
                        : (return_val.type == DalvikType::BOOLEAN ? (return_val.int_val != 0 ? 1 : 0) : -1));
                // S59: dump the receiver's stored fields for empty returns
                // (Ljj;.a returned empty for every KClass — was the <init>
                // iput ever persisted?)
                if (return_val.type != DalvikType::OBJECT_REF) {
                    std::string fl;
                    for (const auto& [fn, fv] : heap_obj->fields) {
                        fl += fn + "(t" + std::to_string(static_cast<int>(fv.type)) +
                              ",id" + std::to_string(fv.object_id) + ") ";
                    }
                    fprintf(stderr, "[IFACE-RT]   recv fields: %s\n",
                            fl.c_str());
                }
            }
            last_invoke_return_ = return_val;
            // S157-B: trace_cap==0 gate (never-read trace).
            if (config_.trace_cap > 0) {
            trace.invoked_method =
                heap_obj->class_descriptor + "." + method_name;
            }
            pc_ = pc + 3;
            return true;
        }
    }
    // Declared-interface dispatch — executes default bodies on the
    // interface itself (F-023 semantics for non-overridden defaults) and
    // still catches the historical "interface methods with impls" cases.
    if (try_recursive_invoke(class_name, method_name, args, return_val, result,
                             iface_proto)) { last_invoke_return_ = return_val;
        // S157-B: trace_cap==0 gate (never-read trace).
        if (config_.trace_cap > 0) {
        trace.invoked_method = class_name + "." + method_name;
        }
        pc_ = pc + 3;
        return true;
    }
    if (heap_obj) {
        // ────────────────────────────────────────────────────────────────
        // M3 F-ROOM-CHAIN (R8 interface-dispatch law): R8 renames the
        // interface method and the implementation method INDEPENDENTLY
        // (e.g. interface Lg/h;->X(IJ)V is implemented as Le/x;->h(IJ)V).
        // A NAME lookup on the runtime class then misses and the call
        // silently degrades to a void stub — exactly how Room's
        // EntityInsertionAdapter.bind lost every parameter bind (insert →
        // NOT NULL constraint failed on microtimer's alarm table). DEX
        // dispatch law: renaming preserves parameter/return types, so when
        // the name lookup misses, resolve by EXACT signature (descriptor)
        // inside the receiver's runtime class and dispatch THAT method.
        // ────────────────────────────────────────────────────────────────
        // F-090i: iface_proto is hoisted above — reuse it here.
        if (!iface_proto.empty()) {
            // F-091b (R-NEW-324, S25): ART interface-dispatch gate on the
            // descriptor-only walk below. The walk is ONLY legal when the
            // declared interface is itself DEX-defined — the R8 case where
            // interface method and implementation are renamed INDEPENDENTLY
            // (the descriptor stays the stable identity). For HOST
            // interfaces (Ljava/util/Iterator;, Ljava/util/Collection;, …)
            // R8 cannot rename: the name IS the contract and the name-based
            // dispatch above is authoritative. Descriptor-guessing on a
            // host interface dispatches an UNRELATED method that merely
            // shares the proto — dooz proof: Iterator.hasNext() →
            // z1/i.isEmpty() (first ()Z on the chain) → hasNext()=false
            // for a NON-EMPTY list → addAll's bulk-copy zero-iterated →
            // the NavController back stack lost the root-graph entry
            // (R-NEW-323 IAE).
            bool f91b_dex_interface = false;
            if (!class_name.empty() && dex_report_) {
                for (const auto& f91b_cls : dex_report_->classes) {
                    if (f91b_cls.name == class_name) {
                        f91b_dex_interface = true;
                        break;
                    }
                }
            }
            if (f91b_dex_interface) {
            // F-NEW-281: ART invoke-interface resolution law (JVMS
            // 5.4.3.4): the candidate must match the (NAME, descriptor)
            // pair — a same-descriptor different-name method is NEVER a
            // candidate. The descriptor-only walk below is the R8
            // independent-rename FALLBACK and must run LAST.
            // Oracle proof of the gap: CompositionLocalAccessorScope.
            // getCurrentValue(local) on a PersistentCompositionLocalHashMap
            // receiver — the class declares no getCurrentValue, so the
            // descriptor walk picked the FIRST same-shape method, the raw
            // PersistentMap.get override (invoke-super + check-cast
            // ValueHolder + return), answering a ValueHolder where the
            // accessor law demands readValue()'s value; the real
            // implementation is the inherited interface DEFAULT
            // PersistentCompositionLocalMap.getCurrentValue = read(this)
            // (getOrElse(key){defaultValueHolder}.readValue(this)).
            // Order: (1) exact (name, descriptor) in the receiver's class
            // chain; (2) exact (name, descriptor) DEFAULT body in the
            // interface hierarchy (receiver interfaces, transitive,
            // bounded); (3) legacy descriptor-only walk (unchanged).
            bool f281_diag = diag_env("MINIANDROID_F281_TRACE");
            {
                std::string f281_walk = heap_obj->class_descriptor;
                for (int hop = 0; hop < 8 && !f281_walk.empty(); ++hop) {
                    for (const auto& cls : dex_report_->classes) {
                        if (cls.name != f281_walk) continue;
                        for (const auto& mi : cls.all_methods()) {
                            if (mi.code_offset == 0 || mi.is_abstract) continue;
                            if (mi.descriptor != iface_proto) continue;
                            if (mi.name != method_name) continue;
                            if (try_recursive_invoke(f281_walk, mi.name, args,
                                                     return_val, result)) {
                                last_invoke_return_ = return_val;
                                trace.invoked_method =
                                    f281_walk + "." + mi.name;
                                if (f281_diag)
                                    std::cerr << "[F281-IFACE-NAME] "
                                              << f281_walk << "." << mi.name
                                              << iface_proto
                                              << " (exact name+descriptor, class chain; call-site "
                                              << class_name << "." << method_name
                                              << ") → REAL DEX dispatched"
                                              << std::endl;
                                pc_ = pc + 3;
                                return true;
                            }
                        }
                        break;  // found the class def; stop scanning classes
                    }
                    auto sup_it = class_to_superclass_.find(f281_walk);
                    if (sup_it == class_to_superclass_.end()) break;
                    f281_walk = sup_it->second;
                    if (f281_walk == "Ljava/lang/Object;") break;
                }
            }
            {
                // (2) interface-hierarchy DEFAULT bodies, exact
                // (name, descriptor). BFS from the receiver's direct
                // interfaces through super-interfaces (bounded 16 levels).
                std::vector<std::string> f281_q;
                auto ifc_it = class_to_interfaces_.find(
                    heap_obj->class_descriptor);
                if (ifc_it != class_to_interfaces_.end())
                    f281_q = ifc_it->second;
                for (int level = 0; level < 16 && !f281_q.empty(); ++level) {
                    std::vector<std::string> f281_next;
                    for (const auto& ifc : f281_q) {
                        bool ifc_has_def = false;
                        for (const auto& cls : dex_report_->classes) {
                            if (cls.name != ifc) continue;
                            for (const auto& mi : cls.all_methods()) {
                                if (mi.code_offset == 0 || mi.is_abstract)
                                    continue;
                                if (mi.descriptor != iface_proto) continue;
                                if (mi.name != method_name) continue;
                                ifc_has_def = true;
                                if (try_recursive_invoke(ifc, mi.name, args,
                                                         return_val, result)) {
                                    last_invoke_return_ = return_val;
                                    trace.invoked_method = ifc + "." + mi.name;
                                    if (f281_diag)
                                        std::cerr << "[F281-IFACE-DEFAULT] "
                                                  << ifc << "." << mi.name
                                                  << iface_proto
                                                  << " (interface-hierarchy default; call-site "
                                                  << class_name << "."
                                                  << method_name
                                                  << ") → REAL DEX dispatched"
                                                  << std::endl;
                                    pc_ = pc + 3;
                                    return true;
                                }
                            }
                            break;  // found the interface def
                        }
                        if (!ifc_has_def) {
                            auto sup_ifc = class_to_interfaces_.find(ifc);
                            if (sup_ifc != class_to_interfaces_.end())
                                for (const auto& p : sup_ifc->second)
                                    f281_next.push_back(p);
                        }
                    }
                    f281_q = f281_next;
                }
            }
            // Walk the receiver's class + superclass chain (DEX virtual
            // dispatch law: inherited implementations answer interface
            // calls; R8 renames per class, so the signature is the only
            // stable identity).
            std::string walk_cls = heap_obj->class_descriptor;
            for (int hop = 0; hop < 8 && !walk_cls.empty(); ++hop) {
                bool cls_found = false;
                for (const auto& cls : dex_report_->classes) {
                    if (cls.name != walk_cls) continue;
                    cls_found = true;
                    bool sig_found = false;
                    for (const auto& mi : cls.all_methods()) {
                        if (mi.code_offset == 0 || mi.is_abstract) continue;
                        if (mi.descriptor != iface_proto) continue;
                        sig_found = true;
                        if (try_recursive_invoke(walk_cls, mi.name, args,
                                                 return_val, result)) {
                            last_invoke_return_ = return_val;
                            trace.invoked_method =
                                walk_cls + "." + mi.name +
                                " [sig-dispatch " + iface_proto + "]";
                            std::cerr << "[INTERFACE-SIG] " << walk_cls << "."
                                      << mi.name << iface_proto
                                      << " (interface " << class_name << "."
                                      << method_name << ") → REAL DEX dispatched"
                                      << std::endl;
                            pc_ = pc + 3;
                            return true;
                        }
                    }
                    if (sig_found) break;
                    break;  // found the class def; stop scanning classes
                }
                auto sup_it = class_to_superclass_.find(walk_cls);
                if (sup_it == class_to_superclass_.end()) break;
                walk_cls = sup_it->second;
                if (walk_cls == "Ljava/lang/Object;") break;
            }
            } // end F-091b DEX-interface gate

            // ────────────────────────────────────────────────────────────
            // F-023 (DEX DEFAULT-INTERFACE-METHOD DISPATCH LAW): the class
            // extends-walk cannot see methods that live ON an interface
            // with code (DEX default methods). ART law: invoke-interface
            // consults every transitively implemented interface of the
            // receiver, including default methods. Generic: collect the
            // implements-set of each class in the receiver's extends
            // chain, close it over super-interfaces (bounded), then
            // dispatch the method matching the EXACT descriptor with code.
            // (Real-APK evidence: AndroidUiFrameClock.getKey default —
            // CoroutineContext.plus NPE before first frame.)
            // ────────────────────────────────────────────────────────────
            // 1. Receiver extends-chain (bounded).
            std::vector<std::string> cls_chain;
            std::string c = heap_obj->class_descriptor;
            for (int hop = 0; hop < 12 && !c.empty() &&
                              c != "Ljava/lang/Object;"; ++hop) {
                cls_chain.push_back(c);
                auto it2 = class_to_superclass_.find(c);
                if (it2 == class_to_superclass_.end()) break;
                c = it2->second;
            }
            // 2. Implements-set with transitive super-interfaces.
            std::vector<std::string> ifq;
            std::set<std::string> visited;
            auto enqueue_ifaces = [&](const std::string& cls) {
                for (const auto& cd : dex_report_->classes) {
                    if (cd.name != cls) continue;
                    for (const auto& ifc : cd.interfaces) {
                        if (!ifc.empty() && visited.insert(ifc).second) {
                            ifq.push_back(ifc);
                        }
                    }
                    break;  // found the class def
                }
            };
            for (const auto& cc : cls_chain) enqueue_ifaces(cc);
            for (size_t qi = 0; qi < ifq.size() && qi < 64; ++qi) {
                enqueue_ifaces(ifq[qi]);  // super-interfaces
            }
            // 3. Dispatch a default method with the exact descriptor
            //    (code, non-abstract).
            for (const auto& ifc : ifq) {
                for (const auto& cd : dex_report_->classes) {
                    if (cd.name != ifc) continue;
                    for (const auto& mi : cd.all_methods()) {
                        if (mi.code_offset == 0 || mi.is_abstract) continue;
                        if (mi.descriptor != iface_proto) continue;
                        if (try_recursive_invoke(ifc, mi.name, args,
                                                 return_val, result,
                                                 iface_proto)) {
                            last_invoke_return_ = return_val;
                            trace.invoked_method =
                                ifc + "." + mi.name +
                                " [default-method " + iface_proto + "]";
                            std::cerr << "[INTERFACE-DEFAULT] " << ifc << "."
                                      << mi.name << iface_proto
                                      << " (interface " << class_name << "."
                                      << method_name << ") → REAL DEX dispatched"
                                      << std::endl;
                            pc_ = pc + 3;
                            return true;
                        }
                    }
                    break;  // found the interface def
                }
            }
        }
    }
    if (!heap_obj && !args.empty() && method_name == "addFragmentToStack") {
        // EXP-058: Debug — why is interface dispatch not working?
        int arg0_type = static_cast<int>(args[0].type);
        uint32_t arg0_obj = args[0].object_id;
        bool has_obj = heap_.has_object(arg0_obj);
        std::string heap_class = has_obj ? heap_.get(arg0_obj)->class_descriptor : "<no heap obj>";
        std::cerr << "[EXP058-IFACE] addFragmentToStack dispatch failed"
                  << " arg0_type=" << arg0_type
                  << " arg0_obj=" << arg0_obj
                  << " has_heap_obj=" << has_obj
                  << " heap_class=" << heap_class
                  << " static_class=" << class_name
                  << std::endl;
    }

    // S59 R-NEW-379 DIAG (env-gated): why did the interface dispatch end
    // at the bridge fallback? Logs the receiver identity and heap state
    // for every interface call that reached this point without a REAL DEX
    // dispatch (no runtime-class hit, no declared-interface body, no
    // signature/default-method walk success).
    if (diag_env("MINIANDROID_IFACE_FAIL_TRACE") &&
        !args.empty()) {
        const DalvikValue& r0 = args[0];
        std::string r0_heap = "<none>";
        if (r0.type == DalvikType::OBJECT_REF && r0.object_id != 0 &&
            heap_.has_object(r0.object_id)) {
            r0_heap = heap_.get(r0.object_id)->class_descriptor;
        }
        fprintf(stderr,
                "[IFACE-FAIL] %s.%s%s recv_type=%d recv_id=%u recv_tag=%s "
                "heap=%s\n",
                class_name.c_str(), method_name.c_str(), iface_proto.c_str(),
                static_cast<int>(r0.type), r0.object_id,
                r0.class_desc.c_str(), r0_heap.c_str());
    }

    // EXP-048: Fall through to bridge_to_api for interface methods
    // F-090d (R-NEW-318): the bridge key must be the RECEIVER'S RUNTIME
    // class — the same EXP-059 law execute_invoke_virtual already applies.
    // The declared interface supplies only the SIGNATURE; framework API
    // handlers are keyed by implementation classes. Live evidence (dooz):
    // `route.isNotBlank()` compiled to invoke-interface
    // CharSequence.length()/charAt() on a real String; bridging with
    // "Ljava/lang/CharSequence;" found no handler → length answered 0 →
    // isBlank=true → NavDestination.setRoute IAE "Cannot have an empty
    // route" → MainActivity.onCreate died → Compose never composed.
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;
    if (config_.enable_api_bridge) {
        std::string api_cls = class_name;
        if (heap_obj && !heap_obj->class_descriptor.empty()) {
            api_cls = heap_obj->class_descriptor;
        } else if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            // String constants ride STRING_REF without a heap object; the
            // runtime class of any CharSequence-typed constant is String.
            api_cls = "Ljava/lang/String;";
        } else if (!args.empty() &&
                   args[0].type == DalvikType::OBJECT_REF &&
                   !args[0].class_desc.empty()) {
            api_cls = args[0].class_desc;
        }
        bridge_to_api(api_cls, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
    }

    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));

    trace.invoked_method = class_name + "." + method_name;

    pc_ = pc + 3;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Returns
// ============================================================================

bool DalvikExecutionEngine::execute_return_void(uint32_t pc, InstructionTrace& trace) {
    // Format: 10x [op] {} (no operands)
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = DalvikValue::make_void();
    
    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN_VOID at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_return(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;
    
    DalvikValue val = get_register(ret_reg);
    
    // CHAR-PROBE campaign: signature-aware return typing. DEX registers are
    // untyped 32-bit cells — a boolean/char/byte/short return leaves the
    // register as raw INT32. Downstream consumers (StringBuilder.append,
    // string concat, ==/!= flows into text) then render "88" for 'X' or
    // "0"/"1" for false/true. Retype by the method's return-type descriptor
    // char, exactly per the Dalvik spec: only raw INT32 is reinterpreted;
    // already-typed values pass through untouched.
    if (val.type == DalvikType::INT32 &&
        current_method_descriptor_.size() >= 2) {
        size_t rparen = current_method_descriptor_.find(')');
        if (rparen != std::string::npos &&
            rparen + 1 < current_method_descriptor_.size()) {
            char rt = current_method_descriptor_[rparen + 1];
            switch (rt) {
                case 'Z':
                    val = DalvikValue::make_bool(val.int_val != 0);
                    break;
                case 'C':
                    val.type = DalvikType::CHAR;
                    val.int_val &= 0xFFFF;
                    break;
                case 'B':
                    val.type = DalvikType::BYTE;
                    val.int_val = static_cast<int8_t>(val.int_val & 0xFF);
                    break;
                case 'S':
                    val.type = DalvikType::SHORT;
                    val.int_val = static_cast<int16_t>(val.int_val & 0xFFFF);
                    break;
                default:
                    break;   // I/J/F/D/L/[/V — leave as-is
            }
        }
    }
    
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});
    
    // EXP-055: Store the return value so try_recursive_invoke can
    // propagate it to the caller. Previously, return_val was always
    // make_void() — so every recursive invoke returned void, and
    // move-result after an invoke always got 0/null. This caused
    // isClientActivated to return void (treated as false), which
    // happened to be correct for the login path but was fundamentally
    // broken for any method that returns a non-zero value.
    last_invoke_return_ = val;
    
    // EXP-059: Debug — log return values for onFragmentCreate and addFragmentToStack
    if (current_method_ == "onFragmentCreate" ||
        (current_method_ == "addFragmentToStack" &&
         current_class_.find("ActionBarLayout") != std::string::npos)) {
        std::cerr << "[EXP059-RETURN] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " ret_reg=v" << (int)ret_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << std::endl;
    }

    // F-044 DIAG (env-gated, diagnostic only): the live dooz derived-state
    // record-validity law (LF/F$a.c watermark/version check) mis-executes —
    // expose the exact DEX-level return values of the two law methods so the
    // comparison (record.g vs re-scanned dependency version) can be traced.
    {
        static thread_local const bool f044 = std::getenv("MINIANDROID_F044_DIAG") != nullptr;
        if (f044 && current_class_ == "LF/F$a;" && current_method_ == "d") {
            std::cerr << "[F044-DIAG] " << current_class_ << "." << current_method_
                      << "() return type=" << static_cast<int>(val.type)
                      << " int_val=" << val.int_val
                      << " obj=" << val.object_id
                      << std::endl;
            // One-shot register-file dump at return (capped at 3 dumps):
            // exposes every register's tag so the stale-tag source is exact.
            static thread_local uint64_t f044_dumps = 0;
            if (f044_dumps < 3 && current_registers_) {
                f044_dumps++;
                std::cerr << "[F044-DIAG] .d register file:";
                for (uint8_t ri = 0; ri < 23; ++ri) {
                    DalvikValue rv = current_registers_->read_v(ri);
                    if (rv.type == DalvikType::REGISTER_UNSET ||
                        rv.type == DalvikType::UNINITIALIZED) continue;
                    std::cerr << " v" << (int)ri << ":t" << static_cast<int>(rv.type)
                              << "(" << rv.int_val << ")";
                }
                std::cerr << std::endl;
            }
        }
        // SnapshotIdSet.contains (LP/j.q) — the record-walk invalidation
        // gate. A TRUE return on an empty set skips every record and makes
        // SnapshotKt.readable (P/l.r) return null inside the dependency
        // version scan while the same readable succeeds from P/l.i.
        if (f044 && current_class_ == "LP/j;" && current_method_ == "q") {
            std::cerr << "[F044-DIAG] LP/j.q(contains) -> "
                      << (val.type == DalvikType::INT32 ? val.int_val : -777)
                      << std::endl;
        }
    }

    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN " + val.to_string() + " at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_return_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;
    
    DalvikValue val = get_register(ret_reg);

    // F-075 (S21) — POLYMORPHIC-ZERO-AT-REFERENCE-USE LAW (return side).
    // Dalvik registers are untyped slots (F-028 law); `const/4 vX, #0` loads
    // the polymorphic zero word — INT32(0) in a primitive context, the NULL
    // REFERENCE in a reference context (ART verifier Zero reg-type,
    // convertible to any reference). return-object IS a reference context:
    // Kotlin `return null` compiles to `const/4 v0, 0; return-object v0`.
    // The old code propagated INT32(0) as the method's return — every
    // identity-sensitive consumer (if-ne vs an object, set/map identity
    // checks) then compared 0-vs-0 through the int fallback and answered
    // EQUAL for (object, null). First real-APK hit: dooz LL/b.remove
    // (PersistentOrderedSet) kept the UNREBUILT map after the trie emptied
    // (`if (node !== newNode)` mis-answered equal), the iterator walked the
    // sentinel and threw CME "Hash code of an element has changed", which
    // fatally killed the composition coroutine (S21 0-pixel gate). Same law
    // family as F-030 (zero-is-null at invoke params).
    if (val.type == DalvikType::INT32 && val.int_val == 0) {
        val = DalvikValue::make_null();
    } else if (val.type == DalvikType::VOID_) {
        val = DalvikValue::make_null();
    }

    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});
    
    // EXP-055: Store the return value (same as execute_return).
    last_invoke_return_ = val;

    // F-044 DIAG (env-gated): the derived-state calculation channel —
    // AndroidComposeView$o.c (the calculation lambda) → P/g$a.a →
    // LF/F$b.o → the record.f store. Expose the return VALUE TAG at each
    // hop: a null that arrives as REGISTER_UNSET instead of a proper
    // null OBJECT_REF corrupts the derived record's value field
    // (field-trace showed f stored as <unset>).
    {
        static thread_local const bool f044 = std::getenv("MINIANDROID_F044_DIAG") != nullptr;
        if (f044 && (current_class_ == "LP/g$a;" ||
                     current_class_ == "LF/F$b;" ||
                     current_class_ == "Landroidx/compose/ui/platform/AndroidComposeView$o;" ||
                     current_class_ == "LP/l;" ||
                     current_class_ == "LF/F;")) {
            std::cerr << "[F044-DIAG] " << current_class_ << "." << current_method_
                      << "() return-object type=" << static_cast<int>(val.type)
                      << " obj=" << val.object_id
                      << " int_val=" << val.int_val
                      << std::endl;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): K0-DRAW-FETCH watch. The
    // Compose LayoutNode.draw dispatch (Lmo0.D0) branches on K0(4): null →
    // Z0 fallback (observed 0 executions in the draw window — impossible for
    // a real tree where most nodes have no draw modifier), non-null → block
    // dispatch (observed only 20 of 82). Watch K0's return value class to
    // answer WHICH node object the fetch answers per call. Env-gated,
    // bounded — zero behavior change.
    // ────────────────────────────────────────────────────────────────────────
    {
        static thread_local const bool k0w_on =
            std::getenv("MINIANDROID_K0_WATCH") != nullptr;
        if (k0w_on && current_class_ == "Lmo0;" && current_method_ == "K0") {
            static thread_local uint64_t k0w_n = 0;
            if (k0w_n++ < 400) {
                const char* k0w_t = "other";
                if (val.type == DalvikType::OBJECT_REF) k0w_t = val.class_desc.c_str();
                else if (val.type == DalvikType::NULL_REF) k0w_t = "NULL";
                else if (val.type == DalvikType::REGISTER_UNSET) k0w_t = "UNSET";
                std::cerr << "[K0-RET] obj=" << val.object_id
                          << " cls=" << k0w_t
                          << " null=" << (val.is_null ? 1 : 0)
                          << std::endl;
            }
        }
    }

    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN_OBJECT " + val.to_string() + " at " + to_hex(pc));

    pc_ = pc + 1;
    return true;
}

// EXP-088+ F5: execute_return_wide — return-wide vAA (opcode 0x10, 11x format)
//
// Returns a 64-bit value (long or double) from a method.
//
// Per Dalvik spec: vAA holds the low 32 bits, vAA+1 holds the high 32 bits.
// Our register file already stores wide values as a single INT64 or FLOAT64
// DalvikValue in vAA (set by const-wide, iget-wide, etc.), so we just read
// the single register.
//
// The returned value is stored in last_invoke_return_ so the caller's
// move-result-wide can pick it up.
//
// Previously this opcode was MISSING from the dispatcher — it fell through
// to handle_unimplemented, causing methods that return long/double to:
//   1. Not actually return (execution continued past the return-wide)
//   2. Leave move-result-wide reading stale/zero data
//
// This is a GENERIC VM fix — affects any APK using long/double returns.
bool DalvikExecutionEngine::execute_return_wide(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;

    DalvikValue val = get_register(ret_reg);

    // If the register doesn't already hold a wide value (INT64 or FLOAT64),
    // coerce to INT64 with the existing int_val as the low 32 bits.
    // This handles cases where const-wide wasn't used to set the register
    // (e.g., the value came from an arithmetic op that stored INT32).
    if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
        int64_t coerced = static_cast<int64_t>(static_cast<uint32_t>(val.int_val));
        val = DalvikValue::make_long(coerced);
    }

    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});

    // Store so try_recursive_invoke / move-result-wide can propagate.
    last_invoke_return_ = val;

    // EXP-088+ F5 diagnostic: log wide returns for key methods
    if (current_method_ == "getTime" ||
        current_method_ == "currentTimeMillis" ||
        current_method_ == "getDuration" ||
        current_method_ == "getSize" ||
        current_method_ == "getLong" ||
        current_method_ == "nextLong") {
        std::cerr << "[EXP088-F5-RETWIDE] " << current_class_ << "."
                  << current_method_ << " PC=" << pc
                  << " ret_reg=v" << (int)ret_reg
                  << " type=" << static_cast<int>(val.type)
                  << " long_val=0x" << std::hex << val.long_val << std::dec
                  << " (" << val.long_val << ")"
                  << std::endl;
    }

    halted_ = true;
    halted_on_return_ = true;

    log("  RETURN_WIDE " + val.to_string() + " at " + to_hex(pc));

    pc_ = pc + 1;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Control Flow
// ============================================================================

bool DalvikExecutionEngine::execute_goto(uint32_t pc, InstructionTrace& trace) {
    // EXP-039 (BLOCKER-036 FIX): Handle all goto variants correctly.
    // goto (0x28) = format 10t: AA|op (1 code unit, offset in high byte)
    // goto/16 (0x29) = format 20t: op|AAAA (2 code units, offset in next word)
    // goto/32 (0x2a) = format 30t: op|AAAAAAAA (3 code units, offset in next 2 words)
    if (pc >= bytecode_.size()) return false;

    uint16_t opcode = bytecode_[pc] & 0xFF;

    int32_t offset;
    uint32_t pc_advance;

    if (opcode == Opcode::GOTO) {
        // Format 10t: offset is in high byte (signed 8-bit)
        offset = static_cast<int8_t>((bytecode_[pc] >> 8) & 0xFF);
        pc_advance = 1;
        // EXP-071: D8/R8 hybrid goto encoding.
        // D8 uses op=0x28 (goto) for BOTH 10t and 20t formats:
        // 1. High byte != 0: Standard 10t format (1 code unit, offset in high byte).
        // 2. High byte == 0: Extended 20t format (2 code units, offset in next word).
        //    This is safe because D8 doesn't generate goto +0 (NOP).
        //    We check that the next word is a reasonable offset (< 10000).
        if (offset == 0 && pc + 1 < bytecode_.size()) {
            int16_t next_offset = static_cast<int16_t>(bytecode_[pc + 1]);
            if (next_offset != 0 && std::abs(next_offset) < 10000) {
                offset = next_offset;
                pc_advance = 2;
            }
        }
    } else if (opcode == Opcode::GOTO_16) {
        // EXP-044 Phase 1: D8/R8 hybrid goto/16 encoding.
        //
        // D8 uses op=0x28 (goto/16) in TWO modes:
        // 1. High byte != 0: The high byte IS the 8-bit signed offset.
        //    Total instruction size: 1 code unit (like 10t format).
        //    The "next word" is the START of the next instruction, NOT an offset.
        //    Example: AndroidUtilities.bold PC=24 → high=0x09=+9 → target=PC=33
        // 2. High byte == 0: Standard 20t format, 16-bit signed offset in next word.
        //    Total instruction size: 2 code units.
        //    Example: (rare, 578 out of 27381 in classes.dex)
        //
        // Evidence: 26803 goto/16 instructions have non-zero high byte,
        // 578 have high byte=0 (standard 20t). The high byte values are
        // always small (±12 range typical), matching short branch offsets.
        //
        // This was the root cause of 20 HALT-GOTO events in Telegram execution.
        uint8_t high_byte = (bytecode_[pc] >> 8) & 0xFF;
        if (high_byte != 0) {
            // D8 hybrid mode: 1-code-unit goto with 8-bit offset in high byte
            offset = static_cast<int8_t>(high_byte);
            pc_advance = 1;
        } else {
            // Standard 20t format: 2 code units, 16-bit offset in next word
            if (pc + 1 >= bytecode_.size()) return false;
            offset = static_cast<int16_t>(bytecode_[pc + 1]);
            pc_advance = 2;
        }
    } else if (opcode == Opcode::GOTO_32) {
        // EXP-044 Phase 1: D8/R8 hybrid goto/32 encoding (same as goto/16).
        //
        // D8 uses op=0x29 (goto/32) in TWO modes:
        // 1. High byte != 0 (10959 occurrences): 8-bit signed offset in high byte.
        //    Total instruction size: 1 code unit.
        // 2. High byte == 0 (24727 occurrences): 16-bit signed offset in next word.
        //    Total instruction size: 2 code units (NOT 3 as per AOSP 30t spec).
        //    The word at PC+2 is the start of the NEXT instruction, not the high
        //    16 bits of a 32-bit offset.
        //
        // Evidence: ApplicationLoader.postInitApplication PC=8:
        //   high=0x00, next=0x0101=257 → target=PC=265 (return-void). Correct!
        //   Standard 30t with 32-bit offset would give 0x10120101 → invalid.
        uint8_t high_byte = (bytecode_[pc] >> 8) & 0xFF;
        if (high_byte != 0) {
            // D8 hybrid mode: 1-code-unit goto with 8-bit offset in high byte
            offset = static_cast<int8_t>(high_byte);
            pc_advance = 1;
        } else {
            // D8 2-code-unit format: 16-bit offset in next word
            if (pc + 1 >= bytecode_.size()) return false;
            offset = static_cast<int16_t>(bytecode_[pc + 1]);
            pc_advance = 2;
        }
    } else {
        // Unknown goto variant — treat as 10t
        offset = static_cast<int8_t>((bytecode_[pc] >> 8) & 0xFF);
        pc_advance = 1;
    }

    uint32_t target = pc + offset;

    // EXP-051: D8 "unreachable" marker — `goto +0` (self-loop).
    //
    // D8/R8 replace `throw vAA` instructions with `goto +0` (a self-loop
    // at the throw site) when the throw is unreachable from the entry
    // point OR when D8 strips the throw as part of dead-code elimination.
    // This pattern shows up in LifecycleRegistry.enforceMainThreadIfNeeded
    // at PC=46 — the bytecode constructs an IllegalStateException but
    // then has `goto +0` instead of `throw v0`.
    //
    // Without special handling, the engine loops forever at this PC
    // (HALT-LOOP). We treat `goto +0` as a "halt method" — equivalent
    // to return-void — so execution continues with the caller.
    //
    // Evidence: bytecode at PC=46 of LifecycleRegistry.enforceMainThreadIfNeeded
    //   (classes.dex, code_off=0x250668) is 0x0027 (goto +0). The throw
    //   that should follow the IllegalStateException.<init> at PC=43 is
    //   missing — D8 replaced it with this self-loop.
    if (offset == 0) {
        trace.status = InstructionTrace::Status::HALT_RETURN;
        trace.operands.push_back({"offset", "0 (D8 unreachable marker)"});
        trace.operands.push_back({"target", "exit_method"});
        halted_ = true;
        halted_on_return_ = true;
        pc_ = pc + pc_advance;
        return true;
    }

    // EXP-044 Phase 1: When goto target == bytecode_.size(), it means "exit
    // the method" (branch past the end = return). This is valid Dalvik behavior
    // for methods that end with a goto that jumps past the last instruction.
    // Example: Intrinsics.throwParameterIsNullNPE PC=15: goto +1 → PC=16
    // where bytecode_size=16. This is equivalent to return-void.
    //
    // EXP-051: Also handle target > bytecode_.size() — D8/R8 sometimes emit
    // `goto +N` where N points past the end as an "unreachable" marker.
    // Example: SpringForce.setDampingRatio PC=19: goto +3 → PC=22,
    // but bytecode_size=20. Without this fix, the engine HALTs with
    // HALT-GOTO. With this fix, we treat it as "exit method" (= return).
    if (target >= bytecode_.size()) {
        trace.status = InstructionTrace::Status::HALT_RETURN;
        trace.operands.push_back({"offset", std::to_string(offset)});
        trace.operands.push_back({"target", "exit_method (past end)"});
        halted_ = true;
        halted_on_return_ = true;
        pc_ = pc + pc_advance;
        return true;
    }

    // Validate target
    if (target < bytecode_.size()) {
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;

        trace.operands.push_back({"offset", std::to_string(offset)});
        trace.operands.push_back({"target", to_hex(target)});
    } else {
        trace.status = InstructionTrace::Status::CRASH_ERROR;
        trace.error_message = "Invalid goto target: " + to_hex(target) +
                              " (offset=" + std::to_string(offset) +
                              ", bytecode_size=" + std::to_string(bytecode_.size()) + ")";
        halted_ = true;
        halt_reason_ = "Invalid goto target";
        pc_ = pc + pc_advance;
        // EXP-043 Phase 1: log invalid goto targets for debugging (first 20 only
        // to avoid log spam). These indicate either real bytecode verification
        // issues or goto/32 misinterpretation.
        static thread_local uint64_t halt_goto_count = 0;
        if (halt_goto_count < 20) {
            std::cerr << "[HALT-GOTO] Invalid goto target PC=" << to_hex(pc)
                      << " in " << current_class_ << "." << current_method_
                      << " target=" << to_hex(target)
                      << " bytecode_size=" << bytecode_.size() << std::endl;
            halt_goto_count++;
        }
    }

    return true;
}

bool DalvikExecutionEngine::execute_if_eqz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);

    DalvikValue val = get_register(test_reg);
    // EXP-055: Treat OBJECT_REF with object_id=0 as null (same as NULL_REF).
    // EXP-058: Also treat VOID_ as zero (same rationale as if-nez).
    // EXP-092+ CRITICAL FIX: Also treat BOOLEAN with int_val==0 as zero.
    //   instance-of returns make_bool(false) which sets type=BOOLEAN, int_val=0.
    //   Without this check, if-eqz on a false BOOLEAN result returns is_zero=false,
    //   causing the branch to NOT be taken — which is the OPPOSITE of correct
    //   behavior. This affects ALL instance-of results in conditional branches.
    //   Same for BYTE, SHORT, CHAR — all integer-like types with int_val.
    // EXP-093/F014: Added INT64, FLOAT32, FLOAT64 to zero-ness check.
    // Per AOSP: if-eqz/if-nez treat ALL primitive types' zero as false.
    // Previously INT64 (long 0L), FLOAT32 (0.0f), FLOAT64 (0.0d) were
    // NOT treated as zero, causing if-eqz to return is_zero=FALSE for
    // a zero long/double/float — the OPPOSITE of correct behavior.
    bool is_zero = (val.type == DalvikType::NULL_REF) ||
                   (val.type == DalvikType::INT32 && val.int_val == 0) ||
                   (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                   (val.type == DalvikType::BYTE && val.int_val == 0) ||
                   (val.type == DalvikType::SHORT && val.int_val == 0) ||
                   (val.type == DalvikType::CHAR && val.int_val == 0) ||
                   (val.type == DalvikType::INT64 && val.long_val == 0) ||
                   (val.type == DalvikType::FLOAT32 && val.float_val == 0.0f) ||
                   (val.type == DalvikType::FLOAT64 && val.double_val == 0.0) ||
                   (val.type == DalvikType::OBJECT_REF && val.object_id == 0) ||
                   (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) ||
                   (val.type == DalvikType::VOID_);

    // EXP-059: Debug — log if-eqz in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IF-EQZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " test_reg=v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " target=" << (pc + offset)
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-eqz in LoginActivity.setPage.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "setPage") {
        std::cerr << "[EXP092-SETPAGE-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-eqz"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_zero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE D: Log if-eqz in lambda$onNextPressed$22 to trace the
    // critical branch at PC=8: if-eqz v4(instance-of result) → PC=46
    if (current_class_.find("LoginActivity$PhoneView") != std::string::npos &&
        current_method_ == "lambda$onNextPressed$22") {
        std::cerr << "[EXP092-IF-EQZ-22] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-eqz"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_zero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    if (is_zero) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            trace.operands.push_back({"target", "exit_method (past end)"});
            pc_ = pc + 2;
        } else {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }

    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", is_zero ? "yes" : "no"});

    return true;
}

bool DalvikExecutionEngine::execute_if_nez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    
    DalvikValue val = get_register(test_reg);
    // EXP-055: Treat OBJECT_REF with object_id=0 as null (same as NULL_REF).
    // EXP-058: Also treat VOID_ as zero — when bridge_to_api returns void
    // for unhandled methods, if-nez must NOT branch. Previously VOID_
    // was treated as non-zero, causing branches that skipped important
    // method calls (e.g., onFragmentCreate was never called because
    // needAddFragmentToStack returned VOID_ on a null delegate).
    // EXP-093/F014: Added INT64, FLOAT32, FLOAT64 to zero-ness check
    // (same as if-eqz handler above).
    bool is_nonzero = !(val.type == DalvikType::NULL_REF ||
                       (val.type == DalvikType::INT32 && val.int_val == 0) ||
                       (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                       (val.type == DalvikType::BYTE && val.int_val == 0) ||
                       (val.type == DalvikType::SHORT && val.int_val == 0) ||
                       (val.type == DalvikType::CHAR && val.int_val == 0) ||
                       (val.type == DalvikType::INT64 && val.long_val == 0) ||
                       (val.type == DalvikType::FLOAT32 && val.float_val == 0.0f) ||
                       (val.type == DalvikType::FLOAT64 && val.double_val == 0.0) ||
                       (val.type == DalvikType::OBJECT_REF && val.object_id == 0) ||
                       (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) ||
                       (val.type == DalvikType::VOID_));
    
    // EXP-059: Debug — log if-nez in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IF-NEZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " test_reg=v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " target=" << (pc + offset)
                  << std::endl;
    }
    
    // EXP-046: Log if-nez in NativeLoader.initNativeLibs
    if (current_class_.find("NativeLoader") != std::string::npos) {
        std::cerr << "[IF-NEZ-DBG] " << current_class_ << "." << current_method_
                  << " PC=" << pc << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " val=" << val.int_val
                  << " nonzero=" << is_nonzero
                  << " target=" << (pc + offset) << std::endl;
    }

    // ── TRAIN-64 (T64, DIAG-ONLY): the branch decision inside the R8-
    // inlined changedToUp helper (Lbo;.h: return h && !d). The UP change's
    // h read answered 1 yet the d read never ran — this logs the exact
    // register/type/value if-nez saw, pinning the drop point.
    if (touch_dispatch_active_ && current_class_ == "Lbo;" &&
        current_method_ == "h") {
        static thread_local uint64_t t64z_n = 0;
        if (t64z_n++ < 64) {
            std::cerr << "[T64-NEZ] Lbo;.h pc=" << pc
                      << " reg=v" << static_cast<int>(test_reg)
                      << " type=" << static_cast<int>(val.type)
                      << " int_val=" << val.int_val
                      << " bool_val="
                      << (val.type == DalvikType::BOOLEAN
                              ? static_cast<int>(val.bool_val) : -1)
                      << " nonzero=" << (is_nonzero ? 1 : 0)
                      << std::endl;
        }
    }

    // EXP-092+ DIRECT TRACE: Log if-nez in onNextPressed and lambda$new$12
    // to prove the exact condition that determines the needShowAlert side path.
    // Critical branches:
    //   lambda$new$12 PC=0:  if-nez v2(response), +3 → PC=3  (null check on response)
    //   lambda$new$12 PC=11: if-nez v0(codeField.length()), +11 → PC=22 (skip setCountry if codeField non-empty)
    if ((current_class_.find("LoginActivity$PhoneView") != std::string::npos &&
         (current_method_ == "onNextPressed" || current_method_ == "lambda$new$12" ||
          current_method_ == "setCountry" || current_method_ == "afterTextChanged" ||
          current_method_.find("lambda$") == 0)) ||
        current_class_.find("PhoneView$2") != std::string::npos) {
        std::cerr << "[EXP092-IF-NEZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " string=\"" << val.string_val << "\""
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-nez/if-eqz in LoginActivity.setPage.
    // The setPage method has 309 instructions and many branches. We need
    // to trace ALL of them to understand what page_value=13 does.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "setPage") {
        std::cerr << "[EXP092-SETPAGE-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-nez"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-nez in fillNextCodeParams to trace why
    // page_value=13 is chosen even with type=TL_auth_sentCodeTypeSms.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "fillNextCodeParams") {
        std::cerr << "[EXP092-FILLNEXT-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-nez"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    if (is_nonzero) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            trace.operands.push_back({"target", "exit_method (past end)"});
            pc_ = pc + 2;
        } else {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    
    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", is_nonzero ? "yes" : "no"});
    
    return true;
}

// ============================================================================
// EXP-043 Phase 1: Proper 21t format if-*z handlers
// Per AOSP:
//   if-ltz vAA, +BBBB : branch if (int) vAA < 0
//   if-gez vAA, +BBBB : branch if (int) vAA >= 0
//   if-gtz vAA, +BBBB : branch if (int) vAA > 0
//   if-lez vAA, +BBBB : branch if (int) vAA <= 0
//
// For OBJECT_REF, NULL_REF, UNINITIALIZED: the value is treated as 0 (which
// means if-ltz=fallthrough, if-gez=branch, if-gtz=fallthrough, if-lez=branch).
// This matches Dalvik's behavior of converting null to 0 for int comparisons.
// ============================================================================

bool DalvikExecutionEngine::execute_if_ltz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA < 0
    // EXP-059: Now correctly dispatched for opcode 0x3A (per AOSP).
    //   Per AOSP: 0x3A = if-ltz ("branch if v < 0").
    // Previously the runtime had if-ltz at 0x39 (off-by-one), which collided
    // with the actual if-nez. The EXP-058 hack treated INT32 if-ltz as if-nez
    // to work around that collision. With the opcode table fixed, if-ltz now
    // correctly means "branch if < 0" for INT32, matching AOSP semantics.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);

    bool taken = false;
    if (val.type == DalvikType::OBJECT_REF) {
        // OBJECT_REF can't be < 0; never branch.
        taken = false;
    } else if (val.type == DalvikType::NULL_REF) {
        // null == 0 → 0 < 0 is false; never branch.
        taken = false;
    } else if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
               val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
               val.type == DalvikType::CHAR) {
        // Standard AOSP if-ltz: branch if val < 0.
        taken = (val.int_val < 0);
    } else if (val.type == DalvikType::INT64) {
        taken = (static_cast<int64_t>(val.long_val) < 0);
    } else {
        // UNINITIALIZED, REGISTER_UNSET, VOID_ → don't branch.
        taken = false;
    }

    if (taken) {
        uint32_t target = pc + offset;
        if (target < bytecode_.size()) {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        } else if (target == bytecode_.size()) {
            // goto past end = exit method
            halted_ = true;
            halted_on_return_ = true;
            pc_ = pc + 2;
            return true;
        } else {
            pc_ = pc + 2;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_gez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA >= 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival >= 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_gtz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA > 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival > 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_lez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA <= 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival <= 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

// ============================================================================
// EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
// Format 22t: B1|A|op CCCC  → 2 code units
//   code[0]: bits 0-7 = opcode, bits 8-11 = vA (4 bits), bits 12-15 = vB (4 bits)
//   code[1]: 16-bit signed branch offset (CCCC)
// Branch target = pc + offset (signed)
// ============================================================================

namespace {

// Helper: extract two 4-bit registers from a 22t opcode word.
// vA = high nibble of low byte  = (instr >> 8) & 0xF
// vB = high nibble of high byte = (instr >> 12) & 0xF
struct If22tRegs {
    uint8_t vA;
    uint8_t vB;
    int16_t offset;
};

If22tRegs decode_22t(uint16_t instr, uint16_t next_word) {
    If22tRegs r;
    r.vA = static_cast<uint8_t>((instr >> 8) & 0xF);
    r.vB = static_cast<uint8_t>((instr >> 12) & 0xF);
    r.offset = static_cast<int16_t>(next_word);
    return r;
}

// Helper: common branch logic for 22t if-* opcodes.
// `taken` is whether the comparison evaluated true.
// On take: pc = pc + offset; On fall-through: pc = pc + 2.
bool do_22t_branch(uint32_t pc, int16_t offset, bool taken,
                   const std::string& opcode_name,
                   uint8_t vA, uint8_t vB,
                   const DalvikValue& a, const DalvikValue& b,
                   InstructionTrace& trace, DalvikExecutionEngine* engine_unused = nullptr) {
    (void)engine_unused;  // signature placeholder
    if (taken) {
        uint32_t target = pc + offset;
        // Note: target may legitimately equal pc + 2 (fall-through) when offset=2,
        // or be backward when offset is negative.
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        trace.pc_after = target;
        // We can't directly set pc_ here since it's a member; the caller does that.
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
    }
    trace.operands.push_back({"vA", "v" + std::to_string(vA) + "=" + a.to_string()});
    trace.operands.push_back({"vB", "v" + std::to_string(vB) + "=" + b.to_string()});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    trace.operands.push_back({"offset", std::to_string(offset)});
    (void)opcode_name;
    return true;
}

} // anonymous namespace

#define IMPLEMENT_IF_22T(name, op, op_name) \
bool DalvikExecutionEngine::execute_##name(uint32_t pc, InstructionTrace& trace) { \
    /* CONT-7 §12 branch-decision diagnostics (shared across all six 22t) */ \
    static thread_local const bool r337_c7_trace = \
        std::getenv("MINIANDROID_C7_IF_TRACE") != nullptr; \
    static thread_local uint64_t r337_c7_if_n = 0; \
    if (pc + 1 >= bytecode_.size()) return false; \
    uint16_t instr = bytecode_[pc]; \
    If22tRegs r = decode_22t(instr, bytecode_[pc + 1]); \
    DalvikValue a = get_register(r.vA); \
    DalvikValue b = get_register(r.vB); \
    /* CHAR-PROBE campaign: extract the numeric value from EVERY integer-like \
       primitive type, not just INT32. Per the Dalvik spec if-eq/if-ne/... \
       22t only ever compare same-width ints, but the interpreter's typed \
       registers (CHAR/BOOLEAN/BYTE/SHORT from signature-aware invoke and \
       field/array loads) all carry their value in int_val. The previous \
       "(type==INT32) ? int_val : 0" collapsed every other primitive to 0 — \
       a char param compared as 0 and EMPTY BOARD CELLS matched it. Same \
       zero-tolerance law as the EXP-093 if-eqz fix. */ \
    auto if22t_int = [](const DalvikValue& v) -> int32_t { return dalvik_int_value(v); }; \
    int32_t a_val = if22t_int(a); \
    int32_t b_val = if22t_int(b); \
    bool taken = false; \
    /* F-069: CLASS_REF participates in reference comparison like
       OBJECT_REF/NULL_REF — its identity token (stable per descriptor,
       see execute_const_class) is the compared word. Kotlin/Java compare
       Class objects with == (Intrinsics.areEqual fast path, map keys,
       KClass lookups); the old code fell to the int_val path where every
       CLASS_REF carried int_val=0, so if-eq on two DIFFERENT Class
       values was TAKEN and if-eq on two SAME-Class values was
       indistinguishable from any other zero. */ \
    /* CODER7 WAVE-11 (P-58): STRING_REF participates in reference \
       comparison — the engine's STRING_REF is a VALUE (no identity; equal \
       contents collapse to one value), so two string registers compare BY \
       CONTENT, and a string-vs-null pair answers never-equal (a string \
       value is never the null reference). The old set excluded STRING_REF: \
       every pair fell to the int tail where dalvik_int_value collapses \
       both to 0 — if-eq TAKEN and if-ne NOT taken for ANY two strings \
       (`str != "lit"` never branched, `str == null` always true). The \
       N10 evidence: `lastSelArg0 != "unset"` answered false for content \
       "2" — the delete loop never ran. */ \
    bool a_is_ref = (a.type == DalvikType::OBJECT_REF || a.type == DalvikType::NULL_REF || a.type == DalvikType::CLASS_REF || a.type == DalvikType::STRING_REF); \
    bool b_is_ref = (b.type == DalvikType::OBJECT_REF || b.type == DalvikType::NULL_REF || b.type == DalvikType::CLASS_REF || b.type == DalvikType::STRING_REF); \
    if (a_is_ref && b_is_ref && a.type == DalvikType::CLASS_REF && b.type == DalvikType::CLASS_REF) { \
        /* F-NEW-225d (completes F-NEW-218/F-069) — CLASS TOKEN DESCRIPTOR \
           IDENTITY LAW. ART: a class has exactly ONE Class object, so \
           `clsA == clsB` holds IFF they name the same class. Engine \
           minted tokens carry ref_id = instruction_sequence_ (F-NEW-218 \
           getClass law) — EVERY token mints a fresh id, so ref_id \
           comparison answers never-equal for two tokens of the SAME \
           class. Observable face (opencalc vc53): Gson's \
           ReflectiveTypeAdapterFactory.getBoundFields loop guard \
           `while (raw != Object.class)` never terminated — the Object \
           token comparison missed, the loop climbed one level further, \
           fed getGenericSuperclass(Object)==null into \
           TypeToken.get(null) → $Gson$Types.getRawType IAE → \
           MainActivity.onCreate APP-BOUNDARY death. LAW: CLASS_REF vs \
           CLASS_REF compares the CANONICAL descriptor (F-NEW-224 form), \
           not the mint id. */ \
        taken = (framework::normalize_class_desc(a.class_desc) op \
                 framework::normalize_class_desc(b.class_desc)); \
        { \
            static thread_local uint64_t f225d_n = 0; \
            if (f225d_n < 24) { \
                ++f225d_n; \
                std::cerr << "[F-NEW-225d] " << op_name << " a=" << a.class_desc \
                          << " b=" << b.class_desc << " taken=" << (taken ? "YES" : "NO") \
                          << " caller=" << current_class_ << "." << current_method_ \
                          << std::endl; \
            } \
        } \
    } else if (a_is_ref && b_is_ref) { \
        /* ── F-C4-569 (W6, 4APP4): CLASS-TOKEN REFERENCE-IDENTITY LAW ── \
           ART (art::mirror::Class, one Class object per classloader+name): \
           `tokenA == tokenB` on Class references is TRUE iff the two \
           tokens name the SAME class. The engine mints heap Class tokens \
           at multiple sites (const-class cache, F-NEW-282 iput \
           materialization, Class.forName bridges, getClass law) — two \
           DISTINCT oids for one referent made every if-eq/if-ne on a \
           Class-token pair answer never-equal. Kotlin compiles `==` on \
           statically NON-NULL Class references (e.g. ClassReference.\
           equals' `jClass == other.jClass`) to a PLAIN if-ne — NOT to \
           Intrinsics.areEqual / Object.equals — so the W5 laws \
           F-C4-567/F-C4-568 (equals bridge + hashCode) never saw this \
           compare at all. Live root (Thunderbird v24, Koin): every \
           ConcurrentHashMap.get(Node) chain-walk compare died at the \
           Kotlin ClassReference.equals if-ne on two heap tokens for the \
           same referent → NoDefinitionFoundException ×32 (the 510 CHM \
           puts + 596 nodes all stored fine — laws 566/568 — the GET \
           simply never matched). Same opcode also answers the CHM \
           getNode `(ek = e.key) == key` fast path. LAW: a Class-token \
           pair in if-eq/if-ne compares REFERENT IDENTITY — the register \
           form's canonical class_desc, the heap form's __referent_desc \
           (F-069/F-103 convention; the W4 567 companion for the opcode \
           path). Non-quantified pairs keep the oid law (OpenJDK \
           reference identity). */ \
        bool f569_a_tok = false, f569_b_tok = false; \
        std::string f569_a_ref, f569_b_ref; \
        if (a.type == DalvikType::CLASS_REF) { \
            f569_a_tok = true; \
            f569_a_ref = a.class_desc; \
        } else if (a.type == DalvikType::OBJECT_REF && a.object_id != 0 && \
                   heap_.has_object(a.object_id)) { \
            const auto* f569_ao = heap_.get(a.object_id); \
            if (f569_ao && \
                f569_ao->class_descriptor == "Ljava/lang/Class;") { \
                auto f569_ar = heap_.get_object_field(a.object_id, \
                                                      "__referent_desc"); \
                if (f569_ar.has_value() && \
                    f569_ar->type == DalvikType::STRING_REF && \
                    !f569_ar->string_val.empty()) { \
                    f569_a_tok = true; \
                    f569_a_ref = f569_ar->string_val; \
                } \
            } \
        } \
        if (b.type == DalvikType::CLASS_REF) { \
            f569_b_tok = true; \
            f569_b_ref = b.class_desc; \
        } else if (b.type == DalvikType::OBJECT_REF && b.object_id != 0 && \
                   heap_.has_object(b.object_id)) { \
            const auto* f569_bo = heap_.get(b.object_id); \
            if (f569_bo && \
                f569_bo->class_descriptor == "Ljava/lang/Class;") { \
                auto f569_br = heap_.get_object_field(b.object_id, \
                                                      "__referent_desc"); \
                if (f569_br.has_value() && \
                    f569_br->type == DalvikType::STRING_REF && \
                    !f569_br->string_val.empty()) { \
                    f569_b_tok = true; \
                    f569_b_ref = f569_br->string_val; \
                } \
            } \
        } \
        if (f569_a_tok && f569_b_tok) { \
            taken = (f569_a_ref op f569_b_ref); \
            static thread_local const bool f569_diag = \
                std::getenv("MINIANDROID_F569_DIAG") != nullptr; \
            static thread_local uint64_t f569_n = 0; \
            if (f569_diag && f569_n++ < 40) { \
                std::cerr << "[F-C4-569] " << op_name \
                          << " a=" << f569_a_ref \
                          << " b=" << f569_b_ref \
                          << " taken=" << (taken ? "YES" : "NO") \
                          << " caller=" << current_class_ << "." \
                          << current_method_ << std::endl; \
            } \
        } else if (a.type == DalvikType::STRING_REF && \
                   b.type == DalvikType::STRING_REF) { \
            /* P-58 (the value-model identity arm): two string registers \
               compare BY CONTENT — the engine's STRING_REF carries no \
               identity, so content equality IS the interning law the \
               compiler's acmp-on-interned-literals realizes. std::string \
               wrappers: CowStr has ==/!= natively; the relational ops \
               compare content lexicographically through the const-string& \
               conversion (a string "reference" compare that reaches the \
               relational opcodes is a malformed-verifier shape anyway — \
               the content order is the honest total order). */ \
            taken = (std::string(a.string_val) op std::string(b.string_val)); \
        } else { \
            /* S231 (cODER-ohc) — STRING_REF vs a NON-STRING reference \
               (NULL_REF, OBJECT_REF, CLASS_REF) is ALWAYS unequal: a \
               materialized string value is never the null reference and \
               never a heap object. The old oid tail collapsed STRING_REF \
               to 0 (it is neither OBJECT_REF nor CLASS_REF), so \
               `str != null` compiled to if-ne answered 0 != 0 = false \
               (and if-eq answered true) — the exact opposite of AOSP \
               acmp law. SolitaireCG evidence: \
               SolitaireCG.onResume `GetRestoreState() != "STATS"` — \
               mRestoreState was null on a cold launch (the app's \
               getLastNonConfigurationInstance answered null, correctly), \
               yet the collapsed compare took the taken==false path and \
               called DisplayStats(), replacing the real game view with \
               the stats screen on every launch. */ \
            bool a_s = (a.type == DalvikType::STRING_REF); \
            bool b_s = (b.type == DalvikType::STRING_REF); \
            if (a_s != b_s) { \
                taken = (0 op 1); \
            } else { \
                uint32_t a_obj = (a.type == DalvikType::OBJECT_REF) ? a.object_id \
                                : (a.type == DalvikType::CLASS_REF) ? a.ref_id : 0; \
                uint32_t b_obj = (b.type == DalvikType::OBJECT_REF) ? b.object_id \
                                : (b.type == DalvikType::CLASS_REF) ? b.ref_id : 0; \
                taken = (a_obj op b_obj); \
            } \
        } \
    } else if (a_is_ref || b_is_ref) { \
        /* F-075 (S21): mixed reference-vs-const/4-zero compare. The zero \
           word is the null reference in a reference context (ART Zero \
           reg-type, convertible to any reference). Compare identities: \
           the zero side answers 0; a NON-zero int against a reference is \
           a verifier impossibility — answer never-equal (if-eq not taken, \
           if-ne taken) instead of collapsing the OBJECT_REF side to 0 \
           through dalvik_int_value. First real-APK hit: dooz LL/b.remove \
           `if (node !== newNode)` where newNode was a const/4-null return \
           tagged INT32(0) — the old int path compared 0==0 and skipped \
           the map rebuild (CME "Hash code of an element has changed"). */ \
        auto f075_ref_id = [](const DalvikValue& v) -> uint32_t { \
            if (v.type == DalvikType::OBJECT_REF) return v.object_id; \
            if (v.type == DalvikType::CLASS_REF)  return static_cast<uint32_t>(v.ref_id); \
            return 0; /* NULL_REF or the zero word */ \
        }; \
        auto f075_is_zero = [](const DalvikValue& v) -> bool { \
            return v.type == DalvikType::NULL_REF || \
                   (v.type == DalvikType::INT32 && v.int_val == 0); \
        }; \
        bool f075_mixed_zero = (a_is_ref ? f075_is_zero(b) : f075_is_zero(a)); \
        if (f075_mixed_zero) { \
            uint32_t a_obj = a_is_ref ? f075_ref_id(a) : 0; \
            uint32_t b_obj = b_is_ref ? f075_ref_id(b) : 0; \
            taken = (a_obj op b_obj); \
        } else { \
            /* ref vs non-zero int: verifier-impossible — never equal; \
               (0 op 1) yields ==:false, !=:true for any op token */ \
            taken = (0 op 1); \
        } \
    } else { \
        taken = (a_val op b_val); \
    } \
    /* EXP-071: Diagnostic for if-lt/if-eq in onConfirm */ \
    if (current_class_.find("PhoneView$6") != std::string::npos && \
        current_method_ == "onConfirm") { \
        std::cerr << "[EXP071-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(type=" << static_cast<int>(a.type) \
                  << " val=" << a_val << ") vs v" << (int)r.vB \
                  << "(type=" << static_cast<int>(b.type) \
                  << " val=" << b_val << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target=" << (pc + r.offset) << std::endl; \
    } \
    /* EXP-092+ DIRECT TRACE: Log every if-* branch in onNextPressed to
       prove the exact condition that determines the needShowAlert side path.
       The critical branch is at PC=604: `if-lt v4, v2, +28 → PC=632`
       where v4=countryState and v2=1. */ \
    if (current_class_.find("LoginActivity$PhoneView") != std::string::npos && \
        current_method_ == "onNextPressed") { \
        std::cerr << "[EXP092-ONNEXT-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(type=" << static_cast<int>(a.type) \
                  << " val=" << a_val; \
        if (a.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << a.object_id; } \
        std::cerr << ") vs v" << (int)r.vB \
                  << "(type=" << static_cast<int>(b.type) \
                  << " val=" << b_val; \
        if (b.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << b.object_id; } \
        std::cerr << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* EXP-092+ PHASE 1: Log every if-* branch in LoginActivity.setPage to
       determine what page_value=13 means. The setPage switch at PC=0-32
       checks for pages 0, 5, 6, 9, 10, 12, 16, 17. page_value=13 does NOT
       match any of these — need to trace the actual branch outcomes. */ \
    if (current_class_.find("LoginActivity;") != std::string::npos && \
        current_class_.find("PhoneView") == std::string::npos && \
        current_method_ == "setPage") { \
        std::cerr << "[EXP092-SETPAGE-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(val=" << a_val \
                  << ") vs v" << (int)r.vB \
                  << "(val=" << b_val \
                  << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* EXP-092+ PHASE 1: Log every if-* branch in fillNextCodeParams to
       understand why page_value=13 is chosen even when the mock response
       has type=TL_auth_sentCodeTypeSms. The critical branch is at PC=67:
       if-eqz v3 (instance-of check for TL_auth_sentCodeTypeFirebaseSms).
       If the type field IS set to TL_auth_sentCodeTypeSms, the instance-of
       checks for FirebaseSms/App/Call should all be false, and the code
       should reach the Sms path. */ \
    if (current_class_.find("LoginActivity;") != std::string::npos && \
        current_class_.find("PhoneView") == std::string::npos && \
        current_method_ == "fillNextCodeParams") { \
        std::cerr << "[EXP092-FILLNEXT-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(val=" << a_val; \
        if (a.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << a.object_id << " cls=" << a.class_desc; } \
        std::cerr << ") vs v" << (int)r.vB \
                  << "(val=" << b_val; \
        if (b.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << b.object_id << " cls=" << b.class_desc; } \
        std::cerr << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* CONT-7 §12 A/B (env-gated, bounded): every 22t branch decision with */ \
    /* exact operand values — the dooz Lek1.b Semaphore ISE fires on a */ \
    /* path that the static bytecode says is unreachable with p=0, so the */ \
    /* branch evaluation itself must be observed at runtime. */ \
    if (r337_c7_trace && r337_c7_if_n < 64) { \
        ++r337_c7_if_n; \
        std::cerr << "[C7-IF] " << op_name << " pc=" << pc \
                  << " v" << (int)r.vA << "(k" << (int)a.type << "=" << a_val \
                  << ") vs v" << (int)r.vB << "(k" << (int)b.type << "=" \
                  << b_val << ") taken=" << (taken ? "YES" : "NO") \
                  << " target=" << (pc + r.offset) \
                  << " caller=" << current_class_ << "." << current_method_ \
                  << std::endl; \
    } \
    do_22t_branch(pc, r.offset, taken, op_name, r.vA, r.vB, a, b, trace); \
    if (taken) { \
        uint32_t target = pc + r.offset; \
        /* EXP-051: D8 unreachable marker — branch target past end-of-method. */ \
        /* Treated as "exit method" (= return-void), same as goto-past-end. */ \
        if (target >= bytecode_.size()) { \
            halted_ = true; halted_on_return_ = true; \
            trace.status = InstructionTrace::Status::HALT_RETURN; \
            trace.operands.push_back({"target", "exit_method (past end)"}); \
            pc_ = pc + 2; \
        } else { \
            pc_ = target; \
        } \
    } else { pc_ = pc + 2; } \
    return true; \
}

IMPLEMENT_IF_22T(if_eq, ==, "if-eq")
IMPLEMENT_IF_22T(if_ne, !=, "if-ne")
IMPLEMENT_IF_22T(if_lt, <,  "if-lt")
IMPLEMENT_IF_22T(if_ge, >=, "if-ge")
IMPLEMENT_IF_22T(if_gt, >,  "if-gt")
IMPLEMENT_IF_22T(if_le, <=, "if-le")

// ============================================================================
// Unimplemented Handler
// ============================================================================

void DalvikExecutionEngine::handle_unimplemented(uint16_t opcode, uint32_t pc, 
                                                InstructionTrace& trace) {
    trace.status = InstructionTrace::Status::UNIMPLEMENTED;
    trace.error_message = "Unimplemented opcode: 0x" + to_hex16(opcode);
    
    log("  UNIMPLEMENTED: 0x" + to_hex16(opcode) + " at " + to_hex(pc)
        + " in " + current_class_ + "." + current_method_);
    // M4-F028 diag: dump the raw code units around the bad pc — evidence
    // for walk-alignment forensics (a pc landing inside a literal means an
    // earlier instruction size or branch was decoded wrong). Throttled per
    // (class, method, pc) so loops can't flood the log.
    {
        static thread_local std::string last_unimpl_site;
        std::string site = current_class_ + "." + current_method_ + "@" +
                           to_hex(pc);
        if (site != last_unimpl_site) {
            last_unimpl_site = site;
            std::string dump;
            uint32_t lo = (pc >= 4) ? pc - 4 : 0;
            uint32_t hi = (pc + 6 <= bytecode_.size()) ? pc + 6
                                                       : (uint32_t)bytecode_.size();
            for (uint32_t u = lo; u < hi; ++u) {
                char buf[16];
                std::snprintf(buf, sizeof(buf), "%04x ", bytecode_[u] & 0xffff);
                dump += (u == pc) ? std::string("[") + buf + "]"
                                  : std::string(" ") + buf;
            }
            std::cerr << "[UNIMPL-DIAG] " << site
                      << " units[pc-4..pc+5]: " << dump << std::endl;
        }
    }
    
    if (config_.stop_on_unimplemented) {
        halted_ = true;
        halt_reason_ = "Unimplemented opcode: 0x" + to_hex16(opcode) + " at PC=" + to_hex(pc);
    }

    // GP-INT-002 (issue #582): the old resume was unconditionally `pc + 1`,
    // so a multi-unit unsupported opcode resumed INSIDE its operand words
    // (PC desync — every later decode misaligned). Resume law now:
    //   - defined-but-unimplemented opcodes: spec-correct instruction width
    //     (the DEX opcode → size table below), so the next fetch lands on
    //     the next instruction boundary;
    //   - UNDEFINED opcode values (no spec format exists): there IS no
    //     valid boundary — the method halts with a structured unsupported
    //     report instead of silently continuing.
    static const uint8_t kDalvikWidth[256] = {
        1, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 1, 1, 1, 1, 1,  // 0x00-0x0f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 2, 1, 1, 2,  // 0x10-0x1f
        2, 1, 2, 2, 3, 3, 3, 1, 1, 2, 3, 3, 3, 2, 2, 2,  // 0x20-0x2f
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0,  // 0x30-0x3f
        0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0x40-0x4f
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0x50-0x5f
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3,  // 0x60-0x6f
        3, 3, 3, 0, 3, 3, 3, 3, 3, 0, 0, 1, 1, 1, 1, 1,  // 0x70-0x7f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  // 0x80-0x8f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  // 0x90-0x9f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  // 0xa0-0xaf
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0xb0-0xbf
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0xc0-0xcf
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0xd0-0xdf
        2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  // 0xe0-0xef
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3,  // 0xf0-0xff
    };

    const uint8_t w = kDalvikWidth[opcode & 0xFF];
    if (w == 0) {
        // Undefined opcode value: no valid resume boundary exists.
        halted_ = true;
        halt_reason_ = "Undefined opcode 0x" + to_hex16(opcode) + " at PC=" +
                       to_hex(pc) + " — no DEX instruction width exists; "
                       "execution cannot resume at an instruction boundary";
        trace.opcode_name = "undefined(0x" + to_hex16(opcode) + ")";
        return;
    }
    pc_ = pc + w;  // spec-correct boundary for defined-but-unimplemented opcodes
}

// ============================================================================
// Register Helpers
// ============================================================================

void DalvikExecutionEngine::set_register(uint16_t reg, const DalvikValue& value) {
    if (current_registers_) {
        current_registers_->write_v(reg, value);
        current_registers_->set_pc(pc_);
    }
}

// F-028b (M4 §A1) — WIDE-PAIR SLOT LAW implementation. Writes the full
// wide value into vReg and the high 32 bits of its bit pattern into the
// vReg+1 shadow slot (INT32-tagged), exactly mirroring ART's physical
// two-slot layout. Bounds-safe: write_v ignores out-of-range registers.
void DalvikExecutionEngine::set_wide_pair(uint16_t reg, const DalvikValue& value) {
    if (!current_registers_) return;
    current_registers_->write_v(reg, value);
    current_registers_->set_pc(pc_);
    uint64_t bits = 0;
    if (value.type == DalvikType::INT64) {
        bits = static_cast<uint64_t>(value.long_val);
    } else if (value.type == DalvikType::FLOAT64) {
        std::memcpy(&bits, &value.double_val, sizeof(bits));
    } else {
        return; // not a wide value — no shadow to fill
    }
    DalvikValue shadow;
    shadow.type = DalvikType::INT32;
    shadow.int_val = static_cast<int32_t>(static_cast<uint32_t>(bits >> 32));
    current_registers_->write_v(static_cast<uint16_t>(reg + 1), shadow);
}

DalvikValue DalvikExecutionEngine::get_register(uint16_t reg) const {
    if (current_registers_) {
        return current_registers_->read_v(reg);
    }
    return DalvikValue::make_uninit();
}

std::string DalvikExecutionEngine::register_name(uint8_t reg) const {
    if (current_registers_ && reg >= current_registers_->get_ins_count()) {
        return "v" + std::to_string(reg);
    } else if (current_registers_) {
        return "p" + std::to_string(reg - (current_registers_->get_size() - current_registers_->get_ins_count()));
    }
    return "v" + std::to_string(reg);
}

// ============================================================================
// API Bridge
// ============================================================================

// CYCLE-E: parse a DEX method proto "(params)return" into per-param type
// strings. Wide types ('J','D') occupy one param slot but two registers.
std::vector<std::string> parse_proto_param_types(const std::string& proto) {
    std::vector<std::string> types;
    size_t lp = proto.find('(');
    size_t rp = proto.find(')');
    if (lp == std::string::npos || rp == std::string::npos || rp <= lp) return types;
    std::string params = proto.substr(lp + 1, rp - lp - 1);
    size_t i = 0;
    while (i < params.size()) {
        char c = params[i];
        if (c == 'L') {
            size_t semi = params.find(';', i);
            if (semi == std::string::npos) break;
            types.push_back(params.substr(i, semi - i + 1));
            i = semi + 1;
        } else if (c == '[') {
            size_t start = i;
            while (i < params.size() && params[i] == '[') i++;
            if (i < params.size() && params[i] == 'L') {
                size_t semi = params.find(';', i);
                if (semi == std::string::npos) break;
                types.push_back(params.substr(start, semi - start + 1));
                i = semi + 1;
            } else {
                types.push_back(params.substr(start, i - start + 1));
                i += 1;
            }
        } else {
            types.push_back(std::string(1, c));
            i += 1;
        }
    }
    return types;
}

// CYCLE-E: signature-aware invoke argument builder (see forward decl).
std::vector<DalvikValue> build_invoke_args(
    const std::vector<DalvikValue>& raw,
    const std::vector<std::string>& types,
    bool is_static) {
    if (types.empty()) return raw;   // unresolvable proto → legacy passthrough
    std::vector<DalvikValue> args;
    size_t idx = 0;
    if (!is_static) {
        // Receiver slot passes through unchanged (identity must be kept).
        if (raw.empty()) return args;
        args.push_back(raw[0]);
        idx = 1;
    }
    for (const std::string& pt : types) {
        if (pt == "J" || pt == "D") {
            if (idx >= raw.size()) break;   // malformed call — keep what we have
            DalvikValue lo = raw[idx];
            DalvikValue hi = (idx + 1 < raw.size())
                                 ? raw[idx + 1]
                                 : DalvikValue::make_int(0);
            if (lo.type == DalvikType::INT64) {
                if (pt == "D") {
                    double d; int64_t bits = lo.long_val;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                } else {
                    args.push_back(lo);
                }
            } else if (lo.type == DalvikType::FLOAT64) {
                // F-028b wide-pair law: a FLOAT64-tagged slot already holds
                // the FULL 64-bit value (the tagged-union model keeps the
                // whole wide in one register). Reinterpret its bits per the
                // param type instead of union-aliasing int_val (the low 32
                // bits) against the possibly-unwritten shadow register —
                // the defect that turned every delegated double param into
                // a ~1e-315 denormal (dooz TransferFunction IAE).
                if (pt == "D") {
                    args.push_back(lo);
                } else {
                    int64_t bits; std::memcpy(&bits, &lo.double_val, sizeof(bits));
                    args.push_back(DalvikValue::make_long(bits));
                }
            } else {
                int64_t combined = (static_cast<int64_t>(hi.int_val) << 32) |
                                   (static_cast<uint32_t>(lo.int_val));
                if (pt == "D") {
                    double d; int64_t bits = combined;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                } else {
                    args.push_back(DalvikValue::make_long(combined));
                }
            }
            idx += 2;
        } else {
            if (idx >= raw.size()) break;   // malformed call — keep what we have
            DalvikValue v = raw[idx];
            if ((pt[0] == 'L' || pt[0] == '[') &&
                v.type == DalvikType::INT32 && v.int_val == 0) {
                // F-030 (MASTER-5 §A) — ZERO-IS-NULL-AT-REFERENCE-USE LAW.
                // Dalvik registers are untyped 32-bit slots (F-028 law);
                // `const/4 vX, #0` loads the POLYMORPHIC zero word, which
                // is an int 0 in a primitive context and the NULL REFERENCE
                // in a reference context. ART's verifier materializes this
                // as the `Zero` reg-type, convertible to ANY reference type
                // (art/runtime/verifier/reg types: Zero -> any ref). The
                // tagged-union engine must therefore re-type an INT32(0)
                // argument as null when the callee's declared param type is
                // a reference (L...; or [...). Without this law the null
                // crosses the invoke boundary tagged INT32(0) and every
                // identity-sensitive consumer (AtomicReferenceArray CAS,
                // == compares) sees boxed-int-0 instead of null — the
                // first real-APK hit: dooz LY1/b;.D passes const/4 #0 as
                // the `expected` state of Segment cell CAS (LY1/j;.j) and
                // the lock-free state machine spins forever because the
                // CAS can never match (correct F-028h identity law: null
                // is not boxed Integer 0). No app special-casing: every
                // real DEX that passes const/4 null into object params
                // benefits (the standard Kotlin/Java `null` idiom).
                args.push_back(DalvikValue::make_null());
            } else if (pt == "F" && v.type == DalvikType::INT32) {
                // EXP-095 CM-019 law: float params arrive as raw bits.
                float f; int32_t bits = v.int_val;
                std::memcpy(&f, &bits, sizeof(f));
                args.push_back(DalvikValue::make_float(f));
            } else if (v.type == DalvikType::INT32) {
                // CHAR-PROBE campaign: signature-aware primitive retyping.
                // DEX registers are untyped; the proto's param char is the
                // only authority. Without this, char params leak their int
                // code into string concat ("88" for 'X') and boolean params
                // print "0"/"1" instead of "true"/"false".
                switch (pt.empty() ? 'I' : pt[0]) {
                    case 'C': {
                        DalvikValue c = v;
                        c.type = DalvikType::CHAR;
                        c.int_val &= 0xFFFF;
                        args.push_back(c);
                        break;
                    }
                    case 'Z':
                        args.push_back(DalvikValue::make_bool(v.int_val != 0));
                        break;
                    case 'B': {
                        DalvikValue b = v;
                        b.type = DalvikType::BYTE;
                        b.int_val = static_cast<int8_t>(v.int_val & 0xFF);
                        args.push_back(b);
                        break;
                    }
                    case 'S': {
                        DalvikValue s = v;
                        s.type = DalvikType::SHORT;
                        s.int_val = static_cast<int16_t>(v.int_val & 0xFFFF);
                        args.push_back(s);
                        break;
                    }
                    default:
                        args.push_back(v);
                        break;
                }
            } else {
                args.push_back(v);
            }
            idx += 1;
        }
    }
    return args;
}

// CYCLE-E: AOSP framework enum constant ordinals. The android.* framework
// is NOT defined in app DEX files, so framework enum <clinit> never runs
// and sget-object of e.g. Paint$Style.STROKE materialized NULL — breaking
// Paint.setStyle / Path.setFillType / PorterDuff modes for every real
// drawing call. Ordinals below are the fixed AOSP declaration orders.
static const miniandroid::dalvik::KvInt kOrdinals[] = {
    {"Landroid/graphics/Paint$Style;.FILL", 0},
    {"Landroid/graphics/Paint$Style;.STROKE", 1},
    {"Landroid/graphics/Paint$Style;.FILL_AND_STROKE", 2},
    {"Landroid/graphics/Paint$Cap;.BUTT", 0},
    {"Landroid/graphics/Paint$Cap;.ROUND", 1},
    {"Landroid/graphics/Paint$Cap;.SQUARE", 2},
    {"Landroid/graphics/Paint$Join;.MITER", 0},
    {"Landroid/graphics/Paint$Join;.ROUND", 1},
    {"Landroid/graphics/Paint$Join;.BEVEL", 2},
    {"Landroid/graphics/Paint$Align;.LEFT", 0},
    {"Landroid/graphics/Paint$Align;.CENTER", 1},
    {"Landroid/graphics/Paint$Align;.RIGHT", 2},
    {"Landroid/graphics/Path$FillType;.WINDING", 0},
    {"Landroid/graphics/Path$FillType;.EVEN_ODD", 1},
    {"Landroid/graphics/Path$FillType;.INVERSE_WINDING", 2},
    {"Landroid/graphics/Path$FillType;.INVERSE_EVEN_ODD", 3},
    {"Landroid/graphics/Path$Direction;.CCW", 0},
    {"Landroid/graphics/Path$Direction;.CW", 1},
    {"Landroid/graphics/PorterDuff$Mode;.CLEAR", 0},
    {"Landroid/graphics/PorterDuff$Mode;.SRC", 1},
    {"Landroid/graphics/PorterDuff$Mode;.DST", 2},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_OVER", 3},
    {"Landroid/graphics/PorterDuff$Mode;.DST_OVER", 4},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_IN", 5},
    {"Landroid/graphics/PorterDuff$Mode;.DST_IN", 6},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_OUT", 7},
    {"Landroid/graphics/PorterDuff$Mode;.DST_OUT", 8},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_ATOP", 9},
    {"Landroid/graphics/PorterDuff$Mode;.DST_ATOP", 10},
    {"Landroid/graphics/PorterDuff$Mode;.XOR", 11},
    {"Landroid/graphics/PorterDuff$Mode;.DARKEN", 12},
    {"Landroid/graphics/PorterDuff$Mode;.LIGHTEN", 13},
    {"Landroid/graphics/PorterDuff$Mode;.MULTIPLY", 14},
    {"Landroid/graphics/PorterDuff$Mode;.SCREEN", 15},
    {"Landroid/graphics/PorterDuff$Mode;.ADD", 16},
    {"Landroid/graphics/PorterDuff$Mode;.OVERLAY", 17},
    {"Landroid/graphics/Shader$TileMode;.CLAMP", 0},
    // S108 ROOT-022: java.nio.ByteOrder constants (OpenJDK order: BIG_ENDIAN
    // declared first). Telegram's NativeByteBuffer ctor does
    // ByteBuffer.allocate(n).order(ByteOrder.LITTLE_ENDIAN) — the sget of
    // LITTLE_ENDIAN answered NULL and order() NPE'd, killing every
    // ByteBuffer write path (NativeByteBuffer.writeInt32 chain).
    {"Ljava/nio/ByteOrder;.BIG_ENDIAN", 0},
    {"Ljava/nio/ByteOrder;.LITTLE_ENDIAN", 1},
    {"Landroid/graphics/Shader$TileMode;.REPEAT", 1},
    {"Landroid/graphics/Shader$TileMode;.MIRROR", 2},
    {"Landroid/graphics/Region$Op;.DIFFERENCE", 0},
    {"Landroid/graphics/Region$Op;.INTERSECT", 1},
    {"Landroid/graphics/Region$Op;.UNION", 2},
    {"Landroid/graphics/Region$Op;.XOR", 3},
    {"Landroid/graphics/Region$Op;.REVERSE_DIFFERENCE", 4},
    {"Landroid/graphics/Region$Op;.REPLACE", 5},
    {"Landroid/graphics/Bitmap$Config;.ALPHA_8", 0},
    {"Landroid/graphics/Bitmap$Config;.RGB_565", 1},
    {"Landroid/graphics/Bitmap$Config;.ARGB_4444", 2},
    {"Landroid/graphics/Bitmap$Config;.ARGB_8888", 3},
    // F-NEW-351: the full AOSP Bitmap.Config family (Bitmap.java decl
    // order; API 26+ adds RGBA_F16, API 26 adds HARDWARE). The compose
    // ImageBitmap config converter consults these by name — the two
    // missing members answered null in the dooz v23 icon draw.
    {"Landroid/graphics/Bitmap$Config;.RGBA_F16", 4},
    {"Landroid/graphics/Bitmap$Config;.HARDWARE", 5},
    // F-NEW-351: the FULL AOSP android.graphics.BlendMode family
    // (BlendMode.java declaration order — API 29). Paint.setBlendMode
    // consumers (compose DrawCache.clear = drawRect(Black, BlendMode
    // .Clear) — the vector-icon cache reset) previously sget NULL: the
    // blend mode never recorded and the cache reset painted SOLID BLACK
    // (the dooz material-icon black squares). Same table drives the sget
    // constant law → identity coherent with enum_arg_ordinal.
    {"Landroid/graphics/BlendMode;.CLEAR", 0},
    {"Landroid/graphics/BlendMode;.SRC", 1},
    {"Landroid/graphics/BlendMode;.DST", 2},
    {"Landroid/graphics/BlendMode;.SRC_OVER", 3},
    {"Landroid/graphics/BlendMode;.DST_OVER", 4},
    {"Landroid/graphics/BlendMode;.SRC_IN", 5},
    {"Landroid/graphics/BlendMode;.DST_IN", 6},
    {"Landroid/graphics/BlendMode;.SRC_OUT", 7},
    {"Landroid/graphics/BlendMode;.DST_OUT", 8},
    {"Landroid/graphics/BlendMode;.SRC_ATOP", 9},
    {"Landroid/graphics/BlendMode;.DST_ATOP", 10},
    {"Landroid/graphics/BlendMode;.XOR", 11},
    {"Landroid/graphics/BlendMode;.DARKEN", 12},
    {"Landroid/graphics/BlendMode;.LIGHTEN", 13},
    {"Landroid/graphics/BlendMode;.MULTIPLY", 14},
    {"Landroid/graphics/BlendMode;.SCREEN", 15},
    {"Landroid/graphics/BlendMode;.PLUS", 16},
    {"Landroid/graphics/BlendMode;.OVERLAY", 17},
    {"Landroid/graphics/BlendMode;.REDUCE", 18},
    {"Landroid/view/View$Visibility;.VISIBLE", 0},
    {"Landroid/view/View$Visibility;.INVISIBLE", 1},
    {"Landroid/view/View$Visibility;.GONE", 2},
    // F-NEW-216 ENUM-CONSTANT NAME LAW (OpenJDK TimeUnit.java): the member
    // is NANOSECONDS — "NANOS" is java.time.temporal.ChronoUnit's name and
    // TimeUnit has no such member. The fictional name made every sget of
    // TimeUnit.NANOSECONDS answer null (droidify face: kotlin toDuration
    // NPE'd on the null receiver inside the Dagger SettingsSerializer
    // chain — datastore settings never built, app died far from cause).
    {"Ljava/util/concurrent/TimeUnit;.NANOSECONDS", 0},
    {"Ljava/util/concurrent/TimeUnit;.MICROSECONDS", 1},
    {"Ljava/util/concurrent/TimeUnit;.MILLISECONDS", 2},
    {"Ljava/util/concurrent/TimeUnit;.SECONDS", 3},
    {"Ljava/util/concurrent/TimeUnit;.MINUTES", 4},
    {"Ljava/util/concurrent/TimeUnit;.HOURS", 5},
    {"Ljava/util/concurrent/TimeUnit;.DAYS", 6},
    {"Landroid/text/TextUtils$TruncateAt;.START", 0},
    {"Landroid/text/TextUtils$TruncateAt;.MIDDLE", 1},
    {"Landroid/text/TextUtils$TruncateAt;.END", 2},
    {"Landroid/text/TextUtils$TruncateAt;.MARQUEE", 3},
    {"Landroid/text/TextUtils$TruncateAt;.END_SMALL", 4},
    {"Landroid/widget/ImageView$ScaleType;.MATRIX", 0},
    {"Landroid/widget/ImageView$ScaleType;.FIT_XY", 1},
    {"Landroid/widget/ImageView$ScaleType;.FIT_START", 2},
    {"Landroid/widget/ImageView$ScaleType;.FIT_CENTER", 3},
    {"Landroid/widget/ImageView$ScaleType;.FIT_END", 4},
    {"Landroid/widget/ImageView$ScaleType;.CENTER", 5},
    {"Landroid/widget/ImageView$ScaleType;.CENTER_CROP", 6},
    {"Landroid/widget/ImageView$ScaleType;.CENTER_INSIDE", 7},
    // 371-CLOSEOUT: java.lang.Thread.State (OpenJDK Thread.java declaration
    // order) — Thread.State.values()/valueOf() used by thread-pool and
    // lifecycle inspection code across real apps.
    {"Ljava/lang/Thread$State;.NEW", 0},
    {"Ljava/lang/Thread$State;.RUNNABLE", 1},
    {"Ljava/lang/Thread$State;.BLOCKED", 2},
    {"Ljava/lang/Thread$State;.WAITING", 3},
    {"Ljava/lang/Thread$State;.TIMED_WAITING", 4},
    {"Ljava/lang/Thread$State;.TERMINATED", 5},
    // F-NEW-295 (CONT-35): android.text.Layout$Alignment — AOSP Layout.java
    // declaration order, decoded instruction-level from the toolchain's
    // android-34.jar clinit (ALIGN_NORMAL=0, ALIGN_OPPOSITE=1,
    // ALIGN_CENTER=2; NO ALIGN_LEFT/ALIGN_RIGHT members exist on this API
    // level). Compose's R8-inlined text-layout alignment resolver
    // (composeStopwatch Ljd1;.<clinit>) calls Layout.Alignment.values(),
    // searches the array for the names "ALIGN_LEFT"/"ALIGN_RIGHT" and falls
    // back to the ALIGN_NORMAL sget when absent — but with no table rows
    // the 371-CLOSEOUT values() arm found no constants and answered NULL,
    // so the clinit's array-length (pc=6) NPE'd and the text pass aborted.
    // Same table drives the sget constant law → identity coherent.
    {"Landroid/text/Layout$Alignment;.ALIGN_NORMAL", 0},
    {"Landroid/text/Layout$Alignment;.ALIGN_OPPOSITE", 1},
    {"Landroid/text/Layout$Alignment;.ALIGN_CENTER", 2},
};
int framework_enum_ordinal(const std::string& class_desc,
                                  const std::string& field_name) {
    return kvint_table_find(kOrdinals, sizeof(kOrdinals) / sizeof(kOrdinals[0]),
                            class_desc + "." + field_name, -1);
}

// 371-CLOSEOUT: framework-enum static accessor support. Returns the ORDERED
// (ordinal, name) constant list for a framework enum class by scanning the
// kOrdinals table above (entries are "Lcls;.NAME", ordinal). Art/Android
// semantics: every enum class has values() → the constants in declaration
// order, and valueOf(String) → the matching constant. The same table drives
// sget constant materialization, so identity is coherent across accessors.
std::vector<std::pair<int, std::string>>
framework_enum_constants(const std::string& class_desc) {
    std::vector<std::pair<int, std::string>> out;
    const std::string prefix = class_desc + ".";
    const size_t kTableSize = sizeof(kOrdinals) / sizeof(kOrdinals[0]);
    for (size_t i = 0; i < kTableSize; ++i) {
        std::string key = kOrdinals[i].k;
        if (key.rfind(prefix, 0) == 0) {
            out.emplace_back(kOrdinals[i].v, key.substr(prefix.size()));
        }
    }
    std::sort(out.begin(), out.end(),
              [](const std::pair<int, std::string>& a,
                 const std::pair<int, std::string>& b) {
                  return a.first < b.first;
              });
    return out;
}

// F-110e (S62+): framework static INT constant table (AOSP values).
// The sget (int) opcode on android.* static final ints previously fell to
// the typed-zero default because the class is not in app DEX and its
// <clinit> never runs. MotionEvent.ACTION_DOWN (0) compared correctly by
// accident, but every non-zero constant (ACTION_UP=1, MOVE=2, CANCEL=3)
// compared false — a touch listener's `event.getAction() == ACTION_UP`
// arm could never fire. Table = AOSP MotionEvent.java values.
int framework_static_int(const std::string& class_desc,
                                const std::string& field_name) {
    static const miniandroid::dalvik::KvInt kStaticInts[] = {
    {"Landroid/view/MotionEvent;.ACTION_DOWN", 0},
    {"Landroid/view/MotionEvent;.ACTION_UP", 1},
    {"Landroid/view/MotionEvent;.ACTION_MOVE", 2},
    {"Landroid/view/MotionEvent;.ACTION_CANCEL", 3},
    {"Landroid/view/MotionEvent;.ACTION_OUTSIDE", 4},
    {"Landroid/view/MotionEvent;.ACTION_POINTER_DOWN", 5},
    {"Landroid/view/MotionEvent;.ACTION_POINTER_UP", 6},
    {"Landroid/view/MotionEvent;.ACTION_MASK", 255},
    // S129 (R-NEW-425, CAP-INPUT-108): AOSP MotionEvent axis constants —
    // VelocityTracker.getAxisVelocity(AXIS_X|AXIS_Y) and the planar-axis
    // set in the native tracker law (VelocityTracker.cpp PLANAR_AXES).
    {"Landroid/view/MotionEvent;.AXIS_X", 0},
    {"Landroid/view/MotionEvent;.AXIS_Y", 1},
    {"Landroid/view/MotionEvent;.AXIS_SCROLL", 26},
    // S123 ROOT-CALC-B — android.view.Gravity constant family (AOSP
    // Gravity.java law). sget of Gravity.TOP in the lib chain previously
    // fell through every synthesis arm and answered NULL_REF; the null
    // register became TypedArray.getInt's defValue slot (non-INT32 →
    // default 0) and SlidingUpPanelLayout.setGravity(0) threw
    // IllegalArgumentException "gravity must be set to either top or
    // bottom" at the calculator's first inflate. AOSP values:
    //   LEFT = AXIS_SPECIFIED|AXIS_PULL_BEFORE<<AXIS_X_SHIFT = 3
    //   TOP  = AXIS_SPECIFIED|AXIS_PULL_BEFORE<<AXIS_Y_SHIFT = 48
    //   END/START carry RELATIVE_HORIZONTAL_GRAVITY (0x00800000).
    {"Landroid/view/Gravity;.NO_GRAVITY", 0},
    {"Landroid/view/Gravity;.LEFT", 3},
    {"Landroid/view/Gravity;.RIGHT", 5},
    {"Landroid/view/Gravity;.TOP", 48},
    {"Landroid/view/Gravity;.BOTTOM", 80},
    {"Landroid/view/Gravity;.CENTER_VERTICAL", 16},
    {"Landroid/view/Gravity;.CENTER_HORIZONTAL", 1},
    {"Landroid/view/Gravity;.CENTER", 17},
    {"Landroid/view/Gravity;.FILL_VERTICAL", 112},
    {"Landroid/view/Gravity;.FILL_HORIZONTAL", 7},
    {"Landroid/view/Gravity;.FILL", 119},
    {"Landroid/view/Gravity;.CLIP_VERTICAL", 128},
    {"Landroid/view/Gravity;.CLIP_HORIZONTAL", 8},
    {"Landroid/view/Gravity;.START", 8388611},       // 0x00800003
    {"Landroid/view/Gravity;.END", 8388613},         // 0x00800005
    {"Landroid/view/Gravity;.RELATIVE_LAYOUT_DIRECTION", 8388608},
    {"Landroid/view/Gravity;.DISPLAY_CLIP_VERTICAL", 0x10000000},
    {"Landroid/view/Gravity;.DISPLAY_CLIP_HORIZONTAL", 0x01000000},
    // S83-GFX-BASE §24/§25: GL constants (GL10 = ES1.0; GLES20 shares the
    // buffer-bit values). l6 evidence: GL10.GL_COLOR_BUFFER_BIT sget
    // resolved 0 → glClear(0) → GL_INVALID_VALUE → black frame.
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_COLOR_BUFFER_BIT", 0x4000},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_DEPTH_BUFFER_BIT", 0x100},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_STENCIL_BUFFER_BIT", 0x400},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_ACCUM_BUFFER_BIT", 0x200},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRUE", 1},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_FALSE", 0},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_BLEND", 0x0BE2},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TEXTURE_2D", 0x0DE1},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_DEPTH_TEST", 0x0B71},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_ALPHA_TEST", 0x0BC0},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_SRC_ALPHA", 0x0302},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_ONE_MINUS_SRC_ALPHA", 0x0303},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRIANGLES", 0x0004},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRIANGLE_STRIP", 0x0005},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRIANGLE_FAN", 0x0006},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_VERTEX_ARRAY", 0x8074},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_COLOR_ARRAY", 0x8076},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TEXTURE_COORD_ARRAY", 0x8078},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_MODELVIEW", 0x1700},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_PROJECTION", 0x1701},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_FLOAT", 0x1406},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_UNSIGNED_SHORT", 0x1403},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_UNSIGNED_BYTE", 0x1401},
    {"Landroid/opengl/GLES20;.GL_COLOR_BUFFER_BIT", 0x4000},
    {"Landroid/opengl/GLES20;.GL_DEPTH_BUFFER_BIT", 0x100},
    {"Landroid/opengl/GLES20;.GL_STENCIL_BUFFER_BIT", 0x400},
    {"Landroid/opengl/GLES20;.GL_TRUE", 1},
    {"Landroid/opengl/GLES20;.GL_FALSE", 0},
    {"Landroid/opengl/GLES20;.GL_FLOAT", 0x1406},
    {"Landroid/opengl/GLES20;.GL_TRIANGLES", 0x0004},
    {"Landroid/opengl/GLES20;.GL_TRIANGLE_STRIP", 0x0005},
    {"Landroid/opengl/GLES20;.GL_TRIANGLE_FAN", 0x0006},
    {"Landroid/opengl/GLES20;.GL_VERTEX_SHADER", 0x8B31},
    {"Landroid/opengl/GLES20;.GL_FRAGMENT_SHADER", 0x8B30},
    {"Landroid/opengl/GLES20;.GL_ARRAY_BUFFER", 0x8892},
    {"Landroid/opengl/GLES20;.GL_STATIC_DRAW", 0x88E4},
    {"Landroid/opengl/GLES20;.GL_TEXTURE_2D", 0x0DE1},
    {"Landroid/opengl/GLES20;.GL_RGBA", 0x1908},
    {"Landroid/opengl/GLES20;.GL_RGB", 0x1907},
    {"Landroid/opengl/GLES20;.GL_UNSIGNED_BYTE", 0x1401},
    {"Landroid/opengl/GLES20;.GL_SRC_ALPHA", 0x0302},
    {"Landroid/opengl/GLES20;.GL_ONE_MINUS_SRC_ALPHA", 0x0303},
    };
    const std::string key = class_desc + "." + field_name;
    for (const auto& e : kStaticInts)
        if (key == e.k) return e.v;
    if (std::getenv("MINIANDROID_S83_DEBUG") &&
        key.find("GL") != std::string::npos)
        std::cerr << "[S83-STATIC-MISS] " << class_desc << "." << field_name
                  << std::endl;
    return -1;
}

// EXP-051: Convert a DalvikValue (engine type) into a CallContext::Arg
// (shadow-registry type). This is the only translation point — keeping
// the engine and the shadow registry decoupled.
framework::CallContext::Arg dalvik_value_to_arg(const DalvikValue& v) {
    using namespace framework;
    CallContext::Arg a;
    switch (v.type) {
        case DalvikType::INT32:
        case DalvikType::BYTE:
        case DalvikType::SHORT:
        case DalvikType::CHAR:
            a.kind = CallContext::Arg::Kind::INT;
            a.int_val = v.int_val;
            break;
        case DalvikType::INT64:
            a.kind = CallContext::Arg::Kind::LONG;
            a.long_val = v.long_val;
            break;
        case DalvikType::FLOAT32:
            a.kind = CallContext::Arg::Kind::FLOAT;
            a.float_val = v.float_val;
            break;
        case DalvikType::FLOAT64:
            a.kind = CallContext::Arg::Kind::DOUBLE;
            a.double_val = v.double_val;
            break;
        case DalvikType::BOOLEAN:
            a.kind = CallContext::Arg::Kind::BOOL;
            a.bool_val = v.bool_val;
            break;
        case DalvikType::STRING_REF:
            a.kind = CallContext::Arg::Kind::STRING;
            a.string_val = v.string_val;
            break;
        case DalvikType::OBJECT_REF:
            a.kind = CallContext::Arg::Kind::OBJECT;
            a.object_id = v.object_id;
            a.object_class = v.class_desc;
            // EXP-091: Also copy string_val — when a String object is passed
            // as an argument (e.g., setText(stringFromLocaleController)),
            // the DalvikValue may have BOTH object_id AND string_val set.
            // The string_val comes from const-string/move-result-object paths
            // where the engine stores the resolved string alongside the ref.
            // Without this, arg_as_string() returns empty for OBJECT args,
            // causing setText(CharSequence) to set empty text on ViewShadow nodes.
            a.string_val = v.string_val;
            break;
        case DalvikType::NULL_REF:
            a.kind = CallContext::Arg::Kind::NULL_REF;
            break;
        case DalvikType::CLASS_REF:
            // MASTER-2 FIX-INTENT-001 (AOSP Intent(Context, Class) law):
            // const-class materializes a Class object whose descriptor is
            // the component identity. Folding CLASS_REF to NULL dropped the
            // descriptor, so Intent(Context, NoteEdit.class) left the
            // component UNSET and startActivity reported ACTIVITY_NOT_FOUND
            // (unote addNote). Carry the descriptor on the arg.
            // F-089 (R-NEW-315): Class IDENTITY law for key/hash surfaces.
            // OpenJDK: a Class object is a SINGLETON per class+loader — all
            // references to X.class are the SAME object and compare
            // equal. The engine materializes a fresh token per evaluation
            // (ref_id = instruction sequence), so identity-keyed surfaces
            // (map caches keyed by Class — androidx.navigation
            // NavigatorProvider's name cache, WeakHashMap<Class,...>)
            // collapsed: every lookup missed, and when ref_id collided at
            // 0 the cache returned the FIRST class's value for EVERY class
            // (dooz: all navigators cached under the name "navigation" →
            // getNavigator("composable") → ISE → composition death).
            // The descriptor IS the deterministic identity: carry it in
            // string_val so arg_as_string()/key builders use it.
            a.kind = CallContext::Arg::Kind::OBJECT;
            a.object_id = v.ref_id;
            a.object_class = v.class_desc;
            a.string_val = v.class_desc;
            break;
        default:
            // VOID_, UNINITIALIZED, REGISTER_UNSET.
            // Default to NULL_REF (treated as null object) which is
            // safe for most call sites.
            a.kind = CallContext::Arg::Kind::NULL_REF;
            break;
    }
    return a;
}

// EXP-051: Convert a CallResult (shadow-registry type) back into a
// DalvikValue (engine type).
DalvikValue call_result_to_dalvik(const framework::CallResult& r) {
    using namespace framework;
    switch (r.ret_kind) {
        case CallResult::RetKind::INT:     return DalvikValue::make_int(r.int_val);
        case CallResult::RetKind::LONG:    return DalvikValue::make_long(r.long_val);
        case CallResult::RetKind::FLOAT:   return DalvikValue::make_float(r.float_val);
        case CallResult::RetKind::DOUBLE:  return DalvikValue::make_double(r.double_val);
        case CallResult::RetKind::BOOL:    return DalvikValue::make_bool(r.bool_val);
        case CallResult::RetKind::STRING:  return DalvikValue::make_string(r.string_val, r.object_id);
        case CallResult::RetKind::OBJECT:  return DalvikValue::make_object(r.object_id, r.object_class);
        case CallResult::RetKind::NULL_REF:return DalvikValue::make_null();
        case CallResult::RetKind::VOID:
        default:                           return DalvikValue::make_void();
    }
}

// ────────────────────────────────────────────────────────────────────────
// F-105 (S59, R-NEW-379) — NOTE on the failed re-homing design: re-homing
// contradicted shadow references onto heap proxies was prototyped and
// REJECTED — the proxy id breaks the NEXT shadow hop (getTag/getParent on
// the proxy id find no ViewShadow node — the entity's id IS the shadow
// table key). The law lives in execute_instance_of instead: reconcile the
// register's creation-site class declaration with the heap record there.
// ────────────────────────────────────────────────────────────────────────

bool DalvikExecutionEngine::try_shadow_dispatch(const std::string& class_name,
                                                const std::string& method,
                                                const std::vector<DalvikValue>& args,
                                                DalvikValue& result,
                                                ApiCallTrace::Status& status) {
    if (shadow_registry_ == nullptr) return false;
    // F-NEW-267 (CONT-61): TOUCH-WINDOW BRIDGE probe — every bridge call the
    // dispatched DEX touch override makes (env-gated, bounded). Answers
    // which framework answers the compose input pipeline asked for and
    // which silently typed-defaulted (the consumed=false decode).
    if (touch_dispatch_active_) {
        static thread_local const bool tw_on =
            diag_env("MINIANDROID_TOUCH_WINDOW_TRACE");
        static thread_local uint64_t tw_n = 0;
        if (tw_on && tw_n++ < 400)
            std::cerr << "[TOUCHWIN-BRIDGE] " << class_name << "." << method
                      << " argc=" << args.size()
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
    }
    // F-NEW-344 probe (CONT-61): every Landroid/text/Layout; bridge call —
    // the compose text intrinsic leg (getDesiredWidth family). Answers
    // whether the intrinsic path reaches the engine and with what args.
    if (class_name == "Landroid/text/Layout;") {
        static thread_local uint64_t lay_n = 0;
        if (lay_n++ < 40) {
            std::cerr << "[F344-LAYOUT] " << method
                      << " argc=" << args.size()
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
    }
    // CONT-36 (F-NEW-297 evidence): DRAW-OP ATTRIBUTION — env-gated,
    // bounded. Every Canvas draw-primitive bridge call INSIDE the
    // custom-view draw window, with the EXECUTING DEX caller. Answers
    // which DEX site records the frame canvas ops (the Compose draw walk
    // stops before the text path — where exactly?).
    {
        static thread_local const bool cdw_on =
            diag_env("MINIANDROID_CANVAS_DRAW_WIN_TRACE");
        static const char* cdw_faces[] = {
            "drawColor", "drawRect", "drawRoundRect", "drawCircle",
            "drawLine", "drawText", "drawTextRun", "drawPosText",
            "drawPath", "drawBitmap", "drawArc", "drawOval",
            "drawPoints", "drawLines", "saveLayer", "clipRect", "clipPath"};
        if (cdw_on && draw_window_active_) {
            for (const char* f : cdw_faces) {
                if (method == f) {
                    static thread_local uint64_t cdw_n = 0;
                    if (cdw_n++ < 400)
                        std::cerr << "[CDW-OP] " << class_name << "."
                                  << method << " caller=" << current_class_
                                  << "." << current_method_ << " recv="
                                  << (!args.empty() ? args[0].object_id : 0u)
                                  << std::endl;
                    break;
                }
            }
        }
    }
    // LAW-C/E/F DETERMINATION DIAG (CONT-18, bounded 60/env-gated): every
    // try_shadow_dispatch entry for a Java-8 default-method / view / stream
    // face — answers which class_name the engine routes, with which
    // receiver, and (paired with the CollectionShadow entry diag) whether
    // the collection shadow even sees the call.
    {
        static const bool lawcef_on =
            diag_env("MINIANDROID_LAWCEF_TRACE");
        static const char* lawcef_faces[] = {
            "removeIf", "getOrDefault", "forEach", "merge",
            "computeIfAbsent", "compute", "sort", "removeAll",
            "retainAll", "subList", "stream", "streamOf",
            "remove", "containsKey", "size", "of", "filter", "collect", "toList"};
        if (lawcef_on) {
            for (const char* f : lawcef_faces) {
                if (method == f) {
                    static thread_local uint64_t lawcef_n = 0;
                    if (lawcef_n++ < 60)
                        std::cerr << "[LAWCEF-ENG] " << class_name << "."
                                  << method << " recv="
                                  << (!args.empty() ? args[0].object_id : 0u)
                                  << " cls="
                                  << (!args.empty() ? std::string(args[0].class_desc)
                                                    : std::string("-"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    break;
                }
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────
    // S81 FIX-1 (VF-DIALOG-ITEMS) — dual-view of the bridge_to_api law:
    // AlertDialog$Builder.setItems reaches the DialogShadow through THIS
    // dispatch path when the receiver's runtime class is in the DEX index
    // (the bridge_to_api copy only covers the class-miss fallthrough, the
    // same two-view shape as R-NEW-339 getSystemService). Materialize the
    // heap array into the builder window's items BEFORE the shadow runs so
    // the dialog paints real item rows; the shadow still records the
    // listener + choice state afterwards.
    // ────────────────────────────────────────────────────────────────────
    if (method == "setItems" &&
        class_name.find("AlertDialog$Builder") != std::string::npos &&
        args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0 &&
        args[1].type == DalvikType::OBJECT_REF && args[1].object_id != 0) {
        uint32_t arr_id = args[1].object_id;
        auto len_f = heap_.get_object_field(arr_id, "__array_length__");
        if (!len_f.has_value() || len_f->type != DalvikType::INT32)
            len_f = heap_.get_object_field(arr_id, "__new_array_length__");
        int32_t n_items = (len_f.has_value() && len_f->type == DalvikType::INT32)
                              ? len_f->int_val : 0;
        if (n_items > 0 && n_items < 512) {
            auto* dsh = shadow_registry_->find_as<framework::DialogShadow>();
            framework::DialogWindow* win =
                dsh ? dsh->window_by_obj(args[0].object_id) : nullptr;
            if (win) {
                win->items.clear();
                for (int32_t i = 0; i < n_items; ++i) {
                    auto el = heap_.get_object_field(
                        arr_id, "array[" + std::to_string(i) + "]");
                    if (el.has_value() && el->type == DalvikType::STRING_REF)
                        win->items.push_back(el->string_val);
                    else if (el.has_value() && el->type == DalvikType::OBJECT_REF &&
                             el->object_id != 0) {
                        auto st = heap_.get_object_field(el->object_id, "s");
                        if (st.has_value() && st->type == DalvikType::STRING_REF)
                            win->items.push_back(st->string_val);
                    }
                }
                std::cerr << "[S81-DIALOG-ITEMS] materialized "
                          << win->items.size() << "/" << n_items
                          << " items for builder obj=" << args[0].object_id
                          << std::endl;
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────
    // R-NEW-339 companion law: Context.getSystemService(Class) must resolve
    // in BOTH dispatch layers. The bridge_to_api copy is only reached via
    // the class-miss fallthrough; when the receiver's runtime class IS in
    // class_info_index_ (ContextWrapper/ContextThemeWrapper-family or any
    // app Context subclass) the dex-body lookup fails differently and the
    // bridge block can be bypassed — the call then answered null, and
    // Compose's AndroidComposeView ctor checkNotNull
    // (getSystemService(AutofillManager::class.java)) threw
    // "Required value was null." on the second fetch (first fetch resolved,
    // producing exactly ONE [EXP093-SVC] autofill line — the dooz marker).
    // Same registry, two views — identical to the bridge_to_api block.
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-197 CONFIG-CONTEXT dual-view law (companion to R-NEW-339):
    // Context.createConfigurationContext(Configuration) must NEVER answer
    // null for ANY context-family receiver. AOSP ContextImpl returns a
    // fresh Context sharing the base's resources identity with the override
    // configuration applied. Live evidence (opencalculator vc53):
    //   Lg/m (AppCompatActivity).attachBaseContext pc=180
    //     createConfigurationContext → pc=184 .getResources() NPE (f141),
    //   Ll/c (ContextThemeWrapper).getResources pc=39 → pc=43 .getResources()
    //     NPE on the unimplemented answer. The appcompat day-night attach
    //     chain aborts → activity never builds its ViewTree → white frame.
    // Identity: one FRESH context object per call (AOSP ContextImpl law —
    // never a shared singleton); the S110 base-context map records the
    // receiver so downstream getBaseContext/getResources resolve.
    // ────────────────────────────────────────────────────────────────────
    if (method == "createConfigurationContext") {
        uint32_t base_recv =
            (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                ? args[0].object_id
                : 0;
        if (base_recv != 0) {
            uint32_t derived = heap_.allocate("Landroid/content/Context;",
                                              pc_, 0);
            uint32_t override_cfg = 0;
            if (args.size() >= 2 &&
                args[1].type == DalvikType::OBJECT_REF)
                override_cfg = args[1].object_id;
            if (auto* ash =
                    shadow_registry_->find_as<framework::ActivityShadow>())
                ash->record_config_context(derived, base_recv, override_cfg);
            result = DalvikValue::make_object(derived,
                                              "Landroid/content/Context;");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
    }
    if (method == "getSystemService") {
        // F-NEW-713 diag (PIC R339 site): entry probe — every gss reaching
        // this law prints its arg shape (capped), so a silent miss is
        // visible (farmerbb/Notepad autofill helper ISE evidence).
        static thread_local uint64_t f713p_n = 0;
        if (f713p_n++ < 16) {
            std::cerr << "[F713P-GSS] receiver=" << class_name
                      << " argc=" << args.size();
            if (args.size() >= 2)
                std::cerr << " arg1_type=" << static_cast<int>(args[1].type)
                          << " arg1_desc=" << args[1].class_desc
                          << " arg1_str=" << args[1].string_val;
            std::cerr << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
        // R-NEW-540 guard fix (CONT-36, site A): substring-only guard
        // missed Application/Service receivers whose runtime class lacks
        // the literal "Context"/"Activity" (the S85-FIX law shape — AOSP:
        // every Context-family instance answers getSystemService). chompass
        // live: receiver = the app Application class → the "jobscheduler"
        // map entry never consulted → null → SystemJobScheduler death.
        bool gss_ctx540 =
            class_name.find("Context") != std::string::npos ||
            class_name.find("Activity") != std::string::npos;
        if (!gss_ctx540) {
            static const char* const kGssRoots540[] = {
                "Landroid/content/Context;",
                "Landroid/app/Activity;",
                "Landroid/app/Application;",
                "Landroid/app/Service;",
                "Landroid/view/View;",
                "Landroid/view/ViewGroup;"};
            for (const char* root : kGssRoots540) {
                if (is_subclass_of(class_name, root)) {
                    gss_ctx540 = true;
                    break;
                }
            }
        }
        if (gss_ctx540) {
        std::string svc_name339;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            svc_name339 = args[1].string_val;
        } else if (args.size() >= 2 && args[1].type == DalvikType::CLASS_REF) {
            static const miniandroid::dalvik::KvPair t_svc_cls339[] = {
    {"Landroid/view/WindowManager;", "window"},
    {"Landroid/view/LayoutInflater;", "layout_inflater"},
    {"Landroid/app/ActivityManager;", "activity"},
    {"Landroid/view/inputmethod/InputMethodManager;", "input_method"},
    {"Landroid/app/NotificationManager;", "notification"},
    {"Landroid/app/AlarmManager;", "alarm"},
    {"Landroid/media/AudioManager;", "audio"},
    {"Landroid/content/ClipboardManager;", "clipboard"},
    {"Landroid/net/ConnectivityManager;", "connectivity"},
    {"Landroid/app/UiModeManager;", "uimode"},
    {"Landroid/app/SearchManager;", "search"},
    {"Landroid/app/KeyguardManager;", "keyguard"},
    {"Landroid/location/LocationManager;", "location"},
    {"Landroid/accounts/AccountManager;", "account"},
    {"Landroid/os/PowerManager;", "power"},
    {"Landroid/os/Vibrator;", "vibrator"},
    {"Landroid/hardware/SensorManager;", "sensor"},
    {"Landroid/hardware/display/DisplayManager;", "display"},
    {"Landroid/view/accessibility/AccessibilityManager;", "accessibility"},
    {"Landroid/view/autofill/AutofillManager;", "autofill"},
    // S83: input service — boxcars EbitenView.initialize registers an input
    // device listener at onCreate; a null InputManager NPE'd APP-BOUNDARY.
    {"Landroid/hardware/input/InputManager;", "input"},
    // R-NEW-540 (CONT-36): JobScheduler — AOSP Context.JOB_SCHEDULER_SERVICE
    // ("jobscheduler", API 21+, never-null on a live context). Live face
    // (chompass): androidx.work SystemJobScheduler.<init> first insn
    // JobSchedulerExtKt.getWmJobScheduler(ctx) →
    // getSystemService(JobScheduler::class.java) → NULL → the ctor NPE'd
    // at pc=0x0 and the whole WorkManager bootstrap died.
    {"Landroid/app/JobScheduler;", "jobscheduler"},
    // F-NEW-639 (S235-1): the AOSP TELEPHONY_SERVICE spelling ("phone") —
    // getSystemService(TelephonyManager.class) resolves through it.
    {"Landroid/telephony/TelephonyManager;", "phone"},
};
            const char* cn = kv_table_find(t_svc_cls339,
                    sizeof(t_svc_cls339) / sizeof(t_svc_cls339[0]),
                    args[1].class_desc);
            if (cn) svc_name339 = cn;
        }
        static const miniandroid::dalvik::KvPair t_svc_map339[] = {
    {"window", "Landroid/view/WindowManager;"},
    {"layout_inflater", "Landroid/view/LayoutInflater;"},
    {"activity", "Landroid/app/ActivityManager;"},
    {"input_method", "Landroid/view/inputmethod/InputMethodManager;"},
    {"notification", "Landroid/app/NotificationManager;"},
    {"alarm", "Landroid/app/AlarmManager;"},
    {"audio", "Landroid/media/AudioManager;"},
    {"clipboard", "Landroid/content/ClipboardManager;"},
    {"connectivity", "Landroid/net/ConnectivityManager;"},
    {"uimode", "Landroid/app/UiModeManager;"},
    {"search", "Landroid/app/SearchManager;"},
    {"keyguard", "Landroid/app/KeyguardManager;"},
    {"location", "Landroid/location/LocationManager;"},
    {"account", "Landroid/accounts/AccountManager;"},
    {"power", "Landroid/os/PowerManager;"},
    {"vibrator", "Landroid/os/Vibrator;"},
    {"sensor", "Landroid/hardware/SensorManager;"},
    {"display", "Landroid/hardware/display/DisplayManager;"},
    {"accessibility", "Landroid/view/accessibility/AccessibilityManager;"},
    {"autofill", "Landroid/view/autofill/AutofillManager;"},
    // F-NEW-639 (S235-1): the AOSP TELEPHONY_SERVICE spelling ("phone").
    {"phone", "Landroid/telephony/TelephonyManager;"},
    // S83: input service (see the class-table note above).
    {"input", "Landroid/hardware/input/InputManager;"},
    // R-NEW-540 (CONT-36): jobscheduler (see the class-table note above).
    {"jobscheduler", "Landroid/app/JobScheduler;"},
};
        const char* sv = kv_table_find(t_svc_map339,
                sizeof(t_svc_map339) / sizeof(t_svc_map339[0]),
                svc_name339);
        if (sv) {
            result = get_or_create_singleton(sv);
            status = ApiCallTrace::Status::IMPLEMENTED;
            std::cerr << "[R339-SVC] getSystemService(\"" << svc_name339
                      << "\") → " << sv
                      << " (shadow layer, caller=" << current_class_ << "."
                      << current_method_ << ")" << std::endl;
            return true;
        }
        }
    }

    // [S34-RFC] who cancels the frame callback?
    if (method == "removeFrameCallback" &&
        class_name == "Landroid/view/Choreographer;") {
        static thread_local uint64_t rfc_n = 0;
        ++rfc_n;
        if (rfc_n <= 6) {
            std::cerr << "[S34-RFC] removeFrameCallback #" << rfc_n
                      << " d=" << recursion_depth_ << " chain:";
            auto frames = call_stack_.snapshot_top_first();
            for (size_t fi = 0; fi < frames.size() && fi < 5; ++fi)
                std::cerr << " <" << frames[fi].first << "."
                          << frames[fi].second << ">";
            std::cerr << std::endl;
        }
    }

    // EXP-071 Phase 8: Generic static-method shadow dispatch fix.
    //
    // For static methods like AndroidUtilities.runOnUIThread(Runnable),
    // args[0] is the FIRST ARGUMENT (the Runnable), not `this`. The
    // previous code used args[0].class_desc as ctx.class_name, which
    // made HandlerShadow's "Lorg/telegram/messenger/AndroidUtilities;"
    // branch fail to match (because args[0].class_desc was the Runnable's
    // class, not "AndroidUtilities"). As a result, runOnUIThread was a
    // silent no-op, the runnable was never enqueued, and the entire
    // async callback chain (Lambda0 → lambda$onConfirm$1 → Lambda1 →
    // lambda$onConfirm$0 → onNextPressed → auth.sendCode) was broken.
    //
    // Fix: try dispatch with the DECLARED class_name FIRST. If the shadow
    // returns not_handled, retry with args[0].class_desc (the runtime
    // class of `this` for instance methods). This works for both:
    //   * Static calls  — class_name="Lorg/telegram/messenger/AndroidUtilities;"
    //   * Instance calls — class_name="Landroid/view/View;" (or args[0].class_desc
    //     for the actual runtime subclass like IntroActivity$4).
    auto build_ctx = [&](const std::string& chosen_class) {
        framework::CallContext ctx;
        ctx.caller = current_class_ + "." + current_method_ + " pc=" +
                     std::to_string(pc_);
        ctx.class_name = chosen_class;
        ctx.method = method;
        // EXP-071 Phase 8: For INSTANCE methods, args[0] is `this` (the receiver)
        // and the remaining args are the parameters. We shift them so that
        // ctx.args[0] is the first PARAMETER (not `this`), and set
        // ctx.receiver_id/receiver_class for `this`.
        //
        // For STATIC methods (current_invoke_is_static_), args[0] is already
        // the first PARAMETER — there's no `this`. We put ALL args in ctx.args
        // without shifting.
        //
        // Without this distinction, static calls like
        // AndroidUtilities.runOnUIThread(Runnable, long) would have their
        // Runnable stolen as `this` and never reach HandlerShadow's enqueue
        // (which expects ctx.args[0] to be the Runnable).
        if (!current_invoke_is_static_ &&
            !args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            ctx.has_receiver = true;
            ctx.receiver_id = args[0].object_id;
            ctx.receiver_class = args[0].class_desc;
            for (size_t i = 1; i < args.size(); i++) {
                ctx.args.push_back(dalvik_value_to_arg(args[i]));
            }
        } else {
            for (const auto& a : args) {
                ctx.args.push_back(dalvik_value_to_arg(a));
            }
        }
        return ctx;
    };

    // Pass 1: try with the declared class_name.
    // ────────────────────────────────────────────────────────────────────
    // CONT-21 / #384 (F-NEW-272) — Thread UncaughtExceptionHandler laws.
    // AOSP Thread law (libcore Thread + AOSP RuntimeInit):
    //   Thread.getUncaughtExceptionHandler()  → the per-thread handler if
    //     set, ELSE Thread.defaultUncaughtExceptionHandler — and on a live
    //     ART runtime the default is NEVER null (RuntimeInit installs
    //     RuntimeInit$KillApplicationHandler at process start).
    //   Thread.setDefaultUncaughtExceptionHandler(h) (static) → installs h.
    //   Thread.getDefaultUncaughtExceptionHandler() (static) → the default.
    //   KillApplicationHandler.uncaughtException(t, e) → logs FATAL
    //     EXCEPTION (process-death modeling stays owned by the runtime's
    //     F-016 exception-honesty machinery — this call itself completes).
    // Runtime evidence (run/cont21/after/dooz_r2): kotlinx coroutine
    // machinery (Llo;.K pc=0x52) runs currentThread()
    // .getUncaughtExceptionHandler().uncaughtException(t,e) whenever a
    // coroutine scope fails; the prior no-op answered null → interface
    // invoke NPE → APP BOUNDARY (the registered CONT-20 next root).
    // Static-vs-instance disambiguation by arg shape (statics carry no
    // receiver): get = 0 args → static; set = 1 arg → static.
    // ────────────────────────────────────────────────────────────────────
    if ((class_name == "Ljava/lang/Thread;" || is_thread_receiver(class_name)) &&
        (method == "getUncaughtExceptionHandler" ||
         method == "setUncaughtExceptionHandler")) {
        auto ensure_default_handler = [&]() -> DalvikValue {
            if (default_uncaught_handler_.object_id != 0 &&
                heap_.has_object(default_uncaught_handler_.object_id))
                return default_uncaught_handler_;
            uint32_t hid = heap_.allocate(
                "Lcom/android/internal/os/RuntimeInit$KillApplicationHandler;",
                pc_, call_stack_.empty() ? 0 : call_stack_.top().frame_id);
            default_uncaught_handler_ = DalvikValue::make_object(
                hid,
                "Lcom/android/internal/os/RuntimeInit$KillApplicationHandler;");
            return default_uncaught_handler_;
        };
        if (method == "getUncaughtExceptionHandler") {
            if (args.empty()) {
                // static Thread.getDefaultUncaughtExceptionHandler()
                result = ensure_default_handler();
            } else {
                // instance: per-thread handler, else the default (AOSP law).
                uint32_t t_oid = args[0].type == DalvikType::OBJECT_REF
                                     ? args[0].object_id
                                     : 0;
                auto it = thread_uncaught_handlers_.find(t_oid);
                if (it != thread_uncaught_handlers_.end() &&
                    it->second.object_id != 0)
                    result = it->second;
                else
                    result = ensure_default_handler();
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // setUncaughtExceptionHandler: 1 arg (static handler) vs
        // 2 args (instance receiver + handler).
        DalvikValue hv = args.size() >= 2 ? args[1] : args[0];
        if (hv.type == DalvikType::OBJECT_REF && hv.object_id != 0) {
            if (args.size() >= 2) {
                thread_uncaught_handlers_[args[0].object_id] = hv;
            } else {
                default_uncaught_handler_ = hv;
            }
        }
        result = DalvikValue::make_void();
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }
    if (method == "uncaughtException" &&
        class_name.find("KillApplicationHandler") != std::string::npos) {
        // AOSP RuntimeInit$KillApplicationHandler: log the fatal exception;
        // the process-death face is modeled by the runtime's existing
        // exception-honesty machinery, so the call itself completes.
        static thread_local uint64_t ueh_log = 0;
        if (ueh_log < 12) {
            ++ueh_log;
            std::cerr << "[UEH-DEFAULT] FATAL EXCEPTION (KillApplicationHandler)"
                      << " thread="
                      << (args.empty() ? 0 : args[0].object_id)
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
        result = DalvikValue::make_void();
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-166 (S134 wave 3): AOSP ContextWrapper BASE-CONTEXT law —
    // served for EVERY ContextWrapper-family receiver, not only Activities.
    // AOSP: getBaseContext()/attachBaseContext() are ContextWrapper
    // CONTRACT methods (mBase set during attach; never null after), and
    // ContextWrapper.<init>(Context base) DELEGATES to attachBaseContext.
    // The S110 law implementation lives inside ActivityShadow::dispatch,
    // but ActivityShadow::handles_class matches only Activity-shaped
    // names — a plain app-level ContextWrapper descendant (WhatsApp
    // LX/00J; extends ContextWrapper) never routed there:
    //   <init>(base)      → REC-MISS → ctor base argument DROPPED
    //   getBaseContext    → REC-MISS → stub null
    //   → the app's own Intrinsics check (LX/00i;.A06 → A0F) threw
    //     "INVOKE_RETURN must not be null" during attachBaseContext →
    //     Application.onCreate never ran → no window → WHITE screen.
    // Route the three shapes here for Context-family receivers,
    // delegating to the SAME law implementation (one state owner:
    // ActivityShadow base_contexts_/application fallbacks — never null).
    // Evidence: s134 WhatsApp run, [REC-MISS] ContextWrapper.<init> +
    // ContextWrapper.getBaseContext + THROWABLE-STACK chain
    // 004.attachBaseContext → 00J.<init> → 009.<init> → A06 → A0F.
    // ────────────────────────────────────────────────────────────────────
    if ((method == "getBaseContext" || method == "attachBaseContext" ||
         (method == "<init>" && !args.empty())) &&
        (class_name.find("ContextWrapper") != std::string::npos ||
         class_name.find("ContextThemeWrapper") != std::string::npos ||
         class_name.find("Context;") != std::string::npos)) {
        if (auto* as = shadow_registry_->find_as<framework::ActivityShadow>()) {
            framework::CallContext ctx166 = build_ctx(class_name);
            // AOSP ctor law: ContextWrapper.<init>(base) ==
            // attachBaseContext(base) — route through the same law.
            if (method == "<init>")
                ctx166.method = "attachBaseContext";
            auto cr166 = as->dispatch(ctx166);
            if (cr166.handled) {
                switch (cr166.status) {
                    case framework::ApiCallStatus::IMPLEMENTED:
                        status = ApiCallTrace::Status::IMPLEMENTED; break;
                    case framework::ApiCallStatus::STUBBED:
                        status = ApiCallTrace::Status::STUBBED; break;
                    default:
                        status = ApiCallTrace::Status::STUBBED; break;
                }
                result = call_result_to_dalvik(cr166);
                std::cerr << "[F166-BASECTX] " << method << " served for "
                          << class_name << " (receiver="
                          << ((!args.empty() &&
                               args[0].type == DalvikType::OBJECT_REF)
                                  ? args[0].object_id : 0u) << ")"
                          << std::endl;
                return true;
            }
        }
    }

    auto cr = shadow_registry_->dispatch(build_ctx(class_name));
    // F-NEW-267 (CONT-64 W1) ANSWER-VALUE probe — env-gated, bounded. The
    // compose relayout reads the view geometry through this bridge during
    // the tap dispatch; the decode needs the ANSWERED VALUES (the walk
    // consumes them for the root measure constraints). Print the geometry
    // getters' int answers when MINIANDROID_TOUCH_WINDOW_TRACE is on.
    if (touch_dispatch_active_ && cr.handled &&
        (class_name == "Landroid/view/View;" || class_name == "Lt4;" ||
         class_name == "Landroid/view/ViewGroup;")) {
        static thread_local uint64_t av_n = 0;
        if (av_n++ < 120 &&
            (method == "getWidth" || method == "getHeight" ||
             method == "getMeasuredWidth" || method == "getMeasuredHeight" ||
             method == "getLeft" || method == "getTop" ||
             method == "getRight" || method == "getBottom" ||
             method == "isLaidOut" || method == "isAttachedToWindow"))
            std::cerr << "[TOUCHWIN-ANSWER] " << class_name << "." << method
                      << " -> "
                      << (method == "isLaidOut" ||
                          method == "isAttachedToWindow"
                              ? std::to_string(cr.bool_val ? 1 : 0)
                              : std::to_string(cr.int_val))
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
    }
    // M3-DIAG (temporary): why do tick-path setText calls miss the shadow?
    static const bool m3sd = std::getenv("MINIANDROID_M3_SHADOW_DIAG") != nullptr;
    if (m3sd && method.find("setText") != std::string::npos) {
        static thread_local uint64_t sd_log = 0;
        if (sd_log < 200) {
            sd_log++;
            fprintf(stderr,
                    "[M3-SHADOW] %s.%s pass1 handled=%d class=%s recv=%u/%s "
                    "args=%zu arg0=%d\n",
                    class_name.c_str(), method.c_str(), (int)cr.handled,
                    class_name.c_str(),
                    (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        ? args[0].object_id : 0u,
                    (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        ? args[0].class_desc.c_str() : "-",
                    args.size(),
                    args.empty() ? -1 : (int)args[0].type);
        }
    }
    // EXP-071 Phase 8 debug — log dispatch attempts for runOnUIThread.
    if (method == "runOnUIThread" || method == "executeOnUIThread") {
        std::cerr << "[EXP071-SHADOW-DISPATCH] pass1 class_name=" << class_name
                  << " method=" << method
                  << " handled=" << (cr.handled ? "YES" : "NO")
                  << std::endl;
    }
    if (cr.handled) {
        // ── F-NEW-259g-a: SHADOW EXCEPTION CHANNEL (conversion) ──────────
        // A shadow-detected JDK/ART contract violation (e.g. ArrayList.get
        // range law) becomes a deferred throw at THIS call site — the same
        // semantics as the engine-side F-141/F-036 throw_deferred laws.
        // ART: the exception surfaces at the invoking frame's call site;
        // the catch-handler redirect resolves at the interpreter boundary.
        if (cr.is_exc) {
            throw_deferred(cr.exc_class, cr.exc_msg, "SHADOW-EXC");
            result = DalvikValue::make_void();
            return true;
        }
        switch (cr.status) {
            case framework::ApiCallStatus::IMPLEMENTED:
                status = ApiCallTrace::Status::IMPLEMENTED; break;
            case framework::ApiCallStatus::STUBBED:
                status = ApiCallTrace::Status::STUBBED; break;
            default:
                status = ApiCallTrace::Status::STUBBED; break;
        }
        result = call_result_to_dalvik(cr);
        // CONT-159: pass-1 answer channel (same law as the pass-2 diag —
        // GLES20/GL statics answer here; the pass-2 diag never sees them).
        static thread_local const bool ans1_on =
            diag_env("MINIANDROID_SHADOW_ANSWER_TRACE");
        if (ans1_on) {
            static thread_local uint64_t ans1_n = 0;
            if (ans1_n < 300) {
                ++ans1_n;
                std::cerr << "[SHADOW-ANSWER-1] " << class_name << "."
                          << method << " ret_type="
                          << static_cast<int>(result.type)
                          << " int=" << result.int_val
                          << " obj=" << result.object_id
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
        return true;
    }

    // Pass 2: try with args[0].class_desc (runtime class of `this`).
    // M3 F-020 ROOT FIX (F2 law extension): constructors are DIRECT
    // invocation targets resolved on the DECLARING class (ART ClassLinker:
    // no virtual constructor dispatch). The runtime-class retry is a
    // virtual-dispatch emulation — it must never route <init>/<clinit>,
    // or an app-named subclass of a framework class (R8 minted
    // `LF/d; extends AtomicInteger`) gets claimed by ViewShadow's
    // user-class catch-all and the real constructor argument is dropped.
    if (method == "<init>" || method == "<clinit>") {
        return false;
    }
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
        !args[0].class_desc.empty() && args[0].class_desc != class_name) {
        cr = shadow_registry_->dispatch(build_ctx(args[0].class_desc));
        if (cr.handled) {
            // F-NEW-259g-a: shadow exception channel (pass-2 conversion).
            if (cr.is_exc) {
                throw_deferred(cr.exc_class, cr.exc_msg, "SHADOW-EXC");
                result = DalvikValue::make_void();
                return true;
            }
            switch (cr.status) {
                case framework::ApiCallStatus::IMPLEMENTED:
                    status = ApiCallTrace::Status::IMPLEMENTED; break;
                case framework::ApiCallStatus::STUBBED:
                    status = ApiCallTrace::Status::STUBBED; break;
                default:
                    status = ApiCallTrace::Status::STUBBED; break;
            }
            result = call_result_to_dalvik(cr);
            // CONT-159 (F-NEW-503 decode diag, env-gated): the shadow
            // answer channel — which (class, method) answered and with what
            // value shape. Pins int-return fidelity end-to-end.
            static thread_local const bool ans_on =
                diag_env("MINIANDROID_SHADOW_ANSWER_TRACE");
            if (ans_on) {
                static thread_local uint64_t ans_n = 0;
                if (ans_n < 300) {
                    ++ans_n;
                    std::cerr << "[SHADOW-ANSWER] " << class_name << "."
                              << method << " status="
                              << (status == ApiCallTrace::Status::IMPLEMENTED
                                      ? "IMPL"
                                      : "STUB")
                              << " ret_type=" << static_cast<int>(result.type)
                              << " int=" << result.int_val
                              << " obj=" << result.object_id
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
            return true;
        }
    }

    // CAMPAIGN 013 (B4, §8): hierarchy-aware shadow dispatch.
    // Root cause: shadows claim framework classes by NAME. App classes whose
    // names match no claim (ChessClock, muellerma StopWatch, ...) never
    // reached ActivityShadow — setContentView/findViewById/getWindow became
    // SILENT no-ops and the app kept the synthetic default screen. The old
    // workarounds grew a hand-maintained list of app class names inside
    // ActivityShadow::handles_class — the per-app special-casing this
    // campaign forbids.
    // General fix (mirrors real Android virtual dispatch): walk the DEX
    // superclass chain of the receiver and retry the shadow registry with
    // each ancestor. ChessClock → android/app/Activity → ActivityShadow
    // handles setContentView exactly as for any other Activity subclass.
    //
    // MASTER CAMPAIGN FIX (F2 constructor-direct law): constructors are
    // DIRECT invocation targets resolved on the DECLARING class (ART
    // ClassLinker: there is no virtual constructor dispatch). The ancestor
    // walk emulates VIRTUAL dispatch only — it must never route <init>/
    // <clinit> to a shadow of an ANCESTOR class. Evidence: with <init>
    // walkable, ViewShadow's user-class catch-all claimed
    // Lfr/neamar/kiss/db/DBHelper;.<init> (an R8 merge target with 24
    // merged androidx/app subclasses) and swallowed real constructors.
    if (method == "<init>" || method == "<clinit>") {
        return false;
    }
    {
        std::string cur;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            !args[0].class_desc.empty()) {
            cur = args[0].class_desc;
            // F-NEW-456 (CONT-112): ART virtual dispatch resolves on the
            // receiver's RUNTIME class, not the static type of the reference.
            // A Context-typed variable holding the Activity (every
            // (Context, AttributeSet) view ctor passes the activity as
            // Context — chess appcompat callers passed `this`, so the static
            // desc was already the runtime class; minimal probes and any
            // framework code holding Context lose the walk here). The heap
            // object knows the REAL class — start the walk from it.
            if (args[0].object_id != 0) {
                std::string rt_cls;
                if (heap_.get_object_class(args[0].object_id, rt_cls) &&
                    !rt_cls.empty()) {
                    cur = rt_cls;
                }
            }
        } else {
            cur = class_name;
        }
        int guard = 0;
        while (!cur.empty() && guard++ < 10) {
            auto sup_it = class_to_superclass_.find(cur);
            if (sup_it == class_to_superclass_.end()) break;
            const std::string sup = sup_it->second;
            if (sup.empty() || sup == cur) break;
            auto cr3 = shadow_registry_->dispatch(build_ctx(sup));
            if (cr3.handled) {
                std::cerr << "[C013-HIER] " << method << " dispatched via superclass chain: "
                          << cur << " -> " << sup
                          << " (declared=" << class_name
                          << " receiver=" << (!args.empty() &&
                             args[0].type == DalvikType::OBJECT_REF
                             ? std::string(args[0].class_desc) : std::string("-"))
                          << ")" << std::endl;
                // F-NEW-259g-a: shadow exception channel (hierarchy walk).
                if (cr3.is_exc) {
                    throw_deferred(cr3.exc_class, cr3.exc_msg, "SHADOW-EXC");
                    result = DalvikValue::make_void();
                    return true;
                }
                switch (cr3.status) {
                    case framework::ApiCallStatus::IMPLEMENTED:
                        status = ApiCallTrace::Status::IMPLEMENTED; break;
                    default:
                        status = ApiCallTrace::Status::STUBBED; break;
                }
                result = call_result_to_dalvik(cr3);
                return true;
            }
            cur = sup;
        }
    }
    return false;
}

// ────────────────────────────────────────────────────────────────────
// VISUAL-CAMPAIGN (EXT-01 gate G25): seed the virtual device identity.
// AOSP law: Build.VERSION.SDK_INT / Build.VERSION.RELEASE / Build.* and
// Settings.Secure.ANDROID_ID are FRAMEWORK-provided statics — a real
// device firmware defines them before any app code runs. MiniAndroid's
// honest virtual identity is Android 15 (SDK_INT=35, RELEASE="15") as of
// F-NEW-473 (CONT-150): the corpus's compose-ui 1.7 apps draw their
// content ONLY on a SDK>=35 device — AndroidComposeView.dispatchDraw's
// content path is gated by a private static predicate p() compiled to
// `SDK_INT >= 35` (byte-verified: Lt4;.p @dooz v23; on SDK<35 the recorded
// GraphicsLayer pipeline (RenderNode) is the only content path, and this
// software runtime implements the SDK>=35 dispatchDraw law instead).
// Insert-if-absent: a real app <clinit> always wins over a seed.
// Evidence: EXT-01 baseline (HelloWorldSelfAware) — AndroidInfo.getId()
// read SDK_INT=0, took the pre-O Build.SERIAL branch and rendered
// "i'm null"; with this seed it takes the Settings.Secure ANDROID_ID
// branch exactly like any Android 8+ device.
// ────────────────────────────────────────────────────────────────────
void DalvikExecutionEngine::seed_framework_device_statics() {
    auto seed = [this](const std::string& key, const DalvikValue& v) {
        static_field_storage_.emplace(key, v);  // insert-if-absent
        // R500 ROOT-REFLECTION-FIELD-IDENTITY: a framework-seeded static IS
        // a declared public field for the reflection surface (getField/
        // getDeclaredField consumers — real Android answers them from the
        // framework metadata the engine models with this seed registry).
        framework_declared_fields_.insert(key);
    };
    seed("Landroid/os/Build$VERSION;.SDK_INT", DalvikValue::make_int(35));
    seed("Landroid/os/Build$VERSION;.RELEASE", DalvikValue::make_string("15", 0));
    seed("Landroid/os/Build$VERSION;.CODENAME", DalvikValue::make_string("REL", 0));
    seed("Landroid/os/Build$VERSION;.SDK", DalvikValue::make_string("35", 0));
    seed("Landroid/os/Build$VERSION;.INCREMENTAL", DalvikValue::make_string("miniandroid.20260905", 0));
    seed("Landroid/os/Build;.MODEL", DalvikValue::make_string("MiniAndroid", 0));
    seed("Landroid/os/Build;.MANUFACTURER", DalvikValue::make_string("MiniAndroid", 0));
    seed("Landroid/os/Build;.BRAND", DalvikValue::make_string("MiniAndroid", 0));
    seed("Landroid/os/Build;.DEVICE", DalvikValue::make_string("miniandroid", 0));
    seed("Landroid/os/Build;.PRODUCT", DalvikValue::make_string("miniandroid", 0));
    seed("Landroid/os/Build;.HARDWARE", DalvikValue::make_string("miniandroid", 0));
    seed("Landroid/os/Build;.FINGERPRINT", DalvikValue::make_string("MiniAndroid/miniandroid/miniandroid:15/MINI.20260905/0:userdebug/test-keys", 0));
    seed("Landroid/os/Build;.SERIAL", DalvikValue::make_string("miniandroid", 0));
    // W20-K (S237-PLAY, Frozen Bubble): AOSP BitmapFactory.Options PUBLIC
    // fields (BitmapFactory.java Options @android-14) — Class.getField on
    // Options must SUCCEED (real Android answers from framework metadata).
    // Defaults per AOSP: inScaled=true, inPremultiplied=true, rest 0/false.
    seed("Landroid/graphics/BitmapFactory$Options;.inScaled",
         DalvikValue::make_bool(true));
    seed("Landroid/graphics/BitmapFactory$Options;.inPremultiplied",
         DalvikValue::make_bool(true));
    seed("Landroid/graphics/BitmapFactory$Options;.inDither",
         DalvikValue::make_bool(false));
    seed("Landroid/graphics/BitmapFactory$Options;.inMutable",
         DalvikValue::make_bool(false));
    seed("Landroid/graphics/BitmapFactory$Options;.inJustDecodeBounds",
         DalvikValue::make_bool(false));
    seed("Landroid/graphics/BitmapFactory$Options;.inSampleSize",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inTargetDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inScreenDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inPreferredDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.outWidth",
         DalvikValue::make_int(-1));
    seed("Landroid/graphics/BitmapFactory$Options;.outHeight",
         DalvikValue::make_int(-1));
    // F-NEW-190 (FINAL CAMPAIGN PHASE 4 — device/context identity, AOSP
    // Build ABI law): Build.SUPPORTED_ABIS / SUPPORTED_64_BIT_ABIS /
    // SUPPORTED_32_BIT_ABIS / CPU_ABI / CPU_ABI2 are framework statics fed
    // from ro.product.cpu.abilist on a real device — NEVER null/empty on
    // any Android build. The runtime models an arm64 android-35 device
    // (SDK_INT=35 + fingerprint above); the list follows the AOSP
    // emulator-equivalent arm64 primary order. Measured face (WhatsApp
    // LX/0Cz;.A01 ×3): the app's own ABI utility threw ISE "No supported
    // ABIs found on this device" — the absent static made its fallback
    // classify the device as unsupported.
    {
        auto seed_array = [this, &seed](const std::string& key,
                                        const std::vector<std::string>& items) {
            uint32_t arr_id = heap_.allocate("[Ljava/lang/String;", 0, 0);
            DalvikValue len = DalvikValue::make_int((int32_t)items.size());
            heap_.set_object_field(arr_id, "__array_length__", len);
            heap_.set_object_field(arr_id, "__new_array_length__", len);
            heap_.set_object_field(arr_id, "__element_type__",
                DalvikValue::make_string("[Ljava/lang/String;", 0));
            for (size_t i = 0; i < items.size(); ++i)
                heap_.set_object_field(arr_id, "array[" + std::to_string(i) + "]",
                                       DalvikValue::make_string(items[i], 0));
            DalvikValue av;
            av.type = DalvikType::OBJECT_REF;
            av.object_id = arr_id;
            av.class_desc = "[Ljava/lang/String;";
            seed(key, av);
        };
        // ── #375 §5 CAPABILITY-HONESTY LAW (FALSE_ADVERTISED_MATRIX
        // FA-01): SUPPORTED_ABIS must not advertise non-executable ABIs
        // unless binary translation exists (AOSP ro.product.cpu.abilist is
        // the device's EXECUTABLE abi list — the app-install ABI matcher
        // and every app-side ABI gate read it as such). The previous seed
        // ([arm64-v8a, armeabi-v7a, armeabi] — an arm64 device persona)
        // advertised ARM native execution that the x86_64 host profile
        // does not have. HONEST seed = the host-executable ABI only
        // (executable_abis=[x86_64] in ENVIRONMENT_PROFILE ENV-005);
        // CPU_ABI2 = "" (AOSP: deprecated, commonly empty on API 21+).
        // App-visible behavior for arm-only APKs is UNCHANGED: the install
        // ABI law still extracts their ARM lib tree for provenance and a
        // load attempt reports the real dlopen refusal (NAT-05 shape).
        // Non-empty list keeps the F-NEW-190 face green (WhatsApp's ABI
        // utility only requires a non-empty list).
        seed_array("Landroid/os/Build;.SUPPORTED_ABIS", {"x86_64"});
        seed_array("Landroid/os/Build;.SUPPORTED_64_BIT_ABIS", {"x86_64"});
        seed_array("Landroid/os/Build;.SUPPORTED_32_BIT_ABIS", {});
        seed("Landroid/os/Build;.CPU_ABI",
             DalvikValue::make_string("x86_64", 0));
        seed("Landroid/os/Build;.CPU_ABI2",
             DalvikValue::make_string("", 0));
    }
    // AOSP: Settings.Secure.ANDROID_ID == the column name "android_id".
    seed("Landroid/provider/Settings$Secure;.ANDROID_ID", DalvikValue::make_string("android_id", 0));
    // Deterministic virtual-device ANDROID_ID (16 lowercase hex chars,
    // same shape as a real device; constant => Rule 12 determinism).
    resource_string_values_["android_id"] = "6f1c3a9d2e5b4780";
    // ────────────────────────────────────────────────────────────────────
    // CONT-366 ROOT-B — android.view.WindowInsets.CONSUMED (API 30+).
    // AOSP (WindowInsets.java): CONSUMED is a public static final
    // WindowInsets — "an empty insets instance where all insets have been
    // consumed". It is NEVER null on any API-30+ device.
    // Runtime evidence (memory v34, first-divergence trace):
    //   ActionBarOverlayLayout.<init> (appcompat decor) →
    //   androidx.core.view.WindowInsetsCompat <clinit> (s0;) → s0$k;
    //   <clinit> → J0.a() == sget WindowInsets.CONSUMED → engine typed-
    //   null → Kotlin/Objects.requireNonNull(x/h.g) NPE "getClass on null
    //   object reference" → s0.v/u unwind → ActionBarOverlayLayout ctor
    //   death → WHITE. Every appcompat-1.6+ decor inflation on the API-30
    //   path touches this static through the same clinit chain.
    // Seed: a REAL heap WindowInsets object (the deterministic empty/
    // consumed instance) — not a string, not a stub. Runtime field
    // identity + requireNonNull both observe an authentic object.
    // ────────────────────────────────────────────────────────────────────
    {
        uint32_t wi_id = heap_.allocate("Landroid/view/WindowInsets;", 0, 0);
        heap_.set_object_field(wi_id, "__insets_consumed__",
                               DalvikValue::make_bool(true));
        DalvikValue wi;
        wi.type = DalvikType::OBJECT_REF;
        wi.object_id = wi_id;
        wi.class_desc = "Landroid/view/WindowInsets;";
        seed("Landroid/view/WindowInsets;.CONSUMED", wi);
    }
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-363 (CONT-67 W1, chessclock 29 first divergence —
    // runtime-proven): Settings.System.DEFAULT_RINGTONE_URI /
    // DEFAULT_NOTIFICATION_URI / DEFAULT_ALARM_ALERT_URI are FRAMEWORK
    // statics — AOSP Settings.java mints them in static init
    // (Uri.withAppendedPath(CONTENT_URI, "ringtone"|"notification_sound"|
    //  "alarm_alert") = content://settings/system/{...}) and they are
    // NEVER null on any device. Evidence: ChessClock.setUpGame reads
    //   sget-object Settings$System.DEFAULT_RINGTONE_URI
    //   invoke-virtual Uri.toString   (pc=321)
    // → engine typed-null → f141 NPE "invoke Uri.toString on a null
    // object reference" → APP-BOUNDARY unwind → the app's entire content
    // never inflates (blank face + 1 uncaught exception).
    // Seed: REAL heap Uri objects carrying uri_raw (the Uri.parse/toString
    // law's canonical field — toString then answers the true URI string,
    // and the SharedPreferences prefAlertSound roundtrip stores a real
    // string, not "null").
    // ────────────────────────────────────────────────────────────────────
    {
        auto seed_uri = [this, &seed](const std::string& key,
                                      const char* raw) {
            uint32_t uri_id = heap_.allocate("Landroid/net/Uri;", 0, 0);
            heap_.set_object_field(uri_id, "uri_raw",
                                   DalvikValue::make_string(raw, 0));
            DalvikValue uv;
            uv.type = DalvikType::OBJECT_REF;
            uv.object_id = uri_id;
            uv.class_desc = "Landroid/net/Uri;";
            seed(key, uv);
        };
        seed_uri("Landroid/provider/Settings$System;.DEFAULT_RINGTONE_URI",
                 "content://settings/system/ringtone");
        seed_uri(
            "Landroid/provider/Settings$System;.DEFAULT_NOTIFICATION_URI",
            "content://settings/system/notification_sound");
        seed_uri(
            "Landroid/provider/Settings$System;.DEFAULT_ALARM_ALERT_URI",
            "content://settings/system/alarm_alert");
    }
}

// ────────────────────────────────────────────────────────────────────
// VISUAL-CAMPAIGN (EXT-01 gate G25): the CYCLE-E Java format engine,
// extracted VERBATIM from the String.format handler (one canonical
// implementation, REUSE-FIRST). Applies
// %[argument_index$][flags][width][.precision]conversion
// with d/i/s/S/f/F/x/X/o/b/B/c/C/e/E/g/G/n, zero/space padding,
// left-align, explicit argument indexes; Java law: null → "null",
// boxed primitives read their "value" field.
// ────────────────────────────────────────────────────────────────────
std::string DalvikExecutionEngine::java_format_walk(
        const std::string& fmt, const std::vector<DalvikValue>& fargs) {
    std::string output;

        // Java-correct stringification of one format argument (§34: null
        // prints as "null", boxed primitives read their "value" field).
        auto elem_to_string = [&](const DalvikValue& v) -> std::string {
            switch (v.type) {
                case DalvikType::STRING_REF: return v.string_val;
                case DalvikType::INT32: return std::to_string(v.int_val);
                case DalvikType::INT64: return std::to_string(v.long_val);
                case DalvikType::FLOAT32: return std::to_string(v.float_val);
                case DalvikType::FLOAT64: return std::to_string(v.double_val);
                case DalvikType::BOOLEAN: return v.bool_val ? "true" : "false";
                case DalvikType::CHAR: return std::string(1, static_cast<char>(v.int_val));
                case DalvikType::OBJECT_REF: {
                    if (v.is_null || v.object_id == 0 || !heap_.has_object(v.object_id))
                        return "null";
                    auto fv = heap_.get_object_field(v.object_id, "value");
                    if (fv.has_value()) {
                        switch (fv->type) {
                            case DalvikType::INT32: return std::to_string(fv->int_val);
                            case DalvikType::INT64: return std::to_string(fv->long_val);
                            case DalvikType::BOOLEAN: return fv->bool_val ? "true" : "false";
                            case DalvikType::CHAR:
                                return std::string(1, static_cast<char>(fv->int_val));
                            case DalvikType::FLOAT32: return std::to_string(fv->float_val);
                            case DalvikType::FLOAT64: return std::to_string(fv->double_val);
                            case DalvikType::STRING_REF: return fv->string_val;
                            default: break;
                        }
                    }
                    // F-NEW-529 (CONT-34, telegram g5/q charset-factory
                    // face): AOSP %s == String.valueOf(obj) == obj.toString()
                    // — the engine answered "object@N", so protobuf/Conscrypt
                    // -style factory ISE messages rendered garbage and the
                    // charset gate killed the chain. Bridge-dispatch the
                    // object's toString (bounded depth; "object@N" stays the
                    // honest last resort for law-less classes).
                    {
                        static thread_local int f529_depth = 0;
                        if (f529_depth < 4) {
                            ++f529_depth;
                            DalvikValue ts_out;
                            ApiCallTrace::Status ts_st =
                                ApiCallTrace::Status::STUBBED;
                            std::vector<DalvikValue> ts_args;
                            ts_args.push_back(v);
                            if (bridge_to_api(v.class_desc, "toString",
                                              ts_args, ts_out, ts_st, 0) &&
                                ts_out.type == DalvikType::STRING_REF) {
                                --f529_depth;
                                return ts_out.string_val;
                            }
                            --f529_depth;
                        }
                    }
                    return "object@" + std::to_string(v.object_id);
                }
                case DalvikType::NULL_REF: return "null";
                default: return "";
            }
        };

        // Java decimal formatting with width/zero-pad/left-align.
        auto pad = [](std::string s, int width, bool zero, bool left) {
            if ((int)s.size() >= width) return s;
            std::string fill((size_t)width - s.size(), zero ? '0' : ' ');
            return left ? (s + fill) : (fill + s);
        };

        size_t arg_idx = 0;
        for (size_t i = 0; i < fmt.size();) {
            if (fmt[i] != '%') { output += fmt[i++]; continue; }
            size_t j = i + 1;
            if (j >= fmt.size()) { output += '%'; break; }
            if (fmt[j] == '%') { output += '%'; i = j + 1; continue; }
            // Optional explicit argument index: %2$s
            size_t spec_start = j;
            int explicit_idx = 0;
            {
                size_t k = j;
                while (k < fmt.size() && isdigit((unsigned char)fmt[k])) k++;
                if (k < fmt.size() && fmt[k] == '$' && k > j) {
                    explicit_idx = std::atoi(fmt.substr(j, k - j).c_str());
                    j = k + 1;
                }
            }
            // Flags
            bool left = false, zero = false, alt = false, plus = false;
            while (j < fmt.size()) {
                char f = fmt[j];
                if (f == '-') left = true;
                else if (f == '0') zero = true;
                else if (f == '#') alt = true;
                else if (f == '+') plus = true;
                else if (f == ' ' || f == ',') { /* accepted, no-op */ }
                else break;
                j++;
            }
            // Width
            int width = 0;
            {
                size_t k = j;
                while (k < fmt.size() && isdigit((unsigned char)fmt[k])) k++;
                if (k > j) { width = std::atoi(fmt.substr(j, k - j).c_str()); j = k; }
            }
            // Precision
            int prec = -1;
            if (j < fmt.size() && fmt[j] == '.') {
                size_t k = j + 1;
                while (k < fmt.size() && isdigit((unsigned char)fmt[k])) k++;
                prec = std::atoi(fmt.substr(j + 1, k - j - 1).c_str());
                j = k;
            }
            if (j >= fmt.size()) { output += fmt.substr(i); break; }
            char conv = fmt[j];

            // Resolve the argument (explicit index is 1-based).
            DalvikValue elem;
            bool have = false;
            if (explicit_idx > 0) {
                size_t pos = (size_t)(explicit_idx - 1);
                if (pos < fargs.size()) { elem = fargs[pos]; have = true; }
            } else {
                if (arg_idx < fargs.size()) { elem = fargs[arg_idx]; have = true; }
                arg_idx++;
            }
            (void)spec_start;

            std::string piece;
            switch (conv) {
                case 'd': case 'i': {
                    int64_t n = 0;
                    if (have) {
                        if (elem.type == DalvikType::INT32) n = elem.int_val;
                        else if (elem.type == DalvikType::INT64) n = elem.long_val;
                        else if (elem.type == DalvikType::OBJECT_REF) {
                            auto fv = heap_.has_object(elem.object_id)
                                          ? heap_.get_object_field(elem.object_id, "value")
                                          : std::nullopt;
                            if (fv.has_value() && fv->type == DalvikType::INT32) n = fv->int_val;
                            else if (fv.has_value() && fv->type == DalvikType::INT64) n = fv->long_val;
                        }
                    }
                    piece = std::to_string(n);
                    if (plus && n >= 0) piece = "+" + piece;
                    piece = pad(piece, width, zero, left);
                    break;
                }
                case 'x': case 'X': {
                    uint64_t n = 0;
                    if (have) {
                        if (elem.type == DalvikType::INT32) n = (uint32_t)elem.int_val;
                        else if (elem.type == DalvikType::INT64) n = (uint64_t)elem.long_val;
                        else if (elem.type == DalvikType::OBJECT_REF) {
                            auto fv = heap_.has_object(elem.object_id)
                                          ? heap_.get_object_field(elem.object_id, "value")
                                          : std::nullopt;
                            if (fv.has_value() && fv->type == DalvikType::INT32)
                                n = (uint32_t)fv->int_val;
                        }
                    }
                    piece = alt ? ("0x" + (conv == 'x'
                                        ? [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::hex << v; s = ss.str(); return s; }(n)
                                        : [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::uppercase << std::hex << v; s = ss.str(); return s; }(n)))
                                : (conv == 'x'
                                        ? [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::hex << v; s = ss.str(); return s; }(n)
                                        : [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::uppercase << std::hex << v; s = ss.str(); return s; }(n));
                    piece = pad(piece, width, zero, left);
                    break;
                }
                case 'f': case 'F': {
                    double d = 0.0;
                    if (have) {
                        if (elem.type == DalvikType::FLOAT32) d = elem.float_val;
                        else if (elem.type == DalvikType::FLOAT64) d = elem.double_val;
                        else if (elem.type == DalvikType::INT32) d = elem.int_val;
                        else if (elem.type == DalvikType::OBJECT_REF) {
                            auto fv = heap_.has_object(elem.object_id)
                                          ? heap_.get_object_field(elem.object_id, "value")
                                          : std::nullopt;
                            if (fv.has_value() && fv->type == DalvikType::FLOAT32) d = fv->float_val;
                            else if (fv.has_value() && fv->type == DalvikType::FLOAT64) d = fv->double_val;
                            else if (fv.has_value() && fv->type == DalvikType::INT32) d = fv->int_val;
                        }
                    }
                    char buf[64];
                    snprintf(buf, sizeof(buf), "%.*f", prec >= 0 ? prec : 6, d);
                    piece = pad(buf, width, zero, left);
                    break;
                }
                case 's': case 'S': {
                    piece = have ? elem_to_string(elem) : "null";
                    if (prec >= 0 && (int)piece.size() > prec) piece = piece.substr(0, prec);
                    if (conv == 'S')
                        std::transform(piece.begin(), piece.end(), piece.begin(), ::toupper);
                    piece = pad(piece, width, /*zero=*/false, left);
                    break;
                }
                case 'b': case 'B': {
                    bool b = have && !(elem.type == DalvikType::BOOLEAN && !elem.bool_val);
                    piece = b ? "true" : "false";
                    if (conv == 'B')
                        std::transform(piece.begin(), piece.end(), piece.begin(), ::toupper);
                    break;
                }
                case 'c': case 'C': {
                    piece = have ? elem_to_string(elem) : "";
                    break;
                }
                case 'e': case 'E': case 'g': case 'G': {
                    double d = 0.0;
                    if (have && elem.type == DalvikType::FLOAT64) d = elem.double_val;
                    else if (have && elem.type == DalvikType::FLOAT32) d = elem.float_val;
                    char buf[64];
                    snprintf(buf, sizeof(buf),
                             conv == 'e' ? "%.*e" : conv == 'E' ? "%.*E" : conv == 'g' ? "%.*g" : "%.*G",
                             prec >= 0 ? prec : 6, d);
                    piece = pad(buf, width, zero, left);
                    break;
                }
                case 'o': {
                    int64_t n = have && elem.type == DalvikType::INT32 ? elem.int_val : 0;
                    char buf[32]; snprintf(buf, sizeof(buf), "%llo", (long long)n);
                    piece = buf;
                    break;
                }
                case 'n': piece = "\n"; break;
                default:
                    // Unknown conversion — Java throws; we keep the spec
                    // verbatim and emit a diagnostic (§34).
                    std::cerr << "UNSUPPORTED_FORMAT_SPECIFICATION spec=%"
                              << conv << std::endl;
                    piece = fmt.substr(i, j - i + 1);
                    break;
            }
            output += piece;
            i = j + 1;
        }
    return output;
}

// R-NEW-345: run one Thread.start() body — the target is either a Runnable
// object (recorded ctor target: Room transaction executor) or the thread
// ITSELF (self-run law for Thread subclasses: kotlinx scheduler Worker,
// Looper threads — they override run() and start with no Runnable). Both
// paths invoke the receiver's REAL DEX run() — AOSP Thread.start()
// virtual-dispatch law, no fake callback.
void DalvikExecutionEngine::run_thread_start_body(uint32_t thread_oid,
                                                  uint32_t target_oid) {
    if (shadow_registry_ == nullptr) return;
    auto* ts_shadow = shadow_registry_->find_as<framework::ThreadShadow>();
    uint32_t run_oid = target_oid ? target_oid : thread_oid;
    // Resolve the receiver's RUNTIME class from the heap (lambda/interface
    // impls and Thread subclasses each live in their own classes).
    std::string rcls = "Ljava/lang/Object;";
    if (heap_.has_object(run_oid)) {
        const auto* robj = heap_.get(run_oid);
        if (robj && !robj->class_descriptor.empty())
            rcls = robj->class_descriptor;
    }
    DalvikValue self = DalvikValue::make_object(run_oid, rcls);
    DalvikValue run_ret;
    DalvikExecutionResult run_res;
    std::vector<DalvikValue> run_args{self};
    // F-110d (S62+): while this body runs, Thread.currentThread() resolves
    // to THIS thread's heap object (AOSP identity law). Save/restore so a
    // nested drain (a body starting another thread) restores the outer
    // identity when the inner body ends.
    uint32_t saved_active_thread = 0;
    if (ts_shadow) {
        saved_active_thread = ts_shadow->current_thread_id() ==
                                      ts_shadow->main_thread_id()
                                  ? 0
                                  : ts_shadow->current_thread_id();
        ts_shadow->set_active_drained_thread(thread_oid);
    }
    // F-110b companion: a drained body runs at drain depth >= 1, so the
    // THREAD-SLEEP YIELD LAW (Thread.sleep inside a drained body) is
    // eligible. Without depth accounting, an infinite while(running)
    // {cycle; sleep(TICK);} body spins at the start site until the
    // loop-visit cap halts it (anuto GameLoop.run).
    int saved_drain_depth = park_drain_last_depth_;
    park_drain_last_depth_ = (saved_drain_depth < 1) ? 1 : saved_drain_depth;
    bool ran = try_recursive_invoke(rcls, "run", run_args, run_ret, run_res,
                                    "()V");
    park_drain_last_depth_ = saved_drain_depth;
    if (ts_shadow) ts_shadow->set_active_drained_thread(saved_active_thread);
    if (park_yield_pending_) {
        park_yield_pending_ = false;  // parked worker frame chain fully unwound
        // F-150 (S72-W4): the body is BLOCKED on Thread.sleep (AOSP), not
        // dead — register it with its WAKE time so the first scheduler
        // boundary at/after the wake re-drains the body. Deterministic
        // counterpart of the sleep elapsing on a real concurrent runtime.
        if (ts_shadow)
            ts_shadow->mark_thread_yielded(thread_oid,
                                           target_oid ? target_oid
                                                      : thread_oid,
                                           park_yield_wake_at_);
    } else if (ts_shadow && thread_oid != 0) {
        // Body completed (loop exit / return) — never re-drain it.
        ts_shadow->clear_thread_yielded(thread_oid);
        // [S193-C8] F-C8-185 TERMINATION LAW: a body that ran to
        // completion (returned or loop-exited without parking) has
        // TERMINATED — JDK Thread state law. isAlive() flips false;
        // join() on this target returns. Was (this line): no state,
        // isAlive() answered true forever.
        ts_shadow->mark_thread_terminated(thread_oid);
        std::cerr << "[THREAD-LIFE] thread o" << thread_oid
                  << " body completed → TERMINATED" << std::endl;
    }
    std::cerr << "[THREAD-START] drained oid=" << run_oid << " cls=" << rcls
              << (target_oid == thread_oid && thread_oid != 0
                      ? " (self-run law)"
                      : "")
              << " → " << (ran ? "REAL DEX run() executed"
                               : "no run() found (no-op)")
              << std::endl;
}

// R-NEW-345: park = deterministic yield point. See the law note at the
// LockSupport case in bridge_to_api. Bounded rounds; reentrancy-guarded so
// a park reached THROUGH drained work yields instead of recursing.
// Returns the work units consumed (0 = global quiescence).
uint64_t DalvikExecutionEngine::drain_park_queues_bounded(const char* reason) {
    static thread_local int park_drain_depth = 0;
    if (park_drain_depth >= 3) return 0;  // nested park: yield only
    if (!shadow_registry_) return 0;
    ++park_drain_depth;
    park_drain_last_depth_ = park_drain_depth;
    auto* hs = shadow_registry_->find_as<framework::HandlerShadow>();
    auto* cs = shadow_registry_->find_as<framework::ChoreographerShadow>();
    auto* ts = shadow_registry_->find_as<framework::ThreadShadow>();
    static thread_local uint64_t park_log = 0;
    bool do_log = park_log < 24;
    uint64_t work_units = 0;
    for (int round = 0; round < 4; ++round) {
        bool did_work = false;
        // 1) main MessageQueue runnables (Executor family + Handler.post +
        //    dispatcher trampoline all enqueue here — one-queue law).
        if (hs) {
            for (int r = 0; r < 16; ++r) {
                std::vector<std::pair<uint32_t, uint32_t>> drained;
                if (hs->drain_ready_ex(&drained) == 0) break;
                did_work = true;
                for (auto& rid_pair : drained) {
                    const uint32_t rid = rid_pair.first;
                    const uint32_t delivery_tid = rid_pair.second;
                    // Same routing as ExecutionEngine::invoke_handler_runnable:
                    // framework tokens ride the touch dispatcher, app runnables
                    // run their REAL DEX run().
                    if (rid >= framework::HandlerShadow::kFrameworkTokenBase)
                        continue;
                    if (!heap_.has_object(rid)) continue;
                    std::string rcls = "Ljava/lang/Object;";
                    if (const auto* robj = heap_.get(rid))
                        if (!robj->class_descriptor.empty())
                            rcls = robj->class_descriptor;
                    DalvikValue ret;
                    DalvikExecutionResult res;
                    std::vector<DalvikValue> run_args{
                        DalvikValue::make_object(rid, rcls)};
                    // F-NEW-289 (CONT-31) MAIN-QUEUE DELIVERY IDENTITY LAW
                    // (AOSP Looper/Handler model): code delivered by the
                    // main MessageQueue ALWAYS executes on the MAIN thread —
                    // inside every main-queue Runnable,
                    //   Thread.currentThread() == Looper.getMainLooper().getThread()
                    // (the DefaultTaskExecutor.isMainThread contract behind
                    // androidx LiveData.assertMainThread). The deterministic
                    // park drain runs NESTED inside a worker thread's
                    // run-to-completion body (F-110d binds the worker
                    // identity there — correct for the body itself), so
                    // without this re-bind the delivery INHERITS the worker
                    // identity and main-thread asserts throw
                    // (composeStopwatch ground truth: R8-renamed
                    // DefaultTaskExecutor.isMainThread Lca;.P()Z answered
                    // false -> Lcm0;.a ISE "Cannot invoke setValue on a
                    // background thread" -> DEFAULT_BACKGROUND_ONLY frame).
                    // Save/restore mirrors run_thread_start_body's F-110d
                    // pattern; 0 = main identity. No-op when already main.
                    //
                    // F-C4-593 (W10): the law is now PER-TASK —
                    // delivery_thread_id 0 (Handler.post on the main
                    // Looper) keeps the main identity verbatim;
                    // non-zero (an Executor.execute task) binds the
                    // EXECUTOR'S worker identity (AOSP ThreadPoolExecutor
                    // delivery — Room's assertNotMainThread must see a
                    // worker thread, or every background query ISE'd).
                    uint32_t saved_mq_identity = 0;
                    bool bound_mq_identity = false;
                    if (ts) {
                        if (ts->current_thread_id() !=
                                ts->main_thread_id() ||
                            delivery_tid != 0) {
                            saved_mq_identity = ts->current_thread_id();
                            ts->set_active_drained_thread(delivery_tid);
                            bound_mq_identity = true;
                        }
                    }
                    try_recursive_invoke(rcls, "run", run_args, ret, res, "()V");
                    if (bound_mq_identity)
                        ts->set_active_drained_thread(saved_mq_identity);
                }
                work_units += drained.size();
            }
        }
        // 2) Choreographer due frame callbacks (vsync during park — the
        //    withFrameNanos continuation resume path). F-NEW-289: doFrame
        //    is a MAIN-looper delivery (AOSP Choreographer rides the main
        //    thread) — same identity law as arm 1.
        if (cs && cs->has_pending_callbacks()) {
            auto due = cs->take_due_callbacks();
            for (auto& d : due) {
                ++work_units;
                DalvikValue ret;
                DalvikExecutionResult res;
                std::vector<DalvikValue> cb_args{
                    DalvikValue::make_object(d.callback_id, d.callback_class),
                    DalvikValue::make_long(d.frame_time_nanos)};
                uint32_t saved_frame_identity = 0;
                bool bound_frame_identity = false;
                if (ts && ts->current_thread_id() != ts->main_thread_id()) {
                    saved_frame_identity = ts->current_thread_id();
                    ts->set_active_drained_thread(0);
                    bound_frame_identity = true;
                }
                try_recursive_invoke(d.callback_class, "doFrame", cb_args, ret,
                                     res);
                if (bound_frame_identity)
                    ts->set_active_drained_thread(saved_frame_identity);
            }
            if (!due.empty()) did_work = true;
        }
        // 3) pending Thread starts (worker spawns observed while parked).
        if (ts) {
            uint32_t t_oid = 0, r_oid = 0;
            int started = 0;
            while (started < 4 && ts->consume_pending_start(t_oid, r_oid)) {
                ++started;
                ++work_units;
                did_work = true;
                run_thread_start_body(t_oid, r_oid);
            }
        }
        if (!did_work) break;
    }
    --park_drain_depth;
    park_drain_last_depth_ = park_drain_depth;
    // R-NEW-345: work dispatched through THIS drain that parked mid-way has
    // unwound by now; clear the yield flag so the caller's loop (main-thread
    // joinBlocking or the worker loop itself) resumes normally.
    park_yield_pending_ = false;
    if (do_log) {
        ++park_log;
        std::cerr << "[PARK-DRAIN] " << reason << " depth=" << park_drain_depth
                  << " work_units=" << work_units << std::endl;
    }
    return work_units;
}

// ─────────────────────────────────────────────────────────────────────────
// F-103 (S58, R-NEW-378): OpenJDK Class.isAssignableFrom assignability walk.
// Law (OpenJDK Class.java / AOSP): `to.isAssignableFrom(from)` is true iff
// `from` is the same class, a subclass, a implementor of `to` (transitively),
// or — for arrays — component-covariant into `to`. `java.lang.Object`
// accepts every reference type. Primitives only match themselves. The walk
// is bounded (16 super hops / 8 interface expansions) like the existing
// try_recursive_invoke_on_super bound.
// ─────────────────────────────────────────────────────────────────────────
bool DalvikExecutionEngine::dalvik_class_assignable(const std::string& from_desc,
                                                    const std::string& to_desc) {
    if (from_desc.empty() || to_desc.empty()) return false;
    if (from_desc == to_desc) return true;
    if (to_desc == "Ljava/lang/Object;") {
        // Reference types (L...; and [...) are Objects; primitives are not.
        return from_desc[0] == 'L' || from_desc[0] == '[';
    }
    // Array covariance: X[] assignable to Y[] iff X assignable to Y;
    // every array is assignable to Object[]'s super-chain (Object,
    // Cloneable, java.io.Serializable).
    if (from_desc[0] == '[' && to_desc[0] == '[') {
        // Component-wise: strip one bracket pair and recurse.
        return dalvik_class_assignable(from_desc.substr(1), to_desc.substr(1));
    }
    if (from_desc[0] == '[' && (to_desc == "Ljava/lang/Cloneable;" ||
                                to_desc == "Ljava/io/Serializable;")) {
        return true;  // JLS: arrays implement Cloneable + Serializable
    }
    // Primitive descriptors only match by identity (handled above).
    if (from_desc.size() == 1 || to_desc.size() == 1) return false;
    // ── CONT-124 (F-NEW-469): SUPERINTERFACE CLOSURE LAW ────────────────────
    // JVMS 5.1 / ART Class::IsAssignableFrom: an interface S is assignable
    // to interface T when S extends T TRANSITIVELY (iface→iface chains of
    // any depth). The prior walk checked each hop's DIRECTLY declared
    // interfaces only — a three-level chain (class implements I3; I3
    // extends I2; I2 extends I1) answered FALSE and the aput-object
    // store-check threw a BOGUS ArrayStoreException on a legal store.
    // Live face (dooz v23, binary 04a89c52): Liw0;.b stored Lf6; (implements
    // Lbu0;) into [Lxt0; — Lbu0; extends Lvt0; extends Lxt0; — the walk
    // answered FALSE, the AIOOBE escaped the Lr;.g recovery re-throw, the
    // LayoutNode placement pass (Lel0;.c/.d) unwound, no Placeable.position
    // write ever landed, and dooz rendered the bare themed background.
    // Law: BFS the superinterface graph from every interface encountered
    // (the start class's own list AND every superclass hop's list) through
    // BOTH the DEX tables (class_to_interfaces_) and the F-NEW-236 framework
    // tables (framework_implements), visited-set bounded. Only previously-
    // FALSE answers can flip to TRUE — permissive in exactly the direction
    // the JVMS law demands; illegal stores are still rejected.
    auto interface_reaches = [&](const std::string& iface,
                                 const std::string& target) -> bool {
        if (iface == target) return true;
        std::vector<std::string> work{iface};
        std::unordered_set<std::string> visited{iface};
        int hops = 0;
        while (!work.empty() && hops < 64) {
            std::string cur = work.back();
            work.pop_back();
            ++hops;
            auto it = class_to_interfaces_.find(cur);
            if (it != class_to_interfaces_.end()) {
                for (const auto& sup : it->second) {
                    if (sup == target) return true;
                    if (visited.insert(sup).second) work.push_back(sup);
                }
            }
            // Platform interfaces carry their parents only in the framework
            // tables (libcore law) — same consult the F-NEW-253 tail makes.
            std::unordered_set<std::string> fw_closure;
            framework::framework_interface_closure(cur, fw_closure);
            for (const auto& sup : fw_closure) {
                if (sup == target) return true;
                if (visited.insert(sup).second) work.push_back(sup);
            }
        }
        return false;
    };
    // R-NEW-010 store-check completion (CONT-122, tower3d live face):
    // JVMS 5.1 / AOSP Class.isAssignableFrom — the STARTING class's OWN
    // declared interfaces count. The walk below only inspects interfaces
    // of the SUPERCLASSES it hops through, so an anonymous class that
    // DIRECTLY implements the target interface
    // (Lcom/badlogic/gdx/backends/android/AndroidApplication$1; implements
    // Lcom/badlogic/gdx/LifecycleListener;) answered FALSE and the
    // aput-object store-check rejected a legal LifecycleListener[] store.
    if (to_desc[0] == 'L') {
        auto own_ifc = class_to_interfaces_.find(from_desc);
        if (own_ifc != class_to_interfaces_.end()) {
            for (const auto& ifc : own_ifc->second)
                if (interface_reaches(ifc, to_desc)) return true;
        }
        if (framework::framework_implements(from_desc, to_desc)) return true;
    }
    // Superclass walk (bounded, same bound as try_recursive_invoke_on_super).
    static constexpr int kMaxAssignHops = 16;
    std::string walk = from_desc;
    for (int hop = 0; hop < kMaxAssignHops; ++hop) {
        auto sup_it = class_to_superclass_.find(walk);
        // F-NEW-254 (CONT-7 W3): DEX + FRAMEWORK HIERARCHY COMPOSITION —
        // one walk. When the DEX tables end at the platform boundary
        // (e.g. Ljava/util/concurrent/CancellationException; has no
        // class_def in the APK), continue through the F-NEW-236 framework
        // extends table instead of stopping — the SAME fallback law
        // is_subclass_of (instance-of path) already implements. Without
        // it, Class.isInstance(Throwable-target) on a platform exception
        // subclass answered FALSE and kotlinx Finishing threw its own
        // ISE "State is …" during dooz composition.
        std::string sup = (sup_it != class_to_superclass_.end())
                              ? sup_it->second
                              : framework::framework_superclass_of(walk);
        if (sup.empty()) break;
        walk = sup;
        if (walk.empty()) break;
        if (walk == to_desc) return true;
        // Interface declared anywhere along the super chain counts —
        // through the FULL superinterface closure (F-NEW-469), not just
        // the directly declared list.
        auto ifc_it = class_to_interfaces_.find(walk);
        if (ifc_it != class_to_interfaces_.end()) {
            for (const auto& ifc : ifc_it->second)
                if (interface_reaches(ifc, to_desc)) return true;
        }
        // F-NEW-292: the hop class may itself be a PLATFORM class whose
        // libcore implements metadata lives in the framework tables
        // (Ljava/lang/Enum; implements Serializable, Comparable — an
        // R8-minified app enum carries those edges ONLY through this hop;
        // its own class_def declares none). Same consult the F-NEW-253
        // tail performs for from_desc, applied per hop so every
        // intermediate platform hop sees the same boot-classpath truth.
        if (framework::framework_implements(walk, to_desc)) return true;
    }
    // Directly-declared interfaces of `from` itself.
    auto ifc_it = class_to_interfaces_.find(from_desc);
    if (ifc_it != class_to_interfaces_.end()) {
        for (const auto& ifc : ifc_it->second)
            if (interface_reaches(ifc, to_desc)) return true;
    }
    // ── F-NEW-253 (CONT-7 W3): PLATFORM HIERARCHY FALLBACK — one central
    // point. Class.isInstance/isAssignableFrom ask assignability between
    // types that may be ENGINE-SHADOWED PLATFORM classes (Landroid/os/Bundle;
    // etc.) with no DEX class_def and no entry in class_to_superclass_ /
    // class_to_interfaces_. The F-NEW-236 framework tables (libcore +
    // android.os source law) are the runtime's boot-classpath metadata:
    // consult the same transitive closure here, after the DEX walk, so
    // EVERY consumer of this walk (the F-103 isInstance law, the
    // saveable platform check, future reflection-family callers) sees
    // the same truth ART sees from its boot classpath.
    // Live face (dooz v23): Parcelable.isInstance(Bundle) answered FALSE
    // → rememberSaveable IAE at registerValue → composition died before
    // the first app frame.
    {
        std::unordered_set<std::string> platform_closure;
        framework::framework_interface_closure(from_desc, platform_closure);
        if (platform_closure.count(to_desc)) return true;
    }
    return false;
}

// ────────────────────────────────────────────────────────────────────────
// F-NEW-223 (user campaign §H) — VIRTUAL EXTERNAL-STORAGE VOLUME LAW.
// AOSP Environment.java + StorageManager: every device has a PRIMARY
// external storage volume, EMULATED, mounted at /storage/emulated/0,
// state MEDIA_MOUNTED, readable+writable by the app. Apps probe it at
// startup (user evidence: opencalc's onCreate died because the path
// "does not exist" — the honest R-NEW-346 metadata law answered ABSENT
// for the raw absolute path, which on real hardware is a MOUNT POINT
// that always exists). The runtime emulates a device: the volume is a
// VIRTUAL MOUNT backed physically by <data_root>/storage/emulated/0
// (the ONE sandbox root law — no writes escape the sandbox, deterministic
// across runs). Translation is a pure prefix map; the backing root is
// materialized on demand so exists() on the mount point is TRUE without
// any app-side mkdirs (AOSP: the volume is mounted at boot, before any
// app runs).
// ────────────────────────────────────────────────────────────────────────
static std::string host_path_for_virtual_volume(const std::string& p) {
    static const char* kMount = "/storage/emulated/0";
    if (p.empty() || p.rfind(kMount, 0) != 0)
        return p;
    namespace fs = std::filesystem;
    fs::path backing =
        fs::path(Storage::app_data_root()) / "storage" / "emulated" / "0";
    // The mount point itself exists from boot (materialize once, idempotent).
    std::error_code mk_ec;
    fs::create_directories(backing, mk_ec);
    std::string rest = p.size() > strlen(kMount) ? p.substr(strlen(kMount)) : "";
    std::string hp = (backing.string() + rest);
    // Collapse the mount point to its canonical host form without
    // touching the caller's spelling of the virtual path.
    return hp;
}

// ─── CONT-97 T1: bridge dispatch census (env MINIANDROID_BRIDGE_CENSUS=1) ───
// Answers: which (class,method) keys consume the measured 145.7K cycles/call
// aggregate? Bounded map keyed on the call's (class,method); RAII record on
// scope exit so the WHOLE law-chain cost is attributed to the key. Zero cost
// when disabled (one relaxed load). Prints at atexit, top 48 by ticks.

// ── CODER7 WAVE-2: the service BRING-DOWN path (AOSP ActiveServices
// bringDownServiceLocked). Law: when a live service is torn down by ANY
// caller (stopService / stopSelf / stopSelfResult) while bound connections
// exist, onUnbind(bindingIntent) is delivered BEFORE onDestroy — exactly as
// the unbind-driven destruction path already does. The wave-1 tree delivered
// onUnbind only on the unbind path; the stop paths skipped it (recorded
// PENDING in the wave-1 issue §7). onDestroy ALWAYS follows on the
// bring-down path (an onUnbind==true return does NOT keep the instance
// alive here — ActiveServices continues bringDownServiceLocked after the
// unbind delivery).
void DalvikExecutionEngine::c7_service_bring_down(ServiceInstance& svc,
                                                  const char* reason) {
    if (!svc.created || svc.destroyed) return;
    if (svc.bindings > 0) {
        // The binding intent of the FIRST live connection is the onUnbind
        // argument (AOSP passes the binding Intent; with several
        // connections the dispatcher delivers one onUnbind for the record —
        // same shape as the unbind path).
        uint32_t c7_bint_oid = 0;
        for (const auto& [conn_oid, cb] : svc.conn_bindings) {
            if (cb.bind_intent_oid != 0) {
                c7_bint_oid = cb.bind_intent_oid;
                break;
            }
        }
        DalvikValue c7_bint =
            (c7_bint_oid != 0 && heap_.has_object(c7_bint_oid))
                ? DalvikValue::make_object(c7_bint_oid,
                                           "Landroid/content/Intent;")
                : DalvikValue::make_null();
        DalvikValue c7_ub;
        bool c7_has_unbind = invoke_lifecycle_method(
            svc.oid, svc.cls, "onUnbind", {c7_bint}, c7_ub);
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "SVC-UNBIND", svc.cls, true,
            std::string("bring-down (") + reason + "): onUnbind delivered" +
                (c7_has_unbind ? " (override answered)" : " (default)"),
            current_class_ + "." + current_method_);
    }
    DalvikValue c7_ignore;
    invoke_lifecycle_method(svc.oid, svc.cls, "onDestroy", {}, c7_ignore);
    svc.destroyed = true;
    svc.started = false;
    svc.bindings = 0;
    svc.conn_bindings.clear();
    miniandroid::diagnostics::FileIoTrace::instance().record(
        "SVC-STOP", svc.cls, true,
        std::string(reason) + " → onDestroy delivered",
        current_class_ + "." + current_method_);
}

namespace {
// ── C9-7 (CODER 9) — in-memory PNG encode (Bitmap.compress FORMAT_PNG) ──
// libpng-backed RGBA encoder (the SAME library the runtime's PNG decoder
// uses — one PNG authority). The write callback appends to a std::vector.
// Error-path note: the setjmp branch leaks only the `rows` pointer array
// (h * sizeof(void*) — bounded, error-only); no other C++ object crosses
// the longjmp.
bool c9_png_encode_rgba(int w, int h,
                               const std::vector<uint8_t>& rgba,
                               std::vector<uint8_t>* out) {
    if (w <= 0 || h <= 0 || rgba.size() != (size_t)w * h * 4 || !out)
        return false;
    png_structp p = png_create_write_struct(PNG_LIBPNG_VER_STRING,
                                            nullptr, nullptr, nullptr);
    if (!p) return false;
    png_infop info = png_create_info_struct(p);
    if (!info) {
        png_destroy_write_struct(&p, nullptr);
        return false;
    }
    std::vector<uint8_t*> rows(h);
    for (int y = 0; y < h; ++y)
        rows[y] = const_cast<uint8_t*>(&rgba[(size_t)y * w * 4]);
    if (setjmp(png_jmpbuf(p))) {
        png_destroy_write_struct(&p, &info);
        return false;
    }
    auto write_fn = [](png_structp pp, png_bytep data, png_size_t len) {
        static_cast<std::vector<uint8_t>*>(png_get_io_ptr(pp))
            ->insert(static_cast<std::vector<uint8_t>*>(png_get_io_ptr(pp))
                         ->end(),
                     data, data + len);
    };
    auto flush_fn = [](png_structp) {};
    png_set_write_fn(p, out, write_fn, flush_fn);
    png_set_IHDR(p, info, (png_uint_32)w, (png_uint_32)h, 8,
                 PNG_COLOR_TYPE_RGBA, PNG_INTERLACE_NONE,
                 PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_write_info(p, info);
    png_write_image(p, rows.data());
    png_write_end(p, nullptr);
    png_destroy_write_struct(&p, &info);
    return true;
}

// ── C9-10 (CODER 9) — DisplayMetrics device-profile law ────────────────
// ONE density authority: resources::device_config() — the SAME
// ResTableConfig the bucket selection (AssetManager2 match) and the C9-1
// BitmapFactory inTargetDensity use. The previous constants
// (2.625/420/1080x1920 hardcoded) diverged from the runtime device the
// moment MINIANDROID_DENSITY selected another bucket (the registered §2
// gap: densityDpi answered 420 while the bucket law served 160/240-
// selected resources). density = dpi/160 (AOSP DisplayMetrics law);
// scaledDensity = density (fontScale 1.0); xdpi/ydpi = densityDpi.
void c9_fill_display_metrics(DalvikHeap& heap,
                                    uint32_t dm_id) {
    if (dm_id == 0 || !heap.has_object(dm_id)) return;
    const auto& cfg = resources::device_config();
    const float density = (float)cfg.density / 160.0f;
    auto set_f = [&](const char* f, float v) {
        heap.set_object_field(dm_id, f, DalvikValue::make_float(v));
    };
    auto set_i = [&](const char* f, int32_t v) {
        heap.set_object_field(dm_id, f, DalvikValue::make_int(v));
    };
    set_f("density", density);
    set_i("densityDpi", (int32_t)cfg.density);
    set_f("scaledDensity", density);
    set_i("widthPixels", (int32_t)cfg.screenWidth);
    set_i("heightPixels", (int32_t)cfg.screenHeight);
    set_f("xdpi", (float)cfg.density);
    set_f("ydpi", (float)cfg.density);
    static thread_local uint64_t c9_dm_log = 0;
    if (c9_dm_log++ < 8)
        std::cerr << "[C9-10] DisplayMetrics <- device_config(): density="
                  << density << " dpi=" << cfg.density << " "
                  << cfg.screenWidth << "x" << cfg.screenHeight
                  << std::endl;
}
}  // namespace

// ── F-NEW-659 (#588 Games-g2) — the framework (0x01-package) string-id
// table.android-4.4w_r1 public.xml (docs/upstream/aosp/public.xml,
// byte-verified ids) × the tag's own core/res/res/values/strings.xml
// (values fetched + verified per row from the googlesource tag; the two
// newer-than-4.4w rows 0x01040018/0x01040019 are NOT carried — their
// texts cannot be verified in this tag). The GATE-A law resolves from
// this table BEFORE the NotFoundException throw: GameControl.newGame
// pc=52 died on android.R.string.unknownName (0x0104000e) — a framework
// id the APK's ARSC table never carries. NOTE: the 4.4w truth for
// unknownName is "(Unknown)" (the lane's log paraphrased "Unknown");
// every value here is the tag's byte-verified English default.
struct F659FrameworkString { uint32_t id; const char* text; };
static const F659FrameworkString f659_table[] = {
    {0x01040000, "Cancel"},
    {0x01040001, "Copy"},
    {0x01040002, "Copy URL"},
    {0x01040003, "Cut"},
    {0x01040004, "Voicemail"},
    {0x01040005, "MSISDN1"},
    {0x01040006, "(No phone number)"},
    {0x01040007, "Couldn't open the page because the URL is invalid."},
    {0x01040008, "The protocol isn't supported."},
    {0x01040009, "Cancel"},                 // android.R.string.no
    {0x0104000a, "OK"},                     // android.R.string.ok
    {0x0104000b, "Paste"},
    {0x0104000c, "Search"},
    {0x0104000d, "Select all"},
    {0x0104000e, "(Unknown)"},              // android.R.string.unknownName
    {0x0104000f, "<Untitled>"},
    {0x01040010, "OK"},
    {0x01040011, "Can't play this video."},
    {0x01040012, "Video problem"},
    {0x01040013, "OK"},                     // android.R.string.yes
    {0x01040014, "Attention"},
    {0x01040015, "This video isn't valid for streaming to this device."},
    {0x01040016, "Select text"},
    {0x01040017, "999+"},
};
const char* framework_string_id_text(uint32_t resid) {
    for (const auto& row : f659_table)
        if (row.id == resid) return row.text;
    return nullptr;
}
} // namespace dalvik
} // namespace miniandroid
