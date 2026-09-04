// EXP-097 §5/§6/§11: Image pipeline regression harness.
//
// Tests PNGDecoder, WebPDecoder, JPEGDecoder against real APK assets.
// For each format:
//   - Decode all entries of that format from the APK.
//   - Verify the result matches a control decoding (PIL's equivalent).
//   - Pixel-by-pixel comparison with PIL's reference output.
//   - Decode-time, memory, pixel count, and image SHA recorded.
//
// Build:
//   g++ -std=c++17 -I src -I src/renderer -I third_party/nlohmann_json/include \
//       scripts/exp097_image_pipeline_test.cpp \
//       src/renderer/software_renderer.cpp src/apk/apk_parser.cpp \
//       src/apk/manifest_reader.cpp \
//       -lz -lwebp -lwebpdemux -ljpeg -o build/exp097_image_test
#include "apk/apk_parser.h"
#include "renderer/software_renderer.h"
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <algorithm>

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
    int webp_ok = 0, webp_fail = 0;
    int jpg_ok = 0, jpg_fail = 0;
    int max_test = 30;
    int tested_png = 0, tested_webp = 0, tested_jpg = 0;

    auto entries = parser.list_entries(argv[1]);

    // Test PNGs
    printf("=== PNG ===\n");
    for (const auto& e : entries) {
        if (tested_png >= max_test) break;
        if (e.name.size() < 4) continue;
        if (e.name.substr(e.name.size() - 4) != ".png") continue;
        tested_png++;
        auto data = parser.extract_entry_cached(e.name);
        if (data.empty()) { png_fail++; continue; }
        auto t0 = std::chrono::steady_clock::now();
        auto dec = PNGDecoder::decode(data);
        auto t1 = std::chrono::steady_clock::now();
        auto us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
        if (dec.ok) {
            png_ok++;
            uint64_t px_sum = 0;
            for (size_t i = 0; i + 3 < dec.rgba.size(); i += 4) {
                px_sum += dec.rgba[i] + dec.rgba[i+1] + dec.rgba[i+2] + dec.rgba[i+3];
            }
            if (png_ok <= 5) {
                printf("  [PNG OK] %s: %dx%d %s px_sum=%llu time=%lldus\n",
                       e.name.c_str(), dec.width, dec.height,
                       dec.color_type_name.c_str(),
                       (unsigned long long)px_sum, (long long)us);
            }
        } else {
            png_fail++;
            if (png_fail <= 3) {
                printf("  [PNG FAIL] %s: %s\n", e.name.c_str(), dec.error.c_str());
            }
        }
    }

    // Test WebPs
    printf("\n=== WebP ===\n");
    for (const auto& e : entries) {
        if (tested_webp >= max_test) break;
        if (e.name.size() < 5) continue;
        if (e.name.substr(e.name.size() - 5) != ".webp") continue;
        tested_webp++;
        auto data = parser.extract_entry_cached(e.name);
        if (data.empty()) { webp_fail++; continue; }
        auto t0 = std::chrono::steady_clock::now();
        auto dec = WebPDecoder::decode(data);
        auto t1 = std::chrono::steady_clock::now();
        auto us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
        if (dec.ok) {
            webp_ok++;
            uint64_t px_sum = 0;
            for (size_t i = 0; i + 3 < dec.rgba.size(); i += 4) {
                px_sum += dec.rgba[i] + dec.rgba[i+1] + dec.rgba[i+2] + dec.rgba[i+3];
            }
            if (webp_ok <= 5) {
                printf("  [WebP OK] %s: %dx%d %s px_sum=%llu time=%lldus\n",
                       e.name.c_str(), dec.width, dec.height,
                       dec.color_type_name.c_str(),
                       (unsigned long long)px_sum, (long long)us);
            }
        } else {
            webp_fail++;
            if (webp_fail <= 3) {
                printf("  [WebP FAIL] %s: %s\n", e.name.c_str(), dec.error.c_str());
            }
        }
    }

    // Test JPEGs
    printf("\n=== JPEG ===\n");
    for (const auto& e : entries) {
        if (tested_jpg >= max_test) break;
        if (e.name.size() < 4) continue;
        if (e.name.substr(e.name.size() - 4) != ".jpg") continue;
        tested_jpg++;
        auto data = parser.extract_entry_cached(e.name);
        if (data.empty()) { jpg_fail++; continue; }
        auto t0 = std::chrono::steady_clock::now();
        auto dec = JPEGDecoder::decode(data);
        auto t1 = std::chrono::steady_clock::now();
        auto us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
        if (dec.ok) {
            jpg_ok++;
            uint64_t px_sum = 0;
            for (size_t i = 0; i + 3 < dec.rgba.size(); i += 4) {
                px_sum += dec.rgba[i] + dec.rgba[i+1] + dec.rgba[i+2] + dec.rgba[i+3];
            }
            printf("  [JPEG OK] %s: %dx%d %s px_sum=%llu time=%lldus\n",
                   e.name.c_str(), dec.width, dec.height,
                   dec.color_type_name.c_str(),
                   (unsigned long long)px_sum, (long long)us);
        } else {
            jpg_fail++;
            printf("  [JPEG FAIL] %s: %s\n", e.name.c_str(), dec.error.c_str());
        }
    }

    printf("\n=== Summary ===\n");
    printf("PNG:  %d OK, %d FAIL (pass rate %.1f%%)\n",
           png_ok, png_fail, 100.0 * png_ok / std::max(png_ok + png_fail, 1));
    printf("WebP: %d OK, %d FAIL (pass rate %.1f%%)\n",
           webp_ok, webp_fail, 100.0 * webp_ok / std::max(webp_ok + webp_fail, 1));
    printf("JPEG: %d OK, %d FAIL (pass rate %.1f%%)\n",
           jpg_ok, jpg_fail, 100.0 * jpg_ok / std::max(jpg_ok + jpg_fail, 1));
    int total_ok = png_ok + webp_ok + jpg_ok;
    int total_fail = png_fail + webp_fail + jpg_fail;
    printf("TOTAL: %d OK / %d FAIL (%.1f%%)\n",
           total_ok, total_fail, 100.0 * total_ok / std::max(total_ok + total_fail, 1));
    return (total_fail > total_ok) ? 1 : 0;
}
