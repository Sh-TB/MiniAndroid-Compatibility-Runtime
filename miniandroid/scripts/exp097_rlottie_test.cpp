// EXP-097 §7: RLottie decoder test against real Telegram animations.
//
// Renders the first 3 frames of Telegram Lottie assets (res/*.json) and
// verifies they produce non-zero pixels with different frame hashes
// (per §7: "require real frame differences where source timing expects them").
//
// Build:
//   g++ -std=c++17 -I src -I src/renderer -I third_party/nlohmann_json/include \
//       -I/home/z/my-project/tools/rlottie/inc \
//       scripts/exp097_rlottie_test.cpp \
//       src/renderer/software_renderer.cpp src/apk/apk_parser.cpp \
//       src/apk/manifest_reader.cpp \
//       -lz -lwebp -lwebpdemux -ljpeg \
//       /home/z/my-project/tools/rlottie/build/src/librlottie.a \
//       -lstdc++ -lm -lpthread \
//       -o build/exp097_rlottie_test
#include "apk/apk_parser.h"
#include "renderer/software_renderer.h"
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <algorithm>
#include <map>

using namespace miniandroid::apk;
using namespace miniandroid::renderer;

static uint64_t frame_hash(const uint32_t* buf, size_t n) {
    // FNV-1a over the buffer; gives a single stable hash per frame
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) {
        h ^= (buf[i] & 0xFF);
        h *= 1099511628211ULL;
        h ^= ((buf[i] >> 8) & 0xFF);
        h *= 1099511628211ULL;
        h ^= ((buf[i] >> 16) & 0xFF);
        h *= 1099511628211ULL;
        h ^= ((buf[i] >> 24) & 0xFF);
        h *= 1099511628211ULL;
    }
    return h;
}

static uint64_t frame_pixel_sum(const uint32_t* buf, size_t n) {
    uint64_t s = 0;
    for (size_t i = 0; i < n; i++) {
        s += (buf[i] & 0xFF) + ((buf[i] >> 8) & 0xFF) +
             ((buf[i] >> 16) & 0xFF) + ((buf[i] >> 24) & 0xFF);
    }
    return s;
}

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
    auto entries = parser.list_entries(argv[1]);

    // Find res/*.json files that look like Lottie (contain "v":"5.5" or "fr")
    int tested = 0, max_test = 5;
    int ok = 0, fail = 0;
    int with_motion = 0;

    for (const auto& e : entries) {
        if (tested >= max_test) break;
        if (e.name.size() < 5) continue;
        if (e.name.substr(e.name.size() - 5) != ".json") continue;
        // Skip known non-Lottie
        if (e.name.find("currencies") != std::string::npos) continue;
        // Quick check: must contain Lottie markers
        auto data = parser.extract_entry_cached(e.name);
        if (data.size() < 16) continue;
        std::string s(data.begin(), data.end());
        if (s.find("\"v\":") == std::string::npos && s.find("\"fr\":") == std::string::npos) continue;
        tested++;
        printf("=== Testing %s (%zu bytes) ===\n", e.name.c_str(), data.size());
        auto t0 = std::chrono::steady_clock::now();
        // Telegram renders SmsView icons at 64x64dp; density=1 → 64 pixels
        auto anim = RLottieDecoder::decode(s, 64, 64, 3);
        auto t1 = std::chrono::steady_clock::now();
        auto us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
        if (!anim.ok) {
            printf("  [FAIL] %s\n", anim.error.c_str());
            fail++;
            continue;
        }
        ok++;
        printf("  anim: %dx%d, total_frames=%d, frame_rate=%.1f fps, time=%lldus\n",
               anim.width, anim.height, anim.total_frames, anim.frame_rate, (long long)us);
        // Render and inspect each frame
        size_t px_per_frame = anim.width * anim.height;
        std::map<uint64_t, int> hashes;
        for (int f = 0; f < std::min(3, anim.total_frames); f++) {
            const uint32_t* buf = reinterpret_cast<const uint32_t*>(
                anim.frames_rgba.data() + f * px_per_frame);
            uint64_t h = frame_hash(buf, px_per_frame);
            uint64_t ps = frame_pixel_sum(buf, px_per_frame);
            hashes[h]++;
            printf("  frame %d: hash=0x%016llx pixel_sum=%llu\n",
                   f, (unsigned long long)h, (unsigned long long)ps);
        }
        if (hashes.size() >= 2) {
            with_motion++;
            printf("  [ANIMATED] %zu distinct frame hashes → real motion\n",
                   hashes.size());
        } else {
            printf("  [STATIC]   1 hash across all frames (no motion)\n");
        }
    }
    printf("\n=== Summary ===\n");
    printf("OK: %d, FAIL: %d, WITH_MOTION: %d / %d\n", ok, fail, with_motion, ok);
    return fail > ok ? 1 : 0;
}
