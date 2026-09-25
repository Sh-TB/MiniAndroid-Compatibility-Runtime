// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — Android Framework Shadow Registry (implementation)

#include "shadow_registry.h"
#include "android_shadows.h"
#include "dialog_shadow.h"
#include "canvas_shadow.h"
#include "bitmap_shadow.h"
#include "matrix_shadow.h"
#include "locale_insets_shadow.h"
#include "gl_surface_shadow.h"
#include "surface_view_shadow.h"
#include "clipboard_shadow.h"
#include "animator_shadow.h"
#include "locks_shadow.h"
#include "atomic_shadow.h"
#include "executor_shadow.h"
#include "pending_intent_shadow.h"
#include "choreographer_shadow.h"
#include "../storage/sqlite_shadow.h"

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// CallContext argument helpers
// ─────────────────────────────────────────────────────────────────────────
int32_t CallContext::arg_as_int(size_t i, int32_t default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    switch (a.kind) {
        case CallContext::Arg::Kind::INT:   return a.int_val;
        case CallContext::Arg::Kind::LONG:  return static_cast<int32_t>(a.long_val);
        case CallContext::Arg::Kind::BOOL:  return a.bool_val ? 1 : 0;
        case CallContext::Arg::Kind::FLOAT: return static_cast<int32_t>(a.float_val);
        case CallContext::Arg::Kind::DOUBLE:return static_cast<int32_t>(a.double_val);
        default: return default_val;
    }
}

bool CallContext::arg_as_bool(size_t i, bool default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    switch (a.kind) {
        case CallContext::Arg::Kind::BOOL: return a.bool_val;
        case CallContext::Arg::Kind::INT:   return a.int_val != 0;
        case CallContext::Arg::Kind::LONG:  return a.long_val != 0;
        default: return default_val;
    }
}

// MG-124..129 (S98): float arg law — setTranslationX/setScaleX/setRotation/
// setPivotX all take float (View.java mTransformationInfo mutators). Dalvik
// float args arrive as Kind::FLOAT; int/long/double coerce per the standard
// DEX value-bag widening rules.
float CallContext::arg_as_float(size_t i, float default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    switch (a.kind) {
        case CallContext::Arg::Kind::FLOAT:  return a.float_val;
        case CallContext::Arg::Kind::DOUBLE: return static_cast<float>(a.double_val);
        case CallContext::Arg::Kind::INT:    return static_cast<float>(a.int_val);
        case CallContext::Arg::Kind::LONG:   return static_cast<float>(a.long_val);
        default: return default_val;
    }
}

std::string CallContext::arg_as_string(size_t i, const std::string& default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    if (a.kind == CallContext::Arg::Kind::STRING) return a.string_val;
    // EXP-091: Support OBJECT_REF strings — when setText(CharSequence) is called
    // with a String object from move-result-object (e.g., from LocaleController.getString()),
    // the arg is OBJECT kind with object_id pointing to a heap String.
    // We need to resolve the actual string value from the object's string_val field.
    if (a.kind == CallContext::Arg::Kind::OBJECT && a.string_val.empty() == false) {
        return a.string_val;
    }
    return default_val;
}

uint32_t CallContext::arg_as_object(size_t i, uint32_t default_val) const {
    if (i >= args.size()) return default_val;
    const auto& a = args[i];
    if (a.kind == CallContext::Arg::Kind::OBJECT) return a.object_id;
    if (a.kind == CallContext::Arg::Kind::NULL_REF) return 0;
    return default_val;
}

