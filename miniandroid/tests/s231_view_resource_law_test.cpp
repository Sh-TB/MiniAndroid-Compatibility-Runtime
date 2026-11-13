// s231_view_resource_law_test — #585 §5 view/resource contract battery.
//
// Directive: #585 EXECUTION MANDATE §5 (comment 6818394994) — "Restore
// Android view/resource contracts". This wave lands the two gaps the §5
// text names with live corpus evidence:
//
//   F-S231-A — AbsListView RecycleBin scrap contract (AOSP ListView.java
//     @android-14, frameworks/base/widgets/AbsListView.java RecycleBin):
//     * previous active rows return to scrap at relayout, keyed by the
//       adapter item-view type (Adapter.getItemViewType ∈
//       [0, getViewTypeCount()));
//     * obtainView pops a scrap view of the SAME type as convertView —
//       the adapter REBINDS a materialized row instead of inflating a
//       fresh one every pass;
//     * AdapterView.ITEM_VIEW_TYPE_IGNORE (-1) rows are NEVER recycled;
//     * an out-of-range type violates the Adapter contract (AOSP throws
//       IllegalStateException at bind) — this runtime counts the
//       violation and binds as type 0 (bounded-lenient, never silent);
//     * scrap beyond capacity drops the OLDEST view (counted).
//     The engine's rebuild path (materialize_adapter_rows_for) now wires
//     these mechanics; the counters surface via recycle_rows_reused() /
//     recycle_rows_inflated() / recycle_type_violations().
//
//   F-S231-B — GridView column contract (AOSP GridView.java), wired into
//   the LIVE measure/layout law (LayoutInflater::measure_layout — the
//   UNIFIED_007 single source of truth), NOT a dormant renderer:
//     * android:numColumns=N>1 → N column tracks, row-major flow;
//     * android:numColumns="auto_fit" (-1) → columns =
//       floor((content_w + hSpacing) / (columnWidth + hSpacing));
//       without columnWidth → 1 column (AOSP AUTO_FIT needs columnWidth);
//     * stretchMode=columnWidth (1): tracks stretch to
//       (content_w − (cols−1)·hSpacing)/cols and items fill the cell;
//     * stretchMode=no_stretch (0): track keeps columnWidth, items keep
//       their measured width, leftover stays right-packed;
//     * vertical/horizontal spacing stride the rows/columns;
//     * an ACTIVE grid wraps to rows·(row-max-h + vSpacing) − vSpacing;
//     * INACTIVE grids keep the generic vertical stack (CONT-102) — no
//       silent behavior change for the existing corpus;
//     * items do NOT span tracks (span is GridLayout semantics — the
//       ViewNode note records this approximation, never silent).
//
// Tests are package-independent: no APK, synthetic nodes (g10 pattern).

#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <cstdio>
#include <map>
#include <string>
#include <vector>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
    else      printf("  PASS: %s\n", what.c_str());
}

// ── F-S231-A: AdapterScrapBin mechanics ────────────────────────────────
static void test_scrap_bin_mechanics() {
    printf("== F-S231-A: RecycleBin scrap mechanics ==\n");
    framework::AdapterScrapBin bin;
    bin.stash(1, 100, 0);
    bin.stash(1, 101, 0);
    uint32_t got = 0;
    check(bin.pop(1, 0, got) && got == 101,
          "same-type pop hands back the LAST stashed row (LIFO scrap)");
    check(bin.pop(1, 0, got) && got == 100,
          "second pop hands back the earlier row");
    check(!bin.pop(1, 0, got),
          "empty bucket pops nothing (cold bind → null convertView)");

    bin.stash(1, 200, 1);
    check(bin.pop(1, 0, got) == false,
          "type-0 bucket unaffected by type-1 stash");
    check(bin.pop(1, 1, got) && got == 200,
          "type-1 pop returns the type-1 row");

    bin.stash(1, 300, framework::AdapterScrapBin::kIgnoreType);
    check(bin.pending(1) == 0,
          "IGNORE-type stash is a no-op (AOSP ITEM_VIEW_TYPE_IGNORE)");

    for (uint32_t i = 0; i < framework::AdapterScrapBin::kScrapCapPerType + 3; ++i)
        bin.stash(1, 1000 + i, 2);
    check(bin.pending(1) == framework::AdapterScrapBin::kScrapCapPerType,
          "scrap bucket bounded at kScrapCapPerType");
    check(bin.dropped() == 3,
          "beyond-capacity drops are COUNTED (drop-oldest)");
    check(bin.pop(1, 2, got) &&
              got == 1000 + framework::AdapterScrapBin::kScrapCapPerType + 2,
          "the newest stashed row survives the prune");

    bin.stash(2, 500, 0);
    bin.stash(3, 501, 0);
    bin.prune([](uint32_t lv) { return lv != 2; });  // ListView 2 died
    check(bin.pending(2) == 0, "dead ListView bin pruned");
    check(bin.pop(3, 0, got) && got == 501,
          "live ListView bin survives prune");
    // bins 1 (mechanics block above) and 3 are alive; only bin 2 was erased
    check(bin.bin_count() == 2,
          "prune removes exactly the dead ListView's bin");
}

