// EXP-088 Phase A4.3 — Standalone PNG decoder test
//
// Loads each known PNG from run/exp088_a4/known_pngs/, decodes it with
// MiniAndroid's own PNGDecoder, and compares the result against the
// expected RGBA buffer that was independently generated and PIL-verified
// by scripts/a4_01_create_known_png.py.
//
// This is the "first failing boundary" diagnostic: if MiniAndroid's decoder
// produces a single byte that differs from PIL, we print the offset and
// exit non-zero.
//
// Usage:
//   ./exp088_a4_png_decoder_test <known_pngs_dir>
//
// Default dir: ../../run/exp088_a4/known_pngs

#include "../src/renderer/software_renderer.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

using miniandroid::renderer::PNGDecoder;
using miniandroid::renderer::DecodedImage;
using json = nlohmann::json;

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

    // Load manifest
    auto manifest_bytes = read_file(dir + "/manifest.json");
    json manifest;
    try {
        manifest = json::parse(manifest_bytes);
    } catch (const std::exception& e) {
        std::cerr << "ERROR: cannot parse manifest.json: " << e.what() << "\n";
        return 2;
    }

    int total = 0, passed = 0;
    for (const auto& case_j : manifest) {
        total++;
        std::string name        = case_j["name"];
        int color_type          = case_j["color_type"];
        int expected_w          = case_j["width"];
        int expected_h          = case_j["height"];
        std::string png_path    = case_j["png_path"];
        std::string expected_rgba_path = case_j["expected_rgba_path"];

        std::cout << "==== " << name << " (color_type=" << color_type << ") ====\n";

        // Read PNG bytes
        std::vector<uint8_t> png_bytes = read_file(png_path);
        std::cout << "  PNG bytes:    " << png_bytes.size() << "\n";

        // Decode with MiniAndroid's decoder
        DecodedImage img = PNGDecoder::decode(png_bytes);
        if (!img.ok) {
            std::cout << "  FAIL: decode error: " << img.error << "\n";
            continue;
        }

        std::cout << "  Decoded:      " << img.width << "x" << img.height
                  << " (" << img.color_type_name << "), "
                  << img.rgba.size() << " bytes RGBA\n";

        if (img.width != expected_w || img.height != expected_h) {
            std::cout << "  FAIL: dimensions mismatch ("
                      << img.width << "x" << img.height << " vs "
                      << expected_w << "x" << expected_h << ")\n";
            continue;
        }

        // Load expected RGBA
        std::vector<uint8_t> expected = read_file(expected_rgba_path);
        std::cout << "  Expected:     " << expected.size() << " bytes RGBA\n";

        if (img.rgba.size() != expected.size()) {
            std::cout << "  FAIL: size mismatch (" << img.rgba.size()
                      << " vs " << expected.size() << ")\n";
            continue;
        }

        // Byte-compare
        size_t first_diff = SIZE_MAX;
        int diff_count = 0;
        for (size_t i = 0; i < img.rgba.size(); i++) {
            if (img.rgba[i] != expected[i]) {
                if (first_diff == SIZE_MAX) first_diff = i;
                diff_count++;
            }
        }

        if (diff_count == 0) {
            std::cout << "  PASS: byte-identical to expected RGBA\n";
            passed++;
        } else {
            std::cout << "  FAIL: " << diff_count << " bytes differ; first at offset "
                      << first_diff << " (got " << int(img.rgba[first_diff])
                      << " expected " << int(expected[first_diff]) << ")\n";
            // Print context
            size_t start = (first_diff >= 8) ? first_diff - 8 : 0;
            size_t end = std::min(first_diff + 16, img.rgba.size());
            std::cout << "  context:";
            for (size_t i = start; i < end; i++) {
                std::cout << " " << int(img.rgba[i]) << "/" << int(expected[i]);
            }
            std::cout << "\n";
        }
    }

    std::cout << "\n==== SUMMARY ====\n";
    std::cout << "Cases:  " << total << "\n";
    std::cout << "Passed: " << passed << "\n";
    std::cout << "Failed: " << (total - passed) << "\n";

    return (passed == total) ? 0 : 1;
}
