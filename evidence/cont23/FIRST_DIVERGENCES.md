# CONT-23 — FIRST DIVERGENCES: the dooz (F6) content frontier, decoded end-to-end

Binary: `fa88902fdee6e982` (byte-exact CONT-22 lineage). APK: dooz_23_toplevel.apk
(sha256 prefix `299eab21ac8b3c61`, identity verified). All counts from fresh runs
under `run/cont23/` (mtrace = full method-entry trace; drawwin = draw-window trace;
ft_owner = field trace on `Lel0.r` = LayoutNode._owner; cl = `MINIANDROID_CL_TRACE`
caller-frame traces).

## 0. What no longer fails (negatives established first)

The registry's F-NEW-265 record described the W6-era chain "measure pass dies
mid-flight (`Lzs0.m` depth-17 unwind) → isPlaced never flips → draw gate skips all
content". At fa88902f every link of that chain has moved:

| W6/W7 state (binary aed46450) | fa88902f state (fresh runs) |
|---|---|
| `Lzs0.m` (MeasureAndLayoutDelegate.measureAndLayout) dies mid-flight | **executes ×9, zero exceptions** (no SYNTH-EXC, no uncaught in the whole run) |
| place-writers `Lbt0.q0/.r0` 0 executions; isPlaced never flips | `Lbt0.q0` ×2 executes; `Lel0.I` (isPlaced) returns TRUE ×32 in the draw window; the walk descends into child nodes |
| `Luc0.<init>` (GraphicsLayerOwnerLayer) 0; `Lyl.z` 0 | `Luc0.<init>` ×1; `Lyl.z` ×6 — the layer draw path arms |
| LifecycleRegistry never leaves CREATED | The outer-engine G09 start/resume transaction dispatches; androidx `ReportFragment$LifecycleCallbacks` executes 1488 ins (ON_START dispatch) + 1842 ins (ON_RESUME dispatch) |

## 1. The composed tree and its owner-field biography

Field trace `MINIANDROID_FIELD_TRACE="Lel0;.r"` (`Lel0.r` = LayoutNode._owner;
writer `Lel0.d` = attach, writer `Lel0.h` = detach — R8 identities verified against
upstream `LayoutNode.attach/detach`, ui 1.11.4):

```
put-obj Lel0.d Lel0.r obj#2004 value=obj#1437   (root attach; 1437 = AndroidComposeView)
put-obj Lel0.d Lel0.r obj#6145 value=obj#1437   … 6 attaches total
put-obj Lel0.h Lel0.r obj#6242 value=0          (owner = null → DETACH)
put-obj Lel0.h Lel0.r obj#6218 value=0
put-obj Lel0.h Lel0.r obj#6194 value=0
```

- 6 LayoutNodes are created and attached; then the LAST-attached subtree
  (6194→6218→6242, an ancestor chain, detached LIFO) is REMOVED.
- Final tree: root(2004) → 6145 → 6170 = the 3-node chrome. Dooz's real UI
  (GameScreen/board) never composes. Draw walk visits exactly these 3 nodes
  (`Lel0.I` recv 2004/6135/6160 = TRUE; ids shift between runs, shape identical);
  `Lgl0.c` (CanvasDrawScope.draw — the app draw-lambda runner) = **0** for the
  whole run; `Lm7` (TextLayout ctor) = 0 (no text ever measured); total
  `Canvas.draw*` bridges in the draw window: only translate/save/restore/concat —
  0 content ops → frame truth DEFAULT_BACKGROUND_ONLY, anchor unchanged.

## 2. The removal is a legitimate applier op — its upstream chain

Runtime call chain (`MINIANDROID_CL_TRACE="Lel0;,Lbt0;"`, top-4 caller frames):

```
Ls21.Y → Lg21.a → Lv02.j(0, 1) → Lel0.Q(6160, 0, 1)  [removeAt(index=0,count=1)]
  → Lel0.M(6160, 6184)  [onChildRemoved]
    → Lel0.h(6184) → Lel0.h(6208) → Lel0.h(6232)   [detach, recursion over subtree]
```

