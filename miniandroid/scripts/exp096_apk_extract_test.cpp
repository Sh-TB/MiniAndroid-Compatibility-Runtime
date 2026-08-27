// EXP-096 §5: Standalone ApkParser extractor test for streaming-ZIP entries.
//
// Builds an APK with mixed normal + data-descriptor entries (see
// exp096_streaming_zip_fixture.py) and verifies that ApkParser extracts
// every entry with the correct bytes — including LFH-size=0 entries.
//
// Build:
//   g++ -std=c++17 -I src/apk -I third_party/nlohmann-json/include \
//       src/apk/apk_parser.cpp scripts/exp096_apk_extract_test.cpp \
//       -lz -o build/apk_extract_test
//
// Run:
//   ./build/apk_extract_test /tmp/mixed.apk
#include "apk_parser.h"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

using namespace miniandroid::apk;

static std::vector<uint8_t> read_file(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(f)),
                                 std::istreambuf_iterator<char>());
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <apk_path>\n";
        return 2;
    }
    ApkParser parser;
    auto info = parser.parse(argv[1]);
    if (!info.is_valid) {
        std::cerr << "FAIL: parse: " << parser.get_last_error() << "\n";
        return 1;
    }
    std::cout << "Package: " << info.package_name << "\n";

    // Expected contents — kept in sync with the python fixture generator.
    // NOTE: these are the SAME bytes the python script put in.
    static const struct { const char* name; const char* content; size_t len; } expected[] = {
        {"normal.txt", "Hello, normal ZIP entry!", 24},
        {"streaming.txt", "Hello, streaming data-descriptor entry!", 39},
        {"empty.txt", "", 0},
    };
    // binary ones we compare as bytes:
    static const uint8_t png_magic[] = {0x89,'P','N','G','\r','\n',0x1a,'\n'};
    static const uint8_t compressed_first = 0;
    static const uint8_t compressed_last = 255;

    int pass = 0, fail = 0;

    for (const auto& e : expected) {
        auto data = parser.extract_entry_cached(e.name);
        if (data.size() != e.len) {
            std::cerr << "FAIL [" << e.name << "]: size=" << data.size()
                      << " expected=" << e.len << " err=" << parser.get_last_error() << "\n";
            fail++;
            continue;
        }
        if (e.len > 0 && std::memcmp(data.data(), e.content, e.len) != 0) {
            std::cerr << "FAIL [" << e.name << "]: content mismatch\n";
            fail++;
            continue;
        }
        std::cout << "PASS [" << e.name << "]: " << e.len << " bytes\n";
        pass++;
    }

    // compressed.bin = bytes(range(256)) * 8 → 2048 bytes
    {
        auto data = parser.extract_entry_cached("compressed.bin");
        if (data.size() != 2048) {
            std::cerr << "FAIL [compressed.bin]: size=" << data.size()
                      << " err=" << parser.get_last_error() << "\n";
            fail++;
        } else if (data[0] != 0 || data[255] != 255 || data[256] != 0) {
            std::cerr << "FAIL [compressed.bin]: content mismatch ("
                      << (int)data[0] << "," << (int)data[255] << ","
                      << (int)data[256] << ")\n";
            fail++;
        } else {
            std::cout << "PASS [compressed.bin]: 2048 bytes\n";
            pass++;
        }
    }

    // png_magic.bin
    {
        auto data = parser.extract_entry_cached("png_magic.bin");
        if (data.size() != 72) {
            std::cerr << "FAIL [png_magic.bin]: size=" << data.size()
                      << " err=" << parser.get_last_error() << "\n";
            fail++;
        } else if (std::memcmp(data.data(), png_magic, 8) != 0) {
            std::cerr << "FAIL [png_magic.bin]: PNG magic mismatch\n";
            fail++;
        } else {
            std::cout << "PASS [png_magic.bin]: 72 bytes (PNG magic OK)\n";
            pass++;
        }
    }

    std::cout << "\n=== Summary ===\n";
    std::cout << "PASS: " << pass << " / FAIL: " << fail << "\n";
    return fail == 0 ? 0 : 1;
}
