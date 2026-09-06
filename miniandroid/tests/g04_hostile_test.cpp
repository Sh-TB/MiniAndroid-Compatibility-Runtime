// g04_hostile_test — G04/G05 §16 hostile-input safety battery.
//
// Law: no hostile input may cause uncontrolled allocation, OOB access,
// crash, infinite loop, unbounded recursion, or silent state corruption.
// The drawable/image/layout layer must fail deterministically (named
// resolution errors, ok=false decoders, bounded geometry).
//
// Time-bound: run under `timeout` in the battery (any hang = failure).

#include "../src/resources/layout_inflater.h"
#include "../src/resources/arsc_parser.h"
#include "../src/apk/apk_parser.h"
#include "../src/renderer/software_renderer.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"
#include "synthetic_arsc.h"

#include <cstdio>
#include <cstring>
#include <chrono>
#include <vector>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
    else      printf("  PASS: %s\n", what.c_str());
}

static std::vector<uint8_t> make_png(uint32_t w, uint32_t h, size_t extra_rows) {
    // minimal PNG: signature + IHDR with attacker-controlled dims; no IDAT
    // rows beyond `extra_rows` bytes (hostile truncation).
    std::vector<uint8_t> d = {0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A};
    auto push32 = [&](uint32_t v) { d.push_back(v>>24); d.push_back(v>>16); d.push_back(v>>8); d.push_back(v); };
    auto push_crc = [&]() { uint32_t c = 0; push32(c); };   // CRC not probed header-only
    push32(13); d.insert(d.end(), {'I','H','D','R'});
    push32(w); push32(h);
    d.push_back(8); d.push_back(2); d.push_back(0); d.push_back(0); d.push_back(0);
    push_crc();
    // truncated IDAT with `extra_rows` bytes (0 = absent)
    if (extra_rows) {
        push32((uint32_t)extra_rows); d.insert(d.end(), {'I','D','A','T'});
        for (size_t i = 0; i < extra_rows; i++) d.push_back(0x55);
    }
    return d;
}

