// S109 WEBVIEW-ENGINE — Canvas2D implementation. See canvas2d.h for laws.
#include "canvas2d.h"
#include "text_shaper.h"
#include <algorithm>
#include <cmath>

namespace miniandroid { namespace webview {

uint32_t parse_css_color(const std::string& s0, bool& ok) {
    ok = true;
    std::string s = s0;
    for (auto& c : s) c = char(::tolower((unsigned char)c));
    size_t a = s.find_first_not_of(" \t");
    if (a == std::string::npos) { ok = false; return 0xff000000; }
    size_t b = s.find_last_not_of(" \t");
    s = s.substr(a, b - a + 1);
    auto pack = [](int r, int g, int bl, int al) {
        return (uint32_t(std::clamp(al,0,255)) << 24) | (uint32_t(std::clamp(bl,0,255)) << 16) |
               (uint32_t(std::clamp(g,0,255)) << 8) | uint32_t(std::clamp(r,0,255));
    };
    if (!s.empty() && s[0] == '#') {
        std::string h = s.substr(1);
        auto hexv = [&](const std::string& hs) -> int {
            int v = 0; for (char c : hs) { v *= 16;
                if (c >= '0' && c <= '9') v += c - '0';
                else if (c >= 'a' && c <= 'f') v += c - 'a' + 10; else return -1; }
            return v; };
        if (h.size() == 3) { int r = hexv(h.substr(0, 1)); if (r < 0) { ok = false; return 0xff000000; }
            r = r * 17; return pack(r, r, r, 255); }
        if (h.size() == 6) { int v = hexv(h); if (v < 0) { ok = false; return 0xff000000; }
            return pack((v >> 16) & 255, (v >> 8) & 255, v & 255, 255); }
        if (h.size() == 8) { int v = hexv(h); if (v < 0) { ok = false; return 0xff000000; }
            return pack((v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255); }
        ok = false; return 0xff000000;
    }
    if (s.rfind("rgba", 0) == 0 || s.rfind("rgb", 0) == 0) {
        size_t p1 = s.find('('), p2 = s.rfind(')');
        if (p1 == std::string::npos || p2 == std::string::npos) { ok = false; return 0xff000000; }
        float comps[4] = {0, 0, 0, 255}; int ci = 0; std::string cur; bool pct = false;
        for (size_t i = p1 + 1; i <= p2; ++i) {
            char c = i < p2 ? s[i] : ',';
            if (c == ',' || i == p2) {
                if (!cur.empty()) {
                    float v = ::atof(cur.c_str());
                    if (cur.back() == '%') { v = v * 255.f / 100.f; pct = true; }
                    if (ci < 4) comps[ci] = v;
                    ++ci;
                }
                cur.clear();
            } else if (c != ' ' && c != '/') cur += c;
        }
        int al = comps[3] > 1.f || pct ? int(comps[3] * (pct ? 255.f / 100.f : 1.f) + .5f)
                                       : int(comps[3] * 255.f + .5f);
        return pack(int(comps[0] + .5f), int(comps[1] + .5f), int(comps[2] + .5f), al);
    }
    struct NV { const char* n; uint32_t c; };
    static const NV kNamed[] = {
        {"white", 0xffffffff}, {"black", 0xff000000}, {"red", 0xffff0000},
        {"green", 0xff008000}, {"lime", 0xff00ff00}, {"blue", 0xff0000ff},
        {"yellow", 0xffffff00}, {"orange", 0xffffa500}, {"purple", 0xff800080},
        {"gray", 0xff808080}, {"grey", 0xff808080}, {"silver", 0xffc0c0c0},
        {"transparent", 0x00000000}, {"aqua", 0xff00ffff}, {"cyan", 0xff00ffff},
        {"fuchsia", 0xffff00ff}, {"magenta", 0xffff00ff}, {"maroon", 0xff800000},
        {"navy", 0xff000080}, {"olive", 0xff808000}, {"teal", 0xff008080},
        {"gold", 0xffffd700}, {"pink", 0xffffc0cb}, {"brown", 0xffa52a2a},
    };
    for (auto& nv : kNamed) if (s == nv.n) return nv.c;
    ok = false;
    return 0xff000000;
}

std::string parse_font_family(const std::string& css_font) {
    // last comma-separated token after the size is the family
    size_t px = css_font.rfind("px");
    std::string rest = px == std::string::npos ? css_font : css_font.substr(px + 2);
    size_t a = rest.find_first_not_of(" \t");
    if (a == std::string::npos) return "sans-serif";
    std::string fam = rest.substr(a);
    // strip quotes
    fam.erase(std::remove(fam.begin(), fam.end(), '"'), fam.end());
    fam.erase(std::remove(fam.begin(), fam.end(), '\''), fam.end());
    size_t comma = fam.find(',');
    if (comma != std::string::npos) fam = fam.substr(0, comma);
    size_t b = fam.find_last_not_of(" \t");
    if (b == std::string::npos) return "sans-serif";
    return fam.substr(0, b + 1);
}

float parse_font_size(const std::string& css_font) {
    size_t px = css_font.find("px");
    if (px == std::string::npos) return 10.f;
    size_t s = px;
    while (s > 0 && (::isdigit((unsigned char)css_font[s - 1]) || css_font[s - 1] == '.')) --s;
    size_t sp = css_font.rfind(' ', s);
    std::string num = css_font.substr(s, px - s);
    if (sp != std::string::npos && sp >= s - 0 && sp < s) num = css_font.substr(sp + 1, px - sp - 1);
    float v = ::atof(num.c_str());
    return v > 0 ? v : 10.f;
}

bool parse_font_bold(const std::string& css_font) {
    return css_font.find("bold") != std::string::npos;
}

// ── state ───────────────────────────────────────────────────────────────
void Canvas2D::set_size(int w, int h) {
    fb_ = std::make_unique<renderer::FrameBuffer>(std::max(1, w), std::max(1, h));
    has_clip_ = false;
    stack_.clear();
    path_.clear();
}

void Canvas2D::save() {
    stack_.push_back({fill_style, stroke_style, fill_rgba_, stroke_rgba_, fill_ok_, stroke_ok_,
                      global_alpha, global_composite_operation, line_width,
                      font, text_align, text_baseline,
                      m_a, m_b, m_c, m_d, m_e, m_f, clip_, has_clip_,
                      fill_pat_, stroke_pat_});
}
void Canvas2D::restore() {
    if (stack_.empty()) return;  // WHATWG: empty stack = no-op
    auto& s = stack_.back();
    fill_style = s.fill_style; stroke_style = s.stroke_style;
    fill_rgba_ = s.fill_rgba; stroke_rgba_ = s.stroke_rgba;
    fill_ok_ = s.fill_ok; stroke_ok_ = s.stroke_ok;
    global_alpha = s.global_alpha; global_composite_operation = s.gco;
    line_width = s.line_width; font = s.font; text_align = s.text_align;
    text_baseline = s.text_baseline;
    m_a = s.m_a; m_b = s.m_b; m_c = s.m_c; m_d = s.m_d; m_e = s.m_e; m_f = s.m_f;
    clip_ = s.clip; has_clip_ = s.has_clip;
    fill_pat_ = s.fill_pat; stroke_pat_ = s.stroke_pat;
    stack_.pop_back();
}
void Canvas2D::set_transform(float a, float b, float c, float d, float e, float f) {
    m_a = a; m_b = b; m_c = c; m_d = d; m_e = e; m_f = f;
}
void Canvas2D::transform(float a, float b, float c, float d, float e, float f) {
    float na = m_a * a + m_c * b, nb = m_b * a + m_d * b;
    float nc = m_a * c + m_c * d, nd = m_b * c + m_d * d;
    float ne = m_a * e + m_c * f + m_e, nf = m_b * e + m_d * f + m_f;
    m_a = na; m_b = nb; m_c = nc; m_d = nd; m_e = ne; m_f = nf;
}
void Canvas2D::rotate(float rad) {
    float cs = ::cosf(rad), sn = ::sinf(rad);
    transform(cs, sn, -sn, cs, 0, 0);
}

// ── pixel compositing ───────────────────────────────────────────────────
void Canvas2D::blend_pixel(int x, int y, uint32_t color, float alpha) {
    if (x < 0 || y < 0 || x >= fb_->get_width() || y >= fb_->get_height()) return;
    if (!in_clip(x, y)) return;
    float a = ((color >> 24) & 255) / 255.f * alpha * global_alpha;
    if (a <= 0) return;
    const std::string& gco = global_composite_operation;
    if (gco == "source-over" || gco.empty()) {
        // FrameBuffer set_pixel blend = src-over on opaque targets
        uint32_t al = uint32_t(std::min(255.f, a * 255.f + (global_alpha >= 1.f ? 0.f : 0.f) + .5f));
        renderer::RGBA c{uint8_t(color & 255), uint8_t((color >> 8) & 255),
                         uint8_t((color >> 16) & 255), uint8_t(al)};
        fb_->set_pixel(x, y, c);
        return;
    }
    // manual per-pixel compositing (read-modify-write, opaque write)
    renderer::RGBA d = fb_->get_pixel(x, y);
    float da = d.a / 255.f;
    float dr = d.r / 255.f, dg = d.g / 255.f, db = d.b / 255.f;
    float sr = (color & 255) / 255.f, sg = ((color >> 8) & 255) / 255.f, sb = ((color >> 16) & 255) / 255.f;
    float orr, og, ob, oa;
    if (gco == "lighter") {
        orr = std::min(1.f, dr + sr * a); og = std::min(1.f, dg + sg * a); ob = std::min(1.f, db + sb * a);
        oa = std::min(1.f, da + a);
    } else if (gco == "destination-out") {
        oa = da * (1 - a); orr = dr; og = dg; ob = db;
    } else if (gco == "destination-over") {
        orr = dr * (1 - a) + sr * a * 0 + sr * (1 - da) * 0 + sr * 0;  // dst under src
        orr = dr + sr * (1 - da) * 0;  // simplified: dst wins where opaque
        orr = sr * (1 - da) + dr; og = sg * (1 - da) + dg; ob = sb * (1 - da) + db;
        orr = std::min(1.f, orr); og = std::min(1.f, og); ob = std::min(1.f, ob);
        oa = std::min(1.f, da + a * (1 - da));
    } else if (gco == "multiply") {
        orr = dr * sr * a + dr * (1 - a); og = dg * sg * a + dg * (1 - a);
        ob = db * sb * a + db * (1 - a);
        oa = da + a * (1 - da);
    } else if (gco == "screen") {
        orr = (1 - (1 - dr) * (1 - sr)) * a + dr * (1 - a);
        og = (1 - (1 - dg) * (1 - sg)) * a + dg * (1 - a);
        ob = (1 - (1 - db) * (1 - sb)) * a + db * (1 - a);
        oa = da + a * (1 - da);
    } else if (gco == "overlay") {
        auto ov = [](float b_, float s_) { return b_ < .5f ? 2 * b_ * s_ : 1 - 2 * (1 - b_) * (1 - s_); };
        orr = ov(dr, sr) * a + dr * (1 - a); og = ov(dg, sg) * a + dg * (1 - a);
        ob = ov(db, sb) * a + db * (1 - a);
        oa = da + a * (1 - da);
    } else {
        // WHATWG law: unknown/unsupported operator → assignment IGNORED;
        // the state keeps its previous value, so this branch should not
        // fire — but if it does, fall back to source-over (honest default).
        renderer::RGBA c{uint8_t(color & 255), uint8_t((color >> 8) & 255),
                         uint8_t((color >> 16) & 255), uint8_t(a * 255.f + .5f)};
        fb_->set_pixel(x, y, c);
        return;
    }
    fb_->set_pixel(x, y, renderer::RGBA{uint8_t(orr * 255 + .5f), uint8_t(og * 255 + .5f),
                                        uint8_t(ob * 255 + .5f), uint8_t(oa * 255 + .5f)});
}

void Canvas2D::blend_hline(int y, int x0, int x1, uint32_t color, float alpha) {
    if (x0 > x1) std::swap(x0, x1);
    for (int x = std::max(0, x0); x <= std::min(fb_->get_width() - 1, x1); ++x)
        blend_pixel(x, y, color, alpha);
}

void Canvas2D::fill_poly_gradient(const std::vector<PathPoint>& pts, const Gradient& g) {
    if (pts.size() < 3 || fb_->get_pixel_count() == 0) return;
    float miny = 1e9f, maxy = -1e9f, minx = 1e9f, maxx = -1e9f;
    for (auto& p : pts) {
        miny = std::min(miny, p.y); maxy = std::max(maxy, p.y);
        minx = std::min(minx, p.x); maxx = std::max(maxx, p.x);
    }
    int y0 = std::max(0, int(::floorf(miny))), y1 = std::min(fb_->get_height() - 1, int(::ceilf(maxy)));
    int x0c = std::max(0, int(::floorf(minx))), x1c = std::min(fb_->get_width() - 1, int(::ceilf(maxx)));
    std::vector<float> xs;
    for (int y = y0; y <= y1; ++y) {
        float cy = y + 0.5f;
        xs.clear();
        for (size_t i = 0; i < pts.size(); ++i) {
            const auto& p1 = pts[i];
            const auto& p2 = pts[(i + 1) % pts.size()];
            if ((p1.y <= cy && p2.y > cy) || (p2.y <= cy && p1.y > cy)) {
                float t = (cy - p1.y) / (p2.y - p1.y);
                xs.push_back(p1.x + t * (p2.x - p1.x));
            }
        }
        std::sort(xs.begin(), xs.end());
        for (size_t i = 0; i + 1 < xs.size(); i += 2) {
            int sx = std::max(x0c, int(::floorf(xs[i])));
            int ex = std::min(x1c, int(::ceilf(xs[i + 1])));
            for (int x = sx; x <= ex; ++x) {
                if (!in_clip(x, y)) continue;
                float ux, uy; inv_map_point(float(x) + .5f, float(y) + .5f, ux, uy);
                float t;
                if (g.type == 0) {
                    float dx = g.x1 - g.x0, dy = g.y1 - g.y0;
                    float len2 = dx * dx + dy * dy;
                    t = len2 > 1e-9f ? ((ux - g.x0) * dx + (uy - g.y0) * dy) / len2 : 0.f;
                } else {
                    float d = ::sqrtf((ux - g.x0) * (ux - g.x0) + (uy - g.y0) * (uy - g.y0));
                    t = (g.r1 - g.r0) > 1e-6f ? (d - g.r0) / (g.r1 - g.r0) : 0.f;
                }
                blend_pixel(x, y, g.color_at(std::clamp(t, 0.f, 1.f)), 1.f);
            }
        }
    }
}

void Canvas2D::fill_poly_scanline(const std::vector<PathPoint>& pts, uint32_t color, float alpha) {
    if (pts.size() < 3 || fb_->get_pixel_count() == 0) return;
    float miny = 1e9f, maxy = -1e9f;
    for (auto& p : pts) { miny = std::min(miny, p.y); maxy = std::max(maxy, p.y); }
    int y0 = std::max(0, int(::floorf(miny))), y1 = std::min(fb_->get_height() - 1, int(::ceilf(maxy)));
    std::vector<float> xs;
    for (int y = y0; y <= y1; ++y) {
        float cy = y + 0.5f;
        xs.clear();
        for (size_t i = 0; i < pts.size(); ++i) {
            const auto& p1 = pts[i];
            const auto& p2 = pts[(i + 1) % pts.size()];
            if ((p1.y <= cy && p2.y > cy) || (p2.y <= cy && p1.y > cy)) {
                float t = (cy - p1.y) / (p2.y - p1.y);
                xs.push_back(p1.x + t * (p2.x - p1.x));
            }
        }
        std::sort(xs.begin(), xs.end());
        for (size_t i = 0; i + 1 < xs.size(); i += 2)
            blend_hline(y, int(::floorf(xs[i])), int(::ceilf(xs[i + 1])), color, alpha);
    }
}

void Canvas2D::stroke_polyline(const std::vector<PathPoint>& pts, uint32_t color, float alpha, float width) {
    int w = std::max(1, int(width + .5f));
    for (size_t i = 0; i + 1 < pts.size(); ++i) {
        float x0 = pts[i].x, y0 = pts[i].y, x1 = pts[i + 1].x, y1 = pts[i + 1].y;
        int steps = std::max(1, int(std::max(::fabsf(x1 - x0), ::fabsf(y1 - y0)) * 2));
        for (int s = 0; s <= steps; ++s) {
            float t = float(s) / steps;
            float px = x0 + t * (x1 - x0), py = y0 + t * (y1 - y0);
            for (int dy = 0; dy < w; ++dy)
                for (int dx = 0; dx < w; ++dx)
                    blend_pixel(int(px) + dx - w / 2, int(py) + dy - w / 2, color, alpha);
        }
    }
}

void Canvas2D::map_point(float x, float y, float& ox, float& oy) const {
    ox = m_a * x + m_c * y + m_e;
    oy = m_b * x + m_d * y + m_f;
}
void Canvas2D::inv_map_point(float px, float py, float& ox, float& oy) const {
    float det = m_a * m_d - m_b * m_c;
    if (::fabsf(det) < 1e-9f) { ox = px; oy = py; return; }
    float tx = px - m_e, ty = py - m_f;
    ox = (m_d * tx - m_c * ty) / det;
    oy = (-m_b * tx + m_a * ty) / det;
}

// ── rect ops ────────────────────────────────────────────────────────────
void Canvas2D::fill_rect(float x, float y, float w, float h) {
    if (fb_->get_pixel_count() == 0) return;
    ++draw_calls;
    sync_colors();
    if (fill_gradient) {
        float px_[4], py_[4];
        map_point(x, y, px_[0], py_[0]); map_point(x + w, y, px_[1], py_[1]);
        map_point(x + w, y + h, px_[2], py_[2]); map_point(x, y + h, px_[3], py_[3]);
        std::vector<PathPoint> poly{{px_[0], py_[0]}, {px_[1], py_[1]}, {px_[2], py_[2]}, {px_[3], py_[3]}};
        fill_poly_gradient(poly, *fill_gradient);
        return;
    }
    if (fill_pat_) {
        for (int yy = 0; yy < int(h); ++yy)
            for (int xx = 0; xx < int(w); ++xx) {
                float mx, my; map_point(x + xx, y + yy, mx, my);
                int tw = fill_pat_->tile->get_width(), th = fill_pat_->tile->get_height();
                int tx = ((int(mx) % tw) + tw) % tw, ty = ((int(my) % th) + th) % th;
                auto c = fill_pat_->tile->get_pixel(tx, ty);
                blend_pixel(int(mx), int(my),
                            (uint32_t(c.a) << 24) | (uint32_t(c.b) << 16) |
                            (uint32_t(c.g) << 8) | c.r, c.a / 255.f);
            }
        return;
    }
    float px_[4], py_[4];
    map_point(x, y, px_[0], py_[0]); map_point(x + w, y, px_[1], py_[1]);
    map_point(x + w, y + h, px_[2], py_[2]); map_point(x, y + h, px_[3], py_[3]);
    std::vector<PathPoint> poly{{px_[0], py_[0]}, {px_[1], py_[1]}, {px_[2], py_[2]}, {px_[3], py_[3]}};
    fill_poly_scanline(poly, fill_rgba_, 1.f);
}

void Canvas2D::stroke_rect(float x, float y, float w, float h) {
    fill_rect(x, y, w, line_width);
    fill_rect(x, y + h - line_width, w, line_width);
    fill_rect(x, y, line_width, h);
    fill_rect(x + w - line_width, y, line_width, h);
}

void Canvas2D::clear_rect(float x, float y, float w, float h) {
    ++draw_calls;
    std::string prev_gco = global_composite_operation;
    std::string prev_fs = fill_style;
    float prev_a = global_alpha;
    global_composite_operation = "destination-out";
    fill_style = "#00000000";
    global_alpha = 1.f;
    fill_rect(x, y, w, h);
    global_composite_operation = prev_gco;
    fill_style = prev_fs;
    global_alpha = prev_a;
}

// ── path ops ────────────────────────────────────────────────────────────
void Canvas2D::close_path() {
    if (!path_.empty()) path_.push_back(path_.front());
}
void Canvas2D::move_to(float x, float y) {
    PathPoint p; map_point(x, y, p.x, p.y);
    path_.push_back(p);
}
void Canvas2D::line_to(float x, float y) {
    PathPoint p; map_point(x, y, p.x, p.y);
    path_.push_back(p);
}
void Canvas2D::arc(float cx, float cy, float r, float a0, float a1, bool ccw) {
    float sweep = a1 - a0;
    if (ccw && sweep > 0) sweep -= 2.f * float(M_PI);
    if (!ccw && sweep < 0) sweep += 2.f * float(M_PI);
    if (!ccw && sweep == 0) sweep = 2.f * float(M_PI);  // equal angles → full circle law
    int steps = std::max(8, int(::fabsf(sweep) / 0.08f));
    for (int i = 0; i <= steps; ++i) {
        float a = a0 + sweep * float(i) / steps;
        float x = cx + r * ::cosf(a), y = cy + r * ::sinf(a);
        if (path_.empty() && i == 0) move_to(x, y); else line_to(x, y);
    }
}
void Canvas2D::quadratic_curve_to(float cpx, float cpy, float x, float y) {
    if (path_.empty()) move_to(cpx, cpy);
    PathPoint p0 = path_.back();
    float qx0, qy0; map_point(cpx, cpy, qx0, qy0);
    float qx1, qy1; map_point(x, y, qx1, qy1);
    int steps = 24;
    for (int i = 1; i <= steps; ++i) {
        float t = float(i) / steps;
        float mx = (1-t)*(1-t)*p0.x + 2*(1-t)*t*qx0 + t*t*qx1;
        float my = (1-t)*(1-t)*p0.y + 2*(1-t)*t*qy0 + t*t*qy1;
        path_.push_back({mx, my});
    }
}
void Canvas2D::bezier_curve_to(float c1x, float c1y, float c2x, float c2y, float x, float y) {
    if (path_.empty()) move_to(c1x, c1y);
    PathPoint p0 = path_.back();
    float b1x, b1y; map_point(c1x, c1y, b1x, b1y);
    float b2x, b2y; map_point(c2x, c2y, b2x, b2y);
    float bx, by; map_point(x, y, bx, by);
    int steps = 32;
    for (int i = 1; i <= steps; ++i) {
        float t = float(i) / steps, u = 1 - t;
        float mx = u*u*u*p0.x + 3*u*u*t*b1x + 3*u*t*t*b2x + t*t*t*bx;
        float my = u*u*u*p0.y + 3*u*u*t*b1y + 3*u*t*t*b2y + t*t*t*by;
        path_.push_back({mx, my});
    }
}
void Canvas2D::rect_path(float x, float y, float w, float h) {
    move_to(x, y); line_to(x + w, y); line_to(x + w, y + h); line_to(x, y + h); close_path();
}
void Canvas2D::fill() {
    if (fb_->get_pixel_count() == 0) return;
    ++draw_calls;
    sync_colors();
    if (fill_gradient) { fill_poly_gradient(path_, *fill_gradient); return; }
    fill_poly_scanline(path_, fill_rgba_, 1.f);
}
void Canvas2D::stroke() {
    if (fb_->get_pixel_count() == 0) return;
    ++draw_calls;
    sync_colors();
    stroke_polyline(path_, stroke_rgba_, 1.f, line_width);
}
void Canvas2D::clip() {
    if (path_.empty()) return;
    float minx = 1e9f, miny = 1e9f, maxx = -1e9f, maxy = -1e9f;
    for (auto& p : path_) {
        minx = std::min(minx, p.x); maxx = std::max(maxx, p.x);
        miny = std::min(miny, p.y); maxy = std::max(maxy, p.y);
    }
    clip_ = {int(minx), int(miny), int(maxx) + 1, int(maxy) + 1};
    has_clip_ = true;
}

// ── text (real TextShaper pipeline — AOSP family resolution law) ───────
void Canvas2D::fill_text(const std::string& t, float x, float y) {
    if (fb_->get_pixel_count() == 0 || t.empty()) return;
    ++draw_calls;
    sync_colors();
    auto& sh = fonts::TextShaper::instance();
    if (!sh.available()) return;
    float size = parse_font_size(font);
    bool bold = parse_font_bold(font);
    std::string fam = parse_font_family(font);
    int face_idx = sh.resolve_family(fam, bold);
    auto& st = sh.shape(t, size, bold, face_idx);
    float tw = st.width;
    float pen_x = x;
    if (text_align == "center") pen_x = x - tw / 2;
    else if (text_align == "right" || text_align == "end") pen_x = x - tw;
    float asc, desc, lh;
    sh.metrics(size, bold, face_idx, &asc, &desc, &lh);
    float baseline = y;
    if (text_baseline == "middle") baseline = y + asc - lh / 2;
    else if (text_baseline == "top" || text_baseline == "hanging") baseline = y + asc;
    else if (text_baseline == "bottom") baseline = y + asc - lh;
    float px_, py_; map_point(pen_x, baseline, px_, py_);
    renderer::RGBA col = to_rgba(fill_rgba_);
    // single-shot draw at the computed pen: the shaper handles per-glyph
    // advances/offsets internally (shaping is not per-glyph re-shaping).
    sh.draw(*fb_, t, px_, py_, size, col, bold, face_idx);
}
void Canvas2D::stroke_text(const std::string& t, float x, float y) {
    // approximation: 1px offsets (corpus uses it for halos only)
    fill_text(t, x + 1, y); fill_text(t, x - 1, y);
    fill_text(t, x, y + 1); fill_text(t, x, y - 1);
}
float Canvas2D::measure_text(const std::string& t) {
    auto& sh = fonts::TextShaper::instance();
    float size = parse_font_size(font);
    bool bold = parse_font_bold(font);
    std::string fam = parse_font_family(font);
    int face_idx = sh.resolve_family(fam, bold);
    return sh.shape(t, size, bold, face_idx).width;
}

// ── images ──────────────────────────────────────────────────────────────
void Canvas2D::draw_image(const renderer::FrameBuffer& src, float dx, float dy, float dw, float dh) {
    if (fb_->get_pixel_count() == 0 || src.get_pixel_count() == 0) return;
    ++draw_calls;
    int sw = src.get_width(), shh = src.get_height();
    for (int yy = 0; yy < int(dh); ++yy)
        for (int xx = 0; xx < int(dw); ++xx) {
            float mx, my; map_point(dx + xx + .5f, dy + yy + .5f, mx, my);
            int sx = int((xx + .5f) / dw * sw), sy = int((yy + .5f) / dh * shh);
            if (sx < 0 || sy < 0 || sx >= sw || sy >= shh) continue;
            auto c = src.get_pixel(sx, sy);
            blend_pixel(int(mx), int(my),
                        (uint32_t(c.a) << 24) | (uint32_t(c.b) << 16) |
                        (uint32_t(c.g) << 8) | c.r, c.a / 255.f);
        }
}

}} // namespace miniandroid::webview
