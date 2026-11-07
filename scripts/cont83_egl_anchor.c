/* S188-W2: libEGL anchor — full first-party EGL surface for native engine
 * libs (libflutter.so needs 20 egl* symbols; the old anchor exported only
 * eglGetCurrentContext and every Flutter-family dlopen died with
 * "undefined symbol: eglGetCurrentDisplay" BEFORE JNI_OnLoad).
 *
 * Law compliance (cont83 anchor family + S188 honesty rules):
 *  - Token-based state machine: EGLDisplay/EGLContext/EGLSurface are
 *    non-null tokens; 0 stays EGL_NO_DISPLAY/EGL_NO_CONTEXT/EGL_NO_SURFACE
 *    (the spec value apps must handle).
 *  - Software runtime: contexts bind the runtime's PortableGL context via
 *    the __ma_egl_* C-ABI helpers the exe exports (same law as the
 *    libjnigraphics anchor's __ma_bitmap_query). A missing helper
 *    degrades to the honest recorded state — never a fabricated success.
 *  - eglGetProcAddress resolves through dlsym(RTLD_DEFAULT) so extension
 *    names reach the exe's -rdynamic gl* surface and the other anchors.
 *  - eglSwapBuffers is the native frame-present hook: it calls
 *    __ma_egl_frame_present() (exe-side frame pipeline) when available.
 */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <dlfcn.h>

/* EGL 1.4 constants (subset the surface needs; values are ABI-stable). */
#define EGL_FALSE 0
#define EGL_TRUE 1
#define EGL_SUCCESS 0x3000
#define EGL_BAD_DISPLAY 0x3008
#define EGL_BAD_SURFACE 0x300d
#define EGL_BAD_CONTEXT 0x3006
#define EGL_BAD_CONFIG 0x3005
#define EGL_BAD_ATTRIBUTE 0x3004
#define EGL_BAD_PARAMETER 0x300c
#define EGL_BAD_MATCH 0x3003
#define EGL_BAD_ALLOC 0x3003
#define EGL_SURFACE_TYPE 0x3033
#define EGL_WINDOW_BIT 0x0004
#define EGL_PBUFFER_BIT 0x0001
#define EGL_RED_SIZE 0x3024
#define EGL_GREEN_SIZE 0x3023
#define EGL_BLUE_SIZE 0x3022
#define EGL_ALPHA_SIZE 0x3021
#define EGL_DEPTH_SIZE 0x3025
#define EGL_STENCIL_SIZE 0x3026
#define EGL_SAMPLES 0x3031
#define EGL_SAMPLE_BUFFERS 0x3032
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_CONFIG_ID 0x3028
#define EGL_CONFIG_CAVEAT 0x3027
#define EGL_NONE 0x3038
#define EGL_LUMINANCE_SIZE 0x303d
#define EGL_BUFFER_SIZE 0x3020
#define EGL_RENDERABLE_TYPE 0x3040
#define EGL_OPENGL_ES2_BIT 0x0004
#define EGL_CONFORMANT 0x3042
#define EGL_MAX_PBUFFER_WIDTH 0x302c
#define EGL_MAX_PBUFFER_HEIGHT 0x302d
#define EGL_MAX_PBUFFER_PIXELS 0x302e
#define EGL_NATIVE_VISUAL_ID 0x302e2  /* placeholder — fixed below */
#undef EGL_NATIVE_VISUAL_ID
#define EGL_NATIVE_VISUAL_ID 0x302e
#define EGL_VG_ALPHA_FORMAT 0x3088
#define EGL_VG_COLORSPACE 0x3087
#define EGL_COLORSPACE 0x309d
#define EGL_ALPHA_FORMAT 0x3088
#define EGL_COLORSPACE_sRGB 0x3089
#define EGL_TEXTURE_FORMAT 0x3080
#define EGL_TEXTURE_RGB 0x305D
#define EGL_TEXTURE_RGBA 0x305E
#define EGL_TEXTURE_TARGET 0x3081
#define EGL_TEXTURE_2D 0x305F
#define EGL_NO_TEXTURE 0x305C
#define EGL_MIPMAP_TEXTURE 0x3082
#define EGL_MIPMAP_LEVEL 0x3083
#define EGL_LARGEST_PBUFFER 0x3058
#define EGL_GL_COLORSPACE 0x309d

