/*
 * UNIFIED_007 — Real Layout Inflater implementation.
 */
#include "layout_inflater.h"
#include <unordered_set>

#include "../fonts/text_shaper.h"
#include "../renderer/software_renderer.h"  // G04 §8: header-only image size probe
#include "res_config.h"                     // G04 §4: device density law
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
        // G10 FIX-G10-002: ViewAnimator family + RadioGroup keep their REAL
        // descriptors (AOSP: ViewSwitcher/ViewFlipper → ViewAnimator →
        // FrameLayout; RadioGroup → LinearLayout) so the DEX-backed
        // superclass chain classifies their container behavior. The old
        // unknown-short-name→View fallback degraded them to content-less
        // leaves (billthefarmer: FAB ViewSwitcher measured 0x0, FABs pushed
        // offscreen; main editor switcher stacked instead of overlapped).
        {"ViewSwitcher", "Landroid/widget/ViewSwitcher;"},
        {"ViewFlipper", "Landroid/widget/ViewFlipper;"},
        {"ViewAnimator", "Landroid/widget/ViewAnimator;"},
        {"RadioGroup", "Landroid/widget/RadioGroup;"},
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

// G11 FIX-G11-001 descriptor gate: "does this descriptor LOOK like app code?"
// Framework/library prefixes are excluded (their tags never carry app
// constructors). The obfuscated-package case (microtimer `Lk/g;`) must PASS
// this gate — the hook's DEX class-index check is the real authority; this
// gate only avoids invoking the hook for framework tags.
bool LayoutInflater::is_app_class_descriptor(const std::string& class_desc) {
    static const char* kNonAppPrefixes[] = {
        "Landroid/", "Ljava/", "Ljavax/", "Ldalvik/", "Lkotlin/", "Lkotlinx/",
        "Lcom/google/android/", "Lcom/google/", "Lorg/apache/", "Lorg/json/",
        "Lorg/xml/", "Lorg/w3c/", "Lorg/ccil/", "Lj$/",
    };
    if (class_desc.size() < 3 || class_desc.front() != 'L') return false;
    for (const char* p : kNonAppPrefixes) {
        if (class_desc.compare(0, std::string(p).size(), p) == 0) return false;
    }
    return true;
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
    return drawable_file_for_name(name, nullptr);
}

// G04 §4 (FIND-G04-AUDIT-003): ALL drawable/mipmap/raw path selection goes
// through the canonical ARSC engine (select_file → resolve_full →
// best_for(device) — the same AssetManager2 law every other lookup uses).
// The previous implementations ranked ZIP PATH STRINGS ("prefer xxxhdpi",
// or "shortest dir name"), a parallel resource system that violated the
// AOSP density-bucket law (isBetterThan: exact > both-above→smaller >
// straddle→higher) and could never report the SELECTED config density.
// out_density: selected ResTable_config.density (raw table form: 0 = unset
// → TypedValue DENSITY_DEFAULT 160; 0xFFFF DENSITY_NONE → never scale).
std::string LayoutInflater::drawable_file_for_name(const std::string& name,
                                                   uint16_t* out_density) {
    const char* types[] = {"drawable", "mipmap", "raw"};
    for (const char* t : types) {
        auto id = arsc_.find_id("", t, name);
        if (!id) continue;
        if (auto sel = arsc_.select_file(*id, apk_entries_, device_config())) {
            if (out_density) *out_density = sel->selected_density();
            return sel->path;
        }
    }
    // Table-less fallback (no ARSC entry — e.g. assets-style files): keep the
    // old zip scan as a LAST resort, never as an authority over the table.
    std::string p = find_apk_file("drawable", name);
    if (p.empty()) p = find_apk_file("mipmap", name);
    if (p.empty()) p = find_apk_file("raw", name);
    if (out_density) *out_density = 0;
    return p;
}

std::string LayoutInflater::drawable_path_for_resid(uint32_t resid) {
    return drawable_file_for_resid(resid, nullptr);
}

std::string LayoutInflater::drawable_file_for_resid(uint32_t resid, uint16_t* out_density) {
    if (auto sel = arsc_.select_file(resid, apk_entries_, device_config())) {
        if (out_density) *out_density = sel->selected_density();
        return sel->path;
    }
    if (out_density) *out_density = 0;
    return "";
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
            // GOLDEN-03 §9: ONE canonical conversion path (AOSP
            // TypedValue.complexToDimensionPixelSize law — rounding +
            // nonzero-floor tail). Was a local switch that treated PT/IN/MM
            // as plain px.
            return complex_to_dimension_pixel_size(val->data, density_context());
        }
        stats.unresolved_refs++;
        return 0;
    }
    if (!ref.is_ref) {
        // raw string form "12dp" / "14sp" / "8px" / "1in" / "12pt" / "5mm"
        // GOLDEN-03 §9: same canonical law for literal dimensions.
        std::string s = v;
        if (s.size() > 2) {
            std::string suf = s.substr(s.size() - 2);
            float val = (float)atof(s.c_str());
            uint8_t unit;
            if (suf == "dp" || suf == "dip") unit = COMPLEX_UNIT_DIP;
            else if (suf == "sp")           unit = COMPLEX_UNIT_SP;
            else if (suf == "px")           unit = COMPLEX_UNIT_PX;
            else if (suf == "in")           unit = COMPLEX_UNIT_IN;
            else if (suf == "pt")           unit = COMPLEX_UNIT_PT;
            else if (suf == "mm")           unit = COMPLEX_UNIT_MM;
            else return 0;
            return complex_unit_to_dimension_pixel_size(unit, val, density_context());
        }
    }
    return 0;
}

