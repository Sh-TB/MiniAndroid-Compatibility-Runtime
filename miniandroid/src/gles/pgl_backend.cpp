// CAMPAIGN 010 R9 — PGLBackend implementation.
// Exactly one TU defines PORTABLEGL_IMPLEMENTATION (this file).
// PortableGL: MIT, rswinkle/PortableGL @ 7cf39dc1741e (verified live 2026-08-30).
//
// PGL headless model (per the embedded canonical example in portablegl.h):
// draw with standard gl* calls, then read `backbuf` directly — there is no
// swap step. frame_end() therefore only tracks a frame counter.
#include "pgl_backend.h"

#define PORTABLEGL_IMPLEMENTATION
#include <portablegl.h>

#include <cstring>

namespace miniandroid {
namespace gles {

static glContext s_ctx;

bool PGLBackend::init(int width, int height, std::string& error) {
    if (inited_ && width == width_ && height == height_) return true;
    // Re-init at new size: PGL owns its buffers; a fresh context is the
    // supported path (init_glContext allocates the back buffer).
    if (inited_) free_glContext(&s_ctx);
    std::memset(&s_ctx, 0, sizeof(s_ctx));
    if (!init_glContext(&s_ctx, &backbuf_, width, height)) {
        error = "init_glContext failed (out of memory?)";
        inited_ = false;
        return false;
    }
    width_ = width;
    height_ = height;
    ctx_ = &s_ctx;
    inited_ = true;
    return true;
}

void PGLBackend::frame_end() {
    if (!inited_) return;
    // Headless PGL renders straight into backbuf_; nothing to swap.
}

const char* pgl_version_string() {
    return "PortableGL rswinkle@7cf39dc (MIT)";
}

}  // namespace gles
}  // namespace miniandroid