R8 ↔ upstream mapping (ui 1.11.4 sources, `upstream/s43/ui_android_src`):

| R8 | Upstream | Law source |
|---|---|---|
| `Ls21.Y` | UiApplier.remove(index,count) | `ui_android_src/.../node/UiApplier.android.kt` `override fun remove(index, count) { current.removeAt(index, count) }` |
| `Lel0.Q(I,I)` | LayoutNode.removeAt(index,count) | LayoutNode.kt:343 "Removes one or more children, starting at index" |
| `Lel0.M(Lel0;)` | LayoutNode.onChildRemoved(child) | calls `child.detach()` when owner != null, then `child._foldedParent = null` |
| `Lel0.h()` | LayoutNode.detach() | LayoutNode.kt:568 — `owner.rectManager.remove(this)` (the observed TreeSet.remove ×3), `this.owner = null` |
| `Lv02.j/c/d/f` | Change-list node ops (removeNode/upNode/insertNode) applied by ComposerImpl.applyChanges | runtime Composer.kt |
| `Lwo` | Recomposer; `Lj9.doFrame` = Choreographer frame callback driving `onEndApplyChanges` | caller frames `<Lwo.e> <Lwo.d> <Ldb1.i> <Lj9.doFrame>` |

So: **the composer itself removed the subtree in a change-list apply driven by the
first doFrame** — the engine executed the applier remove op faithfully. The
removal is upstream-legal behavior for "the content group recomposed to empty".

## 3. Why the content recomposes to empty — the app-side source law

The dooz APK's R8 names were decoded against the app's REAL source (cloned from
github.com/yamin8000/Dooz, the app is open source):

- `MainActivity.onCreate`: `@AndroidEntryPoint` (Hilt), `runBlocking { theme =
  settings.getTheme() }` (DataStore read — completes; the DataStore file-open
  ENOENT falls back to defaults per DataStore law), then `setContent { AppTheme
  { Column { NavHost(startDestination = Nav.Route.Game()) { composable(Game) {
  GameScreen(...) } } } } }`.
- `GameScreen` (`feature_game/ui/Game.kt`): `vm: GameViewModel = hiltViewModel()`;
  `val state = vm.state.collectAsStateWithLifecycle().value` — lifecycle-gated
  StateFlow collection.
- navigation-compose 2.9.8 `NavHost` (sources fetched from
  dl.google.com, navigation-compose/navigation-runtime 2.9.8 — the exact pinned
  family): the destination content is gated by

```kotlin
val currentBackStack by composeNavigator.backStack.collectAsState()
val allVisibleEntries by navController.visibleEntries.collectAsState()
val backStackEntry: NavBackStackEntry? = visibleEntries.lastOrNull()
if (backStackEntry != null) { /* AnimatedContent { GameScreen } */ }
```

`navController.graph = graph` and `navigate(startDestination)` run during
composition (synchronously); the destination content appears only when the
`visibleEntries` StateFlow value reaches the composition through
`collectAsState()`'s LaunchedEffect (produceState) — i.e. **on a subsequent
recomposition**. The observed removal pass = NavHost-internal recomposition
(its remembered effect wrappers replaced; the removed chain carried the
cancelled LaunchedEffects — the 3 `Lsx` " is cancelling" CancellationExceptions,
kotlinx JobSupport `toCancellationException` law, are the onForgotten teardown
of exactly those effects).

**The destination-arriving recomposition never happens.** That is the frontier.

## 4. The scheduler starvation (the actual first divergence for content)

Choreographer/frame-clock evidence at fa88902f (`run/cont23/dooz_after_long`,
120 s / 60 frames requested):

```
[CHOREO] postFrameCallback cb=1169 class=Lh9 (the AndroidUiDispatcher frame-clock callback, re-posted per await)
[CHOREO] doFrame tick t=1016666667ns → 1033333334ns → 1050000001ns   (3 ticks only)
[F100-STATE] quiescence at tick=3 pending_cb=0 queue_size=1
             DEFERRED-UI-PENDING (earliest ready_at=16ms — launch frame is provisional)
[CHOREO-PUMP] 3 frame(s) fired (bound=8)
```

