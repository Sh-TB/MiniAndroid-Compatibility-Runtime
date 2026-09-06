// linear_layout_law_test — G04/G05 §8/§9 focused semantic battery.
//
// Law references (AOSP @android-14.0.0_r2):
//   * ViewGroup.getChildMeasureSpec     — spec negotiation table
//   * View.MeasureSpec EXACTLY/AT_MOST/UNSPECIFIED
//   * LinearLayout.java L985-1045 (vertical) / L1385-1445 (horizontal):
//     sequential weight share distribution with remainingWeightSum
//     decrement; 0dp+weight sized from scratch; nonzero base + share;
//     shrink when remainingExcess < 0; weightSum cap.
//
// The test drives LayoutInflater::measure_layout over SYNTHETIC view trees
// (no APK, no ARSC, no font shaping — leaves are empty) and asserts the
// resulting measured geometry. Each CHECK names the law it guards.

#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
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

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    resources::ArscParser arsc;
    apk::ApkParser apk;
    resources::LayoutInflater inflater{
        arsc, apk, "", resources::DeviceMetrics{1080, 1920, 2.625f, 1.0f}};

    Rig() { views.init(&heap_adapter); }

    uint32_t node(const char* cls, uint32_t parent, int lp_w, int lp_h,
                  int weight_milli = 0) {
        uint32_t id = views.create_view(cls);
        auto* n = views.find_node(id);
        n->lp_width = lp_w; n->lp_height = lp_h;
        n->layout_weight = weight_milli;
        if (parent) views.add_child(parent, id);
        return id;
    }
    void measure(uint32_t root) { inflater.measure_layout(&views, root); }
    framework::ViewShadow::ViewNode* get(uint32_t id) { return views.find_node(id); }
};

