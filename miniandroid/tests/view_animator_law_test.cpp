// view_animator_law_test — S55 F-082 ViewAnimator displayed-child law battery.
//
// Law references (AOSP ViewAnimator.java, verified against the framework
// source family):
//   * initView law: an inflated ViewAnimator starts with mWhichChild = 0
//     and showOnly(0) — child 0 VISIBLE, every other child GONE (mirrored
//     by the inflater's G10 FIX-G10-002b: children >= 1 start GONE).
//   * setDisplayedChild(whichChild) → showOnly(clamp(whichChild)):
//     whichChild >= childCount → childCount-1; whichChild < 0 → 0.
//     showOnly(i): child i VISIBLE, every other child GONE; then
//     requestLayout() + invalidate().
//   * showNext/showPrevious → setDisplayedChild(mWhichChild ± 1) — the
//     clamp inside setDisplayedChild pins the ends (NO wraparound).
//   * getDisplayedChild reflects the last accepted whichChild.
//
// Motivating failure (R-NEW-361-era corpus law): billthefarmer Notes v139
// drives its read↔edit faces through a ViewSwitcher; without the law the
// shadow dropped setDisplayedChild as REC-MISS and the state machine was
// a silent no-op. Generic: ANY ViewAnimator-family receiver.
//
// Tests are package-independent: no APK, no ARSC, synthetic trees.

#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/framework/shadow_registry.h"
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

namespace {

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ShadowRegistry reg;
    framework::ViewShadow* views = nullptr;

    Rig() {
        views = reg.register_shadow<framework::ViewShadow>();
        reg.set_heap(&heap_adapter);
        views->init(&heap_adapter);
    }

    uint32_t child(const char* cls, uint32_t parent) {
        uint32_t id = views->create_view(cls);
        if (parent) views->add_child(parent, id);
        return id;
    }

    framework::CallResult call(const std::string& method, uint32_t recv,
                               int32_t arg0, bool with_arg) {
        framework::CallContext ctx;
        ctx.class_name = "Landroid/widget/ViewSwitcher;";
        ctx.method = method;
        ctx.descriptor = with_arg ? "(I)V" : "()V";
        ctx.has_receiver = true;
        ctx.receiver_id = recv;
        ctx.receiver_class = ctx.class_name;
        if (with_arg) {
            framework::CallContext::Arg a;
            a.kind = framework::CallContext::Arg::Kind::INT;
            a.int_val = arg0;
            ctx.args.push_back(a);
        }
        return views->dispatch(ctx);
    }

    framework::ViewShadow::ViewNode* get(uint32_t id) {
        return views->find_node(id);
    }
};

}  // namespace

