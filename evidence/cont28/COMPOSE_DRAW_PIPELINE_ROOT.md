# CONT-28 / TRACK A — THE SUPER-DISPATCH PROTO LAW + THE RENDERNODE CLAIM LAW:
# THE GRAPHICSLAYER CTOR-SKIP FACE RESOLVED, THE DRAW PIPELINE CLEAN

Wave: CONT-28 (dual-track continuation). Track A resumes the real-Compose
oracle at the divergence CONT-27 recorded as the next wave's opening target:
"GraphicsLayer created WITHOUT executing its <init> (impl field null →
GraphicsLayer.setPosition f141-null-recv)" — the ctor-skip family.

**VERDICT UP FRONT (no success inflation):** the oracle run is now
EXCEPTION-FREE through the entire draw pipeline (crash.log Total Errors: 0 —
the first zero-error draw-pipeline run for the real-Compose oracle), and the
frame carries the app's OWN Material3 theme surface color (`fef7ff`, full-PNG
decode) — real app-owned pixels produced by the real draw path
(`BackgroundNode.drawRect` executing real DEX inside the layer record). The
content compositing step (`GraphicsLayer.draw$ui_graphics` →
`GraphicsLayerImpl.draw` → `Canvas.drawRenderNode`) is NOT yet reached — the
early-return branch before it is the next first divergence, precisely named
with bytecode offsets (§5). Two new generic P0 roots were root-caused, fixed,
and regression-proven: F-NEW-284 (super-dispatch proto law) and F-NEW-285
(RenderNode claim-gate law). dooz itself is untouched and byte-anchored.

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| git HEAD (start) | local was 49 commits BEHIND origin/main (previous sessions' work lived on the remote; local `e99c2fbd` = CONT-10 era). Fetched + fast-forwarded to `9c42dd61` == origin/main (the CONT-27 push). |
| baseline binary rebuilt | BYTE-EXACT `6823170ebd443118...` (the CONT-27 final) — reproduced with `timeout 570 make -j1 BUILD_DIR=build` |
| dooz APK | sha16 `299eab21ac8b3c61` == registry |
| oracle APK | REBUILT size-exact 8,233,173 bytes (sha16 `f2790da666890def` — honest non-byte-identical, toolchain drift; identity = size + id-table + behavior parity: the recorded face reproduces) |
| Simple Calculator APK | re-downloaded from the F-Droid archive: vc8 sha16 `68da25fd9fdf54b4` == CONT-26/27 record EXACTLY |
| registry at lock | 592 rows; F-NEW-284/285 absent (dedup-checked) |
| issues | #383/#384/#385 evidence chain reused from CONT-25/26/27 records (no new directive posts this wave) |

## 1. A1 — THE BASELINE FACE REPRODUCES

At the byte-exact baseline binary the oracle reproduces CONT-27's recorded
state exactly: rc=1 PARTIAL, `GraphicsLayerImpl.setPosition-H0pRuoY` f141-
null-recv inside `GraphicsLayer.setPosition-VbeCjmY pc=10`, caught by
compose's own catch-alls, rethrown via `LayoutNode.rethrowWithComposeStackTrace`
→ `AndroidComposeView.dispatchDraw` → APP BOUNDARY; screenshot sha16
`b5a7a35d5fe0564b`; >200 f141 rows.

## 2. DECODE — THE "CTOR-SKIP" WAS A DISPATCH MISALIGNMENT

Three ground-truth instruments settled the origin question:

1. **DEX allocation census** (`scripts/cont28_newinst_scan.py`, a
   correct-width dalvik walker): the WHOLE app declares exactly ONE
   `new-instance GraphicsLayer` — inside `AndroidGraphicsContext.
   createGraphicsLayer` (109 units). That method NEVER entered (no RET-BEFORE
   row — the uncapped invoke-path instrument), and `GraphicsLayer.<init>`
   never entered either. A GraphicsLayer object could not have come from DEX.
2. **Allocation trace** (new generic `MINIANDROID_ALLOC_TRACE=<class-substr>`
   diagnostic at the DalvikHeap::allocate chokepoint): ZERO allocations of
   `...layer/GraphicsLayer;` in the entire run — while the object's methods
   executed. The receiver was an engine-side substitute.
3. **PARAM-TRACE** pinned the substitute: every `GraphicsLayer.setTopLeft/
   record/setSize/setPosition` frame had `this = obj#1605 cls=
   Landroidx/compose/ui/layout/PlaceableKt$DefaultLayerBlock$1;` — the
   default EMPTY LAYER-BLOCK LAMBDA, not a layer. The lambda flowed from
   `GraphicsLayerOwnerLayer.<init>` a1 → `createLayer` a3 (explicitLayer) ←
   `placeSelf-MLgxB_4` a4 — and placeSelf's entry showed the SMOKING GUN:
   `a3=NULL a4=lambda` where the Function1 overload's call must produce
   `a3=lambda a4=NULL`. The call had been dispatched into the WRONG overload.

**Root F-NEW-284:** `NodeCoordinator` declares two same-name 32-unit
overloads — `placeAt-f8xVGno(JF, GraphicsLayer)V` and `placeAt-f8xVGno(JF,
Function1)V`. The caller chain (`replace$ui` → `placeAt(JF, Function1)`)
invoke-super'd through `LayoutModifierNodeCoordinator.placeAt(JF, Function1)V`
@0x0000 — and `execute_invoke_super` resolved `proto_35c` for arg conversion
but DROPPED it at `try_recursive_invoke` (no 6th arg). Descriptor-less
selection fell to the shape loop; the new env-gated
`MINIANDROID_OVERLOAD_TRACE` captured the mispick live:

```
[OVERLOAD-PICK] Landroidx/compose/ui/node/NodeCoordinator;
    want=placeAt-f8xVGno exact_desc=absent
[OVERLOAD-PICK]   cand placeAt-f8xVGno(JFLandroidx/compose/ui/graphics/layer/GraphicsLayer;)V bc=32
[OVERLOAD-PICK]   cand placeAt-f8xVGno(JFLkotlin/jvm/functions/Function1;)V bc=32
```

JVMS 5.4.5: selection is (name, descriptor)-based; shape-only selection is a
divergence source. ART super-dispatch resolves the SAME (name, proto) as any
invoke.

## 3. F-NEW-284 FIX + RUNTIME PROOF

Fix (dalvik_engine.cpp, execute_invoke_super only, zero app knowledge):
`proto_35c` hoisted to dispatch scope and passed as `try_recursive_invoke`'s
exact-descriptor authority (empty proto preserves legacy behavior). Plus the
generic diagnostics: `MINIANDROID_OVERLOAD_TRACE` (selection site, bounded
120) and `MINIANDROID_ALLOC_TRACE` (heap chokepoint, bounded 200).

Post-fix: the explicitLayer misalignment is GONE. `createLayer` takes the
real `graphicsContext.createGraphicsLayer()` branch; GraphicsLayerV29
objects materialize through the REAL factory chain; `GraphicsLayerV29.record`
receives a REAL GraphicsLayer (`obj#7255 cls=...layer/GraphicsLayer;`) as
parentLayer; `GraphicsLayerV29.setPosition/setInvalidated/recordInternal`
execute real DEX. The f141 GraphicsLayer face count: >200 → 0.

## 4. F-NEW-285 — THE NEXT FACE, ROOT-CAUSED + FIXED

With the layer object real, the first divergence MOVED into the canvas chain:
`AndroidCanvas.drawRect pc=10` f141-null-recv — the WRAPPED canvas null.
FIELD-TRACE (`MINIANDROID_FIELD_TRACE=internalCanvas`) showed the overwrite:

```
[FIELD-TRACE] put-obj AndroidCanvas;.<init>          internalCanvas obj#7248 value=obj#537
[FIELD-TRACE] put-obj AndroidCanvas;.setInternalCanvas internalCanvas obj#7248 value=<unset>
```

`GraphicsLayerV29.record` (@0x0002) calls `Landroid/graphics/RenderNode;.
beginRecording()Landroid/graphics/RecordingCanvas;` and feeds the result to
`setInternalCanvas` (@0x0016). The engine's CanvasShadow ALREADY implements
the RenderNode recording law for `cls.find("RenderNode;")` (canvas_shadow.cpp
beginRecording → returns the node's RecordingCanvas) — but the registry CLAIM
GATE (`handles_class`, canvas_shadow.h) listed only
`Landroid/view/RenderNode;`. The oracle's DEX references the AOSP SDK>=29
graphics-side class `Landroid/graphics/RenderNode;` — unclaimed, the call
answered VOID, the unset value wiped `internalCanvas`, and every recorded
draw op died.

**Fix (canvas_shadow.h only):** `handles_class` claims
`cls.find("RenderNode;") != std::string::npos` — the family the dispatch
already serves. No dispatch logic changed.

Post-fix: beginRecording returns a REAL RecordingCanvas; the <unset>
overwrite is GONE; `BackgroundNode.drawRect` executes (PC=10/68, real
content draw inside the layer record); **crash.log Total Errors: 0** — the
oracle's first exception-free draw-pipeline run; frame = `fef7ff` (the app's
own Material3 theme surface, uniform fill — app-owned pixels, honestly NOT
yet full content).

## 5. THE NEXT ROOT — RECORDED, NOT FIXED

`GraphicsLayer.draw$ui_graphics` (325 units) runs its head condition and
returns at @0x000a BEFORE the compositing body (@0x000b
configureOutlineAndClip … @0x0132 `invoke-interface GraphicsLayerImpl.draw`
→ `GraphicsLayerV29.draw` → @0x0006 `Canvas.drawRenderNode`). Zero
`drawRenderNode` rows; `GraphicsLayerV29.draw` never enters. The
layer-recorded ops therefore reach the frame only through the direct-fill
path; the frame-truth gate still reads DEFAULT_BACKGROUND_ONLY. The
early-return condition (size/isDefined guard family) is the next wave's
opening target, now with the whole pre-compositing chain proven live.

## 6. STATUS LEDGER

| item | status |
|---|---|
| Phase-0 truth lock (HEAD sync/binary/APKs/registry) | TESTED |
| CONT-27 GraphicsLayer face reproduced at baseline | TESTED |
| F-NEW-284 root-caused + fixed (super-dispatch proto) | IMPLEMENTED+TESTED |
| F-NEW-285 root-caused + fixed (RenderNode claim gate) | IMPLEMENTED+TESTED |
| Oracle exception-free through the draw pipeline | TESTED (0 errors) |
| App-owned pixels on the oracle frame (theme surface) | OBSERVED (fef7ff, uniform) |
| RenderNode compositing (drawRenderNode) reached | NOT ACHIEVED (next divergence named, §5) |
| Real app-owned Compose CONTENT pixels (text/buttons) | NOT ACHIEVED (no claim) |
| dooz delivery link | PARTIAL — unchanged, byte-anchored |
| Full regression at final binary | TESTED (REGRESSION_MATRIX.md) |
