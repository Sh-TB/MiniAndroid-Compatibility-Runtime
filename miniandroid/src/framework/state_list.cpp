// state_list.cpp — StateListDrawable law implementation (see state_list.h).

#include "state_list.h"

#include "../resources/axml_parser.h"

namespace miniandroid {
namespace framework {

namespace {

int tri_state(const resources::AxmlElement& item, const char* attr) {
    const auto* a = item.attr(attr, "android");
    if (!a) return -1;  // wildcard (state not declared)
    // AXML booleans compile to Res_value INT_BOOLEAN, but hostile/odd files
    // may carry a string "true"/"false" — accept both deterministically.
    if (a->value.type == resources::DataType::INT_BOOLEAN)
        return (a->value.data != 0) ? 1 : 0;
    if (!a->raw_value.empty()) {
        if (a->raw_value == "true") return 1;
        if (a->raw_value == "false") return 0;
    }
    return -1;
}

bool parse_hex_color(const std::string& s, uint32_t* argb) {
    if (s.empty() || s[0] != '#') return false;
    std::string hex = s.substr(1);
    auto nib = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    };
    for (char c : hex)
        if (nib(c) < 0) return false;
    uint32_t v = 0;
    if (hex.size() == 6) {
        // #RRGGBB → opaque (AOSP Color.parseColor law)
        for (int i = 0; i < 6; ++i) v = (v << 4) | (uint32_t)nib(hex[i]);
        v |= 0xFF000000u;
    } else if (hex.size() == 8) {
        for (int i = 0; i < 8; ++i) v = (v << 4) | (uint32_t)nib(hex[i]);
    } else if (hex.size() == 3) {
        // #RGB → expand each nibble (AOSP Color.parseColor law)
        uint32_t r = (uint32_t)nib(hex[0]), g = (uint32_t)nib(hex[1]),
                 b = (uint32_t)nib(hex[2]);
        v = 0xFF000000u | (r << 20) | (r << 16) | (g << 12) | (g << 8) |
            (b << 4) | b;
    } else {
        return false;
    }
    *argb = v;
    return true;
}

// Extract a color from an <item>: android:color attribute (ColorStateList
// form) or the first nested <shape>/<solid> android:color (shape form).
bool item_color(const resources::AxmlElement& item, uint32_t* argb) {
    if (const auto* a = item.attr("color", "android")) {
        if (a->value.type == resources::DataType::COLOR_ARGB8 ||
            a->value.type == resources::DataType::COLOR_RGB8 ||
            a->value.type == resources::DataType::COLOR_ARGB4 ||
            a->value.type == resources::DataType::COLOR_RGB4) {
            *argb = a->value.data;
            return true;
        }
        if (!a->raw_value.empty() && parse_hex_color(a->raw_value, argb))
            return true;
        // aapt2 compiles colors to COLOR_*; anything else is not a color
        // law — reject.
        return false;
    }
    std::function<bool(const resources::AxmlElement&)> walk =
        [&](const resources::AxmlElement& el) -> bool {
        if (el.name == "solid") {
            if (const auto* c = el.attr("color", "android")) {
                if (!c->raw_value.empty() && parse_hex_color(c->raw_value, argb))
                    return true;
                if (c->value.type >= resources::DataType::COLOR_ARGB8 &&
                    c->value.type <= resources::DataType::COLOR_RGB4) {
                    *argb = c->value.data;
                    return true;
                }
            }
        }
        for (const auto& ch : el.children)
            if (walk(ch)) return true;
        return false;
    };
    for (const auto& ch : item.children)
        if (walk(ch)) return true;
    return false;
}

}  // namespace

bool parse_state_list(const std::vector<uint8_t>& axml,
                      std::vector<ViewShadow::ViewNode::BgStateItem>* out) {
    resources::AxmlParser parser;
    if (!parser.parse(axml) || !parser.valid()) return false;
    const auto& root = parser.root();
    if (root.name != "selector") return false;

    std::vector<ViewShadow::ViewNode::BgStateItem> items;
    for (const auto& item : root.children) {
        if (item.name != "item") continue;
        ViewShadow::ViewNode::BgStateItem it;
        it.state_pressed = tri_state(item, "state_pressed");
        it.state_enabled = tri_state(item, "state_enabled");
        it.state_selected = tri_state(item, "state_selected");
        uint32_t c = 0;
        if (item_color(item, &c)) {
            it.color = c;
            it.has_color = true;
        }
        if (const auto* d = item.attr("drawable", "android")) {
            // Reference form: raw "@drawable/name" or a typed reference —
            // recorded for the caller's resolver; unresolved stays empty.
            if (!d->raw_value.empty()) it.drawable_path = d->raw_value;
        }
        items.push_back(std::move(it));
    }
    *out = std::move(items);
    return true;
}

bool pick_state_list(
    const std::vector<ViewShadow::ViewNode::BgStateItem>& items, bool pressed,
    bool enabled, bool selected, uint32_t* color_out, std::string* path_out) {
    // StateListDrawable.getStateDrawableIndex law: FIRST item in document
    // order whose state spec is satisfied wins; a declared state must match
    // exactly (state_pressed="true" requires pressed), undeclared = wildcard.
    for (const auto& it : items) {
        if (it.state_pressed >= 0 &&
            it.state_pressed != (pressed ? 1 : 0))
            continue;
        if (it.state_enabled >= 0 && it.state_enabled != (enabled ? 1 : 0))
            continue;
        if (it.state_selected >= 0 &&
            it.state_selected != (selected ? 1 : 0))
            continue;
        if (it.has_color && color_out) *color_out = it.color;
        if (path_out) *path_out = it.drawable_path;
        return true;
    }
    return false;
}

}  // namespace framework
}  // namespace miniandroid
