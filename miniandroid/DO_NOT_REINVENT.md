# DO_NOT_REINVENT — the central law, operationalized

> **DO NOT REIMPLEMENT WHAT OPEN SOURCE ALREADY SOLVES.**
> Pipeline: `current custom → GitHub search → mature implementation → build →
> test → benchmark → integration experiment → replace / wrap / keep`.

This file is the standing map of "custom code that has a mature open-source
replacement". Before adding ANY feature below, come here first.

## Standing replacement map

| Domain | MiniAndroid custom today | Mature open source | Action required | Status |
|---|---|---|---|---|
| PNG decode+encode | ~~custom `PNGDecoder`~~ **libpng wired** | libpng 1.6.48 | done in Campaign 010 R1; default build since UNIFIED_011.1 (12/12 fixtures, 100% corpus) | **CLOSED** |
| JPEG/WebP decode | DONE via libjpeg-turbo / libwebp | — | keep | CLOSED |
| Layout measure/layout | custom `measure_layout` (weight bugs known) | **Yoga** | adapter built + differential 10/10 nodes <8px, 35–39× faster (`run/uc010_yoga_layout.cpp`); render-stage wiring remains | PARTIAL (R3 adapter ready) |
| Font bidi/shaping/raster | BitmapFont runtime path; FriBidi+HarfBuzz+FreeType POC proven | FriBidi + HarfBuzz + FreeType (linked) | make the POC the TextView path; retire glyph hacks | OPEN (R4) |
| SVG / VectorDrawable | none real | resvg / nanosvg | integrate when first SVG APK matters | PLANNED (R5) |
| ARSC/AXML parsing | custom (working, non-obfuscated trees) | ARSCLib / androguard-as-oracle | keep custom runtime path; diff-test against oracles; add obfuscated-name support | PARTIAL (R6; resource-resolution semantics stay in-house glue) |
| APK static analysis | ad-hoc scripts | androguard / apktool / JADX / dexlib2 | always prefer these for offline analysis | CLOSED as policy (R7/R8) |
| DEX interpreter | in-house (by design — this IS the project) | — | never replace; use R8 tools around it | KEEP (by charter) |
| GLES/EGL | none | **PortableGL** / SwiftShader / ANGLE | integrate PortableGL first (small, C, CPU) behind renderer interface | OPEN (R9/R10) |
| Audio decode | none real | libavcodec-family / miniaudio / stb_vorbis | pick when audio corpus work starts | PLANNED |
| JSON | DONE via nlohmann | — | keep | CLOSED |
| Lottie | DONE via rlottie | — | keep | CLOSED |
| ZIP | custom streaming reader (data descriptors, CRC) — works on real corpus | miniz / zlib's contrib | evaluate wrap; low priority (proven in the field) | KEEP for now |
| Testing oracles | — | Robolectric / Paparazzi / androguard | extend oracle use in CI-like flows | ONGOING |

## Anti-registry — things people keep re-attempting (stop)

1. Rewriting the PNG decoder from scratch → wire libpng instead (linked already).
2. Hand-rolling bidi/shaping for Persian text → use the proven
   FriBidi→HarfBuzz→FreeType pipeline (`scripts/exp101_persian_rtl_proof.cpp`).
3. Re-implementing ARSC "from the spec" without diffing against androguard.
4. Claiming Yoga/PortableGL/libpng are "integrated" without a benchmark +
   evidence. History: Campaign 010 *did* integrate them (verified in 011.1);
   Campaign 011's re-check wrongly reversed that via a scan-path bug; 011.1
   re-verified from source + build + tests. Lesson: every integration claim
   needs the evidence chain, and every negative claim needs a positive check.
5. Committing APKs, or putting them in ZIPs/releases — external cache only.
6. Building a "new evidence format" — screenshot.png + api_trace.json +
   matrix JSON is the contract; hashes are the language.

## Evidence discipline for any replacement

`PROVEN` requires: source inspected + build succeeded + test executed +
MiniAndroid integration attempted + measured benefit (§1 of CAMPAIGN 010).
Anything less is `PARTIAL`/`RESEARCH` and must be labeled so in
`OPEN_SOURCE_MASTER.md` and commit messages.
