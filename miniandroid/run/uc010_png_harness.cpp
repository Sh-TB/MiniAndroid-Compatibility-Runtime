// CAMPAIGN 010 R1 — differential + benchmark harness (binary A):
//   custom PNGDecoder (MiniAndroid) + libpng 1.6.48 over real APK PNGs.
// Emits per-file TSV: file, decoder, ok, w, h, rgba_sha16, ms
//   usage: uc010_png_harness <corpus_dir> <tsv_out>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <chrono>
#include <algorithm>
#include <dirent.h>

#include "renderer/software_renderer.h"
#include <png.h>

static std::vector<std::string> list_pngs(const std::string& dir) {
    std::vector<std::string> out;
    DIR* d = opendir(dir.c_str());
    if (!d) return out;
    struct dirent* e;
    while ((e = readdir(d))) {
        std::string n = e->d_name;
        if (n.size() > 4 && n.substr(n.size() - 4) == ".png")
            out.push_back(dir + "/" + n);
    }
    closedir(d);
    std::sort(out.begin(), out.end());
    return out;
}

static std::vector<uint8_t> slurp(const std::string& p) {
    std::ifstream f(p, std::ios::binary);
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(f)),
                                 std::istreambuf_iterator<char>());
}

static uint64_t fnv1a(const uint8_t* d, size_t n) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (size_t i = 0; i < n; i++) { h ^= d[i]; h *= 0x100000001b3ULL; }
    return h;
}

static void emit(std::ofstream& tsv, const std::string& name, const char* dec,
                 bool ok, int w, int h, const std::vector<uint8_t>& rgba, double ms,
                 const std::string& err) {
    char h16[17];
    if (ok) snprintf(h16, sizeof h16, "%016llx", (unsigned long long)fnv1a(rgba.data(), rgba.size()));
    else snprintf(h16, sizeof h16, "ERR-%s", err.substr(0, 12).c_str());
    tsv << name << "\t" << dec << "\t" << (ok ? 1 : 0) << "\t" << w << "\t" << h
        << "\t" << h16 << "\t" << ms << "\n";
}

static void run_custom(std::ofstream& tsv, const std::string& name,
                       const std::vector<uint8_t>& bytes) {
    auto t0 = std::chrono::steady_clock::now();
    auto d = miniandroid::renderer::PNGDecoder::decode(bytes);
    auto t1 = std::chrono::steady_clock::now();
    double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    emit(tsv, name, "custom", d.ok, d.width, d.height, d.rgba, ms, d.error);
}

struct LPngCtx { const uint8_t* d; size_t n, off; };
static void lpng_read(png_structp p, png_bytep out, png_size_t n) {
    LPngCtx* c = (LPngCtx*)png_get_io_ptr(p);
    if (c->off + n > c->n) { png_error(p, "read past eof"); return; }
    memcpy(out, c->d + c->off, n); c->off += n;
}

static void run_libpng(std::ofstream& tsv, const std::string& name,
                       const std::vector<uint8_t>& bytes) {
    auto t0 = std::chrono::steady_clock::now();
    std::string err;
    if (png_sig_cmp(bytes.data(), 0, 8)) { emit(tsv, name, "libpng", false, 0, 0, {}, 0, "sig"); return; }
    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, nullptr, nullptr, nullptr);
    png_infop info = png_create_info_struct(png);
    if (!info) { emit(tsv, name, "libpng", false, 0, 0, {}, 0, "info"); return; }
    LPngCtx ctx{bytes.data(), bytes.size(), 0};
    if (setjmp(png_jmpbuf(png))) {
        auto t1 = std::chrono::steady_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        png_destroy_read_struct(&png, &info, nullptr);
        emit(tsv, name, "libpng", false, 0, 0, {}, ms, err.empty() ? "longjmp" : err);
        return;
    }
    png_set_read_fn(png, &ctx, lpng_read);
    png_read_info(png, info);
    png_byte ct = png_get_color_type(png, info);
    png_byte bd = png_get_bit_depth(png, info);
    png_set_palette_to_rgb(png);
    if (bd < 8) png_set_packing(png);
    if (png_get_bit_depth(png, info) == 16) png_set_strip_16(png);
    if (ct == PNG_COLOR_TYPE_GRAY || ct == PNG_COLOR_TYPE_GRAY_ALPHA) png_set_gray_to_rgb(png);
    png_set_expand(png);           // tRNS → alpha, palette/gray expand
    png_set_filler(png, 0xFF, PNG_FILLER_AFTER);
    png_set_interlace_handling(png);
    png_read_update_info(png, info);
    int w = (int)png_get_image_width(png, info);
    int h = (int)png_get_image_height(png, info);
    size_t rowbytes = png_get_rowbytes(png, info);
    std::vector<uint8_t> rgba(rowbytes * h);
    std::vector<png_bytep> rows(h);
    for (int y = 0; y < h; y++) rows[y] = rgba.data() + (size_t)y * rowbytes;
    png_read_image(png, rows.data());
    png_read_end(png, nullptr);
    png_destroy_read_struct(&png, &info, nullptr);
    auto t1 = std::chrono::steady_clock::now();
    double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    emit(tsv, name, "libpng", true, w, h, rgba, ms, "");
}

int main(int argc, char** argv) {
    std::string dir = argc > 1 ? argv[1] : "run/uc010_png_corpus";
    std::string tsvp = argc > 2 ? argv[2] : "/tmp/uc010_png_a.tsv";
    auto files = list_pngs(dir);
    std::ofstream tsv(tsvp);
    tsv << "file\tdecoder\tok\tw\th\trgba\thex\nfile\tdecoder\tok\tw\th\trgba\tms\n";
    size_t ok_c = 0, ok_l = 0;
    double ms_c = 0, ms_l = 0;
    for (auto& p : files) {
        auto bytes = slurp(p);
        run_custom(tsv, p, bytes);
        run_libpng(tsv, p, bytes);
    }
    tsv.close();
    // summarize from file
    std::ifstream in(tsvp); std::string line; std::getline(in, line); // header x2
    std::getline(in, line);
    while (std::getline(in, line)) {
        // parse
        size_t p1 = line.find('\t');
        size_t p2 = line.find('\t', p1 + 1);
        std::string dec = line.substr(p1 + 1, p2 - p1 - 1);
        size_t p3 = line.find('\t', p2 + 1);
        int ok = line[p2 + 1] == '1';
        double ms = atof(line.c_str() + line.rfind('\t') + 1);
        if (dec == "custom") { ms_c += ms; ok_c += ok; }
        if (dec == "libpng") { ms_l += ms; ok_l += ok; }
    }
    printf("corpus %zu PNGs\n", files.size());
    printf("custom : ok %zu (%.2f%%) total %.1f ms\n", ok_c, 100.0 * ok_c / files.size(), ms_c);
    printf("libpng : ok %zu (%.2f%%) total %.1f ms\n", ok_l, 100.0 * ok_l / files.size(), ms_l);
    return 0;
}
