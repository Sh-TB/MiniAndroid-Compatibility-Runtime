// theme_engine.h — S124 THEME/TEMPLATE LOADING BASE (the original-framework law).
//
// User directive (fa): "every app carries a template loader / a theme / a
// template structure — build the base for it; find the ORIGINAL framework and
// load templates and apps according to it." This module IS that base: a
// faithful port of the AOSP theme machinery, researched from the framework
// sources themselves (fetched 2026-09-30, byte-verified):
//
//   libs/androidfw/AssetManager2.cpp
//     - Theme::ApplyStyle (L1635): a Theme is a sorted parallel array of
//       (attr key → entry). Applying a style merges the style's bag through
//       its parent chain; a NORMAL apply never overrides an already-present
//       key; a FORCE apply overwrites (and an undefined value removes).
//     - Theme::GetAttribute (L1732): sorted-array lookup; a TYPE_ATTRIBUTE
//       value hops to the attribute it names, bounded by kMaxIterations=20.
//     - Theme::ResolveAttributeReference (L1757): a TYPE_REFERENCE is
//       dereferenced through the AssetManager (our ARSC resolver).
//   libs/androidfw/AttributeResolution.cpp
//     - ApplyStyle (L220..): the per-attribute resolution priority chain,
//       quoted verbatim from the source: "we prioritize values coming from,
//       first XML attributes, then XML style, then default style, and
//       finally the theme." @null turns back into TYPE_NULL.
//   core/java/android/content/res/ResourcesImpl.java
//     - ThemeImpl.applyStyle (L1471): applyStyleToTheme + ThemeKey append —
//       the Java face of the same overlay law.
//   core/res/res/values/public-final.xml (AOSP main)
//     - frozen framework attr ids for the View-ctor defStyleAttr law
//       (buttonStyle 0x01010048, textViewStyle 0x01010084, ...). IDs are
//       never guessed from memory — read from the fetched table.
//
// What this adds over the pre-S124 service (a single bag_value on the launch
// theme + a 23-row framework default table):
//   1. a real Theme OBJECT with overlay semantics (apply_style force/normal);
//   2. TYPE_ATTRIBUTE hop chains inside the theme (?attr pointing at ?attr);
//   3. subtree android:theme overlays (MaterialComponents ThemeOverlay law:
//      a view tag's android:theme re-themes its whole subtree);
//   4. the defStyleAttr tier for the inflater (widget template defaults).
//
// Honest scope: framework-RES styles (package 0x01, e.g. the style a
// Theme.Material item points at) do NOT resolve through the app ARSC — the
// engine skips them and falls back to the generated FRAMEWORK_THEME_ATTRS
// table (S68 W2 law). This is documented behavior, never invented values.

#pragma once

#include <algorithm>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_set>
#include <vector>

#include "arsc_parser.h"

