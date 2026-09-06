// g11_ctor_law_test — G11 real-DEX constructor + custom-hierarchy law battery.
//
// Law references (AOSP):
//   * LayoutInflater.createView: XML tag -> resolve class -> verify View
//     subtype -> resolve <init>(Context, AttributeSet...) -> invoke -> real
//     constructor body -> super chain (LayoutInflater.java, frameworks/base).
//   * LayoutInflater Factory law: the phone process (re)applies the Factory
//     to EVERY newly created LayoutInflater
//     (AppCompatDelegateImpl.installViewFactory -> setFactory2). A factory
//     installed on one instance must not be silently lost when the runtime
//     recreates the inflater (ResourceRuntime.ensure_loaded()).
//   * ViewGroup.addView: "The specified child already has a parent" — a View
//     is mounted exactly once; a mount that would duplicate a parent edge or
//     create a parent/child cycle is rejected before mutation.
//   * Constructor hostile surface (campaign §28): missing class, missing heap
//     object, garbage/absent arguments, self-mount, ancestor-cycle mount —
//     all must fail loudly / be rejected, never crash, hang, or silently
//     corrupt the hierarchy.
//
// Tests are package-independent: no APK, no ARSC, synthetic trees.

#include "../src/resources/layout_inflater.h"
#include "../src/resources/resource_runtime.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/shadow_registry.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
    else      printf("  PASS: %s\n", what.c_str());
}

// ─────────────────────────────────────────────────────────────────────────
// A. App-descriptor gate (LayoutInflater::is_app_class_descriptor).
//    The gate only filters framework/library prefixes; the DEX class-index
//    is the real authority. Obfuscated app classes (Lk/g;) MUST pass —
//    corpus evidence: microtimer.
// ─────────────────────────────────────────────────────────────────────────
static void test_descriptor_gate() {
    printf("[A] app-class descriptor gate\n");
    using F = bool (*)(const std::string&);
    F gate = &resources::LayoutInflater::is_app_class_descriptor;

    check(gate("Lorg/debian/eugen/headingcalculator/CalculatorDisplay;"),
          "fully-qualified app class passes (headingcalculator)");
    check(gate("Lk/g;"),
          "obfuscated app class passes (microtimer Lk/g;)");
    check(gate("Ldubrowgn/microtimer/RoTimeControl;"),
          "corpus app class passes");
    check(gate("Lcom/example/custom/MyView;"),
          "com.example app namespace passes");
    check(gate("Lomegacentauri/mobi/simplestopwatch/BigTextView;"),
          "simplestopwatch BigTextView passes");

    check(!gate("Landroid/widget/LinearLayout;"),
          "framework android.widget rejected");
    check(!gate("Ljava/lang/Object;"), "java.* rejected");
    check(!gate("Lkotlin/jvm/internal/Intrinsics;"), "kotlin.* rejected");
    check(!gate("Lcom/google/android/material/button/MaterialButton;"),
          "com.google.android.* rejected");
    check(!gate("Lj$/util/Optional;"), "desugared j$ rejected");
    check(!gate(""), "empty descriptor rejected");
    check(!gate("L"), "one-char descriptor rejected");
    check(!gate("org/debian/CalculatorDisplay;"),
          "descriptor without L prefix rejected");
}

// ─────────────────────────────────────────────────────────────────────────
// B. Factory law — the process-wide ctor hook must survive LayoutInflater
//    (re)creation. This is the regression test for the F5-C1 ordering bug:
//    a hook set BEFORE the real inflater exists was silently wiped by
//    ensure_loaded's make_unique.
// ─────────────────────────────────────────────────────────────────────────
static void test_factory_law() {
    printf("[B] LayoutInflater Factory law (hook survives recreation)\n");
    auto& rt = resources::ResourceRuntime::instance();

    // B1: hook installed BEFORE the inflater exists must reach the lazily
    // created inflater (the exact bug that killed headingcalculator).
    {
        int calls = 0;
        rt.set_custom_view_ctor_hook(
            [&](uint32_t, const std::string&) -> bool {
                calls++;
                return true;
            });
        // Force a fresh inflater via the lazy accessor (no APK loaded —
        // the TICTACTOE-GOLDEN lazy path).
        resources::LayoutInflater& inf = rt.inflater();
        auto& hook = inf.custom_view_ctor_hook();
        check(static_cast<bool>(hook), "lazy-created inflater carries the pre-installed hook");
        if (hook) hook(1, "Ltest/View;");
        check(calls == 1, "pre-installed hook is invocable (calls=1)");
    }
    // B2: a hook installed AFTER the inflater exists must propagate
    // immediately and REPLACE the previous one (single-factory law).
    {
        int calls2 = 0;
        rt.set_custom_view_ctor_hook(
            [&](uint32_t, const std::string&) -> bool {
                calls2++;
                return true;
            });
        resources::LayoutInflater& inf = rt.inflater();
        auto& hook = inf.custom_view_ctor_hook();
        check(static_cast<bool>(hook), "post-installed hook propagates to existing inflater");
        if (hook) hook(2, "Ltest/View;");
        check(calls2 == 1, "replacement hook receives the call (calls2=1)");
    }
    rt.set_custom_view_ctor_hook(nullptr);  // leave runtime clean for other tests
}

