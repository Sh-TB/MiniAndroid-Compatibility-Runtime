> RECONCILIATION (post-rebase): origin/main had advanced to CONT-18h; the same root is registered there as **F-NEW-265** (with arm (c) = F-NEW-271). This document = an independent re-derivation of that chain with complementary quantitative evidence; its findings were FOLDED into F-NEW-265's registry row. The 'F-NEW-260' ID in the prose below is the stale local provisional numbering.

# CONT-11 W7 — Dooz Draw-Path Root Cause: `isPlaced` Never Set on Composed Nodes

**Binary under test**: `aed46450c103f2ea` (clean rebuild reproduced the frozen W6 lineage byte-exactly).
**APK**: `upload/canonical_apks/io.github.yamin8000.dooz_23.apk` sha256 `299eab21ac8b3c61…` (identity verified).
**Upstream law source**: `upstream/s43/ui-1.11.4-sources.jar` + `ui-android-1.11.4-sources.jar` (dooz pins
compose runtime 1.11.4, navigation 2.9.8 — the exact sources are the law, per the W6 discipline).
**Baseline**: dooz ×3 anchor `d602648e8e401895` zero-drift, `[C013-ONDRAW] dispatched=YES ops=0`,
6 uncaught = the known setup-phase `La;` CancellationException cascade (W5-classified, unchanged).

---

## 1. The frontier this wave attacked

W6 left ONE root: *layer drawContent chains run (Lpz0;.M0/L0/T0 ×42) but the AndroidCanvas bridge
(Ljt1;) is never constructed → 0 canvas ops*. This wave re-proved the live baseline, then drove the
root cause to its final link with a static ↔ runtime ↔ upstream-source triangulation.

## 2. The full draw pipeline (static decode + upstream 1.11.4 map)

R8 identity of every link (all verified by disassembly + the 1.11.4 sources):

| APK class/method | Upstream 1.11.4 | Proof |
|---|---|---|
| `Lt4;.dispatchDraw` | AndroidComposeView.dispatchDraw | bytecode matches source flow (Trace "AndroidOwner:draw", canvasHolder.drawInto, root.draw) |
| `Lhi;` + `Ly3;` | CanvasHolder + AndroidCanvas (ui-graphics) | `Lhi;.a:Ly3;` holder; `Ly3;.a` = wrapped `android.graphics.Canvas` |
| `Lel0;.i(Ldi;Lrc0;)V` | LayoutNode.draw(canvas, graphicsLayer) | body = `I:Lkz0;.d:Lpz0;.L0(canvas, layer)` |
| `Lpz0;` (super `Lfr0;`) | NodeCoordinator | `s:Lel0;` layoutNode, `t/u` wrapped/inner, `P:Lc31;` **layer: OwnedLayer?** |
| `Lpz0;.L0` | NodeCoordinator.draw | `if (P!=null) layer.drawLayer else {translate; M0; translate-back}` — bytecode-identical shape |
| `Lpz0;.M0` | drawContainedDrawModifiers | `T0(4)` = `head(Nodes.Draw)`; null→`h1`; else `Lgl0;.c(canvas,…)` = CanvasDrawScope.draw |
| `T0(4)` | head(Nodes.Draw) — 4 = `Nodes.Draw` mask (0b100) | NodeKind.kt line 86 |
| `Lqz0;.g(I)Z` | NodeKind.includeSelfInTraversal(mask) | tests 0x80 / 0x400000 (OnPlaced/OnRemeasured) — constant FALSE for Draw, upstream-correct |
| `Lxk0;` / `Lug0;` | Outer / Inner NodeCoordinator | h1 = performDraw: outer → `t.L0` (wrapped.draw); inner → children loop |
| `Lxk0;.h1` tail | layout-bounds debug overlay | gated by `getShowLayoutBounds()`; draws 0.5-alpha rects — not content |
| `Lpz0;.r1(Lf90;,Z)` | OwnedLayer.reuseLayer(drawBlock, invalidateParentLayer) | the two strings "layer should have been released before reuse" / "currently reuse is only supported when we manage the layer lifetime" at 0x118/0x182 |
| `Luc0;` | GraphicsLayerOwnerLayer (OwnedLayer impl) | the ONLY `new-instance Luc0;` in the APK is inside r1's cache-miss branch |
| `Ljt1;` | per-thread platform-Canvas forwarder (text path) | sole ctor site `Lj7;.e` (android.text.Layout.draw path) — W6's "Ljt1; never constructed" was a text-path symptom, not the draw root |

## 3. Runtime trace of the dying chain (all rows in run/w7/*)

Per frame (`MINIANDROID_DRAW_WINDOW_TRACE=1`, 430 rows for 6 frames):

```
Lt4;.onDraw → Lt4;.dispatchDraw → canvasHolder adopt (Ly3;.a = platform canvas) ✓
Lel0;.i (root draw) → Lpz0;.L0 → P==null → Ly3;.f(FF) translate ✓ → Lpz0;.M0
  → Lpz0;.T0(4) → Lqz0;.g(4) → Lxk0;.S0 → (U0 walk) → NULL → h1
  → Lxk0;.h1 → t.L0 → … → Lug0;.h1 (inner coordinator)
  → children loop: count=1 (child = o6128) → gate child.I() == FALSE → child.i NEVER CALLED
  → getShowLayoutBounds()==false → return — frame ends with ZERO content ops
```

