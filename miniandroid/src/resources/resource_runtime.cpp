/*
 * UNIFIED_007 — ResourceRuntime implementation.
 */
#include "resource_runtime.h"
#include "framework_theme_attrs.h"
#include "framework/state_list.h"
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
    // S124 THEME-BASE: the cached AOSP-law Theme is invalid for a new APK,
    // and unbalanced inflate scopes must not leak overlays across APKs.
    base_theme_built_ = false;
    base_theme_valid_ = false;
    base_theme_ = Theme{};
    ThemeEngine::instance().clear_overlays();

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
// ── S125 FRAMEWORK-RES FILE LAW ─────────────────────────────────────────────
// AOSP law: framework-res.apk carries res/drawable + res/color FILES (theme
// windowBackground selectors, text color state lists). The committed
// framework package is table-only, so a package-0x01 reference to such a
// file previously resolved to an honest miss and the window fell back to a
// non-themed surface. This law resolves those references from the committed
// framework_res/res/ tree — the REAL files, byte-verified from the same
// framework-res.apk the table came from (reuse-first: zero invented
// constants). Selector resolution follows the StateListDrawable
// first-match law (first item whose state spec matches the default view
// state) and the item's @color reference derefs through the framework
// table (AssetManager2 ResolveAttributeReference).
std::optional<uint32_t> ResourceRuntime::resolve_framework_file_color(uint32_t resid) {
    if ((resid >> 24) != 0x01) return std::nullopt;
    ArscRouter rt = arsc_router();
    if (!rt.fw) return std::nullopt;
    auto r = rt.fw->resolve_full(resid, device_config());
    if (!r.ok || r.entry_name.empty()) return std::nullopt;
    const std::string& name = r.entry_name;

    // Same search law as ensure_framework_resources (exe-relative + cwd).
    std::vector<std::string> roots;
    if (const char* env = std::getenv("MINIANDROID_FRAMEWORK_RES_DIR"))
        roots.push_back(env);
    char exe_buf[PATH_MAX] = {0};
    ssize_t n = readlink("/proc/self/exe", exe_buf, sizeof(exe_buf) - 1);
    if (n > 0) {
        std::string exe_dir(exe_buf, (size_t)n);
        auto slash = exe_dir.rfind('/');
        if (slash != std::string::npos) exe_dir.resize(slash);
        roots.push_back(exe_dir + "/../framework_res");
        roots.push_back(exe_dir + "/framework_res");
    }
    roots.push_back("framework_res");
    roots.push_back("miniandroid/framework_res");

    static const char* kDirs[] = {"res/drawable/", "res/color/"};
    for (const auto& root : roots) {
        for (const char* dir : kDirs) {
            std::string path = root + "/" + dir + name + ".xml";
            std::ifstream f(path, std::ios::binary);
            if (!f) continue;
            std::vector<uint8_t> axml((std::istreambuf_iterator<char>(f)),
                                      std::istreambuf_iterator<char>());
            std::vector<framework::ViewShadow::ViewNode::BgStateItem> items;
            if (!framework::parse_state_list(axml, &items)) return std::nullopt;
            // StateListDrawable first-match law with the DEFAULT view state
            // (not pressed / enabled / unselected / unchecked).
            for (const auto& it : items) {
                if (it.state_pressed > 0 || it.state_selected > 0 ||
                    it.state_checked > 0)
                    continue;   // requires a non-default state — not first match
                if (it.has_color && it.color != 0) return it.color;
                if (!it.drawable_path.empty() &&
                    it.drawable_path.rfind("@color/", 0) == 0) {
                    auto id = rt.fw->find_id("", "color",
                                             it.drawable_path.substr(7));
                    if (!id) return std::nullopt;
                    auto v = rt.fw->resolve_value(*id);
                    if (v && (v->is_color() || v->is_int()))
                        return (uint32_t)v->data;
                    return std::nullopt;
                }
            }
            return std::nullopt;
        }
    }
    return std::nullopt;
}

