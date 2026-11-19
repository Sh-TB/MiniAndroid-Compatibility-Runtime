// s246_layout_closure_law_test — the LAYOUT DOMAIN CLOSURE matrix (#606).
// The font-domain methodology (#605) applied to view placement: the gap
// surfaces (ScrollView content, ImageView scaleType geometry, TextView box
// law, RelativeLayout rules, GridView columns, composite screens) each
// get their AOSP law asserted. Groups:
//   H1  ScrollView/HorizontalScrollView CONTENT measure laws
//   H2  ImageView scaleType geometry (the scale_image_rect law)
//   H3  TextView -> box laws (shaped text drives wrap_content)
//   H4  RelativeLayout rule graph (below/rightOf/align*/center*)
//   H5  GridView/GridLayout column + flow laws
//   H6  composite screens (login form / scroll list / profile / viewer)
//   H7  FrameLayout stacking + gravity-with-margins
//   H8  spec-negotiation edges (root sentinels, UNSPEC chains, depth)
#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine_impl.h"
#include "../src/renderer/software_renderer.h"

#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
}
static bool near_(int a, int b, int tol) { return a - tol <= b && b <= a + tol; }

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
    framework::ViewShadow::ViewNode* get(uint32_t id) {
        return views.find_node(id);
    }
};
using VN = framework::ViewShadow::ViewNode;

