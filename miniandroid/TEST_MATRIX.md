# TEST_MATRIX — domain status (CAMPAIGN 011 §18)

Status vocabulary: **PROVEN** (evidence, re-runnable) · **PARTIAL** (works with
documented limits) · **BLOCKED** (root-caused obstacle) · **FAILED** (broken,
e.g. bad input) · **UNTESTED** (no evidence).

Canonical runner: `scripts/u011_test_matrix.py` (8-APK matrix, JSON summary,
baseline SHA assertions). Results below = this session (dev build AND clean
clone — identical).

## Per-domain

| Domain | Status | Evidence / notes |
|---|---|---|
| DEX (parse, multi-DEX) | **PROVEN** | Telegram v12: 5 DEX, 12,544 classes, exit 0 |
| Dalvik interpretation | **PARTIAL** | full Telegram journey runs; opcode/API long-tail still growing (EXP-032 coverage docs) |
| ARSC (parse) | **PROVEN** | gmdice named_ids=73/types=8; unote 296/12 loaded |
| ARSC (@string refs in layouts) | **PARTIAL** | headingcalc strings=0 → guarded; top next-action |
| AXML (binary XML) | **PROVEN** | real layouts inflated (gmdice views=10, ssw views=11) |
| Layout inflation (real) | **PROVEN** (non-obfuscated) / **PARTIAL** overall | obfuscated `res/0s.xml` trees abort safely |
| View tree / shadows | **PROVEN** | 95+ bridged classes; findViewById/click dispatch |
| Layout geometry (weight/measure) | **PARTIAL** | simplestopwatch buttons full-height (weight bug) |
| Font (BitmapFont runtime) | **PARTIAL** | renders; overlap on long strings (SFS-010) |
| Font (FriBidi+HarfBuzz+FreeType RTL) | **PROVEN as POC** | EXP-101: 6/6 Persian samples; not yet the TextView path |
| Image (PNG) | **PROVEN** | libpng decode+encode (Campaign 010 R1, default build since 011.1); 12/12 PIL-oracle fixtures; 7,036/7,036 corpus |
| Image (JPEG/WebP) | **PROVEN** | libjpeg-turbo + libwebp wired (EXP-097 CM-024) |
| Drawable rendering | **PROVEN** | EXP-096 BEFORE/AFTER/DIFF tracked evidence |
| Lottie | **PROVEN** | EXP-097/098 — rlottie on SMS screen |
| Touch / click dispatch | **PROVEN** | EXP-088/089 + EXP-100 click records (16/run) |
| Timer / Handler loops | **PARTIAL** | infra proven exactly-once; corpus triggers thin (EXP-088 F) |
| Audio | **PARTIAL** (RECOVERED) | audio_engine + stb_vorbis/minimp3 recovered from UNIFIED_005/008 (33/33 lineage); not wired into default build yet |
| 3D (software renderer) | **PARTIAL** | renderer primitives + recovered tictactoe3d (16/16 lineage); GLES glue adopted |
| GLES/EGL | **PARTIAL** | PortableGL glue adopted (src/gles, 011.1); golden cube 1,668 fps @320×240; GLSL-not-executable + dispatch hook open |
| Compose apps (Dooz) | **BLOCKED** | blank `c035e9ba…` pre-existing; R14 stack traces throw 9 real NPEs (was livelock); current blocker = StringBuilder.append PC-advance |
| Telegram (v12 journey) | **PROVEN** | 3/3 deterministic; 41,233 px; `088ea640…` (011.1, libpng encoder) pixel-identical to `06fb40da…` lineage |
| Telegram (real SMS/network) | **BLOCKED by design** | controlled boundary: mocked `TL_auth_sentCode` |
| Dooz | **BLOCKED** | see Compose |
| Browser/API (WebView-family) | **PARTIAL** | bgclock fullscreen WebView render 2,073,600 px (EXP-101); no real web engine |
| Corpus (14 F-Droid APKs) | **PARTIAL** | 12/14 exit 0 (×2 passes, UNIFIED_002); stopwatch FAILED (truncated); dooz slow-exit-0 |
| XML real APK (headingcalc) | **PARTIAL** | inflation works; @string unresolved → guard fallback (baseline-identical) |
| Determinism (3-run) | **PROVEN** | telegram `088ea640…` ×3 (011.1 session) |

## Per-APK canonical matrix (this session)

| APK | exit | non-white px | screenshot SHA-256 (first 16) | verdict |
|---|---|---|---|---|
| gmdice | 0 | 158,040 | `6425c0f639acaf03` | real UI (improvement) |
| telegram_v12 | 0 | 41,233 | `06fb40da16b1f473` | BASELINE_MATCH ×3 |
| microtimer | 0 | 23,472 | `c200c521628bb8a8` | default screen (= baseline) |
| stopwatch | 1 | 23,472 | `c200c521628bb8a8` | FAILED — truncated APK (pre-existing) |
| simplestopwatch | 0 | 930,980 | `ef334f7ceaab204b` | real controls (improvement) |
| tictactoe | 0 | 0 | `c035e9ba62a884ec` | blank — pre-existing (= baseline) |
| unote | 0 | 23,472 | `c200c521628bb8a8` | guarded fallback (= baseline) |
| dooz | 0 | 0 | `c035e9ba62a884ec` | blank — pre-existing (= baseline), 78–82 s |

Baseline screen SHAs (reference): default `c200c521628bb8a8…`, blank
`c035e9ba62a884ec…`, telegram canonical `06fb40da16b1f473…`, gmdice real UI
`6425c0f639acaf03…`.

## UNIFIED_011.1 canonical matrix (post cross-campaign import — CURRENT)

| APK | exit | non-white px | screenshot SHA-256 (first 16) | verdict |
|---|---|---|---|---|
| gmdice | 0 | 158,040 | `472c1d3c0ee12330` | real UI — behavior identical to 010 verified snapshot |
| telegram_v12 | 0 | 41,233 | `088ea640587ec0d2` | BASELINE_MATCH ×3 (new libpng-encoder baseline; pixel-identical) |
| microtimer | 0 | 23,472 | `eb16ab5c68fa9b6c` | default screen |
| stopwatch | 1 | 23,472 | `eb16ab5c68fa9b6c` | truncated APK (pre-existing) |
| simplestopwatch | 0 | 930,980 | `d495e3cb2ccf6c11` | real controls |
| tictactoe | 0 | 0 | `31ddd4d5b8e6d18e` | blank (pre-existing) |
| unote | 0 | 23,472 | `eb16ab5c68fa9b6c` | safe fallback (guard + reduced tree agree) |
| dooz | 0 | 0 | `31ddd4d5b8e6d18e` | blank (pre-existing); engine progresses post-R14 |

The 011.1 merged binary is byte-identical (same SHAs) to a standalone build
of the recovered UNIFIED_010_FINAL snapshot — the import introduced zero
behavioral delta. Table above (UNIFIED_011 session) kept as historical.
