# S94 — GRAPHICS SOURCE LIBRARY: FINAL REPORT

Campaign: mine 100+ distinct GitHub repositories into a permanent
**Graphics Source Registry** so future graphics problems are solved by
consulting proven upstream implementations and tests before writing code.

Continuity: S92/S93 evidence untouched; no verdict weakened; no FAILED/PARTIAL
reinterpreted. This campaign ADDS a permanent source-knowledge layer.

---

## 0. The permanent mechanism (deployed)

```
new graphics bug
      ↓  tools/source_lookup.py <CATEGORY>          (§14 automatic lookup — deployed + tested)
automatic source-family classification
      ↓  docs/GRAPHICS_SOURCE_REGISTRY.json         (122 distinct verified repos)
Graphics Source Registry lookup
      ↓  run/s94/source_mining/source_to_law.json   (48 laws, each with fetched evidence)
upstream source/test inspection
      ↓  docs/GRAPHICS_DO_NOT_REINVENT.md           (do-not-reinvent table)
existing algorithm/implementation discovered
      ↓  CONSTITUTION_V2.md §170                    (SOURCE-FIRST LAW — permanent)
MiniAndroid semantic law → fixture → real APK
```

## 1. §27 questions — answered with measured numbers

| # | Question | Answer |
|---|---|---|
| 1 | Repositories actually inspected? | **122 distinct GitHub repositories identity-verified** (`git ls-remote --symref`, HEAD SHA recorded). **65 deep-inspected** (20 shallow-cloned with file harvest + 45+ with pinned-SHA source fetches); 57 identity+license verified only (queued future mining). Plus 4 off-GitHub canonicals (AOSP googlesource ×2, mesa, cairo) and 1 directive identity that does not exist (`android/graphics` etc. — recorded UNVERIFIED, never substituted). |
| 2 | Source files? | **426 source files** hash-evidenced (sha256 + byte size at a pinned commit): 366 from 20 clones, 60 pinned-SHA raw fetches (incl. `?format=TEXT` googlesource for minikin `Layout.cpp` and AOSP `View.java`). |
| 3 | Concrete functions/classes? | **789 symbol/class hits** recorded with line numbers (e.g. `hb_ot_shape_internal` @harfbuzz:1171, `AnimationDrawable.setFrame`, `Downsampler.getRoundedSampleSize`, `AwContents.onDraw`, `SkCanvas::clipRect`). |
| 4 | Upstream tests? | **20 test corpora, 3,996 test files counted**: harfbuzz test/ (3,058), wuffs test/ (437), yoga gentest (43 fixture sets + 73 tests), pixelmatch (28), CDroid tests/ (266 incl. CTS-style ninepatch/ripple/animationdrawable), Pillow/Golang GIF tests, testify/paparazzi/Shot/roborazzi suites, WPT + WebGL conformance corpora. |
| 5 | Reusable implementations? | **23 mapped in implementations.jsonl**; license distribution of the 122: 87 SAFE_PORT_WITH_ATTRIBUTION, 22 REFERENCE_ONLY, 6 COPY_REQUIRES_NOTICE (incl. CDroid = LGPL-2.1 verified by pinned-sha fetch — NOT Apache as assumed), 7 pending license clarification. |
| 6 | Reusable fixtures? | wuffs decoder corpus (437), yoga gentest (43 sets), pixelmatch diff fixtures (28), CDroid asset ninepatch PNGs, noto-emoji reference rasters, BackstopJS/resvg golden suites (identity-verified). |
| 7 | Algorithms? | 48 semantic contracts extracted (density pairs, GIF disposal 0–3, clip stack, shaping pipeline, per-codepoint font fallback, NinePatch stretch/padding, frame submission boundaries, AA-aware diff, readiness callbacks). |
| 8 | Semantic laws? | **48 laws (L-S94-*) in source_to_law.json — 48/48 with FETCHED evidence** (file sha256 + symbol line hits). |
| 9 | MiniAndroid gaps mapped? | 10 gap families in gap_map.json spanning the full §12 taxonomy (resource, decode, geometry, rendering, text, animation, interaction, web, compose, surface). |
| 10 | S93 failures traced to upstream evidence? | **All 8 S93 failure titles traced** (bouncy, hotdeath, urlchecker, random_simplestopwatch → density/codec/color laws; bobball, dodge → clip laws; mini-tetris, minicraft → AnimationDrawable + frame-submission laws; simplestopwatch UNREADABLE_TEXT → shaping/fallback/tofu/OCR laws). 20 of 48 laws carry a direct S93 finding link. |
| 11 | Implementations that reduce MiniAndroid code? | wuffs (GIF/PNG/BMP decoder), pixelmatch (AA-aware diff), imagehash (frame identity), CDroid (View/NinePatch/Ripple/StaticLayout C++ semantics — license-gated), glide Downsampler (density), resvg (SVG), Yoga (wiring R3), FriBidi+HarfBuzz+FreeType (text R4), tesseract (OCR oracle), ARSCLib/androguard (ARSC oracles). |
| 12 | Tests that can be ported? | GIF disposal (Pillow/golang/wuffs), density table (glide), clip (Skia/CDroid CTS), shaping (harfbuzz in-house), diff (pixelmatch), layout (yoga gentest), screenshots (testify exclusions, paparazzi determinism). |
| 13 | No adequate upstream implementation? | (a) MiniAndroid's DEX interpreter (charter: in-house by design); (b) resource-resolution runtime glue stays in-house but diff-tested against ARSCLib/androguard; (c) WebView visual-readiness *verifier* for a re-implemented WebView — upstream gives the readiness *contracts* (postVisualStateCallback, AwContents.onDraw gating, ready-to-show) but the adapter must be written; (d) GIF compositor: upstreams provide semantics + tests, not an Android-Drawable-shaped runtime — port required. |
| 14 | Primary reference per subsystem? | Rasterization: google/skia. Android View/Drawable/text-in-C++: houstudio/cdroid (LGPL gate). Shaping: harfbuzz. Android text layout: google/minikin. Glyph raster: freetype. Bidi: fribidi + ICU. PNG/JPEG/WebP: libpng/libjpeg-turbo/libwebp (already wired). GIF: wuffs. Density: AOSP BitmapFactory + glide Downsampler. Surface/frame: AOSP SurfaceView/ViewRootImpl + libGDX AndroidGraphics + SDL + SurfaceFlinger. Web: chromium AwContents + WebKit ImageLoader + WPT. Visual diff: pixelmatch. Screenshot harnesses: roborazzi/paparazzi/testify/Shot. Layout: yoga/constraintlayout/flexbox. |

