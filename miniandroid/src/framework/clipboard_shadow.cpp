// GOLDEN-02 — Clipboard platform shadow implementation.
// See clipboard_shadow.h for the AOSP law mapping.
#include "clipboard_shadow.h"

#include <iostream>

namespace miniandroid { namespace framework {

CallResult ClipboardShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;

    // ── ClipData.newPlainText(CharSequence label, CharSequence text) ────
    // Static factory — allocates the ClipData object and records its real
    // (label, text) content keyed by heap object id.
    if (cls.find("ClipData;") != std::string::npos && m == "newPlainText") {
        uint32_t obj = heap_ ? heap_->allocate("Landroid/content/ClipData;") : 0;
        ClipEntry e;
        e.label = ctx.arg_as_string(0);
        e.text = ctx.arg_as_string(1);
        clips_[obj] = e;
        std::cerr << "[CLIPBOARD] ClipData.newPlainText obj=" << obj
                  << " label=\"" << e.label << "\" text=\"" << e.text << "\""
                  << std::endl;
        return CallResult::handled_object(obj, "Landroid/content/ClipData;");
    }

    // ── ClipboardManager.setPrimaryClip(ClipData clip) ───────────────────
    // The observable state mutation: the primary clip is replaced.
    if (cls.find("ClipboardManager;") != std::string::npos && m == "setPrimaryClip") {
        uint32_t clip_id = ctx.arg_as_object(0, 0);
        primary_clip_id_ = clip_id;
        if (const ClipEntry* e = clip_by_id(clip_id)) {
            primary_clip_ = *e;
            std::cerr << "[CLIPBOARD] setPrimaryClip clip=" << clip_id
                      << " label=\"" << e->label << "\" text=\"" << e->text
                      << "\" (clipboard state mutated)" << std::endl;
        } else {
            primary_clip_ = ClipEntry{};
            std::cerr << "[CLIPBOARD] setPrimaryClip clip=" << clip_id
                      << " (content unknown — clip object not from newPlainText)"
                      << std::endl;
        }
        return CallResult::handled_void();
    }

    // ── ClipboardManager.getPrimaryClip() ────────────────────────────────
    if (cls.find("ClipboardManager;") != std::string::npos && m == "getPrimaryClip") {
        if (primary_clip_id_ != 0) {
            return CallResult::handled_object(primary_clip_id_,
                                              "Landroid/content/ClipData;");
        }
        return CallResult::handled_null();  // AOSP: null when clipboard empty
    }

    // ── ClipboardManager.getText() / getTextPrimary() ────────────────────
    // Deprecated text accessor — returns the primary clip's Item text.
    if (cls.find("ClipboardManager;") != std::string::npos &&
        (m == "getText" || m == "getTextPrimary")) {
        return CallResult::handled_string(primary_clip_.text);
    }

    // ── Legacy android.text.ClipboardManager.setText(CharSequence) ───────
    // Pre-HONEYCOMB API — the deprecated same-service mutator.
    if (cls.find("Landroid/text/ClipboardManager;") != std::string::npos &&
        m == "setText") {
        primary_clip_ = ClipEntry{"", ctx.arg_as_string(0)};
        primary_clip_id_ = 0;  // legacy path has no ClipData object
        std::cerr << "[CLIPBOARD] legacy setText text=\"" << primary_clip_.text
                  << "\" (clipboard state mutated)" << std::endl;
        return CallResult::handled_void();
    }

    // ── ClipboardManager.hasPrimaryClip() ────────────────────────────────
    if (cls.find("ClipboardManager;") != std::string::npos && m == "hasPrimaryClip") {
        return CallResult::handled_bool(primary_clip_id_ != 0 ||
                                        !primary_clip_.text.empty());
    }

    return CallResult::not_handled();
}

}} // namespace miniandroid::framework
