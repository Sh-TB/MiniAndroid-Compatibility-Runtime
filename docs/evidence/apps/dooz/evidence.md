# APP-EVIDENCE — Dooz (io.github.yamin8000.dooz) v18

Status: **LAUNCH = VERIFIED / COMPOSITION = VERIFIED (tree=2 nodes; R-NEW-333) /
MEASURE = VERIFIED / LAYOUT = VERIFIED / PLACEMENT = VERIFIED (F-098) /
DRAW = DISPATCHED-AT-OWNER (F-099), 0 canvas ops (empty-tree frontier) /
GAMEPLAY = NOT TESTED**

## Artifact identity

| Field | Value |
|---|---|
| APK | `io.github.yamin8000.dooz_18.apk` (F-Droid) |
| SHA-256 | `d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17` |
| Size | 1,749,880 bytes |
| UI toolkit | Jetpack Compose (androidx.compose, R8-merged; ui/ui-android 1.6.7) |
| Runtime HEAD | S33 (F-097 + F-098 + F-099, this session) |
| Run dir | `miniandroid/run/s33_det1..3/` |

## Execution evidence (S33, after F-098+F-099)

| Field | Value |
|---|---|
| Exit code | 0 (×3 deterministic runs) |
| Status | `SUCCESS` — zero uncaught exceptions |
| Frame SHA (PNG) | `193466ead8fd21d6…` ×3 (byte-deterministic, unchanged from S28 — honest) |
| Non-white pixels | 802 / 2,073,600 (placeholder frame — honest) |
| Canvas ops | 0 (draw dispatch reaches the node tree; tree is root+1 node — R-NEW-333) |

## Capability matrix (evidence-graded, §15 law)

- [x] **parse** — APK/ARSC/AXMEL/DEX parse, hash-verified
- [x] **launch** — Application `io.github.yamin8000.dooz.content.App` +
      `MainActivity.onCreate` execute as real bytecode
- [x] **attach** — dispatchAttachedToWindow fan-out (default-on): ComposeView +
      AndroidComposeView onAttachedToWindow dispatched; Recomposer machinery drains
- [x] **composition** — slot-table composition completes; **but the composed tree
      is root + 1 node** (R-NEW-333: the view whose composition ran read a
      content-state that was NULL at the time; the app content lambda was stored
      on a different ComposeView instance's state)
- [x] **measure/layout/placement** — F-096/F-096b/F-097 + **F-098**: the placement
      cascade completes as real bytecode; `isPlaced=TRUE` verified at draw time
      (DRAWWIN-ZRET e.G ret=TRUE on the child node — was FALSE pre-F-098)
- [x] **draw dispatch** — **F-099**: the owner-level compose draw dispatch fires
      even with shadow-tree view children present (dispatchDraw-override gate);
      draw walk: dispatchDraw → LayoutNode.draw → NodeCoordinator.draw →
      InnerNodeCoordinator.performDraw → zSortedChildren → child.draw (RECURSION
      EXECUTES) → ViewLayer path (L0.dispatchDraw) → drawBlock →
      drawContainedDrawModifiers → head(Nodes.Draw) checks run
- [ ] **render** — 0 canvas primitives emitted: the composed tree is EMPTY of
      content (root + 1 node) — frontier **R-NEW-333** (composition content-state
      pairing + async content second pass), NOT a draw-pipeline blocker
- [ ] **gameplay** — not testable until render (no visible board)

## Regression gate (S33)

Battery semantic stages 14/14 PASS; corpus trio byte-identical to the S27/S28
baselines: microtimer 1,041,437 non-white px (SHA c51269309cd14594), gmdice
1,744,539 (22f3730f452b562c), stopwatch 1,944,411 (81481eb2aa581c53); dooz ×3
deterministic 193466ead8fd21d6; goldens re-verified at session end.

## Root-cause chain fixed this session (evidence-grade)

1. **F-098** — the active-cycle guard stubbed the LEGAL nested
   `SnapshotObserver.observeReads` (m0/T.a): same singleton observer object
   (#1198), different target node (#824 vs #3101) — compose NESTS observations
   per LayoutNode during placement (upstream 1.6.7 LayoutNodeLayoutDelegate.kt
   placeOuterCoordinator → observeLayoutModifierSnapshotReads(placeOuterCoordinatorBlock)
   → InnerNodeCoordinator.placeAt → onNodePlaced → markNodeAndSubtreeAsPlaced).
   Stub = child's onNodePlaced never ran = isPlaced=FALSE at draw =
   InnerNodeCoordinator.performDraw skipped every child = 0 ops.
   **Fix:** instance-method key = receiver + up to 2 leading object-arg
   identities (F-076 statics law extended); same receiver+payload re-entry
   still stubs (genuine cycles); MAX_RECURSION_DEPTH 80 backstop unchanged.
2. **F-099** — the shadow tree gains view children under AndroidComposeView
   (AndroidViewsHandler family, attached by real DEX addView); the draw-dispatch
   gate required `children.empty()` → the owner never dispatched.
   **Fix:** non-framework node whose class chain overrides `dispatchDraw`
   dispatches its real draw at visit, independent of shadow children.
