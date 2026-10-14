# CONT-23 — GRAPHICAL PROGRESS: per-target state at the verified binary

Binary `fa88902fdee6e982` (byte-exact CONT-22 lineage — zero engine source
changes shipped this wave; see CONT23_REPORT.md §2 for the falsified trial and
its revert). All rows re-measured fresh this wave.

## CROSS_FAMILY_SCOREBOARD (F1–F7, one representative row each)

| Family | APK | Root (current frontier) | Before (CONT-22 report) | After (this wave, fresh) | Render stage | App pixels | Interaction | 3-run |
|---|---|---|---|---|---|---|---|---|
| F1 base-view | opencalc_53 | layout-engine nulls (ConstraintLayout.onLayout, deferred) | 4 uncaught, anchor a976d2f9 | **4 uncaught, anchor a976d2f9fb675cb3 unchanged** | VISUALLY_VERIFIED | app-owned | verified (prior waves) | MATCH ×4 |
| F1 base-view | stopwatch_6 | — (clean) | 0 uncaught, rc 0-era sweep | **0 uncaught** | VISUALLY_VERIFIED | app-owned | n/a | sha 31ddd4d5b8e6d18e |
| F2 2d-canvas | g2048 (anchor) | — (clean) | REAL_APP_CONTENT 59ca1526 | unchanged (anchor suite) | FULLY_VERIFIED | app-owned | verified | MATCH ×3 |
| F2 2d-canvas | tictactoedeluxe (anchor) | — (clean) | af609429 | **af6094295ecb50e3 unchanged** | VISUALLY_VERIFIED | app-owned | verified | MATCH ×3 |
| F3 game-loop | bouncy | libGDX GL20Renderer/EGL native (P10 family) | 2 uncaught (native init) | unchanged (no libGDX work this wave — see report §6) | RENDER_STARTED (surface blocked) | framework only | no | — |
| F3 game-loop | flappycow | — (clean) | SUCCESS 13cf4746 (CONT-21) | unchanged (no wave work) | FULLY_VERIFIED | app-owned | verified | — |
| F4 messaging | telegram / forkgram | Telegram-engine family-internal UI-init faces | 9 uncaught each | **9 uncaught each** (identical census) | RENDER_STARTED | framework chrome | no | shas unchanged |
| F6 compose | dooz_23_toplevel | **F-NEW-277 recomposition starvation** (new; see FIRST_DIVERGENCES.md) | 0 uncaught; visual DEFAULT_BACKGROUND_ONLY; frontier "F-265 measure-pass" | **0 uncaught; visual unchanged; frontier RE-ROOTED — measure pass healthy, content removed by first applyChanges, second applyChanges never runs** | RENDER_STARTED / LIFECYCLE_VERIFIED (frame captured, 0 app ops) | none (background only) | unverified | anchor d602648e8e401895 MATCH ×5 |
| F7 webview | minibrowser v2 | — (clean) | SUCCESS f2169ebc (CONT-21) | unchanged (no wave work) | FULLY_VERIFIED | app-owned | verified | — |
| F5 social/media | NO-TARGET-IN-CORPUS | — | — | — | — | — | — | — |

## Dooz before/after detail (the Phase-1 target)

| Metric | Before wave (pre-fix baseline, fa88902f) | After wave (fa88902f — engine unchanged) | Delta |
|---|---|---|---|
| Compose execution (ComposableLambdaImpl block invokes) | 14 (`Lom.d/h`) | 14 | 0 |
| LayoutNodes created / attached / detached | 6 / 6 / 3 | 6 / 6 / 3 | 0 |
| Measure pass `Lzs0.m` executions (exceptions) | 9 (0) | 9 (0) | 0 |
| Place-writer `Lbt0.q0` executions | 2 | 2 | 0 |
| isPlaced TRUE reads in draw window | 32 | 32 | 0 |
| `Lgl0.c` CanvasDrawScope.draw invocations | 0 | 0 | 0 |
| App-owned draw ops / pixels | 0 / 0 | 0 / 0 | 0 |
| Screenshot SHA-256 (prefix16) | d602648e8e401895 | d602648e8e401895 | unchanged |
| Uncaught faces | 0 | 0 | 0 |
| Engine exit status | 1 (PARTIAL SUCCESS) | 1 (PARTIAL SUCCESS) | unchanged |
| Lifecycle registry reach (androidx dispatch ins) | ON_START 1488 + ON_RESUME 1842 | same | 0 |
| Choreographer ticks (120 s run) | 3, then quiescence, runner never re-arms | same | 0 |

**Honest verdict**: zero graphical movement this wave. The wave's product is the
root-cause decode: the measure/layout frontier named by CONT-22 is healthy; the
content loss happens at the composition/scheduler layer (first applyChanges
removes the NavHost content subtree; the destination-arriving recomposition is
starved at the frame-pump quiescence boundary). The fix belongs to the
Recomposer/AndroidUiDispatcher re-arm law — registered F-NEW-277 (P0).

## Regression gates run this wave

| Suite | Result |
|---|---|
| Anchor suite ×3 (6 anchors, frozen shas) | 18/18 MATCH, zero drift |
| g2048 anchor | included in anchor suite lineage (unchanged) |
| Probe battery (rebuilt canonically) | fcol 20/20, f259 7/7, f259g 12/13 (same known-honest F259-L row), f266 6/6, f268 |
| Lifecycle-transaction probe (NEW, this wave) | 5/5 PASS (locks the G09 start/resume law) |
| Family sweep rc-truth (5 targets) | all rc=1 PARTIAL SUCCESS per engine law; uncaught census identical to CONT-22 (dooz 0, stopwatch 0, opencalc 4, telegram 9, forkgram 9) |
