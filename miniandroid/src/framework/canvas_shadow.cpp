// CAMPAIGN 013 — Canvas/Paint shadow implementation. See canvas_shadow.h.
#include "canvas_shadow.h"
#include "bitmap_shadow.h"
#include "../diagnostics/gfx_provenance.h"
#include "../fonts/text_shaper.h"
#include "../renderer/software_renderer.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <iostream>

namespace miniandroid { namespace framework {

namespace {

renderer::RGBA to_rgba(uint32_t argb) {
    return renderer::RGBA{
        static_cast<uint8_t>((argb >> 16) & 0xFF),
        static_cast<uint8_t>((argb >> 8) & 0xFF),
        static_cast<uint8_t>(argb & 0xFF),
        static_cast<uint8_t>((argb >> 24) & 0xFF)};
}

// Java float args arrive as CallContext::Arg::FLOAT (or DOUBLE).
float arg_as_float(const CallContext& ctx, size_t i, float def = 0.f) {
    if (i >= ctx.args.size()) return def;
    const auto& a = ctx.args[i];
    if (a.kind == CallContext::Arg::Kind::FLOAT) return a.float_val;
    if (a.kind == CallContext::Arg::Kind::DOUBLE) return static_cast<float>(a.double_val);
    if (a.kind == CallContext::Arg::Kind::INT) return static_cast<float>(a.int_val);
    return def;
}

// ── CYCLE-E: Path geometry helpers ──────────────────────────────────────
using PointList = std::vector<std::pair<float, float>>;

// Circle ≈ 4 cubic Béziers: |P0C - P0| = kappa * r (AOSP/Skia constant).
constexpr float kKappa = 0.552284749831f;
constexpr float kDegToRad = 3.14159265358979323846f / 180.0f;

void flatten_cubic(PointList& out, float x0, float y0,
                   float x1, float y1, float x2, float y2,
                   float x3, float y3, int segs = 12) {
    for (int i = 1; i <= segs; ++i) {
        const float t = (float)i / segs, u = 1.0f - t;
        const float a = u * u * u, b = 3 * u * u * t;
        const float c = 3 * u * t * t, d = t * t * t;
        out.push_back({a * x0 + b * x1 + c * x2 + d * x3,
                       a * y0 + b * y1 + c * y2 + d * y3});
    }
}

void flatten_quad(PointList& out, float x0, float y0,
                  float x1, float y1, float x2, float y2, int segs = 8) {
    for (int i = 1; i <= segs; ++i) {
        const float t = (float)i / segs, u = 1.0f - t;
        out.push_back({u * u * x0 + 2 * u * t * x1 + t * t * x2,
                       u * u * y0 + 2 * u * t * y1 + t * t * y2});
    }
}

// Full-oval contour: 4 cubic quadrant arcs starting at (cx+rx, cy),
// travelling clockwise on screen (y-down) — the Skia addOval convention.
void append_oval_contour(PointList& out, float cx, float cy,
                         float rx, float ry) {
    const float k = kKappa;
    out.push_back({cx + rx, cy});
    // right → bottom → left → top → right
    flatten_cubic(out, cx + rx, cy, cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry);
    flatten_cubic(out, cx, cy + ry, cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy);
    flatten_cubic(out, cx - rx, cy, cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry);
    flatten_cubic(out, cx, cy - ry, cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy);
}

// Android angle semantics: degrees, 0° = 3 o'clock, POSITIVE sweep is
// CLOCKWISE on screen (y-down): x = cx + rx·cos(a), y = cy + ry·sin(a)
// with a increasing — 90° lands at 6 o'clock (cy + ry), matching AOSP.
void append_arc_points(PointList& out, float cx, float cy,
                       float rx, float ry, float start_deg, float sweep_deg) {
    if (sweep_deg == 0.f || rx <= 0.f || ry <= 0.f) return;
    float sweep = sweep_deg;
    if (sweep > 360.f) sweep = 360.f;
    if (sweep < -360.f) sweep = -360.f;
    const int segs = std::max(2, (int)std::ceil(std::fabs(sweep) / 5.0f));
    const float a0 = start_deg * kDegToRad;
    const float sw = sweep * kDegToRad;
    for (int i = 1; i <= segs; ++i) {
        const float a = a0 + sw * (float)i / segs;
        out.push_back({cx + rx * std::cos(a), cy + ry * std::sin(a)});
    }
}

// First point of an arc (for addArc/arcTo moveTo semantics).
std::pair<float, float> arc_start_point(float cx, float cy, float rx, float ry,
                                        float start_deg) {
    const float a = start_deg * kDegToRad;
    return {cx + rx * std::cos(a), cy + ry * std::sin(a)};
}

// Honest Path.isConvex: single contour whose turns never flip sign.
bool contour_is_convex(const PointList& pts) {
    if (pts.size() < 3) return false;
    int sign = 0;
    const size_t n = pts.size();
    for (size_t i = 0; i < n; ++i) {
        const auto& p0 = pts[i];
        const auto& p1 = pts[(i + 1) % n];
        const auto& p2 = pts[(i + 2) % n];
        const float cross = (p1.first - p0.first) * (p2.second - p1.second)
                          - (p1.second - p0.second) * (p2.first - p1.first);
        if (std::fabs(cross) < 1e-6f) continue;
        const int s = cross > 0 ? 1 : -1;
        if (sign == 0) sign = s;
        else if (sign != s) return false;
    }
    return true;
}

// Rounded-rect contour: 4 lines + 4 quarter arcs (real corners, not a
// rect approximation). Wind direction per Skia convention (y-down).
void append_roundrect_contour(PointList& out, float l, float t,
                              float r, float b, float rx, float ry, bool ccw) {
    rx = std::min(rx, (r - l) / 2.f);
    ry = std::min(ry, (b - t) / 2.f);
    if (rx <= 0.f || ry <= 0.f) {
        out.push_back({l, t}); out.push_back({r, t});
        out.push_back({r, b}); out.push_back({l, b});
        return;
    }
    if (!ccw) {  // CW: top-left → top-right → bottom-right → bottom-left
        out.push_back({l + rx, t});
        out.push_back({r - rx, t});
        append_arc_points(out, r - rx, t + ry, rx, ry, -90.f, 90.f);   // → right
        out.push_back({r, b - ry});
        append_arc_points(out, r - rx, b - ry, rx, ry, 0.f, 90.f);     // → bottom
        out.push_back({l + rx, b});
        append_arc_points(out, l + rx, b - ry, rx, ry, 90.f, 90.f);    // → left
        out.push_back({l, t + ry});
        append_arc_points(out, l + rx, t + ry, rx, ry, 180.f, 90.f);   // → top
    } else {     // CCW: reverse the CW order
        out.push_back({l + rx, t});
        out.push_back({l, t + ry});
        append_arc_points(out, l + rx, t + ry, rx, ry, 180.f, -90.f);
        out.push_back({l, b - ry});
        out.push_back({l + rx, b});
        append_arc_points(out, l + rx, b - ry, rx, ry, 90.f, -90.f);
        out.push_back({r - rx, b});
        out.push_back({r, b - ry});
        append_arc_points(out, r - rx, b - ry, rx, ry, 0.f, -90.f);
        out.push_back({r, t + ry});
        out.push_back({r - rx, t});
        append_arc_points(out, r - rx, t + ry, rx, ry, -90.f, -90.f);
    }
}

// CYCLE-E: read android.graphics.RectF left/top/right/bottom from the heap
// through the generic shadow HeapAllocator float-field hook.
bool read_rectf_fields(HeapAllocator* heap, uint32_t rect_id,
                       float& l, float& t, float& r, float& b) {
    if (!heap || rect_id == 0) return false;
    return heap->get_object_float_field(rect_id, "left", l) &&
           heap->get_object_float_field(rect_id, "top", t) &&
           heap->get_object_float_field(rect_id, "right", r) &&
           heap->get_object_float_field(rect_id, "bottom", b);
}

}  // namespace

// ── S71 R-NEW-389 FIRST-PIXEL-DIVERGENCE instrumentation ────────────────
// Env-gated (MINIANDROID_CANVAS_OP_TRACE=<path>) per-op evidence line:
//   seq kind x y w h r color stroke stroke_w text_size bold
//   clip_l clip_t clip_r clip_b  a b c d e f  text
// Everything is the RESOLVED record-time state (what the rasterizer sees).
void CanvasShadow::push_op(DrawOp op) {
    if (op_trace_seq_ < kOpTraceCap) {
        if (!op_trace_) {
            const char* p = std::getenv("MINIANDROID_CANVAS_OP_TRACE");
            if (p && *p) op_trace_ = std::fopen(p, "w");
        }
        if (op_trace_) {
            const char* kind_names[] = {"COLOR", "RECT", "ROUNDRECT",
                                        "CIRCLE", "LINE", "TEXT", "PAINT",
                                        "PATH", "BITMAP"};
            const char* kn = kind_names[static_cast<int>(op.kind)];
            std::fprintf(op_trace_,
                         "%llu %s %.3f %.3f %.3f %.3f %.3f %08x %d %.3f "
                         "%.3f %d %d %d %d %d %.6f %.6f %.6f %.6f %.6f "
                         "%.6f \"%s\"\n",
                         static_cast<unsigned long long>(op_trace_seq_++),
                         kn, op.x, op.y, op.w, op.h, op.r, op.color,
                         op.stroke ? 1 : 0, op.stroke_w, op.text_size_px,
                         op.text_bold ? 1 : 0, op.clip_l, op.clip_t,
                         op.clip_r, op.clip_b, mat_.a, mat_.b, mat_.c,
                         mat_.d, mat_.e, mat_.f, op.text.c_str());
        }
    }
    target().push_back(std::move(op));
}

void CanvasShadow::begin_frame() {
    ops_.clear();
    capturing_ = true;
    // UC009: fresh frame = fresh canvas state (AOSP Canvas lifecycle).
    mat_ = Affine2D{};
    clip_ = ClipRect{};
    save_stack_.clear();
    recording_node_ = 0;
}

// CYCLE-E §34: no silent fallbacks — accepted-but-ignored operations are
// reported once per (class, op) so compat gaps are observable in every run.
void CanvasShadow::warn_noop(const std::string& cls, const std::string& op) {
    const std::string key = cls + "::" + op;
    if (noop_warned_.count(key)) return;
    noop_warned_[key] = true;
    std::cerr << "UNSUPPORTED_CANVAS_OPERATION class=" << cls
              << " op=" << op
              << " effect=accepted_not_reproduced" << std::endl;
}

size_t CanvasShadow::replay(renderer::SoftwareCanvas& canvas,
                            renderer::BitmapFont& font,
                            float left, float top, float w, float h) {
    // ── S68 §12: AOSP view clip law ───────────────────────────────────────
    // View.onDraw's canvas is clipped to the view bounds; the app's
    // clipRect stack further intersects it. Both are honored by funneling
    // the effective clip into the SoftwareCanvas for this replay, then
    // clearing it so other views are unaffected.
    const float vl = left, vt = top, vr = left + w, vb = top + h;   // view bounds
    float cl_ = vl, ct_ = vt, cr_ = vr, cb_ = vb;   // effective device clip
    // Per-op clip snapshot (AOSP law — see DrawOp.has_clip): each op carries
    // the clip that was in effect when the app recorded it; ops recorded
    // after restore() carry the restored (outer) clip.
    auto apply_op_clip = [&](const DrawOp& op) {
        float cl = vl, ct = vt, cr = vr, cb = vb;
        if (op.has_clip) {
            // Op-space clip → device = +left/top, then intersect w/ bounds.
            cl = std::max(cl, op.clip_l + left);
            ct = std::max(ct, op.clip_t + top);
            cr = std::min(cr, op.clip_r + left);
            cb = std::min(cb, op.clip_b + top);
        }
        canvas.set_clip(cl, ct, cr, cb);
        cl_ = cl; ct_ = ct; cr_ = cr; cb_ = cb;
    };

    for (const auto& op : ops_) {
        apply_op_clip(op);
        renderer::RGBA c = to_rgba(op.color);
        switch (op.kind) {
            case DrawOp::Kind::DRAW_COLOR: {
                if (op.x < 0.5f) {  // x flag = full-view rect
                    canvas.draw_rect(left, top, left + w, top + h, c);
                } else {
                    canvas.draw_rect(left + op.x, top + op.y,
                                     left + op.x + op.w, top + op.y + op.h, c);
                }
                break;
            }
            case DrawOp::Kind::DRAW_RECT: {
                const float x1 = left + op.x, y1 = top + op.y;
                const float x2 = left + op.w, y2 = top + op.h;
                if (op.stroke) {
                    canvas.draw_rect(x1, y1, x2, y1 + op.stroke_w, c);
                    canvas.draw_rect(x1, y2 - op.stroke_w, x2, y2, c);
                    canvas.draw_rect(x1, y1, x1 + op.stroke_w, y2, c);
                    canvas.draw_rect(x2 - op.stroke_w, y1, x2, y2, c);
                } else {
                    canvas.draw_rect(x1, y1, x2, y2, c);
                }
                break;
            }
            case DrawOp::Kind::DRAW_ROUNDRECT: {
                // Recorded with width/height convention (unlike DRAW_RECT).
                const float x1 = left + op.x, y1 = top + op.y;
                const float x2 = x1 + op.w, y2 = y1 + op.h;
                // S67 FOUNDATION (B7): real rounded-corner rasterization.
                // Upstream law (AOSP Skia RRect / Canvas.drawRoundRect): the
                // shape is the rect minus its four corners, each corner an
                // axis-aligned quarter-circle of radius min(rx, geometry).
                // Rasterized by per-row spans: rows outside the corner bands
                // span the full width; rows inside a corner band span from
                // the quarter-circle chord. Previously v1 drew a plain rect
                // (radius recorded but not rasterized) — every Compose card /
                // Material shape rendered with square corners.
                const float rad = std::min({op.r, op.w * 0.5f, op.h * 0.5f});
                if (rad <= 0.5f) {
                    if (op.stroke) {
                        canvas.draw_rect(x1, y1, x2, y1 + op.stroke_w, c);
                        canvas.draw_rect(x1, y2 - op.stroke_w, x2, y2, c);
                        canvas.draw_rect(x1, y1, x1 + op.stroke_w, y2, c);
                        canvas.draw_rect(x2 - op.stroke_w, y1, x2, y2, c);
                    } else {
                        canvas.draw_rect(x1, y1, x2, y2, c);
                    }
                    break;
                }
                const float rad_sq = rad * rad;
                for (int yy = (int)std::floor(y1); yy < (int)std::ceil(y2); yy++) {
                    // Row-center space (pixel centers at +0.5).
                    const float py = (float)yy + 0.5f;
                    float row_l = x1, row_r = x2;
                    // Top/bottom corner bands: shrink the span by the chord.
                    float dy_top = (y1 + rad) - py;
                    float dy_bot = py - (y2 - rad);
                    float inset = 0.f;
                    if (dy_top > 0.f) {
                        inset = rad - std::sqrt(std::max(0.f, rad_sq - dy_top * dy_top));
                    } else if (dy_bot > 0.f) {
                        inset = rad - std::sqrt(std::max(0.f, rad_sq - dy_bot * dy_bot));
                    }
                    row_l += inset;
                    row_r -= inset;
                    if (row_r <= row_l) continue;
                    if (op.stroke) {
                        // Stroke: top/bottom edge rows + side columns of this
                        // span (approximation: constant stroke width, honest
                        // AOSP-equivalent geometry for the frame-evidence law).
                        if (py - y1 < (float)op.stroke_w || y2 - py <= (float)op.stroke_w) {
                            canvas.draw_rect(row_l, py - 0.5f, row_r, py + 0.5f, c);
                        } else {
                            canvas.draw_rect(row_l, py - 0.5f, row_l + op.stroke_w, py + 0.5f, c);
                            canvas.draw_rect(row_r - op.stroke_w, py - 0.5f, row_r, py + 0.5f, c);
                        }
                    } else {
                        canvas.draw_rect(row_l, py - 0.5f, row_r, py + 0.5f, c);
                    }
                }
                break;
            }
            case DrawOp::Kind::DRAW_CIRCLE: {
                // Rasterize by horizontal spans (framebuffer has no circle op).
                const float cx = left + op.x, cy = top + op.y, rr = op.r;
                if (op.stroke) {
                    for (int dy = -int(rr); dy <= int(rr); dy++) {
                        float t = std::sqrt(std::max(0.f, rr*rr - dy*dy));
                        float band = op.stroke_w;
                        float outer = std::sqrt(std::max(0.f, (rr+band)*(rr+band) - dy*dy));
                        float inner = rr - band > 0 ? std::sqrt(std::max(0.f, (rr-band)*(rr-band) - dy*dy)) : -1;
                        canvas.draw_rect(cx - outer, top + op.y + dy, cx + outer,
                                         top + op.y + dy + 1, c);
                        (void)t; (void)inner;
                    }
                } else {
                    for (int dy = -int(rr); dy <= int(rr); dy++) {
                        float dx = std::sqrt(std::max(0.f, rr*rr - dy*dy));
                        canvas.draw_rect(cx - dx, top + op.y + dy, cx + dx,
                                         top + op.y + dy + 1, c);
                    }
                }
                break;
            }
            case DrawOp::Kind::DRAW_LINE: {
                // Bresenham-lite via rects (axis-dominant lines).
                float x1 = left + op.x, y1 = top + op.y;
                float x2 = left + op.w, y2 = top + op.h;
                float dx = x2 - x1, dy = y2 - y1;
                int steps = int(std::max(std::fabs(dx), std::fabs(dy)));
                if (steps <= 0) steps = 1;
                for (int i = 0; i <= steps; i++) {
                    float px = x1 + dx * i / steps;
                    float py = y1 + dy * i / steps;
                    canvas.draw_rect(px, py, px + std::max(op.stroke_w, 1.f),
                                     py + std::max(op.stroke_w, 1.f), c);
                }
                break;
            }
            case DrawOp::Kind::DRAW_PATH: {
                // FIX-5: even-odd scanline fill across ALL recorded contours
                // (digit glyphs with counters — '0','4','6','8','9' — come
                // out with real holes). Stroke mode outlines each contour.
                if (op.contours.empty()) break;
                // Gather all edges once.
                struct Edge { float x1, y1, x2, y2; };
                std::vector<Edge> edges;
                float min_y = 1e30f, max_y = -1e30f;
                for (const auto& ct : op.contours) {
                    for (size_t i = 0; i < ct.size(); ++i) {
                        const auto& a = ct[i];
                        const auto& b = ct[(i + 1) % ct.size()];
                        if (a.second != b.second) {
                            edges.push_back({a.first + left, a.second + top,
                                             b.first + left, b.second + top});
                        }
                        min_y = std::min(min_y, std::min(a.second, b.second) + top);
                        max_y = std::max(max_y, std::max(a.second, b.second) + top);
                    }
                }
                if (edges.empty() || max_y < min_y) break;
                if (op.stroke) {
                    // Outline: walk each contour with the line rasterizer.
                    for (const auto& ct : op.contours) {
                        for (size_t i = 0; i + 1 < ct.size(); ++i) {
                            float ax = ct[i].first + left, ay = ct[i].second + top;
                            float bx = ct[i + 1].first + left, by = ct[i + 1].second + top;
                            float ddx = bx - ax, ddy = by - ay;
                            int st = int(std::max({std::fabs(ddx), std::fabs(ddy), 1.f}));
                            for (int s = 0; s <= st; ++s) {
                                float px = ax + ddx * s / st;
                                float py = ay + ddy * s / st;
                                canvas.draw_rect(px, py,
                                                 px + std::max(op.stroke_w, 1.f),
                                                 py + std::max(op.stroke_w, 1.f), c);
                            }
                        }
                    }
                    break;
                }
                const int y0 = std::max((int)std::floor(min_y), 0);
                const int y1 = (int)std::ceil(max_y);
                // CYCLE-E: direction-aware crossings for the winding rule.
                std::vector<std::pair<float, int>> xs;
                const bool winding_rule = (op.fill_type == 0);
                for (int y = y0; y <= y1; ++y) {
                    const float sy = (float)y + 0.5f;
                    xs.clear();
                    for (const auto& e : edges) {
                        float ey1 = e.y1, ey2 = e.y2;
                        if ((sy >= ey1 && sy < ey2) || (sy >= ey2 && sy < ey1)) {
                            float t = (sy - ey1) / (ey2 - ey1);
                            xs.push_back({e.x1 + t * (e.x2 - e.x1),
                                          ey2 > ey1 ? 1 : -1});
                        }
                    }
                    if (xs.size() < 2) continue;
                    std::sort(xs.begin(), xs.end(),
                              [](const auto& a, const auto& b) {
                                  return a.first < b.first;
                              });
                    if (winding_rule) {
                        // CYCLE-E: AOSP default — nonzero winding rule.
                        // Same-direction overlapping contours stay filled;
                        // opposite-direction counters punch holes.
                        int winding = 0;
                        float span_start = 0.f;
                        bool inside = false;
                        for (const auto& cr : xs) {
                            if (!inside) {
                                span_start = cr.first;
                                inside = true;
                                winding = cr.second;
                            } else {
                                winding += cr.second;
                                if (winding == 0) {
                                    if (cr.first - span_start >= 0.5f)
                                        canvas.draw_rect(span_start, (float)y,
                                                         cr.first, (float)y + 1, c);
                                    inside = false;
                                }
                            }
                        }
                        if (inside && xs.back().first - span_start >= 0.5f)
                            canvas.draw_rect(span_start, (float)y,
                                             xs.back().first, (float)y + 1, c);
                    } else {
                        // Even-odd: fill between crossing pairs.
                        for (size_t i = 0; i + 1 < xs.size(); i += 2) {
                            float xa = xs[i].first, xb = xs[i + 1].first;
                            if (xb - xa < 0.5f) continue;
                            canvas.draw_rect(xa, (float)y, xb, (float)y + 1, c);
                        }
                    }
                }
                break;
            }
            case DrawOp::Kind::DRAW_TEXT: {
                // S68 §14: paint text size set → REAL shaping pipeline
                // (FreeType/HarfBuzz/FriBidi — full Unicode/RTL/Persian, the
                // SAME engine TextView uses; was ASCII-only bitmap font).
                // No text size → legacy bitmap-font path (byte-identical).
                if (op.text_size_px > 0.f && fonts::TextShaper::instance().available()) {
                    fonts::TextShaper::instance().draw(
                        canvas.fb(), op.text, left + op.x, top + op.y,
                        op.text_size_px, c, op.text_bold);
                } else {
                    canvas.draw_text(op.text, left + op.x, top + op.y, c, &font);
                }
                break;
            }
            case DrawOp::Kind::DRAW_BITMAP: {
                // S68 §12: drawBitmap replay — pixels from BitmapStore,
                // src/dst rect law, nearest sampling (FilterBitmap=false).
                const StoredBitmap* sb = BitmapStore::instance().get(op.bitmap_id);
                if (!sb || sb->rgba.empty()) {
                    // S82-GFX §6: CANVAS chain bit — bitmap unresolved at replay.
                    if (diagnostics::GfxProvenance::instance().enabled())
                        diagnostics::GfxProvenance::instance().record_canvas_bitmap(
                            op.bitmap_id, false, 0, 0, false);
                    break;
                }
                int sw = sb->width, sh = sb->height;
                int sx = 0, sy = 0;
                if (op.has_src) {
                    sx = (int)op.src_l; sy = (int)op.src_t;
                    sw = (int)(op.src_r - op.src_l);
                    sh = (int)(op.src_b - op.src_t);
                }
                int dx = (int)(left + op.x), dy = (int)(top + op.y);
                int dw = op.has_dst ? (int)op.w : sw;
                int dh = op.has_dst ? (int)op.h : sh;
                if (sw <= 0 || sh <= 0 || dw <= 0 || dh <= 0) break;
                if (op.has_affine && (op.affine.b != 0.f || op.affine.c != 0.f)) {
                    // Rotated/skewed dst: inverse-map per-pixel sampling.
                    const Affine2D& m = op.affine;
                    const float det = m.a * m.d - m.b * m.c;
                    if (std::fabs(det) < 1e-9f) break;
                    const float alpha = ((op.color >> 24) & 0xFF) / 255.f;
                    for (int pyi = dy; pyi < dy + dh; pyi++) {
                        for (int pxi = dx; pxi < dx + dw; pxi++) {
                            const float X = (float)pxi - left - m.e;
                            const float Y = (float)pyi - top - m.f;
                            const float u = ( m.d * X - m.c * Y) / det;
                            const float v = (-m.b * X + m.a * Y) / det;
                            if (u < 0.f || v < 0.f || u >= (float)dw || v >= (float)dh) continue;
                            const int spx = sx + (int)(u * (float)sw / (float)dw);
                            const int spy = sy + (int)(v * (float)sh / (float)dh);
                            if (spx < 0 || spy < 0 || spx >= sb->width || spy >= sb->height) continue;
                            const uint8_t* p = &sb->rgba[((size_t)spy * sb->width + spx) * 4];
                            renderer::RGBA src(p[0], p[1], p[2],
                                               (uint8_t)std::min(255.f, p[3] * alpha));
                            if (!canvas.has_clip() ||
                                (pxi >= (int)cl_ && pxi < (int)cr_ && pyi >= (int)ct_ && pyi < (int)cb_)) {
                                renderer::RGBA dstc = canvas.fb().get_pixel(pxi, pyi);
                                canvas.fb().set_pixel(pxi, pyi, renderer::blend(src, dstc));
                            }
                        }
                    }
                } else {
                    canvas.draw_image_region(sb->rgba.data(), sb->width, sb->height,
                                             sx, sy, sw, sh, dx, dy, dw, dh);
                }
                // S82-GFX §6: bitmap resolved + CANVAS_WRITTEN evidence.
                if (diagnostics::GfxProvenance::instance().enabled())
                    diagnostics::GfxProvenance::instance().record_canvas_bitmap(
                        op.bitmap_id, true, sb->width, sb->height, true);
                break;
            }
            case DrawOp::Kind::DRAW_PAINT: {
                canvas.draw_rect(left, top, left + w, top + h, c);
                break;
            }
        }
    }
    capturing_ = false;
    canvas.clear_clip();   // S68: the clip is per-view — never leak it
    return ops_.size();
}

CallResult CanvasShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;


