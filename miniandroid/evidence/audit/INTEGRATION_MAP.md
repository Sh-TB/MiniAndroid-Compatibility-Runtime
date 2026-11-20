# INTEGRATION MAP — v2 (accepted contributions on the shared execution chain)
APK corpus (upload/handoff_apks, 15 originals — SHAs in RAW_LOGS/apk_corpus_identity_2026-11-20.txt)
→ Manifest/Resources   arsc_parser (TypedValue radix AUD-33) · axml_parser · manifest_reader
  · nine-patch npTc parsing (execution_engine.cpp:2876 — AUD-32 corrected) ·
  · OPEN: GridLayout span-tracks/RTL mirror · npLb legacy chunk
→ DEX / Class Loading  class_resolver · dex_parser
→ Dalvik Interpreter   dalvik_interpreter (wave-7 contract) · opcode laws (AUD-46)
→ Framework API        android_shadows + shadow_registry (BUG-7 duplicate RESOLVED S14 —
  the stale 0-byte src/dex copy removed; single authoritative framework/ header)
  · ScrollView wiring PARTIAL (AUD-31) · FORTIFY 3 symbols OPEN (AUD-34)
→ View / Layout        layout_inflater.cpp — GridLayout Bellman-Ford solver PRESENT (:2899/:4364,
  AUD-30 corrected) · #606 s246 law set (47 laws) · scaleType raster parity (c48773a0)
→ Canvas / Drawable    software_renderer · vector_decode — **MG-011 ok-fix APPLIED THIS SESSION
  (AUD-55, vector_decode.cpp:942)** · text_shaper FriBidi/HarfBuzz/FreeType (AUD-28)
→ Input/State          touch_dispatcher · battery law tests s1xx-s23x
→ Rendered Output      5-APK screenshot sha16 gate — 11/11 IDENTICAL (W24 candidate baseline)
→ Regression           .DELETE_ON_ERROR (AUD-09) · battery manifest parity · ABBA discipline

Build side:
core_sources.manifest (single source of truth) →
  Make: FASTPROFILE=1 W24TIERS=1 -j2 all (~290s) — INTEGRATED; canonical path preserved.
  Sanitizer: make UBSAN=1 (-fsanitize=undefined -fno-sanitize-recover=all, build_ubsan/) —
  ADDED S14; full battery clean under it (AUD-47).
  CMake: measured graph + peak RSS (AUD-52): default 1 link / QuickJS 1x / WEBP define ABSENT (OPEN);
  BUILD_TESTS=ON → 50 links + QuickJS 2x, peak 1235 MB (1264520 KB) at -j1 (S14), ctest ctest rc=8 (98% passed).
Repo hygiene: AUD-51 (051af519) — build_w24_cand_a/ + APK untracked, gitignore hardened.

Branch census (S10): merged — s241-law-waves, s237-w27, s238-audit, s239, s240;
absent-but-preserved — wave10/dalvik-accel (15), audit/s236 (7), audit/m16-litehtml (3),
cont24/skeleton-light (2); stashes preserved (62 files, +12,352 lines).
