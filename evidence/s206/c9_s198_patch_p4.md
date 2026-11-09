**S198 rebased phase-3 patch part 4/4** (base `0979678e`; verified `git apply --check` APPLIES_CLEAN on a pristine `0979678e` worktree; the applied result is byte-identical to the in-container-verified tree that produced binary `4d832c255bed513c`: c9_phase3_laws_test **46/46**, density 36/36, zip 42/42, §5/§6 harness **48/49** with ONLY the P-NEW-5 size-word law failing, resourceval **30/31** with ONLY law 29 failing)

```diff
diff --git a/miniandroid/src/resources/plurals.h b/miniandroid/src/resources/plurals.h
new file mode 100644
index 00000000..29edd3e8
--- /dev/null
+++ b/miniandroid/src/resources/plurals.h
@@ -0,0 +1,60 @@
+// plurals.h — C9-20 (CODER 9) — CLDR plural-category selection law.
+//
+// AOSP contract (frameworks/base, core/java/android/content/res/PluralRules
+// ↔ icu4c PluralRules.forLocale().select(quantity)):
+//   * Resources.getQuantityString(id, quantity) takes the NUMBER and
+//     internally maps it to the CLDR category (zero/one/two/few/many/other)
+//     for the resource's locale, THEN reads the matching bag item.
+//   * The plurals bag keys are the android attrs (aapt2 8.13.2 ground
+//     truth, probe /tmp/plur_probe — resources.arsc byte dump):
+//       zero=0x01000004  one=0x01000005  two=0x01000006
+//       few=0x01000007   many=0x01000008 other=0x01000009
+//
+// Documented law subset (CLDR 46 rules, integer operands only — the
+// runtime resolves integer quantities; fractional rules are recorded as
+// a PENDING divergence, honest-miss to OTHER):
+//   default / en: one iff n == 1; else other
+//   fa:           one iff n == 0 or n == 1; else other
+//   ar:           zero 0 · one 1 · two 2 · few n%100∈[3,10] ·
+//                 many n%100∈[11,99] · else other
+//   ru:           one (i%10==1 && i%100!=11) · few (i%10∈[2,4] &&
+//                 !(i%100∈[12,14])) · many (integral rest) · other
+// Unknown locales take the default (en) rules — the same fallback icu4c
+// ships for unlisted languages.
+
+#ifndef MINIANDROID_RESOURCES_PLURALS_H
+#define MINIANDROID_RESOURCES_PLURALS_H
+
+#include <cstdint>
+#include <string>
+
+namespace miniandroid {
+namespace resources {
+
+// The CLDR plural categories — bag-key order matches the attr ids above.
+enum class PluralsQuantity : uint8_t {
+    ZERO = 0, ONE, TWO, FEW, MANY, OTHER,
+};
+
+// The aapt2-pinned bag keys (see header comment — ground truth above).
+constexpr uint32_t kPluralsKey[6] = {
+    0x01000004,  // zero
+    0x01000005,  // one
+    0x01000006,  // two
+    0x01000007,  // few
+    0x01000008,  // many
+    0x01000009,  // other
+};
+
+// CLDR selection law (pure, deterministic). locale is the BCP-47/ISO form
+// ("en", "fa-IR", "ar", "ru-RU" — only the primary subtag matters for the
+// documented subset). n is the integer quantity.
+PluralsQuantity cldr_quantity_law(const std::string& locale, int64_t n);
+
+// Bag-key lookup: the ARSC complex-entry key for a category.
+uint32_t plurals_bag_key(PluralsQuantity q);
+
+}  // namespace resources
+}  // namespace miniandroid
+
+#endif  // MINIANDROID_RESOURCES_PLURALS_H
diff --git a/miniandroid/src/resources/resource_runtime.cpp b/miniandroid/src/resources/resource_runtime.cpp
index e5984791..98ca0069 100644
--- a/miniandroid/src/resources/resource_runtime.cpp
+++ b/miniandroid/src/resources/resource_runtime.cpp
@@ -193,7 +193,9 @@ std::optional<uint32_t> ResourceRuntime::resolve_framework_file_color(uint32_t r
                     !tri_matches(it.state_selected, false) ||
                     !tri_matches(it.state_checked, false) ||
                     !tri_matches(it.state_window_focused, true) ||
-                    !tri_matches(it.state_activated, false))
+                    !tri_matches(it.state_activated, false) ||
+                    !tri_matches(it.state_focused, false) ||
+                    !tri_matches(it.state_hovered, false))
                     continue;   // requires a non-default state — not first match
                 if (it.has_color && it.color != 0) return it.color;
                 if (it.has_color && it.color_ref_id != 0)
diff --git a/miniandroid/src/runtime/execution_engine.cpp b/miniandroid/src/runtime/execution_engine.cpp
index b0417924..46609fa7 100755
--- a/miniandroid/src/runtime/execution_engine.cpp
+++ b/miniandroid/src/runtime/execution_engine.cpp
@@ -4003,10 +4003,45 @@ bool ExecutionEngine::stage_render_frame_impl(ExecutionResult& result, const Exe
                                 sl_it->second.first) {
                                 uint32_t c = 0;
                                 std::string p;
+                                const framework::ViewShadow::ViewNode::
+                                    BgStateItem* win = nullptr;
                                 if (framework::pick_state_list(
                                         sl_it->second.second, node->pressed,
-                                        node->enabled, node->selected, &c, &p)) {
+                                        node->enabled, node->selected, &c, &p,
+                                        node->checked, node->focused, false,
+                                        &win)) {
                                     if (p.empty() && c != 0) eff_bg_color = c;
+                                    // ── C9-19 (CODER 9): the matched item
+                                    // may carry a COMPILED ref
+                                    // (@drawable/@color as Res_value
+                                    // REFERENCE — no raw string). Resolve
+                                    // the identity through the ARSC router:
+                                    // table colors PAINT; file-backed
+                                    // identities are logged with their real
+                                    // path (provenance — never faked).
+                                    if (win && win->drawable_ref_id != 0) {
+                                        auto& art = resources::
+                                            ResourceRuntime::instance()
+                                                .arsc();
+                                        auto v = art.resolve_value(
+                                            win->drawable_ref_id);
+                                        if (v && (v->is_color() || v->is_int())) {
+                                            eff_bg_color = v->data;
+                                        } else if (v && v->is_string() &&
+                                                   !v->string_value.empty()) {
+                                            trace_engine_.info(
+                                                "ExecutionEngine",
+                                                "stage_render_frame",
+                                                "STATE-LIST C9-19 ref 0x" +
+                                                    [] (uint32_t r) {
+                                                        char b[16];
+                                                        std::snprintf(
+                                                            b, sizeof(b), "%08X", r);
+                                                        return std::string(b);
+                                                    }(win->drawable_ref_id) +
+                                                    " -> " + v->string_value);
+                                        }
+                                    }
                                 }
                             }
                             // F-053 (M9): GradientDrawable <shape> law. The
diff --git a/miniandroid/tests/c9_phase3_laws_test.cpp b/miniandroid/tests/c9_phase3_laws_test.cpp
new file mode 100644
index 00000000..0d4ede91
--- /dev/null
+++ b/miniandroid/tests/c9_phase3_laws_test.cpp
@@ -0,0 +1,512 @@
+// C9-4..C9-23 (CODER 9) — phase-3 law test.
+//
+// Pins the 20 resource-pipeline laws delivered in phase 3 (see Issue #521):
+//   C9-4  bitmap_preferred_config_law   — inPreferredConfig conversion
+//   C9-9  resample_bilinear             — Skia kLinear sampling
+//   C9-12 ArscParser name→id hash index — exact parity + wildcard fallback
+//   C9-13 ArscParser owned bytes        — post-free resolve safety
+//   C9-14 ResTable_typeSpec flags       — parse + OR-merge + attach
+//   C9-15 LIBRARY chunk                 — registry + dynamic-ref translation
+//   C9-16 parse_font_family             — REAL aapt2-compiled AXML (embedded)
+//   C9-17 select_font_face_law          — AOSP closest-face law
+//   C9-18 pick_state_list focused/hovered — first-match tri-states
+//   C9-20 cldr_quantity_law             — CLDR category subset + bag keys
+//   C9-23 bitmap_cache_identity_law     — deterministic cache identity
+//
+// Synthetic ARSC tables are crafted in-memory (the resource_config_selection
+// test pattern — no fixture APK dependency). The font-family AXML bytes are
+// aapt2 8.13.2 REAL toolchain output (embedded array, deterministic).
+//
+// Build: link with the full object set (Issue #521 ACH-1 §7 command shape).
+
+#include <framework/bitmap_shadow.h>
+#include <framework/state_list.h>
+
+#include <resources/arsc_parser.h>
+#include <resources/font_family.h>
+#include <resources/plurals.h>
+
+#include <cstdint>
+#include <cstdio>
+#include <cstring>
+#include <string>
+#include <vector>
+
+using namespace miniandroid;
+using namespace miniandroid::resources;
+namespace fw = miniandroid::framework;
+
+static int g_pass = 0, g_fail = 0;
+static void law(bool ok, int num, const char* what) {
+    if (ok) { ++g_pass; }
+    else {
+        ++g_fail;
+        std::printf("  LAW %02d FAIL: %s\n", num, what);
+    }
+}
+
+// ── synthetic ARSC builder (resource_config_selection pattern) ───────────
+static void put16(std::vector<uint8_t>& v, size_t off, uint16_t x) {
+    v[off] = (uint8_t)(x & 0xFF); v[off + 1] = (uint8_t)((x >> 8) & 0xFF);
+}
+static void put32(std::vector<uint8_t>& v, size_t off, uint32_t x) {
+    v[off] = (uint8_t)(x & 0xFF); v[off+1] = (uint8_t)((x>>8)&0xFF);
+    v[off+2] = (uint8_t)((x>>16)&0xFF); v[off+3] = (uint8_t)((x>>24)&0xFF);
+}
+static void append16(std::vector<uint8_t>& v, uint16_t x) { size_t o=v.size(); v.resize(o+2); put16(v,o,x); }
+static void append32(std::vector<uint8_t>& v, uint32_t x) { size_t o=v.size(); v.resize(o+4); put32(v,o,x); }
+
+static std::vector<uint8_t> build_string_pool(const std::vector<std::string>& strings) {
+    std::vector<uint8_t> offsets_blob, data_blob;
+    for (const auto& s : strings) {
+        append32(offsets_blob, (uint32_t)data_blob.size());
+        data_blob.push_back((uint8_t)s.size());
+        data_blob.push_back((uint8_t)s.size());
+        data_blob.insert(data_blob.end(), s.begin(), s.end());
+        data_blob.push_back(0);
+    }
+    while (data_blob.size() % 4) data_blob.push_back(0);
+    const uint32_t sc = (uint32_t)strings.size();
+    const uint32_t hdr = 28, strs = hdr + sc * 4;
+    std::vector<uint8_t> out;
+    append16(out, 0x0001); append16(out, (uint16_t)hdr); append32(out, strs + (uint32_t)data_blob.size());
+    append32(out, sc); append32(out, 0); append32(out, 1u << 8);
+    append32(out, strs); append32(out, 0);
+    out.insert(out.end(), offsets_blob.begin(), offsets_blob.end());
+    out.insert(out.end(), data_blob.begin(), data_blob.end());
+    return out;
+}
+
+// One bag (complex) entry: count maps {name, STRING value}, 28-byte config.
+struct BagMap { uint32_t key; uint32_t string_idx; };
+static std::vector<uint8_t> build_type_chunk_bag(uint8_t type_id,
+                                                 const std::vector<BagMap>& maps) {
+    const uint32_t n = (uint32_t)maps.size();
+    const uint16_t hdr = 20 + 28;
+    const uint32_t entries_start = hdr + 4;
+    // chunk = fixed(20) + config(28) + offsets(4) + entry(16) + maps(12n)
+    //        = entries_start + 16 + 12n  (entry starts AT entries_start)
+    const uint32_t chunk_size = entries_start + 16 + n * 12;
+    std::vector<uint8_t> out;
+    append16(out, 0x0201); append16(out, (uint16_t)hdr); append32(out, chunk_size);
+    out.push_back(type_id); out.push_back(0); append16(out, 0);
+    append32(out, 1); append32(out, entries_start);
+    for (int i = 0; i < 7; ++i) append32(out, 0);   // config: 28 zero bytes
+    append32(out, 0);  // offset[0]
+    // ResTable_entry complex: {size=16, flags=COMPLEX(1), key=0, parent=0, count=n}
+    append16(out, 16); append16(out, 0x0001); append32(out, 0);
+    append32(out, 0); append32(out, n);
+    for (const auto& m : maps) {
+        append32(out, m.key);
+        append16(out, 8); out.push_back(0); out.push_back(0x03);  // Res_value STRING
+        append32(out, m.string_idx);
+    }
+    return out;
+}
+
+// Simple STRING entry, 28-byte config.
+static std::vector<uint8_t> build_type_chunk_string(uint8_t type_id,
+                                                    uint32_t string_idx,
+                                                    uint32_t key_idx = 0) {
+    const uint16_t hdr = 20 + 28;
+    const uint32_t entries_start = hdr + 4;
+    // chunk = fixed(20) + config(28) + offsets(4) + entry(8) + value(8)
+    //        = entries_start + 16
+    const uint32_t chunk_size = entries_start + 16;
+    std::vector<uint8_t> out;
+    append16(out, 0x0201); append16(out, (uint16_t)hdr); append32(out, chunk_size);
+    out.push_back(type_id); out.push_back(0); append16(out, 0);
+    append32(out, 1); append32(out, entries_start);
+    for (int i = 0; i < 7; ++i) append32(out, 0);   // config: 28 zero bytes
+    append32(out, 0);
+    append16(out, 8); append16(out, 0); append32(out, key_idx);
+    append16(out, 8); out.push_back(0); out.push_back(0x03); append32(out, string_idx);
+    return out;
+}
+
+static std::vector<uint8_t> build_type_spec(uint8_t type_id, uint32_t flags) {
+    std::vector<uint8_t> out;
+    append16(out, 0x0202); append16(out, 16); append32(out, 16 + 4);
+    out.push_back(type_id); out.push_back(0); append16(out, 0);
+    append32(out, 1);
+    append32(out, flags);
+    return out;
+}
+
+// LIBRARY chunk (0x0203): {header(12), count, entry*{pkgId u32, name utf16[128]}}
+static std::vector<uint8_t> build_library_chunk(
+        const std::vector<std::pair<uint32_t, std::string>>& libs) {
+    const uint32_t n = (uint32_t)libs.size();
+    const uint32_t chunk_size = 12 + n * (4 + 256);
+    std::vector<uint8_t> out;
+    append16(out, 0x0203); append16(out, 12); append32(out, chunk_size);
+    append32(out, n);
+    for (const auto& l : libs) {
+        append32(out, l.first);
+        for (int i = 0; i < 128; ++i) {
+            uint16_t ch = i < (int)l.second.size() ? (uint16_t)l.second[i] : 0;
+            append16(out, ch);
+        }
+    }
+    return out;
+}
+
+struct TableSpec {
+    std::vector<std::string> global_strings;
+    std::vector<std::string> type_strings;
+    std::vector<std::string> key_strings;
+    // chunks inside the package body (spec + types + libraries)
+    std::vector<std::vector<uint8_t>> inner_chunks;
+    std::vector<std::pair<uint32_t, std::string>> libraries;  // top-level chunk
+    std::string package_name = "t";
+};
+
+static std::vector<uint8_t> build_table(const TableSpec& t) {
+    std::vector<uint8_t> pool = build_string_pool(t.global_strings);
+    std::vector<uint8_t> type_pool = build_string_pool(t.type_strings);
+    std::vector<uint8_t> key_pool = build_string_pool(t.key_strings);
+    std::vector<uint8_t> lib = build_library_chunk(t.libraries);
+
+    std::vector<uint8_t> inner;
+    for (const auto& c : t.inner_chunks)
+        inner.insert(inner.end(), c.begin(), c.end());
+
+    const uint32_t pkg_hdr = 288;
+    const uint32_t tso = pkg_hdr;
+    const uint32_t kso = tso + (uint32_t)type_pool.size();
+    const uint32_t pkg_size = pkg_hdr + (uint32_t)type_pool.size() +
+                              (uint32_t)key_pool.size() + (uint32_t)inner.size();
+
+    std::vector<uint8_t> pkg(pkg_hdr, 0);
+    put16(pkg, 0, 0x0200); put16(pkg, 2, (uint16_t)pkg_hdr);
+    put32(pkg, 4, pkg_size); put32(pkg, 8, 0x7f);
+    for (size_t i = 0; i < t.package_name.size() && i < 256; ++i)
+        pkg[12 + i * 2] = (uint8_t)t.package_name[i];
+    put32(pkg, 268, tso); put32(pkg, 272, 1); put32(pkg, 276, kso); put32(pkg, 280, 1);
+    pkg.insert(pkg.end(), type_pool.begin(), type_pool.end());
+    pkg.insert(pkg.end(), key_pool.begin(), key_pool.end());
+    pkg.insert(pkg.end(), inner.begin(), inner.end());
+
+    const uint32_t table_size = 12 + (uint32_t)pool.size() + (uint32_t)lib.size() + (uint32_t)pkg.size();
+    std::vector<uint8_t> out;
+    append16(out, 0x0002); append16(out, 12); append32(out, table_size);
+    append32(out, 1);   // packageCount
+    out.insert(out.end(), pool.begin(), pool.end());
+    out.insert(out.end(), lib.begin(), lib.end());
+    out.insert(out.end(), pkg.begin(), pkg.end());
+    return out;
+}
+
+// aapt2 8.13.2-compiled res/font-v22/c9font.xml (REAL toolchain bytes —
+// the ATTR-carrying variant: aapt2 font-XML processing writes the
+// android:font/fontWeight/fontStyle attrs into the -v22 file, the
+// base res/font/ file ships attr-less for the support-lib compat path;
+// probe: aapt2 dump xmltree ff.apk --file res/font-v22/c9font.xml).
+static const uint8_t kFontFamilyAxml[] = {
+    0x03, 0x00, 0x08, 0x00, 0xd0, 0x02, 0x00, 0x00, 0x01, 0x00, 0x1c, 0x00, 0xc8, 0x00, 0x00, 0x00,
+    0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
+    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0d, 0x00, 0x00, 0x00, 0x14, 0x00, 0x00, 0x00,
+    0x21, 0x00, 0x00, 0x00, 0x2d, 0x00, 0x00, 0x00, 0x37, 0x00, 0x00, 0x00, 0x43, 0x00, 0x00, 0x00,
+    0x4a, 0x00, 0x00, 0x00, 0x58, 0x00, 0x00, 0x00, 0x0a, 0x0a, 0x66, 0x6f, 0x6e, 0x74, 0x46, 0x61,
+    0x6d, 0x69, 0x6c, 0x79, 0x00, 0x04, 0x04, 0x66, 0x6f, 0x6e, 0x74, 0x00, 0x0a, 0x0a, 0x66, 0x6f,
+    0x6e, 0x74, 0x57, 0x65, 0x69, 0x67, 0x68, 0x74, 0x00, 0x09, 0x09, 0x66, 0x6f, 0x6e, 0x74, 0x53,
+    0x74, 0x79, 0x6c, 0x65, 0x00, 0x07, 0x07, 0x61, 0x6e, 0x64, 0x72, 0x6f, 0x69, 0x64, 0x00, 0x09,
+    0x09, 0x63, 0x39, 0x2d, 0x63, 0x75, 0x73, 0x74, 0x6f, 0x6d, 0x00, 0x04, 0x04, 0x66, 0x6f, 0x6e,
+    0x74, 0x00, 0x0b, 0x0b, 0x66, 0x6f, 0x6e, 0x74, 0x2d, 0x66, 0x61, 0x6d, 0x69, 0x6c, 0x79, 0x00,
+    0x2a, 0x2a, 0x68, 0x74, 0x74, 0x70, 0x3a, 0x2f, 0x2f, 0x73, 0x63, 0x68, 0x65, 0x6d, 0x61, 0x73,
+    0x2e, 0x61, 0x6e, 0x64, 0x72, 0x6f, 0x69, 0x64, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x61, 0x70, 0x6b,
+    0x2f, 0x72, 0x65, 0x73, 0x2f, 0x61, 0x6e, 0x64, 0x72, 0x6f, 0x69, 0x64, 0x00, 0x00, 0x00, 0x00,
+    0x80, 0x01, 0x08, 0x00, 0x18, 0x00, 0x00, 0x00, 0xac, 0x03, 0x01, 0x01, 0x32, 0x05, 0x01, 0x01,
+    0x33, 0x05, 0x01, 0x01, 0x3f, 0x05, 0x01, 0x01, 0x00, 0x01, 0x10, 0x00, 0x18, 0x00, 0x00, 0x00,
+    0x02, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x04, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,
+    0x02, 0x01, 0x10, 0x00, 0x38, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0xff, 0xff, 0xff, 0xff, 0x07, 0x00, 0x00, 0x00, 0x14, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00,
+    0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00,
+    0x08, 0x00, 0x00, 0x03, 0x05, 0x00, 0x00, 0x00, 0x02, 0x01, 0x10, 0x00, 0x60, 0x00, 0x00, 0x00,
+    0x04, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x06, 0x00, 0x00, 0x00,
+    0x14, 0x00, 0x14, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,
+    0x01, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x08, 0x00, 0x00, 0x01, 0x03, 0x00, 0x01, 0x7f,
+    0x08, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x08, 0x00, 0x00, 0x10,
+    0x90, 0x01, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0x08, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x03, 0x01, 0x10, 0x00, 0x18, 0x00, 0x00, 0x00,
+    0x04, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x06, 0x00, 0x00, 0x00,
+    0x02, 0x01, 0x10, 0x00, 0x60, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0xff, 0xff, 0xff, 0xff, 0x06, 0x00, 0x00, 0x00, 0x14, 0x00, 0x14, 0x00, 0x03, 0x00, 0x00, 0x00,
+    0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0x08, 0x00, 0x00, 0x01, 0x01, 0x00, 0x01, 0x7f, 0x08, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00,
+    0xff, 0xff, 0xff, 0xff, 0x08, 0x00, 0x00, 0x10, 0xbc, 0x02, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,
+    0x03, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x08, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00,
+    0x03, 0x01, 0x10, 0x00, 0x18, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0xff, 0xff, 0xff, 0xff, 0x06, 0x00, 0x00, 0x00, 0x02, 0x01, 0x10, 0x00, 0x60, 0x00, 0x00, 0x00,
+    0x0c, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x06, 0x00, 0x00, 0x00,
+    0x14, 0x00, 0x14, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,
+    0x01, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x08, 0x00, 0x00, 0x01, 0x02, 0x00, 0x01, 0x7f,
+    0x08, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x08, 0x00, 0x00, 0x10,
+    0x90, 0x01, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0x08, 0x00, 0x00, 0x10, 0x01, 0x00, 0x00, 0x00, 0x03, 0x01, 0x10, 0x00, 0x18, 0x00, 0x00, 0x00,
+    0x0c, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x06, 0x00, 0x00, 0x00,
+    0x03, 0x01, 0x10, 0x00, 0x18, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff,
+    0xff, 0xff, 0xff, 0xff, 0x07, 0x00, 0x00, 0x00, 0x01, 0x01, 0x10, 0x00, 0x18, 0x00, 0x00, 0x00,
+    0x02, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x04, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,
+};
+
+int main() {
+    std::printf("C9 phase-3 law test\n");
+
+    // ── F-A: C9-4 inPreferredConfig conversion (laws 1–5) ────────────────
+    {
+        std::vector<uint8_t> rgba = {0xFF, 0x80, 0x7F, 0xC0,  0x10, 0x20, 0x30, 0x40};
+        std::vector<uint8_t> orig = rgba;
+        std::string n1 = fw::bitmap_preferred_config_law(1, rgba);
+        law(n1 == "RGB_565", 1, "RGB_565 answers canonical name");
+        law(rgba[0] == (uint8_t)(((0xFF >> 3) * 255 + 15) / 31) &&
+            rgba[1] == (uint8_t)(((0x80 >> 2) * 255 + 31) / 63) &&
+            rgba[3] == 0xFF, 2, "RGB_565 quantization + opaque alpha");
+        std::vector<uint8_t> a8 = {1, 2, 3, 0xAB};
+        std::string n2 = fw::bitmap_preferred_config_law(0, a8);
+        law(n2 == "ALPHA_8" && a8[0] == 0 && a8[1] == 0 && a8[2] == 0 &&
+            a8[3] == 0xAB, 3, "ALPHA_8 keeps only alpha");
+        std::vector<uint8_t> a4 = {0xF1, 0xE2, 0xD3, 0xC4};
+        std::string n3 = fw::bitmap_preferred_config_law(2, a4);
+        law(n3 == "ARGB_4444" && a4[0] == 0xF0 && a4[1] == 0xE0, 4,
+            "ARGB_4444 masks low nibble");
+        std::vector<uint8_t> p = orig;
+        std::string n4 = fw::bitmap_preferred_config_law(3, p);
+        law(n4 == "ARGB_8888" && p == orig, 5, "8888 passthrough");
+    }
+
+    // ── F-B: C9-9 bilinear (laws 6–10) ───────────────────────────────────
+    {
+        fw::StoredBitmap src;
+        src.width = 2; src.height = 2;
+        src.rgba = {0, 0, 0, 255,   200, 0, 0, 255,
+                    0, 200, 0, 255, 200, 200, 0, 255};
+        std::vector<uint8_t> out;
+        fw::resample_bilinear(src, 2, 2, out);
+        law(out == src.rgba, 6, "identity scale byte-exact");
+        fw::resample_bilinear(src, 3, 3, out);
+        // center pixel (1,1): halfway between all four = (100, 100, 0)
+        const uint8_t* c = &out[((size_t)1 * 3 + 1) * 4];
+        law(std::abs((int)c[0] - 100) <= 1 && std::abs((int)c[1] - 100) <= 1 &&
+            c[3] == 255, 7, "half-point center = 4-texel average");
+        fw::resample_bilinear(src, 1, 1, out);
+        const uint8_t* q = &out[0];
+        law(std::abs((int)q[0] - 100) <= 1, 8, "downsample to 1x1 = mean");
+        bool in_range = true;
+        for (size_t i = 0; i < out.size(); ++i)
+            if ((i % 4) != 3 && out[i] > 200) in_range = false;
+        law(in_range, 9, "downsample RGB stays within source range");
+        fw::StoredBitmap degenerate;
+        fw::resample_bilinear(degenerate, 4, 4, out);
+        law(out.size() == 64, 10, "degenerate source safe (zero-filled)");
+    }
+
+    // ── F-C/D/E/F: ARSC laws (laws 11–24) ────────────────────────────────
+    {
+        TableSpec t;
+        t.global_strings = {"res/layout/a.xml", "res/layout/b.xml",
+                            "res/values/strings.xml"};
+        t.type_strings = {"layout", "string"};
+        t.key_strings = {"activity_a", "activity_b", "app_name"};
+        // type 1 (layout): bag entry on key 0? layout entries must be
+        // SIMPLE (file refs) — bag on "app_name" (type 2, entry 2).
+        t.inner_chunks.push_back(build_type_chunk_string(1, 0));      // layout/activity_a
+        t.inner_chunks.push_back(build_type_spec(1, 0x02));           // spec layout: flag 2
+        t.inner_chunks.push_back(build_type_chunk_string(2, 2, 2));   // string/app_name (key idx 2)
+        t.inner_chunks.push_back(build_type_spec(2, 0x00000001 | 0x00000002));
+        t.libraries = {{0x02, "t"}};
+        auto table = build_table(t);
+
+        // C9-13: parse from a buffer that dies immediately after.
+        ArscParser p13;
+        {
+            std::vector<uint8_t> temp = table;
+            bool ok = p13.parse(temp);
+            law(ok, 11, "C9-13: parse from temporary buffer");
+        }
+        auto resolved = p13.resolve(0x7f010000);
+        law(resolved.has_value() && !resolved->configs.empty(), 12,
+            "C9-13: resolve after source buffer freed");
+
+        ArscParser p;
+        law(p.parse(table), 13, "crafted table parses");        // 0x7f010000 = pkg 0x7f, type 1, entry 0 (layout/activity_a)
+        auto id0 = p.find_id("t", "layout", "activity_a");
+        auto id1 = p.find_id("t", "layout", "activity_b");
+        auto id2 = p.find_id("t", "string", "app_name");
+        law(id0 && *id0 == 0x7f010000, 14, "C9-12: hash index exact hit (a)");
+        law(id2 && *id2 == 0x7f020000, 15, "C9-12: hash index exact hit (b)");
+        law(!id1.has_value(), 16, "C9-12: exact miss = nullopt (no wildcard rescue)");
+        // C9-12 parity: brute scan over resolve()'s entries for the same name.
+        bool parity = true;
+        const char* names[] = {"activity_a", "app_name"};
+        const char* types[] = {"layout", "string"};
+        for (int i = 0; i < 2; ++i) {
+            auto via_index = p.find_id("t", types[i], names[i]);
+            std::optional<uint32_t> via_scan;
+            for (uint32_t tid = 1; tid <= 2; ++tid)
+                for (uint32_t eid = 0; eid < 8; ++eid) {
+                    uint32_t rid = (0x7f << 24) | (tid << 16) | eid;
+                    auto r = p.resolve(rid);
+                    if (r && !r->configs.empty() && r->configs.front().name == names[i] &&
+                        r->type_name == types[i]) { via_scan = rid; break; }
+                }
+            if (via_index != via_scan) parity = false;
+        }
+        law(parity, 17, "C9-12: index == brute-scan parity");
+        // wildcard path (empty type) still answers through the scan.
+        auto wild = p.find_id("t", "", "app_name");
+        law(wild && *wild == 0x7f020000, 18, "C9-12: wildcard (empty type) scan");
+
+        // C9-14: spec flags attach.
+        auto r1 = p.resolve(0x7f010000);
+        law(r1 && r1->configs.front().spec_flags == 0x02, 19,
+            "C9-14: spec flags parsed + attached (0x02)");
+        auto r2 = p.resolve(0x7f020000);
+        law(r2 && r2->configs.front().spec_flags == 0x03, 20,
+            "C9-14: spec flags = 0x03 (entry flags law)");
+
+        // C9-15: library registry + translation.
+        law(p.libraries().size() == 1 &&
+            p.libraries().count(0x02) == 1 && p.libraries().at(0x02) == "t", 21,
+            "C9-15: LIBRARY chunk registry");
+        auto dyn = p.translate_dynamic_reference(0x02000000 | 0x010000);
+        law(dyn && *dyn == 0x7f010000, 22,
+            "C9-15: dynamic ref translated to same-name package");
+        law(!p.translate_dynamic_reference(0x7f010000).has_value(), 23,
+            "C9-15: non-library id = honest nullopt");
+        TableSpec t2 = t;
+        t2.libraries = {{0x02, "zzz"}};
+        auto table2 = build_table(t2);
+        ArscParser p2;
+        p2.parse(table2);
+        law(!p2.translate_dynamic_reference(0x02000000).has_value(), 24,
+            "C9-15: no same-name package = honest nullopt");
+    }
+
+    // ── F-G: C9-16 font-family parse on REAL aapt2 bytes (laws 25–26) ────
+    {
+        FontFamily fam = parse_font_family(
+            std::vector<uint8_t>(kFontFamilyAxml,
+                                 kFontFamilyAxml + sizeof(kFontFamilyAxml)),
+            "res/font/c9font.xml");
+        law(fam.valid() && fam.name == "c9-custom" && fam.faces.size() == 3, 25,
+            "C9-16: family name + 3 faces from REAL aapt2 AXML");
+        law(fam.faces.size() == 3 && fam.faces[1].weight == 700 &&
+            fam.faces[2].italic && fam.faces[0].weight == 400, 26,
+            "C9-16: weight/style attributes parsed");
+    }
+
+    // ── F-H: C9-17 closest-face law (laws 27–31) ─────────────────────────
+    {
+        std::vector<FontFaceDecl> faces = {
+            {"@font/r", 0, 400, false, "x"},
+            {"@font/b", 0, 700, false, "x"},
+            {"@font/i", 0, 400, true, "x"},
+            {"@font/bi", 0, 700, true, "x"},
+        };
+        law(select_font_face_law(faces, 700, false) == 1, 27,
+            "C9-17: bold request -> 700 normal face");
+        law(select_font_face_law(faces, 400, true) == 2, 28,
+            "C9-17: italic dominance over weight distance");
+        law(select_font_face_law(faces, 500, false) == 0, 29,
+            "C9-17: 500 tie -> FIRST document-order face (400 vs 700)");
+        auto req = typeface_style_request(kTypefaceBoldItalic);
+        law(req.weight == 700 && req.italic, 30, "C9-17: BOLD_ITALIC -> 700+italic");
+        law(select_font_face_law(faces, kTypefaceBoldItalic) == 3, 31,
+            "C9-17: style-bits overload picks the bold-italic face");
+    }
+
+    // ── F-I: C9-18 focused/hovered first-match (laws 32–34) ──────────────
+    {
+        using BgItem = framework::ViewShadow::ViewNode::BgStateItem;
+        std::vector<BgItem> items(2);
+        // item 0: state_focused=true, color red
+        items[0].state_focused = 1; items[0].color = 0xFFFF0000;
+        items[0].has_color = true;
+        // item 1: fallback (all wildcards), color blue
+        items[1].color = 0xFF0000FF; items[1].has_color = true;
+        uint32_t c = 0; std::string pth;
+        const BgItem* win = nullptr;
+        law(framework::pick_state_list(items, false, true, false, &c, &pth,
+                                       false, false, false, &win) &&
+            c == 0xFF0000FF, 32,
+            "C9-18: default state skips the focused item (was wildcard bug)");
+        law(framework::pick_state_list(items, false, true, false, &c, &pth,
+                                       false, true, false, &win) &&
+            c == 0xFFFF0000, 33,
+            "C9-18: focused view picks the focused item");
+        std::vector<BgItem> hover(2);
+        hover[0].state_hovered = 1; hover[0].has_color = true;
+        hover[0].color = 0xFF00FF00;
+        hover[1].has_color = true; hover[1].color = 0xFF0000FF;
+        law(framework::pick_state_list(hover, false, true, false, &c, &pth,
+                                       false, false, true) &&
+            c == 0xFF00FF00, 34,
+            "C9-18: hovered view picks the hovered item");
+    }
+
+    // ── F-J: C9-20 CLDR selection (laws 35–42) ───────────────────────────
+    {
+        using Q = PluralsQuantity;
+        law(cldr_quantity_law("en-US", 1) == Q::ONE, 35, "en 1 -> ONE");
+        law(cldr_quantity_law("en", 0) == Q::OTHER, 36, "en 0 -> OTHER");
+        law(cldr_quantity_law("fa-IR", 0) == Q::ONE &&
+            cldr_quantity_law("fa", 1) == Q::ONE &&
+            cldr_quantity_law("fa", 2) == Q::OTHER, 37,
+            "fa 0/1 -> ONE, 2 -> OTHER (Persian zero law)");
+        law(cldr_quantity_law("ar", 0) == Q::ZERO &&
+            cldr_quantity_law("ar", 1) == Q::ONE &&
+            cldr_quantity_law("ar", 2) == Q::TWO, 38, "ar 0/1/2 exact");
+        law(cldr_quantity_law("ar", 5) == Q::FEW &&
+            cldr_quantity_law("ar", 20) == Q::MANY &&
+            cldr_quantity_law("ar", 150) == Q::MANY, 39,
+            "ar few/many windows (n%100 3-10 / 11-99)");
+        law(cldr_quantity_law("ru", 21) == Q::ONE &&
+            cldr_quantity_law("ru", 3) == Q::FEW &&
+            cldr_quantity_law("ru", 11) == Q::MANY, 40,
+            "ru one/few/many exceptions");
+        law(plurals_bag_key(Q::OTHER) == 0x01000009 &&
+            plurals_bag_key(Q::ZERO) == 0x01000004, 41,
+            "C9-20: bag keys == aapt2-pinned attrs (probe-verified)");
+        // bag walk through the crafted parser: plurals entry on type 3.
+        TableSpec t3;
+        t3.global_strings = {"no items", "one item", "%d items"};
+        t3.type_strings = {"plurals"};
+        t3.key_strings = {"c9_items"};
+        t3.inner_chunks.push_back(build_type_chunk_bag(
+            1, {{kPluralsKey[1], 1}, {kPluralsKey[5], 2}}));  // one + other
+        auto t3b = build_table(t3);
+        ArscParser p3;
+        law(p3.parse(t3b), 42, "C9-20: plurals bag table parses");
+        auto pr = p3.resolve(0x7f010000);
+        law(pr && pr->configs.front().is_complex &&
+            pr->configs.front().complex_keys.size() == 2, 43,
+            "C9-20: bag entry exposes complex keys for the engine walk");
+    }
+
+    // ── F-K: C9-23 cache identity (laws 44–46) ───────────────────────────
+    {
+        const uint8_t bytes_a[] = {1, 2, 3, 4};
+        const uint8_t bytes_b[] = {1, 2, 3, 5};
+        fw::BitmapCacheIdentityInput in;
+        in.src_bytes = bytes_a; in.src_len = 4;
+        in.source_desc = "res/drawable/x.png";
+        in.source_density = 240; in.target_density = 420;
+        in.sample_size = 1; in.config = 3; in.density_scaled = true;
+        std::string id1 = fw::bitmap_cache_identity_law(in);
+        std::string id2 = fw::bitmap_cache_identity_law(in);
+        law(id1 == id2 && id1.find("res/drawable/x.png") != std::string::npos,
+            44, "C9-23: identity deterministic + provenance suffix");
+        fw::BitmapCacheIdentityInput inb = in;
+        inb.src_bytes = bytes_b;
+        law(fw::bitmap_cache_identity_law(inb) != id1, 45,
+            "C9-23: different bytes -> different identity");
+        fw::BitmapCacheIdentityInput inc = in;
+        inc.sample_size = 2;
+        law(fw::bitmap_cache_identity_law(inc) != id1, 46,
+            "C9-23: different opts -> different identity");
+    }
+
+    std::printf("c9_phase3_laws_test: %d/%d PASS\n", g_pass, g_pass + g_fail);
+    return g_fail == 0 ? 0 : 1;
+}
```
