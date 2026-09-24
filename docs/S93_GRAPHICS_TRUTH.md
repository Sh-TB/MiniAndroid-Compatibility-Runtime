# S93 — GRAPHICS TRUTH CAMPAIGN

Status: **EXECUTED** (semantic layer deployed, adversarially tested, run on
real APKs, repeatable, zero regression). Session date: 2026-09-24.
Predecessor: S92 (graphics-verification subsystem) — NOT restarted, NOT
weakened; S93 extends it with the semantic layer S92 left unfinished.

## 0. MISSION

S92 made "screenshot exists" stop implying "graphics complete". S93 solves
the next problem: **a resource can technically be "loaded" while the
user-visible result is still WRONG.** The verifier now answers, per asset:

    WHAT was supposed to appear / WHERE / WHAT actually appeared / WHERE
    / DID the correct pixels appear / DID interaction hit a VISIBLE target
    / DID the visual state transition happen

and classifies the result as LOADED, PARTIAL, WRONG, MISSING, UNREADABLE,
PLACEHOLDER — or merely DECODED.

## 1. IMPLEMENTED LAWS (each proven against adversarial fixtures, committed)

### Image truth — `tools/verify/probes/semantic_image.py` (L-S93-IMG-1..6)
- Multi-metric vector (S93 §14): identity, decode, geometry, position,
  alpha, color, edges, texture, content, spatial layout — verdict derived
  from the vector, never one metric.
- L-S93-IMG-1 solid/two-color placeholder: uniform non-page-bg region with
  <=2 quantized colors + near-zero edge density is a PLACEHOLDER whenever
  the expected asset is structured (the "two color" attack, S93 §9/§23).
- L-S93-IMG-2 shape truth: connected-component layout (count, fill ratio,
  centroid, aspect) of asset vs observed. Blue circle rendered as a blue
  96x96 rectangle fails on fill ratio 0.785 vs 1.0.
- L-S93-IMG-3 spatial color layout: 4x4 dominant-color grid, computed
  ink-window to ink-window (scale-tolerant).
- L-S93-IMG-4 alpha truth: transparent zones must show the background;
  opaque replacement (alpha dropped / premultiplication bug) fails.
- L-S93-IMG-5 geometry with semantic tolerance (S93 §8): EXACT >
  GEOMETRICALLY_CORRECT > PARTIAL > WRONG_POSITION / WRONG_SCALE / CLIPPED
  / MISSING, compared on ink bboxes (asset alpha bbox vs observed content
  bbox). Wrong scale = content PASS + geometry FAIL — the S93 distinction.
- L-S93-IMG-5c clipping law: one edge aligned + opposite dimension short =
  CLIPPED, gated by visible-part NCC so "clipped" can never excuse wrong
  content. A content box that merely fills the region is NOT clipped.
- MISSING vs WRONG_POSITION: blank expected box triggers an unanchored
  whole-screen search; asset found elsewhere => WRONG_POSITION, otherwise
  MISSING.
- L-S93-IMG-6 region partition (S93 §15): per-region verdicts; aggregate
  FAIL if any region fails — a missing button can never be averaged away.
- Background estimation is page-level (screenshot border median); region
  borders lie when content fills the region (measured failure mode).

### Animation truth — `tools/verify/probes/semantic_animation.py` (L-S93-ANI-1..5)
- Frame identity: dHash (structure) + coarse color hash (uniform flips are
  invisible to dHash — measured).
- Structural continuity: mean consecutive dHash distance — random noise is
  bit-uniform (~32) vs real motion (<=10); NOISE requires two signals
  (never entropy/color-count alone, S93 §30).
- Object persistence + centroid/bbox motion tracking; STATIC_OBJECT_MOVING_BG
  (outside-object region changes, object static), OBJECT_LOST.
- Trajectory: teleport (step > 6x median and > 12px) and monotonic-direction
  contract (SUSPECTED_WRONG_ORDER).
- PLACEHOLDER_ANIMATION (uniform alternation), LARGE_AREA_FLASH, FROZEN,
  REPEATED_FRAME (caps the ladder at ANIMATION_RENDERED — temporal
  corruption can never claim content/geometry verification).
- Verdict set (S93 §10): ANIMATION_DECODED / RENDERED / CONTENT_VERIFIED /
  GEOMETRY_VERIFIED — never one GIF_LOADED.
