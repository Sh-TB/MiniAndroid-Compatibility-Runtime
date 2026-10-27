/* T22 (F-NEW-564 support): libjnigraphics anchor — the first-party 3-func
 * AndroidBitmap surface (T18's named design, reconstructed).
 *
 * The lib calls AndroidBitmap_{getInfo,lockPixels,unlockPixels}(env, jbitmap, ...)
 * with the engine's jobject marshaling (0x500000000|heap_id). The pixel
 * truth lives in the exe's BitmapStore; this anchor reaches it through the
 * exe-exported C-ABI query helper __ma_bitmap_query (RTLD_DEFAULT), then
 * serves the AOSP jnigraphics contract directly on engine-owned storage
 * (no copy; lock/unlock are engine-storage views). Honest failures return
 * the spec negative codes when the id is unknown or the helper is absent
 * (standalone anchor use). */
#include <stdint.h>
#include <stddef.h>
#include <dlfcn.h>

typedef struct {
    uint32_t width;
    uint32_t height;
    int32_t format;    /* ANDROID_BITMAP_FORMAT_* : 1 = RGBA_8888 */
    uint32_t stride;   /* bytes per row */
} AndroidBitmapInfo;

#define ABM_SUCCESS 0
#define ABM_BAD_PARAMETER (-1)
#define ABM_BAD_VALUE (-4)

typedef int (*ma_bitmap_query_fn)(uint32_t heap_id, int32_t* w, int32_t* h,
                                  int32_t* fmt, uint8_t** pixels,
                                  int32_t* stride);

static ma_bitmap_query_fn ma_query(void) {
    static ma_bitmap_query_fn q = (ma_bitmap_query_fn)-1;
    if (q == (ma_bitmap_query_fn)-1)
        q = (ma_bitmap_query_fn)dlsym(RTLD_DEFAULT, "__ma_bitmap_query");
    return q;
}

static uint32_t ma_heap_id(void* jbitmap) {
    /* jobject marshaling law: 0x500000000 | heap_id */
    return (uint32_t)(((uint64_t)(uintptr_t)jbitmap) & 0xffffffffull);
}

__attribute__((visibility("default")))
int AndroidBitmap_getInfo(void* env, void* jbitmap, AndroidBitmapInfo* info) {
    (void)env;
    ma_bitmap_query_fn q = ma_query();
    if (!info || !jbitmap) return ABM_BAD_PARAMETER;
    int32_t w = 0, h = 0, fmt = 0, stride = 0;
    uint8_t* px = NULL;
    if (!q) return ABM_BAD_VALUE;  /* no engine bridge in scope */
    int rc = q(ma_heap_id(jbitmap), &w, &h, &fmt, &px, &stride);
    if (rc != ABM_SUCCESS) return rc;
    info->width = (uint32_t)w;
    info->height = (uint32_t)h;
    info->format = fmt;
    info->stride = (uint32_t)stride;
    return ABM_SUCCESS;
}

__attribute__((visibility("default")))
int AndroidBitmap_lockPixels(void* env, void* jbitmap, void** addrPtr) {
    (void)env;
    ma_bitmap_query_fn q = ma_query();
    if (!jbitmap || !addrPtr) return ABM_BAD_PARAMETER;
    int32_t w = 0, h = 0, fmt = 0, stride = 0;
    uint8_t* px = NULL;
    if (!q) return ABM_BAD_VALUE;
    int rc = q(ma_heap_id(jbitmap), &w, &h, &fmt, &px, &stride);
    if (rc != ABM_SUCCESS) return rc;
    *addrPtr = px;  /* engine-owned storage view; may be NULL for an
                       allocated-but-never-filled bitmap (AOSP allows) */
    return ABM_SUCCESS;
}

__attribute__((visibility("default")))
int AndroidBitmap_unlockPixels(void* env, void* jbitmap) {
    (void)env; (void)jbitmap;
    /* engine-owned storage: mutations are already live in the store */
    return ABM_SUCCESS;
}
