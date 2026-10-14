# CONT-24 — SKEL-LIGHT EXPERIMENT (impact measurement, test-branch only)

Date: 2026-10-09 · Branch: `cont24/skeleton-light-experiment` (NOT merged — main line unchanged by construction)
Baseline binary: `run/cont24/bin/miniandroid_baseline_fa88902f` (sha16 `fa88902fdee6e982`, CONT-22/23 lineage, byte-exact)
Experiment binary: `miniandroid/build/miniandroid` (sha16 `614677b60931b94f`, branch build)
Gate: `MINIANDROID_SKELETON_LIGHT=1` — default OFF (hook fully inert)

## 0. The hypothesis under test (user directive)

"Instead of emulating the graphics stack piece by piece, simulate ONE generic
'skeleton-light' — by adding ONE skeleton-light, thousands of lines for
graphics and roots and Kotlin and other things were deleted. Test it ONLY as a
test; if it has impact, open an Issue explaining the measured impact. Do not
change our main line."

## 1. What was built (one file + one hook)

- `miniandroid/src/renderer/skeleton_light.{h,cpp}` — **490 lines total**
  (header 68 + impl 422), one compact painter:
  self-contained measure pass (MATCH_PARENT/WRAP_CONTENT/margins/orientation
  laws, AOSP LinearLayout default-horizontal) + paint (real `bg_color` fills,
  5×7 ASCII font texts, depth-cycled outlines, image placeholders, clickable
  ticks, GONE/INVISIBLE honoring).
- One env-gated hook in `stage_render_frame_impl` (execution_engine.cpp, +50
  lines incl. census mapping): after the authoritative-root resolution and
  window-background fill, `MINIANDROID_SKELETON_LIGHT=1` replaces the canvas-op
  draw walk with the skeleton paint; fallback to the main-line path is honest
  when the tree is unusable.
- `Makefile`: `skeleton_light.cpp` added to `RENDERER_SOURCES` (2 lines).

**Dependency proof (link-level, checkable):**
`nm -u build/renderer/skeleton_light.o` → 14 undefined symbols total:
C++ runtime (new/delete/unwind), `getenv`, `roundf`, `std::string::find`, and
`ViewShadow::find_node`. **ZERO references** to canvas_shadow, text_shaper,
bitmap_font_data, vector_decode, gif_decoder, bitmap_shadow, state_list.

## 2. Gate-off sanity (hook inertness) — PASS

Anchors re-run on the EXPERIMENT binary with the gate OFF, canonical protocol
(1080×1920, 40 frames, 120 s):

| target | screenshot sha16 | wanted | verdict |
|---|---|---|---|
| dooz | `d602648e8e401895` | `d602648e8e401895` | MATCH (byte-identical) |
| opencalc | `a976d2f9fb675cb3` | `a976d2f9fb675cb3` | MATCH (byte-identical) |

## 3. A/B battery — 11 targets, canonical sweep protocol (5 frames / 15 s)

Baseline = main-line binary, gate off. Skel = experiment binary, gate on.
`colors` = distinct colors (1/9 sampling), `nondom` = non-dominant pixels.
All runs: `scripts/cont24_battery.sh` → `run/cont24/battery_{base,skel}.txt`.