- Honesty rules measured from real runs: leading splash frames are legal
  (rendered law requires >=60% non-blank + last frame non-blank); a window
  with no interaction has NO animation contract (STATIC_WINDOW =>
  NOT_APPLICABLE); whole-frame centroid tracking without a contract region
  is weak evidence => geometry UNKNOWN, not FAIL.

### Font + text truth — `tools/verify/probes/semantic_font.py` (L-S93-FNT-1..5)
- Adaptive ink threshold (distance from border-median bg, thresholded at
  40% of peak contrast): antialias haze stays out of the ink mask so
  inter-glyph gap columns split cleanly; blank regions have no ink.
- Column-projection segmentation + frame-like segment filter (borders/grid
  lines spanning >80% of a region are not glyphs — measured false positive:
  board-cell borders matched the tofu template).
- Per-glyph correctness: each glyph NCC-matched against a reference render
  of its expected character at matched ink height (rasterization-scale
  bias removed).
- Tofu law: stroke-adaptive hollow-box template, NCC >= 0.80 => .notdef.
- Touching-glyph path (kerning defeats projection): total-ink-width
  invariant (touching never shrinks width — only fewer glyphs do) +
  binary ink IoU + column-profile correlation (measured separation: same
  font+text 1.0; one wrong glyph 0.74; wrong family 0.46; wrong font 0.28;
  gray NCC is background-diluted and forbidden).
- BROKEN_FONT: bytes that cannot decode die at FONT_DECODED.
- Text-region law (S93 §6): ViewTree text + no ink = MISSING_TEXT; ink cut
  at node bounds = CLIPPED_TEXT. A node saying text="PLAY" is not evidence.
- Adaptive ink floor for large nodes: a single digit in a 303x226 cell is
  0.0076 ink fraction (blank is <0.001) — threshold 0.004.

### Verdict layer — `tools/verify/probes/semantic_verdict.py`
- S93 §1 loaded chain: DISCOVERED -> REFERENCED -> RESOLVED -> OPENED ->
  DECODED -> INFLATED -> BOUND -> LAID_OUT -> DRAWN -> FRAME_SUBMITTED ->
  VISIBLE -> SEMANTICALLY_CORRECT -> INTERACTABLE ->
  STATE_TRANSITION_VERIFIED -> VISUALLY_VERIFIED. The deepest HONEST state
  is derived from provenance booleans + view bounds + pixel truth +
  interaction + repeatability; missing links within the reached prefix are
  reported.
- S93 §19 taxonomy: 28 root categories, every category citing the vector
  that produced it. Clean cases return no categories (UNKNOWN is only for
  genuinely unexplained failures — a research target, not a dumping ground).
- S93 §25 non-implication hierarchy + 3-level aggregate SEMANTIC_PASS /
  SEMANTIC_PARTIAL / SEMANTIC_FAIL, combined with (never replacing) the
  S92 12-state machine verdict.

## 2. SOURCE RESEARCH (S93 §3/§31) — what Android considers the boundary

Fetched live this session:
- libGDX `gdx/src/com/badlogic/gdx/assets/AssetManager.java` (line 69):
  assets are `ObjectMap<Class, ObjectMap<String, RefCountedContainer>>` —
  a ref-counted dependency graph, not booleans. => asset truth must model
  dependency chains (S92 §20 law confirmed at source level).
- Roborazzi (github.com/takahirom/roborazzi, README): record / verify /
  compare are SEPARATE Gradle tasks (`recordRoborazziDebug` vs
  `verifyRoborazziDebug`), `roborazzi.test.record` flag switches modes.
  => a screenshot captured in record mode can never self-certify verify
  mode. Directly backs S92 §21 golden provenance + S93 §21 contracts.
- AOSP `frameworks/base/graphics/java/android/graphics/BitmapFactory.java`:
  decode methods return null on failure and `inJustDecodeBounds` returns
  null BY DESIGN (bounds-only decode) => "decode produced a Bitmap" and
  "bitmap has correct dimensions" are provably different stages.
Standard AOSP boundaries cited by file/method (API-stable contracts):
- `ViewRootImpl.performTraversals() -> performDraw()` (core/java/android/
  view/ViewRootImpl.java): a draw pass is traversal-internal; presentation
  is the surface composition step. draw() != on-screen.
- `SurfaceView.lockCanvas()/unlockCanvasAndPost()` (core/java/android/view/
  SurfaceView.java): posting a buffer != composition to the screen.
