# OPEN_SOURCE_ADOPTIONS_010 — what was actually adopted, with evidence (§1)

Per Campaign 010 §1, every USE/ADOPT claim below carries: source inspected →
build succeeded → test/example executed → MiniAndroid integration attempted →
measured benefit. Commits: 8d4e25b (R1), 4e128c0 (R9/R10), f131606 (R3),
f9190da (R14 stack traces).

## ADOPTION 1 — libpng replaces custom PNG decode+encode (R1)

- **Repo**: libpng.org (system 1.6.48, Debian `libpng-dev 1.6.48-1+deb13u5`).
- **Decision evidence** (`docs/knowledge/campaign010/evidence/uc010_png_bench.txt`):
  corpus = 7,036 PNGs extracted from 8 real APKs (Telegram, dooz, GMDice,
  simplestopwatch, auxio, newpipe, mindustry, SPD):
  - custom: 6,830/7,036 (97.07%), 1,583 ms
  - libpng 1.6.48: 7,036/7,036 (100%), 958 ms (1.66×)
  - stb_image v2.30: 7,036/7,036 (100%), 698 ms (2.27×)
  - **libpng == stb byte-identical RGBA on all common files** (two independent
    mature decoders agree everywhere) — the ground truth for "who is right".
  - custom == libpng fails on 3 files — all tRNS (`spd_0067_crystal_spire`,
    `telegram_4157_4Kt`, `telegram_4290_8Ac`) — the custom decoder ignored
    tRNS colorkeys; custom also rejected all 188 sub-8-bit-depth images.
- **Integration**: `PNGDecoder::decode` reimplemented over libpng (memory
  reader, `png_set_palette_to_rgb`, `png_set_packing`, `png_set_strip_16`,
  `png_set_gray_to_rgb`, `png_set_tRNS_to_alpha`, `png_set_filler`,
  `png_set_interlace_handling`); `PNGWriter::write_png` reimplemented over
  libpng write path. Custom unfilter/Paeth/CRC-table/chunk-writer DELETED.
- **Fixture upgrade**: `tests/exp088_a4_png_decoder_test.cpp` extended to 12
  fixtures incl. injected-tRNS (PIL silently DROPS RGB/L transparency kwargs —
  discovered and documented), Adam7 interlace, 16-bit gray, 1/4-bit palette.
  12/12 PASS byte-identical to the PIL oracle. The fixture caught a real
  integration bug pre-commit (`png_set_expand` alone does not expand tRNS for
  8-bit RGB/gray → `png_set_tRNS_to_alpha`).
- **Regression**: GMDice pixdata `26fc4116e4ba65b4` + Telegram pixdata
  `b9b06072ea17d7fd` IDENTICAL; non-white px 158,040 / 41,233 unchanged.
  (PNG *file* hashes changed by design — libpng's encoder stream replaces the
  custom one at identical pixel content.)
- **LoC**: software_renderer.cpp 1,460 → 1,077 (−383).

## ADOPTION 2 — PortableGL as the GLES backend (R9/R10)

- **Repo**: rswinkle/PortableGL @ 7cf39dc1741e (pushed 2026-08-04), MIT —
  verified live via git ls-remote + raw LICENSE.
- **Why adopt instead of writing**: a software rasterizer (perspective, depth,
  culling, shading) is est. 800–1,500 LoC custom with weeks of correctness
  risk; PGL provides the full GL pipeline + GL function surface in 16,806
  header LoC with zero custom raster code. R10's "custom renderer benchmark"
  therefore evaluates the *counterfactual* honestly: the recovered tree has
  NO custom 3D renderer; Campaign 010 adds GLES capability as **~350 LoC of
  glue** (`src/gles/PGLBackend` + `GLES20Bridge`) instead of ~1,000 LoC of
  bespoke rasterizer.
- **Golden cube** (`evidence/uc010_gles_cube.png`, `*_1080.png`, bench txts):
  MVP + Lambert + depth-test rotating cube, VBO created THROUGH the
  GLES20Bridge, framebuffer → libpng PNG:
  - 320×240: 1,668 fps / 128.1 Mpx/s (cube = 10.0% of frame)
  - 1080×1920: 27.5 fps / 57.0 Mpx/s (cube = 25.7%)
