// vector_raster.cpp — S27-W1 (#633/#634) the VectorDrawable rasterization
// law. See vector_raster.h for the law text and the v1 subset contract.
#include "vector_raster.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstring>

namespace miniandroid {
namespace framework {
namespace {

struct Pt { float x, y; };

// One flattened contour = closed point ring (implicit closing segment).
using Ring = std::vector<Pt>;

struct PathBuilder {
    std::vector<Pt> cur;
    std::vector<Ring> rings;
    Pt cur_pt{0, 0}, start_pt{0, 0};
    // last cubic control (for S/s) and last quad control (for T/t)
    Pt last_c2{0, 0}, last_q{0, 0};
    bool has_c2 = false, has_q = false;

    void close() {
        if (!cur.empty()) {
            rings.push_back(std::move(cur));
            cur.clear();
        }
        cur_pt = start_pt;
    }
    void move_to(float x, float y) {
        close();
        cur_pt = start_pt = Pt{x, y};
        cur.push_back(cur_pt);
    }
    void line_to(float x, float y) {
        cur.push_back(Pt{x, y});
        cur_pt = Pt{x, y};
    }
    void emit_cubic(const Pt& a, Pt c1, Pt c2, const Pt& b) {
        // 16 fixed segments — deterministic (see header contract).
        constexpr int kSegs = 16;
        for (int i = 1; i <= kSegs; ++i) {
            const float t = (float)i / kSegs, mt = 1.0f - t;
            const float w0 = mt * mt * mt, w1 = 3 * mt * mt * t,
                        w2 = 3 * mt * t * t, w3 = t * t * t;
            cur.push_back(Pt{w0 * a.x + w1 * c1.x + w2 * c2.x + w3 * b.x,
                             w0 * a.y + w1 * c1.y + w2 * c2.y + w3 * b.y});
        }
        cur_pt = b;
        last_c2 = c2;
        has_c2 = true;
        has_q = false;
    }
    void emit_quad(const Pt& a, const Pt& q, const Pt& b) {
        // Quadratic → cubic (standard degree elevation).
        emit_cubic(a, Pt{a.x + 2.0f / 3 * (q.x - a.x),
                         a.y + 2.0f / 3 * (q.y - a.y)},
                   Pt{b.x + 2.0f / 3 * (q.x - b.x),
                     b.y + 2.0f / 3 * (q.y - b.y)},
                   b);
        last_q = q;
        has_q = true;
    }
};

// SVG arc (endpoint parameterization) → cubics. W3C SVG 1.1 F.6.5,
// clamped radii per F.6.6. ≤4 cubics per ≤90° arc slice.
void emit_arc(PathBuilder& b, const Pt& from, float rx, float ry,
              float xrot_deg, bool large_arc, bool sweep, const Pt& to) {
    if (std::fabs(from.x - to.x) < 1e-6f && std::fabs(from.y - to.y) < 1e-6f)
        return;
    rx = std::fabs(rx);
    ry = std::fabs(ry);
    if (rx < 1e-6f || ry < 1e-6f) {
        b.line_to(to.x, to.y);
        return;
    }
    const float phi = xrot_deg * (float)M_PI / 180.0f;
    const float cphi = std::cos(phi), sphi = std::sin(phi);
    const float dx2 = (from.x - to.x) / 2, dy2 = (from.y - to.y) / 2;
    const float x1 = cphi * dx2 + sphi * dy2;
    const float y1 = -sphi * dx2 + cphi * dy2;
    float lambda = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry);
    if (lambda > 1.0f) {
        const float s = std::sqrt(lambda);
        rx *= s;
        ry *= s;
    }
    const float rx2 = rx * rx, ry2 = ry * ry;
    float num = rx2 * ry2 - rx2 * y1 * y1 - ry2 * x1 * x1;
    if (num < 0) num = 0;
    const float den = rx2 * y1 * y1 + ry2 * x1 * x1;
    float co = den > 1e-12f ? std::sqrt(num / den) : 0.0f;
    if (large_arc == sweep) co = -co;
    const float cx0 = co * rx * y1 / ry, cy0 = -co * ry * x1 / rx;
    const float cx = cphi * cx0 - sphi * cy0 + (from.x + to.x) / 2;
    const float cy = sphi * cx0 + cphi * cy0 + (from.y + to.y) / 2;
    auto angle_of = [&](float ux, float uy) {
        const float dot = ux * cphi + uy * sphi;
        const float len = std::sqrt(ux * ux + uy * uy);
        float ang = std::acos(std::clamp(ux / len, -1.0f, 1.0f));
        if (dot < 0) ang = -ang;
        return ang;
    };
    const float th1 = angle_of((x1 - cx0) / rx, (y1 - cy0) / ry);
    float dth = angle_of((-x1 - cx0) / rx, (-y1 - cy0) / ry) - th1;
    if (!sweep && dth > 0) dth -= 2 * (float)M_PI;
    if (sweep && dth < 0) dth += 2 * (float)M_PI;
    // Slice into ≤90° segments.
    const int nseg =
        std::max(1, (int)std::ceil(std::fabs(dth) / ((float)M_PI / 2)));
    const float dts = dth / nseg;
    const float t43 = 4.0f / 3 * std::tan(dts / 4);
    float th = th1;
    Pt p0 = from;
    for (int i = 0; i < nseg; ++i) {
        const float th2 = th + dts;
        auto pt_on = [&](float a) {
            return Pt{cx + rx * (cphi * std::cos(a) - sphi * std::sin(a)),
                      cy + ry * (sphi * std::cos(a) + cphi * std::sin(a))};
        };
        const Pt p1 = pt_on(th2);
        auto deriv = [&](float a, float sgn) {
            const float ca = std::cos(a), sa = std::sin(a);
            return Pt{sgn * rx * (-cphi * sa - sphi * ca),
                      sgn * ry * (-sphi * sa + cphi * ca)};
        };
        const Pt d1 = deriv(th, sweep ? 1 : -1), d2 = deriv(th2, sweep ? 1 : -1);
        b.emit_cubic(p0, Pt{p0.x + t43 * d1.x, p0.y + t43 * d1.y},
                     Pt{p1.x - t43 * d2.x, p1.y - t43 * d2.y}, p1);
        p0 = p1;
        th = th2;
    }
}

// pathData parser → flattened rings in the VECTOR viewport space.
bool parse_pathdata(const std::string& d, std::vector<Ring>& rings,
                    int& contours) {
    PathBuilder b;
    const char* p = d.c_str();
    const char* end = p + d.size();
    char cmd = 0;
    bool first = true;
    while (p < end) {
        while (p < end && (*p == ' ' || *p == ',' || *p == '\n' || *p == '\t' ||
                           *p == '\r'))
            ++p;
        if (p >= end) break;
        if (strchr("MmLlHhVvCcSsQqTtAaZz", *p)) {
            cmd = *p++;
            first = true;
            continue;
        }
        if (!cmd) return false;
        const bool rel = cmd >= 'a' && cmd <= 'z';
        auto read_num = [&](float& v) -> bool {
            while (p < end && (*p == ' ' || *p == ',')) ++p;
            if (p >= end) return false;
            const char* s = p;
            if (*p == '+' || *p == '-') ++p;
            bool dot = false, any = false;
            while (p < end) {
                const char c = *p;
                if (c >= '0' && c <= '9') { any = true; ++p; }
                else if (c == '.' && !dot) { dot = true; ++p; }
                else break;
            }
            if (!any) { p = s; return false; }
            v = strtof(s, nullptr);
            return true;
        };
        float a1 = 0, a2 = 0, a3 = 0, a4 = 0, a5 = 0, a6 = 0, a7 = 0;
        switch (cmd) {
            case 'M': case 'm': {
                if (!read_num(a1) || !read_num(a2)) return false;
                const float x = rel ? b.cur_pt.x + a1 : a1;
                const float y = rel ? b.cur_pt.y + a2 : a2;
                b.move_to(x, y);
                ++contours;
                // Subsequent implicit pairs are Lineto (SVG law).
                cmd = rel ? 'l' : 'L';
                break;
            }
            case 'L': case 'l': {
                if (!read_num(a1) || !read_num(a2)) return false;
                b.line_to(rel ? b.cur_pt.x + a1 : a1,
                          rel ? b.cur_pt.y + a2 : a2);
                break;
            }
            case 'H': case 'h': {
                if (!read_num(a1)) return false;
                b.line_to(rel ? b.cur_pt.x + a1 : a1, b.cur_pt.y);
                break;
            }
            case 'V': case 'v': {
                if (!read_num(a1)) return false;
                b.line_to(b.cur_pt.x, rel ? b.cur_pt.y + a1 : a1);
                break;
            }
            case 'C': case 'c': {
                if (!read_num(a1) || !read_num(a2) || !read_num(a3) ||
                    !read_num(a4) || !read_num(a5) || !read_num(a6))
                    return false;
                const Pt a = b.cur_pt;
                const Pt c1{rel ? a.x + a1 : a1, rel ? a.y + a2 : a2};
                const Pt c2{rel ? a.x + a3 : a3, rel ? a.y + a4 : a4};
                const Pt e{rel ? a.x + a5 : a5, rel ? a.y + a6 : a6};
                b.emit_cubic(a, c1, c2, e);
                break;
            }
            case 'S': case 's': {
                if (!read_num(a1) || !read_num(a2) || !read_num(a3) ||
                    !read_num(a4))
                    return false;
                const Pt a = b.cur_pt;
                const Pt c1 = (b.has_c2 && !first)
                                  ? Pt{2 * a.x - b.last_c2.x,
                                       2 * a.y - b.last_c2.y}
                                  : a;
                const Pt c2{rel ? a.x + a1 : a1, rel ? a.y + a2 : a2};
                const Pt e{rel ? a.x + a3 : a3, rel ? a.y + a4 : a4};
                b.emit_cubic(a, c1, c2, e);
                break;
            }
            case 'Q': case 'q': {
                if (!read_num(a1) || !read_num(a2) || !read_num(a3) ||
                    !read_num(a4))
                    return false;
                const Pt a = b.cur_pt;
                b.emit_quad(a, Pt{rel ? a.x + a1 : a1, rel ? a.y + a2 : a2},
                            Pt{rel ? a.x + a3 : a3, rel ? a.y + a4 : a4});
                break;
            }
            case 'T': case 't': {
                if (!read_num(a1) || !read_num(a2)) return false;
                const Pt a = b.cur_pt;
                const Pt q = (b.has_q && !first)
                                 ? Pt{2 * a.x - b.last_q.x,
                                      2 * a.y - b.last_q.y}
                                 : a;
                b.emit_quad(a, q, Pt{rel ? a.x + a1 : a1,
                                     rel ? a.y + a2 : a2});
                break;
            }
            case 'A': case 'a': {
                if (!read_num(a1) || !read_num(a2) || !read_num(a3) ||
                    !read_num(a4) || !read_num(a5) || !read_num(a6) ||
                    !read_num(a7))
                    return false;
                const Pt a = b.cur_pt;
                const Pt e{rel ? a.x + a6 : a6, rel ? a.y + a7 : a7};
                emit_arc(b, a, a1, a2, a3, a4 != 0, a5 != 0, e);
                break;
            }
            case 'Z': case 'z': {
                b.close();
                break;
            }
            default:
                return false;
        }
        first = false;
    }
    b.close();
    rings = std::move(b.rings);
    return !rings.empty();
}

uint32_t parse_color(const resources::ResValue& v, const std::string& raw) {
    uint32_t argb = 0;
    if (v.is_color()) return v.data;  // 0xAARRGGBB from the typed entry
    // String form: #RRGGBB / #AARRGGBB / #RGB / #ARGB.
    std::string s = raw;
    if (!s.empty() && s[0] == '#') s = s.substr(1);
    auto hexv = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    };
    if (s.size() == 6 || s.size() == 8) {
        uint32_t acc = 0;
        bool ok = true;
        for (char c : s) {
            const int h = hexv(c);
            if (h < 0) { ok = false; break; }
            acc = acc * 16 + (uint32_t)h;
        }
        if (ok) argb = s.size() == 6 ? (0xFF000000u | acc) : acc;
    } else if (s.size() == 3 || s.size() == 4) {
        uint32_t acc = 0;
        bool ok = true;
        for (char c : s) {
            const int h = hexv(c);
            if (h < 0) { ok = false; break; }
            acc = acc * 16 + (uint32_t)h * 16 + (uint32_t)h;
        }
        if (ok) argb = s.size() == 3 ? (0xFF000000u | acc) : acc;
    }
    return argb;
}

}  // namespace

