// CAMPAIGN 010 R3 — Yoga layout adapter experiment.
//
// Inflates a REAL binary layout (GMDice act_gmdice.xml from the actual APK)
// through MiniAndroid's own stack (ResourceRuntime → AxmlParser +
// LayoutInflater), then:
//   (1) runs the CURRENT custom measure_layout (LayoutInflater), and
//   (2) runs facebook/yoga @ bd8fe0d (MIT) via a LinearLayout→Flexbox
//       adapter (orientation/margins/weights/gravity/padding mapping),
// and compares computed geometry + benchmarks both engines.
#include <cstdio>
#include <cmath>
#include <chrono>
#include <string>
#include <vector>
#include <map>
#include <functional>

#include "resources/resource_runtime.h"
#include "framework/android_shadows.h"
#include "framework/shadow_registry.h"

#include <yoga/Yoga.h>

using namespace miniandroid;

static const float DENSITY = 2.625f;   // runtime default device
static const float SCREEN_W = 1080.0f;
static const float SCREEN_H = 1920.0f;

static float pt(float px) { return px / DENSITY; }

// ---- Yoga text measure: same heuristic as LayoutInflater ------------------
struct TextCtx { std::string text; float text_size_px; };

static std::map<const YGNode*, TextCtx> g_text_ctx;

static float text_width_px(const TextCtx& t) {
    float ts = t.text_size_px > 0 ? t.text_size_px : 14.0f * DENSITY;
    return t.text.size() * ts * 0.62f;
}
static float text_height_px(const TextCtx& t) {
    float ts = t.text_size_px > 0 ? t.text_size_px : 14.0f * DENSITY;
    return ts * 1.35f + 2;
}

static YGSize yoga_measure_ctx(const YGNode* node, float /*w*/, YGMeasureMode /*wm*/,
                               float /*h*/, YGMeasureMode /*hm*/) {
    auto it = g_text_ctx.find(node);
    if (it == g_text_ctx.end()) return YGSize{0, 0};
    return YGSize{pt(text_width_px(it->second)), pt(text_height_px(it->second))};
}

// ---- build Yoga tree from ViewShadow tree ---------------------------------
struct YogaMap { uint32_t view_id; YGNodeRef node; float ax; float ay; };

static YGNodeRef build_yoga(framework::ViewShadow* views, uint32_t vid,
                            std::vector<YogaMap>& out, float ox = 0.0f, float oy = 0.0f) {
    auto* n = views->find_node(vid);
    if (!n) return nullptr;
    YGNodeRef y = YGNodeNew();
    out.push_back({vid, y, ox, oy});

    bool is_container = n->class_desc.find("Layout") != std::string::npos ||
                        n->class_desc.find("ScrollView") != std::string::npos;

    int lw = n->lp_width, lh = n->lp_height;
    if (lw == INT_MIN) lw = -2;
    if (lh == INT_MIN) lh = -2;

    if (is_container) {
        bool horiz = (n->orientation == 0);
        YGNodeStyleSetFlexDirection(y, horiz ? YGFlexDirectionRow : YGFlexDirectionColumn);
    }
    if (lw == -1) YGNodeStyleSetWidthPercent(y, 100);
    else if (lw == -2) YGNodeStyleSetWidthAuto(y);
    else YGNodeStyleSetWidth(y, pt((float)lw));
    if (lh == -1) YGNodeStyleSetHeightPercent(y, 100);
    else if (lh == -2) YGNodeStyleSetHeightAuto(y);
    else YGNodeStyleSetHeight(y, pt((float)lh));

    if (n->lp_margin_left) YGNodeStyleSetMargin(y, YGEdgeLeft, pt((float)n->lp_margin_left));
    if (n->lp_margin_top) YGNodeStyleSetMargin(y, YGEdgeTop, pt((float)n->lp_margin_top));
    if (n->lp_margin_right) YGNodeStyleSetMargin(y, YGEdgeRight, pt((float)n->lp_margin_right));
    if (n->lp_margin_bottom) YGNodeStyleSetMargin(y, YGEdgeBottom, pt((float)n->lp_margin_bottom));

    if (n->layout_weight > 0) {
        YGNodeStyleSetFlexGrow(y, n->layout_weight / 1000.0f);
        YGNodeStyleSetFlexBasis(y, 0);
    }
    if (n->lp_gravity & 0x1 /*CENTER_HORIZONTAL*/) YGNodeStyleSetAlignSelf(y, YGAlignCenter);

    if (!n->text.empty()) {
        float ts = n->text_size_px > 0 ? n->text_size_px : 14.0f * DENSITY;
        g_text_ctx[y] = TextCtx{n->text, ts};
        YGNodeSetMeasureFunc(y, yoga_measure_ctx);
    }
    for (uint32_t c : n->children) {
        // child origin = this node's computed absolute position (after the
        // first layout pass we could use margins; here Yoga recursion makes
        // children relative to this node, so record this node's origin).
        YGNodeRef cy = build_yoga(views, c, out, ox, oy);
        if (cy) YGNodeInsertChild(y, cy, YGNodeGetChildCount(y));
    }
    return y;
}

