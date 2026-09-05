/*
 * font_pipeline_probe.cpp — G31–G35 typography diagnostics harness.
 *
 * Campaign: MASTER VISUAL COMPATIBILITY CAMPAIGN, gates G31 (font source),
 * G32 (font resolution trace), G33 (FreeType rasterization), G34 (glyph
 * lookup), G35 (glyph metrics).
 *
 * Prints, WITHOUT changing any runtime behavior:
 *   1. The faces the live TextShaper singleton resolved (paths + metrics).
 *   2. FreeType face facts for each face: unitsPerEm, hhea ascender /
 *      descender / lineGap (scaled at the probe size), glyph count.
 *   3. Per-glyph facts for the EXT-01 HelloWorldSelfAware charset
 *      (lowercase h e l o w r d, uppercase, digits, punctuation, space):
 *      Unicode codepoint → glyph ID (FreeType cmap lookup — G34), advance,
 *      left bearing, bitmap bounds, raster dimensions (G33/G35).
 *   4. The shaped advance of the four REAL rendered lines at the law-derived
 *      text size, through the LIVE TextShaper pipeline (FriBidi→HarfBuzz→
 *      FreeType), so screenshot-level measurements can be tied to metrics.
 *
 * Usage: font_pipeline_probe <pixel_size>
 * Exit 0 when the primary face loaded and all probe glyphs resolved non-zero.
 */
#include "../src/fonts/text_shaper.h"

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_GLYPH_H
#include FT_SFNT_NAMES_H
#include <freetype/tttables.h>

#include <cstdio>
#include <cstring>
#include <string>

using namespace miniandroid;

namespace {

// The four REAL lines the external APK renders (EXT-01 runtime-produced text,
// captured from [EXP092-RENDER] at the current HEAD — not synthetic input).
const char* kRealLines[] = {
    "hello world",
    "i'm 6f1c3a9d2e5b4780",
    "a version 14 android",
    "with api level 34",
};

const char* kProbeChars = "helo wrdHELsend'mvigp043216789.,'!";

struct FaceFacts {
    FT_Face face;
    const char* label;
};

void dump_face(FT_Face face, const char* label, long size_px) {
    if (!face) {
        std::printf("FACE %s: (not loaded)\n", label);
        return;
    }
    std::printf("FACE %s: family='%s' style='%s' num_glyphs=%ld num_faces=%ld\n",
                label, face->family_name ? face->family_name : "?",
                face->style_name ? face->style_name : "?",
                face->num_glyphs, face->num_faces);
    std::printf("  unitsPerEm=%d (F26Dot6 basis; scalable=%d)\n",
                face->units_per_EM, face->face_flags & FT_FACE_FLAG_SCALABLE ? 1 : 0);
    if (FT_Set_Pixel_Sizes(face, 0, (FT_UInt)size_px) == 0) {
        const auto& m = face->size->metrics;
        std::printf("  @%ldpx: metrics.ascender=%.2f descender=%.2f height=%.2f "
                    "max_advance=%.2f  (26.6 raw: asc=%ld desc=%ld h=%ld adv=%ld)\n",
                    size_px, m.ascender / 64.0, m.descender / 64.0,
                    m.height / 64.0, m.max_advance / 64.0,
                    m.ascender, m.descender, m.height, m.max_advance);
        std::printf("  -> Android FontMetrics(ascent=%.0f descent=%.0f) "
                    "lineBox(descent-ascent)=%.2f\n",
                    -(m.ascender / 64.0), -(m.descender / 64.0),
                    (m.descender - m.ascender) / 64.0);
    }
    // OS/2 + hhea raw facts (vertical metric law inputs — G36).
    TT_HoriHeader* hhea = static_cast<TT_HoriHeader*>(
        FT_Get_Sfnt_Table(face, ft_sfnt_hhea));
    TT_OS2* os2 = static_cast<TT_OS2*>(FT_Get_Sfnt_Table(face, ft_sfnt_os2));
    if (hhea)
        std::printf("  hhea: ascender=%d descender=%d lineGap=%d (units)\n",
                    hhea->Ascender, hhea->Descender, hhea->Line_Gap);
    if (os2 && os2->version != 0xFFFF)
        std::printf("  OS/2: usWinAscent=%u usWinDescent=%u sTypoAscender=%d "
                    "sTypoDescender=%d sTypoLineGap=%d fsSelection=0x%04x\n",
                    os2->usWinAscent, os2->usWinDescent, os2->sTypoAscender,
                    os2->sTypoDescender, os2->sTypoLineGap, os2->fsSelection);
}

}  // namespace

