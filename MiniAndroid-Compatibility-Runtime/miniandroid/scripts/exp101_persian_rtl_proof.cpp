// UNIFIED_002 — EXP-101/WS-C4: §14 Persian/RTL proof + §13 font discovery.
//
// EXACT master-request sample set:
//   Latin:   Hello
//   Arabic:  سلام
//   Persian: سلام دنیا
//   Mixed:   Hello سلام World
//   Numbers: 123
//   Fa+Num:  نسخه ۱۲.۱۰.۱
//
// Pipeline per sample: UTF-8 → codepoints → FriBidi (first-strong) →
// HarfBuzz shaping → FreeType raster → framebuffer strip → PNG + metrics
// JSON (codepoints, base dir, glyph ids, advances).
//
// Font matrix (§13): shape "سلام دنیا" with every candidate font and
// record glyph availability (Arabic coverage, .notdef hits).
//
// DIAGNOSTIC/EXPERIMENTAL tooling — outside the runtime, no runtime change.
#include <fribidi/fribidi.h>
#include <harfbuzz/hb.h>
#include <harfbuzz/hb-ft.h>
#include <ft2build.h>
#include FT_FREETYPE_H

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>

struct Rgba { uint8_t r, g, b, a; };
struct Framebuffer {
    int w = 0, h = 0;
    std::vector<Rgba> px;
    Framebuffer(int W, int H) : w(W), h(H), px(W * H, {255, 255, 255, 255}) {}
    void blend(int x, int y, Rgba c) {
        if (x < 0 || y < 0 || x >= w || y >= h) return;
        Rgba& d = px[y * w + x];
        d.r = (c.r * c.a + d.r * (255 - c.a)) / 255;
        d.g = (c.g * c.a + d.g * (255 - c.a)) / 255;
        d.b = (c.b * c.a + d.b * (255 - c.a)) / 255;
    }
};

static void write_ppm(const Framebuffer& fb, const char* path) {
    std::ofstream f(path, std::ios::binary);
    f << "P6\n" << fb.w << " " << fb.h << "\n255\n";
    for (auto& p : fb.px) f << p.r << p.g << p.b;
}

