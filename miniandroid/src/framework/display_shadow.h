// display_shadow.h — CONT-83 F-NEW-389: DisplayManager/Display law.
//
// First divergence surfaced by the CONT-83 graphics trace on the REAL
// corpus app stack.tower3d (libGDX): AndroidGraphics.getDisplayMode NPE'd
// at Display.getRealMetrics because DisplayManager.getDisplay had no
// shadow (the singleton existed via R-339 but every method REC-MISSed).
// AOSP law implemented here (bounded, fixed-portrait device model):
//   DisplayManager.getDisplay(int)   → the canonical Display object
//   Display.getRealMetrics(DisplayMetrics) / getMetrics → fills the AOSP
//     DisplayMetrics field set on the caller's object (widthPixels/
//     heightPixels/density/densityDpi/scaledDensity/xdpi/ydpi)
//   Display.getRotation()            → Surface.ROTATION_0 (0)
//   Display.getWidth/getHeight       → the modeled screen dims
// Density law: the runtime models density=1.0 (mdpi; dp==px — see
// dalvik_engine density notes) → densityDpi/xdpi/ydpi=160.
#pragma once

#include "shadow_registry.h"

#include <string>

namespace miniandroid { namespace framework {

class DisplayShadow : public Shadow {
public:
    std::string name() const override { return "DisplayShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("hardware/display/DisplayManager") !=
                   std::string::npos ||
               cls.find("Landroid/view/Display;") != std::string::npos;
    }

    void init(HeapAllocator* heap) override;
    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"getDisplay", "getMetrics", "getRealMetrics",
                "getRotation", "getWidth", "getHeight", "getRectSize"};
    }

private:
    // Fill the AOSP DisplayMetrics field set on `metrics_id`; false when
    // the object is absent (honest REC-MISS — no fabricated object).
    bool fill_metrics(uint32_t metrics_id, int w, int h);
};

} } // namespace miniandroid::framework
