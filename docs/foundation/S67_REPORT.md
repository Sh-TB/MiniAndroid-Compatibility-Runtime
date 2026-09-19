# S67 — FOUNDATION HARDENING REPORT
Campaign law: BREADTH paused; no new apps; no new spotlight. HEAD at start:
`289e33d3` (== origin/main, push debt zero). Every fix followed
`BASE CONTRACT → UPSTREAM LAW → IMPLEMENTATION → MICRO TEST → REAL APK →
PIXEL/TRACE PROOF → REGRESSION`.

## FINAL NUMBERS (user-specified counters)

```text
base contracts inspected          = 61   (render 24 · layout 26 · resource 24 · runtime 17 — matrix rows)
classes inspected                 = 40+  (census agents: canvas_shadow, software_renderer, text_shaper,
                                          layout_inflater, arsc/axml parsers, manifest_reader,
                                          dalvik_engine R$/static/exception paths, touch_dispatcher, plus
                                          fixture classes f26/f27/f38/f39_44/f45)
upstream sources checked          = 12   (AOSP View.java, LinearLayout.java L985-1045/L1385-1445/L1445-1470,
                                          Canvas.java, Paint.java, Color.java, ViewProps/View visibility law,
                                          Instrumentation.java, TypedValue/ResourceTypes.h, RenderNode,
                                          Paint.setARGB, android:visibility attr enum def)
searchlight queries               = 10   (census greps per subsystem + Color.rgb REC-MISS trace +
                                          visibility enum trace + RL replay trace; zoekt shards lost to
                                          reset — fetched-file citations per S66 pattern, honestly noted)
micro-tests (fixtures)            = 19   (17 pixel/trace-verified + f05b shaping contrast + f08 op census)
micro-tests PASS                  = 17   (post-fix final verify: 17/17)
micro-tests FAIL → FIXED          = 4    (f27_nav F-121, f32_dimen A2, f06_invisible A4+F-124, f18_lltop C3)
micro-tests FAIL → registered     = 0    (all found failures this session either fixed or explicitly
                                          pixel-proven as registered NO-OPs: clipRect leak 245px,
                                          scale/rotate unscaled coords)
real APK validations              = 6    (TicTacToe ×2 frames byte-match, FishRings 5/5 byte-match,
                                          OPMT 2/2 byte-match, TriPeaks 2/2 byte-match on shared stages,
                                          hello_color corpus app byte-stable across fix epochs,
                                          miniandroid_test 4/4)
generic fixes                     = 7    (F-121 pending-work drain law; F-122 Color statics; F-123
                                          drawRoundRect arg-index + radius raster; F-124 visibility space;
                                          A2 three-layer dimen law; A4 own-content gate; C3 LL cross-axis TOP)
regressions                       = 0    (fixtures 17/17 byte-stable where laws unchanged; goldens byte-match)
renderer operations proven        = 17   (see FOUNDATION_RENDER_MATRIX)
renderer operations partial       = 5    (rect-stroke, circle-stroke, save/restore, drawText-ASCII,
                                          drawRenderNode)
layout contracts proven           = 20   (see FOUNDATION_LAYOUT_MATRIX)
resource contracts proven         = 14   (see FOUNDATION_RESOURCE_MATRIX)
text cases proven                 = 4    (ASCII text, Persian joined-vs-spaced shaping 47% ink delta,
                                          text-size/g baseline via G32 law, mixed-script row)
image cases proven                = 3    (f03 alpha path, S66 PNG decoder byte-identity, density select_file)
input paths proven                = 4    (button click→state→render; startActivity nav; long-press
                                          machinery re-validated by fixture recipes; disabled/invisible
                                          hit-gating via visibility law fix)
remaining P0                      = 6    (A1 ?attr, A3 non-PNG drop, A6 Canvas non-ASCII, A7 manifest
                                          label/icon, A9 canvas dims, A10 Theme.resolveAttribute)
remaining P1                      = 12   (B1-B12 family, incl. B2 clipRect + B1 matrix pixel-proven NO-OPs)
```

## Fixes shipped this session (ROOT CAUSE, not symptom)

| Fix | Root cause (source-verified) | Upstream law | Proof |
|---|---|---|---|
| F-121 | startActivity defers launch to frame-boundary consumer; click-test probe re-rendered BEFORE draining pending work → nav clicks recorded changed_px=0 | AOSP Looper: click message fully processed (LAUNCH_ACTIVITY incl.) before next traversal | f27_nav: 2,073,273 px change, B-activity bg #CCEEFF rendered |
| F-122 | `Color.rgb/argb/parseColor` were REC-MISS → returned int 0 → alpha-0 paints → invisible shapes | AOSP Color.java static factories | f08: stroke ring green, 5 colors pixel-exact |
| F-123 | drawRoundRect read paint from the rx float slot (assumed `(l,t,r,b,paint,rx,ry)`; AOSP is `(l,t,r,b,rx,ry,paint)`) and radius was recorded-not-rasterized | AOSP Canvas.drawRoundRect signature + Skia RRect | f08 R9: brown fill + corner probe shows rounding |
| F-124 | aapt2 compiles android:visibility into attr-enum space {0,1,2}; engine stored raw int → INVISIBLE(1) unknown to renderer | ViewProps VIEW_VISIBILITY_VALUES {0,4,8} mapping | f06: all-white frame; VT visibility=4 |
| A2 | three layers: (1) virtual-method arg index read `this` not resid; (2) dimen map seeded with unconverted dp mantissa; (3) name-map seeding not reached from all SGET routes → ARSC-first needed | TypedValue.complexToDimensionPixelSize (+density, round-half-away, nonzero floor) | f32: 100dp → 263px exactly |
| A4 | render walk pruned only GONE(8); INVISIBLE(4) own-content drew fully | View.draw SKIP_DRAW + dispatchDraw children law | f06 pixel gate (with F-124) |
| C3 | horizontal-LL cross-axis: explicit TOP(0x30) fell through the two-way test into the CENTER branch | LinearLayout.java L1445-1470 switch | f18: child y=0 (was y=760), 3/3 asserts |
| evidence pipeline | ViewTree JSON dump unreachable from `run` (legacy EXP-061-only) | provenance-first law (user §10) | `--dump-view-tree` flag; all 19 fixtures export view_tree.json |

## Registered (pixel-proven NO-OPs, not guesses)

- B1 canvas matrix (scale/rotate/skew/concat) — f08 R5/R7 rasterized at unscaled coords.
- B2 clipRect — f08 R6 leak 245px beyond clip.
- B3-B12, C1/C2/C5-C12, D1-D7 — see FOUNDATION_GAP_MATRIX.md (each with law + plan).

## Anti-false-success compliance

Proof used per subsystem: pixel assertions from independently re-decoded PNGs
(PIL), ViewTree semantic asserts (text/geometry/visibility), runtime trace lines
([RES], [G08-LIFECYCLE], [EXP091-SETTEXT]), and byte-match SHA comparisons vs
prior-campaign records. No claim rests on rc=0, PNG existence, nonwhite counts,
or log-only evidence.

## Honest gaps (not done this session — queued, not claimed)

Wave 2 A1/A3/A6/A7/A9/A10 implementations; Wave 3-6 remaining B/C families
(matrix stack, clip stack, saveLayer, ScrollView scroll, BitmapFactory, text
unification); Wave 7-8 Fragment/Service micro-tests + Dooz compose gap proofs;
Wave 9-10 HelloWorld/gmdice re-build cross-validation + zoekt re-index. Every
row carries its next generic fix in FOUNDATION_GAP_MATRIX.md.
