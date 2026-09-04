// CAMPAIGN 013 — Canvas/Paint shadow implementation. See canvas_shadow.h.
#include "canvas_shadow.h"
#include "../renderer/software_renderer.h"

#include <algorithm>
#include <cmath>
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

}  // namespace

void CanvasShadow::begin_frame() {
    ops_.clear();
    capturing_ = true;
    // UC009: fresh frame = fresh canvas state (AOSP Canvas lifecycle).
    tx_ = ty_ = 0;
    save_stack_.clear();
    recording_node_ = 0;
}

size_t CanvasShadow::replay(renderer::SoftwareCanvas& canvas,
                            renderer::BitmapFont& font,
                            float left, float top, float w, float h) {
    for (const auto& op : ops_) {
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
                // v1: filled rect (corner radius recorded but not rasterized).
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
                std::vector<float> xs;
                for (int y = y0; y <= y1; ++y) {
                    const float sy = (float)y + 0.5f;
                    xs.clear();
                    for (const auto& e : edges) {
                        float ey1 = e.y1, ey2 = e.y2;
                        if ((sy >= ey1 && sy < ey2) || (sy >= ey2 && sy < ey1)) {
                            float t = (sy - ey1) / (ey2 - ey1);
                            xs.push_back(e.x1 + t * (e.x2 - e.x1));
                        }
                    }
                    if (xs.size() < 2) continue;
                    std::sort(xs.begin(), xs.end());
                    // Even-odd: fill between crossing pairs.
                    for (size_t i = 0; i + 1 < xs.size(); i += 2) {
                        float xa = xs[i], xb = xs[i + 1];
                        if (xb - xa < 0.5f) continue;
                        canvas.draw_rect(xa, (float)y, xb, (float)y + 1, c);
                    }
                }
                break;
            }
            case DrawOp::Kind::DRAW_TEXT: {
                canvas.draw_text(op.text, left + op.x, top + op.y, c, &font);
                break;
            }
            case DrawOp::Kind::DRAW_PAINT: {
                canvas.draw_rect(left, top, left + w, top + h, c);
                break;
            }
        }
    }
    capturing_ = false;
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
        if (m == "getColor") {
            return CallResult::handled_int((int32_t)paint_color(recv));
        }
        if (m == "setAlpha") {
            uint32_t cur = paint_color(recv);
            uint32_t a = (uint32_t)ctx.arg_as_int(0, 255) & 0xFF;
            paint_color_[recv] = (cur & 0x00FFFFFF) | (a << 24);
            return CallResult::handled_void();
        }
        if (m == "setAntiAlias" || m == "setDither" || m == "setFilterBitmap" ||
            m == "setFakeBoldText" || m == "setUnderlineText" || m == "setFlags") {
            return CallResult::handled_void();
        }
        if (m == "setStrokeWidth") {
            paint_stroke_w_[recv] = arg_as_float(ctx, 0, 1.f);
            return CallResult::handled_void();
        }
        if (m == "setStyle") {
            // Style.STROKE ordinal = 1
            paint_style_[recv] = ctx.arg_as_int(0, 0);
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

    // ── Path (FIX-5: real geometry recording) ─────────────────────────
    if (cls.find("graphics/Path;") != std::string::npos) {
        const uint32_t recv = ctx.receiver_id;
        PathData& pd = paths_[recv];
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
        if (m == "lineTo") {
            if (!pd.open) {  // implicit moveTo(0,0) per Android docs
                pd.contours.push_back({});
                pd.open = true;
                pd.sx = pd.sy = 0;
                pd.contours.back().push_back({0.f, 0.f});
            }
            pd.cx = arg_as_float(ctx, 0);
            pd.cy = arg_as_float(ctx, 1);
            pd.contours.back().push_back({pd.cx, pd.cy});
            return CallResult::handled_void();
        }
        if (m == "quadTo") {
            if (!pd.open) {
                pd.contours.push_back({});
                pd.open = true;
                pd.sx = pd.sy = 0;
                pd.contours.back().push_back({0.f, 0.f});
            }
            const float x1 = arg_as_float(ctx, 0), y1 = arg_as_float(ctx, 1);
            const float x2 = arg_as_float(ctx, 2), y2 = arg_as_float(ctx, 3);
            // Flatten the quadratic Bézier (8 segments — plenty at UI size).
            constexpr int kSegs = 8;
            for (int i = 1; i <= kSegs; ++i) {
                const float t = (float)i / kSegs, u = 1.0f - t;
                const float px = u * u * pd.cx + 2 * u * t * x1 + t * t * x2;
                const float py = u * u * pd.cy + 2 * u * t * y1 + t * t * y2;
                pd.contours.back().push_back({px, py});
            }
            pd.cx = x2; pd.cy = y2;
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
        // Accepted-but-geometry-free Path calls (state-only semantics).
        if (m == "setFillType" || m == "isConvex" || m == "isEmpty" ||
            m == "offset" || m == "transform" || m == "set" || m == "computeBounds")
            return m == "isEmpty" ? CallResult::handled_int(0)
                 : m == "isConvex" ? CallResult::handled_int(1)
                 : CallResult::handled_void();
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
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawRect") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_RECT;
        // (l,t,r,b,paint) — floats
        op.x = arg_as_float(ctx, 0); op.y = arg_as_float(ctx, 1);
        op.w = arg_as_float(ctx, 2); op.h = arg_as_float(ctx, 3);
        uint32_t paint_id = ctx.arg_as_object(4);
        op.color = paint_color(paint_id);
        op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] == 1;
        auto sw = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw != paint_stroke_w_.end() ? sw->second : 1.f;
        // NOTE: drawRect stores ABSOLUTE edges in x,y,w,h (existing replay
        // convention) — translate shifts both edges.
        op.x += tx_; op.w += tx_;
        op.y += ty_; op.h += ty_;
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawRoundRect") {
        // Compose backgrounds/cards are round rects. Approximate as rect with
        // corner radius recorded (replay draws filled rect — honest v1).
        DrawOp op; op.kind = DrawOp::Kind::DRAW_ROUNDRECT;
        // args are (l,t,r,b,paint,rx,ry)
        float l = arg_as_float(ctx, 0), t = arg_as_float(ctx, 1);
        float r = arg_as_float(ctx, 2), b = arg_as_float(ctx, 3);
        op.x = l + tx_; op.y = t + ty_; op.w = r - l; op.h = b - t;
        op.r = arg_as_float(ctx, 5, 0.f);
        uint32_t paint_id = ctx.arg_as_object(4);
        op.color = paint_color(paint_id);
        auto sw2 = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw2 != paint_stroke_w_.end() ? sw2->second : 1.f;
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawCircle") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_CIRCLE;
        op.x = arg_as_float(ctx, 0); op.y = arg_as_float(ctx, 1);
        op.r = arg_as_float(ctx, 2);
        uint32_t paint_id = ctx.arg_as_object(3);
        op.color = paint_color(paint_id);
        op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] == 1;
        auto sw = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw != paint_stroke_w_.end() ? sw->second : 1.f;
        op.x += tx_; op.y += ty_;
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawLine") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_LINE;
        op.x = arg_as_float(ctx, 0); op.y = arg_as_float(ctx, 1);
        op.w = arg_as_float(ctx, 2); op.h = arg_as_float(ctx, 3);
        uint32_t paint_id = ctx.arg_as_object(4);
        op.color = paint_color(paint_id);
        auto sw = paint_stroke_w_.find(paint_id);
        op.stroke_w = sw != paint_stroke_w_.end() ? sw->second : 1.f;
        op.x += tx_; op.w += tx_;   // absolute endpoints convention
        op.y += ty_; op.h += ty_;
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawText") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_TEXT;
        op.text = ctx.arg_as_string(0);
        op.x = arg_as_float(ctx, 1);
        op.y = arg_as_float(ctx, 2);
        uint32_t paint_id = ctx.arg_as_object(ctx.args.size() >= 4 ? 3 : 0);
        op.color = paint_color(paint_id);
        op.x += tx_; op.y += ty_;
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawPath") {
        // FIX-5: real path rasterization — apps that build their own glyphs
        // (stopwatch digits, clock hands) now produce real pixels.
        const uint32_t path_id = ctx.arg_as_object(0, 0);
        const uint32_t paint_id = ctx.arg_as_object(ctx.args.size() >= 2 ? 1 : 0);
        auto pit = paths_.find(path_id);
        if (pit != paths_.end() && !pit->second.contours.empty()) {
            DrawOp op; op.kind = DrawOp::Kind::DRAW_PATH;
            op.color = paint_color(paint_id);
            op.stroke = paint_style_.count(paint_id) && paint_style_[paint_id] == 1;
            op.stroke_w = paint_stroke_w_.count(paint_id) ? paint_stroke_w_[paint_id] : 1.0f;
            op.contours = pit->second.contours;
            if (tx_ != 0.f || ty_ != 0.f) {
                for (auto& c : op.contours)
                    for (auto& p : c) { p.first += tx_; p.second += ty_; }
            }
            target().push_back(op);
        }
        return CallResult::handled_void();
    }
    if (m == "drawPaint") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_PAINT;
        op.color = paint_color(ctx.arg_as_object(0));
        target().push_back(op);
        return CallResult::handled_void();
    }
    if (m == "translate") {
        // AOSP Canvas.translate — needed by Compose child positioning.
        tx_ += arg_as_float(ctx, 0, 0.f);
        ty_ += arg_as_float(ctx, 1, 0.f);
        return CallResult::handled_void();
    }
    if (m == "save") {
        save_stack_.push_back({tx_, ty_});
        return CallResult::handled_int((int)save_stack_.size());
    }
    if (m == "restore") {
        if (!save_stack_.empty()) {
            tx_ = save_stack_.back().first;
            ty_ = save_stack_.back().second;
            save_stack_.pop_back();
        }
        return CallResult::handled_void();
    }
    if (m == "drawRenderNode") {
        // AOSP compositing: replay a recorded RenderNode's display list into
        // this canvas, offset by the node's position.
        const uint32_t node_id = ctx.arg_as_object(0, 0);
        auto it = render_nodes_.find(node_id);
        if (it != render_nodes_.end()) {
            float ox = node_pos_l_.count(node_id) ? node_pos_l_[node_id] : 0.f;
            float oy = node_pos_t_.count(node_id) ? node_pos_t_[node_id] : 0.f;
            auto& tgt = target();
            for (const DrawOp& op : it->second) {
                DrawOp c = op;
                c.x += ox; c.y += oy;
                tgt.push_back(c);
            }
        }
        return CallResult::handled_void();
    }
    if (m == "rotate" || m == "scale" || m == "skew" || m == "concat" ||
        m == "clipRect" || m == "saveLayer" || m == "restoreToCount" ||
        m == "drawOval" || m == "drawArc" || m == "drawPath" ||
        m == "drawBitmap" || m == "drawPoint" || m == "drawPosText") {
        // Accepted (flat state model); complex geometry is TODO on evidence.
        return CallResult::handled_void();
    }
    if (m == "getWidth") return CallResult::handled_int(1080);
    if (m == "getHeight") return CallResult::handled_int(1920);
    return CallResult::not_handled();
}

} } // namespace miniandroid::framework
