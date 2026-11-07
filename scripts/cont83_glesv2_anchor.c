/* S188-W2 libGLESv2 anchor — UPGRADED in S188-W9 to the full GLES2 face
 * (F-NEW-589, the real-GL lane).
 *
 * W2 history: the 15 GLES2 symbols libflutter.so needed that the exe's
 * PortableGL surface does NOT export.
 *
 * W9 live evidence (evidence/s188_w9/w9_gl1.console.log): with the OSMesa
 * EGL lane active, Impeller ACCEPTED the OpenGLES backend
 * ("Using the Impeller rendering backend (OpenGLES)") — then libflutter's
 * DIRECT glGetString binding (its UND gl* resolve through the DT_NEEDED
 * dependency scope = this anchor, then the global scope = the exe's
 * PortableGL) crashed: PortableGL's glGetString derefs its global context
 * pointer without a null guard, and no PortableGL context exists on the
 * engine lane (fault_addr=0xa04, frame miniandroid glGetString+0x46).
 * libflutter's UND census: 106 gl* symbols (F-NEW-584 census law applied to
 * the ELF demand list).
 *
 * NEW resolution-order law (supersedes the W2 15-symbol law for the ENGINE
 * lane): the SQLite law says Load Real — Mesa llvmpipe (GL 4.5 +
 * GL_ARB_ES3_compatibility, a REAL software GL) is a strictly stronger
 * provider than PortableGL for a native engine lane. This anchor now serves
 * ALL 106 demanded gl* as typed delegators:
 *   1. OSMesa present  -> the REAL llvmpipe entry point (the engine renders
 *      through actual software GL bound to the EGL anchor's OSMesa contexts)
 *   2. OSMesa absent   -> the W2 hand-written first-party faces where they
 *      exist (15), else an honest no-op/zero — the engine then fails its own
 *      validation CLEANLY (logged) instead of crashing inside PortableGL's
 *      unguarded context deref.
 * The exe's PortableGL export surface is UNTOUCHED: the DEX/JS GLES bridge
 * (gles20_bridge.cpp) keeps its own PortableGL state machine — no golden
 * risk for the JS lane.
 */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>

typedef unsigned int GLenum;
typedef unsigned char GLboolean;
typedef unsigned int GLuint;
typedef int GLint;
typedef int GLsizei;
typedef float GLfloat;
typedef float GLclampf;
typedef unsigned int GLbitfield;
typedef unsigned char GLubyte;
typedef char GLchar;
typedef intptr_t GLintptr;
typedef intptr_t GLsizeiptr;

#define S188_GLES_LOG 0
#if S188_GLES_LOG
#define GLOG(...) fprintf(stderr, __VA_ARGS__)
#else
#define GLOG(...) do {} while (0)
#endif

/* ── F-NEW-589: the OSMesa lane (same candidate law as the EGL anchor) ── */
static void* g_osa_h = NULL;
static int g_osa_state = 0;   /* 0 untried, 1 open, -1 absent */

static void* osa_fn(const char* name, void** cache) {
    if (*cache) return *cache;
    if (g_osa_state < 0) return NULL;
    if (!g_osa_h) {
        const char* cands[5];
        int n = 0;
        cands[n++] = getenv("MINIANDROID_OSMESA_PATH");
        cands[n++] = "/home/z/my-project/third_party/osmesa/usr/lib/x86_64-linux-gnu/libOSMesa.so.8";
        cands[n++] = "/usr/lib/x86_64-linux-gnu/libOSMesa.so.8";
        cands[n++] = "libOSMesa.so.8";
        cands[n++] = NULL;
        for (int i = 0; i < n; ++i) {
            if (!cands[i]) continue;
            g_osa_h = dlopen(cands[i], RTLD_NOW | RTLD_LOCAL);
            if (g_osa_h) break;
        }
        g_osa_state = g_osa_h ? 1 : -1;
    }
    if (!g_osa_h) return NULL;
    *cache = dlsym(g_osa_h, name);
    return *cache;
}

/* ── W2 fallback faces (kept verbatim for the OSMesa-absent lane) ─────── */
static char g_attr_names[16][64];
static unsigned char g_attr_set[16];
static unsigned char g_tex_bound[4096];

__attribute__((weak)) extern void __ma_pgl_frame_end(void);
__attribute__((weak)) extern int __ma_gles_tex_bound(GLuint name);

__attribute__((visibility("default")))
void __s188_anchor_note_texture(GLuint name) {
    if (name && name < 4096) g_tex_bound[name] = 1;
}

