// s132_svg_reader.cpp — R-NEW-442 (S132 Wave-2): SVG-ASSET law.
//
// Telegram SvgHelper family loads PLAIN-TEXT .svg assets through the
// drawable slot. The runtime already owns the SVG path grammar
// (flatten_path_data = PathParser/PathEvaluator law) and the scanline
// fill (bg_vector paint law) — this adapter adds ONLY the text-XML
// reader for the MEASURED Telegram feature subset (scripts/s132 fan-out
// scan: 50 files = <path>/<circle>/<rect>/<ellipse>; ZERO gradients,
// masks, clipPaths, strokes, transforms in path-attr form) and reuses
// flatten_path_data + the existing bg_vector paint pipeline.
//
// Law anchors (SVG 1.1 + W3C): viewBox maps the user space onto the
// drawable bounds (same viewport→bounds law as VectorDrawable); fill
// accepts #rgb/#rrggbb/#aarrggbb forms; fill-rule evenOdd maps to the
// even-odd fill type; fill-opacity multiplies alpha.
#include "layout_inflater.h"

#include <cmath>
#include <cstdlib>
#include <map>

namespace miniandroid {
namespace resources {
namespace {

// Deterministic 64-segment ellipse approximation (16 per quadrant) —
// same subdivision discipline as the arc law in flatten_path_data.
void ellipse_contour(float cx, float cy, float rx, float ry,
                     std::vector<std::pair<float, float>>& out) {
    if (rx <= 0 || ry <= 0) return;
    constexpr int N = 64;
    for (int i = 0; i < N; ++i) {
        const float th = 2.f * 3.14159265358979323846f * float(i) / N;
        out.emplace_back(cx + rx * std::cos(th), cy + ry * std::sin(th));
    }
}

uint32_t parse_svg_color(const std::string& v) {
    if (v.empty() || v == "none") return 0;
    if (v[0] != '#') {
        // Measured Telegram set is hex-only; the named forms below cover
        // the SVG-1.1 basic color keywords that appear in hand-made icons.
        if (v == "black") return 0xff000000u;
        if (v == "white") return 0xffffffffu;
        if (v == "red") return 0xffff0000u;
        if (v == "green") return 0xff00ff00u;
        if (v == "blue") return 0xff0000ffu;
        if (v == "gray" || v == "grey") return 0xff888888u;
        return 0;
    }
    std::string h = v.substr(1);
    for (char& c : h)
        if (c >= 'A' && c <= 'F') c = char(c - 'A' + 'a');
    auto nib = [](char c) -> uint32_t {
        if (c >= '0' && c <= '9') return uint32_t(c - '0');
        if (c >= 'a' && c <= 'f') return uint32_t(c - 'a' + 10);
        return 0;
    };
    if (h.size() == 3) {
        uint32_t r = nib(h[0]) * 17, g = nib(h[1]) * 17, b = nib(h[2]) * 17;
        return 0xff000000u | (r << 16) | (g << 8) | b;
    }
    if (h.size() == 6) {
        uint32_t r = (nib(h[0]) << 4) | nib(h[1]);
        uint32_t g = (nib(h[2]) << 4) | nib(h[3]);
        uint32_t b = (nib(h[4]) << 4) | nib(h[5]);
        return 0xff000000u | (r << 16) | (g << 8) | b;
    }
    if (h.size() == 8) {  // #AARRGGBB
        uint32_t a = (nib(h[0]) << 4) | nib(h[1]);
        uint32_t r = (nib(h[2]) << 4) | nib(h[3]);
        uint32_t g = (nib(h[4]) << 4) | nib(h[5]);
        uint32_t b = (nib(h[6]) << 4) | nib(h[7]);
        return (a << 24) | (r << 16) | (g << 8) | b;
    }
    return 0;
}

float svg_float(const std::map<std::string, std::string>& a,
                const char* k, float def) {
    auto it = a.find(k);
    if (it == a.end()) return def;
    return strtof(it->second.c_str(), nullptr);
}

std::string svg_str(const std::map<std::string, std::string>& a,
                    const char* k) {
    auto it = a.find(k);
    return it == a.end() ? std::string() : it->second;
}

// Decode the five named entities (bounded scan) — Telegram icons carry
// &amp; inside label paths.
std::string decode_entities(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size();) {
        if (s[i] == '&') {
            size_t j = s.find(';', i);
            if (j != std::string::npos && j - i <= 8) {
                std::string e = s.substr(i + 1, j - i - 1);
                if (e == "amp") out += '&';
                else if (e == "lt") out += '<';
                else if (e == "gt") out += '>';
                else if (e == "quot") out += '"';
                else if (e == "apos") out += '\'';
                else out += s.substr(i, j - i + 1);
                i = j + 1;
                continue;
            }
        }
        out += s[i++];
    }
    return out;
}

struct SvgTag {
    std::string name;
    std::map<std::string, std::string> attrs;
    bool selfclose = false;
};

// Minimal text-XML tokenizer for the SVG subset: tags, quoted attributes,
// comments/PIs skipped. A law-abiding APP ADAPTER, not a general engine
// (reuse_registry: the general-engine slot is nanoSVG/resvg if a corpus
// APK ever measures beyond this subset).
bool next_svg_tag(const std::string& s, size_t& pos, SvgTag& t) {
    while (pos < s.size()) {
        size_t lt = s.find('<', pos);
        if (lt == std::string::npos) return false;
        if (s.compare(lt, 4, "<!--") == 0) {
            size_t e = s.find("-->", lt);
            if (e == std::string::npos) return false;
            pos = e + 3;
            continue;
        }
        if (s.compare(lt, 2, "<?") == 0 || s.compare(lt, 2, "<!") == 0) {
            size_t e = s.find('>', lt);
            if (e == std::string::npos) return false;
            pos = e + 1;
            continue;
        }
        size_t p = lt + 1;
        bool closing = p < s.size() && s[p] == '/';
        if (closing) ++p;
        while (p < s.size() && (isalnum((unsigned char)s[p]) ||
                                s[p] == ':' || s[p] == '_' || s[p] == '-'))
            ++p;
        t.name = s.substr(lt + 1 + (closing ? 1 : 0), p - lt - 1 - (closing ? 1 : 0));
        t.attrs.clear();
        t.selfclose = false;
        // attributes
        while (p < s.size()) {
            while (p < s.size() && isspace((unsigned char)s[p])) ++p;
            if (p >= s.size()) return false;
            if (s[p] == '>') { pos = p + 1; return !closing; }
            if (s[p] == '/' && p + 1 < s.size() && s[p + 1] == '>') {
                t.selfclose = true;
                pos = p + 2;
                return !closing;
            }
            size_t eq = s.find('=', p);
            if (eq == std::string::npos) break;
            std::string an = s.substr(p, eq - p);
            while (!an.empty() && isspace((unsigned char)an.back())) an.pop_back();
            p = eq + 1;
            while (p < s.size() && isspace((unsigned char)s[p])) ++p;
            if (p >= s.size()) break;
            char q = s[p];
            if (q != '"' && q != '\'') break;
            size_t ve = s.find(q, p + 1);
            if (ve == std::string::npos) return false;
            t.attrs[an] = decode_entities(s.substr(p + 1, ve - p - 1));
            p = ve + 1;
        }
        return false;
    }
    return false;
}

}  // namespace

bool LayoutInflater::apply_svg_background(
    framework::ViewShadow::ViewNode& node, const std::string& svg_path,
    InflateStats& stats) {
    std::string text(apk_.extract_entry_cached(svg_path).begin(),
                     apk_.extract_entry_cached(svg_path).end());
    if (text.empty()) {
        auto bytes = apk_.extract_entry(apk_path_, svg_path);
        text.assign(bytes.begin(), bytes.end());
    }
    if (text.empty()) {
        stats.warnings.push_back("svg asset extract failed: " + svg_path);
        return false;
    }

    size_t pos = 0;
    SvgTag t;
    bool have_root = false;
    float minx = 0, miny = 0;
    VMat base;  // viewBox offset (identity until a viewBox is read)

    node.bg_vector = {};
    while (next_svg_tag(text, pos, t)) {
        if (t.name == "svg" && !have_root) {
            have_root = true;
            const std::string vb = svg_str(t.attrs, "viewBox");
            if (!vb.empty()) {
                float vw = 0, vh = 0;
                size_t vp = 0;
                parse_floats(vb, vp, minx) && parse_floats(vb, vp, miny) &&
                    parse_floats(vb, vp, vw) && parse_floats(vb, vp, vh);
                if (vw > 0 && vh > 0) {
                    node.bg_vector.viewport_w = vw;
                    node.bg_vector.viewport_h = vh;
                    base.e = -minx;
                    base.f = -miny;
                }
            }
            continue;
        }
        if (!have_root) continue;
        if (t.name == "path") {
            framework::ViewShadow::ViewNode::VectorPathData pd;
            const std::string d = svg_str(t.attrs, "d");
            std::string fill = svg_str(t.attrs, "fill");
            pd.fill_color = parse_svg_color(fill);
            pd.has_fill = pd.fill_color != 0;
            pd.fill_alpha = svg_float(t.attrs, "fill-opacity", 1.f);
            if (svg_str(t.attrs, "fill-rule") == "evenodd") pd.fill_type = 1;
            if (pd.has_fill && !d.empty()) {
                flatten_path_data(d, base, pd.contours);
                if (!pd.contours.empty())
                    node.bg_vector.paths.push_back(std::move(pd));
            }
            continue;
        }
        if (t.name == "circle" || t.name == "ellipse" || t.name == "rect") {
            framework::ViewShadow::ViewNode::VectorPathData pd;
            std::string fill = svg_str(t.attrs, "fill");
            if (fill.empty()) fill = "#000000";  // SVG default fill = black
            pd.fill_color = parse_svg_color(fill);
            pd.has_fill = pd.fill_color != 0;
            pd.fill_alpha = svg_float(t.attrs, "fill-opacity", 1.f);
            std::vector<std::pair<float, float>> c;
            if (t.name == "circle") {
                ellipse_contour(svg_float(t.attrs, "cx", 0.f),
                                svg_float(t.attrs, "cy", 0.f),
                                svg_float(t.attrs, "r", 0.f),
                                svg_float(t.attrs, "r", 0.f), c);
            } else if (t.name == "ellipse") {
                ellipse_contour(svg_float(t.attrs, "cx", 0.f),
                                svg_float(t.attrs, "cy", 0.f),
                                svg_float(t.attrs, "rx", 0.f),
                                svg_float(t.attrs, "ry", 0.f), c);
            } else {
                const float x = svg_float(t.attrs, "x", 0.f);
                const float y = svg_float(t.attrs, "y", 0.f);
                const float w = svg_float(t.attrs, "width", 0.f);
                const float h = svg_float(t.attrs, "height", 0.f);
                float rx = svg_float(t.attrs, "rx", 0.f);
                if (w > 0 && h > 0) {
                    if (rx > 0) {
                        rx = std::min(rx, std::min(w, h) / 2.f);
                        ellipse_contour(x + rx, y + rx, rx, rx, c);
                        ellipse_contour(x + w - rx, y + rx, rx, rx, c);
                        ellipse_contour(x + w - rx, y + h - rx, rx, rx, c);
                        ellipse_contour(x + rx, y + h - rx, rx, rx, c);
                    } else {
                        c = {{x, y}, {x + w, y}, {x + w, y + h}, {x, y + h}};
                    }
                }
            }
            if (pd.has_fill && !c.empty()) {
                for (auto& [px, py] : c) {
                    float ox, oy;
                    base.map(px, py, ox, oy);
                    px = ox; py = oy;
                }
                pd.contours.push_back(std::move(c));
                node.bg_vector.paths.push_back(std::move(pd));
            }
            continue;
        }
        // <g>/<defs>/<style>/... — the measured subset carries none that
        // change paint; recorded as honest non-features.
    }

    if (!node.bg_vector.paths.empty()) {
        node.bg_vector_valid = true;
        static thread_local uint64_t s132_svg_log = 0;
        if (s132_svg_log < 12) {
            ++s132_svg_log;
            std::cerr << "[R442-SVG] " << svg_path << " paths="
                      << node.bg_vector.paths.size()
                      << " viewport=" << node.bg_vector.viewport_w
                      << "x" << node.bg_vector.viewport_h << std::endl;
        }
        return true;
    }
    stats.warnings.push_back("svg produced no paths: " + svg_path);
    return false;
}

}  // namespace resources
}  // namespace miniandroid
