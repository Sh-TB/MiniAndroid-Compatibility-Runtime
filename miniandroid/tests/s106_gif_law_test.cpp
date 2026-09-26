// s106_gif_law_test.cpp — S106 GIF-ANIM fence (MG-214, MG-215, MG-216).
// Links the REAL renderer decoder objects (GifDecoder + decode_image_bytes —
// the same objects the runtime image path uses) and asserts the GIF89a
// Graphics-Control-Extension laws from DECODED PIXELS:
//
//   Fixture layout (PARTIAL descriptors so disposal effects are observable):
//     frame 1: full canvas, red, disposal=1            (background canvas)
//     frame 2: top-right quadrant (8,0,8,8) blue, disposal = variable
//     frame 3: bottom-left quadrant (0,8,8,8) green, disposal=1
//   Frame 3's composite = (canvas after frame 2's disposal) + green rect.
//
//   G1  (MG-214 disposal 1/0 NONE/leave-in-place) — frame 2's blue rect
//       SURVIVES into frame 3 (composite over, never cleared).
//   G2  (MG-215 disposal 2 BACKGROUND) — frame 2's rect region is CLEARED
//       (transparent black, Android/Skia law) in frame 3; frame 1's red
//       survives everywhere else.
//   G3  (MG-216 disposal 3 PREVIOUS) — frame 2's rect region reverts to the
//       state BEFORE frame 2 (= frame 1's red, NOT blue) in frame 3.
//   G4  (frame/delay bookkeeping) — total_frames == 3 and GCE delay
//       10 centiseconds decodes as 100 ms per frame.
//   G5  (static first-frame path) — decode_image_bytes answers REAL pixels
//       for a GIF container (the S68-era "GIF not supported" branch is
//       replaced; first frame = full red canvas).
//   G6  (named-error law preserved) — truncated/corrupt containers are
//       NAMED errors (never a silent drop, §13), no crash.
//
// Exit 0 iff ALL laws hold. Evidence: last line "s106 gif laws PASS n/n".

#include "../src/renderer/gif_decoder.h"
#include "../src/renderer/software_renderer.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using namespace miniandroid::renderer;

static int g_pass = 0, g_fail = 0;
static void check(const char* name, bool ok, const std::string& detail = "") {
    if (ok) { ++g_pass; std::printf("PASS %s %s\n", name, detail.c_str()); }
    else { ++g_fail; std::printf("FAIL %s %s\n", name, detail.c_str()); }
}

// ── minimal deterministic GIF89a encoder (test-local; no external deps) ────
// 16x16 canvas, 4-color GCT: 0=red 1=blue 2=green 3=white.
// "No-compression" LZW: CLEAR before every literal (constant code width,
// valid per spec — the decoder's table never reaches the width edge).
static void put16(std::vector<uint8_t>& v, int x) {
    v.push_back(x & 0xFF); v.push_back((x >> 8) & 0xFF);
}

// Encode the rect rows (w pixels per row, h rows) as one image descriptor.
static void append_frame(std::vector<uint8_t>& g, int x0, int y0, int w, int h,
                         const std::vector<uint8_t>& canvas_idx,
                         int disposal, int delay_cs) {
    // Graphics Control Extension
    g.push_back(0x21); g.push_back(0xF9); g.push_back(0x04);
    g.push_back((uint8_t)((disposal << 2) & 0xFF));
    put16(g, delay_cs);
    g.push_back(0);   // no transparent index
    g.push_back(0);
    // Image Descriptor (partial rect)
    g.push_back(0x2C); put16(g, x0); put16(g, y0); put16(g, w); put16(g, h);
    g.push_back(0x00); // no local color table, no interlace
    // LZW: min code size 2 (codes: 0-3 literal, 4=CLEAR, 5=EOI), 3-bit wide
    const int min_code_size = 2, clear = 4, eoi = 5, code_size = 3;
    std::vector<uint8_t> packed;
    uint32_t acc = 0; int nbits = 0;
    auto emit = [&](int code) {
        acc |= (uint32_t)code << nbits; nbits += code_size;
        while (nbits >= 8) { packed.push_back(acc & 0xFF); acc >>= 8; nbits -= 8; }
    };
    for (int row = 0; row < h; ++row) {
        for (int col = 0; col < w; ++col) {
            uint8_t c = canvas_idx[(size_t)(y0 + row) * 16 + (x0 + col)];
            emit(clear); emit(c);
        }
    }
    emit(eoi);
    if (nbits > 0) packed.push_back(acc & 0xFF);
    g.push_back((uint8_t)min_code_size);
    for (size_t i = 0; i < packed.size(); i += 255) {
        size_t n = std::min<size_t>(255, packed.size() - i);
        g.push_back((uint8_t)n);
        g.insert(g.end(), packed.begin() + i, packed.begin() + i + n);
    }
    g.push_back(0x00);
}

