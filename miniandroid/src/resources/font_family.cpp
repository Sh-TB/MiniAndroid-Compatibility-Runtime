// font_family.cpp — C9-16/C9-17 (CODER 9) implementation. See font_family.h.

#include "font_family.h"

#include "axml_parser.h"

#include <algorithm>
#include <cstdlib>

namespace miniandroid {
namespace resources {

namespace {
// android:fontWeight range law (FontResourcesParser): values outside
// 0..1000 clamp to the nearest bound; absent = 400.
int32_t clamp_weight(int32_t w) {
    if (w < 0) return 0;
    if (w > 1000) return 1000;
    return w;
}
}  // namespace

FontFamily parse_font_family(const std::vector<uint8_t>& axml,
                             const std::string& source_path) {
    FontFamily out;
    out.source_path = source_path;
    resources::AxmlParser parser;
    if (!parser.parse(axml) || !parser.valid()) return out;
    const auto& root = parser.root();
    if (root.name != "font-family") return out;   // honest miss
    if (const auto* a = root.attr("fontFamily", "android"))
        if (!a->raw_value.empty()) out.name = a->raw_value;

    for (const auto& child : root.children) {
        if (child.name != "font") continue;
        FontFaceDecl decl;
        decl.source_path = source_path;
        if (const auto* f = child.attr("font", "android")) {
            if (!f->raw_value.empty()) decl.font_ref = f->raw_value;
            if (f->value.type == DataType::REFERENCE ||
                f->value.type == DataType::DYNAMIC_REFERENCE)
                decl.font_ref_id = f->value.data;
        }
        if (const auto* w = child.attr("fontWeight", "android")) {
            int32_t v = 0;
            if (w->value.type == DataType::INT_DEC ||
                w->value.type == DataType::INT_HEX) {
                v = (int32_t)w->value.data;
            } else if (!w->raw_value.empty()) {
                v = (int32_t)strtol(w->raw_value.c_str(), nullptr, 10);
            }
            decl.weight = clamp_weight(v == 0 && w->raw_value != "0" ? 400 : v);
        }
        if (const auto* s = child.attr("fontStyle", "android")) {
            // AOSP FontResourcesParser: "italic" → ITALIC, anything else
            // (absent / "normal") → NORMAL. The compiled value is an int
            // (0 normal / 1 italic) for aapt2 — both forms accepted.
            if (s->value.type == DataType::INT_DEC ||
                s->value.type == DataType::INT_HEX) {
                decl.italic = (s->value.data & 0x1) != 0;
            } else {
                decl.italic = (s->raw_value == "italic");
            }
        }
        if (!decl.font_ref.empty() || decl.font_ref_id != 0)
            out.faces.push_back(std::move(decl));
    }
    return out;
}

TypefaceRequest typeface_style_request(int style) {
    TypefaceRequest r;
    switch (style) {
        case kTypefaceBold:
        case kTypefaceBoldItalic:
            r.weight = 700;
            break;
        default:
            r.weight = 400;   // NORMAL / ITALIC / unknown styles
            break;
    }
    r.italic = (style & kTypefaceItalic) != 0;
    return r;
}

int select_font_face_law(const std::vector<FontFaceDecl>& faces,
                         int32_t req_weight, bool req_italic) {
    if (faces.empty()) return -1;
    int best = -1;
    int best_italic_penalty = 1;   // 0 = italic matches, 1 = mismatch
    int32_t best_dist = 0;
    for (size_t i = 0; i < faces.size(); ++i) {
        const int ip = faces[i].italic == req_italic ? 0 : 1;
        const int32_t dist = std::abs(faces[i].weight - req_weight);
        if (best < 0 || ip < best_italic_penalty ||
            (ip == best_italic_penalty && dist < best_dist)) {
            best = (int)i;
            best_italic_penalty = ip;
            best_dist = dist;
        }
        // ties (ip == best_italic_penalty && dist == best_dist) keep the
        // earlier candidate — document order, deterministic.
    }
    return best;
}

int select_font_face_law(const std::vector<FontFaceDecl>& faces, int style) {
    const TypefaceRequest req = typeface_style_request(style);
    return select_font_face_law(faces, req.weight, req.italic);
}

}  // namespace resources
}  // namespace miniandroid
