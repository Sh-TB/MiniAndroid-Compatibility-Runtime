// CAMPAIGN 010 R1 — binary B: stb_image v2.30-only PNG decode bench.
// Same TSV format as binary A. No rlottie/libpng/custom decoder linked.
//   usage: uc010_stb_bench <corpus_dir> <tsv_out>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <chrono>
#include <algorithm>
#include <dirent.h>

#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#include "stb_image.h"

static uint64_t fnv1a(const uint8_t* d, size_t n) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < n; i++) { h ^= d[i]; h *= 0x100000001b3ULL; }
    return h;
}

static void emit(std::ofstream& tsv, const std::string& name,
                 bool ok, int w, int h, const std::vector<uint8_t>& rgba, double ms,
                 const std::string& err) {
    char h16[24];
    if (ok) snprintf(h16, sizeof h16, "%016llx", (unsigned long long)fnv1a(rgba.data(), rgba.size()));
    else snprintf(h16, sizeof h16, "ERR-%s", err.substr(0, 12).c_str());
    tsv << name << "\tstb230\t" << (ok ? 1 : 0) << "\t" << w << "\t" << h
        << "\t" << h16 << "\t" << ms << "\n";
}

int main(int argc, char** argv) {
    std::string dir = argc > 1 ? argv[1] : "run/uc010_png_corpus";
    std::string tsvp = argc > 2 ? argv[2] : "/tmp/uc010_png_b.tsv";
    std::vector<std::string> files;
    DIR* d = opendir(dir.c_str());
    struct dirent* e;
    while ((e = readdir(d))) {
        std::string n = e->d_name;
        if (n.size() > 4 && n.substr(n.size() - 4) == ".png")
            files.push_back(dir + "/" + n);
    }
    closedir(d);
    std::sort(files.begin(), files.end());

    std::ofstream tsv(tsvp);
    size_t ok = 0; double ms = 0;
    for (auto& p : files) {
        std::ifstream f(p, std::ios::binary);
        std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(f)),
                                    std::istreambuf_iterator<char>());
        auto t0 = std::chrono::steady_clock::now();
        int w, h, c;
        uint8_t* px = stbi_load_from_memory(bytes.data(), (int)bytes.size(), &w, &h, &c, 4);
        auto t1 = std::chrono::steady_clock::now();
        double m = std::chrono::duration<double, std::milli>(t1 - t0).count();
        if (px) {
            std::vector<uint8_t> rgba(px, px + (size_t)w * h * 4);
            emit(tsv, p, true, w, h, rgba, m, "");
            stbi_image_free(px);
            ok++; ms += m;
        } else {
            emit(tsv, p, false, 0, 0, {}, m, stbi_failure_reason());
            ms += m;
        }
    }
    tsv.close();
    printf("stb 2.30: ok %zu/%zu (%.2f%%) total %.1f ms\n", ok, files.size(),
           100.0 * ok / files.size(), ms);
    return 0;
}