// PNG encoding via system zlib (RGB8, filter-0 rows).
#include <zlib.h>
static uint32_t crc_table[256];
static void crc_init() {
    for (uint32_t n = 0; n < 256; n++) {
        uint32_t c = n;
        for (int k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        crc_table[n] = c;
    }
}
static uint32_t crc_upd(uint32_t crc, const uint8_t* buf, size_t n) {
    crc ^= 0xFFFFFFFFu;
    for (size_t i = 0; i < n; i++) crc = crc_table[(crc ^ buf[i]) & 0xFF] ^ (crc >> 8);
    return crc ^ 0xFFFFFFFFu;
}
static void png_chunk(FILE* f, const char* type, const uint8_t* data, size_t n) {
    uint8_t h[4] = {(uint8_t)(n >> 24), (uint8_t)(n >> 16), (uint8_t)(n >> 8), (uint8_t)n};
    fwrite(h, 1, 4, f); fwrite(type, 1, 4, f);
    if (n) fwrite(data, 1, n, f);
    // CRC-32 over type+data
    std::vector<uint8_t> tmp(4 + n);
    memcpy(tmp.data(), type, 4);
    if (n) memcpy(tmp.data() + 4, data, n);
    uint32_t crc = crc_upd(0, tmp.data(), tmp.size());
    uint8_t c[4] = {(uint8_t)(crc >> 24), (uint8_t)(crc >> 16), (uint8_t)(crc >> 8), (uint8_t)crc};
    fwrite(c, 1, 4, f);
}
static void write_png2(const Framebuffer& fb, const char* path) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    static const uint8_t sig[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    fwrite(sig, 1, 8, f);
    uint8_t ihdr[13];
    ihdr[0] = fb.w >> 24; ihdr[1] = fb.w >> 16; ihdr[2] = fb.w >> 8; ihdr[3] = fb.w;
    ihdr[4] = fb.h >> 24; ihdr[5] = fb.h >> 16; ihdr[6] = fb.h >> 8; ihdr[7] = fb.h;
    ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
    png_chunk(f, "IHDR", ihdr, 13);
    std::vector<uint8_t> raw((size_t)fb.w * 3 * fb.h + fb.h);
    for (int y = 0; y < fb.h; y++) {
        raw[(size_t)y * (fb.w * 3 + 1)] = 0;
        for (int x = 0; x < fb.w; x++) {
            const Rgba& p = fb.px[(size_t)y * fb.w + x];
            size_t o = (size_t)y * (fb.w * 3 + 1) + 1 + x * 3;
            raw[o] = p.r; raw[o + 1] = p.g; raw[o + 2] = p.b;
        }
    }
    uLongf clen = compressBound((uLong)raw.size());
    std::vector<uint8_t> comp(clen);
    compress2(comp.data(), &clen, raw.data(), raw.size(), 6);
    png_chunk(f, "IDAT", comp.data(), clen);
    png_chunk(f, "IEND", nullptr, 0);
    fclose(f);
}

static std::u32string utf8_to_u32(const std::string& s) {
    std::u32string out;
    size_t i = 0;
    while (i < s.size()) {
        uint32_t cp = (unsigned char)s[i];
        int extra = (cp < 0x80) ? 0 : (cp < 0xE0 ? 1 : (cp < 0xF0 ? 2 : 3));
        if (cp >= 0x80) cp &= (extra == 1 ? 0x1F : (extra == 2 ? 0x0F : 0x07));
        for (int k = 0; k < extra && i + 1 < s.size(); ++k)
            cp = (cp << 6) | ((unsigned char)s[++i] & 0x3F);
        out.push_back(cp);
        ++i;
    }
    return out;
}

struct SampleResult {
    std::string name, input;
    std::string base_dir;
    bool bidi_ok = false;
    size_t glyph_count = 0;
    std::vector<uint32_t> glyph_ids;
    std::vector<int> advances;
    bool shaped_ok = false;
    long nonwhite = 0;
    std::string visual_hex;  // codepoints of logical input (first 16)
};

int main(int argc, char** argv) {
    crc_init();
    const char* font_path = (argc > 1) ? argv[1]
        : "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
    const char* out_prefix = (argc > 2) ? argv[2] : "run/exp101_persian/proof";

    std::vector<std::pair<std::string, std::string>> samples = {
        {"latin_hello", "Hello"},
        {"arabic_salaam", "سلام"},
        {"persian_salaam_donya", "سلام دنیا"},
        {"mixed_hello_salaam_world", "Hello سلام World"},
        {"numbers_123", "123"},
        {"persian_version_numbers", "نسخه ۱۲.۱۰.۱"},
    };

    FT_Library ft;
    if (FT_Init_FreeType(&ft)) { fprintf(stderr, "FT init fail\n"); return 1; }
    FT_Face face;
    if (FT_New_Face(ft, font_path, 0, &face)) { fprintf(stderr, "FT face fail %s\n", font_path); return 1; }
    FT_Set_Pixel_Sizes(face, 0, 48);
    hb_font_t* hb_font = hb_ft_font_create(face, nullptr);
    if (!hb_font) { fprintf(stderr, "HB font fail\n"); return 1; }

    Framebuffer fb(1080, 72 * (int)samples.size() + 24);
    std::ostringstream mj;
    mj << "{\n  \"font\": \"" << font_path << "\",\n  \"font_px\": 48,\n  \"samples\": [\n";

    int pen_y = 56;
    bool all_ok = true;
    std::ostringstream samples_json;
    for (size_t si = 0; si < samples.size(); ++si) {
        auto& [name, text] = samples[si];
        std::u32string u32 = utf8_to_u32(text);

        // FriBidi — first-strong base direction
        std::vector<FriBidiChar> src(u32.begin(), u32.end());
        FriBidiParType base = FRIBIDI_PAR_LTR;
        for (FriBidiChar ch : src) {
            FriBidiCharType t = fribidi_get_bidi_type(ch);
            if (t == FRIBIDI_TYPE_R || t == FRIBIDI_TYPE_AL) { base = FRIBIDI_PAR_RTL; break; }
            if (t == FRIBIDI_TYPE_L) { base = FRIBIDI_PAR_LTR; break; }
        }
        std::vector<FriBidiChar> vis(src.size() + 1);
        FriBidiLevel lvl = fribidi_log2vis(src.data(), (FriBidiStrIndex)src.size(),
                                           &base, vis.data(), nullptr, nullptr, nullptr);
        bool bidi_ok = lvl >= 0;

        // HarfBuzz shaping of the VISUAL order
        hb_buffer_t* buf = hb_buffer_create();
        hb_buffer_add_utf32(buf, vis.data(), (int)vis.size(), 0, -1);
        hb_buffer_guess_segment_properties(buf);
        hb_shape(hb_font, buf, nullptr, 0);
        unsigned gn = 0;
        hb_glyph_info_t* gi = hb_buffer_get_glyph_infos(buf, &gn);
        hb_glyph_position_t* gp = hb_buffer_get_glyph_positions(buf, nullptr);

        SampleResult r;
        r.name = name; r.input = text;
        r.base_dir = (base == FRIBIDI_PAR_RTL) ? "RTL" : "LTR";
        r.bidi_ok = bidi_ok;
        r.glyph_count = gn;
        int x = 24;
        long nonwhite = 0;
        for (unsigned k = 0; k < gn; ++k) {
            r.glyph_ids.push_back(gi[k].codepoint);
            r.advances.push_back(gp[k].x_advance);
            FT_Int bx = x + (gp[k].x_offset >> 6);
            FT_Int by = pen_y - (gp[k].y_offset >> 6);
            if (FT_Load_Glyph(face, gi[k].codepoint, FT_LOAD_DEFAULT)) continue;
            if (FT_Render_Glyph(face->glyph, FT_RENDER_MODE_NORMAL)) continue;
            FT_GlyphSlot g = face->glyph;
            FT_Bitmap& bm = g->bitmap;
            for (unsigned ry = 0; ry < bm.rows; ++ry)
                for (unsigned rx = 0; rx < bm.width; ++rx) {
                    uint8_t a = bm.buffer[ry * bm.pitch + rx];
                    if (a) {
                        fb.blend(bx + g->bitmap_left + (int)rx,
                                 by - g->bitmap_top + (int)ry,
                                 {0, 0, 0, a});
                    }
                }
            x += gp[k].x_advance >> 6;
        }
        // count non-white on the strip we just drew
        for (int yy = pen_y - 52; yy < pen_y + 16; ++yy)
            for (int xx = 0; xx < fb.w; ++xx) {
                auto& p = fb.px[(size_t)yy * fb.w + xx];
                if (p.r < 250 || p.g < 250 || p.b < 250) nonwhite++;
            }
        r.nonwhite = nonwhite;
        r.shaped_ok = gn > 0;
        if (gn == 0 || nonwhite == 0) all_ok = false;

        char hex[200] = {0};
        for (size_t k = 0; k < u32.size() && k < 16; ++k)
            snprintf(hex + strlen(hex), sizeof(hex) - strlen(hex), "U+%04X ", u32[k]);
        r.visual_hex = hex;

        mj << "  {\"sample\": \"" << name << "\", \"input_utf8\": \"" << text
           << "\", \"codepoints\": \"" << hex << "\", \"base_direction\": \"" << r.base_dir
           << "\", \"bidi_ok\": " << (bidi_ok ? "true" : "false")
           << ", \"glyph_count\": " << gn
           << ", \"glyph_ids\": [";
        for (size_t k = 0; k < r.glyph_ids.size(); ++k)
            mj << r.glyph_ids[k] << (k + 1 < r.glyph_ids.size() ? "," : "");
        mj << "], \"advances\": [";
        for (size_t k = 0; k < r.advances.size(); ++k)
            mj << r.advances[k] << (k + 1 < r.advances.size() ? "," : "");
        mj << "], \"strip_nonwhite_px\": " << nonwhite
           << ", \"shaped_ok\": " << (r.shaped_ok ? "true" : "false") << "}"
           << (si + 1 < samples.size() ? "," : "") << "\n";

        pen_y += 72;
        hb_buffer_destroy(buf);
    }

    // ---- §13 font matrix: shape "سلام دنیا" per font, record coverage ----
    mj << "],\n  \"all_ok\": " << (all_ok ? "true" : "false")
       << ",\n  \"proof_status\": \"" << (all_ok ? "OK" : "PARTIAL") << "\","
       << "\n  \"font_matrix\": [\n";
    std::vector<std::string> fonts = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf",
        "/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-VariableFont_wght.ttf",
    };
    for (size_t fi = 0; fi < fonts.size(); ++fi) {
        FT_Face f2 = nullptr;
        bool open_ok = (FT_New_Face(ft, fonts[fi].c_str(), 0, &f2) == 0);
        bool arabic_cmap = false;
        int notdef_shaped = -1, num_glyphs = -1;
        bool variable = false;
        if (open_ok) {
            num_glyphs = (int)f2->num_glyphs;
#ifdef FT_HAS_VARIATION
            variable = FT_HAS_VARIATION(f2) != 0;
#endif
            arabic_cmap = FT_Get_Char_Index(f2, 0x0633) != 0;  // U+0633 س
            hb_font_t* hb2 = hb_ft_font_create(f2, nullptr);
            const char* probe = "سلام دنیا";
            std::u32string u32 = utf8_to_u32(probe);
            std::vector<FriBidiChar> src(u32.begin(), u32.end());
            FriBidiParType base = FRIBIDI_PAR_RTL;
            std::vector<FriBidiChar> vis(src.size() + 1);
            fribidi_log2vis(src.data(), (FriBidiStrIndex)src.size(), &base,
                            vis.data(), nullptr, nullptr, nullptr);
            hb_buffer_t* b2 = hb_buffer_create();
            hb_buffer_add_utf32(b2, vis.data(), (int)vis.size(), 0, -1);
            hb_buffer_guess_segment_properties(b2);
            hb_shape(hb2, b2, nullptr, 0);
            unsigned gn2 = 0;
            hb_glyph_info_t* gi2 = hb_buffer_get_glyph_infos(b2, &gn2);
            notdef_shaped = 0;
            for (unsigned k = 0; k < gn2; ++k)
                if (gi2[k].codepoint == 0) notdef_shaped++;
            hb_buffer_destroy(b2);
            hb_font_destroy(hb2);
            FT_Done_Face(f2);
        }
        // §13: Arabic coverage = cmap presence of U+0633 (س) — the single
        // authoritative check (glyph-id domain is meaningless for coverage).
        mj << "  {\"font\": \"" << fonts[fi] << "\", \"opened\": "
           << (open_ok ? "true" : "false") << ", \"num_glyphs\": " << num_glyphs
           << ", \"variable\": " << (variable ? "true" : "false")
           << ", \"arabic_cmap\": " << (arabic_cmap ? "true" : "false")
           << ", \"notdef_after_shape\": " << notdef_shaped << "}"
           << (fi + 1 < fonts.size() ? "," : "") << "\n";
    }
    mj << "]\n}\n";

    char path[512];
    snprintf(path, sizeof(path), "%s.ppm", out_prefix);
    write_ppm(fb, path);
    snprintf(path, sizeof(path), "%s.png", out_prefix);
    write_png2(fb, path);
    snprintf(path, sizeof(path), "%s_metrics.json", out_prefix);
    std::ofstream mf(path);
    mf << mj.str();
    mf.close();

    printf("EXP101_PERSIAN_PROOF: samples=%zu all_ok=%d out=%s.png\n",
           samples.size(), all_ok ? 1 : 0, out_prefix);
    hb_font_destroy(hb_font);
    FT_Done_FreeType(ft);
    return all_ok ? 0 : 2;
}
