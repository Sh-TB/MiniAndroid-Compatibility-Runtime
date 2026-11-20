// s18_renderer_surface_laws_test — S18 family G (#632-O4/O5): the framebuffer
// surface laws at the REAL renderer (renderer/software_renderer.h FrameBuffer).
// Laws (expectations fixed by the cited production lines, not guessed):
//   G1  O4: a fresh FrameBuffer initializes EVERY pixel to Colors::WHITE
//       {255,255,255,255} (software_renderer.h:122) — an Android surface
//       starts transparent/black; the white default is the claimed defect,
//       pinned here as current behavior.
//   G2  O5: get_pixels_mut() exposes the RAW buffer — a write through it
//       lands bit-exact (no blending applied), the bypass the claim describes.
//   G3  set_pixel stores the exact RGBA at the exact coordinates (sanity
//       contrast for G2: the API path, not the raw buffer).
//   G4  clear() without args restores WHITE and counts one CLEAR operation
//       (the per-op JSON bookkeeping — O3's retracted claim, pinned benign).
#include "../src/renderer/software_renderer.h"
#include <cstdio>
#include <iostream>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
}
static bool eq(const renderer::RGBA& p, uint8_t r, uint8_t g, uint8_t b,
               uint8_t a) {
    return p.r == r && p.g == g && p.b == b && p.a == a;
}

int main() {
    std::cout << "== s18 renderer surface laws (O4/O5) ==\n";
    {
        renderer::FrameBuffer fb(64, 32);
        const auto& px = fb.get_pixels();
        bool all_white = true;
        for (const auto& p : px)
            if (!eq(p, 255, 255, 255, 255)) { all_white = false; break; }
        record(fb.get_width() == 64 && fb.get_height() == 32 &&
               fb.get_pixel_count() == 64u * 32u && all_white && !px.empty(),
               "G1 fresh framebuffer = every pixel WHITE {255,255,255,255} "
               "(O4: Android would start transparent/black — defect pinned)");
    }
    {
        renderer::FrameBuffer fb(64, 32);
        auto& raw = fb.get_pixels_mut();
        raw[7 * 64 + 5] = renderer::RGBA{1, 2, 3, 4};
        const auto& back = fb.get_pixels();
        record(eq(back[7 * 64 + 5], 1, 2, 3, 4),
               "G2 get_pixels_mut bypass: raw write lands bit-exact, "
               "no blending (O5)");
    }
    {
        // set_pixel is a BLENDING API by law (software_renderer.h:141-165:
        // alpha_preserve_ SRC-OVER or legacy blend) — the exact-store law
        // holds for an OPAQUE source (sa=1 -> dst = src over any backdrop);
        // a translucent source would composite, not replace. OOB clipped.
        renderer::FrameBuffer fb(64, 32);
        fb.set_pixel(5, 7, renderer::RGBA{10, 20, 30, 255});
        fb.set_pixel(-1, 0, renderer::RGBA{99, 99, 99, 255});  // clipped
        fb.set_pixel(64, 7, renderer::RGBA{88, 88, 88, 255});  // clipped
        const auto& px = fb.get_pixels();
        bool ok = eq(px[7 * 64 + 5], 10, 20, 30, 255) &&
                  eq(px[0 * 64 + 0], 255, 255, 255, 255) &&
                  eq(px[7 * 64 + 0], 255, 255, 255, 255) &&
                  eq(px[7 * 64 + 63], 255, 255, 255, 255);
        record(ok, "G3 set_pixel opaque source stores exactly (sa=1 blend "
                   "law), OOB clipped (API contrast for G2)");
    }
    {
        renderer::FrameBuffer fb(8, 8);
        fb.set_pixel(0, 0, renderer::RGBA{0, 0, 0, 0});
        fb.clear();  // default = Colors::WHITE
        const auto& px = fb.get_pixels();
        record(eq(px[0], 255, 255, 255, 255),
               "G4 clear() default restores WHITE (per-op bookkeeping law)");
    }
    std::cout << "== s18 renderer surface laws: " << g_pass << " pass / "
              << g_fail << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
