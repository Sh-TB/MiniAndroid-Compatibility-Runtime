/*
 * UNIFIED_007 — Real Layout Inflater implementation.
 */
#include "layout_inflater.h"
#include "../fonts/text_shaper.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cctype>
#include <functional>
#include <iostream>

namespace miniandroid {
namespace resources {

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
static inline uint32_t li_parse_hex_color(const std::string& s) {
    // formats: #AARRGGBB, #RRGGBB, #ARGB, #RGB
    std::string h = s;
    if (h.empty() || h[0] != '#') return 0;
    h = h.substr(1);
    auto hexval = [](char c) -> uint32_t {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return 0;
    };
    if (h.size() == 6) {
        return 0xFF000000u | (hexval(h[0]) << 20) | (hexval(h[1]) << 16) |
               (hexval(h[2]) << 12) | (hexval(h[3]) << 8) |
               (hexval(h[4]) << 4) | hexval(h[5]);
    }
    if (h.size() == 8) {
        return (hexval(h[0]) << 28) | (hexval(h[1]) << 24) | (hexval(h[2]) << 20) |
               (hexval(h[3]) << 16) | (hexval(h[4]) << 12) | (hexval(h[5]) << 8) |
               (hexval(h[6]) << 4) | hexval(h[7]);
    }
    if (h.size() == 3) {
        return 0xFF000000u | (hexval(h[0]) << 20) | (hexval(h[0]) << 16) |
               (hexval(h[1]) << 12) | (hexval(h[1]) << 8) |
               (hexval(h[2]) << 4) | hexval(h[2]);
    }
    if (h.size() == 4) {
        return (hexval(h[0]) << 28) | (hexval(h[0]) << 24) | (hexval(h[1]) << 20) |
               (hexval(h[1]) << 16) | (hexval(h[2]) << 12) | (hexval(h[2]) << 8) |
               (hexval(h[3]) << 4) | hexval(h[3]);
    }
    return 0;
}

LayoutInflater::ParsedRef LayoutInflater::parse_ref(const std::string& v) {
    ParsedRef out;
    if (v.empty()) return out;
    if (v[0] == '@') {
        out.is_ref = true;
        std::string body = v.substr(1);
        if (body.compare(0, 8, "android:") == 0) body = body.substr(8);
        size_t slash = body.find('/');
        if (slash != std::string::npos) {
            std::string kind = body.substr(0, slash);
            out.name = body.substr(slash + 1);
            if (kind == "string") out.kind = RefKind::STRING;
            else if (kind == "color" || kind == "colors") out.kind = RefKind::COLOR;
            else if (kind == "dimen") out.kind = RefKind::DIMEN;
            else if (kind == "drawable" || kind == "mipmap") out.kind = RefKind::DRAWABLE;
            else if (kind == "layout") out.kind = RefKind::LAYOUT;
            else if (kind == "style") out.kind = RefKind::STYLE;
            else if (kind == "id") out.kind = RefKind::ID;
            else if (kind == "bool") out.kind = RefKind::BOOL;
            else if (kind == "integer") out.kind = RefKind::INTEGER;
        } else {
            out.name = body;
        }
        // "+id" form
        if (out.name.compare(0, 1, "+") == 0) out.name = out.name.substr(1);
    } else {
        out.literal = v;
    }
    return out;
}

uint32_t LayoutInflater::parse_hex_color(const std::string& s) {
    return li_parse_hex_color(s);
}

int LayoutInflater::gravity_bits(const std::string& s) {
    int g = 0;
    auto has = [&](const char* k) { return s.find(k) != std::string::npos; };
    // AOSP Gravity: LEFT=3 RIGHT=5 CENTER_HORIZONTAL=1 START=8388611 END=8388613
    if (has("center")) g |= 0x11;
    if (has("center_horizontal")) g = (g & ~0x7) | 0x1;
    if (has("center_vertical")) g = (g & ~0x70) | 0x10;
    if (has("left") || has("start")) g |= 0x3;
    if (has("right") || has("end")) g |= 0x5;
    if (has("top")) g |= 0x30;
    if (has("bottom")) g |= 0x50;
    if (has("fill")) g |= 0x77;
    return g;
}

std::string LayoutInflater::class_to_descriptor(const std::string& xml_name) {
    static const std::unordered_map<std::string, std::string> KNOWN = {
        {"TextView", "Landroid/widget/TextView;"},
        {"Button", "Landroid/widget/Button;"},
        {"ImageButton", "Landroid/widget/ImageButton;"},
        {"ImageView", "Landroid/widget/ImageView;"},
        {"EditText", "Landroid/widget/EditText;"},
        {"CheckBox", "Landroid/widget/CheckBox;"},
        {"RadioButton", "Landroid/widget/RadioButton;"},
        {"Switch", "Landroid/widget/Switch;"},
        {"ToggleButton", "Landroid/widget/ToggleButton;"},
        {"ProgressBar", "Landroid/widget/ProgressBar;"},
        {"SeekBar", "Landroid/widget/SeekBar;"},
        {"Spinner", "Landroid/widget/Spinner;"},
        {"ListView", "Landroid/widget/ListView;"},
        {"GridView", "Landroid/widget/GridView;"},
        {"NumberPicker", "Landroid/widget/NumberPicker;"},
        {"TimePicker", "Landroid/widget/TimePicker;"},
        {"DatePicker", "Landroid/widget/DatePicker;"},
        {"LinearLayout", "Landroid/widget/LinearLayout;"},
        {"FrameLayout", "Landroid/widget/FrameLayout;"},
        {"RelativeLayout", "Landroid/widget/RelativeLayout;"},
        {"AbsoluteLayout", "Landroid/widget/AbsoluteLayout;"},
        {"TableLayout", "Landroid/widget/TableLayout;"},
        {"TableRow", "Landroid/widget/TableRow;"},
        {"GridLayout", "Landroid/widget/GridLayout;"},
        {"ScrollView", "Landroid/widget/ScrollView;"},
        {"HorizontalScrollView", "Landroid/widget/HorizontalScrollView;"},
        {"View", "Landroid/view/View;"},
        {"ViewGroup", "Landroid/view/ViewGroup;"},
        {"ViewStub", "Landroid/view/ViewStub;"},
        {"Space", "Landroid/widget/Space;"},
        {"TextureView", "Landroid/view/TextureView;"},
        {"SurfaceView", "Landroid/view/SurfaceView;"},
        {"VideoView", "Landroid/widget/VideoView;"},
        {"WebView", "Landroid/webkit/WebView;"},
        {"Toolbar", "Landroid/widget/Toolbar;"},
        {"ActionBar", "Landroid/app/ActionBar;"},
        {"TabHost", "Landroid/widget/TabHost;"},
        {"TabWidget", "Landroid/widget/TabWidget;"},
        {"GestureOverlayView", "Landroid/gesture/GestureOverlayView;"},
        {"PagerTitleStrip", "Landroid/support/v4/view/PagerTitleStrip;"},
        {"ViewPager", "Landroid/support/v4/view/ViewPager;"},
        // appcompat / material-common (map to closest real widget)
        {"androidx.appcompat.widget.AppCompatTextView", "Landroid/widget/TextView;"},
        {"androidx.appcompat.widget.AppCompatButton", "Landroid/widget/Button;"},
        {"androidx.appcompat.widget.AppCompatEditText", "Landroid/widget/EditText;"},
        {"androidx.appcompat.widget.AppCompatImageView", "Landroid/widget/ImageView;"},
        {"androidx.appcompat.widget.AppCompatCheckBox", "Landroid/widget/CheckBox;"},
        {"androidx.appcompat.widget.AppCompatRadioButton", "Landroid/widget/RadioButton;"},
        {"androidx.appcompat.widget.AppCompatSpinner", "Landroid/widget/Spinner;"},
        {"androidx.appcompat.widget.Toolbar", "Landroid/widget/Toolbar;"},
        {"com.google.android.material.button.MaterialButton", "Landroid/widget/Button;"},
        {"com.google.android.material.textfield.MaterialAutoCompleteTextView", "Landroid/widget/EditText;"},
        {"com.google.android.material.textfield.TextInputEditText", "Landroid/widget/EditText;"},
        {"com.google.android.material.floatingactionbutton.FloatingActionButton", "Landroid/widget/ImageView;"},
    };
    auto it = KNOWN.find(xml_name);
    if (it != KNOWN.end()) return it->second;
    if (xml_name.find('.') != std::string::npos) {
        // custom view: fully-qualified
        return "L" + xml_name + ";";
    }
    // unknown short name — treat as generic View (evidence warning added by caller)
    return "Landroid/view/View;";
}

LayoutInflater::LayoutInflater(ArscParser& arsc, apk::ApkParser& apk, const std::string& apk_path,
                               const DeviceMetrics& metrics)
    : arsc_(arsc), apk_(apk), apk_path_(apk_path), metrics_(metrics) {
    auto info = apk.parse(apk_path);
    if (info.is_valid) apk_entries_ = info.all_entries;
}

std::string LayoutInflater::find_apk_file(const std::string& type, const std::string& name) {
    // exact match: res/<type>*/<name>.<ext>
    std::string best;
    for (const auto& e : apk_entries_) {
        const std::string prefix = "res/";
        if (e.compare(0, prefix.size(), prefix) != 0) continue;
        size_t s2 = e.find('/', prefix.size());
        if (s2 == std::string::npos) continue;
        std::string dir = e.substr(prefix.size(), s2 - prefix.size());
        std::string base_dir = dir.substr(0, dir.find('-'));
        if (base_dir != type) continue;
        std::string fname = e.substr(s2 + 1);
        size_t dot = fname.find('.');
        std::string stem = dot == std::string::npos ? fname : fname.substr(0, dot);
        if (stem == name) {
            if (best.empty() || dir.find('-') == std::string::npos || dir.size() < best.size())
                best = e;
        }
    }
    return best;
}

std::string LayoutInflater::drawable_path_for_name(const std::string& name) {
    std::string p = find_apk_file("drawable", name);
    if (p.empty()) p = find_apk_file("mipmap", name);
    if (p.empty()) p = find_apk_file("raw", name);
    return p;
}

std::string LayoutInflater::drawable_path_for_resid(uint32_t resid) {
    auto r = arsc_.resolve(resid);
    if (!r) return "";
    return drawable_path_for_name(r->name);
}

// ---------------------------------------------------------------------------
// attribute value resolution
// ---------------------------------------------------------------------------
std::string LayoutInflater::resolve_string_ref(const std::string& name, InflateStats& stats) {
    auto id = arsc_.find_id("", "string", name);
    if (!id) { stats.unresolved_refs++; stats.warnings.push_back("string not found: " + name); return ""; }
    auto s = arsc_.resolve_string(*id);
    if (s) { stats.strings_resolved++; return *s; }
    stats.unresolved_refs++;
    return "";
}

uint32_t LayoutInflater::resolve_color(const std::string& v, InflateStats& stats) {
    if (v.empty()) return 0;
    auto ref = parse_ref(v);
    if (!ref.is_ref) {
        if (v[0] == '#') return li_parse_hex_color(v);
        return 0;
    }
    if (ref.kind == RefKind::COLOR) {
        auto id = arsc_.find_id("", "color", ref.name);
        if (!id) { stats.unresolved_refs++; return 0; }
        auto val = arsc_.resolve_value(*id);
        if (val && (val->is_color() || val->is_int())) {
            stats.colors_resolved++;
            return val->data;
        }
        stats.unresolved_refs++;
    }
    return 0;
}

int LayoutInflater::resolve_dimen_px(const std::string& v, InflateStats& stats) {
    auto ref = parse_ref(v);
    if (ref.is_ref && ref.kind == RefKind::DIMEN) {
        auto id = arsc_.find_id("", "dimen", ref.name);
        if (!id) { stats.unresolved_refs++; return 0; }
        auto val = arsc_.resolve_value(*id);
        if (val && val->is_dimension()) {
            stats.dimens_resolved++;
            float px;
            switch (val->dim_unit) {
                case DIM_DIP: px = val->dim_value * metrics_.density; break;
                case DIM_SP:  px = val->dim_value * metrics_.density * metrics_.scale_fonts; break;
                default:      px = val->dim_value; break;  // PX/PT/IN/MM treated as px
            }
            return (int)std::lround(px);
        }
        stats.unresolved_refs++;
        return 0;
    }
    if (!ref.is_ref) {
        // raw string form "12dp" / "14sp" / "8px"
        std::string s = v;
        float mult = metrics_.density;
        if (s.size() > 2) {
            std::string suf = s.substr(s.size() - 2);
            float val = (float)atof(s.c_str());
            if (suf == "dp" || suf == "dip") return (int)std::lround(val * mult);
            if (suf == "sp") return (int)std::lround(val * mult * metrics_.scale_fonts);
            if (suf == "px") return (int)std::lround(val);
            if (s.back() == 'p' || isdigit((unsigned char)s.back())) {
                if (suf == "in") return (int)std::lround(val * 160 * mult);
            }
        }
    }
    return 0;
}

int LayoutInflater::parse_dim_attr(const AxmlAttribute* attr, InflateStats& stats) {
    if (!attr) return 0;
    if (attr->value.is_dimension()) {
        float px;
        switch (attr->value.dim_unit) {
            case DIM_DIP: px = attr->value.dim_value * metrics_.density; break;
            case DIM_SP:  px = attr->value.dim_value * metrics_.density * metrics_.scale_fonts; break;
            default:      px = attr->value.dim_value; break;
        }
        stats.dimens_resolved++;
        return (int)std::lround(px);
    }
    if (attr->value.is_string()) return resolve_dimen_px(attr->value.string_value, stats);
    if (!attr->raw_value.empty()) return resolve_dimen_px(attr->raw_value, stats);
    return 0;
}

uint32_t LayoutInflater::parse_color_attr(const AxmlAttribute* attr, InflateStats& stats) {
    if (!attr) return 0;
    if (attr->value.is_color() || attr->value.is_int()) {
        stats.colors_resolved++;
        return attr->value.data;
    }
    if (attr->value.is_reference()) {
        auto val = arsc_.resolve_value(attr->value.ref_id);
        if (val && (val->is_color() || val->is_int())) {
            stats.colors_resolved++;
            return val->data;
        }
        stats.unresolved_refs++;
        return 0;
    }
    if (!attr->raw_value.empty()) return resolve_color(attr->raw_value, stats);
    if (attr->value.is_string()) return resolve_color(attr->value.string_value, stats);
    return 0;
}

int LayoutInflater::resolve_size_or_match(const AxmlAttribute* attr, InflateStats& stats) {
    if (!attr) return -2;
    // aapt compiles "match_parent"/"fill_parent"/"wrap_content" as INT_DEC
    // (-1 / -2) — handle BEFORE the string checks.
    if (attr->value.is_int() || attr->value.type == DataType::INT_DEC ||
        attr->value.type == DataType::INT_HEX) {
        int v = (int)attr->value.data;
        if (v == -1) return -1;
        if (v == -2) return -2;
        return v;
    }
    if (attr->value.is_dimension()) return parse_dim_attr(attr, stats);
    std::string s = !attr->raw_value.empty() ? attr->raw_value : attr->value.string_value;
    if (s == "match_parent" || s == "fill_parent") return -1;
    if (s == "wrap_content" || s.empty() || s == "@null") return -2;
    if (s[0] == '@') {
        // dimen ref
        int px = resolve_dimen_px(s, stats);
        return px;
    }
    if (s[0] == '-') {
        if (s == "-1") return -1;
        if (s == "-2") return -2;
    }
    if (isdigit((unsigned char)s[0])) return resolve_dimen_px(s, stats);
    return -2;
}

uint32_t LayoutInflater::resolve_id_attr(const AxmlAttribute* attr, InflateStats& stats) {
    if (!attr) return 0;
    // aapt compiles @id/@+id as a typed REFERENCE — the id is in the data word
    if (attr->value.is_reference()) return attr->value.ref_id;
    std::string s = !attr->raw_value.empty() ? attr->raw_value : attr->value.string_value;
    if (s.empty()) return 0;
    if (s.compare(0, 9, "@android:") == 0) {
        // @android:id/list → well-known system ids
        auto ref = parse_ref(s);
        // system id from data field if typed reference
        if (attr->value.is_reference()) return attr->value.ref_id;
        return 0;
    }
    if (s[0] == '@') {
        auto ref = parse_ref(s);
        if (ref.kind == RefKind::ID || !ref.name.empty()) {
            auto id = arsc_.find_id("", "id", ref.name);
            if (id) { stats.ids_resolved++; return *id; }
            stats.unresolved_refs++;
        }
        return 0;
    }
    return 0;
}

// ---------------------------------------------------------------------------
// style application (complex entries from ARSC)
// ---------------------------------------------------------------------------
void LayoutInflater::apply_style(framework::ViewShadow::ViewNode& node, Attrs& a,
                                 uint32_t style_resid, InflateStats& stats) {
    auto r = arsc_.resolve(style_resid);
    if (!r) return;
    const ArscEntry* e = r->best();
    if (!e || !e->is_complex) return;
    // name of style for evidence
    a.style_name = r->name;
    for (const auto& item : e->complex_items) {
        if (item.is_string()) {
            // textSize etc are not strings; skip
            continue;
        }
        if (item.is_dimension()) {
            // could be textSize/textSize from style — apply to textSize if unset
            if (a.text_size_px == 0 && !a.from_style_text_size) {
                float px;
                switch (item.dim_unit) {
                    case DIM_DIP: px = item.dim_value * metrics_.density; break;
                    case DIM_SP:  px = item.dim_value * metrics_.density * metrics_.scale_fonts; break;
                    default:      px = item.dim_value; break;
                }
                a.style_text_size_px = px;
                a.from_style_text_size = true;
                stats.styles_applied++;
            }
        } else if (item.is_color()) {
            if (a.text_color == 0) a.style_text_color = item.data;
            stats.styles_applied++;
        }
    }
}

void LayoutInflater::apply_style_by_name(framework::ViewShadow::ViewNode& node, Attrs& a,
                                         const std::string& style_name, InflateStats& stats) {
    auto id = arsc_.find_id("", "style", style_name);
    if (id) apply_style(node, a, *id, stats);
}

// ---------------------------------------------------------------------------
// per-element inflation
// ---------------------------------------------------------------------------
uint32_t LayoutInflater::inflate_element(framework::ViewShadow* views, const AxmlElement& el,
                                         uint32_t parent_view_id, InflateStats& stats) {
    stats.elements_total++;

    // <include layout="@layout/other"/>
    if (el.name == "include") {
        const AxmlAttribute* lay = el.attr("layout");
        if (lay) {
            auto ref = parse_ref(!lay->raw_value.empty() ? lay->raw_value : lay->value.string_value);
            if (ref.kind == RefKind::LAYOUT) {
                auto id = arsc_.find_id("", "layout", ref.name);
                if (id) {
                    auto path = arsc_.apk_path_for(*id, apk_entries_);
                    if (!path) path = find_apk_file("layout", ref.name);
                    if (path) {
                        std::vector<uint8_t> xml = apk_.extract_entry_cached(*path);
                        if (xml.empty()) xml = apk_.extract_entry(apk_path_, *path);
                        AxmlParser sub;
                        if (sub.parse(xml)) {
                            stats.includes_expanded++;
                            uint32_t created = 0;
                            for (const auto& child : sub.root().children)
                                created = inflate_element(views, child, parent_view_id, stats);
                            return created;
                        }
                    }
                }
            }
        }
        stats.warnings.push_back("include unresolved");
        return 0;
    }

    // <requestFocus/> etc — no view
    if (el.name == "requestFocus" || el.name == "requestLayout" || el.name == "tag") return 0;

    std::string class_desc;
    const AxmlAttribute* class_attr = el.attr("class");
    if (class_attr) class_desc = class_to_descriptor(!class_attr->raw_value.empty()
                                                     ? class_attr->raw_value
                                                     : class_attr->value.string_value);
    else class_desc = class_to_descriptor(el.name);

    // <merge> → inflate children into parent directly
    if (el.name == "merge") {
        uint32_t last = parent_view_id;
        for (const auto& child : el.children)
            last = inflate_element(views, child, parent_view_id, stats);
        return last;
    }

    uint32_t view_id = views->create_view(class_desc);
    auto* node = views->find_node(view_id);
    if (!node) return 0;
    stats.views_created++;
    if (parent_view_id) views->add_child(parent_view_id, view_id);

    Attrs a;
    apply_element_attrs(*node, el, a, stats);

    // android:id
    const AxmlAttribute* ida = el.attr("id");
    if (ida) {
        uint32_t aid = resolve_id_attr(ida, stats);
        if (aid) node->android_view_id = (int32_t)aid;
        if (!ida->raw_value.empty()) {
            auto ref = parse_ref(ida->raw_value);
            node->android_id_name = ref.name;
        }
        if (node->android_id_name.empty() && aid) {
            // aapt strips the raw string for compiled @id/name references —
            // resolve the name through resources.arsc (id → key name) so
            // RelativeLayout sibling rules can bind by name.
            if (id_names_.empty()) {
                for (auto& [rid, nm] : arsc_.list_type("", "id"))
                    id_names_[rid] = nm;
            }
            auto it = id_names_.find(aid);
            if (it != id_names_.end()) node->android_id_name = it->second;
        }
    }

    // children
    uint32_t last_child = 0;
    for (const auto& child : el.children) {
        uint32_t cid = inflate_element(views, child, view_id, stats);
        if (cid) last_child = cid;
    }
    (void)last_child;
    return view_id;
}

void LayoutInflater::apply_element_attrs(framework::ViewShadow::ViewNode& node,
                                         const AxmlElement& el, Attrs& a, InflateStats& stats) {
    auto raw_of = [&](const AxmlAttribute* at) -> std::string {
        if (!at) return "";
        return !at->raw_value.empty() ? at->raw_value : at->value.string_value;
    };

    // style attr (may be a style name literal "@style/Foo" or reference)
    const AxmlAttribute* style_attr = el.attr("style", "");
    if (style_attr) {
        std::string sv = raw_of(style_attr);
        if (!sv.empty()) {
            auto ref = parse_ref(sv);
            if (ref.kind == RefKind::STYLE) apply_style_by_name(node, a, ref.name, stats);
            else if (sv[0] == '@') {
                auto id = arsc_.find_id("", "style", sv.substr(1));
                if (id) apply_style(node, a, *id, stats);
            }
        }
    }

    for (const auto& at : el.attributes) {
        if (at.ns != "android" && at.ns != "app") continue;
        const std::string& n = at.name;
        const std::string raw = raw_of(&at);

        if (n == "layout_width") a.layout_width = resolve_size_or_match(&at, stats), a.width_set = true;
        else if (n == "layout_height") a.layout_height = resolve_size_or_match(&at, stats), a.height_set = true;
        else if (n == "layout_margin") { a.ml = a.mt = a.mr = a.mb = parse_dim_attr(&at, stats); }
        else if (n == "layout_marginLeft") a.ml = parse_dim_attr(&at, stats);
        else if (n == "layout_marginTop") a.mt = parse_dim_attr(&at, stats);
        else if (n == "layout_marginRight") a.mr = parse_dim_attr(&at, stats);
        else if (n == "layout_marginBottom") a.mb = parse_dim_attr(&at, stats);
        else if (n == "padding") a.padding_all = parse_dim_attr(&at, stats);
        else if (n == "paddingLeft") a.pl = parse_dim_attr(&at, stats);
        else if (n == "paddingTop") a.pt = parse_dim_attr(&at, stats);
        else if (n == "paddingRight") a.pr = parse_dim_attr(&at, stats);
        else if (n == "paddingBottom") a.pb = parse_dim_attr(&at, stats);
        else if (n == "orientation") {
            a.orientation = (raw == "horizontal") ? 0 : 1;
            if (at.value.is_int()) a.orientation = (int)at.value.data;
        }
        else if (n == "gravity") {
            if (at.value.is_int()) a.gravity = (int)at.value.data;
            else a.gravity = gravity_bits(raw);
        }
        else if (n == "layout_gravity") {
            if (at.value.is_int()) a.layout_gravity = (int)at.value.data;
            else a.layout_gravity = gravity_bits(raw);
        }
        else if (n == "layout_weight") {
            if (at.value.type == DataType::FLOAT) {
                // float bits
                float f; memcpy(&f, &at.value.data, 4);
                a.layout_weight = (int)std::lround(f * 1000.0f);
                a.weight_sum_valid = false;
            } else if (at.value.is_dimension() || at.value.is_int()) {
                a.layout_weight = (int)at.value.data;
            } else a.layout_weight = (int)(atof(raw.c_str()) * 1000.0f);
            if (a.layout_weight == 0 && raw == "1") a.layout_weight = 1000;
        }
        else if (n == "weightSum") a.weight_sum = (float)atof(raw.c_str()), a.weight_sum_valid = true;
        else if (n == "text") {
            if (at.value.is_reference()) {
                auto val = arsc_.resolve_value(at.value.ref_id);
                if (val && val->is_string()) { a.text = val->string_value; stats.strings_resolved++; }
                else stats.unresolved_refs++;
            } else if (at.value.is_string()) {
                if (!raw.empty() && raw[0] == '@') a.text = resolve_string_ref(parse_ref(raw).name, stats);
                else a.text = raw;
            } else if (!raw.empty()) {
                if (raw[0] == '@') a.text = resolve_string_ref(parse_ref(raw).name, stats);
                else a.text = raw;
            }
        }
        else if (n == "hint") {
            if (at.value.is_reference()) {
                auto val = arsc_.resolve_value(at.value.ref_id);
                if (val && val->is_string()) { a.hint = val->string_value; stats.strings_resolved++; }
            } else a.hint = raw;
        }
        else if (n == "textSize") {
            if (at.value.is_dimension()) a.text_size_px = parse_dim_attr(&at, stats);
            else a.text_size_px = (float)resolve_dimen_px(raw, stats);
            node.text_size_sp = a.text_size_px / metrics_.density;
        }
        else if (n == "textColor") a.text_color = parse_color_attr(&at, stats);
        else if (n == "fontFamily") {
            // G32: AOSP TextView law — fontFamily names a system family
            // (fonts.xml) or an app font; arrives as a raw AXML string.
            a.font_family = raw;
        }
        else if (n == "textAppearance") {
            // G46: AOSP TextView law (TextView.java@android-14.0.0_r50
            // applyTextAppearance L4435+): the referenced framework style's
            // textSize applies UNLESS the view sets an explicit textSize
            // (view attrs are read after the appearance → they win).
            // Framework style id law (core/res/res/values/styles.xml
            // @android-14.0.0_r50 L862-864):
            //   <style name="TextAppearance.Large"> <item name="textSize">22sp</item>
            // = android:style 0x01030042 (verified from the EXT-01 AXML:
            //   textAppearance data=0x01030042).
            uint32_t sid = at.value.is_reference() ? at.value.ref_id : 0;
            if (sid == 0x01030042) {
                a.appearance_text_size_sp = 22.0f;
                a.appearance_resolved = true;
            } else if (sid != 0) {
                stats.unresolved_refs++;
                stats.warnings.push_back("framework TextAppearance 0x" + [&]{
                    char b[16]; snprintf(b, sizeof b, "%x", sid);
                    return std::string(b); }() + " not in the verified law table");
            }
        }
        else if (n == "textStyle") {
            if (raw.find("bold") != std::string::npos) { a.text_style |= 1; }
            if (raw.find("italic") != std::string::npos) { a.text_style |= 2; }
        }
        else if (n == "background") {
            if (at.value.is_reference()) {
                std::string p = drawable_path_for_resid(at.value.ref_id);
                if (!p.empty()) a.bg_drawable = p;
                else {
                    auto val = arsc_.resolve_value(at.value.ref_id);
                    if (val && (val->is_color() || val->is_int())) a.bg_color = val->data;
                }
            } else if (!raw.empty() && raw[0] == '#') {
                a.bg_color = li_parse_hex_color(raw);
            } else if (!raw.empty() && raw[0] == '@') {
                auto ref = parse_ref(raw);
                if (ref.kind == RefKind::DRAWABLE) {
                    std::string p = drawable_path_for_name(ref.name);
                    if (!p.empty()) a.bg_drawable = p;
                } else if (ref.kind == RefKind::COLOR) {
                    a.bg_color = resolve_color(raw, stats);
                }
            }
        }
        else if (n == "src" || n == "srcCompat") {
            if (at.value.is_reference()) {
                std::string p = drawable_path_for_resid(at.value.ref_id);
                if (!p.empty()) a.src_drawable = p;
            } else if (!raw.empty() && raw[0] == '@') {
                auto ref = parse_ref(raw);
                if (ref.kind == RefKind::DRAWABLE) a.src_drawable = drawable_path_for_name(ref.name);
            }
        }
        else if (n == "onClick") a.onClick = raw;
        else if (n == "visibility") {
            if (at.value.is_int()) a.visibility = (int)at.value.data;
            else a.visibility = raw == "invisible" ? 4 : raw == "gone" ? 8 : 0;
        }
        else if (n == "clickable") a.clickable = (raw == "true") || at.value.is_reference();
        else if (n == "enabled") node.enabled = raw != "false";
        else if (n == "lines") a.num_lines = atoi(raw.c_str());
        else if (n == "singleLine") a.single_line = raw == "true";
        else if (n == "elevation") a.elevation_px = parse_dim_attr(&at, stats);
        // layout_* relative positioning params (RelativeLayout) — recorded, best-effort
        else if (n == "layout_alignParentBottom") { if (raw == "true") a.layout_gravity |= 0x50; }
        else if (n == "layout_alignParentTop") { if (raw == "true") a.layout_gravity |= 0x30; }
        else if (n == "layout_centerHorizontal") { if (raw == "true") a.layout_gravity |= 0x1; }
        else if (n == "layout_centerInParent") { if (raw == "true") a.layout_gravity |= 0x11; }
        else if (n == "layout_centerVertical") { if (raw == "true") a.layout_gravity |= 0x10; }
        // FIX-2c: RelativeLayout sibling-dependency rules. The referenced id
        // name (from "@id/name" / "@+id/name") is resolved later, at layout
        // time, against the inflated sibling set (AOSP applies rules against
        // the dependency graph, not raw ids).
        else if (n == "layout_below" || n == "layout_above" ||
                 n == "layout_toRightOf" || n == "layout_toLeftOf") {
            std::string nm = parse_ref(raw).name;
            // Strip a leading "+" (android:id=@+id/name convention).
            if (!nm.empty() && nm[0] == '+') nm.erase(nm.begin());
            if (nm.empty() && at.value.is_reference()) {
                // compiled reference without raw string: resolve via arsc
                if (id_names_.empty())
                    for (auto& [rid, rnm] : arsc_.list_type("", "id"))
                        id_names_[rid] = rnm;
                auto it = id_names_.find(at.value.ref_id);
                if (it != id_names_.end()) nm = it->second;
            }
            if (n == "layout_below") a.rel_below = nm;
            else if (n == "layout_above") a.rel_above = nm;
            else if (n == "layout_toRightOf") a.rel_right_of = nm;
            else a.rel_left_of = nm;
        }
        else if (n == "layout_alignLeft") { /* align with sibling's left edge */ auto r = parse_ref(raw); std::string nm = r.name; if (!nm.empty() && nm[0]=='+') nm.erase(nm.begin()); a.rel_left_of = nm; }
        else if (n == "layout_alignRight") { auto r = parse_ref(raw); std::string nm = r.name; if (!nm.empty() && nm[0]=='+') nm.erase(nm.begin()); a.rel_right_of = nm; }
    }

    // Apply to node
    node.text = a.text;
    node.hint = a.hint;
    if (a.text_size_px > 0) node.text_size_px = a.text_size_px;
    else if (a.appearance_resolved && a.appearance_text_size_sp > 0) {
        // G46: TypedValue.complexToDimensionPixelSize law — sp -> px with
        // round-to-nearest: px = (int)(sp * scaledDensity + 0.5). Here
        // scaledDensity = density * fontScale = 2.625 * 1.0.
        float px_f = a.appearance_text_size_sp * metrics_.density * metrics_.scale_fonts;
        int px = (int)(px_f + 0.5f);
        node.text_size_px = (float)px;
        node.text_size_sp = a.appearance_text_size_sp;
        std::cerr << "[G46-TEXTAPPEARANCE] TextAppearance.Large textSize="
                  << a.appearance_text_size_sp << "sp -> " << px
                  << "px (scaledDensity=" << metrics_.density * metrics_.scale_fonts
                  << ")\n";
    }
    if (a.text_color != 0) node.text_color = a.text_color;
    node.text_style = a.text_style;
    node.text_bold = (a.text_style & 1) != 0;
    node.text_italic = (a.text_style & 2) != 0;
    node.font_family = a.font_family;  // G32
    node.padding_left = a.pl + a.padding_all;
    node.padding_top = a.pt + a.padding_all;
    node.padding_right = a.pr + a.padding_all;
    node.padding_bottom = a.pb + a.padding_all;
    if (a.orientation >= 0) node.orientation = a.orientation;
    if (a.gravity >= 0) { node.text_gravity = a.gravity; node.container_gravity = a.gravity; node.gravity_set = true; }
    if (a.layout_gravity >= 0) node.child_gravity = a.layout_gravity;
    node.layout_weight = a.layout_weight;
    node.lp_margin_left = a.ml; node.lp_margin_top = a.mt;
    node.lp_margin_right = a.mr; node.lp_margin_bottom = a.mb;
    node.lp_width = a.layout_width; node.lp_height = a.layout_height;
    node.visibility = a.visibility;
    node.clickable = a.clickable || !a.onClick.empty();
    node.num_lines = a.num_lines;
    if (!a.onClick.empty()) node.onClick_handler = a.onClick;
    // FIX-2c: relative-layout sibling rules onto the node
    node.rel_below_name = a.rel_below;
    node.rel_above_name = a.rel_above;
    node.rel_right_of_name = a.rel_right_of;
    node.rel_left_of_name = a.rel_left_of;
    if (a.bg_color != 0) { node.bg_color = a.bg_color; node.bg_from_xml = true; }
    if (!a.bg_drawable.empty()) { node.bg_drawable_path = a.bg_drawable; node.bg_from_xml = true; }
    if (!a.src_drawable.empty()) node.src_drawable_path = a.src_drawable;
    // width/height semantics on node
    node.width = a.layout_width;
    node.height = a.layout_height;
}

// ---------------------------------------------------------------------------
// inflate entry points
// ---------------------------------------------------------------------------
uint32_t LayoutInflater::inflate_layout_resid(framework::ViewShadow* views, uint32_t layout_resid,
                                              InflateStats& stats) {
    auto path = arsc_.apk_path_for(layout_resid, apk_entries_);
    if (!path) {
        auto r = arsc_.resolve(layout_resid);
        if (r) path = find_apk_file("layout", r->name);
    }
    if (!path) {
        stats.warnings.push_back("layout resid not found in ARSC/APK: 0x" + [&]{ 
            char b[16]; snprintf(b, sizeof b, "%x", layout_resid); return std::string(b); }());
        return 0;
    }
    std::vector<uint8_t> xml = apk_.extract_entry_cached(*path);
    if (xml.empty()) xml = apk_.extract_entry(apk_path_, *path);
    if (xml.empty()) {
        stats.warnings.push_back("layout extract failed: " + *path);
        return 0;
    }
    AxmlParser parser;
    if (!parser.parse(xml)) {
        stats.warnings.push_back("AXML parse failed: " + *path + " (" + parser.last_error() + ")");
        return 0;
    }
    // inflate root element as the content root
    uint32_t root = inflate_element(views, parser.root(), 0, stats);
    if (root) measure_layout(views, root);
    return root;
}

uint32_t LayoutInflater::inflate_layout_by_name(framework::ViewShadow* views, const std::string& name,
                                                InflateStats& stats) {
    auto id = arsc_.find_id("", "layout", name);
    if (!id) return 0;
    return inflate_layout_resid(views, *id, stats);
}

std::string InflateStats::to_json() const {
    std::string out = "{";
    out += "\"elements_total\":" + std::to_string(elements_total);
    out += ",\"views_created\":" + std::to_string(views_created);
    out += ",\"strings_resolved\":" + std::to_string(strings_resolved);
    out += ",\"colors_resolved\":" + std::to_string(colors_resolved);
    out += ",\"dimens_resolved\":" + std::to_string(dimens_resolved);
    out += ",\"drawables_resolved\":" + std::to_string(drawables_resolved);
    out += ",\"styles_applied\":" + std::to_string(styles_applied);
    out += ",\"includes_expanded\":" + std::to_string(includes_expanded);
    out += ",\"ids_resolved\":" + std::to_string(ids_resolved);
    out += ",\"unresolved_refs\":" + std::to_string(unresolved_refs);
    out += ",\"warnings\":[";
    for (size_t i = 0; i < warnings.size(); i++) {
        if (i) out += ",";
        std::string w;
        for (char c : warnings[i]) { if (c == '"') w += "\\\""; else if (c != '\n') w += c; }
        out += "\"" + w + "\"";
    }
    out += "]}";
    return out;
}

// ===========================================================================
// MEASURE + LAYOUT PASS (real, per AOSP semantics — simplified but honest)
//
// Sizes:  MATCH_PARENT(-1): parent content size
//         WRAP_CONTENT(-2): content size (text or children)
//         >=0: exact px
// Containers: LinearLayout (vertical/horizontal + weights), FrameLayout
// (gravity), RelativeLayout (best-effort top-down), ScrollView (vertical,
// unbounded height child).
// Every node gets left/top/right/bottom/width/height recorded for evidence.
// ===========================================================================

namespace {

struct LNode {
    framework::ViewShadow::ViewNode* n;
    uint32_t id;
    int ml, mt, mr, mb;
};

inline int content_w(const framework::ViewShadow::ViewNode& n) {
    return std::max(0, n.measured_width - n.padding_left - n.padding_right);
}
inline int content_h(const framework::ViewShadow::ViewNode& n) {
    return std::max(0, n.measured_height - n.padding_top - n.padding_bottom);
}

} // namespace

void LayoutInflater::measure_layout(framework::ViewShadow* views, uint32_t root_id) {
    // =======================================================================
    // MEASURE PASS — AOSP MeasureSpec semantics (FIX-2, generic; no app
    // special-casing). Replaces the fixed 0.62f char-width text estimate:
    // leaf text desired size now comes from the REAL shaping pipeline
    // (FriBidi/HarfBuzz/FreeType via fonts::layout_text), and parent/child
    // size negotiation follows ViewGroup.getChildMeasureSpec:
    //
    //   child dim >= 0        -> EXACTLY child
    //   MATCH_PARENT (-1)     -> EXACTLY(parent) | AT_MOST(parent) | UNSPEC
    //   WRAP_CONTENT (-2)     -> AT_MOST(parent)  | UNSPEC
    //
    // Every node records the full geometry evidence (class, lp, measured,
    // bounds, text metrics) for the proof artifacts.
    // =======================================================================
    enum Mode { M_UNSPEC = 0, M_EXACTLY, M_AT_MOST };
    struct Spec { int size; Mode mode; };

    auto child_spec = [](const Spec& p, int padding, int child_dim) -> Spec {
        const int avail = std::max(0, p.size - padding);
        if (child_dim >= 0)  return {child_dim, M_EXACTLY};
        if (child_dim == -1) {  // MATCH_PARENT
            switch (p.mode) {
                case M_EXACTLY: return {avail, M_EXACTLY};
                case M_AT_MOST: return {avail, M_AT_MOST};
                default:        return {avail, M_UNSPEC};
            }
        }
        // WRAP_CONTENT (-2) and any unknown sentinel behave as wrap.
        switch (p.mode) {
            case M_EXACTLY: return {avail, M_AT_MOST};
            case M_AT_MOST: return {avail, M_AT_MOST};
            default:        return {avail, M_UNSPEC};
        }
    };

    auto resolve_final = [](int content, const Spec& s) -> int {
        switch (s.mode) {
            case M_EXACTLY: return s.size;
            case M_AT_MOST: return std::min(content, s.size);
            default:        return content;
        }
    };

    auto is_container_node = [](const framework::ViewShadow::ViewNode* n) -> bool {
        return n->class_desc.find("Layout") != std::string::npos ||
               n->class_desc.find("ScrollView") != std::string::npos ||
               n->class_desc.find("ListView") != std::string::npos ||
               n->class_desc.find("ViewGroup") != std::string::npos ||
               n->class_desc.find("Toolbar") != std::string::npos ||
               n->class_desc.find("ViewPager") != std::string::npos ||
               n->class_desc.find("RecyclerView") != std::string::npos;
    };

    // -----------------------------------------------------------------------
    // measure(vid, spec_w, spec_h) -> desired (w, h) including own padding.
    // Children are measured FIRST (bottom-up) exactly like AOSP.
    // -----------------------------------------------------------------------
    std::function<std::pair<int,int>(uint32_t, const Spec&, const Spec&, int)> measure =
        [&](uint32_t vid, const Spec& sw, const Spec& sh, int depth) -> std::pair<int,int> {
        auto* n = views->find_node(vid);
        if (!n) return {0, 0};
        // Defensive depth cap: a real Android view tree is acyclic and
        // shallow; a cycle here (inflater bug) must fail loudly instead of
        // overflowing the stack.
        if (depth > 100) {
            fprintf(stderr, "[U007-LAYOUT] ERROR: measure depth > 100 at view %u (%s) — cycle suspected\n",
                    vid, n->class_desc.c_str());
            return {0, 0};
        }

        const bool container = is_container_node(n);
        const int hpad = n->padding_left + n->padding_right;
        const int vpad = n->padding_top + n->padding_bottom;

        // 1) measure children with AOSP-derived specs.
        std::vector<std::pair<int,int>> child_sizes(n->children.size());
        for (size_t i = 0; i < n->children.size(); i++) {
            auto* cn = views->find_node(n->children[i]);
            if (!cn) { child_sizes[i] = {0, 0}; continue; }
            int cw = cn->lp_width  == INT_MIN ? -2 : cn->lp_width;
            int ch = cn->lp_height == INT_MIN ? -2 : cn->lp_height;
            Spec csw = child_spec(sw, hpad + cn->lp_margin_left + cn->lp_margin_right, cw);
            Spec csh = child_spec(sh, vpad + cn->lp_margin_top + cn->lp_margin_bottom, ch);
            // ScrollView measures its single child with UNSPECIFIED height
            // (AOSP ScrollView.onMeasure law).
            if (n->class_desc.find("ScrollView;") != std::string::npos &&
                n->class_desc.find("Horizontal") == std::string::npos)
                csh = {std::max(0, sh.size - vpad), M_UNSPEC};
            child_sizes[i] = measure(n->children[i], csw, csh, depth + 1);
        }

        int content_w = 0, content_h = 0;
        if (!container) {
            // ---- leaf: real text/image content size ----
            const std::string& t = !n->text.empty() ? n->text : n->hint;
            float ts = n->text_size_px > 0 ? n->text_size_px
                                           : 14.0f * metrics_.density;
            if (!t.empty()) {
                // Real shaped measurement with word wrap against the
                // available content width (SINGLE SOURCE OF TRUTH with the
                // draw path — fonts::layout_text).
                const float avail_w = sw.mode == M_UNSPEC ? 0.0f
                                          : (float)std::max(0, sw.size - hpad);
                // G32: measure with the SAME face the draw path resolves
                // (AOSP fonts.xml family law).
                int face_idx = fonts::FACE_SYSTEM;
                if (!n->font_family.empty())
                    face_idx = fonts::TextShaper::instance().resolve_family(
                        n->font_family, n->text_bold);
                auto lay = fonts::layout_text(t, ts, n->text_bold, avail_w,
                                              n->num_lines, face_idx);
                content_w = std::max(content_w, (int)std::ceil(
                    avail_w > 0 ? std::min(lay.max_line_width, avail_w)
                                : lay.max_line_width));
                content_h = std::max(content_h, (int)std::ceil(lay.block_height()));
                // Evidence: remember the measured line count (task §3 log).
                n->num_lines = (n->num_lines > 0)
                             ? std::min(n->num_lines, (int)lay.lines.size())
                             : (int)lay.lines.size();
            }
            if (!n->src_drawable_path.empty() ||
                (n->image_drawable_path.empty() && n->class_desc.find("ImageView") != std::string::npos)) {
                // image default 48dp when no intrinsic size is known (AOSP
                // ImageView wrap fallback).
                content_w = std::max(content_w, (int)std::lround(48 * metrics_.density));
                content_h = std::max(content_h, (int)std::lround(48 * metrics_.density));
            }
            if (n->class_desc.find("EditText") != std::string::npos &&
                content_h < (int)std::lround(40 * metrics_.density))
                content_h = (int)std::lround(40 * metrics_.density);
            if (n->class_desc.find("ProgressBar") != std::string::npos) {
                content_w = std::max(content_w, (int)std::lround(48 * metrics_.density));
                content_h = std::max(content_h, (int)std::lround(48 * metrics_.density));
            }
            // Compound minimum (AOSP getSuggestedMinimum: 0 + padding).
            content_w = std::max(content_w, 0);
            content_h = std::max(content_h, 0);
        } else {
            // ---- container: children determine content size ----
            const bool is_ll = n->class_desc.find("LinearLayout") != std::string::npos;
            const bool is_scrollv = n->class_desc.find("ScrollView") != std::string::npos &&
                                    n->class_desc.find("Horizontal") == std::string::npos;
            const bool is_scrollh = n->class_desc.find("HorizontalScrollView") != std::string::npos;
            bool horizontal = n->orientation == 0;
            if (is_scrollv) horizontal = false;
            if (is_scrollh) horizontal = true;
            if (n->class_desc.find("FrameLayout") != std::string::npos ||
                n->class_desc.find("RelativeLayout") != std::string::npos ||
                (!is_ll && !is_scrollv && !is_scrollh)) {
                for (const auto& cs : child_sizes) {
                    content_w = std::max(content_w, cs.first);
                    content_h = std::max(content_h, cs.second);
                }
            } else if (horizontal) {
                for (size_t i = 0; i < n->children.size(); i++) {
                    auto* cn = views->find_node(n->children[i]);
                    int m = cn ? cn->lp_margin_left + cn->lp_margin_right : 0;
                    content_w += child_sizes[i].first + m;
                    content_h = std::max(content_h, child_sizes[i].second +
                                    (cn ? cn->lp_margin_top + cn->lp_margin_bottom : 0));
                }
            } else {
                for (size_t i = 0; i < n->children.size(); i++) {
                    auto* cn = views->find_node(n->children[i]);
                    int m = cn ? cn->lp_margin_top + cn->lp_margin_bottom : 0;
                    content_h += child_sizes[i].second + m;
                    content_w = std::max(content_w, child_sizes[i].first +
                                    (cn ? cn->lp_margin_left + cn->lp_margin_right : 0));
                }
            }
        }

        // 2) resolve own lp against the incoming spec (resolveSizeAndState).
        int lpw = n->lp_width  == INT_MIN ? -2 : n->lp_width;
        int lph = n->lp_height == INT_MIN ? -2 : n->lp_height;
        int final_w = lpw >= 0 ? lpw : resolve_final(content_w, sw);
        int final_h = lph >= 0 ? lph : resolve_final(content_h, sh);
        // EXACTLY spec wins for match_parent too (already EXACTLY from
        // child_spec); explicit lp never shrinks below the spec EXACTLY size
        // when larger (AOSP chooses the child's explicit size).
        n->measured_width = final_w + hpad;
        n->measured_height = final_h + vpad;
        return {n->measured_width, n->measured_height};
    };

    // Root fills the screen (EXACTLY), per AOSP window measure.
    auto root_size = measure(root_id,
                             {metrics_.screen_width, M_EXACTLY},
                             {metrics_.screen_height, M_EXACTLY}, 0);
    (void)root_size;

    // Full per-view geometry evidence (task §3 log format). Gated by env to
    // keep normal runs quiet; U007_LAYOUT_DEBUG=2 also dumps every node.
    if (getenv("U007_LAYOUT_DEBUG")) {
        fprintf(stderr, "[U007-LAYOUT] root measured %dx%d\n",
                root_size.first, root_size.second);
        std::function<void(uint32_t, int)> dump = [&](uint32_t vid, int depth) {
            auto* n = views->find_node(vid);
            if (!n) return;
            fprintf(stderr,
                "[U007-LAYOUT] %*sview %u %s id_name=%s lp=%d/%d weight=%d "
                "measured=%dx%d text_size=%.1f lines=%d below='%s' above='%s' "
                "right_of='%s' left_of='%s' cgrav=0x%x text='%s'\n",
                depth * 2, "", vid, n->class_desc.c_str(),
                n->android_id_name.c_str(), n->lp_width, n->lp_height,
                n->layout_weight, n->measured_width, n->measured_height,
                n->text_size_px, n->num_lines,
                n->rel_below_name.c_str(), n->rel_above_name.c_str(),
                n->rel_right_of_name.c_str(), n->rel_left_of_name.c_str(),
                n->child_gravity,
                n->text.substr(0, 40).c_str());
            for (uint32_t cid : n->children) dump(cid, depth + 1);
        };
        dump(root_id, 1);
    }


    // ---- layout (top-down): assign geometry ----
    struct Task { uint32_t id; int left, top, width, height; };
    std::vector<Task> stack;
    stack.push_back({root_id, 0, 0, root_size.first, root_size.second});
    while (!stack.empty()) {
        Task t = stack.back(); stack.pop_back();
        auto* n = views->find_node(t.id);
        if (!n) continue;
        n->measured_left = t.left; n->measured_top = t.top;
        n->measured_width = t.width; n->measured_height = t.height;
        n->measured_right = t.left + t.width;
        n->measured_bottom = t.top + t.height;
        n->x = t.left; n->y = t.top;
        n->width = t.width; n->height = t.height;
        n->laid_out = true;
        if (n->visibility == 8 /*GONE*/) continue;

        int cl = t.left + n->padding_left;
        int ct = t.top + n->padding_top;
        int cw = std::max(0, t.width - n->padding_left - n->padding_right);
        int ch = std::max(0, t.height - n->padding_top - n->padding_bottom);

        bool is_ll = n->class_desc.find("LinearLayout") != std::string::npos;
        bool is_fl = n->class_desc.find("FrameLayout") != std::string::npos;
        bool is_rl = n->class_desc.find("RelativeLayout") != std::string::npos;
        bool is_scroll = n->class_desc.find("ScrollView") != std::string::npos &&
                         n->class_desc.find("Horizontal") == std::string::npos;
        bool horizontal = n->orientation == 0;

        // gather visible children + margins
        std::vector<uint32_t> kids;
        for (uint32_t cid : n->children) {
            auto* cn = views->find_node(cid);
            if (cn && cn->visibility != 8) kids.push_back(cid);
        }

        if (is_ll && (horizontal || !is_scroll) && (horizontal || true)) {
            if (horizontal) {
                // horizontal: weights expand surplus width
                int total_margin = 0, fixed_w = 0, weight_total = 0;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    total_margin += cn->lp_margin_left + cn->lp_margin_right;
                    if (cn->layout_weight > 0) {
                        weight_total += cn->layout_weight;   // weighted child base = 0 (AOSP)
                    } else {
                        fixed_w += (cn->lp_width >= 0 ? cn->lp_width : cn->measured_width);
                    }
                }
                int avail = std::max(0, cw - total_margin);
                int weight_px = weight_total > 0 ? std::max(0, avail - fixed_w) : 0;
                // FIND-GRAVITY-VERTICAL FIX (AOSP LinearLayout@1cdfff55
                // layoutHorizontal): the container's main-axis gravity
                // (mGravity & HORIZONTAL_GRAVITY_MASK) positions the WHOLE
                // CHILD ROW when leftover width exists — LEFT (default),
                // CENTER_HORIZONTAL → half the leftover before the row,
                // RIGHT → all of it. Pre-fix the row always started at the
                // padding left. Child layout_gravity still governs only the
                // cross axis (below), identical to AOSP.
                int content_w = 0;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    int w2 = cn->layout_weight > 0 && weight_total > 0
                           ? weight_px * cn->layout_weight / weight_total
                           : (cn->lp_width >= 0 ? cn->lp_width : cn->measured_width);
                    content_w += w2 + cn->lp_margin_left + cn->lp_margin_right;
                }
                int hg_main = n->gravity_set ? n->container_gravity : -1;
                int block_x = cl;
                if (hg_main >= 0 && content_w < cw) {
                    // Axis-field equality law: mask the axis field FIRST
                    // (HORIZONTAL = 0x7) then compare — a bare `& 0x5` test
                    // misfires on CENTER (0x11 & 0x5 = 0x1 ≠ 0).
                    int hf = hg_main & 0x7;
                    if (hf == 0x5)           block_x = cl + (cw - content_w);   // RIGHT
                    else if (hf == 0x1)      block_x = cl + (cw - content_w) / 2; // CENTER_HORIZONTAL
                }
                int x = block_x;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    x += cn->lp_margin_left;
                    int w = cn->layout_weight > 0 && weight_total > 0
                          ? weight_px * cn->layout_weight / weight_total
                          : (cn->lp_width >= 0 ? cn->lp_width : cn->measured_width);
                    int h = cn->lp_height >= 0 ? cn->lp_height
                          : (cn->lp_height == -1 ? ch : cn->measured_height);
                    int y = ct;
                    // EXT-AOSP-001: same container-gravity fallback for the
                    // horizontal row's cross axis (LinearLayout.java L1777-1778).
                    int vg = cn->child_gravity >= 0 ? cn->child_gravity
                           : (n->gravity_set ? n->container_gravity : -1);
                    // Cross-axis vertical law (EXT-AOSP-001), masked-field
                    // equality: BOTTOM (0x50 field) → bottom; otherwise
                    // center (covers CENTER 0x10 and the no-bit default).
                    // Pre-fix a bare `& 0x50` test misfired on CENTER 0x11.
                    if (vg >= 0) {
                        int vf = vg & 0x70;
                        if (vf == 0x50) y = ct + ch - h;
                        else            y = ct + (ch - h) / 2;
                    }
                    if (w > cw) w = cw;
                    stack.push_back({cid, x, y, w, h});
                    x += w + cn->lp_margin_right;
                }
            } else {
                // vertical: weights expand surplus height
                int total_margin = 0, fixed_h = 0, weight_total = 0;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    total_margin += cn->lp_margin_top + cn->lp_margin_bottom;
                    if (cn->layout_weight > 0) {
                        weight_total += cn->layout_weight;   // weighted child base = 0 (AOSP)
                    } else {
                        fixed_h += (cn->lp_height >= 0 ? cn->lp_height : cn->measured_height);
                    }
                }
                int avail = std::max(0, ch - total_margin);
                int weight_px = weight_total > 0 ? std::max(0, avail - fixed_h) : 0;
                // FIND-GRAVITY-VERTICAL FIX (AOSP LinearLayout@1cdfff55
                // layoutVertical): the container's main-axis gravity
                // (mGravity & VERTICAL_GRAVITY_MASK) positions the whole
                // CHILD BLOCK when leftover height exists — TOP (default),
                // CENTER_VERTICAL → half the leftover above the block,
                // BOTTOM → all of it. Pre-fix the block always started at
                // the padding top, so setGravity(0x11) centered horizontally
                // but top-aligned vertically (visible in the old goldens).
                // Child layout_gravity still governs only the cross axis
                // (below), identical to AOSP.
                int content_h = 0;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    int h2 = cn->layout_weight > 0 && weight_total > 0
                           ? weight_px * cn->layout_weight / weight_total
                           : (cn->lp_height >= 0 ? cn->lp_height : cn->measured_height);
                    content_h += h2 + cn->lp_margin_top + cn->lp_margin_bottom;
                }
                int vg_main = n->gravity_set ? n->container_gravity : -1;
                int block_y = ct;
                if (vg_main >= 0 && content_h < ch) {
                    // Axis-field equality law: mask the axis field FIRST
                    // (VERTICAL = 0x70) then compare — a bare `& 0x50` test
                    // misfires on CENTER (0x11 & 0x50 = 0x10 ≠ 0), which
                    // pushed the block to the BOTTOM in the first attempt.
                    int vf = vg_main & 0x70;
                    if (vf == 0x50)          block_y = ct + (ch - content_h);      // BOTTOM
                    else if (vf == 0x10)     block_y = ct + (ch - content_h) / 2;  // CENTER_VERTICAL
                }
                int y = block_y;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    y += cn->lp_margin_top;
                    int h = cn->layout_weight > 0 && weight_total > 0
                          ? weight_px * cn->layout_weight / weight_total
                          : (cn->lp_height >= 0 ? cn->lp_height : cn->measured_height);
                    int w = cn->lp_width >= 0 ? cn->lp_width
                          : (cn->lp_width == -1 ? cw : cn->measured_width);
                    int x = cl;
                    // EXT-AOSP-001 (LinearLayout.java@1cdfff55 L1284/L1466):
                    // `lp.gravity < 0 ? mGravity : lp.gravity` — a child with
                    // no explicit layout_gravity inherits the container's
                    // gravity (set via XML android:gravity or the programmatic
                    // setGravity intercept). child_gravity == -1 encodes
                    // "unset" identically to AOSP's -1 sentinel.
                    int vg = cn->child_gravity >= 0 ? cn->child_gravity
                           : (n->gravity_set ? n->container_gravity : -1);
                    if (vg >= 0 && (vg & 0x1)) x = cl + (cw - w) / 2;
                    else if (vg >= 0 && (vg & 0x7) == 0x5) x = cl + cw - w;
                    if (w > cw) w = cw;
                    stack.push_back({cid, x, y, w, h});
                    y += h + cn->lp_margin_bottom;
                }
            }
        } else if (is_fl || is_rl || is_scroll) {
            if (is_rl) {
                // FIX-2c: RelativeLayout with REAL dependency rules (AOSP
                // applyVerticalSizeRules/applyHorizontalSizeRules, simplified
                // to the common subset). Fixed-point over children: a child
                // positioned relative to a sibling resolves once that
                // sibling's geometry is known.
                auto name_to_id = [&](const std::string& nm) -> uint32_t {
                    if (nm.empty()) return 0;
                    for (uint32_t cid : kids) {
                        auto* cn = views->find_node(cid);
                        if (cn && cn->android_id_name == nm) return cid;
                    }
                    return 0;
                };
                struct Box { int x, y, w, h; bool done; };
                std::map<uint32_t, Box> boxes;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    int w = cn->lp_width >= 0 ? cn->lp_width
                          : (cn->lp_width == -1 ? cw : cn->measured_width);
                    int h = cn->lp_height >= 0 ? cn->lp_height
                          : (cn->lp_height == -1 ? ch : cn->measured_height);
                    w = std::min(w, cw); h = std::min(h, ch > 0 ? ch : h);
                    boxes[cid] = {cl, ct, std::max(0, w), std::max(0, h), false};
                }
                // heights first (layout_below chains), then widths, 3 passes.
                for (int pass = 0; pass < 3; ++pass) {
                    int resolved = 0;
                    for (uint32_t cid : kids) {
                        auto* cn = views->find_node(cid);
                        Box& b = boxes[cid];
                        int vg = cn->child_gravity >= 0 ? cn->child_gravity
                                                       : n->container_gravity;
                        // ── vertical ──
                        int y = b.y;
                        if (!cn->rel_below_name.empty()) {
                            if (uint32_t bid = name_to_id(cn->rel_below_name)) {
                                y = boxes[bid].y + boxes[bid].h + cn->lp_margin_top;
                            }
                        } else if (!cn->rel_above_name.empty()) {
                            if (uint32_t bid = name_to_id(cn->rel_above_name)) {
                                y = boxes[bid].y - b.h - cn->lp_margin_bottom;
                            }
                        } else if (vg & 0x50) {           // alignParentBottom
                            y = ct + ch - b.h - cn->lp_margin_bottom;
                        } else if (vg & 0x10) {           // centerVertical
                            y = ct + (ch - b.h) / 2;
                        } else if (pass == 0) {           // default: flow top
                            y = ct;
                        }
                        if (y != b.y || b.done) {
                            b.y = y;
                            if (pass == 0 || !b.done) resolved++;
                        }
                        // ── horizontal ──
                        int x = b.x;
                        if (!cn->rel_right_of_name.empty()) {
                            if (uint32_t rid = name_to_id(cn->rel_right_of_name)) {
                                x = boxes[rid].x + boxes[rid].w + cn->lp_margin_left;
                            }
                        } else if (!cn->rel_left_of_name.empty()) {
                            if (uint32_t lid = name_to_id(cn->rel_left_of_name)) {
                                x = boxes[lid].x - b.w - cn->lp_margin_right;
                            }
                        } else if (vg & 0x1) {            // centerHorizontal
                            x = cl + (cw - b.w) / 2;
                        } else if ((vg & 0x7) == 0x5) {   // alignParentRight
                            x = cl + cw - b.w - cn->lp_margin_right;
                        } else if (pass == 0) {
                            x = cl;
                        }
                        if (x != b.x || b.done) {
                            b.x = x;
                            if (pass == 0 || !b.done) resolved++;
                        }
                        b.done = true;
                    }
                    if (resolved == 0) break;
                }
                for (uint32_t cid : kids) {
                    const Box& b = boxes[cid];
                    stack.push_back({cid, b.x, b.y, b.w, b.h});
                }
            } else {
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    int w = cn->lp_width >= 0 ? cn->lp_width
                          : (cn->lp_width == -1 ? cw : cn->measured_width);
                    int h = cn->lp_height >= 0 ? cn->lp_height
                          : (cn->lp_height == -1 ? ch : cn->measured_height);
                    int x = cl, y = ct;
                    int vg = cn->child_gravity >= 0 ? cn->child_gravity : n->container_gravity;
                    if (vg > 0) {
                        if (vg & 0x1) x = cl + (cw - w) / 2;
                        else if (vg & 0x7) { if ((vg & 0x7) == 0x5) x = cl + cw - w; }
                        if (vg & 0x10) y = ct + (ch - h) / 2;
                        else if (vg & 0x30) { if ((vg & 0x70) == 0x50) y = ct + ch - h; }
                    }
                    if (x + w > t.left + t.width) w = std::max(0, t.left + t.width - x);
                    stack.push_back({cid, x, y, w, h});
                }
            }
        } else {
            // generic ViewGroup: stack children vertically top-down
            int y = ct;
            for (uint32_t cid : kids) {
                auto* cn = views->find_node(cid);
                int w = cn->lp_width == -1 ? cw : (cn->lp_width >= 0 ? cn->lp_width : cn->measured_width);
                int h = cn->lp_height >= 0 ? cn->lp_height : cn->measured_height;
                if (h <= 0) h = (int)std::lround(40 * metrics_.density);
                stack.push_back({cid, cl, y, std::min(w, cw), h});
                y += h;
            }
        }
    }
}

} // namespace resources
} // namespace miniandroid
