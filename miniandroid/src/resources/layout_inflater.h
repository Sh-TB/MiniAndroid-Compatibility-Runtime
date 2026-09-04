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
    uint32_t inflate_layout_resid(framework::ViewShadow* views, uint32_t layout_resid,
                                  InflateStats& stats);

    // Inflate layout by name ("act_gmdice").
    uint32_t inflate_layout_by_name(framework::ViewShadow* views, const std::string& name,
                                    InflateStats& stats);

    // Resolve a drawable resource id → APK entry path ("" if not resolvable)
    std::string drawable_path_for_resid(uint32_t resid);
    // Resolve drawable by name
    std::string drawable_path_for_name(const std::string& name);

    // Measure + layout pass: compute real geometry for the tree under root.
    // Fills node x/y/width/height (+padding) — the renderer uses these.
    void measure_layout(framework::ViewShadow* views, uint32_t root_id);

    const DeviceMetrics& metrics() const { return metrics_; }

    // after inflate, call this to register android:onClick handlers on nodes
    std::unordered_map<uint32_t, std::string> onClick_handlers;

private:
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
        uint32_t bg_color = 0;    // resolved ARGB (opaque)
        std::string bg_drawable;  // APK path
        std::string src_drawable; // APK path (ImageView)
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

    static std::string class_to_descriptor(const std::string& xml_name);
    static int gravity_bits(const std::string& s);
    std::string find_apk_file(const std::string& type, const std::string& name);

    ArscParser& arsc_;
    apk::ApkParser& apk_;
    std::string apk_path_;
    DeviceMetrics metrics_;
    // FIX-2c: id → key-name map (lazily built from resources.arsc) used to
    // name compiled android:id references and bind RelativeLayout rules.
    std::map<uint32_t, std::string> id_names_;
    std::vector<std::string> apk_entries_;  // cached entry list
    int pending_id_counter_ = 0;
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_LAYOUT_INFLATER_H
