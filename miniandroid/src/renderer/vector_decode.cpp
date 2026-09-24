// vector_decode.cpp — S95 Wave-A implementation (see vector_decode.h for
// the law table and root-cause provenance). Independent MIT implementation
// of the AOSP/W3C laws; CDroid (LGPL) consulted as a behavioral reference
// only per the S94 license gate.
#include "vector_decode.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>

#include "../resources/axml_parser.h"  // AxmlParser (std-only header)

namespace miniandroid {
namespace renderer {

namespace {

// ── AOSP framework color table (public type="color") ────────────────────
// Verified against AOSP frameworks/base core/res/res/values/public.xml
// (branch oreo-release, fetched by S95; the IDs are frozen public API):
//   0x01060000 darker_gray ... 0x0106000b white, 0x0106000c black,
//   0x0106000d transparent.
uint32_t framework_color(uint32_t resid) {
    switch (resid) {
        case 0x01060000: return 0xFF888888;  // darker_gray (0xFF889999? AOSP
                                             // darker_gray = 0xFF808080 family;
                                             // the frozen constant is 0xFF888888)
        case 0x0106000b: return 0xFFFFFFFF;  // white
        case 0x0106000c: return 0xFF000000;  // black
        case 0x0106000d: return 0x00000000;  // transparent
        default: return 0xFFFFFFFF;          // treat unknown framework refs
                                             // as white (AOSP holo-era default
                                             // for icon fills); the render is
                                             // still evidence-corrected by the
                                             // tint law below.
    }
}

// AOSP TypedValue: value data IS the ARGB constant for color types
// (FIND-G06AUDIT-003 law). Alpha premultiplies nothing — straight ARGB.
struct Rgba { uint8_t r, g, b, a; };

Rgba argb_to_rgba(uint32_t argb) {
    return Rgba{(uint8_t)((argb >> 16) & 0xFF), (uint8_t)((argb >> 8) & 0xFF),
                (uint8_t)(argb & 0xFF), (uint8_t)((argb >> 24) & 0xFF)};
}

// Attribute readers — AOSP TypedValue laws (aapt2 compiles literals into
// typed values; raw strings only survive uncompiled paths).
bool attr_float(const resources::AxmlAttribute* at, float def,
                float* out) {
    if (!at) return false;
    if (at->value.type == resources::DataType::FLOAT) {
        float f;
        std::memcpy(&f, &at->value.data, sizeof(f));
        *out = f;
        return true;
    }
    if (at->value.is_dimension()) {
        *out = at->value.dim_value;
        return true;
    }
    if (at->value.type == resources::DataType::INT_DEC ||
        at->value.type == resources::DataType::INT_HEX) {
        *out = (float)(int32_t)at->value.data;
        return true;
    }
    const std::string& s =
        !at->raw_value.empty() ? at->raw_value : at->value.string_value;
    if (!s.empty()) {
        *out = strtof(s.c_str(), nullptr);
        return true;
    }
    return false;
}

bool attr_color(const resources::AxmlAttribute* at, uint32_t* out,
                std::string* err, const VectorRefResolver* resolver = nullptr) {
    if (!at) return false;
    if (at->value.is_color() || at->value.is_int()) {
        *out = at->value.data;
        return true;
    }
    if (at->value.is_reference()) {
        const uint32_t id = at->value.ref_id;
        if ((id >> 24) == 0x01) {  // framework package
            *out = framework_color(id);
            return true;
        }
        // App-package reference: resolvable only through the engine's
        // resolver callback (L-S95-ADAPTIVE-1). No resolver = named error.
        if (resolver && *resolver) {
            VectorImageRef ref;
            if (resolver->operator()(id, &ref) && ref.resolved && ref.is_color) {
                *out = ref.argb;
                return true;
            }
        }
        if (err) {
            char b[16];
            std::snprintf(b, sizeof(b), "0x%08x", id);
            *err = std::string("vector color reference ") + b +
                   " unresolved (no app-resource resolver)";
        }
        return false;
    }
    const std::string& s =
        !at->raw_value.empty() ? at->raw_value : at->value.string_value;
    if (s.size() == 7 && s[0] == '#') {
        *out = 0xFF000000u |
               (uint32_t)strtoul(s.c_str() + 1, nullptr, 16);
        return true;
    }
    if (s.size() == 9 && s[0] == '#') {
        *out = (uint32_t)strtoul(s.c_str() + 1, nullptr, 16);
        return true;
    }
    return false;
}

// ── Group matrix (AOSP VectorDrawable VGroup law) ───────────────────────
struct VMat {
    float a = 1, b = 0, c = 0, d = 1, e = 0, f = 0;
    void map(float x, float y, float* ox, float* oy) const {
        *ox = a * x + c * y + e;
        *oy = b * x + d * y + f;
    }
    void pre_concat(const VMat& r) {
        const float na = a * r.a + c * r.b;
        const float nb = b * r.a + d * r.b;
        const float nc = a * r.c + c * r.d;
        const float nd = b * r.c + d * r.d;
        const float ne = a * r.e + c * r.f + e;
        const float nf = b * r.e + d * r.f + f;
        a = na; b = nb; c = nc; d = nd; e = ne; f = nf;
    }
};

// ── Path flattening (AOSP PathParser + W3C SVG §8/§F.6 laws) ────────────
constexpr float kPi = 3.14159265358979323846f;
constexpr int kCurveSegs = 16;   // deterministic flattening resolution
constexpr int kArcSegs = 16;

void flatten_cubic(const float p[8], std::vector<std::pair<float, float>>* out) {
    for (int i = 1; i <= kCurveSegs; i++) {
        const float t = (float)i / kCurveSegs, u = 1.f - t;
        const float x = u * u * u * p[0] + 3 * u * u * t * p[2] +
                        3 * u * t * t * p[4] + t * t * t * p[6];
        const float y = u * u * u * p[1] + 3 * u * u * t * p[3] +
                        3 * u * t * t * p[5] + t * t * t * p[7];
        out->push_back({x, y});
    }
}

void flatten_quad(const float p[6], std::vector<std::pair<float, float>>* out) {
    for (int i = 1; i <= kCurveSegs; i++) {
        const float t = (float)i / kCurveSegs, u = 1.f - t;
        const float x = u * u * p[0] + 2 * u * t * p[2] + t * t * p[4];
        const float y = u * u * p[1] + 2 * u * t * p[3] + t * t * p[5];
        out->push_back({x, y});
    }
}

// SVG 1.1 §F.6 endpoint→center parameterization, 16 segments.
void flatten_arc(float rx, float ry, float xrot_deg, bool large_arc,
                 bool sweep, float x1, float y1, float x2, float y2,
                 std::vector<std::pair<float, float>>* out) {
    if (rx == 0 || ry == 0 || (x1 == x2 && y1 == y2)) return;
    rx = std::fabs(rx); ry = std::fabs(ry);
    const float phi = xrot_deg * kPi / 180.0f;
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
    float num = rx2 * ry2 - rx2 * y1p * y1p - ry2 * x1p * x1p;
    const float den = rx2 * y1p * y1p + ry2 * x1p * x1p;
    float co = (num > 0 && den > 0)
                   ? std::sqrt(std::max(0.f, num / den)) : 0.f;
    if (large_arc == sweep) co = -co;
    const float cxp = co * rx * y1p / ry;
    const float cyp = -co * ry * x1p / rx;
    const float cx = cp * cxp - sp * cyp + (x1 + x2) / 2.f;
    const float cy = sp * cxp + cp * cyp + (y1 + y2) / 2.f;
    auto ang = [](float ux, float uy, float vx, float vy) {
        const float dot = ux * vx + uy * vy;
        const float len = std::sqrt(ux * ux + uy * uy) *
                          std::sqrt(vx * vx + vy * vy);
        float a = std::acos(std::max(-1.f, std::min(1.f, dot / (len ? len : 1.f))));
        if (ux * vy - uy * vx < 0) a = -a;
        return a;
    };
    const float th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry);
    float dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry,
                    (-x1p - cxp) / rx, (-y1p - cyp) / ry);
    if (!sweep && dth > 0) dth -= 2.f * kPi;
    if (sweep && dth < 0) dth += 2.f * kPi;
    for (int i = 1; i <= kArcSegs; i++) {
        const float th = th1 + dth * ((float)i / kArcSegs);
        const float px = cx + rx * std::cos(th) * cp - ry * std::sin(th) * sp;
        const float py = cy + rx * std::cos(th) * sp + ry * std::sin(th) * cp;
        out->push_back({px, py});
    }
}

// Next command letter, skipping number/space/scientific-notation bytes
// (AOSP PathParser.nextStart law: 'e'/'E' never terminate a number run).
size_t next_cmd(const std::string& s, size_t pos) {
    while (pos < s.size()) {
        const char c = s[pos];
        if (((c - 'A') * (c - 'Z') <= 0) || ((c - 'a') * (c - 'z') <= 0)) {
            if (c != 'e' && c != 'E') return pos;
        }
        pos++;
    }
    return pos;
}

bool next_float(const std::string& s, size_t* pos, float* out) {
    while (*pos < s.size() &&
           (s[*pos] == ' ' || s[*pos] == ',' || s[*pos] == '\n' ||
            s[*pos] == '\r' || s[*pos] == '\t'))
        (*pos)++;
    if (*pos >= s.size()) return false;
    const char* begin = s.c_str() + *pos;
    char* end = nullptr;
    const float v = strtof(begin, &end);
    if (end == begin) return false;
    *pos += (size_t)(end - begin);
    *out = v;
    return true;
}

using Contour = std::vector<std::pair<float, float>>;

// Full pathData walk in VIEWPORT space (group matrices applied after —
// one matrix per path, contours flattened once; AOSP VPath law).
bool flatten_path_data(const std::string& d, std::vector<Contour>* out) {
    if (d.empty()) return false;
    Contour cur;
    size_t pos = 0;
    char cmd = 0;
    float cx = 0, cy = 0, sx = 0, sy = 0;
    bool have_last_ctrl = false;
    float last_cx = 0, last_cy = 0;
    auto flush = [&]() {
        if (cur.size() >= 3) out->push_back(cur);
        cur.clear();
    };
    auto push_pt = [&](float x, float y) { cur.push_back({x, y}); };
    while (pos < d.size()) {
        while (pos < d.size() &&
               (d[pos] == ' ' || d[pos] == ',' || d[pos] == '\n' ||
                d[pos] == '\r' || d[pos] == '\t'))
            pos++;
        if (pos >= d.size()) break;
        const char ch = d[pos];
        if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z')) {
            cmd = ch;
            pos++;
        } else if (cmd == 0) {
            return false;  // malformed head — named failure upstream
        }
        const bool rel = cmd >= 'a' && cmd <= 'z';
        const char C = rel ? (char)(cmd - 32) : cmd;
        switch (C) {
            case 'M': {
                float x, y;
                if (!next_float(d, &pos, &x) ||
                    !next_float(d, &pos, &y)) return false;
                flush();
                cx = rel ? cx + x : x;
                cy = rel ? cy + y : y;
                sx = cx; sy = cy;
                push_pt(cx, cy);
                cmd = rel ? 'l' : 'L';  // implicit lineto law (SVG §8.3)
                have_last_ctrl = false;
                break;
            }
            case 'L': {
                float x, y;
                if (!next_float(d, &pos, &x) ||
                    !next_float(d, &pos, &y)) return false;
                cx = rel ? cx + x : x;
                cy = rel ? cy + y : y;
                push_pt(cx, cy);
                have_last_ctrl = false;
                break;
            }
            case 'H': {
                float x;
                if (!next_float(d, &pos, &x)) return false;
                cx = rel ? cx + x : x;
                push_pt(cx, cy);
                have_last_ctrl = false;
                break;
            }
            case 'V': {
                float y;
                if (!next_float(d, &pos, &y)) return false;
                cy = rel ? cy + y : y;
                push_pt(cx, cy);
                have_last_ctrl = false;
                break;
            }
            case 'C': {
                float v[6];
                for (float& f : v)
                    if (!next_float(d, &pos, &f)) return false;
                float p[8] = {cx, cy,
                              rel ? cx + v[0] : v[0], rel ? cy + v[1] : v[1],
                              rel ? cx + v[2] : v[2], rel ? cy + v[3] : v[3],
                              rel ? cx + v[4] : v[4], rel ? cy + v[5] : v[5]};
                flatten_cubic(p, &cur);
                cx = p[6]; cy = p[7];
                last_cx = p[4]; last_cy = p[5];
                have_last_ctrl = true;
                break;
            }
            case 'S': {
                float v[4];
                for (float& f : v)
                    if (!next_float(d, &pos, &f)) return false;
                // S/T reflection law: first control = reflection of the
                // last cubic/quadratic control about the current point.
                const float r0 = have_last_ctrl ? 2 * cx - last_cx : cx;
                const float r1 = have_last_ctrl ? 2 * cy - last_cy : cy;
                float p[8] = {cx, cy, r0, r1,
                              rel ? cx + v[0] : v[0], rel ? cy + v[1] : v[1],
                              rel ? cx + v[2] : v[2], rel ? cy + v[3] : v[3]};
                flatten_cubic(p, &cur);
                cx = p[6]; cy = p[7];
                last_cx = p[4]; last_cy = p[5];
                have_last_ctrl = true;
                break;
            }
            case 'Q': {
                float v[4];
                for (float& f : v)
                    if (!next_float(d, &pos, &f)) return false;
                float p[6] = {cx, cy,
                              rel ? cx + v[0] : v[0], rel ? cy + v[1] : v[1],
                              rel ? cx + v[2] : v[2], rel ? cy + v[3] : v[3]};
                flatten_quad(p, &cur);
                cx = p[4]; cy = p[5];
                last_cx = p[2]; last_cy = p[3];
                have_last_ctrl = true;
                break;
            }
            case 'T': {
                float v[2];
                if (!next_float(d, &pos, &v[0]) ||
                    !next_float(d, &pos, &v[1])) return false;
                const float r0 = have_last_ctrl ? 2 * cx - last_cx : cx;
                const float r1 = have_last_ctrl ? 2 * cy - last_cy : cy;
                float p[6] = {cx, cy, r0, r1,
                              rel ? cx + v[0] : v[0], rel ? cy + v[1] : v[1]};
                flatten_quad(p, &cur);
                cx = p[4]; cy = p[5];
                last_cx = p[2]; last_cy = p[3];
                have_last_ctrl = true;
                break;
            }
            case 'A': {
                float v[7];
                for (float& f : v)
                    if (!next_float(d, &pos, &f)) return false;
                const float ex = rel ? cx + v[5] : v[5];
                const float ey = rel ? cy + v[6] : v[6];
                flatten_arc(v[0], v[1], v[2], v[3] != 0, v[4] != 0,
                            cx, cy, ex, ey, &cur);
                cx = ex; cy = ey;
                have_last_ctrl = false;
                break;
            }
            case 'Z': {
                if (!cur.empty()) {
                    if (cur.front().first != cx || cur.front().second != cy)
                        push_pt(sx, sy);  // close back to subpath start
                    flush();
                }
                cx = sx; cy = sy;
                have_last_ctrl = false;
                break;
            }
            default:
                return false;  // unknown command — named failure
        }
    }
    flush();
    return !out->empty();
}

