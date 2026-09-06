/*
 * UNIFIED_007 — REAL Layout Inflater.
 *
 * Inflates compiled binary layout XML (AXML) from the APK into a real
 * ViewShadow view tree. Everything comes from the APK itself:
 *   - layout XML:            res/layout/<name>.xml   (found via ARSC)
 *   - strings/colors/dimens: resources.arsc
 *   - drawables:             res/drawable-xxx/name.ext  (extracted from APK)
 *   - styles/themes:         resources.arsc complex entries
 *
 * No JSON sidecars, no manual caches — the exact anti-pattern UNIFIED_007
 * forbids. This module replaces layout_cache.json inflation.
 */

#ifndef MINIANDROID_LAYOUT_INFLATER_H
#define MINIANDROID_LAYOUT_INFLATER_H

#include <string>
#include <map>
#include <vector>
#include <functional>
#include <unordered_map>

#include "arsc_parser.h"
#include "axml_parser.h"
#include "../framework/view_ancestry.h"  // G12 FIX-G12-001: framework ancestry law
#include "../framework/android_shadows.h"
#include "../apk/apk_parser.h"

namespace miniandroid {
namespace resources {

// Virtual device metrics for dp→px (Pixel-1-like: 1080×1920 @ 420dpi)
struct DeviceMetrics {
    int screen_width = 1080;
    int screen_height = 1920;
    float density = 2.625f;   // px per dp
    float scale_fonts = 1.0f; // user font scale
};

struct InflateStats {
    int elements_total = 0;
    int views_created = 0;
    int strings_resolved = 0;
    int colors_resolved = 0;
    int dimens_resolved = 0;
    int drawables_resolved = 0;
    int styles_applied = 0;
    int includes_expanded = 0;
    int ids_resolved = 0;
    int unresolved_refs = 0;
    std::vector<std::string> warnings;
    std::string to_json() const;
};

class LayoutInflater {
public:
    LayoutInflater(ArscParser& arsc, apk::ApkParser& apk, const std::string& apk_path,
                   const DeviceMetrics& metrics = DeviceMetrics{});

    // Inflate layout by resource id (e.g. 0x7f030000 from setContentView).
    // Returns root view_id (0 on failure).
    // G11 FIX-G11-002 (AOSP LayoutInflater.inflate law): parent_view_id lets
    // LayoutInflater.inflate(resId, root[, attachToRoot]) attach the inflated
    // tree INTO an existing view (app constructors inflate their own
    // children this way — CalculatorDisplay.<init>). parent 0 = window path.
    uint32_t inflate_layout_resid(framework::ViewShadow* views, uint32_t layout_resid,
                                  InflateStats& stats, uint32_t parent_view_id = 0);

    // Inflate layout by name ("act_gmdice").
    uint32_t inflate_layout_by_name(framework::ViewShadow* views, const std::string& name,
                                    InflateStats& stats);

    // Resolve a drawable resource id → APK entry path ("" if not resolvable)
    std::string drawable_path_for_resid(uint32_t resid);
    // Resolve drawable by name
    std::string drawable_path_for_name(const std::string& name);
    // G04 §4: canonical selection that ALSO reports the SELECTED config
    // density (raw ResTable_config form: 0=unset→DENSITY_DEFAULT 160,
    // 0xFFFF=DENSITY_NONE → caller must not scale). Single implementation
    // of the density-bucket law; the plain-path variants delegate here.
    std::string drawable_file_for_resid(uint32_t resid, uint16_t* out_density);
    std::string drawable_file_for_name(const std::string& name, uint16_t* out_density);

    // Measure + layout pass: compute real geometry for the tree under root.
    // Fills node x/y/width/height (+padding) — the renderer uses these.
    void measure_layout(framework::ViewShadow* views, uint32_t root_id);

    const DeviceMetrics& metrics() const { return metrics_; }

    // G10 FIX-G10-002 (AOSP class-hierarchy law): container behavior
    // (LinearLayout/FrameLayout/RelativeLayout measure+layout semantics)
    // follows the RESOLVED SUPERCLASS CHAIN of the view's class, not the
    // leaf class-name substring. App-defined subclasses (CalculatorDisplay
    // extends LinearLayout) and framework containers (ViewSwitcher extends
    // FrameLayout) must classify by their real ancestors. The executor
    // wires its DEX-backed is_subclass_of here; without it the inflater
    // falls back to the legacy substring law (keeps law-test harnesses
    // that drive the inflater standalone green).
    void set_is_a(std::function<bool(const std::string&, const std::string&)> fn) {
        is_a_ = std::move(fn);
    }
    bool is_a(const std::string& class_desc, const std::string& ancestor) const {
        if (is_a_) return is_a_(class_desc, ancestor);
        // G12 FIX-G12-001: framework ancestry law before the legacy
        // substring fallback (TableRow extends LinearLayout — the substring
        // test called it a leaf and measured 0x0 rows).
        if (framework::framework_is_subclass(class_desc, ancestor)) return true;
        // legacy fallback: descriptor-substring containment
        return !ancestor.empty() && class_desc.find(ancestor) != std::string::npos;
    }

