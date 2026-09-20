// bitmap_shadow.h — S68 FINAL BASE CLOSURE §12/§13: android.graphics.Bitmap
// + BitmapFactory shadows with a process-wide pixel store.
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (AOSP graphics/BitmapFactory.java + graphics/Bitmap.java):
//   * BitmapFactory maps an ENCODED byte stream (PNG/JPEG/WebP/...) to a
//     Bitmap whose pixels are the decoded image (format chosen by magic,
//     never by extension — see renderer::decode_image_bytes).
//   * decodeResource(Resources, int id) resolves the id through the asset
//     pipeline; a FAILED decode returns NULL (never a silently-empty
//     bitmap — callers check and fall back per Android contract).
//   * Bitmap.createBitmap(w, h, config) yields a bitmap whose pixels are
//     all ZERO (transparent black in ARGB_8888); eraseColor paints it.
//   * createScaledBitmap(src, w, h, filter) resamples the WHOLE source
//     into the requested size; filter=true → bilinear, false → nearest
//     (the runtime implements nearest for both deterministically until a
//     bilinear consumer appears — registered honestly).
//   * Canvas.drawBitmap consumes these pixels via the BitmapStore.
//
// STORAGE: one process-wide BitmapStore keyed by heap object id. The
// runtime is single-threaded and deterministic (EXP-051 law), so a plain
// std::map keeps iteration/lookup deterministic.
//
// APK RESOLUTION: decodeResource needs resid → APK entry bytes. The shadow
// itself knows nothing about APKs (§16 boundary): the ENGINE registers a
// bytes resolver hook at init (set_drawable_bytes_resolver) using its own
// canonical drawable path law. If no resolver is registered, decodeResource
// honestly returns null (observe: no fake bitmap).
// ─────────────────────────────────────────────────────────────────────────
#pragma once

#include "shadow_registry.h"

#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <vector>

namespace miniandroid { namespace framework {

struct StoredBitmap {
    int width = 0, height = 0;
    std::vector<uint8_t> rgba;        // width*height*4, premultiplied OFF
    bool has_pixels = false;          // false = allocated-but-never-filled
    std::string source_desc;          // provenance (resource path / "createBitmap")
};

class BitmapStore {
public:
    static BitmapStore& instance();

    // Register a fresh bitmap object (pixels optional). Overwrites nothing
    // if the id already holds a live bitmap (heap ids are unique).
    void create(uint32_t obj_id, int w, int h, const std::string& desc);
    void store(uint32_t obj_id, int w, int h, std::vector<uint8_t> rgba,
               const std::string& desc);
    const StoredBitmap* get(uint32_t obj_id) const;
    StoredBitmap* get_mut(uint32_t obj_id);
    void erase(uint32_t obj_id);
    size_t size() const { return store_.size(); }

private:
    BitmapStore() = default;
    std::map<uint32_t, StoredBitmap> store_;
};

class BitmapShadow : public Shadow {
public:
    std::string name() const override { return "BitmapShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls == "Landroid/graphics/Bitmap;" ||
               cls.find("graphics/Bitmap;") != std::string::npos ||
               cls == "Landroid/graphics/BitmapFactory;" ||
               cls.find("graphics/BitmapFactory;") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    // Engine hook: resid → decoded bytes (+ path + density for traces).
    // Registered once at engine init; empty function = decodeResource
    // honestly returns null.
    using DrawableBytesResolver =
        std::function<bool(uint32_t resid, std::vector<uint8_t>& bytes,
                           std::string& path, uint16_t& density)>;
    static void set_drawable_bytes_resolver(DrawableBytesResolver fn);
    static const DrawableBytesResolver& drawable_bytes_resolver();

    // Shared decode-and-register helper (used by every decode* entry):
    // returns the new Bitmap object id, or 0 on failed decode (AOSP null).
    static uint32_t decode_and_register(const std::vector<uint8_t>& bytes,
                                        const std::string& desc,
                                        HeapAllocator* heap);
};

} } // namespace miniandroid::framework