int main() {
    printf("== G04/G05 §16: hostile drawable/image/layout safety ==\n");

    // ── 1. header probe must reject hostile images without crashing ────────
    printf("[1] probe_image_size hostile boundaries\n");
    {
        renderer::ImageSizeProbe p;
        std::vector<uint8_t> sig_only = {0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A};
        check(!renderer::probe_image_size(sig_only, &p), "PNG signature-only rejected");
        std::vector<uint8_t> huge = make_png(0xFFFFFFFF, 0xFFFFFFFF, 0);
        check(!renderer::probe_image_size(huge, &p) || p.width > 0,
              "0xFFFFFFFF dims do not crash probe (declared dims bounded by int)");
        std::vector<uint8_t> zero = make_png(0, 0, 0);
        check(!renderer::probe_image_size(zero, &p), "0x0 dims rejected");
        std::vector<uint8_t> webp_trunc = {'R','I','F','F',0,0,0,0,'W','E','B','P','V','P','8','X'};
        check(!renderer::probe_image_size(webp_trunc, &p), "truncated WebP header rejected");
        std::vector<uint8_t> jpeg_garbage = {0xFF,0xD8,0xFF,0x00,0x01,0x02};
        check(!renderer::probe_image_size(jpeg_garbage, &p), "garbage JPEG rejected");
        std::vector<uint8_t> empty;
        check(!renderer::probe_image_size(empty, &p), "empty buffer rejected");
    }

    // ── 2. PNGDecoder must fail safely on truncated payload ────────────────
    printf("[2] PNGDecoder fail-safe boundaries\n");
    {
        auto huge = make_png(60000, 60000, 100);   // 14 GB request, 100 B data
        auto t0 = std::chrono::steady_clock::now();
        auto r = renderer::PNGDecoder::decode(huge);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                      std::chrono::steady_clock::now() - t0).count();
        check(!r.ok && r.rgba.empty(), "declared 60000x60000 + 100B payload → ok=false");
        check(ms < 5000, "decode attempt bounded (" + std::to_string(ms) + " ms)");
        auto trunc = make_png(8, 8, 10);
        auto r2 = renderer::PNGDecoder::decode(trunc);
        check(!r2.ok, "truncated IDAT → ok=false (no OOB)");
    }

    // ── 3. fit_center_rect degenerate inputs ───────────────────────────────
    printf("[3] fit_center_rect degenerate inputs\n");
    {
        auto z = renderer::fit_center_rect(0, 10, 0, 0, 100, 100);
        check(z.w == 0 && z.h == 0, "zero src → empty rect");
        auto z2 = renderer::fit_center_rect(10, 10, 0, 0, 0, 0);
        check(z2.w == 0 && z2.h == 0, "zero box → empty rect");
        auto n = renderer::fit_center_rect(-5, 10, 0, 0, 100, 100);
        check(n.w == 0 && n.h == 0, "negative src → empty rect");
        auto big = renderer::fit_center_rect(1, 1, 0, 0, 2000000000, 2000000000);
        check(big.w > 0 && big.w <= 2000000000, "extreme upscale stays in int range");
    }

    // ── 4. resolver hostile chains (named errors, bounded) ─────────────────
    printf("[4] resolver hostile reference chains\n");
    {
        using namespace synthetic_arsc;
        const uint32_t A = 0x7f010000, B = 0x7f010001;
        std::vector<TypeVariant> vars;
        // cycle: A → B → A ; dangling: C → 0x7f010999
        vars.push_back({1, "drawable", 0, {
            {"a", false, 0, 0x01, B},                  // REFERENCE → B
            {"b", false, 0, 0x01, A},                  // REFERENCE → A (cycle)
            {"c", false, 0, 0x01, 0x7f010999},         // dangling target
            {"self", false, 0, 0x01, A},               // self-cycle via alias? A→B→A covers
        }});
        auto table = build({}, vars);
        resources::ArscParser arsc;
        check(arsc.parse(table), "hostile table parses (structure legal)");
        const resources::ResTableConfig dev;
        auto rc = arsc.resolve_full(A, dev);
        check(rc.error == resources::ResolutionError::CYCLE && !rc.ok,
              "A→B→A → named CYCLE error");
        auto rd = arsc.resolve_full(0x7f010002, dev);
        check(rd.error == resources::ResolutionError::MISSING_REFERENCE_TARGET && !rd.ok,
              "dangling reference → named MISSING_REFERENCE_TARGET");
        auto ri = arsc.resolve_full(0x00010000, dev);
        check(!ri.ok && ri.error == resources::ResolutionError::INVALID_ID,
              "package byte 0 → named INVALID_ID");
        // 20-hop chain (depth cap 16)
        std::vector<TypeVariant> chain_var;
        std::vector<EntrySpec> entries;
        for (int i = 0; i < 20; i++) {
            EntrySpec e; e.name = "n" + std::to_string(i);
            e.value_type = 0x01;
            e.value_data = i < 19 ? 0x7f010000 + (uint32_t)i + 1 : 0x7f020000;
            entries.push_back(e);
        }
        std::vector<TypeVariant> v2 = {{1, "drawable", 0, entries},
                                       {2, "layout", 0, {{"terminal", false, 0, 0x03, 0, 0}}}};
        auto t2 = build({}, v2);
        resources::ArscParser a2;
        a2.parse(t2);
        auto r20 = a2.resolve_full(0x7f010000, dev);
        check(!r20.ok && r20.error == resources::ResolutionError::DEPTH_EXCEEDED,
              "20-hop chain → bounded DEPTH_EXCEEDED (cap 16)");
        // select_file on a cycle must return nullopt (no hang)
        auto sel = arsc.select_file(A, {"res/x.png"}, dev);
        check(!sel.has_value(), "select_file on cycle → nullopt (no hang)");
    }

    // ── 5. pathological layout depth (cap 100) ─────────────────────────────
    printf("[5] pathological layout depth\n");
    {
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter ha(&heap);
        framework::ViewShadow views; views.init(&ha);
        resources::ArscParser arsc; apk::ApkParser apk;
        resources::LayoutInflater inflater(arsc, apk, "", resources::DeviceMetrics{});
        uint32_t prev = 0, root = 0;
        for (int i = 0; i < 150; i++) {           // > 100 → depth cap must fire
            uint32_t id = views.create_view("Landroid/widget/LinearLayout;");
            auto* n = views.find_node(id);
            n->lp_width = -1; n->lp_height = -1;
            if (prev) views.add_child(prev, id); else root = id;
            prev = id;
        }
        bool threw = false;
        try { inflater.measure_layout(&views, root); }
        catch (...) { threw = true; }
        check(!threw, "150-deep tree measured without crash (depth cap 100 logs)");
    }

    // ── 6. excessive child count (bounded time) ────────────────────────────
    printf("[6] excessive child count\n");
    {
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter ha(&heap);
        framework::ViewShadow views; views.init(&ha);
        resources::ArscParser arsc; apk::ApkParser apk;
        resources::LayoutInflater inflater(arsc, apk, "", resources::DeviceMetrics{});
        uint32_t root = views.create_view("Landroid/widget/LinearLayout;");
        auto* rn = views.find_node(root);
        rn->lp_width = -1; rn->lp_height = -1; rn->orientation = 1;
        for (int i = 0; i < 10000; i++) {
            uint32_t id = views.create_view("Landroid/view/View;");
            auto* n = views.find_node(id);
            n->lp_width = -1; n->lp_height = -2;
            views.add_child(root, id);
        }
        auto t0 = std::chrono::steady_clock::now();
        inflater.measure_layout(&views, root);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                      std::chrono::steady_clock::now() - t0).count();
        check(ms < 5000, "10000-child measure bounded (" + std::to_string(ms) + " ms)");
    }

    // ── 7. invalid weight values (no overflow/hang) ────────────────────────
    printf("[7] invalid weight values\n");
    {
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter ha(&heap);
        framework::ViewShadow views; views.init(&ha);
        resources::ArscParser arsc; apk::ApkParser apk;
        resources::LayoutInflater inflater(arsc, apk, "", resources::DeviceMetrics{});
        uint32_t root = views.create_view("Landroid/widget/LinearLayout;");
        auto* rn = views.find_node(root);
        rn->lp_width = -1; rn->lp_height = -1; rn->orientation = 1;
        uint32_t a = views.create_view("Landroid/view/View;");
        views.find_node(a)->lp_width = -1; views.find_node(a)->lp_height = 0;
        views.find_node(a)->layout_weight = -5000;          // NEGATIVE weight
        views.add_child(root, a);
        uint32_t b = views.create_view("Landroid/view/View;");
        auto* bn = views.find_node(b);
        bn->lp_width = -1; bn->lp_height = 0;
        bn->layout_weight = 2000000000;                     // huge weight (milli)
        views.add_child(root, b);
        inflater.measure_layout(&views, root);
        check(rn->measured_height == 1920 && bn->measured_height >= 0,
              "negative + huge weights → finite, non-negative geometry");
    }

    // ── 8. unknown lp sentinel + missing drawable fallback ─────────────────
    printf("[8] unknown lp sentinel + missing drawable fallback\n");
    {
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter ha(&heap);
        framework::ViewShadow views; views.init(&ha);
        resources::ArscParser arsc; apk::ApkParser apk;
        resources::LayoutInflater inflater(arsc, apk, "", resources::DeviceMetrics{});
        uint32_t root = views.create_view("Landroid/widget/LinearLayout;");
        auto* rn = views.find_node(root);
        rn->lp_width = -1; rn->lp_height = -1; rn->orientation = 0;
        uint32_t odd = views.create_view("Landroid/view/View;");
        views.find_node(odd)->lp_width = -3;                // unknown sentinel
        views.find_node(odd)->lp_height = -3;
        views.add_child(root, odd);
        inflater.measure_layout(&views, root);
        auto* on = views.find_node(odd);
        check(on->measured_width == 0,
              "unknown sentinel behaves as wrap (empty leaf → 0, no spec leak)");
        // ImageView with a nonexistent drawable id: intrinsic fails, 48dp
        // fallback applies (AOSP unresolvable-drawable law).
        uint32_t img = views.create_view("Landroid/widget/ImageView;");
        views.find_node(img)->lp_width = -2; views.find_node(img)->lp_height = -2;
        views.find_node(img)->image_resource_id = 0x7f019999;   // absent id
        views.add_child(root, img);
        inflater.measure_layout(&views, root);
        auto* im = views.find_node(img);
        int fw = (int)std::lround(48 * 2.625f);
        check(im->measured_width == fw,
              "missing drawable → 48dp fallback (" + std::to_string(fw) + "px)");
    }

    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    return g_fail == 0 ? 0 : 1;
}
