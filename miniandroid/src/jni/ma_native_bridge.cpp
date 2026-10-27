// T22 (F-NEW-564 support): C-ABI bridge from the first-party anchor set to
// the engine's BitmapStore. The anchor .so files cannot reach C++ engine
// objects directly; this file (compiled INTO the exe, -rdynamic) exports a
// flat C surface the anchors dlsym(RTLD_DEFAULT).
//
// jobject marshaling law (dlopen_exec.cpp): jobject = 0x500000000|heap_id,
// so the low 32 bits are the engine heap object id = BitmapStore key.
#include "framework/bitmap_shadow.h"

#include <cstdint>
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