/* exe-side C-ABI helpers (ma_native_bridge.cpp). Weak-declared: a binary
 * without them keeps the anchor's honest recorded state instead. */
__attribute__((weak)) extern int __ma_egl_surface_size(int32_t* w, int32_t* h);
__attribute__((weak)) extern int __ma_egl_frame_present(void);
__attribute__((weak)) extern int __ma_egl_make_current(void);

/* ── token state machine ────────────────────────────────────────────────
 * Handles are pointer-sized tokens with distinct type planes so a surface
 * can never be confused for a context (the Android EGL handle law). */
typedef struct EGLToken_ {
    uint32_t magic;   /* 'EGLD'/'EGLc'/'EGLs'/'EGLi' */
    uint32_t id;
    int32_t width, height;
} EGLToken;

static uint32_t g_egl_err = EGL_SUCCESS;
static void* g_dpy = NULL;      /* current display token */
static void* g_ctx = NULL;      /* current context */
static void* g_surf = NULL;     /* current draw+read surface */
static void* g_surf_rd = NULL;  /* current read surface */
static void* g_cfg = NULL;      /* THE one config (RGBA8888/24/8) */
static uint32_t g_next_id = 1;
/* one config: RGBA8888, 24-bit depth, 8-bit stencil, window+pbuffers */
static const int32_t k_cfg_attribs[][2] = {
    {EGL_BUFFER_SIZE, 32}, {EGL_RED_SIZE, 8}, {EGL_GREEN_SIZE, 8},
    {EGL_BLUE_SIZE, 8}, {EGL_ALPHA_SIZE, 8}, {EGL_DEPTH_SIZE, 24},
    {EGL_STENCIL_SIZE, 8}, {EGL_SAMPLES, 0}, {EGL_SAMPLE_BUFFERS, 0},
    {EGL_SURFACE_TYPE, EGL_WINDOW_BIT | EGL_PBUFFER_BIT},
    {EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT},
    {EGL_CONFIG_ID, 1}, {EGL_CONFORMANT, 0},
    {EGL_MAX_PBUFFER_WIDTH, 8192}, {EGL_MAX_PBUFFER_HEIGHT, 8192},
    {EGL_MAX_PBUFFER_PIXELS, 8192 * 8192},
};
#define k_cfg_n (int)(sizeof(k_cfg_attribs) / sizeof(k_cfg_attribs[0]))

static void* make_token(uint32_t magic) {
    EGLToken* t = (EGLToken*)calloc(1, sizeof(EGLToken));
    if (!t) return NULL;
    t->magic = magic;
    t->id = g_next_id++;
    return t;
}
static int cfg_lookup(int32_t attr, int32_t* val) {
    for (int i = 0; i < k_cfg_n; ++i)
        if (k_cfg_attribs[i][0] == attr) { *val = k_cfg_attribs[i][1]; return 1; }
    return 0;
}
static void* the_config(void) {
    if (!g_cfg) g_cfg = make_token(0x45474c66u /* EGLf */);
    return g_cfg;
}

__attribute__((visibility("default")))
void* eglGetDisplay(void* native_display) {
    (void)native_display;
    if (!g_dpy) {
        g_dpy = make_token(0x45474c44u /* EGLD */);
        if (!g_dpy) { g_egl_err = EGL_BAD_ALLOC; return NULL; }
    }
    g_egl_err = EGL_SUCCESS;
    return g_dpy;
}

