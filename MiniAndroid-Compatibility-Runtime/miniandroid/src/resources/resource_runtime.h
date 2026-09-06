/*
 * UNIFIED_007 — ResourceRuntime: process-wide ARSC + LayoutInflater access.
 * Loaded lazily from the APK being executed; reused by ActivityShadow
 * (setContentView), TextView.setText(resid), renderer (drawable extraction),
 * and touch dispatch (onClick handler resolution).
 */
#ifndef MINIANDROID_RESOURCE_RUNTIME_H
#define MINIANDROID_RESOURCE_RUNTIME_H

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <optional>

#include "arsc_parser.h"
#include "axml_parser.h"
#include "layout_inflater.h"
#include "../apk/apk_parser.h"

namespace miniandroid {
namespace resources {

class ResourceRuntime {
public:
    static ResourceRuntime& instance();

    // Ensure ARSC + APK cache loaded for this APK. Returns false on failure.
    bool ensure_loaded(const std::string& apk_path);

    ArscParser& arsc() { return arsc_; }
    apk::ApkParser& apk() { return apk_; }
    // TICTACTOE-GOLDEN campaign: always return a usable inflater. The old
    // accessor dereferenced a null unique_ptr for APKs with no
    // resources.arsc (fixtures, plain-asset apps) the moment any code path
    // needed the layout engine without ARSC — e.g. the generic
    // setContentView(View) measure pass for programmatic View trees.
    LayoutInflater& inflater() {
        if (!inflater_) {
            metrics_ = DeviceMetrics{};
            inflater_ = std::make_unique<LayoutInflater>(arsc_, apk_, apk_path_, metrics_);
            apply_custom_view_ctor_hook();
            apply_is_a();
        }
        return *inflater_;
    }

    // ── G11 FIX-G11-001 (AOSP LayoutInflater Factory law) ───────────
    // The custom-view constructor hook is a PROCESS-WIDE framework
    // setting (like AppCompatDelegateImpl installing Factory2), NOT a
    // property of one LayoutInflater instance: ensure_loaded() recreates
    // the inflater whenever the APK path changes, and AOSP's law is that
    // the phone process (re)applies the Factory to EVERY newly created
    // LayoutInflater (AppCompatDelegateImpl.installViewFactory →
    // LayoutInflater.setFactory2 on each new PhoneLayoutInflater).
    // ResourceRuntime owns the hook and propagates it to every inflater
    // it creates — the engine installs it once, order-independent.
    void set_custom_view_ctor_hook(LayoutInflater::CustomViewCtorHook fn) {
        custom_view_ctor_hook_ = std::move(fn);
        if (inflater_) inflater_->set_custom_view_ctor_hook(custom_view_ctor_hook_);
    }

    // G12 FIX-G12-002: same Factory law for the superclass classifier —
    // an is_a installed on one instance was silently wiped by the next
    // ensure_loaded (app containers classified as leaves on the window
    // path). Owned process-wide, re-applied on every (re)creation.
    void set_is_a(std::function<bool(const std::string&, const std::string&)> fn) {
        is_a_ = std::move(fn);
        if (inflater_) inflater_->set_is_a(is_a_);
    }

private:
    void apply_custom_view_ctor_hook() {
        if (inflater_ && custom_view_ctor_hook_)
            inflater_->set_custom_view_ctor_hook(custom_view_ctor_hook_);
    }
    void apply_is_a() {
        if (inflater_ && is_a_)
            inflater_->set_is_a(is_a_);
    }

public:
    const DeviceMetrics& metrics() const { return metrics_; }
    bool loaded() const { return loaded_; }
    const std::string& apk_path() const { return apk_path_; }

    // VISUAL-CAMPAIGN (EXT-01 gate G49) — theme window background.
    // AOSP law (PhoneWindow.generateLayout → DecorView): the window
    // background comes from the activity/application theme attribute
    // android:windowBackground (0x01010054) of the style referenced by
    // <application android:theme>. It paints BEHIND all content — for
    // HelloWorldSelfAware this is the black behind the white text.
    // Returns nullopt when the APK declares no resolvable theme item
    // (caller falls back to the plain default surface).
    std::optional<uint32_t> resolve_window_background_argb(const std::string& apk_path);

    // Evidence dump
    std::string stats_json() const;

private:
    ResourceRuntime() = default;
    ArscParser arsc_;
    apk::ApkParser apk_;
    std::unique_ptr<LayoutInflater> inflater_;
    DeviceMetrics metrics_;
    bool loaded_ = false;
    std::string apk_path_;
    std::string load_error_;
    // G11 FIX-G11-001: process-wide custom-view constructor hook (Factory
    // law — survives LayoutInflater recreation in ensure_loaded()).
    LayoutInflater::CustomViewCtorHook custom_view_ctor_hook_;
    // G12 FIX-G12-002: process-wide superclass classifier (same Factory law).
    std::function<bool(const std::string&, const std::string&)> is_a_;
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_RESOURCE_RUNTIME_H
