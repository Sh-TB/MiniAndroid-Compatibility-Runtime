**S198 rebased phase-3 patch part 2/4** (base `0979678e`; verified `git apply --check` APPLIES_CLEAN on a pristine `0979678e` worktree; the applied result is byte-identical to the in-container-verified tree that produced binary `4d832c255bed513c`: c9_phase3_laws_test **46/46**, density 36/36, zip 42/42, §5/§6 harness **48/49** with ONLY the P-NEW-5 size-word law failing, resourceval **30/31** with ONLY law 29 failing)

```diff
diff --git a/miniandroid/src/dex/dalvik_engine.cpp b/miniandroid/src/dex/dalvik_engine.cpp
index 11cea802..4f471211 100755
--- a/miniandroid/src/dex/dalvik_engine.cpp
+++ b/miniandroid/src/dex/dalvik_engine.cpp
@@ -131,6 +131,10 @@ bool str_char_at_unit(const std::string& s, int32_t idx, int32_t& out) {
 #include "../framework/view_ancestry.h"  // G12 FIX-G12-001: AOSP framework ancestry law
 #include "../storage/sqlite_shadow.h"    // M3 F-ROOM-CHAIN: SQLite family shadow
 #include "../resources/resource_runtime.h"  // G10 FIX-G10-002: early classifier wiring
+#include "../resources/font_family.h"    // C9-16/C9-17 (CODER 9): font-family + weight law
+#include "../resources/plurals.h"        // C9-20 (CODER 9): CLDR plural-category law
+#include <png.h>                          // C9-7 (CODER 9): Bitmap.compress PNG encode
+#include <setjmp.h>                       // C9-7: libpng error contract
 #include <chrono>
 #include <unordered_map>  // CONT-29 W1: METHOD-CENSUS (env-gated, read-only)
 #include <x86intrin.h>  // S61 PERF: __rdtsc phase timers
@@ -35610,6 +35614,87 @@ void DalvikExecutionEngine::c7_service_bring_down(ServiceInstance& svc,
         current_class_ + "." + current_method_);
 }
 
+namespace {
+// ── C9-7 (CODER 9) — in-memory PNG encode (Bitmap.compress FORMAT_PNG) ──
+// libpng-backed RGBA encoder (the SAME library the runtime's PNG decoder
+// uses — one PNG authority). The write callback appends to a std::vector.
+// Error-path note: the setjmp branch leaks only the `rows` pointer array
+// (h * sizeof(void*) — bounded, error-only); no other C++ object crosses
+// the longjmp.
+static bool c9_png_encode_rgba(int w, int h,
+                               const std::vector<uint8_t>& rgba,
+                               std::vector<uint8_t>* out) {
+    if (w <= 0 || h <= 0 || rgba.size() != (size_t)w * h * 4 || !out)
+        return false;
+    png_structp p = png_create_write_struct(PNG_LIBPNG_VER_STRING,
+                                            nullptr, nullptr, nullptr);
+    if (!p) return false;
+    png_infop info = png_create_info_struct(p);
+    if (!info) {
+        png_destroy_write_struct(&p, nullptr);
+        return false;
+    }
+    std::vector<uint8_t*> rows(h);
+    for (int y = 0; y < h; ++y)
+        rows[y] = const_cast<uint8_t*>(&rgba[(size_t)y * w * 4]);
+    if (setjmp(png_jmpbuf(p))) {
+        png_destroy_write_struct(&p, &info);
+        return false;
+    }
+    auto write_fn = [](png_structp pp, png_bytep data, png_size_t len) {
+        static_cast<std::vector<uint8_t>*>(png_get_io_ptr(pp))
+            ->insert(static_cast<std::vector<uint8_t>*>(png_get_io_ptr(pp))
+                         ->end(),
+                     data, data + len);
+    };
+    auto flush_fn = [](png_structp) {};
+    png_set_write_fn(p, out, write_fn, flush_fn);
+    png_set_IHDR(p, info, (png_uint_32)w, (png_uint_32)h, 8,
+                 PNG_COLOR_TYPE_RGBA, PNG_INTERLACE_NONE,
+                 PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
+    png_write_info(p, info);
+    png_write_image(p, rows.data());
+    png_write_end(p, nullptr);
+    png_destroy_write_struct(&p, &info);
+    return true;
+}
+
+// ── C9-10 (CODER 9) — DisplayMetrics device-profile law ────────────────
+// ONE density authority: resources::device_config() — the SAME
+// ResTableConfig the bucket selection (AssetManager2 match) and the C9-1
+// BitmapFactory inTargetDensity use. The previous constants
+// (2.625/420/1080x1920 hardcoded) diverged from the runtime device the
+// moment MINIANDROID_DENSITY selected another bucket (the registered §2
+// gap: densityDpi answered 420 while the bucket law served 160/240-
+// selected resources). density = dpi/160 (AOSP DisplayMetrics law);
+// scaledDensity = density (fontScale 1.0); xdpi/ydpi = densityDpi.
+static void c9_fill_display_metrics(DalvikHeap& heap,
+                                    uint32_t dm_id) {
+    if (dm_id == 0 || !heap.has_object(dm_id)) return;
+    const auto& cfg = resources::device_config();
+    const float density = (float)cfg.density / 160.0f;
+    auto set_f = [&](const char* f, float v) {
+        heap.set_object_field(dm_id, f, DalvikValue::make_float(v));
+    };
+    auto set_i = [&](const char* f, int32_t v) {
+        heap.set_object_field(dm_id, f, DalvikValue::make_int(v));
+    };
+    set_f("density", density);
+    set_i("densityDpi", (int32_t)cfg.density);
+    set_f("scaledDensity", density);
+    set_i("widthPixels", (int32_t)cfg.screenWidth);
+    set_i("heightPixels", (int32_t)cfg.screenHeight);
+    set_f("xdpi", (float)cfg.density);
+    set_f("ydpi", (float)cfg.density);
+    static thread_local uint64_t c9_dm_log = 0;
+    if (c9_dm_log++ < 8)
+        std::cerr << "[C9-10] DisplayMetrics <- device_config(): density="
+                  << density << " dpi=" << cfg.density << " "
+                  << cfg.screenWidth << "x" << cfg.screenHeight
+                  << std::endl;
+}
+}  // namespace
+
 bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                                           const std::string& method,
                                           const std::vector<DalvikValue>& args_raw,
@@ -37754,6 +37839,101 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
             return DalvikValue::make_object(tf_id,
                                             "Landroid/graphics/Typeface;");
         };
+        // ── C9-17 (CODER 9) — font-family resolution for CUSTOM families ───
+        // AOSP FontListFontFamilyTypefaceAdapter: Typeface.create(family,
+        // style/weight/italic) resolves the family through its font-family
+        // definition (res/font/<family>.xml), selecting the closest
+        // (weight, italic) face — NOT the filename heuristics. The law:
+        //   1. parse res/font/<fam>.xml via resources::parse_font_family
+        //   2. pick the face with resources::select_font_face_law
+        //   3. resolve @font/<name> → the real APK font-file entry via the
+        //      ARSC router (type "font"), extract the bytes
+        //   4. register the face (TextShaper::register_app_font_memory) and
+        //      answer its index — the SAME __font_face_idx__ channel the
+        //      createFromAsset law feeds (Paint.setTypeface consumes it).
+        // Framework aliases (sans-serif family) and missing XMLs fall back
+        // to the existing behavior (honest miss, no fake face).
+        auto tf_face_idx = [&](const std::string& fam, int32_t weight,
+                               bool italic) -> int {
+            auto& rt = resources::ResourceRuntime::instance();
+            if (!rt.ensure_loaded(apk_path_)) return -1;
+            std::vector<std::string> entries;
+            for (const auto& ze : rt.apk().list_entries_cached("res/"))
+                entries.push_back(ze.name);
+            // The family definition: res/font/<family>.xml — aapt2's font
+            // processing may version-qualify the ATTR-CARRYING file
+            // (res/font-v22/<family>.xml ground truth: the base res/font/
+            // file ships attr-less for the support-lib compat path; probe
+            // `aapt2 dump xmltree`). Law: try the plain file first, then
+            // the -vNN variants, and use the first that PARSES as a
+            // font-family with faces.
+            std::string xml_entry;
+            std::vector<uint8_t> xml_bytes;
+            auto try_xml = [&](const std::string& e) -> bool {
+                for (const auto& en : entries)
+                    if (en == e) {
+                        auto b = rt.apk().extract_entry(apk_path_, e);
+                        if (b.empty()) return false;
+                        auto doc = resources::parse_font_family(b, e);
+                        if (doc.valid()) {
+                            xml_entry = e;
+                            xml_bytes = std::move(b);
+                            return true;
+                        }
+                    }
+                return false;
+            };
+            if (!try_xml("res/font/" + fam + ".xml")) {
+                // version-qualified fallback: res/font-vNN/<fam>.xml
+                const std::string suffix = "/" + fam + ".xml";
+                for (const auto& en : entries) {
+                    if (en.rfind("res/font-v", 0) != 0 ||
+                        en.size() <= suffix.size() ||
+                        en.compare(en.size() - suffix.size(), suffix.size(),
+                                   suffix) != 0)
+                        continue;
+                    if (try_xml(en)) break;
+                }
+            }
+            if (xml_bytes.empty()) return -1;
+            auto fam_doc = resources::parse_font_family(xml_bytes, xml_entry);
+            if (!fam_doc.valid()) return -1;
+            const int idx = resources::select_font_face_law(fam_doc.faces,
+                                                            weight, italic);
+            if (idx < 0) return -1;
+            const auto& decl = fam_doc.faces[idx];
+            // The face FILE: res/font/<name>.ttf/.otf — from the compiled
+            // ref through the ARSC router (type "font"), else from the raw
+            // @font/<name> string.
+            std::string face_entry;
+            if (decl.font_ref_id != 0) {
+                auto sel = rt.arsc().select_file(
+                    decl.font_ref_id, entries, resources::device_config());
+                if (sel) face_entry = sel->path;
+            }
+            if (face_entry.empty() && decl.font_ref.rfind("@font/", 0) == 0) {
+                const std::string base = decl.font_ref.substr(6);
+                static const char* kSuffixes[] = {".ttf", ".otf"};
+                for (const char* suf : kSuffixes) {
+                    const std::string cand = "res/font/" + base + suf;
+                    for (const auto& e : entries)
+                        if (e == cand) { face_entry = cand; break; }
+                    if (!face_entry.empty()) break;
+                }
+            }
+            if (face_entry.empty()) return -1;
+            auto face_bytes = rt.apk().extract_entry(apk_path_, face_entry);
+            if (face_bytes.empty()) return -1;
+            const int face = fonts::TextShaper::instance().
+                register_app_font_memory(face_bytes, face_entry,
+                                         decl.italic || weight >= 600);
+            std::cerr << "[C9-17] font-family '" << fam << "' -> face idx "
+                      << face << " (" << face_entry << " weight="
+                      << decl.weight << " italic=" << decl.italic
+                      << " requested=" << weight << "/" << italic << ")"
+                      << std::endl;
+            return face;
+        };
         // create(String, int) / create(Typeface, int)
         if (method == "create" && args.size() == 2) {
             std::string fam =
@@ -37770,6 +37950,13 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                 result = it->second;
             } else {
                 result = tf_make(fam, style, -1, -1);
+                // ── C9-17: resolve the font-family face for CUSTOM families
+                const auto req = resources::typeface_style_request(style);
+                const int face = tf_face_idx(fam, req.weight, req.italic);
+                if (face >= 0 && result.type == DalvikType::OBJECT_REF)
+                    heap_.set_object_field(result.object_id,
+                                           "__font_face_idx__",
+                                           DalvikValue::make_int(face));
                 static_field_storage_[key] = result;
             }
             status = ApiCallTrace::Status::IMPLEMENTED;
@@ -37793,6 +37980,12 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                 result = it->second;
             } else {
                 result = tf_make(fam, -1, weight, italic);
+                // ── C9-17: resolve the font-family face for CUSTOM families
+                const int face = tf_face_idx(fam, weight, italic != 0);
+                if (face >= 0 && result.type == DalvikType::OBJECT_REF)
+                    heap_.set_object_field(result.object_id,
+                                           "__font_face_idx__",
+                                           DalvikValue::make_int(face));
                 static_field_storage_[key] = result;
             }
             status = ApiCallTrace::Status::IMPLEMENTED;
@@ -40906,6 +41099,67 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         }
     }
     // ────────────────────────────────────────────────────────────────────
+    // ── C9-7 (CODER 9) — Bitmap.compress: REAL PNG encode ─────────────
+    // AOSP Bitmap.compress(CompressFormat, int quality, OutputStream):
+    // FORMAT_PNG (1) encodes the bitmap's pixels and writes the bytes to
+    // the stream (quality is IGNORED for PNG — AOSP doc). FORMAT_JPEG (2)
+    // / FORMAT_WEBP (3): the runtime links NO lossy encoder — the law
+    // answers the AOSP FAILURE contract (false) LOUDLY instead of a fake
+    // success or a crash. The stream: the ByteArrayOutputStream family
+    // buffer (the same storage its toByteArray law reads) — one byte
+    // authority; the heap-field mirror gap for DEX subclasses is recorded
+    // honestly below.
+    if (method == "compress" && class_name == "Landroid/graphics/Bitmap;") {
+        const uint32_t recv =
+            (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                ? args[0].object_id : 0;
+        const int32_t fmt = args.size() >= 2
+                                ? dalvik_int_value(args[1]) : 0;
+        uint32_t stream_oid = 0;
+        if (args.size() >= 4 && args[3].type == DalvikType::OBJECT_REF)
+            stream_oid = args[3].object_id;
+        const framework::StoredBitmap* sb =
+            framework::BitmapStore::instance().get(recv);
+        if (!sb || sb->recycled || stream_oid == 0) {
+            std::cerr << "[C9-7] Bitmap.compress format=" << fmt
+                      << " -> false (" << (!sb ? "no store entry"
+                                          : sb->recycled ? "recycled"
+                                                         : "null stream")
+                      << ")" << std::endl;
+            result = DalvikValue::make_bool(false);
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (fmt != 1) {   // FORMAT_PNG == 1; JPEG=2 / WEBP=3 unsupported
+            std::cerr << "[C9-7] Bitmap.compress format=" << fmt
+                      << " — EXPLICIT-UNSUPPORTED (no lossy encoder in the "
+                      << "runtime) -> false (AOSP failure contract)"
+                      << std::endl;
+            result = DalvikValue::make_bool(false);
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        std::vector<uint8_t> png;
+        if (!c9_png_encode_rgba(sb->width, sb->height, sb->rgba, &png)) {
+            std::cerr << "[C9-7] Bitmap.compress PNG encode FAILED ("
+                      << sb->width << "x" << sb->height << ") -> false"
+                      << std::endl;
+            result = DalvikValue::make_bool(false);
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        // One byte authority: append into the BAOS family buffer.
+        baos_buffers_[stream_oid] +=
+            std::string(png.begin(), png.end());
+        std::cerr << "[C9-7] Bitmap.compress PNG " << sb->width << "x"
+                  << sb->height << " -> " << png.size()
+                  << " bytes into BAOS o" << stream_oid
+                  << " (quality ignored per AOSP PNG law)" << std::endl;
+        result = DalvikValue::make_bool(true);
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+    // ────────────────────────────────────────────────────────────────────
     // LOADING-CAMPAIGN: java.io.ByteArrayOutputStream — the canonical
     // in-memory byte sink of the readAll/toByteArray pattern (probe-proven
     // first divergence: REC-MISS'd ctor → null array → FileOutputStream.
@@ -50913,6 +51167,36 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
     // threw NPE at the dooz composition (R8 z1/k.c = CollectionsKt.
     // listOf). Heap-fields-backed ("array[N]" + "__array_length__") so
     // the F-036 iterator law serves them with zero new machinery.
+    if (class_name == "Ljava/util/Collections;" &&
+        (method == "synchronizedList" || method == "synchronizedMap" ||
+         method == "synchronizedSet" ||
+         method == "synchronizedCollection") &&
+        args.size() >= 1 && args[0].type == DalvikType::OBJECT_REF) {
+        // C9-25 (CODER 9, S188 Phase-K cohort) — OpenJDK
+        // Collections.synchronized{List,Map,Set,Collection}: each returns a
+        // NON-NULL delegating wrapper; every read AND write delegates to
+        // the backing container. Single-threaded law: the wrapper is
+        // observably the backing container (identity = exact delegation;
+        // same reasoning as the unmodifiable* branch below).
+        // Pre-fix: NO handler → STUB answered NULL → Kotlin Intrinsics NPE
+        // "synchronizedList(...) must not be null" (astroloop vc6
+        // HangarState.<init>, S188 cohort: hangar died at APP BOUNDARY →
+        // NO_ROOT default background). OpenJDK contract: never null.
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        result = args[0];
+        {
+            static thread_local uint64_t c9_sync_n = 0;
+            if (c9_sync_n < 16) {
+                ++c9_sync_n;
+                std::cerr << "[C9-25] Collections." << method
+                          << " → backing container (OpenJDK delegate view;"
+                          << " single-thread identity) caller="
+                          << current_class_ << "." << current_method_
+                          << std::endl;
+            }
+        }
+        return true;
+    }
     if (class_name == "Ljava/util/Collections;" &&
         (method == "singletonList" || method == "emptyList" ||
          method == "emptyMap" || method == "emptySet" ||
@@ -63190,23 +63474,12 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
         // Engine-bridge framing: args[0] = receiver (Display), args[1] = the
         // DisplayMetrics OUT object (same convention as getSystemService's
-        // args[1] string). Fill the SAME device-profile law as
-        // Resources.getDisplayMetrics (density 2.625 / 420dpi / 1080x1920).
+        // args[1] string). C9-10: fill the SAME device-profile law as
+        // Resources.getDisplayMetrics — from device_config(), not the
+        // hardcoded 2.625/420/1080x1920 constants.
         uint32_t dm_id = args[1].object_id;
         if (dm_id != 0) {
-            auto set_f = [&](const char* f, float v) {
-                heap_.set_object_field(dm_id, f, DalvikValue::make_float(v));
-            };
-            auto set_i = [&](const char* f, int32_t v) {
-                heap_.set_object_field(dm_id, f, DalvikValue::make_int(v));
-            };
-            set_f("density", 2.625f);        // device-density law (420/160)
-            set_i("densityDpi", 420);        // DENSITY_420
-            set_f("scaledDensity", 2.625f);  // fontScale 1.0
-            set_i("widthPixels", 1080);      // device profile law
-            set_i("heightPixels", 1920);
-            set_f("xdpi", 420.0f);
-            set_f("ydpi", 420.0f);
+            c9_fill_display_metrics(heap_, dm_id);
         }
         result = DalvikValue::make_void();
         status = ApiCallTrace::Status::IMPLEMENTED;
@@ -63356,24 +63629,17 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         return true;
     }
 
+    // ── C9-10: the metric sites below feed from c9_fill_display_metrics
+    // (namespace-scope helper above) — ONE device-profile law for every
+    // DisplayMetrics surface.
     if (method == "getDisplayMetrics" &&
         class_name == "Landroid/content/res/Resources;") {
         DalvikValue dm = get_or_create_singleton("Landroid/util/DisplayMetrics;");
-        // Re-assert the device fields on every call (idempotent; guards any
+        // C9-10: re-assert the device fields on every call — now fed from
+        // device_config() (the ONE device law; idempotent against any
         // earlier density=1.0 population from the legacy singleton path).
-        auto set_f = [&](const char* f, float v) {
-            heap_.set_object_field(dm.object_id, f, DalvikValue::make_float(v));
-        };
-        auto set_i = [&](const char* f, int32_t v) {
-            heap_.set_object_field(dm.object_id, f, DalvikValue::make_int(v));
-        };
-        set_f("density", 2.625f);      // THE device-density law (2.625 = 420/160)
-        set_i("densityDpi", 420);      // DENSITY_420 — matches density law
-        set_f("scaledDensity", 2.625f);// fontScale 1.0 (F-023 default)
-        set_i("widthPixels", 1080);    // device profile law
-        set_i("heightPixels", 1920);
-        set_f("xdpi", 420.0f);
-        set_f("ydpi", 420.0f);
+        if (dm.type == DalvikType::OBJECT_REF)
+            c9_fill_display_metrics(heap_, dm.object_id);
         result = dm;
         status = ApiCallTrace::Status::IMPLEMENTED;
         return true;
@@ -63736,6 +64002,10 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
     if (method == "getDisplayMetrics" &&
         class_name.find("Resources") != std::string::npos) {
         result = get_or_create_singleton("Landroid/util/DisplayMetrics;");
+        // C9-10: the generic Resources family answers the same
+        // device_config-fed fields (no bare singleton without the law).
+        if (result.type == DalvikType::OBJECT_REF)
+            c9_fill_display_metrics(heap_, result.object_id);
         status = ApiCallTrace::Status::IMPLEMENTED;
         return true;
     }
@@ -63748,17 +64018,29 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         result = get_or_create_singleton("Landroid/content/res/Configuration;");
         if (result.type == DalvikType::OBJECT_REF &&
             heap_.has_object(result.object_id)) {
-            // ── CONT-102 (F-NEW-431): Configuration.densityDpi law (AOSP
-            // ConfigurationCompat). The Configuration answers the SAME
-            // display identity the DisplayMetrics shadow serves
-            // (display_shadow.cpp densityDpi=160 — ONE identity law, no
-            // second value invented). Cold and warm reads answer the same
-            // object (resource-selection coherence).
-            auto cur = heap_.get_object_field(result.object_id, "densityDpi");
-            if (!cur.has_value() || cur->type != DalvikType::INT32 ||
-                cur->int_val == 0)
-                heap_.set_object_field(result.object_id, "densityDpi",
-                                       DalvikValue::make_int(160));
+            // ── C9-22 (CODER 9): Configuration fields fed from
+            // device_config() — the ONE device authority. The old constant
+            // densityDpi=160 was a SECOND device value inside one runtime
+            // (G04 single-device law violation): DisplayMetrics and bucket
+            // selection answered the requested density while Configuration
+            // answered 160. Law: densityDpi = device density, the dp
+            // fields = the configured dp screen, orientation = portrait.
+            auto set_if = [&](const char* f, int32_t v) {
+                auto cur = heap_.get_object_field(result.object_id, f);
+                if (!cur.has_value() || cur->type != DalvikType::INT32 ||
+                    cur->int_val != v)
+                    heap_.set_object_field(result.object_id, f,
+                                           DalvikValue::make_int(v));
+            };
+            const auto& cfg = resources::device_config();
+            set_if("densityDpi", (int32_t)cfg.density);
+            set_if("screenWidthDp", (int32_t)cfg.screenWidthDp);
+            set_if("screenHeightDp", (int32_t)cfg.screenHeightDp);
+            set_if("smallestScreenWidthDp",
+                   (int32_t)cfg.smallestScreenWidthDp);
+            // ── CONT-102 legacy note superseded by C9-22: the old code
+            // answered densityDpi=160 here (the "ONE identity" comment
+            // pointed at display_shadow's 160 — itself the divergence).
             // ── F-NEW-452 (CONT-107): Configuration.locale non-null law
             // (AOSP Configuration.setToDefaults: locale = Locale.getDefault()
             // — Resources.getConfiguration() NEVER answers a Configuration
@@ -64050,8 +64332,39 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                 xo && yo && xo->class_descriptor == "Ljava/lang/Class;" &&
                 yo->class_descriptor == "Ljava/lang/Class;";
         }
+        // ── C9-27 (CODER 9, S188 Phase-K): MIXED-FORM CLASS IDENTITY law ─
+        // ART interns ONE java.lang.Class per class; the engine carries
+        // that identity in TWO register forms — the heap-backed token
+        // (OBJECT_REF, runtime class Ljava/lang/Class;, identity content
+        // = the __referent_desc field, F-069/F-103 convention) and the
+        // CLASS_REF register-form (identity content = class_desc). The VM
+        // law behind "Class.equals is Object identity": the VM guarantees
+        // ONE Class object per classloader+name — so ACROSS register
+        // forms the compare must resolve to the same descriptor identity.
+        // The F-C4-567 gates covered same-form pairs only (CLASS_REF×
+        // CLASS_REF, heap-token×heap-token); a MIXED pair matched NO gate
+        // → fail-soft false → androidx SavedStateHandlesVM initializer
+        // loop answered "No initializer set for given class
+        // androidx.lifecycle.G" (astroloop v6 MainActivity.onCreate, IAE
+        // ×8 escaping onCreate; [F069-EQUALS] x:type=7:oid=1355:cls=
+        // Ljava/lang/Class; y:type=6:oid=0:cls=Landroidx/lifecycle/G;).
+        // A/B on the real APK: uncaught 9→0 after this law.
+        bool mixed_class_form_pair = false;
+        if (x.type == DalvikType::OBJECT_REF &&
+            y.type == DalvikType::CLASS_REF && x.object_id != 0 &&
+            heap_.has_object(x.object_id)) {
+            const auto* xo = heap_.get(x.object_id);
+            mixed_class_form_pair =
+                xo && xo->class_descriptor == "Ljava/lang/Class;";
+        } else if (x.type == DalvikType::CLASS_REF &&
+                   y.type == DalvikType::OBJECT_REF && y.object_id != 0 &&
+                   heap_.has_object(y.object_id)) {
+            const auto* yo = heap_.get(y.object_id);
+            mixed_class_form_pair =
+                yo && yo->class_descriptor == "Ljava/lang/Class;";
+        }
         if (app_dex_receiver || base_object_receiver || class_or_null_case ||
-            heap_class_token_pair) {
+            heap_class_token_pair || mixed_class_form_pair) {
             if (f069d) {
                 std::cerr << "[F069-EQUALS] x:type=" << static_cast<int>(x.type)
                           << ":oid=" << x.object_id
@@ -64107,6 +64420,24 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                             eq = (xr->string_val == yr->string_val);
                     }
                 }
+            } else if (mixed_class_form_pair) {
+                // ── C9-27: descriptor identity ACROSS register forms ────
+                // token.__referent_desc == CLASS_REF.class_desc, and the
+                // symmetric orientation. Same law as the same-form gates:
+                // one interned Class per descriptor.
+                if (x.type == DalvikType::OBJECT_REF) {
+                    auto xr = heap_.get_object_field(x.object_id,
+                                                     "__referent_desc");
+                    eq = xr.has_value() &&
+                         xr->type == DalvikType::STRING_REF &&
+                         xr->string_val == y.class_desc;
+                } else {
+                    auto yr = heap_.get_object_field(y.object_id,
+                                                     "__referent_desc");
+                    eq = yr.has_value() &&
+                         yr->type == DalvikType::STRING_REF &&
+                         x.class_desc == yr->string_val;
+                }
             } else if (x.type == DalvikType::NULL_REF &&
                        y.type == DalvikType::NULL_REF) {
                 eq = true;
@@ -67598,6 +67929,397 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         return true;
     }
 
+    // ────────────────────────────────────────────────────────────────────────
+    // C9-24 (CODER 9, S188 Phase-K cohort) — platform font-resource API
+    // laws (AOSP android.graphics.fonts.Font / FontFamily / Typeface.
+    // CustomFallbackBuilder, API 26+). AOSP ResourcesCompat.getFont
+    // (androidx.core) ends in EXACTLY these platform classes: Font.Builder
+    // (AssetManager, res-path).build() → FontFamily.Builder(font).
+    // build() → Typeface.CustomFallbackBuilder(family).build().
+    // Evidence (astroloop vc6, one binary main d3a8d0e, run_s188_c9):
+    //   R$font.exo2_regular=0x7f080001 → F513-GETVALUE resolved STRING
+    //   "res/Wx.ttf" → androidx Typefaces cache UID
+    //   "null-res/Wx.ttf-0-2131230721-0" ( getResourcePackageName STUB
+    //   answered null — C9-24b below) → cache miss → Font$Builder/
+    //   FontFamily$Builder/CustomFallbackBuilder all [S186I-STUB] null →
+    //   Font.getStyle() NPE → ResourcesCompat rethrow "Font resource ID
+    //   #0x7f080001 could not be retrieved." → FontManager.initialize
+    //   dead at APP BOUNDARY → NO_ROOT, 18 uncaught, default background.
+    // The real rasterizer behind these classes is the SAME FreeType
+    // registry the cont70-ANT6 Typeface.createFromAsset law serves
+    // (startup FIX-4/F-NEW-315 scan already registered res/Wx.ttf et al).
+    // One registry, one face identity — no second font authority.
+    // AOSP failure laws: Font.Builder.build throws IOException on a
+    // missing asset (real: `Cannot open font file` family); CustomFall-
+    // backBuilder.build throws IOException when the family is empty.
+    // ────────────────────────────────────────────────────────────────────────
+    if (class_name == "Landroid/graphics/fonts/Font$Builder;" &&
+        method == "<init>" && args.size() >= 3) {
+        // AOSP Font.Builder ctor family — TWO live shapes (astroloop q/k.h
+        // pins the (Resources, int resourceId) one via C9-24-DIAG:
+        //   a0=recv a1=t7 Resources a2=t1 resid):
+        //   1. (AssetManager, String path[, int ttcIndex]) → __font_path__
+        //   2. (Resources, int resourceId) → __font_resid__  (AOSP
+        //      buildFromResources: getValue(id, tv, true) → tv.string path)
+        // <init> convention (F-C4-585 house law): mutate args[0], VOID.
+        if (args[0].type == DalvikType::OBJECT_REF &&
+            args[0].object_id != 0 && heap_.has_object(args[0].object_id)) {
+            if (args.size() >= 3 && args[2].type == DalvikType::INT32 &&
+                args[1].type == DalvikType::OBJECT_REF) {
+                heap_.set_object_field(args[0].object_id, "__font_resid__",
+                                       args[2]);
+            } else {
+                auto c9_str_arg = [&](const DalvikValue& a) -> std::string {
+                    if (a.type == DalvikType::STRING_REF) return a.string_val;
+                    if (a.type == DalvikType::OBJECT_REF && a.object_id != 0 &&
+                        a.class_desc.find("String") != std::string::npos) {
+                        for (const char* fld :
+                             {"__string_value__", "value", "sb_value"}) {
+                            auto s = heap_.get_object_field(a.object_id, fld);
+                            if (s.has_value() &&
+                                s->type == DalvikType::STRING_REF)
+                                return s->string_val;
+                        }
+                    }
+                    return "";
+                };
+                for (int ci = 1; ci < (int)args.size(); ++ci) {
+                    std::string p = c9_str_arg(args[ci]);
+                    if (!p.empty()) {
+                        heap_.set_object_field(
+                            args[0].object_id, "__font_path__",
+                            DalvikValue::make_string(p, 0));
+                        break;
+                    }
+                }
+            }
+        }
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        result = DalvikValue::make_void();
+        return true;
+    }
+    if (class_name == "Landroid/graphics/fonts/Font$Builder;" &&
+        (method == "build" || method == "setWeight" ||
+         method == "setSlant" || method == "setTtcIndex")) {
+        if (method == "build") {
+            std::string fpath;
+            if (args.size() >= 1 && args[0].type == DalvikType::OBJECT_REF &&
+                args[0].object_id != 0) {
+                if (auto p = heap_.get_object_field(args[0].object_id,
+                                                    "__font_path__");
+                    p.has_value() && p->type == DalvikType::STRING_REF)
+                    fpath = p->string_val;
+                if (fpath.empty()) {
+                    // AOSP buildFromResources: getValue(id, tv, true) →
+                    // tv.string is the res/ zip path (F513 authority).
+                    if (auto rid = heap_.get_object_field(args[0].object_id,
+                                                          "__font_resid__");
+                        rid.has_value() && rid->type == DalvikType::INT32 &&
+                        rid->int_val != 0) {
+                        auto& rt_f = resources::ResourceRuntime::instance();
+                        if (rt_f.loaded() || rt_f.ensure_loaded(apk_path_)) {
+                            if (auto v = rt_f.arsc().resolve_value(
+                                    (uint32_t)rid->int_val);
+                                v && v->is_string())
+                                fpath = v->string_value;
+                        }
+                    }
+                }
+            }
+            int fface = fpath.empty()
+                            ? -1
+                            : fonts::TextShaper::instance().app_face_index_for_name(
+                                  fpath);
+            if (fface < 0) {
+                // AOSP Font.Builder.build: missing asset → IOException.
+                throw_deferred("Ljava/io/IOException;",
+                               "Cannot open font file " + fpath, "C9-24");
+                result = DalvikValue::make_null();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            uint32_t fobj = heap_.allocate("Landroid/graphics/fonts/Font;",
+                                           pc_, 0);
+            heap_.set_object_field(fobj, "__font_path__",
+                                   DalvikValue::make_string(fpath, 0));
+            heap_.set_object_field(fobj, "__font_face_idx__",
+                                   DalvikValue::make_int(fface));
+            result = DalvikValue::make_object(
+                fobj, "Landroid/graphics/fonts/Font;");
+        } else {
+            // setWeight/setSlant/setTtcIndex: AOSP mutates the builder and
+            // returns it (fluent). The face identity is path-keyed in the
+            // registry; weight/slant variants remain a registered subset
+            // gap (named, same as C9-17 closest-face limit).
+            result = args.empty() ? DalvikValue::make_null()
+                                  : args[0];
+        }
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+    if (class_name == "Landroid/graphics/fonts/Font;" &&
+        method == "getStyle" && args.size() >= 1) {
+        // AOSP Font.getStyle(): non-null FontStyle (weight/slant pair).
+        uint32_t fs = heap_.allocate("Landroid/graphics/fonts/FontStyle;",
+                                     pc_, 0);
+        heap_.set_object_field(fs, "getWeight", DalvikValue::make_int(400));
+        heap_.set_object_field(fs, "getSlant", DalvikValue::make_int(0));
+        result = DalvikValue::make_object(
+            fs, "Landroid/graphics/fonts/FontStyle;");
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+    if (class_name == "Landroid/graphics/fonts/FontStyle;" &&
+        (method == "getWeight" || method == "getSlant")) {
+        result = DalvikValue::make_int(method == "getWeight" ? 400 : 0);
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+    if (class_name == "Landroid/graphics/fonts/FontFamily$Builder;") {
+        if (method == "<init>" && args.size() >= 2) {
+            // ctor(Font first) — receiver-mutation convention (see C9-24
+            // Font$Builder.<init> note): family slots live on args[0].
+            if (args[0].type == DalvikType::OBJECT_REF &&
+                args[0].object_id != 0 && heap_.has_object(args[0].object_id)) {
+                if (args[1].type == DalvikType::OBJECT_REF &&
+                    args[1].object_id != 0) {
+                    heap_.set_object_field(args[0].object_id, "font0", args[1]);
+                    heap_.set_object_field(args[0].object_id, "font_count",
+                                           DalvikValue::make_int(1));
+                } else {
+                    heap_.set_object_field(args[0].object_id, "font_count",
+                                           DalvikValue::make_int(0));
+                }
+            }
+            result = DalvikValue::make_void();
+        } else if (method == "addFont" || method == "addFontDetails") {
+            uint32_t fam_id = args.empty()
+                                  ? 0
+                                  : (args[0].type == DalvikType::OBJECT_REF
+                                         ? args[0].object_id
+                                         : 0);
+            if (fam_id != 0 && args.size() >= 2 &&
+                args[1].type == DalvikType::OBJECT_REF &&
+                args[1].object_id != 0) {
+                int n = 0;
+                if (auto c = heap_.get_object_field(fam_id, "font_count");
+                    c.has_value() && c->type == DalvikType::INT32)
+                    n = c->int_val;
+                if (n < 16) {  // bounded: AOSP families are small
+                    heap_.set_object_field(
+                        fam_id, "font" + std::to_string(n), args[1]);
+                    heap_.set_object_field(fam_id, "font_count",
+                                           DalvikValue::make_int(n + 1));
+                }
+                result = args[0];  // fluent: returns the builder
+            } else {
+                result = args.empty() ? DalvikValue::make_null() : args[0];
+            }
+        } else if (method == "build") {
+            // AOSP FontFamily.Builder.build: IllegalStateException when
+            // empty (never a silent null family).
+            uint32_t fam_id = args.empty()
+                                  ? 0
+                                  : (args[0].type == DalvikType::OBJECT_REF
+                                         ? args[0].object_id
+                                         : 0);
+            int n = 0;
+            if (fam_id != 0) {
+                if (auto c = heap_.get_object_field(fam_id, "font_count");
+                    c.has_value() && c->type == DalvikType::INT32)
+                    n = c->int_val;
+            }
+            if (n <= 0) {
+                throw_deferred("Ljava/lang/IllegalStateException;",
+                               "Empty font family", "C9-24");
+                result = DalvikValue::make_null();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            uint32_t ffam = heap_.allocate(
+                "Landroid/graphics/fonts/FontFamily;", pc_, 0);
+            for (int i = 0; i < n && i < 16; ++i) {
+                if (auto f = heap_.get_object_field(
+                        fam_id, "font" + std::to_string(i));
+                    f.has_value())
+                    heap_.set_object_field(ffam,
+                                           "font" + std::to_string(i), *f);
+            }
+            heap_.set_object_field(ffam, "font_count",
+                                   DalvikValue::make_int(n));
+            result = DalvikValue::make_object(
+                ffam, "Landroid/graphics/fonts/FontFamily;");
+        } else {
+            result = DalvikValue::make_null();
+        }
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+    if (class_name == "Landroid/graphics/Typeface$CustomFallbackBuilder;" &&
+        (method == "<init>" || method == "build" || method == "setStyle" ||
+         method == "setWeight" || method == "setSystemFallback")) {
+        if (method == "<init>") {
+            // receiver-mutation convention: __family_oid__ lives on args[0].
+            if (args.size() >= 2 && args[0].type == DalvikType::OBJECT_REF &&
+                args[0].object_id != 0 && heap_.has_object(args[0].object_id) &&
+                args[1].type == DalvikType::OBJECT_REF)
+                heap_.set_object_field(args[0].object_id, "__family_oid__",
+                                       args[1]);
+            {
+                static thread_local uint64_t c9_cfb_diag = 0;
+                if (c9_cfb_diag < 6) {
+                    ++c9_cfb_diag;
+                    std::cerr << "[C9-24-DIAG] CustomFallbackBuilder.<init> argc="
+                              << args.size() << " a0=t" << (int)args[0].type
+                              << (args.size() >= 2
+                                      ? (" a1=t" + std::to_string((int)args[1].type))
+                                      : "")
+                              << std::endl;
+                }
+            }
+            result = DalvikValue::make_void();
+        } else if (method == "build") {
+            uint32_t cb_id = args.empty()
+                                 ? 0
+                                 : (args[0].type == DalvikType::OBJECT_REF
+                                        ? args[0].object_id
+                                        : 0);
+            uint32_t fam_oid = 0;
+            if (cb_id != 0) {
+                if (auto f = heap_.get_object_field(cb_id, "__family_oid__");
+                    f.has_value() && f->type == DalvikType::OBJECT_REF)
+                    fam_oid = f->object_id;
+            }
+            std::string fpath;
+            int n = 0;
+            if (fam_oid != 0) {
+                if (auto c = heap_.get_object_field(fam_oid, "font_count");
+                    c.has_value() && c->type == DalvikType::INT32)
+                    n = c->int_val;
+                if (n > 0) {
+                    if (auto f0 = heap_.get_object_field(fam_oid, "font0");
+                        f0.has_value() && f0->type == DalvikType::OBJECT_REF &&
+                        f0->object_id != 0) {
+                        if (auto p = heap_.get_object_field(
+                                f0->object_id, "__font_path__");
+                            p.has_value() && p->type == DalvikType::STRING_REF)
+                            fpath = p->string_val;
+                    }
+                }
+            }
+            int cface = fpath.empty()
+                            ? -1
+                            : fonts::TextShaper::instance().app_face_index_for_name(
+                                  fpath);
+            if (cface < 0) {
+                // AOSP: build() throws IOException when the family carried
+                // no loadable font — never a silent null Typeface.
+                throw_deferred("Ljava/io/IOException;",
+                               "font family failed to resolve " + fpath,
+                               "C9-24");
+                result = DalvikValue::make_null();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            uint32_t tf = heap_.allocate("Landroid/graphics/Typeface;", pc_,
+                                         call_stack_.empty()
+                                             ? 0
+                                             : call_stack_.top().frame_id);
+            heap_.set_object_field(tf, "__font_face_idx__",
+                                   DalvikValue::make_int(cface));
+            result = DalvikValue::make_object(
+                tf, "Landroid/graphics/Typeface;");
+        } else {
+            // setStyle/setWeight/setSystemFallback: AOSP fluent setters
+            // return the builder itself — never null (the null build()
+            // receiver NPE family, astroloop q/k.h pc-chain pinned).
+            result = args.empty() ? DalvikValue::make_null() : args[0];
+        }
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+
+    // ────────────────────────────────────────────────────────────────────────
+    // C9-26 (CODER 9, S188 cohort) — VibratorManager / Vibrator contract
+    // (AOSP android.os.VibratorManager, API 31+; SDK_INT here reports 35).
+    // getSystemService("vibrator_manager") now returns the singleton (see
+    // the t_service_map row above) — its AOSP methods must answer real
+    // values: getDefaultVibrator() is NEVER null (VibratorManager.java:
+    // returns the default vibrator of the device), getVibratorIds() is a
+    // non-null (possibly length-1) int[]. Vibrator: hasVibrator() true on
+    // any real device; vibrate() family void (haptic fire is a device
+    // effect, unobservable in a headless runtime); hasAmplitudeControl()
+    // false (honest minimal device).
+    // ────────────────────────────────────────────────────────────────────────
+    if (class_name == "Landroid/os/VibratorManager;" &&
+        (method == "getDefaultVibrator" || method == "getVibratorIds")) {
+        if (method == "getDefaultVibrator") {
+            result = get_or_create_singleton("Landroid/os/Vibrator;");
+        } else {
+            uint32_t arr = heap_.allocate("[I", pc_, 0);
+            heap_.set_object_field(arr, "__array_length__",
+                                   DalvikValue::make_int(1));
+            heap_.set_object_field(arr, "array[0]",
+                                   DalvikValue::make_int(0));
+            result = DalvikValue::make_object(arr, "[I");
+        }
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+    if (class_name == "Landroid/os/Vibrator;" &&
+        (method == "hasVibrator" || method == "hasAmplitudeControl")) {
+        result = DalvikValue::make_bool(method == "hasVibrator");
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+
+    // ────────────────────────────────────────────────────────────────────────
+    // C9-24b (CODER 9, S188 cohort) — Resources.getResourcePackageName /
+    // getResourceTypeName / getResourceEntryName (AOSP Resources.java).
+    // The S186I-STUB answered NULL for a valid app id — impossible per the
+    // AOSP contract (throws NotFoundException on unknown id; never null).
+    // The null poisoned androidx Typefaces cache UIDs ("null-res/Wx.ttf-…"
+    // — astroloop trace, same run as C9-24 evidence) and any other
+    // resource-name consumer. All three answer from the ONE ARSC table the
+    // F513 law resolves against.
+    // ────────────────────────────────────────────────────────────────────────
+    if (class_name == "Landroid/content/res/Resources;" &&
+        (method == "getResourcePackageName" ||
+         method == "getResourceTypeName" ||
+         method == "getResourceEntryName") &&
+        args.size() >= 2 && args[1].type == DalvikType::INT32) {
+        int32_t rn_resid = args[1].int_val;
+        auto& rt_rn = resources::ResourceRuntime::instance();
+        if ((rt_rn.loaded() || rt_rn.ensure_loaded(apk_path_))) {
+            if (auto rr = rt_rn.arsc().resolve((uint32_t)rn_resid); rr) {
+                const std::string* ans = nullptr;
+                if (method == "getResourcePackageName")
+                    ans = &rr->package_name;
+                else if (method == "getResourceTypeName")
+                    ans = &rr->type_name;
+                else
+                    ans = &rr->name;
+                if (ans && !ans->empty()) {
+                    result = DalvikValue::make_string(*ans, 0);
+                    status = ApiCallTrace::Status::IMPLEMENTED;
+                    return true;
+                }
+            }
+        }
+        // AOSP: unknown id → NotFoundException (app-table ids only, same
+        // framework-res boundary scoping as the F513 law).
+        if ((((uint32_t)rn_resid) >> 24 & 0xFF) == 0x7f) {
+            throw_deferred(
+                "Landroid/content/res/Resources$NotFoundException;",
+                "Unable to find resource ID #0x" +
+                    to_hex((uint32_t)rn_resid),
+                "C9-24b");
+        }
+        result = DalvikValue::make_null();
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+
     // ────────────────────────────────────────────────────────────────────────
     // P1.3 — Window.getDecorView → View
     // ────────────────────────────────────────────────────────────────────────
@@ -68729,7 +69451,99 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
     // EXP-067: Resources.getDrawable(int) → Drawable (returns resource name as string for now)
     // Real drawable decoding (bitmap loading) is a future EXP. For now, return the
     // drawable's resource name so the renderer can look up the asset path.
-    if (method == "getDrawable" &&
+    // ── C9-20 (CODER 9) — Resources.getQuantityString law ───────────────
+    // AOSP Resources.java: getQuantityString(id, quantity[, formatArgs]) =
+    // CLDR plural category for (locale, quantity) → the matching item of
+    // the plurals BAG entry (complex entry, ResTable_map array), formatted
+    // with String.format when args are given. Missing entry →
+    // NotFoundException. The bag keys are the aapt2-pinned attrs
+    // (resources::kPluralsKey — probe-verified 0x01000004..0x01000009);
+    // the category comes from resources::cldr_quantity_law (documented
+    // CLDR 46 subset: default/en/fa/ar/ru).
+    if ((method == "getQuantityString" || method == "getQuantityText") &&
+        class_name.find("Resources") != std::string::npos &&
+        args.size() >= 3) {
+        const uint32_t resid = (uint32_t)dalvik_int_value(args[1]);
+        const int64_t quantity = (int64_t)dalvik_int_value(args[2]);
+        auto& rt = resources::ResourceRuntime::instance();
+        std::string picked;
+        bool found = false;
+        if (resid != 0 && rt.ensure_loaded(apk_path_)) {
+            auto r = rt.arsc().resolve(resid);
+            if (r) {
+                const resources::ArscEntry* best = r->best_for(resources::device_config());
+                if (best && best->is_complex) {
+                    const auto q = resources::cldr_quantity_law(
+                        resources::device_config().language_str(), quantity);
+                    const uint32_t want_key = resources::plurals_bag_key(q);
+                    // CLDR fallback law (AOSP PluralRules + ResTable lookups):
+                    // the exact category first; a MISSING category falls back
+                    // OTHER → OTHER missing → the LAST item in document order
+                    // (AOSP: ResTable + PluralRules fallback chain).
+                    for (int attempt = 0; attempt < 2 && !found; ++attempt) {
+                        uint32_t key = attempt == 0
+                                           ? want_key
+                                           : resources::plurals_bag_key(
+                                                 resources::PluralsQuantity::OTHER);
+                        for (size_t k = 0; k < best->complex_keys.size(); ++k) {
+                            if (best->complex_keys[k] != key) continue;
+                            if (k < best->complex_items.size() &&
+                                best->complex_items[k].is_string()) {
+                                picked = best->complex_items[k].string_value;
+                                found = true;
+                                break;
+                            }
+                        }
+                    }
+                }
+            }
+        }
+        if (!found) {
+            throw_deferred(
+                "Landroid/content/res/Resources$NotFoundException;",
+                "plurals resource 0x" +
+                    [](uint32_t r) {
+                        char b[16];
+                        std::snprintf(b, sizeof(b), "%08X", r);
+                        return std::string(b);
+                    }(resid),
+                "C9-20");
+            result = DalvikValue::make_null();
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        // Format args law: %d / %s substitution from the varargs (the
+        // engine models the Object... tail as one scalar arg).
+        if (args.size() >= 4) {
+            const auto& fa = args[3];
+            std::string out;
+            for (size_t ci = 0; ci < picked.size(); ++ci) {
+                if (picked[ci] == '%' && ci + 1 < picked.size() &&
+                    picked[ci + 1] == 'd') {
+                    out += std::to_string(quantity);
+                    ++ci;
+                } else if (picked[ci] == '%' && ci + 1 < picked.size() &&
+                           picked[ci + 1] == 's') {
+                    if (fa.type == DalvikType::STRING_REF) out += fa.string_val;
+                    else out += std::to_string(dalvik_int_value(fa));
+                    ++ci;
+                } else {
+                    out += picked[ci];
+                }
+            }
+            picked = out;
+        }
+        static thread_local uint64_t c9_pl_log = 0;
+        if (c9_pl_log++ < 8)
+            std::cerr << "[C9-20] getQuantityString resid=0x" << std::hex
+                      << resid << std::dec << " quantity=" << quantity
+                      << " -> '" << picked << "'" << std::endl;
+        result = DalvikValue::make_string(picked, 0);
+        status = ApiCallTrace::Status::IMPLEMENTED;
+        return true;
+    }
+
+    if ((method == "getDrawable" || method == "getDrawableForDensity") &&
         (class_name.find("Resources") != std::string::npos ||
          class_name.find("Context") != std::string::npos ||
          class_name.find("Activity") != std::string::npos)) {
@@ -68739,6 +69553,17 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
         // likewise delegates to its Resources.
         // Receiver-first args: args[0] = this (Context/Resources),
         // args[1] = the resid int.
+        // ── C9-11 (CODER 9): getDrawableForDensity(id, density) resolves
+        // the SAME law under a REQUESTED-density config (AOSP
+        // ResourcesImpl.getDrawableForDensity: value.density = density
+        // before decode — the selected bucket may differ from the device
+        // bucket, and the decode scales bucket→requested via C9-1).
+        const bool c9_dfd = method == "getDrawableForDensity";
+        int32_t requested_density = 0;
+        if (c9_dfd && args.size() >= 3 &&
+            (args[2].type == DalvikType::INT32 ||
+             args[2].type == DalvikType::BOOLEAN))
+            requested_density = args[2].int_val;
         int32_t resid = args.size() >= 2 &&
                                 (args[1].type == DalvikType::INT32 ||
                                  args[1].type == DalvikType::BOOLEAN ||
@@ -68762,15 +69587,26 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                 std::vector<std::string> entries;
                 for (const auto& e : rt.apk().list_entries_cached())
                     entries.push_back(e.name);
+                // C9-11: the select config = the device config with the
+                // density OVERridden by the request (AOSP value.density
+                // override law); density 0/invalid keeps the device config.
+                resources::ResTableConfig sel_cfg = resources::device_config();
+                if (c9_dfd && requested_density > 0)
+                    sel_cfg.density = (uint16_t)requested_density;
                 auto sel = rt.arsc().select_file(
-                    static_cast<uint32_t>(resid), entries,
-                    resources::device_config());
+                    static_cast<uint32_t>(resid), entries, sel_cfg);
                 if (sel) {
                     path = sel->path;
                     resource_drawable_path_by_resid_[static_cast<uint32_t>(resid)] =
                         sel->path;
-                    resource_drawable_density_by_resid_[static_cast<uint32_t>(resid)] =
-                        sel->selected_density();
+                    // C9-11: the recorded decode density = the REQUESTED
+                    // density (the C9-1 chain scales bucket → requested); the
+                    // plain getDrawable path keeps the bucket density.
+                    resource_drawable_density_by_resid_
+                        [static_cast<uint32_t>(resid)] =
+                        (c9_dfd && requested_density > 0)
+                            ? (uint16_t)requested_density
+                            : sel->selected_density();
                 }
             }
         }
@@ -69196,6 +70032,12 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
     {"textservices", "Landroid/view/textservice/TextServicesManager;"},
     {"restrictions", "Landroid/content/RestrictionsManager;"},
     {"dropbox", "Landroid/os/DropBoxManager;"},
+    // C9-26 (CODER 9, S188 cohort; astroloop vc6 HangarSurfaceView.<init>
+    // pc=121: SDK_INT=35 → AOSP Context.VIBRATOR_MANAGER_SERVICE exists
+    // since API 31 — the app's Kotlin cast-to-nonnull NPE'd on the null
+    // answer: "null cannot be cast to non-null type android.os.
+    // VibratorManager"). Never-null row per the F-C4-542 family.
+    {"vibrator_manager", "Landroid/os/VibratorManager;"},
 };
 
         const char* smp = kv_table_find(t_service_map,
@@ -78214,6 +79056,30 @@ measure_cm_done:;
             // open(String, int) — second arg is access mode
             asset_name = args[1].string_val;
         }
+        // ── C9-21 (CODER 9) — access-mode validation law ────────────────
+        // AOSP AssetManager.open(String, int accessMode): the mode MUST be
+        // one of ACCESS_UNKNOWN(0) / ACCESS_STREAMING(1) / ACCESS_RANDOM(2)
+        // / ACCESS_BUFFER(3) — Preconditions.checkArgument rejects anything
+        // else (API 28+). The mode only selects the native read strategy;
+        // the SERVED BYTES are identical (the runtime's one stream law),
+        // so the accepted modes flow through unchanged.
+        if (args.size() >= 2 &&
+            (args[1].type == DalvikType::INT32 ||
+             args[1].type == DalvikType::BOOLEAN)) {
+            const int64_t access_mode = dalvik_int_value(args[1]);
+            if (access_mode < 0 || access_mode > 3) {
+                std::cerr << "[C9-21] AssetManager.open access mode "
+                          << access_mode << " REJECTED (AOSP Preconditions "
+                          << "contract: 0..3)" << std::endl;
+                throw_deferred("Ljava/lang/IllegalArgumentException;",
+                               "Invalid access mode " +
+                                   std::to_string(access_mode),
+                               "C9-21");
+                result = DalvikValue::make_null();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
         // R-1 FIX (bridge duplicate site): same AOSP FileNotFoundException
         // contract as the try_recursive_invoke site — one contract, both
         // dispatch layers (the audit's duplicate-open-site finding).
```
