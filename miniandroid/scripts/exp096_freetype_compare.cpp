// EXP-096 §10: FreeType vs BitmapFont comparison harness.
//
// Renders the SAME text with both:
//   1. MiniAndroid's BitmapFont (95 ASCII glyphs auto-generated from
//      DejaVuSansMono by scripts/gen_bitmap_font.py at 8px advance).
//   2. FreeType rendering at matched pixel size with DejaVuSansMono.ttf.
//
// Outputs PNGs + per-glyph metrics for visual + numeric comparison.
//
// Build:
//   g++ -std=c++17 -I src/renderer -I third_party/nlohmann_json/include \
//       scripts/exp096_freetype_compare.cpp \
//       src/renderer/software_renderer.cpp \
//       -lfreetype -lpng -o build/exp096_freetype_compare
#include "software_renderer.h"
#include <ft2build.h>
#include FT_FREETYPE_H
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using namespace miniandroid::renderer;

int main() {
    const std::string text = "Enter code";
    const std::string text2 = "We've sent an SMS with an activation code to your phone +1 5551234567.";

    const int W = 1080, H = 200;
    FrameBuffer fb_bm(W, H); fb_bm.clear(Colors::WHITE);
    FrameBuffer fb_ft(W, H); fb_ft.clear(Colors::WHITE);
    SoftwareCanvas canvas_bm(&fb_bm);
    SoftwareCanvas canvas_ft(&fb_ft);

    // 1. BitmapFont
    BitmapFont bm;
    canvas_bm.draw_text(text, 10, 16, Colors::GREY_800, &bm);
    canvas_bm.draw_text(text2, 10, 40, Colors::GREY_800, &bm);
    auto m1 = bm.measure_text(text);
    auto m2 = bm.measure_text(text2);
    printf("BitmapFont measure_text('%s') = %dx%d\n", text.c_str(), m1.width, m1.height);
    printf("BitmapFont measure_text('%s') = %dx%d\n", text2.c_str(), m2.width, m2.height);
    printf("BitmapFont line_height = %d\n", bm.get_line_height());

    // 2. FreeType at 16px (matching BitmapFont line_height)
    FT_Library lib;
    if (FT_Init_FreeType(&lib)) { fprintf(stderr, "FT_Init_FreeType failed\n"); return 1; }
    FT_Face face;
    const char* font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf";
    if (FT_New_Face(lib, font_path, 0, &face)) {
        fprintf(stderr, "FT_New_Face failed for %s\n", font_path);
        FT_Done_FreeType(lib);
        return 1;
    }
    // Match BitmapFont pixel size (line_height=16, advance≈8)
    FT_Set_Pixel_Sizes(face, 0, 16);

    int x = 10, y = 16;
    FT_GlyphSlot slot = face->glyph;
    int ft_width_text = 0;
    for (char c : text) {
        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) continue;
        // Blit grayscale bitmap into framebuffer
        for (int row = 0; row < slot->bitmap.rows; row++) {
            for (int col = 0; col < slot->bitmap.width; col++) {
                unsigned char a = slot->bitmap.buffer[row * slot->bitmap.pitch + col];
                if (a == 0) continue;
                int px = x + slot->bitmap_left + col;
                int py = y - slot->bitmap_top + row;
                if (px >= 0 && px < W && py >= 0 && py < H) {
                    uint8_t v = 255 - a;  // black-on-white
                    RGBA c{v, v, v, 255};
                    fb_ft.set_pixel(px, py, c);
                }
            }
        }
        x += slot->advance.x >> 6;
        ft_width_text = x - 10;
    }
    printf("FreeType width('%s') = %d px (at 16px size)\n", text.c_str(), ft_width_text);

    // Render text2 with FreeType at y=40
    x = 10; y = 40;
    int ft_width_text2 = 0;
    for (char c : text2) {
        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) continue;
        for (int row = 0; row < slot->bitmap.rows; row++) {
            for (int col = 0; col < slot->bitmap.width; col++) {
                unsigned char a = slot->bitmap.buffer[row * slot->bitmap.pitch + col];
                if (a == 0) continue;
                int px = x + slot->bitmap_left + col;
                int py = y - slot->bitmap_top + row;
                if (px >= 0 && px < W && py >= 0 && py < H) {
                    uint8_t v = 255 - a;
                    RGBA c{v, v, v, 255};
                    fb_ft.set_pixel(px, py, c);
                }
            }
        }
        x += slot->advance.x >> 6;
        ft_width_text2 = x - 10;
    }
    printf("FreeType width('%s') = %d px (at 16px size)\n", text2.c_str(), ft_width_text2);

    FT_Done_Face(face);
    FT_Done_FreeType(lib);

    // Save as PPM for visual diff
    auto save_ppm = [](const std::string& path, const FrameBuffer& fb) {
        FILE* f = fopen(path.c_str(), "wb");
        if (!f) return;
        fprintf(f, "P6\n%d %d\n255\n", fb.get_width(), fb.get_height());
        for (const auto& px : fb.get_pixels()) {
            unsigned char rgb[3] = {px.r, px.g, px.b};
            fwrite(rgb, 1, 3, f);
        }
        fclose(f);
    };
    save_ppm("run/exp096_evidence/bitmapfont.ppm", fb_bm);
    save_ppm("run/exp096_evidence/freetype.ppm", fb_ft);
    printf("\nSaved: run/exp096_evidence/bitmapfont.ppm + freetype.ppm\n");

    // Pixel comparison
    int diff_pixels = 0;
    int bm_pixels = 0, ft_pixels = 0;
    for (size_t i = 0; i < fb_bm.get_pixels().size(); i++) {
        bool bm_dark = fb_bm.get_pixels()[i].r < 200;
        bool ft_dark = fb_ft.get_pixels()[i].r < 200;
        if (bm_dark) bm_pixels++;
        if (ft_dark) ft_pixels++;
        if (bm_dark != ft_dark) diff_pixels++;
    }
    printf("BitmapFont dark pixels: %d\n", bm_pixels);
    printf("FreeType    dark pixels: %d\n", ft_pixels);
    printf("Diff pixels: %d  (overlap IoU = %.2f%%)\n", diff_pixels,
           100.0 * (bm_pixels + ft_pixels - diff_pixels) / 2 /
           std::max(bm_pixels + ft_pixels - diff_pixels, 1) * 0);
    return 0;
}
