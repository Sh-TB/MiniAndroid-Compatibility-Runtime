# CODER 9 — Base Resources, Assets & Image Pipeline · Achievement Log

**Role:** CODER 9 — generic Android Resources / Assets / Bitmap / Drawable / Typeface foundation.
**Repository:** Sh-TB/MiniAndroid-Compatibility-Runtime (this Issue is my complete work log — no commits, no pushes, no other channel).
**Base SHA:** `25b5a01b2313d681d2dd24d1d4c108110f13395a` (branch `coder9/c9-resource-laws`, local sandbox only; the manager reviews/integrates).
**Deliverable:** unified patch (581 lines, source-only) pasted in the first comment of this Issue.

---

## ACH-1 [IMPLEMENTED] [TESTED] — C9-1: BitmapFactory.Options density law (decode-time)

**1. Original failure.** `BitmapFactory.decodeResource` ignored the SELECTED resource bucket's density entirely: `BitmapShadow::dispatch` received `density` from the engine resolver and dropped it (`bitmap_shadow.cpp`, old line ~262: `f240_decode_with_options(bytes, path, heap_, opts)` — no density argument). `Options.inDensity/inTargetDensity/inScaled` were never read. Every app that decoded a resource and measured it (`getWidth()` puzzle-board math, Glide/Coil override sizing, wrap_content consumers of decoded bitmaps) got RAW encoded dims instead of AOSP density-scaled dims.

**2. Why generic.** AOSP `BitmapFactory.decodeResourceStream` + native `BitmapFactory.cpp` scale EVERY resource decode by `targetDensity/inDensity`. Density is a core resource-table semantic (ResTable_config), not an app behavior.

**3. Source-backed expected behavior** (aosp-mirror/platform_frameworks_base, `graphics/java/android/graphics/BitmapFactory.java`, verified at master):
- `decodeResourceStream`: `value.density == DENSITY_DEFAULT(0) → opts.inDensity = 160`; `DENSITY_ANY(0xFFFE) → DENSITY_NONE(0xFFFF)`; else `value.density`. `opts.inTargetDensity = display densityDpi` when 0. Seeds are written back onto the app-visible Options.
- native: scale applies iff `inScaled && inDensity!=0 && inDensity!=DENSITY_NONE && inTargetDensity!=0 && inDensity!=inTargetDensity`; `scale = target/in_density`; `scaledWidth = (int)(dim*scale + 0.5f)`.
- `setDensityFromOptions`: bitmap marked `inDensity`, then `inTargetDensity` when scaled. **`Options` has NO public `outDensity` field** (verified against the API-34 class layout).
- bounds-only pass: out* = RAW dims, null return, no scaling.

**4. Root cause.** The decode-time half of the density law never existed; only the draw-time half (`g04_image_draw_rect`, execution_engine.cpp) was implemented. `out*` also carried raw dims even with `inSampleSize` (AOSP: final dims).

**5. Implementation.**
- Pure, unit-testable law `bitmap_factory_density_law()` (declared in `bitmap_shadow.h`) — sample → density-scale → final dims + `bitmap_density` (setDensityFromOptions result).
- `f240_decode_with_options(..., int32_t resource_density = -1)`: decodeResourceStream seeding (resource path only; decodeStream/File/ByteArray never seed — AOSP parity), opts read/write-back, bounds→RAW, full-decode→FINAL out*, resample chain raw→sample→scale, allocation-safety refusal (1<<24 px ceiling, same as g04) logged loudly.
- `decodeResource` call site passes the resolver's selected-bucket density (`(int32_t)density`).
- `StoredBitmap` provenance fields: `density, source_density, target_density, source_width, source_height, sample_size, density_scaled`. **Provenance law:** `source_desc` stays the PURE zip path (route_bitmap_object re-uses it as a zip path — the old `#sample` suffix polluted it); law fingerprint lives in the new fields.
- Removed the old desc-pollution (`desc + "#sampleN"`).

