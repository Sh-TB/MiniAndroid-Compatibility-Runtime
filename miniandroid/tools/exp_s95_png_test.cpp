// exp_s95_png_test.cpp — S95 differential probe: decode real-APK PNG bytes
// with the runtime's PNGDecoder and dump center/corner pixels (PIL oracle
// cross-check for the P-mode+tRNS settings.png glyph divergence).
#include "renderer/software_renderer.h"
#include <cstdio>
#include <fstream>
#include <vector>

using namespace miniandroid::renderer;

int main(int argc, char** argv) {
    if (argc < 2) { std::fprintf(stderr, "usage: %s png_file\n", argv[0]); return 2; }
    std::ifstream f(argv[1], std::ios::binary);
    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),
                               std::istreambuf_iterator<char>());
    DecodedImage out;
    bool ok = decode_image_bytes(bytes, &out);
    std::printf("ok=%d size=%dx%d type=%s err=%s\n", ok ? 1 : 0, out.width,
                out.height, out.color_type_name.c_str(), out.error.c_str());
    if (!ok) return 1;
    auto px = [&](int x, int y) {
        const uint8_t* p = &out.rgba[((size_t)y * out.width + x) * 4];
        std::printf("  (%d,%d) = %d,%d,%d,%d\n", x, y, p[0], p[1], p[2], p[3]);
    };
    px(2, 2);                 // background (transparent in PIL)
    px(out.width / 2, out.height / 2);   // gear center (hole -> transparent)
    px(out.width / 2, 10);    // gear teeth top area
    px(out.width / 4, out.height / 2);   // gear body
    return 0;
}
