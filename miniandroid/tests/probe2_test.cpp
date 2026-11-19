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
    resources::ArscParser arsc; apk::ApkParser apk;
    resources::LayoutInflater inflater{arsc, apk, "", resources::DeviceMetrics{1080,1920,2.625f,1.0f}};
    Rig(){ views.init(&heap_adapter); }
    uint32_t node(const char* cls, uint32_t par, int w, int h){
        uint32_t id = views.create_view(cls);
        auto* n = views.find_node(id);
        n->lp_width = w; n->lp_height = h;
        if (par) views.add_child(par, id);
        return id;
    }
    void measure(uint32_t r){ inflater.measure_layout(&views, r); }
    VN* get(uint32_t id){ return views.find_node(id); }
};
static void box(const char* t, VN* n){
    printf("  %-8s (%d,%d) %dx%d cell=(%d,%d)\n", t, n->measured_left, n->measured_top,
           n->measured_width, n->measured_height, n->grid_row, n->grid_col);
}
int main(){
    printf("[Q1] GL explicit (1,2) single 200x100:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", g, 200, 100);
        r.get(a)->grid_row = 1; r.get(a)->grid_col = 2;
        r.measure(g);
        box("a", r.get(a));
    }
    printf("[Q2] GL explicit (1,1) second row col1 (colCount2):\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t s = r.node("Landroid/view/View;", g, 200, 100);
        r.get(s)->grid_col_span = 2;
        uint32_t c = r.node("Landroid/view/View;", g, 100, 50);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 1;
        r.measure(g);
        box("s", r.get(s)); box("c", r.get(c));
    }
    printf("[Q3] GL span2 600 + 200:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t s = r.node("Landroid/view/View;", g, 600, 100);
        r.get(s)->grid_col_span = 2;
        r.node("Landroid/view/View;", g, 200, 100);
        r.measure(g);
        box("s", r.get(s));
        for (uint32_t cid : r.get(g)->children) box("kid", r.get(cid));
    }
    printf("[Q4] GL FILL/CENTER cell (0,1):\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t c = r.node("Landroid/view/View;", g, 100, 50);
        r.get(c)->grid_row = 0; r.get(c)->grid_col = 1;
        r.get(c)->child_gravity = 0x7 | 0x70;
        r.measure(g);
        box("fill", r.get(c));
    }
    printf("[Q5] FL rtl START 0x800003:\n");
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        r.get(fl)->layout_dir = 1;
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x00800003;
        r.measure(fl);
        box("c", r.get(c));
    }
    printf("[Q6] RL rtl toEndOf:\n");
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        r.get(rl)->layout_dir = 1;
        uint32_t va = r.node("Landroid/view/View;", rl, 300, 150);
        r.get(va)->android_id_name = "a";
        r.get(va)->rel_align_parent_right = true;
        uint32_t vb = r.node("Landroid/view/View;", rl, 200, 150);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_right_of_name = "a";
        r.get(vb)->rel_right_of_is_end = true;
        r.get(vb)->lp_margin_left = 20;
        r.measure(rl);
        box("a", r.get(va)); box("b", r.get(vb));
    }
    printf("[Q7] GridView rtl 2cols:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = 2;
        r.get(g)->grid_v_spacing = 10;
        r.node("Landroid/view/View;", g, 500, 200);
        r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        for (uint32_t cid : r.get(g)->children) box("kid", r.get(cid));
    }
    return 0;
}