int main() {
    printf("== F-082 §A: init law — inflated ViewSwitcher starts at child 0 ==\n");
    {
        printf("[1] two-face ViewSwitcher: displayed_child defaults to 0\n");
        Rig r;
        uint32_t sw = r.child("Landroid/widget/ViewSwitcher;", 0);
        uint32_t face_a = r.child("Lorg/app/MarkdownFace;", sw);
        uint32_t face_b = r.child("Lorg/app/EditFace;", sw);
        (void)face_b;
        check(r.get(sw)->displayed_child == 0,
              "mWhichChild starts at 0 (ViewAnimator.initView)");
    }

    printf("== F-082 §B: setDisplayedChild clamp + showOnly visibility walk ==\n");
    {
        printf("[2] setDisplayedChild(1) shows child 1, GONEs child 0\n");
        Rig r;
        uint32_t sw = r.child("Landroid/widget/ViewSwitcher;", 0);
        uint32_t face_a = r.child("Lorg/app/MarkdownFace;", sw);
        uint32_t face_b = r.child("Lorg/app/EditFace;", sw);
        auto res = r.call("setDisplayedChild", sw, 1, true);
        check(res.handled, "setDisplayedChild is handled by ViewShadow");
        check(r.get(sw)->displayed_child == 1, "mWhichChild = 1");
        check(r.get(face_a)->visibility == 8,
              "child 0 GONE (showOnly walk)");
        check(r.get(face_b)->visibility == 0,
              "child 1 VISIBLE (showOnly walk)");
        check(r.views->layout_dirty,
              "requestLayout() flagged (showOnly tail)");

        printf("[3] clamp high: setDisplayedChild(99) pins to childCount-1\n");
        auto res2 = r.call("setDisplayedChild", sw, 99, true);
        check(res2.handled && r.get(sw)->displayed_child == 1,
              "whichChild clamped to childCount-1 (AOSP clamp)");
        printf("[4] clamp low: setDisplayedChild(-3) pins to 0\n");
        auto res3 = r.call("setDisplayedChild", sw, -3, true);
        check(res3.handled && r.get(sw)->displayed_child == 0,
              "whichChild clamped to 0 (AOSP clamp)");
        check(r.get(face_a)->visibility == 0 && r.get(face_b)->visibility == 8,
              "showOnly(0) re-applied after clamp");
    }

    printf("== F-082 §C: showNext/showPrevious — step + end clamp, NO wraparound ==\n");
    {
        printf("[5] showNext from 0 → 1; showNext again pins at 1 (two faces)\n");
        Rig r;
        uint32_t sw = r.child("Landroid/widget/ViewSwitcher;", 0);
        uint32_t face_a = r.child("Lorg/app/A;", sw);
        uint32_t face_b = r.child("Lorg/app/B;", sw);
        auto n1 = r.call("showNext", sw, 0, false);
        check(n1.handled && r.get(sw)->displayed_child == 1, "showNext → 1");
        auto n2 = r.call("showNext", sw, 0, false);
        check(n2.handled && r.get(sw)->displayed_child == 1,
              "showNext clamps at end (no wraparound to 0)");
        check(r.get(face_a)->visibility == 8 && r.get(face_b)->visibility == 0,
              "visibility walk consistent after end clamp");

        printf("[6] showPrevious from 1 → 0; showPrevious again pins at 0\n");
        auto p1 = r.call("showPrevious", sw, 0, false);
        check(p1.handled && r.get(sw)->displayed_child == 0,
              "showPrevious → 0");
        auto p2 = r.call("showPrevious", sw, 0, false);
        check(p2.handled && r.get(sw)->displayed_child == 0,
              "showPrevious clamps at 0 (no wraparound)");
    }

    printf("== F-082 §D: getDisplayedChild reflects the accepted whichChild ==\n");
    {
        printf("[7] getDisplayedChild returns the clamp-adjusted value\n");
        Rig r;
        uint32_t sw = r.child("Landroid/widget/ViewSwitcher;", 0);
        r.child("Lorg/app/A;", sw);
        r.child("Lorg/app/B;", sw);
        r.call("setDisplayedChild", sw, 1, true);
        auto g1 = r.call("getDisplayedChild", sw, 0, false);
        check(g1.handled && g1.ret_kind == framework::CallResult::RetKind::INT &&
              g1.int_val == 1,
              "getDisplayedChild → 1 after setDisplayedChild(1)");
    }

    printf("== F-082 §E: empty ViewSwitcher hostile surface ==\n");
    {
        printf("[8] setDisplayedChild/showNext on a childless ViewAnimator\n");
        Rig r;
        uint32_t sw = r.child("Landroid/widget/ViewSwitcher;", 0);
        auto res = r.call("setDisplayedChild", sw, 5, true);
        check(res.handled && r.get(sw)->displayed_child == 0,
              "childless switcher clamps to 0 without crash");
        auto res2 = r.call("showNext", sw, 0, false);
        check(res2.handled && r.get(sw)->displayed_child == 0,
              "childless showNext stays at 0 without crash");
    }

    printf("== F-082 §F: method family is dispatched (REC-MISS closure) ==\n");
    {
        printf("[9] ViewAnimator family methods all handled on the shadow\n");
        Rig r;
        uint32_t sw = r.child("Landroid/widget/ViewSwitcher;", 0);
        r.child("Lorg/app/A;", sw);
        r.child("Lorg/app/B;", sw);
        const char* family[] = {"setDisplayedChild", "getDisplayedChild",
                                "showNext", "showPrevious"};
        bool all = true;
        for (const char* m : family) {
            framework::CallContext ctx;
            ctx.class_name = "Landroid/widget/ViewSwitcher;";
            ctx.method = m;
            ctx.has_receiver = true;
            ctx.receiver_id = sw;
            ctx.receiver_class = ctx.class_name;
            auto res = r.views->dispatch(ctx);
            all = all && res.handled;
        }
        check(all, "setDisplayedChild/getDisplayedChild/showNext/showPrevious "
                   "all handled (no REC-MISS fallback)");
    }

    printf("\nF-082 view_animator_law_test: %d checks, %d failures\n",
           g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
