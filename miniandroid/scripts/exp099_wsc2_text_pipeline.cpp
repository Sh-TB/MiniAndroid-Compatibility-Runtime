// WS-C2-E1: Full text pipeline proof — Unicode → FriBidi → HarfBuzz →
// FreeType → glyph bitmaps → framebuffer (PPM+PNG), with metrics JSON.
//
// Mirrors the campaign required pipeline (§6 WS-C2):
//   Unicode → bidi → shaping → glyph selection → metrics →
//   rasterization → layout → framebuffer
//
// Build: see scripts/build_wsc2_text_pipeline.sh
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
        uint32_t a = c.a;
        d.r = (c.r * a + d.r * (255 - a)) / 255;
        d.g = (c.g * a + d.g * (255 - a)) / 255;
        d.b = (c.b * a + d.b * (255 - a)) / 255;
    }
};

static void write_ppm(const Framebuffer& fb, const char* path) {
    std::ofstream f(path, std::ios::binary);
    f << "P6\n" << fb.w << " " << fb.h << "\n255\n";
    for (auto& p : fb.px) { f << p.r << p.g << p.b; }
}

// Reorder logical → visual via FriBidi, return visual codepoints + base dir.
// Base direction: AOSP TextDirectionHeuristics.FIRSTSTRONG default — the
// paragraph direction is taken from the FIRST STRONG directional character.
static std::vector<uint32_t> apply_bidi(const std::u32string& in, FriBidiParType& base) {
    std::vector<FriBidiChar> src(in.begin(), in.end());
    // First-strong heuristic (mirrors android.text.TextDirectionHeuristics)
    base = FRIBIDI_PAR_LTR;
    for (FriBidiChar ch : src) {
        FriBidiCharType t = fribidi_get_bidi_type(ch);
        if (t == FRIBIDI_TYPE_R || t == FRIBIDI_TYPE_AL) { base = FRIBIDI_PAR_RTL; break; }
        if (t == FRIBIDI_TYPE_L) { base = FRIBIDI_PAR_LTR; break; }
    }
    std::vector<FriBidiChar> dst(src.size() + 1);
    std::vector<FriBidiStrIndex> map_l2v(src.size() + 1, 0);
    std::vector<FriBidiStrIndex> map_v2l(src.size() + 1, 0);
    std::vector<FriBidiLevel> embed(src.size() + 1, 0);
    FriBidiLevel level = fribidi_log2vis(const_cast<FriBidiChar*>(src.data()),
                                          (FriBidiStrIndex)src.size(),
                                          &base, dst.data(),
                                          map_l2v.data(), map_v2l.data(),
                                          embed.data());
    fribidi_boolean ok = (level >= 0);
    if (!ok) return src;
    dst.resize(src.size());
    return dst;
}

