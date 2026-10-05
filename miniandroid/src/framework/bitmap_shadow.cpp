// bitmap_shadow.cpp — S68 §12/§13: Bitmap/BitmapFactory implementation.
// See bitmap_shadow.h for the upstream law.
#include "bitmap_shadow.h"
#include "../diagnostics/gfx_provenance.h"
#include "../renderer/software_renderer.h"
#include "../resources/res_config.h"
#include "../storage/data_root.h"  // LOADING-CAMPAIGN: ONE path law (ST-5 fix)

#include <algorithm>
#include <cmath>
#include <iostream>

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// BitmapStore
// ─────────────────────────────────────────────────────────────────────────
BitmapStore& BitmapStore::instance() {
    static BitmapStore store;
    return store;
}

void BitmapStore::create(uint32_t obj_id, int w, int h, const std::string& desc) {
    StoredBitmap& b = store_[obj_id];
    b.width = w; b.height = h;
    b.rgba.assign((size_t)std::max(0, w) * std::max(0, h) * 4, 0);
    b.has_pixels = true;   // zero-filled = transparent black (AOSP createBitmap)
    b.source_desc = desc;
}

void BitmapStore::store(uint32_t obj_id, int w, int h, std::vector<uint8_t> rgba,
                        const std::string& desc) {
    StoredBitmap& b = store_[obj_id];
    b.width = w; b.height = h;
    b.rgba = std::move(rgba);
    b.has_pixels = true;
    b.source_desc = desc;
}

const StoredBitmap* BitmapStore::get(uint32_t obj_id) const {
    auto it = store_.find(obj_id);
    return it != store_.end() ? &it->second : nullptr;
}

StoredBitmap* BitmapStore::get_mut(uint32_t obj_id) {
    auto it = store_.find(obj_id);
    return it != store_.end() ? &it->second : nullptr;
}

void BitmapStore::erase(uint32_t obj_id) { store_.erase(obj_id); }

// ─────────────────────────────────────────────────────────────────────────
// Resolver hook
// ─────────────────────────────────────────────────────────────────────────
static BitmapShadow::DrawableBytesResolver& resolver_slot() {
    static BitmapShadow::DrawableBytesResolver fn;
    return fn;
}
void BitmapShadow::set_drawable_bytes_resolver(DrawableBytesResolver fn) {
    resolver_slot() = std::move(fn);
}

// LOADING-CAMPAIGN (R-10 FIX): stream-bytes resolver slot (engine-registered).
static BitmapShadow::StreamBytesResolver& stream_resolver_slot() {
    static BitmapShadow::StreamBytesResolver fn;
    return fn;
}
void BitmapShadow::set_stream_bytes_resolver(StreamBytesResolver fn) {
    stream_resolver_slot() = std::move(fn);
}
const BitmapShadow::DrawableBytesResolver& BitmapShadow::drawable_bytes_resolver() {
    return resolver_slot();
}
const BitmapShadow::StreamBytesResolver& BitmapShadow::stream_bytes_resolver() {
    return stream_resolver_slot();
}

uint32_t BitmapShadow::decode_and_register(const std::vector<uint8_t>& bytes,
                                           const std::string& desc,
                                           HeapAllocator* heap) {
    if (!heap) return 0;
    renderer::DecodedImage decoded;
    if (!renderer::decode_image_bytes(bytes, &decoded, resources::device_config().density) || decoded.width <= 0 ||
        decoded.height <= 0 || decoded.rgba.empty()) {
        // AOSP: failed decode → null. The failure is ALREADY reported by
        // decode_image_bytes (format named) — never silent.
        std::cerr << "[BITMAP-FACTORY] decode FAILED (" << desc << "): "
                  << decoded.error << std::endl;
        if (diagnostics::GfxProvenance::instance().enabled())
            diagnostics::GfxProvenance::instance().record_image(
                "bitmapfactory-decode", 0, desc, !bytes.empty(), false, 0, 0,
                "", 0, 0, 0, 0, 0, false, decoded.error);
        return 0;
    }
    const uint32_t obj = heap->allocate("Landroid/graphics/Bitmap;");
    BitmapStore::instance().store(obj, decoded.width, decoded.height,
                                  std::move(decoded.rgba), desc);
    std::cerr << "[BITMAP-FACTORY] decoded " << desc << " -> Bitmap obj=" << obj
              << " (" << decoded.width << "x" << decoded.height << ", "
              << decoded.color_type_name << ")" << std::endl;
    if (diagnostics::GfxProvenance::instance().enabled())
        diagnostics::GfxProvenance::instance().record_image(
            "bitmapfactory-decode", 0, desc, !bytes.empty(), true,
            decoded.width, decoded.height, decoded.color_type_name, 0,
            0, 0, 0, 0, false, "");
    return obj;
}