/* ── the 15 W2 faces: OSMesa first, W2 behavior as fallback ───────────── */
__attribute__((visibility("default")))
void glBindAttribLocation(GLuint program, GLuint index, const char* name) {
    typedef void (*PFN)(GLuint, GLuint, const char*);
    static void* p;
    void* f = osa_fn("glBindAttribLocation", &p);
    if (f) { ((PFN)f)(program, index, name); return; }
    if (index < 16 && name) {
        strncpy(g_attr_names[index], name, sizeof(g_attr_names[index]) - 1);
        g_attr_names[index][sizeof(g_attr_names[index]) - 1] = 0;
        g_attr_set[index] = 1;
    }
    GLOG("[GLES2A] glBindAttribLocation prog=%u idx=%u name=%s\n",
         program, index, name ? name : "(null)");
}

__attribute__((visibility("default")))
void glCompressedTexSubImage2D(GLenum target, GLint level, GLint xoff,
                               GLint yoff, GLsizei w, GLsizei h,
                               GLenum format, GLsizei imgsz, const void* data) {
    typedef void (*PFN)(GLenum, GLint, GLint, GLint, GLsizei, GLsizei, GLenum,
                        GLsizei, const void*);
    static void* p;
    void* f = osa_fn("glCompressedTexSubImage2D", &p);
    if (f) { ((PFN)f)(target, level, xoff, yoff, w, h, format, imgsz, data); return; }
    GLOG("[GLES2A] glCompressedTexSubImage2D fmt=%x size=%d\n", format, imgsz);
}

__attribute__((visibility("default")))
void glCopyTexSubImage2D(GLenum target, GLint level, GLint xoff, GLint yoff,
                         GLint x, GLint y, GLsizei w, GLsizei h) {
    typedef void (*PFN)(GLenum, GLint, GLint, GLint, GLint, GLint, GLsizei,
                        GLsizei);
    static void* p;
    void* f = osa_fn("glCopyTexSubImage2D", &p);
    if (f) { ((PFN)f)(target, level, xoff, yoff, x, y, w, h); return; }
    GLOG("[GLES2A] glCopyTexSubImage2D\n");
}

__attribute__((visibility("default")))
void glFinish(void) {
    typedef void (*PFN)(void);
    static void* p;
    void* f = osa_fn("glFinish", &p);
    if (f) { ((PFN)f)(); return; }
    if (__ma_pgl_frame_end) __ma_pgl_frame_end();
    GLOG("[GLES2A] glFinish\n");
}

__attribute__((visibility("default")))
void glFlush(void) {
    typedef void (*PFN)(void);
    static void* p;
    void* f = osa_fn("glFlush", &p);
    if (f) { ((PFN)f)(); return; }
    if (__ma_pgl_frame_end) __ma_pgl_frame_end();
    GLOG("[GLES2A] glFlush\n");
}

__attribute__((visibility("default")))
void glGetBufferParameteriv(GLenum target, GLenum pname, GLint* params) {
    typedef void (*PFN)(GLenum, GLenum, GLint*);
    static void* p;
    void* f = osa_fn("glGetBufferParameteriv", &p);
    if (f) { ((PFN)f)(target, pname, params); return; }
    (void)target;
    if (params) *params = 0;
    GLOG("[GLES2A] glGetBufferParameteriv pname=%x -> 0\n", pname);
}

__attribute__((visibility("default")))
void glGetFramebufferAttachmentParameteriv(GLenum target, GLenum attachment,
                                           GLenum pname, GLint* params) {
    typedef void (*PFN)(GLenum, GLenum, GLenum, GLint*);
    static void* p;
    void* f = osa_fn("glGetFramebufferAttachmentParameteriv", &p);
    if (f) { ((PFN)f)(target, attachment, pname, params); return; }
    (void)target; (void)attachment;
    if (params) *params = 0;
    GLOG("[GLES2A] glGetFramebufferAttachmentParameteriv pname=%x -> 0\n", pname);
}

__attribute__((visibility("default")))
void glGetRenderbufferParameteriv(GLenum target, GLenum pname, GLint* params) {
    typedef void (*PFN)(GLenum, GLenum, GLint*);
    static void* p;
    void* f = osa_fn("glGetRenderbufferParameteriv", &p);
    if (f) { ((PFN)f)(target, pname, params); return; }
    (void)target;
    if (params) *params = 0;
    GLOG("[GLES2A] glGetRenderbufferParameteriv pname=%x -> 0\n", pname);
}