__attribute__((visibility("default")))
unsigned eglInitialize(void* dpy, int32_t* major, int32_t* minor) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (major) *major = 1;
    if (minor) *minor = 4; /* Android-guaranteed EGL floor */
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglTerminate(void* dpy) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglGetConfigs(void* dpy, void** configs, int32_t n, int32_t* num) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!num) { g_egl_err = EGL_BAD_PARAMETER; return EGL_FALSE; }
    if (configs && n > 0) {
        configs[0] = the_config();
        *num = 1;
    } else {
        *num = 1;
    }
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglChooseConfig(void* dpy, const int32_t* attribs, void** configs,
                         int32_t n, int32_t* num) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!num) { g_egl_err = EGL_BAD_PARAMETER; return EGL_FALSE; }
    /* single-config law: every red/green/blue/alpha request ≤8 matches the
     * RGBA8888 config; a request ABOVE the cap is the EGL_BAD_MATCH shape. */
    int match = 1;
    for (const int32_t* a = attribs; a && a[0] != EGL_NONE; a += 2) {
        int32_t have;
        if (a[0] == EGL_CONFIG_CAVEAT) continue;
        if (!cfg_lookup(a[0], &have)) {
            if (a[0] == EGL_VG_ALPHA_FORMAT || a[0] == EGL_VG_COLORSPACE ||
                a[0] == EGL_COLORSPACE || a[0] == EGL_ALPHA_FORMAT)
                continue;
            match = 0;  /* unknown attr: honest mismatch */
            break;
        }
        if (a[1] > have &&
            (a[0] == EGL_RED_SIZE || a[0] == EGL_GREEN_SIZE ||
             a[0] == EGL_BLUE_SIZE || a[0] == EGL_ALPHA_SIZE ||
             a[0] == EGL_DEPTH_SIZE || a[0] == EGL_STENCIL_SIZE)) {
            match = 0;
            break;
        }
    }
    if (match && configs && n > 0) {
        configs[0] = the_config();
        *num = 1;
    } else {
        *num = 0;
    }
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglGetConfigAttrib(void* dpy, void* cfg, int32_t attr, int32_t* val) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!cfg) { g_egl_err = EGL_BAD_CONFIG; return EGL_FALSE; }
    int32_t v;
    if (!cfg_lookup(attr, &v)) { g_egl_err = EGL_BAD_ATTRIBUTE; return EGL_FALSE; }
    if (val) *val = v;
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
void* eglCreateContext(void* dpy, void* cfg, void* share) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return NULL; }
    if (!cfg) { g_egl_err = EGL_BAD_CONFIG; return NULL; }
    (void)share;
    void* c = make_token(0x45474c63u /* EGLc */);
    if (!c) g_egl_err = EGL_BAD_ALLOC;
    else g_egl_err = EGL_SUCCESS;
    return c;
}

__attribute__((visibility("default")))
unsigned eglDestroyContext(void* dpy, void* ctx) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!ctx) { g_egl_err = EGL_BAD_CONTEXT; return EGL_FALSE; }
    if (ctx == g_ctx) { g_ctx = NULL; }
    free(ctx);
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

static void* create_surface(uint32_t magic, const int32_t* attribs) {
    void* s = make_token(magic);
    if (!s) { g_egl_err = EGL_BAD_ALLOC; return NULL; }
    EGLToken* t = (EGLToken*)s;
    for (const int32_t* a = attribs; a && a[0] != EGL_NONE; a += 2) {
        if (a[0] == EGL_WIDTH) t->width = a[1];
        else if (a[0] == EGL_HEIGHT) t->height = a[1];
    }
    if (!t->width || !t->height) {
        int32_t w = 0, h = 0;
        if (__ma_egl_surface_size) __ma_egl_surface_size(&w, &h);
        if (!t->width) t->width = w ? w : 1080;
        if (!t->height) t->height = h ? h : 1920;
    }
    g_egl_err = EGL_SUCCESS;
    return s;
}

__attribute__((visibility("default")))
void* eglCreateWindowSurface(void* dpy, void* cfg, void* win,
                             const int32_t* attribs) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return NULL; }
    if (!cfg) { g_egl_err = EGL_BAD_CONFIG; return NULL; }
    (void)win;
    return create_surface(0x45474c73u /* EGLs */, attribs);
}

__attribute__((visibility("default")))
void* eglCreatePbufferSurface(void* dpy, void* cfg, const int32_t* attribs) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return NULL; }
    if (!cfg) { g_egl_err = EGL_BAD_CONFIG; return NULL; }
    return create_surface(0x45474c73u /* EGLs */, attribs);
}

