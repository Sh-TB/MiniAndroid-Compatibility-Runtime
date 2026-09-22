// vector_inflater.cpp — S83-GFX-BASE §14: VectorDrawable inflation.
//
// SPLIT FROM layout_inflater.cpp for review clarity (same TU family; the
// declaration lives in layout_inflater.h next to apply_shape_background).
//
// LAW (AOSP frameworks/base/graphics/java/android/graphics/drawable/
// VectorDrawable.java + android.util.PathParser):
//   * <vector> root: viewportWidth/Height define the path coordinate space;
//     the drawable maps the viewport onto its bounds (scale both axes).
//   * <group>: T(translate) · T(pivot) · R(rotate) · S(scale) · T(-pivot)
//     composed onto the PARENT group matrix (nested groups legal).
//   * <path>: pathData (SVG-style M/L/H/V/C/S/Q/T/A/Z commands, relative and
//     absolute), fillColor/fillAlpha, strokeColor/strokeWidth/strokeAlpha,
//     fillType ("winding" default, "evenOdd").
//   * Curves flattened with fixed subdivision (16/cubic) — deterministic;
//     icons render pixel-true at runtime densities with this resolution.
//
// The parse output lands in ViewNode::bg_vector; the engine paints it via
// the scanline fill shared with the Canvas drawPath law.
#include "layout_inflater.h"
#include "axml_parser.h"

#include <cmath>
#include <cstdlib>
#include <functional>