| target | family | base rc | base colors | skel rc | skel colors | skel tree stats | verdict |
|---|---|---|---|---|---|---|---|
| dooz | Compose | 1 | 1 (#fafafa) BLANK | **0** | 2 | nodes=2 boxes=1 | structure hint on a blank face; **rc flip 1→0 is VERDICT INFLATION (see §5)** |
| opencalc | View app | 1 | 217 rich | 1 | 4 | 56n/13b/15t/6-nonASCII/depth 7 | structure visible; fidelity LOSS vs real render |
| unote | View app | 0 | 128 rich | 0 | 6 | 14n/5b/3t | fidelity loss, structure ok |
| microtimer | View app | 0 | 120 rich | 0 | 7 | 26n/9b/1t | fidelity loss, structure ok |
| gmdice | View game | 0 | 187 rich | 0 | 7 | 10n/2b/6t/5-click | fidelity loss, structure ok |
| stopwatch | View app | 1 | 1 BLANK | 1 | 1 UNCHANGED | no [SKEL-LIGHT] line | tree ABSENT at frame time → skeleton cannot help |
| tictactoe | View game | 0 | 364 rich | 0 | 5 | 18n/7b/11t, 2.09M px touched | full-coverage structure; fidelity loss |
| telegram | complex | 1 | 1 BLANK | 1 | 2 | 5n/1b | first non-blank pixels at this protocol (structure only) |
| notes | AppCompat | 1 | 65 | 1 | 2 | 6n/1b | wash (baseline already flat) |
| flappycow | Surface/GL game | **0** | **507 rich** | **1** | **1 BLANK** | nodes=1 | **REGRESSION: skeleton replaced the surface-composite path and killed the game** |
| ballbreak | Canvas game | 1 | 1 BLANK | 1 | 2 | 5n/1b | structure hint on a blank face |

Determinism (3 fresh runs each, skel mode): dooz `4163ee86125d52c0` ×3,
tictactoe `4bce76f0a58269a7` ×3, telegram `e88f290b3550711a` ×3 —
byte-identical. Same-hash-across-targets observation: telegram/notes/ballbreak
skel frames are byte-identical (`e88f290b3550711a`) — the "generic minimum
frame" (1 outline + window bg) is target-independent.

## 4. The LOC census — how many thousands of lines?

For the **classic-canvas frame family** (the family the skeleton actually
serves), the machinery the skeleton path does not execute:

| file | lines | skel-replaceable |
|---|---|---|
| execution_engine.cpp draw walk (2903–5162) | 2,260 | ~2,140 (prologue+hook+copy ≈120 remain) |
| canvas_shadow.cpp (Canvas op emulation) | 2,261 | 2,261 (0 references from skel) |
| text_shaper.cpp (HarfBuzz/FreeType/FriBidi) | 1,166 | 1,166 |
| bitmap_font_data.h | 2,028 | 2,028 (5×7 font = 672 bytes inline) |
| software_renderer.cpp | 1,434 | ~1,284 (FrameBuffer/RGBA ≈150 stay) |
| vector_decode.cpp | 949 | 949 |
| bitmap_shadow.cpp (decode for paint) | 604 | 604 |
| state_list.cpp | 176 | 176 |
| **total** | **10,878** | **~10,600** |

→ **One 490-line, zero-new-dependency module replaces the role of ~10.6K lines
of machinery for producing an informative frame of a View-family app.**
The user's "thousands of lines" claim is CONFIRMED for frame production.

Honesty scope (must not be overstated): this is per-ROLE, not per-repo. The
machinery still serves other roles — canvas_shadow serves DEX apps' own
`Canvas` API calls at runtime; text_shaper feeds the measure pass and non-frame
consumers; bitmap decode serves app logic (`BitmapFactory.getPixels` etc.).
The census measures "frame production for the View family", nothing more.

The registry angle: 586 roots total, **255 (43.5%) graphics-labeled**
(canvas/draw/render/text/font/bitmap/color/inflate/layout/view/surface…);
105 of them ROOT-CAUSED-FIXED — i.e. roughly one in seven of all fixed roots
exists because of the per-op graphics emulation whose *frame role* the skeleton
covers. ("Roots" + "graphics" + "thousands of lines" — all three parts of the
user's claim check out quantitatively.)

## 5. Hazards measured (the cost side)

1. **VERDICT INFLATION (proven):** dooz flipped rc 1→0 / `Status: SUCCESS`
   because painting the ComposeView *wrapper outline* set
   `app_draw_ops>0` → `app_content_proof()`. That is exactly the
   FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT violation. A production skeleton
   needs its own verdict class (e.g. `SKELETON_STRUCTURE_ONLY`), strictly
   weaker than REAL_APP_CONTENT.
2. **Surface-family destruction (proven):** flappycow 507-color SUCCESS →
   blank + rc 1. A global hook must never replace the GL/surface composite
   path; family routing is mandatory.
3. **Fidelity loss (proven):** every rich render (opencalc 217 → 4 colors,
   tictactoe 364 → 5) collapses to structure. Non-ASCII text (6 runs in
   opencalc) renders as placeholder bars only.
4. **No help where the tree is absent:** stopwatch unchanged — AppCompat tree
   missing at frame time; the skeleton cannot invent a tree.
5. **Masking side-effect:** opencalc log "uncaught" grep hits 9→3 — the same
   2 exception roots (e1/d.f, ConstraintLayout.onLayout) simply stop
   REPEATING per frame when the draw walk is skipped. Fewer log lines ≠
   fewer defects.

## 6. Verdict (the answer to "does it have impact?")

- **Where it WINS:** (a) machinery arithmetic — 490 LOC vs ~10.6K LOC for the
  View-family frame role, with link-level proof of independence; (b) first
  pixels on baseline-BLANK View-family faces (telegram, ballbreak) and a
  structure hint on the Compose blank (dooz); (c) a deterministic generic
  minimum frame usable as a cheap smoke-test across the corpus; (d) it would
  have made ~105 graphics-labeled root hunts unnecessary *for frame
  production* — but those hunts also fixed non-frame semantics, so this is an
  upper bound, not a counterfactual.
- **Where it CANNOT win:** Compose content (dooz's real blocker is
  F-NEW-277 recomposition starvation — composition, not paint); games via
  surfaces (must keep the composite path); real glyph fidelity; trees that
  never existed.
- **Bottom line:** the skeleton is a legitimate *diagnostic and fallback
  layer* (structure-only verdict class), not a main-line replacement. The
  main line stays source-first; this experiment is committed as evidence and
  a reusable instrument (`MINIANDROID_SKELETON_LIGHT=1`), default OFF.

## 7. Reproduce

```bash
git checkout cont24/skeleton-light-experiment
cd miniandroid && timeout 570 make -j1 BUILD_DIR=build   # binary 614677b60931b94f
# A:
bash scripts/cont24_battery.sh /home/z/my-project/run/cont24/bin/miniandroid_baseline_fa88902f run/cont24/base base
# B:
bash scripts/cont24_battery.sh miniandroid/build/miniandroid run/cont24/skel skel
```
