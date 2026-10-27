/* T22 (F-NEW-564 support): libandroid anchor — honest first-party surface
 * for the symbols libtmessages binds (T18's "honest surfaces" design,
 * reconstructed from the tracked spec text).
 *
 * Laws (software runtime, no display/audio hardware):
 *  - IDENTITY: ANativeWindow_fromSurface / AAssetManager_fromJava return a
 *    NON-NULL opaque token derived from the passed jobject (0 = input null)
 *    so app null-checks behave like a real device.
 *  - OPERATIONS: window lock/unlockAndPost/setBuffersGeometry honestly
 *    report no window buffers (AOSP negative/0 semantics, documented
 *    deviation: no pixels are served — the GL/EGL software path is the
 *    render surface); asset open returns NULL (asset absent = legal state
 *    apps must handle), asset read serves nothing.
 *  - No app special-casing: the surface is the platform primitive. */
#include <stdint.h>
#include <stddef.h>

/* ── ANativeWindow family ──────────────────────────────────────────────── */
typedef struct ANativeWindow ANativeWindow;
typedef struct ANativeWindow_Buffer {
    int32_t width, height, stride;  /* stride in pixels */
    int32_t format;
    void* bits;
} ANativeWindow_Buffer;

static void* ma_window_token(void* jsurface) {
    /* jobject/surface marshaling law: 0x500000000 | heap_id; 0 stays 0 */
    uint64_t v = (uint64_t)(uintptr_t)jsurface;
    if (!v) return NULL;
    return (void*)(uintptr_t)(0x600000000ull | (v & 0xffffffffull));
}

__attribute__((visibility("default")))
ANativeWindow* ANativeWindow_fromSurface(void* env, void* surface) {
    (void)env;
    return (ANativeWindow*)ma_window_token(surface);
}

__attribute__((visibility("default")))
void ANativeWindow_release(ANativeWindow* window) { (void)window; }

__attribute__((visibility("default")))
int ANativeWindow_lock(ANativeWindow* window, ANativeWindow_Buffer* outBuffer,
                       void* outRectangle) {
    /* honest: the software runtime's window has no lockable CPU buffer */
    (void)window; (void)outBuffer; (void)outRectangle;
    return -1; /* AOSP: nonzero = failure */
}

__attribute__((visibility("default")))
int ANativeWindow_unlockAndPost(ANativeWindow* window) {
    (void)window;
    return 0; /* nothing locked -> nothing to post (honest no-op) */
}

__attribute__((visibility("default")))
int32_t ANativeWindow_setBuffersGeometry(ANativeWindow* window, int32_t width,
                                         int32_t height, int32_t format) {
    /* accept the request (identity window keeps no geometry state) */
    (void)window; (void)width; (void)height; (void)format;
    return 0;
}

__attribute__((visibility("default")))
int32_t ANativeWindow_getWidth(ANativeWindow* window) {
    (void)window; return 0;
}

__attribute__((visibility("default")))
int32_t ANativeWindow_getHeight(ANativeWindow* window) {
    (void)window; return 0;
}

/* ── AAsset family (honest: engine-side assets are served by the DEX
 *    AssetManager shadow; the NDK AAsset surface has no file descriptors
 *    to hand out in this runtime) ──────────────────────────────────────── */
typedef struct AAssetManager AAssetManager;
typedef struct AAsset AAsset;

__attribute__((visibility("default")))
AAssetManager* AAssetManager_fromJava(void* env, void* assetManager) {
    (void)env;
    return (AAssetManager*)ma_window_token(assetManager);
}

__attribute__((visibility("default")))
AAsset* AAssetManager_open(AAssetManager* mgr, const char* filename, int mode) {
    (void)mgr; (void)filename; (void)mode;
    return NULL; /* asset absent — a legal state apps must handle */
}

__attribute__((visibility("default")))
void AAsset_close(AAsset* asset) { (void)asset; }

__attribute__((visibility("default")))
int AAsset_read(AAsset* asset, void* buf, size_t count) {
    (void)asset; (void)buf; (void)count;
    return 0; /* EOF on a NULL/absent asset */
}