namespace miniandroid {
namespace resources {

// ─────────────────────────────────────────────────────────────────────────
// S124 FW-PACKAGE: the AOSP AssetManager2 multi-package law. A resource id's
// top byte names the package: 0x01 = framework-res (the ORIGINAL framework
// resource table every app inherits), 0x7f = the app. The framework table is
// loaded from a real framework-res resources.arsc; when absent the engine
// degrades to the generated FRAMEWORK_THEME_ATTRS table (honest fallback).
// ─────────────────────────────────────────────────────────────────────────
struct ArscRouter {
    const ArscParser* app = nullptr;
    const ArscParser* fw = nullptr;   // framework-res (package 0x01)
    const ArscParser* for_id(uint32_t id) const {
        if ((id >> 24) == 0x01 && fw) return fw;
        return app;
    }
};

// AOSP ResourceTypes.h Res_value TYPE_NULL data codes.
static constexpr uint32_t DATA_NULL_UNDEFINED = 0;
static constexpr uint32_t DATA_NULL_EMPTY = 1;

// AOSP AssetManager2.cpp IsUndefined law: @null (DATA_NULL_EMPTY) is a valid
// value; the undefined sentinel is TYPE_NULL with any other data word.
inline bool theme_value_is_undefined(const ResValue& v) {
    return v.type == DataType::NULL_ && v.data != DATA_NULL_EMPTY;
}

// ─────────────────────────────────────────────────────────────────────────────
// Theme — the AOSP AssetManager2::Theme port over our ARSC parser.
// ─────────────────────────────────────────────────────────────────────────────
class Theme {
public:
    // Theme::ApplyStyle (AssetManager2.cpp L1635): merge one style's bag.
    // The style's OWN keys apply first (nearest), then the parent chain
    // (bag_parent), bounded + cycle-safe. force=false never overrides an
    // existing key; force=true overwrites (an undefined value removes the
    // previous entry — the AOSP "forced undefined removes" branch).
    // S124 FW-PACKAGE: the walk routes each chain hop through the package
    // router — app themes climbing into Theme.Material resolve the REAL
    // framework bags from framework-res.
    void apply_style(const ArscRouter& rt, const ResTableConfig& device,
                     uint32_t style_resid, bool force) {
        static const bool diag = std::getenv("MINIANDROID_THEME_DIAG") != nullptr;
        uint32_t cur = style_resid;
        int hops = 0;
        std::unordered_set<uint32_t> visited{style_resid};
        while (cur != 0 && hops <= 24) {
            const ArscParser* arsc = rt.for_id(cur);
            if (!arsc) break;
            auto r = arsc->resolve(cur);
            if (!r) break;
            const ArscEntry* e = r->best();
            if (!e || !e->is_complex) {
                // AOSP GetBag tolerates simple styles (single value, no bag):
                // they contribute nothing to the overlay. The PARENT CHAIN
                // still continues (a simple bridge style does not end
                // inheritance — AOSP walks the declared parent regardless).
                uint32_t parent = e ? e->bag_parent : 0;
                if (parent == 0 || parent == cur || visited.count(parent)) break;
                visited.insert(parent);
                cur = parent;
                hops++;
                continue;
            }
            for (size_t i = 0; i < e->complex_keys.size() && i < e->complex_items.size(); ++i) {
                merge_key(e->complex_keys[i], e->complex_items[i], force);
            }
            uint32_t parent = e->bag_parent;
            if (parent == 0 || parent == cur || visited.count(parent)) break;
            visited.insert(parent);
            cur = parent;
            hops++;
        }
        if (diag)
            fprintf(stderr, "[S124-THEME] apply_style resid=0x%x force=%d -> keys=%zu\n",
                    style_resid, force ? 1 : 0, kv_.size());
        keys_applied_ += 1;
    }

    // Theme::GetAttribute (AssetManager2.cpp L1732): sorted-array binary
    // lookup; TYPE_ATTRIBUTE values hop to their named attribute (≤20 hops,
    // the AOSP kMaxIterations law). Returns the RAW entry (may still be a
    // reference — callers resolve through resolve_attribute / the ARSC).
    const ResValue* get_attribute(uint32_t attr_key) const {
        constexpr uint32_t kMaxIterations = 20;   // AOSP law constant
        uint32_t resid = attr_key;
        for (uint32_t i = 0; i <= kMaxIterations; i++) {
            auto it = std::lower_bound(kv_.begin(), kv_.end(), resid,
                [](const std::pair<uint32_t, ResValue>& p, uint32_t k) {
                    return p.first < k;
                });
            if (it == kv_.end() || it->first != resid) return nullptr;
            if (theme_value_is_undefined(it->second)) return nullptr;
            if (it->second.type == DataType::ATTRIBUTE) {
                resid = it->second.data;   // hop to the attribute it names
                continue;
            }
            return &it->second;
        }
        return nullptr;   // hop bound exceeded — honest miss
    }