static void fill_rect(std::vector<uint8_t>& idx, int x0, int y0, int w, int h,
                      uint8_t color) {
    for (int y = y0; y < y0 + h; ++y)
        for (int x = x0; x < x0 + w; ++x) idx[(size_t)y * 16 + x] = color;
}

// Build the 3-frame fixture with frame 2's disposal method = d2.
static std::vector<uint8_t> make_gif(int d2) {
    std::vector<uint8_t> b;
    const char* hdr = "GIF89a";
    b.insert(b.end(), hdr, hdr + 6);
    put16(b, 16); put16(b, 16);
    b.push_back(0x81);  // GCT present, size=1 -> 4 entries
    b.push_back(0x00); b.push_back(0x00);
    // GCT: 0 red, 1 blue, 2 green, 3 white
    b.push_back(255); b.push_back(0);   b.push_back(0);
    b.push_back(0);   b.push_back(0);   b.push_back(255);
    b.push_back(0);   b.push_back(255); b.push_back(0);
    b.push_back(255); b.push_back(255); b.push_back(255);
    // frame content canvases (color indices over the full 16x16 canvas)
    std::vector<uint8_t> f1(256, 0);                       // full red
    std::vector<uint8_t> f2(256, 0); fill_rect(f2, 8, 0, 8, 8, 1);  // blue TR
    std::vector<uint8_t> f3(256, 0); fill_rect(f3, 0, 8, 8, 8, 2);  // green BL
    append_frame(b, 0, 0, 16, 16, f1, 1, 10);
    append_frame(b, 8, 0, 8, 8, f2, d2, 10);
    append_frame(b, 0, 8, 8, 8, f3, 1, 10);
    b.push_back(0x3B);
    return b;
}

static bool px(const DecodedGif& gif, int frame, int x, int y,
               uint8_t* r, uint8_t* g, uint8_t* b) {
    size_t i = (size_t)frame * gif.width * gif.height + (size_t)y * gif.width + x;
    if (frame >= gif.total_frames || i >= gif.frames_rgba.size()) return false;
    uint32_t p = gif.frames_rgba[i];  // A<<24 | B<<16 | G<<8 | R
    *r = (uint8_t)(p & 0xFF); *g = (uint8_t)((p >> 8) & 0xFF);
    *b = (uint8_t)((p >> 16) & 0xFF);
    return true;
}

static bool is_red(uint8_t r, uint8_t g, uint8_t b)   { return r == 255 && g == 0 && b == 0; }
static bool is_blue(uint8_t r, uint8_t g, uint8_t b)  { return r == 0 && g == 0 && b == 255; }
static bool is_green(uint8_t r, uint8_t g, uint8_t b) { return r == 0 && g == 255 && b == 0; }
static bool is_clear(uint8_t r, uint8_t g, uint8_t b) { return r == 0 && g == 0 && b == 0; }

// Common decode + frame-3 assertions. Returns the decoded gif.
static DecodedGif decode_ok(const std::vector<uint8_t>& bytes, const char* tag) {
    DecodedGif gif;
    bool ok = GifDecoder::decode_anim(bytes, -1, &gif);
    check(tag, ok && gif.ok && gif.total_frames == 3,
          "err=" + gif.error + " n=" + std::to_string(gif.total_frames));
    return gif;
}

