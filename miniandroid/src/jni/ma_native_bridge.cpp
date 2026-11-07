// T22 (F-NEW-564 support): C-ABI bridge from the first-party anchor set to
// the engine's BitmapStore. The anchor .so files cannot reach C++ engine
// objects directly; this file (compiled INTO the exe, -rdynamic) exports a
// flat C surface the anchors dlsym(RTLD_DEFAULT).
//
// jobject marshaling law (dlopen_exec.cpp): jobject = 0x500000000|heap_id,
// so the low 32 bits are the engine heap object id = BitmapStore key.
#include "framework/bitmap_shadow.h"
#include "gles/pgl_backend.h"

#include <cstdint>
#include <cstdio>
#include <cstring>

using namespace miniandroid::framework;

extern "C" __attribute__((visibility("default")))
int __ma_bitmap_query(uint32_t heap_id, int32_t* w, int32_t* h,
                      int32_t* fmt_rgba8888, uint8_t** pixels,
                      int32_t* stride_bytes) {
    const StoredBitmap* bm = BitmapStore::instance().get(heap_id);
    if (!bm) return -4;  // ANDROID_BITMAP_RESULT_BAD_VALUE (unknown id)
    if (w) *w = bm->width;
    if (h) *h = bm->height;
    if (fmt_rgba8888) *fmt_rgba8888 = 1;  // ANDROID_BITMAP_FORMAT_RGBA_8888
    if (stride_bytes) *stride_bytes = bm->width * 4;
    if (pixels) {
        // StoredBitmap pixels are engine-owned; the native lib reads (and
        // may modify) them in place between lock/unlock — no copy, the
        // engine renders the SAME storage (single-storey law).
        static thread_local std::vector<uint8_t> tl_empty;
        *pixels = bm->rgba.empty() ? nullptr : const_cast<uint8_t*>(bm->rgba.data());
    }
    return 0;  // ANDROID_BITMAP_RESULT_SUCCESS
}

// ── S188-W2: EGL anchor hooks ───────────────────────────────────────────
// The libEGL/libGLESv2 anchors (scripts/cont83_egl_anchor.c /
// cont83_glesv2_anchor.c) reach the engine's software-GL reality through
// this flat C surface (same law as __ma_bitmap_query). Weak-linkage
// callers in the anchors degrade to their recorded state when these are
// absent — never a fabricated success.
extern "C" __attribute__((visibility("default")))
int __ma_egl_surface_size(int32_t* w, int32_t* h) {
    auto& pgl = miniandroid::gles::PGLBackend::instance();
    if (!pgl.ok()) return -1;  // no surface yet: anchor falls back
    if (w) *w = pgl.width();
    if (h) *h = pgl.height();
    return 0;
}

extern "C" __attribute__((visibility("default")))
int __ma_egl_make_current(void) {
    auto& pgl = miniandroid::gles::PGLBackend::instance();
    if (!pgl.ok()) return -1;
    // Bind the PGL context as current so the native engine's gl* calls
    // land on OUR software context (the same one the View lane draws to —
    // single-context law, gl_surface_shadow precedent).
    return pgl.make_current() ? 0 : -1;
}

extern "C" __attribute__((visibility("default")))
int __ma_egl_frame_present(void) {
    auto& pgl = miniandroid::gles::PGLBackend::instance();
    if (!pgl.ok()) return -1;
    pgl.frame_end();
    static int s_frames = 0;
    if (++s_frames <= 8 || (s_frames & 63) == 0)
        fprintf(stderr, "[S188-EGl-ANCHOR] frame_present n=%d %dx%d\n",
                s_frames, pgl.width(), pgl.height());
    return 0;
}

extern "C" __attribute__((visibility("default")))
void __ma_pgl_frame_end(void) {
    auto& pgl = miniandroid::gles::PGLBackend::instance();
    if (pgl.ok()) pgl.frame_end();
}