// ── F-S231-A: engine recycle counters (wiring surface) ─────────────────
static void test_engine_counter_surface() {
    printf("== F-S231-A: engine recycle counter surface ==\n");
    dalvik::DalvikExecutionEngine engine;
    check(engine.recycle_rows_reused() == 0 &&
              engine.recycle_rows_inflated() == 0 &&
              engine.recycle_type_violations() == 0,
          "counters start zeroed (honest measurement)");
    check(engine.adapter_scrap().bin_count() == 0,
          "no bins before any adapter bind");
}

// ── F-S231-B: GridView column law via the LIVE measure_layout ──────────
struct GridRig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    resources::ArscParser arsc;
    apk::ApkParser apk;
    resources::LayoutInflater inflater{
        arsc, apk, "", resources::DeviceMetrics{1080, 1920, 2.625f, 1.0f}};

    GridRig() { views.init(&heap_adapter); }

    uint32_t node(const char* cls, uint32_t parent, int lp_w, int lp_h) {
        uint32_t id = views.create_view(cls);
        auto* n = views.find_node(id);
        n->lp_width = lp_w;
        n->lp_height = lp_h;
        if (parent) views.add_child(parent, id);
        return id;
    }
    void measure(uint32_t root) { inflater.measure_layout(&views, root); }
    framework::ViewShadow::ViewNode* get(uint32_t id) {
        return views.find_node(id);
    }
};