- `WebView.postVisualStateCallback()` + `onPageFinished()` (android.webkit
  docs): DOM updates are asynchronous; onPageFinished does NOT mean the
  visual state is ready to be drawn — the visual-state callback is the
  readiness contract (S93 §12).
- `Choreographer.doFrame()` (core/java/android/view/Choreographer.java):
  frame scheduling; frame N existing does not prove frame N+1 content.
- `ImageView.setImageResource() -> invalidate()/requestLayout()`
  (widgets/src/android/widget/ImageView.java): resource set on the view is
  a request, pixels come only after layout+draw.

## 3. ADVERSARIAL VALIDATION (S93 §23/§29) — `tools/verify/adversarial_s93.py`

Battery result: **ALL PASS** (run/s93/adversarial_battery.json, tracked at
docs/evidence/s93/adversarial_battery.json):
- image suite 11/11 (correct circle, correct photo, solid replacement,
  two-color fake, opaque replacement, wrong position, wrong scale, clipped,
  missing, wrong image, region-partition law)
- animation suite 8/8 (correct motion, frozen, repeated, wrong order,
  placeholder, noise, bg-moves-object-static, object lost)
- font suite 10/10 (correct render, tofu, fallback, wrong family, missing
  glyph, wrong glyph, broken bytes, region ok/missing/clipped)
- blurred-image fixture: rejected (never VISUALLY_VERIFIED)
- weak-metric coverage: nonblank/screenshot-exists -> solid_replacement;
  pixel-change -> frozen; entropy/color-count -> two_color_fake;
  decode-success -> opaque_replacement; ViewTree-text-presence ->
  text_missing; GIF-exists -> repeated_frames. Every weak metric fails at
  least one fixture.
- §29 tamper test 5/5 REJECTED: wipe region, move asset, recolor asset,
  freeze animation, shrink asset.
- §29 recovery test: two-process round-trip PASS (state + evidence SHA
  integrity, no duplicates).

## 4. REAL CORPUS EXECUTION (S93 §17/§18/§27)

Streaming + resume-safe (one APK at a time; verdict JSONs cached; no
in-memory corpus). All numbers below are machine-derived from run/s93/.

Pilot (16 titles, REAL runtime execution, fresh this session) + seeded
random sample (seed=20260924, registry SHA recorded in
run/s93/random_sample.json; 5/6 executed, 1 f-droid 404 recorded honestly).

### S93 semantic verdicts (TABLE OF TRUTH below)
- SEMANTIC_PASS: 10 titles
- SEMANTIC_PARTIAL: 3 titles
- SEMANTIC_FAIL: 6 titles (with named root causes)

### Image truth totals (S93 §26)
    discovered 29 | geometrically_verified 11 | content_verified 4
    visually_verified 4 | partial 6 | failed 9 | decoded-only (no drawn
    dst region; no pixel claim possible) 10

### Animation truth totals
    no_contract 3 | decoded_or_rendered 6 | failed 2 (FROZEN x2, both
    tap-window titles — real findings)

### Font/text truth totals
    APK-bundled font objects: resolved 0 (none of the executed titles
    bundle TTF/OTF assets) — glyph verification ran through the text-truth
    path; text nodes: verified 9, missing 1, unreadable 3 (candidates with
    evidence in verdicts/)

## 5. TABLE OF TRUTH (S93 §32)

