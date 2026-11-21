// s18_constraint_law_test — S18-cont family H (#632-B5 falsification): the
// B5 claim "ConstraintLayout is classified as FrameLayout — no constraint
// solving at all" cites view_renderer.cpp:70, which BATCH 3 proved is NOT
// COMPILED. The LIVE engine implements the F-148 (S72-W4) ConstraintLayout
// law (layout_inflater.cpp:3502-3531): per-axis topological anchor
// resolution, MATCH_CONSTRAINT spans, bias law, parent = padding box.
// Expectations fixed BEFORE the run from that documented production law:
//   * no-anchor child  -> (0,0) + margins
//   * one anchor       -> edge = anchor edge ± margin, other edge from size
//   * both anchors     -> leftover = span - size, offset = bias * leftover
//                         (default bias 0.5), fixed size kept
//   * MATCH_CONSTRAINT (lp == 0) + both anchors -> EXACTLY span
// Edge codes (android_shadows.h:2213-2218): 1 = LEFT/TOP, 2 = RIGHT/BOTTOM;
// cl_bias_x/cl_bias_y default 0.5.
// Laws:
//   H1  solving exists: child B anchored top->A.bottom lands at y=60 (A's
//       bottom edge), left->parent.LEFT at x=0 — NOT stacked at (0,0)
//   H2  bias law: child C 100px wide with BOTH parent anchors centers in
//       the 500px parent: left = 0 + 0.5*(500-100) = 200
//   H3  MATCH_CONSTRAINT: child D lp_height=0 with both parent anchors
//       measures EXACTLY the 800px span at y=0
#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine_impl.h"

#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
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
    uint32_t node(const char* cls, uint32_t parent, int lp_w, int lp_h) {
        uint32_t id = views.create_view(cls);
        auto* n = views.find_node(id);
        n->lp_width = lp_w; n->lp_height = lp_h;
        if (parent) views.add_child(parent, id);
        return id;
    }
    void measure(uint32_t root) { inflater.measure_layout(&views, root); }
    framework::ViewShadow::ViewNode* get(uint32_t id) {
        return views.find_node(id);
    }
};
using VN = framework::ViewShadow::ViewNode;

static const char* kCL = "Landroidx/constraintlayout/widget/ConstraintLayout;";

int main() {
    std::cout << "== s18 constraint anchor laws (B5 falsification) ==\n";

    {   // H1: real anchor solving — B binds to A's bottom edge
        Rig r;
        uint32_t root = r.node(kCL, 0, 500, 800);
        uint32_t a = r.node("Landroid/view/View;", root, 100, 60);
        r.get(a)->android_id_name = "a";
        uint32_t b = r.node("Landroid/view/View;", root, 80, 40);
        r.get(b)->cl_top_to = "a"; r.get(b)->cl_top_edge = 2;    // TOP -> A.BOTTOM
        r.get(b)->cl_left_to = "parent"; r.get(b)->cl_left_edge = 1;  // LEFT -> parent.LEFT
        r.measure(root);
        VN* kb = r.get(b);
        record(kb->measured_top == 60 && kb->measured_left == 0,
               "H1 anchor solving: B.top=" + std::to_string(kb->measured_top) +
               " B.left=" + std::to_string(kb->measured_left) +
               " (pinned: top=A.bottom=60; FrameLayout-stacking would give 0)");
    }
    {   // H2: both parent anchors + fixed size -> bias-centered
        Rig r;
        uint32_t root = r.node(kCL, 0, 500, 800);
        uint32_t c = r.node("Landroid/view/View;", root, 100, 50);
        r.get(c)->cl_left_to = "parent"; r.get(c)->cl_left_edge = 1;
        r.get(c)->cl_right_to = "parent"; r.get(c)->cl_right_edge = 2;
        r.measure(root);
        VN* kc = r.get(c);
        record(kc->measured_left == 200 && kc->measured_width == 100,
               "H2 bias 0.5: C.left=" + std::to_string(kc->measured_left) +
               " w=" + std::to_string(kc->measured_width) +
               " (pinned: 0 + 0.5*(500-100) = 200)");
    }
    {   // H3: MATCH_CONSTRAINT + both parent anchors -> EXACTLY span
        Rig r;
        uint32_t root = r.node(kCL, 0, 500, 800);
        uint32_t d = r.node("Landroid/view/View;", root, 200, 0);
        r.get(d)->cl_top_to = "parent"; r.get(d)->cl_top_edge = 1;
        r.get(d)->cl_bottom_to = "parent"; r.get(d)->cl_bottom_edge = 2;
        r.measure(root);
        VN* kd = r.get(d);
        record(kd->measured_height == 800 && kd->measured_top == 0 &&
                   kd->measured_width == 200,
               "H3 MATCH_CONSTRAINT: D.height=" +
                   std::to_string(kd->measured_height) + " top=" +
                   std::to_string(kd->measured_top) +
                   " (pinned: EXACTLY span 800)");
    }

    std::cout << "== s18 constraint anchor laws: " << g_pass << " pass / "
              << g_fail << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
