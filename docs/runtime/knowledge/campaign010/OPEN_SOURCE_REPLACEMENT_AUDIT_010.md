# OPEN_SOURCE_REPLACEMENT_AUDIT_010 — MiniAndroid subsystem census (§2)

Campaign: 010 (replace custom code with real open-source components)
Method: full `src/` census + marker scan (`database/uc010_source_audit.json`),
live GitHub verification of every candidate (commit SHAs via `git ls-remote`,
licenses via raw.githubusercontent — gh API was rate-limited, R35 fallback).

## 1. Census summary (total src = 67,608 LoC + 8,665 root mains)

| Directory | LoC | Files | Role | Mature OSS exists? | Campaign 010 action |
|---|---|---|---|---|---|
| dex/ | 27,913 | 24 | DEX parser+interpreter+engine | smali/dexlib2/JADX (tooling) | **KEEP** (interpreter remains ours); tooling delegated to androguard |
| runtime/ | 10,929 | 9 | execution engine / app runtime | none directly | **KEEP** |
| resources/ | 4,830 | 12 | ARSC/AXML/inflater/res-config (AOSP-ported res_config) | ARSCLib (Java) | **KEEP** glue; parser oracle = ARSCLib/Androguard (R6) |
| renderer/ | 1,077 | 2 | software renderer + codecs | libpng/libwebp/libjpeg/rlottie | **REPLACED PNG (R1)** — custom decode+encode → libpng |
| api/ | 3,749 | 5 | API bridge / context / prefs | — | KEEP |
| framework/ | 2,862 | 5 | View shadows / registry | Robolectric (oracle) | KEEP; layout math → Yoga adapter (R3 ADOPT) |
| apk/ | 2,083 | 4 | APK zip/manifest parser | apk-parser (npm), androguard | KEEP (zip_reader is thin); androguard = oracle |
| storage/ | 1,545 | 2 | file sandbox / prefs | sqlite3 | KEEP |
| diagnostics/ | 807 | 4 | trace / click audit | — | KEEP |
| jni/ | 219 | 1 | JNI bridge | — | KEEP |
| **gles/** | **~350** | 4 | **NEW: PortableGL backend + GLES20Bridge** | PortableGL (MIT) | **ADOPTED instead of writing a rasterizer (R9/R10)** |

Marker scan (R32, src only): **198 hits** — framework 22, dex 123, runtime 21,
api 13, resources 4, jni 3, renderer 3, root mains 7. Classified: the dex/
cluster is dominated by documented EXP diagnostics (logged halts/stubs), not
silent fakes. Full classified list in DO_NOT_REINVENT_010.md §4.

## 2. Codec state (R1)

| Format | Before Campaign 010 | After |
|---|---|---|
| PNG | **custom PNGDecoder (378 LoC) + custom PNGWriter (185 LoC)** — 97.07% success on 7,036 real APK PNGs, 3 tRNS misdecodes, no 1/2/4-bit depth, no Adam7 | **libpng 1.6.48 decode+encode** — 100% decode, 12/12 extended PIL fixtures, 1.66× faster; custom code deleted (commit 8d4e25b) |
| WebP | libwebp 1.5.0 wrapper (EXP-097) | unchanged (already open-source) |
| JPEG | libjpeg-turbo 2.1.5 wrapper | unchanged |
| Lottie | rlottie (vendored, static) | unchanged (already open-source) |
| stb_image v2.30 | not present | vendored `third_party/stb/` (PD/MIT dual, nothings/stb @ 2c980bb) — verified equal-correctness alternative; NOT linked into runtime (global stbi_* symbol collision with rlottie's bundled v2.19) |

## 3. Layout state (R3)

| Aspect | Before | After |
|---|---|---|
| LinearLayout measure/layout | custom `LayoutInflater::measure_layout` (~200 LoC) + simpler engine fallback pass (no weight/gravity/margin in the engine path) | **Yoga adapter** (orientation/margins/weights/gravity/padding → Flexbox) proven on real GMDice AXML: 100% agreement <8px, ~35–39× faster (f131606) |
| Weights/gravity coverage | inflater: yes (weights ×1000 fixed-point); engine fallback: no | Yoga: flexGrow/alignSelf/justify semantics (superset) |

## 4. GLES state (R9/R10)

Recovered tree had **zero** GLES code — the "Software 3D PROVEN" history lives
in pre-008 archives only. Campaign 010 decision: adopt PortableGL instead of
writing a custom rasterizer (see GLES_BACKEND_COMPARISON_010.md).

## 5. Text stack (R4)

- Current runtime text = generated 8×16 BitmapFont (EXP-092); FreeType/
  HarfBuzz/FriBidi are **linked** but only exercised by exp tools (Persian/RTL
  §14 proof pipeline from UNIFIED_002). SheenBidi 9c048a3 (Apache-2.0) built +
  linked OK; bidi differential harness produced uncalibrated level diffs
  (mixed base-direction flags — harness bug, documented) → **E: Investigate
  Later**; FriBidi stays (it is the §14-PROVEN pipeline).

## 6. Audio (R11)

Recovered tree contains **no audio playback code** (history: minimp3/mpg123
era binaries are archive-only). miniaudio 0.11.25 (PD/MIT) verified:
compiles+links+`ma_context_init` SUCCESS on this host. When audio re-enters
the runtime, miniaudio is the evidence-backed single-dependency backend
candidate (vs 4-library stack) — recorded in DO_NOT_REINVENT_010.md.

## 7. Vector/SVG (R5)

nanosvg 239e102 (Zlib): parse+rasterize proven (1,308/2,304 px on a
two-shape Android-style icon test). Current VectorDrawable handling is
AOSP-color-filter based; nanosvg is the candidate for arbitrary SVG
drawables — adopt when corpus demand appears (no current corpus APK blocked
on SVG).
