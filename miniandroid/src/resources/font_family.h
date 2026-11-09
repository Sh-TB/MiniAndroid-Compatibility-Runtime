// font_family.h — C9-16/C9-17 (CODER 9) — font-family XML + weight law.
//
// AOSP contract (frameworks/base, graphics/java/android/graphics/Typeface.java
// + core/java/android/content/res/FontResourcesParser.java):
//   * res/font/*.xml <font-family> declares a NAMED family whose <font>
//     children each carry android:font="@font/file", android:fontWeight
//     (0..1000, default 400) and android:fontStyle ("normal"|"italic").
//   * Typeface.create(family, style) resolves the family to the face whose
//     (weight, italic) is the CLOSEST to the request (the FontListFont-
//     FamilyTypefaceAdapter style-distance law): italic mismatch is the
//     dominant penalty, then absolute weight distance; document order
//     breaks ties deterministically.
//   * The legacy filename-heuristic path (face -bold/-italic suffixes) stays
//     the fallback when no font-family XML exists for the name.
//
// Pure + unit-tested (tests/c9_phase3_laws_test.cpp); the engine hookup
// (dalvik_engine.cpp Typeface laws) consumes these functions.

#ifndef MINIANDROID_RESOURCES_FONT_FAMILY_H
#define MINIANDROID_RESOURCES_FONT_FAMILY_H

#include "arsc_parser.h"

#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid {
namespace resources {

// One <font> child of a <font-family>.
struct FontFaceDecl {
    std::string font_ref;      // raw android:font value ("@font/foo_regular")
    uint32_t font_ref_id = 0;  // compiled REFERENCE id (0 = none/raw only)
    int32_t weight = 400;      // android:fontWeight (AOSP default 400)
    bool italic = false;       // android:fontStyle == "italic"
    // Provenance: res/font/<family>.xml the decl was parsed from.
    std::string source_path;
};

// A parsed <font-family> document.
struct FontFamily {
    std::string name;  // android:fontFamily attr ("" = filename carries it)
    std::vector<FontFaceDecl> faces;
    std::string source_path;
    bool valid() const { return !faces.empty(); }
};

// C9-16 — parse a compiled res/font/*.xml AXML document. Returns an
// INVALID family (faces empty) for non-font-family roots (honest miss —
// the caller falls back to the filename heuristics).
FontFamily parse_font_family(const std::vector<uint8_t>& axml,
                             const std::string& source_path);

// AOSP Typeface style bits (Typeface.java): NORMAL=0, BOLD=1,
// ITALIC=2, BOLD_ITALIC=3.
constexpr int kTypefaceNormal = 0;
constexpr int kTypefaceBold = 1;
constexpr int kTypefaceItalic = 2;
constexpr int kTypefaceBoldItalic = 3;

// style → (requested weight, requested italic) — AOSP Typeface.create
// defaults: BOLD maps to weight 700, everything else to 400 (the pre-
// variable-font contract; create(Typeface,int weight,boolean italic)
// passes the weight through, clamped to 0..1000).
struct TypefaceRequest {
    int32_t weight = 400;
    bool italic = false;
};
TypefaceRequest typeface_style_request(int style);

// C9-17 — the AOSP closest-face law (pure, deterministic). Returns the
// index into `faces` of the winner, or -1 when faces is empty.
//   1. italic mismatch dominates (an exact-italic candidate always beats
//      a non-matching one — AOSP style-distance first component),
//   2. then minimal |weight - requested weight|,
//   3. ties answer the FIRST document-order candidate.
int select_font_face_law(const std::vector<FontFaceDecl>& faces,
                         int32_t req_weight, bool req_italic);

// Convenience: style-bits overload.
int select_font_face_law(const std::vector<FontFaceDecl>& faces, int style);

}  // namespace resources
}  // namespace miniandroid

#endif  // MINIANDROID_RESOURCES_FONT_FAMILY_H