- **GLSL honesty** (no fake claims): PortableGL executes C-function shaders,
  NOT GLSL strings. `glShaderSource` stores APK GLSL verbatim (traceable),
  `glCompileShader` records-but-does-not-compile. Arbitrary APK shaders need a
  GLSL→C translator (PGL's suggested pattern) or Mesa llvmpipe — recorded in
  GLES_BACKEND_COMPARISON_010.md. We do NOT claim APK-shader execution.
- **Regression**: additive module; goldens unchanged (see REGRESSION_010.md).

## ADOPTION 3 — Yoga layout adapter (R3)

- **Repo**: facebook/yoga @ bd8fe0d6d243 (2026-08-27), MIT + bundled
  gtest/gmock build — built `libyogacore.a` (cmake 4.4.2 via pip).
- **Integration experiment** (`evidence/uc010_yoga_differential.txt`):
  LinearLayout→Flexbox adapter (orientation, margins, weights→flexGrow,
  gravity→alignSelf, padding, percent sizes, inflater-heuristic text measure)
  over a tree inflated from the REAL GMDice `act_gmdice` binary XML via the
  runtime's own ResourceRuntime→AxmlParser→LayoutInflater stack:
  - geometry agreement: **10/10 nodes within 8px** (max diff 2.2px = dp
    point-grid rounding), 6/10 within 1.5px
  - speed: yoga ≈0.00003 ms/pass vs custom `measure_layout` ≈0.0011 ms/pass
    = **~35–39× faster** on this tree
- **Correctness gap closed**: weights/gravity/margins exist only in the
  inflater path today; the engine's fallback layout ignores them entirely.
  Yoga semantics cover the full LinearLayout surface (flexGrow/alignSelf/
  justify) — the adapter is the scaffold for wiring Yoga bounds into the
  engine render stage (recorded as follow-up surgery; not silently claimed
  as runtime-wide replacement yet).

## ADOPTION 4 — real stack traces via interpreter CallStack (R14, unblocks
Kotlin Intrinsics)

- `CallStack::snapshot_top_first()` + `Thread.getStackTrace` materializing
  real `StackTraceElement[]` (dotted names, up to 64 frames) +
  `StackTraceElement.getClassName/getMethodName/getFileName/getLineNumber`
  accessors; ThreadShadow falls through to the engine implementation.
- Evidence (dooz attach-run): `[UC010-STACKTRACE] 6 real frames (top=LM1/i;)`;
  Kotlin Intrinsics now throws **real NullPointerException**s
  (`LM1/i;.d pc=17`, propagates) instead of livelocking in its null-check
  stack walk (the old EXP-093 empty-array stub + OOB-null aget = endless loop).
- Regression: goldens identical.

## ADOPTIONS 5–7 — verified, evidence-level (no runtime change yet)

| Component | Commit verified | License | Build+test evidence | Class |
|---|---|---|---|---|
| miniaudio 0.11.25 | mackron/miniaudio @ 9634bed | PD/MIT | compiles+links+`ma_context_init`=SUCCESS (`evidence/uc010_miniaudio.txt`) | B (adopt when audio re-enters runtime) |
| nanosvg 239e102 | memononen/nanosvg @ 239e102 | Zlib | parse+rasterize 1,308 px (`evidence/uc010_nanosvg.txt`) | B (arbitrary-SVG drawables) |
| SheenBidi 9c048a3 | Tehreer/SheenBidi @ 9c048a3 | Apache-2.0 | builds `libSheenBidi.a`, links, runs Persian bidi (`evidence/uc010_sheenbidi.txt`); level-differential harness needs calibration (base-direction flag mismatch — documented) | E (keep FriBidi, §14-PROVEN) |

## Live-verified upstreams (R35 sweep, 2026-08-30)

nothings/stb 2c980bb (PD/MIT) · facebook/yoga bd8fe0d (MIT) ·
rswinkle/PortableGL 7cf39dc (MIT) · Tehreer/SheenBidi 9c048a3 (Apache-2.0) ·
mackron/miniaudio 9634bed (PD/MIT) · linebender/resvg 021d44b (Apache-2.0) ·
memononen/nanosvg 239e102 (Zlib) · catchorg/Catch2 317ac1e (BSL-1.0) ·
google/googletest 36ba75f (BSD-3) · kcat/openal-soft 99f3f1c (GPL-2/LGPL) ·
libsdl-org/SDL 4698bc2 (Zlib).