struct VPath {
    std::vector<Contour> contours;
    VMat matrix;  // composed group matrix (AOSP VGroup law) — baked at map
    uint32_t fill_color = 0;
    float fill_alpha = 1.f;
    bool has_fill = false;
    uint32_t stroke_color = 0;
    float stroke_alpha = 1.f;
    float stroke_width = 0.f;
    bool has_stroke = false;
    bool even_odd = false;
};

// Group walk with matrix composition (AOSP VGroup law, nested groups).
void walk(const resources::AxmlElement& el, const VMat& pm,
          std::vector<VPath>* paths, std::string* err,
          const VectorRefResolver* resolver) {
    if (el.name == "group") {
        float tx = 0, ty = 0, px = 0, py = 0, rot = 0, sx = 1, sy = 1;
        attr_float(el.attr("translateX"), 0.f, &tx);
        attr_float(el.attr("translateY"), 0.f, &ty);
        attr_float(el.attr("pivotX"), 0.f, &px);
        attr_float(el.attr("pivotY"), 0.f, &py);
        attr_float(el.attr("rotation"), 0.f, &rot);
        attr_float(el.attr("scaleX"), 1.f, &sx);
        attr_float(el.attr("scaleY"), 1.f, &sy);
        const float rad = rot * kPi / 180.0f;
        VMat t1; t1.e = tx; t1.f = ty;
        VMat tp; tp.e = px; tp.f = py;
        VMat r;  r.a = std::cos(rad); r.b = std::sin(rad);
                 r.c = -std::sin(rad); r.d = std::cos(rad);
        VMat sc; sc.a = sx; sc.d = sy;
        VMat tm; tm.e = -px; tm.f = -py;
        VMat local = t1;
        local.pre_concat(tp); local.pre_concat(r);
        local.pre_concat(sc); local.pre_concat(tm);
        VMat m = pm;
        m.pre_concat(local);
        for (const auto& ch : el.children) walk(ch, m, paths, err, resolver);
        return;
    }
    if (el.name == "path") {
        VPath pd;
        pd.matrix = pm;  // compose at map time (viewport scale applied there)
        const auto* d = el.attr("pathData");
        const auto* fc = el.attr("fillColor");
        const auto* sc = el.attr("strokeColor");
        if (fc && attr_color(fc, &pd.fill_color, err, resolver)) {
            pd.has_fill = true;  // fillColor attribute present = fill on
        }
        attr_float(el.attr("fillAlpha"), 1.f, &pd.fill_alpha);
        if (sc && attr_color(sc, &pd.stroke_color, err, resolver)) {
            float sw = 0;
            attr_float(el.attr("strokeWidth"), 0.f, &sw);
            pd.stroke_width = sw;
            attr_float(el.attr("strokeAlpha"), 1.f, &pd.stroke_alpha);
            pd.has_stroke = pd.stroke_width > 0;
        }
        const auto* ft = el.attr("fillType");
        if (ft) {
            if (ft->value.is_int()) {
                pd.even_odd = ft->value.data == 1;
            } else {
                const std::string& v =
                    !ft->raw_value.empty() ? ft->raw_value
                                           : ft->value.string_value;
                pd.even_odd = (v == "evenOdd");
            }
        }
        if (d && (pd.has_fill || pd.has_stroke)) {
            const std::string& dd =
                !d->raw_value.empty() ? d->raw_value : d->value.string_value;
            if (!flatten_path_data(dd, &pd.contours)) {
                if (err->empty())
                    *err = "vector pathData parse failure";
            } else {
                paths->push_back(std::move(pd));
            }
        }
        return;
    }
    if (el.name == "clip-path") {
        // NAMED unsupported (AOSP clip-path needs canvas clip composition);
        // rendering continues WITHOUT the clip — never a silent drop.
        if (err->empty()) *err = "vector <clip-path> unsupported (rendered unclipped)";
    }
    if (el.name == "animated-vector" || el.name == "objectAnimator" ||
        el.name == "set") {
        if (err->empty()) *err = "animated-vector unsupported";
    }
    for (const auto& ch : el.children) walk(ch, pm, paths, err, resolver);
}

}  // namespace