Not counted: README-only inspection never counts as deep inspection
(57 identity-verified repos are explicitly labeled `IDENTITY_ONLY`).

## 2. Source-first law and automation

- **CONSTITUTION_V2.md §170 GRAPHICS SOURCE-FIRST LAW** — permanent, 13-step
  mandatory workflow + binding rules (never from memory, stars ≠ correctness,
  >~50 LOC requires a registry search first, preference order AOSP → … → reference).
- **tools/source_lookup.py** — deployed; `WRONG_CLIP` → 6 sources + 6 laws,
  `UNREADABLE_TEXT` → shaping/layout/bidi/raster/OCR families; unknown categories
  exit 2; `--from-failure-map` classifies an entire S93 failure map per title.
- **docs/GRAPHICS_SOURCE_REGISTRY.md/.json** — permanent, machine-readable,
  identity migrations preserved (`identity_history`), mirror/fork policy explicit,
  maintenance law (§15: moving repos are updated, never silently replaced).

## 3. Identity-verification honesty (no fake entries)

- 127 registry entries → **122 verified distinct** GitHub repositories.
- Directive-listed questionable identities were verified, not guessed:
  `android/graphics`, `google/android-codelabs`, `android/platform_frameworks_support`
  do not resolve on GitHub → recorded UNVERIFIED (directive §3 requirement).
