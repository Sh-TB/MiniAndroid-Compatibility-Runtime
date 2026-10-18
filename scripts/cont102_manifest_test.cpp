// CONT-102 debug: parse the c102b probe manifest, print activity attrs.
#include "../miniandroid/src/apk/manifest_reader.h"
#include <fstream>
#include <iostream>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    // argv[1] = path to the APK; we need the raw AndroidManifest.xml —
    // simplest: accept a path to a RAW manifest file instead.
    std::ifstream f(argv[1], std::ios::binary);
    std::vector<char> buf((std::istreambuf_iterator<char>(f)),
                          std::istreambuf_iterator<char>());
    miniandroid::apk::ManifestReader mr;
    std::string raw(buf.data(), buf.size());
    std::vector<unsigned char> bytes(raw.begin(), raw.end());
    auto mi = mr.parse(bytes);
    std::cout << "pkg=" << mi.package_name
              << " activities=" << mi.activities.size()
              << " target=" << mi.target_sdk_version
              << " min=" << mi.min_sdk_version << "\n";
    for (const auto& a : mi.activities) {
        std::cout << "  act " << a.name
                  << " exported=" << a.exported
                  << " declared=" << a.exported_declared
                  << " launchMode=" << a.launch_mode << "\n";
    }
    return 0;
}