// ─────────────────────────────────────────────────────────────────────────
// CallResult factories
// ─────────────────────────────────────────────────────────────────────────
CallResult CallResult::handled_int(int32_t v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::INT; r.int_val = v; return r;
}
CallResult CallResult::handled_long(int64_t v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::LONG; r.long_val = v; return r;
}
CallResult CallResult::handled_float(float v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::FLOAT; r.float_val = v; return r;
}
CallResult CallResult::handled_double(double v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::DOUBLE; r.double_val = v; return r;
}
CallResult CallResult::handled_bool(bool v) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::BOOL; r.bool_val = v; return r;
}
CallResult CallResult::handled_string(const std::string& s, uint32_t ref_id) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::STRING; r.string_val = s; r.object_id = ref_id; return r;
}
CallResult CallResult::handled_object(uint32_t obj_id, const std::string& cls) {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::OBJECT; r.object_id = obj_id; r.object_class = cls; return r;
}
CallResult CallResult::handled_null() {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::NULL_REF; return r;
}
CallResult CallResult::handled_void() {
    CallResult r; r.handled = true; r.status = ApiCallStatus::IMPLEMENTED;
    r.ret_kind = RetKind::VOID; return r;
}
CallResult CallResult::not_handled() {
    CallResult r; r.handled = false; r.status = ApiCallStatus::UNHANDLED; return r;
}

// ─────────────────────────────────────────────────────────────────────────
// ShadowRegistry
// ─────────────────────────────────────────────────────────────────────────
CallResult ShadowRegistry::dispatch(const CallContext& ctx) {
    calls_dispatched_++;
    // F-057 (M9): view-node duality law.
    //
    // The runtime models the DecorView chain as decor → activity node →
    // content → app views (F023-PARENTLINK): the ACTIVITY object doubles as
    // a VIEW NODE. Compose's ViewTree* owner walks call View methods
    // (getTag / getParent) on every hop of that chain; class-based shadow
    // routing resolved those calls on the ActivityShadow identity and the
    // walk dead-ended → owners reported null → Intrinsics NPE at
    // AndroidComposeView.onAttachedToWindow (dooz compose chain).
    //
    // AOSP law (PhoneWindow/DecorView): every node of that parent chain IS
    // a View. The activity-as-node is a modeling duality, so View-methods
    // on an object that has a ViewShadow node must resolve through the
    // ViewShadow tree FIRST, regardless of the object's primary identity.
    if ((ctx.method == "getParent" || ctx.method == "getTag") &&
        ctx.receiver_id != 0) {
        // F-090c (R-NEW-317) name-law fix: ViewShadow::name() answers "View",
        // so the old `!= "ViewShadow"` filter SKIPPED the ViewShadow-first
        // route on every call — dead code since F-057. Owner-tag walks whose
        // bridge key is an app class (dooz MainActivity receiver →
        // ViewTreeLifecycleOwner.get) fell through to the EXP-075 Activity
        // gate (ViewShadow::handles_class rejects "*Activity;") →
        // ActivityShadow → no tag / no parent → walk dead-ended →
        // "ViewTreeLifecycleOwner not found" ISE → Compose composition died
        // before the first frame. Route by the shadow's C++ TYPE (same
        // identity find_as uses), not by its display name.
        for (auto& s : shadows_) {
            if (dynamic_cast<framework::ViewShadow*>(s.get()) == nullptr)
                continue;
            CallResult r = s->dispatch(ctx);
            if (r.handled) {
                calls_handled_++;
                return r;
            }
        }
    }
    for (auto& s : shadows_) {
        if (!s->handles_class(ctx.class_name)) continue;
        CallResult r = s->dispatch(ctx);
        if (r.handled) {
            calls_handled_++;
            return r;
        }
    }
    calls_fallback_++;
    return CallResult::not_handled();
}

ShadowRegistry::Stats ShadowRegistry::stats() const {
    Stats s;
    s.shadow_count = shadows_.size();
    for (const auto& sh : shadows_) {
        s.total_implemented += sh->implemented_methods().size();
        s.total_stubbed     += sh->stubbed_methods().size();
    }
    s.calls_dispatched = calls_dispatched_;
    s.calls_handled    = calls_handled_;
    s.calls_fallback   = calls_fallback_;
    return s;
}

Shadow* ShadowRegistry::find(const std::string& name) const {
    for (const auto& s : shadows_) {
        if (s->name() == name) return s.get();
    }
    return nullptr;
}