- Migrations recorded with history: `notofonts/noto-emoji` → `googlefonts/noto-emoji`;
  `facebookarchive/screenshot-tests-for-android` → `facebook/screenshot-tests-for-android`;
  `renderdoc/renderdoc` → `baldurk/renderdoc`.
- Duplicates collapsed to one canonical record with multiple families
  (skia, androidx, harfbuzz, icu, minikin, freetype, accompanist, compose-samples,
  nowinandroid) — no repository counted twice.
- Off-GitHub canonicals preserved as references, excluded from the distinct count:
  google/minikin (googlesource), aosp-mirror/platform_frameworks_native
  (absent from aosp-mirror; LineageOS fork recorded as separate evidence source),
  mesa3d/mesa + cairo/cairo (freedesktop).

## 4. Deep-mining highlights (exact locations, not "handles images")

- `harfbuzz/harfbuzz@873dbc1e32` — `src/hb-ot-shape.cc:1171 hb_ot_shape_internal`;
  `test/shape/data/in-house/tests/` (arabic-mark-order, use-syllable, …) → shaping
  law + PORT_TEST for UNREADABLE_TEXT.
- `google/minikin` (googlesource `main`) — `libs/minikin/Layout.cpp` (doLayout,
  layoutLine, MinikinPaint) → per-codepoint font-fallback law L-S94-TEXT-4.
- `aosp-mirror/platform_frameworks_base` — `BitmapFactory.java` (decodeResourceStream,
  inDensity/inTargetDensity/inSampleSize), `Canvas.java` (clipRect/saveLayer/quickReject),
  `View.java` (draw() @1794–1813, dispatchTouchEvent @16551, getHitRect @20459),
  `SurfaceView.java` (updateSurface/mHaveSurface), `ViewRootImpl.java`
  (performTraversals), `NinePatchDrawable.java`, `AnimationDrawable.java`
  (selectDrawable/setFrame/run) — 8 files, all pinned-sha evidenced.
- `google/skia` — `src/core/SkCanvas.cpp` (MCRec clip stack), `src/codec/SkPngCodec.cpp`
  (premultiply during swizzle), `src/codec/SkGifCodec.cpp` (disposal-aware decode).
- `chromium/chromium` — `android_webview/.../AwContents.java` (onDraw/isReadyToDraw/
  requestDraw) → WebView paint-gating law L-S94-WEB-2.
- `libgdx/libgdx` — `AndroidGraphics.java` (onDrawFrame/surfaceChanged/resume/pause)
  → GLSurfaceView frame-submission law L-S94-SURFACE-2.
- `houstudio/cdroid@da89e06b` (S94 §5 mandatory deep dive) — 58 files harvested:
  `view.h` (87KB; onDraw/onMeasure/onLayout/onTouchEvent), `textview.cc` (274KB;
  measureText @7147), `imageview.cc` (stretch), `viewgroup.cc` (dispatch),
  `ninepatch.cc`+`ninepatchdrawable.cc`+`ninepatchrenderer.cc` (stretch-region laws),
  `rippledrawable.cc`+`rippleforeground/background`, `animationdrawable.cc`,
  `vectordrawable.cc` (65KB), `staticlayout.cc`+`dynamiclayout.cc`, `canvas.*`,
  plus 266 test files incl. `cts_ninepatchdrawable_test.cc`,
  `cts_rippledrawable_test.cc`, `cts_animationdrawable_test.cc` and fixture
  `ninepatch_0.9.png`/`ninepatch_1.9.png`. VERDICT: highest-value C++ semantic
  reference for MiniAndroid View/Drawable subsystems; **LICENSE = LGPL-2.1
  (pinned-sha verified, sha256 6da7ddf4…)** → behavioral reference / dynamic link;
  static port requires LGPL compliance.
- `google/wuffs@f31d952b` — `release/c/wuffs-v0.4.c`: `wuffs_gif__decoder` + disposal
  state machine; 437-file test corpus → GIF decoder port candidate.
- `mapbox/pixelmatch@b2800051` — `index.js`: colorDelta/antialias/maxDelta/threshold
  → AA-aware diff law to cut WRONG_COLOR false positives.

## 5. §20 deterministic random sample