std::optional<uint32_t> ResourceRuntime::resolve_window_background_argb(
        const std::string& apk_path) {
    if (!ensure_loaded(apk_path)) return std::nullopt;

    // 1. Theme from the binary manifest — AOSP law (PhoneWindow.generateLayout /
    //    ActivityInfo.theme): the LAUNCHER activity's android:theme overrides
    //    the application-level theme for the launch window. S68 W2 already
    //    captures the launcher theme (mi.activity_theme_resid); it was never
    //    consulted here, so apps declaring their theme per-activity (gmdice)
    //    fell through to the no-theme fallback.
    std::vector<uint8_t> mf = apk_.extract_entry_cached("AndroidManifest.xml");
    if (mf.empty()) return std::nullopt;
    apk::ManifestReader mr;
    apk::ManifestInfo mi = mr.parse(mf);
    uint32_t theme_resid = mi.activity_theme_resid != 0
                               ? mi.activity_theme_resid
                               : mi.application_theme_resid;
    if (theme_resid == 0) return std::nullopt;

    // 2. GOLDEN-03 §8: attribute-KEY bag query through the canonical
    //    resolver — ResTable_map key 0x01010054 (android:windowBackground)
    //    with ResTable_map_entry parent-chain inheritance (cycle-safe,
    //    hop-bounded). Replaces the hand-rolled positional scan.
    //    S95: a FRAMEWORK style root (package 0x01, e.g. Theme.Material.Light
    //    = 0x01030237) never appears in the app ARSC — skip the bag query
    //    for it (a false bag hit with an unresolvable ref would nullopt the
    //    whole chain) and let the framework table answer below.
    std::optional<ResValue> wb;
    if ((theme_resid >> 24) != 0x01) {
        wb = arsc_.bag_value(theme_resid, 0x01010054, device_config());
    }
    static const bool s95_dbg = std::getenv("MINIANDROID_S95_DBG") != nullptr;
    if (s95_dbg) std::cerr << "[S95-THEME] resid=0x" << std::hex << theme_resid
                           << " bag=" << (wb.has_value() ? "hit" : "miss")
                           << std::dec << std::endl;
    if (wb) {
        // 3. GOLDEN-03 §7: follow reference hops through the canonical
        //    bounded/cycle-safe path, then decode the color via the ONE
        //    color law.
        ResValue v = *wb;
        if (v.is_reference()) {
            ResolutionResult r = arsc_.resolve_full(v.ref_id, device_config());
            if (!r.ok) return std::nullopt;
            v = *r.value();
        }
        return color_data_to_argb((uint8_t)v.type, v.data);
    }
    // 2b. S95 (L-S95-DEFTHEME-1): a theme whose bag lacks
    //     android:windowBackground (e.g. a FRAMEWORK root style like
    //     Theme.Material.Light — aapt2 does not embed framework-res in
    //     the app ARSC) inherits the framework default through the same
    //     S68 chain (flavor law: *.Light naming / framework style id).
    auto fb = resolve_theme_attr_typed(apk_path, 0x01010054, -1);
    if (s95_dbg) std::cerr << "[S95-THEME] typed fb=" << (fb.has_value() ? "hit" : "miss") << std::endl;
    if (fb.has_value()) {
        // S125 FRAMEWORK-RES FILE LAW: a reference (theme windowBackground
        // = @drawable/screen_background_selector_light) resolves through
        // the committed framework res/ file tree first.
        if (fb->is_reference()) {
            auto file_color = resolve_framework_file_color(fb->ref_id);
            if (file_color) return file_color;
        }
        // The framework table emits INT_HEX (data IS the #AARRGGBB
        // constant — the same law everywhere an INT_HEX color resolves);
        // only literal COLOR_* types go through the named decoder.
        if (fb->is_int()) return (uint32_t)fb->data;
        return color_data_to_argb((uint8_t)fb->type, fb->data);
    }
    return std::nullopt;
}

