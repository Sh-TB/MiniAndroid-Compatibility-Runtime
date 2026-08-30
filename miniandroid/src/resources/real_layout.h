/*
 * MiniAndroid Runtime - UNIFIED_007 EXP-121
 * RealInflater: in-runtime layout inflation from the REAL APK.
 *   resources.arsc (ArscParser) + binary AXML (AxmlParser)
 *   → RView tree → ViewShadow nodes (same tree the engine mutates via
 *   real bytecode: findViewById, setText, setOnClickListener ...).
 *
 * Replaces the previous offline layout_cache.json dependency
 * (tools/exp087_layout_cache_generator.py) as the PRIMARY path; the cache
 * remains as a fallback and for regression safety.
 */

#ifndef MINIANDROID_REAL_LAYOUT_H
#define MINIANDROID_REAL_LAYOUT_H

#include "arsc_parser.h"
#include "axml_parser.h"
#include "../apk/apk_parser.h"
#include "../framework/android_shadows.h"
#include <string>
#include <vector>
#include <memory>

namespace miniandroid {
namespace resources {

struct InflateReport {
    bool ok = false;
    std::string error;
    std::string layout_path;          // actual zip path used
    uint32_t layout_res_id = 0;
    int view_count = 0;
    int text_view_count = 0, button_count = 0, image_view_count = 0;
    int edit_text_count = 0, view_group_count = 0, custom_count = 0;
    int attr_count = 0;               // total XML attributes consumed
    int unresolved_refs = 0;          // framework refs we cannot resolve (honest)
    int resolved_string_refs = 0, resolved_color_refs = 0, resolved_drawable_refs = 0;
    uint32_t root_view_id = 0;        // shadow tree root
    std::vector<std::string> notes;   // e.g. custom views treated as TextView
};

class RealInflater {
public:
    RealInflater(apk::ApkParser& apk, ArscParser& arsc, float density = 2.f)
        : apk_(apk), arsc_(arsc), density_(density) {}

    // Inflate by resource id (as passed to setContentView(int)).
    InflateReport inflate_into_shadow(uint32_t layout_res_id,
                                      framework::ViewShadow* views,
                                      uint32_t activity_object_id);

    // Inflate by type+name (harness convenience).
    InflateReport inflate_into_shadow(const std::string& type,
                                      const std::string& name,
                                      framework::ViewShadow* views,
                                      uint32_t activity_object_id);

private:
    struct RView;
    RView build(const AxmlNode& node, InflateReport& rep);
    void convert_and_attach(const RView& rv, uint32_t parent_shadow_id,
                            framework::ViewShadow* views,
                            uint32_t activity_object_id, InflateReport& rep);
    bool resolve_attr(const AxmlAttribute& a, ResolvedValue& out) const;
    int dim_px(const AxmlAttribute& a) const;
    uint32_t color_of(const AxmlAttribute& a, InflateReport& rep) const;
    void load_shape_drawable(const std::string& zip_path, RView& rv,
                             InflateReport& rep);
    std::string drawable_path_for(const AxmlAttribute& a, InflateReport& rep) const;

    struct RView {
        std::string cls;
        int android_id = 0;
        int lp_w = -2, lp_h = -2;         // -1 match, -2 wrap, >=0 px
        int ml = 0, mt = 0, mr = 0, mb = 0;
        int pl = 0, pt = 0, pr = 0, pb = 0;
        int orientation = 1;
        float weight = 0;
        int gravity = -1, layout_gravity = -1, text_gravity = -1;
        std::string text, hint;
        float text_size = 0;              // px (converted)
        uint32_t text_color = 0;
        bool text_color_set = false;
        bool bold = false, italic = false, single_line = false;
        std::string on_click;
        bool bg_color_set = false;
        uint32_t bg_color = 0;
        std::string bg_drawable;          // zip path (bitmap)
        bool bg_shape_has_solid = false; uint32_t bg_shape_solid = 0;
        bool bg_shape_has_gradient = false;
        uint32_t grad_start = 0, grad_end = 0; int grad_angle = 0;
        float corner_radius = 0;
        bool has_stroke = false; uint32_t stroke_color = 0; float stroke_w = 0;
        std::string src_path;             // ImageView source
        bool clickable = false;
        int visibility = 0;
        // relative layout rules
        int rel_below = 0, rel_above = 0, rel_leftof = 0, rel_rightof = 0;
        int rel_align_left = 0, rel_align_right = 0, rel_align_top = 0, rel_align_bottom = 0;
        bool rel_parent_top = false, rel_parent_bottom = false;
        bool rel_parent_left = false, rel_parent_right = false;
        bool rel_center_h = false, rel_center_v = false, rel_center = false;
        std::vector<RView> children;
    };

    apk::ApkParser& apk_;
    ArscParser& arsc_;
    float density_;
};

}  // namespace resources
}  // namespace miniandroid

#endif  // MINIANDROID_REAL_LAYOUT_H
