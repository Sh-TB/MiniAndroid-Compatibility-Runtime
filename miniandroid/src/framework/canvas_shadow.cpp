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
        ops_.push_back(op);
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
        ops_.push_back(op);
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
        ops_.push_back(op);
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
        ops_.push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawText") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_TEXT;
        op.text = ctx.arg_as_string(0);
        op.x = arg_as_float(ctx, 1);
        op.y = arg_as_float(ctx, 2);
        uint32_t paint_id = ctx.arg_as_object(ctx.args.size() >= 4 ? 3 : 0);
        op.color = paint_color(paint_id);
        ops_.push_back(op);
        return CallResult::handled_void();
    }
    if (m == "drawPaint") {
        DrawOp op; op.kind = DrawOp::Kind::DRAW_PAINT;
        op.color = paint_color(ctx.arg_as_object(0));
        ops_.push_back(op);
        return CallResult::handled_void();
    }
    if (m == "save" || m == "restore" || m == "translate" || m == "rotate" ||
        m == "scale" || m == "skew" || m == "concat" || m == "clipRect" ||
        m == "saveLayer" || m == "restoreToCount" || m == "drawOval" ||
        m == "drawRoundRect" || m == "drawArc" || m == "drawPath" ||
        m == "drawBitmap" || m == "drawPoint" || m == "drawPosText") {
        // State ops are accepted (state model is flat); complex geometry ops
        // are TODO on evidence.
        return CallResult::handled_void();
    }
    if (m == "getWidth") return CallResult::handled_int(1080);
    if (m == "getHeight") return CallResult::handled_int(1920);
    return CallResult::not_handled();
}

} } // namespace miniandroid::framework
