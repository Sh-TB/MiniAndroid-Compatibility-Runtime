/*
 * resource_trace — GOLDEN-03 §12 (recreated, FIND-G04-AUDIT-001) + G04/G05
 * §18 extension: the evidence tool for the resource→pixel pipeline.
 *
 * Channel map (each stage of the campaign's canonical pipeline):
 *   resource ID
 *   → package/type/entry decomposition            (ResId law)
 *   → requested device config                     (device_config law)
 *   → selected config per reference-chain step    (resolve_full/isBetterThan)
 *   → alias/reference chain                       (bounded, cycle-safe)
 *   → typed value (type/data/raw semantics)       (TypedValue law)
 *   → drawable/file/XML classification            (value-IS-path law)
 *   → density: selected density → target density → scaled intrinsic dims
 *                                                (BitmapFactory law)
 *   → layout attribute consumption + measure + bounds
 *       (--layout: inflates the layout and reports the measured geometry of
 *        every view, incl. per-node selected drawable + intrinsic size)
 *
 * The tool prints ONLY what the canonical resolver produces — no fixture
 * knowledge, no sidecars. Exit codes: 0 ok, 1 resolution failure,
 * 2 usage error.
 *
 * Usage:
 *   resource_trace <apk> <resid-hex|package:type/name> [options]
 * Options:
 *   --json <file>     write full JSON evidence
 *   --bag <attr-hex>  dump a style/bag entry's ResTable_map items (G03 §8)
 *   --density <dpi>   override device density (default 420)
 *   --locale <l[-c]>  override locale (default en-US)
 *   --sdk <v>         override sdkVersion (default 34)
 *   --layout          for layout ids: inflate + measure + dump view geometry
 */
#include "resources/arsc_parser.h"
#include "resources/res_config.h"
#include "resources/layout_inflater.h"
#include "resources/resource_runtime.h"
#include "apk/apk_parser.h"
#include "renderer/software_renderer.h"
#include "framework/android_shadows.h"
#include "framework/heap_adapter.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <iostream>
#include <fstream>
#include <sstream>

using namespace miniandroid;
using resources::ArscParser;
using resources::ResolutionResult;
using resources::ResTableConfig;
using resources::ResValue;

static std::string hex32(uint32_t v) {
    char b[16];
    snprintf(b, sizeof b, "0x%08x", v);
    return b;
}

static std::string json_escape(const std::string& s) {
    std::string o;
    for (char c : s) {
        if (c == '"' || c == '\\') { o += '\\'; o += c; }
        else if (c == '\n') o += "\\n";
        else if (c < 0x20) { char b[8]; snprintf(b, sizeof b, "\\u%04x", c); o += b; }
        else o += c;
    }
    return o;
}

struct Options {
    std::string apk, ref, bag_attr, json_out;
    bool layout_mode = false;
    int density = 0, sdk = 0;
    std::string locale;
};

static bool parse_args(int argc, char** argv, Options* o) {
    if (argc < 3) return false;
    o->apk = argv[1];
    o->ref = argv[2];
    for (int i = 3; i < argc; i++) {
        std::string a = argv[i];
        auto val = [&](void) -> const char* { return i + 1 < argc ? argv[++i] : nullptr; };
        if (a == "--json") { const char* v = val(); if (!v) return false; o->json_out = v; }
        else if (a == "--bag") { const char* v = val(); if (!v) return false; o->bag_attr = v; }
        else if (a == "--density") { const char* v = val(); if (!v) return false; o->density = atoi(v); }
        else if (a == "--sdk") { const char* v = val(); if (!v) return false; o->sdk = atoi(v); }
        else if (a == "--locale") { const char* v = val(); if (!v) return false; o->locale = v; }
        else if (a == "--layout") o->layout_mode = true;
        else return false;
    }
    return true;
}

// device_config() is a global singleton fed by env vars; the tool applies
// explicit overrides through the same env channel so ONE device definition
// serves both the tool and the runtime (single-device law).
static void apply_device_overrides(const Options& o) {
    if (o.density > 0) setenv("MINIANDROID_DENSITY", std::to_string(o.density).c_str(), 1);
    if (o.sdk > 0) setenv("MINIANDROID_SDK", std::to_string(o.sdk).c_str(), 1);
    if (!o.locale.empty()) setenv("MINIANDROID_LOCALE", o.locale.c_str(), 1);
    if (o.sdk > 0) {
        // MINIANDROID_SDK feeds the device's sdkVersion when supported by the
        // config builder; unknown env names are ignored upstream (honest).
        setenv("MINIANDROID_SDKVERSION", std::to_string(o.sdk).c_str(), 1);
    }
}