__attribute__((visibility("default")))
void glGetShaderPrecisionFormat(GLenum shadertype, GLenum precisiontype,
                                GLint* range, GLint* precision) {
    typedef void (*PFN)(GLenum, GLenum, GLint*, GLint*);
    static void* p;
    void* f = osa_fn("glGetShaderPrecisionFormat", &p);
    if (f) { ((PFN)f)(shadertype, precisiontype, range, precision); return; }
    (void)shadertype;
    switch (precisiontype) {
        case 0x8DF4: case 0x8DF5: case 0x8DF6:
            if (range) { range[0] = 127; range[1] = 127; }
            if (precision) *precision = 23;
            break;
        case 0x8DF7: case 0x8DF8: case 0x8DF9:
            if (range) { range[0] = 31; range[1] = 30; }
            if (precision) *precision = 0;
            break;
        default:
            if (range) { range[0] = 0; range[1] = 0; }
            if (precision) *precision = 0;
            break;
    }
}

__attribute__((visibility("default")))
GLboolean glIsTexture(GLuint texture) {
    typedef GLboolean (*PFN)(GLuint);
    static void* p;
    void* f = osa_fn("glIsTexture", &p);
    if (f) return ((PFN)f)(texture);
    GLboolean r = (texture != 0 && texture < 4096 &&
                   (g_tex_bound[texture] ||
                    (__ma_gles_tex_bound && __ma_gles_tex_bound(texture))))
                      ? 1 : 0;
    GLOG("[GLES2A] glIsTexture %u -> %d\n", texture, (int)r);
    return r;
}

__attribute__((visibility("default")))
void glVertexAttrib1f(GLuint index, GLfloat x) {
    typedef void (*PFN)(GLuint, GLfloat);
    static void* p;
    void* f = osa_fn("glVertexAttrib1f", &p);
    if (f) { ((PFN)f)(index, x); return; }
    GLOG("[GLES2A] glVertexAttrib1f idx=%u x=%f\n", index, x);
}

__attribute__((visibility("default")))
void glVertexAttrib2fv(GLuint index, const GLfloat* v) {
    typedef void (*PFN)(GLuint, const GLfloat*);
    static void* p;
    void* f = osa_fn("glVertexAttrib2fv", &p);
    if (f) { ((PFN)f)(index, v); return; }
    GLOG("[GLES2A] glVertexAttrib2fv idx=%u\n", index);
}

__attribute__((visibility("default")))
void glVertexAttrib3fv(GLuint index, const GLfloat* v) {
    typedef void (*PFN)(GLuint, const GLfloat*);
    static void* p;
    void* f = osa_fn("glVertexAttrib3fv", &p);
    if (f) { ((PFN)f)(index, v); return; }
    GLOG("[GLES2A] glVertexAttrib3fv idx=%u\n", index);
}

__attribute__((visibility("default")))
void glVertexAttrib4fv(GLuint index, const GLfloat* v) {
    typedef void (*PFN)(GLuint, const GLfloat*);
    static void* p;
    void* f = osa_fn("glVertexAttrib4fv", &p);
    if (f) { ((PFN)f)(index, v); return; }
    GLOG("[GLES2A] glVertexAttrib4fv idx=%u\n", index);
}

__attribute__((visibility("default")))
void glEGLImageTargetTexture2DOES(GLenum target, void* image) {
    typedef void (*PFN)(GLenum, void*);
    static void* p;
    void* f = osa_fn("glEGLImageTargetTexture2DOES", &p);
    if (f) { ((PFN)f)(target, image); return; }
    GLOG("[GLES2A] glEGLImageTargetTexture2DOES image=%p\n", image);
}

/* ── the remaining 91 demanded gl*: typed OSMesa delegators ──────────────
 * Macro one-liners: MA_GLn(ret, name, defret, t1..tn) — no-OSMesa fallback
 * answers the honest zero/default (the engine then fails its own validation
 * cleanly, logged, never a fabricated success). */
#define MA_G0(ret, name, defret)                                              \
    typedef ret (*PFN_##name)(void); static void* p_##name;                   \
    __attribute__((visibility("default"))) ret name(void) {                   \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)();                                      \
        return (ret)(defret);                                                 \
    }
#define MA_G1(ret, name, t1, a1, defret)                                      \
    typedef ret (*PFN_##name)(t1); static void* p_##name;                     \
    __attribute__((visibility("default"))) ret name(t1 a1) {                  \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1);                                    \
        return (ret)(defret);                                                 \
    }
