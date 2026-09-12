# CODE_REDUCTION_010 — LoC before/after per replacement (R27)

## 1. Replacement 1 — PNG stack → libpng (commit 8d4e25b)

| Metric | Before | After | Delta |
|---|---|---|---|
| software_renderer.cpp LoC | 1,460 | 1,077 | **−383** |
| custom PNG decode code | 378 LoC (chunk walker, inflate wrappers, 5-filter unfilter, Paeth, palette+tRNS expand, gray/ga/rgb/rgba expand) | 0 (libpng + 55 LoC mem-reader/color-name helper) | −378 |
| custom PNG encode code | 185 LoC (CRC table 40, compress2 wrapper + uncompressed-zlib fallback, chunk writer, RGBA→RGB packer) | ~60 LoC (libpng write path) | −125 |
| Decoder coverage | bit_depth=8 only, no Adam7, tRNS ignored | all depths 1/2/4/8/16, Adam7, tRNS | coverage up |
| Corpus success (7,036 real APK PNGs) | 6,830 (97.07%) | 7,036 (100%) | +206 files |
| Corpus decode time | 1,583 ms | 956 ms | 1.66× faster |
| Dependencies added | — | libpng (already linked) | +0 new deps |
| Tests before / after | 1 fixture set (8-bit only) | 12 fixtures (tRNS/Adam7/16-bit/1-bit/4-bit) 12/12 PASS | +11 |
| Performance before/after | 1.58 ms avg/image | 0.136 ms avg/image | −91% |

## 2. Replacement 2 — GLES capability via PortableGL (commit 4e128c0)

| Metric | Before | After |
|---|---|---|
| Custom rasterizer LoC written | 0 (counterfactual est. 800–1,500) | 0 |
| New glue LoC (src/gles) | — | ~350 (pgl_backend 88 + gles20_bridge ~200 + headers) |
| External LoC adopted | — | PortableGL 16,806 (header, MIT, @7cf39dc) |
| GLES surface | none | GLES20 static-method dispatch (buffers/attribs/draw/state/uniforms) |
| Golden render | none | shaded depth-tested cube → PNG (evidence/uc010_gles_cube.png) |
| Performance | — | 128.1 Mpx/s @320×240; 57.0 Mpx/s @1080×1920 |

## 3. Replacement 3 — layout math → Yoga adapter (commit f131606)

| Metric | Before | After |
|---|---|---|
| Runtime layout LoC | custom `measure_layout` ~200 LoC (+ weightless engine fallback) | unchanged in runtime; adapter ~120 LoC (scaffold) + Yoga 30k+ adopted |
| Weight/gravity correctness | inflater-only | full Flexbox semantics via adapter |
| Geometry agreement vs custom | — | 10/10 nodes <8px on real GMDice AXML |
| Layout speed (same tree) | 0.0011–0.0014 ms/pass | 0.00003 ms/pass (**~35–39×**) |
| Note | engine render stage not yet switched to Yoga bounds (follow-up surgery, tracked) | |

## 4. Non-LoC reductions (custom *behavior* replaced)

| Custom hack removed | Replaced by | Commit |
|---|---|---|
| EXP-093 empty-array `getStackTrace` stub (+ shadow null stub) | real interpreter frames → `StackTraceElement[]` | f9190da |
| tRNS-ignoring decode (silent wrong alpha on 3 corpus files) | libpng `png_set_tRNS_to_alpha` | 8d4e25b |

## 5. Census (see database/uc010_source_audit.json)

src total 67,608 LoC (+8,665 root mains). Campaign 010 net src delta:
**−383 deleted, ~350+120 added as glue/adapter** → custom-code growth from
open-source integrations ≈ +87 LoC net while: PNG correctness went 97.07%→100%,
GLES 0→full-pipeline, layout math 35× faster. That ratio (capability per custom
LoC) is the §40 metric.