// ─────────────────────────────────────────────────────────────────────────
// Diagnostic dump
// ─────────────────────────────────────────────────────────────────────────
std::string format_shadow_report(const ShadowRegistry& reg) {
    std::ostringstream os;
    auto st = reg.stats();
    os << "Shadow Registry Report\n";
    os << "======================\n";
    os << "Shadows registered:        " << st.shadow_count << "\n";
    os << "Methods fully implemented:  " << st.total_implemented << "\n";
    os << "Methods stubbed:           " << st.total_stubbed << "\n";
    os << "Calls dispatched:           " << st.calls_dispatched << "\n";
    os << "  handled by a shadow:      " << st.calls_handled << "\n";
    os << "  fell through to legacy:   " << st.calls_fallback << "\n";
    if (st.calls_dispatched > 0) {
        double coverage = 100.0 * st.calls_handled / st.calls_dispatched;
        os << "Shadow coverage:            " << std::fixed << std::setprecision(1)
           << coverage << "%\n";
    }
    return os.str();
}

// ─────────────────────────────────────────────────────────────────────────
// MASTER CAMPAIGN FIX — canonical platform shadow registration.
// ONE list, used by every registry owner (cmd_run + ApplicationRuntime).
// Registration order matters: ArchTaskExecutorShadow first (EXP-052 law:
// wins over the legacy bridge chain for isMainThread); ViewShadow before
// DialogShadow (CAMPAIGN 013 B1: dialog decor trees build on ViewShadow
// nodes); ClipboardShadow/LayoutInflaterShadow last (first handled wins).
// ─────────────────────────────────────────────────────────────────────────
void register_platform_shadows(ShadowRegistry& reg) {
    reg.register_shadow<ArchTaskExecutorShadow>();
    reg.register_shadow<CollectionShadow>();
    reg.register_shadow<ThreadShadow>();
    // F-141 chain (S72-W3): java.lang.Runtime singleton law — registered
    // with the subsystem shadows (exact-class claim) BEFORE any catch-all
    // path. Evidence: dooz Lxr1;.<clinit> needed Runtime.getRuntime().
    // availableProcessors() during Dispatchers.Default init; the generic
    // stub returned null and the F-141 NPE law fired at the consumer.
    reg.register_shadow<RuntimeShadow>();
    // F-141c (S72-W3): android.app.FragmentManager/FragmentTransaction —
    // androidx LifecycleDispatcher report-fragment install path (dooz).
    reg.register_shadow<FragmentManagerShadow>();
    reg.register_shadow<LooperShadow>();
    reg.register_shadow<HandlerShadow>();
    reg.register_shadow<ActivityShadow>();
    reg.register_shadow<IntentShadow>();
    // M3 FAMILY-L ROOT FIX: java.util.concurrent.locks family
    // (ReentrantReadWriteLock/ReadLock/WriteLock/ReentrantLock). Exact-class
    // claims only; registered with the other subsystem shadows so the
    // catch-all view path can never capture lock descriptors. Root-gap
    // evidence: microtimer Room insert path (Kotlin Intrinsics null-check
    // on readLock() result) under the F-016 real-unwind law.
    reg.register_shadow<LocksShadow>();
    // M3 F-020 ROOT FIX: java.util.concurrent.atomic family
    // (AtomicReference/AtomicInteger/AtomicLong/AtomicBoolean + subclasses).
    // Exact prefix claim, registered before ViewShadow so the catch-all
    // view path can never capture atomic descriptors. Root-gap evidence:
    // dooz Compose snapshot chain — AtomicReference.<init>(globalSnapshot)
    // missed every shadow, the bridge's view-parent retry routed the ctor
    // to ViewShadow (phantom view node, dropped value), get() returned
    // null, SnapshotKt.currentSnapshot() was null, and the fail-soft
    // null-receiver iget manufactured snapshot id 0 → Compose readError
    // ISE at setContent (dooz PARTIAL).
    reg.register_shadow<AtomicShadow>();
    // M3 §4 EXECUTOR/EXECUTORS CLOSURE: executor family on the deterministic
    // virtual scheduler (one MessageQueue law). Exact-class claims only.
    reg.register_shadow<ExecutorShadow>();
    // M3 F-018 ROOT FIX: android.app intent-sender + alarm scheduling
    // family (PendingIntent.get* AMS record law, AlarmManager cancel/
    // exact-alarm capability law). Exact-class claims only; registered
    // before ViewShadow so the catch-all view path can never capture
    // framework alarm descriptors. Root-gap evidence: microtimer second-
    // run path (F-012 rc-law) — no PendingIntent factory existed, the
    // unresolved static call silently returned null, and the Kotlin
    // Intrinsics null-check threw NPE at MainActivity.onCreate.
    reg.register_shadow<PendingIntentShadow>();
    // F-050 ROOT FIX: android.view.Choreographer family (frame-pump law).
    // Compose's AndroidUiDispatcher/AndroidUiFrameClock park the first
    // composition at withFrameNanos behind a posted FrameCallback; without
    // this shadow postFrameCallback silently dropped and doFrame never
    // fired (dooz AndroidComposeView children=0, blank frame). Exact-class
    // claim; registered before ViewShadow so the catch-all view path can
    // never capture the Choreographer descriptor.
    reg.register_shadow<ChoreographerShadow>();
    // M3 F-ROOM-CHAIN: SQLite family (REAL sqlite3 backend). Exact-class
    // claims only; registered before ViewShadow so the catch-all view
    // path can never capture framework database descriptors.
    reg.register_shadow<storage::DatabaseShadow>();
    // S56 F-085: WebSettings property-bag shadow — registered BEFORE
    // ViewShadow so the WebSettings descriptor can never fall through to
    // the view catch-all (WebSettings getters would otherwise be claimed
    // by method-name heuristics on the wrong receiver domain).
    reg.register_shadow<WebSettingsShadow>();
    // S83-GFX-BASE §32: F-NEW-159 semantic shadows — android.os.LocaleList /
    // java.util.Locale / android.view.WindowInsetsController. Registered
    // BEFORE ViewShadow (exact-class claims) so the catch-all view path can
    // never capture these descriptors; the producers (Configuration.
    // getLocales, Window.getInsetsController) resolve in the engine bridge.
    reg.register_shadow<LocaleInsetsShadow>();
    // S83-GFX-BASE §24/§25: GLSurfaceView + GL10/EGL model — registered
    // BEFORE ViewShadow; GL-specific methods handled here, View methods
    // fall through to the ViewShadow catch-all (GLSurfaceView IS-A View).
    reg.register_shadow<GLSurfaceViewShadow>();
    // S86 §F-NEW-164: SurfaceView + SurfaceHolder real-surface law —
    // registered BEFORE ViewShadow (SurfaceView IS-A View; View methods
    // fall through). Ground truth: dozingcat Dodge FieldView lockCanvas
    // draw loop; compositor side = CanvasShadow::replay_surface.
    reg.register_shadow<SurfaceViewShadow>();
    reg.register_shadow<ViewShadow>();
    reg.register_shadow<DialogShadow>();
    reg.register_shadow<ArrayAdapterShadow>();
    // S68 §12/§13: Bitmap/BitmapFactory pixel store — BEFORE CanvasShadow so
    // drawBitmap resolves pixels (Canvas itself never decodes).
    reg.register_shadow<BitmapShadow>();
    // S83-GFX-BASE §C1: android.graphics.Matrix — real 3x3 value semantics
    // (m0..m8 heap fields). Registered BEFORE CanvasShadow so Canvas.concat
    // / drawBitmap(Bitmap,Matrix,Paint) resolve matrices. Exact-class claim.
    reg.register_shadow<MatrixShadow>();
    reg.register_shadow<CanvasShadow>();
    reg.register_shadow<LayoutInflaterShadow>();
    reg.register_shadow<ClipboardShadow>();
    // S99-MG-223: android.animation animator family — static factories
    // (ofInt/ofFloat/ofArgb/ofObject) MUST return a non-null animator.
    // Exact-family claim; registered last: no earlier shadow claims these
    // descriptors, the engine default (null object) is what broke babydots
    // (ValueAnimator.setRepeatCount on a null object reference → APP
    // BOUNDARY unwind).
    reg.register_shadow<AnimatorShadow>();
}

}} // namespace miniandroid::framework
