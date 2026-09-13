# S33 SESSION RECORD — R-NEW-332 closed (F-098 + F-099), R-NEW-333 registered

HEAD at session start: 79ac165b (S27, fast-forwarded; S28 F-097 was uncommitted in the live
workspace and is included in the S33 commit). HEAD at session end: 4cf6b9c1.

## 1. R-NEW-332 ROOT CAUSE (evidence-grade, two blockers)

**Blocker A — the active-cycle guard stubbed a legal nested observation.**
The draw-window trace showed: `InnerNodeCoordinator.performDraw (c.u1)` → zSortedChildren sort →
exactly ONE `isPlaced` check (e.G, recv=3101) returning FALSE → no `child.draw` recursion → 0 ops.
ARG-TRACE bound the killer: `[M3-19-CYCLE] Lm0/T;.a#1198 re-entered (depth=16) — active-cycle stub,
lifetime_calls=2`. `m0/T.a` = `SnapshotObserver.observeReads(target, onChanged, block)`. Call #1
(recv=#1198, target node#824) executed; call #2 (recv=#1198, target node#3101) was STUBBED — same
singleton observer object, different target node.

**Blocker B — the draw-dispatch gate required childless leaves.**
After the placement cascade completed (post-F-098), the shadow tree legitimately gained view
children under AndroidComposeView (M0/L0 = AndroidViewsHandler family, attached by real DEX
addView). `[C013-ONDRAW]` (the compose draw dispatch) disappeared entirely because the gate
required `node->children.empty()`.

## 2. UPSTREAM COMPOSE 1.6.7 LAW

- `LayoutNode.attach()` (LayoutNode.kt:440): only the ROOT node gets `isPlaced=true` at attach;
  every child is placed exclusively via the placement cascade:
  `placeable.place → MeasurePassDelegate.placeAt → placeOuterCoordinator → (not-placed branch)
  snapshotObserver.observeLayoutModifierSnapshotReads(layoutNode, false, placeOuterCoordinatorBlock)
  → block → outerCoordinator.place → InnerNodeCoordinator.placeAt (InnerNodeCoordinator.kt:147)
  → measurePassDelegate.onNodePlaced → if (!isPlaced) markNodeAndSubtreeAsPlaced → isPlaced=true`.
- Observations NEST per LayoutNode during the cascade (a child's placement executes inside the
  parent's still-open observation, all on the ONE owner observer) — re-entrancy is contractual.
- `InnerNodeCoordinator.performDraw` (InnerNodeCoordinator.kt:170):
  `zSortedChildren.forEach { if (child.isPlaced) child.draw(canvas) }` — unplaced children are
  legally skipped (this gate was upstream-correct; the runtime state beneath it was wrong).
- `AndroidComposeView.dispatchDraw` (AndroidComposeView.android.kt:1220): draws the whole
  LayoutNode tree via `canvasHolder.drawInto { root.draw }` INDEPENDENT of platform view children
  (interop children only display-list-update through the clip-to-zero super.dispatchDraw path).
- AOSP ViewGroup law: a class that OVERRIDES `dispatchDraw` carries its own draw dispatch.

## 3. FIX (smallest generic, no class names)

- **F-098** — instance-method identity refinement of the M3-19/F-076 active-cycle key:
  key = receiver + up to 2 leading object-arg identities (statics law of F-076 mirrored).
  Same receiver + same payload re-entry = genuine cycle (stub preserved). Same receiver +
  different payload = legal nested visitor/observer dispatch (executes real DEX).
  MAX_RECURSION_DEPTH (80) remains the backstop.
- **F-099** — the render walk dispatches the real draw at visit for a non-framework view node
  whose class chain OVERRIDES `dispatchDraw`, independent of shadow-tree children
  (generic `chain_overrides_method` check; compose family qualifies, plain ViewGroups do not).

## 4. POST-FIX EVIDENCE (semantic transition)

- Pre-F-098: `[DRAWWIN-ZRET] e.G recv=3101 ret=FALSE` (draw window) — no recursion.
- Post-F-098: `e.G recv=3146 ret=TRUE` during the layout window AND at draw; the draw window
  shows the second `LayoutNode.draw (e.n)` + `NodeCoordinator.draw (l.M0)` (recursion) and the
  child's ViewLayer path (`L0.dispatchDraw` chain — the child carries a graphicsLayer).
- Post-F-099: `[C013-ONDRAW] view=792 dispatched=YES ops=0` — the owner-level dispatch fires.

## 5. RESIDUAL (honest) — R-NEW-333

Canvas ops remain 0 because the composed tree is root + 1 node (census: exactly 2 LayoutNode
ctor chains; the child's zSortedChildren is empty). Evidence chain for R-NEW-333 (registry 320):
`AbstractComposeView.Content() = content.value?.invoke()`; RET-TRACE shows the composition's
content-state read (o1290) returned NULL (line 304840) BEFORE its write (line 304889, value =
AndroidComposeView$c — not a composable function); a DIFFERENT ComposeView instance's content
state (o111) received the real app content lambda (o98 = LN/a = ComposableLambdaImpl, full
Function2..Function23 ladder). Two ComposeView instances / two content states; the composition
that ran read the state whose write never landed. Next: instance↔shadow-node↔state pairing,
then the Recomposer second pass / frame pump for async nav/viewmodel content.

## 6. REGRESSION GATE (all green)

- Semantic battery 14/14 PASS (links, long/cmp/conv 14, switch 25, pass3 bridge 66, mutf8 14).
- helloworld_golden §28: **ALL PASS (26 checks)** — real aapt2+ECJ+D8 toolchain fixture,
  resource-backed discriminator, gravity/sp laws, deterministic replay (screenshot SHA
  8a0f2c41f5945730…, 1080×1920).
- tictactoe_golden §29: **ALL PASS (8 checks)** — 10 frames byte-identical across runs
  (613cfccc0f27…).
- Corpus trio (fresh runs, byte-match S27/S28 baselines): microtimer 1,041,437 non-white px
  (c51269309cd14594), gmdice 1,744,539 (22f3730f452b562c), stopwatch 1,944,411
  (81481eb2aa581c53).
- Dooz ×3 deterministic rc=0, SHA 193466ead8fd21d6 (placeholder unchanged — honest frontier).

## 7. APP MATRIX (launch vs render vs gameplay, evidence-graded)

| App | LAUNCH | RENDER | GAMEPLAY | Est. pipeline % |
|---|---|---|---|---|
| Hello family + goldens (View) | VERIFIED | VERIFIED (real frames, byte-locked) | interaction VERIFIED (ttt golden) | 100 |
| ChessClock | VERIFIED | VERIFIED (frame-provenance forensic) | n/a | 100 |
| GM Dice (View) | VERIFIED | VERIFIED | VERIFIED (tap→roll→repaint, pixel-diff) | 100 |
| MicroTimer (View) | VERIFIED | VERIFIED (1,041,437 px) | partial (render-side) | 95 |
| SimpleStopwatch (View) | VERIFIED | VERIFIED (1,944,411 px, GATE H app-truth) | partial | 95 |
| Dooz (Compose) | VERIFIED | DISPATCH VERIFIED, content blocked (R-NEW-333) | NOT TESTED | 70 |
| STTT (Compose+fragments) | VERIFIED | BLOCKED (R-NEW-331 fragment host) | NOT TESTED | 55 |
| Telegram | VERIFIED (to LifecycleRegistry) | BLOCKED (R-NEW-331 + R-NEW-303 desugared streams) | NOT TESTED | 35 |
| WhatsApp / TikTok | NOT OBTAINABLE (Play-only distribution, no APK source; honest) | — | — | 0 |

## 8. NEXT FRONTIER (highest value)

R-NEW-333 (composition content-state pairing) → first real Dooz frame → interaction test;
then R-NEW-331 (fragment-host family: STTT + Telegram); corpus expansion per MASTER CAMPAIGN 3.
