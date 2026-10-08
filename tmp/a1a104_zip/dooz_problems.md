

## A104: dooz (TicTacToe) APK execution — Compose Navigation boundary

**Status:** FRAME_CAPTURED — Compose runtime internals missing

**APK:** io.github.yamin8000.dooz v18 (SHA: d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17)

**Execution:**
- 20,166 IMPLEMENTED APIs (the largest of any app tested)
- 253 STUBBED, 0 MISSING, 0 ERROR
- ViewTree: ComposeView → AndroidComposeView (0 children, 0 draw ops)
- Screenshot: 1 unique color (250,250,250 = white background)

**Root cause:** Compose Navigation's NavHost calls addNavigator("composable", ComposableNavigator()) 
during composition, but the composition never materializes because the Compose runtime 
internals (SlotTable, Composer, Applier, LayoutNode) are not implemented.

The error chain:
1. NavHost composable calls NavController.addNavigator("composable", ComposableNavigator())
2. This should happen inside the composition (setContent → recompose)
3. But AndroidComposeView.dispatchDraw has 0 ops — the composition never ran
4. So when NavHost tries to navigate to a "composable" destination:
   "Could not find Navigator with name "composable"" ISE is thrown

**Honest status:** dooz is a Compose app that requires the full Compose runtime 
(WAVE 8 — multi-week effort). The runtime correctly:
- Loads the APK (1.75MB)
- Parses 20166+ methods
- Dispatches onCreate/onStart/onResume
- Creates ComposeView + AndroidComposeView
- Calls setContent on AbstractComposeView

But cannot:
- Materialize the Compose composition (SlotTable slot management)
- Run the Composer (recompose loop)
- Apply changes via Applier (LayoutNode tree building)
- Measure/layout/draw the LayoutNode tree

This is the same boundary as battleship (Compose-based).