// ─────────────────────────────────────────────────────────────────────────
// ──────────────────────────────────────────────────────────────────────────
// Nearest-neighbour resample (createScaledBitmap; bilinear registered as
// pending until a consumer demands it — the runtime answers honestly).
// Defined below; forward-declared for the F-NEW-240 helper.
// ──────────────────────────────────────────────────────────────────────────
static void resample_nearest(const StoredBitmap& src, int dw, int dh,
                             std::vector<uint8_t>& out);

// F-NEW-240 — AOSP BitmapFactory.Options law (fairymahjong CONT-4 face).
// Kotlin's canonical "decode bounds first" idiom:
//   val opts = BitmapFactory.Options(); opts.inJustDecodeBounds = true
//   BitmapFactory.decodeStream(open(path), null, opts)
//   if (opts.outWidth <= 0 || opts.outHeight <= 0) error("Invalid …")
// AOSP BitmapFactory.java: inJustDecodeBounds=true parses ONLY the image
// header — decodeStream/decodeFile/decodeResource/decodeByteArray fill
// opts.outWidth/outHeight/outMimeType and return NULL without allocating
// a bitmap. The pre-fix engine ran the FULL decode and never wrote the
// out* fields → outWidth stayed 0 → every bounds-checked loader threw
// its own "Invalid" error on perfectly valid artwork (the game's own
// IllegalStateException "Invalid fairy artwork: tiles/07-portrait.png").
// Also honored here: inSampleSize (AOSP: out dims = (dim + s-1) / s,
// nearest subsample) and out* is filled in the FULL-decode mode too.
// ─────────────────────────────────────────────────────────────────────────
static std::string f240_mime_of(const std::vector<uint8_t>& b) {
    if (b.size() >= 4 && b[0] == 0x89 && b[1] == 'P' && b[2] == 'N' &&
        b[3] == 'G')
        return "image/png";
    if (b.size() >= 3 && b[0] == 0xFF && b[1] == 0xD8 && b[2] == 0xFF)
        return "image/jpeg";
    if (b.size() >= 6 && (!memcmp(b.data(), "GIF87a", 6) ||
                          !memcmp(b.data(), "GIF89a", 6)))
        return "image/gif";
    if (b.size() >= 12 && !memcmp(b.data(), "RIFF", 4) &&
        !memcmp(b.data() + 8, "WEBP", 4))
        return "image/webp";
    if (b.size() >= 2 && b[0] == 'B' && b[1] == 'M') return "image/bmp";
    return "";
}

