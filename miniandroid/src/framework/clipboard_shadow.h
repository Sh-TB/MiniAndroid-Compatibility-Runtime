// GOLDEN-02 — Clipboard platform shadow (generic Android behavior).
//
// AOSP laws transferred (frameworks/base/core/java/android/content):
//   * ClipData.newPlainText(CharSequence label, CharSequence text):
//     creates a ClipData with one ClipDescription (MIME_TYPE_TEXT_PLAIN)
//     and one Item whose text is the given CharSequence. Returns the new
//     ClipData object — never null for non-null inputs.
//   * ClipboardManager.setPrimaryClip(ClipData clip): replaces the primary
//     clip on the (per-context) clipboard service. The clip is retained —
//     the state mutation the app's callback performs and that later calls
//     (getPrimaryClip/getText) observe.
//
// The shadow stores REAL (label, text) string content so the runtime trace
// and any later getPrimaryClip/getText observe the mutated clipboard state.
// No fixture-specific code: these are platform APIs any APK may call.
//
#ifndef MINIANDROID_FRAMEWORK_CLIPBOARD_SHADOW_H
#define MINIANDROID_FRAMEWORK_CLIPBOARD_SHADOW_H

#include "shadow_registry.h"

#include <map>
#include <string>

namespace miniandroid { namespace framework {

class ClipboardShadow : public Shadow {
public:
    std::string name() const override { return "ClipboardShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("Landroid/content/ClipData;") != std::string::npos ||
               cls.find("Landroid/content/ClipDescription;") != std::string::npos ||
               cls.find("Landroid/content/ClipboardManager;") != std::string::npos ||
               cls.find("Landroid/text/ClipboardManager;") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    // ── accessors for evidence / diagnostics ────────────────────────────
    struct ClipEntry {
        std::string label;
        std::string text;
    };
    // The current primary clip (id + content), 0 id = clipboard empty.
    uint32_t primary_clip_id() const { return primary_clip_id_; }
    const ClipEntry* clip_by_id(uint32_t obj_id) const {
        auto it = clips_.find(obj_id);
        return it == clips_.end() ? nullptr : &it->second;
    }

private:
    std::map<uint32_t, ClipEntry> clips_;  // heap obj id → clip content
    uint32_t primary_clip_id_ = 0;
    ClipEntry primary_clip_;
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_CLIPBOARD_SHADOW_H