    // Theme::ResolveAttributeReference: resolve the FINAL typed value for a
    // theme attr key — attribute hops (inside the theme) followed by one
    // package-routed ARSC reference deref. An unresolvable reference returns
    // the raw reference (callers downstream treat ref_id meaningfully — the
    // same contract as the pre-S124 service).
    std::optional<ResValue> resolve_attribute(const ArscRouter& rt,
                                              const ResTableConfig& device,
                                              uint32_t attr_key) const {
        const ResValue* raw = get_attribute(attr_key);
        if (!raw) return std::nullopt;
        ResValue out = *raw;
        if (out.is_reference()) {
            const ArscParser* arsc = rt.for_id(out.ref_id);
            if (arsc) {
                ResolutionResult r = arsc->resolve_full(out.ref_id, device);
                if (r.ok) out = *r.value();
            }
            // unresolved reference: return the raw ref (honest, per contract)
        }
        return out;
    }

    size_t size() const { return kv_.size(); }
    uint32_t applied_styles() const { return keys_applied_; }

private:
    void merge_key(uint32_t key, const ResValue& v, bool force) {
        auto it = std::lower_bound(kv_.begin(), kv_.end(), key,
            [](const std::pair<uint32_t, ResValue>& p, uint32_t k) {
                return p.first < k;
            });
        const bool found = it != kv_.end() && it->first == key;
        if (found) {
            if (!force) return;                    // normal apply: keep first
            if (theme_value_is_undefined(v)) {     // forced undefined: remove
                kv_.erase(it);
                return;
            }
            it->second = v;                        // forced overwrite
            return;
        }
        if (theme_value_is_undefined(v)) return;   // undefined never inserts
        kv_.insert(it, {key, v});                  // sorted insert
    }

    std::vector<std::pair<uint32_t, ResValue>> kv_;   // sorted by attr key
    uint32_t keys_applied_ = 0;
};

// ─────────────────────────────────────────────────────────────────────────────
// ThemeEngine — process-wide overlay scope + the ONE resolution service.
//
// Base theme: built and cached by ResourceRuntime (it owns the manifest
// reader and the per-APK ARSC). Overlays: the LayoutInflater pushes an
// overlay when a tag carries android:theme (AOSP MaterialComponents
// ThemeOverlay law — MaterialThemeOverlay.wrap wraps the subtree context in
// a ContextThemeWrapper that applyStyle()s the referenced style). Resolution
// walks overlays TOP-DOWN (the newest overlay wins), then falls through to
// the caller-provided base theme, then to the framework default table.
// ─────────────────────────────────────────────────────────────────────────────
class ThemeEngine {
public:
    static ThemeEngine& instance() {
        static ThemeEngine e;
        return e;
    }

    // android:theme subtree scope. The cookie guards unbalanced pops (an
    // inflate path that bails early must not pop a foreign overlay).
    uint32_t push_overlay(uint32_t style_resid) {
        overlays_.emplace_back();
        overlays_.back().style_resid = style_resid;
        return (uint32_t)overlays_.size();   // cookie = 1-based depth
    }
    void pop_overlay(uint32_t cookie) {
        if (cookie == 0 || cookie > overlays_.size()) return;   // honest no-op
        overlays_.resize(cookie - 1);
    }
    void clear_overlays() { overlays_.clear(); }
    size_t overlay_count() const { return overlays_.size(); }

    // THE resolution service (AttributeResolution.cpp ApplyStyle law, theme
    // tier first: overlays → base → framework table). flavor_hint < 0 means
    // "caller has no flavor opinion" (the base theme's flavor decides).
    std::optional<ResValue> resolve_attr(const ArscRouter& rt,
                                         const ResTableConfig& device,
                                         const Theme* base_theme,
                                         uint32_t attr_key) {
        static const bool diag = std::getenv("MINIANDROID_THEME_DIAG") != nullptr;
        // 1. android:theme overlays, newest first (ThemeOverlay law).
        for (auto it = overlays_.rbegin(); it != overlays_.rend(); ++it) {
            if (!it->expanded) {
                it->theme.apply_style(rt, device, it->style_resid, /*force=*/false);
                it->expanded = true;
                it->expanded_size = it->theme.size();
            }
            if (auto v = it->theme.resolve_attribute(rt, device, attr_key)) {
                if (diag)
                    fprintf(stderr, "[S124-THEME] attr=0x%x -> OVERLAY 0x%x\n",
                            attr_key, it->style_resid);
                return v;
            }
        }
        // 2. base theme (activity > application chain, AOSP ActivityInfo law).
        if (base_theme) {
            if (auto v = base_theme->resolve_attribute(rt, device, attr_key)) {
                if (diag)
                    fprintf(stderr, "[S124-THEME] attr=0x%x -> BASE type=%d data=0x%x\n",
                            attr_key, (int)v->type, v->data);
                return v;
            }
        }
        resolve_misses_++;
        return std::nullopt;   // caller decides the framework-table fallback
    }

