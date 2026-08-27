// EXP-096 §11: Image pipeline verification against real Telegram assets.
//
// Tests MiniAndroid's PNGDecoder against:
//   - Small Telegram PNG icons (res/hmR.png, res/RWK.png, res/MiB.png)
//   - Realistic Telegram PNGs (varied sizes)
//
// Reports: count decoded OK / FAIL, dimensions, color_type, pixel sum
// (a non-zero pixel sum confirms decode produced real pixels).
//
// Build:
//   g++ -std=c++17 -I src -I src/renderer -I third_party/nlohmann_json/include \
//       scripts/exp096_image_pipeline_test.cpp \
//       src/renderer/software_renderer.cpp \
//       src/apk/apk_parser.cpp src/apk/manifest_reader.cpp \
//       -lz -o build/exp096_image_pipeline_test
#include "apk/apk_parser.h"
#include "renderer/software_renderer.h"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using namespace miniandroid::apk;
using namespace miniandroid::renderer;

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <apk>\n";
        return 2;
    }
    ApkParser parser;
    auto info = parser.parse(argv[1]);
    if (!info.is_valid) {
        std::cerr << "FAIL: parse: " << parser.get_last_error() << "\n";
        return 1;
    }
    int png_ok = 0, png_fail = 0;
    int webp_seen = 0, webp_skipped = 0;
    int jpg_seen = 0, jpg_skipped = 0;
    int total_pixels = 0;
    int tested = 0;
    int max_test = 50;  // cap for runtime

    // List all entries
    std::vector<std::string> test_pngs, test_webps, test_jpgs;
    auto entries = parser.list_entries(argv[1]);
    for (const auto& e : entries) {
        if (e.name.size() < 4) continue;
        std::string ext = e.name.substr(e.name.size() - 4);
        if (ext == ".png") test_pngs.push_back(e.name);
        else if (ext == "webp") test_webps.push_back(e.name);
        else if (ext == ".jpg") test_jpgs.push_back(e.name);
    }
    printf("PNG: %zu, WebP: %zu, JPEG: %zu\n",
           test_pngs.size(), test_webps.size(), test_jpgs.size());

    // Test first N small PNGs
    for (const auto& name : test_pngs) {
        if (tested >= max_test) break;
        auto data = parser.extract_entry_cached(name);
        if (data.empty()) { png_fail++; continue; }
        // Verify PNG magic
        if (data.size() < 8 || data[0] != 0x89 || data[1] != 0x50) {
            png_fail++; continue;
        }
        auto dec = PNGDecoder::decode(data);
        if (dec.ok) {
            png_ok++;
            // Sum pixels for sanity
            uint64_t px_sum = 0;
            for (size_t i = 0; i + 3 < dec.rgba.size(); i += 4) {
                px_sum += dec.rgba[i] + dec.rgba[i+1] + dec.rgba[i+2];
            }
            total_pixels += dec.width * dec.height;
            if (tested < 5) {
                printf("  [PNG OK] %s: %dx%d %s px_sum=%llu\n",
                       name.c_str(), dec.width, dec.height,
                       dec.color_type_name.c_str(),
                       (unsigned long long)px_sum);
            }
        } else {
            png_fail++;
            if (png_fail <= 3) {
                printf("  [PNG FAIL] %s: %s\n", name.c_str(), dec.error.c_str());
            }
        }
        tested++;
    }

    printf("\n=== Summary ===\n");
    printf("PNG: %d OK, %d FAIL (%.1f%% pass rate)\n",
           png_ok, png_fail, 100.0 * png_ok / std::max(png_ok + png_fail, 1));
    printf("WebP: %zu (decoder NOT IMPLEMENTED — would need libwebp)\n", test_webps.size());
    printf("JPEG: %zu (decoder NOT IMPLEMENTED — would need libjpeg-turbo)\n", test_jpgs.size());
    printf("Decoded total pixel area: %d\n", total_pixels);
    return (png_fail > png_ok) ? 1 : 0;
}
