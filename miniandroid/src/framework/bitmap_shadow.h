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
    // ── C9-1 (CODER 9) — decode-law provenance (byte-level chain) ────────
    // source_desc stays the PURE APK entry path (route_bitmap_object uses
    // it as a zip path — suffixes would break the entry lookup); the
    // decode-law fingerprint lives in these fields instead.
    uint16_t density = 0;             // density the bitmap is MARKED with (opts.outDensity; 0 = none)
    uint16_t source_density = 0;      // inDensity actually applied (selected entry config / opts)
    uint16_t target_density = 0;      // inTargetDensity actually applied
    int32_t source_width = 0;         // raw decoder output (pre-sample, pre-scale)
    int32_t source_height = 0;
    int32_t sample_size = 1;          // opts.inSampleSize applied (1 = none)
    bool density_scaled = false;      // density scale actually applied
    // CONT-65 F-NEW-355: original container bytes for ANIMATED formats
    // (GIF89a/GIF87a only — stb_image first-frame decode can't recover
    // delays). Populated by decode_and_register on GIF magic; empty for
    // every other format (bounded by asset size, one copy per bitmap).
    std::vector<uint8_t> source_gif_bytes;
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

    // LOADING-CAMPAIGN (R-10 FIX): stream object id → REAL bytes. The
    // engine owns open_assets_ (asset/file/apkfd keys) and registers this
    // hook; decodeStream drains the stream's bytes through it (AOSP
    // BitmapFactory.decodeStream: the canonical asset/network→bitmap path).
    using StreamBytesResolver =
        std::function<bool(uint32_t stream_id, std::vector<uint8_t>& bytes,
                           std::string& source_desc)>;
    static void set_stream_bytes_resolver(StreamBytesResolver fn);
    static const StreamBytesResolver& stream_bytes_resolver();

    // Shared decode-and-register helper (used by every decode* entry):
    // returns the new Bitmap object id, or 0 on failed decode (AOSP null).
    static uint32_t decode_and_register(const std::vector<uint8_t>& bytes,
                                        const std::string& desc,
                                        HeapAllocator* heap);
};

// ── C9-1 (CODER 9) — AOSP BitmapFactory.Options density law, pure & testable
// ─────────────────────────────────────────────────────────────────────────
// Law chain (source-backed, aosp-mirror/platform_frameworks_base master,
// graphics/java/android/graphics/BitmapFactory.java):
//   decodeResourceStream (lines ~557-574):
//     if (opts.inDensity == 0 && value != null) {
//         density = value.density == TypedValue.DENSITY_DEFAULT (0)
//                     ? DisplayMetrics.DENSITY_DEFAULT (160)
//                 : value.density == TypedValue.DENSITY_ANY (0xFFFE)
//                     ? Bitmap.DENSITY_NONE (0xFFFF) : value.density;
//         opts.inDensity = density;
//     }
//     if (opts.inTargetDensity == 0 && res != null)
//         opts.inTargetDensity = res.getDisplayMetrics().densityDpi;
//   BitmapFactory.cpp native scale:
//     scale applies iff inScaled && inDensity != 0 &&
//       inDensity != DENSITY_NONE(0xFFFF) && inTargetDensity != 0 &&
//       inDensity != inTargetDensity;
//     scale = (float)inTargetDensity / (float)inDensity;
//     scaledWidth  = (int)(decodedWidth  * scale + 0.5f);
//     scaledHeight = (int)(decodedHeight * scale + 0.5f);
//   setDensityFromOptions (lines ~682-700):
//     bitmap.setDensity(inDensity); then, when inScaled &&
//     inTargetDensity != 0 && inDensity != inTargetDensity,
//     bitmap.setDensity(inTargetDensity) — the SCALED bitmap is MARKED
//     with the target density.
//   Options has NO public outDensity field — the density lives on the
//   Bitmap (Bitmap.getDensity). out* carry the FINAL dims (sample-size
//   and density scale composed).
// This mirrors the draw-layer law g04_image_draw_rect (execution_engine.cpp)
// so decode-time and draw-time density cannot drift.
struct BitmapFactoryDensityInput {
    int32_t raw_width = 0;         // decoder output (source pixels)
    int32_t raw_height = 0;
    int32_t in_density = 0;        // opts.inDensity AFTER decodeResourceStream seeding
                                   // (0 = unset, 160 = DENSITY_DEFAULT, 0xFFFF = DENSITY_NONE)
    int32_t in_target_density = 0; // opts.inTargetDensity (0 = unset → no scaling)
    bool in_scaled = true;         // opts.inScaled — AOSP Java default true
    int32_t in_sample_size = 1;    // opts.inSampleSize (values < 1 clamp to 1)
};
struct BitmapFactoryDensityResult {
    int32_t width = 0;             // FINAL dims (inSampleSize → density scale)
    int32_t height = 0;
    int32_t sampled_width = 0;     // after inSampleSize only
    int32_t sampled_height = 0;
    int32_t bitmap_density = 0;    // setDensityFromOptions result (Bitmap.getDensity)
    bool density_scaled = false;   // density scale actually applied
    bool valid = false;            // false = degenerate input (raw dims <= 0)
};
BitmapFactoryDensityResult bitmap_factory_density_law(
    const BitmapFactoryDensityInput& in);

} } // namespace miniandroid::framework
