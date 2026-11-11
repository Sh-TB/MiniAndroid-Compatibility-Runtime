// S188-W14 F-NEW-586 + F-NEW-587 — native GL surface completion TU.
//
// F-NEW-586 PINNED CONTRACT (evidence/s188_w13/W13_LOADING_PROGRESS.json):
// se.tube42.p9.android (LIBGDX alley) libgdx.so dlopen failed with
//   "undefined symbol: glCopyTexImage2D"
// lib/x86_64/libgdx.so needs exactly glCopyTexImage2D + glCopyTexSubImage2D
// beyond the PortableGL surface (all 138 other gl* symbols resolve).
// app.halma's libgdx.so does not import them, which is why halma already
// dlopen'd OK.
//
// F-NEW-587 PINNED CONTRACT (evidence/s188_w14/W14_GDX_VERIFY.json):
// after 586, p9's next dlopen blocker is the declared-but-unimplemented
// PGL surface: glGetActiveAttrib, ... glVertexAttrib4fv (35 symbols,
// exact list in the W14 evidence) + __android_log_print (bionic_compat).
// These are implemented here with HONEST minimal semantics — the first
// blocker is dlopen itself; runtime-call semantics upgrade only where the
// app actually calls (the F-NEW-505 incremental-contract method).
//
// Implementation notes: glCopyTexImage2D copies from the read buffer via
// glReadPixels then uploads. The introspection/state family is no-op or
// constant per the GLES2 spec, because PortableGL has no GLSL pipeline
// (glLinkProgram is an empty stub in portablegl.h) — a real driver-level
// answer is impossible for a software rasterizer without a compiler.
// The exe is linked -rdynamic, so these definitions satisfy the dlopen
// symbol resolution of bionic-compiled libgdx-family libraries.
#include "pgl_backend.h"

#include <portablegl.h>

#include <vector>

// GLES2 precision-precision enums absent from the desktop-oriented
// portablegl.h — exact GL spec values.
#ifndef GL_FLOAT_VEC4
#define GL_FLOAT_VEC4 0x8B52
#endif
#ifndef GL_LOW_FLOAT
#define GL_LOW_FLOAT    0x8DF0
#define GL_MEDIUM_FLOAT 0x8DF1
#define GL_HIGH_FLOAT   0x8DF2
#define GL_LOW_INT      0x8DF3
#define GL_MEDIUM_INT   0x8DF4
#define GL_HIGH_INT     0x8DF5
#endif

