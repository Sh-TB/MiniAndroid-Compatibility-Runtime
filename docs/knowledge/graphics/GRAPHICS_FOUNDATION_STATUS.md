# GRAPHICS FOUNDATION STATUS — S83-GFX-BASE (§43)

Date: 2026-09-22 · Base: `4df34d30` (S82) · Wave HEAD: `6c7d2a22` + this wave's
finalize commit · Binary: `miniandroid/build/miniandroid` (PortableGL-enabled)

Canonical companions (frozen in this wave):
- `docs/knowledge/graphics/GRAPHICS_CONTRACT.md` — semantic law C1–C8
- `docs/audit/GRAPHICS_FOUNDATION_AUDIT.{md,json}` — per-class statuses (JSON
  is machine-canonical; MD carries the audit + wave-1 delta table)
- `docs/evidence/s83gfx/` — 12 JPGs + SHA256SUMS
- `run/s82gfx/LADDER_VERDICT.json` + `run/s83/fanout/FANOUT_S159.json`

## 1. What this wave set out to do

S82 proved one path pixel-correct (ImageView fixture chain) but the graphics
surface was still a patch collection: per-class behaviors lived ad hoc in the
engine/flater, several audit classes were MISSING/STUB, and two registered
blockers (F-NEW-157 GL frontier, F-NEW-159 null-framework receiver) capped the
corpus. The S83 directive: stop waiting for bugs to name the gaps — audit the
whole graphics foundation, write the contract, close P0/P1 gaps with
fixture-pinned implementations, and keep every regression gate green.

## 2. Foundation audit (§4) — result

All 27+ classes classified (IMPLEMENTED / PARTIAL / STUB / NO-OP /
WRONG_SEMANTICS / MISSING) against source reads + S82 pixel evidence.
Headline findings at audit time: VectorDrawable, NinePatchDrawable, Matrix,
LocaleList, WindowInsetsController, Surface = MISSING; Canvas carried five
named semantic gaps (drawPoints/drawLines/drawPosText NO-OP, clipPath NO-OP,
saveLayer without isolation, drawBitmap(Matrix,paint) unresolved); GLSurfaceView
was WRONG_SEMANTICS (construction unwind = F-NEW-157); the framebuffer did not
preserve alpha.

## 3. Contract (§5)

`GRAPHICS_CONTRACT.md` now defines the law every implementation must state:
C1 Canvas state (pre-concat affine + clip + save stack), C2 Paint
independence, C3 Bitmap honesty, C4 Drawable bounds/state/level/alpha/tint,
C5 View lifecycle, C6 Surface/frame/present/capture separation, C7 provenance
chain + FIRST_DIVERGENCE derivation, C8 honesty law. Every new fixture cites
its contract sections.

## 4. Implemented this wave (each with source law → fixture → pixel pin → regression)

1. **Canvas Foundation completed (C1, §6–10)** — drawPoints/drawLines/
   drawPosText recorded and rasterized; clipPath rasterized as scanline spans
   (per-op path-clip snapshot, device-baked); saveLayer/restore real offscreen
   layer isolation (SAVE_LAYER/END_LAYER op markers; alpha/clip inside a layer
   no longer leaks to the base surface); drawBitmap(bitmap,Matrix,paint)
   resolved through the new Matrix shadow with per-pixel exact sampling.
   Pins: `l5b_canvas2` (layer_alpha_blend_128, layer_isolation_no_opaque_red,
   clippath inside/outside, drawlines_blue, drawpoints_orange,
   matrix_rotate_gray, drawpostext_abc).
2. **Matrix (§9)** — `matrix_shadow.cpp`: real heap-object android.graphics.Matrix
   (set/reset/pre/post rotate/scale/skew/concat, mapPoints) replacing the
   MISSING class; the canvas affine remains internal (C1) but the API object
   now exists with AOSP composition order.
3. **VectorDrawable (§14, C4)** — `vector_inflater.cpp`: viewport→bounds
   scaling, pathData commands, fillType even-odd, SVG arc endpoint
   parameterization. Pins: `l4c_vector` (green rect body, even-odd hole shows
   the layer beneath, red ring, white arc circle).
4. **NinePatchDrawable (§14, C4)** — marker-driven stretch law: static regions
   drawn 1:1 anchored to their edges, only the marker patch zone expands.
   Pins: `l4d_ninepatch` (red stripe stays in the left 1:1 zone, blue in the
   right, teal fills the stretched middle — positional assertions, not just
   color presence).
5. **GLSurfaceView + EGL + GLES11 routing (§24–25, C6 GL path)** —
   `gl_surface_shadow.cpp`: real renderer lifecycle (setRenderer →
   onSurfaceCreated → onSurfaceChanged → onDrawFrame) with app bytecode
   dispatched for real; GL10/GL11/GLES10/GLES11 routed into the PortableGL
   software context (one GL, one framebuffer); EGLDisplay/Config/Context/
   Surface as real heap objects with state-honest statics. Pin: `l6_glsurface`
   — app `glClearColor(0.1,0.6,0.9)/glClear` presented pixel-exact
   (26,153,230), provenance chain
   SURFACE_CREATED→RENDERER_BOUND→DRAW_SUBMITTED→FRAMEBUFFER_UPDATED→
   SURFACE_WRITTEN→BUFFER_PRESENTED all true. This moves F-NEW-157 from
   WRONG_SEMANTICS to ADVANCED (the libGDX AndroidGraphics chain itself
   remains open — honestly recorded).
