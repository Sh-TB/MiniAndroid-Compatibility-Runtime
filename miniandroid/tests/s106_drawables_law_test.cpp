// s106_drawables_law_test.cpp — S106 drawable-family micro-gap fence.
// Drives the REAL engine objects (ApkParser + ArscParser + ResourceRuntime +
// LayoutInflater + vector_decode) against a REAL aapt2-built fixture APK
// (tests/fixtures/s106_drawables). Asserts AOSP upstream laws from decoded
// pixels / parsed state:
//
//   V1  (MG-002 viewport mapping)   — viewport units map by raster/vp scale.
//   V2  (MG-003 fillType evenOdd)   — overlapping contours punch a hole.
//   V3  (MG-004 winding nonzero)    — nonzero fills regardless of winding dir.
//   V4  (MG-005 strokeWidth)        — stroke ink widens with strokeWidth.
//   V5  (MG-009/010 pivot+rotation) — rotation about pivot 0,0 vs 12,12 is a
//                                     pure translation by the pivot delta.
//   V6  (MG-011 group scale)        — scaleX/Y 2 doubles the ink bbox.
//   V7  (MG-012 group translation)  — translateX/Y shifts ink by exact px.
//   V8  (MG-013 nested transforms)  — outer translate ∘ inner rotate compose.
//   V9  (MG-014 group alpha)        — android:alpha=0.25 quarter-fills ink.
//   L1  (MG-016 layer ordering)     — items parse in document order.
//   L2  (MG-017 layer inset)        — left/top insets land as px offsets.
//   S1  (MG-020 state selected)     — selected=true picks the selected item.
//   S2  (MG-021 state disabled)     — enabled=false picks the disabled item.
//   S3  (MG-022 state checked)      — checked=true picks the checked item
//                                     (S106 state_checked API extension).
//   S4  (MG-023 fallback)           — no state match -> wildcard last item.
//   S5  (first-match law)           — earlier items win over later wildcards.
//   A1  (MG-047 adaptive bg)        — background color fills the canvas.
//   A2  (MG-048 adaptive fg)        — foreground vector draws OVER background.
//   M1  (MG-046 mipmap indirection) — @mipmap/ic_wrapper id resolves through
//                                     the XML to the wrapped drawable ref.
//
// Exit 0 iff ALL laws hold. Usage: s106_drawables_law_test <fixture.apk>

#include "../src/apk/apk_parser.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/state_list.h"
#include "../src/renderer/gif_decoder.h"
#include "../src/renderer/software_renderer.h"
#include "../src/renderer/vector_decode.h"
#include "../src/resources/arsc_parser.h"
#include "../src/resources/layout_inflater.h"
#include "../src/resources/resource_runtime.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void check(const char* name, bool ok, const std::string& detail = "") {
    if (ok) { ++g_pass; std::printf("PASS %s %s\n", name, detail.c_str()); }
    else { ++g_fail; std::printf("FAIL %s %s\n", name, detail.c_str()); }
}

static std::string g_apk;

static std::vector<uint8_t> entry(const std::string& path) {
    apk::ApkParser p;
    return p.extract_entry(g_apk, path);
}

struct Ink { int minx, miny, maxx, maxy; long count; };

static Ink ink_bbox(const renderer::DecodedImage& img) {
    Ink b{img.width, img.height, -1, -1, 0};
    for (int y = 0; y < img.height; ++y)
        for (int x = 0; x < img.width; ++x) {
            const uint8_t a = img.rgba[((size_t)y * img.width + x) * 4 + 3];
            if (a > 24) {
                b.count++;
                b.minx = std::min(b.minx, x); b.maxx = std::max(b.maxx, x);
                b.miny = std::min(b.miny, y); b.maxy = std::max(b.maxy, y);
            }
        }
    return b;
}

