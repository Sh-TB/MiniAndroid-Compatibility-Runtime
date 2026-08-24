// Quick check: decode lock.png with MiniAndroid's PNGDecoder and print
// pixel (16, 0) — PIL says this is (0, 0, 0, 0).

#include "../src/renderer/software_renderer.h"
#include "../src/apk/apk_parser.h"

#include <cstdio>
#include <fstream>
#include <iostream>
#include <vector>

using miniandroid::renderer::PNGDecoder;
using miniandroid::renderer::DecodedImage;
using miniandroid::apk::ApkParser;

int main() {
    std::string apk_path = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk";
    ApkParser apk;
    apk.parse(apk_path);

    for (auto name : {"res/drawable-mdpi-v4/lock.png",
                       "res/drawable-mdpi-v4/settings.png",
                       "res/drawable-mdpi-v4/menu.png"}) {
        auto png = apk.extract_entry_cached(name);
        auto img = PNGDecoder::decode(png);
        if (!img.ok) {
            std::cerr << name << ": decode error: " << img.error << "\n";
            continue;
        }
        std::cout << name << ": " << img.width << "x" << img.height
                  << " (" << img.color_type_name << ")\n";
        // Print first row
        std::cout << "  Row 0:\n";
        for (int x = 0; x < std::min(img.width, 27); x++) {
            const uint8_t* p = img.rgba.data() + (0 * img.width + x) * 4;
            if (p[3] > 0) {
                std::cout << "    (" << x << ",0): (" << (int)p[0] << ","
                          << (int)p[1] << "," << (int)p[2] << "," << (int)p[3] << ")\n";
            }
        }
        // Print row 5 (where there should be content)
        std::cout << "  Row 5 (first 10 non-transparent):\n";
        int shown = 0;
        for (int x = 0; x < img.width && shown < 10; x++) {
            const uint8_t* p = img.rgba.data() + (5 * img.width + x) * 4;
            if (p[3] > 0) {
                std::cout << "    (" << x << ",5): (" << (int)p[0] << ","
                          << (int)p[1] << "," << (int)p[2] << "," << (int)p[3] << ")\n";
                shown++;
            }
        }
    }
    return 0;
}