    // Raw (unresolved) theme entry — the Theme::GetAttribute law. Overlays
    // newest-first, then the base theme. References stay RAW (the caller
    // decides: style resids must NOT be dereferenced — a style entry is a
    // bag, not a value).
    std::optional<ResValue> resolve_attr_raw(const ArscRouter& rt,
                                             const ResTableConfig& device,
                                             const Theme* base_theme,
                                             uint32_t attr_key) {
        for (auto it = overlays_.rbegin(); it != overlays_.rend(); ++it) {
            if (!it->expanded) {
                it->theme.apply_style(rt, device, it->style_resid, /*force=*/false);
                it->expanded = true;
                it->expanded_size = it->theme.size();
            }
            if (const ResValue* raw = it->theme.get_attribute(attr_key)) return *raw;
        }
        if (base_theme) {
            if (const ResValue* raw = base_theme->get_attribute(attr_key)) return *raw;
        }
        resolve_misses_++;
        return std::nullopt;
    }

    // ─────────────────────────────────────────────────────────────────────
    // View-ctor defStyleAttr law (frameworks/base View.java ctor chain):
    // every framework widget ctor passes its default-style attr; the theme
    // maps it to the widget's default style. Ids VERIFIED from the fetched
    // core/res/res/values/public-final.xml (AOSP main) — never guessed.
    // Custom views inflate through View(Context, AttributeSet) → defStyleAttr
    // = 0 (no default style) — the table answers 0 for unknown tags.
    // ─────────────────────────────────────────────────────────────────────
    static uint32_t framework_def_style_attr(const std::string& tag_name) {
        static const struct { const char* tag; uint32_t attr; } LAW[] = {
            {"Button",       0x01010048u},   // buttonStyle
            {"CheckBox",     0x0101006cu},   // checkboxStyle
            {"RadioButton",  0x0101007eu},   // radioButtonStyle
            {"EditText",     0x0101006eu},   // editTextStyle
            {"ProgressBar",  0x01010077u},   // progressBarStyle
            {"SeekBar",      0x0101007bu},   // seekBarStyle
            {"Spinner",      0x01010081u},   // spinnerStyle
            {"ScrollView",   0x01010080u},   // scrollViewStyle
            {"ListView",     0x01010074u},   // listViewStyle
            {"GridView",     0x01010071u},   // gridViewStyle
            {"Switch",       0x0101043fu},   // switchStyle
            {"Toolbar",      0x010104aau},   // toolbarStyle
            {"ImageButton",  0x01010072u},   // imageButtonStyle
            {"TextView",     0x01010084u},   // textViewStyle
        };
        for (const auto& l : LAW)
            if (tag_name == l.tag) return l.attr;
        return 0;   // AOSP law: unknown/custom classes carry defStyleAttr 0
    }

    uint64_t resolve_misses() const { return resolve_misses_; }

private:
    struct OverlayScope {
        uint32_t style_resid = 0;
        Theme theme;
        bool expanded = false;
        size_t expanded_size = 0;
    };
    std::vector<OverlayScope> overlays_;   // innermost = newest
    uint64_t resolve_misses_ = 0;
};

}  // namespace resources
}  // namespace miniandroid
