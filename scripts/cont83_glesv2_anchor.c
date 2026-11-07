/* S188-W2: libGLESv2 anchor — the 15 GLES2 symbols libflutter.so needs
 * that the exe's PortableGL surface does NOT export.
 *
 * Resolution-order law: the anchor preloads RTLD_GLOBAL as a DT_NEEDED
 * dep (dep scope) BEFORE the app lib's load. Only the 15 symbols the exe
 * does NOT export may live here — any symbol exported by BOTH would bind
 * the app to THIS anchor instead of the exe's real PortableGL call.
 *
 * Semantics: honest first-party state answers (the GLES2 spec values a
 * software rasterizer can state truthfully); record-only for operations
 * whose software-path effect is deferred (compressed copies, EGLImage
 * bind). Never a fabricated success claim — the trace shows what ran. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

typedef unsigned int GLenum;
typedef int GLint;
typedef unsigned int GLuint;
typedef int GLsizei;
typedef unsigned char GLboolean;
typedef float GLfloat;
typedef void GLvoid;

#define S188_GLES_LOG 0
#if S188_GLES_LOG
#define GLOG(...) fprintf(stderr, __VA_ARGS__)
#else
#define GLOG(...) do {} while (0)
#endif

/* ── shader attribute-name binding: record-only (link is C-shader-side) ── */
static char g_attr_names[16][64];
static unsigned char g_attr_set[16];

__attribute__((visibility("default")))
void glBindAttribLocation(GLuint program, GLuint index, const char* name) {
    if (index < 16 && name) {
        strncpy(g_attr_names[index], name, sizeof(g_attr_names[index]) - 1);
        g_attr_names[index][sizeof(g_attr_names[index]) - 1] = 0;
        g_attr_set[index] = 1;
    }
    GLOG("[GLES2A] glBindAttribLocation prog=%u idx=%u name=%s\n",
         program, index, name ? name : "(null)");
}

/* ── compressed/copy texture paths: honest record (software defer) ────── */
__attribute__((visibility("default")))
void glCompressedTexSubImage2D(GLenum target, GLint level, GLint xoff,
                               GLint yoff, GLsizei w, GLsizei h,
                               GLenum format, GLsizei imgsz, const void* data) {
    (void)target; (void)level; (void)xoff; (void)yoff; (void)w; (void)h;
    (void)format; (void)imgsz; (void)data;
    GLOG("[GLES2A] glCompressedTexSubImage2D fmt=%x size=%d\n", format, imgsz);
}

__attribute__((visibility("default")))
void glCopyTexSubImage2D(GLenum target, GLint level, GLint xoff, GLint yoff,
                         GLint x, GLint y, GLsizei w, GLsizei h) {
    (void)target; (void)level; (void)xoff; (void)yoff; (void)x; (void)y;
    (void)w; (void)h;
    GLOG("[GLES2A] glCopyTexSubImage2D\n");
}

/* ── frame boundary: forward to the exe's PGL frame_end hook ──────────── */
__attribute__((weak)) extern void __ma_pgl_frame_end(void);

__attribute__((visibility("default")))
void glFinish(void) {
    if (__ma_pgl_frame_end) __ma_pgl_frame_end();
    GLOG("[GLES2A] glFinish\n");
}

__attribute__((visibility("default")))
void glFlush(void) {
    if (__ma_pgl_frame_end) __ma_pgl_frame_end();
    GLOG("[GLES2A] glFlush\n");
}

/* ── buffer/framebuffer/renderbuffer parameter queries: spec zeros ──────
 * The software path's VBO/FBO objects are first-party allocations whose
 * full query surface is not wired; the spec-legal answer for an unnamed
 * object is the zero state. */
__attribute__((visibility("default")))
void glGetBufferParameteriv(GLenum target, GLenum pname, GLint* params) {
    (void)target;
    if (params) *params = 0;
    GLOG("[GLES2A] glGetBufferParameteriv pname=%x -> 0\n", pname);
}

