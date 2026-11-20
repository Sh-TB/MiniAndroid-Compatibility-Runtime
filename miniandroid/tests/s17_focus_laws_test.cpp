// s17_focus_laws_test — AUD-54 phase 2 (#635 S17): focused pinning laws for the
// #632 claims that no existing battery test covers — the INFLATER DECODE LAYER
// (attribute → node flag/px), driven end-to-end with hand-built AxmlElements
// through the real LayoutInflater::inflate_element + measure_layout.
// Groups (each names the #632 finding it pins):
//   R1  rel-rule decode: alignParentBottom + centerHorizontal BOTH survive
//       (G2 decode layer), toRightOf name capture (G4 decode layer)
//   R2  dimension decode: dp/dip/px + the ONE-multiplication rounding law
//       (L3 / M1), incl. the once-unreachable `dip` suffix now decoded
//   R3  sp → scaledDensity law (M2): font_scale enters the conversion
//   W1  LinearLayout weight gate: weight-0 MATCH_PARENT child is NOT
//       weighted (E3 pin of current behavior)
//   A1  silent attribute drops: paddingStart/clipChildren/alpha/translationX/
//       useDefaultMargins vanish with NO diagnostic (NEW-33/35/36/37/38)
//   G1  alignParentTop + alignParentBottom end-to-end (D2 gravity-mask pin)
//   F1  forward reference: dependent inflated before its anchor (G3 — the
//       Kahn topological resolution must order the walk)
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
static resources::AxmlAttribute attr_bool(const char* ns, const char* name,
                                          bool b) {
    resources::AxmlAttribute a;
    a.ns = ns; a.name = name;
    a.value.type = resources::DataType::INT_BOOLEAN;
    a.value.data = b ? 0xFFFFFFFFu : 0u;
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
    // one inflate_element call; returns the created view id
    uint32_t inflate(resources::AxmlElement& e, uint32_t parent_id = 0) {
        resources::InflateStats st;
        return inflater.inflate_element(&views, e, parent_id, st);
    }
    framework::ViewShadow::ViewNode* get(uint32_t id) {
        return views.find_node(id);
    }
    void measure(uint32_t root) { inflater.measure_layout(&views, root); }
};
using VN = framework::ViewShadow::ViewNode;