**6. Changed files.** `miniandroid/src/framework/bitmap_shadow.{h,cpp}`.

**7. Build & test commands.**
```
cd miniandroid && make -j$(nproc) all
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include \
  -o build/c9_bitmap_density_law_test tests/c9_bitmap_density_law_test.cpp \
  build/apk/*.o build/dex/*.o build/runtime/*.o build/diagnostics/*.o build/resources/*.o \
  build/renderer/*.o build/gles/*.o build/fonts/*.o build/framework/*.o build/api/*.o \
  build/storage/*.o build/webview/*.o build/quickjs/*.o build/jni/*.o build/audio/*.o \
  -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
  -lsqlite3 -lssl -lcrypto -lmpg123 -lsndfile
./build/c9_bitmap_density_law_test
```

**8. Hashes.** Runtime binary `84a516570720699f3b5fa8d9c6e9b157009d464eff76cc95775b00994b5a6fb2`; fixture APK `5010f8178f026510c86e98e6b17014a6525b9ca5bcbca1d04817baf36729ae46` (post-processed, deterministic); screenshot @420 `c056ac343a65c29e…` @160 `659b6727a238b278…`.

**9. Before/after.** BEFORE: decodeResource of `res/drawable-hdpi/c9_photo.png` (60x30) at 420dpi → 60x30; opts ignored; `out*`=raw. AFTER → `105x53` (= (int)(60*1.75+0.5) × (int)(30*1.75+0.5)), `opts.inDensity=240` / `inTargetDensity=420` seeded and app-visible; `inSampleSize=2` composes → `53x26`; bounds pass → RAW `60x30` + `mime=image/png`; nodpi → unscaled `40x20`. Engine log line carries the full fingerprint: `[BITMAP-FACTORY] decoded … (105x53 src=60x30 sample=1 density=240->420 SCALED mime=image/png)`.

**10. View/draw provenance.** §6 harness: APK entry `res/drawable-hdpi-v4/c9_photo.png` → ARSC `select_file` (hdpi bucket, density 240) → resolver bytes → f240 law → ImageView `setImageResource` node → engine frame walk → screenshot pixels (green-family region x4-50,y34-90). Full harness: `scripts/c9/validate_c9_resources.sh` → 41/41 PASS.

**11. Regression.** `resource_config_selection_test` 48/48, `resource_core_law_test` 42/42, `resource_hostile_test` 18/18 — zero regressions.

**12. Limitations.** Nearest-neighbour resample (bilinear stays a registered runtime gap, unchanged); zero-scaled dims clamp to 1 (recorded divergence — AOSP can fail the decode); density>1<<24 px scales refuse with a loud diagnostic; `inPreferredConfig/inMutable/inPremultiplied` still ignored (PENDING, next phase).

---

## ACH-2 [IMPLEMENTED] [TESTED] — C9-2: AssetFileDescriptor data-offset law (openFd/openRawResourceFd)

**1. Original failure.** `AssetManager.openFd` (and `openRawResourceFd`) seeded `AssetFileDescriptor.startOffset` with `ZipEntry.offset` — the LOCAL FILE HEADER offset (apk_parser.h:159, set from `cde.relative_offset_local_header`), not the entry DATA offset. Any app seeking the raw fd (`FileInputStream(fd).getChannel().position(afd.getStartOffset())`, SoundPool/media AFD loads) read LFH bytes (30 + name + extra) instead of asset data.

**2. Why generic.** AOSP `AssetManager2.openFd → Asset`: startOffset = offset of the entry's data inside the APK (APPNOTE.TXT §4.3.7). One law for every APK.

**3. Source-backed expected behavior.** `data_offset = LFH_offset + 30 + LFH.file_name_length + LFH.extra_field_length`, resolved from the LOCAL header because LFH and CDE extra fields may legally differ (APPNOTE.TXT §4.4.11).