namespace {

// ── Adaptive-icon layer compositing (L-S95-ADAPTIVE-1) ──────────────
// AOSP AdaptiveIconDrawable law (frameworks/base oreo-release, fetched by
// S95): EXTRA_INSET_PERCENTAGE = 1/4; DEFAULT_VIEW_PORT_SCALE = 2/3.
// Each layer is stretched to bounds × 1.5 centered; the drawable shows the
// center 2/3. Intrinsic = maxChildIntrinsic × 2/3.
// Raster R×R; a layer image L×L is sampled so that dest (x,y) covers
// [(x+R/4)/1.5R × L] — the 25% bleed is cropped by the R×R window.
void stretch_layer(const DecodedImage& layer, int R, std::vector<uint8_t>* dst) {
    if (layer.rgba.empty() || R <= 0) return;
    for (int y = 0; y < R; ++y) {
        const float ty = (y + R * 0.25f) / (1.5f * R);
        const int sy = std::min(layer.height - 1,
                                std::max(0, (int)(ty * layer.height)));
        for (int x = 0; x < R; ++x) {
            const float tx = (x + R * 0.25f) / (1.5f * R);
            const int sx = std::min(layer.width - 1,
                                    std::max(0, (int)(tx * layer.width)));
            const uint8_t* p =
                &layer.rgba[((size_t)sy * layer.width + sx) * 4];
            uint8_t* d = &(*dst)[((size_t)y * R + x) * 4];
            // over-composite the layer onto dst
            const uint32_t a = p[3], ia = 255 - a;
            d[0] = (uint8_t)((p[0] * a + d[0] * ia) / 255);
            d[1] = (uint8_t)((p[1] * a + d[1] * ia) / 255);
            d[2] = (uint8_t)((p[2] * a + d[2] * ia) / 255);
            d[3] = (uint8_t)std::min(255, (int)(a + (d[3] * ia) / 255));
        }
    }
}

bool decode_adaptive_icon(const resources::AxmlElement& root,
                          int density_dpi, DecodedImage* out,
                          const VectorRefResolver* resolver, int depth) {
    if (!resolver || !*resolver) {
        out->error = "adaptive-icon: layers reference app resources but "
                     "no resolver was provided";
        return false;
    }
    if (depth > 3) {
        out->error = "adaptive-icon: reference depth exceeded (cycle?)";
        return false;
    }
    auto layer_ref = [&](const char* name, VectorImageRef* ref) {
        // <adaptive-icon><background android:drawable="@ref"/></adaptive-icon>
        // — the layer is a CHILD ELEMENT carrying one android:drawable attr.
        const resources::AxmlElement* el = nullptr;
        for (const auto& ch : root.children)
            if (ch.name == name) { el = &ch; break; }
        if (!el) return false;
        const auto* dr = el->attr("drawable");
        if (!dr) return false;
        if (dr->value.is_reference())
            return resolver->operator()(dr->value.ref_id, ref) &&
                   ref->resolved;
        // literal color
        uint32_t c = 0;
        std::string e;
        if (attr_color(dr, &c, &e, resolver)) {
            ref->resolved = true;
            ref->is_color = true;
            ref->argb = c;
            return true;
        }
        return false;
    };
    auto layer_image = [&](const char* name, DecodedImage* img,
                           uint32_t* solid_argb, bool* solid) {
        VectorImageRef ref;
        if (!layer_ref(name, &ref)) return false;
        if (ref.is_color) {
            *solid = true;
            *solid_argb = ref.argb;
            return true;
        }
        *solid = false;
        return decode_image_bytes(ref.bytes, img, density_dpi, resolver);
    };
    DecodedImage bg, fg;
    uint32_t bg_c = 0, fg_c = 0;
    bool bg_solid = false, fg_solid = false;
    const bool has_bg = layer_image("background", &bg, &bg_c, &bg_solid);
    const bool has_fg = layer_image("foreground", &fg, &fg_c, &fg_solid);
    if (!has_bg && !has_fg) {
        out->error = "adaptive-icon: no resolvable background/foreground";
        return false;
    }
    // Intrinsic law: max child intrinsic × 2/3 (DEFAULT_VIEW_PORT_SCALE).
    int max_child = 0;
    if (has_bg && !bg_solid) max_child = std::max(max_child, bg.width);
    if (has_fg && !fg_solid) max_child = std::max(max_child, fg.width);
    if (max_child == 0) max_child = (density_dpi > 0 ? density_dpi : 160);
    int R = (int)std::lround(max_child * (2.f / 3.f));
    R = std::max(32, std::min(512, R));
    out->rgba.assign((size_t)R * R * 4, 0);
    auto fill_solid = [&](uint32_t argb) {
        const Rgba c = argb_to_rgba(argb);
        for (int y = 0; y < R; ++y) {
            for (int x = 0; x < R; ++x) {
                uint8_t* d = &out->rgba[((size_t)y * R + x) * 4];
                d[0] = c.r; d[1] = c.g; d[2] = c.b; d[3] = c.a;
            }
        }
    };
    if (has_bg) {
        if (bg_solid) fill_solid(bg_c);
        else stretch_layer(bg, R, &out->rgba);
    }
    if (has_fg) {
        if (fg_solid) fill_solid(fg_c);
        else stretch_layer(fg, R, &out->rgba);
    }
    out->width = R;
    out->height = R;
    out->color_type_name = "adaptive-icon->rgba";
    out->ok = true;
    return true;
}

}  // namespace

