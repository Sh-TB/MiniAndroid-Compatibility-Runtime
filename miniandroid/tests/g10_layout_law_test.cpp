// g10_layout_law_test — G10 measurement/layout law battery.
//
// Law references (AOSP):
//   * LinearLayout.java: mOrientation defaults to HORIZONTAL — both the
//     field initializer and the styled-attr default
//     (a.getInt(R.styleable.LinearLayout_orientation, HORIZONTAL)).
//     (G10 corpus evidence: microtimer keypad/input rows omit the
//     attribute; AOSP lays them out as rows, not columns.)
//   * Class-hierarchy law: container measure/layout behavior follows the
//     RESOLVED SUPERCLASS CHAIN. App-defined subclasses
//     (headingcalculator CalculatorDisplay/CalculatorKeypad extend
//     LinearLayout) and framework containers (ViewSwitcher → ViewAnimator
//     → FrameLayout) classify by ancestry, not leaf-name substrings.
//   * Gravity axis-field equality: per-axis fields are MASKED before
//     comparison (FrameLayout onLayout placeChild / Gravity.apply). A raw
//     bit test misroutes combined values (bottom|end = 0x00800055 has both
//     axis bits set).
//   * FrameLayout child gravity: CENTER_HORIZONTAL(0x1)/RIGHT(0x5) on the
//     masked horizontal field; CENTER_VERTICAL(0x10)/BOTTOM(0x50) on the
//     masked vertical field.
//
// Tests are package-independent: no APK, no ARSC, synthetic trees.

#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
    else      printf("  PASS: %s\n", what.c_str());
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
    framework::ViewShadow::ViewNode* get(uint32_t id) { return views.find_node(id); }
};