Decisive counts (whole-run METHOD-TRACE, 85,838 method entries, 12 frames):

| Probe | Count | Meaning |
|---|---|---|
| `Lgl0;.c` (CanvasDrawScope.draw — runs app draw lambdas) | **0** | content never drawn |
| `Lyl;.z` (layered content driver) | **0** | same, layered path |
| `Luc0;.<init>` (GraphicsLayerOwnerLayer) | **0** | no OwnedLayer ever built (legit: no graphicsLayer modifiers) |
| `Lpz0;.r1` (reuseLayer/factory) | 2 | called with drawBlock=NULL, exited before construct |
| `Lqz0;.a / .b` (chain attach/detach) | 65 / 65 | modifier nodes attach with REAL kindSets (e.g. `kindSet=13` = Any\|**Draw**\|Semantics on o6325) |
| `[C013-ONDRAW] … dispatched=YES ops=0` | every frame | dispatch faithful; zero ops |

## 4. THE ROOT CAUSE (final link, runtime-proven)

**Field traces on `Lbt0;.w` (`MeasurePassDelegate.isPlaced`, upstream LayoutNode.kt:826
"isPlaced = measurePassDelegate.isPlaced — this node AND ALL OF ITS PARENTS have been placed")**:

```
get Lel0;.I  ×89      ← the draw-walk gate reads it every frame
put Lel0;.d  ×1       ← initial false at node attach
put (writers) ×0      ← Lbt0;.q0/.r0/.u0@0x84 — the place-pass writers — NEVER EXECUTED
```

And at draw time (ft10/ft3):

```
[FIELD-TRACE] get Lug0;.h1 Liw0;.g obj#2007 value=1     ← children count = 1 (child = o6128)
[LIFEWIN-ZRET] decl=Lel0;.I recv=6128(Lel0;) ret=FALSE  ← isPlaced(o6128) = FALSE
```

`Lel0;.I()` decodes to `J:Lil0;.p:Lbt0;.w:Z` = `measurePassDelegate.isPlaced` — exact upstream shape.

### Statement of the root

**The dooz destination LayoutNodes materialized by the W6 composition fixes never complete the
measure/place lifecycle, so `LayoutNode.isPlaced` stays false. The draw walk's upstream gate
`if (layoutNode.isPlaced) child.draw(canvas, graphicsLayer)` (InnerNodeCoordinator.performDraw)
skips every content node. `CanvasDrawScope.draw` therefore executes zero times and no app draw
lambda ever reaches the (healthy) canvas bridge.**

Upstream anchors:
- `NodeCoordinator.drawBlock`: "if (layoutNode.isPlaced) { draw } else { skip — the layer will be
  invalidated again when the node is finally placed }" — upstream RELIES on placement completing
  later; the engine's place pass never completes it.
- `AndroidComposeView.dispatchDraw` calls `measureAndLayout()` BEFORE `root.draw(...)` — the
  engine's dispatchDraw runs the APK bytecode faithfully, but the measure/place pass that runs
  does not reach the newly inserted subtree.

### What is NOT the problem (negatives established this wave)

- The canvas bridge (adopt + platform-canvas routing) is healthy: `Ly3;.f(FF)` executes through
  the engine's canvas heap object inside the draw window.
- `r1`/`Luc0;`/`P` (the OwnedLayer machinery) is legitimately inert — dooz's drawn UI uses no
  `graphicsLayer{}` modifiers; `P==null` is the upstream-normal plain-draw path.
- `Lqz0;.g(4)=false` is upstream-correct (`includeSelfInTraversal(Draw)=false`).
- W6's "Ljt1; never constructed" was the text-layout draw path (`Lj7;.e`, android.text.Layout.draw)
  — a downstream symptom of the same empty content walk, not an independent root.

## 5. Next wave's fix surface (precise, generic)

Make the compose measure/place lifecycle complete for composition-inserted nodes so `isPlaced`
flips true before draw — i.e. the engine-side equivalent of `measureAndLayout()` reaching the
inserted subtree (upstream: `root.requestLayout()` → `measureAndLayout` in dispatchDraw; writers
of `Lbt0;.w` = the place pass `Lbt0;.q0/.r0`). The candidate upstream pair to reproduce inside the
engine's layout scheduler: measure pass (`Lil0;`) → place pass (`Lbt0;.q0/.r0`) setting
`w=true` up the parent chain. No app-specific or R8-specific code is required — the trigger is the
generic "node inserted by applier → request layout → measure+place before next draw" law.

## 6. Tooling committed this wave

- `scripts/cont11_flatxref.py` — desync-proof flat u16-pattern xref scanner (new-instance /
  invoke / field refs with enclosing class;method).
- `scripts/cont11_rawscan.py` — correct per-method Dalvik disassembler (proper 35c register lists,
  field/method resolution, payload skipping).
- `scripts/cont11_w7_baseline.{sh,py}` — canonical baseline ×3 + draw-window trace harness.
- `scripts/cont11_xref.py` — first-generation walker (kept for reference; superseded by flatxref).

Run artifacts (gitignored `run/w7/`): dooz_base1-3, dooz_drawwin (430 rows), dooz_mtrace (85,838
method entries), ft/ft2/…/ft11 field traces, pt param-trace, summaries in w7_baseline_summary.json.
