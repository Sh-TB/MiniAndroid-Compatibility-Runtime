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
    dalvik::DalvikHeap heap; framework::DalvikHeapAdapter ha{&heap};
    framework::ViewShadow views; resources::ArscParser arsc; apk::ApkParser apk;
    resources::LayoutInflater inflater{arsc, apk, "", resources::DeviceMetrics{1080,1920,2.625f,1.0f}};
    Rig(){ views.init(&ha); }
    uint32_t node(const char* cls, uint32_t par, int w, int h){
        uint32_t id = views.create_view(cls);
        auto* n = views.find_node(id); n->lp_width = w; n->lp_height = h;
        if (par) views.add_child(par, id); return id;
    }
    void measure(uint32_t r){ inflater.measure_layout(&views, r); }
    VN* get(uint32_t id){ return views.find_node(id); }
};
static void box(const char* t, VN* n){
    printf("  %-6s (%d,%d) %dx%d cell=(%d,%d)\n", t, n->measured_left, n->measured_top,
           n->measured_width, n->measured_height, n->grid_row, n->grid_col);
}
int main(){
    printf("[W1] G3.1 tree: (0,0)100w, (1,0)300w, auto 200w:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        r.node("Landroid/view/View;", g, 100, 100);
        uint32_t tall = r.node("Landroid/view/View;", g, 300, 100);
        r.get(tall)->grid_row = 1; r.get(tall)->grid_col = 0;
        r.node("Landroid/view/View;", g, 200, 100);
        r.measure(g);
        for (uint32_t cid : r.get(g)->children) box("kid", r.get(cid));
    }
    printf("[W2b] GridView rtl 2cols 500w sp10:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = 2;
        r.get(g)->grid_h_spacing = 0; r.get(g)->grid_v_spacing = 10;
        r.get(g)->layout_dir = 1;
        r.node("Landroid/view/View;", g, 500, 200);
        r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        for (uint32_t cid : r.get(g)->children) box("kid", r.get(cid));
        printf("  resolved=%d\n", r.get(g)->layout_dir_resolved);
    }
    printf("[W2] G4.3 tree: (0,0)200w sib + (0,1) 100x50 CENTER:\n");
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        r.node("Landroid/view/View;", g, 200, 100);
        uint32_t c = r.node("Landroid/view/View;", g, 100, 50);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 1;
        r.get(c)->child_gravity = 0x1 | 0x10;
        r.measure(g);
        box("c", r.get(c));
    }
    return 0;
}