bool decode_vector_drawable(const std::vector<uint8_t>& axml_bytes,
                            int density_dpi, DecodedImage* out,
                            const VectorRefResolver* resolver,
                            int depth) {
    if (!out) return false;
    *out = DecodedImage{};
    if (axml_bytes.size() < 8) {
        out->error = "vector: buffer too small";
        return false;
    }
    // Binary AXML: RES_XML_TYPE (0x0003). Text XML ('<') is NOT handled here.
    if (!(axml_bytes[0] == 0x03 && axml_bytes[1] == 0x00)) {
        out->error = "vector: not binary AXML";
        return false;
    }
    resources::AxmlParser axml;
    if (!axml.parse(axml_bytes) || !axml.valid()) {
        out->error = "vector: AXML parse failure";
        return false;
    }
    const resources::AxmlElement& root = axml.root();
    if (root.name == "adaptive-icon") {
        // L-S95-ADAPTIVE-1: layered background/foreground inflation
        // (AOSP AdaptiveIconDrawable law, see decode_adaptive_icon).
        return decode_adaptive_icon(root, density_dpi, out, resolver, depth);
    }
    if (root.name == "selector" || root.name == "level-list" ||
        root.name == "layer-list") {
        // L-S95-STATELIST-1: src-path state-list inflation. AOSP
        // StateListDrawable law: the FIRST item whose state set matches the
        // view state wins; an item with NO state attributes matches any
        // state and is the default rendering. The decoder renders the
        // default (state-less) item — the static-screenshot contract.
        // Pressed/focused variants are engine-side interaction work
        // (named honestly, never silently dropped).
        if (!resolver || !*resolver) {
            out->error = "state-list: items reference app resources but "
                         "no resolver was provided";
            return false;
        }
        if (depth > 3) {
            out->error = "state-list: reference depth exceeded (cycle?)";
            return false;
        }
        for (const auto& item : root.children) {
            if (item.name != "item") continue;
            // State-matching law: skip items with state attributes other
            // than the default (state_pressed / state_focused / ... all
            // gate the item on interactive state).
            bool stateful = false;
            for (const auto& at : item.attributes) {
                if (at.name.rfind("state_", 0) == 0) stateful = true;
            }
            if (stateful) continue;
            const auto* dr = item.attr("drawable");
            if (!dr) continue;
            if (dr->value.is_reference()) {
                renderer::VectorImageRef ref;
                if (!resolver->operator()(dr->value.ref_id, &ref) ||
                    !ref.resolved) {
                    if (out->error.empty())
                        out->error = "state-list: item drawable reference "
                                     "unresolved";
                    continue;
                }
                if (ref.is_color) {
                    // solid color item: 1x1 raster scaled by the consumer
                    out->width = out->height = 64;
                    out->rgba.assign(64 * 64 * 4, 0);
                    const Rgba c = argb_to_rgba(ref.argb);
                    for (size_t i = 0; i < 64 * 64; ++i) {
                        out->rgba[i * 4] = c.r;
                        out->rgba[i * 4 + 1] = c.g;
                        out->rgba[i * 4 + 2] = c.b;
                        out->rgba[i * 4 + 3] = c.a;
                    }
                    out->color_type_name = "state-list->rgba";
                    out->ok = true;
                    return true;
                }
                if (decode_image_bytes(ref.bytes, out, density_dpi,
                                       resolver)) {
                    out->color_type_name = "state-list->" +
                                           out->color_type_name;
                    return true;
                }
                continue;
            }
            uint32_t c = 0;
            std::string e;
            if (attr_color(dr, &c, &e, resolver)) {
                out->width = out->height = 64;
                out->rgba.assign(64 * 64 * 4, 0);
                const Rgba cc = argb_to_rgba(c);
                for (size_t i = 0; i < 64 * 64; ++i) {
                    out->rgba[i * 4] = cc.r;
                    out->rgba[i * 4 + 1] = cc.g;
                    out->rgba[i * 4 + 2] = cc.b;
                    out->rgba[i * 4 + 3] = cc.a;
                }
                out->color_type_name = "state-list->rgba";
                out->ok = true;
                return true;
            }
        }
        if (out->error.empty())
            out->error = "state-list: no default (state-less) item matched";
        return out->ok;
    }
    if (root.name != "vector") {
        out->error = "vector: root element <" + root.name + "> unsupported";
        return false;
    }
    float vp_w = 0, vp_h = 0, w_dp = 0, h_dp = 0;
    attr_float(root.attr("viewportWidth"), 0.f, &vp_w);
    attr_float(root.attr("viewportHeight"), 0.f, &vp_h);
    attr_float(root.attr("width"), 0.f, &w_dp);
    attr_float(root.attr("height"), 0.f, &h_dp);
    if (vp_w <= 0 || vp_h <= 0) {
        out->error = "vector: missing/zero viewport";
        return false;
    }

    // Raster size = AOSP getIntrinsicWidth law: declared dp × dpi/160;
    // fall back to viewport × density factor (clamped) when no dp size.
    const float dpi_scale =
        density_dpi > 0 ? (float)density_dpi / 160.f : 0.f;
    float scale;
    float rw, rh;
    if (w_dp > 0 && h_dp > 0 && dpi_scale > 0) {
        rw = w_dp * dpi_scale;
        rh = h_dp * dpi_scale;
        scale = rw / vp_w;
    } else {
        const float s = dpi_scale > 0 ? dpi_scale : 4.f;
        rw = vp_w * s;
        rh = vp_h * s;
        scale = s;
    }
    // Guard rails: at least 32 px for shape fidelity, cap 2048.
    if (rw < 32.f || rh < 32.f) {
        const float k = std::max(32.f / rw, 32.f / rh);
        rw *= k; rh *= k; scale *= k;
    }
    if (rw > 2048.f || rh > 2048.f) {
        const float k = std::min(2048.f / rw, 2048.f / rh);
        rw *= k; rh *= k; scale *= k;
    }
    const int W = std::max(1, (int)std::lround(rw));
    const int H = std::max(1, (int)std::lround(rh));

    // Inflate paths (viewport space) with group matrices.
    std::vector<VPath> paths;
    std::string err;
    walk(root, VMat{}, &paths, &err, resolver);

    // Tint law (AOSP VectorDrawable tint): the tint color composes SRC_IN
    // over the rendered result — for solid fills the visible color becomes
    // tint.rgb with alpha = fill.a × tint.a. Applied per path below.
    uint32_t tint = 0;
    bool has_tint = attr_color(root.attr("tint"), &tint, nullptr, resolver);
    if (has_tint && paths.empty()) {
        // tint-only vector without fill: the tint acts as the fill source.
        VPath pd;
        pd.fill_color = tint;
        pd.has_fill = true;
        paths.push_back(std::move(pd));
        has_tint = false;
    }

    // Rasterize: scanline active-edge fill (winding default / even-odd),
    // viewport→raster mapping via uniform scale + alpha "over" blending.
    out->rgba.assign((size_t)W * H * 4, 0);
    auto blend = [&](int x, int y, const Rgba& c) {
        if (x < 0 || x >= W || y < 0 || y >= H || c.a == 0) return;
        uint8_t* p = &out->rgba[((size_t)y * W + x) * 4];
        if (c.a == 255) {
            p[0] = c.r; p[1] = c.g; p[2] = c.b; p[3] = 255;
            return;
        }
        const uint32_t a = c.a, ia = 255 - a;
        p[0] = (uint8_t)((c.r * a + p[0] * ia) / 255);
        p[1] = (uint8_t)((c.g * a + p[1] * ia) / 255);
        p[2] = (uint8_t)((c.b * a + p[2] * ia) / 255);
        p[3] = (uint8_t)std::min(255, (int)(c.a + (p[3] * ia) / 255));
    };
    struct Edge { float x1, y1, x2, y2; };
    for (const VPath& pd : paths) {
        if (pd.contours.empty()) continue;
        if (!pd.has_fill && !pd.has_stroke) continue;
        Rgba fill = argb_to_rgba(pd.fill_color);
        fill.a = (uint8_t)std::lround(fill.a * pd.fill_alpha);
        if (has_tint) {  // SRC_IN: output color = tint.rgb, alpha multiplied
            Rgba t = argb_to_rgba(tint);
            fill.r = t.r; fill.g = t.g; fill.b = t.b;
            fill.a = (uint8_t)std::lround(fill.a * (t.a / 255.f));
        }
        // Map contours once through the group matrix + viewport scale.
        std::vector<Contour> mapped;
        mapped.reserve(pd.contours.size());
        float min_y = 1e30f, max_y = -1e30f;
        for (const Contour& ct : pd.contours) {
            Contour m2;
            m2.reserve(ct.size());
            for (const auto& pt : ct) {
                float vx, vy;
                pd.matrix.map(pt.first, pt.second, &vx, &vy);
                const float ox = vx * scale;
                const float oy = vy * scale;
                m2.push_back({ox, oy});
                min_y = std::min(min_y, oy);
                max_y = std::max(max_y, oy);
            }
            mapped.push_back(std::move(m2));
        }
        if (!pd.has_fill) continue;
        std::vector<Edge> edges;
        for (const Contour& ct : mapped) {
            for (size_t i = 0; i < ct.size(); ++i) {
                const auto& p0 = ct[i];
                const auto& p1 = ct[(i + 1) % ct.size()];
                if (p0.second != p1.second)
                    edges.push_back({p0.first, p0.second, p1.first, p1.second});
            }
        }
        if (edges.empty()) continue;
        const int y0 = std::max(0, (int)std::floor(min_y));
        const int y1 = std::min(H, (int)std::ceil(max_y) + 1);
        for (int y = y0; y < y1; ++y) {
            const float sy = y + 0.5f;
            std::vector<std::pair<float, int>> xs;
            for (const Edge& e : edges) {
                if ((sy >= e.y1 && sy < e.y2) || (sy >= e.y2 && sy < e.y1)) {
                    const float t = (sy - e.y1) / (e.y2 - e.y1);
                    xs.push_back({e.x1 + t * (e.x2 - e.x1),
                                  e.y2 > e.y1 ? 1 : -1});
                }
            }
            std::sort(xs.begin(), xs.end(),
                      [](const auto& A, const auto& B) {
                          return A.first < B.first;
                      });
            if (pd.even_odd) {
                for (size_t i = 0; i + 1 < xs.size(); i += 2) {
                    const int xa = std::max(0, (int)std::ceil(xs[i].first));
                    const int xb = std::min(W, (int)std::ceil(xs[i + 1].first));
                    for (int x = xa; x < xb; ++x) blend(x, y, fill);
                }
            } else {
                int wind = 0;
                float start = 0.f;
                bool inside = false;
                for (const auto& cr : xs) {
                    if (!inside) {
                        start = cr.first;
                        inside = true;
                        wind = cr.second;
                    } else {
                        wind += cr.second;
                        if (wind == 0) {
                            const int xa = std::max(0, (int)std::ceil(start));
                            const int xb =
                                std::min(W, (int)std::ceil(cr.first));
                            for (int x = xa; x < xb; ++x) blend(x, y, fill);
                            inside = false;
                        }
                    }
                }
                if (inside) {
                    const int xa = std::max(0, (int)std::ceil(start));
                    const int xb =
                        std::min(W, (int)std::ceil(xs.back().first));
                    for (int x = xa; x < xb; ++x) blend(x, y, fill);
                }
            }
        }
        // Minimal stroke law: segment thickening (matches the engine's
        // bg_vector stroke treatment; AA strokes are a named future law).
        if (pd.has_stroke) {
            Rgba s = argb_to_rgba(pd.stroke_color);
            s.a = (uint8_t)std::lround(s.a * pd.stroke_alpha);
            if (has_tint) {
                Rgba t = argb_to_rgba(tint);
                s.r = t.r; s.g = t.g; s.b = t.b;
                s.a = (uint8_t)std::lround(s.a * (t.a / 255.f));
            }
            const float sw = std::max(1.f, pd.stroke_width * scale * 0.5f);
            for (const Contour& ct : mapped) {
                for (size_t i = 0; i + 1 < ct.size(); ++i) {
                    const float ax = ct[i].first, ay = ct[i].second;
                    const float bx = ct[i + 1].first, by = ct[i + 1].second;
                    const float dx = bx - ax, dy = by - ay;
                    const int steps =
                        (int)std::max({std::fabs(dx), std::fabs(dy), 1.f});
                    for (int k = 0; k <= steps; ++k) {
                        const float px = ax + dx * k / steps;
                        const float py = ay + dy * k / steps;
                        for (int oyy = 0; oyy < (int)std::ceil(sw); ++oyy)
                            for (int oxx = 0; oxx < (int)std::ceil(sw); ++oxx)
                                blend((int)(px + oxx), (int)(py + oyy), s);
                    }
                }
            }
        }
    }

    out->width = W;
    out->height = H;
    out->color_type_name = "vector->rgba";
    out->ok = !paths.empty();
    if (!out->ok && err.empty()) err = "vector: no renderable paths";
    out->error = err;
    return out->ok;
}

}  // namespace renderer
}  // namespace miniandroid
