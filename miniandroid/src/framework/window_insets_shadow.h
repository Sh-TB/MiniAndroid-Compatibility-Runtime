// window_insets_shadow.h — S113 ROOT-059: android.view.WindowInsets platform law.
//
// LAW (AOSP android.view.WindowInsets + androidx.core.view.WindowInsetsCompat):
//   * WindowInsets$Builder exists API 29+; new WindowInsets.Builder(src).build()
//     materializes a non-null WindowInsets snapshot. R8 API-model outlines
//     (HalfKt$$ExternalSyntheticApiModelOutline0.m) route androidx Impl30's
//     platform access through it.
//   * consumeDisplayCutout()/consumeStableInsets()/consumeSystemWindowInsets()
//     return a NON-null WindowInsets. androidx WindowInsetsCompat$Impl.<clinit>
//     builds its CONSUMED constant exactly through this chain —
//     Builder.build().consumeDisplayCutout().consumeStableInsets()
//     .consumeSystemWindowInsets() — and any null in the chain NPEs the class
//     init (mykanji ground truth: 21x EXC-UNWIND NullPointerException through
//     Impl28.consumeDisplayCutout; the null entered at WindowInsets$Builder
//     REC-MISS returning null). ROOT-059: the chain must never see null.
//   * No display cutout on this runtime: getDisplayCutout() → null (AOSP law
//     for cutout-free devices); system-window insets are 0.
#pragma once

#include "shadow_registry.h"

#include <string>
#include <vector>

namespace miniandroid { namespace framework {

class WindowInsetsShadow : public Shadow {
public:
    std::string name() const override { return "WindowInsetsShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls == "Landroid/view/WindowInsets;" ||
               cls.rfind("Landroid/view/WindowInsets$Builder", 0) == 0;
    }

    void init(HeapAllocator* heap) override;
    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"<init>", "build", "consumeDisplayCutout", "consumeStableInsets",
                "consumeSystemWindowInsets", "getDisplayCutout",
                "getSystemWindowInsetLeft", "getSystemWindowInsetTop",
                "getSystemWindowInsetRight", "getSystemWindowInsetBottom",
                "replaceSystemWindowInsets", "getInsets"};
    }

private:
    HeapAllocator* heap_ = nullptr;
    uint32_t materialize();
};

}} // namespace miniandroid::framework