int LayoutInflater::parse_dim_attr(const AxmlAttribute* attr, InflateStats& stats) {
    if (!attr) return 0;
    if (attr->value.is_dimension()) {
        stats.dimens_resolved++;
        // GOLDEN-03 §9: canonical TypedValue law (raw complex word + context).
        return complex_to_dimension_pixel_size(attr->value.data, density_context());
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
// ── GOLDEN-03 §8 — verified framework attribute constants ──────────────
// Every constant below was READ FROM APK BYTES (never from memory):
//   0x01010095 textSize          — helloworld_golden fixture AXML resource map
//   0x01010098 textColor         — EXT-01 AND helloworld_golden maps (agree)
// Framework TextAppearance.Large = 0x01030042 with textSize 22sp — AOSP
// core/res/res/values/styles.xml; the id was verified from the EXT-01 AXML
// (textAppearance attr data=0x01030042) and the 22sp→58px G46 runtime law.
static constexpr uint32_t ATTR_TEXT_SIZE  = 0x01010095;
static constexpr uint32_t ATTR_TEXT_COLOR = 0x01010098;
// M3 FIX-M3-002 (style-bag layout params — AOSP obtainStyledAttributes
// precedence law): the element's `style=` reference participates in
// layout_* attribute resolution on real Android (LayoutInflater derives
// LayoutParams through obtainStyledAttributes, whose resolution chain is
// [direct XML attr] > [style= bag] > [defStyleAttr/theme]). Ground truth:
// org.debian.eugen.headingcalculator v1 res/layout/calculator_keypad.xml —
// every <Button> carries NO layout_width/height/weight but references
// style/keypad_button whose bag holds layout_width=0dp, layout_height=-1
// (match), layout_margin=1dp, layout_weight=1 — a real device renders a
// full-width weighted keypad; ignoring the bag collapsed every button to
// wrap_content 66x123 (keypad filled 1/3 of the row).
static constexpr uint32_t ATTR_LAYOUT_WIDTH  = 0x010100f4;
static constexpr uint32_t ATTR_LAYOUT_HEIGHT = 0x010100f5;
static constexpr uint32_t ATTR_LAYOUT_MARGIN = 0x010100f6;
static constexpr uint32_t ATTR_LAYOUT_WEIGHT = 0x01010181;
static constexpr uint32_t FRAMEWORK_STYLE_TEXTAPPEARANCE_LARGE = 0x01030042;
static constexpr float    TEXTAPPEARANCE_LARGE_SP = 22.0f;

// §9: the ONE TypedValue conversion context for this inflater.
resources::DensityContext LayoutInflater::density_context() const {
    return DensityContext::from_density(metrics_.density, metrics_.scale_fonts);
}

bool LayoutInflater::apply_style_item(Attrs& a, uint32_t attr_key,
                                      const ResValue& item, InflateStats& stats) {
    (void)stats;
    ResValue v = item;
    // AOSP Style law: a style item may itself be a reference
    // (e.g. <item name="textColor">@color/foo</item>) — dereference through
    // the canonical resolver before interpreting.
    if (v.is_reference()) {
        auto rv = arsc_.resolve_value(v.ref_id);
        if (!rv) return false;
        v = *rv;
    }
    // M3 FIX-M3-002: layout_* keys from the style bag. First-writer wins
    // within the style chain (the element's own style beats its parent
    // style — the apply_style walk applies nearest bags first).
    if (attr_key == ATTR_LAYOUT_WIDTH || attr_key == ATTR_LAYOUT_HEIGHT) {
        const bool width_key = attr_key == ATTR_LAYOUT_WIDTH;
        int& slot = width_key ? a.style_layout_width : a.style_layout_height;
        if (slot != INT_MIN) return false;             // first-writer wins
        {
            static const bool m3dbg = std::getenv("MINIANDROID_M3_STYLE_DIAG") != nullptr;
            if (m3dbg)
                fprintf(stderr, "[M3-STYLE] key=0x%x probe type=%d data=%d ref=%d\n",
                        attr_key, (int)v.type, (int)v.data, (int)item.is_reference());
        }
        if (!v.is_dimension() && !v.is_int()) return false;
        int px;
        if (v.is_dimension())
            px = complex_to_dimension_pixel_size(v.data, density_context());
        else px = (int)v.data;                          // -1 match / -2 wrap / raw px
        slot = px;
        return true;
    }
    if (attr_key == ATTR_LAYOUT_MARGIN) {
        if (a.style_margin_all != INT_MIN) return false;
        if (!v.is_dimension() && !v.is_int()) return false;
        a.style_margin_all = v.is_dimension()
                                 ? complex_to_dimension_pixel_size(v.data, density_context())
                                 : (int)v.data;
        return true;
    }
    if (attr_key == ATTR_LAYOUT_WEIGHT) {
        if (a.style_layout_weight >= 0) return false;  // first-writer wins
        float f;
        if (v.type == DataType::FLOAT) {
            memcpy(&f, &v.data, 4);
        } else if (v.is_int()) {
            f = (float)v.data;   // aapt2 may store 1.0 as INT 1
        } else return false;
        a.style_layout_weight = (int)std::lround(f * 1000.0f);
        return true;
    }
    if (attr_key == ATTR_TEXT_SIZE) {
        if (a.from_style_text_size) return false;      // first-writer wins
        if (!v.is_dimension()) return false;
        a.style_text_size_px =
            complex_to_dimension_pixel_size(v.data, density_context());
        a.from_style_text_size = true;
        return true;
    }
    if (attr_key == ATTR_TEXT_COLOR) {
        if (a.style_text_color != 0) return false;
        if (!v.is_color() && !v.is_int()) return false;
        a.style_text_color = v.data;
        return true;
    }
    return false;   // key not consumed by the inflater (honest stats)
}

void LayoutInflater::apply_style(framework::ViewShadow::ViewNode& node, Attrs& a,
                                 uint32_t style_resid, InflateStats& stats) {
    (void)node;
    auto r = arsc_.resolve(style_resid);
    if (!r) return;
    const ArscEntry* e = r->best();
    if (!e || !e->is_complex) return;
    // name of style for evidence
    a.style_name = r->name;
    // GOLDEN-03 §8: attribute-KEY-aware application (AOSP ResTable_map law).
    // The previous code iterated complex_items POSITIONALLY and applied any
    // dimension as textSize / any color as textColor regardless of which
    // attribute they actually carried.
    for (size_t i = 0; i < e->complex_keys.size() && i < e->complex_items.size(); ++i) {
        static const bool m3dbg = std::getenv("MINIANDROID_M3_STYLE_DIAG") != nullptr;
        if (m3dbg && !e->complex_keys.empty() && i < 12)
            fprintf(stderr, "[M3-BAG] style=0x%x key[%zu]=0x%x type=%d\n",
                    style_resid, i, e->complex_keys[i],
                    (int)e->complex_items[i].type);
        if (apply_style_item(a, e->complex_keys[i], e->complex_items[i], stats)) {
            stats.styles_applied++;
        }
    }
    // M3 FIX-M3-002 (AOSP style parent-chain law): attributes resolve
    // through the style's ResTable_map_entry parent chain — a child style
    // (keypad_button_digit) inherits its parent's bag (keypad_button:
    // textColor, layout_width/height/weight/margin). Previously only the
    // own keys were consulted, so parent-supplied attributes were silently
    // dropped. Nearest-bag-first (the loop above already consumed the
    // child's own keys — first-writer-wins inside apply_style_item keeps
    // child > parent precedence). Bounded + cycle-safe like bag_value.
    uint32_t cur = style_resid;
    int hops = 0;
    std::unordered_set<uint32_t> visited{style_resid};
    while (hops++ < 8) {
        auto pr = arsc_.resolve(cur);
        if (!pr) break;
        const ArscEntry* pe = pr->best();
        if (!pe || !pe->is_complex) break;
        // M3 FIX-M3-003b: parent lives in bag_parent now (entry.value is
        // overwritten with complex_items[0] for single-value compat).
        uint32_t parent = pe->bag_parent;
        if (parent == 0 || parent == cur || visited.count(parent)) break;
        visited.insert(parent);
        cur = parent;
        auto pa = arsc_.resolve(cur);
        if (!pa) break;
        const ArscEntry* pae = pa->best();
        if (!pae || !pae->is_complex) break;
        for (size_t i = 0; i < pae->complex_keys.size() && i < pae->complex_items.size(); ++i) {
            if (apply_style_item(a, pae->complex_keys[i], pae->complex_items[i], stats)) {
                stats.styles_applied++;
            }
        }
    }
}

void LayoutInflater::apply_style_by_name(framework::ViewShadow::ViewNode& node, Attrs& a,
                                         const std::string& style_name, InflateStats& stats) {
    auto id = arsc_.find_id("", "style", style_name);
    if (id) apply_style(node, a, *id, stats);
}

// ── GOLDEN-03 §8/G46 — textAppearance resolution (generic) ───────────────
bool LayoutInflater::resolve_text_appearance(uint32_t style_resid, Attrs& a,
                                             InflateStats& stats) {
    (void)stats;
    // AOSP TextView.applyTextAppearance: the referenced style's textSize
    // applies unless the view sets an explicit textSize.
    // 1) GENERIC path: query the style bag by the AOSP textSize key through
    //    the canonical resolver — works for ANY app-local style (any package),
    //    parent inheritance included, cycle-safe.
    if (auto item = arsc_.bag_value(style_resid, ATTR_TEXT_SIZE, device_config())) {
        ResValue v = *item;
        if (v.is_reference()) {
            auto rv = arsc_.resolve_value(v.ref_id);
            if (!rv) return false;
            v = *rv;
        }
        if (v.is_dimension()) {
            a.appearance_text_size_px =
                complex_to_dimension_pixel_size(v.data, density_context());
            a.appearance_resolved = true;
            return true;
        }
        return false;
    }
    // 2) Framework style table — byte-verified entries only (see the constant
    //    block above). Unknown framework ids stay unresolved with a warning;
    //    nothing is invented.
    if (style_resid == FRAMEWORK_STYLE_TEXTAPPEARANCE_LARGE) {
        // Encoded exactly as the ARSC would: mantissa 22 @ radix 0, unit SP.
        const uint32_t data22sp = (22u << COMPLEX_MANTISSA_SHIFT) | COMPLEX_UNIT_SP;
        a.appearance_text_size_px =
            complex_to_dimension_pixel_size(data22sp, density_context());
        a.appearance_resolved = true;
        return true;
    }
    return false;
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
        // G10 FIX-G10-003 (AOSP LayoutInflater merge law): <merge> has no
        // view of its own — its children attach DIRECTLY to the parent.
        // At the ROOT (parent_view_id == 0) the attach target is the window
        // content frame (PhoneWindow DecorView contentParent) — synthesize
        // one FrameLayout so ALL merged children land under ONE rendered
        // root. Returning the LAST merged child orphaned every earlier
        // subtree (billthefarmer: the main editor ViewSwitcher never
        // rendered; only the FAB switcher under the returned id survived).
        if (parent_view_id == 0) {
            uint32_t decor = views->create_view("Landroid/widget/FrameLayout;");
            if (auto* dn = views->find_node(decor)) {
                dn->lp_width = -1;    // window content frame fills the window
                dn->lp_height = -1;
            }
            for (const auto& child : el.children)
                inflate_element(views, child, decor, stats);
            return decor;
        }
        for (const auto& child : el.children)
            inflate_element(views, child, parent_view_id, stats);
        return parent_view_id;
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

    // G11 FIX-G11-001 (AOSP LayoutInflater.createView law): a fully-qualified
    // app-class tag is an INSTANTIATION. Execute the class's real DEX
    // constructor BEFORE XML children inflate — the constructor itself may
    // build the child hierarchy (CalculatorDisplay.<init> inflates
    // calculator_display.xml into itself via LayoutInflater.inflate(res, this)).
    // App-class test is a pure descriptor gate (framework prefixes excluded);
    // the hook re-verifies the class actually exists in the app DEX.
    if (custom_view_ctor_hook_ && is_app_class_descriptor(node->class_desc)) {
        const bool constructed = custom_view_ctor_hook_(view_id, node->class_desc);
        if (!constructed) {
            stats.warnings.push_back(
                "custom-view constructor not executed: " + node->class_desc);
        }
    }

    // children
    uint32_t last_child = 0;
    for (const auto& child : el.children) {
        uint32_t cid = inflate_element(views, child, view_id, stats);
        if (cid) last_child = cid;
    }
    (void)last_child;
    // G10 FIX-G10-002b (AOSP ViewAnimator law): ViewAnimator.initView calls
    // showOnly(mWhichChild=0) — at inflation only the FIRST child is
    // visible; the rest are GONE until showNext/showPrevious. Without this
    // both switcher children render overlapped (billthefarmer FABs drew
    // edit-over-accept; the preview MarkdownView covered the editor).
    if (node->class_desc.find("ViewSwitcher") != std::string::npos ||
        node->class_desc.find("ViewFlipper") != std::string::npos ||
        node->class_desc.find("ViewAnimator") != std::string::npos) {
        for (size_t i = 1; i < node->children.size(); i++) {
            if (auto* cn = views->find_node(node->children[i]))
                cn->visibility = 8;   // GONE (ViewAnimator.showOnly(0) law)
        }
    }
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
        else if (n == "layout_margin") { a.ml = a.mt = a.mr = a.mb = parse_dim_attr(&at, stats); a.margin_set = true; }
        else if (n == "layout_marginLeft") a.ml = parse_dim_attr(&at, stats), a.margin_set = true;
        else if (n == "layout_marginTop") a.mt = parse_dim_attr(&at, stats), a.margin_set = true;
        else if (n == "layout_marginRight") a.mr = parse_dim_attr(&at, stats), a.margin_set = true;
        else if (n == "layout_marginBottom") a.mb = parse_dim_attr(&at, stats), a.margin_set = true;
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
            a.weight_set = true;   // M3 FIX-M3-002: direct attr beats style bag
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
            // G46/GOLDEN-03 §8: AOSP TextView law (applyTextAppearance): the
            // referenced style's textSize applies UNLESS the view sets an
            // explicit textSize (view attrs are read after the appearance →
            // they win). Resolution is GENERIC: app-local style bags go
            // through the canonical bag resolver (key 0x01010095, parent
            // inheritance included); framework styles fall to the byte-
            // verified framework table.
            uint32_t sid = at.value.is_reference() ? at.value.ref_id : 0;
            if (sid != 0) {
                if (!resolve_text_appearance(sid, a, stats)) {
                    stats.unresolved_refs++;
                    stats.warnings.push_back("framework TextAppearance 0x" + [&]{
                        char b[16]; snprintf(b, sizeof b, "%x", sid);
                        return std::string(b); }() + " not in the verified law table");
                }
            }
        }
        else if (n == "textStyle") {
            if (raw.find("bold") != std::string::npos) { a.text_style |= 1; }
            if (raw.find("italic") != std::string::npos) { a.text_style |= 2; }
        }
        else if (n == "lineSpacingMultiplier") {
            // G47: AOSP TextView L1477 — mSpacingMult = a.getFloat(attr, ...).
            // FLOAT typed value: data holds the IEEE-754 bits.
            if (at.value.type == DataType::FLOAT) {
                float f; memcpy(&f, &at.value.data, 4);
                a.line_spacing_mult = f;
            } else a.line_spacing_mult = (float)atof(raw.c_str());
        }
        else if (n == "lineSpacingExtra") {
            // G47: AOSP TextView L1473 — mSpacingAdd =
            // a.getDimensionPixelSize(attr, ...) (px after unit conversion).
            a.line_spacing_add_px = (float)parse_dim_attr(&at, stats);
        }
        else if (n == "elegantTextHeight") {
            // G36: TextView L4485 setElegantTextHeight — uses the font's own
            // hhea box for the font-padding extents instead of the win-clamped
            // maximum.
            a.elegant_text_height = at.value.type == DataType::INT_BOOLEAN
                                          ? at.value.data != 0
                                          : (raw == "true");
        }
        else if (n == "includeFontPadding") {
            // G47: TextView L1440 — mIncludeFontPadding = a.getBoolean(...)
            // (default TRUE — layout must say false explicitly).
            a.include_font_pad = at.value.type == DataType::INT_BOOLEAN
                                          ? at.value.data != 0
                                          : (raw != "false");
        }
        else if (n == "background") {
            if (at.value.is_reference()) {
                uint16_t sel_d = 0;
                std::string p = drawable_file_for_resid(at.value.ref_id, &sel_d);
                if (!p.empty()) { a.bg_drawable = p; a.bg_drawable_density = sel_d; }
                else {
                    auto val = arsc_.resolve_value(at.value.ref_id);
                    if (val && (val->is_color() || val->is_int())) a.bg_color = val->data;
                }
            } else if (at.value.is_color()) {
                // FIND-G06AUDIT-003: aapt2 compiles android:background="#RRGGBB"
                // into a TYPED COLOR Res_value (COLOR_RGB8/ARGB8/...), not a raw
                // string. Res_value COLOR law: data IS the ARGB constant.
                a.bg_color = at.value.data;
                stats.colors_resolved++;
            } else if (!raw.empty() && raw[0] == '#') {
                a.bg_color = li_parse_hex_color(raw);
            } else if (!raw.empty() && raw[0] == '@') {
                auto ref = parse_ref(raw);
                if (ref.kind == RefKind::DRAWABLE) {
                    uint16_t sel_d = 0;
                    std::string p = drawable_file_for_name(ref.name, &sel_d);
                    if (!p.empty()) { a.bg_drawable = p; a.bg_drawable_density = sel_d; }
                } else if (ref.kind == RefKind::COLOR) {
                    a.bg_color = resolve_color(raw, stats);
                }
            }
        }
        else if (n == "src" || n == "srcCompat") {
            if (at.value.is_reference()) {
                uint16_t sel_d = 0;
                std::string p = drawable_file_for_resid(at.value.ref_id, &sel_d);
                if (!p.empty()) { a.src_drawable = p; a.src_drawable_density = sel_d; }
            } else if (!raw.empty() && raw[0] == '@') {
                auto ref = parse_ref(raw);
                if (ref.kind == RefKind::DRAWABLE) {
                    uint16_t sel_d = 0;
                    a.src_drawable = drawable_file_for_name(ref.name, &sel_d);
                    a.src_drawable_density = sel_d;
                }
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
        else if (n == "singleLine") a.single_line = at.value.is_bool() ? at.value.data != 0 : raw == "true";
        else if (n == "elevation") a.elevation_px = parse_dim_attr(&at, stats);
        // layout_* relative positioning params (RelativeLayout) — recorded, best-effort
        // MASTER-2 FIX-MEASURE-002b (compiled-boolean law): layout booleans
        // in release-minified AXML carry NO raw string (value type 0x12,
        // data 0/1) — raw=="true" never matched, silently dropping
        // alignParentTop/Bottom/center* (scope v140: every custom view's
        // cgrav stayed 0xffffffff). The boolean is the TYPED value; the raw
        // string is only a fallback for aapt-opt-compiled sources.
        // MASTER-2 FIX-MEASURE-002c (sentinel-OR law): a.layout_gravity's
        // "absent" sentinel is -1; `-1 | bit` stays -1, so alignParent*/
        // center* bits were DEAD on every node without an explicit
        // android:layout_gravity (scope v140 cgrav stayed 0xffffffff).
        // Accumulate from 0 when the sentinel is unset.
        #define RL_GRAVITY_OR(bit) a.layout_gravity = (a.layout_gravity >= 0 ? a.layout_gravity : 0) | (bit)
        else if (n == "layout_alignParentBottom") { bool b = at.value.is_bool() ? at.value.data != 0 : raw == "true"; if (b) { a.rel_align_parent_bottom = true; RL_GRAVITY_OR(0x50); } }
        else if (n == "layout_alignParentTop") { bool b = at.value.is_bool() ? at.value.data != 0 : raw == "true"; if (b) { a.rel_align_parent_top = true; RL_GRAVITY_OR(0x30); } }
        else if (n == "layout_centerHorizontal") { bool b = at.value.is_bool() ? at.value.data != 0 : raw == "true"; if (b) { a.rel_center_horizontal = true; RL_GRAVITY_OR(0x1); } }
        else if (n == "layout_centerInParent") { bool b = at.value.is_bool() ? at.value.data != 0 : raw == "true"; if (b) { a.rel_center_in_parent = true; RL_GRAVITY_OR(0x11); } }
        else if (n == "layout_centerVertical") { bool b = at.value.is_bool() ? at.value.data != 0 : raw == "true"; if (b) { a.rel_center_vertical = true; RL_GRAVITY_OR(0x10); } }
        // FIX-2c: RelativeLayout sibling-dependency rules. The referenced id
        // name (from "@id/name" / "@+id/name") is resolved later, at layout
        // time, against the inflated sibling set (AOSP applies rules against
        // the dependency graph, not raw ids).
        // MASTER-2 FIX-MEASURE-002: the name resolver is shared by the
        // position family AND the ALIGN_* family (the previous alignLeft/
        // alignRight branch had no compiled-reference fallback, so rules
        // like layout_alignLeft="@id/scope" — value type 0x03, no raw
        // string — resolved to EMPTY and were silently dropped; ground
        // truth org.billthefarmer.scope v140 res/v9.xml XScale).
        else if (n == "layout_below" || n == "layout_above" ||
                 n == "layout_toRightOf" || n == "layout_toLeftOf" ||
                 n == "layout_alignLeft" || n == "layout_alignRight" ||
                 n == "layout_alignTop" || n == "layout_alignBottom") {
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
            else if (n == "layout_toLeftOf") a.rel_left_of = nm;
            // ALIGN_* edge alignment — own fields, NOT aliases of the
            // position family (AOSP RelativeLayout.ALIGN_LEFT sets mLeft to
            // the anchor's left EDGE; toLeftOf sets mRight BEFORE the
            // anchor's left edge).
            else if (n == "layout_alignLeft") a.rel_align_left = nm;
            else if (n == "layout_alignRight") a.rel_align_right = nm;
            else if (n == "layout_alignTop") a.rel_align_top = nm;
            else a.rel_align_bottom = nm;
        }
        // MASTER-2 FIX-MEASURE-002: alignParentLeft/Right had NO parsing at
        // all (only Top/Bottom mapped into layout_gravity bits) — scope's
        // YScale/Unit (alignParentLeft) and Scope/XScale (alignParentRight)
        // lost those anchors.
        else if (n == "layout_alignParentLeft") { a.rel_align_parent_left = at.value.is_bool() ? at.value.data != 0 : raw == "true"; }
        else if (n == "layout_alignParentRight") { a.rel_align_parent_right = at.value.is_bool() ? at.value.data != 0 : raw == "true"; }
    }

    // Apply to node
    node.text = a.text;
    node.hint = a.hint;
    if (a.text_size_px > 0) node.text_size_px = a.text_size_px;
    else if (a.style_text_size_px > 0) {
        // GOLDEN-03 §8: style-bag textSize now reaches the node (AOSP order:
        // view explicit attrs win over style attrs; appearance below wins
        // only when no style provided one — TextView applyTextAppearance).
        node.text_size_px = a.style_text_size_px;
        node.text_size_sp = a.style_text_size_px / metrics_.density;
    }
    else if (a.appearance_resolved && a.appearance_text_size_px > 0) {
        // G46/GOLDEN-03 §8: the appearance px was produced by the canonical
        // complexToDimensionPixelSize law at resolution time (22sp → 58px).
        node.text_size_px = a.appearance_text_size_px;
        node.text_size_sp = a.appearance_text_size_px / metrics_.density;
        std::cerr << "[G46-TEXTAPPEARANCE] TextAppearance textSize="
                  << a.appearance_text_size_px << "px (density="
                  << metrics_.density * metrics_.scale_fonts << ")\n";
    }
    if (a.text_color != 0) node.text_color = a.text_color;
    else if (a.style_text_color != 0) node.text_color = a.style_text_color;   // GOLDEN-03 §8
    node.text_style = a.text_style;
    node.text_bold = (a.text_style & 1) != 0;
    node.text_italic = (a.text_style & 2) != 0;
    node.font_family = a.font_family;  // G32
    node.line_spacing_mult = a.line_spacing_mult;      // G47
    node.line_spacing_add_px = a.line_spacing_add_px;  // G47
    node.include_font_pad = a.include_font_pad;        // G47
    node.elegant_text_height = a.elegant_text_height;  // G36
    node.padding_left = a.pl + a.padding_all;
    node.padding_top = a.pt + a.padding_all;
    node.padding_right = a.pr + a.padding_all;
    node.padding_bottom = a.pb + a.padding_all;
    if (a.orientation >= 0) node.orientation = a.orientation;
    if (a.gravity >= 0) { node.text_gravity = a.gravity; node.container_gravity = a.gravity; node.gravity_set = true; }
    if (a.layout_gravity >= 0) node.child_gravity = a.layout_gravity;
    node.layout_weight = a.layout_weight;
    node.weight_sum = a.weight_sum;                 // G04 §9: weightSum law
    node.weight_sum_valid = a.weight_sum_valid;
    node.lp_margin_left = a.ml; node.lp_margin_top = a.mt;
    node.lp_margin_right = a.mr; node.lp_margin_bottom = a.mb;
    node.lp_width = a.layout_width; node.lp_height = a.layout_height;
    // M3 FIX-M3-002: style-bag layout params — AOSP obtainStyledAttributes
    // precedence: the direct XML attribute wins; when the XML is silent the
    // style= bag (and its parent chain) supplies layout_width/height/weight/
    // margin. Ground truth: headingcalculator keypad_button (0dp + weight 1
    // + match_height from the style bag, no direct layout attrs in XML).
    if (!a.width_set && a.style_layout_width != INT_MIN)
        node.lp_width = a.style_layout_width;
    if (!a.height_set && a.style_layout_height != INT_MIN)
        node.lp_height = a.style_layout_height;
    if (!a.weight_set && a.style_layout_weight >= 0)
        node.layout_weight = a.style_layout_weight;
    if (!a.margin_set && a.style_margin_all != INT_MIN) {
        node.lp_margin_left = node.lp_margin_right =
        node.lp_margin_top = node.lp_margin_bottom = a.style_margin_all;
    }
    node.visibility = a.visibility;
    node.clickable = a.clickable || !a.onClick.empty();
    node.num_lines = a.num_lines;
    if (!a.onClick.empty()) node.onClick_handler = a.onClick;
    // FIX-2c: relative-layout sibling rules onto the node
    node.rel_below_name = a.rel_below;
    node.rel_above_name = a.rel_above;
    node.rel_right_of_name = a.rel_right_of;
    node.rel_left_of_name = a.rel_left_of;
    // MASTER-2 FIX-MEASURE-002: ALIGN_* family + alignParentLeft/Right
    node.rel_align_left_name = a.rel_align_left;
    node.rel_align_right_name = a.rel_align_right;
    node.rel_align_top_name = a.rel_align_top;
    node.rel_align_bottom_name = a.rel_align_bottom;
    node.rel_align_parent_left = a.rel_align_parent_left;
    node.rel_align_parent_right = a.rel_align_parent_right;
    node.rel_align_parent_top = a.rel_align_parent_top;
    node.rel_align_parent_bottom = a.rel_align_parent_bottom;
    node.rel_center_in_parent = a.rel_center_in_parent;
    node.rel_center_horizontal = a.rel_center_horizontal;
    node.rel_center_vertical = a.rel_center_vertical;
    if (a.bg_color != 0) { node.bg_color = a.bg_color; node.bg_from_xml = true; }
    if (!a.bg_drawable.empty()) {
        node.bg_drawable_path = a.bg_drawable; node.bg_from_xml = true;
        node.bg_drawable_density = a.bg_drawable_density;   // G04 §4
    }
    if (!a.src_drawable.empty()) {
        node.src_drawable_path = a.src_drawable;
        node.src_density = a.src_drawable_density;          // G04 §4
    }
    // width/height semantics on node
    node.width = a.layout_width;
    node.height = a.layout_height;
}

// ---------------------------------------------------------------------------
// inflate entry points
// ---------------------------------------------------------------------------
uint32_t LayoutInflater::inflate_layout_resid(framework::ViewShadow* views, uint32_t layout_resid,
                                              InflateStats& stats, uint32_t parent_view_id) {
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
    // inflate root element as the content root. parent_view_id != 0 is the
    // LayoutInflater.inflate(resId, root[, attachToRoot=true]) path — the
    // inflated root attaches INTO the given parent (G11 FIX-G11-002).
    uint32_t root = inflate_element(views, parser.root(), parent_view_id, stats);
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

// ── G04 §8: drawable intrinsic size (AOSP Drawable.getIntrinsicWidth law) ──
// ImageView.onMeasure (ImageView.java L1147) uses the drawable's intrinsic
// size as the content dimension. The intrinsic size of a BitmapDrawable is
// the encoded bitmap size SCALED by targetDensity/inDensity
// (BitmapDrawable.cpp scaleFromDensity). Header probe only — no decode
// (measure must not pay decode cost; the renderer decodes at draw time).
bool LayoutInflater::image_intrinsic_size(const std::string& path,
                                          uint16_t sel_density,
                                          int* out_w, int* out_h) {
    if (path.empty() || !out_w || !out_h) return false;
    auto it = image_probe_cache_.find(path);
    if (it == image_probe_cache_.end()) {
        auto bytes = apk_.extract_entry_cached(path);
        renderer::ImageSizeProbe p;
        if (bytes.empty() || !renderer::probe_image_size(bytes, &p)) {
            image_probe_cache_[path] = {-1, -1};
            return false;
        }
        it = image_probe_cache_.emplace(path, std::make_pair(p.width, p.height)).first;
    }
    if (it->second.first <= 0 || it->second.second <= 0) return false;
    int w = it->second.first, h = it->second.second;
    // BitmapFactory density law: 0 → DENSITY_DEFAULT(160); DENSITY_NONE → no
    // scale; else scale by device/selected (the single-device law — the same
    // device_config() the config matcher uses).
    uint16_t src_d = (sel_density == 0xFFFF) ? 0 : (sel_density ? sel_density : 160);
    if (src_d > 0) {
        uint16_t tgt = device_config().density;
        if (tgt > 0 && src_d != tgt) {
            float s = float(tgt) / float(src_d);
            w = std::max(1, (int)std::lround(w * s));
            h = std::max(1, (int)std::lround(h * s));
        }
    }
    *out_w = w;
    *out_h = h;
    return true;
}

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

    auto is_container_node = [&](const framework::ViewShadow::ViewNode* n) -> bool {
        const std::string& cd = n->class_desc;
        // G10 FIX-G10-002: superclass-chain law first — any ViewGroup
        // subclass (incl. app classes like CalculatorDisplay extends
        // LinearLayout) is a container even when its leaf class name does
        // not contain the ancestor's substring.
        if (is_a(cd, "Landroid/view/ViewGroup;")) return true;
        return cd.find("Layout") != std::string::npos ||
               cd.find("ScrollView") != std::string::npos ||
               cd.find("ListView") != std::string::npos ||
               cd.find("ViewGroup") != std::string::npos ||
               cd.find("Toolbar") != std::string::npos ||
               cd.find("ViewPager") != std::string::npos ||
               cd.find("RecyclerView") != std::string::npos;
    };

    // -----------------------------------------------------------------------
    // measure(vid, spec_w, spec_h) -> desired (w, h) including own padding.
    // Children are measured FIRST (bottom-up) exactly like AOSP.
    // -----------------------------------------------------------------------
    std::function<std::pair<int,int>(uint32_t, const Spec&, const Spec&, int)> measure =
        [&](uint32_t vid, const Spec& sw, const Spec& sh, int depth) -> std::pair<int,int> {
        auto* n = views->find_node(vid);
        if (!n) return {0, 0};
        // G12 diagnostic (opt-in): incoming specs + container classification — level 3.
        if (getenv("U007_LAYOUT_DEBUG") &&
            std::string(getenv("U007_LAYOUT_DEBUG") ? getenv("U007_LAYOUT_DEBUG") : "") == "3") {
            static const std::string mode_names[] = {"UNSPEC", "EXACTLY", "AT_MOST"};
            fprintf(stderr, "[U007-SPEC] view %u %s spec=%d/%s x %d/%s depth=%d container=%d vgsub=%d llsub=%d\n",
                    vid, n->class_desc.c_str(), sw.size,
                    mode_names[(int)sw.mode].c_str(), sh.size,
                    mode_names[(int)sh.mode].c_str(), depth,
                    (int)is_container_node(n),
                    (int)is_a(n->class_desc, "Landroid/view/ViewGroup;"),
                    (int)is_a(n->class_desc, "Landroid/widget/LinearLayout;"));
        }
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
        const bool parent_ll = is_a(n->class_desc, "Landroid/widget/LinearLayout;");
        // MASTER CAMPAIGN FIX (F10 real-DEX onMeasure): custom leaf Views
        // whose DEX chain overrides onMeasure execute the REAL override
        // through the engine hook (View.measure → onMeasure →
        // setMeasuredDimension). The override is authoritative for its
        // subtree measure; the returned size becomes the content size.
        if (!is_container_node(n) && n->overrides_on_measure &&
            custom_view_measure_hook_) {
            auto encode = [](const Spec& s) -> int {
                // Android MeasureSpec encoding: mode in the top 2 bits.
                int mode_bits = s.mode == M_EXACTLY ? 1
                              : s.mode == M_AT_MOST ? 2 : 0;
                return (mode_bits << 30) | (s.size & 0x3FFFFFFF);
            };
            int ow = 0, oh = 0;
            if (custom_view_measure_hook_(vid, encode(sw), encode(sh), ow, oh)) {
                n->measured_width = ow;
                n->measured_height = oh;
                return {ow, oh};
            }
        }
        // G10 FIX-G10-001 (AOSP LinearLayout.java): the orientation field is
        // `mOrientation = a.getInt(..., HORIZONTAL)` with the field itself
        // initialized to HORIZONTAL — an orientation that was never set
        // (XML omitted the attribute / programmatic construction) means
        // HORIZONTAL. ViewNode keeps -1 as the "unset" evidence value; the
        // layout law consumes unset as horizontal at every decision point.
        const bool horiz_ll = n->orientation != 1;
        // ===================================================================
        // MASTER-2 FIX-MEASURE-002 (§13): AOSP RelativeLayout measure law.
        // (RelativeLayout.java, android-15.0.0_r1 onMeasure). Previously RL
        // children were measured in declaration order with plain
        // ViewGroup.getChildMeasureSpec specs — a wrap_content child
        // anchored to siblings (below=/toRightOf=/alignParentRight=...)
        // measured at FULL available size regardless of its anchors, and
        // unparsed rules (alignLeft/alignTop/alignBottom/
        // alignParentLeft/alignParentRight) left whole constraint families
        // missing. Evidence: org.billthefarmer.scope v140 res/v9.xml —
        // Scope (wrap×wrap, toRightOf=yscale, above=xscale,
        // alignParentTop+Right) and Unit measured 0x0/1080x1920 where AOSP
        // resolves Scope to EXACTLY(1035)xEXACTLY(1860) and Unit to
        // EXACTLY(45)xEXACTLY(60) at 1080x1920.
        //
        // AOSP structure implemented here:
        //   1. two dependency-sorted passes (horizontal, vertical) —
        //      anchors measured + positioned before their dependents;
        //   2. applyHorizontalSizeRules / applyVerticalSizeRules — resolve
        //      the child's mLeft/mRight/mTop/mBottom from sibling anchors
        //      (+ their margins) or parent edges;
        //   3. getChildMeasureSpec — constraint-aware spec derivation
        //      (both edges fixed → EXACTLY(end-start); explicit size →
        //      EXACTLY(min(maxAvailable, size)); match_parent →
        //      EXACTLY(maxAvailable); wrap → AT_MOST(maxAvailable));
        //   4. positionChildHorizontal/Vertical — cache the remaining edge
        //      from the measured size at MEASURE time (AOSP onLayout only
        //      replays these cached edges).
        // Hostile deviation (documented): AOSP throws
        // "IllegalStateException: circular dependency in RelativeLayout";
        // the runtime falls back to declaration order + diagnostic so the
        // hostile battery's no-crash law holds.
        // ===================================================================
        const bool is_rl_container =
            container && is_a(n->class_desc, "Landroid/widget/RelativeLayout;");
        int content_w = 0, content_h = 0;
        bool rl_edges_aggregated = false;
        if (is_rl_container) {
            const int NOT_SET = INT_MIN;
            struct Edge { int l = NOT_SET, r = NOT_SET, t = NOT_SET, b = NOT_SET; };
            std::map<uint32_t, Edge> edges;

            auto name_to_id = [&](const std::string& nm) -> uint32_t {
                if (nm.empty()) return 0;
                for (uint32_t cid : n->children) {
                    auto* cn = views->find_node(cid);
                    if (cn && cn->visibility != 8 && cn->android_id_name == nm)
                        return cid;
                }
                return 0;
            };

            // Kahn topological sort over one axis' anchor rules (AOSP
            // DependencyGraph.getSortedViews). Self-dependency ignored
            // (AOSP da3003 law); cycle → declaration order + diagnostic.
            auto topo = [&](auto&& deps_of) -> std::vector<size_t> {
                const size_t N = n->children.size();
                std::vector<size_t> indeg(N, 0), order;
                std::vector<std::vector<size_t>> adj(N);
                for (size_t i = 0; i < N; i++)
                    for (uint32_t dep : deps_of(i)) {
                        if (!dep) continue;
                        for (size_t j = 0; j < N; j++)
                            if (j != i && n->children[j] == dep) {
                                adj[j].push_back(i);
                                indeg[i]++;
                            }
                    }
                std::vector<size_t> ready;
                for (size_t i = 0; i < N; i++)
                    if (!indeg[i]) ready.push_back(i);
                while (!ready.empty()) {
                    size_t u = ready.back(); ready.pop_back();
                    order.push_back(u);
                    for (size_t v : adj[u])
                        if (--indeg[v] == 0) ready.push_back(v);
                }
                if (order.size() != N) {
                    if (getenv("U007_LAYOUT_DEBUG"))
                        fprintf(stderr, "[U007-LAYOUT] RelativeLayout circular "
                                        "dependency — declaration order fallback\n");
                    order.resize(N);
                    for (size_t i = 0; i < N; i++) order[i] = i;
                }
                return order;
            };
            auto horiz_deps = [&](size_t i) -> std::vector<uint32_t> {
                auto* cn = views->find_node(n->children[i]);
                if (!cn) return {};
                return {name_to_id(cn->rel_right_of_name),
                        name_to_id(cn->rel_left_of_name),
                        name_to_id(cn->rel_align_left_name),
                        name_to_id(cn->rel_align_right_name)};
            };
            auto vert_deps = [&](size_t i) -> std::vector<uint32_t> {
                auto* cn = views->find_node(n->children[i]);
                if (!cn) return {};
                return {name_to_id(cn->rel_below_name),
                        name_to_id(cn->rel_above_name),
                        name_to_id(cn->rel_align_top_name),
                        name_to_id(cn->rel_align_bottom_name)};
            };

            // AOSP getChildMeasureSpec (RelativeLayout constraint law).
            auto rl_child_spec = [&](int start, int end, int childSize,
                                     int startMargin, int endMargin,
                                     int startPad, int endPad,
                                     int mySize) -> Spec {
                const bool isUnspec = mySize < 0;
                if (isUnspec) {
                    if (start != NOT_SET && end != NOT_SET)
                        return {std::max(0, end - start), M_EXACTLY};
                    if (childSize >= 0) return {childSize, M_EXACTLY};
                    return {0, M_UNSPEC};
                }
                const int ts = start == NOT_SET ? startPad + startMargin : start;
                const int te = end == NOT_SET ? mySize - endPad - endMargin : end;
                const int maxAvail = te - ts;
                if (start != NOT_SET && end != NOT_SET)
                    return {std::max(0, maxAvail), M_EXACTLY};
                if (childSize >= 0)
                    return {maxAvail >= 0 ? std::min(maxAvail, childSize)
                                          : childSize,
                            M_EXACTLY};
                if (childSize == -1) return {std::max(0, maxAvail), M_EXACTLY};
                // WRAP_CONTENT and unknown sentinels.
                if (maxAvail >= 0) return {maxAvail, M_AT_MOST};
                return {0, M_UNSPEC};
            };

            const int myWidth = sw.mode == M_UNSPEC ? -1 : sw.size;
            const int myHeight = sh.mode == M_UNSPEC ? -1 : sh.size;
            const int cg_default = n->child_gravity >= 0 ? n->child_gravity : 0;

            // ---- horizontal pass (sorted) ----
            for (size_t i : topo(horiz_deps)) {
                auto* cn = views->find_node(n->children[i]);
                if (!cn || cn->visibility == 8) { child_sizes[i] = {0, 0}; continue; }
                Edge& e = edges[n->children[i]];
                // applyHorizontalSizeRules (anchor margins included, AOSP).
                if (uint32_t a = name_to_id(cn->rel_left_of_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.r = edges[a].l - (an->lp_margin_left + cn->lp_margin_right);
                }
                if (uint32_t a = name_to_id(cn->rel_right_of_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.l = edges[a].r + (an->lp_margin_right + cn->lp_margin_left);
                }
                if (uint32_t a = name_to_id(cn->rel_align_left_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.l = edges[a].l + cn->lp_margin_left;
                }
                if (uint32_t a = name_to_id(cn->rel_align_right_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.r = edges[a].r - cn->lp_margin_right;
                }
                if (cn->rel_align_parent_left)
                    e.l = n->padding_left + cn->lp_margin_left;
                if (cn->rel_align_parent_right)
                    e.r = myWidth - n->padding_right - cn->lp_margin_right;

                const Spec wspec = rl_child_spec(e.l, e.r, cn->lp_width,
                                                 cn->lp_margin_left,
                                                 cn->lp_margin_right,
                                                 n->padding_left,
                                                 n->padding_right, myWidth);
                // measureChildHorizontal height law (modern targets:
                // mAllowBrokenMeasureSpecs=false,
                // mMeasureVerticalWithPaddingMargin=false).
                Spec hspec;
                if (myHeight < 0) {
                    if (cn->lp_height >= 0) hspec = {cn->lp_height, M_EXACTLY};
                    else hspec = {0, M_UNSPEC};
                } else if (cn->lp_height == -1) {
                    hspec = {std::max(0, myHeight), M_EXACTLY};
                } else {
                    hspec = {std::max(0, myHeight), M_AT_MOST};
                }
                auto sz = measure(n->children[i], wspec, hspec, depth + 1);
                child_sizes[i] = sz;
                // positionChildHorizontal — cache edges from measured width.
                if (e.l == NOT_SET && e.r != NOT_SET) {
                    e.l = e.r - sz.first;
                } else if (e.l != NOT_SET && e.r == NOT_SET) {
                    e.r = e.l + sz.first;
                } else if (e.l == NOT_SET && e.r == NOT_SET) {
                    if ((cn->rel_center_in_parent || cn->rel_center_horizontal) &&
                        myWidth >= 0 && sw.mode != M_EXACTLY) {
                        // centerHorizontal law (wrap RL → positionAtEdge).
                        e.l = (myWidth - sz.first) / 2;
                        e.r = e.l + sz.first;
                    } else {
                        e.l = n->padding_left + cn->lp_margin_left;
                        e.r = e.l + sz.first;
                    }
                }
                // FIX-MEASURE-002e: cache for the onLayout replay.
                cn->rl_cached_left = e.l;
                cn->rl_cached_right = e.r;
                cn->rl_edges_valid = true;
            }

            // ---- vertical pass (sorted) ----
            for (size_t i : topo(vert_deps)) {
                auto* cn = views->find_node(n->children[i]);
                if (!cn || cn->visibility == 8) { child_sizes[i] = {0, 0}; continue; }
                Edge& e = edges[n->children[i]];
                // applyVerticalSizeRules.
                if (uint32_t a = name_to_id(cn->rel_above_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.b = edges[a].t - (an->lp_margin_top + cn->lp_margin_bottom);
                }
                if (uint32_t a = name_to_id(cn->rel_below_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.t = edges[a].b + (an->lp_margin_bottom + cn->lp_margin_top);
                }
                if (uint32_t a = name_to_id(cn->rel_align_top_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.t = edges[a].t + cn->lp_margin_top;
                }
                if (uint32_t a = name_to_id(cn->rel_align_bottom_name)) {
                    auto* an = views->find_node(a);
                    if (an) e.b = edges[a].b - cn->lp_margin_bottom;
                }
                // MASTER-2 FIX-MEASURE-002d: explicit RL rule booleans
                // (the legacy gravity-bit masks overlap — 0x50 & 0x30 =
                // 0x10 — and cannot encode RL rules unambiguously).
                if (cn->rel_align_parent_top)
                    e.t = n->padding_top + cn->lp_margin_top;
                if (cn->rel_align_parent_bottom)
                    e.b = myHeight - n->padding_bottom - cn->lp_margin_bottom;

                const Spec wspec = rl_child_spec(e.l, e.r, cn->lp_width,
                                                 cn->lp_margin_left,
                                                 cn->lp_margin_right,
                                                 n->padding_left,
                                                 n->padding_right, myWidth);
                const Spec hspec = rl_child_spec(e.t, e.b, cn->lp_height,
                                                 cn->lp_margin_top,
                                                 cn->lp_margin_bottom,
                                                 n->padding_top,
                                                 n->padding_bottom, myHeight);
                auto sz = measure(n->children[i], wspec, hspec, depth + 1);
                child_sizes[i] = sz;
                // positionChildVertical — cache edges from measured height.
                if (e.t == NOT_SET && e.b != NOT_SET) {
                    e.t = e.b - sz.second;
                } else if (e.t != NOT_SET && e.b == NOT_SET) {
                    e.b = e.t + sz.second;
                } else if (e.t == NOT_SET && e.b == NOT_SET) {
                    if ((cn->rel_center_in_parent || cn->rel_center_vertical) &&
                        myHeight >= 0 && sh.mode != M_EXACTLY) {
                        e.t = (myHeight - sz.second) / 2;
                        e.b = e.t + sz.second;
                    } else {
                        e.t = n->padding_top + cn->lp_margin_top;
                        e.b = e.t + sz.second;
                    }
                }
                // FIX-MEASURE-002e: cache for the onLayout replay.
                cn->rl_cached_top = e.t;
                cn->rl_cached_bottom = e.b;
            }

            // AOSP wrap-RL content: max extents over resolved EDGES (not
            // child content sizes), margins included.
            content_w = 0; content_h = 0;
            for (size_t i = 0; i < n->children.size(); i++) {
                auto* cn = views->find_node(n->children[i]);
                if (!cn || cn->visibility == 8) continue;
                const Edge& e = edges[n->children[i]];
                if (e.r != INT_MIN) content_w = std::max(content_w, e.r + cn->lp_margin_right);
                if (e.b != INT_MIN) content_h = std::max(content_h, e.b + cn->lp_margin_bottom);
            }
            (void)cg_default;
            rl_edges_aggregated = true;
        } else for (size_t i = 0; i < n->children.size(); i++) {
            auto* cn = views->find_node(n->children[i]);
            if (!cn) { child_sizes[i] = {0, 0}; continue; }
            int cw_ = cn->lp_width  == INT_MIN ? -2 : cn->lp_width;
            int ch_ = cn->lp_height == INT_MIN ? -2 : cn->lp_height;
            Spec csw = child_spec(sw, hpad + cn->lp_margin_left + cn->lp_margin_right, cw_);
            Spec csh = child_spec(sh, vpad + cn->lp_margin_top + cn->lp_margin_bottom, ch_);
            // G04 §9 (LinearLayout.java L855 useExcessSpace law): a
            // 0dp+weight child is NOT measured at its content size in the
            // first pass — it contributes only its margins to mTotalLength
            // and is sized from scratch with an EXACTLY share in the weight
            // pass. Measure it with an EXACTLY-0 main-axis spec (cross axis
            // still normal) so its cross-axis content size stays correct.
            if (parent_ll && cn->layout_weight > 0) {
                if (!horiz_ll && ch_ == 0) csh = {0, M_EXACTLY};
                if (horiz_ll && cw_ == 0)  csw = {0, M_EXACTLY};
            }
            // ScrollView measures its single child with UNSPECIFIED height
            // (AOSP ScrollView.onMeasure law).
            if (n->class_desc.find("ScrollView;") != std::string::npos &&
                n->class_desc.find("Horizontal") == std::string::npos)
                csh = {std::max(0, sh.size - vpad), M_UNSPEC};
            child_sizes[i] = measure(n->children[i], csw, csh, depth + 1);
        }

        // ===================================================================
        // MASTER-2 FIX-MEASURE-004 (§16): AOSP LinearLayout weight re-
        // distribution happens INSIDE onMeasure (measureVertical
        // L985-1045 / measureHorizontal) — EVERY measure pass must produce
        // the weighted share, because a later measure-only pass (renderer,
        // re-layout) would otherwise reset 0dp+weight children to their
        // first-pass EXACTLY(0) size. Evidence: headingcalculator v1 —
        // weight=1000 button rows measured EXACTLY(480) in the layout-
        // phase weight pass, then a renderer measure pass reset them to
        // 1080x0 (SPEC trace: depth=3 EXACTLY(0) with no re-measure
        // afterwards). The layout-phase weight law stays: it recomputes
        // the same shares for positioning (idempotent).
        // ===================================================================
        if (!is_rl_container && container &&
            is_a(n->class_desc, "Landroid/widget/LinearLayout;") &&
            !is_a(n->class_desc, "Landroid/widget/TableLayout;") &&
            !is_a(n->class_desc, "Landroid/widget/TableRow;")) {
            const bool main_horiz = n->orientation != 1;   // FIX-G10-001
            const Spec& mspec = main_horiz ? sw : sh;
            const Spec& cspec = main_horiz ? sh : sw;
            if (mspec.mode != M_UNSPEC) {
                const int mpad = main_horiz ? hpad : vpad;
                const int cpad = main_horiz ? vpad : hpad;
                std::vector<size_t> vis;
                for (size_t i = 0; i < n->children.size(); i++) {
                    auto* cn = views->find_node(n->children[i]);
                    if (cn && cn->visibility != 8) vis.push_back(i);
                }
                int total_length = 0;
                float weight_total = 0.0f;
                bool has_weight = false;
                for (size_t i : vis) {
                    auto* cn = views->find_node(n->children[i]);
                    const int m = main_horiz
                                      ? cn->lp_margin_left + cn->lp_margin_right
                                      : cn->lp_margin_top + cn->lp_margin_bottom;
                    const int lp_main = main_horiz ? cn->lp_width : cn->lp_height;
                    if (cn->layout_weight > 0) {
                        has_weight = true;
                        weight_total += cn->layout_weight / 1000.0f;
                        if (lp_main != 0)
                            total_length += (lp_main >= 0 ? lp_main
                                                          : cn->measured_width) + m;
                        else
                            total_length += m;
                    } else {
                        total_length += (lp_main >= 0 ? lp_main
                                                      : (main_horiz ? cn->measured_width
                                                                    : cn->measured_height)) + m;
                    }
                }
                if (has_weight && weight_total > 0.0f) {
                    int excess = mspec.size - mpad - total_length;
                    float rws = (n->weight_sum_valid && n->weight_sum > 0.0f)
                                    ? n->weight_sum : weight_total;
                    for (size_t i : vis) {
                        auto* cn = views->find_node(n->children[i]);
                        if (cn->layout_weight <= 0) continue;
                        const float wgt = cn->layout_weight / 1000.0f;
                        int share = 0;
                        if (rws > 0.0f) {
                            share = (int)(wgt * (float)excess / rws);
                            excess -= share;
                            rws -= wgt;
                        }
                        const int lp_main = main_horiz ? cn->lp_width
                                                       : cn->lp_height;
                        const int base = lp_main == 0 ? 0
                                       : (lp_main >= 0 ? lp_main
                                                       : (main_horiz ? cn->measured_width
                                                                     : cn->measured_height));
                        const int final_main = std::max(0, base + share);
                        // Cross-axis spec law: the weighted re-measure uses
                        // the SAME cross spec the first pass used (AOSP
                        // measureChildBeforeLayout passes the container's
                        // own spec through getChildMeasureSpec) — for a
                        // wrap/match cross child that is child_spec's
                        // mode-preserving law, NOT EXACTLY(available).
                        // FIX-MEASURE-004b: EXACTLY(available) inflated
                        // match-height buttons inside a wrap-height row to
                        // the full 1920 (unote buttons row covered the
                        // whole screen after the measure-phase weight law).
                        const int lp_cross = main_horiz ? cn->lp_height
                                                        : cn->lp_width;
                        const int cm = main_horiz
                                           ? cn->lp_margin_top + cn->lp_margin_bottom
                                           : cn->lp_margin_left + cn->lp_margin_right;
                        const Spec main_s{std::max(0, final_main), M_EXACTLY};
                        const Spec cross_s = child_spec(cspec, cm, lp_cross);
                        child_sizes[i] = main_horiz
                                             ? measure(n->children[i], main_s,
                                                       cross_s, depth + 1)
                                             : measure(n->children[i], cross_s,
                                                       main_s, depth + 1);
                    }
                }
            }
        }

        // ===================================================================
        // M3 FIX-M3-004 (§4/§6 — AOSP LinearLayout match-parent second-pass
        // remeasure, LinearLayout.java measureVertical/measureHorizontal
        // "Remeasure the match-parent children" block): a MATCH_PARENT
        // child is FIRST measured with the parent's full spec size, then
        // REMEASURED against the space LEFT by the non-match siblings —
        // EXACTLY(specSize - usedByOthers) when the container spec is
        // exact/at-most. Without the second pass a [wrap header, match
        // body] vertical pair gives the body the FULL parent height and
        // the pair overflows (headingcalculator: keypad measured
        // EXACTLY(1920) next to a 158px display → keypad rows pitched
        // 480px and the bottom rows fell off-screen; the AOSP result is
        // EXACTLY(1762) → rows share the remainder). This is a
        // measurement-semantics law (not layout-time geometry): every
        // later pass recomputes the same share.
        // ===================================================================
        if (!is_rl_container && container &&
            is_a(n->class_desc, "Landroid/widget/LinearLayout;") &&
            !is_a(n->class_desc, "Landroid/widget/TableLayout;") &&
            !is_a(n->class_desc, "Landroid/widget/TableRow;")) {
            const bool main_horiz2 = n->orientation != 1;   // FIX-G10-001
            const Spec& mspec2 = main_horiz2 ? sw : sh;
            if (mspec2.mode != M_UNSPEC) {
                const int mpad2 = main_horiz2 ? hpad : vpad;
                // 1) used = main-axis size consumed by NON-match children
                //    (final values after the weight pass above).
                int used = 0;
                bool has_match = false;
                std::vector<size_t> match_idx;
                for (size_t i = 0; i < n->children.size(); i++) {
                    auto* cn = views->find_node(n->children[i]);
                    if (!cn || cn->visibility == 8) continue;
                    const int lp_main = main_horiz2 ? cn->lp_width : cn->lp_height;
                    const int m = main_horiz2
                                      ? cn->lp_margin_left + cn->lp_margin_right
                                      : cn->lp_margin_top + cn->lp_margin_bottom;
                    if (lp_main == -1) {
                        has_match = true;
                        match_idx.push_back(i);
                    } else {
                        used += (main_horiz2 ? child_sizes[i].first
                                             : child_sizes[i].second) + m;
                    }
                }
                // 2) remeasure every match-parent child with the remainder.
                if (has_match) {
                    const int remaining =
                        std::max(0, mspec2.size - mpad2 - used);
                    const Spec& cspec2 = main_horiz2 ? sh : sw;
                    for (size_t i : match_idx) {
                        auto* cn = views->find_node(n->children[i]);
                        const int lp_cross = main_horiz2 ? cn->lp_height
                                                        : cn->lp_width;
                        const int cm = main_horiz2
                                           ? cn->lp_margin_top + cn->lp_margin_bottom
                                           : cn->lp_margin_left + cn->lp_margin_right;
                        const Spec main_s{remaining, M_EXACTLY};
                        const Spec cross_s = child_spec(cspec2, cm, lp_cross);
                        child_sizes[i] = main_horiz2
                                             ? measure(n->children[i], main_s,
                                                       cross_s, depth + 1)
                                             : measure(n->children[i], cross_s,
                                                       main_s, depth + 1);
                    }
                }
            }
        }

        if (!rl_edges_aggregated) {
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
                                              n->num_lines, face_idx,
                                              n->line_spacing_mult,
                                              n->line_spacing_add_px,
                                              n->include_font_pad,
                                              n->elegant_text_height);
                content_w = std::max(content_w, (int)std::ceil(
                    avail_w > 0 ? std::min(lay.max_line_width, avail_w)
                                : lay.max_line_width));
                content_h = std::max(content_h, (int)std::ceil(lay.block_height()));
                // Evidence: remember the measured line count (task §3 log).
                n->num_lines = (n->num_lines > 0)
                             ? std::min(n->num_lines, (int)lay.lines.size())
                             : (int)lay.lines.size();
            }
            // G04 §8 (ImageView.java onMeasure L1141+ law): the drawable's
            // density-scaled intrinsic size IS the image content dimension.
            // The 48dp default applies ONLY when no intrinsic size is
            // knowable (no file / unprobeable image) — the AOSP wrap
            // fallback for an unresolvable drawable.
            int iw = 0, ih = 0;
            if (image_intrinsic_size(n->src_drawable_path, n->src_density, &iw, &ih) ||
                image_intrinsic_size(n->image_drawable_path, n->src_density, &iw, &ih)) {
                content_w = std::max(content_w, iw);
                content_h = std::max(content_h, ih);
                n->src_w = iw; n->src_h = ih;   // evidence + draw-path reuse
            } else if (!n->src_drawable_path.empty() ||
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
            // MASTER CAMPAIGN FIX (F8 default-onMeasure law — AOSP
            // View.java getDefaultSize): a custom leaf View whose chain
            // defines NO onMeasure override measures itself with
            // getDefaultSize(suggestedMinimum, spec): AT_MOST/EXACTLY →
            // specSize (the parent-available size), NOT the content size.
            // The flag is computed by the DEX engine at constructor time
            // (class_chain_defines_method — semantic ancestry, no name
            // heuristics). Evidence: org.billthefarmer.scope v140 —
            // Scope/YScale/XScale/Unit (plain View subclasses, wrap_content)
            // measured 0x0/0x1920 under the content-only model where AOSP
            // measures them at the available size.
            if (n->aosp_default_measure && content_w == 0 && content_h == 0 &&
                n->src_drawable_path.empty() && n->image_drawable_path.empty()) {
                if (sw.mode != M_UNSPEC)
                    content_w = std::max(0, sw.size - hpad);
                if (sh.mode != M_UNSPEC)
                    content_h = std::max(0, sh.size - vpad);
            }
            // Compound minimum (AOSP getSuggestedMinimum: 0 + padding).
            content_w = std::max(content_w, 0);
            content_h = std::max(content_h, 0);
        } else {
            // ---- container: children determine content size ----
            const bool is_ll = is_a(n->class_desc, "Landroid/widget/LinearLayout;");
            const bool is_scrollv = n->class_desc.find("ScrollView") != std::string::npos &&
                                    n->class_desc.find("Horizontal") == std::string::npos;
            const bool is_scrollh = n->class_desc.find("HorizontalScrollView") != std::string::npos;
            bool horizontal = n->orientation != 1;   // FIX-G10-001: unset (-1) = HORIZONTAL
            // G12 FIX-G12-001: AOSP TableLayout stacks its rows VERTICALLY
            // (android.widget.TableLayout — rows are its only children, its
            // own LinearLayout orientation field is never XML-set). Without
            // this the table measured as a horizontal row (content_w = sum
            // of row widths).
            if (is_a(n->class_desc, "Landroid/widget/TableLayout;"))
                horizontal = false;
            if (is_scrollv) horizontal = false;
            if (is_scrollh) horizontal = true;
            if (is_a(n->class_desc, "Landroid/widget/FrameLayout;") ||
                is_a(n->class_desc, "Landroid/widget/RelativeLayout;") ||
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
        } // !rl_edges_aggregated (RL content came from resolved edges)

        // 2) resolve own lp against the incoming spec (resolveSizeAndState).
        // G04 §8 FIX (caught by the law battery): the spec size INCLUDES the
        // view's own padding (AOSP View.measure → setMeasuredDimension
        // resolves the TOTAL size against the spec; LinearLayout adds
        // mPadding* into the content BEFORE resolve). Resolving the padding-
        // exclusive content and then re-adding padding double-counted it for
        // EXACTLY/AT_MOST specs (a 1080px EXACTLY container with 100px
        // padding measured 1180px and laid children out 100px too wide).
        int lpw = n->lp_width  == INT_MIN ? -2 : n->lp_width;
        int lph = n->lp_height == INT_MIN ? -2 : n->lp_height;
        int total_content_w = content_w + hpad;
        int total_content_h = content_h + vpad;
        // MASTER-2 FIX-MEASURE-003 (AOSP resolveSizeAndState law): an
        // EXACTLY spec is the PARENT'S COMMAND and ALWAYS wins — the view's
        // own lp never enters its own resolve (LinearLayout's weight re-
        // measure constructs the spec directly via
        // makeMeasureSpec(share, EXACTLY), so a 0dp+weight child resolves
        // to its WEIGHT SHARE, not back to lp=0). The previous
        // `lph >= 0 ? lph : …` shortcut re-applied the XML 0dp on top of
        // the share: headingcalculator's weight=1000 button rows measured
        // EXACTLY(480) then collapsed to 0 (SPEC-OUT evidence: content=
        // 296x123 -> 1080x0 under EXACTLY(480)). The lp shortcut is kept
        // ONLY for non-EXACTLY specs (conservative: fixed-lp children
        // measured through paths whose spec does not encode the lp).
        int final_w = (lpw >= 0 && sw.mode != M_EXACTLY)
                          ? lpw : resolve_final(total_content_w, sw);
        int final_h = (lph >= 0 && sh.mode != M_EXACTLY)
                          ? lph : resolve_final(total_content_h, sh);
        // EXACTLY spec wins for match_parent too (already EXACTLY from
        // child_spec); explicit lp never shrinks below the spec EXACTLY size
        // when larger (AOSP chooses the child's explicit size).
        n->measured_width = final_w;
        n->measured_height = final_h;
        // G12 diagnostic (opt-in): measure result — level 3.
        if (getenv("U007_LAYOUT_DEBUG") &&
            std::string(getenv("U007_LAYOUT_DEBUG") ? getenv("U007_LAYOUT_DEBUG") : "") == "3") {
            fprintf(stderr, "[U007-SPEC-OUT] view %u %s content=%dx%d -> %dx%d\n",
                    vid, n->class_desc.c_str(), content_w, content_h,
                    final_w, final_h);
        }
        return {n->measured_width, n->measured_height};
    };

    // Root fills the screen (EXACTLY), per AOSP window measure.
    // Root spec: the window hands the content root EXACTLY(screen); the
    // root's OWN lp then shapes its spec per ViewGroup.getChildMeasureSpec
    // (explicit px → EXACTLY(lp); match_parent → EXACTLY(screen);
    // wrap_content → AT_MOST(screen)). MASTER-2 FIX-MEASURE-003 companion:
    // with resolve now spec-pure under EXACTLY, the root's explicit lp
    // must be encoded HERE (a 0-height root measures 0, not the window
    // size — g10 law test [13]).
    std::pair<int,int> root_size_first;
    {
        auto* rn = views->find_node(root_id);
        Mode rwm = M_EXACTLY, rhm = M_EXACTLY;
        int rws = metrics_.screen_width, rhs = metrics_.screen_height;
        if (rn) {
            const int lpw = rn->lp_width  == INT_MIN ? -2 : rn->lp_width;
            const int lph = rn->lp_height == INT_MIN ? -2 : rn->lp_height;
            if (lpw >= 0) rws = lpw;
            else if (lpw == -2) rwm = M_AT_MOST;
            if (lph >= 0) rhs = lph;
            else if (lph == -2) rhm = M_AT_MOST;
        }
        root_size_first = measure(root_id, {rws, rwm}, {rhs, rhm}, 0);
    }
    (void)root_size_first;

    // Full per-view geometry evidence (task §3 log format). Gated by env to
    // keep normal runs quiet; U007_LAYOUT_DEBUG=2 also dumps every node.
    if (getenv("U007_LAYOUT_DEBUG")) {
        fprintf(stderr, "[U007-LAYOUT] root measured %dx%d\n",
                root_size_first.first, root_size_first.second);
        std::function<void(uint32_t, int)> dump = [&](uint32_t vid, int depth) {
            auto* n = views->find_node(vid);
            if (!n) return;
            fprintf(stderr,
                "[U007-LAYOUT] %*sview %u %s id_name=%s lp=%d/%d weight=%d "
                "orient=%d measured=%dx%d at=(%d,%d) vis=%d clickable=%d "
                "text_size=%.1f lines=%d below='%s' above='%s' "
                "right_of='%s' left_of='%s' cgrav=0x%x text='%s'\n",
                depth * 2, "", vid, n->class_desc.c_str(),
                n->android_id_name.c_str(), n->lp_width, n->lp_height,
                n->layout_weight, n->orientation, n->measured_width,
                n->measured_height,
                n->measured_left, n->measured_top, n->visibility,
                (int)(n->clickable || !n->onClick_handler.empty()),
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
    stack.push_back({root_id, 0, 0, root_size_first.first, root_size_first.second});
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

        bool is_ll = is_a(n->class_desc, "Landroid/widget/LinearLayout;");
        bool is_fl = is_a(n->class_desc, "Landroid/widget/FrameLayout;");
        bool is_rl = is_a(n->class_desc, "Landroid/widget/RelativeLayout;");
        bool is_scroll = n->class_desc.find("ScrollView") != std::string::npos &&
                         n->class_desc.find("Horizontal") == std::string::npos;
        bool horizontal = n->orientation != 1;   // FIX-G10-001: unset (-1) = HORIZONTAL
        // G12 FIX-G12-001: TableLayout stacks rows VERTICALLY (see measure).
        if (is_ll && is_a(n->class_desc, "Landroid/widget/TableLayout;"))
            horizontal = false;

        // gather visible children + margins
        std::vector<uint32_t> kids;
        for (uint32_t cid : n->children) {
            auto* cn = views->find_node(cid);
            if (cn && cn->visibility != 8) kids.push_back(cid);
        }

        if (is_ll && (horizontal || !is_scroll) && (horizontal || true)) {
            if (horizontal) {
                // ── G04 §9: AOSP LinearLayout weight law, EXACT port ────
                // (LinearLayout.java @android-14 L1385-1445 measureHorizontal;
                //  sequential share distribution with remainingWeightSum
                //  decrement — NOT one division by the total).
                //   remainingExcess = size − mTotalLength   (may be negative →
                //                             weighted children SHRINK)
                //   remainingWeightSum = weightSum > 0 ? weightSum : totalWeight
                //   per weighted child (in order):
                //     share = (int)(childWeight * remainingExcess / remainingWeightSum)
                //     remainingExcess −= share; remainingWeightSum −= childWeight
                //     main size = (lp == 0) ? share : measuredBase + share   [≥ 0]
                // The 0dp+weight child is measured FROM SCRATCH with EXACTLY
                // share; a nonzero-base child keeps its base and takes the
                // share on top (shrinkable). Every weighted child is
                // effectively re-measured with an EXACTLY spec (second pass).
                int total_length = 0;
                float weight_total = 0.0f;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    int m = cn->lp_margin_left + cn->lp_margin_right;
                    if (cn->layout_weight > 0) {
                        weight_total += cn->layout_weight / 1000.0f;
                        if (cn->lp_width != 0)
                            total_length += (cn->lp_width >= 0 ? cn->lp_width
                                                        : cn->measured_width) + m;
                        else
                            total_length += m;   // 0dp+weight: measured from scratch
                    } else {
                        total_length += (cn->lp_width >= 0 ? cn->lp_width
                                                    : cn->measured_width) + m;
                    }
                }
                int remaining_excess = cw - total_length;   // shrinkable (§9 law)
                float remaining_weight_sum =
                    (n->weight_sum_valid && n->weight_sum > 0.0f)
                        ? n->weight_sum : weight_total;
                // sequential shares (exact AOSP rounding/decrement order)
                std::vector<int> final_w(kids.size());
                for (size_t i = 0; i < kids.size(); i++) {
                    auto* cn = views->find_node(kids[i]);
                    if (cn->layout_weight > 0 && weight_total > 0.0f) {
                        float wgt = cn->layout_weight / 1000.0f;
                        int share = 0;
                        if (remaining_weight_sum > 0.0f) {
                            share = (int)(wgt * (float)remaining_excess /
                                          remaining_weight_sum);
                            remaining_excess -= share;
                            remaining_weight_sum -= wgt;
                        }
                        int base = cn->lp_width == 0 ? 0
                                 : (cn->lp_width >= 0 ? cn->lp_width
                                                      : cn->measured_width);
                        final_w[i] = std::max(0, base + share);
                        // AOSP second pass (LinearLayout.java L1435): EXACTLY
                        // re-measure of the weighted subtree (see vertical).
                        int cross = std::max(0, ch - cn->lp_margin_top - cn->lp_margin_bottom);
                        Spec rsh = cn->lp_height >= 0 ? Spec{cn->lp_height, M_EXACTLY}
                                 : cn->lp_height == -1 ? Spec{cross, M_EXACTLY}
                                 : Spec{cross, M_AT_MOST};
                        measure(kids[i], {std::max(0, final_w[i]), M_EXACTLY}, rsh, 0);
                    } else if (cn->lp_width >= 0) {
                        final_w[i] = cn->lp_width;
                    } else {
                        final_w[i] = cn->measured_width;
                    }
                }
                // FIND-GRAVITY-VERTICAL FIX (AOSP LinearLayout@1cdfff55
                // layoutHorizontal): the container's main-axis gravity
                // (mGravity & HORIZONTAL_GRAVITY_MASK) positions the WHOLE
                // CHILD BLOCK when leftover width exists — LEFT (default),
                // CENTER_HORIZONTAL → half the leftover left of the block,
                // RIGHT → all of it. Child layout_gravity still governs only
                // the cross axis (below), identical to AOSP.
                int content_w = 0;
                for (size_t i = 0; i < kids.size(); i++) {
                    auto* cn = views->find_node(kids[i]);
                    content_w += final_w[i] + cn->lp_margin_left + cn->lp_margin_right;
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
                for (size_t i = 0; i < kids.size(); i++) {
                    uint32_t cid = kids[i];
                    auto* cn = views->find_node(cid);
                    x += cn->lp_margin_left;
                    int w = final_w[i];
                    // G04 §8 FIX: cross axis uses the measured height (same
                    // View.layout law as the vertical fix above).
                    int h = cn->lp_height >= 0 ? cn->lp_height : cn->measured_height;
                    int y = ct;
                    // EXT-AOSP-001: same container-gravity fallback for the
                    // horizontal row's cross axis (LinearLayout.java L1777-1778).
                    int vg = cn->child_gravity >= 0 ? cn->child_gravity
                           : (n->gravity_set ? n->container_gravity : -1);
                    // Cross-axis vertical law (EXT-AOSP-001), masked-field
                    // equality: BOTTOM (0x50 field) → bottom; otherwise
                    // center (covers CENTER 0x10 and the no-bit default).
                    // Pre-fix a bare `& 0x50` test misfired on CENTER 0x11.
                    // FIND-G06AUDIT-004: the margin law holds on this axis
                    // too (layoutHorizontal placeChild: topMargin added on
                    // TOP/center, rightMargin subtracted on BOTTOM).
                    int cmt = cn->lp_margin_top, cmb = cn->lp_margin_bottom;
                    if (vg >= 0) {
                        int vf = vg & 0x70;
                        if (vf == 0x50) y = ct + ch - h - cmb;
                        else            y = ct + (ch - h) / 2 + cmt - cmb;
                    } else {
                        y = ct + cmt;
                    }
                    if (w > cw) w = cw;
                    // G04 §9: the weight distribution IS the EXACTLY
                    // re-measure — record the final main size on the node so
                    // evidence/dumps see post-weight measured dims.
                    cn->measured_width = w;
                    stack.push_back({cid, x, y, w, h});
                    x += w + cn->lp_margin_right;
                }
            } else {
                // ── G04 §9: AOSP LinearLayout weight law, EXACT port ────
                // (LinearLayout.java @android-14 L985-1045 measureVertical.)
                // Sequential share distribution with remainingWeightSum
                // decrement; 0dp+weight measured from scratch with EXACTLY
                // share; nonzero-base child keeps base and takes the share on
                // top (shrinkable when remainingExcess < 0). weightSum caps
                // the sum when > 0.
                int total_length = 0;
                float weight_total = 0.0f;
                for (uint32_t cid : kids) {
                    auto* cn = views->find_node(cid);
                    int m = cn->lp_margin_top + cn->lp_margin_bottom;
                    if (cn->layout_weight > 0) {
                        weight_total += cn->layout_weight / 1000.0f;
                        if (cn->lp_height != 0)
                            total_length += (cn->lp_height >= 0 ? cn->lp_height
                                                          : cn->measured_height) + m;
                        else
                            total_length += m;   // 0dp+weight: measured from scratch
                    } else {
                        total_length += (cn->lp_height >= 0 ? cn->lp_height
                                                      : cn->measured_height) + m;
                    }
                }
                int remaining_excess = ch - total_length;   // shrinkable (§9 law)
                float remaining_weight_sum =
                    (n->weight_sum_valid && n->weight_sum > 0.0f)
                        ? n->weight_sum : weight_total;
                std::vector<int> final_h(kids.size());
                for (size_t i = 0; i < kids.size(); i++) {
                    auto* cn = views->find_node(kids[i]);
                    if (cn->layout_weight > 0 && weight_total > 0.0f) {
                        float wgt = cn->layout_weight / 1000.0f;
                        int share = 0;
                        if (remaining_weight_sum > 0.0f) {
                            share = (int)(wgt * (float)remaining_excess /
                                          remaining_weight_sum);
                            remaining_excess -= share;
                            remaining_weight_sum -= wgt;
                        }
                        int base = cn->lp_height == 0 ? 0
                                 : (cn->lp_height >= 0 ? cn->lp_height
                                                       : cn->measured_height);
                        final_h[i] = std::max(0, base + share);
                        // AOSP second pass (LinearLayout.java L1031): the
                        // weighted child (and its whole subtree) is RE-
                        // MEASURED with an EXACTLY share on the main axis —
                        // first-pass specs were resolved against the
                        // pre-weight container size and are stale.
                        int cross = std::max(0, cw - cn->lp_margin_left - cn->lp_margin_right);
                        Spec rsw = cn->lp_width >= 0 ? Spec{cn->lp_width, M_EXACTLY}
                                 : cn->lp_width == -1 ? Spec{cross, M_EXACTLY}
                                 : Spec{cross, M_AT_MOST};
                        measure(kids[i], rsw, {std::max(0, final_h[i]), M_EXACTLY}, 0);
                    } else if (cn->lp_height >= 0) {
                        final_h[i] = cn->lp_height;
                    } else {
                        final_h[i] = cn->measured_height;
                    }
                }
                // FIND-GRAVITY-VERTICAL FIX (AOSP LinearLayout@1cdfff55
                // layoutVertical): the container's main-axis gravity
                // (mGravity & VERTICAL_GRAVITY_MASK) positions the whole
                // CHILD BLOCK when leftover height exists — TOP (default),
                // CENTER_VERTICAL → half the leftover above the block,
                // BOTTOM → all of it. Child layout_gravity still governs only
                // the cross axis (below), identical to AOSP.
                int content_h = 0;
                for (size_t i = 0; i < kids.size(); i++) {
                    auto* cn = views->find_node(kids[i]);
                    content_h += final_h[i] + cn->lp_margin_top + cn->lp_margin_bottom;
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
                for (size_t i = 0; i < kids.size(); i++) {
                    uint32_t cid = kids[i];
                    auto* cn = views->find_node(cid);
                    y += cn->lp_margin_top;
                    int h = final_h[i];
                    // G04 §8 FIX: layout consumes the MEASURED cross size
                    // (View.layout law). The old recomputation
                    // `lp == -1 ? cw : measured` ignored the margins the
                    // measure pass had already subtracted, inflating
                    // match_parent children back to the full content width.
                    int w = cn->lp_width >= 0 ? cn->lp_width : cn->measured_width;
                    int x = cl;
                    // EXT-AOSP-001 (LinearLayout.java@1cdfff55 L1284/L1466):
                    // `lp.gravity < 0 ? mGravity : lp.gravity` — a child with
                    // no explicit layout_gravity inherits the container's
                    // gravity (set via XML android:gravity or the programmatic
                    // setGravity intercept). child_gravity == -1 encodes
                    // "unset" identically to AOSP's -1 sentinel.
                    int vg = cn->child_gravity >= 0 ? cn->child_gravity
                           : (n->gravity_set ? n->container_gravity : -1);
                    // FIND-G06AUDIT-004 (LinearLayout.layoutVertical
                    // placeChild law): every branch adds the child's own
                    // horizontal margins — LEFT (default) childLeft =
                    // paddingLeft + lp.leftMargin; CENTER adds
                    // leftMargin − rightMargin; RIGHT subtracts rightMargin.
                    int cml = cn->lp_margin_left, cmr = cn->lp_margin_right;
                    if (vg >= 0 && (vg & 0x1)) x = cl + (cw - w) / 2 + cml - cmr;
                    else if (vg >= 0 && (vg & 0x7) == 0x5) x = cl + cw - w - cmr;
                    else x = cl + cml;
                    if (w > cw) w = cw;
                    // G04 §9: the weight distribution IS the EXACTLY
                    // re-measure — record the final main size on the node so
                    // evidence/dumps see post-weight measured dims.
                    cn->measured_height = h;
                    // MASTER-2 §22 diagnostic (U007_LAYOUT_DEBUG=4): vertical
                    // stacking contract per child.
                    if (getenv("U007_LAYOUT_DEBUG") &&
                        std::string(getenv("U007_LAYOUT_DEBUG")) == "4") {
                        fprintf(stderr,
                                "[VSTACK] parent=%u %s kid=%u %s y=%d h=%d "
                                "lp=%d/%d measured=%dx%d kids=%zu\n",
                                t.id, n->class_desc.c_str(), cid,
                                cn->class_desc.c_str(), y, h, cn->lp_width,
                                cn->lp_height, cn->measured_width,
                                cn->measured_height, kids.size());
                    }
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
                    // MASTER-2 FIX-MEASURE-002e (AOSP onLayout replay law):
                    // RelativeLayout.onLayout replays the edges cached at
                    // MEASURE time — it never recomputes from measured
                    // sizes. Prefer the cached edges when the measure pass
                    // resolved them; the legacy fixed-point below stays as
                    // fallback for children without cached edges
                    // (programmatic addView paths).
                    if (cn && cn->rl_edges_valid) {
                        const int bx = cl + cn->rl_cached_left - n->padding_left;
                        const int by = ct + cn->rl_cached_top - n->padding_top;
                        const int bw = std::max(0, cn->rl_cached_right - cn->rl_cached_left);
                        const int bh = std::max(0, cn->rl_cached_bottom - cn->rl_cached_top);
                        boxes[cid] = {bx, by, bw, bh, true};
                        continue;
                    }
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
                        (void)vg;
                        // ── vertical ──
                        // MASTER-2 FIX-MEASURE-002d: explicit RL rule
                        // booleans (overlapping legacy masks misrouted
                        // alignParentTop into the alignParentBottom branch).
                        // ALIGN_TOP/ALIGN_BOTTOM edge alignment added —
                        // AOSP RelativeLayout.applyVerticalSizeRules.
                        int y = b.y;
                        if (!cn->rel_below_name.empty()) {
                            if (uint32_t bid = name_to_id(cn->rel_below_name)) {
                                y = boxes[bid].y + boxes[bid].h + cn->lp_margin_top;
                            }
                        } else if (!cn->rel_above_name.empty()) {
                            if (uint32_t bid = name_to_id(cn->rel_above_name)) {
                                y = boxes[bid].y - b.h - cn->lp_margin_bottom;
                            }
                        } else if (!cn->rel_align_top_name.empty()) {
                            if (uint32_t bid = name_to_id(cn->rel_align_top_name)) {
                                y = boxes[bid].y + cn->lp_margin_top;
                            }
                        } else if (!cn->rel_align_bottom_name.empty()) {
                            if (uint32_t bid = name_to_id(cn->rel_align_bottom_name)) {
                                y = boxes[bid].y + boxes[bid].h - b.h - cn->lp_margin_bottom;
                            }
                        } else if (cn->rel_align_parent_bottom) {
                            y = ct + ch - b.h - cn->lp_margin_bottom;
                        } else if (cn->rel_center_in_parent || cn->rel_center_vertical) {
                            y = ct + (ch - b.h) / 2;
                        } else if (cn->rel_align_parent_top || pass == 0) {
                            y = ct;              // alignParentTop / flow top
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
                        } else if (!cn->rel_align_left_name.empty()) {
                            if (uint32_t lid = name_to_id(cn->rel_align_left_name)) {
                                x = boxes[lid].x + cn->lp_margin_left;
                            }
                        } else if (!cn->rel_align_right_name.empty()) {
                            if (uint32_t rid = name_to_id(cn->rel_align_right_name)) {
                                x = boxes[rid].x + boxes[rid].w - b.w - cn->lp_margin_right;
                            }
                        } else if (cn->rel_center_in_parent || cn->rel_center_horizontal) {
                            x = cl + (cw - b.w) / 2;
                        } else if (cn->rel_align_parent_right) {
                            x = cl + cw - b.w - cn->lp_margin_right;
                        } else if (cn->rel_align_parent_left || pass == 0) {
                            x = cl;              // alignParentLeft / flow left
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
                    // G10 FIX-G10-004 (AOSP Gravity axis-field equality law —
                    // same masked-field rule as the LinearLayout fixes):
                    // mask the axis field FIRST, then compare. Raw bit tests
                    // misroute combined gravities: bottom|end (0x00800055)
                    // has bit0 set, so `vg & 0x1` turned RIGHT into CENTER;
                    // 0x55 also carries 0x10, so `vg & 0x10` turned BOTTOM
                    // into CENTER_VERTICAL (billthefarmer FAB pair was
                    // centered instead of bottom-right).
                    if (vg > 0) {
                        const int hf = vg & 0x7;
                        if (hf == 0x1) x = cl + (cw - w) / 2;
                        else if (hf == 0x5) x = cl + cw - w;
                        const int vf = vg & 0x70;
                        if (vf == 0x10) y = ct + (ch - h) / 2;
                        else if (vf == 0x50) y = ct + ch - h;
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