#define MA_G2(ret, name, t1, a1, t2, a2, defret)                              \
    typedef ret (*PFN_##name)(t1, t2); static void* p_##name;                 \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2) {           \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2);                                \
        return (ret)(defret);                                                 \
    }
#define MA_G3(ret, name, t1, a1, t2, a2, t3, a3, defret)                      \
    typedef ret (*PFN_##name)(t1, t2, t3); static void* p_##name;             \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2, t3 a3) {    \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2, a3);                            \
        return (ret)(defret);                                                 \
    }
#define MA_G4(ret, name, t1, a1, t2, a2, t3, a3, t4, a4, defret)              \
    typedef ret (*PFN_##name)(t1, t2, t3, t4); static void* p_##name;         \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2, t3 a3,      \
                                                    t4 a4) {                  \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2, a3, a4);                        \
        return (ret)(defret);                                                 \
    }
#define MA_G5(ret, name, t1, a1, t2, a2, t3, a3, t4, a4, t5, a5, defret)      \
    typedef ret (*PFN_##name)(t1, t2, t3, t4, t5); static void* p_##name;     \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2, t3 a3,      \
                                                    t4 a4, t5 a5) {           \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2, a3, a4, a5);                    \
        return (ret)(defret);                                                 \
    }
#define MA_G7(ret, name, t1, a1, t2, a2, t3, a3, t4, a4, t5, a5, t6, a6,      \
              t7, a7, defret)                                                 \
    typedef ret (*PFN_##name)(t1, t2, t3, t4, t5, t6, t7); static void* p_##name; \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2, t3 a3,      \
        t4 a4, t5 a5, t6 a6, t7 a7) {                                         \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2, a3, a4, a5, a6, a7);            \
        return (ret)(defret);                                                 \
    }
#define MA_G8(ret, name, t1, a1, t2, a2, t3, a3, t4, a4, t5, a5, t6, a6,      \
              t7, a7, t8, a8, defret)                                         \
    typedef ret (*PFN_##name)(t1, t2, t3, t4, t5, t6, t7, t8);                \
    static void* p_##name;                                                    \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2, t3 a3,      \
        t4 a4, t5 a5, t6 a6, t7 a7, t8 a8) {                                  \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2, a3, a4, a5, a6, a7, a8);        \
        return (ret)(defret);                                                 \
    }
