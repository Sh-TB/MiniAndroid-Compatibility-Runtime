/*
 * UNIFIED_007 — ResourceRuntime implementation.
 */
#include "resource_runtime.h"
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

} // namespace resources
} // namespace miniandroid