    // G11 FIX-G11-001: descriptor gate for the constructor hook — true when
    // the descriptor does not belong to a framework/library package.
    static bool is_app_class_descriptor(const std::string& class_desc);

    // after inflate, call this to register android:onClick handlers on nodes
    std::unordered_map<uint32_t, std::string> onClick_handlers;

    // ── G11 FIX-G11-001 (AOSP LayoutInflater.createView law) ────────────
    // A fully-qualified app-class XML tag (<org.debian.eugen…CalculatorKeypad/>)
    // is an INSTANTIATION: the runtime must execute the class's REAL DEX
    // constructor <init>(Context, AttributeSet)/(Context) so the app-side
    // hierarchy built inside it (LayoutInflater.inflate(res, this), addView,
    // findViewById) exists. The resources layer cannot depend on the dex
    // layer, so the executor installs this hook (same law as set_is_a).
    // Hook returns true when a constructor executed (class found in app DEX).
    using CustomViewCtorHook =
        std::function<bool(uint32_t view_id, const std::string& class_desc)>;
    void set_custom_view_ctor_hook(CustomViewCtorHook fn) {
        custom_view_ctor_hook_ = std::move(fn);
    }
    const CustomViewCtorHook& custom_view_ctor_hook() const {
        return custom_view_ctor_hook_;
    }

    // MASTER CAMPAIGN FIX (F10 real-DEX onMeasure): the executor installs
    // this hook (same law as the ctor hook — resources layer cannot depend
    // on the dex layer). The measure pass calls it for a leaf node whose
    // DEX chain overrides onMeasure; the hook executes the REAL bytecode
    // and returns the setMeasuredDimension write-back.
    using CustomViewMeasureHook =
        std::function<bool(uint32_t view_id, int wspec, int hspec,
                           int& out_w, int& out_h)>;
    void set_custom_view_measure_hook(CustomViewMeasureHook fn) {
        custom_view_measure_hook_ = std::move(fn);
    }
    const CustomViewMeasureHook& custom_view_measure_hook() const {
        return custom_view_measure_hook_;
    }

private:
    // G04 §8: drawable intrinsic-size probe cache (path → natural dims;
    // {-1,-1} = probe failed — never retried, honest 48dp fallback applies).
    std::map<std::string, std::pair<int,int>> image_probe_cache_;
    bool image_intrinsic_size(const std::string& path, uint16_t sel_density,
                              int* out_w, int* out_h);
    struct Attrs {
        int  id_resid = 0;
        int  layout_width = -2;   // -1 match, -2 wrap, >0 px
        int  layout_height = -2;
        bool width_set = false, height_set = false;
        int  ml = 0, mt = 0, mr = 0, mb = 0;
        int  pl = 0, pt = 0, pr = 0, pb = 0;
        int  orientation = -1;
        int  gravity = -1;        // android:gravity (container content gravity)
        int  layout_gravity = -1; // child gravity inside parent
        int  layout_weight = 0;
        std::string text, hint;
        float text_size_px = 0;
        uint32_t text_color = 0;
        int  text_style = 0;      // bit0 bold, bit1 italic
        std::string font_family;  // G32: android:fontFamily (raw string)
        // G46/GOLDEN-03 §8: TextAppearance textSize, ALREADY converted to px
        // through the canonical TypedValue law (complexToDimensionPixelSize —
        // 22sp → 58px at density 2.625).
        float appearance_text_size_px = 0;
        bool  appearance_resolved = false;
        // G47: android:lineSpacingMultiplier / lineSpacingExtra /
        // elegantTextHeight / includeFontPadding (TextView defaults).
        float line_spacing_mult = 1.0f;
        float line_spacing_add_px = 0.0f;
        bool include_font_pad = true;
        bool elegant_text_height = false;
        uint32_t bg_color = 0;    // resolved ARGB (opaque)
        std::string bg_drawable;  // APK path
        std::string src_drawable; // APK path (ImageView)
        // G04 §4: SELECTED config density (raw form) for the file-backed
        // drawables above — drives the BitmapFactory inDensity→inTargetDensity
        // scaling law at draw and intrinsic-size measurement.
        uint16_t bg_drawable_density = 0;
        uint16_t src_drawable_density = 0;
        std::string onClick;      // handler method name
        int  visibility = 0;      // 0 visible, 4 invisible, 8 gone
        bool clickable = false;
        int  num_lines = -1;
        bool single_line = false;
        int  padding_all = 0;
        int  elevation_px = 0;
        bool weight_sum_valid = false;
        float weight_sum = 0;
        std::string style_name;   // resolved style for evidence
        // FIX-2c: RelativeLayout sibling-dependency rules (referenced id names)
        std::string rel_below, rel_above, rel_right_of, rel_left_of;
        // applied style values
        bool from_style_text_size = false;
        uint32_t style_text_color = 0;
        float style_text_size_px = 0;
    };

