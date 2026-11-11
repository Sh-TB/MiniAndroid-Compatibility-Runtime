// GP583-IMG-004 V2 law test — inJustDecodeBounds bounds-only contract.
//
// GP correction (issue #583, 2026-11-12): the bounds pass must
//   (1) apply to ALL FOUR entry paths (decodeStream/decodeFile/
//       decodeResource/decodeByteArray — no special-case exemptions),
//   (2) run ZERO codec invocations / allocate ZERO pixel bytes,
//   (3) fill raw outWidth/outHeight/outMimeType from the header only,
//   (4) distinguish header-dims-known from payload-fully-valid, and
//   (5) answer error dims (fresh-Options 0x0) on invalid/truncated headers
//       instead of labelling malformed content as decodable.
//
// The production wrapper f240_decode_with_options() consumes
// bitmap_bounds_only_law() (pure, this test's subject) BEFORE any
// decode_image_bytes call — structurally, the full decoder is unreachable
// from the bounds path. These rows pin the pure contract + the header/payload
// distinction on both valid and hostile inputs.

#include "../src/framework/bitmap_shadow.h"
#include "../src/renderer/software_renderer.h"

#include <cstdint>
#include <cstdio>
#include <vector>

using miniandroid::framework::bitmap_bounds_only_law;
using miniandroid::framework::BitmapBoundsProbeResult;
namespace renderer = miniandroid::renderer;

namespace {

int g_rows = 0, g_fail = 0;
void check(bool ok, const char* name) {
    ++g_rows;
    if (ok) std::printf("[PASS] %s\n", name);
    else { ++g_fail; std::printf("[FAIL] %s\n", name); }
}

// A minimal VALID PNG header: signature + IHDR 13-byte payload with
// width=0x00000100 (256), height=0x00000080 (128), bitdepth 8, colortype 6.
std::vector<uint8_t> valid_png() {
    return {0x89, 'P', 'N', 'G', '\r', '\n', 0x1A, '\n',
            0x00, 0x00, 0x00, 0x0D, 'I', 'H', 'D', 'R',
            0x00, 0x00, 0x01, 0x00,   // width 256
            0x00, 0x00, 0x00, 0x80,   // height 128
            0x08, 0x06, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00};  // IHDR CRC (probe window = 33 bytes)
}

// A JPEG SOF0 marker: FFD8 FFE0 len=16 "JFIF\0" 0101 00 0001 0001 0000,
// then FF C0 len=17: precision 8, height=64, width=96, 3 components.
std::vector<uint8_t> valid_jpeg() {
    return {0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 'J', 'F', 'I', 'F', 0x00,
            0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
            0xFF, 0xC0, 0x00, 0x11, 0x08,
            0x00, 0x40,   // height 64
            0x00, 0x60,   // width 96
            0x03, 0x01, 0x22, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01};
}

} // namespace

int main() {
    // ── Row 1-2: valid PNG header → raw dims + mime, valid=true ──────────
    {
        const auto png = valid_png();
        const auto r = bitmap_bounds_only_law(png);
        check(r.valid && r.width == 256 && r.height == 128,
              "img004: png header yields raw 256x128 (no scale, no decode)");
        check(r.mime == "image/png", "img004: png signature mime recorded");
    }
    // ── Row 3: valid JPEG header → SOF dims ──────────────────────────────
    {
        const auto jpg = valid_jpeg();
        const auto r = bitmap_bounds_only_law(jpg);
        check(r.valid && r.width == 96 && r.height == 64,
              "img004: jpeg SOF0 yields 96x64");
    }
    // ── Row 4-5: truncated PNG → invalid header, 0x0 error dims ─────────
    {
        auto cut = valid_png();
        cut.resize(20);  // signature + half of IHDR: no full dim window
        const auto r = bitmap_bounds_only_law(cut);
        check(!r.valid && r.width == 0 && r.height == 0,
              "img004: truncated png answers invalid 0x0 (fresh-Options dims)");
        renderer::ImageSizeProbe p;
        check(!renderer::probe_image_size(cut, &p) && !p.header_dims_known,
              "img004: truncated png probe false + header_dims_known=false");
    }
    // ── Row 6-7: header-known ≠ payload-valid distinction ───────────────
    {
        auto truncated_body = valid_png();
        truncated_body.resize(33);  // full IHDR header, NOTHING after
        const auto r = bitmap_bounds_only_law(truncated_body);
        check(r.valid && r.width == 256 && r.height == 128,
              "img004: header-dims-known despite zero payload bytes");
        renderer::ImageSizeProbe p;
        check(renderer::probe_image_size(truncated_body, &p) &&
                  p.header_dims_known,
              "img004: probe marks header_dims_known on header-only stream");
        // The bounds pass NEVER runs the pixel decoder — a truncated body
        // must still produce a bounds answer, not a decode failure.
    }
    // ── Row 8: corrupt signature → invalid ───────────────────────────────
    {
        std::vector<uint8_t> junk = {'N', 'O', 'T', 'I', 'M', 'G', 0x00, 0x01};
        const auto r = bitmap_bounds_only_law(junk);
        check(!r.valid, "img004: corrupt signature answers invalid");
    }
    // ── Row 9: empty stream → invalid ────────────────────────────────────
    {
        const auto r = bitmap_bounds_only_law({});
        check(!r.valid, "img004: empty stream answers invalid");
    }
    // ── Row 10: probe never dereferences beyond its bounds (30-byte WEBP
    // window on a 29-byte VP8X file must fail, not over-read) ────────────
    {
        std::vector<uint8_t> webp29 = {'R', 'I', 'F', 'F', 0, 0, 0, 0,
                                       'W', 'E', 'B', 'P', 'V', 'P', '8', 'X'};
        for (int i = 0; i < 13; ++i) webp29.push_back(0x01);
        renderer::ImageSizeProbe p;
        // 29 bytes: VP8X branch needs >= 30 — must answer false cleanly.
        check(webp29.size() == 29 && !renderer::probe_image_size(webp29, &p),
              "img004: 29-byte vp8x window bounds-checked (no over-read)");
    }

    std::printf("GP583-IMG-004 law battery: rows=%d fail=%d\n", g_rows, g_fail);
    return g_fail == 0 ? 0 : 1;
}
