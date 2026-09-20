// CAMPAIGN 013 — Canvas/Paint shadow: REAL app onDraw() execution.
//
// Apps draw custom views by overriding View.onDraw(Canvas) and calling
// android.graphics.Canvas / android.graphics.Paint methods. bouncy's
// CanvasFieldView/ScoreView (libGDX canvas backend) and thousands of game/
// utility apps live on this path. Previously the runtime could not execute
// onDraw at all: custom views painted nothing (or the grey C013
// placeholder when the screen was blank).
//
// Model (no fake drawing):
//   1. ExecutionEngine allocates a Canvas heap object per draw dispatch.
//   2. try_recursive_invoke(view_class, "onDraw", {view, canvas}) runs the
//      app's REAL draw bytecode; CanvasShadow records primitive ops.
//   3. replay() maps recorded ops onto the SoftwareCanvas inside the view's
//      measured bounds — the same framebuffer every other view paints into.
//
// Supported primitives (evidence-driven, extend on demand):
//   drawColor/drawARGB/drawRGB, drawRect, drawCircle, drawLine, drawText,
//   drawPaint, save/restore/translate/rotate (state tracked for text/colors),
//   Paint: setColor/getColor/setAlpha/setAntiAlias/setStyle/setStrokeWidth/
//   setTextSize.

#pragma once

#include "shadow_registry.h"
#include "../renderer/software_renderer.h"

#include <cstdint>
#include <cmath>
#include <map>
#include <string>
#include <vector>

namespace miniandroid { namespace framework {

class CanvasShadow;
class PaintShadow;

// ── S68 FOUNDATION (§12 Canvas transform law, upstream Skia SkCanvas) ────
// AOSP Canvas.translate/scale/rotate/skew/concat pre-concatenate the CURRENT
// matrix with the new transform: device = M_prev ∘ Op ∘ local. The matrix
// applies to EVERY recorded primitive. This is the full 2D affine:
//   x' = a*x + c*y + e ;  y' = b*x + d*y + f
struct Affine2D {
    float a = 1, b = 0, c = 0, d = 1, e = 0, f = 0;
    void map(float x, float y, float& ox, float& oy) const {
        ox = a * x + c * y + e;
        oy = b * x + d * y + f;
    }
    // M = M ∘ translate(tx,ty)
    void pre_translate(float tx, float ty) {
        e += a * tx + c * ty;
        f += b * tx + d * ty;
    }
    // M = M ∘ scale(sx,sy)
    void pre_scale(float sx, float sy) {
        a *= sx; b *= sx; c *= sy; d *= sy;
    }
    // M = M ∘ rotate(degrees) — Android positive angle = clockwise in the
    // y-down screen space (Skia law): +x axis maps onto +y (down) at 90°.
    void pre_rotate(float degrees) {
        const float rad = degrees * 3.14159265358979323846f / 180.0f;
        const float cs = std::cos(rad), sn = std::sin(rad);
        // R = [cs -sn ; sn cs] (y-down clockwise). M = M ∘ R:
        const float na = a * cs - c * sn;
        const float nb = b * cs - d * sn;
        const float nc = a * sn + c * cs;
        const float nd = b * sn + d * cs;
        a = na; b = nb; c = nc; d = nd;
    }
    // M = M ∘ skew(kx,ky): x' = x + kx*y ; y' = ky*x + y
    void pre_skew(float kx, float ky) {
        const float na = a + c * ky;
        const float nb = b + d * ky;
        const float nc = a * kx + c;
        const float nd = b * kx + d;
        a = na; b = nb; c = nc; d = nd;
    }
    // M = M ∘ C where C is a raw 2x3 (a,b,c,d,e,f).
    void pre_concat(const Affine2D& r) {
        const float na = a * r.a + c * r.b;
        const float nb = b * r.a + d * r.b;
        const float nc = a * r.c + c * r.d;
        const float nd = b * r.c + d * r.d;
        const float ne = a * r.e + c * r.f + e;
        const float nf = b * r.e + d * r.f + f;
        a = na; b = nb; c = nc; d = nd; e = ne; f = nf;
    }
    // Pure-translate (the historically baked fast path) — replay must keep
    // producing BYTE-IDENTICAL pixels for this class (regression law).
    bool is_translate_only() const {
        return a == 1.f && b == 0.f && c == 0.f && d == 1.f;
    }
    bool is_identity() const {
        return is_translate_only() && e == 0.f && f == 0.f;
    }
    // Mean geometry scale — stroke widths scale with sqrt(|det|) per Skia.
    float mean_scale() const {
        return std::sqrt(std::fabs(a * d - b * c));
    }
};

// One recorded draw primitive (coordinates in VIEW space, density=1).
struct DrawOp {
    enum class Kind {
        DRAW_COLOR, DRAW_RECT, DRAW_ROUNDRECT, DRAW_CIRCLE, DRAW_LINE, DRAW_TEXT, DRAW_PAINT,
        DRAW_PATH,
        // S68 §12: bitmap draw — pixels resolved from BitmapStore at replay.
        DRAW_BITMAP
    };
    Kind kind = Kind::DRAW_COLOR;
    float x = 0, y = 0, w = 0, h = 0;   // rect: x,y,w,h ; line: x1,y1,x2,y2 in x,y,w,h
    float r = 0;                        // circle radius / roundrect corner radius
    uint32_t color = 0xFF000000;
    float stroke_w = 1.0f;
    std::string text;                   // DRAW_TEXT
    // Paint style: 0=fill, 1=stroke
    bool stroke = false;
    // DRAW_PATH: flattened contours (absolute canvas-space points). Filled
    // with the path's fill rule (CYCLE-E: WINDING default per AOSP, or
    // EVEN_ODD when the app set Path.FillType); stroke mode draws contour
    // outlines.
    std::vector<std::vector<std::pair<float, float>>> contours;
    // CYCLE-E: Path.FillType recorded at drawPath time.
    // 0 = WINDING (AOSP default), 1 = EVEN_ODD.
    int fill_type = 0;