**4. Root cause.** The ZIP layer never computed the data offset; `extract_entry_using_central_dir_` did it correctly per-extraction (apk_parser.cpp:520) but the AFD path consumed the un-corrected `offset` field.

**5. Implementation.** `ZipEntry` gains `uint64_t data_offset` + `bool has_data_offset` (honest-miss flag). `parse_central_directory` resolves it from the LFH itself with bounds+overflow guards and a signature check; hostile archives leave `has_data_offset=false` and BOTH engine call sites (openFd dalvik_engine.cpp ~65980, openRawResourceFd ~46459) fall back LOUDLY (`[ASSET-FD] C9-2 WARNING`) instead of silently pretending. Diagnostics now print both: `off=<data> (lfh=<lfh>)`.

**6. Changed files.** `miniandroid/src/apk/apk_parser.{h,cpp}`, `miniandroid/src/dex/dalvik_engine.cpp` (2 AFD sites).

**7. Build & test commands.**
```
g++ -std=c++17 -w -g -O1 -Isrc -o build/c9_zip_data_offset_law_test \
  tests/c9_zip_data_offset_law_test.cpp build/apk/apk_parser.o build/apk/manifest_reader.o \
  build/resources/string_pool.o build/resources/arsc_parser.o build/resources/res_id.o \
  build/resources/res_config.o build/dex/mutf8.o -lz -lpthread
./build/c9_zip_data_offset_law_test
```

**8. Hashes.** Law-1 fd-window SHA-256 `c20543f9e6e71e690bac8634545464f2c29d688cc69acf1b175251fc29df78ba` (raw-fd read == independent extraction, two read paths agree); AFD window in fixture: `data_offset=8638 afd_startOffset=8638 length=115 sha256=8259064cffadba0a405bc59fb3e010bbfeb0fa2fd377f9848856aa5b6ef42510`.