bool vector_rasterize(const resources::AxmlElement& root, int w, int h,
                      std::vector<uint8_t>& rgba, VectorRasterStats& stats) {
    if (w <= 0 || h <= 0) return false;
    // Viewport → bounds mapping: aspect-preserving, centered (AOSP
    // VectorDrawable.draw: canvas.scale(w/vbW, h/vbH) with the viewport
    // translated so content centers — the min-scale + center law).
    float vbw = 0, vbh = 0;
    const resources::AxmlAttribute* vw = root.attr("viewportWidth");
    const resources::AxmlAttribute* vh = root.attr("viewportHeight");
    if (vw) std::memcpy(&vbw, &vw->value.data, 4);
    if (vh) std::memcpy(&vbh, &vh->value.data, 4);
    if (vbw <= 0 || vbh <= 0) {
        vbw = (float)w;
        vbh = (float)h;
    }
    const float s = std::min((float)w / vbw, (float)h / vbh);
    const float ox = ((float)w - vbw * s) / 2.0f;
    const float oy = ((float)h - vbh * s) / 2.0f;

    rgba.assign((size_t)w * h * 4, 0);
    bool any = false;
    for (const auto& el : root.children) {
        if (el.name != "path") continue;
        ++stats.paths;
        const resources::AxmlAttribute* pd = el.attr("pathData");
        if (!pd || pd->value.string_value.empty()) {
            ++stats.skipped_paths;
            if (stats.first_skip.empty())
                stats.first_skip = "path without pathData";
            continue;
        }
        std::vector<Ring> rings;
        int contours = 0;
        if (!parse_pathdata(pd->value.string_value, rings, contours)) {
            ++stats.skipped_paths;
            if (stats.first_skip.empty())
                stats.first_skip = "pathData parse failure: " +
                                   pd->value.string_value.substr(0, 32);
            continue;
        }
        stats.contours += contours;
        // fillColor: typed COLOR entry or "#aarrggbb" string; fillAlpha
        // (FLOAT, default 1) multiplies the color's alpha.
        uint32_t argb = 0;
        const resources::AxmlAttribute* fc = el.attr("fillColor");
        if (fc) argb = parse_color(fc->value, fc->value.string_value);
        float fill_alpha = 1.0f;
        const resources::AxmlAttribute* fa = el.attr("fillAlpha");
        if (fa) std::memcpy(&fill_alpha, &fa->value.data, 4);
        if (!fc || (argb >> 24) == 0) {
            if (!fc) {
                ++stats.skipped_paths;
                if (stats.first_skip.empty())
                    stats.first_skip = "path without fillColor (stroke-only?)";
                continue;
            }
        }
        float alpha = ((float)(argb >> 24)) / 255.0f * fill_alpha;
        if (alpha <= 0.0f) { ++stats.painted_paths; continue; }
        const float cr = (float)((argb >> 16) & 0xFF);
        const float cg = (float)((argb >> 8) & 0xFF);
        const float cb = (float)(argb & 0xFF);
        // Device-space edges (even-odd scanline fill).
        std::vector<float> ex0, ey0, ex1, ey1;
        for (const auto& ring : rings) {
            for (size_t i = 0; i < ring.size(); ++i) {
                const Pt& a = ring[i];
                const Pt& bpt = ring[(i + 1) % ring.size()];
                const float y0 = oy + a.y * s, y1 = oy + bpt.y * s;
                if (std::fabs(y0 - y1) < 1e-6f) continue;
                ex0.push_back(ox + a.x * s);
                ey0.push_back(y0);
                ex1.push_back(ox + bpt.x * s);
                ey1.push_back(y1);
            }
        }
        std::vector<float> xs;
        xs.reserve(16);
        for (int y = 0; y < h; ++y) {
            const float sy = (float)y + 0.5f;
            xs.clear();
            for (size_t e = 0; e < ex0.size(); ++e) {
                const float y0 = ey0[e], y1 = ey1[e];
                if ((y0 <= sy && y1 > sy) || (y1 <= sy && y0 > sy)) {
                    xs.push_back(ex0[e] +
                                 (sy - y0) * (ex1[e] - ex0[e]) / (y1 - y0));
                }
            }
            if (xs.size() < 2) continue;
            std::sort(xs.begin(), xs.end());
            for (size_t i = 0; i + 1 < xs.size(); i += 2) {
                int x0 = (int)std::ceil(xs[i] - 0.5f);
                int x1 = (int)std::ceil(xs[i + 1] - 0.5f);
                if (x0 < 0) x0 = 0;
                if (x1 > w) x1 = w;
                for (int x = x0; x < x1; ++x) {
                    uint8_t* px = &rgba[((size_t)y * w + x) * 4];
                    // Over-composite (later paths paint over earlier).
                    const float inv = 1.0f - alpha;
                    px[0] = (uint8_t)(cb * alpha + px[0] * inv);
                    px[1] = (uint8_t)(cg * alpha + px[1] * inv);
                    px[2] = (uint8_t)(cr * alpha + px[2] * inv);
                    px[3] = (uint8_t)std::min(
                        255.0f, alpha * 255.0f + px[3]);
                }
            }
        }
        ++stats.painted_paths;
        any = true;
    }
    return any;
}

}  // namespace framework
}  // namespace miniandroid