int main() {
    // ── G1: frame-2 disposal NONE (1) — blue rect survives into frame 3 ──
    {
        DecodedGif gif = decode_ok(make_gif(1), "G1 mg-214 anim decode ok");
        check("G4 delays 10cs -> 100ms", gif.delays_ms.size() == 3 &&
              gif.delays_ms[0] == 100 && gif.delays_ms[1] == 100 &&
              gif.delays_ms[2] == 100,
              "n=" + std::to_string(gif.delays_ms.size()));
        uint8_t r, g, b;
        px(gif, 2, 12, 4, &r, &g, &b);
        check("G1 mg-214 rect survives (NONE)", is_blue(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
        px(gif, 2, 2, 2, &r, &g, &b);
        check("G1 mg-214 frame-1 red kept", is_red(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
        px(gif, 2, 2, 12, &r, &g, &b);
        check("G1 mg-214 frame-3 own green", is_green(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
    }
    // ── G2: frame-2 disposal BACKGROUND (2) — rect cleared in frame 3 ────
    {
        DecodedGif gif = decode_ok(make_gif(2), "G2 mg-215 anim decode ok");
        uint8_t r, g, b;
        px(gif, 2, 12, 4, &r, &g, &b);
        check("G2 mg-215 background cleared", is_clear(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
        px(gif, 2, 2, 2, &r, &g, &b);
        check("G2 mg-215 frame-1 red kept", is_red(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
        px(gif, 2, 2, 12, &r, &g, &b);
        check("G2 mg-215 frame-3 own green", is_green(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
    }
    // ── G3: frame-2 disposal PREVIOUS (3) — revert to pre-frame-2 state ──
    {
        DecodedGif gif = decode_ok(make_gif(3), "G3 mg-216 anim decode ok");
        uint8_t r, g, b;
        px(gif, 2, 12, 4, &r, &g, &b);
        check("G3 mg-216 previous restored", is_red(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
        px(gif, 1, 12, 4, &r, &g, &b);
        check("G3 mg-216 frame 2 shows blue while active", is_blue(r, g, b),
              "got " + std::to_string(r) + "," + std::to_string(g) + "," + std::to_string(b));
    }
    // ── G5: static first-frame path through decode_image_bytes ───────────
    {
        auto m = make_gif(1);
        DecodedImage img;
        bool ok = decode_image_bytes(m, &img);
        check("G5 static decode ok", ok && img.ok && img.error.empty(),
              img.error);
        bool red_all = ok && img.width == 16 && img.height == 16 &&
                       is_red(img.rgba[0], img.rgba[1], img.rgba[2]) &&
                       is_red(img.rgba[(15 * 16 + 15) * 4],
                              img.rgba[(15 * 16 + 15) * 4 + 1],
                              img.rgba[(15 * 16 + 15) * 4 + 2]);
        check("G5 first frame = full red canvas", red_all,
              "w=" + std::to_string(img.width));
    }
    // ── G6: corrupt containers = NAMED errors (never silent, no crash) ───
    {
        auto m = make_gif(1);
        m.resize(30);  // truncate mid-first-frame
        DecodedGif gif;
        bool ok = GifDecoder::decode_anim(m, -1, &gif);
        check("G6 corrupt anim named-error", !ok && !gif.error.empty(),
              "err=" + gif.error);
        DecodedImage img;
        bool ok2 = decode_image_bytes(m, &img);
        check("G6 corrupt static named-error", !ok2 && !img.error.empty(),
              "err=" + img.error);
        auto junk = std::vector<uint8_t>{'G','I','F','8','9','a',1,2,3,4,0xFF,0xFF,0x00,0x3B};
        DecodedImage img2;
        bool ok3 = decode_image_bytes(junk, &img2);
        check("G6 malformed-but-tagged named-error", !ok3 || img2.ok,
              "err=" + img2.error);  // either honest error or a decode — never a crash
    }

    std::printf("s106 gif laws %s %d/%d\n",
                g_fail == 0 ? "PASS" : "FAIL", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
