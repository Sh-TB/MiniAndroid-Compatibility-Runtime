// s98_scroll_transform_law_test.cpp — S98 layout/geometry micro-gap fence
// (MG-123, MG-124..MG-129). Drives the REAL ViewShadow::dispatch (the same
// bridge every DEX View call flows through) and asserts the AOSP View.java
// laws:
//
//   T1 (MG-123 scrollTo)      — scrollTo(30,40) sets the offsets; getScrollX/Y
//                               read them back (View.java L14600+).
//   T2 (MG-123 scrollBy)      — scrollBy(10,-5) ADDS to the current offsets
//                               (scrollBy == scrollTo(mScrollX+x, mScrollY+y)).
//   T3 (MG-123 defaults)      — a fresh view reads scroll 0/0 (View.java:
//                               mScrollX/mScrollY default 0).
//   T4 (MG-124 setTranslationX/Y + getters) — value law + default 0.
//   T5 (MG-126 setScaleX/Y + getters)       — value law + default 1.
//   T6 (MG-128 setRotation + getRotation)   — value law + default 0.
//   T7 (MG-129 setPivotX/Y + getters)       — value law + default 0.
//   T8 (render law, translation) — the draw-walk delta composition:
//                               child content origin = untranslated +
//                               Σancestor translations − Σancestor scrolls.
//                               Asserted on the ViewNode fields the walk
//                               consumes (scroll_x/y + translation_x/y
//                               survive round-trip through dispatch).
//
// Exit 0 iff ALL laws hold.

#include "../src/framework/android_shadows.h"

#include <cstdio>

using namespace miniandroid::framework;

static int g_pass = 0, g_fail = 0;

static void check(const char* name, bool ok, const std::string& detail = "") {
    if (ok) { ++g_pass; std::printf("PASS %s %s\n", name, detail.c_str()); }
    else    { ++g_fail; std::printf("FAIL %s %s\n", name, detail.c_str()); }
}

static CallContext make_ctx(ViewShadow& shadow, const char* method,
                            const char* descriptor, float a0, float a1) {
    CallContext ctx;
    ctx.class_name = "Landroid/view/View;";
    ctx.method = method;
    ctx.descriptor = descriptor;
    ctx.has_receiver = true;
    ctx.receiver_id = 4242;  // any node id; get_or_create_node materializes it
    ctx.receiver_class = "Landroid/view/View;";
    CallContext::Arg arg0; arg0.kind = CallContext::Arg::Kind::FLOAT; arg0.float_val = a0;
    CallContext::Arg arg1; arg1.kind = CallContext::Arg::Kind::FLOAT; arg1.float_val = a1;
    ctx.args.push_back(arg0);
    ctx.args.push_back(arg1);
    (void)shadow;
    return ctx;
}

