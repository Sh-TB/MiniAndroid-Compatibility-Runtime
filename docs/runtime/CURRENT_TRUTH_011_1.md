# CURRENT_TRUTH_011_1

**Date**: 2026-08-30 · **Canonical HEAD**: see `status_011_1.json` · **Method**:
every row below is backed by source + build + test evidence produced in this
campaign unless explicitly graded otherwise. Terminology: PROVEN / PARTIAL /
BLOCKED / FAILED / NOT_PROVEN (§24), plus RECOVERED for code restored from
archives and preserved-but-not-wired.

## Capability truth table (§14, §24)

| Capability | CURRENT_STATUS | HISTORICAL_STATUS | BEST_COMMIT / SOURCE | BEST_EVIDENCE | KNOWN_FAILURES | CURRENT_BLOCKER |
|---|---|---|---|---|---|---|
| DEX interpreter | PROVEN | 216+ opcodes, real APK execution since EXP-030s | `3b862e5` (dalvik_engine from 010 lineage) | v12: exit 0, 12,544 classes, 41,233 px | opcode gaps documented in EXP071 audit | long-tail opcodes on demand |
| ARSC resources | PROVEN | 007 pipeline; 009 config matching | `23900f8` + `3b862e5` (res_config) | gmdice views=10 strings=2 REAL UI | per-version value fragility (SFS-010) | @string refs unresolved on some APKs |
| AXML / inflation | PROVEN (non-obfuscated) | 007; guard 011 | `23900f8` (guard retained in `3b862e5`) | ssw views=11, 930,980 px | obfuscated res/0s.xml paths (unote, headingcalc) | obfuscated resource names |
| Images | PROVEN | custom ≤97.07% corpus → libpng 100% | `3b862e5` (libpng from 8d4e25b) | 7,036/7,036 PNG corpus; 12/12 fixtures; tRNS/Adam7/16-bit | PIL tRNS-kwarg drop documented | — |
| WebP / JPEG | PROVEN | EXP-097 | bbe0ce3 lineage | decoders linked (libwebp, libjpeg) | — | — |
| Lottie | PROVEN | EXP-097/098 rlottie wiring | bbe0ce3 | RLottieImageView → decoder on SMS screen | — | — |
| Font | PROVEN | FreeType+HarfBuzz+FriBidi; §14 RTL 6/6 | bbe0ce3 + WS-C2 proof | proof.png c15673b6; font matrix | FreeSans lacks Arabic cmap | in-runtime text_shaper not wired (recovered module) |
| Layout | PROVEN (inflater) / ADAPTER-READY (Yoga) | 007 inflater; 010 Yoga adapter 10/10 <8px, 35–39× | f131606 lineage | evidence/uc010_yoga_differential.txt | engine render stage not switched | Yoga bounds wiring into engine |
| Touch / input | PROVEN | EXP-088/089 automation; EXP-100 audit | 7cc4254 | 16 click records/run; click#3→StartMessaging→LoginActivity | per-click stderr persistence (fixed by 002) | — |
| Audio | PARTIAL (RECOVERED) | 005 PROVEN 33/33 in lineage; reduced in 009/010 | d6b4020 lineage → `3b862e5` (vendored) | UNIFIED_005_INDEX; audio_report 33/33; fixtures + test_audio.cpp | not in default build | wiring audio_engine into runtime; miniaudio (B-class) verified as alternative |
| 3D rendering | PARTIAL (RECOVERED+PROVEN lineage) | 005 tictactoe3d 16/16; 010 golden cube | 4e128c0 lineage | cube 1,668 fps @320×240, 27.5 fps @1080×1920 | not exercised by default make target | GLES20 dispatch hook into engine chain |
| GLES | PARTIAL | 0 = none before 010 | `3b862e5` (src/gles glue) | evidence/uc010_gles_cube*.png + bench | GLSL strings not executable by PGL | GLSL→C translator or llvmpipe |
| Compose | BLOCKED | blank since first tried | — | matrix dooz/tictactoe blank (pre-existing) | LM1/i;.f StringBuilder.append(null) PC-advance livelock | interpreter fix (R14 removed the previous livelock; next site located) |
| Dooz | BLOCKED (improved) | 002 TIMEOUT→exit0; 008 attach chain; 010 9 real NPEs | 4e128c0/f9190da lineage | dooz_demand_profile.json; REGRESSION_010 | screen blank; attach runs | StringBuilder.append PC-advance |
| Telegram v12 | PROVEN | 000 OBSERVED → 002 chain PROVEN → 010/011.1 stable | `3b862e5` | 3/3 × 088ea640…; non-white 41,233; sendCode→sentCode PROVEN (controlled boundary) | manifest HASH MISMATCH honest note (v12) | SMS-code entry not exercised (no real code) |
| Browser / API persistence | PARTIAL (RECOVERED) | 007 job-server tasks PROVEN; server absent since 009 | u007_job_server.cpp (vendored) | EXP089 plan + 008 knowledge docs | server not running in this session | rebuild+run job server |
| Corpus | PROVEN | 14 → 25 → 31 APKs | `3b862e5` (31-row registry) | apks.json + matrix runs | stopwatch truncated; tinymusic corrupt (both honest) | — |
| Observability | PROVEN | EXP-100 per-click evidence; u011 evidence index | `3b862e5` | docs/evidence/u011_1/ + SHA256SUMS | stderr traces huge → external cache | — |

