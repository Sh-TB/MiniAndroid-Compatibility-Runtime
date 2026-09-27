// S109 WEBVIEW-ENGINE — Canvas2D raster subsystem.
//
// SEMANTIC LAW (WHATWG HTML §4.12.5 canvas — 2D rendering context):
// A canvas element owns a bitmap; getContext('2d') returns a drawing
// context whose operations mutate that bitmap; the bitmap composites
// into the page (here: blitted into the runtime framebuffer by the
// view-tree render walk). This is the REAL raster layer — paths are
// scanline-filled on the FrameBuffer, text goes through TextShaper
// (the same FriBidi/HarfBuzz/FreeType pipeline Android views use, with
// AOSP family resolution), and composite operations are per-pixel
// Porter-Duff/blend math on the actual bitmap.
#pragma once
#include "../renderer/software_renderer.h"
#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid { namespace webview {

uint32_t parse_css_color(const std::string& s, bool& ok);   // → 0xAARRGGBB
std::string parse_font_family(const std::string& css_font); // "bold 20px Courier" → "Courier"
float parse_font_size(const std::string& css_font);
bool parse_font_bold(const std::string& css_font);

struct Pattern {                       // createPattern result (tiled tile)
    std::unique_ptr<renderer::FrameBuffer> tile;
    Pattern() : tile(std::make_unique<renderer::FrameBuffer>(1, 1)) {}
};

struct PathPoint { float x, y; };

// CanvasGradient (WHATWG §4.12.5.1.3): color interpolation along a line
// (linear) or radius (radial), piecewise between stops.
struct Gradient {
    int type = 0;                  // 0 = linear, 1 = radial
    float x0 = 0, y0 = 0, x1 = 0, y1 = 0, r0 = 0, r1 = 1;
    struct Stop { float pos; uint32_t color; };
    std::vector<Stop> stops;
    uint32_t color_at(float t) const {
        if (stops.empty()) return 0xff000000;
        if (t <= stops.front().pos) return stops.front().color;
        if (t >= stops.back().pos) return stops.back().color;
        for (size_t i = 0; i + 1 < stops.size(); ++i) {
            const auto& a = stops[i];
            const auto& b = stops[i + 1];
            if (t >= a.pos && t <= b.pos) {
                float k = (b.pos - a.pos) > 1e-6f ? (t - a.pos) / (b.pos - a.pos) : 0.f;
                auto ch = [k](uint32_t ca, uint32_t cb, int shift) {
                    float fa = float((ca >> shift) & 255), fb = float((cb >> shift) & 255);
                    return uint8_t(fa * (1 - k) + fb * k + .5f);
                };
                return (uint32_t(ch(a.color, b.color, 24)) << 24) |
                       (uint32_t(ch(a.color, b.color, 16)) << 16) |
                       (uint32_t(ch(a.color, b.color, 8)) << 8) |
                       uint32_t(ch(a.color, b.color, 0));
            }
        }
        return stops.back().color;
    }
};

class Canvas2D {
public:
    Canvas2D() : fb_(std::make_unique<renderer::FrameBuffer>(1, 1)) {}
    int width() const { return fb_->get_width(); }
    int height() const { return fb_->get_height(); }
    renderer::FrameBuffer& bitmap() { return *fb_; }
    const renderer::FrameBuffer& bitmap() const { return *fb_; }
    void set_size(int w, int h);   // WHATWG: resize resets the bitmap (transparent
                                   // black → here: transparent, composited over page)

    // ── state ──
    void save(); void restore();
    void set_transform(float a, float b, float c, float d, float e, float f);
    void transform(float a, float b, float c, float d, float e, float f);
    void translate(float x, float y) { transform(1, 0, 0, 1, x, y); }
    void scale(float x, float y) { transform(x, 0, 0, y, 0, 0); }
    void rotate(float rad);
    void reset_transform() { set_transform(1, 0, 0, 1, 0, 0); }

    // style properties (JS-facing)
    std::string fill_style = "#000000";
    std::string stroke_style = "#000000";
    Gradient* fill_gradient = nullptr;    // set when fillStyle is a gradient
    Gradient* stroke_gradient = nullptr;
    float global_alpha = 1.f;
    std::string global_composite_operation = "source-over";  // invalid → ignored law
    float line_width = 1.f;
    std::string font = "10px sans-serif";
    std::string text_align = "start";
    std::string text_baseline = "alphabetic";

