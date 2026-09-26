// gif_decoder.cpp — S106 GIF-ANIM-1 (MG-214/215/216): REAL animated-GIF
// decode wired into the ONE format-detecting decoder (S68 §13 law: every
// image consumer goes through decode_image_bytes; a container this decoder
// refuses must be NAMED, never silently dropped).
//
// ROOT CAUSE PROVENANCE (S106, replacing the S68-era EXPLICIT-UNSUPPORTED
// branch): games ship GIF assets (micro-gaps MG-214..216 filed OBSERVED from
// real-APK evidence with "per-class machine fence pending"). The engine
// answered "GIF format not supported (no decoder wired)" for every GIF.
// The vendored stb_image (third_party/stb/stb_image.h) implements the full
// GIF89a LZW decoder INCLUDING the disposal semantics — we wire it instead
// of writing a fourth image decoder by hand (reuse-first law).
//
// LAW SOURCES (checked before writing code — §170 source-first):
//   * GIF89a spec (Graphics Control Extension): disposal method 0/1 = leave
//     in place (composite next frame OVER the canvas), 2 = restore to
//     background (clear the frame rect), 3 = restore to previous (revert to
//     the canvas as it was BEFORE the frame was drawn). Delay = centiseconds.
//   * stb_image animated-GIF implementation (stbi__gif): composites each
//     frame onto the running canvas and applies disposal between frames —
//     exactly the semantics above; disposal==3 with no two-back buffer
//     degrades to disposal==2 (spec-permissible fallback).
//
// Frame layout: frames_rgba holds 32-bit pixels in the SAME layout the
// RLottieDecoder exposes (uint32 = A<<24 | B<<16 | G<<8 | R on little-endian
// bytes, i.e. the byte order execution_engine's anim_frame_rgba repack
// expects), frames concatenated, `total_frames` entries of width*height.
#include "gif_decoder.h"

#define STBI_ONLY_GIF
#define STB_IMAGE_IMPLEMENTATION
#include "../../third_party/stb/stb_image.h"

#include <cstring>
#include <iostream>

namespace miniandroid {
namespace renderer {

static const char* kTag = "[S106-GIF]";

// Static (first-frame) decode for the decode_image_bytes path. A corrupt or
// truncated container is a NAMED error — never a silent drop (§13 law).
bool GifDecoder::decode_first_frame(const std::vector<uint8_t>& bytes,
                                    DecodedImage* out) {
    if (!out) return false;
    out->error.clear();
    int x = 0, y = 0, comp = 0, frames = 0;
    // NOTE: stb writes *z unguarded — always pass a real int (S106).
    stbi_uc* pixels = stbi_load_gif_from_memory(
        const_cast<stbi_uc*>(bytes.data()), static_cast<int>(bytes.size()),
        nullptr, &x, &y, &frames, &comp, 4);
    if (!pixels) {
        const char* reason = stbi_failure_reason();
        out->error = std::string("gif decode failed: ") +
                     (reason ? reason : "unknown stb error");
        std::cerr << kTag << " NAMED-ERROR " << out->error << " ("
                  << bytes.size() << " bytes)" << std::endl;
        return false;
    }
    out->width = x;
    out->height = y;
    out->ok = true;
    out->rgba.assign(pixels, pixels + static_cast<size_t>(x) * y * 4);
    stbi_image_free(pixels);
    return true;
}

// Full animated decode (all frames + delays). max_frames <= 0 = all.
bool GifDecoder::decode_anim(const std::vector<uint8_t>& bytes, int max_frames,
                             DecodedGif* out) {
    if (!out) return false;
    out->error.clear();
    int x = 0, y = 0, z = 0, comp = 0;
    int* delays = nullptr;
    stbi_uc* stacked = stbi_load_gif_from_memory(
        const_cast<stbi_uc*>(bytes.data()), static_cast<int>(bytes.size()),
        &delays, &x, &y, &z, &comp, 4);
    if (!stacked) {
        const char* reason = stbi_failure_reason();
        out->error = std::string("gif anim decode failed: ") +
                     (reason ? reason : "unknown stb error");
        std::cerr << kTag << " NAMED-ERROR " << out->error << " ("
                  << bytes.size() << " bytes)" << std::endl;
        return false;
    }
    out->width = x;
    out->height = y;
    out->total_frames = z;
    const size_t npix = static_cast<size_t>(x) * y;
    if (delays) {
        for (int f = 0; f < z; ++f) out->delays_ms.push_back(delays[f]);
        stbi_image_free(delays);
    } else {
        out->delays_ms.assign(z, 0);
    }
    const int cap = (max_frames > 0) ? max_frames : z;
    out->frames_rgba.reserve(static_cast<size_t>(std::min(cap, z)) * npix);
    // stb gives RGBA bytes per stacked frame; repack to the RLottie uint32
    // layout (A<<24 | B<<16 | G<<8 | R) so animation consumers share ONE
    // frame representation.
    for (int f = 0; f < z && f < cap; ++f) {
        const stbi_uc* src = stacked + static_cast<size_t>(f) * npix * 4;
        for (size_t i = 0; i < npix; ++i) {
            uint32_t r = src[i * 4 + 0], g = src[i * 4 + 1],
                     b = src[i * 4 + 2], a = src[i * 4 + 3];
            out->frames_rgba.push_back((a << 24) | (b << 16) | (g << 8) | r);
        }
    }
    stbi_image_free(stacked);
    out->ok = true;
    std::cerr << kTag << " decoded " << out->total_frames << " frames "
              << x << "x" << y << " (" << bytes.size() << " bytes)"
              << std::endl;
    return true;
}

}  // namespace renderer
}  // namespace miniandroid