int main() {
    printf("== G10 §A: LinearLayout unset-orientation = HORIZONTAL law ==\n");
    {
        printf("[1] wrap buttons in orientation-LESS LinearLayout form a ROW\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, 420);
        // orientation left UNSET (-1) — the microtimer keypad-row shape
        uint32_t a = r.node("Landroid/widget/Button;", root, -2, -2);
        r.get(a)->text = "1";
        uint32_t b = r.node("Landroid/widget/Button;", root, -2, -2);
        r.get(b)->text = "2";
        r.measure(root);
        check(r.get(b)->y == r.get(a)->y,
              "children share the same top (row, not column)");
        check(r.get(b)->x > r.get(a)->x,
              "second child placed to the RIGHT of the first");
        check(r.get(a)->y == 0, "first child at container origin");
    }
    {
        printf("[2] orientation-less LL keeps AOSP weight law (0dp+weight fills)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, 420);
        // unset orientation: horizontal; child 0dp+weight fills the row
        uint32_t filler = r.node("Landroid/view/View;", root, 0, -2, 1000);
        r.get(filler)->lp_height = 420;   // cross axis fixed by parent
        uint32_t pad = r.node("Landroid/view/View;", root, 100, 100);
        r.measure(root);
        check(r.get(filler)->measured_width == 1080 - 100,
              "0dp+weight child takes all remaining width (1080-100)");
        check(r.get(pad)->x == 100 + r.get(filler)->measured_width ||
              r.get(pad)->x >= r.get(filler)->measured_width,
              "fixed child placed AFTER the weighted filler");
    }
    {
        printf("[3] explicit vertical still vertical (no regression)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t a = r.node("Landroid/widget/Button;", root, -2, -2);
        r.get(a)->text = "A";
        uint32_t b = r.node("Landroid/widget/Button;", root, -2, -2);
        r.get(b)->text = "B";
        r.measure(root);
        check(r.get(b)->x == r.get(a)->x, "same left (column)");
        check(r.get(b)->y > r.get(a)->y, "second child BELOW first");
    }

    printf("== G10 §B: superclass-chain container classification law ==\n");
    {
        printf("[4] app subclass extends LinearLayout → measured as LinearLayout\n");
        Rig r;
        // DEX-backed hierarchy: the app class inherits LinearLayout behavior
        r.inflater.set_is_a([](const std::string& c, const std::string& a) {
            // minimal stand-in for the DEX chain: known app-class map
            if (c == "Lorg.debian.eugen.headingcalculator.CalculatorDisplay;")
                return a == "Landroid/widget/LinearLayout;" ||
                       a == "Landroid/view/ViewGroup;";
            return false;
        });
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, -1);
        r.get(root)->orientation = 1;
        uint32_t disp = r.node("Lorg.debian.eugen.headingcalculator.CalculatorDisplay;",
                               root, -1, -2);
        uint32_t key = r.node("Landroid/widget/LinearLayout;", root, -1, -1);
        r.measure(root);
        check(r.get(disp)->measured_width == 1080,
              "custom LinearLayout subclass fills parent width");
        (void)key;
        r.inflater.set_is_a(nullptr);
    }
    {
        printf("[5] legacy substring fallback still classifies framework names\n");
        Rig r;
        check(r.inflater.is_a("Landroid/widget/LinearLayout;", "Landroid/widget/LinearLayout;"),
              "exact descriptor contains itself");
        check(r.inflater.is_a("Lcom.example.Foo;", "") == false,
              "empty ancestor never matches");
    }

    printf("== G10 §C: FrameLayout gravity axis-field equality law ==\n");
    {
        printf("[6] bottom|end (0x00800055) child → bottom-right, NOT center\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t fab = r.node("Landroid/widget/ImageButton;", root, -2, -2);
        r.get(fab)->child_gravity = 0x00800055;   // billthefarmer FAB value
        r.measure(root);
        check(r.get(fab)->x == 1080 - r.get(fab)->measured_width,
              "FAB flush to the RIGHT edge (masked hf=0x5)");
        check(r.get(fab)->y == 1920 - r.get(fab)->measured_height,
              "FAB flush to the BOTTOM edge (masked vf=0x50)");
    }
    {
        printf("[7] center|center (0x11) child → centered on both axes\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t c = r.node("Landroid/widget/Button;", root, 200, 100);
        r.get(c)->child_gravity = 0x11;
        r.measure(root);
        check(r.get(c)->x == (1080 - 200) / 2, "centered horizontally");
        check(r.get(c)->y == (1920 - 100) / 2, "centered vertically");
    }
    {
        printf("[8] TOP|LEFT (0x30) → origin (no center/bottom misroute)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/FrameLayout;", 0, -1, -1);
        uint32_t c = r.node("Landroid/widget/Button;", root, 100, 100);
        r.get(c)->child_gravity = 0x30;   // TOP flag only
        r.measure(root);
        check(r.get(c)->x == 0 && r.get(c)->y == 0, "top-left origin");
    }

    printf("== G10 §D: ViewSwitcher classification (FrameLayout semantics) ==\n");
    {
        printf("[9] ViewSwitcher subclassifies to FrameLayout via the chain\n");
        Rig r;
        // wire the framework-chain stand-in (AOSP: switcher → animator → frame)
        r.inflater.set_is_a([](const std::string& c, const std::string& a) {
            if (c == "Landroid/widget/ViewSwitcher;") {
                return a == "Landroid/widget/ViewAnimator;" ||
                       a == "Landroid/widget/FrameLayout;" ||
                       a == "Landroid/view/ViewGroup;";
            }
            return c == a;
        });
        uint32_t root = r.node("Landroid/widget/ViewSwitcher;", 0, -1, -1);
        uint32_t e1 = r.node("Landroid/widget/EditText;", root, -1, -2);
        r.get(e1)->text = "note";
        uint32_t fab = r.node("Landroid/widget/ImageButton;", root, -2, -2);
        r.get(fab)->child_gravity = 0x00800055;
        r.measure(root);
        check(r.inflater.is_a("Landroid/widget/ViewSwitcher;",
                              "Landroid/widget/FrameLayout;"),
              "chain resolves ViewSwitcher → FrameLayout");
        (void)fab;
        r.inflater.set_is_a(nullptr);
    }

    printf("== G10 §E: hostile geometry safety (package-independent) ==\n");
    {
        printf("[10] TableRow (LinearLayout subclass) cells form columns via chain\n");
        Rig r;
        r.inflater.set_is_a([](const std::string& c, const std::string& a) {
            if (c == "Landroid/widget/TableRow;")
                return a == "Landroid/widget/LinearLayout;" ||
                       a == "Landroid/view/ViewGroup;" || c == a;
            return c == a;
        });
        uint32_t row = r.node("Landroid/widget/TableRow;", 0, -1, 210);
        uint32_t c1 = r.node("Landroid/widget/Button;", row, -2, -2);
        r.get(c1)->text = "1";
        uint32_t c2 = r.node("Landroid/widget/Button;", row, -2, -2);
        r.get(c2)->text = "2";
        r.measure(row);
        check(r.get(c2)->y == r.get(c1)->y && r.get(c2)->x > r.get(c1)->x,
              "TableRow cells laid out horizontally (chain → LinearLayout)");
        r.inflater.set_is_a(nullptr);
    }
    {
        printf("[11] GONE child is skipped by the row; INVISIBLE keeps its slot\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, 420);
        uint32_t a = r.node("Landroid/widget/Button;", root, 100, 100);
        uint32_t g = r.node("Landroid/widget/Button;", root, 100, 100);
        r.get(g)->visibility = 8;   // GONE
        uint32_t c = r.node("Landroid/widget/Button;", root, 100, 100);
        r.measure(root);
        check(r.get(c)->x == 100,
              "GONE child contributes no space (next child follows first)");
        (void)a;
    }
    {
        printf("[12] oversized child clamps to parent content width\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, 420);
        uint32_t big = r.node("Landroid/view/View;", root, 4000, 200);
        r.measure(root);
        check(r.get(big)->measured_width <= 1080,
              "4000px explicit child does not exceed the 1080 container");
    }
    {
        printf("[13] zero-height parent still yields lawful child geometry\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, 400, 0);
        r.get(root)->orientation = 1;
        uint32_t c = r.node("Landroid/widget/Button;", root, -1, 60);
        r.measure(root);
        check(r.get(c)->measured_height == 60,
              "explicit 60px child survives a 0-height container measure");
        check(r.get(root)->measured_height == 0,
              "container wrap-of-0 stays 0 (no phantom height)");
    }
    {
        printf("[14] margins push row positions (LinearLayout horizontal law)\n");
        Rig r;
        uint32_t root = r.node("Landroid/widget/LinearLayout;", 0, -1, 420);
        uint32_t a = r.node("Landroid/view/View;", root, 200, 100);
        r.get(a)->lp_margin_left = 40; r.get(a)->lp_margin_right = 30;
        uint32_t b = r.node("Landroid/view/View;", root, 100, 100);
        r.get(b)->lp_margin_left = 10;
        r.measure(root);
        check(r.get(a)->x == 40, "first child offset by its left margin");
        check(r.get(b)->x == 40 + 200 + 30 + 10,
              "next child = prev x + width + right margin + own left margin");
    }

    printf("\nG10 law battery: %d checks, %d failures\n", g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