int main(int argc, char** argv) {
    Options opt;
    if (!parse_args(argc, argv, &opt)) {
        fprintf(stderr,
                "usage: resource_trace <apk> <0xRRttteeee|package:type/name>\n"
                "       [--json FILE] [--bag ATTR_HEX] [--density DPI] [--sdk V]\n"
                "       [--locale l[-c]] [--layout]\n");
        return 2;
    }
    apply_device_overrides(opt);

    apk::ApkParser apk;
    auto info = apk.parse(opt.apk);
    if (!info.is_valid) {
        fprintf(stderr, "apk parse failed: %s\n", opt.apk.c_str());
        return 2;
    }
    std::vector<uint8_t> arsc_data = apk.extract_entry_cached("resources.arsc");
    ArscParser arsc;
    if (arsc_data.empty() || !arsc.parse(arsc_data)) {
        fprintf(stderr, "resources.arsc missing or unparseable: %s\n",
                arsc.last_error().c_str());
        return 2;
    }

    // ── resolve the request to a resource id ────────────────────────────────
    uint32_t resid = 0;
    std::string kind_note;
    if (opt.ref.rfind("0x", 0) == 0 || opt.ref.rfind("0X", 0) == 0) {
        resid = (uint32_t)strtoul(opt.ref.c_str(), nullptr, 16);
    } else {
        // package:type/name — find in the named package (or first match)
        size_t c1 = opt.ref.find(':'), c2 = opt.ref.find('/');
        if (c1 == std::string::npos || c2 == std::string::npos || c2 < c1) {
            fprintf(stderr, "bad reference form: %s\n", opt.ref.c_str());
            return 2;
        }
        std::string pkg = opt.ref.substr(0, c1);
        std::string type = opt.ref.substr(c1 + 1, c2 - c1 - 1);
        std::string name = opt.ref.substr(c2 + 1);
        auto id = arsc.find_id(pkg, type, name);
        if (!id && !pkg.empty()) id = arsc.find_id("", type, name);  // any-package
        if (!id) {
            fprintf(stderr, "not found in ARSC: %s\n", opt.ref.c_str());
            return 1;
        }
        resid = *id;
        kind_note = "by-name";
    }

    const ResTableConfig& device = resources::device_config();
    std::vector<std::string> paths;
    for (const auto& e : info.all_entries) paths.push_back(e);

    // ── canonical resolution ────────────────────────────────────────────────
    ResolutionResult rr = arsc.resolve_full(resid, device);
    const resources::ResolutionStep* term = rr.terminal();

    printf("== resource_trace ==\n");
    printf("apk: %s\n", opt.apk.c_str());
    printf("request: %s%s\n", hex32(resid).c_str(),
           kind_note.empty() ? "" : " (by name)");
    printf("device: density=%u dpi sdk=%u locale=%.2s-%.2s screen=%ux%u sw%udp\n",
           device.density, device.sdkVersion, device.language, device.country,
           device.screenWidth, device.screenHeight, device.smallestScreenWidthDp);

    if (!rr.ok) {
        printf("result: FAILED error=%s\n", resources::resolution_error_name(rr.error));
        if (!opt.json_out.empty()) {
            std::ofstream j(opt.json_out);
            j << rr.to_json();
        }
        return 1;
    }

    printf("decomposition: package=%s type=%s entry=%s\n",
            rr.package_name.c_str(), rr.type_name.c_str(), rr.entry_name.c_str());
    printf("chain hops: %zu\n", rr.reference_hops());
    for (size_t i = 0; i < rr.chain.size(); i++) {
        const auto& st = rr.chain[i];
        printf("  [%zu] %s %s/%s selected_config=(%s) matched=%s\n",
               i, hex32(st.id).c_str(), st.package_name.c_str(),
               (st.type_name + "/" + st.entry_name).c_str(),
               st.selected_config_desc.c_str(),
               st.selected_by_match ? "yes" : "default-fallback");
    }

    // ── typed value semantics ───────────────────────────────────────────────
    if (term) {
        const ResValue& v = term->raw_value;
        printf("typed value: type=0x%02x data=0x%08x", (unsigned)v.type, v.data);
        if (v.is_string()) printf(" string=\"%s\"", json_escape(v.string_value).c_str());
        if (v.is_color()) printf(" argb=#%08x", v.data);
        if (v.is_dimension())
            printf(" dim=%.3f unit=%u (px=%.1f @%.0fdpi)", v.dim_value, v.dim_unit,
                   v.dim_value * (v.dim_unit == 0 ? 1.0f : device.density / 160.0f),
                   (float)device.density);
        if (v.is_reference()) printf(" ref→%s", hex32(v.ref_id).c_str());
        printf("\n");
    }

    // ── G04: file/drawable boundary + density law ───────────────────────────
    auto sel = arsc.select_file(resid, paths, device);
    if (sel) {
        uint16_t sd = sel->selected_density();
        const char* kind =
            sel->path.size() > 4 && sel->path.compare(sel->path.size() - 4, 4, ".xml") == 0
                ? "XML" : "BINARY";
        printf("file: %s (%s)\n", sel->path.c_str(), kind);
        printf("density: selected=%u target=%u scale=%.4f intrinsic=",
               sd == 0xFFFF ? 0 : (sd ? sd : 160), device.density,
               sd == 0xFFFF ? 1.0f
                            : float(device.density) / float(sd ? sd : 160));
        auto bytes = apk.extract_entry_cached(sel->path);
        renderer::ImageSizeProbe probe;
        if (!bytes.empty() && renderer::probe_image_size(bytes, &probe)) {
            float sc = sd == 0xFFFF ? 1.0f
                                    : float(device.density) / float(sd ? sd : 160);
            printf("%dx%d scaled=%dx%d bytes=%zu\n", probe.width, probe.height,
                   (int)std::lround(probe.width * sc),
                   (int)std::lround(probe.height * sc), bytes.size());
        } else {
            printf("unknown (probe failed) bytes=%zu\n", bytes.size());
        }
    } else if (rr.type_name == "drawable" || rr.type_name == "mipmap" ||
               rr.type_name == "raw" || rr.type_name == "layout") {
        printf("file: NOT A VALUE-IS-PATH ENTRY (value type or resolution)\n");
    }

    // ── bag dump (G03 §8 law: ResTable_map + parent chain) ──────────────────
    if (!opt.bag_attr.empty()) {
        uint32_t attr = (uint32_t)strtoul(opt.bag_attr.c_str(), nullptr, 16);
        auto v = arsc.bag_value(resid, attr, device);
        printf("bag attr %s: %s\n", hex32(attr).c_str(),
               v ? "FOUND" : "not-found (incl. parent chain)");
        if (v) printf("  type=0x%02x data=0x%08x\n", (unsigned)v->type, v->data);
    }

    // ── G04/G05 §18: layout consumption + measure + bounds channel ──────────
    bool is_layout = rr.type_name == "layout";
    if (opt.layout_mode && is_layout) {
        resources::DeviceMetrics metrics;   // single-device defaults (420dpi)
        if (opt.density > 0) metrics.density = opt.density / 160.0f;
        resources::LayoutInflater inflater(arsc, apk, opt.apk, metrics);
        // ViewShadow needs a heap for create_view (object allocation law) —
        // a standalone DalvikHeap + adapter mirrors the runtime wiring.
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter heap_adapter(&heap);
        framework::ViewShadow views;
        views.init(&heap_adapter);
        resources::InflateStats stats;
        uint32_t root = inflater.inflate_layout_resid(&views, resid, stats);
        if (root) {
            inflater.measure_layout(&views, root);
            printf("inflate: root=%s views=%d strings=%d colors=%d drawables=%d "
                   "unresolved=%d\n",
                   hex32(root).c_str(), stats.views_created, stats.strings_resolved,
                   stats.colors_resolved, stats.drawables_resolved,
                   stats.unresolved_refs);
            // measured geometry dump (measure → layout bounds evidence)
            std::function<void(uint32_t, int)> dump = [&](uint32_t vid, int depth) {
                auto* n = views.find_node(vid);
                if (!n) return;
                printf("  view[%*s%-*s] %s lp=%d/%d w=%d/%d measured %d,%d %dx%d "
                       "img='%s' src_density=%u\n",
                       depth * 2, "", 24 - depth * 2, "",
                       n->class_desc.c_str(), n->lp_width, n->lp_height,
                       n->width, n->height, n->measured_left, n->measured_top,
                       n->measured_width, n->measured_height,
                       n->src_drawable_path.c_str(), n->src_density);
                for (uint32_t c : n->children) dump(c, depth + 1);
            };
            printf("measure tree:\n");
            dump(root, 1);
        } else {
            printf("inflate: FAILED (elements_total=%d warnings=%zu%s)\n",
                   stats.elements_total, stats.warnings.size(),
                   stats.warnings.empty() ? ""
                     : (" first='" + stats.warnings.front() + "'").c_str());
        }
    } else if (is_layout) {
        printf("(layout id: pass --layout for inflate+measure evidence)\n");
    }

    if (!opt.json_out.empty()) {
        std::ofstream j(opt.json_out);
        j << rr.to_json();
        printf("json evidence: %s\n", opt.json_out.c_str());
    }
    return 0;
}