6. **LocaleList/Locale/WindowInsetsController (§32, C8)** —
   `locale_insets_shadow.cpp`: semantic shadows with real heap objects and
   AOSP state laws (appearance bits `(cur&~mask)|(values&mask)`, behavior,
   visibleMask). This is the F-NEW-159 root-cause fix — no catch, no null
   masking.
7. **Provenance §34** — FIRST_DIVERGENCE auto-derivation in the instrument's
   finalize(): walks each event's applicable chain bits in canonical C7 order
   and names the first 0 bit (with its passed predecessors), plus a global
   first divergence; derived from recorded bits only, never hand-claimed.

## 5. Regression gates (all green, post-implementation binary)

| Gate | Result |
|------|--------|
| Golden fixture ladder (incl. 3 new fixtures) | **10/10 PASS** (was 6/7; l6 now real-pass) |
| Foundation battery | **26/26 rc=0** |
| Pixel goldens verifier | **24/24 PASS** (f54 7/7 after evidence resync; pixel shas unchanged) |
| Fanout F-NEW-159 (35-title family rerun) | **35/35 signature eliminated; 35/35 advanced past the old blocker** |

## 6. Fanout discipline (ONE FIX → MULTIPLE TITLES)

The LocaleInsetsShadow fix was measured against the whole F-NEW-156
35-title onCreate-unwind family at the new binary
(`scripts/s83_fanout_rerun.py` → `run/s83/fanout/FANOUT_S159.json`):
- 35/35: no `toLanguageTags`/`setSystemBarsAppearance` in any exception
  context (a `[REC-MISS]` dispatch line = the shadow handled the call —
  execution continued).
- 35/35: advanced to per-title NEXT roots, now named per title in the JSON:
  Godot `RuntimeException` (GAME-001/007), libGDX `GdxRuntimeException`
  (GAME-003, MAND-001), `Resources$NotFoundException` (GAME-002),
  TypedArray-null / ServiceLoader-null (MAND-002), kotlin `now(...) must not
  be null` (APP-001), plus per-title NPEs.
- No status inflation: all 35 remain onCreate-boundary failures; what changed
  is that the shared null-receiver root no longer hides their true next
  blockers. MAND-002/APP-001 records carry `S83_OBSERVED` with the exact
  advance.

## 7. Honest counters

- Ladder l6 passes through the REAL GL path (app bytecode → GL10 dispatch →
  PGL software framebuffer → present → capture). No fake fill anywhere; the
  provenance chain is bit-verified.
- Titles remain BLOCKED (onCreate unwind); no STATE-*) was upgraded anywhere
  in this wave. The only registry changes are root-cause statuses
  (F-NEW-159 → ROOT-CAUSED-FIXED, F-NEW-157 → ADVANCED) and the two
  `S83_OBSERVED` probe records.
- Remaining foundation gaps (next waves, priority order): RasterSurface
  stride/format/dirty/present object + framebuffer alpha preservation (C6);
  Bitmap density/copy/config honesty; code-level LayerDrawable + Inset/Clip/
  Rotate drawables; ImageView scale types beyond FIT_CENTER; view alpha;
  Paint Shader/ColorFilter/Xfermode (P2); Region; SurfaceView/TextureView
  surface lifecycle; GLSL shader parsing frontier; libGDX AndroidGraphics
  chain (F-NEW-157 completion, unlocks P4 engines).

## 8. Definition of Done check (§41)

- [x] Graphics audited class-by-class with statuses + evidence (§4)
- [x] Contract canonical document (§5)
- [x] Canvas/Matrix/Clip/saveLayer semantics implemented + pixel-pinned (§6–10)
- [x] Drawable family gaps closed: Vector + NinePatch (+ fixtures) (§14–15)
- [x] GL surface lifecycle real (software) with fixture proof (§24–25)
- [x] F-NEW-159 root-caused-fixed via semantic shadow, 35-title fanout rerun (§32)
- [x] Provenance + FIRST_DIVERGENCE auto-derivation (§33–34)
- [x] Regression: 26/26 battery + 24/24 goldens + 10/10 ladder (§41)
- [ ] RasterSurface object + framebuffer alpha (next wave, P0 remainder)
- [ ] Real-app non-blank unlock (awaits next per-title root waves)

---

# S83-B2 — FOUNDATION COMPLETION + GRAPHICS SWEEP (2026-09-22)

Base: `010afcab` (S83-GFX-BASE wave 1) · this wave's HEAD appended in the
same commit · Binary rebuilt clean at every step; every gate re-run after
each change.

## 9. What this second wave closed (§39 proactive-completion directive)