- The launch-frame pump quiesces after 3 ticks; the last pending frame-clock
  callback (cb=1169) was REMOVED (the handler-path dispatch won — upstream
  AndroidUiDispatcher "whichever comes first" law) and never re-posted.
- After quiescence every per-frame pump re-enters with `pending_cb=0
  queue_size=0`; the deferred 16ms-due View.post entry eventually drains, but
  **the Recomposer runner never re-arms its `withFrameNanos` await** — no second
  applyChanges runs (`Lel0.r` puts stay at 6; no insert ops after the removal
  pass in the change list trace).
- kotlinx-side state at the stall: `[PARK-DRAIN] park depth=0 work_units=1`
  cycles (the AndroidUiDispatcher parks WITH work), runnables re-enqueued at a
  frozen `ready_at=300ms` virtual stamp.

Upstream laws for the next fix (all vendored/verified this wave):
- `AndroidUiDispatcher.android.kt` (runtime-android): one-MessageQueue law —
  dispatcher work is scheduled BOTH as a handler message and (for the frame
  clock) a Choreographer callback; the runner must be re-armed when either path
  delivers.
- `Recomposer.kt` `runRecomposeAndApplyChanges`: the runner loops
  `withFrameNanos { recompose; applyChanges }` — every frame tick must resume
  the awaiting runner.
- Engine: `pump_compose_frames` (runtime/execution_engine.cpp:6171) quiescence
  law + the F-115b frozen-launch-frame law (deliberate anchor determinism) —
  the fix must re-arm the runner WITHOUT breaking the frozen anchor goldens
  (18/18 byte-identical is the gate).

## 5. Falsification record (audit layer caught a false root)

This wave's first hypothesis ("the engine never dispatches onStart/onResume, so
the LifecycleRegistry never leaves CREATED — the dooz gate") was DISPROVEN by
its own falsification probe:

- A dedicated probe APK (`fixtures/lifecycle_transaction_probe`) registering an
  ActivityLifecycleCallbacks on the activity (the API 29+
  `ReportFragment$LifecycleCallbacks.registerIn` path) **PASSED 5/5 rows at the
  unmodified pre-fix binary** — the full AOSP start/resume transaction
  (`created,created-cb,preStarted,onStart,started,postStarted,preResumed,onResume,resumed,postResumed`)
  already fires from the OUTER engine (`execution_engine.cpp:1522-1561`,
  FIND-G09-LC-001 law).
- A trial patch that added the same transaction to the DEX engine's launch
  driver was shown to DOUBLE-dispatch the transaction (probe trace repeated)
  and was **reverted**; the working tree was restored to the byte-exact
  fa88902f lineage. The trial is recorded here and in the worklog — the
  registry receives NO root for the lifecycle gap (no genuine defect; the
  existing law holds).
- The probe is kept and committed as a **locked regression test** for the
  start/resume transaction law (it fails if the G09 pairing regresses).

## 6. Evidence file inventory (run/cont23/)

| File | Content |
|---|---|
| dooz_prefix_r1/r2, dooz_prefix re-anchor ×2 | pre-wave dooz truth (rc=1, 0 uncaught, anchor MATCH) |
| dooz_mtrace | full method-entry trace (72,936 METHOD-IN rows) — composition/measure/draw census |
| dooz_drawwin | draw-window trace — I()=TRUE ×32, walk over 3 nodes, 0 content ops |
| dooz_ft_owner, dooz_after_ft | `Lel0.r` owner-field biography (6 attaches, 3 detaches) |
| dooz_cl, dooz_cl2 | caller-frame traces — the applier remove chain |
| dooz_after_long | 120 s run — pump quiescence + starvation evidence |
| lctx_probe | the locked lifecycle-transaction probe run (5/5 PASS) |
| family/*.log, sweep_* | fresh family sweep logs + census |
| probes/ | rebuilt probe battery logs |