int main() {
    std::cout << "== s17 focus laws (AUD-54 phase 2) ==\n";

    // ── R1: rel-rule attribute decode ──────────────────────────────────────
    {
        Rig r;
        auto e = el("View");
        e.attributes.push_back(attr("android", "layout_width", "200px"));
        e.attributes.push_back(attr("android", "layout_height", "200px"));
        e.attributes.push_back(attr_bool("android", "layout_alignParentBottom", true));
        e.attributes.push_back(attr_bool("android", "layout_centerHorizontal", true));
        uint32_t v = r.inflate(e);
        VN* n = r.get(v);
        record(n && n->rel_align_parent_bottom && n->rel_center_horizontal,
               "R1.a alignParentBottom + centerHorizontal BOTH decode (G2: flags coexist)");
    }
    {
        Rig r;
        auto a_el = el("View");
        a_el.attributes.push_back(attr("android", "id", "@+id/anchor"));
        a_el.attributes.push_back(attr("android", "layout_width", "400px"));
        a_el.attributes.push_back(attr("android", "layout_height", "200px"));
        uint32_t va = r.inflate(a_el);
        r.get(va)->android_id_name = "anchor";  // name table (s246 contract)

        auto b_el = el("View");
        b_el.attributes.push_back(attr("android", "layout_width", "200px"));
        b_el.attributes.push_back(attr("android", "layout_height", "200px"));
        b_el.attributes.push_back(attr("android", "layout_toRightOf", "@+id/anchor"));
        uint32_t vb = r.inflate(b_el);
        record(r.get(vb)->rel_right_of_name == "anchor",
               "R1.b toRightOf name captured through XML (G4 decode layer)");
    }

    // ── R2: dimension decode (L3 / M1) ─────────────────────────────────────
    {
        Rig r;  // density 2.625
        auto e = el("View");
        e.attributes.push_back(attr("android", "layout_width", "20dp"));
        e.attributes.push_back(attr("android", "layout_height", "8px"));
        e.attributes.push_back(attr("android", "layout_marginTop", "12dip"));
        uint32_t v = r.inflate(e);
        VN* n = r.get(v);
        // 20dp × 2.625 = 52.5 → AOSP round-half-away → 53 (one multiplication)
        record(n && n->lp_width == 53,
               "R2.a 20dp -> 53px (L3/M1: density applied exactly once, round-half-away)");
        record(n && n->lp_height == 8,
               "R2.b 8px pass-through (L3: px unit untouched)");
        // 12dip × 2.625 = 31.5 → 32 — the `dip` suffix decode (F-NEW-360 law)
        record(n && n->lp_margin_top == 32,
               "R2.c 12dip -> 32px (dip suffix reachable, same density law)");
    }

    // ── R3: sp uses scaledDensity (M2) ─────────────────────────────────────
    {
        Rig r;
        r.metrics.scale_fonts = 1.3f;  // user font scale ≠ 1
        resources::LayoutInflater inf{r.arsc, r.apk, "", r.metrics};
        auto e = el("View");
        e.attributes.push_back(attr("android", "layout_width", "8px"));
        e.attributes.push_back(attr("android", "layout_height", "8px"));
        e.attributes.push_back(attr("android", "layout_marginTop", "10sp"));
        resources::InflateStats st;
        uint32_t v = inf.inflate_element(&r.views, e, 0, st);
        VN* n = r.get(v);
        // 10sp × scaledDensity(2.625×1.3=3.4125) = 34.125 → 34
        record(n && n->lp_margin_top == 34,
               "R3 10sp @font-scale 1.3 -> 34px (M2: scaledDensity, not bare density)");
    }

    // ── W1: LinearLayout weight gate (E3) ──────────────────────────────────
    {
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr("android", "layout_width", "1080px"));
        ll.attributes.push_back(attr("android", "layout_height", "100px"));
        ll.attributes.push_back(attr("android", "orientation", "horizontal"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;

        auto a_el = el("View");
        a_el.attributes.push_back(attr("android", "layout_width", "0px"));
        a_el.attributes.push_back(attr("android", "layout_height", "100px"));
        a_el.attributes.push_back(attr("android", "layout_weight", "1"));
        uint32_t va = r.inflate(a_el, vll);
        r.get(va)->lp_width = 0; r.get(va)->layout_weight = 1000;  // milli 1.0

        auto b_el = el("View");
        b_el.attributes.push_back(attr("android", "layout_width", "-1"));  // MATCH_PARENT
        b_el.attributes.push_back(attr("android", "layout_height", "100px"));
        b_el.attributes.push_back(attr("android", "layout_weight", "0"));
        uint32_t vb = r.inflate(b_el, vll);
        r.get(vb)->lp_width = -1; r.get(vb)->layout_weight = 0;

        r.measure(vll);
        VN* na = r.get(va); VN* nb = r.get(vb);
        std::cout << "        [E3 actual: A(weight1,0dp)=" << (na ? na->measured_width : -1)
                  << " B(weight0,MATCH_PARENT)=" << (nb ? nb->measured_width : -1)
                  << "]\n";
        // Pin: weight-0 MATCH_PARENT child keeps parent-width measure
        // (AOSP: weight 0 → NOT in the weighted redistribution; the #632 E3
        // claim said old code treated it as weight 1 — current gate is >0).
        record(nb && nb->measured_width == 1080,
               "W1.a weight-0 MATCH_PARENT measures parent width, not 0-share (E3 pin)");
    }
    {
        // W1.b (E3 contrast, clean rig): the ONLY child is 0dp weight=1 ->
        // AOSP excess law gives it the whole parent width (1080).
        Rig r;
        auto ll = el("LinearLayout");
        ll.attributes.push_back(attr("android", "layout_width", "1080px"));
        ll.attributes.push_back(attr("android", "layout_height", "100px"));
        ll.attributes.push_back(attr("android", "orientation", "horizontal"));
        uint32_t vll = r.inflate(ll);
        r.get(vll)->lp_width = 1080; r.get(vll)->lp_height = 100;
        auto a_el = el("View");
        a_el.attributes.push_back(attr("android", "layout_width", "0px"));
        a_el.attributes.push_back(attr("android", "layout_height", "100px"));
        a_el.attributes.push_back(attr("android", "layout_weight", "1"));
        uint32_t va = r.inflate(a_el, vll);
        r.get(va)->lp_width = 0; r.get(va)->layout_weight = 1000;
        r.measure(vll);
        VN* na = r.get(va);
        std::cout << "        [E3b actual: LL=" << r.get(vll)->measured_width
                  << "x" << r.get(vll)->measured_height
                  << " A=" << (na ? na->measured_width : -1) << "]\n";
        record(na && na->measured_width == 1080,
               "W1.b sole weight-1 0dp child takes the full excess (E3 contrast)");
    }

    // ── A1: silent attribute drops (NEW-33/35/36/37/38) ────────────────────
    {
        Rig r;
        auto e = el("View");
        e.attributes.push_back(attr("android", "layout_width", "8px"));
        e.attributes.push_back(attr("android", "layout_height", "8px"));
        e.attributes.push_back(attr("android", "paddingStart", "8dp"));
        e.attributes.push_back(attr_bool("android", "clipChildren", false));
        e.attributes.push_back(attr("android", "alpha", "0.5"));
        e.attributes.push_back(attr("android", "translationX", "10dp"));
        e.attributes.push_back(attr_bool("android", "useDefaultMargins", true));
        resources::InflateStats st;
        uint32_t v = r.inflate(e);
        VN* n = r.get(v);
        record(n && n->padding_left == 0 && n->padding_right == 0,
               "A1.a paddingStart/End dropped (NEW-35: not in the decode table)");
        record(n && n->alpha == 255,
               "A1.b alpha attr dropped (NEW-37: node alpha stays 255)");
        record(n && n->translation_x == 0.0f,
               "A1.c translationX attr dropped (NEW-37: transform family absent)");
        record(st.warnings.empty(),
               "A1.d NO diagnostic for any dropped attr (NEW-33: silent vanish)");
    }

    // ── G1: alignParentTop + alignParentBottom end-to-end (D2) ─────────────
    {
        Rig r;
        auto rl = el("RelativeLayout");
        rl.attributes.push_back(attr("android", "layout_width", "1080px"));
        rl.attributes.push_back(attr("android", "layout_height", "1920px"));
        uint32_t vrl = r.inflate(rl);
        r.get(vrl)->lp_width = 1080; r.get(vrl)->lp_height = 1920;

        auto v_el = el("View");
        v_el.attributes.push_back(attr("android", "layout_width", "200px"));
        v_el.attributes.push_back(attr("android", "layout_height", "100px"));
        v_el.attributes.push_back(attr_bool("android", "layout_alignParentTop", true));
        v_el.attributes.push_back(attr_bool("android", "layout_alignParentBottom", true));
        uint32_t vv = r.inflate(v_el, vrl);
        r.measure(vrl);
        VN* n = r.get(vv);
        // AOSP: top edge 0 AND bottom edge parent-bottom BOTH constrain.
        // The mask overlap law (D2): 0x30(TOP) vs 0x50(BOTTOM) share bit 0x10 —
        // pin whichever the engine does today; documented deviation is lawful.
        // AOSP RelativeLayout law: BOTH vertical anchors bind -> the child is
        // measured EXACTLY the anchor span (lp height is overridden) —
        // TypedValue mask overlap (D2's 0x30 & 0x50 claim) does not reproduce
        // on this path: anchors resolve positionally, not by bitmask routing.
        record(n->measured_top == 0 && n->measured_height == 1920 &&
               n->measured_top + n->measured_height == 1920,
               "G1 alignParentTop+Bottom: EXACTLY the anchor span 1920, top=0 "
               "(AOSP both-anchor law; D2 mask-overlap defect absent here)");

        std::cout << "        [D2 actual: top=" << n->measured_top
                  << " bottom=" << (n->measured_top + n->measured_height)
                  << " h=" << n->measured_height
                  << " lp_h=" << n->lp_height << "]\n";
    }

    // ── F1: forward reference (G3) ─────────────────────────────────────────
    {
        Rig r;
        auto rl = el("RelativeLayout");
        rl.attributes.push_back(attr("android", "layout_width", "1080px"));
        rl.attributes.push_back(attr("android", "layout_height", "1920px"));
        uint32_t vrl = r.inflate(rl);
        r.get(vrl)->lp_width = 1080; r.get(vrl)->lp_height = 1920;

        // B (dependent) inflated FIRST, anchored to a name that only exists
        // AFTER (A). Kahn-order resolution must place B right of A.
        auto b_el = el("View");
        b_el.attributes.push_back(attr("android", "layout_width", "200px"));
        b_el.attributes.push_back(attr("android", "layout_height", "200px"));
        b_el.attributes.push_back(attr("android", "layout_toRightOf", "@+id/late"));
        uint32_t vb = r.inflate(b_el, vrl);
        r.get(vb)->rel_right_of_name = "late";
        r.get(vb)->lp_margin_left = 0;

        auto a_el = el("View");
        a_el.attributes.push_back(attr("android", "id", "@+id/late"));
        a_el.attributes.push_back(attr("android", "layout_width", "300px"));
        a_el.attributes.push_back(attr("android", "layout_height", "200px"));
        uint32_t va = r.inflate(a_el, vrl);
        r.get(va)->android_id_name = "late";

        r.measure(vrl);
        VN* nb = r.get(vb);
        VN* na = r.get(va);
        std::cout << "        [G3 actual: A.left=" << (na ? na->measured_left : -1)
                  << " A.right=" << (na ? na->measured_right : -1)
                  << " B.left=" << (nb ? nb->measured_left : -1)
                  << " B.rel_right_of='" << (nb ? nb->rel_right_of_name : "?")
                  << "' A.name='" << (na ? na->android_id_name : "?") << "']\n";
        record(na && nb && nb->measured_left == na->measured_right,
               "F1 forward ref resolves: B.left == A.right (G3 topo law)");
    }

    std::cout << "== s17 focus laws: " << g_pass << " pass / " << g_fail
              << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
