/*
 * UNIFIED_007 — ResourceRuntime implementation.
 */
#include "resource_runtime.h"
#include "framework_theme_attrs.h"
#include "../apk/manifest_reader.h"
#include <fstream>
#include <iostream>

namespace miniandroid {
namespace resources {

ResourceRuntime& ResourceRuntime::instance() {
    static ResourceRuntime rt;
    return rt;
}

bool ResourceRuntime::ensure_loaded(const std::string& apk_path) {
    if (loaded_ && apk_path_ == apk_path) return true;
    loaded_ = false;
    apk_path_ = apk_path;

    // read arsc through the APK parser (caches ZIP data for later extraction)
    auto info = apk_.parse(apk_path);
    if (!info.is_valid) {
        load_error_ = "apk parse failed: " + apk_path;
        return false;
    }
    std::vector<uint8_t> arsc_data = apk_.extract_entry_cached("resources.arsc");
    if (arsc_data.empty()) {
        load_error_ = "no resources.arsc in " + apk_path;
        return false;
    }
    if (!arsc_.parse(arsc_data)) {
        load_error_ = "arsc parse failed: " + arsc_.last_error();
        return false;
    }
    metrics_ = DeviceMetrics{};  // default 1080x1920 @420dpi
    inflater_ = std::make_unique<LayoutInflater>(arsc_, apk_, apk_path_, metrics_);
    // G11 FIX-G11-001 (AOSP Factory law): a freshly created LayoutInflater
    // starts factory-less — re-apply the process-wide custom-view ctor hook
    // (AppCompatDelegateImpl.installViewFactory re-applies Factory2 on every
    // new PhoneLayoutInflater).
    apply_custom_view_ctor_hook();
    // MASTER CAMPAIGN FIX (F10): same Factory law for the real-DEX
    // onMeasure hook.
    apply_custom_view_measure_hook();
    // M3 FIX-M3-001 (§7 cross-pass geometry law): re-apply the DEX
    // superclass classifier too. apply_is_a() existed but was never wired
    // into ensure_loaded — the recreated inflater silently fell back to
    // substring classification, so the AUTHORITATIVE window measure ran
    // with a different ancestry law than the render pass
    // (headingcalculator: CalculatorDisplay extends LinearLayout measured
    // 1080x1920 via View-default in the window pass vs 1080x158 via the
    // inherited container law in the render pass — the cross-pass
    // oscillation root cause). One classification law for EVERY pass.
    apply_is_a();
    loaded_ = true;
    std::cerr << "[U007-RES] ResourceRuntime loaded: " << apk_path
              << " named_ids=" << arsc_.stats().named_ids
              << " types=" << arsc_.stats().entries_by_type.size() << std::endl;
    return true;
}

std::string ResourceRuntime::stats_json() const {
    if (!loaded_) return "{\"loaded\":false,\"error\":\"" + load_error_ + "\"}";
    return arsc_.to_json(400);
}

// ─────────────────────────────────────────────────────────────────────────────
// VISUAL-CAMPAIGN (EXT-01 gate G49): theme → windowBackground → ARGB.
//
// AOSP chain (frameworks/base):
//   PhoneWindow.generateLayout()
//     → a.getWindowBackground from theme attribute android:windowBackground
//     → DecorView paints it behind all content.
// Manifest ground truth (aapt2 dump xmltree, EXT-01 fixture):
//   <application android:theme(0x01010000)=@0x7f060000>
//   style/AppTheme: bag { 0x01010054 (@android:windowBackground) = @color/colorPrimary }
//   @color/colorPrimary = #000000
// Attribute ids 0x01010000 (theme) / 0x01010054 (windowBackground) verified
// from the aapt2 dump above — NOT hardcoded from memory.
// ─────────────────────────────────────────────────────────────────────────────
std::optional<uint32_t> ResourceRuntime::resolve_window_background_argb(
        const std::string& apk_path) {
    if (!ensure_loaded(apk_path)) return std::nullopt;

    // 1. Application-level theme from the binary manifest.
    std::vector<uint8_t> mf = apk_.extract_entry_cached("AndroidManifest.xml");
    if (mf.empty()) return std::nullopt;
    apk::ManifestReader mr;
    apk::ManifestInfo mi = mr.parse(mf);
    if (mi.application_theme_resid == 0) return std::nullopt;

    // 2. GOLDEN-03 §8: attribute-KEY bag query through the canonical
    //    resolver — ResTable_map key 0x01010054 (android:windowBackground)
    //    with ResTable_map_entry parent-chain inheritance (cycle-safe,
    //    hop-bounded). Replaces the hand-rolled positional scan.
    auto wb = arsc_.bag_value(mi.application_theme_resid, 0x01010054,
                              device_config());
    if (!wb) return std::nullopt;

    // 3. GOLDEN-03 §7: follow reference hops through the canonical bounded/
    //    cycle-safe path, then decode the color via the ONE color law.
    ResValue v = *wb;
    if (v.is_reference()) {
        ResolutionResult r = arsc_.resolve_full(v.ref_id, device_config());
        if (!r.ok) return std::nullopt;
        v = *r.value();
    }
    return color_data_to_argb((uint8_t)v.type, v.data);
}

// F-093 (R-NEW-326, S25): theme attribute resolution — see resource_runtime.h.
std::optional<ResValue> ResourceRuntime::resolve_theme_attr_value(
        const std::string& apk_path, uint32_t attr_key) {
    static const bool f93_diag = std::getenv("MINIANDROID_F093_DIAG") != nullptr;
    if (!ensure_loaded(apk_path)) return std::nullopt;

    // 1. Application-level theme from the binary manifest.
    std::vector<uint8_t> mf = apk_.extract_entry_cached("AndroidManifest.xml");
    if (mf.empty()) return std::nullopt;
    apk::ManifestReader mr;
    apk::ManifestInfo mi = mr.parse(mf);
    if (mi.application_theme_resid == 0) {
        // F-094 (R-NEW-327): plain-text manifests carry android:theme as
        // a reference string ("@style/AppTheme.NoActionBar") — resolve the
        // style name to a resid through the canonical ARSC find_id.
        if (!mi.application_theme_ref.empty()) {
            std::string ref = mi.application_theme_ref;
            if (ref.rfind("@", 0) == 0) ref.erase(0, 1);
            // form: "<type>/<name>" (aapt2 also accepts "android:style/…")
            size_t slash = ref.find('/');
            std::string type = "style", name = ref;
            if (slash != std::string::npos) {
                type = ref.substr(0, slash);
                name = ref.substr(slash + 1);
            }
            if (type.rfind("android:", 0) == 0) type.erase(0, 8);
            if (auto id = arsc_.find_id(mi.package_name, type, name)) {
                mi.application_theme_resid = *id;
                if (f93_diag)
                    std::cerr << "[F093-DIAG] theme_ref=" 
                              << mi.application_theme_ref << " → resid 0x"
                              << std::hex << *id << std::dec << std::endl;
            }
        }
        if (mi.application_theme_resid == 0) {
            if (f93_diag)
                std::cerr << "[F093-DIAG] no application_theme_resid in manifest"
                          << std::endl;
            return std::nullopt;
        }
    }
    if (f93_diag)
        std::cerr << "[F093-DIAG] theme_resid=0x" << std::hex
                  << mi.application_theme_resid << std::dec << " attr=0x"
                  << std::hex << attr_key << std::dec << std::endl;

    // 2. Attribute-KEY bag query through the canonical resolver —
    //    ResTable_map key with parent-chain inheritance (cycle-safe).
    auto v = arsc_.bag_value(mi.application_theme_resid, attr_key,
                             device_config());
    if (!v) return std::nullopt;

    // 3. Dereference one reference hop (style item referencing a color /
    //    bool resource) through the canonical bounded path.
    ResValue out = *v;
    if (out.is_reference()) {
        ResolutionResult r = arsc_.resolve_full(out.ref_id, device_config());
        if (!r.ok) return out;   // raw reference still meaningful to caller
        out = *r.value();
    }
    return out;
}

// ─────────────────────────────────────────────────────────────────────────
// S68 W2 (A1/A10): ?attr resolution service (see resource_runtime.h law).
// ─────────────────────────────────────────────────────────────────────────
ResourceRuntime::LaunchTheme ResourceRuntime::resolve_launch_theme(
        const std::string& apk_path) {
    LaunchTheme out;
    if (!ensure_loaded(apk_path)) return out;

    uint32_t theme_resid = 0;
    std::string theme_ref;
    std::vector<uint8_t> mf = apk_.extract_entry_cached("AndroidManifest.xml");
    if (mf.empty()) return out;
    apk::ManifestReader mr;
    apk::ManifestInfo mi = mr.parse(mf);
    // AOSP ActivityInfo.theme law: the ACTIVITY theme overrides the
    // application theme for the launch window.
    if (mi.activity_theme_resid != 0) theme_resid = mi.activity_theme_resid;
    else if (mi.application_theme_resid != 0) theme_resid = mi.application_theme_resid;
    else {
        // F-094 law: plain-text manifests carry android:theme as a
        // reference string — resolve through the canonical ARSC find_id.
        theme_ref = !mi.activity_theme_ref.empty() ? mi.activity_theme_ref
                                                   : mi.application_theme_ref;
        std::string ref = theme_ref;
        if (ref.rfind("@", 0) == 0) ref.erase(0, 1);
        std::string type = "style", name = ref;
        size_t slash = ref.find('/');
        if (slash != std::string::npos) {
            type = ref.substr(0, slash);
            name = ref.substr(slash + 1);
        }
        if (type.rfind("android:", 0) == 0) type.erase(0, 8);
        if (auto id = arsc_.find_id(mi.package_name, type, name))
            theme_resid = *id;
    }
    if (theme_resid == 0) return out;
    out.resid = theme_resid;

    // Flavor law: walk the theme style NAME + parent chain; the framework's
    // *.Light convention decides dark vs light (generic, never app-specific).
    // Framework style ids (0x0103xxxx) do not resolve through the app ARSC
    // (aapt2 does not embed framework-res) — the walk consults the AOSP
    // public.xml style-id law for the framework theme roots.
    static const struct { uint32_t id; bool light; } FRAMEWORK_THEMES[] = {
        {0x01030224u, false},  // Theme.Material            (AOSP public.xml)
        {0x01030237u, true},   // Theme.Material.Light
        {0x01030128u, false},  // Theme.DeviceDefault
        {0x0103012bu, true},   // Theme.DeviceDefault.Light
        {0x0103006bu, false},  // Theme.Holo
        {0x0103006eu, true},   // Theme.Holo.Light
    };
    uint32_t cur = theme_resid;
    for (int hop = 0; hop < 8 && cur != 0; hop++) {
        bool resolved_framework = false;
        for (const auto& ft : FRAMEWORK_THEMES) {
            if (ft.id == cur) { out.flavor = ft.light ? 1 : 0; resolved_framework = true; break; }
        }
        if (resolved_framework) break;
        auto e = arsc_.resolve(cur);
        if (!e) break;
        if (e->name.find("Light") != std::string::npos) { out.flavor = 1; break; }
        const ArscEntry* best = e->best();
        cur = best ? best->bag_parent : 0;
    }
    out.valid = true;
    return out;
}

std::optional<ResValue> ResourceRuntime::resolve_theme_attr_typed(
        const std::string& apk_path, uint32_t attr_key, int flavor_hint) {
    // 1. Theme chain (activity theme > application theme).
    LaunchTheme lt = resolve_launch_theme(apk_path);
    if (lt.valid) {
        auto v = arsc_.bag_value(lt.resid, attr_key, device_config());
        if (v) {
            ResValue out = *v;
            if (out.is_reference()) {
                ResolutionResult r = arsc_.resolve_full(out.ref_id, device_config());
                if (r.ok) out = *r.value();
            }
            return out;
        }
    }
    // 2. Framework theme defaults (AOSP law; generated table).
    if ((attr_key >> 24) == 0x01) {
        const int flavor = flavor_hint >= 0 ? flavor_hint : lt.flavor;
        for (size_t i = 0; i < FRAMEWORK_THEME_ATTR_COUNT; i++) {
            const auto& fa = FRAMEWORK_THEME_ATTRS[i];
            if (fa.id != attr_key) continue;
            ResValue out;
            const uint32_t raw = flavor == 1 ? fa.light : fa.dark;
            // disabledAlpha is an AOSP FRACTION (TypedValue FRACTION_UNIT:
            // data = value * (1<<15)); booleans carry INT_BOOLEAN; the rest
            // are colors/ints (INT_HEX consumers accept is_int()).
            if (attr_key == 0x01010033 /*disabledAlpha*/) {
                out.type = DataType::FRACTION;
                out.data = (int32_t)raw;
            } else if (attr_key == 0x0101020d /*windowFullscreen*/) {
                out.type = DataType::INT_BOOLEAN;
                out.data = (int32_t)raw;
            } else {
                out.type = DataType::INT_HEX;
                out.data = (int32_t)raw;
            }
            return out;
        }
    }
    return std::nullopt;
}

} // namespace resources
} // namespace miniandroid
