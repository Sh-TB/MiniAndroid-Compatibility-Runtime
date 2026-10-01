// S135 overlay draw_text isolation test — standalone (no runtime link).
#include "../miniandroid/src/renderer/bitmap_font_data.h"
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

using namespace miniandroid::renderer;

struct GlyphView { int advance; const uint8_t* bitmap; };

static GlyphView get_glyph(char c) {
    int i = static_cast<int>(c) - 32;
    if (i < 0 || i >= 95) i = 0;
    return {bitmap_font_table[i].advance, bitmap_font_table[i].bitmap};
}

static void draw_text(std::vector<uint8_t>& fb, int W, int H,
                      const std::string& text, int x, int y) {
    int cx = x;
    for (char ch : text) {
        GlyphView g = get_glyph(ch);
        for (int row = 0; row < 16; ++row) {
            const uint8_t bits = g.bitmap[row];
            for (int col = 0; col < 8; ++col) {
                if (bits & (0x80 >> col)) {
                    int px = cx + col, py = y + row;
                    if (px >= 0 && px < W && py >= 0 && py < H) {
                        size_t i = (static_cast<size_t>(py) * W + px) * 3;
                        fb[i] = 225; fb[i+1] = 228; fb[i+2] = 235;
                    }
                }
            }
        }
        cx += g.advance;
    }
}

int main() {
    const int W = 560, H = 140;
    std::vector<uint8_t> fb(static_cast<size_t>(W) * H * 3, 16);
    for (size_t i = 0; i < fb.size(); i += 3) { fb[i+1] = 20; fb[i+2] = 28; }
    draw_text(fb, W, H, "APK com.droidify", 10, 10);
    draw_text(fb, W, H, "com.droidify.MainActivity", 10, 40);
    draw_text(fb, W, H, "RUN 1790864627419-1", 10, 70);
    draw_text(fb, W, H, "apk=/tmp/my-project/apk-cache/corpus/droidify.apk", 10, 100);
    std::ofstream f("/tmp/s135_font_test.ppm", std::ios::binary);
    f << "P6\n" << W << " " << H << "\n255\n";
    f.write(reinterpret_cast<const char*>(fb.data()), fb.size());
    printf("written /tmp/s135_font_test.ppm\n");
    return 0;
}
