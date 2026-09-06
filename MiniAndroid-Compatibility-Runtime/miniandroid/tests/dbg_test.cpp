#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"
#include <cstdio>
using namespace miniandroid;
int main() {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter ha(&heap);
    framework::ViewShadow views; views.init(&ha);
    resources::ArscParser arsc; apk::ApkParser apk;
    resources::LayoutInflater inflater(arsc, apk, "", resources::DeviceMetrics{});
    uint32_t root = views.create_view("Landroid/widget/LinearLayout;");
    auto* rn = views.find_node(root);
    rn->lp_width = -1; rn->lp_height = -1;
    rn->padding_left = 50; rn->padding_right = 50; rn->padding_top = 20; rn->padding_bottom = 40;
    printf("default orientation = %d\n", rn->orientation);
    uint32_t child = views.create_view("Landroid/view/View;");
    auto* cn = views.find_node(child);
    cn->lp_width = -1; cn->lp_height = -1;
    views.add_child(root, child);
    inflater.measure_layout(&views, root);
    printf("child measured: %d,%d %dx%d\n", cn->measured_left, cn->measured_top, cn->measured_width, cn->measured_height);
    return 0;
}