    uint32_t inflate_element(framework::ViewShadow* views, const AxmlElement& el,
                             uint32_t parent_view_id, InflateStats& stats);
    void apply_element_attrs(framework::ViewShadow::ViewNode& node,
                             const AxmlElement& el, Attrs& a, InflateStats& stats);
    void apply_style(framework::ViewShadow::ViewNode& node, Attrs& a,
                     uint32_t style_resid, InflateStats& stats);
    void apply_style_by_name(framework::ViewShadow::ViewNode& node, Attrs& a,
                             const std::string& style_name, InflateStats& stats);

    // attribute value helpers
    enum class RefKind { NONE, STRING, COLOR, DIMEN, DRAWABLE, LAYOUT, STYLE, ID, BOOL, INTEGER };
    struct ParsedRef {
        RefKind kind = RefKind::NONE;
        std::string name;      // e.g. "app_name"
        std::string literal;   // raw literal if not a ref
        bool is_ref = false;
    };
    static ParsedRef parse_ref(const std::string& v);
    std::string resolve_string_ref(const std::string& name, InflateStats& stats);
    uint32_t resolve_color(const std::string& v, InflateStats& stats);   // @color or #hex or literal
    int      resolve_dimen_px(const std::string& v, InflateStats& stats); // @dimen or "Ndp"/"Nsp"/"Npx"
    int      parse_dim_attr(const AxmlAttribute* attr, InflateStats& stats); // typed or raw dim
    uint32_t parse_color_attr(const AxmlAttribute* attr, InflateStats& stats);
    int      resolve_size_or_match(const AxmlAttribute* attr, InflateStats& stats); // -1/-2/px
    uint32_t resolve_id_attr(const AxmlAttribute* attr, InflateStats& stats);
    static uint32_t parse_hex_color(const std::string& s);

    // ── GOLDEN-03 §8/§9 ─────────────────────────────────────────────────
    // §9: the ONE TypedValue conversion context for this inflater.
    DensityContext density_context() const;
    // §8: apply ONE style-bag item selected by its AOSP attribute KEY
    // (ResTable_map law) — textSize/textColor with reference dereferencing.
    // Returns true when the item was applied (counted in stats).
    bool apply_style_item(Attrs& a, uint32_t attr_key, const ResValue& item,
                          InflateStats& stats);
    // §8/G46: textAppearance resolution — generic app-style bags via the
    // canonical bag resolver (parent inheritance included) + the byte-verified
    // framework TextAppearance table. Returns false when unresolvable.
    bool resolve_text_appearance(uint32_t style_resid, Attrs& a, InflateStats& stats);

    static std::string class_to_descriptor(const std::string& xml_name);
    static int gravity_bits(const std::string& s);
    std::string find_apk_file(const std::string& type, const std::string& name);

    ArscParser& arsc_;
    apk::ApkParser& apk_;
    std::string apk_path_;
    DeviceMetrics metrics_;
    // G10 FIX-G10-002: DEX-backed superclass-chain classifier (may be null)
    std::function<bool(const std::string&, const std::string&)> is_a_;
    // G11 FIX-G11-001: DEX constructor-execution bridge (may be unset —
    // standalone law-test harnesses drive the inflater without the engine).
    CustomViewCtorHook custom_view_ctor_hook_;
    CustomViewMeasureHook custom_view_measure_hook_;
    // FIX-2c: id → key-name map (lazily built from resources.arsc) used to
    // name compiled android:id references and bind RelativeLayout rules.
    std::map<uint32_t, std::string> id_names_;
    std::vector<std::string> apk_entries_;  // cached entry list
    int pending_id_counter_ = 0;
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_LAYOUT_INFLATER_H
