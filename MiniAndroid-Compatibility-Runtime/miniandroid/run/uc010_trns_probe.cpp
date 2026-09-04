// Probe: which libpng transform set yields tRNS→alpha for RGB/gray 8-bit?
#include <cstdio>
#include <cstring>
#include <vector>
#include <fstream>
#include <png.h>
#include <csetjmp>

struct Ctx { const unsigned char* d; size_t n, off; };
static void rd(png_structp p, png_bytep o, png_size_t n) {
    Ctx* c = (Ctx*)png_get_io_ptr(p);
    memcpy(o, c->d + c->off, n); c->off += n;
}

static void probe(const char* path, int mode, const char* label) {
    std::ifstream f(path, std::ios::binary);
    std::vector<unsigned char> buf((std::istreambuf_iterator<char>(f)),
                                    std::istreambuf_iterator<char>());
    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, 0, 0, 0);
    png_infop info = png_create_info_struct(png);
    Ctx ctx{buf.data(), buf.size(), 0};
    if (setjmp(png_jmpbuf(png))) { printf("%-28s LONGJMP\n", label); return; }
    png_set_read_fn(png, &ctx, rd);
    png_read_info(png, info);
    png_byte ct = png_get_color_type(png, info);
    if (mode & 1) png_set_palette_to_rgb(png);
    if (png_get_bit_depth(png, info) < 8) png_set_packing(png);
    if (ct == 0 || ct == 4) png_set_gray_to_rgb(png);
    if (mode & 2) png_set_expand(png);
    if (mode & 4) png_set_tRNS_to_alpha(png);
    if (mode & 8) png_set_filler(png, 0xFF, PNG_FILLER_AFTER);
    png_set_interlace_handling(png);
    png_read_update_info(png, info);
    int w = png_get_image_width(png, info), h = png_get_image_height(png, info);
    int ch = png_get_channels(png, info);
    size_t rb = png_get_rowbytes(png, info);
    std::vector<unsigned char> out(rb * h);
    std::vector<png_bytep> rows(h);
    for (int y = 0; y < h; y++) rows[y] = out.data() + y * rb;
    png_read_image(png, rows.data());
    png_read_end(png, 0);
    printf("%-28s ct=%d ch=%d  first-px:", label, ct, ch);
    for (int i = 0; i < ch; i++) printf(" %3d", out[i]);
    printf("\n");
    png_destroy_read_struct(&png, &info, 0);
}

int main() {
    const char* rgb = "/tmp/uc010_a4/rgb_trns.png";
    const char* gry = "/tmp/uc010_a4/gray_trns.png";
    printf("-- rgb_trns (key 12,34,56 -> alpha should be 0) --\n");
    probe(rgb, 1|8,              "palette_to_rgb+filler");
    probe(rgb, 1|2|8,            "..+png_set_expand");
    probe(rgb, 1|4|8,            "..+tRNS_to_alpha");
    probe(rgb, 1|4,              "..tRNS_to_alpha no-filler");
    probe(rgb, 1|2|4|8,          "expand+tRNS_to_alpha+filler");
    printf("-- gray_trns (key 77 -> alpha 0) --\n");
    probe(gry, 1|8,              "gray_to_rgb+filler");
    probe(gry, 1|2|8,            "..+png_set_expand");
    probe(gry, 1|4|8,            "..+tRNS_to_alpha");
    return 0;
}