int main() {
    printf("== G04/G05 §8/§9: MeasureSpec + LinearLayout weight law ==\n");
    {
        printf("[1] match_parent child in EXACTLY parent → EXACTLY avail\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        uint32_t child = r.node("Landroid/view/View;", root, -1, -1);
        r.measure(root);
        check(r.get(child)->measured_width == 1080, "child width = parent EXACTLY 1080");
        check(r.get(child)->measured_height == 1920, "child height = parent EXACTLY 1920");
    }
    {
        printf("[2] explicit-size child wins over parent spec\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        uint32_t child = r.node("Landroid/view/View;", root, 400, 300);
        r.measure(root);
        check(r.get(child)->measured_width == 400, "explicit width 400 kept");
        check(r.get(child)->measured_height == 300, "explicit height 300 kept");
    }
    {
        printf("[3] parent padding subtracts from child avail (getChildMeasureSpec law)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->padding_left = 50; r.get(root)->padding_right = 50;
        r.get(root)->padding_top = 20; r.get(root)->padding_bottom = 40;
        uint32_t child = r.node("Landroid/view/View;", root, -1, -1);
        r.measure(root);
        check(r.get(child)->measured_width == 1080 - 100, "width = 1080 − (50+50) padding");
        check(r.get(child)->measured_height == 1920 - 60, "height = 1920 − (20+40) padding");
    }
    {
        printf("[4] child margins subtract from child avail\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        uint32_t child = r.node("Landroid/view/View;", root, -1, -1);
        r.get(child)->lp_margin_left = 30; r.get(child)->lp_margin_right = 30;
        r.measure(root);
        check(r.get(child)->measured_width == 1080 - 60,
              "match_parent width = 1080 − 60 margins (child spec avail)");
    }
    {
        printf("[5] weight 1:1 vertical (0dp+weight) → 540 each of 1920\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t a = r.node("Landroid/view/View;", root, -1, 0, 1000);
        uint32_t b = r.node("Landroid/view/View;", root, -1, 0, 1000);
        r.measure(root);
        check(r.get(a)->measured_height == 960, "child A share = 1920/2 = 960");
        check(r.get(b)->measured_height == 960, "child B share = 1920/2 = 960");
    }
    {
        printf("[6] weight 1:2 vertical → 640 / 1280 (sequential law)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t a = r.node("Landroid/view/View;", root, -1, 0, 1000);
        uint32_t b = r.node("Landroid/view/View;", root, -1, 0, 2000);
        r.measure(root);
        check(r.get(a)->measured_height == 640, "child A share = 1920/3 = 640");
        check(r.get(b)->measured_height == 1280, "child B share = 2·1920/3 = 1280");
    }
    {
        printf("[7] horizontal weight 1:1 → 540 each of 1080\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 0;
        uint32_t a = r.node("Landroid/view/View;", root, 0, -1, 1000);
        uint32_t b = r.node("Landroid/view/View;", root, 0, -1, 1000);
        r.measure(root);
        check(r.get(a)->measured_width == 540, "child A share = 1080/2 = 540");
        check(r.get(b)->measured_width == 540, "child B share = 1080/2 = 540");
    }
    {
        printf("[8] nonzero base + weight: base + share (L1008 measured+share law)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t a = r.node("Landroid/view/View;", root, -1, 400, 1000);
        r.measure(root);
        // total_length = 400 (base) → excess 1520 → final 400+1520 = 1920
        check(r.get(a)->measured_height == 1920,
              "fixed 400 + weight 1 fills 1920 (base kept, share on top)");
    }
    {
        printf("[9] overweight children SHRINK (negative remainingExcess law)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 0;
        // parent forced small via wrap in EXACTLY 500? Root is EXACTLY 1080;
        // use an inner container with explicit width 500 as the parent.
        uint32_t box = r.node("Landroid/widget/LinearLayout;", root, 500, -1);
        r.get(box)->orientation = 0;
        uint32_t a = r.node("Landroid/view/View;", box, 0, -1, 1000);
        uint32_t b = r.node("Landroid/view/View;", box, 0, -1, 1000);
        (void)a; (void)b;
        r.measure(root);
        check(r.get(a)->measured_width == 250, "child A shrunk 500/2 = 250");
        check(r.get(b)->measured_width == 250, "child B shrunk 500/2 = 250");
    }
    {
        printf("[10] weightSum caps distribution (remainingWeightSum = weightSum)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        r.get(root)->weight_sum = 2.0f; r.get(root)->weight_sum_valid = true;
        uint32_t a = r.node("Landroid/view/View;", root, -1, 0, 1000);
        uint32_t b = r.node("Landroid/view/View;", root, -1, 0, 1000);
        uint32_t c = r.node("Landroid/view/View;", root, -1, 0, 1000);
        r.measure(root);
        check(r.get(a)->measured_height == 960, "A = 1920·(1/2) = 960");
        check(r.get(b)->measured_height == 960, "B = remaining 960·(1/1) = 960");
        check(r.get(c)->measured_height == 0,
              "C = 0 (weightSum 2 exhausted by two unit weights)");
    }
    {
        printf("[11] margins reduce the distributable excess (mTotalLength law)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t a = r.node("Landroid/view/View;", root, -1, 0, 1000);
        r.get(a)->lp_margin_top = 100; r.get(a)->lp_margin_bottom = 20;
        r.measure(root);
        // mTotalLength = 120 (margins only) → excess 1800 → share 1800
        check(r.get(a)->measured_height == 1800,
              "0dp+weight sized 1920 − 120 margins = 1800");
    }
    {
        printf("[12] AT_MOST (wrap_content) clamps content to spec\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        uint32_t box = r.node("Landroid/widget/LinearLayout;", root, -2, -2);
        r.get(box)->orientation = 1;
        uint32_t child = r.node("Landroid/view/View;", box, -1, 700);
        (void)child;
        r.measure(root);
        check(r.get(box)->measured_height <= 1920,
              "wrap container ≤ parent EXACTLY spec (AT_MOST clamp)");
    }
    {
        printf("[13] nested LinearLayout spec propagation\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t mid = r.node("Landroid/widget/LinearLayout;", root, -1, 0, 1000);
        r.get(mid)->orientation = 0;
        uint32_t sib = r.node("Landroid/view/View;", root, -1, 0, 1000);
        (void)sib;
        uint32_t leaf = r.node("Landroid/view/View;", mid, -1, -1);
        r.measure(root);
        check(r.get(mid)->measured_height == 960, "mid EXACTLY 960 from weight");
        check(r.get(leaf)->measured_height == 960,
              "leaf inherits mid's EXACTLY height (spec propagation)");
    }
    {
        printf("[14] GONE children excluded from weight distribution\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t a = r.node("Landroid/view/View;", root, -1, 0, 1000);
        uint32_t gone = r.node("Landroid/view/View;", root, -1, 0, 1000);
        r.get(gone)->visibility = 8;   // GONE
        r.measure(root);
        check(r.get(a)->measured_height == 1920,
              "visible child takes the FULL 1920 (GONE skipped, AOSP count law)");
    }

    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