    // ── RenderNode (UC009 H-072: Compose recording model) ─────────────
    if (cls == "Landroid/view/RenderNode;" || cls.find("RenderNode;") != std::string::npos) {
        const uint32_t recv = ctx.receiver_id;
        if (m == "beginRecording") {
            // AOSP: switches this node into recording mode and returns the
            // node's RecordingCanvas. We route subsequent Canvas ops into
            // the node's op list; the returned object is a shared
            // RecordingCanvas receiver (single-threaded draw = safe).
            recording_node_ = recv;
            uint32_t canvas_id = heap_ ? heap_->get_or_create("Landroid/graphics/RecordingCanvas;") : recv;
            return CallResult::handled_object(canvas_id, "Landroid/graphics/RecordingCanvas;");
        }
        if (m == "endRecording") {
            recording_node_ = 0;
            return CallResult::handled_void();
        }
        if (m == "setPosition") {
            // setPosition(left, top, right, bottom)
            if (ctx.args.size() >= 4) {
                node_pos_l_[recv] = arg_as_float(ctx, 0, 0.f);
                node_pos_t_[recv] = arg_as_float(ctx, 1, 0.f);
            }
            return CallResult::handled_bool(true);
        }
        if (m == "setTranslationX" || m == "setTranslationY" || m == "setElevation" ||
            m == "setAlpha" || m == "setCameraDistance" || m == "setPivotX" || m == "setPivotY" ||
            m == "setScaleX" || m == "setScaleY" || m == "setRotation" || m == "setClipToBounds" ||
            m == "setClipToOutline" || m == "setOutline" || m == "setHasDisplayList" ||
            m == "setUsageHint" || m == "isValid" || m == "discardDisplayList") {
            return CallResult::handled_bool(true);
        }
        return CallResult::not_handled();
    }