// Decode once, serve the AOSP Options contract, and (optionally) register.
// Returns the bitmap object id (0 = null result: failed decode OR the
// bounds-only pass, which never allocates per AOSP).
static uint32_t f240_decode_with_options(const std::vector<uint8_t>& bytes,
                                         const std::string& desc,
                                         HeapAllocator* heap, uint32_t opts_id) {
    if (!heap) return 0;
    renderer::DecodedImage decoded;
    if (!renderer::decode_image_bytes(bytes, &decoded,
                                      resources::device_config().density) ||
        decoded.width <= 0 || decoded.height <= 0 || decoded.rgba.empty()) {
        std::cerr << "[BITMAP-FACTORY] decode FAILED (" << desc << "): "
                  << decoded.error << std::endl;
        // AOSP still records best-effort out* (0) on failure — nothing to
        // write here; the caller answers null.
        return 0;
    }
    if (opts_id != 0) {
        heap->set_object_int_field(opts_id, "outWidth", decoded.width);
        heap->set_object_int_field(opts_id, "outHeight", decoded.height);
        const std::string mime = f240_mime_of(bytes);
        if (!mime.empty()) heap->set_object_string_field(opts_id, "outMimeType", mime);
    }
    // Bounds-only pass: header consumed, NO bitmap allocation (AOSP law —
    // decodeStream with inJustDecodeBounds answers null).
    if (opts_id != 0) {
        int32_t bounds_only = 0;
        heap->get_object_int_field(opts_id, "inJustDecodeBounds", bounds_only);
        if (bounds_only) {
            std::cerr << "[BITMAP-FACTORY] bounds-only " << desc << " -> "
                      << decoded.width << "x" << decoded.height
                      << " (null per AOSP inJustDecodeBounds)" << std::endl;
            return 0;
        }
    }
    // Full decode — honor inSampleSize (AOSP: (dim + s - 1) / s).
    int32_t sample = 1;
    if (opts_id != 0) heap->get_object_int_field(opts_id, "inSampleSize", sample);
    if (sample < 1) sample = 1;
    if (sample > 1) {
        const int dw = (decoded.width + sample - 1) / sample;
        const int dh = (decoded.height + sample - 1) / sample;
        StoredBitmap full;
        full.width = decoded.width;
        full.height = decoded.height;
        full.rgba = std::move(decoded.rgba);
        full.has_pixels = true;
        full.source_desc = desc;
        std::vector<uint8_t> out;
        resample_nearest(full, dw, dh, out);
        const uint32_t obj = heap->allocate("Landroid/graphics/Bitmap;");
        BitmapStore::instance().store(obj, dw, dh, std::move(out),
                                      desc + "#sample" + std::to_string(sample));
        std::cerr << "[BITMAP-FACTORY] decoded " << desc << " -> Bitmap obj="
                  << obj << " (" << dw << "x" << dh << ", inSampleSize="
                  << sample << ")" << std::endl;
        return obj;
    }
    const uint32_t obj = heap->allocate("Landroid/graphics/Bitmap;");
    BitmapStore::instance().store(obj, decoded.width, decoded.height,
                                  std::move(decoded.rgba), desc);
    std::cerr << "[BITMAP-FACTORY] decoded " << desc << " -> Bitmap obj=" << obj
              << " (" << decoded.width << "x" << decoded.height << ")"
              << std::endl;
    return obj;
}

static void resample_nearest(const StoredBitmap& src, int dw, int dh,
                             std::vector<uint8_t>& out) {
    out.assign((size_t)dw * dh * 4, 0);
    for (int y = 0; y < dh; y++) {
        const int sy = std::min(src.height - 1, (y * src.height) / dh);
        for (int x = 0; x < dw; x++) {
            const int sx = std::min(src.width - 1, (x * src.width) / dw);
            const uint8_t* p = &src.rgba[((size_t)sy * src.width + sx) * 4];
            uint8_t* q = &out[((size_t)y * dw + x) * 4];
            q[0] = p[0]; q[1] = p[1]; q[2] = p[2]; q[3] = p[3];
        }
    }
}

