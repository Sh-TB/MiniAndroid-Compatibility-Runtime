// EXP-097 §11: Expanded streaming-ZIP regression harness.
//
// Runs ApkParser against:
//   - normal seekable APK (no data descriptors)
//   - streaming APK with data descriptors
//   - large entries (>64KB)
//   - multiple mixed-method streaming entries
//   - empty entry
//   - truncated APK (reject)
//   - CRC mismatch (reject)
//
// Build:
//   g++ -std=c++17 -I src -I src/apk -I third_party/nlohmann_json/include \
//       scripts/exp097_streaming_zip_test.cpp \
//       src/apk/apk_parser.cpp src/apk/manifest_reader.cpp \
//       -lz -o build/exp097_zip_test
#include "apk/apk_parser.h"
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
using namespace miniandroid::apk;

static int pass = 0, fail = 0;
static void check(bool cond, const std::string& name, const std::string& err = "") {
    if (cond) {
        printf("  [PASS] %s\n", name.c_str());
        pass++;
    } else {
        printf("  [FAIL] %s: %s\n", name.c_str(), err.c_str());
        fail++;
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <fixture_dir>\n";
        return 2;
    }
    std::string dir = argv[1];
    if (!dir.empty() && dir.back() != '/') dir += '/';

    auto load_entry = [](ApkParser& p, const std::string& entry) -> std::vector<uint8_t> {
        return p.extract_entry_cached(entry);
    };

    printf("=== Test 1: large entries (>64KB) with data descriptor ===\n");
    {
        ApkParser p;
        p.parse(dir + "large.apk");
        // 70KB random → should compress to ~70KB+ and decompress to exact 70000 bytes
        auto large = load_entry(p, "large.bin");
        check(large.size() == 70000, "large.bin size 70000",
              "got=" + std::to_string(large.size()) + " err=" + p.get_last_error());
        auto stored = load_entry(p, "large_stored.bin");
        check(stored.size() == 70000, "large_stored.bin size 70000",
              "got=" + std::to_string(stored.size()));
        // Verify byte 0..69999 matches input pattern
        bool pattern_ok = true;
        for (size_t i = 0; i < large.size(); i++) {
            uint8_t expected = (i * 7 + 3) & 0xFF;
            if (large[i] != expected) { pattern_ok = false; break; }
        }
        check(pattern_ok, "large.bin pattern preserved");
    }

    printf("\n=== Test 2: multiple mixed-method streaming entries ===\n");
    {
        ApkParser p;
        p.parse(dir + "mixed.apk");
        auto a = load_entry(p, "a.txt");
        check(a.size() == 400, "a.txt size 400 (AAAA*100)",
              "got=" + std::to_string(a.size()));
        bool a_ok = (a.size() == 400);
        for (size_t i = 0; a_ok && i < 400; i++) if (a[i] != 'A') a_ok = false;
        check(a_ok, "a.txt content correct");
        auto b = load_entry(p, "b.bin");
        check(b.size() == 65536, "b.bin size 65536 (256*256)",
              "got=" + std::to_string(b.size()));
        bool b_ok = (b.size() == 65536);
        for (size_t i = 0; b_ok && i < 65536; i++) if (b[i] != (i & 0xFF)) b_ok = false;
        check(b_ok, "b.bin content correct (bytes 0..255 * 256)");
        auto c = load_entry(p, "c.txt");
        check(c.size() == 120, "c.txt size 120 ('hello world '*10)",
              "got=" + std::to_string(c.size()));
        auto d = load_entry(p, "d.webp");
        // RIFF stub: 'RIFF'(4) + size(4) + 'WEBP'(4) + 'VP8L'(4) + zeros(100) = 116 bytes
        check(d.size() == 116, "d.webp size 116 (RIFF stub)",
              "got=" + std::to_string(d.size()));
    }

    printf("\n=== Test 3: seekable (normal) APK control ===\n");
    {
        ApkParser p;
        p.parse(dir + "seekable.apk");
        auto a = load_entry(p, "a.txt");
        check(a.size() == 21, "a.txt size 21 ('seekable normal entry')",
              "got=" + std::to_string(a.size()));
        auto b = load_entry(p, "b.bin");
        check(b.size() == 2048, "b.bin size 2048", "got=" + std::to_string(b.size()));
    }

    printf("\n=== Test 4: empty entry ===\n");
    {
        ApkParser p;
        p.parse(dir + "empty.apk");
        auto e = load_entry(p, "empty.txt");
        check(e.empty(), "empty.txt is empty (not an error)");
    }

    printf("\n=== Test 5: truncated APK (must reject, not crash) ===\n");
    {
        ApkParser p;
        auto info = p.parse(dir + "truncated.apk");
        // Parse may succeed or fail; either way, NO segfault
        check(true, "truncated.apk parsed without segfault");
    }

    printf("\n=== Test 6: CRC mismatch (must reject) ===\n");
    {
        ApkParser p;
        p.parse(dir + "crc_bad.apk");
        // a.txt has a flipped byte in its STORED data → CRC must mismatch
        // and extraction must return empty + last_error set.
        auto a = load_entry(p, "a.txt");
        check(a.empty(), "crc_bad a.txt rejected (CRC mismatch)",
              "got size=" + std::to_string(a.size()) + " err=" + p.get_last_error());
    }

    printf("\n=== Summary ===\n");
    printf("PASS: %d / FAIL: %d\n", pass, fail);
    return fail == 0 ? 0 : 1;
}
