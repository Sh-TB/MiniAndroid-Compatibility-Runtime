/*
 * UNIFIED_007 — Real Layout Inflater implementation.
 */
#include "layout_inflater.h"
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
    }

    // Apply to node
    node.text = a.text;
    node.hint = a.hint;
    if (a.text_size_px > 0) node.text_size_px = a.text_size_px;
    if (a.text_color != 0) node.text_color = a.text_color;
    node.text_style = a.text_style;
    node.text_bold = (a.text_style & 1) != 0;
    node.text_italic = (a.text_style & 2) != 0;
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
    // ---- measure (bottom-up): compute desired size of every node ----
    // measure(node, parent_spec_w, parent_spec_h) → desired {w,h}
    std::function<std::pair<int,int>(uint32_t, int, int, bool, bool)> measure =
        [&](uint32_t vid, int pw, int ph, bool pw_exact, bool ph_exact) -> std::pair<int,int> {
        auto* n = views->find_node(vid);
        if (!n) return {0, 0};

        int desired_w = 0, desired_h = 0;
        bool is_container = n->class_desc.find("Layout") != std::string::npos ||
                            n->class_desc.find("ScrollView") != std::string::npos ||
                            n->class_desc.find("ListView") != std::string::npos ||
                            n->class_desc.find("ViewGroup") != std::string::npos ||
                            n->class_desc.find("Toolbar") != std::string::npos;

        // children desired sizes first
        std::vector<std::pair<int,int>> child_sizes(n->children.size());
        for (size_t i = 0; i < n->children.size(); i++) {
            auto* cn = views->find_node(n->children[i]);
            if (!cn) { child_sizes[i] = {0,0}; continue; }
            int cw = cn->lp_width, ch = cn->lp_height;
            if (cw == INT_MIN) cw = -2;
            if (ch == INT_MIN) ch = -2;
            // pass parent content specs; children can match only if parent exact
            child_sizes[i] = measure(n->children[i], pw, ph, pw_exact, ph_exact);
            (void)cw; (void)ch;
        }

        if (!is_container) {
            // leaf: text-based or image-based size
            if (!n->src_drawable_path.empty() || n->image_drawable_path.empty()) {
                // image default 48dp if unknown; wrap
                desired_w = std::max(desired_w, (int)std::lround(48 * metrics_.density));
                desired_h = std::max(desired_h, (int)std::lround(48 * metrics_.density));
            }
            if (!n->text.empty() || !n->hint.empty()) {
                float ts = n->text_size_px > 0 ? n->text_size_px : 14.0f * metrics_.density;
                const std::string& t = !n->text.empty() ? n->text : n->hint;
                desired_w = std::max(desired_w, (int)std::lround(t.size() * ts * 0.62f));
                desired_h = std::max(desired_h, (int)std::lround(ts * 1.35f) + 2);
            }
            if (n->class_desc.find("EditText") != std::string::npos && desired_h < 40 * metrics_.density)
                desired_h = (int)std::lround(40 * metrics_.density);
            if (n->class_desc.find("ProgressBar") != std::string::npos) {
                desired_w = std::max(desired_w, (int)std::lround(48 * metrics_.density));
                desired_h = std::max(desired_h, (int)std::lround(48 * metrics_.density));
            }
        } else {
            // container: sum/extent of children
            bool horizontal = n->orientation == 0;
            if (n->class_desc.find("ScrollView") != std::string::npos) horizontal = false;
            if (n->class_desc.find("HorizontalScrollView") != std::string::npos) horizontal = true;
            if (n->class_desc.find("FrameLayout") != std::string::npos ||
                n->class_desc.find("RelativeLayout") != std::string::npos) {
                for (size_t i = 0; i < n->children.size(); i++) {
                    desired_w = std::max(desired_w, child_sizes[i].first);
                    desired_h = std::max(desired_h, child_sizes[i].second);
                }
            } else if (horizontal) {
                int total_w = 0, max_h = 0;
                for (size_t i = 0; i < n->children.size(); i++) {
                    auto* cn = views->find_node(n->children[i]);
                    int cmw = cn && cn->lp_margin_left != INT_MIN ? cn->lp_margin_left + cn->lp_margin_right : 0;
                    total_w += child_sizes[i].first + cmw;
                    max_h = std::max(max_h, child_sizes[i].second);
                }
                desired_w = total_w; desired_h = max_h;
            } else {
                int max_w = 0, total_h = 0;
                for (size_t i = 0; i < n->children.size(); i++) {
                    auto* cn = views->find_node(n->children[i]);
                    int cmh = cn && cn->lp_margin_top != INT_MIN ? cn->lp_margin_top + cn->lp_margin_bottom : 0;
                    max_w = std::max(max_w, child_sizes[i].first);
                    total_h += child_sizes[i].second + cmh;
                }
                desired_w = max_w; desired_h = total_h;
            }
            if (n->class_desc.find("ScrollView") != std::string::npos && n->children.size() == 1)
                desired_h = child_sizes[0].second;
        }

        // resolve against layout params
        int lpw = n->lp_width, lph = n->lp_height;
        if (lpw == INT_MIN) lpw = -2;
        if (lph == INT_MIN) lph = -2;
        int final_w = lpw >= 0 ? lpw : (lpw == -1 ? (pw_exact ? pw : std::max(desired_w, 0)) : desired_w);
        int final_h = lph >= 0 ? lph : (lph == -1 ? (ph_exact ? ph : std::max(desired_h, 0)) : desired_h);
        final_w += n->padding_left + n->padding_right;
        final_h += n->padding_top + n->padding_bottom;
        n->measured_width = final_w;    // desired size (pre-layout)
        n->measured_height = final_h;
        return {final_w, final_h};
    };

    // root fills the screen
    auto root_size = measure(root_id, metrics_.screen_width, metrics_.screen_height, true, true);
    if (getenv("U007_LAYOUT_DEBUG")) {
        fprintf(stderr, "[U007-LAYOUT] root measured %dx%d\n", root_size.first, root_size.second);
        if (auto* rn = views->find_node(root_id)) {
            for (uint32_t cid : rn->children) {
                if (auto* cn = views->find_node(cid)) {
                    fprintf(stderr, "[U007-LAYOUT]   child %u %s lp=%d/%d weight=%d measured=%dx%d\n",
                            cid, cn->class_desc.c_str(), cn->lp_width, cn->lp_height,
                            cn->layout_weight, cn->measured_width, cn->measured_height);
                }
            }
        }
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
                int x = cl;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    x += cn->lp_margin_left;
                    int w = cn->layout_weight > 0 && weight_total > 0
                          ? weight_px * cn->layout_weight / weight_total
                          : (cn->lp_width >= 0 ? cn->lp_width : cn->measured_width);
                    int h = cn->lp_height >= 0 ? cn->lp_height
                          : (cn->lp_height == -1 ? ch : cn->measured_height);
                    int y = ct;
                    int vg = cn->child_gravity;
                    if (vg >= 0 && !(vg & 0x30)) { /* no vertical bit: center */ y = ct + (ch - h) / 2; }
                    else if (vg & 0x50) y = ct + ch - h;
                    else if (vg & 0x10) y = ct + (ch - h) / 2;
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
                int y = ct;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    y += cn->lp_margin_top;
                    int h = cn->layout_weight > 0 && weight_total > 0
                          ? weight_px * cn->layout_weight / weight_total
                          : (cn->lp_height >= 0 ? cn->lp_height : cn->measured_height);
                    int w = cn->lp_width >= 0 ? cn->lp_width
                          : (cn->lp_width == -1 ? cw : cn->measured_width);
                    int x = cl;
                    int vg = cn->child_gravity;
                    if (vg >= 0 && (vg & 0x1)) x = cl + (cw - w) / 2;
                    else if (vg >= 0 && (vg & 0x7) == 0x5) x = cl + cw - w;
                    if (w > cw) w = cw;
                    stack.push_back({cid, x, y, w, h});
                    y += h + cn->lp_margin_bottom;
                }
            }
        } else if (is_fl || is_rl || is_scroll) {
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
