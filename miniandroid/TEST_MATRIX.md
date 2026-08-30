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
| Image (PNG) | **PARTIAL** | custom decoder incl. palette/tRNS; libpng not wired (R1 open) |
| Image (JPEG/WebP) | **PROVEN** | libjpeg-turbo + libwebp wired (EXP-097 CM-024) |
| Drawable rendering | **PROVEN** | EXP-096 BEFORE/AFTER/DIFF tracked evidence |
| Lottie | **PROVEN** | EXP-097/098 — rlottie on SMS screen |
| Touch / click dispatch | **PROVEN** | EXP-088/089 + EXP-100 click records (16/run) |
| Timer / Handler loops | **PARTIAL** | infra proven exactly-once; corpus triggers thin (EXP-088 F) |
| Audio | **UNTESTED** | no proven audio corpus journey |
| 3D (software renderer) | **PARTIAL** | renderer primitives + docs; no GLES backend |
| GLES/EGL | **BLOCKED** | no backend; PortableGL first candidate (R9/R10) |
| Compose apps (Dooz) | **BLOCKED** | blank `c035e9ba…` byte-identical old/new; Kotlin Intrinsics NPE analysis (UNIFIED_002) |
| Telegram (v12 journey) | **PROVEN** | 3/3 `06fb40da…` = baseline; 41,233 px |
| Telegram (real SMS/network) | **BLOCKED by design** | controlled boundary: mocked `TL_auth_sentCode` |
| Dooz | **BLOCKED** | see Compose |
| Browser/API (WebView-family) | **PARTIAL** | bgclock fullscreen WebView render 2,073,600 px (EXP-101); no real web engine |
| Corpus (14 F-Droid APKs) | **PARTIAL** | 12/14 exit 0 (×2 passes, UNIFIED_002); stopwatch FAILED (truncated); dooz slow-exit-0 |
| XML real APK (headingcalc) | **PARTIAL** | inflation works; @string unresolved → guard fallback (baseline-identical) |
| Determinism (3-run) | **PROVEN** | telegram `06fb40da…` ×3 this session |

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