    // ── Paint ──────────────────────────────────────────────────────────
    if (cls.find("Paint;") != std::string::npos) {
        const uint32_t recv = ctx.receiver_id;
        if (m == "setColor") {
            paint_color_[recv] = (uint32_t)ctx.arg_as_int(0, 0xFF000000);
            return CallResult::handled_void();
        }
        if (m == "setARGB") {
            // ────────────────────────────────────────────────────────────
            // S67 FOUNDATION (A5, f08_canvasops fixture): Paint.setARGB was
            // UNHANDLED — the call fell through to not_handled(), the paint
            // color stayed 0xFF000000, and every setARGB-colored shape drew
            // black (or was silently dropped). Upstream law (AOSP Paint
            // .java setARGB): setARGB(a,r,g,b) == setColor((a<<24)|(r<<16)|
            // (g<<8)|b) with per-channel 8-bit truncation. Same storage as
            // setColor so every downstream consumer (paint_color()) sees it.
            // ────────────────────────────────────────────────────────────
            uint32_t a = (uint32_t)ctx.arg_as_int(0, 255) & 0xFF;
            uint32_t r = (uint32_t)ctx.arg_as_int(1, 0) & 0xFF;
            uint32_t g = (uint32_t)ctx.arg_as_int(2, 0) & 0xFF;
            uint32_t b = (uint32_t)ctx.arg_as_int(3, 0) & 0xFF;
            paint_color_[recv] = (a << 24) | (r << 16) | (g << 8) | b;
            return CallResult::handled_void();
        }
        if (m == "getColor") {
            return CallResult::handled_int((int32_t)paint_color(recv));
        }
        if (m == "setAlpha") {
            uint32_t cur = paint_color(recv);
            uint32_t a = (uint32_t)ctx.arg_as_int(0, 255) & 0xFF;
            paint_color_[recv] = (cur & 0x00FFFFFF) | (a << 24);
            return CallResult::handled_void();
        }
        if (m == "setAntiAlias" || m == "setDither" ||
            m == "setFakeBoldText" || m == "setUnderlineText" || m == "setFlags") {
            if (m == "setFakeBoldText")
                paint_fake_bold_[recv] = ctx.arg_as_bool(0, false);
            return CallResult::handled_void();
        }
        if (m == "setFilterBitmap") {
            // S68 §12: consumed by Canvas.drawBitmap (nearest vs bilinear).
            paint_filter_bitmap_[recv] = ctx.arg_as_bool(0, false);
            return CallResult::handled_void();
        }
        if (m == "setStrokeWidth") {
            paint_stroke_w_[recv] = arg_as_float(ctx, 0, 1.f);
            return CallResult::handled_void();
        }
        if (m == "setStyle") {
            // CYCLE-E: accept the AOSP ordinal (int callers) OR the framework
            // enum object synthesized by the engine (Paint.Style.* — the arg
            // previously arrived as NULL and the call silently degraded to
            // FILL). Ordinals: 0 FILL, 1 STROKE, 2 FILL_AND_STROKE.
            int style = enum_arg_ordinal(ctx, 0, -1);
            if (style < 0 || style > 2) style = 0;
            paint_style_[recv] = style;
            return CallResult::handled_void();
        }
        if (m == "setTextSize") {
            paint_text_size_[recv] = arg_as_float(ctx, 0, 32.f);
            return CallResult::handled_void();
        }
        if (m == "setTextAlign" || m == "setTypeface" || m == "setShadowLayer") {
            return CallResult::handled_void();
        }
        if (m == "<init>") {
            paint_color_[recv] = 0xFF000000;
            return CallResult::handled_void();
        }
        return CallResult::not_handled();
    }

