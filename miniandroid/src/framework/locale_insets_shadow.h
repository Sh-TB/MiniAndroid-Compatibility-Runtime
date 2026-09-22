// locale_insets_shadow.h — S83-GFX-BASE §32: F-NEW-159 root-cause fix.
//
// F-NEW-159 = NULL-FRAMEWORK-RECEIVER NPE family (registered in the
// S82-GFX fanout probe, reproduced ×2 on MAND-002 + APP-001):
//   * `Landroid/os/LocaleList;.toLanguageTags` on a NULL receiver —
//     produced by Configuration.getLocales() resolving to null.
//   * `Landroid/view/WindowInsetsController;.setSystemBarsAppearance` on a
//     NULL receiver — produced by Window.getInsetsController() resolving to
//     null (androidx WindowInsetsControllerCompat wraps whatever the
//     platform returns; a null platform controller = NPE in app code).
//
// LAW (AOSP): these are REAL stateful framework objects, never null on a
// live Configuration/Window. The fix is a semantic shadow — a real object
// with real state — NOT `return null`, NOT `catch NPE`, NOT `ignore`.
//
// State model (single-threaded deterministic runtime):
//   LocaleList             languageTags string field (device default
//                          "en-US"), locale list materialized as child
//                          Ljava/util/Locale; objects on demand.
//   WindowInsetsController appearance/behavior/interruptors recorded as
//                          heap fields; show/hide set the visibility mask.
// ─────────────────────────────────────────────────────────────────────────
#pragma once

#include "shadow_registry.h"

#include <string>

namespace miniandroid { namespace framework {

class LocaleInsetsShadow : public Shadow {
public:
    std::string name() const override { return "LocaleInsetsShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("os/LocaleList;") != std::string::npos ||
               cls == "Ljava/util/Locale;" ||
               cls.find("view/WindowInsetsController") != std::string::npos;
    }

    void init(HeapAllocator* heap) override;
    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"toLanguageTags", "isEmpty", "size", "get", "indexOf",
                "getDefault", "getAdjustedDefault", "wrap", "setLocale",
                "toLanguageTag", "getLanguage", "getCountry", "toString",
                "setSystemBarsAppearance", "setSystemBarsBehavior", "show",
                "hide", "getSystemBarsAppearance", "setDecorFitsSystemWindows"};
    }

    // Device default language tags (AOSP locale default is en-US on our
    // software device profile — mirrors the density 2.625 / 1080x1920 law).
    static constexpr const char* kDefaultLanguageTags = "en-US";

private:
    uint32_t ensure_list(const std::string& tags);
    uint32_t ensure_locale(const std::string& tag);
    uint32_t ensure_controller();
};

} } // namespace miniandroid::framework
