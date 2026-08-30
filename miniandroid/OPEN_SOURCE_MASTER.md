# OPEN_SOURCE_MASTER — every external component, graded honestly

Legend — **Used**: linked/loaded by the runtime · **Built**: compiled from
source this environment · **Tested**: executed with a check · **Integrated**:
on the load-bearing path of a proven journey. Provenance grades per §4.

## 1. Integrated & load-bearing

| Project | Repo | Version / commit | License | Built | Tested | Integrated | Purpose | Why selected |
|---|---|---|---|---|---|---|---|---|
| rlottie | Samsung/rlottie | commit `43075538` (manual static build) | MIT | YES (this env) | YES (EXP-097 frames + SMS screen) | YES — RLottieImageView on SMS screen (`bbe0ce3`) | Lottie animations | Telegram itself uses rlottie → highest fidelity |
| libwebp | webmproject/libwebp | 1.5.0 (system) | BSD-3 | system | YES (corpus images) | YES — WebP drawables | WebP decode | Android's own image stack uses libwebp |
| libjpeg-turbo | libjpeg-turbo | 2.1.5 (system, `-ljpeg`) | IJG/BSD-3 | system | YES | YES — JPEG drawables | JPEG decode | drop-in libjpeg API, SIMD speed |
| zlib | madler/zlib | 1.3.1 (system) | zlib | system | YES (every APK) | YES — APK/ZIP inflate | DEFLATE | the reference implementation |
| nlohmann/json | nlohmann/json | 3.11.3 (vendored single header, auto-download) | MIT | vendored | YES (all JSON I/O) | YES — traces/reports | JSON | de-facto C++ standard |
| FreeType | freetype/freetype | 2.13.x (system, `26.2.20`) | FTL/GPL-2 | system | YES (EXP-096 §10 + EXP-101 POC) | PARTIAL — linked; text path is BitmapFont today | glyph rasterization | Android uses FreeType |
| HarfBuzz | harfbuzz/harfbuzz | 10.2.0 (system) | MIT/OLD-MIT | system | YES (EXP-101 RTL POC 6/6) | PARTIAL — POC path | shaping | Android's shaper |
| FriBidi | fribidi/fribidi | 1.0.16 (system) | LGPL-2.1+ | system | YES (EXP-101 RTL POC) | PARTIAL — POC path | bidi | Android's bidi |
| libpng | pnggroup/libpng | 1.6.48 (system) | PNG | system | linked only | **NO — decode path still custom PNGDecoder** (R1 open) | PNG decode | CAMPAIGN 010 R1 target; wire it |

## 2. Built/tested as external oracles (not runtime deps)

| Project | Repo | Version | License | Result |
|---|---|---|---|---|
| Robolectric | robolectric/robolectric | 4.14.1 | MIT | oracle tool built & ran 1/1 (EXP-102, commit `8f0a85b`); pom system-jar→aar fix upstreamed to our repo for reproducibility |
| androguard | redballoon-security/ofroguard | 4.1.4 (pip) | LGPL-2.1+ | census tool ran 14/15 APKs (EXP-102); reference oracle for manifest/ARSC |
| Maven | apache/maven | 3.9.9 (portable) | Apache-2.0 | toolchain for the oracle |
| nlohmann auto-fetch | (see above) | 3.11.3 | MIT | Makefile downloads if missing (vendored copy is tracked) |

## 3. Researched, NOT integrated (CAMPAIGN 010 pipeline output — HISTORICAL grades)

| Candidate | Repo | Verdict this session | Why it mattered |
|---|---|---|---|
| Yoga | facebook/yoga | NOT in repo — research only (R3 open) | measure/layout semantics vs custom inflater |
| PortableGL | rswinkle/PortableGL | NOT in repo — research only (R9/R10 open) | GLES2-on-CPU backend candidate |
| SwiftShader | google/swiftshader | NOT integrated | heavy; Apache-2.0; candidate GLES backend |
| ANGLE | google/angle | NOT integrated | EGL/GLES translation layer candidate |
| Skia / SkiaUI2 / Skiko | google/skia, JetBrains/skiko | research docs only | full UI-stack replacement thesis |
| Compose Multiplatform | JetBrains/compose-multiplatform | research docs only | UI layer thesis |
| SkShaper | google/skia (modules) | research docs only | shaping alternative |
| resvg / nanosvg | linebender/resvg, tinylibs/nanosvg | NOT integrated | SVG/VectorDrawable candidates (R5) |
| ARSCLib / Androguard-as-parser | reAndroid/ARSCLib | NOT integrated; androguard used as oracle | ARSC/AXML dedup (R6) |
| apktool / JADX / smali-baksmali / dexlib2 | iBotPeaches, skylot, JesusFreke | research docs only (R7/R8) | static analysis offload |
| Wuffs / stb_image | google/wuffs, nothings/stb | NOT integrated | image decode alternatives (R1) |
| libavif | AOMediaCodec/libavif | NOT integrated | AVIF future |

Rule (§16/central law): before writing ANY new decoder/parser/layout/font/GLES
code, check §1–§3 and `DO_NOT_REINVENT.md`; wrap or replace with the mature
component, then benchmark, then decide keep/replace — and record the outcome here.

## 4. Provenance of externals (§17)

| component | version pin | modified? | integration path |
|---|---|---|---|
| rlottie | commit `43075538` static lib at `$(RLOTTIE_DIR)` (default `../tools/rlottie`) | NO | linked `-I…/inc` + `librlottie.a` |
| system libs | see versions in §1 | NO | pkg-config/`-l` |
| nlohmann/json | 3.11.3 single header | NO | `third_party/nlohmann_json/include` (tracked) + Makefile auto-fetch |
| Robolectric oracle | 4.14.1 | build files only (`tools/robolectric-oracle`, pom fix) | external JVM tool |
| androguard | 4.1.4 pip | NO | analysis scripts |
