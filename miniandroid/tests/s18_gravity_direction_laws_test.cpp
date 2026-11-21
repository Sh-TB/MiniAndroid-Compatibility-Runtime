// s18_gravity_direction_laws_test — S18 family D (#632-D4/D5/D6): the gravity
// direction/fill laws at the LIVE inflater path (the D/E rows cite
// view_renderer.cpp lines, which BATCH 3 proved are NOT COMPILED — the laws
// target layout_inflater.cpp instead).
// Expectations fixed BEFORE the run (methodology §D), derived from the
// documented production laws:
//   * gravity_bits decode (layout_inflater.cpp:96-133): fill_vertical -> 0x70,
//     fill_horizontal -> 0x7, start/end -> LEFT/RIGHT low bits with the
//     RELATIVE flag 0x00800000 ABSENT (documented limitation, :105-107).
//   * horizontal cross-axis law (:4853-4883): vf = vg & 0x70; 0x50 -> bottom,
//     0x10 -> center, EVERYTHING ELSE (incl. 0x70 FILL) -> top; height stays
//     the child's own (no stretch branch exists).
//   * vertical cross-axis law (:5006-5034): hf = vg & 0x7; 0x1 -> center,
//     0x5 -> right, else -> left; width never stretched; the RTL START/END
//     flip (:5022-5028) fires ONLY when the relative bit 0x00800000 is set
//     AND layout_dir_resolved == 1.
// Divergences from AOSP are pinned as defect laws and documented per case.
// Laws:
//   D1  layout_gravity="fill_vertical" in a horizontal row: child keeps its
//       40px height, top-aligned (AOSP: stretched to the 100px container)
//   D2  layout_gravity="fill_horizontal" in a vertical column: child keeps
//       40px width, left-aligned (AOSP: stretched to the 100px container)
//   D3  layout_gravity="start" (STRING path) under layoutDirection=rtl: NO
//       flip — x stays 0 (the decoder drops the 0x00800000 flag, so the
//       :5022 flip law can never fire for XML-declared start/end; AOSP: x=60)
//   D4  layout_gravity INT 0x00800003 (AOSP Gravity.START) under RTL: the
//       flip DOES fire — x=60 (isolates the defect to the string decoder)
//   D5  layout_gravity INT 0x11000000 (DISPLAY_CLIP_V|H): placement identical
//       to a no-gravity control child — the DISPLAY bits are inert
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
static resources::AxmlAttribute attr_int(const char* ns, const char* name,
                                         uint32_t v) {
    resources::AxmlAttribute a;
    a.ns = ns; a.name = name;
    a.value.type = resources::DataType::INT_DEC;
    a.value.data = v;
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

// one child View with given px size and an optional layout_gravity attr
static uint32_t add_child(Rig& r, uint32_t parent, int w, int h,
                          bool use_str, const char* sval, uint32_t ival,
                          bool has_gravity) {
    auto ch = el("View");
    ch.attributes.push_back(attr_str("android", "layout_width", "0px"));
    ch.attributes.push_back(attr_str("android", "layout_height", "0px"));
    if (has_gravity) {
        if (use_str)
            ch.attributes.push_back(attr_str("android", "layout_gravity", sval));
        else
            ch.attributes.push_back(attr_int("android", "layout_gravity", ival));
    }
    uint32_t id = r.inflate(ch, parent);
    r.get(id)->lp_width = w;
    r.get(id)->lp_height = h;
    return id;
}

int main() {
    std::cout << "== s18 gravity direction laws (D4/D5/D6) ==\n";

    {   // D1: fill_vertical in a horizontal row — no stretch branch
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr_str("android", "layout_width", "1080px"));
        ll.attributes.push_back(attr_str("android", "layout_height", "100px"));
        ll.attributes.push_back(attr_str("android", "orientation", "horizontal"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;
        uint32_t kid = add_child(r, vll, 200, 40, true, "fill_vertical", 0, true);
        r.measure(vll);
        VN* k = r.get(kid);
        record(k->measured_height == 40 && k->measured_top == 0 &&
                   k->measured_width == 200,
               "D1 fill_vertical: h=40 top=0 (pinned: no stretch; AOSP "
               "expects 100px) got h=" + std::to_string(k->measured_height) +
               " top=" + std::to_string(k->measured_top));
    }
    {   // D2: fill_horizontal in a vertical column — no stretch branch
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr_str("android", "layout_width", "100px"));
        ll.attributes.push_back(attr_str("android", "layout_height", "600px"));
        ll.attributes.push_back(attr_str("android", "orientation", "vertical"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 100; r.get(vll)->lp_height = 600;
        uint32_t kid = add_child(r, vll, 40, 100, true, "fill_horizontal", 0, true);
        r.measure(vll);
        VN* k = r.get(kid);
        record(k->measured_width == 40 && k->measured_left == 0,
               "D2 fill_horizontal: w=40 left=0 (pinned: no stretch; AOSP "
               "expects 100px) got w=" + std::to_string(k->measured_width) +
               " left=" + std::to_string(k->measured_left));
    }
    {   // D3: STRING "start" under RTL — decoder drops the relative flag
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr_str("android", "layout_width", "100px"));
        ll.attributes.push_back(attr_str("android", "layout_height", "600px"));
        ll.attributes.push_back(attr_str("android", "orientation", "vertical"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 100; r.get(vll)->lp_height = 600;
        r.get(vll)->layout_dir = 1;  // RTL (rdir walk resolves children)
        uint32_t kid = add_child(r, vll, 40, 100, true, "start", 0, true);
        r.measure(vll);
        VN* k = r.get(kid);
        record(k->measured_left == 0,
               "D3 string start under RTL: left=0 (pinned: no flip — "
               "0x00800000 absent; AOSP expects 60) got left=" +
                   std::to_string(k->measured_left));
    }
    {   // D4: INT AOSP Gravity.START under RTL — the flip law fires
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr_str("android", "layout_width", "100px"));
        ll.attributes.push_back(attr_str("android", "layout_height", "600px"));
        ll.attributes.push_back(attr_str("android", "orientation", "vertical"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 100; r.get(vll)->lp_height = 600;
        r.get(vll)->layout_dir = 1;
        uint32_t kid = add_child(r, vll, 40, 100, false, nullptr, 0x00800003u, true);
        r.measure(vll);
        VN* k = r.get(kid);
        record(k->measured_left == 60,
               "D4 INT 0x00800003 under RTL: left=60 (flip law fires when the "
               "relative flag is present) got left=" +
                   std::to_string(k->measured_left));
    }
    {   // D5: DISPLAY_CLIP bits are inert — identical to a no-gravity control
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr_str("android", "layout_width", "100px"));
        ll.attributes.push_back(attr_str("android", "layout_height", "600px"));
        ll.attributes.push_back(attr_str("android", "orientation", "vertical"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 100; r.get(vll)->lp_height = 600;
        uint32_t a = add_child(r, vll, 40, 100, false, nullptr, 0x11000000u, true);
        uint32_t b = add_child(r, vll, 40, 100, false, nullptr, 0, false);
        r.measure(vll);
        VN* ka = r.get(a); VN* kb = r.get(b);
        record(ka->measured_left == 0 && kb->measured_left == 0 &&
                   ka->measured_width == 40 && kb->measured_width == 40,
               "D5 DISPLAY_CLIP 0x11000000 inert: clip-child left=" +
                   std::to_string(ka->measured_left) + " control left=" +
                   std::to_string(kb->measured_left));
    }

    std::cout << "== s18 gravity direction laws: " << g_pass << " pass / "
              << g_fail << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
