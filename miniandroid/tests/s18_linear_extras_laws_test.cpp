// s18_linear_extras_laws_test — S18 family E (#632-E6/E7): LinearLayout
// baseline/divider absence laws at the LIVE inflater (the D/E rows cite
// view_renderer.cpp lines, which BATCH 3 proved are NOT COMPILED).
// Expectations fixed BEFORE the run (methodology §E), derived from the
// documented production laws:
//   * horizontal cross-axis law (layout_inflater.cpp:4853-4883): the y
//     switch has TOP/CENTER/BOTTOM branches ONLY — no baseline branch exists
//     anywhere in the measure/layout path (grep: zero baselineAligned hits).
//     AOSP LinearLayout baselineAligned defaults TRUE and offsets shorter
//     children onto the shared baseline.
//   * decode census: showDividers/dividerPadding match NO case in the
//     attribute decoder — silently dropped (S17 A1 law: dropped AND
//     stats.warnings EMPTY). AOSP SHOW_DIVIDER_MIDDLE inserts divider
//     drawable sizes between children in measure AND layout.
// Laws:
//   E1  horizontal row, children 30px/60px tall: BOTH tops == 0 (pinned:
//       top-aligned; AOSP baseline law would offset the 30px child to y=30)
//   E2  showDividers="middle" on a horizontal row: child B left == 100 ==
//       the no-divider control run, and the inflate stats carry ZERO
//       warnings (silent vanish) — AOSP would push B to 100+dividerWidth
//   E3  showDividers="middle" on a vertical column: child B top == 100 ==
//       the no-divider control run — AOSP would push B to 100+dividerHeight
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
static resources::AxmlAttribute attr_str(const char* ns, const char* name,
                                         const char* raw) {
    resources::AxmlAttribute a;
    a.ns = ns; a.name = name; a.raw_value = raw;
    a.value.type = resources::DataType::STRING;
    a.value.string_value = raw;
    return a;
}
static resources::AxmlElement el(const char* cls) {
    resources::AxmlElement e; e.name = cls; return e;
}

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    resources::ArscParser arsc;
    apk::ApkParser apk;
    resources::DeviceMetrics metrics{1080, 1920, 2.625f, 1.0f};
    resources::LayoutInflater inflater{arsc, apk, "", metrics};
    Rig() { views.init(&heap_adapter); }
    uint32_t inflate(resources::AxmlElement& e, uint32_t parent = 0) {
        resources::InflateStats st;
        return inflater.inflate_element(&views, e, parent, st);
    }
    framework::ViewShadow::ViewNode* get(uint32_t id) {
        return views.find_node(id);
    }
    void measure(uint32_t root) { inflater.measure_layout(&views, root); }
};
using VN = framework::ViewShadow::ViewNode;

static uint32_t add_child(Rig& r, uint32_t parent, int w, int h) {
    auto ch = el("View");
    ch.attributes.push_back(attr_str("android", "layout_width", "0px"));
    ch.attributes.push_back(attr_str("android", "layout_height", "0px"));
    uint32_t id = r.inflate(ch, parent);
    r.get(id)->lp_width = w;
    r.get(id)->lp_height = h;
    return id;
}

int main() {
    std::cout << "== s18 linear extras laws (E6/E7) ==\n";

    {   // E1: no baseline branch — both tops at the content edge
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr_str("android", "layout_width", "1080px"));
        ll.attributes.push_back(attr_str("android", "layout_height", "100px"));
        ll.attributes.push_back(attr_str("android", "orientation", "horizontal"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;
        uint32_t a = add_child(r, vll, 100, 30);
        uint32_t b = add_child(r, vll, 100, 60);
        r.measure(vll);
        VN* ka = r.get(a); VN* kb = r.get(b);
        record(ka->measured_top == 0 && kb->measured_top == 0,
               "E1 baseline absence: top(30px)=" +
                   std::to_string(ka->measured_top) + " top(60px)=" +
                   std::to_string(kb->measured_top) +
                   " (pinned: top-aligned; AOSP baseline law expects 30)");
    }
    {   // E2: showDividers dropped silently — horizontal placement unchanged
        int left_ctrl = -1, left_div = -1; int warn_div = -1;
        {   // control run (no divider attr)
            Rig r;
            auto ll = el("LinearLayout");
            ll.attributes.push_back(attr_str("android", "layout_width", "1080px"));
            ll.attributes.push_back(attr_str("android", "layout_height", "100px"));
            ll.attributes.push_back(attr_str("android", "orientation", "horizontal"));
            uint32_t vll = r.inflate(ll);
            r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;
            add_child(r, vll, 100, 100);
            uint32_t b = add_child(r, vll, 200, 100);
            r.measure(vll);
            left_ctrl = r.get(b)->measured_left;
        }
        {   // divider run
            Rig r;
            auto ll = el("LinearLayout");
            ll.attributes.push_back(attr_str("android", "layout_width", "1080px"));
            ll.attributes.push_back(attr_str("android", "layout_height", "100px"));
            ll.attributes.push_back(attr_str("android", "orientation", "horizontal"));
            ll.attributes.push_back(attr_str("android", "showDividers", "middle"));
            resources::InflateStats st;
            uint32_t vll = r.inflater.inflate_element(
                &r.views, ll, 0, st);
            r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;
            add_child(r, vll, 100, 100);
            uint32_t b = add_child(r, vll, 200, 100);
            r.measure(vll);
            left_div = r.get(b)->measured_left;
            warn_div = (int)st.warnings.size();
        }
        record(left_ctrl == 100 && left_div == 100 && warn_div == 0,
               "E2 showDividers middle: control left=" +
                   std::to_string(left_ctrl) + " divider left=" +
                   std::to_string(left_div) + " warnings=" +
                   std::to_string(warn_div) +
                   " (pinned: inert + silent; AOSP expects +dividerWidth)");
    }
    {   // E3: showDividers dropped silently — vertical placement unchanged
        int top_ctrl = -1, top_div = -1;
        {   // control run
            Rig r;
            auto ll = el("LinearLayout");
            ll.attributes.push_back(attr_str("android", "layout_width", "100px"));
            ll.attributes.push_back(attr_str("android", "layout_height", "600px"));
            ll.attributes.push_back(attr_str("android", "orientation", "vertical"));
            uint32_t vll = r.inflate(ll);
            r.get(vll)->lp_width = 100; r.get(vll)->lp_height = 600;
            add_child(r, vll, 40, 100);
            uint32_t b = add_child(r, vll, 40, 200);
            r.measure(vll);
            top_ctrl = r.get(b)->measured_top;
        }
        {   // divider run
            Rig r;
            auto ll = el("LinearLayout");
            ll.attributes.push_back(attr_str("android", "layout_width", "100px"));
            ll.attributes.push_back(attr_str("android", "layout_height", "600px"));
            ll.attributes.push_back(attr_str("android", "orientation", "vertical"));
            ll.attributes.push_back(attr_str("android", "showDividers", "middle"));
            uint32_t vll = r.inflate(ll);
            r.get(vll)->lp_width = 100; r.get(vll)->lp_height = 600;
            add_child(r, vll, 40, 100);
            uint32_t b = add_child(r, vll, 40, 200);
            r.measure(vll);
            top_div = r.get(b)->measured_top;
        }
        record(top_ctrl == 100 && top_div == 100,
               "E3 showDividers middle: control top=" +
                   std::to_string(top_ctrl) + " divider top=" +
                   std::to_string(top_div) +
                   " (pinned: inert; AOSP expects +dividerHeight)");
    }

    std::cout << "== s18 linear extras laws: " << g_pass << " pass / "
              << g_fail << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
