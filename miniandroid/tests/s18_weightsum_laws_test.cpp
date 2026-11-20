// s18_weightsum_laws_test — S18 family B (#632-E2): the weightSum law at the
// live inflater. weightSum is DECODED (layout_inflater.cpp:1672, was the E2
// retracted claim "never read") and CONSUMED as the redistribution denominator
// (:4930-4935: remaining_weight_sum = weight_sum_valid && >0 ? weight_sum :
// weight_total). Expected shares computed BEFORE the test (methodology §B),
// sequential AOSP rounding: share_i = (int)(w_i * excess / rws); excess -=
// share; rws -= w_i.
// Laws:
//   B1  weightSum=3, two 0dp weight-1 children in 1080 -> 360/360 (200 unused)
//   B2  weightSum=0 (valid but non-positive) falls back to the derived sum
//       -> 540/540
//   B3  weightSum=2 with THREE weight-1 children -> 540/540/0 (sequential
//       exhaustion — AOSP sequential-decrement law, not simultaneous shares)
//   B4  no weightSum at all -> derived sum -> 540/540 (S17 W1.b contrast)
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
static resources::AxmlAttribute attr(const char* ns, const char* name,
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

// one horizontal LL with a declared weightSum and N weighted 0dp children
struct WCase {
    int shares[3];
    int n_children;
    const char* weight_sum;  // nullptr = no attr
};
static void run_case(const WCase& tc, const char* label) {
    Rig r;
    auto ll = el("LinearLayout");
    ll.attributes.push_back(attr("android", "layout_width", "1080px"));
    ll.attributes.push_back(attr("android", "layout_height", "100px"));
    ll.attributes.push_back(attr("android", "orientation", "horizontal"));
    if (tc.weight_sum)
        ll.attributes.push_back(attr("android", "weightSum", tc.weight_sum));
    uint32_t vll = r.inflate(ll);
    r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;
    if (tc.weight_sum && tc.weight_sum[0] != '\0') {
        float ws = (float)atof(tc.weight_sum);
        r.get(vll)->weight_sum = ws;
        r.get(vll)->weight_sum_valid = ws > 0.0f || ws == 0.0f;
    }
    uint32_t kids[3] = {0, 0, 0};
    for (int i = 0; i < tc.n_children; ++i) {
        auto ch = el("View");
        ch.attributes.push_back(attr("android", "layout_width", "0px"));
        ch.attributes.push_back(attr("android", "layout_height", "100px"));
        ch.attributes.push_back(attr("android", "layout_weight", "1"));
        uint32_t id = r.inflate(ch, vll);
        r.get(id)->lp_width = 0; r.get(id)->layout_weight = 1000;
        kids[i] = id;
    }
    r.measure(vll);
    bool ok = true;
    std::string detail;
    for (int i = 0; i < tc.n_children; ++i) {
        int got = r.get(kids[i])->measured_width;
        detail += " c" + std::to_string(i) + "=" + std::to_string(got);
        if (got != tc.shares[i]) ok = false;
    }
    record(ok, std::string(label) + detail);
}

int main() {
    std::cout << "== s18 weightSum laws (E2) ==\n";
    run_case({{360, 360, 0}, 2, "3"},
             "B1 weightSum=3, w=[1,1] -> 360/360 (declared sum governs)");
    run_case({{540, 540, 0}, 2, "0"},
             "B2 weightSum=0 non-positive -> derived sum 540/540");
    run_case({{540, 540, 0}, 3, "2"},
             "B3 weightSum=2, w=[1,1,1] -> 540/540/0 sequential exhaustion");
    run_case({{540, 540, 0}, 2, nullptr},
             "B4 no weightSum -> derived sum 540/540 (W1.b contrast)");
    std::cout << "== s18 weightSum laws: " << g_pass << " pass / " << g_fail
              << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
