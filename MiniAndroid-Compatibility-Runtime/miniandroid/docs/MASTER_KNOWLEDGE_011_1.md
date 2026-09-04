# MASTER_KNOWLEDGE_011_1 (§23)

The consolidated knowledge graph of MiniAndroid after UNIFIED_011.1. This file
is the *index*; depth lives in the referenced docs (all in-repo).

## 1. Architecture
- Software Android runtime in C++17: ZIP/APK parser → binary AXML manifest →
  DEX parser → Dalvik interpreter (real APK execution, no VM) → object model →
  shadow framework (android.* bridges) → resources (ARSC/AXML) → software
  renderer → framebuffer → PNG.
- Key docs: `docs/architecture.md`, `docs/architecture-current.md`,
  `docs/execution-flow.md`, `docs/dependency-map.md`,
  `ARCHITECTURE_U007.md` (campaign008 knowledge), `API.md` (010 archive root).

## 2. Runtime / DEX / Android APIs
- Interpreter: 216+ opcodes, invoke dispatch (vtable + method refs), exceptions,
  execution guard/observatory, batch interpreter; audit `docs/EXP071_OPCODE_AUDIT.md`.
- Object model & lifetime: `docs/METHODINFO_LIFETIME_REPORT.md`, EXP032 phase reports.
- API surface: `docs/knowledge/OA_API_MAP.md`, api_dispatcher, android_stubs;
  type-aware STUBBED defaults (86bd646) prevent silent-wrong-value traps (F012).
- Silent-false-success map: `docs/knowledge/ANDROID_SILENT_FALSE_SUCCESS_MAP.md`.

## 3. Resources (ARSC/AXML) & Layout
- Pipeline: arsc_parser → axml_parser → layout_inflater → resource_runtime
  (recovered 007 work, commit 23900f8); works on non-obfuscated APKs
  (GMDice real UI, SimpleStopwatch real controls); zero-regression guard.
- Config matching: `src/resources/res_config.*` (Campaign 009).
- Yoga adapter: 10/10 geometry agreement, ~35–39× faster; render-stage wiring
  open (`run/uc010_yoga_layout.cpp`, `GLES_BACKEND_COMPARISON_010.md` sibling notes).
- Known limits: obfuscated res names (unote), unresolved @string (headingcalc).

## 4. Fonts & Text
- FreeType 2.13.3 + HarfBuzz 10.2.0 + FriBidi 1.0.16; bitmap font (EXP-092);
  `FREETYPE_VS_BITMAPFONT.md`; font matrix (Arabic cmap coverage).
- Persian/RTL: §14 proof 6/6 (codepoints+bidi+glyphs), proof.png c15673b6.
- Recovered `src/fonts/text_shaper` (008) — ready to wire.

## 5. Images
- libpng decode+encode (ADOPTED, 010): 7,036/7,036 real-PNG corpus, tRNS,
  Adam7, 1/2/4/16-bit; 12-fixture test vs PIL oracle; libpng==stb identity.
- libwebp + libjpeg (EXP-097); rlottie Lottie on SMS screen (EXP-098).
- stb_image vendored as benchmark oracle (three-way identity method).

## 6. Audio (§ recovered)
- Campaign 005: audio_engine + stb_vorbis/minimp3, MediaPlayer bridge —
  33/33 in its lineage (WAV artifacts produced).
- Recovered & vendored in 011.1; not wired. miniaudio verified as B-class
  alternative (`OPEN_SOURCE_ADOPTIONS_010.md`).

## 7. Input / Timing / Rendering / 3D / GLES
- Touch: runtime-embedded automation (EXP-088/089) + env-gated click/chain
  audit (EXP-100) — click#3 IntroActivity$4 → LoginActivity; per-click records.
- Timing: handler queue semantics (EXP-086 phase7, EXP-088 phaseF), SystemClock
  still ABSENT (F004 open — Uri too).