    // ── S68 §12 additions ────────────────────────────────────────────────
    // DRAW_BITMAP: heap object id of the android.graphics.Bitmap; source
    // subset in source pixels (has_src=false → whole bitmap); destination
    // rect in op space (baked with the record-time affine); filterBitmap
    // selection (AOSP default false = nearest).
    uint32_t bitmap_id = 0;
    bool has_src = false, has_dst = false;
    float src_l = 0, src_t = 0, src_r = 0, src_b = 0;
    bool filter_bitmap = false;
    // DRAW_TEXT: paint text size (0 = unknown → legacy bitmap font path);
    // text scale from the record-time matrix (origin/advance transform).
    float text_size_px = 0;
    bool text_bold = false;
    // Record-time affine SNAPSHOT for ops replayed per-pixel (bitmap):
    // lets rotated/scaled destinations sample correctly.
    bool has_affine = false;
    Affine2D affine;
    // ── S68 §12: PER-OP CLIP SNAPSHOT (AOSP law) ─────────────────────────
    // The clip in effect AT RECORD TIME applies to this op (ops recorded
    // after clipRect() are clipped; ops after restore() are not). Reading
    // the canvas's final clip state at replay time is a semantic bug the
    // f08 R6 probe exposed (clip leak persisted because restore() had
    // already deactivated the clip when replay ran).
    bool has_clip = false;
    float clip_l = 0, clip_t = 0, clip_r = 0, clip_b = 0;
};

class CanvasShadow : public Shadow {
public:
    std::string name() const override { return "CanvasShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls == "Landroid/graphics/Canvas;" ||
               cls.find("graphics/Canvas;") != std::string::npos ||
               cls == "Landroid/graphics/Paint;" ||
               cls.find("graphics/Paint;") != std::string::npos ||
               // FIX-5: android.graphics.Path — real path recording so apps
               // that draw their own glyphs/shapes (simplestopwatch digit
               // fonts, clock hands) execute their REAL onDraw bytecode and
               // produce real pixels instead of a swallowed drawPath.
               cls == "Landroid/graphics/Path;" ||
               cls.find("graphics/Path;") != std::string::npos ||
               // UC009 H-072: Compose draws through RenderNode recording.
               cls == "Landroid/view/RenderNode;" ||
               cls.find("graphics/RecordingCanvas;") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    // Begin a fresh op capture for one onDraw dispatch.
    void begin_frame();
    // Replay captured ops into (left,top,w,h) view-space bounds.
    // Returns the number of ops replayed.
    size_t replay(class miniandroid::renderer::SoftwareCanvas& canvas,
                  class miniandroid::renderer::BitmapFont& font,
                  float left, float top, float w, float h);

    bool capturing() const { return capturing_; }
    // S68 §12: real canvas dimensions (engine framebuffer law — getWidth/
    // getHeight answer these; was hardcoded 1080x1920).
    void set_canvas_size(int w, int h) { canvas_w_ = w; canvas_h_ = h; }
    // Paint color lookup (0 default opaque black); shared by Canvas dispatch.
    uint32_t paint_color(uint32_t paint_id) const {
        auto it = paint_color_.find(paint_id);
        return it != paint_color_.end() ? it->second : 0xFF000000u;
    }
    const std::vector<DrawOp>& ops() const { return ops_; }

private:
    bool capturing_ = false;
    std::vector<DrawOp> ops_;
    // UC009 H-072: AOSP RenderNode recording model. Compose (1.7+) records
    // every LayoutNode's drawing into a RenderNode via a RecordingCanvas,
    // then composites with Canvas.drawRenderNode. We mirror the model:
    // beginRecording switches the op target to the node's list;
    // drawRenderNode replays a node's ops (offset by its position).
    std::map<uint32_t, std::vector<DrawOp>> render_nodes_;   // node id -> recorded ops
    std::map<uint32_t, float> node_pos_l_, node_pos_t_;      // node id -> position
    uint32_t recording_node_ = 0;                            // 0 = frame target
    // ── S68 §12: FULL canvas state = affine matrix + clip stack ──────────
    // AOSP Canvas law: save()/restore() snapshot BOTH the matrix and the
    // clip (Canvas.java: "the current matrix and clip are copied"). The
    // old model tracked only (tx,ty) pairs; scale/rotate/skew/clipRect
    // were accepted-not-reproduced NO-OPs (S67 pixel-proven 245-px clip
    // leak + unscaled geometry).
    Affine2D mat_;
    struct ClipRect { float l = 0, t = 0, r = 0, b = 0; bool active = false; };
    ClipRect clip_;                       // view/op space (baked like ops)
    struct SavedState { Affine2D mat; ClipRect clip; };
    std::vector<SavedState> save_stack_;

    std::vector<DrawOp>& target() {
        return recording_node_ ? render_nodes_[recording_node_] : ops_;
    }
    // ── S71 R-NEW-389 instrumentation (env-gated, render-neutral) ─────────
    // MINIANDROID_CANVAS_OP_TRACE=<path>: append one line per recorded
    // DrawOp — kind, geometry, resolved paint state (color/stroke/width/
    // text size/bold), clip, and the record-time matrix snapshot. FIRST
    // PIXEL DIVERGENCE evidence: diffing this trace between two builds of
    // different source (golden vs current) names the first op whose
    // arguments/state differ — no screenshot guessing. OFF by default; the
    // only cost when OFF is one null-pointer check per op.
    void push_op(DrawOp op);
    FILE* op_trace_ = nullptr;       // lazily opened on first traced op
    uint64_t op_trace_seq_ = 0;
    static constexpr uint64_t kOpTraceCap = 200000;   // bounded evidence cap
    std::map<uint32_t, uint32_t> paint_color_;    // paint obj -> ARGB
    std::map<uint32_t, float> paint_stroke_w_;    // paint obj -> width
    std::map<uint32_t, int> paint_style_;         // paint obj -> 0 fill / 1 stroke
    std::map<uint32_t, float> paint_text_size_;   // paint obj -> text size
    // S68 §12/§14: paint text styling consumed by the Canvas text path.
    std::map<uint32_t, bool> paint_fake_bold_;    // setFakeBoldText
    std::map<uint32_t, bool> paint_filter_bitmap_;// setFilterBitmap
    // S68 §12: canvas dimensions (real framebuffer — was hardcoded 1080x1920).
    int canvas_w_ = 1080, canvas_h_ = 1920;
    // FIX-5: android.graphics.Path recording (per heap object id).
    struct PathData {
        float cx = 0, cy = 0;                     // current point
        float sx = 0, sy = 0;                     // sub-path start
        bool open = false;
        // CYCLE-E: recorded Path.FillType. Android ordinals:
        // 0 WINDING, 1 EVEN_ODD, 2 INVERSE_WINDING, 3 INVERSE_EVEN_ODD.
        // Inverse variants fill the OUTSIDE; rasterization maps them to the
        // base rule and reports a diagnostic (rare in practice).
        int fill_type = 0;                        // AOSP default = WINDING
        std::vector<std::vector<std::pair<float, float>>> contours;
    };
    std::map<uint32_t, PathData> paths_;          // path obj -> geometry
    // CYCLE-E: honest diagnostics for accepted-but-ignored operations
    // (owner rule §34: no silent fallbacks). Warn once per op name.
    std::map<std::string, bool> noop_warned_;
    void warn_noop(const std::string& cls, const std::string& op);

    // S68 §12: stamp the CURRENT clip onto an op at record time.
    void stamp_clip(DrawOp& op) const {
        if (clip_.active) {
            op.has_clip = true;
            op.clip_l = clip_.l; op.clip_t = clip_.t;
            op.clip_r = clip_.r; op.clip_b = clip_.b;
        }
    }

    // CYCLE-E: resolve an enum-typed argument to its AOSP ordinal. Prefers
    // the synthesized framework enum object's "ordinal" heap field; falls
    // back to a plain int arg (legacy callers); `def` when neither applies.
    int enum_arg_ordinal(const CallContext& ctx, size_t i, int def) const {
        if (i >= ctx.args.size()) return def;
        const auto& a = ctx.args[i];
        if (a.kind == CallContext::Arg::Kind::OBJECT && heap_) {
            int32_t ord = 0;
            if (heap_->get_object_int_field(a.object_id, "ordinal", ord))
                return ord;
            return def;
        }
        return ctx.arg_as_int(i, def);
    }
    friend class PaintShadow;
};

} } // namespace miniandroid::framework