#define MA_G9(ret, name, t1, a1, t2, a2, t3, a3, t4, a4, t5, a5, t6, a6,      \
              t7, a7, t8, a8, t9, a9, defret)                                 \
    typedef ret (*PFN_##name)(t1, t2, t3, t4, t5, t6, t7, t8, t9);            \
    static void* p_##name;                                                    \
    __attribute__((visibility("default"))) ret name(t1 a1, t2 a2, t3 a3,      \
        t4 a4, t5 a5, t6 a6, t7 a7, t8 a8, t9 a9) {                           \
        void* f = osa_fn(#name, &p_##name);                                   \
        if (f) return ((PFN_##name)f)(a1, a2, a3, a4, a5, a6, a7, a8, a9);    \
        return (ret)(defret);                                                 \
    }

MA_G1(void, glActiveTexture, GLenum, texture, 0)
MA_G2(void, glAttachShader, GLuint, program, GLuint, shader, 0)
MA_G2(void, glBindBuffer, GLenum, target, GLuint, buffer, 0)
MA_G2(void, glBindFramebuffer, GLenum, target, GLuint, framebuffer, 0)
MA_G2(void, glBindRenderbuffer, GLenum, target, GLuint, renderbuffer, 0)
MA_G2(void, glBindTexture, GLenum, target, GLuint, texture, 0)
MA_G4(void, glBlendColor, GLclampf, r, GLclampf, g, GLclampf, b, GLclampf, a, 0)
MA_G1(void, glBlendEquation, GLenum, mode, 0)
MA_G2(void, glBlendFunc, GLenum, sfactor, GLenum, dfactor, 0)
MA_G4(void, glBufferData, GLenum, target, GLsizeiptr, size, const void*, data,
      GLenum, usage, 0)
MA_G4(void, glBufferSubData, GLenum, target, GLintptr, offset, GLsizeiptr,
      size, const void*, data, 0)
MA_G1(GLenum, glCheckFramebufferStatus, GLenum, target, 0)
MA_G1(void, glClear, GLbitfield, mask, 0)
MA_G4(void, glClearColor, GLclampf, r, GLclampf, g, GLclampf, b, GLclampf, a, 0)
MA_G1(void, glClearStencil, GLint, s, 0)
MA_G4(void, glColorMask, GLboolean, r, GLboolean, g, GLboolean, b, GLboolean,
      a, 0)
MA_G1(void, glCompileShader, GLuint, shader, 0)
MA_G0(GLuint, glCreateProgram, 0)
MA_G1(GLuint, glCreateShader, GLenum, type, 0)
MA_G8(void, glCompressedTexImage2D, GLenum, target, GLint, level, GLenum,
      internalformat, GLsizei, width, GLsizei, height, GLint, border, GLsizei,
      imageSize, const void*, data, 0)
MA_G1(void, glCullFace, GLenum, mode, 0)
MA_G2(void, glDeleteBuffers, GLsizei, n, const GLuint*, buffers, 0)
MA_G2(void, glDeleteFramebuffers, GLsizei, n, const GLuint*, framebuffers, 0)
MA_G1(void, glDeleteProgram, GLuint, program, 0)
MA_G2(void, glDeleteRenderbuffers, GLsizei, n, const GLuint*, renderbuffers, 0)
MA_G1(void, glDeleteShader, GLuint, shader, 0)
MA_G2(void, glDeleteTextures, GLsizei, n, const GLuint*, textures, 0)
MA_G1(void, glDepthMask, GLboolean, flag, 0)
MA_G1(void, glDisable, GLenum, cap, 0)
MA_G1(void, glDisableVertexAttribArray, GLuint, index, 0)
MA_G3(void, glDrawArrays, GLenum, mode, GLint, first, GLsizei, count, 0)
MA_G4(void, glDrawElements, GLenum, mode, GLsizei, count, GLenum, type,
      const void*, indices, 0)
MA_G1(void, glEnable, GLenum, cap, 0)
MA_G1(void, glEnableVertexAttribArray, GLuint, index, 0)
MA_G4(void, glFramebufferRenderbuffer, GLenum, target, GLenum, attachment,
      GLenum, renderbuffertarget, GLuint, renderbuffer, 0)
MA_G5(void, glFramebufferTexture2D, GLenum, target, GLenum, attachment, GLenum,
      textarget, GLuint, texture, GLint, level, 0)
MA_G1(void, glFrontFace, GLenum, mode, 0)
MA_G2(void, glGenBuffers, GLsizei, n, GLuint*, buffers, 0)
MA_G2(void, glGenFramebuffers, GLsizei, n, GLuint*, framebuffers, 0)
MA_G2(void, glGenRenderbuffers, GLsizei, n, GLuint*, renderbuffers, 0)
MA_G2(void, glGenTextures, GLsizei, n, GLuint*, textures, 0)
MA_G1(void, glGenerateMipmap, GLenum, target, 0)
MA_G0(GLenum, glGetError, 0)
MA_G1(const GLubyte*, glGetString, GLenum, name, 0)
MA_G2(void, glGetIntegerv, GLenum, pname, GLint*, data, 0)
MA_G4(void, glGetProgramInfoLog, GLuint, program, GLsizei, bufsize, GLsizei*,
      length, GLchar*, infolog, 0)
MA_G3(void, glGetProgramiv, GLuint, program, GLenum, pname, GLint*, params, 0)
MA_G4(void, glGetShaderInfoLog, GLuint, shader, GLsizei, bufsize, GLsizei*,
      length, GLchar*, infolog, 0)
MA_G3(void, glGetShaderiv, GLuint, shader, GLenum, pname, GLint*, params, 0)
MA_G2(GLint, glGetUniformLocation, GLuint, program, const GLchar*, name, -1)
MA_G1(void, glLineWidth, GLfloat, width, 0)
MA_G1(void, glLinkProgram, GLuint, program, 0)
MA_G2(void, glPixelStorei, GLenum, pname, GLint, param, 0)
MA_G7(void, glReadPixels, GLint, x, GLint, y, GLsizei, width, GLsizei, height,
      GLenum, format, GLenum, type, void*, data, 0)
MA_G4(void, glRenderbufferStorage, GLenum, target, GLenum, internalformat,
      GLsizei, width, GLsizei, height, 0)
MA_G4(void, glScissor, GLint, x, GLint, y, GLsizei, width, GLsizei, height, 0)
MA_G4(void, glShaderSource, GLuint, shader, GLsizei, count,
      const GLchar* const*, string, const GLint*, length, 0)
MA_G3(void, glStencilFunc, GLenum, func, GLint, ref, GLuint, mask, 0)
MA_G4(void, glStencilFuncSeparate, GLenum, face, GLenum, func, GLint, ref,
      GLuint, mask, 0)
MA_G1(void, glStencilMask, GLuint, mask, 0)
MA_G2(void, glStencilMaskSeparate, GLenum, face, GLuint, mask, 0)
MA_G3(void, glStencilOp, GLenum, fail, GLenum, zfail, GLenum, zpass, 0)
MA_G4(void, glStencilOpSeparate, GLenum, face, GLenum, sfail, GLenum, dpfail,
      GLenum, dppass, 0)
MA_G9(void, glTexImage2D, GLenum, target, GLint, level, GLint, internalformat,
      GLsizei, width, GLsizei, height, GLint, border, GLenum, format, GLenum,
      type, const void*, pixels, 0)
MA_G3(void, glTexParameterf, GLenum, target, GLenum, pname, GLfloat, param, 0)
MA_G3(void, glTexParameterfv, GLenum, target, GLenum, pname, const GLfloat*,
      params, 0)
MA_G3(void, glTexParameteri, GLenum, target, GLenum, pname, GLint, param, 0)
MA_G3(void, glTexParameteriv, GLenum, target, GLenum, pname, const GLint*,
      params, 0)
MA_G9(void, glTexSubImage2D, GLenum, target, GLint, level, GLint, xoffset,
      GLint, yoffset, GLsizei, width, GLsizei, height, GLenum, format, GLenum,
      type, const void*, pixels, 0)
MA_G2(void, glUniform1f, GLint, location, GLfloat, v0, 0)
MA_G3(void, glUniform1fv, GLint, location, GLsizei, count, const GLfloat*,
      value, 0)
MA_G2(void, glUniform1i, GLint, location, GLint, v0, 0)
MA_G3(void, glUniform1iv, GLint, location, GLsizei, count, const GLint*,
      value, 0)
MA_G3(void, glUniform2f, GLint, location, GLfloat, v0, GLfloat, v1, 0)
MA_G3(void, glUniform2fv, GLint, location, GLsizei, count, const GLfloat*,
      value, 0)
MA_G3(void, glUniform2i, GLint, location, GLint, v0, GLint, v1, 0)
MA_G3(void, glUniform2iv, GLint, location, GLsizei, count, const GLint*,
      value, 0)
MA_G4(void, glUniform3f, GLint, location, GLfloat, v0, GLfloat, v1, GLfloat,
      v2, 0)
MA_G3(void, glUniform3fv, GLint, location, GLsizei, count, const GLfloat*,
      value, 0)
MA_G4(void, glUniform3i, GLint, location, GLint, v0, GLint, v1, GLint, v2, 0)
MA_G3(void, glUniform3iv, GLint, location, GLsizei, count, const GLint*,
      value, 0)
MA_G5(void, glUniform4f, GLint, location, GLfloat, v0, GLfloat, v1, GLfloat,
      v2, GLfloat, v3, 0)
MA_G3(void, glUniform4fv, GLint, location, GLsizei, count, const GLfloat*,
      value, 0)
MA_G5(void, glUniform4i, GLint, location, GLint, v0, GLint, v1, GLint, v2,
      GLint, v3, 0)
MA_G3(void, glUniform4iv, GLint, location, GLsizei, count, const GLint*,
      value, 0)
MA_G4(void, glUniformMatrix2fv, GLint, location, GLsizei, count, GLboolean,
      transpose, const GLfloat*, value, 0)
MA_G4(void, glUniformMatrix3fv, GLint, location, GLsizei, count, GLboolean,
      transpose, const GLfloat*, value, 0)
MA_G4(void, glUniformMatrix4fv, GLint, location, GLsizei, count, GLboolean,
      transpose, const GLfloat*, value, 0)
MA_G1(void, glUseProgram, GLuint, program, 0)
/* glVertexAttribPointer is 6 args — defined manually below. */
typedef void (*PFN_glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean,
                                          GLsizei, const void*);
static void* p_glVertexAttribPointer;
__attribute__((visibility("default")))
void glVertexAttribPointer(GLuint index, GLint size, GLenum type,
                           GLboolean normalized, GLsizei stride,
                           const void* pointer) {
    void* f = osa_fn("glVertexAttribPointer", &p_glVertexAttribPointer);
    if (f) ((PFN_glVertexAttribPointer)f)(index, size, type, normalized,
                                          stride, pointer);
}
MA_G4(void, glViewport, GLint, x, GLint, y, GLsizei, width, GLsizei, height, 0)
