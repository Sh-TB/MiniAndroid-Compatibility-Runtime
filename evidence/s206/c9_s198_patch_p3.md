**S198 rebased phase-3 patch part 3/4** (base `0979678e`; verified `git apply --check` APPLIES_CLEAN on a pristine `0979678e` worktree; the applied result is byte-identical to the in-container-verified tree that produced binary `4d832c255bed513c`: c9_phase3_laws_test **46/46**, density 36/36, zip 42/42, §5/§6 harness **48/49** with ONLY the P-NEW-5 size-word law failing, resourceval **30/31** with ONLY law 29 failing)

```diff
diff --git a/miniandroid/src/framework/android_shadows.h b/miniandroid/src/framework/android_shadows.h
index a07d13c6..330c57f8 100755
--- a/miniandroid/src/framework/android_shadows.h
+++ b/miniandroid/src/framework/android_shadows.h
@@ -1676,6 +1676,13 @@ public:
             // activated=false.
             int state_window_focused = -1;
             int state_activated = -1;
+            // C9-18 (CODER 9): the remaining standard View states. Framework
+            // selectors (btn_default family) declare state_focused / 
+            // state_hovered items BEFORE the fallback item — without these
+            // tri-states the focused item parsed as a wildcard and
+            // first-match picked the WRONG variant for the default state.
+            int state_focused = -1;
+            int state_hovered = -1;
             uint32_t color = 0;           // android:color or shape solid
             bool has_color = false;
             // S127: android:color as a REFERENCE (@color/…, the aapt2
@@ -1685,6 +1692,11 @@ public:
             // the ARSC router (resolve_framework_file_color).
             uint32_t color_ref_id = 0;
             std::string drawable_path;    // android:drawable file (may be empty)
+            // C9-19 (CODER 9): android:drawable as a COMPILED reference —
+            // aapt2 stores @drawable/x as Res_value REFERENCE (data = resid);
+            // the raw "@drawable/x" string only survives for string forms.
+            // The engine dereferences this id through the ARSC resolver.
+            uint32_t drawable_ref_id = 0;
         };
         std::vector<BgStateItem> bg_state_items;
         // CAMPAIGN 013 B1: dialog window item/button routing. When
diff --git a/miniandroid/src/framework/bitmap_shadow.cpp b/miniandroid/src/framework/bitmap_shadow.cpp
index c11a4a78..bbc50582 100644
--- a/miniandroid/src/framework/bitmap_shadow.cpp
+++ b/miniandroid/src/framework/bitmap_shadow.cpp
@@ -260,6 +260,10 @@ static uint32_t f240_decode_with_options(const std::vector<uint8_t>& bytes,
     int32_t in_density = 0, in_target_density = 0, in_sample = 1;
     int32_t in_scaled = 1;  // AOSP Java field default: inScaled = true
     bool in_scaled_present = false;
+    // ── C9-4/5/6 (CODER 9): the remaining Options contract ────────────
+    int32_t in_preferred = 3;   // inPreferredConfig — AOSP default ARGB_8888
+    int32_t in_mutable = 0;     // inMutable — AOSP default false
+    int32_t in_premult = 1;     // inPremultiplied — AOSP default TRUE
     if (resource_density >= 0) {
         // decodeResourceStream law — TypedValue.density → opts.inDensity.
         constexpr int32_t kDensityAny = 0xFFFE;      // TypedValue.DENSITY_ANY
@@ -282,6 +286,12 @@ static uint32_t f240_decode_with_options(const std::vector<uint8_t>& bytes,
         }
         in_scaled_present = heap->get_object_int_field(opts_id, "inScaled", in_scaled);
         heap->get_object_int_field(opts_id, "inSampleSize", in_sample);
+        // C9-4/5/6: honor the rest of the Options contract (defaults above
+        // apply when the app never set the field — AOSP field-initializer
+        // law, not silent drops).
+        heap->get_object_int_field(opts_id, "inPreferredConfig", in_preferred);
+        heap->get_object_int_field(opts_id, "inMutable", in_mutable);
+        heap->get_object_int_field(opts_id, "inPremultiplied", in_premult);
         // AOSP decodeResourceStream MUTATES the app's Options (the seeded
         // values are app-visible afterwards).
         if (in_density != 0)
@@ -359,6 +369,29 @@ static uint32_t f240_decode_with_options(const std::vector<uint8_t>& bytes,
         sb->sample_size = law.sampled_width != decoded.width || law.sampled_height != decoded.height
                               ? law_in.in_sample_size : 1;
         sb->density_scaled = law.density_scaled;
+        // ── C9-4/5/6: record + apply the real Options contract ──────────
+        sb->config = (in_preferred == 0 || in_preferred == 1 || in_preferred == 2)
+                         ? in_preferred : 3;
+        sb->mutable_bitmap = in_mutable != 0;
+        sb->premultiplied = in_premult != 0;
+        if (sb->config != 3) {
+            const std::string cfg_name =
+                bitmap_preferred_config_law(sb->config, sb->rgba);
+            std::cerr << "[BITMAP-FACTORY] C9-4 inPreferredConfig honored: "
+                      << desc << " -> " << cfg_name << std::endl;
+        }
+        // ── C9-23: byte-derived cache identity (Glide/Coil substrate) ──
+        BitmapCacheIdentityInput id_in;
+        id_in.src_bytes = bytes.data();
+        id_in.src_len = bytes.size();
+        id_in.source_desc = desc;
+        id_in.source_density = sb->source_density;
+        id_in.target_density = sb->target_density;
+        id_in.sample_size = sb->sample_size;
+        id_in.config = sb->config;
+        id_in.density_scaled = sb->density_scaled;
+        std::cerr << "[BITMAP-FACTORY] C9-23 identity "
+                  << bitmap_cache_identity_law(id_in) << std::endl;
     }
     // CONT-65 F-NEW-355: keep the original container bytes for animated
     // GIFs so the render walk can decode the full frame timeline
@@ -398,6 +431,122 @@ static void resample_nearest(const StoredBitmap& src, int dw, int dh,
     }
 }
 
+// ── C9-4 (CODER 9) — inPreferredConfig conversion law ──────────────────
+// See bitmap_shadow.h for the source-backed contract. The store is RGBA;
+// the law rewrites the buffer in place and answers the canonical name.
+std::string bitmap_preferred_config_law(int32_t in_preferred_config,
+                                        std::vector<uint8_t>& rgba) {
+    switch (in_preferred_config) {
+        case 0: {  // ALPHA_8 — RGB forced 0, alpha preserved
+            for (size_t i = 0; i + 3 < rgba.size(); i += 4) {
+                rgba[i] = 0; rgba[i + 1] = 0; rgba[i + 2] = 0;
+            }
+            return "ALPHA_8";
+        }
+        case 1: {  // RGB_565 — alpha dropped, 565-quantized (REAL loss)
+            for (size_t i = 0; i + 3 < rgba.size(); i += 4) {
+                const uint8_t r5 = (uint8_t)(rgba[i] >> 3);
+                const uint8_t g6 = (uint8_t)(rgba[i + 1] >> 2);
+                const uint8_t b5 = (uint8_t)(rgba[i + 2] >> 3);
+                rgba[i]     = (uint8_t)((r5 * 255 + 15) / 31);
+                rgba[i + 1] = (uint8_t)((g6 * 255 + 31) / 63);
+                rgba[i + 2] = (uint8_t)((b5 * 255 + 15) / 31);
+                rgba[i + 3] = 0xFF;
+            }
+            return "RGB_565";
+        }
+        case 2: {  // ARGB_4444 — deprecated, 444-quantized
+            for (size_t i = 0; i + 3 < rgba.size(); i += 4) {
+                rgba[i]     = (uint8_t)(rgba[i] & 0xF0);
+                rgba[i + 1] = (uint8_t)(rgba[i + 1] & 0xF0);
+                rgba[i + 2] = (uint8_t)(rgba[i + 2] & 0xF0);
+                rgba[i + 3] = (uint8_t)(rgba[i + 3] & 0xF0);
+            }
+            return "ARGB_4444";
+        }
+        default:   // ARGB_8888 / unknown → AOSP default passthrough
+            return "ARGB_8888";
+    }
+}
+
+// ── C9-9 (CODER 9) — bilinear resample law (Skia kLinear sampling) ─────
+// Sample point = ((x + 0.5) * sw / dw) - 0.5, clamped to [0, sw-1]; the
+// 4 surrounding texels weight-blended, rounded to nearest u8. Identity
+// scale degenerates to integer coordinates → byte-exact passthrough.
+void resample_bilinear(const StoredBitmap& src, int dw, int dh,
+                       std::vector<uint8_t>& out) {
+    out.assign((size_t)dw * dh * 4, 0);
+    if (dw <= 0 || dh <= 0 || src.width <= 0 || src.height <= 0) return;
+    const float xr = (float)src.width / (float)dw;
+    const float yr = (float)src.height / (float)dh;
+    for (int y = 0; y < dh; y++) {
+        float fy = ((float)y + 0.5f) * yr - 0.5f;
+        fy = std::max(0.0f, std::min((float)(src.height - 1), fy));
+        const int y0 = (int)fy;
+        const int y1 = std::min(src.height - 1, y0 + 1);
+        const float ty = fy - (float)y0;
+        for (int x = 0; x < dw; x++) {
+            float fx = ((float)x + 0.5f) * xr - 0.5f;
+            fx = std::max(0.0f, std::min((float)(src.width - 1), fx));
+            const int x0 = (int)fx;
+            const int x1 = std::min(src.width - 1, x0 + 1);
+            const float tx = fx - (float)x0;
+            const uint8_t* p00 = &src.rgba[((size_t)y0 * src.width + x0) * 4];
+            const uint8_t* p10 = &src.rgba[((size_t)y0 * src.width + x1) * 4];
+            const uint8_t* p01 = &src.rgba[((size_t)y1 * src.width + x0) * 4];
+            const uint8_t* p11 = &src.rgba[((size_t)y1 * src.width + x1) * 4];
+            uint8_t* q = &out[((size_t)y * dw + x) * 4];
+            for (int c = 0; c < 4; ++c) {
+                const float v = (float)p00[c] * (1 - tx) * (1 - ty) +
+                                (float)p10[c] * tx * (1 - ty) +
+                                (float)p01[c] * (1 - tx) * ty +
+                                (float)p11[c] * tx * ty;
+                q[c] = (uint8_t)std::lround(v);
+            }
+        }
+    }
+}
+
+// ── C9-23 (CODER 9) — cache-identity law implementation ──────────────
+std::string bitmap_cache_identity_law(const BitmapCacheIdentityInput& in) {
+    auto fnv1a64 = [](const uint8_t* data, size_t len, uint64_t h) {
+        for (size_t i = 0; i < len; ++i) {
+            h ^= (uint64_t)data[i];
+            h *= 0x100000001b3ull;
+        }
+        return h;
+    };
+    uint64_t h = 0xcbf29ce484222325ull;
+    if (in.src_bytes && in.src_len)
+        h = fnv1a64(in.src_bytes, in.src_len, h);
+    h = fnv1a64((const uint8_t*)in.source_desc.data(),
+                in.source_desc.size(), h);
+    const uint8_t tail[] = {
+        (uint8_t)(in.source_density & 0xFF),
+        (uint8_t)(in.source_density >> 8),
+        (uint8_t)(in.target_density & 0xFF),
+        (uint8_t)(in.target_density >> 8),
+        (uint8_t)(in.sample_size & 0xFF),
+        (uint8_t)((in.sample_size >> 8) & 0xFF),
+        (uint8_t)((in.sample_size >> 16) & 0xFF),
+        (uint8_t)((in.sample_size >> 24) & 0xFF),
+        (uint8_t)(in.config & 0xFF),
+        (uint8_t)(in.density_scaled ? 1 : 0),
+    };
+    h = fnv1a64(tail, sizeof(tail), h);
+    char hex[32];
+    std::snprintf(hex, sizeof(hex), "%016llx", (unsigned long long)h);
+    std::string id = "c9:";
+    id += hex;
+    id += ":" + in.source_desc;
+    id += ":d" + std::to_string(in.source_density) + "->" +
+          std::to_string(in.target_density);
+    id += ":s" + std::to_string(in.sample_size);
+    id += ":c" + std::to_string(in.config);
+    if (in.density_scaled) id += ":scaled";
+    return id;
+}
+
 CallResult BitmapShadow::dispatch(const CallContext& ctx) {
     const std::string& cls = ctx.class_name;
     const std::string& m = ctx.method;
@@ -564,16 +713,37 @@ CallResult BitmapShadow::dispatch(const CallContext& ctx) {
             const StoredBitmap* sb = store.get(src);
             if (!sb || dw <= 0 || dh <= 0 || !heap_)
                 return CallResult::handled_null();
+            // ── C9-9 (CODER 9): filter=true now performs the REAL bilinear
+            // resample (Skia kLinear half-pixel-center law); filter=false
+            // keeps the nearest-neighbour law. filter=true on a RECYCLED
+            // source has no pixels to sample — AOSP throws; answer null
+            // loudly (recorded divergence, same spirit as decode refusal).
+            std::vector<uint8_t> out;
             if (filter) {
-                std::cerr << "[BITMAP] createScaledBitmap filter=true: bilinear "
-                          << "resample not implemented — nearest used (registered)"
-                          << std::endl;
+                if (sb->recycled) {
+                    std::cerr << "[BITMAP] createScaledBitmap(filter=true) "
+                              << "on RECYCLED source — null (no pixels to "
+                              << "sample)" << std::endl;
+                    return CallResult::handled_null();
+                }
+                resample_bilinear(*sb, dw, dh, out);
+            } else {
+                resample_nearest(*sb, dw, dh, out);
             }
-            std::vector<uint8_t> out;
-            resample_nearest(*sb, dw, dh, out);
             const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
             store.store(obj, dw, dh, std::move(out),
                         "createScaledBitmap(" + sb->source_desc + ")");
+            if (auto* nb = store.get_mut(obj)) {
+                // AOSP createScaledBitmap: result inherits source mutability
+                // and premultiplied state; the config is preserved.
+                nb->config = sb->config;
+                nb->mutable_bitmap = sb->mutable_bitmap;
+                nb->premultiplied = sb->premultiplied;
+            }
+            std::cerr << "[BITMAP] createScaledBitmap " << sb->width << "x"
+                      << sb->height << " -> " << dw << "x" << dh
+                      << " filter=" << (filter ? "bilinear(C9-9)" : "nearest")
+                      << std::endl;
             return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
         }
         // createBitmap overloads:
@@ -586,8 +756,25 @@ CallResult BitmapShadow::dispatch(const CallContext& ctx) {
             const int w = ctx.arg_as_int(0, 0);
             const int h = ctx.arg_as_int(1, 0);
             if (w <= 0 || h <= 0 || !heap_) return CallResult::handled_null();
+            // ── C9-4/C9-5 (CODER 9): createBitmap(w, h, Config) — the
+            // requested config is REAL (ALPHA_8/RGB_565/ARGB_4444 honored
+            // with the same conversion law as decode) and the result is
+            // MUTABLE (AOSP Bitmap.createBitmap(w,h,config) contract).
+            int32_t cfg = ctx.arg_as_int(2, 3);
+            if (cfg != 0 && cfg != 1 && cfg != 2) cfg = 3;
             const uint32_t obj = heap_->allocate("Landroid/graphics/Bitmap;");
             store.create(obj, w, h, "createBitmap(w,h,config)");
+            if (auto* nb = store.get_mut(obj)) {
+                nb->config = cfg;
+                nb->mutable_bitmap = true;
+                if (cfg != 3) {
+                    const std::string name =
+                        bitmap_preferred_config_law(cfg, nb->rgba);
+                    std::cerr << "[BITMAP] createBitmap config honored: "
+                              << name << " (" << w << "x" << h << ")"
+                              << std::endl;
+                }
+            }
             return CallResult::handled_object(obj, "Landroid/graphics/Bitmap;");
         }
         // F-NEW-495b (CONT-157): androidx passes a DELIBERATE NULL dm —
@@ -855,10 +1042,12 @@ CallResult BitmapShadow::dispatch(const CallContext& ctx) {
         return CallResult::handled_int(sb ? sb->width * sb->height * 4 : 0);
     }
     if (m == "getConfig") {
+        // ── C9-4 (CODER 9): answer the REAL stored config, never a constant.
         // Bitmap$Config statics alias to ints (engine law at
         // dalvik_engine.cpp Bitmap$Config table): ALPHA_8=0, RGB_565=1,
-        // ARGB_4444=2, ARGB_8888=3. The runtime decodes to ARGB_8888.
-        return CallResult::handled_int(3);
+        // ARGB_4444=2, ARGB_8888=3.
+        const StoredBitmap* sb = store.get(recv);
+        return CallResult::handled_int(sb ? sb->config : 3);
     }
     if (m == "eraseColor") {
         StoredBitmap* sb = store.get_mut(recv);
@@ -876,17 +1065,49 @@ CallResult BitmapShadow::dispatch(const CallContext& ctx) {
     if (m == "getPixel") {
         const StoredBitmap* sb = store.get(recv);
         if (!sb) return CallResult::handled_int(0);
+        // ── C9-8 (CODER 9): recycled bitmaps serve no pixels (AOSP
+        // Bitmap.getPixel throws IllegalStateException once recycled; the
+        // engine answers the failure LOUDLY and deterministically instead
+        // of reading freed storage).
+        if (sb->recycled) {
+            std::cerr << "[BITMAP] getPixel on RECYCLED bitmap "
+                      << sb->source_desc
+                      << " — IllegalStateException contract (0 answered)"
+                      << std::endl;
+            return CallResult::handled_int(0);
+        }
         const int x = ctx.arg_as_int(0, 0), y = ctx.arg_as_int(1, 0);
         if (x < 0 || y < 0 || x >= sb->width || y >= sb->height)
             return CallResult::handled_int(0);
         const uint8_t* p = &sb->rgba[((size_t)y * sb->width + x) * 4];
-        const uint32_t argb = ((uint32_t)p[3] << 24) | ((uint32_t)p[0] << 16) |
-                              ((uint32_t)p[1] << 8) | p[2];
+        uint32_t argb = ((uint32_t)p[3] << 24) | ((uint32_t)p[0] << 16) |
+                        ((uint32_t)p[1] << 8) | p[2];
+        // C9-4: ALPHA_8 getPixel contract — the pixel IS the alpha
+        // ((a<<24), RGB zero — AOSP Bitmap.java ALPHA_8 doc).
+        if (sb->config == 0) argb &= 0xFF000000u;
         return CallResult::handled_int((int32_t)argb);
     }
     if (m == "setPixel") {
         StoredBitmap* sb = store.get_mut(recv);
         if (sb) {
+            // ── C9-8 (CODER 9): recycle + mutability contracts (AOSP
+            // Bitmap.setPixel throws IllegalStateException on recycled and
+            // on immutable bitmaps; the engine logs the violation loudly
+            // and leaves the store unchanged — never a silent fake write).
+            if (sb->recycled) {
+                std::cerr << "[BITMAP] setPixel on RECYCLED bitmap "
+                          << sb->source_desc
+                          << " — IllegalStateException contract (write dropped)"
+                          << std::endl;
+                return CallResult::handled_void();
+            }
+            if (!sb->mutable_bitmap) {
+                std::cerr << "[BITMAP] setPixel on IMMUTABLE bitmap "
+                          << sb->source_desc
+                          << " — IllegalStateException contract (write dropped)"
+                          << std::endl;
+                return CallResult::handled_void();
+            }
             const int x = ctx.arg_as_int(0, 0), y = ctx.arg_as_int(1, 0);
             const uint32_t argb = (uint32_t)ctx.arg_as_int(2, 0xFF000000);
             if (x >= 0 && y >= 0 && x < sb->width && y < sb->height) {
@@ -961,17 +1182,29 @@ CallResult BitmapShadow::dispatch(const CallContext& ctx) {
         return CallResult::handled_void();
     }
     if (m == "recycle") {
-        return CallResult::handled_void();   // deterministic GC: no-op
+        // ── C9-8 (CODER 9): AOSP Bitmap.recycle() — frees the pixel data,
+        // marks the bitmap recycled (idempotent). isRecycled() flips;
+        // pixel access answers the loud IllegalStateException contract.
+        if (StoredBitmap* sb = store.get_mut(recv)) {
+            if (!sb->recycled)
+                std::cerr << "[BITMAP] recycle obj=" << recv << " ("
+                          << sb->source_desc << ") — pixels freed" << std::endl;
+            sb->recycled = true;
+            sb->rgba.clear();
+            sb->rgba.shrink_to_fit();
+            sb->has_pixels = false;
+        }
+        return CallResult::handled_void();
     }
     if (m == "isRecycled") {
-        return CallResult::handled_bool(false);
-    }
-    if (m == "compress") {
-        std::cerr << "[BITMAP] compress(): encoder not wired — "
-                  << "EXPLICIT-UNSUPPORTED -> false (AOSP failure contract)"
-                  << std::endl;
-        return CallResult::handled_bool(false);
+        const StoredBitmap* sb = store.get(recv);
+        return CallResult::handled_bool(sb ? sb->recycled : false);
     }
+    // ── C9-7 (CODER 9): compress DECLINED here — the real PNG encode lives
+    // in the engine bridge (same TU as the ByteArrayOutputStream law it
+    // must write through). Declining keeps the AOSP contract one-homed;
+    // the engine answers FORMAT_PNG with real bytes, other formats with
+    // the loud EXPLICIT-UNSUPPORTED false.
     if (m == "sameAs") {
         const StoredBitmap* a = store.get(recv);
         const StoredBitmap* b = store.get(ctx.arg_as_object(0, 0));
@@ -981,7 +1214,16 @@ CallResult BitmapShadow::dispatch(const CallContext& ctx) {
                                         a->rgba == b->rgba);
     }
     if (m == "isMutable" || m == "hasAlpha" || m == "isPremultiplied") {
-        return CallResult::handled_bool(m == "hasAlpha" || m == "isMutable");
+        // ── C9-5/C9-6 (CODER 9): answer the REAL stored flags. AOSP:
+        // decodes are immutable unless Options.inMutable; the premultiplied
+        // default is TRUE (the old constant false answered the opposite of
+        // the AOSP field initializer). hasAlpha follows the config (RGB_565
+        // is opaque — AOSP Bitmap.hasAlpha doc).
+        const StoredBitmap* sb = store.get(recv);
+        if (!sb) return CallResult::handled_bool(m == "hasAlpha" || m == "isMutable");
+        if (m == "isMutable") return CallResult::handled_bool(sb->mutable_bitmap);
+        if (m == "isPremultiplied") return CallResult::handled_bool(sb->premultiplied);
+        return CallResult::handled_bool(sb->config != 1);   // RGB_565 opaque
     }
     if (m == "getGenerationId") {
         // No render-node invalidation tracking yet — constant is honest here.
diff --git a/miniandroid/src/framework/bitmap_shadow.h b/miniandroid/src/framework/bitmap_shadow.h
index bee8740b..f8f144f4 100644
--- a/miniandroid/src/framework/bitmap_shadow.h
+++ b/miniandroid/src/framework/bitmap_shadow.h
@@ -55,6 +55,14 @@ struct StoredBitmap {
     int32_t source_height = 0;
     int32_t sample_size = 1;          // opts.inSampleSize applied (1 = none)
     bool density_scaled = false;      // density scale actually applied
+    // ── C9-4/5/6 (CODER 9) — decode-law Options contract ──────────────────
+    // Bitmap$Config aliases to ints (engine law: ALPHA_8=0, RGB_565=1,
+    // ARGB_4444=2, ARGB_8888=3). Every decode/creation path records the
+    // REAL config it served; getConfig answers this, never a constant.
+    int32_t config = 3;               // ARGB_8888 default (AOSP Options default)
+    bool mutable_bitmap = false;      // decodes immutable; inMutable=true upgrades (C9-5)
+    bool premultiplied = true;        // AOSP inPremultiplied default TRUE (C9-6)
+    bool recycled = false;            // C9-8: recycle() law flag (frees pixels)
     // CONT-65 F-NEW-355: original container bytes for ANIMATED formats
     // (GIF89a/GIF87a only — stb_image first-frame decode can't recover
     // delays). Populated by decode_and_register on GIF magic; empty for
@@ -172,4 +180,47 @@ struct BitmapFactoryDensityResult {
 BitmapFactoryDensityResult bitmap_factory_density_law(
     const BitmapFactoryDensityInput& in);
 
+// ── C9-4 (CODER 9) — inPreferredConfig conversion law (pure, testable) ────
+// AOSP BitmapFactory native: the decode output pixel format follows
+// Options.inPreferredConfig. The store is RGBA; the law converts the buffer
+// to the requested config and reports the canonical config name:
+//   ALPHA_8 (0): RGB forced 0, alpha preserved (AOSP ALPHA_8 stores only
+//                alpha; getPixel answers (a<<24))
+//   RGB_565 (1): alpha dropped, 565-quantized (REAL precision loss:
+//                r5=r>>3, g6=g>>2, b5=b>>3, re-expanded)
+//   ARGB_4444 (2): 444-quantized (deprecated, same shape as 565 law)
+//   ARGB_8888 (3): passthrough
+// Unknown values keep ARGB_8888 (AOSP null/unknown → default 8888 path).
+std::string bitmap_preferred_config_law(int32_t in_preferred_config,
+                                        std::vector<uint8_t>& rgba);
+
+// ── C9-9 (CODER 9) — bilinear resample law (pure, testable) ─────────────
+// AOSP/Skia kLinear sampling for Bitmap.createScaledBitmap(src, dw, dh,
+// filter=true): sample point = ((x + 0.5) * sw / dw) - 0.5, clamped to
+// [0, sw-1]; the 4 surrounding texels are weight-blended (float, then
+// rounded to nearest u8). Identity scale (dw==sw, dh==sh) answers the
+// source bytes EXACTLY (the law degenerates to integer coordinates).
+void resample_bilinear(const StoredBitmap& src, int dw, int dh,
+                       std::vector<uint8_t>& out);
+
+// ── C9-23 (CODER 9) — cache-identity law (Glide/Coil substrate) ───────
+// The generic image-loader contract: a decode result is identified by
+// (source entry bytes, source desc, selected density pair, sample size,
+// config). Two decodes with the SAME identity MUST answer pixel-identical
+// bitmaps (byte-derived, deterministic — no timestamps, no pointers). The
+// identity is a 64-bit FNV-1a over all inputs rendered hex + a
+// human-readable provenance suffix. FNV-1a is a CACHE identity (collision
+// safety within one runtime run), not a security hash — documented here.
+struct BitmapCacheIdentityInput {
+    const uint8_t* src_bytes = nullptr;   // APK entry bytes (null = create path)
+    size_t src_len = 0;
+    std::string source_desc;
+    uint16_t source_density = 0;
+    uint16_t target_density = 0;
+    int32_t sample_size = 1;
+    int32_t config = 3;
+    bool density_scaled = false;
+};
+std::string bitmap_cache_identity_law(const BitmapCacheIdentityInput& in);
+
 } } // namespace miniandroid::framework
diff --git a/miniandroid/src/framework/state_list.cpp b/miniandroid/src/framework/state_list.cpp
index 92df83fa..16a4c0bf 100644
--- a/miniandroid/src/framework/state_list.cpp
+++ b/miniandroid/src/framework/state_list.cpp
@@ -127,6 +127,12 @@ bool parse_state_list(const std::vector<uint8_t>& axml,
         // S127: window_focused/activated framework selector states.
         it.state_window_focused = tri_state(item, "state_window_focused");
         it.state_activated = tri_state(item, "state_activated");
+        // C9-18 (CODER 9): the remaining standard states — a declared
+        // focused/hovered item must now actually MATCH the view state
+        // instead of silently acting as a wildcard (first-match ordering
+        // law depends on it).
+        it.state_focused = tri_state(item, "state_focused");
+        it.state_hovered = tri_state(item, "state_hovered");
         uint32_t c = 0;
         uint32_t cref = 0;
         if (item_color(item, &c, &cref)) {
@@ -138,6 +144,15 @@ bool parse_state_list(const std::vector<uint8_t>& axml,
             // Reference form: raw "@drawable/name" or a typed reference —
             // recorded for the caller's resolver; unresolved stays empty.
             if (!d->raw_value.empty()) it.drawable_path = d->raw_value;
+            // ── C9-19 (CODER 9): the COMPILED form — aapt2 stores
+            // @drawable/x as Res_value REFERENCE (data = resid). Recorded
+            // alongside the raw string; the engine dereferences the id
+            // through the ARSC resolver (find_id/resolve_full), so the
+            // state-list item carries a resolvable identity, not a string.
+            if (d->value.type == resources::DataType::REFERENCE ||
+                d->value.type == resources::DataType::DYNAMIC_REFERENCE ||
+                d->value.type == resources::DataType::ATTRIBUTE)
+                it.drawable_ref_id = d->value.data;
         }
         items.push_back(std::move(it));
     }
@@ -148,7 +163,8 @@ bool parse_state_list(const std::vector<uint8_t>& axml,
 bool pick_state_list(
     const std::vector<ViewShadow::ViewNode::BgStateItem>& items, bool pressed,
     bool enabled, bool selected, uint32_t* color_out, std::string* path_out,
-    bool checked) {
+    bool checked, bool focused, bool hovered,
+    const ViewShadow::ViewNode::BgStateItem** winner_out) {
     // StateListDrawable.getStateDrawableIndex law: FIRST item in document
     // order whose state spec is satisfied wins; a declared state must match
     // exactly (state_pressed="true" requires pressed), undeclared = wildcard.
@@ -165,8 +181,16 @@ bool pick_state_list(
         if (it.state_checked >= 0 &&
             it.state_checked != (checked ? 1 : 0))
             continue;
+        // C9-18: focused/hovered declared states must match exactly.
+        if (it.state_focused >= 0 &&
+            it.state_focused != (focused ? 1 : 0))
+            continue;
+        if (it.state_hovered >= 0 &&
+            it.state_hovered != (hovered ? 1 : 0))
+            continue;
         if (it.has_color && color_out) *color_out = it.color;
         if (path_out) *path_out = it.drawable_path;
+        if (winner_out) *winner_out = &it;
         return true;
     }
     return false;
diff --git a/miniandroid/src/framework/state_list.h b/miniandroid/src/framework/state_list.h
index 670991e5..4f0071be 100644
--- a/miniandroid/src/framework/state_list.h
+++ b/miniandroid/src/framework/state_list.h
@@ -38,11 +38,18 @@ bool parse_state_list(const std::vector<uint8_t>& axml,
                       std::vector<ViewShadow::ViewNode::BgStateItem>* out);
 
 // AOSP first-match law. Returns true when an item matched and fills the
-// winner's color (when has_color) or drawable path.
+// winner's color (when has_color) or drawable path. C9-18: focused/hovered
+// participate (defaults = the plain default view state).
 bool pick_state_list(
     const std::vector<ViewShadow::ViewNode::BgStateItem>& items, bool pressed,
     bool enabled, bool selected, uint32_t* color_out, std::string* path_out,
-    bool checked = false);  // S106 MG-022: android:state_checked law
+    bool checked = false,  // S106 MG-022: android:state_checked law
+    bool focused = false,  // C9-18: android:state_focused law
+    bool hovered = false,  // C9-18: android:state_hovered law
+    // C9-19 (CODER 9): when non-null, receives the MATCHED item — the
+    // engine dereferences its compiled drawable_ref_id through the ARSC
+    // router (the raw-string path alone left compiled refs unresolved).
+    const ViewShadow::ViewNode::BgStateItem** winner_out = nullptr);
 
 }  // namespace framework
 }  // namespace miniandroid
diff --git a/miniandroid/src/resources/arsc_parser.cpp b/miniandroid/src/resources/arsc_parser.cpp
index 5f70e8b3..28fbf108 100644
--- a/miniandroid/src/resources/arsc_parser.cpp
+++ b/miniandroid/src/resources/arsc_parser.cpp
@@ -414,7 +414,35 @@ bool ArscParser::parse_package(const uint8_t* base, size_t avail, size_t chunk_o
         if (ctype == RES_TABLE_TYPE_TYPE) {
             if (!parse_type_chunk(base, avail, pkg, pos, csize)) return false;
         } else if (ctype == RES_TABLE_TYPE_SPEC_TYPE) {
-            // skip
+            // ── C9-14 (CODER 9) — ResTable_typeSpec parse ────────────────
+            // AOSP ResourceTypes.h: { header(8), id@8, res0@9, res1@10,
+            // entryCount@12, flags[entryCount] }. Each u32 records the
+            // config-varies flags for the entry at its index. Multiple spec
+            // chunks per type are legal — flags OR-merge (deterministic).
+            if (pos + 20 <= avail && csize >= 20 && pos + csize <= avail) {
+                uint8_t spec_type_id = base[pos + 8];
+                uint32_t spec_count = rd32(base + pos + 12);
+                // C9-14 offset law (aapt2 8.13.2 ground truth, ff/plur
+                // probe dump): the ResTable_typeSpec struct is 16 bytes
+                // (header 8 + id 1 + res0 1 + res1 2 + entryCount 4) and
+                // the flags[entryCount] array starts at max(16,
+                // headerSize) — aapt2 writes headerSize=16, some writers
+                // pad to 20.
+                size_t spec_flags_off = pos + (rd16(base + pos + 2) > 16
+                                                   ? rd16(base + pos + 2)
+                                                   : 16);
+                const uint64_t need = (uint64_t)(spec_flags_off - pos) +
+                                      (uint64_t)spec_count * 4ull;
+                if (need <= csize) {
+                    auto& flags = pkg.type_specs[spec_type_id];
+                    if (flags.size() < spec_count) flags.resize(spec_count, 0);
+                    const uint8_t* fp = base + spec_flags_off;
+                    for (uint32_t si = 0; si < spec_count; ++si) {
+                        flags[si] |= rd32(fp + (size_t)si * 4);   // OR-merge
+                    }
+                }
+            }
+            // hostile/truncated spec chunk: skipped honestly (never fails parse)
         } else {
             // unknown — skip
         }
@@ -431,11 +459,18 @@ bool ArscParser::parse_package(const uint8_t* base, size_t avail, size_t chunk_o
 // ---------------------------------------------------------------------------
 bool ArscParser::parse(const std::vector<uint8_t>& data) {
     valid_ = false;
-    data_ = data.data();
+    // C9-13 (CODER 9): OWN the bytes. The old `data_ = data.data()` aliased
+    // the caller's vector — parse-only while it lived, but data_ stayed
+    // dangling after the call (latent use-after-free for any lazy reader).
+    data_owned_ = data;
+    data_ = data_owned_.data();
     size_ = data.size();
     packages_.clear();
     type_entries_.clear();
     id_index_.clear();
+    name_index_.clear();   // C9-12
+    libraries_.clear();    // C9-15
+    parsed_pkg_ids_.clear();
     stats_ = Stats{};
 
     if (size_ < 12) { last_error_ = "too small"; return false; }
@@ -454,10 +489,47 @@ bool ArscParser::parse(const std::vector<uint8_t>& data) {
 
     size_t pos = header_size + pool_size;
     size_t pkg_seen = 0;
-    while (pos + 8 <= total_size && pkg_seen < package_count) {
+    // C9-15: the loop no longer stops at package_count — RES_TABLE_LIBRARY
+    // chunks are table-level siblings of the packages (commonly FIRST, but
+    // a trailing chunk is legal too) and must not be silently dropped.
+    while (pos + 8 <= total_size) {
         uint16_t ctype = rd16(p + pos);
         uint32_t csize = rd32(p + pos + 4);
         if (csize == 0) break;
+        if (ctype == RES_TABLE_LIBRARY_TYPE) {
+            // ── C9-15 (CODER 9) — LIBRARY chunk parse ────────────────
+            // AOSP ResTable_lib { header, count, entry[count] } with
+            // entry = { uint32 packageId; uint16 packageName[128]; }.
+            // Bounds-guarded; malformed entries skip honestly, the chunk
+            // never fails the whole parse (an unknown library cannot
+            // invalidate the packages that DID parse).
+            if (pos + 12 > total_size || csize > total_size - pos) { pos += csize; continue; }
+            uint32_t lib_count = rd32(p + pos + 8);
+            size_t lib_hdr = rd16(p + pos + 2);
+            if (lib_hdr < 12) lib_hdr = 12;
+            size_t ep = pos + lib_hdr;
+            for (uint32_t li = 0; li < lib_count; ++li) {
+                if (ep + 4 > total_size || ep + 4 > pos + csize) break;
+                uint32_t lib_pkg_id = rd32(p + ep);
+                // UTF-16LE name, NUL-terminated within 128 units.
+                std::string name;
+                bool ok = false;
+                for (int ci = 0; ci < 128; ++ci) {
+                    size_t ch_off = ep + 4 + (size_t)ci * 2;
+                    if (ch_off + 2 > total_size || ch_off + 2 > pos + csize) break;
+                    uint16_t ch = rd16(p + ch_off);
+                    if (ch == 0) { ok = true; break; }
+                    if (ch < 0x80) name += (char)ch;
+                    else { name.clear(); break; }  // non-ASCII: unusable name
+                }
+                if (ok && !name.empty() && lib_pkg_id != 0)
+                    libraries_[lib_pkg_id] = name;
+                ep += 4 + 128 * 2;
+            }
+            pos += csize;
+            continue;
+        }
+        if (pkg_seen >= package_count) break;   // C9-15: packages still capped
         if (ctype == RES_TABLE_PACKAGE_TYPE) {
             // S124 FW-PACKAGE (AOSP AssetManager2 staged-package law): API 31+
             // tables append small STAGED package chunks that duplicate the
@@ -516,6 +588,34 @@ void ArscParser::finish_index() {
             }
         }
     }
+    // ── C9-14 (CODER 9): attach ResTable_typeSpec entry flags ───────────
+    // Flags were parsed per (package, type_id); entries receive the flag
+    // vector slot at their entry_index when in range.
+    for (auto& e : type_entries_) {
+        for (const auto& pkg : packages_) {
+            if (pkg.id != e.package_id) continue;
+            auto sit = pkg.type_specs.find((uint8_t)e.type_index);
+            if (sit != pkg.type_specs.end() && e.entry_index < sit->second.size())
+                e.spec_flags = sit->second[e.entry_index];
+            break;
+        }
+    }
+    // ── C9-12 (CODER 9): build the O(1) name→id index ───────────────────
+    // Exact (package,type,name) keys only. FIRST document-order id wins
+    // (type_entries_ is parse order — deterministic, unlike the unordered
+    // scan this replaces). Keys with an empty component never enter the
+    // index; find_id serves those through the legacy wildcard scan.
+    name_index_.clear();
+    for (const auto& e : type_entries_) {
+        if (e.name.empty() || e.type_name.empty()) continue;
+        std::string pkg_name;
+        for (const auto& pkg : packages_)
+            if (pkg.id == e.package_id) { pkg_name = pkg.name; break; }
+        if (pkg_name.empty()) continue;
+        std::string key = pkg_name;
+        key += '\x1f'; key += e.type_name; key += '\x1f'; key += e.name;
+        name_index_.emplace(key, e.resource_id);   // emplace = first wins
+    }
     stats_.named_ids = (uint32_t)by_id_.size();
     stats_.entries_by_type.clear();
     for (const auto& kv : by_id_) {
@@ -592,6 +692,16 @@ std::optional<ResolvedResource> ArscParser::resolve(uint32_t resource_id) const
 
 std::optional<uint32_t> ArscParser::find_id(const std::string& package, const std::string& type,
                                             const std::string& name) const {
+    // ── C9-12 (CODER 9): exact lookups answer through the parse-time index
+    // (O(1)). Legacy semantics preserved: empty ANY component = wildcard →
+    // falls through to the bounded scan below.
+    if (!package.empty() && !type.empty() && !name.empty()) {
+        std::string key = package;
+        key += '\x1f'; key += type; key += '\x1f'; key += name;
+        auto it = name_index_.find(key);
+        if (it != name_index_.end()) return it->second;
+        return std::nullopt;   // exact miss: no wildcard rescue (parity law)
+    }
     for (const auto& kv : by_id_) {
         const ArscEntry* e = kv.second.front();
         if (!name.empty() && e->name != name) continue;
@@ -607,6 +717,27 @@ std::optional<uint32_t> ArscParser::find_id(const std::string& package, const st
     return std::nullopt;
 }
 
+// ── C9-15 (CODER 9) — dynamic-reference translation law (pure) ────────────
+// AOSP DynamicRefTable.lookupResourceId: a DYNAMIC_REFERENCE value carries
+// a per-table LIBRARY package id in its high byte; the real id is recovered
+// by mapping the library slot to the package that is actually present under
+// the same NAME. No library slot, no same-name package, or a non-dynamic id
+// → honest nullopt (callers keep the raw id).
+std::optional<uint32_t> ArscParser::translate_dynamic_reference(uint32_t id) const {
+    if (libraries_.empty()) return std::nullopt;
+    const uint32_t pkg_bits = (id >> 24) & 0xFFu;
+    auto lit = libraries_.find(pkg_bits);
+    if (lit == libraries_.end()) return std::nullopt;
+    for (const auto& pkg : packages_) {
+        if (pkg.name == lit->second) {
+            const uint32_t real = ResId::pack(pkg.id, (uint8_t)((id >> 16) & 0xFFu),
+                                              (uint16_t)(id & 0xFFFFu));
+            return real;
+        }
+    }
+    return std::nullopt;
+}
+
 // ─────────────────────────────────────────────────────────────────────────────
 // GOLDEN-03 §4/§6 — canonical structured resolution.
 // AOSP law: AssetManager2/ResTable resolveReference walks REFERENCE values
diff --git a/miniandroid/src/resources/arsc_parser.h b/miniandroid/src/resources/arsc_parser.h
index bf49c3cd..0bb64da9 100644
--- a/miniandroid/src/resources/arsc_parser.h
+++ b/miniandroid/src/resources/arsc_parser.h
@@ -6,7 +6,8 @@
  *   RES_STRING_POOL_TYPE      (0x0001)  global + package string pools (UTF-8/UTF-16)
  *   RES_TABLE_PACKAGE_TYPE    (0x0200)  package: id, name, typeStrings, keyStrings
  *   RES_TABLE_TYPE_TYPE       (0x0201)  type (per config): entries incl. SPARSE
- *   RES_TABLE_TYPE_SPEC_TYPE  (0x0202)  (skipped; config mask not needed)
+ *   RES_TABLE_TYPE_SPEC_TYPE  (0x0202)  C9-14: per-entry spec flags parsed
+*   RES_TABLE_LIBRARY_TYPE    (0x0203)  C9-15: dynamic-ref library registry
  *
  * Res_value dataTypes handled: NULL, REFERENCE, ATTRIBUTE, STRING, FLOAT,
  * DIMENSION, FRACTION, INT_DEC, INT_HEX, INT_BOOLEAN, COLOR_ARGB8, COLOR_RGB8,
@@ -49,6 +50,10 @@ static constexpr uint16_t RES_XML_START_ELEMENT     = 0x0102;
 static constexpr uint16_t RES_XML_END_ELEMENT       = 0x0103;
 static constexpr uint16_t RES_XML_RESOURCE_MAP      = 0x0180;
 static constexpr uint16_t RES_TABLE_PACKAGE_TYPE    = 0x0200;
+// C9-15 (CODER 9): AOSP ResourceTypes.h — RES_TABLE_LIBRARY_TYPE. Sibling of
+// the package chunks under the root table; declares {packageId, packageName}
+// pairs the table's DYNAMIC_REFERENCE values refer to.
+static constexpr uint16_t RES_TABLE_LIBRARY_TYPE    = 0x0203;
 static constexpr uint16_t RES_TABLE_TYPE_TYPE       = 0x0201;
 static constexpr uint16_t RES_TABLE_TYPE_SPEC_TYPE  = 0x0202;
 
@@ -126,6 +131,9 @@ struct ArscEntry {
     uint32_t   bag_parent = 0;     // 0 = no parent
     std::vector<uint32_t> complex_keys;           // VISUAL-CAMPAIGN G49: ResTable_map name keys
     std::vector<ResValue> complex_items;  // for arrays/attrs
+    // C9-14 (CODER 9): ResTable_typeSpec entry flags (AOSP: OR of every
+    // spec chunk seen for the entry's type). 0 = no spec chunk present.
+    uint32_t   spec_flags = 0;
 };
 
 // ─────────────────────────────────────────────────────────────────────────────
@@ -213,8 +221,27 @@ public:
     // Resolve full resource by id.
     std::optional<ResolvedResource> resolve(uint32_t resource_id) const;
     // Find id by name (first package containing it). type e.g. "layout".
+    // C9-12 (CODER 9): exact (package,type,name) lookups answer through a
+    // parse-time hash index (O(1)); calls with ANY empty component keep the
+    // legacy wildcard scan semantics (documented AOSP getIdentifier allows
+    // null defType/defPackage). Results are identical to the O(n) walk —
+    // pinned by the c9_phase3 parity law.
     std::optional<uint32_t> find_id(const std::string& package, const std::string& type,
                                     const std::string& name) const;
+
+    // ── C9-15 (CODER 9) — LIBRARY chunk registry ───────────────────────
+    // Parsed RES_TABLE_LIBRARY_TYPE (0x0203) chunks: dynamic package id →
+    // package name. Empty map = table carried no library chunk (the common
+    // single-APK case — same answer as before, now explicit).
+    const std::map<uint32_t, std::string>& libraries() const { return libraries_; }
+
+    // C9-15 translation law (pure): a DYNAMIC_REFERENCE value whose package
+    // bits name a LIBRARY package is re-packed onto the REAL package with
+    // the same NAME (AOSP DynamicRefTable: library ids are per-table slots,
+    // resolved by name against the packages actually present). Returns
+    // nullopt when id is not a library ref or no same-name package exists
+    // (honest miss — the caller keeps the raw id and its own diagnostics).
+    std::optional<uint32_t> translate_dynamic_reference(uint32_t id) const;
     // Convenience: resolve id → value of best config (follows one REFERENCE hop).
     std::optional<ResValue> resolve_value(uint32_t resource_id) const;
     // Resolve string by id (no reference hop).
@@ -372,6 +399,8 @@ private:
         // type_id → list of type chunks (one per config)
         std::map<uint8_t, std::vector<TypeChunk>> types;
         // entry_index → resource id mapping is implicit: id = (package<<24)|(type<<16)|entry
+    // C9-14: ResTable_typeSpec chunk flags per entry index (type_id → flags).
+    std::map<uint8_t, std::vector<uint32_t>> type_specs;
     };
 
     bool parse_string_pool(const uint8_t* base, size_t avail, size_t chunk_offset, Pool& out);
@@ -383,8 +412,23 @@ private:
                                  const Package& pkg, ResValue& out);
     static std::string config_to_string(const uint8_t* cfg, size_t cfg_size);
 
+    // C9-13 (CODER 9): the parser OWNS its bytes. data_ previously aliased
+    // the caller's vector (dangling the moment that vector died — every
+    // post-parse resolve read freed memory). Law: parse() copies the bytes
+    // once; data_ points into the owned buffer only.
+    std::vector<uint8_t> data_owned_;
     const uint8_t* data_ = nullptr;
     size_t size_ = 0;
+
+    // C9-12 (CODER 9): parse-time name→id index. Key = package + 0x1f +
+    // type + 0x1f + name (0x1f never occurs in resource/type/package
+    // names). FIRST document-order id wins (deterministic; the legacy O(n)
+    // walk raced over unordered_map iteration order when several packages
+    // carried the same name).
+    std::unordered_map<std::string, uint32_t> name_index_;
+
+    // C9-15: RES_TABLE_LIBRARY_TYPE registry (dynamic pkg id → name).
+    std::map<uint32_t, std::string> libraries_;
     Pool global_strings_;
     std::vector<Package> packages_;
     // S124 FW-PACKAGE: ids of packages already parsed (staged duplicates skip).
diff --git a/miniandroid/src/resources/font_family.cpp b/miniandroid/src/resources/font_family.cpp
new file mode 100644
index 00000000..0fcf0729
--- /dev/null
+++ b/miniandroid/src/resources/font_family.cpp
@@ -0,0 +1,113 @@
+// font_family.cpp — C9-16/C9-17 (CODER 9) implementation. See font_family.h.
+
+#include "font_family.h"
+
+#include "axml_parser.h"
+
+#include <algorithm>
+#include <cstdlib>
+
+namespace miniandroid {
+namespace resources {
+
+namespace {
+// android:fontWeight range law (FontResourcesParser): values outside
+// 0..1000 clamp to the nearest bound; absent = 400.
+int32_t clamp_weight(int32_t w) {
+    if (w < 0) return 0;
+    if (w > 1000) return 1000;
+    return w;
+}
+}  // namespace
+
+FontFamily parse_font_family(const std::vector<uint8_t>& axml,
+                             const std::string& source_path) {
+    FontFamily out;
+    out.source_path = source_path;
+    resources::AxmlParser parser;
+    if (!parser.parse(axml) || !parser.valid()) return out;
+    const auto& root = parser.root();
+    if (root.name != "font-family") return out;   // honest miss
+    if (const auto* a = root.attr("fontFamily", "android"))
+        if (!a->raw_value.empty()) out.name = a->raw_value;
+
+    for (const auto& child : root.children) {
+        if (child.name != "font") continue;
+        FontFaceDecl decl;
+        decl.source_path = source_path;
+        if (const auto* f = child.attr("font", "android")) {
+            if (!f->raw_value.empty()) decl.font_ref = f->raw_value;
+            if (f->value.type == DataType::REFERENCE ||
+                f->value.type == DataType::DYNAMIC_REFERENCE)
+                decl.font_ref_id = f->value.data;
+        }
+        if (const auto* w = child.attr("fontWeight", "android")) {
+            int32_t v = 0;
+            if (w->value.type == DataType::INT_DEC ||
+                w->value.type == DataType::INT_HEX) {
+                v = (int32_t)w->value.data;
+            } else if (!w->raw_value.empty()) {
+                v = (int32_t)strtol(w->raw_value.c_str(), nullptr, 10);
+            }
+            decl.weight = clamp_weight(v == 0 && w->raw_value != "0" ? 400 : v);
+        }
+        if (const auto* s = child.attr("fontStyle", "android")) {
+            // AOSP FontResourcesParser: "italic" → ITALIC, anything else
+            // (absent / "normal") → NORMAL. The compiled value is an int
+            // (0 normal / 1 italic) for aapt2 — both forms accepted.
+            if (s->value.type == DataType::INT_DEC ||
+                s->value.type == DataType::INT_HEX) {
+                decl.italic = (s->value.data & 0x1) != 0;
+            } else {
+                decl.italic = (s->raw_value == "italic");
+            }
+        }
+        if (!decl.font_ref.empty() || decl.font_ref_id != 0)
+            out.faces.push_back(std::move(decl));
+    }
+    return out;
+}
+
+TypefaceRequest typeface_style_request(int style) {
+    TypefaceRequest r;
+    switch (style) {
+        case kTypefaceBold:
+        case kTypefaceBoldItalic:
+            r.weight = 700;
+            break;
+        default:
+            r.weight = 400;   // NORMAL / ITALIC / unknown styles
+            break;
+    }
+    r.italic = (style & kTypefaceItalic) != 0;
+    return r;
+}
+
+int select_font_face_law(const std::vector<FontFaceDecl>& faces,
+                         int32_t req_weight, bool req_italic) {
+    if (faces.empty()) return -1;
+    int best = -1;
+    int best_italic_penalty = 1;   // 0 = italic matches, 1 = mismatch
+    int32_t best_dist = 0;
+    for (size_t i = 0; i < faces.size(); ++i) {
+        const int ip = faces[i].italic == req_italic ? 0 : 1;
+        const int32_t dist = std::abs(faces[i].weight - req_weight);
+        if (best < 0 || ip < best_italic_penalty ||
+            (ip == best_italic_penalty && dist < best_dist)) {
+            best = (int)i;
+            best_italic_penalty = ip;
+            best_dist = dist;
+        }
+        // ties (ip == best_italic_penalty && dist == best_dist) keep the
+        // earlier candidate — document order, deterministic.
+    }
+    return best;
+}
+
+int select_font_face_law(const std::vector<FontFaceDecl>& faces, int style) {
+    const TypefaceRequest req = typeface_style_request(style);
+    return select_font_face_law(faces, req.weight, req.italic);
+}
+
+}  // namespace resources
+}  // namespace miniandroid
diff --git a/miniandroid/src/resources/font_family.h b/miniandroid/src/resources/font_family.h
new file mode 100644
index 00000000..a58cd500
--- /dev/null
+++ b/miniandroid/src/resources/font_family.h
@@ -0,0 +1,87 @@
+// font_family.h — C9-16/C9-17 (CODER 9) — font-family XML + weight law.
+//
+// AOSP contract (frameworks/base, graphics/java/android/graphics/Typeface.java
+// + core/java/android/content/res/FontResourcesParser.java):
+//   * res/font/*.xml <font-family> declares a NAMED family whose <font>
+//     children each carry android:font="@font/file", android:fontWeight
+//     (0..1000, default 400) and android:fontStyle ("normal"|"italic").
+//   * Typeface.create(family, style) resolves the family to the face whose
+//     (weight, italic) is the CLOSEST to the request (the FontListFont-
+//     FamilyTypefaceAdapter style-distance law): italic mismatch is the
+//     dominant penalty, then absolute weight distance; document order
+//     breaks ties deterministically.
+//   * The legacy filename-heuristic path (face -bold/-italic suffixes) stays
+//     the fallback when no font-family XML exists for the name.
+//
+// Pure + unit-tested (tests/c9_phase3_laws_test.cpp); the engine hookup
+// (dalvik_engine.cpp Typeface laws) consumes these functions.
+
+#ifndef MINIANDROID_RESOURCES_FONT_FAMILY_H
+#define MINIANDROID_RESOURCES_FONT_FAMILY_H
+
+#include "arsc_parser.h"
+
+#include <cstdint>
+#include <string>
+#include <vector>
+
+namespace miniandroid {
+namespace resources {
+
+// One <font> child of a <font-family>.
+struct FontFaceDecl {
+    std::string font_ref;      // raw android:font value ("@font/foo_regular")
+    uint32_t font_ref_id = 0;  // compiled REFERENCE id (0 = none/raw only)
+    int32_t weight = 400;      // android:fontWeight (AOSP default 400)
+    bool italic = false;       // android:fontStyle == "italic"
+    // Provenance: res/font/<family>.xml the decl was parsed from.
+    std::string source_path;
+};
+
+// A parsed <font-family> document.
+struct FontFamily {
+    std::string name;  // android:fontFamily attr ("" = filename carries it)
+    std::vector<FontFaceDecl> faces;
+    std::string source_path;
+    bool valid() const { return !faces.empty(); }
+};
+
+// C9-16 — parse a compiled res/font/*.xml AXML document. Returns an
+// INVALID family (faces empty) for non-font-family roots (honest miss —
+// the caller falls back to the filename heuristics).
+FontFamily parse_font_family(const std::vector<uint8_t>& axml,
+                             const std::string& source_path);
+
+// AOSP Typeface style bits (Typeface.java): NORMAL=0, BOLD=1,
+// ITALIC=2, BOLD_ITALIC=3.
+constexpr int kTypefaceNormal = 0;
+constexpr int kTypefaceBold = 1;
+constexpr int kTypefaceItalic = 2;
+constexpr int kTypefaceBoldItalic = 3;
+
+// style → (requested weight, requested italic) — AOSP Typeface.create
+// defaults: BOLD maps to weight 700, everything else to 400 (the pre-
+// variable-font contract; create(Typeface,int weight,boolean italic)
+// passes the weight through, clamped to 0..1000).
+struct TypefaceRequest {
+    int32_t weight = 400;
+    bool italic = false;
+};
+TypefaceRequest typeface_style_request(int style);
+
+// C9-17 — the AOSP closest-face law (pure, deterministic). Returns the
+// index into `faces` of the winner, or -1 when faces is empty.
+//   1. italic mismatch dominates (an exact-italic candidate always beats
+//      a non-matching one — AOSP style-distance first component),
+//   2. then minimal |weight - requested weight|,
+//   3. ties answer the FIRST document-order candidate.
+int select_font_face_law(const std::vector<FontFaceDecl>& faces,
+                         int32_t req_weight, bool req_italic);
+
+// Convenience: style-bits overload.
+int select_font_face_law(const std::vector<FontFaceDecl>& faces, int style);
+
+}  // namespace resources
+}  // namespace miniandroid
+
+#endif  // MINIANDROID_RESOURCES_FONT_FAMILY_H
diff --git a/miniandroid/src/resources/plurals.cpp b/miniandroid/src/resources/plurals.cpp
new file mode 100644
index 00000000..0d0845dd
--- /dev/null
+++ b/miniandroid/src/resources/plurals.cpp
@@ -0,0 +1,48 @@
+// plurals.cpp — C9-20 (CODER 9) implementation. See plurals.h for the
+// source-backed contract and the documented CLDR rule subset.
+
+#include "plurals.h"
+
+namespace miniandroid {
+namespace resources {
+
+PluralsQuantity cldr_quantity_law(const std::string& locale, int64_t n) {
+    // primary language subtag: strip region/script ("-IR", "-Latn"),
+    // lowercase (locale tags are case-insensitive for the subtag).
+    std::string lang;
+    for (char c : locale) {
+        if (c == '-' || c == '_') break;
+        lang += (char)((c >= 'A' && c <= 'Z') ? c + 32 : c);
+    }
+    if (lang == "fa") {
+        // CLDR fa: one for i = 0..1 (Persian counts zero as "one").
+        return (n == 0 || n == 1) ? PluralsQuantity::ONE
+                                  : PluralsQuantity::OTHER;
+    }
+    if (lang == "ar") {
+        if (n == 0) return PluralsQuantity::ZERO;
+        if (n == 1) return PluralsQuantity::ONE;
+        if (n == 2) return PluralsQuantity::TWO;
+        const int64_t m = n % 100;
+        if (m >= 3 && m <= 10) return PluralsQuantity::FEW;
+        if (m >= 11 && m <= 99) return PluralsQuantity::MANY;
+        return PluralsQuantity::OTHER;
+    }
+    if (lang == "ru") {
+        const int64_t i10 = n % 10, i100 = n % 100;
+        if (i10 == 1 && i100 != 11) return PluralsQuantity::ONE;
+        if (i10 >= 2 && i10 <= 4 && !(i100 >= 12 && i100 <= 14))
+            return PluralsQuantity::FEW;
+        return PluralsQuantity::MANY;
+    }
+    // default (en + every unlisted language): one iff n == 1.
+    return (n == 1) ? PluralsQuantity::ONE : PluralsQuantity::OTHER;
+}
+
+uint32_t plurals_bag_key(PluralsQuantity q) {
+    const uint8_t i = (uint8_t)q;
+    return i < 6 ? kPluralsKey[i] : kPluralsKey[5];
+}
+
+}  // namespace resources
+}  // namespace miniandroid
```
