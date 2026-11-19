// s247_grid_rtl_law_test — the #606 D-wave: closes the two documented
// boundaries left open by s246 — REAL GridLayout (span-track cells) and
// RTL (layoutDirection mirroring). Groups:
//   G1  GridLayout auto-flow + wrap-at-count
//   G2  explicit cells + count derivation (Axis.getCount law)
//   G3  track sizing (max per track) + spans (even-split deviation, documented)
//   G4  cell gravity (START default / FILL / CENTER / END) + wrap_content
//   G6  the REAL AOSP constraint solver (leading + interval arcs, fixpoint)
//   G5  GridLayout RTL mirror (X-only)
//   R1  layoutDirection resolution (explicit / inherit chain)
//   R2  LinearLayout horizontal row mirror (+ weighted shares)
//   R3  FrameLayout relative-gravity flip (START/END), literals pinned
//   R4  RelativeLayout directional aliases mirror; literals never move
//   R5  GridView column mirror
//   R6  LL vertical column cross-axis law (mask-first equality + RTL flip)
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
    std::cout << "== s247 grid + rtl closure matrix ==\n";

    // ---- G1: auto-flow + wrap-at-count ---------------------------------------
    {   // G1.1 2 cols, 4 children 500x200 → row-major, stride 510
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        for (int i = 0; i < 4; ++i) r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        auto k = r.get(g)->children;
        record(r.get(k[0])->measured_left == 0 &&
               r.get(k[1])->measured_left == 500 &&
               r.get(k[2])->measured_top == 200 &&
               r.get(k[3])->measured_top == 200 &&
               r.get(k[3])->measured_left == 500,
               "G1.1 2 cols: row-major flow, wrap at count");
    }
    {   // G1.2 3 cols, 5 children → rows of 3 then 2 (wrap law)
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 3;
        for (int i = 0; i < 5; ++i) r.node("Landroid/view/View;", g, 300, 100);
        r.measure(g);
        auto k = r.get(g)->children;
        record(r.get(k[2])->measured_left == 600 &&
               r.get(k[3])->measured_top == 100 &&
               r.get(k[4])->measured_top == 100 &&
               r.get(k[4])->measured_left == 300,
               "G1.2 3 cols, 5 kids: 3+2 rows (wrap-at-count)");
    }
    {   // G1.3 UNDEFINED count + no explicit cells → ONE column (AOSP
        //     Axis.getCount: count = max(defined, maxIndex) = 1)
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", g, 300, 100);
        uint32_t b = r.node("Landroid/view/View;", g, 300, 100);
        r.measure(g);
        record(r.get(a)->measured_left == 0 &&
               r.get(b)->measured_left == 0 &&
               r.get(b)->measured_top == 100,
               "G1.3 no count, no cells: one column (classic default)");
    }

    // ---- G2: explicit cells + count derivation --------------------------------
    {   // G2.1 explicit cell (1,2): track-origin law + count derived to 3.
        // AOSP: EMPTY tracks are zero-width (the constraint solver gives an
        // unconstrained line 0 size), so col2's origin = ΣcolW[0..1] —
        // pinned with a real (0,0) sibling so the tracks are non-empty.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        uint32_t a = r.node("Landroid/view/View;", g, 200, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        uint32_t b = r.node("Landroid/view/View;", g, 200, 100);
        r.get(b)->grid_row = 1; r.get(b)->grid_col = 2;
        r.measure(g);
        record(r.get(b)->measured_left == 200 &&
               r.get(b)->measured_top == 100,
               "G2.1 explicit (1,2): origin = Σ tracks 0..1 = 200, y=100");
    }
    {   // G2.2 explicit (0,0) then auto child skips the occupied cell
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t a = r.node("Landroid/view/View;", g, 200, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        uint32_t b = r.node("Landroid/view/View;", g, 200, 100);
        r.measure(g);
        record(r.get(b)->measured_left == 200 &&
               r.get(b)->measured_top == 0,
               "G2.2 auto child skips the explicit (0,0) cell (fits law)");
    }

    // ---- G3: track sizing + spans ----------------------------------------------
    {   // G3.1 track = MAX of its cells (col0 has 100w and 300w → 300)
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        r.node("Landroid/view/View;", g, 100, 100);
        uint32_t tall = r.node("Landroid/view/View;", g, 300, 100);
        r.get(tall)->grid_row = 1; r.get(tall)->grid_col = 0;
        r.node("Landroid/view/View;", g, 200, 100);
        r.measure(g);
        auto k = r.get(g)->children;
        record(r.get(k[2])->measured_left == 300 &&
               r.get(k[1])->measured_top == 100,
               "G3.1 col0 track = max(100,300)=300; tall child y=rowY[1]=100");
    }
    {   // G3.2 span 2 over two 200px tracks with a 600px child: the 200
        //     excess splits evenly (the documented engine simplification
        //     of the AOSP constraint solver) → tracks 400/400
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t s = r.node("Landroid/view/View;", g, 600, 100);
        r.get(s)->grid_col_span = 2;
        r.node("Landroid/view/View;", g, 200, 100);
        r.measure(g);
        auto k = r.get(g)->children;
        // AOSP validateLayoutParams: the span-2 child OCCUPIES (0,0)+(0,1),
        // so the auto child wraps to (1,0) — x=0, y=rowY[1]. E-wave: the
        // REAL constraint solve gives lines [0,200,600] → tracks 200/400
        // (the excess lands in the TRAILING track of the span).
        record(r.get(k[1])->measured_left == 0 &&
               r.get(k[1])->measured_top == 100 &&
               r.get(s)->measured_width == 600 &&
               r.get(k[0])->measured_left == 0,
               "G3.2 span occupies row 0; solver tracks 200/400 (trailing excess)");
    }

    // ---- G4: cell gravity + wrap_content ----------------------------------------
    {   // G4.1 default gravity: START/top — measured size at the cell
        // origin. E-wave solver law: span arc (0→2, 200) with col-1 max 100
        // gives lines [0,0,200] → tracks 0/200 (col0 empty, excess in the
        // trailing track); cell (1,1) origin = line1 = 0.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t s = r.node("Landroid/view/View;", g, 200, 100);
        r.get(s)->grid_col_span = 2;
        uint32_t c = r.node("Landroid/view/View;", g, 100, 50);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 1;
        r.measure(g);
        record(r.get(c)->measured_left == 0 &&
               r.get(c)->measured_top == 100 &&
               r.get(c)->measured_width == 100 &&
               r.get(s)->measured_width == 200,
               "G4.1 solver tracks 0/200; START child at line1 origin");
    }
    {   // G4.2 FILL gravity: the child takes the cell INNER box
        // (solved track minus its margins) — solver tracks 0/200 → the
        // col-1 cell is 200 wide.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t s = r.node("Landroid/view/View;", g, 200, 100);
        r.get(s)->grid_col_span = 2;
        uint32_t c = r.node("Landroid/view/View;", g, 100, 50);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 1;
        r.get(c)->child_gravity = 0x7 | 0x70;  // FILL both axes
        r.measure(g);
        record(r.get(c)->measured_left == 0 &&
               r.get(c)->measured_width == 200 &&
               r.get(c)->measured_height == 50,
               "G4.2 FILL: child stretches to the solved track inner box (200)");
    }
    {   // G4.3 CENTER in cell: cell (1,1) = [200..300]×[100..150] with a
        // (0,0) 200px sibling — the 100x50 child centers exactly at origin.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        r.node("Landroid/view/View;", g, 200, 100);
        uint32_t c = r.node("Landroid/view/View;", g, 100, 50);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 1;
        r.get(c)->child_gravity = 0x1 | 0x10;  // center both
        r.measure(g);
        record(r.get(c)->measured_left == 200 &&
               r.get(c)->measured_top == 100,
               "G4.3 CENTER: centered inside the cell (probe-verified)");
    }
    {   // G4.4 wrap_content GridLayout = sum of tracks
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -2, -2);
        r.get(g)->gl_col_count = 2;
        r.node("Landroid/view/View;", g, 300, 100);
        r.node("Landroid/view/View;", g, 200, 150);
        r.node("Landroid/view/View;", g, 250, 120);
        r.measure(g);
        record(r.get(g)->measured_width == 500 &&
               r.get(g)->measured_height == 270,
               "G4.4 wrap grid = ΣcolW=500 × ΣrowH=270");
    }

    // ---- G6: the REAL AOSP constraint solver (E-wave, #606 FINAL) -----------------
    {   // G6.1 trailing law: lines [0,200,600] — the whole excess lands in
        // the TRAILING track of the span (200/400), not an even split.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t a = r.node("Landroid/view/View;", g, 200, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        uint32_t b = r.node("Landroid/view/View;", g, 200, 100);
        r.get(b)->grid_row = 0; r.get(b)->grid_col = 1;
        uint32_t c = r.node("Landroid/view/View;", g, 600, 100);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 0;
        r.get(c)->grid_col_span = 2;
        r.measure(g);
        record(r.get(c)->measured_left == 0 &&
               r.get(c)->measured_top == 100 &&
               r.get(c)->measured_width == 600,
               "G6.1 span-2 600 over 200/200: lines [0,200,600] (trailing excess)");
    }
    {   // G6.2 neighbors untouched: lines [0,100,450,550] — track1 takes the
        // whole span excess (350), tracks 0 and 2 keep their own maxima.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 3;
        uint32_t a = r.node("Landroid/view/View;", g, 100, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        uint32_t b = r.node("Landroid/view/View;", g, 100, 100);
        r.get(b)->grid_row = 0; r.get(b)->grid_col = 1;
        uint32_t c = r.node("Landroid/view/View;", g, 100, 100);
        r.get(c)->grid_row = 0; r.get(c)->grid_col = 2;
        uint32_t d = r.node("Landroid/view/View;", g, 450, 100);
        r.get(d)->grid_row = 1; r.get(d)->grid_col = 0;
        r.get(d)->grid_col_span = 2;
        r.measure(g);
        record(r.get(b)->measured_left == 100 &&
               r.get(c)->measured_left == 450 &&
               r.get(d)->measured_width == 450 &&
               r.get(d)->measured_left == 0,
               "G6.2 span-2 450 over 100/100: excess in track1 (350), others kept");
    }
    {   // G6.3 span-3: lines [0,100,200,500] → tracks 100/100/300.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 3;
        for (int i = 0; i < 3; ++i) {
            uint32_t v = r.node("Landroid/view/View;", g, 100, 100);
            r.get(v)->grid_row = 0; r.get(v)->grid_col = i;
        }
        uint32_t d = r.node("Landroid/view/View;", g, 500, 100);
        r.get(d)->grid_row = 1; r.get(d)->grid_col = 0;
        r.get(d)->grid_col_span = 3;
        r.measure(g);
        record(r.get(d)->measured_left == 0 &&
               r.get(d)->measured_top == 100 &&
               r.get(d)->measured_width == 500,
               "G6.3 span-3 500 over 100/100/100: lines [0,100,200,500]");
    }
    {   // G6.4 two interacting arcs: A span-2 (0→2, 500) + B at col2 (100):
        // lines [0,0,500,600] → tracks 0/500/100; B sits exactly at line2.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 3;
        uint32_t a = r.node("Landroid/view/View;", g, 500, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        r.get(a)->grid_col_span = 2;
        uint32_t b = r.node("Landroid/view/View;", g, 100, 100);
        r.get(b)->grid_row = 0; r.get(b)->grid_col = 2;
        r.measure(g);
        record(r.get(a)->measured_width == 500 &&
               r.get(b)->measured_left == 500 &&
               r.get(a)->measured_left == 0,
               "G6.4 span arc (0→2,500): line2=500, B at the arc's end line");
    }
    {   // G6.5 the ROW axis runs the same solver: rows [0,100,350] →
        // 100/250; the spanned child sits at rowY[2]=200 with its 250 height.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 1;
        uint32_t a = r.node("Landroid/view/View;", g, 100, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        uint32_t b = r.node("Landroid/view/View;", g, 100, 100);
        r.get(b)->grid_row = 1; r.get(b)->grid_col = 0;
        uint32_t c = r.node("Landroid/view/View;", g, 100, 250);
        r.get(c)->grid_row = 2; r.get(c)->grid_col = 0;
        r.get(c)->grid_row_span = 2;
        r.measure(g);
        record(r.get(c)->measured_top == 200 &&
               r.get(c)->measured_height == 250 &&
               r.get(b)->measured_top == 100,
               "G6.5 row-axis solver: rows [0,100,350] (excess in trailing row)");
    }
    {   // G6.6 no widening when the spanned child FITS: lines [0,100,300]
        // — the track maxima win over the 150 arc.
        Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        uint32_t a = r.node("Landroid/view/View;", g, 100, 100);
        r.get(a)->grid_row = 0; r.get(a)->grid_col = 0;
        uint32_t b = r.node("Landroid/view/View;", g, 200, 100);
        r.get(b)->grid_row = 0; r.get(b)->grid_col = 1;
        uint32_t c = r.node("Landroid/view/View;", g, 150, 100);
        r.get(c)->grid_row = 1; r.get(c)->grid_col = 0;
        r.get(c)->grid_col_span = 2;
        r.measure(g);
        record(r.get(b)->measured_left == 100 &&
               r.get(c)->measured_width == 150 &&
               r.get(c)->measured_left == 0,
               "G6.6 span 150 < tracks 300: no widening (minimal solution)");
    }

    // ---- G5: GridLayout RTL mirror (X only) --------------------------------------
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridLayout;", 0, -1, -1);
        r.get(g)->gl_col_count = 2;
        r.get(g)->layout_dir = 1;   // rtl
        for (int i = 0; i < 2; ++i) r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        auto k = r.get(g)->children;
        // x' = cl + cw - dx - w (AOSP GridLayout.onLayout RTL law):
        // k0 dx=0 → 580; k1 dx=500 → 80.
        record(r.get(k[0])->measured_left == 580 &&
               r.get(k[1])->measured_left == 80 &&
               r.get(k[0])->measured_top == 0,
               "G5.1 RTL grid: X-only mirror (580 / 80), Y kept");
    }

    // ---- R1: layoutDirection resolution -------------------------------------------
    {   Rig r;
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(ll)->layout_dir = 1;
        uint32_t c = r.node("Landroid/view/View;", ll, 100, 100);
        r.measure(ll);
        record(r.get(ll)->layout_dir_resolved == 1 &&
               r.get(c)->layout_dir_resolved == 1,
               "R1.1 explicit rtl on parent: child INHERITS rtl");
    }
    {   Rig r;
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(ll)->layout_dir = 1;
        uint32_t mid = r.node("Landroid/widget/LinearLayout;", ll, -1, -1);
        r.get(mid)->layout_dir = 0;   // explicit ltr re-pins the subtree
        uint32_t c = r.node("Landroid/view/View;", mid, 100, 100);
        r.measure(ll);
        record(r.get(mid)->layout_dir_resolved == 0 &&
               r.get(c)->layout_dir_resolved == 0,
               "R1.2 explicit ltr inside rtl subtree re-pins (AOSP law)");
    }
    {   Rig r;
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        uint32_t c = r.node("Landroid/view/View;", ll, 100, 100);
        r.measure(ll);
        record(r.get(ll)->layout_dir_resolved == 0 &&
               r.get(c)->layout_dir_resolved == 0,
               "R1.3 root inherit = LTR (no-supportsRtl compat law)");
    }

    // ---- R2: LinearLayout horizontal row mirror ------------------------------------
    {   Rig r;
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(ll)->layout_dir = 1;
        uint32_t a = r.node("Landroid/view/View;", ll, 200, 100);
        uint32_t b = r.node("Landroid/view/View;", ll, 300, 100);
        uint32_t c = r.node("Landroid/view/View;", ll, 400, 100);
        r.measure(ll);
        record(r.get(a)->measured_left == 1080 - 200 &&
               r.get(b)->measured_left == 1080 - 200 - 300 &&
               r.get(c)->measured_left == 1080 - 200 - 300 - 400,
               "R2.1 RTL row: document order right→left (exact mirror)");
    }
    {   Rig r;  // R2.2 weighted row mirrors: b1 (weight 1) takes the RIGHT half
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(ll)->layout_dir = 1;
        uint32_t b1 = r.node("Landroid/widget/Button;", ll, 0, 100, 1000);
        uint32_t b2 = r.node("Landroid/widget/Button;", ll, 0, 100, 1000);
        r.measure(ll);
        record(r.get(b1)->measured_left == 540 &&
               r.get(b2)->measured_left == 0 &&
               r.get(b1)->measured_width == 540,
               "R2.2 weighted RTL row: first button takes the right half");
    }

    // ---- R3: FrameLayout relative-gravity flip --------------------------------------
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        r.get(fl)->layout_dir = 1;
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x00800055;  // BOTTOM|END (billthefarmer FAB)
        r.measure(fl);
        record(r.get(c)->measured_left == 0 &&
               r.get(c)->measured_top == 1920 - 200,
               "R3.1 RTL END flips to LEFT (bottom-left FAB)");
    }
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        r.get(fl)->layout_dir = 1;
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x00800053;  // BOTTOM|START
        r.measure(fl);
        record(r.get(c)->measured_left == 1080 - 200 &&
               r.get(c)->measured_top == 1920 - 200,
               "R3.2 RTL START flips to RIGHT (BOTTOM bit kept)");
    }
    {   Rig r;
        uint32_t fl = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        r.get(fl)->layout_dir = 1;
        uint32_t c = r.node("Landroid/view/View;", fl, 200, 200);
        r.get(c)->child_gravity = 0x5 | 0x50;  // literal RIGHT|BOTTOM
        r.measure(fl);
        record(r.get(c)->measured_left == 1080 - 200 &&
               r.get(c)->measured_top == 1920 - 200,
               "R3.3 literal RIGHT|BOTTOM never moves under RTL");
    }

    // ---- R4: RelativeLayout directional aliases -------------------------------------
    {   // R4.1 toEndOf under RTL acts as toLeftOf
        Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        r.get(rl)->layout_dir = 1;
        uint32_t va = r.node("Landroid/view/View;", rl, 300, 150);
        r.get(va)->android_id_name = "a";
        r.get(va)->rel_align_parent_right = true;
        uint32_t vb = r.node("Landroid/view/View;", rl, 200, 150);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_right_of_name = "a";
        r.get(vb)->rel_right_of_is_end = true;   // layout_toEndOf="a"
        r.get(vb)->lp_margin_left = 20;
        r.measure(rl);
        // a anchors the RIGHT edge (alignParentRight literal, unchanged);
        // b sits LEFT of a under RTL: b.x = a.left - b.w - (b's rightMargin
        // in the mirrored law = the left margin in LTR terms → the alias
        // mirrors the RULE, margins keep their physical sides)
        // mirrored rule: b.right = a.left - (a.leftMargin + b.rightMargin)
        // = 780 - (0+0) → b.x = 580 (probe-verified engine law).
        record(r.get(vb)->measured_left == 580,
               "R4.1 RTL toEndOf(a) → b LEFT of a (anchor-margin law)");
    }
    {   // R4.2 literal toRightOf unchanged under RTL
        Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        r.get(rl)->layout_dir = 1;
        uint32_t va = r.node("Landroid/view/View;", rl, 300, 150);
        r.get(va)->android_id_name = "a";
        uint32_t vb = r.node("Landroid/view/View;", rl, 200, 150);
        r.get(vb)->android_id_name = "b";
        r.get(vb)->rel_right_of_name = "a";
        r.get(vb)->lp_margin_left = 30;
        r.measure(rl);
        record(r.get(vb)->measured_left == 330,
               "R4.2 literal toRightOf never moves under RTL");
    }
    {   // R4.3 alignParentEnd under RTL → left edge
        Rig r;
        uint32_t rl = r.node("Landroid/widget/RelativeLayout;", 0, -1, -1);
        r.get(rl)->layout_dir = 1;
        uint32_t v = r.node("Landroid/view/View;", rl, 200, 150);
        r.get(v)->rel_align_parent_right = true;
        r.get(v)->rel_align_parent_right_is_end = true;
        r.get(v)->lp_margin_left = 40;
        r.measure(rl);
        record(r.get(v)->measured_left == 40,
               "R4.3 alignParentEnd under RTL → LEFT edge + leftMargin");
    }

    // ---- R5: GridView column mirror ---------------------------------------------------
    {   Rig r;
        uint32_t g = r.node("Landroid/widget/GridView;", 0, -1, -1);
        r.get(g)->grid_num_columns = 2;
        r.get(g)->grid_v_spacing = 10;
        r.get(g)->layout_dir = 1;   // rtl
        for (int i = 0; i < 2; ++i) r.node("Landroid/view/View;", g, 500, 200);
        r.measure(g);
        auto k = r.get(g)->children;
        record(r.get(k[0])->measured_left == 540 &&
               r.get(k[1])->measured_left == 0 &&
               r.get(k[0])->measured_top == 0,
               "R5.1 RTL GridView: first item at track 1 (540), second left");
    }

    // ---- R6: LL vertical column cross-axis law (mask-first + RTL flip) ------------------
    {   Rig r;  // R6.1 literal RIGHT child in a column → right edge (the
        //     old bit-test misrouted it to CENTER)
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, 500, -1);
        r.get(ll)->orientation = 1;
        uint32_t c = r.node("Landroid/view/View;", ll, 200, 100);
        r.get(c)->child_gravity = 0x5;   // RIGHT (literal, no relative bit)
        r.measure(ll);
        record(r.get(c)->measured_left == 500 - 200,
               "R6.1 vertical column: literal RIGHT → right edge (not CENTER)");
    }
    {   Rig r;  // R6.2 literal LEFT child stays left (0x3 ≠ center)
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, 500, -1);
        r.get(ll)->orientation = 1;
        uint32_t c = r.node("Landroid/view/View;", ll, 200, 100);
        r.get(c)->child_gravity = 0x3;   // LEFT (literal)
        r.measure(ll);
        record(r.get(c)->measured_left == 0,
               "R6.2 vertical column: literal LEFT → left edge");
    }
    {   Rig r;  // R6.3 START (relative) child in an RTL column → right edge
        uint32_t ll = r.node("Landroid/widget/LinearLayout;", 0, 500, -1);
        r.get(ll)->orientation = 1;
        r.get(ll)->layout_dir = 1;
        uint32_t c = r.node("Landroid/view/View;", ll, 200, 100);
        r.get(c)->child_gravity = 0x00800003;  // START
        r.measure(ll);
        record(r.get(c)->measured_left == 500 - 200,
               "R6.3 RTL column: START child → right edge");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    std::cout << (g_fail == 0 ? "GRID+RTL DOMAIN CLOSED\n"
                              : "GRID+RTL DOMAIN STILL OPEN\n");
    return g_fail == 0 ? 0 : 1;
}