// ─────────────────────────────────────────────────────────────────────────
// C. LayoutInflaterShadow dispatch — from()/inflate() hostile surface.
// ─────────────────────────────────────────────────────────────────────────
static void test_inflater_shadow() {
    printf("[C] LayoutInflaterShadow dispatch (hostile args)\n");
    dalvik::DalvikHeap heap;
    // Engine-backed adapter: the LayoutInflater.from singleton law holds in
    // the ENGINE's api_singletons_ cache (same cache the real runtime uses).
    dalvik::DalvikExecutionEngine engine;
    framework::DalvikHeapAdapter heap_adapter{&heap, &engine};
    framework::ShadowRegistry reg;
    reg.register_shadow<framework::ViewShadow>();
    // Dispatch against the REGISTERED shadow instance (the registry wires
    // heap_/registry_ on the instances it owns — a stack copy is unwired).
    auto* inflater_shadow = reg.register_shadow<framework::LayoutInflaterShadow>();
    reg.set_heap(&heap_adapter);

    // C1: from(Context) — singleton object, stable across calls.
    framework::CallContext ctx;
    ctx.class_name = "Landroid/view/LayoutInflater;";
    ctx.method = "from";
    auto r1 = inflater_shadow->dispatch(ctx);
    auto r2 = inflater_shadow->dispatch(ctx);
    check(r1.handled && r1.ret_kind == framework::CallResult::RetKind::OBJECT &&
          r1.object_id != 0,
          "LayoutInflater.from returns a real object");
    check(r1.object_id == r2.object_id,
          "LayoutInflater.from is a shared singleton (same object id)");

    // C2: inflate(0) — AOSP InflateException-free subset: null.
    framework::CallContext c0;
    c0.class_name = "Landroid/view/LayoutInflater;";
    c0.method = "inflate";
    framework::CallContext::Arg a0;
    a0.kind = framework::CallContext::Arg::Kind::INT;
    a0.int_val = 0;
    c0.args.push_back(a0);
    auto r0 = inflater_shadow->dispatch(c0);
    check(r0.handled && r0.ret_kind == framework::CallResult::RetKind::NULL_REF,
          "inflate(0) -> null (no crash)");

    // C3: garbage resid (no ARSC loaded) -> null, no crash.
    framework::CallContext cg = c0;
    cg.args[0].int_val = 0x7f030042;
    auto rg_ = inflater_shadow->dispatch(cg);
    check(rg_.handled && rg_.ret_kind == framework::CallResult::RetKind::NULL_REF,
          "inflate(garbage resid, no ARSC) -> null (no crash)");

    // C4: wrong argument KIND (string instead of int) -> treated as
    // missing/default, null result, no crash (hostile arg surface).
    framework::CallContext cs;
    cs.class_name = "Landroid/view/LayoutInflater;";
    cs.method = "inflate";
    framework::CallContext::Arg sarg;
    sarg.kind = framework::CallContext::Arg::Kind::STRING;
    sarg.string_val = "not-an-int";
    cs.args.push_back(sarg);
    auto rs = inflater_shadow->dispatch(cs);
    check(rs.handled && rs.ret_kind == framework::CallResult::RetKind::NULL_REF,
          "inflate(wrong-kind arg) -> null (no crash)");

    // C5: unknown method -> not handled (pass-through), no crash.
    framework::CallContext cx;
    cx.class_name = "Landroid/view/LayoutInflater;";
    cx.method = "obtainStyledAttributes";
    auto rx = inflater_shadow->dispatch(cx);
    check(!rx.handled, "unknown LayoutInflater method passes through");
}

// ─────────────────────────────────────────────────────────────────────────
// D. addView single-mount law + hostile surface (§28).
// ─────────────────────────────────────────────────────────────────────────
static void test_addview_law() {
    printf("[D] addView single-mount + cycle hostile laws\n");
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    views.init(&heap_adapter);

    uint32_t root = views.create_view("Landroid/widget/LinearLayout;");
    uint32_t a = views.create_view("Landroid/widget/Button;");
    uint32_t b = views.create_view("Landroid/widget/Button;");

    // D1: normal mounts preserve order + count.
    check(views.add_child(root, a), "first mount succeeds");
    check(views.add_child(root, b), "second mount succeeds");
    check(views.find_node(root)->children.size() == 2,
          "child count is exactly 2 after two mounts");
    check(views.find_node(root)->children[0] == a &&
          views.find_node(root)->children[1] == b,
          "mount order preserved (AOSP addView index law)");

    // D2: duplicate same-parent mount must NOT duplicate the edge.
    check(views.add_child(root, a),
          "re-addView of an already-mounted child is accepted (no-op)");
    check(views.find_node(root)->children.size() == 2,
          "duplicate mount does not duplicate the child entry");

    // D3: re-parent move (AOSP single-parent law).
    uint32_t c = views.create_view("Landroid/widget/FrameLayout;");
    check(views.add_child(c, a), "re-mount under another parent succeeds");
    check(views.find_node(root)->children.size() == 1,
          "old parent lost the child on re-mount");
    check(views.find_node(c)->children.size() == 1 &&
          views.find_node(a)->parent_id == c,
          "new parent owns exactly one edge to the child");

    // D4: self-mount rejected.
    check(!views.add_child(root, root), "addView(self) rejected");

    // D5: ancestor-cycle rejected (mounting an ancestor under its own
    // descendant would create A->B->A and infinite measure/BFS recursion).
    check(views.add_child(root, c), "c now under root (A->C)");
    // root -> c -> ... try to mount root under c: cycle root->c->root.
    check(!views.add_child(c, root), "ancestor-cycle mount rejected");

    // D6: null nodes rejected, no crash.
    check(!views.add_child(0, a), "null parent rejected");
    check(!views.add_child(root, 99999), "missing child id rejected");
}

int main() {
    test_descriptor_gate();
    test_factory_law();
    test_inflater_shadow();
    test_addview_law();
    printf("\nG11 ctor law battery: %d checks, %d failures\n", g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
