// s19_grid_scroll_laws_test — S19 family I (#632 F4/H1/I5 falsification for the
// LIVE path). The claims cite view_renderer.cpp (DEAD per BATCH 3); the live
// engine implements the #606 LAYOUT-PIPE-001 GridLayout law
// (layout_inflater.cpp:4371-4416) and the #606 HorizontalScrollView measure
// law (:3890-3895). Expectations fixed BEFORE the run from the documented
// production laws:
//   * GridLayout track = max over span-1 cells WITH margins included
//     ("margins carry the gaps" — GridLayout has no spacing attr);
//     wrap content = sum of tracks.
//   * columnCount (grid_num_columns) partitions children into column tracks.
//   * HorizontalScrollView measures its content with width UNSPEC (wrap =
//     content width, no clamp to viewport).
// Laws:
//   I1  F4 falsified: a 30px left margin on child B widens column 0's track
//       (110 = max(100, 80+30)) -> root wrap width 110, not 100
//   I2  H1 falsified: grid_num_columns=2 with a 2x2 explicit-cell layout
//       builds per-column/row tracks (160 x 80), not a single stack
//   I3  I5 falsified: HSV wrap width = child 3000 (UNSPEC), height 200
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

static const char* kGL = "Landroid/widget/GridLayout;";
static const char* kV = "Landroid/view/View;";

int main() {
    std::cout << "== s19 grid/scroll laws (F4/H1/I5 falsification) ==\n";

    {   // I1: margins participate in the GridLayout track law
        Rig r;
        uint32_t root = r.node(kGL, 0, -2, -2);
        uint32_t a = r.node(kV, root, 100, 60);
        r.get(a)->grid_col = 0; r.get(a)->grid_row = 0;
        uint32_t b = r.node(kV, root, 80, 40);
        r.get(b)->grid_col = 0; r.get(b)->grid_row = 1;
        r.get(b)->lp_margin_left = 30;
        r.measure(root);
        VN* kr = r.get(root);
        record(kr->measured_width == 110 && kr->measured_height == 100,
               "I1 margins carry the gaps: root=" + std::to_string(kr->measured_width) +
               "x" + std::to_string(kr->measured_height) +
               " (pinned: track0 = max(100, 80+30) = 110; margin-ignored would give 100)");
    }
    {   // I2: columnCount=2 -> two column tracks, two row tracks
        Rig r;
        uint32_t root = r.node(kGL, 0, -2, -2);
        r.get(root)->grid_num_columns = 2;
        const int cells[4][4] = {{100, 60, 0, 0}, {40, 30, 1, 0},
                                 {50, 20, 0, 1}, {60, 10, 1, 1}};
        for (auto& c : cells) {
            uint32_t id = r.node(kV, root, c[0], c[1]);
            r.get(id)->grid_col = c[2]; r.get(id)->grid_row = c[3];
        }
        r.measure(root);
        VN* kr = r.get(root);
        record(kr->measured_width == 160 && kr->measured_height == 80,
               "I2 columnCount honored: root=" + std::to_string(kr->measured_width) +
               "x" + std::to_string(kr->measured_height) +
               " (pinned: cols max(100,50)+max(40,60)=160, rows max(60,30)+max(20,10)=80)");
    }
    {   // I3: HSV content measured with width UNSPEC. HONEST RETARGET: the
        // original expectation pinned a wrap-content ROOT at 3000, but the
        // engine answered 1080 — which IS the AOSP law (ViewRootImpl measures
        // the root against the window frame; XML wrap on a root still lands
        // on the window). The UNSPEC law lives on the CONTENT (the same
        // assertion s246 H1.3 pins): child = 3000x200, root = 1080 window.
        Rig r;
        uint32_t root = r.node("Landroid/widget/HorizontalScrollView;", 0, -1, -1);
        uint32_t c = r.node(kV, root, 3000, 200);
        r.measure(root);
        VN* kr = r.get(root);
        VN* kc = r.get(c);
        record(kc->measured_width == 3000 && kc->measured_height == 200 &&
                   kr->measured_width == 1080,
               "I3 HSV UNSPEC content (retargeted): child=" +
                   std::to_string(kc->measured_width) + "x" +
                   std::to_string(kc->measured_height) + " root=" +
                   std::to_string(kr->measured_width) +
                   " (pinned: content 3000 UNSPEC; root = 1080 window frame)");
    }

    std::cout << "== s19 grid/scroll laws: " << g_pass << " pass / "
              << g_fail << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