- Renderer: software_renderer (shapes, text, images) → framebuffer → PNG.
- 3D: tictactoe3d (005, real perspective+minimax 16/16) recovered.
- GLES: PortableGL glue `src/gles` (buffers/attribs/draw/state/uniforms),
  golden cube evidence; GLSL strings stored verbatim, NOT executed (honesty note);
  dispatch hook open.

## 8. Compose / Dooz / Telegram / Browser-API
- Compose: blank screens (dooz, tictactoe) — attach runs but UI empty.
- Dooz: attach chain mapped (008/009); R14 stack traces → 9 real NPEs;
  current blocker `LM1/i;.f StringBuilder.append(null)` PC-advance (dooz_demand_profile.json).
- Telegram: v12.10.1 deterministic (3/3 × 088ea640 post-import; pixel-identical
  to 06fb40da lineage); auth chain sendCode→mocked sentCode→setPage(2) PROVEN
  (controlled boundary); manifest HASH MISMATCH note standing.
- Browser/API persistence: u007_job_server (task queue) recovered; absent from
  runtime since 009 reduction — rebuild to resume stress runs.

## 9. Open Source (see also `OPEN_SOURCE_MASTER.md`, `DO_NOT_REINVENT.md`)
- Central law: DO NOT REIMPLEMENT WHAT OPEN SOURCE ALREADY SOLVES.
- ADOPTED: libpng, rlottie, FriBidi/HarfBuzz/FreeType, libwebp, libjpeg,
  PortableGL (glue). VENDORED: nlohmann_json, stb_image, stb_vorbis, minimp3.
  ADAPTER-READY: Yoga. VERIFIED-NOT-INTEGRATED: miniaudio, nanosvg, resvg,
  Catch2, gtest, openal-soft, SDL. REJECTED: SheenBidi (calibration),
  SwiftShader (memory blocker, research only).
- Provenance JSONs: `docs/knowledge/campaign008/LIBRARY_PROVENANCE_008.json`,
  `campaign009/LIBRARY_PROVENANCE_009.json`, `campaign010/LIBRARY_PROVENANCE_010.json`.

## 10. Testing
- Matrix runner: `scripts/u011_test_matrix.py` (8 canonical APKs, SHA + pixel
  metrics); corpus registry `tests/corpus/apks.json` (31 rows); ZERO-APK
  download scripts `scripts/download_test_apks.{sh,py}`; PNG fixture suite
  (12/12); Robolectric + paparazzi oracles under `tools/`; golden/ expected
  view-tree/screenshot/object-model.
- Baselines after import: gmdice 158,040 px; ssw 930,980 px; telegram v12
  41,233 px / 088ea640… 3/3 (pixel-identical to 06fb40da lineage).

## 11. Failures (preserve — see `CURRENT_TRUTH_011_1.md` §"failed approaches")
Custom PNG codec (tRNS bug) · EXP-093 stack-trace stub (livelock) ·
GLSL-on-PGL (by design) · SheenBidi differential (uncalibrated) ·
SwiftShader (memory) · uNote-UI misreading · 011 availability mis-grading.

## 12. Where everything lives
- Source: `miniandroid/src/**` · Tests: `miniandroid/tests/` · Tools: `miniandroid/tools/`
- Evidence: `miniandroid/docs/evidence/u011/`, `u011_1/` (in-repo, ≤100KB PNGs)
- External caches (never in repo): `/home/z/my-project/apk_cache`,
  `/home/z/my-project/u011_1_forensics/` (archives + extractions + diffs),
  `/tmp/my-project/download/corpus/` (18-APK corpus incl. 73MB Telegram),
  `download/UNIFIED_011_1_backup/` (bundle + patches)
- Master docs: `README.md`, `MASTER_PROJECT_STATE*.md`,
  `MASTER_CHANGELOG_KNOWLEDGE_011.md`, `MASTER_RECONCILIATION_011_1.md`,
  `CODER_HANDOFF_011_1.md`, `RELEASE_NOTES_011_1.md`, `status.json`,
  `status_011_1.json`, `START_HERE.md`.
