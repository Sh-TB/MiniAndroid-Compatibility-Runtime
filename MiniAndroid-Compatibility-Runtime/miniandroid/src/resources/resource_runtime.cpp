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

    // 2. Style entry (complex/bag) — pick the DEFAULT config (no qualifiers)
    //    exactly like Resources in an unqualified environment.
    auto r = arsc_.resolve(mi.application_theme_resid);
    if (!r) return std::nullopt;
    const ArscEntry* style = r->best();
    if (!style || !style->is_complex) return std::nullopt;

    // 3. android:windowBackground item inside the bag (parent-theme default
    //    resolution is NOT needed here: apps that override windowBackground
    //    carry the item in their own style bag; apps that don't keep the
    //    platform default — out of scope for this gate).
    std::optional<ResValue> wb;
    for (size_t i = 0; i < style->complex_keys.size() && i < style->complex_items.size(); ++i) {
        if (style->complex_keys[i] == 0x01010054) { wb = style->complex_items[i]; break; }
    }
    if (!wb) return std::nullopt;

    // 4. Follow reference hops (@color/…) up to 5, then require a color.
    ResValue v = *wb;
    int hops = 0;
    while (v.is_reference() && hops < 5) {
        auto v2 = arsc_.resolve_value(v.ref_id);
        if (!v2) return std::nullopt;
        v = *v2;
        hops++;
    }
    switch (v.type) {
        case DataType::COLOR_ARGB8: return v.data;                       // #AARRGGBB
        case DataType::COLOR_RGB8:  return 0xFF000000u | v.data;         // #RRGGBB → opaque
        case DataType::COLOR_ARGB4: {
            uint32_t a = (v.data >> 12) & 0xF, rr = (v.data >> 8) & 0xF,
                     g = (v.data >> 4) & 0xF, b = v.data & 0xF;
            return (a * 0x11) << 24 | (rr * 0x11) << 16 | (g * 0x11) << 8 | (b * 0x11);
        }
        case DataType::COLOR_RGB4: {
            uint32_t rr = (v.data >> 8) & 0xF, g = (v.data >> 4) & 0xF, b = v.data & 0xF;
            return 0xFF000000u | (rr * 0x11) << 16 | (g * 0x11) << 8 | (b * 0x11);
        }
        default: return std::nullopt;
    }
}

} // namespace resources
} // namespace miniandroid
