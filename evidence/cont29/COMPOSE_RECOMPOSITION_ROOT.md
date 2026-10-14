# CONT-29 / TRACK A — THE FRAME-1 GROUP-DELETION ROOT:
# THE COMPOSE CONTENT WAS DELETED BY THE RECOMPOSER'S FIRST APPLY

Wave: CONT-29 (dual-track continuation). Track A opens at the divergence
CONT-28 recorded as the next wave's target: "GraphicsLayer.draw$ui_graphics
returns at @0x000a before the compositing body".

**VERDICT UP FRONT (no success inflation):** the CONT-28 face was a MISREAD —
decoded against the oracle's own DEX with a ground-truth disassembler, the
@0x000a return is the `isReleased` guard and it is NEVER taken (the whole APK
has no path that clears the flag, and `release$ui_graphics` never entered —
runtime-proven). The compositing body runs END-TO-END on the software path
(`drawWithChildTracking` → `drawBlock.invoke` — NOT the `drawRenderNode` arm,
which is hardware-only). The real reason the oracle frame is a uniform theme
surface is now PROVEN at name+bytecode+runtime level: **the NavHost
destination content (Column + 2 Texts) was REMOVED from the slot table by the
first Recomposer apply** — `Operation$RemoveCurrentGroup` →
`ComposerKt.removeCurrentGroup` → `SlotWriter.removeGroup` ×2 — recorded by
`GapComposer.recordDelete()` from `GapComposer.end()` (the differ's
end-of-region cleanup) while the groups were still live. The recording law
(skip-advance accounting across skipped inner scopes) is the next wave's
fix target; NOT fixed this wave → the Track A outcome is honestly PARTIAL
(first divergence moved + precise recorder named).

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| git HEAD | `baa6654c` == origin/main (the CONT-28 push); flappycow submodule `-dirty` = run-artifact noise, pointer unchanged |
| baseline binary | clean rebuild from HEAD source: **BYTE-EXACT `d35a60d43f83331c`** (134,656,256 bytes) — reproduction proven (a mid-session save raced a failed make and captured a partial file; the clean rebuild settles the artifact question) |
| dooz APK | sha16 `299eab21ac8b3c61` == registry |
| oracle APK | present, sha16 `f2790da666890def` (CONT-28 rebuild) |
| Simple Calculator APK | sha16 `68da25fd9fdf54b4` == CONT-26/27/28 record EXACTLY |
| registry at lock | 594 rows; F-NEW-286 absent (dedup-checked) |
| new tools | `scripts/cont29_ag_disasm.py` + `cont29_ag_method.py` (androguard ground-truth disassembly — androguard installed this session), `cont29_isreleased_scan.py`, `cont29_callers_scan.py`, `cont29_find_methods.py`, `cont29_pkg_census.py` |

NOTE: the campaign's `cont28_disasm.py` width table mis-decodes `/from16`
moves (0x01–0x0b all width 1), which shifts every subsequent pc — the root
cause of the CONT-28 §5 misread. All CONT-29 decode uses androguard.

## 1. A1 — THE BASELINE FACE REPRODUCES

`rc=1`, screenshot `b270ff040b3601dc` (deterministic), 0 engine errors.
PARAM-TRACE over the facade class: 911 rows.

## 2. THE @0x000a FACE WAS THE `isReleased` GUARD — NEVER TAKEN

Ground truth (androguard, `draw$ui_graphics` 325 units):

```
@0x0006 iget-boolean v3, v1, GraphicsLayer->isReleased
@0x0008 if-eqz v3, +3  -> @0x000b
@0x000a return-void                 <- taken iff isReleased==true
@0x000b invoke-direct configureOutlineAndClip()V
@0x000e invoke-direct recreateDisplayListIfNeeded()V
...
@0x0093 if-nez v0, +0x99 -> @0x012c  (v0 = isHardwareAccelerated(native))
   software arm: softwareDrawScope ... drawWithChildTracking(...)
   hardware arm: @0x0130 impl; @0x0132 invoke-interface impl.draw(canvas)
```

Runtime + DEX proof the guard never fires:
* `release$ui_graphics()` NEVER entered (PARAM-TRACE, 0 rows).
* DEX census (`cont29_isreleased_scan.py`): across the WHOLE oracle APK the
  facade `isReleased` is written ONLY by `release$ui_graphics` (val=1). No
  DEX path ever writes it back to 0 — released facades are dead by design;
  Compose draws a different object.
