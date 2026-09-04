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
#include <map>
#include <string>
#include <vector>

namespace miniandroid { namespace framework {

class CanvasShadow;
class PaintShadow;

// One recorded draw primitive (coordinates in VIEW space, density=1).
struct DrawOp {
    enum class Kind {
        DRAW_COLOR, DRAW_RECT, DRAW_ROUNDRECT, DRAW_CIRCLE, DRAW_LINE, DRAW_TEXT, DRAW_PAINT
    };
    Kind kind = Kind::DRAW_COLOR;
    float x = 0, y = 0, w = 0, h = 0;   // rect: x,y,w,h ; line: x1,y1,x2,y2 in x,y,w,h
    float r = 0;                        // circle radius / roundrect corner radius
    uint32_t color = 0xFF000000;
    float stroke_w = 1.0f;
    std::string text;                   // DRAW_TEXT
    // Paint style: 0=fill, 1=stroke
    bool stroke = false;
};

class CanvasShadow : public Shadow {
public:
    std::string name() const override { return "CanvasShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls == "Landroid/graphics/Canvas;" ||
               cls.find("graphics/Canvas;") != std::string::npos ||
               cls == "Landroid/graphics/Paint;" ||
               cls.find("graphics/Paint;") != std::string::npos ||
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
    float tx_ = 0, ty_ = 0;                                  // canvas translate state
    std::vector<std::pair<float,float>> save_stack_;

    std::vector<DrawOp>& target() {
        return recording_node_ ? render_nodes_[recording_node_] : ops_;
    }
    std::map<uint32_t, uint32_t> paint_color_;    // paint obj -> ARGB
    std::map<uint32_t, float> paint_stroke_w_;    // paint obj -> width
    std::map<uint32_t, int> paint_style_;         // paint obj -> 0 fill / 1 stroke
    std::map<uint32_t, float> paint_text_size_;   // paint obj -> text size
    friend class PaintShadow;
};

} } // namespace miniandroid::framework