int main(int argc, char** argv) {
    const char* apk_path = argc > 1 ? argv[1] : "download/corpus/gmdice.apk";
    const char* layout_name = argc > 2 ? argv[2] : "act_gmdice";

    auto& rr = resources::ResourceRuntime::instance();
    if (!rr.ensure_loaded(apk_path)) {
        printf("resource runtime FAIL: %s\n", rr.stats_json().c_str());
        return 1;
    }
    // Standalone heap: ViewShadow::create_view needs a HeapAllocator for
    // object ids; layout geometry does not depend on Dalvik heap semantics,
    // so a trivial id allocator is sufficient for this experiment.
    struct HarnessHeap : framework::HeapAllocator {
        uint32_t next = 1000;
        uint32_t allocate(const std::string&) override { return next++; }
        uint32_t get_singleton(const std::string&) override { return 0; }
        uint32_t get_or_create(const std::string& c) override { return allocate(c); }
        bool has_object(uint32_t) override { return true; }
    } harness_heap;
    framework::ShadowRegistry registry;
    registry.register_shadow<framework::ViewShadow>();
    registry.set_heap(&harness_heap);
    auto* views_p = registry.find_as<framework::ViewShadow>();
    resources::InflateStats stats;
    uint32_t root = rr.inflater().inflate_layout_by_name(views_p, layout_name, stats);
    if (!root) {
        printf("inflate FAIL: %s\n", stats.to_json().c_str());
        return 1;
    }  // R3: inflated via runtime ResourceRuntime stack
    rr.inflater().measure_layout(views_p, root);
    printf("inflated %s: %d elements\n", layout_name, stats.elements_total);

    // ---- Yoga adapter run --------------------------------------------------
    std::vector<YogaMap> ym;
    YGNodeRef yroot = build_yoga(views_p, root, ym);
    if (!yroot) { printf("yoga build FAIL\n"); return 1; }

    // Absolute-origin fixup: Yoga coords are parent-relative — run one
    // layout pass, then accumulate the ancestor chain per node.
    YGNodeCalculateLayout(yroot, pt(SCREEN_W), pt(SCREEN_H), YGDirectionLTR);
    std::map<uint32_t, std::pair<float,float>> rel;
    for (auto& m : ym)
        rel[m.view_id] = { YGNodeLayoutGetLeft(m.node), YGNodeLayoutGetTop(m.node) };
    std::map<uint32_t, std::pair<float,float>> absol;
    std::function<void(uint32_t,float,float)> accumulate = [&](uint32_t vid, float ax, float ay) {
        auto* n = views_p->find_node(vid);
        auto r = rel[vid];
        absol[vid] = { ax + r.first, ay + r.second };
        if (n) for (uint32_t c : n->children) accumulate(c, ax + r.first, ay + r.second);
    };
    accumulate(root, 0, 0);

    const int ITERS = 1000;
    auto t0 = std::chrono::steady_clock::now();
    for (int i = 0; i < ITERS; i++)
        YGNodeCalculateLayout(yroot, pt(SCREEN_W), pt(SCREEN_H), YGDirectionLTR);
    auto t1 = std::chrono::steady_clock::now();
    double yoga_ms = std::chrono::duration<double, std::milli>(t1 - t0).count() / ITERS;

    // ---- custom engine run (timed) ----------------------------------------
    auto t2 = std::chrono::steady_clock::now();
    for (int i = 0; i < ITERS; i++)
        rr.inflater().measure_layout(views_p, root);
    auto t3 = std::chrono::steady_clock::now();
    double custom_ms = std::chrono::duration<double, std::milli>(t3 - t2).count() / ITERS;

    // ---- compare ------------------------------------------------------------
    int compared = 0, agree = 0, close8 = 0;
    printf("\n%-5s %-30s %22s %14s %10s\n", "id", "class", "custom(x,y)", "yoga_px(x,y)", "d(x,y)");
    for (auto& m : ym) {
        auto* n = views_p->find_node(m.view_id);
        if (!n) continue;
        float yx = absol[m.view_id].first * DENSITY;
        float yy = absol[m.view_id].second * DENSITY;
        float dx = std::fabs(yx - (float)n->x), dy = std::fabs(yy - (float)n->y);
        compared++;
        if (dx < 1.5f && dy < 1.5f) agree++;
        if (dx < 8.0f && dy < 8.0f) close8++;
        if (compared <= 24)
            printf("%-5u %-30s %9d,%-9d %8.0f,%-5.0f %6.1f,%.1f\n",
                   m.view_id, n->class_desc.substr(0, 29).c_str(),
                   n->x, n->y, yx, yy, dx, dy);
    }
    printf("\nnodes compared: %d  exact-agree(<1.5px): %d (%.1f%%)  agree(<8px): %d (%.1f%%)\n",
           compared, agree, compared ? 100.0 * agree / compared : 0,
           close8, compared ? 100.0 * close8 / compared : 0);
    printf("layout speed (%d iters): yoga %.4f ms/pass, custom %.4f ms/pass (%.2fx)\n",
           ITERS, yoga_ms, custom_ms, custom_ms / yoga_ms);
    return 0;
}