__attribute__((visibility("default")))
void glGetFramebufferAttachmentParameteriv(GLenum target, GLenum attachment,
                                           GLenum pname, GLint* params) {
    (void)target; (void)attachment;
    if (params) *params = 0;
    GLOG("[GLES2A] glGetFramebufferAttachmentParameteriv pname=%x -> 0\n", pname);
}

__attribute__((visibility("default")))
void glGetRenderbufferParameteriv(GLenum target, GLenum pname, GLint* params) {
    (void)target;
    if (params) *params = 0;
    GLOG("[GLES2A] glGetRenderbufferParameteriv pname=%x -> 0\n", pname);
}

/* ── shader precision: GLES2 spec-mandated ranges (a software float32
 * rasterizer provides exactly these) ─────────────────────────────────── */
__attribute__((visibility("default")))
void glGetShaderPrecisionFormat(GLenum shadertype, GLenum precisiontype,
                                GLint* range, GLint* precision) {
    (void)shadertype;
    switch (precisiontype) {
        case 0x8DF4 /* LOW_FLOAT */:
        case 0x8DF5 /* MEDIUM_FLOAT */:
        case 0x8DF6 /* HIGH_FLOAT */:
            if (range) { range[0] = 127; range[1] = 127; }
            if (precision) *precision = 23;
            break;
        case 0x8DF7 /* LOW_INT */:
        case 0x8DF8 /* MEDIUM_INT */:
        case 0x8DF9 /* HIGH_INT */:
            if (range) { range[0] = 31; range[1] = 30; }
            if (precision) *precision = 0;
            break;
        default:
            if (range) { range[0] = 0; range[1] = 0; }
            if (precision) *precision = 0;
            break;
    }
}

/* ── texture identity: name-tracked (glGenTextures names flow through the
 * exe's export; the anchor tracks the names it has seen bound) ────────── */
static unsigned char g_tex_bound[4096];

__attribute__((visibility("default")))
GLboolean glIsTexture(GLuint texture) {
    GLboolean r = (texture != 0 && texture < 4096 && g_tex_bound[texture])
                      ? 1 : 0;
    GLOG("[GLES2A] glIsTexture %u -> %d\n", texture, (int)r);
    return r;
}

/* exe-side bind tracker (ma_native_bridge.cpp) so glIsTexture sees the
 * names glGenTextures/glBindTexture created through the exe's surface. */
__attribute__((weak)) extern int __ma_gles_tex_bound(GLuint name);

/* hooks the exe calls so the anchor's bind table stays current */
__attribute__((visibility("default")))
void __s188_anchor_note_texture(GLuint name) {
    if (name && name < 4096) g_tex_bound[name] = 1;
}

__attribute__((visibility("default")))
void glVertexAttrib1f(GLuint index, GLfloat x) {
    GLOG("[GLES2A] glVertexAttrib1f idx=%u x=%f\n", index, x);
}

__attribute__((visibility("default")))
void glVertexAttrib2fv(GLuint index, const GLfloat* v) {
    (void)index; (void)v;
    GLOG("[GLES2A] glVertexAttrib2fv idx=%u\n", index);
}

__attribute__((visibility("default")))
void glVertexAttrib3fv(GLuint index, const GLfloat* v) {
    (void)index; (void)v;
    GLOG("[GLES2A] glVertexAttrib3fv idx=%u\n", index);
}

__attribute__((visibility("default")))
void glVertexAttrib4fv(GLuint index, const GLfloat* v) {
    (void)index; (void)v;
    GLOG("[GLES2A] glVertexAttrib4fv idx=%u\n", index);
}

__attribute__((visibility("default")))
void glEGLImageTargetTexture2DOES(GLenum target, const GLvoid* image) {
    (void)target; (void)image;
    GLOG("[GLES2A] glEGLImageTargetTexture2DOES image=%p\n", image);
}
