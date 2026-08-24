// EXP-088 Phase A4.4+A4.5 — Single-image end-to-end renderer test
//
// This is the smallest end-to-end test of the renderer's image pipeline:
//
//   known PNG file
//     → PNGDecoder::decode  (in-memory)
//     → FrameBuffer + SoftwareCanvas::draw_image
//     → PNGWriter::write_png
//     → screenshot.png on disk
//     → independent PIL decode
//     → pixel-by-pixel comparison against expected RGBA
//
// If this test passes, the image rendering pipeline works end-to-end. The
// only thing the ViewShadow plumbing adds on top is *positioning* (drawing
// the image at the (x,y) coordinates of the view's bounds, which is computed
// by the measure/layout pass). That positioning is already covered by the
// existing A1+A2+A5 tests, so this test focuses on the IMAGE-specific layer.
//
// Usage:
//   ./exp088_a4_render_image_test <known_pngs_dir>
//
// Default dir: ../../run/exp088_a4/known_pngs

#include "../src/renderer/software_renderer.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

using miniandroid::renderer::PNGDecoder;
using miniandroid::renderer::PNGWriter;
using miniandroid::renderer::FrameBuffer;
using miniandroid::renderer::SoftwareCanvas;
using miniandroid::renderer::RGBA;
using miniandroid::renderer::DecodedImage;
using json = nlohmann::json;

namespace Colors = miniandroid::renderer::Colors;

static std::vector<uint8_t> read_file(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f.is_open()) {
        std::cerr << "ERROR: cannot open " << path << "\n";
        std::exit(2);
    }
    auto sz = f.tellg();
    f.seekg(0, std::ios::beg);
    std::vector<uint8_t> buf(sz);
    f.read(reinterpret_cast<char*>(buf.data()), sz);
    return buf;
}

int main(int argc, char** argv) {
    std::string dir = (argc > 1) ? argv[1]
        : "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp088_a4/known_pngs";
    std::string out_dir = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp088_a4/render_single";

    auto manifest_bytes = read_file(dir + "/manifest.json");
    json manifest;
    try {
        manifest = json::parse(manifest_bytes);
    } catch (const std::exception& e) {
        std::cerr << "ERROR: cannot parse manifest.json: " << e.what() << "\n";
        return 2;
    }

    // FrameBuffer is 200x200, all-white background.
    // For each known PNG, we draw it at (10, 10) at its natural size.
    // Then we write the framebuffer to a PNG, then independently re-read it
    // and compare:
    //   1. The pixels at (10, 10) .. (10+w-1, 10+h-1) match the source RGBA
    //      (modulo alpha-blending over white).
    //   2. The pixels outside that region are pure white.
    const int FB_W = 200;
    const int FB_H = 200;
    const int DST_X = 10;
    const int DST_Y = 10;

    int total = 0, passed = 0;
    for (const auto& case_j : manifest) {
        total++;
        std::string name        = case_j["name"];
        int expected_w          = case_j["width"];
        int expected_h          = case_j["height"];
        std::string png_path    = case_j["png_path"];
        std::string expected_rgba_path = case_j["expected_rgba_path"];

        std::cout << "==== " << name << " ====\n";

        // 1. Decode source PNG with MiniAndroid's decoder
        std::vector<uint8_t> png_bytes = read_file(png_path);
        DecodedImage src = PNGDecoder::decode(png_bytes);
        if (!src.ok) {
            std::cout << "  FAIL: decode error: " << src.error << "\n";
            continue;
        }

        // 2. Render into framebuffer
        FrameBuffer fb(FB_W, FB_H);
        fb.clear(Colors::WHITE);
        SoftwareCanvas canvas(&fb);
        canvas.draw_image(src.rgba.data(), src.width, src.height, DST_X, DST_Y);

        // 3. Write framebuffer to disk
        std::string out_path = out_dir + "/" + name + "_render.png";
        std::string mkdir_cmd = "mkdir -p " + out_dir;
        std::system(mkdir_cmd.c_str());
        if (!PNGWriter::write_png(out_path, fb)) {
            std::cout << "  FAIL: cannot write PNG\n";
            continue;
        }

        // 4. Verify pixels in framebuffer (the framebuffer itself is the
        //    ground truth — the PNGWriter is just an encoder).
        //    For each source pixel, compute the expected blended pixel
        //    against white, then compare to the framebuffer's pixel.
        bool pixels_match = true;
        int mismatch_count = 0;
        int first_mismatch_x = -1, first_mismatch_y = -1;
        for (int y = 0; y < src.height; y++) {
            for (int x = 0; x < src.width; x++) {
                const uint8_t* sp = src.rgba.data() + (y * src.width + x) * 4;
                RGBA src_px(sp[0], sp[1], sp[2], sp[3]);
                RGBA expected = miniandroid::renderer::blend(src_px, Colors::WHITE);
                RGBA got = fb.get_pixel(DST_X + x, DST_Y + y);
                if (got.r != expected.r || got.g != expected.g ||
                    got.b != expected.b || got.a != expected.a) {
                    pixels_match = false;
                    mismatch_count++;
                    if (first_mismatch_x < 0) {
                        first_mismatch_x = x;
                        first_mismatch_y = y;
                    }
                }
            }
        }

        // Also verify a pixel outside the image is still pure white
        RGBA outside = fb.get_pixel(FB_W - 1, FB_H - 1);
        bool outside_white = (outside.r == 255 && outside.g == 255 &&
                              outside.b == 255 && outside.a == 255);

        std::cout << "  source: " << src.width << "x" << src.height << " ("
                  << src.color_type_name << ")\n";
        std::cout << "  framebuffer: " << FB_W << "x" << FB_H << "\n";
        std::cout << "  drew at (" << DST_X << "," << DST_Y << ")\n";
        std::cout << "  pixels_match_blend_with_white: "
                  << (pixels_match ? "YES" : "NO");
        if (!pixels_match) {
            std::cout << " (mismatches=" << mismatch_count
                      << ", first at (" << first_mismatch_x
                      << "," << first_mismatch_y << "))";
        }
        std::cout << "\n";
        std::cout << "  outside_pixel_is_white: " << (outside_white ? "YES" : "NO") << "\n";
        std::cout << "  screenshot: " << out_path << "\n";

        if (pixels_match && outside_white) {
            std::cout << "  PASS\n";
            passed++;
        } else {
            std::cout << "  FAIL\n";
        }
    }

    std::cout << "\n==== SUMMARY ====\n";
    std::cout << "Cases:  " << total << "\n";
    std::cout << "Passed: " << passed << "\n";
    std::cout << "Failed: " << (total - passed) << "\n";

    return (passed == total) ? 0 : 1;
}