int main() {
    ViewShadow shadow;

    // ── T3: defaults ──────────────────────────────────────────────────
    {
        auto r = shadow.dispatch(make_ctx(shadow, "getScrollX", "()I", 0, 0));
        check("T3a mg-123 scrollX default 0", r.handled && r.int_val == 0,
              "got " + std::to_string(r.int_val));
        auto r2 = shadow.dispatch(make_ctx(shadow, "getScrollY", "()I", 0, 0));
        check("T3b mg-123 scrollY default 0", r2.handled && r2.int_val == 0,
              "got " + std::to_string(r2.int_val));
    }

    // ── T1: scrollTo + getters ────────────────────────────────────────
    {
        auto w = shadow.dispatch(make_ctx(shadow, "scrollTo", "(II)V", 30, 40));
        check("T1a mg-123 scrollTo handles", w.handled);
        auto x = shadow.dispatch(make_ctx(shadow, "getScrollX", "()I", 0, 0));
        auto y = shadow.dispatch(make_ctx(shadow, "getScrollY", "()I", 0, 0));
        check("T1b mg-123 scrollTo state", x.int_val == 30 && y.int_val == 40,
              "x=" + std::to_string(x.int_val) + " y=" + std::to_string(y.int_val));
    }

    // ── T2: scrollBy accumulates ──────────────────────────────────────
    {
        shadow.dispatch(make_ctx(shadow, "scrollBy", "(II)V", 10, -5));
        auto x = shadow.dispatch(make_ctx(shadow, "getScrollX", "()I", 0, 0));
        auto y = shadow.dispatch(make_ctx(shadow, "getScrollY", "()I", 0, 0));
        check("T2 mg-123 scrollBy adds", x.int_val == 40 && y.int_val == 35,
              "x=" + std::to_string(x.int_val) + " y=" + std::to_string(y.int_val));
    }

    // ── T4: translation ───────────────────────────────────────────────
    {
        auto x0 = shadow.dispatch(make_ctx(shadow, "getTranslationX", "()F", 0, 0));
        check("T4a mg-124 translationX default 0", x0.float_val == 0.0f);
        shadow.dispatch(make_ctx(shadow, "setTranslationX", "(F)V", 12.5f, 0));
        shadow.dispatch(make_ctx(shadow, "setTranslationY", "(F)V", -3.25f, 0));
        auto x = shadow.dispatch(make_ctx(shadow, "getTranslationX", "()F", 0, 0));
        auto y = shadow.dispatch(make_ctx(shadow, "getTranslationY", "()F", 0, 0));
        check("T4b mg-124/125 translation round-trip",
              x.float_val == 12.5f && y.float_val == -3.25f,
              "x=" + std::to_string(x.float_val) + " y=" + std::to_string(y.float_val));
    }

    // ── T5: scale (default 1 = View.java mScaleX/mScaleY) ─────────────
    {
        auto x0 = shadow.dispatch(make_ctx(shadow, "getScaleX", "()F", 0, 0));
        auto y0 = shadow.dispatch(make_ctx(shadow, "getScaleY", "()F", 0, 0));
        check("T5a mg-126/127 scale defaults 1",
              x0.float_val == 1.0f && y0.float_val == 1.0f);
        shadow.dispatch(make_ctx(shadow, "setScaleX", "(F)V", 2.0f, 0));
        shadow.dispatch(make_ctx(shadow, "setScaleY", "(F)V", 0.5f, 0));
        auto x = shadow.dispatch(make_ctx(shadow, "getScaleX", "()F", 0, 0));
        auto y = shadow.dispatch(make_ctx(shadow, "getScaleY", "()F", 0, 0));
        check("T5b mg-126/127 scale round-trip",
              x.float_val == 2.0f && y.float_val == 0.5f);
    }

    // ── T6: rotation ──────────────────────────────────────────────────
    {
        auto r0 = shadow.dispatch(make_ctx(shadow, "getRotation", "()F", 0, 0));
        check("T6a mg-128 rotation default 0", r0.float_val == 0.0f);
        shadow.dispatch(make_ctx(shadow, "setRotation", "(F)V", 45.0f, 0));
        auto r = shadow.dispatch(make_ctx(shadow, "getRotation", "()F", 0, 0));
        check("T6b mg-128 rotation round-trip", r.float_val == 45.0f);
    }

    // ── T7: pivot ─────────────────────────────────────────────────────
    {
        shadow.dispatch(make_ctx(shadow, "setPivotX", "(F)V", 540.0f, 0));
        shadow.dispatch(make_ctx(shadow, "setPivotY", "(F)V", 960.0f, 0));
        auto x = shadow.dispatch(make_ctx(shadow, "getPivotX", "()F", 0, 0));
        auto y = shadow.dispatch(make_ctx(shadow, "getPivotY", "()F", 0, 0));
        check("T7 mg-129 pivot round-trip",
              x.float_val == 540.0f && y.float_val == 960.0f);
    }

    // ── T8: node state survives for the draw walk ─────────────────────
    {
        const auto* n = shadow.find_node(4242);
        check("T8 s98 walk delta inputs",
              n && n->scroll_x == 40 && n->scroll_y == 35 &&
              n->translation_x == 12.5f && n->translation_y == -3.25f,
              "walk consumes scroll+translation node state");
    }

    std::printf("S98 SCROLL/TRANSFORM LAW BATTERY: %d passed, %d failed\n",
                g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