**9. Before/after.** BEFORE: startOffset = LFH offset (for the fixture's stored PNG entry: 56 bytes BEFORE the real data — the PNG magic would NOT be at the seek point). AFTER: `startOffset == zip data offset` byte-exact (asserted in harness step [9] against an independent python zipfile re-read of the same APK).

**10. View/draw provenance.** Harness step [9]: engine-run `CASE05 afd startOffset=8638 length=115 declared=115` + `createInputStream` 115 bytes == `AssetManager.open` 115 bytes (match=true) + fd-window SHA printed. Also proves compressed entries: `openFd(c9_compressed.txt DEFLATE) → FileNotFoundException` (AOSP nested-file law) while `open()` serves the 2000 inflated bytes.

**11. Regression.** Same trio: 48/48, 42/42, 18/18. The law test itself: **42/42** — 6 crafted-ZIP laws: LFH-extra≠CDE-extra discriminator, plain, multi-entry, data-descriptor (streaming), prepended-stub offsets, hostile LFH → honest miss.

**12. Limitations.** ZIP64 archives unhandled (pre-existing parser scope); the A/B on the BASE parser is documented from source + the runtime log line (the old struct had no data_offset field to compare against — the concept did not exist).

---

## ACH-3 [IMPLEMENTED] [TESTED] — C9-3: VectorDrawable intrinsic law (Resources.getDrawable)

**1. Original failure.** `Resources.getDrawable(R.drawable.c9_vector)` materialized a bare drawable shell with `__dr_width__/__dr_height__` unset → `getIntrinsicWidth/Height` answered **-1x-1** for every XML vector. Every wrap_content/Glide-style consumer of vector drawables saw "no intrinsic size".

**2. Why generic.** AOSP `VectorDrawable.inflate` answers intrinsics from `android:width/height` evaluated at the target density. Vector drawables are the modern APK icon format.

**3. Source-backed expected behavior.** VectorDrawable intrinsic = android:width/height dimension at the drawable's target density (`applyDimension` law: dp×density/160, px as-is, pt×density/72, in×density, mm×density/25.4).

**4. Root cause.** getDrawable's materialization only filled intrinsics for RASTER paths (`raster` branch); the XML branch kept the shell at -1 (with a comment assuming "intrinsic -1 per AOSP when there is no bitmap" — wrong for VectorDrawable, which HAS intrinsic dims without a bitmap).

**5. Implementation.** Non-raster branch (`ext == xml/axml`): AXML-parse the resolved bytes; on a `<vector>` root, read `android:width/height` dimensions and set `__dr_width__/__dr_height__` = (int)(px+0.5). Loud `[RES] C9-3 vector intrinsic …` diagnostic. The existing S109 ROOT-033b `getIntrinsicWidth/Height` bridge then answers app-visible intrinsics unchanged.

**6. Changed files.** `miniandroid/src/dex/dalvik_engine.cpp` (one branch in the getDrawable law).

**7/8. Commands & hashes.** Same build command as ACH-1; same binary. Fixture evidence: `CASE06 vector drawable=intrinsic 126x126` (48dp @ 420dpi → 126px) + `[RES] C9-3 vector intrinsic 126x126 (density 420) for res/drawable/c9_vector.xml`.

**9. Before/after.** BEFORE: `intrinsic -1x-1` (observed in the first harness run, log preserved). AFTER: `intrinsic 126x126`.

**10. View/draw provenance.** The same vector paints through the View chain: blue-family pixels (#3F51B5/#FFC107 triangle → blue region x14-114, y182-284) present in ALL THREE density runs' screenshots.

**11. Regression.** Same trio — zero regressions.

**12. Limitations.** Only the root `<vector>` dims; `<adaptive-icon>`/nested intrinsic chains stay -1 (pre-existing); animated-vector PENDING.

---

## Synthetic test harness (§5) — [IMPLEMENTED] [TESTED] 41/41

`miniandroid/tests/fixtures/c9_resources/` — aapt2+ECJ+D8 REAL toolchain build (vendored `tools/`, android-34 stubs restored from Maven Central per `scripts/build/bootstrap_toolchain.sh` coordinates). `scripts/c9/validate_c9_resources.sh` builds + post-processes (one entry rewritten DEFLATE for the compressed-asset case) + runs the engine under 4 device configs (420/en-US, 420/fa-IR, 160/en-US, 240/en-US) + asserts every case:

| §5 case | Status | Evidence line |
|---|---|---|
| 1 PNG drawable | PASS | CASE01 natural=105x53 (hdpi→420) |
| 2 WebP drawable | PASS | CASE02 bounds=24x12 mime=image/webp natural=63x32 |
| 3 Nested asset | PASS | CASE03 list=[deep]; 29 bytes; head=43392d4e45535445 |
| 4 Compressed asset | PASS | open 2000 bytes; openFd → FileNotFoundException |
| 5 Uncompressed asset | PASS | AFD startOffset=8638=len(zip data offset), len=115, stream==open bytes |
| 6 VectorDrawable | PASS | CASE06 intrinsic 126x126 (C9-3); blue pixels on screen |
| 7 Density-qualified | PASS | @160→mdpi 40x20, @240→hdpi 60x30 scale 1.0, @420→hdpi×1.75=105x53 |
| 8 Locale-qualified | PASS | en-US 'Hello C9' vs fa-IR 'سلام کد۹' |
| 9 Custom font | PASS | CASE09 typeface=loaded (assets/fonts/c9_font.ttf, DejaVuSans) |
| 10 Missing resource | PASS | decodeResource→null; getString→NotFoundException |
| 11 Missing asset | PASS | open→FileNotFoundException |
| 12 Invalid image | PASS | decodeResource(R.raw.c9_invalid)→null (no fake pixels) |
| +nodpi law | PASS | CASE13 40x20 unscaled at 420 (DENSITY_NONE) |
| +View chain §6 | PASS | CASE14 children=3, texts=Hello C9 |

**§6 pixel law (not "non-white ⇒ success"):** per-run color-family assertions — @160 paints the RED mdpi pattern (2618 px), @240/@420 paint the GREEN hdpi pattern (2784/2832 px), the blue vector paints in all runs (~4100 px). The painted pixels CHANGE with the selected bucket — bucket selection proven at the framebuffer level. Screenshot SHA-256s: 420/en `c056ac34…`, 160/en `659b6727…`, 240/en `542f053a…`, 420/fa `8f1f9f42…`.

**One-command reproduction:**
```
bash scripts/c9/validate_c9_resources.sh /tmp/c9_evidence
```

## Resource coverage matrix (initial inspection — §4)

The full 10-column matrix (resource type / entry / current impl / AOSP semantics / qualifier rules / decoder / missing behavior / dependents / tests / required proof) was built during inspection; the highest-impact generic laws it surfaced are ACH-1..3 above. Condensed state per area:

- **ARSC parse/lookup:** strong — dense/OFFSET16/SPARSE/COMPACT encodings, structured ResolutionResult chain, bag inheritance, theme overlays. Gaps: name→id hash (find_id O(n)), TypeSpec mask skipped, LIBRARY chunk absent, dangling `data_` pointer (latent). PENDING (next phase).
- **Config matching:** AOSP-verbatim isBetterThan/match incl. density buckets + version tie-break; locale script/BCP-47 simplified (documented). Observed working at 160/240/420 + fa-IR in this harness.
- **AssetManager:** open/list/openFd solid after C9-2; ASSETS-WITHOUT-ARSC law in place. openFd startOffset [FIXED]; AFD raw-fd seek path proven byte-level.
- **Drawable:** ColorDrawable/GradientDrawable/LayerDrawable/StateList paths live in the walk; vector raster has clip-path/gradient gaps (named errors, pre-existing); intrinsic law [FIXED] (C9-3).
- **BitmapFactory:** inJustDecodeBounds + inSampleSize existed; density law [FIXED] (C9-1); Bitmap.compress=false (explicit-unsupported), recycle no-op — PENDING.
- **Typeface:** createFromAsset/createFromFile + startup scan of res/assets .ttf/.otf work (CASE09); font-family XML + weight axes absent — PENDING.
- **Image loading (Glide/Coil):** decodeResource/Stream bytes resolution + bounds contract + (now) density law give the generic substrate; cache-identity contract not yet formalized — PENDING.

## Regression summary
`resource_config_selection_test` 48/48 · `resource_core_law_test` 42/42 · `resource_hostile_test` 18/18 · C9-1 laws 36/36 · C9-2 laws 42/42 · C9 harness 41/41. All executed on the C9 binary at base `25b5a01…` + patch.

## Known limitations / next steps (priority order)
1. `inPreferredConfig/inMutable/inPremultiplied` honor + `Bitmap.compress` via the existing PNGWriter.
2. ARSC name→id hash index + TypeSpec mask + LIBRARY chunk (O(n) find_id today).
3. font-family XML + weight/style selection beyond filename heuristics.
4. StateList `state_focused/state_hovered` + item-drawable ref resolution (currently unresolved strings).
5. Bilinear resample for createScaledBitmap(filter=true).
6. Glide/Coil cache-identity contract (key = APK entry SHA + selected config + opts fingerprint — fields now exist on StoredBitmap).

## Security note
The access token is used env-var only (`GH_TOKEN`), never printed, never committed, never embedded in any file, patch, log or this Issue. No pushes to main; no branches created on the remote.


---

## UPDATE (session 2) — full reconstruction, re-verification, and durable GitHub record

The sandbox recycle destroyed the local tree; everything was rebuilt this session from this Issue's documented contracts and re-verified from scratch at base `25b5a01` + patch #1:

- **Patch #2 posted (comment 2)** — the previously local-only synthetic harness + both law tests, 10 files / 1295 lines, text-only (binary fixture assets regenerate via `scripts/c9/gen_c9_fixture_assets.py`). Round-trip verified: patches #1+#2 apply cleanly to a fresh `25b5a01` worktree.
- **Fresh verification:** C9-1 laws **36/36** · C9-2 laws **42/42** · regressions **48/48 / 42/42 / 18/18** · §5/§6 harness **41/41** (`bash scripts/c9/validate_c9_resources.sh /tmp/c9_evidence`). Full evidence + hashes in comment 3, incl. `CASE05 startOffset=13824` == independent APPNOTE §4.3.7 arithmetic and the 4 distinct screenshot SHAs (bucket selection proven at the framebuffer level).
- **Toolchain mirror fallback** found and documented (repo1 429 → `maven-central.storage-download.googleapis.com`, ECJ 3.33.0 exact pin; aapt2/r8 from dl.google.com).
- **NEW [OBSERVED] gap registered:** `DisplayMetrics.densityDpi` shadow not fed from `device_config()` (answers 420 always); bucket selection + intrinsics unaffected (proven) — PENDING future law.
- **Channel:** the PAT holds Contents:read only (push 403) — this Issue remains the complete record; local branch `coder9/c9-resource-laws` (2 commits on `25b5a01`) is push-ready once Contents:write is granted, or the manager can cherry-pick comments 1-2 directly.



---

## PHASE 3 (session 3) — the 20-problem close-out: C9-4..C9-23 [IMPLEMENTED] [TESTED]

Patch #3 posted as comments 4-6 (parts a/b/c; apply in order on `439b0a3d` + #1 + #2; **full clean rebuild required — see the ODR note in comment 7**). Session-3 report + verification matrix in comment 7. One-line ledger:

| # | Law | Status |
|---|-----|--------|
| C9-4 | Options.inPreferredConfig honored (real ALPHA_8/RGB_565/ARGB_4444 conversion; getConfig answers the stored config) | [IMPLEMENTED] [TESTED] |
| C9-5 | Options.inMutable honored; Bitmap.isMutable answers the stored flag | [IMPLEMENTED] [TESTED] |
| C9-6 | Options.inPremultiplied honored; isPremultiplied fixed from constant-false to the AOSP default true | [IMPLEMENTED] [TESTED] |
| C9-7 | Bitmap.compress: FORMAT_PNG real libpng encode into the BAOS byte authority; JPEG/WEBP loud honest-miss | [IMPLEMENTED] [TESTED] |
| C9-8 | Bitmap.recycle real: pixels freed, isRecycled flips, pixel access answers the loud ISE contract | [IMPLEMENTED] [TESTED] |
| C9-9 | createScaledBitmap(filter=true) = Skia kLinear bilinear (identity byte-exact) | [IMPLEMENTED] [TESTED] |
| C9-10 | DisplayMetrics (Resources + Display) fed from device_config() — the registered §2 densityDpi gap CLOSED | [IMPLEMENTED] [TESTED] |
| C9-11 | Resources.getDrawableForDensity: request-density bucket selection + C9-1 scaling chain | [IMPLEMENTED] [TESTED] |
| C9-12 | ARSC name→id O(1) hash index (parity-proven; wildcard scan preserved) | [IMPLEMENTED] [TESTED] |
| C9-13 | parser owns its ARSC bytes (dangling data_ alias removed; post-free resolve proven) | [IMPLEMENTED] [TESTED] |
| C9-14 | ResTable_typeSpec parsed (aapt2 ground-truth offset law max(16,headerSize)) + OR-merge + ArscEntry.spec_flags | [IMPLEMENTED] [TESTED] |
| C9-15 | LIBRARY chunk (0x0203) registry + translate_dynamic_reference law | [IMPLEMENTED] [TESTED] |
| C9-16 | font-family XML parser (res/font + -vNN attr-carrying variants; REAL aapt2 bytes law-tested) | [IMPLEMENTED] [TESTED] |
| C9-17 | closest-face weight law + Typeface.create custom-family hookup → __font_face_idx__ | [IMPLEMENTED] [TESTED] |
| C9-18 | state_focused/state_hovered tri-states (framework-selector first-match ordering fixed) | [IMPLEMENTED] [TESTED] |
| C9-19 | state-list compiled drawable refs recorded + engine ARSC deref (colors paint; provenance logged) | [IMPLEMENTED] [TESTED] |
| C9-20 | plurals bag walk + CLDR quantity law (aapt2-pinned keys; en/fa/ar/ru subset) + NotFoundException | [IMPLEMENTED] [TESTED] |
| C9-21 | AssetManager.open access-mode validation law (0..3, AOSP Preconditions contract) | [IMPLEMENTED] [TESTED] |
| C9-22 | Configuration fields fed from device_config() (kills the second hardcoded device value 160) | [IMPLEMENTED] [TESTED] |
| C9-23 | bitmap cache-identity law (FNV-1a over bytes+desc+densities+opts) — Glide/Coil substrate formalized | [IMPLEMENTED] [TESTED] |

**Session-3 verification:** phase-3 law test **46/46** · C9-1 **36/36** · C9-2 **42/42** · resource trio **48/48 / 42/42 / 18/18** · §5/§6 harness **41/41**. Gate byte-identity: fixture APK SHA-256 and all four screenshot SHAs == the session-2 records (phase-3 laws are byte-inert for every pre-existing gate). Ground-truth corrections: typeSpec flags offset (16, not 20), plurals bag keys (0x01000004..09), font-XML -v22 attr-carrying variant, harness res/raw makedirs. **Integration law: clean full rebuild (stale-header ODR hazard — comment 7).**


---

## UPDATE (session 5) — S190: everything rebased onto current main `5119a93` + C9-27 first-ever patch

- **S190 report** (comment 24): phase-3 (C9-4..C9-23) + S188-W1 (C9-24/24b/25/26) REBASED onto `5119a93` — per-file/per-hunk matrix, 13 clean / 2 hand-resolved / 1 SUPERSEDED (3c = main's own S179 repair). **Unified patch parts 1–4 = comments 25–28** (file-boundary split, no mid-word concat).
- **C9-27 mixed-form Class identity law** — reconstructed as real code on the current line (first patchable form; previously prose-only). astroloop vc6 POST run: Errors 0, 0 throwables, 0 IAE, 8 frames (pin `79aa8348…cf7` SHA-verified).
- **Gates on binary `6817d366cfacc3ee`: 232/232 GREEN** (46/46 + 36/36 + 42/42 + 48/48 + 42/42 + 18/18). Harness 41/41 on this binary = PENDING (container toolchain bootstrap).
- quickjs.c pin recorded in full for the Makefile guard (`21f072e8…c54`); guard itself stays PENDING main-coder scope.
- **Addendum 1–3 (comments 29–31):** strict same-container astroloop A/B (PRE pristine `5119a93`: 3 uncaught / 3 C9-domain chains → POST rebase: **0 C9-domain uncaught**, app reaches its own render loop) · S187 = **SUPERSEDED by main's F-NEW-491 line** (verified) · R350-FORNAME contract = **OBSERVED WORKING** (deferred CNFE delivered to the app's catch @0xe — S188's bridge question answered) · remaining astroloop blocker = `HangarSurfaceView.run` loop spin (loop-lane hand-off, pc-level receipts) · **§5/§6 harness 41/41 PASS on `6817d366cfacc3ee`** (fixture SHA `84017f3e…` byte-pinned) — **total gates 273/273 GREEN**.
- Open frontier: C9-28 NinePatch fixture (P-NEW-2) · HangarSurfaceView loop pump (loop lane, receipts posted) · quickjs.c Makefile fetch-guard (main-coder scope, sha256 pin recorded).
