// surface_view_shadow.h — S86 §F-NEW-164: SurfaceView + SurfaceHolder model.
//
// LAW (AOSP android.view.SurfaceView / android.view.SurfaceHolder):
//   * A SurfaceView owns an OFF-SCREEN surface (a separate buffer the
//     compositor blits into the view hierarchy at the view's bounds).
//   * getHolder() returns the view's SurfaceHolder (ONE holder per view,
//     stable for the view's lifetime).
//   * SurfaceHolder.lockCanvas(null) → Canvas bound to the surface buffer
//     (null only while the surface is destroyed — AOSP never returns null
//     while created; MiniAndroid's surface is created at first lifecycle
//     dispatch, so a real canvas is the honest law).
//   * SurfaceHolder.unlockCanvasAndPost(c) → posts the buffer; the
//     compositor shows it on the next frame pass (CanvasShadow::replay_).
//   * addCallback(Callback) registers surfaceCreated/surfaceChanged/
//     surfaceDestroyed receivers — dispatched by the engine's render stage
//     (dispatch_surface_view_lifecycle), mirroring the GLSurfaceView law
//     (F-NEW-157 shadow family).
//   * SurfaceView IS-A View: View-family methods fall through to
//     ViewShadow (registration order: BEFORE ViewShadow).
//
// Ground truth (upstream source, read this wave):
//   github.com/dozingcat/dodge-android FieldView — "Extends SurfaceView for
//   maximum performance and runs in a separate thread"; drawField() =
//   lockCanvas → drawRect(black) + goal zones + bullets → unlockCanvasAndPost.
#ifndef MINIANDROID_FRAMEWORK_SURFACE_VIEW_SHADOW_H
#define MINIANDROID_FRAMEWORK_SURFACE_VIEW_SHADOW_H

#include "shadow_registry.h"

namespace miniandroid { namespace framework {

class SurfaceViewShadow : public Shadow {
public:
    std::string name() const override { return "SurfaceViewShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("view/SurfaceView;") != std::string::npos ||
               cls.find("view/SurfaceHolder") != std::string::npos;
    }

    void init(HeapAllocator* heap) override { heap_ = heap; }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"getHolder", "lockCanvas", "unlockCanvasAndPost",
                "addCallback", "removeCallback", "setFormat", "setType",
                "setFixedSize", "setKeepScreenOn"};
    }

private:
    // heap field names (GLSurfaceViewShadow field-law pattern):
    static constexpr const char* kHolder = "svHolder";      // view → holder
    static constexpr const char* kOwner = "svOwner";        // holder → view
    static constexpr const char* kCallback = "svCallback";  // holder → Callback
    static constexpr const char* kTarget = "svTarget";      // canvas → view
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_SURFACE_VIEW_SHADOW_H