* Body methods DID execute: `configureOutlineAndClip` ×22,
  `recreateDisplayListIfNeeded` ×19, `transformCanvas` ×19,
  `getShadowElevation` ×39, `drawWithChildTracking` ×40, `recordInternal` ×21,
  `addSubLayer` ×13, `draw` ×19.

## 3. THE SOFTWARE COMPOSITING ARM IS THE LIVE PATH

`isHardwareAccelerated(native)` is false on the engine's software canvas, so
Compose's own code takes the software arm:
`drawWithChildTracking(drawScope)` → **`drawBlock.invoke(drawScope)`**
(@0x0031 of drawWithChildTracking — 152 units) — the content lambda
re-executes directly onto the frame canvas. The `impl.draw →
Canvas.drawRenderNode` arm (CONT-28's named "next divergence") is the
HARDWARE-only arm and is correctly not taken. Both facades got real record
blocks: `record-mL-hObY` stored `GraphicsLayerOwnerLayer$recordLambda$1`
into facade 7255 (root) AND facade 7304 (child); `drawWithChildTracking`
read both blocks at draw time.

## 4. THE CONTENT CHAIN RUNS — THEN THE CONTENT IS GONE

Draw-window census (`MINIANDROID_DRAW_WINDOW_TRACE`, 3000-row budget):
`recordLambda$1.invoke` ×18, `NodeCoordinator$drawBlock$1.invoke` ×18,
`drawBlockCallToDrawModifiers$1.invoke` ×18, `NodeCoordinator.draw` ×21,
`drawContainedDrawModifiers` ×26, `AndroidCanvas.translate` ×31,
`BackgroundNode.drawRect` ×3 (once per frame — the ONLY content draw),
`AndroidCanvas.drawRect` ×3. Zero text draws.

Coordinator-draw census (PARAM-TRACE, exact receiver ids): SEVEN distinct
coordinators ever drew — 5500/5507/5497 (root), 5342/5366 (layer-2),
1989/1276. The Text node's coordinator NEVER drew.

Why: **the destination content was already deleted.**

## 5. THE DELETION — RUNTIME PROVEN, STEP BY STEP

1. Composition #1 (`Recomposer.composeInitial`) created and attached the
   destination content: `TextStringSimpleNode` obj#5538 (engine frame 68328)
   and obj#5630 (frame 69231), coordinators 5540/5631, `onAttach` run.
2. First frame dispatch: `GapComposer.recomposeToGroupEnd()` ×3 (composer
   obj#2149) → `RecomposeScopeImpl.compose(composer)` on exactly two scopes:
   obj#3953 (`NavHostKt$$ExternalSyntheticLambda3` → `NavHost$lambda$80` →
   `NavHost(...)` re-ran) and obj#4544 (`AnimatedContentKt$AnimatedContent$9`)
   ×2. **Zero `RecomposeScopeImpl.invoke` rows; zero app-lambda
   re-invocation** (all three `ComposableSingletons$MainActivityKt` lambdas
   invoked exactly once each — the initial composition only).
3. The apply (`Recomposer$runRecomposeAndApplyChanges$2` →
   `CompositionImpl.applyChangesInLocked`) executed the change list:
   `Operation$RemoveCurrentGroup` (stateless singleton, obj#6620 — the ONLY
   allocation of the class) → `ComposerKt.removeCurrentGroup(writer,
   rememberManager)` → `writer.forAllDataInRememberOrder(currentGroup,
   forgetCallback)` (the mass `forgetting`/`recordLeaving` flood) +
   `SlotWriter.removeGroup()` ×2 (writer obj#6690).
4. Mass `onDetach` via `RememberEventDispatcher`: TailModifierNode ×3,
   `EnterExitTransitionModifierNode`, `BlockGraphicsLayerModifier`,
   `BackwardsCompatNode`, `LayoutModifierImpl`,
   **`TextStringSimpleNode` ×2 (5538, 5630)** — the whole destination
   subtree (AnimatedContent content + transition modifiers + texts).
5. NOTHING re-created it: no further `TextStringSimpleNode` allocations, no
   destination-lambda re-entry. The draw-time tree = root + Surface + NavHost
   shell without destination → only the Surface background paints → the
   uniform `fef7ff` frame.

## 6. THE NAVIGATION LAYER IS CORRECT (ruled out as cause)

* `maxLifecycle` writes legal: destination entry impl obj#4088 = STARTED
  (obj#35) at setup → **RESUMED (obj#36)** at frame; graph entry obj#4121 =
  CREATED. Enum ground truth: `Lifecycle.State` ordinals verified from
  `<clinit>` (32=DESTROYED..36=RESUMED) — enum identity is correct engine-side.
* `markTransitionComplete` ran via `NavControllerImpl` — the DESTROY path
  NOT taken (`NavControllerViewModel.clear` never entered; probe = 0 rows).
* `populateVisibleEntries` filter law (`maxLifecycle.isAtLeast(STARTED)`)
  verified with correct constants; `isAtLeast` receiver set = {33,34,35,36}
  with the constant arg obj#35 (STARTED).
* The NavHost derived read (`visibleEntries.filter { navigatorName ==
  "composable" }.lastOrNull()`) received a REAL ArrayList (obj#6633) at the
  recomposition — the state did not flip. `lastOrNull` call sites: EmptyList
  (early setup), ArrayList 4395 (composition #1), ArrayList 6633 (recompose).
* `updateBackStackLifecycle` decoded (450 units) — the RESUMED/STARTED/
  CREATED assignment law matches real nav-runtime.

## 7. THE REMOVER — `GapComposer.recordDelete` (PINNED, NOT FIXED)

DEX caller census of `ComposerChangeListWriter.removeCurrentGroup()`:
**exactly one caller — `GapComposer.recordDelete()`**, called from:
* `GapComposer.end(Z)V` (663 units) @0x00bc and @0x0114 — the differ's
  end-of-region cleanup;
* `GapComposer.startReplaceGroup` @0x0036.

`recordDelete()`: `reportFreeMovableContent(reader.currentGroup)` then
`changeListWriter.removeCurrentGroup()` → the `Operation$RemoveCurrentGroup`
op → at apply: `forAllDataInRememberOrder` (forget everything) +
`removeGroup()`.

**The law divergence:** during the recompose of the NavHost scope, inner
scopes were SKIPPED (legitimate Compose skip — `changed=false`, scopes not
re-invoked, `setUsed` only ever i1). Real Compose's differ ADVANCES past
skipped-but-live groups (they are kept); the engine's differ instead reached
`end()` with those groups un-revisited and recorded `recordDelete` — deleting
the live destination groups. The `isReleased` guard CONT-28 named, the
`drawRenderNode` arm CONT-28 named, and every navigation-state hypothesis
examined this wave are ALL ruled out with runtime evidence.

## 8. NEXT WAVE'S FIX TARGET (named, not fixed)

`GapComposer.end()` differ group-accounting across skipped inner scopes:
decode the 663-unit `end()`, the skip-advance path
(`RecomposeScopeImpl.compose` → block `changed` skip → `skipToGroupEnd`
advance) and `startReplaceGroup`, then implement the accounting law
(skipped-live groups advance the differ; only genuinely-dropped groups
record `recordDelete`) in the engine's execution — generic, zero app
knowledge, dedup-checked against the registry (594 rows; F-NEW-286 absent).

## 9. STATUS LEDGER

| item | status |
|---|---|
| Phase-0 truth lock (HEAD/binary/APKs/registry) | TESTED |
| CONT-28 `isReleased` face reproduced + CORRECTED (misread recorded honestly) | TESTED |
| Software compositing path proven end-to-end (drawWithChildTracking → drawBlock.invoke) | OBSERVED |
| Frame-1 group deletion root-caused (RemoveCurrentGroup ×2, mass detach) | OBSERVED |
| Navigation layer ruled out (maxLifecycle/visibleEntries/enums correct) | TESTED |
| Remover pinned: GapComposer.recordDelete ← end()/startReplaceGroup | OBSERVED |
| Differ accounting fix implemented | NOT ACHIEVED (next wave's opening target) |
| Real app-owned Compose CONTENT pixels | NOT ACHIEVED (no claim) |
| dooz delivery link | PARTIAL — unchanged, byte-anchored |
| Full regression at final binary | TESTED (REGRESSION_MATRIX.md) |
