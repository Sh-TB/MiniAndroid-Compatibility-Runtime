/* UNIFIED_007 EXP-121 — RealInflater implementation. */

#include "real_layout.h"
#include "../renderer/software_renderer.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <functional>

namespace miniandroid {
namespace resources {

using framework::ViewShadow;

// Gravity bits (AOSP android.view.Gravity)
static const int kGravityCenterV = 0x10;
static const int kGravityCenterH = 0x01;
static const int kGravityCenter = 0x11;
static const int kGravityTop = 0x30;
static const int kGravityBottom = 0x50;
static const int kGravityLeft = 0x03;
static const int kGravityRight = 0x05;
static const int kGravityStart = 0x00800003;
static const int kGravityEnd = 0x00800005;

static bool is_view_group(const std::string& cls) {
    return cls == "LinearLayout" || cls == "FrameLayout" ||
           cls == "RelativeLayout" || cls == "ScrollView" ||
           cls == "HorizontalScrollView" || cls == "GridLayout" ||
           cls == "TableLayout" || cls == "TableRow" ||
           cls == "AbsoluteLayout" || cls == "RadioGroup" ||
           cls == "Toolbar" || cls == "ViewPager" ||
           cls == "ConstraintLayout" || cls == "CoordinatorLayout" ||
           cls == "AppBarLayout" || cls == "CollapsingToolbarLayout" ||
           cls == "RecyclerView" || cls == "ListView" || cls == "GridView";
}
static bool is_text_like(const std::string& cls) {
    return cls == "TextView" || cls == "Button" || cls == "EditText" ||
           cls == "CheckBox" || cls == "RadioButton" || cls == "ToggleButton" ||
           cls == "Switch";
}

void RealInflater::load_shape_drawable(const std::string& zip_path, RView& rv,
                                       InflateReport& rep) {
    auto xml = apk_.extract_entry_cached(zip_path);
    if (xml.empty()) return;
    AxmlParser ax;
    if (!ax.parse(xml.data(), xml.size())) return;
    std::vector<RView*> stack;
    RView tmp;
    tmp.cls = ax.root().name;
    stack.push_back(&tmp);
    // flatten walk
    std::function<void(const AxmlNode&)> walk = [&](const AxmlNode& n) {
        for (const auto& a : n.attrs) {
            const std::string& nm = a.name;
            if (nm == "color" || nm == "startColor" || nm == "endColor") {
                uint32_t c = color_of(a, rep);
                if (a.raw_value.empty() && a.value_type >= 0x1c) {
                    c = ArscParser::color_from_data(a.value_type, a.value_data);
                } else if (a.value_type == 0x01) {
                    auto r = arsc_.resolve(a.value_data);
                    if (r.found && r.is_color) c = r.color_argb;
                } else if (!a.raw_value.empty() && a.raw_value[0] == '#') {
                    c = strtoul(a.raw_value.c_str() + 1, nullptr, 16);
                    if (a.raw_value.size() <= 7) c |= 0xff000000u;
                }
                if (nm == "color") { rv.bg_shape_has_solid = true; rv.bg_shape_solid = c; }
                if (nm == "startColor") { rv.bg_shape_has_gradient = true; rv.grad_start = c; }
                if (nm == "endColor") { rv.bg_shape_has_gradient = true; rv.grad_end = c; }
            } else if (nm == "angle") {
                rv.grad_angle = a.value_data;
            } else if (nm == "radius" || nm == "topLeftRadius" || nm == "radius2") {
                rv.corner_radius = dim_px(a);
            } else if (nm == "width" && n.name == "stroke") {
                rv.has_stroke = true; rv.stroke_w = dim_px(a);
                if (a.value_type == 0x01) {
                    auto r = arsc_.resolve(a.value_data);
                    if (r.found && r.is_color) { rv.stroke_color = r.color_argb; }
                }
            } else if (nm == "color" && n.name == "stroke") {
                rv.stroke_color = color_of(a, rep);
                rv.has_stroke = true;
            }
        }
        for (const auto& c : n.children) walk(c);
    };
    walk(ax.root());
}

// Resolve an attribute value: chase @refs via ARSC; framework refs recorded.
bool RealInflater::resolve_attr(const AxmlAttribute& a, ResolvedValue& out) const {
    if (a.value_type == 0x03 || a.value_type == 0x00) {  // string
        out.found = true;
        out.type = VAL_STRING;
        out.str = a.raw_value;
        return true;
    }
    if (a.value_type == 0x01) {  // REFERENCE
        uint8_t pkg = uint8_t((a.value_data >> 24) & 0xff);
        if (pkg == 0x01) {  // framework resource — not available (honest)
            out.found = false;
            return false;
        }
        out = arsc_.resolve(a.value_data);
        return out.found;
    }
    out.found = true;
    out.type = a.value_type;
    out.data = a.value_data;
    return true;
}

int RealInflater::dim_px(const AxmlAttribute& a) const {
    if (a.value_type == 0x05) {  // DIMENSION
        float v = ArscParser::complex_to_float(a.value_data);
        uint8_t unit = uint8_t(a.value_data & 0xf);
        switch (unit) {
            case 1: case 2: return int(std::lround(v * density_));  // dp/sp
            case 0: return int(std::lround(v));                     // px
            case 3: return int(std::lround(v * density_ * 72.f / 96.f));
            default: return int(std::lround(v * density_));
        }
    }
    if (a.value_type == 0x10 || a.value_type == 0x11) return int(a.value_data);
    if (a.value_type == 0x04) {  // FLOAT
        float f; std::memcpy(&f, &a.value_data, 4);
        return int(std::lround(f * density_));
    }
    return 0;
}

uint32_t RealInflater::color_of(const AxmlAttribute& a, InflateReport& rep) const {
    if (a.value_type >= 0x1c && a.value_type <= 0x1f)
        return ArscParser::color_from_data(a.value_type, a.value_data);
    if (a.value_type == 0x01) {
        auto r = arsc_.resolve(a.value_data);
        if (r.found && r.is_color) { rep.resolved_color_refs++; return r.color_argb; }
        if (r.found && r.type == VAL_STRING && !r.str.empty() && r.str[0] == '#') {
            uint32_t c = strtoul(r.str.c_str() + 1, nullptr, 16);
            if (r.str.size() <= 7) c |= 0xff000000u;
            rep.resolved_color_refs++;
            return c;
        }
        rep.unresolved_refs++;
        return 0;
    }
    if (!a.raw_value.empty() && a.raw_value[0] == '#') {
        uint32_t c = strtoul(a.raw_value.c_str() + 1, nullptr, 16);
        if (a.raw_value.size() <= 7) c |= 0xff000000u;
        return c;
    }
    return 0;
}

std::string RealInflater::drawable_path_for(const AxmlAttribute& a,
                                            InflateReport& rep) const {
    if (a.value_type != 0x01) return {};
    auto paths = arsc_.drawable_paths(a.value_data);
    // Prefer the highest-density variant (xxxhdpi > xxhdpi > ... > mdpi),
    // matching Android device scaling at our runtime density (>= 2.0).
    auto rank = [](const std::string& p) -> int {
        if (p.find("drawable-xxxhdpi") != std::string::npos ||
            p.find("mipmap-xxxhdpi") != std::string::npos) return 6;
        if (p.find("drawable-xxhdpi") != std::string::npos ||
            p.find("mipmap-xxhdpi") != std::string::npos) return 5;
        if (p.find("drawable-xhdpi") != std::string::npos ||
            p.find("mipmap-xhdpi") != std::string::npos) return 4;
        if (p.find("-hdpi") != std::string::npos) return 3;
        if (p.find("-mdpi") != std::string::npos) return 2;
        return 1;  // res/drawable/ or res/mipmap/ (unqualified)
    };
    std::string best;
    int best_rank = -1;
    for (const auto& p : paths) {
        if (!apk_.extract_entry_cached(p).empty() && rank(p) > best_rank) {
            best = p;
            best_rank = rank(p);
        }
    }
    if (!best.empty()) {
        rep.resolved_drawable_refs++;
        return best;
    }
    if (!paths.empty()) rep.unresolved_refs++;
    return {};
}

RealInflater::RView RealInflater::build(const AxmlNode& node, InflateReport& rep) {
    RView rv;
    rv.cls = node.name;
    rep.view_count++;
    rep.attr_count += int(node.attrs.size());
    if (is_view_group(rv.cls)) rep.view_group_count++;
    else if (rv.cls == "Button") rep.button_count++;
    else if (rv.cls == "ImageView" || rv.cls == "ImageButton") rep.image_view_count++;
    else if (rv.cls == "EditText") rep.edit_text_count++;
    else if (is_text_like(rv.cls)) rep.text_view_count++;
    else if (rv.cls != "View" && rv.cls != "merge") rep.custom_count++;

    for (const auto& a : node.attrs) {
        const std::string& n = a.name;
        if (n == "id") {
            rv.android_id = int(a.value_data);
        } else if (n == "layout_width") {
            rv.lp_w = (a.value_type == 0x10) ? int(a.value_data) : dim_px(a);
        } else if (n == "layout_height") {
            rv.lp_h = (a.value_type == 0x10) ? int(a.value_data) : dim_px(a);
        } else if (n == "layout_margin") {
            rv.ml = rv.mt = rv.mr = rv.mb = dim_px(a);
        } else if (n == "layout_marginLeft" || n == "layout_marginStart") {
            rv.ml = dim_px(a);
        } else if (n == "layout_marginTop") {
            rv.mt = dim_px(a);
        } else if (n == "layout_marginRight" || n == "layout_marginEnd") {
            rv.mr = dim_px(a);
        } else if (n == "layout_marginBottom") {
            rv.mb = dim_px(a);
        } else if (n == "padding") {
            rv.pl = rv.pt = rv.pr = rv.pb = dim_px(a);
        } else if (n == "paddingLeft") {
            rv.pl = dim_px(a);
        } else if (n == "paddingTop") {
            rv.pt = dim_px(a);
        } else if (n == "paddingRight") {
            rv.pr = dim_px(a);
        } else if (n == "paddingBottom") {
            rv.pb = dim_px(a);
        } else if (n == "orientation") {
            rv.orientation = int(a.value_data);
        } else if (n == "layout_weight") {
            if (a.value_type == 0x04) std::memcpy(&rv.weight, &a.value_data, 4);
            else rv.weight = float(a.value_data) / (1 << 20);
        } else if (n == "gravity") {
            rv.gravity = int(a.value_data);
        } else if (n == "layout_gravity") {
            rv.layout_gravity = int(a.value_data);
        } else if (n == "text") {
            ResolvedValue r;
            if (resolve_attr(a, r) && r.type == VAL_STRING) {
                rv.text = r.str;
                rep.resolved_string_refs++;
            }
        } else if (n == "hint") {
            ResolvedValue r;
            if (resolve_attr(a, r) && r.type == VAL_STRING) rv.hint = r.str;
        } else if (n == "textSize") {
            rv.text_size = float(dim_px(a));
        } else if (n == "textColor") {
            rv.text_color = color_of(a, rep);
            rv.text_color_set = true;
        } else if (n == "textStyle") {
            int v = int(a.value_data);
            rv.bold = (v & 1) != 0;
            rv.italic = (v & 2) != 0;
        } else if (n == "singleLine" || n == "maxLines") {
            rv.single_line = (a.value_data != 0) || n == "singleLine";
        } else if (n == "onClick") {
            rv.on_click = a.raw_value;
        } else if (n == "background") {
            // color ref / color literal / drawable ref
            if (a.value_type >= 0x1c) {
                rv.bg_color_set = true;
                rv.bg_color = color_of(a, rep);
            } else if (a.value_type == 0x01) {
                auto r = arsc_.resolve(a.value_data);
                if (r.found && r.is_color) {
                    rv.bg_color_set = true;
                    rv.bg_color = r.color_argb;
                    rep.resolved_color_refs++;
                } else {
                    std::string p = drawable_path_for(a, rep);
                    if (!p.empty()) {
                        if (p.size() > 4 && p.substr(p.size() - 4) == ".xml")
                            load_shape_drawable(p, rv, rep);
                        else
                            rv.bg_drawable = p;
                    }
                }
            } else if (!a.raw_value.empty() && a.raw_value[0] == '#') {
                rv.bg_color_set = true;
                rv.bg_color = color_of(a, rep);
            }
        } else if (n == "src") {
            std::string p = drawable_path_for(a, rep);
            if (!p.empty()) rv.src_path = p;
        } else if (n == "clickable") {
            rv.clickable = a.value_data != 0;
        } else if (n == "visibility") {
            rv.visibility = int(a.value_data);
        } else if (n == "layout_below") {
            rv.rel_below = int(a.value_data);
        } else if (n == "layout_above") {
            rv.rel_above = int(a.value_data);
        } else if (n == "layout_toLeftOf" || n == "layout_toStartOf") {
            rv.rel_leftof = int(a.value_data);
        } else if (n == "layout_toRightOf" || n == "layout_toEndOf") {
            rv.rel_rightof = int(a.value_data);
        } else if (n == "layout_alignLeft" || n == "layout_alignStart") {
            rv.rel_align_left = int(a.value_data);
        } else if (n == "layout_alignRight" || n == "layout_alignEnd") {
            rv.rel_align_right = int(a.value_data);
        } else if (n == "layout_alignTop") {
            rv.rel_align_top = int(a.value_data);
        } else if (n == "layout_alignBottom") {
            rv.rel_align_bottom = int(a.value_data);
        } else if (n == "layout_alignParentTop") {
            rv.rel_parent_top = a.value_data != 0;
        } else if (n == "layout_alignParentBottom") {
            rv.rel_parent_bottom = a.value_data != 0;
        } else if (n == "layout_alignParentLeft" || n == "layout_alignParentStart") {
            rv.rel_parent_left = a.value_data != 0;
        } else if (n == "layout_alignParentRight" || n == "layout_alignParentEnd") {
            rv.rel_parent_right = a.value_data != 0;
        } else if (n == "layout_centerHorizontal") {
            rv.rel_center_h = a.value_data != 0;
        } else if (n == "layout_centerVertical") {
            rv.rel_center_v = a.value_data != 0;
        } else if (n == "layout_centerInParent") {
            rv.rel_center = a.value_data != 0;
        }
    }
    for (const auto& c : node.children) rv.children.push_back(build(c, rep));
    return rv;
}

void RealInflater::convert_and_attach(const RView& rv, uint32_t parent_shadow_id,
                                      ViewShadow* views, uint32_t activity_object_id,
                                      InflateReport& rep) {
    std::string cd = rv.cls.find(';') == std::string::npos
                         ? "Landroid/widget/" + rv.cls + ";"
                         : rv.cls;
    if (rv.cls.find('.') != std::string::npos && rv.cls.find(';') == std::string::npos) {
        cd = "L" + rv.cls + ";";  // custom view FQCN
    }
    uint32_t vid = views->create_view(cd);
    if (parent_shadow_id != 0) views->add_child(parent_shadow_id, vid);
    if (ViewShadow::ViewNode* n = views->find_node(vid)) {
        n->android_view_id = rv.android_id;
        n->lp_width = rv.lp_w;
        n->lp_height = rv.lp_h;
        n->lp_margin_left = rv.ml;
        n->lp_margin_top = rv.mt;
        n->lp_margin_right = rv.mr;
        n->lp_margin_bottom = rv.mb;
        n->padding_l = rv.pl;
        n->padding_t = rv.pt;
        n->padding_r = rv.pr;
        n->padding_b = rv.pb;
        n->orientation = rv.orientation;
        n->layout_weight = rv.weight;
        n->text = rv.text;
        n->hint = rv.hint;
        n->text_size_px = rv.text_size;
        if (rv.text_color_set) n->text_color = rv.text_color;
        n->text_style_bold = rv.bold;
        n->text_style_italic = rv.italic;
        n->single_line = rv.single_line;
        n->on_click_method = rv.on_click;
        n->clickable = rv.clickable || !rv.on_click.empty();
        n->visibility = rv.visibility;
        n->context_object_id = activity_object_id;
        n->gravity = rv.gravity;
        n->layout_gravity = rv.layout_gravity;
        if (rv.text_gravity >= 0) n->text_gravity = rv.text_gravity;
        n->bg_color = rv.bg_color;
        n->bg_drawable_path = rv.bg_drawable;
        n->bg_shape_has_solid = rv.bg_shape_has_solid;
        n->bg_shape_solid = rv.bg_shape_solid;
        n->bg_shape_has_gradient = rv.bg_shape_has_gradient;
        n->bg_shape_grad_start = rv.grad_start;
        n->bg_shape_grad_end = rv.grad_end;
        n->bg_shape_grad_angle = rv.grad_angle;
        n->bg_shape_corner_radius = rv.corner_radius;
        n->bg_shape_has_stroke = rv.has_stroke;
        n->bg_shape_stroke_color = rv.stroke_color;
        n->bg_shape_stroke_width = rv.stroke_w;
        n->rel_below = rv.rel_below;
        n->rel_above = rv.rel_above;
        n->rel_leftof = rv.rel_leftof;
        n->rel_rightof = rv.rel_rightof;
        n->rel_align_left = rv.rel_align_left;
        n->rel_align_right = rv.rel_align_right;
        n->rel_align_top = rv.rel_align_top;
        n->rel_align_bottom = rv.rel_align_bottom;
        n->rel_parent_top = rv.rel_parent_top;
        n->rel_parent_bottom = rv.rel_parent_bottom;
        n->rel_parent_left = rv.rel_parent_left;
        n->rel_parent_right = rv.rel_parent_right;
        n->rel_center_h = rv.rel_center_h;
        n->rel_center_v = rv.rel_center_v;
        n->rel_center = rv.rel_center;
        if (!rv.src_path.empty()) {
            n->image_drawable_path = rv.src_path;
        }
    }
    if (rep.root_view_id == 0) rep.root_view_id = vid;
    for (const auto& c : rv.children)
        convert_and_attach(c, vid, views, activity_object_id, rep);
}

InflateReport RealInflater::inflate_into_shadow(uint32_t layout_res_id,
                                                ViewShadow* views,
                                                uint32_t activity_object_id) {
    InflateReport rep;
    rep.layout_res_id = layout_res_id;
    // find real path (config variants, obfuscated names)
    auto paths = arsc_.drawable_paths(layout_res_id);
    std::string path;
    for (const auto& p : paths) {
        if (!apk_.extract_entry_cached(p).empty()) { path = p; break; }
    }
    if (path.empty()) {
        std::string name = arsc_.entry_name(layout_res_id);
        if (!name.empty()) path = "res/layout/" + name + ".xml";
    }
    if (path.empty()) {
        rep.error = "layout path not found for id 0x" +
                    ([](uint32_t v) {
                        char b[16]; snprintf(b, sizeof b, "%08x", v); return std::string(b);
                    })(layout_res_id);
        return rep;
    }
    rep.layout_path = path;
    auto xml = apk_.extract_entry_cached(path);
    if (xml.empty()) { rep.error = "layout xml empty: " + path; return rep; }
    AxmlParser ax;
    if (!ax.parse(xml.data(), xml.size())) {
        rep.error = "AXML parse failed: " + ax.error();
        return rep;
    }
    RView root = build(ax.root(), rep);
    convert_and_attach(root, 0, views, activity_object_id, rep);
    rep.ok = rep.root_view_id != 0;
    if (!rep.ok) rep.error = "shadow tree creation failed";
    return rep;
}

InflateReport RealInflater::inflate_into_shadow(const std::string& type,
                                                const std::string& name,
                                                ViewShadow* views,
                                                uint32_t activity_object_id) {
    uint32_t id = arsc_.find_id(type, name);
    if (!id) {
        InflateReport rep;
        rep.error = "resource not found: " + type + "/" + name;
        return rep;
    }
    return inflate_into_shadow(id, views, activity_object_id);
}

}  // namespace resources
}  // namespace miniandroid