int main() {
    std::cout << "== s246 layout closure matrix ==\n";

    // ---- H1: ScrollView CONTENT laws ----------------------------------------
    {   // H1.1 small content: child keeps CONTENT height, viewport stays 1920
        Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;  // vertical content (AOSP default is H)
        r.node("Landroid/view/View;", ll, -1, 100);
        r.measure(sv);
        record(r.get(ll)->measured_height == 100 &&
               r.get(sv)->measured_height == 1920,
               "H1.1 scroll child = content 100, viewport 1920");
    }
    {   // H1.2 content taller than viewport grows PAST it (UNSPEC law)
        Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;  // vertical content (AOSP default is H)
        for (int i = 0; i < 3; ++i) r.node("Landroid/view/View;", ll, -1, 800);
        r.measure(sv);
        record(r.get(ll)->measured_height == 2400,
               "H1.2 content 2400 > viewport, child grows past (UNSPEC)");
    }
    {   // H1.3 HorizontalScrollView: UNSPEC width, cross axis EXACTLY
        Rig r;
        uint32_t hsv = r.node("Landroid/widget/HorizontalScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", hsv, -2, -1);
        r.node("Landroid/view/View;", ll, 3000, 200);
        r.measure(hsv);
        record(r.get(ll)->measured_width == 3000 &&
               r.get(ll)->measured_height == 1920,
               "H1.3 HSV child width 3000 (UNSPEC), height EXACTLY viewport");
    }
    {   // H1.4 ScrollView wrap_content height = content when smaller
        Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -2);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;  // vertical content (AOSP default is H)
        r.node("Landroid/view/View;", ll, -1, 400);
        r.measure(sv);
        record(r.get(sv)->measured_height == 400,
               "H1.4 wrap ScrollView = content 400 (AT_MOST law)");
    }
    {   // H1.5 scroll rows stack in document order at x=0
        Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;  // vertical content (AOSP default is H)
        for (int i = 0; i < 4; ++i) r.node("Landroid/view/View;", ll, -1, 120);
        r.measure(sv);
        bool ok = true;
        for (uint32_t cid : r.get(ll)->children)
            if (r.get(cid)->measured_left != 0) ok = false;
        record(ok && r.get(ll)->children[2] &&
               r.get(r.get(ll)->children[2])->measured_top == 240,
               "H1.5 rows at y=0/120/240, x=0 (document order)");
    }
    {   // H1.6 GONE row skipped by scroll content stack
        Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;  // vertical content (AOSP default is H)
        r.node("Landroid/view/View;", ll, -1, 120);
        uint32_t gone = r.node("Landroid/view/View;", ll, -1, 120);
        r.get(gone)->visibility = 8;  // GONE (android.view.View.GONE)
        uint32_t c = r.node("Landroid/view/View;", ll, -1, 120);
        r.measure(sv);
        record(r.get(c)->measured_top == 120,
               "H1.6 GONE row skipped, third row at y=120");
    }

    // ---- H2: ImageView scaleType geometry (the pure law) --------------------
    {   using namespace renderer;
        // (A real nonzero src: the guard rejects 0-size drawables honestly.)
        auto f = scale_image_rect(1, 200, 150, 100, 100, 400, 300); // fitXY
        record(f.x == 100 && f.y == 100 && f.w == 400 && f.h == 300,
               "H2.1 fitXY fills the box exactly");
        f = scale_image_rect(5, 200, 100, 100, 100, 400, 300);      // center
        record(f.w == 200 && f.h == 100 && f.x == 200 && f.y == 200,
               "H2.2 center: unscaled, centered, cropped");
        f = scale_image_rect(6, 100, 200, 0, 0, 400, 400);          // centerCrop
        record(f.w == 400 && f.h == 800 && f.y == -200,
               "H2.3 centerCrop covers box, aspect kept, centered overflow");
        f = scale_image_rect(3, 100, 200, 0, 0, 400, 400);          // fitCenter
        record(f.w == 200 && f.h == 400 && f.x == 100 && f.y == 0,
               "H2.4 fitCenter: largest fit, centered");
        f = scale_image_rect(2, 100, 200, 0, 0, 400, 400);          // fitStart
        record(f.w == 200 && f.h == 400 && f.x == 0 && f.y == 0,
               "H2.5 fitStart anchored top-left");
        f = scale_image_rect(4, 100, 200, 0, 0, 400, 400);          // fitEnd
        record(f.w == 200 && f.h == 400 && f.x == 200 && f.y == 0,
               "H2.6 fitEnd anchored right (vertical fits exactly)");
        f = scale_image_rect(3, 400, 100, 0, 0, 200, 200);          // wide src
        record(f.w == 200 && f.h == 50 && f.y == 75,
               "H2.7 fitCenter wide 400x100 -> 200x50 centered");
        f = scale_image_rect(7, 50, 50, 0, 0, 400, 400);            // centerInside
        record(f.w == 50 && f.h == 50 && f.x == 175 && f.y == 175,
               "H2.8 centerInside: small src never upscales");
    }
    {   Rig r;  // H2.9 the node default is fitCenter (3)
        uint32_t iv = r.node("Landroid/widget/ImageView;", 0, -1, -1);
        record(r.get(iv)->scale_type == 3, "H2.9 ImageView default fitCenter");
    }

    // ---- H3: TextView -> box laws --------------------------------------------
    {   Rig r;
        uint32_t tv = r.node("Landroid/widget/TextView;", 0, -2, -2);
        r.get(tv)->text = "Hello Layout";
        r.get(tv)->text_size_px = 40;
        r.measure(tv);
        auto* n = r.get(tv);
        record(n->measured_width > 100 && n->measured_height >= 40 &&
               n->measured_height <= 120,
               "H3.1 wrap TextView = shaped width, one-line box (w=" +
               std::to_string(n->measured_width) + " h=" +
               std::to_string(n->measured_height) + ")");
    }
    {   Rig r;
        uint32_t tv = r.node("Landroid/widget/TextView;", 0, 400, 120);
        r.get(tv)->text = "Fixed";
        r.get(tv)->text_size_px = 40;
        r.measure(tv);
        record(r.get(tv)->measured_width == 400 &&
               r.get(tv)->measured_height == 120,
               "H3.2 explicit text box kept exactly");
    }
    {   Rig r;
        uint32_t a = r.node("Landroid/widget/TextView;", 0, -2, -2);
        r.get(a)->text = "S"; r.get(a)->text_size_px = 40;
        uint32_t b = r.node("Landroid/widget/TextView;", 0, -2, -2);
        r.get(b)->text = "S"; r.get(b)->text_size_px = 80;
        r.measure(a); r.measure(b);
        record(r.get(b)->measured_width > r.get(a)->measured_width &&
               r.get(b)->measured_height >= r.get(a)->measured_height,
               "H3.3 text_size scales the wrap box");
    }
    {   Rig r;
        uint32_t tv = r.node("Landroid/widget/TextView;", 0, 300, 60);
        r.get(tv)->text = "Centered";
        r.get(tv)->text_gravity = 0x11;  // center|center_vertical
        r.measure(tv);
        record(r.get(tv)->measured_width == 300 &&
               r.get(tv)->measured_height == 60,
               "H3.4 text_gravity does not move the BOX (renderer centers ink)");
    }
    {   Rig r;  // H3.5 text inside a weighted row fills the share
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(ll)->orientation = 0;
        uint32_t t = r.node("Landroid/widget/TextView;", ll, 0, -2, 1000);
        r.get(t)->text = "Weighted"; r.get(t)->text_size_px = 40;
        uint32_t btn = r.node("Landroid/widget/Button;", ll, 300, 100);
        r.measure(ll);
        record(r.get(t)->measured_width == 1080 - 300 &&
               r.get(btn)->measured_width == 300,
               "H3.5 weighted text + fixed button share the row");
    }

    // ---- H4: RelativeLayout rule graph ---------------------------------------
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", rl, 400, 200);
        a = 0; (void)a;
        // name-based rules need android:id names
        uint32_t va = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_below_name = "a";
        r.measure(rl);
        record(r.get(va)->measured_top == 0 &&
               r.get(vb)->measured_top == 200 &&
               r.get(vb)->measured_left == 0,
               "H4.1 below: B.y = A.bottom (200)");
    }
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t va = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_below_name = "a";
        r.get(vb)->lp_margin_top = 50;
        r.measure(rl);
        record(r.get(vb)->measured_top == 250,
               "H4.2 below + topMargin: B.y = 200+50");
    }
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t va = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_right_of_name = "a";
        r.get(vb)->lp_margin_left = 30;
        r.measure(rl);
        record(r.get(vb)->measured_left == 430,
               "H4.3 toRightOf + leftMargin: B.x = 400+30");
    }
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t va = r.node("Landroid/view/View;", rl, 400, 200);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_left_of_name = "a";
        r.get(vb)->lp_margin_right = 20;
        r.measure(rl);
        // AOSP applyHorizontalSizeRules LEFT_OF: the child's RIGHT edge is
        // anchored at the anchor's LEFT minus the child's rightMargin ->
        // B.x = A.left - B.w - mr = 0 - 200 - 20 = -220 (off-screen when
        // the anchor sits at the parent edge — lawful, no auto-flip).
        record(r.get(vb)->measured_left == -220,
               "H4.4 toLeftOf + rightMargin: B.x = A.left-w-mr = -220");
    }
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t v = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(v)->rel_align_parent_right = true;
        r.get(v)->lp_margin_right = 40;
        r.measure(rl);
        record(r.get(v)->measured_left == 1080 - 200 - 40,
               "H4.5 alignParentRight + margin");
    }
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t v = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(v)->rel_align_parent_bottom = true;
        r.get(v)->lp_margin_bottom = 60;
        r.measure(rl);
        record(r.get(v)->measured_top == 1920 - 200 - 60,
               "H4.6 alignParentBottom + margin");
    }
    {   Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t v = r.node("Landroid/view/View;", rl, 200, 200);
        r.get(v)->rel_center_in_parent = true;
        r.measure(rl);
        record(r.get(v)->measured_left == 440 &&
               r.get(v)->measured_top == 860,
               "H4.7 centerInParent: (1080-200)/2, (1920-200)/2");
    }
    {   Rig r;  // H4.8 two-pass chain: C below B below A all resolve
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        const char* names[] = {"a", "b", "c"};
        uint32_t ids[3];
        for (int i = 0; i < 3; ++i) {
            ids[i] = r.node("Landroid/view/View;", rl, 300, 150);
            r.get(ids[i])->android_id_name = names[i];
            if (i) r.get(ids[i])->rel_below_name = names[i - 1];
        }
        r.measure(rl);
        record(r.get(ids[2])->measured_top == 300,
               "H4.8 chain below: C.y = 2*150");
    }
    {   Rig r;  // H4.9 match_parent child fills the relative root
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t v = r.node("Landroid/view/View;", rl, -1, -1);
        r.measure(rl);
        record(r.get(v)->measured_width == 1080 &&
               r.get(v)->measured_height == 1920,
               "H4.9 match_parent child fills relative root");
    }
    {   Rig r;  // H4.10 alignTop: B.y = A.y + topMargin
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t va = r.node("Landroid/view/View;", rl, 300, 150);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 300, 150);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_align_top_name = "a";
        r.get(vb)->lp_margin_top = 25;
        r.measure(rl);
        record(r.get(vb)->measured_top == 25,
               "H4.10 alignTop: B.y = A.y + topMargin");
    }

    // ---- H5: GridView/GridLayout laws ----------------------------------------
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = 2;
        r.get(g)->grid_h_spacing = 10; r.get(g)->grid_v_spacing = 10;
        for (int i = 0; i < 4; ++i) r.node("Landroid/view/View;", g, 500, 300);
        r.measure(g);
        auto kids = r.get(g)->children;
        bool ok = r.get(kids[0])->measured_left == 0 &&
                  r.get(kids[1])->measured_left >= 510 &&
                  r.get(kids[1])->measured_top == 0 &&
                  r.get(kids[2])->measured_top >= 310 &&
                  r.get(kids[3])->measured_top >= 310 &&
                  r.get(kids[3])->measured_left >= 510;
        record(ok, "H5.1 GridView 2 cols: row-major flow with spacing");
    }
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = -1;         // AUTO_FIT
        r.get(g)->grid_column_width = 500;
        r.get(g)->grid_h_spacing = 10; r.get(g)->grid_v_spacing = 10;
        for (int i = 0; i < 4; ++i) r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        // cols = (1080+10)/(500+10) = 2 -> row-major: children 0,1 on row 0,
        // children 2,3 on row 1 (top >= 210).
        record(r.get(r.get(g)->children[0])->measured_top == 0 &&
               r.get(r.get(g)->children[1])->measured_top == 0 &&
               r.get(r.get(g)->children[2])->measured_top >= 210 &&
               r.get(r.get(g)->children[3])->measured_top >= 210,
               "H5.2 AUTO_FIT columnWidth 500 -> 2 cols, row-major");
    }
    {   Rig r;  // H5.3 GridLayout: the engine's documented fallback law is
        // the vertical document flow (GridLayout itself is not a measured
        // ViewGroup here — the GridView carries the real grid laws; AOSP
        // apps using true GridLayout cells need the span-track law, #606
        // documents this as the known fallback boundary).
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", g, 300, 200);
        uint32_t b = r.node("Landroid/view/View;", g, 300, 200);
        r.measure(g);
        record(r.get(a)->measured_left == 0 &&
               r.get(a)->measured_top == 0 &&
               r.get(b)->measured_left == 0 &&
               r.get(b)->measured_top == 200,
               "H5.3 GridLayout fallback: vertical document flow");
    }

    // ---- H6: composite screens ------------------------------------------------
    {   // H6.1 login form: header wrap + input 120 + button row 1:1
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t hdr = r.node("Landroid/widget/TextView;", root, -1, -2);
        r.get(hdr)->text = "Sign in"; r.get(hdr)->text_size_px = 48;
        uint32_t in = r.node("Landroid/widget/EditText;", root, -1, 120);
        (void)in;
        uint32_t row = r.node("Landroid/widget/LinearLayout;", root, -1, 140);
        r.get(row)->orientation = 0;
        uint32_t b1 = r.node("Landroid/widget/Button;", row, 0, -1, 1000);
        uint32_t b2 = r.node("Landroid/widget/Button;", row, 0, -1, 1000);
        r.measure(root);
        record(r.get(b1)->measured_width == 540 &&
               r.get(b2)->measured_width == 540 &&
               r.get(b2)->measured_left == 540 &&
               r.get(row)->measured_top >= 120 &&
               r.get(b1)->measured_height == 140,
               "H6.1 login form: weighted buttons 540 each, row below input");
    }
    {   // H6.2 scroll list: 10 rows of 120 -> content 1200, row 5 at y=600
        Rig r;
        uint32_t sv = r.node("Landroid/widget/ScrollView;", 0, -1, -1);
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", sv, -1, -2);
        r.get(ll)->orientation = 1;  // vertical content (AOSP default is H)
        for (int i = 0; i < 10; ++i) r.node("Landroid/view/View;", ll, -1, 120);
        r.measure(sv);
        record(r.get(ll)->measured_height == 1200 &&
               r.get(r.get(ll)->children[5])->measured_top == 600,
               "H6.2 scroll list: content 1200, row5 y=600");
    }
    {   // H6.3 profile card: avatar left, name rightOf, bio below name
        Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        uint32_t av = r.node("Landroid/widget/ImageView;", rl, 150, 150);
        r.get(av)->android_id_name = "avatar";
        uint32_t nm = r.node("Landroid/widget/TextView;", rl, 500, 80);
        r.get(nm)->android_id_name = "name";
        r.get(nm)->rel_right_of_name = "avatar";
        r.get(nm)->lp_margin_left = 24;
        uint32_t bio = r.node("Landroid/widget/TextView;", rl, 600, 200);
        r.get(bio)->rel_below_name = "name";
        r.measure(rl);
        record(r.get(av)->measured_left == 0 &&
               r.get(nm)->measured_left == 174 &&
               r.get(bio)->measured_top == 80 &&
               r.get(av)->measured_top == 0,
               "H6.3 profile card: avatar 0,0; name x=174; bio y=80");
    }
    {   // H6.4 image viewer: fullscreen image + bottom-centered caption
        Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t iv = r.node("Landroid/widget/ImageView;", fl, -1, -1);
        uint32_t cap = r.node("Landroid/widget/TextView;", fl, -2, -2);
        r.get(cap)->text = "Caption"; r.get(cap)->text_size_px = 40;
        r.get(cap)->child_gravity = 0x50 | 0x1;  // BOTTOM|CENTER_HORIZONTAL
        r.measure(fl);
        record(r.get(iv)->measured_width == 1080 &&
               r.get(iv)->measured_height == 1920 &&
               r.get(cap)->measured_bottom >= 1920 - 160,
               "H6.4 viewer: image fullscreen, caption anchored bottom");
    }
    {   // H6.5 dashboard grid: 2 cols, 6 tiles 500x300
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = 2;
        r.get(g)->grid_v_spacing = 16;
        for (int i = 0; i < 6; ++i) r.node("Landroid/view/View;", g, 500, 300);
        r.measure(g);
        auto kids = r.get(g)->children;
        record(r.get(kids[4])->measured_top >= 632 &&
               r.get(kids[5])->measured_top >= 632 &&
               r.get(kids[5])->measured_left >= 510,
               "H6.5 dashboard: row3 tiles at y>=632, col2 right");
    }

    // ---- H7: FrameLayout stacking + gravity-with-margins ----------------------
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", fl, -1, -1);
        uint32_t b = r.node("Landroid/view/View;", fl, -1, -1);
        r.measure(fl);
        record(r.get(a)->measured_left == 0 && r.get(b)->measured_left == 0 &&
               r.get(a)->measured_width == 1080 &&
               r.get(b)->measured_width == 1080,
               "H7.1 FrameLayout children all stack at the full box");
    }
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x11;  // center both
        r.get(c)->lp_margin_left = 40; r.get(c)->lp_margin_right = 0;
        r.measure(fl);
        // AOSP FrameLayout.onLayout center law: childLeft =
        //   parentLeft + (parentRight - parentLeft - width)/2
        //   + leftMargin - rightMargin = (1080-200)/2 + 40 - 0 = 480
        record(r.get(c)->measured_left == 480,
               "H7.2 center + leftMargin: x=(cw-w)/2+ml (AOSP) = 480");
    }
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x5 | 0x10;  // RIGHT|CENTER_VERTICAL
        r.measure(fl);
        record(r.get(c)->measured_left == 880 &&
               r.get(c)->measured_top == 860,
               "H7.3 right|center_vertical: x=1080-200, y=(1920-200)/2");
    }
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -2, -2);
        uint32_t a = r.node("Landroid/view/View;", fl, 300, 400);
        uint32_t b = r.node("Landroid/view/View;", fl, 500, 200);
        r.measure(fl);
        record(r.get(fl)->measured_width == 500 &&
               r.get(fl)->measured_height == 400,
               "H7.4 wrap FrameLayout sizes to the LARGEST child");
    }

    // ---- H8: spec-negotiation edges -------------------------------------------
    {   Rig r;  // H8.1 INT_MIN sentinel root -> MATCH_PARENT (R-NEW-302)
        Rig r2;
        uint32_t root = r2.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r2.get(root)->lp_width = INT_MIN; r2.get(root)->lp_height = INT_MIN;
        r2.measure(root);
        record(r2.get(root)->measured_width == 1080 &&
               r2.get(root)->measured_height == 1920,
               "H8.1 unset root sentinel = MATCH_PARENT (window law)");
    }
    {   Rig r;  // H8.2 explicit root lp shapes the root box
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, 600, 800);
        r.measure(root);
        record(r.get(root)->measured_width == 600 &&
               r.get(root)->measured_height == 800,
               "H8.2 explicit root 600x800 kept (FIX-MEASURE-003)");
    }
    {   Rig r;  // H8.3 deep nesting stays in bounds, no crash
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t cur = root;
        for (int i = 0; i < 5; ++i) {
            cur = r.node("Landroid/widget/LinearLayout;", cur, -1, -1);
            r.get(cur)->orientation = 1;
        }
        r.node("Landroid/view/View;", cur, -1, 300);
        r.measure(root);
        record(r.get(cur)->measured_width <= 1080 &&
               r.get(cur)->measured_width > 0,
               "H8.3 depth-6 chain lawful widths");
    }
    {   Rig r;  // H8.4 zero-height parent still yields child geometry
        uint32_t p = r.node("Landroid/widget/LinearLayout;", 0, -1, 0);
        uint32_t c = r.node("Landroid/view/View;", p, -1, 100);
        r.measure(p);
        record(r.get(c)->measured_height == 100,
               "H8.4 zero-height parent: child still measures content (g10 [13])");
    }
    {   Rig r;  // H8.5 wrap child inside AT_MOST parent clamps
        uint32_t p = r.node("Landroid/widget/LinearLayout;", 0, 300, -2);
        uint32_t c = r.node("Landroid/view/View;", p, -2, 500);
        r.measure(p);
        record(r.get(c)->measured_width <= 300,
               "H8.5 AT_MOST parent clamps wrap child to spec");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    std::cout << (g_fail == 0 ? "LAYOUT DOMAIN CLOSED\n"
                              : "LAYOUT DOMAIN STILL OPEN\n");
    return g_fail == 0 ? 0 : 1;
}