    // ── Path (FIX-5 + CYCLE-E: real geometry recording) ──────────────
    if (cls.find("graphics/Path;") != std::string::npos) {
        const uint32_t recv = ctx.receiver_id;
        PathData& pd = paths_[recv];
        // Android docs: a segment call on an empty path implies moveTo(0,0).
        auto ensure_open = [&pd]() {
            if (!pd.open) {
                pd.contours.push_back({});
                pd.open = true;
                pd.sx = pd.sy = 0.f;
                pd.contours.back().push_back({0.f, 0.f});
            }
        };
        if (m == "reset" || m == "rewind") {
            pd = PathData{};
            return CallResult::handled_void();
        }
        if (m == "moveTo") {
            pd.contours.push_back({});
            pd.cx = pd.sx = arg_as_float(ctx, 0);
            pd.cy = pd.sy = arg_as_float(ctx, 1);
            pd.open = true;
            pd.contours.back().push_back({pd.cx, pd.cy});
            return CallResult::handled_void();
        }
        if (m == "rMoveTo") {
            // CYCLE-E: relative move — starts a NEW sub-path offset from the
            // last point; empty path behaves as moveTo(dx,dy) per AOSP.
            float bx = 0.f, by = 0.f;
            if (!pd.contours.empty() && !pd.contours.back().empty()) {
                bx = pd.contours.back().back().first;
                by = pd.contours.back().back().second;
            }
            pd.contours.push_back({});
            pd.cx = pd.sx = bx + arg_as_float(ctx, 0);
            pd.cy = pd.sy = by + arg_as_float(ctx, 1);
            pd.open = true;
            pd.contours.back().push_back({pd.cx, pd.cy});
            return CallResult::handled_void();
        }
        if (m == "lineTo") {
            ensure_open();
            pd.cx = arg_as_float(ctx, 0);
            pd.cy = arg_as_float(ctx, 1);
            pd.contours.back().push_back({pd.cx, pd.cy});
            return CallResult::handled_void();
        }
        if (m == "rLineTo") {
            // CYCLE-E: relative line from the current point.
            ensure_open();
            pd.cx += arg_as_float(ctx, 0);
            pd.cy += arg_as_float(ctx, 1);
            pd.contours.back().push_back({pd.cx, pd.cy});
            return CallResult::handled_void();
        }
        if (m == "quadTo") {
            ensure_open();
            const float x1 = arg_as_float(ctx, 0), y1 = arg_as_float(ctx, 1);
            const float x2 = arg_as_float(ctx, 2), y2 = arg_as_float(ctx, 3);
            // Flatten the quadratic Bézier (8 segments — plenty at UI size).
            flatten_quad(pd.contours.back(), pd.cx, pd.cy, x1, y1, x2, y2);
            pd.cx = x2; pd.cy = y2;
            return CallResult::handled_void();
        }
        if (m == "rQuadTo") {
            // CYCLE-E: relative quadratic control/end points.
            ensure_open();
            const float dx1 = arg_as_float(ctx, 0), dy1 = arg_as_float(ctx, 1);
            const float dx2 = arg_as_float(ctx, 2), dy2 = arg_as_float(ctx, 3);
            flatten_quad(pd.contours.back(), pd.cx, pd.cy,
                         pd.cx + dx1, pd.cy + dy1, pd.cx + dx2, pd.cy + dy2);
            pd.cx += dx2; pd.cy += dy2;
            return CallResult::handled_void();
        }
        if (m == "cubicTo") {
            // CYCLE-E: cubic Bézier — the workhorse behind real glyph
            // outlines, bubble tails, and curved dividers. Flattened to a
            // 12-segment polyline (sub-pixel accuracy at UI sizes).
            ensure_open();
            const float x1 = arg_as_float(ctx, 0), y1 = arg_as_float(ctx, 1);
            const float x2 = arg_as_float(ctx, 2), y2 = arg_as_float(ctx, 3);
            const float x3 = arg_as_float(ctx, 4), y3 = arg_as_float(ctx, 5);
            flatten_cubic(pd.contours.back(), pd.cx, pd.cy,
                          x1, y1, x2, y2, x3, y3);
            pd.cx = x3; pd.cy = y3;
            return CallResult::handled_void();
        }
        if (m == "rCubicTo") {
            // CYCLE-E: relative cubic — all six offsets from current point.
            ensure_open();
            const float dx1 = arg_as_float(ctx, 0), dy1 = arg_as_float(ctx, 1);
            const float dx2 = arg_as_float(ctx, 2), dy2 = arg_as_float(ctx, 3);
            const float dx3 = arg_as_float(ctx, 4), dy3 = arg_as_float(ctx, 5);
            flatten_cubic(pd.contours.back(), pd.cx, pd.cy,
                          pd.cx + dx1, pd.cy + dy1,
                          pd.cx + dx2, pd.cy + dy2,
                          pd.cx + dx3, pd.cy + dy3);
            pd.cx += dx3; pd.cy += dy3;
            return CallResult::handled_void();
        }
        if (m == "close") {
            if (pd.open && !pd.contours.empty()) {
                pd.contours.back().push_back({pd.sx, pd.sy});
                pd.cx = pd.sx; pd.cy = pd.sy;
                pd.open = false;
            }
            return CallResult::handled_void();
        }
        if (m == "offset") {
            // CYCLE-E: REAL geometry offset (was: silently ignored).
            // offset(dx,dy) shifts the recorded path; offset(dx,dy,dst)
            // stores the shifted copy into dst and leaves this path alone.
            const float dx = arg_as_float(ctx, 0, 0.f);
            const float dy = arg_as_float(ctx, 1, 0.f);
            if (ctx.args.size() >= 3) {
                const uint32_t dst_id = ctx.arg_as_object(2, 0);
                PathData& dst = paths_[dst_id];
                dst = pd;
                for (auto& c : dst.contours)
                    for (auto& p : c) { p.first += dx; p.second += dy; }
                dst.cx += dx; dst.cy += dy; dst.sx += dx; dst.sy += dy;
            } else if (dx != 0.f || dy != 0.f) {
                for (auto& c : pd.contours)
                    for (auto& p : c) { p.first += dx; p.second += dy; }
                pd.cx += dx; pd.cy += dy; pd.sx += dx; pd.sy += dy;
            }
            return CallResult::handled_void();
        }
        if (m == "setFillType") {
            // CYCLE-E: recorded and honored by the rasterizer (was: ignored).
            // Accepts an int ordinal or the synthesized Path.FillType enum
            // object. Android ordinals: 0 WINDING, 1 EVEN_ODD,
            // 2 INVERSE_WINDING, 3 INVERSE_EVEN_ODD.
            int ft = enum_arg_ordinal(ctx, 0, -1);
            if (ft < 0 || ft > 3) ft = 0;
            if (ft == 2 || ft == 3)
                warn_noop(cls, "setFillType(INVERSE_*) base-rule-applied");
            pd.fill_type = ft;
            return CallResult::handled_void();
        }
        if (m == "isEmpty") {
            // CYCLE-E: honest answer (was: constant 0).
            return CallResult::handled_int(pd.contours.empty() ? 1 : 0);
        }
        if (m == "isConvex") {
            // CYCLE-E: honest geometric answer (was: constant 1).
            const bool convex = pd.contours.size() == 1 &&
                                contour_is_convex(pd.contours.front());
            return CallResult::handled_int(convex ? 1 : 0);
        }
        if (m == "set") {
            // CYCLE-E: copy another path's geometry + fill type.
            const uint32_t src_id = ctx.arg_as_object(0, 0);
            auto sit = paths_.find(src_id);
            if (sit != paths_.end() && src_id != recv) pd = sit->second;
            return CallResult::handled_void();
        }
        if (m == "addRect") {
            // addRect(l,t,r,b,dir) | addRect(RectF,dir); dir 0=CCW 1=CW.
            float l, t, r, b;
            if (ctx.args.size() >= 5) {
                l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
                r = arg_as_float(ctx, 2); b = arg_as_float(ctx, 3);
            } else if (!read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
                warn_noop(cls, "addRect(RectF-unresolved)");
                return CallResult::handled_void();
            }
            const bool ccw = ctx.arg_as_int(ctx.args.size() >= 5 ? 4 : 1, 0) != 1;
            PointList c;
            if (ccw) { c = {{l, t}, {l, b}, {r, b}, {r, t}}; }   // visually CCW (y-down)
            else     { c = {{l, t}, {r, t}, {r, b}, {l, b}}; }   // visually CW
            pd.contours.push_back(std::move(c));
            pd.open = false;
            pd.cx = pd.sx = l; pd.cy = pd.sy = t;
            return CallResult::handled_void();
        }
        if (m == "addOval") {
            // addOval(l,t,r,b,dir) | addOval(RectF,dir).
            float l, t, r, b;
            if (ctx.args.size() >= 5) {
                l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
                r = arg_as_float(ctx, 2); b = arg_as_float(ctx, 3);
            } else if (!read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
                warn_noop(cls, "addOval(RectF-unresolved)");
                return CallResult::handled_void();
            }
            PointList c;
            append_oval_contour(c, (l + r) / 2.f, (t + b) / 2.f,
                                (r - l) / 2.f, (b - t) / 2.f);
            pd.contours.push_back(std::move(c));
            pd.open = false;
            pd.cx = pd.sx = l + (r - l) / 2.f; pd.cy = pd.sy = t;
            return CallResult::handled_void();
        }
        if (m == "addCircle") {
            PointList c;
            append_oval_contour(c, arg_as_float(ctx, 0), arg_as_float(ctx, 1),
                                arg_as_float(ctx, 2), arg_as_float(ctx, 2));
            pd.contours.push_back(std::move(c));
            pd.open = false;
            return CallResult::handled_void();
        }
        if (m == "addRoundRect") {
            // addRoundRect(l,t,r,b,rx,ry[,dir]) | (RectF,rx,ry[,dir]).
            float l, t, r, b;
            size_t base = 0;
            if (ctx.args.size() >= 6 && ctx.args[0].kind != CallContext::Arg::Kind::OBJECT) {
                l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
                r = arg_as_float(ctx, 2); b = arg_as_float(ctx, 3);
                base = 4;
            } else if (read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
                base = 1;   // rx/ry start after the RectF argument
            } else {
                warn_noop(cls, "addRoundRect(RectF-unresolved)");
                return CallResult::handled_void();
            }
            const float rx = arg_as_float(ctx, base, 0.f);
            const float ry = arg_as_float(ctx, base + 1, rx);
            const bool ccw = ctx.arg_as_int(base + 2, 0) != 1;
            PointList c;
            append_roundrect_contour(c, l, t, r, b, rx, ry, ccw);
            pd.contours.push_back(std::move(c));
            pd.open = false;
            return CallResult::handled_void();
        }
        if (m == "addArc" || m == "arcTo") {
            // addArc(oval, start, sweep) — new open contour.
            // arcTo(oval, start, sweep, forceMoveTo) — appends/continues.
            float l, t, r, b;
            size_t rect_args = 0;      // oval arg count (4 floats | RectF=1)
            bool force_move = true;
            if (m == "addArc") rect_args = (ctx.args.size() >= 7) ? 4 : 1;
            else               rect_args = (ctx.args.size() >= 8) ? 4 : 1;
            const size_t ai = rect_args;   // start/sweep start index
            if (rect_args == 4) {
                l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
                r = arg_as_float(ctx, 2); b = arg_as_float(ctx, 3);
            } else if (!read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
                warn_noop(cls, m + "(RectF-unresolved)");
                return CallResult::handled_void();
            }
            if (m == "arcTo") force_move = ctx.arg_as_bool(rect_args + 3, true);
            const float start = arg_as_float(ctx, ai, 0.f);
            const float sweep = arg_as_float(ctx, ai + 1, 0.f);
            const float cx = (l + r) / 2.f, cy = (t + b) / 2.f;
            const float rx = (r - l) / 2.f, ry = (b - t) / 2.f;
            const auto ep = arc_start_point(cx, cy, rx, ry, start + sweep);
            if (!force_move && pd.open && !pd.contours.empty()) {
                const auto sp = arc_start_point(cx, cy, rx, ry, start);
                pd.contours.back().push_back(sp);       // lineTo the arc start
                append_arc_points(pd.contours.back(), cx, cy, rx, ry, start, sweep);
                pd.cx = ep.first; pd.cy = ep.second;
            } else {
                PointList c;
                c.push_back(arc_start_point(cx, cy, rx, ry, start));
                append_arc_points(c, cx, cy, rx, ry, start, sweep);
                pd.contours.push_back(std::move(c));
                pd.open = true;
                pd.cx = pd.sx = ep.first;
                pd.cy = pd.sy = ep.second;
            }
            return CallResult::handled_void();
        }
        if (m == "addPath") {
            // addPath(src) | addPath(src, dx, dy) — append contours.
            const uint32_t src_id = ctx.arg_as_object(0, 0);
            auto sit = paths_.find(src_id);
            if (sit != paths_.end() && src_id != recv) {
                const float dx = ctx.args.size() >= 3 ? arg_as_float(ctx, 1, 0.f) : 0.f;
                const float dy = ctx.args.size() >= 3 ? arg_as_float(ctx, 2, 0.f) : 0.f;
                for (const auto& c : sit->second.contours) {
                    PointList copy = c;
                    if (dx != 0.f || dy != 0.f)
                        for (auto& p : copy) { p.first += dx; p.second += dy; }
                    pd.contours.push_back(std::move(copy));
                }
            }
            return CallResult::handled_void();
        }
        // Accepted-but-geometry-free Path calls (state-only semantics).
        if (m == "transform" || m == "computeBounds") {
            warn_noop(cls, m);
            return CallResult::handled_void();
        }
        return CallResult::not_handled();
    }

