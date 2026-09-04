// CAMPAIGN 010 R9 — PortableGL-backed GLES surface for MiniAndroid.
//
// PortableGL (rswinkle/PortableGL @ 7cf39dc, MIT) is adopted INSTEAD OF
// writing a custom software rasterizer. This module owns the PGL context
// and exposes a framebuffer the runtime's render pipeline can consume.
//
// NOTE ON SHADERS: PortableGL executes C-function vertex/fragment shaders
// (its design), not GLSL source strings. The GLES20 bridge stores GLSL
// source verbatim (for inspection/trace) and real drawing goes through
// pglCreateProgram C shaders. A GLSL->C translator (or Mesa llvmpipe) is
// the future route for arbitrary APK shaders — recorded honestly in
// GLES_BACKEND_COMPARISON_010.md.
#ifndef MINIANDROID_PGL_BACKEND_H
#define MINIANDROID_PGL_BACKEND_H

#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid {
namespace gles {

class PGLBackend {
public:
    // Initialize (or re-initialize) the PGL context at WxH.
    bool init(int width, int height, std::string& error);

    // Finish the frame: PGL swaps its back buffer internally on
    // glFlush/glFinish equivalents; call this after drawing.
    void frame_end();

    int width() const { return width_; }
    int height() const { return height_; }

    // Direct access to the PGL back buffer (pix_t = u32 RGBA8888).
    const uint32_t* pixels() const { return backbuf_; }

    bool ok() const { return inited_; }

private:
    int width_ = 0, height_ = 0;
    uint32_t* backbuf_ = nullptr;
    bool inited_ = false;
    // Opaque glContext storage (defined in portablegl.h; kept out of this
    // header so the runtime does not include PGL everywhere).
    void* ctx_ = nullptr;
};

}  // namespace gles
}  // namespace miniandroid

#endif  // MINIANDROID_PGL_BACKEND_H