- seed 20260924, `random.Random(seed).sample` over the 36 canonical artifact-bearing
  titles (pool sha256 recorded), registry SHA `f38c9af5f83896bd…`.
- selected 8: 2048, Chess Clock, Memory, MicroTimer, Mini Tetris, TriPeaks,
  com.dozingcatsoftware.dodge, uNote — categories: ui-interactive, text-heavy,
  game-animation, canvas-game, normal-app.
- results reference existing machine evidence with explicit pointers
  (Mini Tetris → S93 ANIMATION_FROZEN; dodge → S93 WRONG_CLIP); the rest are
  recorded `SELECTED_NOT_YET_EXECUTED_IN_S94` — no unexecuted claims made.
- graphics-heavy coverage is by pool construction (artifact-bearing titles only).

## 6. Success criteria (§28) — status

| Criterion | Status |
|---|---|
| New graphics bug → automatic classification → registry lookup | **DONE** (tools/source_lookup.py + CATEGORY_RULES + failure-map classifier) |
| Upstream source/test inspection before implementing | **DONE as law** (CONSTITUTION §170 step 4–6; >50 LOC gate) |
| Existing algorithm discovered → semantic law → fixture → APK | **chains recorded for all 8 S93 failure titles** (gap_map.json); fixture/APK verification is the NEXT campaign's execution work (P0 roadmap) |
| Registry is permanent + maintained | **DONE** (md+json, identity_history, maintenance law) |
| "Coder knows where the strongest implementation and tests are" | **DONE** (48 laws → 20 test corpora → 23 reusable implementations, all hash-pinned) |

## 7. §29 accounting

- Registry count: **127 entries** (122 distinct GitHub-verified + 4 off-GitHub
  canonicals + 1 unverified directive identity).
- Source findings: **49** (findings.jsonl) — 48 laws + 1 CDroid deep-dive record.
- Reusable implementations: **23** (implementations.jsonl).
- Reusable test corpora: **20** / 3,996 test files (tests.jsonl).
- Commit/remote SHAs: recorded at push time in the worklog (this file's commit
  is the campaign deliverable; see `git log --oneline | grep s94`).
- Remaining blockers:
  1. 57 identity-verified repos are `IDENTITY_ONLY` — deep mining queued.
  2. License clarifications pending for 7 repos (root-license-file absent).
  3. P0 engineering execution (density fixture table, GIF disposal port, clip
     stack law in engine, R4 text wiring, OCR probe) is the next campaign's work —
     S94 delivered the source→law→test chains, not the engine changes.
  4. resvg test suite and noto-emoji reference rasters recorded but not yet
     fetched (PENDING_FETCH markers in source_to_law.json are now 0/48 for laws;
     these fixture fetches remain queued).

## 8. Evidence file inventory

```
docs/GRAPHICS_SOURCE_REGISTRY.md / .json      permanent registry (md + machine)
docs/GRAPHICS_DO_NOT_REINVENT.md              expanded do-not-reinvent table
docs/GRAPHICS_SOURCE_ROADMAP.md               P0–P4 roadmap with measured fan-out
docs/S94_GRAPHICS_SOURCE_MINING.md            this report
run/s94/source_mining/repositories.json       127 identity records + HEAD SHAs + licenses
run/s94/source_mining/license_map.json        per-repo license evidence
run/s94/source_mining/findings.jsonl          49 findings (sha256 + symbol line hits)
run/s94/source_mining/implementations.jsonl   23 reusable implementations
run/s94/source_mining/tests.jsonl             20 upstream test corpora
run/s94/source_mining/source_to_law.json      48 laws + category lookup rule
run/s94/source_mining/gap_map.json            10 gap families + S93 traces
run/s94/source_mining/random_sample.json      §20 seeded sample
run/s94/source_mining/clones_harvest.json     20-clone deep harvest
run/s94/source_mining/rawfetch_results.json   pinned-SHA fetch results
tools/source_lookup.py                        §14 automatic consultation tool
CONSTITUTION_V2.md §170                       GRAPHICS SOURCE-FIRST LAW
```