static void test_grid_columns_law() {
    printf("== F-S231-B: GridView numColumns/stretch law (live path) ==\n");
    printf("[1] numColumns=3 → 3 tracks, row-major flow\n");
    {
        GridRig r;
        uint32_t grid = r.node("Landroid/widget/GridView;", 0, 900, 600);
        auto* g = r.get(grid);
        g->grid_num_columns = 3;
        g->grid_stretch_mode = 1;  // columnWidth
        for (int i = 0; i < 6; ++i)
            r.node("Landroid/widget/TextView;", grid, -1, 100);
        r.measure(grid);
        auto* a = r.get(r.get(grid)->children[0]);
        auto* b = r.get(r.get(grid)->children[1]);
        auto* c = r.get(r.get(grid)->children[2]);
        auto* d = r.get(r.get(grid)->children[3]);
        check(a->measured_width == 300 && b->measured_width == 300 &&
                  c->measured_width == 300,
              "stretch columnWidth: track = content/3 = 300px");
        check(a->measured_left == 0 && b->measured_left == 300 &&
                  c->measured_left == 600,
              "row-major: items 0,1,2 fill row 0 left→right");
        check(d->measured_left == a->measured_left &&
                  d->measured_top > a->measured_top,
              "item 3 wraps to row 1 col 0 below");
    }
    printf("[2] AUTO_FIT + columnWidth → floor((w+hsp)/(cw+hsp)) columns\n");
    {
        GridRig r;
        uint32_t grid = r.node("Landroid/widget/GridView;", 0, 900, 600);
        auto* g = r.get(grid);
        g->grid_num_columns = -1;   // AUTO_FIT
        g->grid_column_width = 300; // → (900)/(300) = 3
        g->grid_stretch_mode = 1;
        for (int i = 0; i < 3; ++i)
            r.node("Landroid/widget/TextView;", grid, -1, 100);
        r.measure(grid);
        auto* a = r.get(r.get(grid)->children[0]);
        auto* c = r.get(r.get(grid)->children[2]);
        check(a->measured_width == 300 && c->measured_left == 600,
              "AUTO_FIT derives 3 columns from columnWidth=300 in 900px");
    }
    printf("[3] AUTO_FIT WITHOUT columnWidth → 1 column (vertical stack, CONT-102)\n");
    {
        GridRig r;
        uint32_t grid = r.node("Landroid/widget/GridView;", 0, 900, 600);
        auto* g = r.get(grid);
        g->grid_num_columns = -1;  // no columnWidth → law OFF
        for (int i = 0; i < 3; ++i)
            r.node("Landroid/widget/TextView;", grid, -1, 100);
        r.measure(grid);
        auto* a = r.get(r.get(grid)->children[0]);
        auto* b = r.get(r.get(grid)->children[1]);
        check(a->measured_left == b->measured_left &&
                  b->measured_top > a->measured_top,
              "AUTO_FIT without columnWidth stays the vertical stack");
    }
    printf("[4] spacing strides both axes\n");
    {
        GridRig r;
        uint32_t grid = r.node("Landroid/widget/GridView;", 0, 906, 600);
        auto* g = r.get(grid);
        g->grid_num_columns = 3;
        g->grid_h_spacing = 3;   // track = (906 − 2·3)/3 = 300
        g->grid_v_spacing = 10;
        g->grid_stretch_mode = 1;
        for (int i = 0; i < 6; ++i)
            r.node("Landroid/widget/TextView;", grid, -1, 100);
        r.measure(grid);
        auto* nodes = r.get(grid);
        auto* a = r.get(nodes->children[0]);
        auto* b = r.get(nodes->children[1]);
        auto* d = r.get(nodes->children[3]);
        check(a->measured_width == 300,
              "hSpacing subtracted before the track split");
        check(b->measured_left == 303,
              "column stride = track + hSpacing");
        check(d->measured_top == a->measured_top + 110,
              "row stride = row-max-height + vSpacing");
    }
    printf("[5] wrap law: grid wraps rows·(row-max-h + vSpacing) − vSpacing\n");
    {
        GridRig r;
        uint32_t grid = r.node("Landroid/widget/GridView;", 0, 900, -2);
        auto* g = r.get(grid);
        g->grid_num_columns = 3;
        g->grid_v_spacing = 5;
        g->grid_stretch_mode = 1;
        for (int i = 0; i < 6; ++i)
            r.node("Landroid/widget/TextView;", grid, -1, 40);
        r.measure(grid);
        auto* gg = r.get(grid);
        check(gg->measured_height == 2 * 40 + 5,
              "2 rows × 40px + 1 gap = 85px wrap height");
    }
    printf("[6] unparsed numColumns (0) keeps the law OFF (no silent change)\n");
    {
        GridRig r;
        uint32_t grid = r.node("Landroid/widget/GridView;", 0, 900, 600);
        for (int i = 0; i < 3; ++i)
            r.node("Landroid/widget/TextView;", grid, -1, 100);
        r.measure(grid);
        auto* nodes = r.get(grid);
        auto* a = r.get(nodes->children[0]);
        auto* b = r.get(nodes->children[1]);
        check(a->measured_left == b->measured_left &&
                  b->measured_top > a->measured_top,
              "law-off GridView = CONT-102 vertical stack (regression guard)");
    }
}

int main() {
    printf("== s231_view_resource_law_test — #585 §5 contracts ==\n");
    test_scrap_bin_mechanics();
    test_engine_counter_surface();
    test_grid_columns_law();
    printf("RESULT: %d checks, %d failed\n", g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