// F-093 (R-NEW-326, S25): theme attribute resolution — see resource_runtime.h.
// S124 LAW UPGRADE: the old body resolved against the APPLICATION theme only
// (a single bag_value). Every obtainStyledAttributes consumer (the F-NEW-175
// shadow) runs under an ACTIVITY context whose theme chain is activity >
// application — so this service now delegates to resolve_theme_attr_typed:
// overlays → base Theme object → framework default table (the AOSP
// ContextThemeWrapper chain), keeping the "raw reference still meaningful"
// contract for unresolvable refs.
std::optional<ResValue> ResourceRuntime::resolve_theme_attr_value(
        const std::string& apk_path, uint32_t attr_key) {
    static const bool f93_diag = std::getenv("MINIANDROID_F093_DIAG") != nullptr;
    auto out = resolve_theme_attr_typed(apk_path, attr_key, -1);
    if (f93_diag)
        std::cerr << "[F093-DIAG] S124 engine path attr=0x" << std::hex
                  << attr_key << std::dec
                  << " hit=" << (out ? "YES" : "no") << std::endl;
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
    if (!ensure_loaded(apk_path)) return std::nullopt;

    // S124 THEME-BASE — the original-framework resolution order (fetched
    // AOSP libs/androidfw/AttributeResolution.cpp ApplyStyle + AssetManager2
    // Theme): (a) android:theme subtree overlays (ThemeOverlay law, newest
    // first), (b) the base Theme object (activity > application, attr-hop
    // + reference deref per Theme::GetAttribute / ResolveAttributeReference,
    // package-routed into framework-res), then (c) the generated framework
    // default table.
    auto v = ThemeEngine::instance().resolve_attr(arsc_router(), device_config(),
                                                  &base_theme(), attr_key);
    if (v) return v;

    // 2. Framework theme defaults (AOSP law; generated table).
    if ((attr_key >> 24) == 0x01) {
        LaunchTheme lt = resolve_launch_theme(apk_path);
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

// S124 THEME-BASE (the original-framework loading base — user directive: apps
// carry themes/templates; load them through the REAL framework law). The base
// Theme is built once per APK with Theme::apply_style (AssetManager2
// Theme::ApplyStyle law): the launch theme merges its bag through the parent
// chain into a sorted key→value overlay set; normal apply (force=false) keeps
// the nearest-writer — the AOSP precedence inside one theme chain.
// ─────────────────────────────────────────────────────────────────────────
// S124 FW-PACKAGE: load the ORIGINAL framework resource table once. Paths
// tried in order: $MINIANDROID_FRAMEWORK_ARSC, <exe_dir>/../framework_res/
// resources.arsc, <exe_dir>/framework_res/resources.arsc, cwd-relative
// framework_res/resources.arsc. The table is the AOSP multi-package base
// (AssetManager2 ApkAssets[framework-res, app]): Theme.Material + the whole
// framework style/attr/color system become resolvable for app themes.
// ─────────────────────────────────────────────────────────────────────────
bool ResourceRuntime::ensure_framework_resources() {
    if (fw_arsc_loaded_) return true;
    static bool attempted = false;
    if (attempted) return false;
    attempted = true;

    std::vector<std::string> candidates;
    if (const char* env = std::getenv("MINIANDROID_FRAMEWORK_ARSC"))
        candidates.push_back(env);
    char exe_buf[PATH_MAX] = {0};
    ssize_t n = readlink("/proc/self/exe", exe_buf, sizeof(exe_buf) - 1);
    if (n > 0) {
        std::string exe_dir(exe_buf, (size_t)n);
        auto slash = exe_dir.rfind('/');
        if (slash != std::string::npos) exe_dir.resize(slash);
        candidates.push_back(exe_dir + "/../framework_res/resources.arsc");
        candidates.push_back(exe_dir + "/framework_res/resources.arsc");
    }
    candidates.push_back("framework_res/resources.arsc");
    candidates.push_back("miniandroid/framework_res/resources.arsc");

    for (const auto& p : candidates) {
        std::ifstream f(p, std::ios::binary);
        if (!f) continue;
        std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),
                                  std::istreambuf_iterator<char>());
        if (data.empty()) continue;
        if (fw_arsc_.parse(data)) {
            fw_arsc_loaded_ = true;
            std::cerr << "[S124-FWRES] framework-res table loaded: " << p
                      << " bytes=" << data.size()
                      << " types=" << fw_arsc_.stats().entries_by_type.size()
                      << std::endl;
            return true;
        }
        std::cerr << "[S124-FWRES] parse FAILED for " << p << ": "
                  << fw_arsc_.last_error() << std::endl;
        return false;
    }
    std::cerr << "[S124-FWRES] framework-res table NOT FOUND (degrading to "
              << "generated attr-default table)" << std::endl;
    return false;
}

const Theme& ResourceRuntime::base_theme() {
    if (base_theme_built_) return base_theme_;
    base_theme_built_ = true;
    LaunchTheme lt = resolve_launch_theme(apk_path_);
    if (lt.valid && lt.resid != 0) {
        base_theme_.apply_style(arsc_router(), device_config(), lt.resid, /*force=*/false);
        base_theme_valid_ = base_theme_.size() > 0;
    }
    static const bool diag = std::getenv("MINIANDROID_THEME_DIAG") != nullptr;
    if (diag)
        fprintf(stderr, "[S124-THEME] base_theme apk=%s resid=0x%x valid=%d keys=%zu\n",
                apk_path_.c_str(), lt.resid, base_theme_valid_ ? 1 : 0,
                base_theme_.size());
    return base_theme_;
}

// S124: the View-ctor defStyleAttr law — raw theme entry → style resid
// (references stay raw: a style entry is a bag, not a value).
uint32_t ResourceRuntime::resolve_def_style_resid(const std::string& apk_path,
                                                  uint32_t def_style_attr) {
    if (def_style_attr == 0 || !ensure_loaded(apk_path)) return 0;
    auto raw = ThemeEngine::instance().resolve_attr_raw(
        arsc_router(), device_config(), &base_theme(), def_style_attr);
    if (!raw) return 0;
    if (raw->type == DataType::REFERENCE || raw->type == DataType::DYNAMIC_REFERENCE)
        return raw->ref_id;
    // legacy plain-text themes carry "@style/Foo" string items
    if (raw->type == DataType::STRING &&
        raw->string_value.rfind("@style/", 0) == 0) {
        const ArscParser* arsc = arsc_router().for_id(0x7f000000);
        if (arsc) {
            if (auto id = arsc->find_id("", "style", raw->string_value.substr(7)))
                return *id;
        }
    }
    return 0;
}

} // namespace resources
} // namespace miniandroid