static renderer::DecodedImage decode_xml(const std::string& path) {
    auto bytes = entry(path);
    renderer::DecodedImage img;
    if (bytes.empty()) { img.error = "entry missing: " + path; return img; }
    decode_vector_drawable(bytes, 160, &img);
    return img;
}

int main(int argc, char** argv) {
    if (argc < 2) { std::printf("usage: %s <fixture.apk>\n", argv[0]); return 2; }
    g_apk = argv[1];

    // ── V1 (MG-002): viewport mapping ────────────────────────────────────
    {
        auto a = decode_xml("res/drawable/vec_viewport24.xml");  // scale 2
        auto b = decode_xml("res/drawable/vec_viewport48.xml");  // scale 1
        check("V1 mg-002 viewport24 decode", a.ok, a.error);
        check("V1 mg-002 viewport48 decode", b.ok, b.error);
        auto ia = ink_bbox(a), ib = ink_bbox(b);
        bool law = a.ok && b.ok &&
                   std::abs(ia.minx - 12) <= 2 && std::abs(ia.maxx - 35) <= 2 &&
                   std::abs(ib.minx - 6) <= 2 && std::abs(ib.maxx - 17) <= 2;
        check("V1 mg-002 viewport px mapping (24u@2x vs 48u@1x)", law,
              "a[" + std::to_string(ia.minx) + ".." + std::to_string(ia.maxx) +
              "] b[" + std::to_string(ib.minx) + ".." + std::to_string(ib.maxx) + "]");
    }
    // ── V2/V3 (MG-003/004): fillType + winding ───────────────────────────
    {
        auto eo = decode_xml("res/drawable/vec_evenodd.xml");
        auto nz = decode_xml("res/drawable/vec_nonzero.xml");
        auto cc = decode_xml("res/drawable/vec_winding_ccw.xml");
        check("V2 mg-003 evenodd decode", eo.ok, eo.error);
        check("V3 mg-004 nonzero decode", nz.ok, nz.error);
        auto px = [](const renderer::DecodedImage& i, int x, int y) {
            return i.rgba[((size_t)y * i.width + x) * 4 + 3];
        };
        // fill 4..20, inner 8..16 (viewport 24, scale 2): outer (5,5)->(10,10);
        // center (12,12)->(24,24)
        bool hole = eo.ok && px(eo, 24, 24) <= 24 && px(eo, 10, 10) > 200;
        check("V2 mg-003 evenOdd punches hole", hole,
              "center=" + std::to_string(px(eo, 24, 24)));
        bool filled = nz.ok && px(nz, 24, 24) > 200 && px(nz, 10, 10) > 200;
        check("V3 mg-004 nonzero fills intersection", filled,
              "center=" + std::to_string(px(nz, 24, 24)));
        bool winding_dir = cc.ok && px(cc, 24, 24) > 200;
        check("V3 mg-004 nonzero winding-direction-insensitive", winding_dir,
              "center=" + std::to_string(px(cc, 24, 24)));
    }
    // ── V4 (MG-005): stroke width ────────────────────────────────────────
    {
        auto s1 = decode_xml("res/drawable/vec_stroke1.xml");
        auto s6 = decode_xml("res/drawable/vec_stroke6.xml");
        check("V4 mg-005 stroke decode", s1.ok && s6.ok, s1.error + s6.error);
        auto i1 = ink_bbox(s1), i6 = ink_bbox(s6);
        check("V4 mg-005 stroke ink widens", i6.count > i1.count * 2,
              "sw1=" + std::to_string(i1.count) + " sw6=" + std::to_string(i6.count));
    }
    // ── V5 (MG-009/010): pivot + rotation ────────────────────────────────
    {
        // Scale-2 about pivot (0,0) vs (12,12) on the same square: the two
        // results differ by exactly Δpivot·(s−1)·scale_px = 12·1·2 = 24 px
        // (AOSP VGroup pivot law — pivot-relative transform composition).
        auto s0 = decode_xml("res/drawable/vec_pivot_scale0.xml");
        auto s12 = decode_xml("res/drawable/vec_pivot_scale12.xml");
        check("V5 mg-009 pivot decode", s0.ok && s12.ok, s0.error + s12.error);
        auto b0 = ink_bbox(s0), b12 = ink_bbox(s12);
        bool law = std::abs((b12.minx - b0.minx) + 24) <= 3 &&
                   std::abs((b12.miny - b0.miny) + 24) <= 3;
        check("V5 mg-009 pivot translation law", law,
              "d=(" + std::to_string(b12.minx - b0.minx) + "," +
              std::to_string(b12.miny - b0.miny) + ") expect (-24,-24)");
        // MG-010 rotation: rot90 about (12,12) maps (x,y)->(24-y, x):
        // triangle (8,8),(18,8),(8,18) -> vp bbox x 6..16, y 8..18
        auto r = decode_xml("res/drawable/vec_rot90.xml");
        check("V5 mg-010 rotation decode", r.ok, r.error);
        auto br = ink_bbox(r);
        bool rot = std::abs(br.minx - 12) <= 3 && std::abs(br.maxx - 31) <= 3 &&
                   std::abs(br.miny - 16) <= 3;
        check("V5 mg-010 rot90 exact mapping", rot,
              "[" + std::to_string(br.minx) + ".." + std::to_string(br.maxx) +
              "," + std::to_string(br.miny) + "]");
    }
    // ── V6 (MG-011): scale ───────────────────────────────────────────────
    {
        auto s = decode_xml("res/drawable/vec_scale.xml");
        check("V6 mg-011 scale decode", s.ok, s.error);
        auto b = ink_bbox(s);
        // 2..8 square scaled 2x from (0,0), scale 2 px/u: expect 8..32 px
        bool law = std::abs(b.minx - 8) <= 2 && std::abs(b.maxx - 31) <= 3;
        check("V6 mg-011 scale 2x doubles bbox", law,
              "[" + std::to_string(b.minx) + ".." + std::to_string(b.maxx) + "]");
    }
    // ── V7 (MG-012): translation ─────────────────────────────────────────
    {
        auto s = decode_xml("res/drawable/vec_translate.xml");
        check("V7 mg-012 translate decode", s.ok, s.error);
        auto b = ink_bbox(s);
        // 2..8 + translate(6,3): vp 8..14, 5..11 -> px 16..28, 10..22
        bool law = std::abs(b.minx - 16) <= 2 && std::abs(b.maxx - 27) <= 3 &&
                   std::abs(b.miny - 10) <= 2;
        check("V7 mg-012 translate exact shift", law,
              "[" + std::to_string(b.minx) + ".." + std::to_string(b.maxx) + "," +
              std::to_string(b.miny) + "]");
    }
    // ── V8 (MG-013): nested composition ──────────────────────────────────
    {
        auto s = decode_xml("res/drawable/vec_nested.xml");
        check("V8 mg-013 nested decode", s.ok, s.error);
        auto b = ink_bbox(s);
        // translate(10,0) ∘ rot90(0,0) on triangle: lands at vp x 2..8,
        // y 2..8 -> px 4..16 (a non-composed path would sit at px 24+)
        bool law = b.maxx <= 20 && b.minx >= 2 && b.miny >= 2;
        check("V8 mg-013 nested composition order", law,
              "[" + std::to_string(b.minx) + ".." + std::to_string(b.maxx) + "]");
    }
    // ── V9 (MG-014): group alpha inheritance ─────────────────────────────
    {
        auto a = decode_xml("res/drawable/vec_group_alpha.xml");
        auto f = decode_xml("res/drawable/vec_alpha_full.xml");
        check("V9 mg-014 alpha decode", a.ok && f.ok, a.error + f.error);
        auto px = [](const renderer::DecodedImage& i, int x, int y) {
            return i.rgba[((size_t)y * i.width + x) * 4 + 3];
        };
        int fa = px(a, 24, 24), ff = px(f, 24, 24);
        bool law = ff == 255 && fa >= 50 && fa <= 75;  // 0.25 * 255 ≈ 64
        check("V9 mg-014 group alpha 0.25 inherited", law,
              "alpha=" + std::to_string(fa) + " (full=" + std::to_string(ff) + ")");
    }
    // ── L1/L2 (MG-016/017): layer-list ordering + inset ──────────────────
    {
        auto& rt = resources::ResourceRuntime::instance();
        check("L0 runtime loaded", rt.ensure_loaded(g_apk), "ensure_loaded");
        framework::ViewShadow::ViewNode node;
        resources::InflateStats stats;
        rt.inflater().apply_layer_list_background(
            node, "res/drawable/layers_order.xml", stats);
        bool two = node.bg_layers_valid && node.bg_layers.size() == 2;
        check("L1 mg-016 layer items in doc order", two,
              "n=" + std::to_string(node.bg_layers.size()));
        bool colors = two && node.bg_layers[0].kind == 2 &&
                      node.bg_layers[0].shape_solid == 0xFFFF0000 &&
                      node.bg_layers[1].shape_solid == 0xFF00FF00;
        check("L1 mg-016 layer colors preserved", colors, "");
        framework::ViewShadow::ViewNode node2;
        rt.inflater().apply_layer_list_background(
            node2, "res/drawable/layers_inset.xml", stats);
        // inset 12dp × density 2.625 = 31.5 px (rounds to 31/32)
        int exp = (int)(12.f * rt.inflater().metrics().density);
        bool inset = node2.bg_layers_valid && node2.bg_layers.size() == 1 &&
                     std::abs(node2.bg_layers[0].left - exp) <= 1 &&
                     std::abs(node2.bg_layers[0].top - exp) <= 1;
        check("L2 mg-017 layer inset px law", inset,
              "left=" + std::to_string(node2.bg_layers[0].left) +
              " expect " + std::to_string(exp));
    }
    // ── S1..S5 (MG-020..023): state-list laws ────────────────────────────
    {
        auto bytes = entry("res/drawable/sel_states.xml");
        std::vector<framework::ViewShadow::ViewNode::BgStateItem> items;
        bool parsed = framework::parse_state_list(bytes, &items);
        check("S0 selector parsed", parsed && items.size() == 5,
              "n=" + std::to_string(items.size()));
        uint32_t c = 0; std::string p;
        bool sel = framework::pick_state_list(items, false, true, true, &c, &p) &&
                   c == 0xFF101010;   // state_selected
        check("S1 mg-020 selected state", sel, "");
        bool dis = framework::pick_state_list(items, false, false, false, &c, &p) &&
                   c == 0xFF404040;   // state_enabled=false
        check("S2 mg-021 disabled state", dis, "");
        bool chk = framework::pick_state_list(items, false, true, false, &c, &p,
                                              /*checked=*/true) &&
                   c == 0xFF202020;   // state_checked (S106 API)
        check("S3 mg-022 checked state", chk, "");
        bool fb = framework::pick_state_list(items, false, true, false, &c, &p,
                                             /*checked=*/false) &&
                  c == 0xFF505050;    // wildcard last item
        check("S4 mg-023 wildcard fallback", fb, "");
        // first-match: pressed matches item 3 even though checked(2) is
        // wildcard-free? item1 selected requires selected -> skip; item2
        // checked requires checked -> skip; item3 pressed wins.
        bool fm = framework::pick_state_list(items, true, true, false, &c, &p,
                                             false) &&
                  c == 0xFF303030;
        check("S5 first-match document order", fm, "");
    }
    // ── A1/A2 (MG-047/048): adaptive icon layers ─────────────────────────
    {
        auto& rt = resources::ResourceRuntime::instance();
        rt.ensure_loaded(g_apk);
        auto entries = apk::ApkParser().list_entries(g_apk);
        std::vector<std::string> names;
        for (const auto& e : entries) names.push_back(e.name);
        renderer::VectorRefResolver resolver =
            [&rt, &names](uint32_t resid,
                          renderer::VectorImageRef* out) -> bool {
            auto val = rt.arsc().resolve_value(resid);
            if (val && (val->is_color() || val->is_int())) {
                out->resolved = true; out->is_color = true; out->argb = val->data;
                return true;
            }
            auto sel = rt.arsc().select_file(resid, names,
                                             resources::device_config());
            if (!sel) return false;
            out->resolved = true; out->is_color = false; out->path = sel->path;
            out->bytes = apk::ApkParser().extract_entry(g_apk, sel->path);
            return !out->bytes.empty();
        };
        auto bytes = entry("res/mipmap-anydpi-v26/ic_adaptive.xml");
        renderer::DecodedImage img;
        bool ok = renderer::decode_vector_drawable(bytes, 160, &img, &resolver);
        check("A0 adaptive decode", ok && img.ok, img.error);
        auto px = [&](int x, int y) {
            const uint8_t* q = &img.rgba[((size_t)y * img.width + x) * 4];
            return std::make_tuple(q[0], q[1], q[2], q[3]);
        };
        auto [r1, g1, b1, a1] = px(4, img.height / 2);       // bg-only zone
        check("A1 mg-047 background color fills", a1 > 0 && b1 > r1 && b1 > g1,
              "rgb=" + std::to_string(r1) + "," + std::to_string(g1) + "," +
              std::to_string(b1));
        // foreground vector (white square 8..16 vp) sits over the bg: find
        // white-ish pixels (r≈g≈b, high) — proves the fg layer drew.
        bool white = false;
        for (int y = 0; y < img.height && !white; ++y)
            for (int x = 0; x < img.width && !white; ++x) {
                auto [r, g, b, a] = px(x, y);
                if (a == 255 && r > 240 && g > 240 && b > 240) white = true;
            }
        check("A2 mg-048 foreground over background", white, "");
    }
    // ── M1 (MG-046): mipmap XML indirection ──────────────────────────────
    {
        auto& rt = resources::ResourceRuntime::instance();
        rt.ensure_loaded(g_apk);
        auto id = rt.arsc().find_id("com.miniandroid.s106drawables", "mipmap",
                                    "ic_wrapper");
        check("M1 mg-046 mipmap id found", id.has_value(), "");
        if (id) {
            auto res = rt.arsc().resolve_full(*id, resources::device_config());
            const resources::ResValue* v = res.value();
            // The entry's value chain must land on the drawable XML file
            // (the <bitmap android:src="@drawable/vec_alpha_full"> wrapper).
            bool chain = res.ok && v && !v->string_value.empty() &&
                         v->string_value.find("ic_wrapper") != std::string::npos;
            check("M1 mg-046 mipmap resolves to xml", chain,
                  "val=" + (v ? v->string_value : std::string("<null>")));
            auto bytes = v ? entry(v->string_value) : std::vector<uint8_t>{};
            resources::AxmlParser p;
            bool is_xml = !bytes.empty() && p.parse(bytes) && p.valid();
            check("M1 mg-046 wrapper parses as AXML", is_xml, "");
            // The indirection target: a drawable reference inside the XML
            bool ref_found = false;
            std::function<void(const resources::AxmlElement&)> walk =
                [&](const resources::AxmlElement& el) {
                    for (const auto& at : el.attributes)
                        if (at.value.is_reference()) ref_found = true;
                    for (const auto& ch : el.children) walk(ch);
                };
            if (is_xml) walk(p.root());
            check("M1 mg-046 xml carries drawable reference", ref_found, "");
        }
    }

    std::printf("s106 drawables laws %s %d/%d\n",
                g_fail == 0 ? "PASS" : "FAIL", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
