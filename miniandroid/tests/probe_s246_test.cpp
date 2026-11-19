// probe_s246 — prints ACTUAL engine geometry for the failing clusters:
// H1 (scroll content past viewport, row stacking, GONE), H4.4/H4.7
// (relative leftOf / centerInParent), H5.3 (GridLayout fallback).
#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine_impl.h"

#include <cstdio>

using namespace miniandroid;
using VN = framework::ViewShadow::ViewNode;
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
    VN* get(uint32_t id) { return views.find_node(id); }
};
static void box(const char* tag, VN* n) {
    printf("  %-10s box=(%d,%d) %dx%d\n", tag, n->measured_left,
           n->measured_top, n->measured_width, n->measured_height);
}
int main() {
    printf("[P1] scroll content 3x800:\n");
    {   Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;
        for (int i = 0; i < 3; ++i) r.node("Landroid/view/View;", ll, -1, 800);
        r.measure(sv);
        box("scrollview", r.get(sv)); box("content", r.get(ll));
    }
    printf("[P2] scroll rows 4x120 + GONE middle:\n");
    {   Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;
        uint32_t a = r.node("Landroid/view/View;", ll, -1, 120);
        uint32_t g = r.node("Landroid/view/View;", ll, -1, 120);
        r.get(g)->visibility = 2;
        uint32_t c = r.node("Landroid/view/View;", ll, -1, 120);
        r.measure(sv);
        box("row0", r.get(a)); box("gone", r.get(g)); box("row2", r.get(c));
    }
    printf("[P3] scroll list 10x120, child[5]:\n");
    {   Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;
        for (int i = 0; i < 10; ++i) r.node("Landroid/view/View;", ll, -1, 120);
        r.measure(sv);
        box("content", r.get(ll));
        uint32_t k5 = r.get(ll)->children[5];
        box("row5", r.get(k5));
    }
    printf("[P4] relative leftOf:\n");
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t va = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_left_of_name = "a";
        r.get(vb)->lp_margin_right = 20;
        r.measure(rl);
        box("a", r.get(va)); box("b", r.get(vb));
    }
    printf("[P5] relative centerInParent:\n");
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t v = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(v)->rel_center_in_parent = true;
        r.measure(rl);
        box("c", r.get(v));
    }
    printf("[P6] gridlayout fallback:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", g, 300, 200);
        uint32_t b = r.node("Landroid/view/View;", g, 300, 200);
        r.measure(g);
        box("grid", r.get(g)); box("a", r.get(a)); box("b", r.get(b));
    }
    printf("[P7] HSV wrap width:\n");
    {   Rig r;
        uint32_t hsv = r.node("Landroid/widget/HorizontalScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", hsv, -2, -1);
        r.node("Landroid/view/View;", ll, 3000, 200);
        r.measure(hsv);
        box("hsv", r.get(hsv)); box("content", r.get(ll));
    }
    printf("[P8] FL center+leftMargin40\n");
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x11;
        r.get(c)->lp_margin_left = 40;
        r.measure(fl);
        box("c", r.get(c));
    }
    printf("[P9] AUTO_FIT cols=2 (500w,sp10) 4 kids 500x200\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = -1;
        r.get(g)->grid_column_width = 500;
        r.get(g)->grid_h_spacing = 10; r.get(g)->grid_v_spacing = 10;
        for (int i = 0; i < 4; ++i) r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        for (uint32_t cid : r.get(g)->children)
            box("kid", r.get(cid));
    }
    return 0;
}
