// display_shadow.cpp — CONT-83 F-NEW-389 implementation (see the header
// for the AOSP law + the fixed-portrait device model).
#include "display_shadow.h"

#include <iostream>

namespace miniandroid { namespace framework {

void DisplayShadow::init(HeapAllocator* heap) {
    heap_ = heap;
}

bool DisplayShadow::fill_metrics(uint32_t metrics_id, int w, int h) {
    if (!heap_ || metrics_id == 0 || !heap_->has_object(metrics_id))
        return false;
    heap_->set_object_int_field(metrics_id, "widthPixels", w);
    heap_->set_object_int_field(metrics_id, "heightPixels", h);
    heap_->set_object_float_field(metrics_id, "density", 1.0f);
    heap_->set_object_int_field(metrics_id, "densityDpi", 160);
    heap_->set_object_float_field(metrics_id, "scaledDensity", 1.0f);
    heap_->set_object_float_field(metrics_id, "xdpi", 160.0f);
    heap_->set_object_float_field(metrics_id, "ydpi", 160.0f);
    return true;
}

CallResult DisplayShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;

    // ── DisplayManager statics/instances ────────────────────────────────
    if (ctx.class_name.find("hardware/display/DisplayManager") !=
        std::string::npos) {
        if (m == "getDisplay") {
            // AOSP: getDisplay(int displayId) → Display. One canonical
            // Display object per run (the DEFAULT_DISPLAY model).
            if (!heap_) return CallResult{};
            const uint32_t d = heap_->get_or_create("Landroid/view/Display;");
            return CallResult::handled_object(
                d, "Landroid/view/Display;");
        }
        if (m == "getDisplays" || m == "getDisplays") {
            if (!heap_) return CallResult{};
            const uint32_t d = heap_->get_or_create("Landroid/view/Display;");
            return CallResult::handled_object(
                d, "Landroid/view/Display;");
        }
        return CallResult{};
    }

    // ── Display instance methods ────────────────────────────────────────
    if (ctx.class_name.find("Landroid/view/Display;") != std::string::npos ||
        ctx.class_name.find("android/view/Display") != std::string::npos) {
        // The engine's fixed-portrait model: 1080x1920 (matches the run
        // config the frame pump and canvas laws already use).
        const int w = 1080, h = 1920;
        if (m == "getRealMetrics" || m == "getMetrics") {
            // AOSP: getRealMetrics(DisplayMetrics outMetrics) — fills the
            // CALLER's object and returns void. args[0] = the metrics.
            uint32_t mid = ctx.args.empty() ? 0 : ctx.args[0].object_id;
            if (fill_metrics(mid, w, h))
                return CallResult::handled_void();
            return CallResult{};
        }
        if (m == "getRotation")
            return CallResult::handled_int(0);   // Surface.ROTATION_0
        if (m == "getWidth") return CallResult::handled_int(w);
        if (m == "getHeight") return CallResult::handled_int(h);
        return CallResult{};
    }
    return CallResult{};
}

} } // namespace miniandroid::framework