int main(int argc, char** argv) {
    long size_px = argc > 1 ? std::atol(argv[1]) : 58;

    auto& sh = fonts::TextShaper::instance();
    if (!sh.available()) {
        std::fprintf(stderr, "PROBE FAIL: TextShaper unavailable\n");
        return 2;
    }
    std::printf("\n== live TextShaper faces ==\n");
    std::printf("primary_font_path=%s\n", sh.primary_font_path().c_str());
    std::printf("monospace_font_path=%s\n", sh.monospace_font_path().c_str());
    std::printf("app_fonts_registered=%zu\n", sh.app_font_count());
    std::printf("resolve_family(monospace)=%d\n",
                sh.resolve_family("monospace", false));

    // Raw FreeType view of the same files (G33/G35 evidence).
    FT_Library lib;
    if (FT_Init_FreeType(&lib)) return 2;
    const std::string primary_path = sh.primary_font_path();
    const std::string mono_path = sh.monospace_font_path();
    const char* paths[] = {
        primary_path.c_str(),
        mono_path.c_str(),
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    };
    for (const char* p : paths) {
        FT_Face f = nullptr;
        if (FT_New_Face(lib, p, 0, &f) == 0) {
            dump_face(f, p, size_px);
            FT_Done_Face(f);
        } else {
            std::printf("FACE %s: FT_New_Face FAILED\n", p);
        }
    }

    std::printf("\n== glyph lookup + metrics @ %ldpx (G33/G34/G35) ==\n", size_px);
    FT_Face f = nullptr;
    // G32: probe the face the family law resolves — 'monospace' for EXT-01.
    const std::string& probe_path =
        sh.resolve_family("monospace", false) >= 0 ? mono_path : primary_path;
    if (FT_New_Face(lib, probe_path.c_str(), 0, &f) != 0) return 2;
    FT_Set_Pixel_Sizes(f, 0, (FT_UInt)size_px);
    int bad = 0;
    for (const char* p = kProbeChars; *p; ++p) {
        FT_UInt gi = FT_Get_Char_Index(f, static_cast<FT_ULong>(*p));
        if (gi == 0) {
            std::printf("  U+%04X '%c': NOTDEF (gid=0)\n", (unsigned)*p, *p);
            ++bad;
            continue;
        }
        if (FT_Load_Glyph(f, gi, FT_LOAD_DEFAULT)) { ++bad; continue; }
        if (FT_Render_Glyph(f->glyph, FT_RENDER_MODE_NORMAL)) { ++bad; continue; }
        FT_GlyphSlot g = f->glyph;
        std::printf("  U+%04X '%c' gid=%3u adv=%.2f lsb=%.2f rsb=%.2f "
                    "ink=%dx%d@(+%d,%+d) asc_ink_top=%d\n",
                    (unsigned)*p, *p, gi, g->advance.x / 64.0,
                    g->metrics.horiBearingX / 64.0,
                    (g->advance.x - g->metrics.horiBearingX
                     - g->metrics.width) / 64.0,
                    g->bitmap.width, g->bitmap.rows,
                    g->bitmap_left, g->bitmap_top, g->bitmap_top);
    }

    std::printf("\n== live pipeline shaping of the REAL EXT-01 lines ==\n");
    for (const char* line : kRealLines) {
        const auto& st = sh.shape(line, (float)size_px, false, fonts::FACE_SYSTEM);
        std::printf("  line %-22s glyphs=%zu width=%.2f notdef=%zu rtl=%d\n",
                    line, st.glyphs.size(), st.width, st.notdef_count,
                    st.rtl_base ? 1 : 0);
    }

    std::printf("\nPROBE RESULT: %s (%d bad glyphs)\n",
                bad == 0 ? "PASS" : "FAIL", bad);
    FT_Done_Face(f);
    FT_Done_FreeType(lib);
    return bad == 0 ? 0 : 1;
}