extern "C" {

// GP583-GLES-005: bounded copy-allocation law. The old code only rejected
// negative dimensions and then allocated (size_t)width*height*4 unchecked —
// an accidental or adversarial very large positive size requested enormous
// host memory straight from APK-controlled native code. Law (both faces):
//   (1) checked multiplication (no silent 32-bit wrap, no size_t overflow);
//   (2) a hard byte budget (64 MiB) — every GLES max texture dimension is
//       far below it, so legit app faces never trip;
//   (3) the copy extent is clipped to the READ framebuffer — a copy larger
//       than the pixels that can actually be read must not allocate its
//       full request (PGL fb geometry, pgl_read_extent());
//   (4) allocation failure is caught at the C ABI boundary — a bad_alloc
//       must never escape into bionic-compiled caller frames.
// PortableGL exposes no public per-call error setter (documented face above);
// an over-budget copy returns without touching the texture, keeping the
// previous texture contents intact — the honest degradation this module
// already documents for read failures.
static constexpr size_t kGlCopyMaxBytes = 64ull * 1024 * 1024;  // 64 MiB

// Read-framebuffer extent (false = no current context — nothing to read).
// pgl_framebuffer_size comes from pgl_backend.h (C++ linkage — the local
// extern "C" forward declared a mangled C++ symbol as a C symbol and the
// link died on the namespace-mangled definition).
static bool pgl_read_extent(int* fb_w, int* fb_h) {
    return miniandroid::gles::pgl_framebuffer_size(fb_w, fb_h) &&
           fb_w != nullptr && fb_h != nullptr && *fb_w > 0 && *fb_h > 0;
}

// GLES2 §3.7.2: copy a w×h block at (x,y) of the read color buffer into
// a fresh texture image (target level). border must be 0 (GLES2).
void glCopyTexImage2D(GLenum target, GLint level, GLint internalformat,
                      GLint x, GLint y, GLsizei width, GLsizei height,
                      GLint border) {
    if (width < 0 || height < 0 || border != 0) {
        return; // GLES2: INVALID_VALUE (no public error setter in PortableGL)
    }
    int fb_w = 0, fb_h = 0;
    if (pgl_read_extent(&fb_w, &fb_h)) {
        // Clip the request to the readable extent (spec: reading outside
        // the framebuffer is undefined — allocating for it is never useful).
        if (x < 0) { width += x; x = 0; }
        if (y < 0) { height += y; y = 0; }
        if (x >= fb_w || y >= fb_h) return;
        if (width > fb_w - x) width = fb_w - x;
        if (height > fb_h - y) height = fb_h - y;
    }
    const size_t bytes = (size_t)width * (size_t)height * 4;
    if (width <= 0 || height <= 0 || bytes > kGlCopyMaxBytes) return;
    std::vector<unsigned char> buf;
    try {
        buf.resize(bytes);
    } catch (...) {
        return;  // C ABI boundary: host exceptions never escape to APK code
    }
    glReadPixels(x, y, width, height, GL_RGBA, GL_UNSIGNED_BYTE, buf.data());
    glTexImage2D(target, level, internalformat, width, height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, buf.data());
}

// Copy into an existing texture image at (xoffset,yoffset).
void glCopyTexSubImage2D(GLenum target, GLint level,
                         GLint xoffset, GLint yoffset,
                         GLint x, GLint y, GLsizei width, GLsizei height) {
    if (width < 0 || height < 0) {
        return; // GLES2: INVALID_VALUE (no public error setter in PortableGL)
    }
    int fb_w = 0, fb_h = 0;
    if (pgl_read_extent(&fb_w, &fb_h)) {
        if (x < 0) { width += x; x = 0; }
        if (y < 0) { height += y; y = 0; }
        if (x >= fb_w || y >= fb_h) return;
        if (width > fb_w - x) width = fb_w - x;
        if (height > fb_h - y) height = fb_h - y;
    }
    const size_t bytes = (size_t)width * (size_t)height * 4;
    if (width <= 0 || height <= 0 || bytes > kGlCopyMaxBytes) return;
    std::vector<unsigned char> buf;
    try {
        buf.resize(bytes);
    } catch (...) {
        return;  // C ABI boundary: host exceptions never escape to APK code
    }
    glReadPixels(x, y, width, height, GL_RGBA, GL_UNSIGNED_BYTE, buf.data());
    glTexSubImage2D(target, level, xoffset, yoffset, width, height,
                    GL_RGBA, GL_UNSIGNED_BYTE, buf.data());
}

// ─── F-NEW-587: declared-but-unimplemented PGL surface ──────────────────

// Program/shader introspection. PortableGL has no GLSL pipeline (no
// compile/link), so there are no active uniforms/attribs to enumerate.
// glGetProgramiv(GL_ACTIVE_*) returns 0 (PGL stub), so well-behaved apps
// enumerate nothing; if a caller enumerates anyway it gets an empty name.
void glGetActiveAttrib(GLuint program, GLuint index, GLsizei bufsize,
                       GLsizei* length, GLint* size, GLenum* type,
                       GLchar* name) {
    if (length) *length = 0;
    if (size) *size = 1;
    if (type) *type = GL_FLOAT_VEC4;
    if (bufsize > 0 && name) name[0] = '\0';
    (void)program; (void)index;
}

void glGetActiveUniform(GLuint program, GLuint index, GLsizei bufsize,
                        GLsizei* length, GLint* size, GLenum* type,
                        GLchar* name) {
    glGetActiveAttrib(program, index, bufsize, length, size, type, name);
}

// GLES2 precision queries — REAL IEEE float32/int ranges of the software
// backend (these constants are exact for float32 math, not guesses).
void glGetShaderPrecisionFormat(GLenum shadertype, GLenum precisiontype,
                                GLint* range, GLint* precision) {
    (void)shadertype;
    switch (precisiontype) {
        case GL_LOW_FLOAT:    range[0] = 15;  range[1] = 15;  *precision = 10; break;
        case GL_MEDIUM_FLOAT: range[0] = 127; range[1] = 127; *precision = 15; break;
        case GL_HIGH_FLOAT:   range[0] = 127; range[1] = 127; *precision = 23; break;
        case GL_LOW_INT:      range[0] = 15;  range[1] = 15;  *precision = 0;  break;
        case GL_MEDIUM_INT:
        case GL_HIGH_INT:     range[0] = 31;  range[1] = 31;  *precision = 0;  break;
        default:              range[0] = 0;   range[1] = 0;   *precision = 0;  break;
    }
}

// Read-back of driver state. PGL owns uniform/attrib storage internally
// with no public enumeration, so zero-fill is the honest answer.
void glGetUniformfv(GLuint program, GLint location, GLfloat* params) {
    (void)program; (void)location;
    if (params) params[0] = 0.0f;
}
void glGetUniformiv(GLuint program, GLint location, GLint* params) {
    (void)program; (void)location;
    if (params) params[0] = 0;
}
void glGetVertexAttribfv(GLuint index, GLenum pname, GLfloat* params) {
    (void)index; (void)pname;
    if (params) params[0] = 0.0f;
}
void glGetVertexAttribiv(GLuint index, GLenum pname, GLint* params) {
    (void)index; (void)pname;
    if (params) params[0] = 0;
}

// Attached-shader enumeration: no shader-registry interposition point
// (glCreateShader is PGL-owned), so zero shaders is the honest answer.
void glGetAttachedShaders(GLuint program, GLsizei maxcount,
                          GLsizei* count, GLuint* shaders) {
    (void)program; (void)shaders;
    if (count) *count = 0;
}

// Object-existence queries: FALSE unless tracked. PGL object registries
// are internal; no interposition point exists for glGenTextures etc.
GLboolean glIsBuffer(GLuint buffer) { (void)buffer; return GL_FALSE; }
GLboolean glIsShader(GLuint shader) { (void)shader; return GL_FALSE; }
GLboolean glIsTexture(GLuint texture) { (void)texture; return GL_FALSE; }

// Container/attachment queries — minimal honest answers.
void glGetBufferParameteriv(GLenum target, GLenum pname, GLint* params) {
    (void)target; (void)pname;
    if (params) params[0] = 0;
}
void glGetFramebufferAttachmentParameteriv(GLenum target, GLenum attachment,
                                           GLenum pname, GLint* params) {
    (void)target; (void)attachment; (void)pname;
    if (params) params[0] = GL_NONE;
}
void glGetRenderbufferParameteriv(GLenum target, GLenum pname, GLint* params) {
    (void)target; (void)pname;
    if (params) params[0] = 0;
}

// Explicit attribute binding: PGL assigns locations itself; unsupported.
void glBindAttribLocation(GLuint program, GLuint index, const GLchar* name) {
    (void)program; (void)index; (void)name;
}

// Immediate vertex-attribute values: the PGL vertex pipeline reads client
// arrays via glVertexAttribPointer; immediate per-vertex values are not
// part of its draw model. no-op (libgdx uses pointer arrays).
void glVertexAttrib1f(GLuint index, GLfloat x) { (void)index; (void)x; }
void glVertexAttrib1fv(GLuint index, const GLfloat* v) { (void)index; (void)v; }
void glVertexAttrib2f(GLuint index, GLfloat x, GLfloat y) {
    (void)index; (void)x; (void)y;
}
void glVertexAttrib2fv(GLuint index, const GLfloat* v) { (void)index; (void)v; }
void glVertexAttrib3f(GLuint index, GLfloat x, GLfloat y, GLfloat z) {
    (void)index; (void)x; (void)y; (void)z;
}
void glVertexAttrib3fv(GLuint index, const GLfloat* v) { (void)index; (void)v; }
void glVertexAttrib4f(GLuint index, GLfloat x, GLfloat y, GLfloat z,
                      GLfloat w) {
    (void)index; (void)x; (void)y; (void)z; (void)w;
}
void glVertexAttrib4fv(GLuint index, const GLfloat* v) { (void)index; (void)v; }

// State/compiler calls with no software-backend effect.
void glHint(GLenum target, GLenum mode) { (void)target; (void)mode; }
void glSampleCoverage(GLclampf value, GLboolean invert) {
    (void)value; (void)invert;
}
void glReleaseShaderCompiler(void) {}
void glShaderBinary(GLsizei n, const GLuint* shaders, GLenum binaryformat,
                    const void* binary, GLsizei length) {
    (void)n; (void)shaders; (void)binaryformat; (void)binary; (void)length;
}
void glValidateProgram(GLuint program) { (void)program; }
void glFinish(void) {}  // software raster is synchronous
void glFlush(void) {}

// Compressed textures are unsupported by the software backend (same policy
// as the DEX-side GLES20 bridge).
void glCompressedTexSubImage2D(GLenum target, GLint level, GLint xoffset,
                               GLint yoffset, GLsizei width, GLsizei height,
                               GLenum format, GLsizei imageSize,
                               const void* data) {
    (void)target; (void)level; (void)xoffset; (void)yoffset; (void)width;
    (void)height; (void)format; (void)imageSize; (void)data;
}

} // extern "C"