    // ── Canvas ─────────────────────────────────────────────────────────
    if (!capturing_) return CallResult::not_handled();  // outside draw dispatch

    const uint32_t recv = ctx.receiver_id;
    if (m == "drawColor" || m == "drawARGB" || m == "drawRGB") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_COLOR; op.x = 0.f;  // full view
        if (m == "drawColor") op.color = (uint32_t)ctx.arg_as_int(0, 0xFFFFFFFF);
        else if (m == "drawARGB") {
            op.color = ((uint32_t)ctx.arg_as_int(0, 255) << 24) |
                       ((uint32_t)ctx.arg_as_int(1, 0) << 16) |
                       ((uint32_t)ctx.arg_as_int(2, 0) << 8) |
                       (uint32_t)ctx.arg_as_int(3, 0);
        } else {
            op.color = 0xFF000000u |
                       ((uint32_t)ctx.arg_as_int(0, 0) << 16) |
                       ((uint32_t)ctx.arg_as_int(1, 0) << 8) |
                       (uint32_t)ctx.arg_as_int(2, 0);
        }
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawRect") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_RECT;
        // (l,t,r,b,paint) — floats
        float l = arg_as_float(ctx, 0), t = arg_as_float(ctx, 1);
        float r = arg_as_float(ctx, 2), b = arg_as_float(ctx, 3);
        uint32_t paint_id = ctx.arg_as_object(4);
        op.color = paint_color(paint_id);
        op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;  // 1=STROKE, 2=FILL_AND_STROKE (CYCLE-E)
        auto sw = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw != paint_stroke_w_.end() ? sw->second : 1.f;
        // NOTE: drawRect stores ABSOLUTE edges in x,y,w,h (existing replay
        // convention). S68: the matrix bakes all four corners — under a
        // translate this is byte-identical to the old tx_/ty_ adds; under
        // scale the corners normalize; under rotate/skew the rect becomes a
        // quad polygon drawn through the DRAW_PATH scanline rasterizer.
        if (mat_.is_translate_only()) {
            op.x = l + mat_.e; op.w = r + mat_.e;
            op.y = t + mat_.f; op.h = b + mat_.f;
        } else if (mat_.b == 0.f && mat_.c == 0.f) {
            // Axis-aligned scale/translate: normalized corner box.
            const float x1 = mat_.a * l + mat_.e, x2 = mat_.a * r + mat_.e;
            const float y1 = mat_.d * t + mat_.f, y2 = mat_.d * b + mat_.f;
            op.x = std::min(x1, x2); op.w = std::max(x1, x2);
            op.y = std::min(y1, y2); op.h = std::max(y1, y2);
            op.stroke_w *= mat_.mean_scale();
        } else {
            // Rotated/skewed: quad → winding-filled polygon.
            const float cx[4] = {l, r, r, l}, cy[4] = {t, t, b, b};
            PointList quad;
            for (int i = 0; i < 4; i++) {
                float px, py; mat_.map(cx[i], cy[i], px, py);
                quad.push_back({px, py});
            }
            op = DrawOp{}; op.kind = DrawOp::Kind::DRAW_PATH;
            op.color = paint_color(paint_id);
            op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;
            op.stroke_w = (sw != paint_stroke_w_.end() ? sw->second : 1.f) * mat_.mean_scale();
            op.fill_type = 0;
            op.contours.push_back(std::move(quad));
        }
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawRoundRect") {
        // S67 FOUNDATION (F-123, f08_canvasops fixture): AOSP arg-index law.
        // The float overload signature is drawRoundRect(left, top, right,
        // bottom, rx, ry, Paint) — PAINT LAST (index 6). The handler
        // previously assumed (l,t,r,b,paint,rx,ry), so the paint id was
        // read from the rx float slot: every drawRoundRect rendered with
        // the default paint color (black) regardless of the app's Paint —
        // fan-out across every card/rounded-shape UI in the corpus.
        DrawOp op; op.kind = DrawOp::Kind::DRAW_ROUNDRECT;
        float l = arg_as_float(ctx, 0), t = arg_as_float(ctx, 1);
        float r = arg_as_float(ctx, 2), b = arg_as_float(ctx, 3);
        const float rx = arg_as_float(ctx, 4, 0.f);          // rx (AOSP slot 4)
        uint32_t paint_id = ctx.arg_as_object(6);  // Paint (AOSP slot 6)
        if (mat_.b != 0.f || mat_.c != 0.f) {
            // S68: rotated/skewed rounded rect — bake to a corner-arc polygon
            // (8 segments per corner) through the DRAW_PATH rasterizer.
            PointList c;
            append_roundrect_contour(c, l, t, r, b, rx, arg_as_float(ctx, 5, rx), true);
            for (auto& p : c) { float px, py; mat_.map(p.first, p.second, px, py); p = {px, py}; }
            DrawOp pop; pop.kind = DrawOp::Kind::DRAW_PATH;
            pop.color = paint_color(paint_id);
            pop.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;
            pop.stroke_w = (paint_stroke_w_.count(paint_id) ? paint_stroke_w_[paint_id] : 1.f)
                           * mat_.mean_scale();
            pop.fill_type = 0;
            pop.contours.push_back(std::move(c));
            stamp_clip(pop);
            push_op(std::move(pop));
            return CallResult::handled_void();
        }
        const float sx = mat_.a, sy = mat_.d;
        op.x = l * sx + mat_.e; op.y = t * sy + mat_.f;
        op.w = (r - l) * std::fabs(sx); op.h = (b - t) * std::fabs(sy);
        op.r = rx * mat_.mean_scale();
        op.color = paint_color(paint_id);
        op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;
        auto sw2 = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw2 != paint_stroke_w_.end() ? sw2->second : 1.f;
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawCircle") {
        float cx0 = arg_as_float(ctx, 0), cy0 = arg_as_float(ctx, 1);
        float rad = arg_as_float(ctx, 2);
        uint32_t paint_id = ctx.arg_as_object(3);
        if (mat_.b != 0.f || mat_.c != 0.f || std::fabs(mat_.a - mat_.d) > 1e-6f) {
            // S68: circle under rotate/skew/unequal-scale → oval polygon
            // (kappa 4-cubic approximation) through the DRAW_PATH rasterizer.
            PointList c;
            append_oval_contour(c, cx0, cy0, rad, rad);
            for (auto& p : c) { float px, py; mat_.map(p.first, p.second, px, py); p = {px, py}; }
            DrawOp pop; pop.kind = DrawOp::Kind::DRAW_PATH;
            pop.color = paint_color(paint_id);
            pop.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;
            pop.stroke_w = (paint_stroke_w_.count(paint_id) ? paint_stroke_w_[paint_id] : 1.f)
                           * mat_.mean_scale();
            pop.fill_type = 0;
            pop.contours.push_back(std::move(c));
            stamp_clip(pop);
            push_op(std::move(pop));
            return CallResult::handled_void();
        }
        DrawOp op; op.kind = DrawOp::Kind::DRAW_CIRCLE;
        mat_.map(cx0, cy0, op.x, op.y);
        op.r = rad * mat_.mean_scale();
        op.color = paint_color(paint_id);
        op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;  // 1=STROKE, 2=FILL_AND_STROKE (CYCLE-E)
        auto sw = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw != paint_stroke_w_.end() ? sw->second : 1.f;
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawLine") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_LINE;
        float x1 = arg_as_float(ctx, 0), y1 = arg_as_float(ctx, 1);
        float x2 = arg_as_float(ctx, 2), y2 = arg_as_float(ctx, 3);
        mat_.map(x1, y1, x1, y1);
        mat_.map(x2, y2, x2, y2);
        op.x = x1; op.y = y1;
        op.w = x2; op.h = y2;
        uint32_t paint_id = ctx.arg_as_object(4);
        op.color = paint_color(paint_id);
        auto sw = paint_stroke_w_.find(paint_id);
        op.stroke_w = (sw != paint_stroke_w_.end() ? sw->second : 1.f) * mat_.mean_scale();
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawText") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_TEXT;
        op.text = ctx.arg_as_string(0);
        // S81: opt-in canvas text trace (§43 LOCATE step — app-drawn text)
        static const bool s_ctext_trace = std::getenv("MINIANDROID_TEXT_TRACE") != nullptr;
        if (s_ctext_trace) {
            float tx_ = 0.f, ty_ = 0.f;
            mat_.map(op.x, op.y, tx_, ty_);
            std::cerr << "[S81-CANVAS-TEXT] op=(" << op.x << "," << op.y
                      << ")->(" << tx_ << "," << ty_ << ") text=\""
                      << op.text.substr(0, 60) << "\"" << std::endl;
        }
        op.x = arg_as_float(ctx, 1);
        op.y = arg_as_float(ctx, 2);
        uint32_t paint_id = ctx.arg_as_object(ctx.args.size() >= 4 ? 3 : 0);
        op.color = paint_color(paint_id);
        // S68 §14: carry the paint text styling so replay can use the REAL
        // shaping pipeline (FreeType/HarfBuzz/FriBidi — Persian/Arabic/RTL
        // were 0-px on this path under the ASCII bitmap font).
        auto ts = paint_text_size_.find(paint_id);
        op.text_size_px = ts != paint_text_size_.end() ? ts->second : 0.f;
        op.text_bold = paint_fake_bold_.count(paint_id) && paint_fake_bold_[paint_id];
        mat_.map(op.x, op.y, op.x, op.y);
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawPath") {
        // FIX-5 + CYCLE-E: real path rasterization — apps that build their own
        // glyphs (stopwatch digits, clock hands) now produce real pixels.
        const uint32_t path_id = ctx.arg_as_object(0, 0);
        const uint32_t paint_id = ctx.arg_as_object(ctx.args.size() >= 2 ? 1 : 0);
        auto pit = paths_.find(path_id);
        if (pit != paths_.end() && !pit->second.contours.empty()) {
            DrawOp op; op.kind = DrawOp::Kind::DRAW_PATH;
            op.color = paint_color(paint_id);
            op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;  // 1=STROKE, 2=FILL_AND_STROKE (CYCLE-E)
            op.stroke_w = paint_stroke_w_.count(paint_id) ? paint_stroke_w_[paint_id] : 1.0f;
            op.contours = pit->second.contours;
            // CYCLE-E: honor the path's recorded fill rule (AOSP default is
            // WINDING; EVEN_ODD and the INVERSE_* variants map per Android).
            const int ft = pit->second.fill_type;
            op.fill_type = (ft == 1 || ft == 3) ? 1 : 0;
            // S68: bake contours with the FULL matrix (was: translate only).
            if (!mat_.is_identity()) {
                for (auto& c : op.contours)
                    for (auto& p : c) { float px, py; mat_.map(p.first, p.second, px, py); p = {px, py}; }
                op.stroke_w *= mat_.mean_scale();
            }
            stamp_clip(op);
            push_op(std::move(op));
        }
        return CallResult::handled_void();
    }
    if (m == "drawOval") {
        // CYCLE-E: REAL oval rasterization (was: silently swallowed).
        // Overloads: drawOval(l,t,r,b,paint) | drawOval(RectF,paint).
        float l, t, r, b;
        uint32_t paint_id = 0;
        bool ok = false;
        if (ctx.args.size() >= 5) {
            l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
            r = arg_as_float(ctx, 2); b = arg_as_float(ctx, 3);
            paint_id = ctx.arg_as_object(4);
            ok = true;
        } else if (read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
            paint_id = ctx.arg_as_object(1);
            ok = true;
        }
        if (ok && r > l && b > t) {
            DrawOp op; op.kind = DrawOp::Kind::DRAW_PATH;
            op.color = paint_color(paint_id);
            op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;  // 1=STROKE, 2=FILL_AND_STROKE (CYCLE-E)
            op.stroke_w = paint_stroke_w_.count(paint_id) ? paint_stroke_w_[paint_id] : 1.0f;
            op.fill_type = 0;   // convex — fill rule irrelevant
            // 4-cubic oval approximation (Skia kappa) — real curve pixels,
            // NOT a rounded rect and NOT the bounding box.
            PointList c;
            append_oval_contour(c, (l + r) / 2.f, (t + b) / 2.f,
                                (r - l) / 2.f, (b - t) / 2.f);
            op.contours.push_back(std::move(c));
            if (!mat_.is_identity()) {
                for (auto& cc : op.contours)
                    for (auto& p : cc) { float px, py; mat_.map(p.first, p.second, px, py); p = {px, py}; }
                op.stroke_w *= mat_.mean_scale();
            }
            stamp_clip(op);
            push_op(std::move(op));
        } else if (!ok) {
            // Degenerate rects legitimately draw nothing (AOSP); unresolved
            // ARGUMENTS are a compat problem worth reporting.
            warn_noop(cls, "drawOval(unresolved-args)");
        }
        return CallResult::handled_void();
    }
    if (m == "drawArc") {
        // CYCLE-E: REAL arc rasterization (was: silently swallowed).
        // Overloads: drawArc(l,t,r,b,start,sweep,useCenter,paint) — 8 args;
        //            drawArc(RectF,start,sweep,useCenter,paint) — 5 args.
        float l, t, r, b, start, sweep;
        bool use_center;
        uint32_t paint_id = 0;
        bool ok = false;
        if (ctx.args.size() >= 8) {
            l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
            r = arg_as_float(ctx, 2); b = arg_as_float(ctx, 3);
            start = arg_as_float(ctx, 4);
            sweep = arg_as_float(ctx, 5);
            use_center = ctx.arg_as_bool(6, false);
            paint_id = ctx.arg_as_object(7);
            ok = true;
        } else if (ctx.args.size() >= 5 &&
                   ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            if (read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
                start = arg_as_float(ctx, 1);
                sweep = arg_as_float(ctx, 2);
                use_center = ctx.arg_as_bool(3, false);
                paint_id = ctx.arg_as_object(4);
                ok = true;
            }
        }
        if (ok && r > l && b > t) {
            if (sweep == 0.f) return CallResult::handled_void();  // AOSP: nothing
            const float cx = (l + r) / 2.f, cy = (t + b) / 2.f;
            const float rx = (r - l) / 2.f, ry = (b - t) / 2.f;
            const bool full = sweep >= 360.f || sweep <= -360.f;
            DrawOp op; op.kind = DrawOp::Kind::DRAW_PATH;
            op.color = paint_color(paint_id);
            op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] >= 1;  // 1=STROKE, 2=FILL_AND_STROKE (CYCLE-E)
            op.stroke_w = paint_stroke_w_.count(paint_id) ? paint_stroke_w_[paint_id] : 1.0f;
            op.fill_type = 0;
            PointList c;
            if (full) {
                append_oval_contour(c, cx, cy, rx, ry);
            } else {
                c.push_back(arc_start_point(cx, cy, rx, ry, start));
                append_arc_points(c, cx, cy, rx, ry, start, sweep);
                if (use_center) {
                    // Pie wedge: arc + two radii (close via wrap-around edge).
                    c.push_back({cx, cy});
                    c.push_back(c.front());
                } else if (!op.stroke) {
                    // Chord close for filled arcs.
                    c.push_back(c.front());
                }
                // stroke open arc: polyline only — handled by the stroke walk
            }
            op.contours.push_back(std::move(c));
            if (!mat_.is_identity()) {
                for (auto& cc : op.contours)
                    for (auto& p : cc) { float px, py; mat_.map(p.first, p.second, px, py); p = {px, py}; }
                op.stroke_w *= mat_.mean_scale();
            }
            stamp_clip(op);
            push_op(std::move(op));
        } else if (!ok) {
            warn_noop(cls, "drawArc(unresolved-args)");
        }
        return CallResult::handled_void();
    }
    if (m == "drawPaint") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_PAINT;
        op.color = paint_color(ctx.arg_as_object(0));
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "translate") {
        // AOSP Canvas.translate — pre-concatenates onto the current matrix.
        mat_.pre_translate(arg_as_float(ctx, 0, 0.f), arg_as_float(ctx, 1, 0.f));
        return CallResult::handled_void();
    }
    if (m == "scale") {
        // S68 §12 (was accepted_not_reproduced NO-OP — S67 pixel-proven):
        // scale(sx,sy[,px,py]) pre-concatenates; pivot variants translate
        // around first (AOSP Canvas.scale(sx,sy,pivotX,pivotY) law).
        const float sx = arg_as_float(ctx, 0, 1.f), sy = arg_as_float(ctx, 1, sx);
        if (ctx.args.size() >= 4) {
            const float px = arg_as_float(ctx, 2, 0.f), py = arg_as_float(ctx, 3, 0.f);
            mat_.pre_translate(px, py);
            mat_.pre_scale(sx, sy);
            mat_.pre_translate(-px, -py);
        } else {
            mat_.pre_scale(sx, sy);
        }
        return CallResult::handled_void();
    }
    if (m == "rotate") {
        // S68 §12: rotate(degrees[,px,py]) — positive = clockwise in y-down
        // space (Skia law); pivot variants rotate around (px, py).
        const float deg = arg_as_float(ctx, 0, 0.f);
        if (ctx.args.size() >= 3) {
            const float px = arg_as_float(ctx, 1, 0.f), py = arg_as_float(ctx, 2, 0.f);
            mat_.pre_translate(px, py);
            mat_.pre_rotate(deg);
            mat_.pre_translate(-px, -py);
        } else {
            mat_.pre_rotate(deg);
        }
        return CallResult::handled_void();
    }
    if (m == "skew") {
        mat_.pre_skew(arg_as_float(ctx, 0, 0.f), arg_as_float(ctx, 1, 0.f));
        return CallResult::handled_void();
    }
    if (m == "concat") {
        // android.graphics.Matrix values live in heap fields when a Matrix
        // shadow recorded them; without a Matrix object we cannot honor the
        // op — report it (no silent no-op).
        const uint32_t mid = ctx.arg_as_object(0, 0);
        Affine2D c;
        bool ok = false;
        float v = 0.f;
        // AOSP Matrix stores 9 floats (3x3) named m[0..8] via setValues;
        // the heap field names we accept: m0..m8 (setValues layout).
        auto try_read = [&](const char* name, float& out) {
            return heap_ && heap_->get_object_float_field(mid, name, out);
        };
        if (mid != 0 && try_read("m0", c.a) && try_read("m3", c.c) &&
            try_read("m6", c.e) && try_read("m1", c.b) &&
            try_read("m4", c.d) && try_read("m7", c.f)) {
            ok = true;   // affine rows of the 3x3 (perspective row ignored)
        }
        if (ok) {
            mat_.pre_concat(c);
            return CallResult::handled_void();
        }
        warn_noop(cls, "concat(Matrix-unresolved)");
        return CallResult::handled_void();
    }
    if (m == "save") {
        // AOSP: save() snapshots BOTH matrix and clip; flags accepted.
        save_stack_.push_back({mat_, clip_});
        return CallResult::handled_int((int)save_stack_.size() + 1);  // AOSP saveCount starts at 1
    }
    if (m == "restore") {
        if (!save_stack_.empty()) {
            mat_ = save_stack_.back().mat;
            clip_ = save_stack_.back().clip;
            save_stack_.pop_back();
        }
        return CallResult::handled_void();
    }
    if (m == "restoreToCount") {
        // AOSP: restore to the state save() returned n → keep first n-1
        // entries of the save stack (saveCount baseline 1).
        const int n = ctx.arg_as_int(0, 1);
        while ((int)save_stack_.size() >= n && n >= 1 && !save_stack_.empty() &&
               (int)save_stack_.size() > n - 1) {
            save_stack_.pop_back();
        }
        if (!save_stack_.empty()) { /* states restored lazily on next op? */ }
        if (n >= 1 && (int)save_stack_.size() == n - 1) {
            mat_ = save_stack_.empty() ? Affine2D{} : save_stack_.back().mat;
            clip_ = save_stack_.empty() ? ClipRect{} : save_stack_.back().clip;
        }
        return CallResult::handled_void();
    }
    if (m == "saveLayer" || m == "saveLayerAlpha") {
        // S68: LAYER ISOLATION is DEFERRED-BY-CONTRACT (offscreen buffer +
        // alpha compositing). The STATE snapshot (matrix+clip) is honored —
        // draws land on the shared framebuffer at restore time. Reported.
        warn_noop(cls, "saveLayer(deferred-layer-isolation; state honored)");
        save_stack_.push_back({mat_, clip_});
        return CallResult::handled_int((int)save_stack_.size() + 1);
    }
    if (m == "getSaveCount") {
        return CallResult::handled_int((int)save_stack_.size() + 1);
    }
    if (m == "drawRenderNode") {
        // AOSP compositing: replay a recorded RenderNode's display list into
        // this canvas, offset by the node's position (transformed through
        // the current matrix — S68: map() covers translate + scale/rotate).
        const uint32_t node_id = ctx.arg_as_object(0, 0);
        auto it = render_nodes_.find(node_id);
        if (it != render_nodes_.end()) {
            float ox = node_pos_l_.count(node_id) ? node_pos_l_[node_id] : 0.f;
            float oy = node_pos_t_.count(node_id) ? node_pos_t_[node_id] : 0.f;
            mat_.map(ox, oy, ox, oy);
            // Node-local translate is the only recorded matrix inside a
            // node (RecordingCanvas starts fresh) — the outer affine folds
            // into the offset for translate-only inner state, which is what
            // Compose child positioning produces.
            for (const DrawOp& op : it->second) {
                DrawOp c = op;
                stamp_clip(c);
                c.x += ox; c.y += oy;
                if (c.kind == DrawOp::Kind::DRAW_RECT || c.kind == DrawOp::Kind::DRAW_LINE)
                    { c.w += ox; c.h += oy; }
                push_op(std::move(c));
            }
        }
        return CallResult::handled_void();
    }
    if (m == "clipRect" || m == "clipPath") {
        if (m == "clipPath") {
            // DEFERRED-BY-CONTRACT: region-op on a general path (antialias
            // sampling). Rect clip is the dominant consumer in the corpus.
            warn_noop(cls, "clipPath(deferred)");
            return CallResult::handled_bool(true);
        }
        // clipRect(l,t,r,b[,op]) | clipRect(l,t,w,h[,op]) | clipRect(RectF[,op])
        float l, t, r, b;
        if (ctx.args.size() >= 4 &&
            ctx.args[0].kind != CallContext::Arg::Kind::OBJECT) {
            l = arg_as_float(ctx, 0); t = arg_as_float(ctx, 1);
            const float a2 = arg_as_float(ctx, 2), a3 = arg_as_float(ctx, 3);
            // AOSP overload disambiguation: (l,t,r,b) or (l,t,w,h). The
            // width/height variant passes right/bottom == l+w / t+h.
            const int op_idx = ctx.args.size() >= 5 ? 4 : -1;
            (void)op_idx;
            r = l + a2;   // resolve via heuristic below
            b = t + a3;
            // Heuristic law: a2>a3 or a2==a3 both plausible... AOSP apps use
            // the (l,t,r,b) form overwhelmingly; we follow the ABSOLUTE form
            // when a2 > l and a3 > t (edges ahead of origin), else the W/H form.
            if (a2 > l && a3 > t) { r = a2; b = a3; }
        } else if (!read_rectf_fields(heap_, ctx.arg_as_object(0), l, t, r, b)) {
            warn_noop(cls, "clipRect(RectF-unresolved)");
            return CallResult::handled_bool(false);
        }
        // Bake with the CURRENT matrix into op space (same space as draws).
        float cl, ct, cr, cb;
        if (mat_.is_translate_only()) {
            cl = l + mat_.e; ct = t + mat_.f;
            cr = r + mat_.e; cb = b + mat_.f;
        } else {
            const float cx[4] = {l, r, l, r}, cy[4] = {t, t, b, b};
            cl = ct = 1e30f; cr = cb = -1e30f;
            for (int i = 0; i < 4; i++) {
                float px, py; mat_.map(cx[i], cy[i], px, py);
                cl = std::min(cl, px); cr = std::max(cr, px);
                ct = std::min(ct, py); cb = std::max(cb, py);
            }
        }
        if (!clip_.active) {
            clip_ = {cl, ct, cr, cb, true};
        } else {
            // AOSP RegionOp.INTERSECT default law.
            clip_ = {std::max(clip_.l, cl), std::max(clip_.t, ct),
                     std::min(clip_.r, cr), std::min(clip_.b, cb), true};
        }
        return CallResult::handled_bool(clip_.r > clip_.l && clip_.b > clip_.t);
    }
    if (m == "drawBitmap") {
        // S68 §12 (was accepted_not_reproduced): drawBitmap family.
        //   (Bitmap, float l, float t, Paint)                     args: obj,f,f,obj
        //   (Bitmap, Rect src, RectF|Rect dst, Paint)             args: obj,obj,obj,obj
        //   (int[] colors, int off, int stride, x,y,w,h, hasAlpha, Paint)
        const uint32_t paint_id = ctx.arg_as_object(ctx.args.size() - 1, 0);
        DrawOp op; op.kind = DrawOp::Kind::DRAW_BITMAP;
        op.color = paint_color(paint_id);
        auto fb = paint_filter_bitmap_.find(paint_id);
        op.filter_bitmap = fb != paint_filter_bitmap_.end() && fb->second;
        if (ctx.args.size() >= 9 && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            // int[] variant — materialize pixels into a synthetic Bitmap.
            const uint32_t colors = ctx.arg_as_object(0, 0);
            const int off = ctx.arg_as_int(1, 0), stride = ctx.arg_as_int(2, 0);
            const int bx = ctx.arg_as_int(3, 0), by = ctx.arg_as_int(4, 0);
            const int bw = ctx.arg_as_int(5, 0), bh = ctx.arg_as_int(6, 0);
            if (heap_ && bw > 0 && bh > 0) {
                std::vector<uint8_t> rgba((size_t)bw * bh * 4, 0);
                int32_t alen = 0;
                heap_->get_object_array_length(colors, alen);
                int filled = 0;
                for (int row = 0; row < bh; row++) {
                    for (int col = 0; col < bw; col++) {
                        const int idx = off + row * stride + col;
                        int32_t argb = 0;
                        if (idx < alen && heap_->get_object_int_field(
                                colors, "array[" + std::to_string(idx) + "]", argb)) {
                            rgba[((size_t)row * bw + col) * 4 + 0] = (argb >> 16) & 0xFF;
                            rgba[((size_t)row * bw + col) * 4 + 1] = (argb >> 8) & 0xFF;
                            rgba[((size_t)row * bw + col) * 4 + 2] = argb & 0xFF;
                            rgba[((size_t)row * bw + col) * 4 + 3] = (argb >> 24) & 0xFF;
                            filled++;
                        }
                    }
                }
                if (filled > 0) {
                    const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
                    framework::BitmapStore::instance().store(obj, bw, bh, std::move(rgba),
                                                             "drawBitmap(int[])");
                    op.bitmap_id = obj;
                    op.x = bx; op.y = by; op.w = (float)bw; op.h = (float)bh;
                    op.has_dst = true;
                }
            }
        } else if (ctx.args.size() >= 4 &&
                   ctx.args[2].kind == CallContext::Arg::Kind::OBJECT) {
            // (Bitmap, src Rect, dst Rect/RectF, Paint)
            op.bitmap_id = ctx.arg_as_object(0, 0);
            float sl, st, sr, sbl;
            if (read_rectf_fields(heap_, ctx.arg_as_object(1), sl, st, sr, sbl)) {
                op.has_src = true;
                op.src_l = sl; op.src_t = st; op.src_r = sr; op.src_b = sbl;
            }
            float dl, dt, dr, db;
            if (read_rectf_fields(heap_, ctx.arg_as_object(2), dl, dt, dr, db)) {
                op.has_dst = true;
                op.x = dl; op.y = dt; op.w = dr - dl; op.h = db - dt;
            }
        } else {
            // (Bitmap, float l, float t, Paint) — dst = natural size.
            op.bitmap_id = ctx.arg_as_object(0, 0);
            float l = arg_as_float(ctx, 1), t = arg_as_float(ctx, 2);
            mat_.map(l, t, l, t);
            op.x = l; op.y = t;
            op.has_dst = false;   // replay resolves natural size from the store
        }
        if (op.has_dst) {
            // Bake the dst rect with the CURRENT matrix (same law as rects).
            if (!op.has_src || true) { /* dst baking below */ }
            float dl = op.x, dt = op.y, dr = op.x + op.w, db = op.y + op.h;
            float bl, bt, br, bb;
            if (mat_.is_translate_only()) {
                bl = dl + mat_.e; bt = dt + mat_.f; br = dr + mat_.e; bb = db + mat_.f;
                op.x = bl; op.y = bt; op.w = br - bl; op.h = bb - bt;
                op.affine = Affine2D{};
                op.has_affine = false;
            } else {
                const float cx[4] = {dl, dr, dl, dr}, cy[4] = {dt, dt, db, db};
                bl = bt = 1e30f; br = bb = -1e30f;
                for (int i = 0; i < 4; i++) {
                    float px, py; mat_.map(cx[i], cy[i], px, py);
                    bl = std::min(bl, px); br = std::max(br, px);
                    bt = std::min(bt, py); bb = std::max(bb, py);
                }
                op.x = bl; op.y = bt; op.w = br - bl; op.h = bb - bt;
                op.affine = mat_;
                op.has_affine = true;   // rotated/scaled → per-pixel sampling
            }
        }
        if (op.bitmap_id != 0) { stamp_clip(op); push_op(std::move(op)); }
        else warn_noop(cls, "drawBitmap(bitmap-unresolved)");
        return CallResult::handled_void();
    }
    if (m == "drawPoint") {
        // AOSP: a point is a SQUARE of side strokeWidth centered on (x,y)
        // (Paint.Cap.SQUARE butt default for points law).
        DrawOp op; op.kind = DrawOp::Kind::DRAW_RECT;
        float px = arg_as_float(ctx, 0), py = arg_as_float(ctx, 1);
        uint32_t paint_id = ctx.arg_as_object(2);
        op.color = paint_color(paint_id);
        auto sw = paint_stroke_w_.find(paint_id);
        const float width = sw != paint_stroke_w_.end() && sw->second > 0.f ? sw->second : 1.f;
        mat_.map(px, py, px, py);
        op.x = px - width / 2; op.y = py - width / 2;
        op.w = op.x + width; op.h = op.y + width;   // absolute-edges convention
        op.stroke = false;
        stamp_clip(op);
        push_op(std::move(op));
        return CallResult::handled_void();
    }
    if (m == "drawPosText" || m == "drawPoints" || m == "drawLines" ||
        m == "drawBitmapMesh" || m == "drawVertices" || m == "drawPicture" ||
        m == "drawTextRun" || m == "drawTextOnPath") {
        // Accepted but geometry not reproduced (registered, honest).
        warn_noop(cls, m);
        return CallResult::handled_void();
    }
    if (m == "getWidth") return CallResult::handled_int(canvas_w_);
    if (m == "getHeight") return CallResult::handled_int(canvas_h_);
    // F-095 (R-NEW-328) software-renderer truth law: the runtime renders
    // through a software framebuffer — Canvas.isHardwareAccelerated() MUST
    // answer false. Upstream consumers branch on it: compose 1.6.7
    // ViewLayer.dispatchDraw clips manually when the canvas is software
    // (ViewLayer.android.kt: `if (clipPath != null || !canvas.isHardwareAccelerated)`)
    // and RenderNodeLayer.drawLayer falls back to direct drawBlock drawing
    // (RenderNodeLayer.android.kt) — the honest answer keeps both on their
    // correct software path. The default (unhandled → false) already matched,
    // but answering EXPLICITLY documents the law and guards against a future
    // default flip silently re-routing compose into the hardware/RenderNode
    // path we cannot reproduce.
    if (m == "isHardwareAccelerated") return CallResult::handled_bool(false);
    return CallResult::not_handled();
}

} } // namespace miniandroid::framework
