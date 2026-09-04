// EXP-117 (Campaign 005 Phase F): render a REAL Telegram Lottie animation
// through the runtime's RLottieDecoder (rlottie — the same library Telegram
// uses). Extracts N frames -> PNGs -> animation strip evidence.
#include "renderer/software_renderer.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <cstdio>
#include <cstring>

using namespace miniandroid::renderer;
using json = nlohmann::json;

int main(int argc, char** argv) {
    const char* lottie_path = argc > 1 ? argv[1] : "run_exp005/tg_lottie/01N.json";
    std::string out_dir = argc > 2 ? argv[2] : "run_exp005/tg_lottie";
    int frames = argc > 3 ? std::atoi(argv[3]) : 4;

    auto anim = RLottieDecoder::decode_file(lottie_path, 256, 256, frames);
    json report;
    report["experiment"] = "EXP-117 REAL Telegram Lottie render (rlottie)";
    report["lottie_path"] = lottie_path;
    report["ok"] = anim.ok;
    if (!anim.ok) {
        report["error"] = anim.error;
        std::ofstream(out_dir + "/exp117_lottie_report.json") << report.dump(2);
        printf("FAILED: %s\n", anim.error.c_str());
        return 1;
    }
    report["name"] = anim.name;
    report["width"] = anim.width;
    report["height"] = anim.height;
    report["total_frames"] = anim.total_frames;
    report["frame_rate"] = anim.frame_rate;
    report["frames_rendered"] = int(anim.frames_rgba.size()) /
                                (anim.width * anim.height);

    int n = int(anim.frames_rgba.size()) / (anim.width * anim.height);
    for (int f = 0; f < n; ++f) {
        FrameBuffer fb(anim.width, anim.height);
        const uint32_t* src = anim.frames_rgba.data() + size_t(f) * anim.width * anim.height;
        for (int y = 0; y < anim.height; ++y)
            for (int x = 0; x < anim.width; ++x) {
                uint32_t p = src[size_t(y) * anim.width + x];
                fb.set_pixel(x, y, RGBA(uint8_t(p >> 16), uint8_t(p >> 8),
                                        uint8_t(p), uint8_t(p >> 24)));
            }
        char fn[64];
        std::snprintf(fn, sizeof(fn), "exp117_frame_%02d.png", f);
        PNGWriter::write_png(out_dir + "/" + fn, fb);
        report["frames"].push_back(fn);
        std::printf("rendered %s\n", fn);
    }
    std::ofstream(out_dir + "/exp117_lottie_report.json") << report.dump(2) << "\n";
    printf("VERDICT: REAL Telegram Lottie %dx%d @%.0ffps, %d/%d frames rendered via rlottie\n",
           anim.width, anim.height, anim.frame_rate, n, anim.total_frames);
    return 0;
}