int main(int argc, char** argv) {
    // Test strings: Persian/Arabic mixed bidi + Latin control (SMS-screen-like)
    std::vector<std::pair<std::string, std::string>> samples = {
        {"fa_code_msg", "کد تأیید تلگرام ۱۲۳۴۵ — Telegram code 67890"},
        {"fa_sms_body", "ما یک کد به شماره شما فرستادیم +98 912 345 6789"},
        {"en_enter_code", "Enter code"},
        {"mixed_didnt", "کد را دریافت نکردید؟ Didn't get the code?"},
    };
    const char* font_path = (argc > 1) ? argv[1]
        : "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
    const int FONT_PX = 42;

    FT_Library ft;
    if (FT_Init_FreeType(&ft)) { fprintf(stderr, "FT init fail\n"); return 1; }
    FT_Face face;
    if (FT_New_Face(ft, font_path, 0, &face)) { fprintf(stderr, "FT face fail\n"); return 1; }
    FT_Set_Pixel_Sizes(face, 0, FONT_PX);

    hb_font_t* hb_font = hb_ft_font_create(face, nullptr);
    if (!hb_font) { fprintf(stderr, "HB font fail\n"); return 1; }

    // Canvas: 1080-wide strip like the runtime's framebuffer rows
    Framebuffer fb(1080, 340);
    int pen_y = 56;
    std::ostringstream metrics;
    metrics << "[\n";

    // Convert UTF-8 → UTF-32
    auto utf8_to_u32 = [](const std::string& s) {
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
    };

    bool all_ok = true;
    for (size_t si = 0; si < samples.size(); ++si) {
        auto& [name, text] = samples[si];
        std::u32string logical = utf8_to_u32(text);
        FriBidiParType base = FRIBIDI_PAR_LTR;
        std::vector<uint32_t> visual = apply_bidi(logical, base);

        // Shape the VISUAL order string with HarfBuzz
        hb_buffer_t* buf = hb_buffer_create();
        hb_buffer_add_utf32(buf, visual.data(), (int)visual.size(), 0, -1);
        hb_buffer_guess_segment_properties(buf);
        hb_shape(hb_font, buf, nullptr, 0);
        unsigned n;
        hb_glyph_info_t* info = hb_buffer_get_glyph_infos(buf, &n);
        hb_glyph_position_t* pos = hb_buffer_get_glyph_positions(buf, &n);

        // Layout: RTL base → right-align at 1080-40; LTR → left-align 40
        int total_w = 0;
        for (unsigned g = 0; g < n; ++g) total_w += (pos[g].x_advance >> 6);
        int pen_x = (base == FRIBIDI_PAR_RTL) ? (1080 - 40 - total_w) : 40;

        int minx = 1 << 30, maxx = -(1 << 30);
        int shaped_dark = 0;
        for (unsigned g = 0; g < n; ++g) {
            if (FT_Load_Glyph(face, info[g].codepoint, FT_LOAD_DEFAULT)) continue;
            FT_Render_Glyph(face->glyph, FT_RENDER_MODE_NORMAL);
            FT_GlyphSlot gs = face->glyph;
            int gx = pen_x + (pos[g].x_offset >> 6) + gs->bitmap_left;
            int gy = pen_y - (pos[g].y_offset >> 6) - gs->bitmap_top;
            if (gx < minx) minx = gx;
            if (gx + (int)gs->bitmap.width > maxx) maxx = gx + gs->bitmap.width;
            for (unsigned r = 0; r < gs->bitmap.rows; ++r) {
                for (unsigned c = 0; c < gs->bitmap.width; ++c) {
                    uint8_t a = gs->bitmap.buffer[r * gs->bitmap.pitch + c];
                    if (a) ++shaped_dark;
                    fb.blend(gx + (int)c, gy + (int)r, {20, 20, 20, a});
                }
            }
            pen_x += (pos[g].x_advance >> 6);
        }
        bool ok = (n > 0 && total_w > 0 && maxx > minx);
        all_ok = all_ok && ok;
        metrics << "  {\"sample\": \"" << name << "\", \"base_dir\": \""
                << (base == FRIBIDI_PAR_RTL ? "RTL" : "LTR")
                << "\", \"codepoints\": " << logical.size()
                << ", \"glyphs\": " << n
                << ", \"advance_px\": " << total_w
                << ", \"bbox\": [" << minx << ", " << maxx << "]"
                << ", \"dark_px\": " << shaped_dark
                << ", \"ok\": " << (ok ? "true" : "false") << "}"
                << (si + 1 < samples.size() ? "," : "") << "\n";
        pen_y += 70;
        hb_buffer_destroy(buf);
    }
    metrics << "]\n";

    write_ppm(fb, "run/wsc2_text_pipeline.ppm");
    std::ofstream("run/wsc2_text_pipeline_metrics.json") << metrics.str();

    // Non-white pixel count on the framebuffer (§14 evidence)
    long nonwhite = 0;
    for (auto& p : fb.px) if (!(p.r == 255 && p.g == 255 && p.b == 255)) ++nonwhite;
    printf("TEXT_PIPELINE: samples=%zu font=%s ok=%d nonwhite=%ld\n",
           samples.size(), font_path, all_ok, nonwhite);
    printf(" framebuffer: run/wsc2_text_pipeline.ppm\n");
    printf(" metrics: run/wsc2_text_pipeline_metrics.json\n");

    hb_font_destroy(hb_font);
    FT_Done_Face(face);
    FT_Done_FreeType(ft);
    return all_ok ? 0 : 1;
}