    // ── rect ops ──
    void fill_rect(float x, float y, float w, float h);
    void stroke_rect(float x, float y, float w, float h);
    void clear_rect(float x, float y, float w, float h);

    // ── path ops ──
    void begin_path() { path_.clear(); }
    void close_path();
    void move_to(float x, float y);
    void line_to(float x, float y);
    void arc(float cx, float cy, float r, float a0, float a1, bool ccw = false);
    void quadratic_curve_to(float cpx, float cpy, float x, float y);
    void bezier_curve_to(float c1x, float c1y, float c2x, float c2y, float x, float y);
    void rect_path(float x, float y, float w, float h);
    void fill();
    void stroke();
    void clip();

    // ── text ──
    void fill_text(const std::string& t, float x, float y);
    void stroke_text(const std::string& t, float x, float y);
    float measure_text(const std::string& t);

    // ── images/patterns ──
    void draw_image(const renderer::FrameBuffer& src, float dx, float dy, float dw, float dh);
    Pattern* make_pattern(const renderer::FrameBuffer& src) {
        auto* p = new Pattern();
        p->tile = std::make_unique<renderer::FrameBuffer>(src.get_width(), src.get_height());
        p->tile->set_alpha_preserve(true);
        auto& tpx = p->tile->get_pixels_mut();
        const auto& spx = src.get_pixels();
        for (size_t i = 0; i < spx.size() && i < tpx.size(); ++i) tpx[i] = spx[i];
        owned_patterns_.push_back(p);
        return p;
    }

    size_t draw_calls = 0;

private:
    std::unique_ptr<renderer::FrameBuffer> fb_;
    std::vector<PathPoint> path_;
    uint32_t fill_rgba_ = 0xff000000, stroke_rgba_ = 0xff000000;
    bool fill_ok_ = true, stroke_ok_ = true;
    struct ClipRect { int x0, y0, x1, y1; };
    ClipRect clip_{-1, -1, -1, -1};
    bool has_clip_ = false;
    struct State {
        std::string fill_style, stroke_style;
        uint32_t fill_rgba, stroke_rgba; bool fill_ok, stroke_ok;
        float global_alpha; std::string gco; float line_width;
        std::string font, text_align, text_baseline;
        float m_a, m_b, m_c, m_d, m_e, m_f;
        ClipRect clip; bool has_clip;
        Pattern* fill_pat; Pattern* stroke_pat;
    };
    std::vector<State> stack_;
    std::vector<Pattern*> owned_patterns_;
    Pattern* fill_pat_ = nullptr;
    Pattern* stroke_pat_ = nullptr;
    float m_a = 1, m_b = 0, m_c = 0, m_d = 1, m_e = 0, m_f = 0;

    void sync_colors() {
        fill_rgba_ = parse_css_color(fill_style, fill_ok_);
        stroke_rgba_ = parse_css_color(stroke_style, stroke_ok_);
    }
    void blend_pixel(int x, int y, uint32_t color, float alpha);
    void blend_hline(int y, int x0, int x1, uint32_t color, float alpha);
    void fill_poly_scanline(const std::vector<PathPoint>& pts, uint32_t color, float alpha);
    void fill_poly_gradient(const std::vector<PathPoint>& pts, const Gradient& g);
    void inv_map_point(float px, float py, float& ox, float& oy) const;
    void stroke_polyline(const std::vector<PathPoint>& pts, uint32_t color, float alpha, float width);
    void map_point(float x, float y, float& ox, float& oy) const;
    renderer::RGBA to_rgba(uint32_t c) const {
        return renderer::RGBA{uint8_t(c & 255), uint8_t((c >> 8) & 255),
                              uint8_t((c >> 16) & 255), uint8_t((c >> 24) & 255)};
    }
    bool in_clip(int x, int y) const {
        return !has_clip_ || (x >= clip_.x0 && y >= clip_.y0 && x < clip_.x1 && y < clip_.y1);
    }
};

}} // namespace miniandroid::webview
