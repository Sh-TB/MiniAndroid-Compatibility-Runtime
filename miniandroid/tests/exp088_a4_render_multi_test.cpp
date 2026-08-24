// EXP-088 Phase A4.6 — Multiple-image render test
//
// Draws multiple known-PNG images into a single framebuffer, each at a
// different (x, y) location, then verifies all images reach the framebuffer
// with correct pixel values.
//
// This mimics what simplestopwatch does (3 ImageButtons in a row), without
// going through the ViewShadow plumbing.
//
// Usage:
//   ./exp088_a4_render_multi_test <known_pngs_dir>

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

struct ImagePlacement {
    std::string name;
    int x;
    int y;
    int w;
    int h;
    std::vector<uint8_t> rgba;  // w * h * 4 bytes
};

int main(int argc, char** argv) {
    std::string dir = (argc > 1) ? argv[1]
        : "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp088_a4/known_pngs";
    std::string out_dir = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp088_a4/render_multi";

    auto manifest_bytes = read_file(dir + "/manifest.json");
    json manifest;
    try {
        manifest = json::parse(manifest_bytes);
    } catch (const std::exception& e) {
        std::cerr << "ERROR: cannot parse manifest.json: " << e.what() << "\n";
        return 2;
    }

    // Decode all 4 known PNGs into RGBA buffers
    std::vector<ImagePlacement> placements;
    int x = 5;
    int y = 5;
    for (const auto& case_j : manifest) {
        std::string name     = case_j["name"];
        std::string png_path = case_j["png_path"];
        std::vector<uint8_t> png_bytes = read_file(png_path);
        DecodedImage img = PNGDecoder::decode(png_bytes);
        if (!img.ok) {
            std::cerr << "FAIL: decode " << name << ": " << img.error << "\n";
            return 1;
        }
        placements.push_back({name, x, y, img.width, img.height, img.rgba});
        // Place images side-by-side with a 5-pixel gap
        x += img.width + 5;
    }

    // Render into a framebuffer sized to hold all images
    int total_w = 5 + placements.size() * (16 + 5) + 5;
    int fb_w = std::max(total_w, 100);
    int fb_h = 80;

    FrameBuffer fb(fb_w, fb_h);
    fb.clear(Colors::WHITE);
    SoftwareCanvas canvas(&fb);

    for (const auto& p : placements) {
        canvas.draw_image(p.rgba.data(), p.w, p.h, p.x, p.y);
    }

    // Write framebuffer to disk
    std::string out_path = out_dir + "/multi_render.png";
    std::string mkdir_cmd = "mkdir -p " + out_dir;
    std::system(mkdir_cmd.c_str());
    if (!PNGWriter::write_png(out_path, fb)) {
        std::cerr << "FAIL: cannot write PNG\n";
        return 1;
    }

    // Verify each placement's pixels match alpha-blended source
    bool all_ok = true;
    for (const auto& p : placements) {
        int mismatch_count = 0;
        int first_x = -1, first_y = -1;
        for (int dy = 0; dy < p.h; dy++) {
            for (int dx = 0; dx < p.w; dx++) {
                const uint8_t* sp = p.rgba.data() + (dy * p.w + dx) * 4;
                RGBA src_px(sp[0], sp[1], sp[2], sp[3]);
                RGBA expected = miniandroid::renderer::blend(src_px, Colors::WHITE);
                RGBA got = fb.get_pixel(p.x + dx, p.y + dy);
                if (got.r != expected.r || got.g != expected.g ||
                    got.b != expected.b || got.a != expected.a) {
                    mismatch_count++;
                    if (first_x < 0) { first_x = dx; first_y = dy; }
                }
            }
        }
        std::cout << "[" << p.name << "] at (" << p.x << "," << p.y << ") "
                  << p.w << "x" << p.h
                  << "  mismatch_count=" << mismatch_count;
        if (mismatch_count > 0) {
            std::cout << " first at (" << first_x << "," << first_y << ")";
        }
        std::cout << (mismatch_count == 0 ? "  PASS\n" : "  FAIL\n");
        if (mismatch_count > 0) all_ok = false;
    }

    // Also verify the gaps between images are pure white
    bool gaps_white = true;
    for (int yy = 5; yy < 5 + 16; yy++) {
        for (int xx = 0; xx < fb_w; xx++) {
            // Skip if this pixel is inside any image
            bool in_image = false;
            for (const auto& p : placements) {
                if (xx >= p.x && xx < p.x + p.w && yy >= p.y && yy < p.y + p.h) {
                    in_image = true;
                    break;
                }
            }
            if (in_image) continue;
            RGBA got = fb.get_pixel(xx, yy);
            if (got.r != 255 || got.g != 255 || got.b != 255) {
                gaps_white = false;
                std::cout << "  gap mismatch at (" << xx << "," << yy << "): "
                          << (int)got.r << "," << (int)got.g << "," << (int)got.b << "\n";
                break;
            }
        }
        if (!gaps_white) break;
    }
    std::cout << "gaps_white: " << (gaps_white ? "YES" : "NO") << "\n";

    std::cout << "\nScreenshot: " << out_path << "\n";
    std::cout << (all_ok && gaps_white ? "ALL PASS\n" : "FAIL\n");
    return (all_ok && gaps_white) ? 0 : 1;
}