namespace miniandroid {
namespace resources {

namespace {

struct VMat {
    float a = 1, b = 0, c = 0, d = 1, e = 0, f = 0;
    void map(float x, float y, float& ox, float& oy) const {
        ox = a * x + c * y + e;
        oy = b * x + d * y + f;
    }
    void pre_concat(const VMat& r) {   // this = this ∘ r
        const float na = a * r.a + c * r.b;
        const float nb = b * r.a + d * r.b;
        const float nc = a * r.c + c * r.d;
        const float nd = b * r.c + d * r.d;
        const float ne = a * r.e + c * r.f + e;
        const float nf = b * r.e + d * r.f + f;
        a = na; b = nb; c = nc; d = nd; e = ne; f = nf;
    }
};

// Float attribute: aapt2 FLOAT type (data = IEEE bits), dimension, or string.
float attr_float(const AxmlAttribute* at, float def) {
    if (!at) return def;
    if (at->value.type == DataType::FLOAT) {
        float f;
        std::memcpy(&f, &at->value.data, sizeof(f));
        return f;
    }
    if (at->value.is_dimension()) return at->value.dim_value;
    if (at->value.is_fraction()) return complex_to_float(at->value.data);
    const std::string s = !at->raw_value.empty() ? at->raw_value
                                                 : at->value.string_value;
    if (!s.empty()) return strtof(s.c_str(), nullptr);
    return def;
}

// ── SVG pathData flattening (PathParser + PathEvaluator law) ────────────
struct PathCursor {
    float cx = 0, cy = 0;      // current point
    float sx = 0, sy = 0;      // subpath start
};

void flatten_cubic(const float p[6], std::vector<std::pair<float, float>>& out) {
    const int N = 16;
    for (int i = 1; i <= N; i++) {
        const float t = (float)i / N, u = 1.f - t;
        const float x = u * u * u * p[0] + 3 * u * u * t * p[2] +
                        3 * u * t * t * p[4] + t * t * t * p[6];
        const float y = u * u * u * p[1] + 3 * u * u * t * p[3] +
                        3 * u * t * t * p[5] + t * t * t * p[7];
        out.push_back({x, y});
    }
}

void flatten_quad(const float p[4], std::vector<std::pair<float, float>>& out) {
    const int N = 12;
    for (int i = 1; i <= N; i++) {
        const float t = (float)i / N, u = 1.f - t;
        const float x = u * u * p[0] + 2 * u * t * p[2] + t * t * p[4];
        const float y = u * u * p[1] + 2 * u * t * p[3] + t * t * p[5];
        out.push_back({x, y});
    }
}

// Arc endpoint→center parameterization (SVG arc spec §F.6), 16 segments.
void flatten_arc(float rx, float ry, float xrot_deg, bool large_arc, bool sweep,
                 float x1, float y1, float x2, float y2,
                 std::vector<std::pair<float, float>>& out) {
    if (rx == 0 || ry == 0 || (x1 == x2 && y1 == y2)) return;
    rx = std::fabs(rx); ry = std::fabs(ry);
    const float phi = xrot_deg * 3.14159265358979323846f / 180.0f;
    const float cp = std::cos(phi), sp = std::sin(phi);
    const float dx2 = (x1 - x2) / 2.f, dy2 = (y1 - y2) / 2.f;
    const float x1p = cp * dx2 + sp * dy2;
    const float y1p = -sp * dx2 + cp * dy2;
    const float rx2 = rx * rx, ry2 = ry * ry;
    const float lam = x1p * x1p / rx2 + y1p * y1p / ry2;
    if (lam > 1.f) {
        const float s = std::sqrt(lam);
        rx *= s; ry *= s;
    }
    const float rx2c = rx * rx, ry2c = ry * ry;
    float num = rx2c * ry2c - rx2c * y1p * y1p - ry2c * x1p * x1p;
    const float den = rx2c * y1p * y1p + ry2c * x1p * x1p;
    float co = num > 0 && den > 0 ? std::sqrt(std::max(0.f, num / den)) : 0.f;
    if (large_arc == sweep) co = -co;
    const float cxp = co * rx * y1p / ry;
    const float cyp = -co * ry * x1p / rx;
    const float cx = cp * cxp - sp * cyp + (x1 + x2) / 2.f;
    const float cy = sp * cxp + cp * cyp + (y1 + y2) / 2.f;
    auto ang = [&](float ux, float uy, float vx, float vy) {
        const float dot = ux * vx + uy * vy;
        const float len = std::sqrt(ux * ux + uy * uy) * std::sqrt(vx * vx + vy * vy);
        float a = std::acos(std::max(-1.f, std::min(1.f, dot / (len ? len : 1.f))));
        if (ux * vy - uy * vx < 0) a = -a;
        return a;
    };
    const float th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry);
    float dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry,
                    (-x1p - cxp) / rx, (-y1p - cyp) / ry);
    if (!sweep && dth > 0) dth -= 2.f * 3.14159265358979323846f;
    if (sweep && dth < 0) dth += 2.f * 3.14159265358979323846f;
    const int N = 16;
    for (int i = 1; i <= N; i++) {
        const float th = th1 + dth * ((float)i / N);
        const float px = cx + rx * std::cos(th) * cp - ry * std::sin(th) * sp;
        const float py = cy + rx * std::cos(th) * sp + ry * std::sin(th) * cp;
        out.push_back({px, py});
    }
}

bool parse_floats(const std::string& s, size_t& pos, float& out) {
    while (pos < s.size() && (s[pos] == ' ' || s[pos] == ',' || s[pos] == '\n' ||
                              s[pos] == '\r' || s[pos] == '\t'))
        pos++;
    if (pos >= s.size()) return false;
    const char* begin = s.c_str() + pos;
    char* end = nullptr;
    const float v = strtof(begin, &end);
    if (end == begin) return false;
    pos += (size_t)(end - begin);
    out = v;
    return true;
}

void flatten_path_data(const std::string& d, const VMat& m,
                       std::vector<std::vector<std::pair<float, float>>>& contours) {
    if (d.empty()) return;
    std::vector<std::pair<float, float>> cur;
    PathCursor c;
    char cmd = 0;
    size_t pos = 0;
    // last cubic/quadratic control point for S/T reflection laws
    bool have_last_ctrl = false;
    float last_cx = 0, last_cy = 0;
    auto flush = [&]() {
        if (cur.size() >= 3) {
            contours.push_back(cur);
        }
        cur.clear();
    };
    while (pos < d.size()) {
        while (pos < d.size() && (d[pos] == ' ' || d[pos] == ',' || d[pos] == '\n' ||
                                  d[pos] == '\r' || d[pos] == '\t'))
            pos++;
        if (pos >= d.size()) break;
        const char ch = d[pos];
        if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z')) {
            cmd = ch;
            pos++;
        } else if (cmd == 0) {
            break;   // malformed head
        }
        const bool rel = cmd >= 'a' && cmd <= 'z';
        const char C = rel ? (char)(cmd - 32) : cmd;
        auto argf = [&](float& v) { return parse_floats(d, pos, v); };
        switch (C) {
            case 'M': {
                float x, y;
                if (!argf(x) || !argf(y)) return;
                flush();
                c.cx = rel ? c.cx + x : x;
                c.cy = rel ? c.cy + y : y;
                c.sx = c.cx; c.sy = c.cy;
                float ox, oy; m.map(c.cx, c.cy, ox, oy);
                cur.push_back({ox, oy});
                cmd = rel ? 'l' : 'L';   // implicit lineto law
                break;
            }
            case 'L': {
                float x, y;
                if (!argf(x) || !argf(y)) return;
                c.cx = rel ? c.cx + x : x;
                c.cy = rel ? c.cy + y : y;
                float ox, oy; m.map(c.cx, c.cy, ox, oy);
                cur.push_back({ox, oy});
                break;
            }
            case 'H': {
                float x;
                if (!argf(x)) return;
                c.cx = rel ? c.cx + x : x;
                float ox, oy; m.map(c.cx, c.cy, ox, oy);
                cur.push_back({ox, oy});
                break;
            }
            case 'V': {
                float y;
                if (!argf(y)) return;
                c.cy = rel ? c.cy + y : y;
                float ox, oy; m.map(c.cx, c.cy, ox, oy);
                cur.push_back({ox, oy});
                break;
            }
            case 'C': {
                float p[6];
                for (int i = 0; i < 6; i++)
                    if (!argf(p[i])) return;
                if (rel) for (int i = 0; i < 6; i += 2) p[i] += c.cx, p[i+1] += c.cy;
                have_last_ctrl = true; last_cx = p[2]; last_cy = p[3];
                float q[8] = {c.cx, c.cy, p[0], p[1], p[2], p[3], p[4], p[5]};
                flatten_cubic(q, cur);
                c.cx = p[4]; c.cy = p[5];
                break;
            }
            case 'S': {
                float p[4];
                for (int i = 0; i < 4; i++)
                    if (!argf(p[i])) return;
                if (rel) for (int i = 0; i < 4; i += 2) p[i] += c.cx, p[i+1] += c.cy;
                const float rcx = have_last_ctrl ? 2 * c.cx - last_cx : c.cx;
                const float rcy = have_last_ctrl ? 2 * c.cy - last_cy : c.cy;
                have_last_ctrl = true; last_cx = p[0]; last_cy = p[1];
                float q[8] = {c.cx, c.cy, rcx, rcy, p[0], p[1], p[2], p[3]};
                flatten_cubic(q, cur);
                c.cx = p[2]; c.cy = p[3];
                break;
            }
            case 'Q': {
                float p[4];
                for (int i = 0; i < 4; i++)
                    if (!argf(p[i])) return;
                if (rel) for (int i = 0; i < 4; i += 2) p[i] += c.cx, p[i+1] += c.cy;
                have_last_ctrl = true; last_cx = p[0]; last_cy = p[1];
                float q[6] = {c.cx, c.cy, p[0], p[1], p[2], p[3]};
                flatten_quad(q, cur);
                c.cx = p[2]; c.cy = p[3];
                break;
            }
            case 'T': {
                float x, y;
                if (!argf(x) || !argf(y)) return;
                const float px = rel ? c.cx + x : x;
                const float py = rel ? c.cy + y : y;
                const float rcx = have_last_ctrl ? 2 * c.cx - last_cx : c.cx;
                const float rcy = have_last_ctrl ? 2 * c.cy - last_cy : c.cy;
                have_last_ctrl = true; last_cx = rcx; last_cy = rcy;
                float q[6] = {c.cx, c.cy, rcx, rcy, px, py};
                flatten_quad(q, cur);
                c.cx = px; c.cy = py;
                break;
            }
            case 'A': {
                float rx, ry, rot, x, y;
                int la = 0, sw = 0;
                if (!argf(rx) || !argf(ry) || !argf(rot) ||
                    !parse_floats(d, pos, (float&)la) ||
                    !parse_floats(d, pos, (float&)sw) ||
                    !argf(x) || !argf(y))
                    return;
                const float ex = rel ? c.cx + x : x;
                const float ey = rel ? c.cy + y : y;
                flatten_arc(rx, ry, rot, la != 0, sw != 0, c.cx, c.cy, ex, ey, cur);
                c.cx = ex; c.cy = ey;
                have_last_ctrl = false;
                break;
            }
            case 'Z': {
                if (!cur.empty()) {
                    cur.push_back({c.sx, c.sy});
                }
                c.cx = c.sx; c.cy = c.sy;
                flush();
                break;
            }
            default:
                return;   // unknown command — keep what we have (honest)
        }
        have_last_ctrl = have_last_ctrl && (C == 'C' || C == 'S' || C == 'Q' || C == 'T');
    }
    flush();
}

}  // namespace