CallResult BitmapShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    

    // ── BitmapFactory statics ────────────────────────────────────────────
    if (cls.find("BitmapFactory;") != std::string::npos) {
        if (m == "decodeResource" || m == "decodeResourceStream") {
            // decodeResource(Resources res, int id[, Options opts]) — the
            // resid is argument index 1 (Resources occupies slot 0).
            const uint32_t resid = (uint32_t)ctx.arg_as_int(1, 0);
            if (resid == 0) return CallResult::handled_null();
            std::vector<uint8_t> bytes;
            std::string path;
            uint16_t density = 0;
            if (drawable_bytes_resolver() &&
                drawable_bytes_resolver()(resid, bytes, path, density)) {
                // F-NEW-240: decodeResource(res, id[, opts]) — opts at slot 2.
                const uint32_t bmp = f240_decode_with_options(
                    bytes, path, heap_, ctx.arg_as_object(2, 0));
                if (bmp == 0) return CallResult::handled_null();
                return CallResult::handled_object(bmp, "Landroid/graphics/Bitmap;");
            }
            std::cerr << "[BITMAP-FACTORY] decodeResource resid=0x" << std::hex
                      << resid << std::dec
                      << " unresolved (no resolver/unmatched entry) -> null"
                      << std::endl;
            return CallResult::handled_null();
        }
        if (m == "decodeByteArray") {
            // decodeByteArray(byte[] data, int offset, int length[, Options])
            const uint32_t arr = ctx.arg_as_object(0, 0);
            const int off = ctx.arg_as_int(1, 0);
            const int len = ctx.arg_as_int(2, 0);
            if (arr == 0 || len <= 0 || !heap_) return CallResult::handled_null();
            int32_t arr_len = 0;
            heap_->get_object_array_length(arr, arr_len);
            std::vector<uint8_t> bytes;
            bytes.reserve((size_t)len);
            bool readable = true;
            for (int i = 0; i < len; i++) {
                int32_t v = 0;
                if (heap_->get_object_int_field(arr, "array[" + std::to_string(off + i) + "]", v))
                    bytes.push_back((uint8_t)v);
                else { readable = false; break; }
            }
            if (!readable || bytes.size() != (size_t)len) {
                std::cerr << "[BITMAP-FACTORY] decodeByteArray byte[] unreadable (obj="
                          << arr << ") -> null" << std::endl;
                return CallResult::handled_null();
            }
            // F-NEW-240: decodeByteArray(data, off, len[, opts]) — opts slot 3.
            const uint32_t bmp = f240_decode_with_options(
                bytes, "decodeByteArray", heap_, ctx.arg_as_object(3, 0));
            if (bmp == 0) return CallResult::handled_null();
            return CallResult::handled_object(bmp, "Landroid/graphics/Bitmap;");
        }
        if (m == "decodeFile") {
            const std::string path = ctx.arg_as_string(0, "");
            if (path.empty()) return CallResult::handled_null();
            // LOADING-CAMPAIGN (ST-5 FIX): the ONE path-law translation —
            // Android logical paths (/data/…, /storage/emulated/0/…, /data/
            // user/0/… alias) map to the sandbox backing; DENIED absolute
            // host paths answer the AOSP contract (null + loud diagnostic,
            // never a host read). Previously this opened the raw string as
            // a HOST path (the two external-storage spellings broke here).
            Storage::PathResolution pr = Storage::resolve_android_path(path);
            if (!pr.allowed) {
                std::cerr << "[BITMAP-FACTORY] decodeFile DENIED (outside app"
                             " namespace): " << path << std::endl;
                return CallResult::handled_null();
            }
            FILE* f = fopen(pr.host_path.string().c_str(), "rb");
            if (!f) {
                std::cerr << "[BITMAP-FACTORY] decodeFile open FAILED: "
                          << pr.host_path.string() << " (logical " << path
                          << ")" << std::endl;
                return CallResult::handled_null();
            }
            std::vector<uint8_t> bytes;
            uint8_t buf[8192];
            size_t n;
            while ((n = fread(buf, 1, sizeof buf, f)) > 0)
                bytes.insert(bytes.end(), buf, buf + n);
            fclose(f);
            // F-NEW-240: decodeFile(path[, opts]) — opts slot 1.
            const uint32_t bmp = f240_decode_with_options(
                bytes, path, heap_, ctx.arg_as_object(1, 0));
            if (bmp == 0) return CallResult::handled_null();
            return CallResult::handled_object(bmp, "Landroid/graphics/Bitmap;");
        }
        if (m == "decodeStream") {
            // LOADING-CAMPAIGN (R-10 FIX): AOSP decodeStream is the canonical
            // asset/network→bitmap path. The engine-registered resolver
            // drains the stream object's REAL bytes (asset / sandbox file /
            // AFD-backed sources through open_assets_); a failed decode or
            // an unresolvable stream answers null LOUDLY (AOSP: null only
            // for non-image data — never for "stream type unsupported").
            const uint32_t stream_id = ctx.arg_as_object(0, 0);
            if (stream_id == 0) return CallResult::handled_null();
            if (!stream_bytes_resolver()) {
                std::cerr << "[BITMAP-FACTORY] decodeStream: no stream-bytes"
                             " resolver registered — EXPLICIT-UNSUPPORTED -> null"
                          << std::endl;
                return CallResult::handled_null();
            }
            std::vector<uint8_t> bytes;
            std::string source_desc;
            if (!stream_bytes_resolver()(stream_id, bytes, source_desc) ||
                bytes.empty()) {
                std::cerr << "[BITMAP-FACTORY] decodeStream: stream o"
                          << stream_id << " yielded no bytes (honest null)"
                          << std::endl;
                return CallResult::handled_null();
            }
            // F-NEW-240: decodeStream(stream, rect[, opts]) — opts slot 2.
            // The bounds-only pass fills outWidth/outHeight/outMimeType and
            // answers null WITHOUT allocating (AOSP inJustDecodeBounds law).
            const uint32_t bmp = f240_decode_with_options(
                bytes, "decodeStream:" + source_desc, heap_,
                ctx.arg_as_object(2, 0));
            if (bmp == 0) return CallResult::handled_null();
            return CallResult::handled_object(bmp, "Landroid/graphics/Bitmap;");
        }
        return CallResult::not_handled();
    }

    // ── Bitmap instance methods + statics ───────────────────────────────
    BitmapStore& store = BitmapStore::instance();
    const uint32_t recv = ctx.receiver_id;

    if (m == "createBitmap" || m == "createScaledBitmap") {
        {
            static thread_local uint64_t cb_dbg = 0;
            static thread_local const bool cb_dbg_on =
                std::getenv("MINIANDROID_S109_BITMAP") != nullptr;
            if (cb_dbg_on && cb_dbg < 12) {
                ++cb_dbg;
                std::cerr << "[S109-BITMAP] " << m
                          << " static=" << (ctx.has_receiver ? 0 : 1)
                          << " argc=" << ctx.args.size();
                for (size_t i = 0; i < ctx.args.size() && i < 4; ++i) {
                    std::cerr << " a" << i << "k" << (int)ctx.args[i].kind;
                    if (ctx.args[i].kind == CallContext::Arg::Kind::INT)
                        std::cerr << "=" << ctx.args[i].int_val;
                    if (ctx.args[i].kind == CallContext::Arg::Kind::OBJECT)
                        std::cerr << "=o" << ctx.args[i].object_id;
                }
                std::cerr << std::endl;
            }
        }
        if (m == "createScaledBitmap") {
            // (Bitmap src, int dw, int dh, boolean filter) — static.
            const uint32_t src = ctx.arg_as_object(0, 0);
            const int dw = ctx.arg_as_int(1, 0);
            const int dh = ctx.arg_as_int(2, 0);
            const bool filter = ctx.arg_as_bool(3, false);
            const StoredBitmap* sb = store.get(src);
            if (!sb || dw <= 0 || dh <= 0 || !heap_)
                return CallResult::handled_null();
            if (filter) {
                std::cerr << "[BITMAP] createScaledBitmap filter=true: bilinear "
                          << "resample not implemented — nearest used (registered)"
                          << std::endl;
            }
            std::vector<uint8_t> out;
            resample_nearest(*sb, dw, dh, out);
            const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
            store.store(obj, dw, dh, std::move(out),
                        "createScaledBitmap(" + sb->source_desc + ")");
            return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
        }
        // createBitmap overloads:
        //  (int w, int h, Config)                       args=3 (Config obj|int)
        //  (int[] colors, int w, int h, Config)         args=4+
        //  (Bitmap src [, int x, int y, int w, int h])  args=1 | 5+
        //  (Bitmap src, int x, int y, int w, int h, Matrix m, boolean filter)
        if (ctx.args.size() >= 3 && ctx.args[0].kind == CallContext::Arg::Kind::INT &&
            ctx.args[1].kind == CallContext::Arg::Kind::INT) {
            const int w = ctx.arg_as_int(0, 0);
            const int h = ctx.arg_as_int(1, 0);
            if (w <= 0 || h <= 0 || !heap_) return CallResult::handled_null();
            const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
            store.create(obj, w, h, "createBitmap(w,h,config)");
            return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
        }
        if (ctx.args.size() >= 4 && ctx.args[0].kind == CallContext::Arg::Kind::OBJECT) {
            // int[] colors variant: (colors, w, h, config) — colors[0] INT kind.
            if (ctx.args[0].kind == CallContext::Arg::Kind::OBJECT &&
                ctx.args[1].kind == CallContext::Arg::Kind::INT) {
                const uint32_t colors = ctx.arg_as_object(0, 0);
                const int w = ctx.arg_as_int(1, 0);
                const int h = ctx.arg_as_int(2, 0);
                const StoredBitmap* probe = store.get(colors);
                if (probe) {
                    // colors is a Bitmap? No — colors is int[]; store lookup
                    // returning data would be a hash collision — treat as array.
                }
                if (colors != 0 && heap_ && w > 0 && h > 0) {
                    std::vector<uint8_t> rgba((size_t)w * h * 4, 0);
                    int32_t arr_len = 0;
                    heap_->get_object_array_length(colors, arr_len);
                    const int need = w * h;
                    int filled = 0;
                    for (int i = 0; i < need && i < arr_len; i++) {
                        int32_t argb = 0;
                        if (!heap_->get_object_int_field(colors, "array[" + std::to_string(i) + "]", argb))
                            break;
                        rgba[(size_t)i * 4 + 0] = (uint8_t)((argb >> 16) & 0xFF);
                        rgba[(size_t)i * 4 + 1] = (uint8_t)((argb >> 8) & 0xFF);
                        rgba[(size_t)i * 4 + 2] = (uint8_t)(argb & 0xFF);
                        rgba[(size_t)i * 4 + 3] = (uint8_t)((argb >> 24) & 0xFF);
                        filled++;
                    }
                    if (filled == need) {
                        const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
                        store.store(obj, w, h, std::move(rgba), "createBitmap(colors,w,h)");
                        return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
                    }
                }
            }
            // (Bitmap src, x, y, w, h) crop variant.
            const uint32_t src = ctx.arg_as_object(0, 0);
            const StoredBitmap* sb = store.get(src);
            if (sb && ctx.args.size() >= 5) {
                const int x = ctx.arg_as_int(1, 0);
                const int y = ctx.arg_as_int(2, 0);
                const int w = ctx.arg_as_int(3, 0);
                const int h = ctx.arg_as_int(4, 0);
                if (w <= 0 || h <= 0 || x < 0 || y < 0 || x + w > sb->width ||
                    y + h > sb->height) {
                    std::cerr << "[BITMAP] createBitmap crop out of bounds ("
                              << x << "," << y << " " << w << "x" << h
                              << " of " << sb->width << "x" << sb->height
                              << ") -> IllegalArgumentException law" << std::endl;
                    return CallResult::handled_null();  // AOSP throws; null keeps app alive under exception-honesty
                }
                std::vector<uint8_t> rgba((size_t)w * h * 4, 0);
                for (int row = 0; row < h; row++) {
                    const uint8_t* p = &sb->rgba[((size_t)(y + row) * sb->width + x) * 4];
                    std::copy(p, p + (size_t)w * 4, &rgba[(size_t)row * w * 4]);
                }
                const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
                store.store(obj, w, h, std::move(rgba), "createBitmap(src,x,y,w,h)");
                return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
            }
            if (sb) {
                // (Bitmap src) copy variant.
                const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
                store.store(obj, sb->width, sb->height, sb->rgba,
                            "createBitmap(src copy)");
                return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
            }
        }
        return CallResult::handled_null();
    }

    if (m == "getWidth") {
        const StoredBitmap* sb = store.get(recv);
        return CallResult::handled_int(sb ? sb->width : 0);
    }
    if (m == "getHeight") {
        const StoredBitmap* sb = store.get(recv);
        return CallResult::handled_int(sb ? sb->height : 0);
    }
    if (m == "getRowBytes") {
        const StoredBitmap* sb = store.get(recv);
        return CallResult::handled_int(sb ? sb->width * 4 : 0);
    }
    if (m == "getByteCount") {
        const StoredBitmap* sb = store.get(recv);
        return CallResult::handled_int(sb ? sb->width * sb->height * 4 : 0);
    }
    if (m == "getConfig") {
        // Bitmap$Config statics alias to ints (engine law at
        // dalvik_engine.cpp Bitmap$Config table): ALPHA_8=0, RGB_565=1,
        // ARGB_4444=2, ARGB_8888=3. The runtime decodes to ARGB_8888.
        return CallResult::handled_int(3);
    }
    if (m == "eraseColor") {
        StoredBitmap* sb = store.get_mut(recv);
        if (sb) {
            const uint32_t argb = (uint32_t)ctx.arg_as_int(0, 0xFF000000);
            const uint8_t r = (argb >> 16) & 0xFF, g = (argb >> 8) & 0xFF,
                          b = argb & 0xFF, a = (argb >> 24) & 0xFF;
            for (size_t i = 0; i + 3 < sb->rgba.size(); i += 4) {
                sb->rgba[i] = r; sb->rgba[i + 1] = g;
                sb->rgba[i + 2] = b; sb->rgba[i + 3] = a;
            }
        }
        return CallResult::handled_void();
    }
    if (m == "getPixel") {
        const StoredBitmap* sb = store.get(recv);
        if (!sb) return CallResult::handled_int(0);
        const int x = ctx.arg_as_int(0, 0), y = ctx.arg_as_int(1, 0);
        if (x < 0 || y < 0 || x >= sb->width || y >= sb->height)
            return CallResult::handled_int(0);
        const uint8_t* p = &sb->rgba[((size_t)y * sb->width + x) * 4];
        const uint32_t argb = ((uint32_t)p[3] << 24) | ((uint32_t)p[0] << 16) |
                              ((uint32_t)p[1] << 8) | p[2];
        return CallResult::handled_int((int32_t)argb);
    }
    if (m == "setPixel") {
        StoredBitmap* sb = store.get_mut(recv);
        if (sb) {
            const int x = ctx.arg_as_int(0, 0), y = ctx.arg_as_int(1, 0);
            const uint32_t argb = (uint32_t)ctx.arg_as_int(2, 0xFF000000);
            if (x >= 0 && y >= 0 && x < sb->width && y < sb->height) {
                uint8_t* p = &sb->rgba[((size_t)y * sb->width + x) * 4];
                p[0] = (argb >> 16) & 0xFF; p[1] = (argb >> 8) & 0xFF;
                p[2] = argb & 0xFF;         p[3] = (argb >> 24) & 0xFF;
            }
        }
        return CallResult::handled_void();
    }
    if (m == "getPixels") {
        // getPixels(int[] pixels, int offset, int stride, int x, int y, int w, int h)
        const uint32_t dst = ctx.arg_as_object(0, 0);
        const int off = ctx.arg_as_int(1, 0);
        const int stride = ctx.arg_as_int(2, 0);
        const int x = ctx.arg_as_int(3, 0), y = ctx.arg_as_int(4, 0);
        const int w = ctx.arg_as_int(5, 0), h = ctx.arg_as_int(6, 0);
        const StoredBitmap* sb = store.get(recv);
        if (!sb || dst == 0 || !heap_) return CallResult::handled_void();
        for (int row = 0; row < h; row++) {
            for (int col = 0; col < w; col++) {
                const int sx = x + col, sy = y + row;
                uint32_t argb = 0;
                if (sx >= 0 && sy >= 0 && sx < sb->width && sy < sb->height) {
                    const uint8_t* p = &sb->rgba[((size_t)sy * sb->width + sx) * 4];
                    argb = ((uint32_t)p[3] << 24) | ((uint32_t)p[0] << 16) |
                           ((uint32_t)p[1] << 8) | p[2];
                }
                const int idx = off + row * stride + col;
                heap_->set_object_int_field(dst, "array[" + std::to_string(idx) + "]",
                                           (int32_t)argb);
            }
        }
        return CallResult::handled_void();
    }
    if (m == "recycle") {
        return CallResult::handled_void();   // deterministic GC: no-op
    }
    if (m == "isRecycled") {
        return CallResult::handled_bool(false);
    }
    if (m == "compress") {
        std::cerr << "[BITMAP] compress(): encoder not wired — "
                  << "EXPLICIT-UNSUPPORTED -> false (AOSP failure contract)"
                  << std::endl;
        return CallResult::handled_bool(false);
    }
    if (m == "sameAs") {
        const StoredBitmap* a = store.get(recv);
        const StoredBitmap* b = store.get(ctx.arg_as_object(0, 0));
        if (!a || !b) return CallResult::handled_bool(false);
        return CallResult::handled_bool(a->width == b->width &&
                                        a->height == b->height &&
                                        a->rgba == b->rgba);
    }
    if (m == "isMutable" || m == "hasAlpha" || m == "isPremultiplied") {
        return CallResult::handled_bool(m == "hasAlpha" || m == "isMutable");
    }
    if (m == "getGenerationId") {
        // No render-node invalidation tracking yet — constant is honest here.
        return CallResult::handled_int(1);
    }
    if (m == "<init>") {
        return CallResult::handled_void();
    }
    return CallResult::not_handled();
}

} } // namespace miniandroid::framework
