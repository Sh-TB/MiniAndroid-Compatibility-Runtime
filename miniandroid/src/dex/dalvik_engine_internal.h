// dalvik_engine_internal.h — ISSUE-612 WAVE-4 split support.
// Verbatim relocation of the F-107a trivially-destructible utility block
// (dalvik_engine.cpp lines 187-589: structs, static const tables, inline
// helpers) and the IEEE bit/conv law helpers (21553-21586), shared by the
// five split engine TUs. Stateful non-inline helpers remain single
// definitions in dalvik_engine_core.cpp, declared here (de-static'd).
// Inline functions with function-local statics keep single-instance
// semantics per the C++ inline rule.
#pragma once
#ifndef MINIANDROID_DALVIK_ENGINE_INTERNAL_H
#define MINIANDROID_DALVIK_ENGINE_INTERNAL_H

#include "dex/dalvik_engine_impl.h"

namespace miniandroid {
namespace dalvik {

// ── TRAIN-59 (S144) ContentValues flat mirror (see the header law) ──────
// Keyed by the ContentValues heap oid; written by the put() handler while
// the boxed value is live on the heap; read by the sqlite shadow's
// SQLiteDatabase.update arm (storage::DatabaseShadow holds no engine
// reference, so the snapshot crosses as plain POD).

// EXP-065: Forward declaration — used by the setHintText capture stub
// in try_recursive_invoke (defined later in this file at line ~5795).
framework::CallContext::Arg dalvik_value_to_arg(const DalvikValue& v);

// S83 APX-ACT forward declaration — the shadow-result → DalvikValue
// converter is defined later in this file (EXP-051, near try_shadow_dispatch).
DalvikValue call_result_to_dalvik(const framework::CallResult& r);

// ─── M3 FIELD-TRACE (AG diagnostic) ───────────────────────────────────────
// MINIANDROID_FIELD_TRACE=<substr> — env-gated, deterministic, bounded.
// Logs iget/iput field accesses whose FIELD NAME contains <substr>, or ALL
// accesses when <substr> is "1"/"all" (hard-capped at 2000 lines so a
// full-corpus run can never flood the log). Disabled by default: the check
// is a single thread_local pointer compare — cheap when off.

// CONT-42 THROUGHPUT LAW: the field-trace call sites build a
// (current_class_ + "." + current_method_) temporary BEFORE calling
// field_trace_active — a heap string allocation per iget/iput/sget tick
// (1.9M+ iget-object per dooz run) even though the trace is OFF in every
// normal run. This zero-cost pre-check short-circuits the argument build;
// semantics identical (the temporary was only ever consumed when the
// filter env is set).
inline bool field_trace_filter_set() {
    static thread_local const char* ft_filter =
        std::getenv("MINIANDROID_FIELD_TRACE");
    return ft_filter != nullptr;
}
// ─────────────────────────────────────────────────────────────────────────
// F-107a (R-NEW-381, S61): trivially-destructible lookup tables.
//
// ROOT CAUSE (gprof, dooz v23 90s profile): function-local `static` containers
// of std::string (map/set/vector) in the interpreter's hot path cost a
// thread-safe-init guard + a __cxa_atexit cleanup thunk (__tcf_N) at every
// reference. The profile showed the cleanup thunk __tcf_0 entered 739M times
// (50% of wall) plus 464M std::function/_M_manager churn and 259M json
// destroys — while the interpreter core (fetch_decode_execute) was <2%.
// The engine spent its budget on evidence/static machinery, not execution.
//
// LAW (F-107a): the interpreter hot path must not contain function-local
// statics with non-trivial destructors. Data tables become file-scope arrays
// of const char* (trivially destructible → zero guard, zero cleanup thunk,
// zero construction). Small-table linear scans also beat std::map lookups
// for ≤64-entry tables (cache locality), so this is not a trade.
// ─────────────────────────────────────────────────────────────────────────
// (ambient namespace: miniandroid::dalvik — F-107a helpers below)
struct KvPair { const char* k; const char* v; };
struct KvInt { const char* k; int v; };

inline const char* kv_table_find(const KvPair* tbl, size_t n, const std::string& k) {
    for (size_t i = 0; i < n; ++i) if (k == tbl[i].k) return tbl[i].v;
    return nullptr;
}
inline int kvint_table_find(const KvInt* tbl, size_t n, const std::string& k, int def) {
    for (size_t i = 0; i < n; ++i) if (k == tbl[i].k) return tbl[i].v;
    return def;
}

// F-107b (R-NEW-381, S61): batched FIFO cap for trace vectors.
// The old law erased ONE element from the FRONT on every push once the cap
// was reached — vector::erase(begin) is O(n) per call (the gprof profile
// showed _M_erase at 0.94s/7230 calls). Batching: let the vector grow to
// cap+BATCH, then drop BATCH in ONE erase — identical FIFO order, identical
// steady-state cap (bounded lag of BATCH), 1/BATCH the memmove traffic.
//
// CONT-42 THROUGHPUT LAW (gprof, dooz 60s profile): even BATCHED, the FIFO
// erase on the ApiCallTrace ring was 9.0% of wall (1.56M pushes; every batch
// memmoves cap × sizeof(ApiCallTrace) ≈ 750KB — ~18GB of memmove per dooz
// run). The trace ring's consumers (S135 missing/ERROR census + first-20
// emission, S69 optional JSON dump, ApiCallRecord recording) are tallies —
// the SURVIVOR SET (last cap entries) is the contract, not the element
// order. The ring form: until cap, push_back; at cap, OVERWRITE slot
// [cursor++ % cap] — O(1), zero memmove, identical survivor set.
// ring_normalize_chrono() restores the exact chronological FIFO order once
// at execution end (single O(cap) std::rotate) so every downstream consumer
// still reads chronological order; call sites that never normalize keep the
// physical order (diagnostics-only delta, documented).
template <class T>
inline void batched_cap_push(std::vector<T>& v, size_t& cursor,
                             const size_t cap, T&& item) {
    if (cap == 0) { v.push_back(std::move(item)); return; }
    if (v.size() < cap) {
        v.push_back(std::move(item));
        return;
    }
    v[cursor] = std::move(item);
    cursor = (cursor + 1) % cap;
}

// CONT-42: rotate the survivor ring into chronological order in place
// (physical [oldest..newest | wrapped] → true FIFO), then zero the cursor.
// After this the vector is byte-for-byte the shape the old batched-FIFO
// produced (modulo the survivor-lag difference the ring removes entirely).
template <class T>
inline void ring_normalize_chrono(std::vector<T>& v, size_t& cursor) {
    if (cursor == 0 || cursor >= v.size()) { cursor = 0; return; }
    std::rotate(v.begin(), v.begin() + static_cast<long>(cursor), v.end());
    cursor = 0;
}
inline bool kv_table_contains(const KvPair* tbl, size_t n, const std::string& k) {
    for (size_t i = 0; i < n; ++i) if (k == tbl[i].k) return true;
    return false;
}
inline const char* str_table_contains(const char* const* tbl, size_t n, const std::string& k) {
    for (size_t i = 0; i < n; ++i) if (k == tbl[i]) return tbl[i];
    return nullptr;
}

// ─── S61 PERF PHASE TIMERS (F-107 forensics; env MINIANDROID_PERF_PHASES=1) ───
// Zero-cost when disabled (one relaxed load per phase). Prints at engine dtor.
// (ambient namespace — S61 PERF)
struct PhaseClock {
    struct Phase {
        std::atomic<uint64_t> ns{0};
        std::atomic<uint64_t> calls{0};
    };
    bool on = false;
    Phase invoke_internal;    // execute_method_internal
    Phase recursive_invoke;   // try_recursive_invoke
    Phase bridge;             // bridge_to_api
    Phase fetch_exec;         // fetch_decode_execute (the instruction loop)
    Phase subclass;           // is_subclass_of
    Phase overrides;          // chain_overrides_method
    Phase invoke_resolve;     // try_recursive_invoke: entry → dispatch decision
    Phase invoke_execute;     // execute_method_internal call inside tri
    Phase invoke_native;      // JNI/native dispatch
    Phase invoke_bridge;      // bridge_to_api call inside tri
    Phase em_setup;           // execute_method_internal: entry → frame push
    Phase em_fetch;           // the fetch_decode_execute call
    Phase em_pop;             // fetch end → return
    Phase resolve_field_ph;   // resolve_field
    Phase class_init_ph;      // ensure_class_initialized
    Phase sget_resolve_ph;    // sget handler: resolve_field portion
    Phase sget_init_ph;       // sget handler: ensure_class_initialized portion
    Phase sget_tail_ph;       // sget handler: storage lookup + synthesis
    std::atomic<uint64_t> ci_warm{0}, ci_cold{0}, ci_skipfw{0};
    Phase find_class;         // class_info_index_ lookups are cheap; skip
    // S62 R-NEW-381: per-instruction bucket split (env-gated, zero-cost off).
    // Answers where the ~640us/instruction actually sits: pre-switch loop
    // top, the invoke-kind switch cases, the non-invoke switch cases, or the
    // post-switch bookkeeping. Sum over the TOP-LEVEL frame ≈ wall.
    Phase insn_pre;           // while-top → before switch
    Phase insn_sw_non;        // non-invoke switch cases
    Phase insn_sw_inv;        // invoke-kind switch cases (incl. nested bodies)
    Phase insn_post;          // after switch → while bottom
    void enter(Phase& ph, uint64_t& t0) {
        if (!on) return;
        t0 = __rdtsc(); ++ph.calls;
    }
    void exit(Phase& ph, uint64_t t0) {
        if (!on) return;
        ph.ns.fetch_add(__rdtsc() - t0, std::memory_order_relaxed);
    }
};
inline PhaseClock& phase_clock() {
    static PhaseClock pc;
    return pc;
}
// end S61 PERF

// S61 PERF: per-opcode tick histogram (256 opcodes).
struct OpHistogram {
    std::atomic<uint64_t> ns[256];
    std::atomic<uint64_t> count[256];
    OpHistogram() { for (int i = 0; i < 256; ++i) { ns[i].store(0); count[i].store(0); } }
};
inline OpHistogram& op_hist() { static OpHistogram h; return h; }
inline std::atomic<uint64_t>& f107_init_depth() { static std::atomic<uint64_t> d{0}; return d; }

// F-107a: file-scope trivially-destructible framework View hierarchy table
// (was a function-local static array of std::pair<std::string,std::string> in
// build_class_dex_index — its __cxa_atexit cleanup thunk was the profile #1).
static const miniandroid::dalvik::KvPair kFrameworkViews[] = {
    {"Landroid/view/View;", "Ljava/lang/Object;"},
    {"Landroid/view/ViewGroup;", "Landroid/view/View;"},
    {"Landroid/widget/LinearLayout;", "Landroid/view/ViewGroup;"},
    {"Landroid/widget/FrameLayout;", "Landroid/view/ViewGroup;"},
    {"Landroid/widget/RelativeLayout;", "Landroid/view/ViewGroup;"},
    // ── F-NEW-628 (S209): AOSP AbsoluteLayout.java — `public class
    // AbsoluteLayout extends ViewGroup` (deprecated since API 3, still a
    // public platform widget). The SDL2 ≤2.0.x Java bootstrap's CONTENT
    // ROOT: gomoku's SDLActivity.onCreate builds AbsoluteLayout(this) →
    // addView(SDLSurface) → setContentView (live evidence run
    // s209/ab2/gomoku_run1: without this edge the class fell to the
    // unknown-class stub — no view node, addView stubbed, and the
    // F-NEW-233 window-root check answered NO_ROOT despite the completed
    // R349 attach+measure wave, because root id 26 was a bare heap
    // object, not a view node).
    {"Landroid/widget/AbsoluteLayout;", "Landroid/view/ViewGroup;"},
    {"Landroid/widget/ScrollView;", "Landroid/widget/FrameLayout;"},
    {"Landroid/widget/HorizontalScrollView;", "Landroid/widget/FrameLayout;"},
    {"Landroid/widget/TextView;", "Landroid/view/View;"},
    {"Landroid/widget/EditText;", "Landroid/widget/TextView;"},
    {"Landroid/widget/Button;", "Landroid/widget/TextView;"},
    {"Landroid/widget/ImageButton;", "Landroid/widget/ImageView;"},
    {"Landroid/widget/ImageView;", "Landroid/view/View;"},
    {"Landroid/widget/CheckBox;", "Landroid/widget/Button;"},
    {"Landroid/widget/RadioButton;", "Landroid/widget/Button;"},
    {"Landroid/widget/ToggleButton;", "Landroid/widget/Button;"},
    {"Landroid/widget/CheckedTextView;", "Landroid/widget/TextView;"},
    {"Landroid/widget/AutoCompleteTextView;", "Landroid/widget/EditText;"},
    {"Landroid/widget/MultiAutoCompleteTextView;", "Landroid/widget/AutoCompleteTextView;"},
    {"Landroid/widget/Space;", "Landroid/view/View;"},
    {"Landroid/view/TextureView;", "Landroid/view/View;"},
    {"Landroid/view/SurfaceView;", "Landroid/view/View;"},
    // F-NEW-606 (S197): AOSP GLSurfaceView.java L163 — `public class
    // GLSurfaceView extends SurfaceView` (verified live 2026-11-08,
    // android.googlesource.com + aosp-mirror). Without this edge the
    // GLSurfaceView20 -> GLSurfaceView -> (dead end) instance-of View
    // walk failed inside AndroidInput.<init> and the ctor skipped
    // setOnTouchListener — the libGDX family was tap-dead (see the full
    // law comment in framework/view_ancestry.h).
    {"Landroid/opengl/GLSurfaceView;", "Landroid/view/SurfaceView;"},
    {"Landroid/content/Context;", "Ljava/lang/Object;"},
    {"Landroid/content/ContextWrapper;", "Landroid/content/Context;"},
    {"Landroid/app/Activity;", "Landroid/content/ContextWrapper;"},
    {"Landroidx/appcompat/app/AppCompatActivity;", "Landroid/app/Activity;"},
    {"Landroidx/fragment/app/FragmentActivity;", "Landroidx/appcompat/app/AppCompatActivity;"},
    {"Landroidx/fragment/app/Fragment;", "Ljava/lang/Object;"},
    {"Landroidx/appcompat/widget/AppCompatTextView;", "Landroid/widget/TextView;"},
    {"Landroidx/appcompat/widget/AppCompatEditText;", "Landroid/widget/EditText;"},
    {"Landroidx/appcompat/widget/AppCompatButton;", "Landroid/widget/Button;"},
    {"Landroidx/appcompat/widget/AppCompatImageView;", "Landroid/widget/ImageView;"},
    {"Landroidx/appcompat/widget/AppCompatCheckBox;", "Landroid/widget/CheckBox;"},
    // S104 R-004 CLASS-IDENTITY: real-descriptor inflation (S101 law
    // corpus-wide) needs the FULL extends chain for the family the inflater
    // now creates under real androidx/material descriptors. Chains land in
    // the existing platform edges below (RadioButton->Button,
    // AutoCompleteTextView->EditText, AppCompat*->platform).
    {"Landroidx/appcompat/widget/AppCompatRadioButton;", "Landroid/widget/RadioButton;"},
    {"Landroidx/appcompat/widget/AppCompatSpinner;", "Landroid/widget/Spinner;"},
    {"Lcom/google/android/material/button/MaterialButton;", "Landroidx/appcompat/widget/AppCompatButton;"},
    {"Lcom/google/android/material/textfield/MaterialAutoCompleteTextView;", "Landroid/widget/AutoCompleteTextView;"},
    {"Lcom/google/android/material/textfield/TextInputEditText;", "Landroidx/appcompat/widget/AppCompatEditText;"},
    {"Lcom/google/android/material/floatingactionbutton/FloatingActionButton;", "Landroidx/appcompat/widget/AppCompatImageView;"},
    {"Landroid/widget/ViewAnimator;", "Landroid/widget/FrameLayout;"},
    {"Landroid/widget/ViewSwitcher;", "Landroid/widget/ViewAnimator;"},
    {"Landroid/widget/ViewFlipper;", "Landroid/widget/ViewAnimator;"},
    {"Landroid/widget/TableLayout;", "Landroid/widget/LinearLayout;"},
    {"Landroid/widget/TableRow;", "Landroid/widget/LinearLayout;"},
    {"Landroid/widget/RadioGroup;", "Landroid/widget/LinearLayout;"},
    {"Landroid/widget/GridLayout;", "Landroid/view/ViewGroup;"},
    {"Landroid/widget/Toolbar;", "Landroid/view/ViewGroup;"},
    // S101 REAL-CLASS-IDENTITY LAW: appcompat Toolbar inflates under its
    // real descriptor (in the APK dex). Seed keeps non-appcompat APKs and
    // synthetic views classifying it as a ViewGroup container.
    {"Landroidx/appcompat/widget/Toolbar;", "Landroid/view/ViewGroup;"},
};
static const size_t kNumFrameworkViews = sizeof(kFrameworkViews) / sizeof(kFrameworkViews[0]);



// CYCLE-E: parse a DEX method proto "(params)return" into per-param type
// strings ('F','J','D','I','Z',…, full 'L…;' / '[…' for references).
std::vector<std::string> parse_proto_param_types(const std::string& proto);

// CYCLE-E: signature-aware invoke argument builder.
// raw    — register VALUES in call order (raw[0] is the RECEIVER for
//          instance calls, the first PARAM for static calls).
// types  — callee param types from parse_proto_param_types (may be empty
//          when the proto is unresolvable → raw passthrough, legacy law).
// Per the proto: 'F' params reinterpret INT32 raw float bits (const/const-32
// are not float-typed — EXP-095 CM-019 law); 'J'/'D' merge lo/hi register
// pairs. Fixes the range-call receiver misalignment (receiver consumed as
// the first param → final param dropped off the end, e.g. the Paint of
// Canvas.drawRect(l,t,r,b,paint)) and the 35c literal-float raw-bit leak.
std::vector<DalvikValue> build_invoke_args(
    const std::vector<DalvikValue>& raw,
    const std::vector<std::string>& types,
    bool is_static);

// CYCLE-E: AOSP framework enum constant ordinals (android.* classes are not
// defined in app DEX files, so their enum <clinit> never runs; without this
// table sget-object of Paint.Style.STROKE etc. materializes NULL).
int framework_enum_ordinal(const std::string& class_desc,
                                  const std::string& field_name);
// F-110e: framework static INT constant table (definition near the enum table).
int framework_static_int(const std::string& class_desc,
                                const std::string& field_name);

// CHAR-PROBE campaign: numeric view of an integer-like primitive register.
// The interpreter carries CHAR/BOOLEAN/BYTE/SHORT values in int_val once
// signature-aware invoke/field typing is in play; arithmetic, comparisons
// and array indexing must use that value instead of collapsing every
// non-INT32 register to 0. Mirrors the EXP-093 if-eqz zero-law.
static inline int32_t dalvik_int_value(const DalvikValue& v) {
    switch (v.type) {
        case DalvikType::INT32:
        case DalvikType::CHAR:
        case DalvikType::BOOLEAN:
        case DalvikType::BYTE:
        case DalvikType::SHORT:   return v.int_val;
        case DalvikType::INT64:   return static_cast<int32_t>(v.long_val);
        default:                  return 0;
    }
}

// CODER7: boolean view of a boolean-carrying register (same int_val
// convention as dalvik_int_value; used by the onUnbind return-value law).
inline bool dalvik_bool_value(const DalvikValue& v) {
    switch (v.type) {
        case DalvikType::BOOLEAN:
        case DalvikType::INT32:
        case DalvikType::CHAR:
        case DalvikType::BYTE:
        case DalvikType::SHORT:   return v.int_val != 0;
        default:                  return false;
    }
}

// F-028 (MASTER-4 §A1) — UNTYPED-REGISTER CONVERSION LAW, raw-bits view.
// Dalvik registers are UNTYPED storage slots; the OPCODE — not a runtime
// value tag — defines the source interpretation. This helper exposes the
// slot's raw 32-bit word (low half for wide values) so the conversion and
// float-comparison/arithmetic sites can reinterpret it per the opcode's
// source type, exactly as ART does on raw 32-bit slots. First real-APK
// hit: Material3 LG0/b.<clinit> (dooz) built FontScaleConverter table
// keys via const/high16 float bits + float-to-int and threw ISE "You
// should only apply non-linear scaling to font scales > 1".
inline uint32_t dalvik_raw_bits32(const DalvikValue& v) {
    switch (v.type) {
        case DalvikType::FLOAT32: {
            uint32_t b; std::memcpy(&b, &v.float_val, sizeof(b));
            return b;
        }
        case DalvikType::INT64:
            return static_cast<uint32_t>(v.long_val);   // low slot
        case DalvikType::FLOAT64: {
            uint64_t w; std::memcpy(&w, &v.double_val, sizeof(w));
            return static_cast<uint32_t>(w);            // low slot
        }
        default:
            // INT32/CHAR/BOOLEAN/BYTE/SHORT carry the value in int_val;
            // refs are a DEX verify error — expose the stored int word
            // like ART would.
            return static_cast<uint32_t>(v.int_val);
    }
}

// ── verbatim helper block 8858-8877 (anon wrapper dropped) ──
// F-NEW-304 helper: resolve a preference-XML attribute value to text.
// String literals answer as-is; resource refs resolve through the ARSC
// string pool (AOSP Resources.getString). Returns "" when unresolvable —
// the caller records the honest gap instead of inventing text.
inline std::string fnew304_resolve_pref_text(const resources::ResValue& val) {
    if (val.is_string()) return val.string_value;
    if (val.type == resources::DataType::STRING &&
        !val.string_value.empty()) {
        return val.string_value;
    }
    if (val.ref_id != 0) {
        auto& rt = resources::ResourceRuntime::instance();
        if (rt.arsc().resolve_string(val.ref_id)) {
            return *rt.arsc().resolve_string(val.ref_id);
        }
    }
    return std::string();
}

// ── verbatim helper block 21553-21586 (anon wrapper dropped) ──
inline int32_t conv_f2i(double d) {
    if (std::isnan(d)) return 0;
    if (d >= 2147483647.0)  return INT32_MAX;
    if (d <= -2147483648.0) return INT32_MIN;
    return static_cast<int32_t>(d);
}
inline int64_t conv_f2l(double d) {
    if (std::isnan(d)) return 0;
    if (d >= 9223372036854775807.0)  return INT64_MAX;
    if (d <= -9223372036854775808.0) return INT64_MIN;
    return static_cast<int64_t>(d);
}
// Dalvik registers are raw bit storage: const-wide/const-wide/high16 load a
// DOUBLE's bit pattern tagged INT64 (the engine's type tags are an internal
// approximation). Floating handlers must therefore reinterpret INT64-tagged
// registers as their bit pattern when a double is expected — otherwise every
// double constant routed through const-wide would read as garbage.
inline double bits_l2d(int64_t l) {
    double d;
    static_assert(sizeof(double) == sizeof(int64_t), "64-bit double required");
    std::memcpy(&d, &l, sizeof(d));
    return d;
}
// MASTER RECONCILIATION (2026-09-03): int-bits → float reinterpret, the
// 32-bit companion of bits_l2d. const/const/16 opcodes store raw bit patterns
// tagged INT32; the unary neg-float handler needs the NUMERIC value.
inline float bits_i2f(int32_t i) {
    float f;
    static_assert(sizeof(float) == sizeof(int32_t), "32-bit float required");
    std::memcpy(&f, &i, sizeof(f));
    return f;
}

// ── verbatim helper block 38357-38417 (anon wrapper dropped) ──
struct BridgeCensus {
    bool on = false;
    std::unordered_map<std::string, std::pair<uint64_t, uint64_t>> kv; // key -> (calls, ticks)
};
inline BridgeCensus& bridge_census() {
    static BridgeCensus bc;
    return bc;
}
struct BridgeCensusGuard {
    uint64_t t0 = 0;
    bool on = false;
    std::string key; // stack-local per call: nested bridge calls each own
                     // their frame's key (the first draft shared one
                     // thread_local and nested subtrees clobbered it).
    void begin(const std::string& cls, const std::string& mth) {
        on = true;
        t0 = __rdtsc();
        key.assign(cls);
        key.push_back('|');
        key.append(mth);
    }
    ~BridgeCensusGuard() {
        BridgeCensus& bc = bridge_census();
        if (!on || !bc.on) return;
        auto& slot = bc.kv[key];
        slot.first += 1;
        slot.second += __rdtsc() - t0;
    }
};
inline void bridge_census_init() {
    static const bool c97_once = [] {
        BridgeCensus& bc = bridge_census();
        bc.on = std::getenv("MINIANDROID_BRIDGE_CENSUS") != nullptr;
        if (bc.on) {
            std::atexit([] {
            BridgeCensus& bc2 = bridge_census();
            std::vector<std::pair<std::string, std::pair<uint64_t, uint64_t>>> rows(
                bc2.kv.begin(), bc2.kv.end());
            std::sort(rows.begin(), rows.end(),
                      [](auto& a, auto& b) { return a.second.second > b.second.second; });
            uint64_t total_ticks = 0, total_calls = 0;
            for (auto& r : rows) { total_ticks += r.second.second; total_calls += r.second.first; }
            fprintf(stderr, "[BRIDGE-CENSUS] keys=%zu calls=%llu ticks=%llu\n",
                    rows.size(), (unsigned long long)total_calls,
                    (unsigned long long)total_ticks);
            for (size_t i = 0; i < rows.size() && i < 48; ++i)
                fprintf(stderr, "[BRIDGE-CENSUS] %-3zu %-70s calls=%-9llu ticks=%-13llu cy/call=%llu\n",
                        i, rows[i].first.c_str(),
                        (unsigned long long)rows[i].second.first,
                        (unsigned long long)rows[i].second.second,
                        (unsigned long long)(rows[i].second.first
                            ? rows[i].second.second / rows[i].second.first : 0));
            fflush(stderr);
        });
        }
        return true;
    }();
    (void)c97_once;
}

// ── verbatim helper block 38470-38549 (anon wrapper dropped) ──
// ── C9-7 (CODER 9) — in-memory PNG encode (Bitmap.compress FORMAT_PNG) ──
// libpng-backed RGBA encoder (the SAME library the runtime's PNG decoder
// uses — one PNG authority). The write callback appends to a std::vector.
// Error-path note: the setjmp branch leaks only the `rows` pointer array
// (h * sizeof(void*) — bounded, error-only); no other C++ object crosses
// the longjmp.
inline bool c9_png_encode_rgba(int w, int h,
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
inline void c9_fill_display_metrics(DalvikHeap& heap,
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
// ── cross-TU stateful helper declarations ──
std::map<uint32_t, std::vector<CvFlat>>& g_content_values_mirror_ref();
std::vector<CvFlat> content_values_flat_snapshot(uint32_t oid);
bool field_trace_active(const char* field_name, const char* where, const char* class_desc = nullptr);
std::string dalvik_value_to_string(const DalvikValue& v);
// ── cross-TU helper declarations (linker-driven additions) ──
uint32_t csl_wrap_single(DalvikHeap& heap, uint32_t pc, int32_t argb,
                         uint32_t frame_id = 0);
std::string s130_norm_cls(std::string cls);
std::string s134_dex_field_key(const std::string& cls,
                               const std::string& name,
                               bool dex_defined);
std::vector<std::pair<int, std::string>> framework_enum_constants(
    const std::string& class_desc);
bool c9_png_encode_rgba(int w, int h,
                        const std::vector<uint8_t>& rgba,
                        std::vector<uint8_t>* out);
void c9_fill_display_metrics(DalvikHeap& heap, uint32_t dm_id);
const char* framework_string_id_text(uint32_t resid);

// ── cross-TU variables (defined in core, used in invoke) ──
extern std::map<std::string, uint64_t> g_d7_read_census;
extern uint64_t g_d7_draws;

} // namespace dalvik
} // namespace miniandroid

#endif
// W23-BENCH op=F run=1 t=1795118487