void LayoutInflater::apply_vector_background(
    framework::ViewShadow::ViewNode& node, const std::string& xml_path,
    InflateStats& stats) {
    std::vector<uint8_t> xml = apk_.extract_entry_cached(xml_path);
    if (xml.empty()) xml = apk_.extract_entry(apk_path_, xml_path);
    if (xml.empty()) {
        stats.warnings.push_back("vector drawable extract failed: " + xml_path);
        return;
    }
    AxmlParser parser;
    if (!parser.parse(xml)) {
        stats.warnings.push_back("vector AXML parse failed: " + xml_path);
        return;
    }
    const AxmlElement& root = parser.root();
    if (root.name != "vector") return;

    node.bg_vector = {};
    node.bg_vector.viewport_w =
        attr_float(root.attr("viewportWidth", "android"), 0.f);
    node.bg_vector.viewport_h =
        attr_float(root.attr("viewportHeight", "android"), 0.f);
    if (node.bg_vector.viewport_w <= 0 || node.bg_vector.viewport_h <= 0) {
        stats.warnings.push_back("vector missing viewport: " + xml_path);
        return;
    }

    // Group transform stack — AOSP group law:
    // M = M_parent · T(translate) · T(pivot) · R(rotate) · S(scale) · T(-pivot)
    VMat identity;
    std::function<void(const AxmlElement&, const VMat&)> walk =
        [&](const AxmlElement& el, const VMat& pm) {
            if (el.name == "group") {
                const float tx = attr_float(el.attr("translateX", "android"), 0.f);
                const float ty = attr_float(el.attr("translateY", "android"), 0.f);
                const float px = attr_float(el.attr("pivotX", "android"), 0.f);
                const float py = attr_float(el.attr("pivotY", "android"), 0.f);
                const float rot = attr_float(el.attr("rotation", "android"), 0.f);
                const float sx = attr_float(el.attr("scaleX", "android"), 1.f);
                const float sy = attr_float(el.attr("scaleY", "android"), 1.f);
                const float rad = rot * 3.14159265358979323846f / 180.0f;
                VMat t1; t1.e = tx; t1.f = ty;
                VMat tp; tp.e = px; tp.f = py;
                VMat r;  r.a = std::cos(rad); r.b = std::sin(rad);
                         r.c = -std::sin(rad); r.d = std::cos(rad);
                VMat sc; sc.a = sx; sc.d = sy;
                VMat tm; tm.e = -px; tm.f = -py;
                // local = t1 · tp · r · sc · tm ; M = pm · local
                VMat local = t1;
                local.pre_concat(tp); local.pre_concat(r);
                local.pre_concat(sc); local.pre_concat(tm);
                VMat m = pm;
                m.pre_concat(local);
                for (const auto& ch : el.children) walk(ch, m);
                return;
            }
            if (el.name == "path") {
                framework::ViewShadow::ViewNode::VectorPathData pd;
                const AxmlAttribute* pd_attr = el.attr("pathData", "android");
                const AxmlAttribute* fc = el.attr("fillColor", "android");
                const AxmlAttribute* sc_attr = el.attr("strokeColor", "android");
                if (fc) {
                    pd.fill_color = parse_color_attr(fc, stats);
                    pd.has_fill = pd.fill_color != 0;
                }
                pd.fill_alpha = attr_float(el.attr("fillAlpha", "android"), 1.f);
                if (sc_attr) {
                    pd.stroke_color = parse_color_attr(sc_attr, stats);
                    pd.stroke_alpha = attr_float(el.attr("strokeAlpha", "android"), 1.f);
                    pd.stroke_width = (float)parse_dim_attr(el.attr("strokeWidth", "android"), stats);
                    pd.has_stroke = pd.stroke_color != 0 && pd.stroke_width > 0;
                }
                const AxmlAttribute* ft = el.attr("fillType", "android");
                if (ft) {
                    // aapt2 compiles the fillType enum into INT space
                    // (none/winding=0, evenOdd=1); the raw string only
                    // survives in legacy/res-raw layouts.
                    if (ft->value.is_int()) {
                        pd.fill_type = ft->value.data == 1 ? 1 : 0;
                    } else {
                        const std::string v = !ft->raw_value.empty()
                                                  ? ft->raw_value : ft->value.string_value;
                        if (v == "evenOdd") pd.fill_type = 1;
                    }
                }
                if (pd_attr && (pd.has_fill || pd.has_stroke)) {
                    flatten_path_data(
                        !pd_attr->raw_value.empty() ? pd_attr->raw_value
                                                    : pd_attr->value.string_value,
                        pm, pd.contours);
                    if (!pd.contours.empty())
                        node.bg_vector.paths.push_back(std::move(pd));
                }
                return;
            }
            // clip-path / other children: recorded as honest gap
            for (const auto& ch : el.children) walk(ch, pm);
        };
    for (const auto& ch : root.children) walk(ch, identity);

    if (!node.bg_vector.paths.empty()) node.bg_vector_valid = true;
}

}  // namespace resources
}  // namespace miniandroid
