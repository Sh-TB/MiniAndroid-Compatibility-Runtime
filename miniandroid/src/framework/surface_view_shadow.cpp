// surface_view_shadow.cpp — S86 §F-NEW-164 implementation (see header law).
#include "surface_view_shadow.h"
#include "canvas_shadow.h"

#include <iostream>

namespace miniandroid { namespace framework {

CallResult SurfaceViewShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    if (!heap_) return CallResult::not_handled();

    // ── SurfaceView instance methods ─────────────────────────────────────
    if (cls.find("view/SurfaceView;") != std::string::npos) {
        const uint32_t self = ctx.receiver_id;
        if (m == "getHolder") {
            // AOSP: one holder per view, stable. Store on the view object
            // (svHolder) and back-link the owner (svOwner) so holder calls
            // resolve their SurfaceView without a shadow-side map.
            uint32_t holder = 0;
            auto hf = heap_->get_object_ref_field(self, kHolder, holder);
            if (!hf || holder == 0 || !heap_->has_object(holder)) {
                holder = heap_->allocate("Landroid/view/SurfaceHolder;");
                heap_->set_object_ref_field(self, kHolder, holder,
                                            "Landroid/view/SurfaceHolder;",
                                            "", false);
                heap_->set_object_int_field(holder, kOwner,
                                            static_cast<int32_t>(self));
            }
            return CallResult::handled_object(
                holder, "Landroid/view/SurfaceHolder;");
        }
        // setWillNotDraw / setZOrderOnTop / setZOrderMediaOverlay — surface
        // plumbing accepted as recorded (no pixel effect on the raster law).
        if (m == "setWillNotDraw" || m == "setZOrderOnTop" ||
            m == "setZOrderMediaOverlay" || m == "setSecure") {
            return CallResult::handled_void();
        }
        return CallResult::not_handled();  // View-family → ViewShadow
    }

    // ── SurfaceHolder instance methods ───────────────────────────────────
    if (cls.find("view/SurfaceHolder") != std::string::npos) {
        const uint32_t self = ctx.receiver_id;   // the holder object

        if (m == "lockCanvas") {
            // AOSP: returns a Canvas bound to the surface buffer. Owner
            // missing ⇒ surface never created — honest null (AOSP would
            // also hand out no buffer before surfaceCreated).
            int32_t owner_int = 0;
            heap_->get_object_int_field(self, kOwner, owner_int);
            if (owner_int == 0) return CallResult::handled_null();
            uint32_t view_id = static_cast<uint32_t>(owner_int);
            uint32_t canvas = heap_->allocate("Landroid/graphics/Canvas;");
            heap_->set_object_int_field(canvas, kTarget,
                                        static_cast<int32_t>(view_id));
            if (registry_) {
                if (auto* cs = registry_->find_as<CanvasShadow>())
                    cs->begin_surface_frame(view_id);
            }
            return CallResult::handled_object(
                canvas, "Landroid/graphics/Canvas;");
        }
        if (m == "unlockCanvasAndPost") {
            // AOSP: post the drawn buffer. The Canvas arg carries svTarget
            // (the owning view); end the surface capture → POST.
            uint32_t canvas_id = ctx.arg_as_object(0, 0);
            uint32_t target = 0;
            if (canvas_id != 0)
                heap_->get_object_int_field(canvas_id, kTarget,
                                            reinterpret_cast<int32_t&>(target));
            if (registry_) {
                if (auto* cs = registry_->find_as<CanvasShadow>()) {
                    bool posted = cs->end_surface_frame();
                    static int sv_log = 0;
                    if (sv_log < 24) {
                        ++sv_log;
                        std::cerr << "[F-NEW-164] unlockCanvasAndPost canvas="
                                  << canvas_id << " view=" << target
                                  << " posted=" << (posted ? "YES" : "NO")
                                  << std::endl;
                    }
                    return CallResult::handled_void();
                }
            }
            return CallResult::handled_void();
        }
        if (m == "addCallback") {
            uint32_t cb = ctx.arg_as_object(0, 0);
            if (cb != 0)
                heap_->set_object_ref_field(self, kCallback, cb, "", "",
                                            false);
            return CallResult::handled_void();
        }
        if (m == "removeCallback") {
            heap_->set_object_ref_field(self, kCallback, 0, "", "", false);
            return CallResult::handled_void();
        }
        if (m == "setFormat" || m == "setType" || m == "setFixedSize" ||
            m == "setKeepScreenOn") {
            return CallResult::handled_void();
        }
        if (m == "isCreating") return CallResult::handled_bool(false);
        if (m == "getSurface") {
            // Minimal Surface token object (bitmap-free; the Canvas path is
            // the draw law apps actually hit).
            uint32_t surf = heap_->get_or_create(
                "Landroid/view/Surface;");
            return CallResult::handled_object(
                surf, "Landroid/view/Surface;");
        }
        return CallResult::not_handled();
    }

    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