The audit's remaining render-blocking classes were closed with the same
discipline (source law → fixture → pixel pin → regression):

1. **LayerDrawable XML (`<layer-list>`)** — AOSP LayerDrawable.inflate law:
   items parse in DOCUMENT ORDER and paint bottom→top; per-item
   left/top/right/bottom insets; item forms = `@drawable` ref (ARSC
   canonical resolution), `<color>` inline, inline `<shape>` (full
   GradientState subset parse). Ownership follows the F-053 last-writer
   law.
2. **GradientDrawable RING/LINE kinds + dash strokes** — the f053 shape
   draw law now renders: RING annulus (innerRadius/thickness px override;
   ratio law = bounds-dim / ratio, default 9 — the documented
   developer.android.com contract), LINE (single horizontal center line in
   the stroke paint), and dashWidth/dashGap modulation on stroke bands
   (edge-direction mod pattern; corner arcs stay solid — honest
   simplification). **Toolchain law discovered and pinned**: aapt2 compiles
   `android:shape` as the INT_DEC enum with data word = kind and the
   enum order is rectangle=0, oval=1, **line=2, ring=3** (matches the
   GradientDrawable Java constants; the earlier in-tree comment had the
   ring/line pair swapped and the fixture pins caught it).
3. **Code-level LayerDrawable/GradientDrawable** — the F-NEW-158 capture
   family extended: `LayerDrawable.<init>(Drawable[])` children +
   `setLayerInset` materialized into the SAME bg_layers paint law;
   `GradientDrawable` GradientState setters (setShape/setColor/
   setCornerRadius/setStroke/setInnerRadius/setThickness) captured on the
   drawable object and applied at `setBackground` (AOSP mBackground swap).
   Pins: pad+inset-ring and rounded-rect+stroke-follows-corner.
4. **R-NEW-403 (doz family root cause)** — `CollectionShadow::handles_class`
   had NO `Ljava/util/WeakHashMap;` entry: every WeakHashMap op REC-MISSed,
   `keySet()` answered null, and `Set.iterator()` NPE killed dooz (Glide
   RequestManager lifecycle registry, `Lg/b;.d`) before the first frame.
   Fix routes the whole WeakHashMap family into the real CollectionShadow
   map laws (plus a bridge-side keySet/values view law for registry-less
   modes). Observed: dooz advances crash-before-frame → rendered shell;
   the NEXT frontier is the shared WindowRecomposer context chain
   (R-NEW-344 family). Fanout: every Glide/lifecycle WeakHashMap registry
   in the corpus shares this family.

New fixtures: `l4e_layerlist`, `l4f_codelayer` (source under
`fixtures/s83gfx/`, pins in `scripts/s83b_ladder.py`, verdict
`run/s83b/S83B_LADDER.json`, evidence `docs/evidence/s83b/`).

## 10. Sweep: 10 apps + 20 games + 2 mandatory high-level (§41 real runs)

Every title re-run at this HEAD with provenance instrumentation
(`scripts/s83b_sweep.py` → `run/s83b/sweep/SWEEP_RESULTS.json`), the final
frame measured by the S81 visual audit (levels L0–L5, honest, no score),
plus an interactive `--click-test` pass (`scripts/s83b_interact.py`) that
drives real clicks through the canonical TouchDispatcher:

- **Games (26 run)**: own-built Snake Deluxe / Mini Tetris / 2048 / S72
  snake remain the L3 leaders; Snake autoplay re-proven at HEAD (3 apples,
  100-frame continuous run, prefix-verified, GIF evidence). TicTacToe
  Classic reached 9 DISTINCT STATES under clicks (real X/O gameplay).
  gmdice 4 distinct states (dice roll law intact). The F-NEW-156
  onCreate-unwind family still caps the fresh-corpus faces (honest L2).
- **Apps (12 run)**: Notes/gmdice/keyboard honest renders; uNote interactive
  produced no new state (honest — recorded); chessclock/solitaire-family
  still onCreate-boundary.
- **Mandatory high-level**: P9 (libGDX) and TimeLimit still hit their
  documented frontiers (F-NEW-157 / ServiceLoader family) — advanced past
  the S83 LocaleList root, not passed. No fake upgrades.

## 11. Regression gates (final binary)

| Gate | Result |
|------|--------|
| Foundation battery | **26/26 rc=0** |
| Pixel goldens | **24/24** (shas unchanged) |
| Golden fixture ladder | **10/10** |
| S83-B2 foundation ladder | **2/2** (new pins) |
| Snake autoplay | **3 captures**, 100-frame run, prefix verified |

## 12. Remaining honest frontier (P2–P4, updated)

Paint Shader/Xfermode rasterization (record-only today), Bitmap
density/copy/config breadth, Region, SurfaceView/TextureView surface
lifecycle, standalone Inset/Clip/Rotate drawables beyond layer insets,
GLSL shader parsing, libGDX AndroidGraphics chain (F-NEW-157), and the
Compose recomposer context chain (R-NEW-344 family, now with dooz18 as
its newest member). Each is named with evidence — none silently dropped.