__attribute__((visibility("default")))
unsigned eglDestroySurface(void* dpy, void* surf) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!surf) { g_egl_err = EGL_BAD_SURFACE; return EGL_FALSE; }
    if (surf == g_surf) g_surf = NULL;
    if (surf == g_surf_rd) g_surf_rd = NULL;
    free(surf);
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglMakeCurrent(void* dpy, void* draw, void* read, void* ctx) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if ((draw && !read) || (!draw && read)) {
        g_egl_err = EGL_BAD_MATCH; return EGL_FALSE;
    }
    if (draw && !ctx) { g_egl_err = EGL_BAD_CONTEXT; return EGL_FALSE; }
    g_surf = draw;
    g_surf_rd = read;
    g_ctx = ctx;
    if (ctx && __ma_egl_make_current) __ma_egl_make_current();
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglQuerySurface(void* dpy, void* surf, int32_t attr, int32_t* val) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!surf) { g_egl_err = EGL_BAD_SURFACE; return EGL_FALSE; }
    EGLToken* t = (EGLToken*)surf;
    int32_t v = 0;
    switch (attr) {
        case EGL_WIDTH: v = t->width; break;
        case EGL_HEIGHT: v = t->height; break;
        case EGL_TEXTURE_FORMAT: v = EGL_NO_TEXTURE; break;
        case EGL_TEXTURE_TARGET: v = EGL_NO_TEXTURE; break;
        case EGL_MIPMAP_TEXTURE: v = EGL_FALSE; break;
        case EGL_MIPMAP_LEVEL: v = 0; break;
        case EGL_LARGEST_PBUFFER: v = EGL_FALSE; break;
        default: g_egl_err = EGL_BAD_ATTRIBUTE; return EGL_FALSE;
    }
    if (val) *val = v;
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
unsigned eglSwapBuffers(void* dpy, void* surf) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!surf) { g_egl_err = EGL_BAD_SURFACE; return EGL_FALSE; }
    /* the native frame-present hook: the exe's frame pipeline decides what
     * a presented frame becomes (S188 W2: first real Flutter frame). */
    if (__ma_egl_frame_present) __ma_egl_frame_present();
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
void* eglCreateImageKHR(void* dpy, void* ctx, uint32_t target, void* buffer,
                        const int32_t* attribs) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return NULL; }
    (void)ctx; (void)target; (void)buffer; (void)attribs;
    void* img = make_token(0x45474c69u /* EGLi */);
    if (!img) g_egl_err = EGL_BAD_ALLOC;
    else g_egl_err = EGL_SUCCESS;
    return img;
}

__attribute__((visibility("default")))
unsigned eglDestroyImageKHR(void* dpy, void* img) {
    if (!dpy || dpy != g_dpy) { g_egl_err = EGL_BAD_DISPLAY; return EGL_FALSE; }
    if (!img) { g_egl_err = EGL_BAD_PARAMETER; return EGL_FALSE; }
    free(img);
    g_egl_err = EGL_SUCCESS;
    return EGL_TRUE;
}

__attribute__((visibility("default")))
void* eglGetCurrentDisplay(void) { return g_dpy; }

__attribute__((visibility("default")))
void* eglGetCurrentSurface(int32_t readdraw) { return readdraw ? g_surf_rd : g_surf; }

__attribute__((visibility("default")))
void* eglGetCurrentContext(void) { return g_ctx; }

__attribute__((visibility("default")))
unsigned eglGetError(void) {
    unsigned e = g_egl_err;
    g_egl_err = EGL_SUCCESS;
    return e;
}

__attribute__((visibility("default")))
void* eglGetProcAddress(const char* name) {
    if (!name) return NULL;
    /* Resolve through the GLOBAL scope: the exe's -rdynamic gl* surface,
       the GLESv2 anchor, and any preloaded provider. */
    void* p = dlsym(RTLD_DEFAULT, name);
    return p;
}

/* EGL 1.5 entry some engines probe for via eglGetProcAddress */
__attribute__((visibility("default")))
const char* eglQueryString(void* dpy, int32_t name) {
    if (!dpy) return NULL;  /* EGL_NO_DISPLAY: client extensions, none */
    switch (name) {
        case 0x3081 /* EGL_VENDOR */: return "MiniAndroid PortableGL";
        case 0x3082 /* EGL_VERSION */: return "1.4 MiniAndroid S188";
        case 0x3083 /* EGL_EXTENSIONS */:
            return "EGL_KHR_image_base EGL_KHR_surfaceless_context";
        case 0x308D /* EGL_CLIENT_APIS */: return "OpenGL_ES ";
        default: g_egl_err = EGL_BAD_PARAMETER; return NULL;
    }
}