## Open-source component current truth (§16)

| Library | Status | Where | Note |
|---|---|---|---|
| libpng 1.6.48 (system) | **ADOPTED** — decode+encode | software_renderer.cpp | replaces custom codec; 100% corpus |
| rlottie 43075538 | ADOPTED | external build + Makefile link | SMS screen animation |
| FriBidi 1.0.16 / HarfBuzz 10.2.0 / FreeType 2.13.3 | ADOPTED (system) | text pipeline | §14 RTL proof |
| libwebp / libjpeg-turbo | ADOPTED (system) | image decode | EXP-097 |
| nlohmann_json | VENDORED | third_party/nlohmann_json | — |
| stb_image 2.30 | VENDORED (oracle/bench) | third_party/stb | Campaign 010 three-way identity |
| stb_vorbis + minimp3 | VENDORED (recovered, 005) | third_party/audio | not wired |
| PortableGL 7cf39dc | ADOPTED (glue) | src/gles; portablegl.h external | add to include path to build GLES harness |
| Yoga bd8fe0d | ADAPTER READY | run/uc010_yoga_layout.cpp | lib not vendored; render-stage wiring open |
| miniaudio 9634bed | VERIFIED (B-class) | evidence txt (010) | adopt when audio re-enters |
| nanosvg 239e102 | VERIFIED (B-class) | evidence txt | arbitrary-SVG drawables |
| SheenBidi 9c048a3 | REJECTED for now (E-class) | evidence txt | FriBidi §14-PROVEN; differential needs calibration |
| SwiftShader | RESEARCH ONLY | 008/009 knowledge docs | memory blocker recorded |
| resvg / Catch2 / gtest / openal-soft / SDL | VERIFIED upstreams (R35 sweep) | OPEN_SOURCE_ADOPTIONS_010 | live-verified 2026-08-30 |

## Preserved historical implementations (§15, §17) — do not delete

`src/audio/`, `src/fonts/`, `src/games/`, `src/gles/` (active glue),
`third_party/audio/`, `third_party/stb/`, `src/renderer/view_renderer.*`,
`src/resources/real_layout.*`, `tools/exp113…exp124`, `tools/u007_job_server.cpp`,
`tests/test_audio.cpp`, `tests/fixtures/audio/`, `run/uc010_*.cpp`,
`tools/campaign010/`, `scripts/u007_*`, `scripts/build_unified_007*.py`,
`docs/knowledge/campaign005…010/`. Wiring status and reasons:
`docs/CROSS_CAMPAIGN_RECOVERY_011_1.md` §4.

## Important failed approaches (§15) — keep for the next coder

1. Custom PNG decoder — failed on tRNS colorkeys + sub-8-bit depths (3 corpus files silently wrong alpha) → replaced by libpng; the *fixture set* is the permanent lesson.
2. EXP-093 empty-array getStackTrace stub → Kotlin Intrinsics stack-walk livelock → replaced by real frames (R14).
3. SheenBidi differential harness — base-direction flag mismatch; not calibrated; FriBidi kept.
4. GLSL source execution via PortableGL — impossible by design (C-function shaders); translator/llvmpipe recorded as the route.
5. SwiftShader as GLES backend — memory blocker recorded in Campaign 008/009 knowledge.
6. "uNote UI at 23,472 px" interpretation — disproven by corpus comparison (shared default screen).
7. 011's "archives not available" grading — disproven; the archives were in `/tmp/my-project` all along; negative availability claims now require a filesystem-wide check.
