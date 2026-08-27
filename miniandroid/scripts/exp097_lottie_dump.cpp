// EXP-097 §7: Dump first 3 frames of a Lottie animation to RGBA files.
#include "renderer/software_renderer.h"
#include <cstdio>
#include <cstring>
#include <string>
using namespace miniandroid::renderer;

int main(int argc, char** argv) {
    std::string s;
    char buf[4096];
    while (true) {
        size_t n = fread(buf, 1, sizeof(buf), stdin);
        if (n == 0) break;
        s.append(buf, n);
    }
    auto anim = RLottieDecoder::decode(s, 64, 64, 3);
    if (!anim.ok) {
        fprintf(stderr, "FAIL: %s\n", anim.error.c_str());
        return 1;
    }
    size_t ppf = 64 * 64;
    for (int f = 0; f < 3; f++) {
        char path[256];
        snprintf(path, sizeof(path), argv[1], f);
        FILE* out = fopen(path, "wb");
        if (!out) continue;
        const uint32_t* b = reinterpret_cast<const uint32_t*>(anim.frames_rgba.data()) + f * ppf;
        for (size_t i = 0; i < ppf; i++) {
            uint8_t rgba[4] = {
                static_cast<uint8_t>(b[i] & 0xFF),
                static_cast<uint8_t>((b[i] >> 8) & 0xFF),
                static_cast<uint8_t>((b[i] >> 16) & 0xFF),
                static_cast<uint8_t>((b[i] >> 24) & 0xFF)
            };
            fwrite(rgba, 1, 4, out);
        }
        fclose(out);
        printf("wrote %s\n", path);
    }
    return 0;
}
