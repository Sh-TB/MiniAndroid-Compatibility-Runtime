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
#include "theme_engine.h"
#include "../apk/apk_parser.h"
#include <sys/utsname.h>
#include <unistd.h>
#include <climits>

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

    // MASTER CAMPAIGN FIX (F10): same Factory law for the real-DEX
    // onMeasure hook.
    void set_custom_view_measure_hook(LayoutInflater::CustomViewMeasureHook fn) {
        custom_view_measure_hook_ = std::move(fn);
        if (inflater_) inflater_->set_custom_view_measure_hook(custom_view_measure_hook_);
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
    void apply_custom_view_measure_hook() {
        if (inflater_ && custom_view_measure_hook_)
            inflater_->set_custom_view_measure_hook(custom_view_measure_hook_);
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
    // S125 FRAMEWORK-RES FILE LAW: package-0x01 references whose entry is a
    // res/ FILE (theme windowBackground selectors — files the arsc-only
    // framework package does not carry) resolve from the committed
    // framework_res/res/ tree (REAL AOSP framework-res.apk files,
    // byte-verified; reuse-first SS31). A color-bearing selector resolves
    // through the StateListDrawable first-match/default law and its
    // @color reference through the framework table. No invented colors,
    // no package-name checks (the 0x01 test IS the AOSP package router).
    std::optional<uint32_t> resolve_framework_file_color(uint32_t resid);

    // S127 (R-NEW-423 follow-up, AOSP AssetManager2 ResolveAttributeReference
    // law): a REFERENCE whose target is a COLOR resolves package-routed —
    // package-0x01 ids through the framework table, app ids through the app
    // table — with resolve_full's bounded reference-chain walk terminating on
    // the first non-reference value (e.g. Theme.Material.Light
    // windowBackground = @color/background_material_light
    // = @color/material_grey_50 = #fffafafa). A terminal STRING "res/…"
    // (file-backed drawable/color) resolves through the committed framework
    // res/ tree. Returns the final ARGB, or nullopt (honest miss).
    std::optional<uint32_t> resolve_color_reference_argb(uint32_t resid);

    // F-093 (R-NEW-326, S25): theme attribute resolution through the
    // APPLICATION theme's style parent chain (ArscParser::bag_value —
    // ResTable_map key query with cycle-safe parent hops). Upstream law:
    // ContextThemeWrapper.obtainStyledAttributes(styleable[]) resolves
    // every attr id against the activity theme (attribute > style bag >
    // parent chain). Used by the AppCompat theme gate
    // (AppCompatDelegateImpl.createSubDecor → TypedArray.getBoolean(
    // windowActionBar)) — without it every AppCompatActivity app throws
    // ISE "You need to use a Theme.AppCompat theme (or descendant)".
    std::optional<ResValue> resolve_theme_attr_value(const std::string& apk_path,
                                                     uint32_t attr_key);

    // ── S68 W2 (A1/A10): ?attr resolution service ────────────────────────
    // AOSP law: ?attr/name (TypedValue TYPE_ATTRIBUTE) resolves through the
    // THEME of the context — the LAUNCH activity's theme when set, else the
    // application theme. When the theme chain lacks the attr and the id is
    // a FRAMEWORK attr (0x01xxxxxx), the AOSP framework theme default
    // applies (framework_theme_attrs.h, generated from AOSP law files).
    // Flavor (dark=Theme.Material vs light=Theme.Material.Light) follows
    // the framework's *.Light naming convention on the parent chain.
    struct LaunchTheme {
        uint32_t resid = 0;      // resolved theme style id (0 = none)
        int flavor = 0;          // 0 = dark (Theme.Material), 1 = light
        bool valid = false;
    };
    LaunchTheme resolve_launch_theme(const std::string& apk_path);
    // flavor_hint: 0 dark / 1 light; -1 = detect from the theme chain.
    std::optional<ResValue> resolve_theme_attr_typed(const std::string& apk_path,
                                                     uint32_t attr_key,
                                                     int flavor_hint = -1);
    // S124 THEME-BASE: the AOSP-law Theme object for the launch theme
    // (activity > application), built ONCE per APK with Theme::apply_style
    // overlay semantics (AssetManager2.cpp Theme::ApplyStyle law). The
    // resolution order for every theme attr becomes: android:theme subtree
    // overlays (ThemeEngine stack) → base theme → framework default table.
    const Theme& base_theme();
    bool base_theme_valid() const { return base_theme_valid_; }
    // S124: the View-ctor defStyleAttr law — resolve a widget's default-style
    // ATTR (e.g. buttonStyle 0x01010048) through the theme chain (overlays →
    // base) to the STYLE RESID it names, WITHOUT dereferencing the style
    // entry (a style is a bag, not a value — AOSP ApplyStyle loads the bag
    // from the raw resid). Returns 0 when the chain carries none.
    uint32_t resolve_def_style_resid(const std::string& apk_path,
                                     uint32_t def_style_attr);
    // S124 FW-PACKAGE: load the ORIGINAL framework resource table
    // (framework-res resources.arsc, package 0x01) once per process. This is
    // the base every Android app's themes/templates resolve against (AOSP
    // AssetManager2 multi-package law). Returns false when the table file is
    // absent — the engine then degrades to the generated attr-default table.
    bool ensure_framework_resources();
    ArscRouter arsc_router() {
        ensure_framework_resources();
        ArscRouter r;
        r.app = &arsc_;
        r.fw = fw_arsc_loaded_ ? &fw_arsc_ : nullptr;
        return r;
    }

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
    // MASTER CAMPAIGN FIX (F10): process-wide real-DEX onMeasure hook
    // (same Factory law).
    LayoutInflater::CustomViewMeasureHook custom_view_measure_hook_;
    // G12 FIX-G12-002: process-wide superclass classifier (same Factory law).
    std::function<bool(const std::string&, const std::string&)> is_a_;
    // S124 THEME-BASE: cached AOSP-law Theme for the loaded APK.
    Theme base_theme_;
    bool base_theme_valid_ = false;
    bool base_theme_built_ = false;
    // S124 FW-PACKAGE: the ORIGINAL framework resource table (package 0x01).
    ArscParser fw_arsc_;
    bool fw_arsc_loaded_ = false;
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_RESOURCE_RUNTIME_H