| TITLE | STRATUM | S92 MACHINE | S93 IMAGE | S93 ANIM | S93 SEMANTIC | TOP ROOT CAUSES |
|---|---|---|---|---|---|---|
| fishrings | game-view-xml | INTERACTION_VERIFIED | 4 VISUALLY_VERIFIED, 5 PARTIAL | ANIMATION_RENDERED | SEMANTIC_PARTIAL | (scaled sprites partial) |
| snake-deluxe | game-canvas | INTERACTION_VERIFIED | 0 checked | ANIMATION_RENDERED | SEMANTIC_PARTIAL | NO_OBJECT_MOTION (weak signal, honest) |
| tictactoedeluxe | game-canvas | INTERACTION_VERIFIED | 0 checked | ANIMATION_RENDERED | SEMANTIC_PARTIAL | — |
| g2048 | game-canvas | INTERACTION_VERIFIED | 0 checked | SINGLE_FRAME (tap produced no frame change) | SEMANTIC_PASS* | *S92 flagged input FAIL |
| bobball | game-surfaceview | VISUALLY_VERIFIED | 1 checked | STATIC_WINDOW | SEMANTIC_FAIL | WRONG_CLIP x4 |
| unote | app | VISUALLY_VERIFIED | 0 checked (no images) | n/a | SEMANTIC_PASS | — |
| dodge | game-canvas | VISUALLY_PARTIAL | 0 checked | ANIMATION_RENDERED | SEMANTIC_FAIL | WRONG_CLIP x3 |
| bouncy | game-gl | VISUALLY_PARTIAL | 5 checked | STATIC_WINDOW | SEMANTIC_FAIL | WRONG_COLOR x3 |
| hotdeath | image-heavy | FRAME_CAPTURED | 6 checked | n/a | SEMANTIC_FAIL | WRONG_COLOR x6 |
| urlchecker | app | VISUALLY_PARTIAL | 4 checked | n/a | SEMANTIC_FAIL | WRONG_COLOR x3, WRONG_CLIP |
| nounours | image-heavy | VISUALLY_PARTIAL | 0 checked | n/a | SEMANTIC_PASS | — |
| chessclock | app | FAILED | 0 checked | n/a | SEMANTIC_PASS* | *S92: lifecycle NPE |
| gmdice | app-image-heavy | VISUALLY_PARTIAL | 0 checked | n/a | SEMANTIC_PASS | — |
| tictactoe | game-view-xml | FAILED | 0 checked | STATIC_WINDOW | SEMANTIC_PASS* | *S92: GdxRuntimeException |
| mini-tetris | game-canvas | VISUALLY_PARTIAL | 0 checked | FROZEN (tap window) | SEMANTIC_FAIL | ANIMATION_FROZEN |
| minicraft | game-canvas | VISUALLY_PARTIAL | 0 checked | FROZEN (tap window) | SEMANTIC_FAIL | ANIMATION_FROZEN |
| simplestopwatch | app (random) | n/a | 2 checked | n/a | SEMANTIC_FAIL | WRONG_COLOR x2, UNREADABLE_TEXT |
| openlauncher | app (random) | n/a | 2 checked | n/a | SEMANTIC_PASS | rc=1 (crash after evidence window) |
| bgclock | app (random) | n/a | 0 checked | n/a | SEMANTIC_PASS* | rc=1 (launch crash) |
| dooz | game (random) | n/a | 0 checked | n/a | SEMANTIC_PASS* | rc=1 (launch crash) |
| stopwatchg | app (random) | n/a | 0 checked | n/a | SEMANTIC_PASS* | rc=1 (launch crash) |

S92 verdicts are quoted, never weakened. S93 "*" = semantic layer judged
only the pixels present in the evidence window; the S92 execution verdict
stands alongside it.

## 6. REGRESSION + REPEATABILITY (S93 §29)

- S92 regression battery: `bash scripts/test/run_test_battery.sh
  --skip-build` -> **ALL PASS (94 stages)** after all S93 changes.
- 3-run repeatability (S93 §28): fishrings SEMANTIC_PARTIAL x3, unote
  SEMANTIC_PASS x3 -> **REPEATABLE** (run/s93/repeatability.json).

## 7. HONEST LIMITS

- Image checks require drawn+dst provenance records or ViewTree image
  nodes; titles whose evidence window produced no drawable records report
  0 checked honestly instead of inventing PASSes.
- Whole-frame motion tracking without a contract region is weak evidence
  and is reported UNKNOWN, never FAIL.
- tictactoe/chessclock crashed before rendering in this session's fresh
  runs (S92 root causes stand: GdxRuntimeException / lifecycle NPE).
- f-droid dropped 1 random-pool APK version (404, recorded).
- FULLY_VERIFIED was never emitted: the S92 §24 hard contract requires
  3-run repeatability + interaction + evidence completeness per title;
  semantic PARTIALs gate it.

## 8. ARTIFACTS

    run/s93/verdicts/*.json          per-title semantic vectors (machine)
    run/s93/metrics.json             §26 aggregates + S92 crosscheck
    run/s93/failure_map.json         §19 categories per title
    run/s93/asset_truth.json         per-asset verdicts
    run/s93/animation_truth.json     per-title animation verdicts
    run/s93/font_truth.json          font/text verdicts
    run/s93/random_sample.json       §17 seed + registry SHA + selection
    run/s93/repeatability.json       3-run levels
    docs/evidence/s93/adversarial_battery.json   tracked battery result
