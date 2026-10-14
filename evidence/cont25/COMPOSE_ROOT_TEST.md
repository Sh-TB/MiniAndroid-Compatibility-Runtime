# CONT-25 / PHASE 1 — COMPOSE ROOT TEST AGAINST THE WHITE-SCREEN CORPUS

Wave directive: test the real Compose execution root (the Composer /
slot-tracking / composition-progress root) against the white-screen corpus;
do NOT continue Skeleton-Light as a rendering solution (Issue #385 proved
verdict inflation + Surface/GL destruction hazards — Skeleton-Light stays
diagnostic-only).

**Root under test — VERDICT UP FRONT:** the "slot tracking" wording is NOT
proven. Source + runtime evidence re-roots the first divergence at the
SCHEDULER layer: **F-NEW-277 recomposition starvation at the frame-pump
quiescence boundary** (already registered CONT-23 — REUSED, not duplicated).
The Composer itself is healthy: composition #1 executes with real slot
operations (CONT-22 ledger: Lrn1 ×10366 ComposableLambda slot ops, Lom ×14),
slot tracking does not "fail" — **composition #2 never starts** because the
Recomposer runner's wake-up is starved.

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| git HEAD (start) | `05f6d1625ffcb1418163b8179d776ebee6b3aa42` == origin/main (fetched) |
| working tree | clean except `tmp/flappycow` submodule pointer (test artifact) |
| baseline binary | rebuilt from HEAD, BYTE-EXACT `fa88902fdee6e982e7f9696c339dda6e53af8fbb2c98de88651531d4ec428405` (CONT-22/23/24 lineage; preserved copy `run/cont24/bin/miniandroid_baseline_fa88902f`) |
| patch binary | `e980887e39aee977c4634ea9944fb80aaec3ba6c1e01556f146054cc89b651d2` |
| Issues read | #383 (BASE-FIRST plan + amendment comment), #384 (ARCH-001 matrix + CONT-21/22/23 wave reports), #385 (Skeleton-Light measurement — hazards: verdict inflation, Surface/GL destruction, fidelity loss, tree-absent no-op, log masking) |
| root registry | 586 rows; F-NEW-277 CLASSIFIED P0 (recomposition starvation); F-NEW-266/271 ROOT-CAUSED-FIXED; status_counts intact |
| dooz first divergence (CONT-23 decode, re-verified live this wave) | launch-frame pump quiesces at tick 3; second applyChanges never runs; 3 LayoutNodes of NavHost chrome, 0 app draw ops |
| compose first divergence (fresh, this wave) | see §2 — itsfrz and droidify block BEFORE the Composer at earlier generic roots |

Verification commands: `git fetch origin && git rev-parse HEAD origin/main`,
`timeout 570 make -j1 BUILD_DIR=build` (miniandroid/), `sha256sum build/miniandroid`.

---

## 1. COMPOSE CORPUS + PREFLIGHT (directive §5 — no three variants of one APK)

| target | APK | version | SHA-256 (prefix) | source | Compose evidence | preflight |
|---|---|---|---|---|---|---|
| dooz (primary) | `upload/canonical_apks/io.github.yamin8000.dooz_23.apk` | 1.0.23 | `299eab21ac8b3c61` | F-Droid (pinned family) | compose 1.11.4 family in-APK (CONT-12 matrix) | OK — reaches Composer |
| itsfrz tictactoe (control B) | `tmp/cont25_apks/itsfrz_5.apk` | 1.0.5 (vc5) | `2a057a9a519acd81` | F-Droid re-download, sha == registry `miniandroid/APK_REGISTRY.json` | 133 `androidx/compose` strings in classes.dex | OK — universal (x86+ARM), no native blocker |
| droidify (control C) | `tmp/cont25_apks/droidify_770.apk` | 0.7.7 (vc770) | `da3070f3f18bdbed` | F-Droid `repo/com.looker.droidify_770.apk` | 2030 `androidx/compose` strings | OK — universal ABIs incl. x86_64 |
| rttt (REJECTED) | `tmp/cont25_apks/rttt_3.apk` | 1.3 (vc3) | `704fa51869ad7ff4` | F-Droid re-download | 0 compose strings; main activity `org.libsdl.app.SDLActivity`; `lib/arm64-v8a/libSDL3.so` only | **environment blocker: ARM-only native SDL** — excluded per campaign rules |
| PF Dicer (REJECTED) | `tmp/cont25_apks/dicer_101.apk` | 2.0.0 (vc101) | `f2b4d3f021c3a620` | F-Droid re-download | 0 compose strings (view-based Secuso splash) | not a Compose target |
| Antimine (REJECTED) | `tmp/cont25_apks/antimine.apk` | 17.6.3 F | `e7b635b6629bc5b0` | F-Droid re-download | 0 compose strings in dex; libGDX game | not a Compose target |

All three selected targets: white/near-blank at baseline, Compose detected,
activity launched, 0 real draw ops — exactly the directive's selection profile.

---

## 2. BASELINES BEFORE FIX (directive §6)

Protocol: `miniandroid/build/miniandroid run --package <pkg> --data-root <store>
--width 1080 --height 1920 --frames 5 --max-seconds 15 -o <dir>` (canonical
sweep protocol; installs at `run/cont25/store_*`).

### dooz (io.github.yamin8000.dooz)

```text
launch:            OK (rc=1 PARTIAL SUCCESS per engine law)
activity:          MainActivity (Hilt @AndroidEntryPoint)
compose entry:     YES (setContent -> composition #1 runs)
composer:          YES (slot ops execute — Lrn1 x10366)
slot tracking:     NO FAILURE OBSERVED (composition #1 legal end-to-end)
layout node:       6 created / 6 attached / 3 detached (chrome only)
measure:           Lzs0.m x9, ZERO exceptions
layout:            place-writer Lbt0.q0 x2; isPlaced TRUE x32 in draw window
dispatchDraw:      runs per frame; walk honors isPlaced
real draw:         0 app draw ops; Lgl0.c (CanvasDrawScope.draw) = 0
verdict:           DEFAULT_BACKGROUND_ONLY (first_missing_stage=APP_DRAW_OPS)
pixels:            colors=1 (#fafafa), nondom=0
screenshot SHA:    d602648e8e401895 (== frozen anchor, x3)
first divergence:  F-NEW-277 — pump quiescence at tick 3 starves recomposition #2
uncaught:          0
```

### itsfrz tictactoe (com.itsfrz.tictactoe)

```text
launch:            OK (rc=1)
activity:          MainActivity
compose entry:     NEVER REACHED — dies in onCreate
composer:          no
slot tracking:     n/a
layout node:       FragmentContainerView node only (framework)
measure/layout:    framework defaults
dispatchDraw:      0 ops
real draw:         0
verdict:           DEFAULT_BACKGROUND_ONLY (first_missing_stage=APP_PIXELS)
pixels:            colors=1 (#202230 dark theme bg), nondom=0
screenshot SHA:    d55056a8928a26ff x3
first divergence:  NOT the Compose root — NPE "Parameter specified as non-null
                   is null: method androidx.fragment.app.FragmentContainerView.
                   <init>, parameter fm" (caller Lo4/k;.e) unwinds to
                   MainActivity.onCreate [APP-BOUNDARY]; 3 uncaught faces
                   (crash.log). Fragment host wiring family — attach to
                   R-NEW-331/F-NEW-168 lineage per root accounting.
uncaught:          3 (o4/e clinit, q/a, /q.S per-frame repeats)
```

### droidify (com.looker.droidify)

```text
launch:            OK (rc=1)
activity:          MainActivity
compose entry:     NEVER REACHED — dies in onCreate
composer:          no
slot tracking:     n/a
layout node:       none (framework bg only)
real draw:         0
verdict:           DEFAULT_BACKGROUND_ONLY (first_missing_stage=APP_DRAW_OPS)
pixels:            colors=1 (#303030), nondom=0
screenshot SHA:    b5a7a35d5fe0564b x3 (note: byte-identical to the tictactoe
                   blank — blank-frame SHAs are not discriminative across
                   targets; semantic traces used instead)
first divergence:  NOT the Compose root — [HALT-LOOP] 50001 visits at
                   PC=0x5a in kotlinx.coroutines.DelayKt.runBlocking
                   (BlockingCoroutine.joinBlocking park loop; F084 interpreter
                   halt synthesizes VirtualMachineError -> APP-BOUNDARY
                   unwind, 4 uncaught faces incl. protobuf Lite init).
                   R-NEW-345 residual arm (the park-drain law drains
                   queued work but the joinBlocking coroutine never
                   completes).
uncaught:          4
```

### Diagnostic split (directive §13) — do NOT collapse

| stage | dooz | itsfrz | droidify |
|---|---|---|---|
| A Composer failure (slot/Composer) | **NO — composer healthy** | blocked earlier | blocked earlier |
| B composition succeeds, LayoutNode/update fails | NO — composition #1 OK; **recomposition #2 never runs (scheduler)** | n/a | n/a |
| C layout succeeds, draw fails | NO — layout machinery healthy (measure x9, place x2) | n/a | n/a |
| D draw succeeds, presentation fails | n/a (draw never had content) | n/a | n/a |
| E capture = framework chrome only | **YES — this is the observed face** | YES | YES |

---

## 3. SOURCE-FIRST INVESTIGATION (directive §4) — THE SEMANTIC LAW MAP

### 3.1 Upstream laws read (authoritative sources)

| source | law |
|---|---|
| `upstream/s43/runtime/commonMain/androidx/compose/runtime/Recomposer.kt` (1.11.4) | runner loop `while(shouldKeepRecomposing) { awaitWorkAvailable(); if(!recordComposerModifications()) continue; parentFrameClock.withFrameNanos { sendFrame; recompose; applyChanges } }`; `hasSchedulingWork` = snapshotInvalidations OR compositionInvalidations OR **hasBroadcastFrameClockAwaiters** OR hasNextFrameEndAwaiters (L1010–1019); `onNewFrameAwaiter()` (L396) resumes the parked `workContinuation` when `deriveStateLocked()` yields PendingWork — **a frame awaiter is itself work-available** |
| `upstream/s43/ui_android_src/.../AndroidUiDispatcher.android.kt` | ONE-queue law: `dispatch()` enqueues trampoline + schedules dispatchCallback BOTH as handler message and Choreographer frame ("whichever comes first"); handler-path `run()` removes the frame callback **only if `toRunOnFrame.isEmpty()`** |
| `upstream/s43/ui_android_src/.../GlobalSnapshotManager.android.kt` | `setContent -> ensureStarted()`: every global snapshot write -> conflated channel -> `Snapshot.sendApplyNotifications()` on AndroidUiDispatcher.Main -> Recomposer apply-observer -> invalidation -> runner wake |
| `upstream/nav_s36/NavHost.kt` (navigation-compose 2.9.8 family) | `navController.graph = graph` during composition; `allVisibleEntries by navController.visibleEntries.collectAsState()` (L850); `backStackEntry = visibleEntries.lastOrNull()` (L861); content gated `if (backStackEntry != null)` |
| AOSP MessageQueue.next | the main Looper NEVER exits while messages are pending: future-dated head -> `nativePollOnce(head.when - now)` -> dispatch when due |

### 3.2 MiniAndroid mismatch (the corrected root, per directive §3)

```text
SOURCE LAW:           AOSP MessageQueue.next() + Recomposer.awaitWorkAvailable:
                      dispatcher resumptions ride future-due main-queue work;
                      quiescence is an EMPTY queue, not a future-dated head.
ALGORITHM IN
MINIANDROID:          pump_compose_frames (execution_engine.cpp:6184) breaks
                      on `!did_work` — "nothing due NOW" = quiescence; the
                      virtual clock never advances; future-due dispatcher
                      work is stranded. The engine's OWN drain_quiescent
                      (M3 FINDING-009, execution_engine.cpp:7804) already
                      states the correct law — the compose pump predates it
                      (internal parity contradiction).
OBSERVED DIVERGENCE:  dooz fires 3 frames; the last re-posted Lj9 frame
                      callback (cb=7308->8168->8331) never re-posts at tick 3;
                      the runner suspends on workContinuation (no
                      invalidations, no awaiters); the 16ms View.post strand
                      sits future-due (later REMOVED, never run); the 300ms
                      worker chain only runs inside late park-drain cycles;
                      [CHOREO] shows no postFrameCallback after tick 3.
WHY IT IS GENERIC:    any Compose app whose launch-frame work completes
                      before its dispatcher resumptions become due starves
                      identically. Layer: runtime/frame-clock +
                      compose/recomposer-scheduling. NOT slot tracking; NOT
                      Composer; NOT measure/layout (all proven healthy).
MINIMAL FIX:          poll-timeout parity in pump_compose_frames, scoped to
                      the compose frame family (see §4).
```

Runtime trace evidence: `run/cont25/probe_pump/run.log` (MINIANDROID_METHOD_TRACE=1,
fresh dooz run: [CHOREO] lifecycle 1169/7308/8168/8331, [F100-PUMP] drain
rounds, tick-3 tail method sequence ending `Lad;.addLast` (task enqueued,
nobody dispatched), quiescence census); CONT-23 traces re-used for the
composition/applier decode (run/cont23/dooz_mtrace 72,936 rows).

---

## 4. THE FIX (directive §7 — smallest generic, no forbidden patterns)

`miniandroid/src/runtime/execution_engine.cpp` — `pump_compose_frames`
quiescence arm (+34 lines, one law):

```text
F-NEW-277 POLL-TIMEOUT PARITY (with drain_quiescent / M3 FINDING-009):
at the pump's `!did_work` boundary, if THIS pump call served at least one
Choreographer frame (fired_frames > 0 — the compose frame family is active)
AND the handler queue holds future-due entries, advance the virtual clock to
the next ready time (advance_virtual(next_ready - now)) and keep ticking.
Apps that never post a frame callback keep the F-115b frozen launch-frame
law byte-exactly.
```

Forbidden-pattern audit:

```text
if package == ... / if app == ... / if Dooz ...   : NONE (grep audit)
screenshot manipulation / forced draw             : NONE
exception suppression / fake LayoutNode           : NONE
artificial PC advancement                          : NONE
app-specific constants                             : NONE (next_ready_ms is
                                                     queue state, not data)
```

Scope-guard rationale: `fired_frames > 0` is the S135 COMPOSE renderer-family
signal the pump already arms on (`set_renderer_family(COMPOSE)` at pump
entry) — family routing, not app routing. The skeleton-light lesson
(Issue #385 §4: a global paint hook destroyed the Surface/GL family) is
respected: the Surface/GL, Canvas and View families keep byte-identical
behavior (proven §6).

---

## 5. AFTER THE FIX — CAUSAL CHAIN AUDIT (directive §8, §14)

Patch binary `e980887e39aee977` reruns (`run/cont25/fix_*`):

| target | screenshot | verdict | change |
|---|---|---|---|
| dooz | `d602648e8e401895` | DEFAULT_BACKGROUND_ONLY | [F277-POLL] fast-forward FIRES once (advance to 16ms); the 16ms strand now RUNS (was: stranded, later removed-never-run); pump quiesces at tick 5 with an EMPTY queue; **no new frame callbacks post — recomposition #2 still never runs** |
| itsfrz | `d55056a8928a26ff` | unchanged | fix inert (fired_frames=0 — never reaches composition) — scope-guard PROOF |
| droidify | `b5a7a35d5fe0564b` | unchanged | fix inert (fired_frames=0) — scope-guard PROOF |

Causal chain status (directive §8):

```text
BASE 0 real draw
  -> FIRST DIVERGENCE (pump quiescence strands future-due work)   [PROVEN]
  -> GENERIC FIX (poll-timeout parity)                            [LANDED]
  -> COMPOSER PROGRESSES                                          [NO — runner
      still never wakes: the wake-up work is NOT in the handler
      queue at quiescence; only 13 trampoline tasks dispatch in
      the whole 15s run (5x Lh9 dispatcher rounds, 4x Lzh
      continuation tasks, 4 one-shot tasks) — the produceState/
      LaunchedEffect collect coroutine's dispatch and the
      GlobalSnapshotManager channel monitor resumptions never
      materialize as queue work]
  -> COMPOSITION/APPLY CHANGES #2                                 [NO]
  -> REAL LAYOUTNODE CONTENT                                      [NO]
  -> MEASURE/LAYOUT/REAL DRAW/MEANINGFUL PIXELS                   [NO]
```

**Comparison against Issue #385 (directive §14):**

| approach | pixels | class |
|---|---|---|
| BASE | blank (1 color) | DEFAULT_BACKGROUND_ONLY |
| SKELETON-LIGHT (issue #385) | diagnostic structure only | SKELETON_STRUCTURE_ONLY — NOT real app content |
| REAL ROOT FIX (this wave, arm 1) | still blank | **NO Compose draw yet** — the divergence moved one link deeper (invalidation delivery), see §7 |

Per the directive: the answer is honestly **NO** — the first arm of the
F-277 fix does not produce app-owned pixels; the next first divergence is
reported instead of claiming success.

---

## 6. REGRESSION GATE (patch binary e980887e39aee977)

| gate | result |
|---|---|
| Anchor suite x3 (6 frozen anchors: dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tictactoedeluxe af6094295ecb50e3) | **18/18 MATCH** (run/cont21/anchor_* at patch binary — script re-run) |
| Probe battery | fcol 440 PASS / 0 FAIL (20/20 rows), f259 7/7 (154 PASS / 0 FAIL), f259g 264 PASS / 22 FAIL = the SAME single known-honest F259-L row ("throwing slot propagated=false") repeated across runs — matches the recorded 12/13 drift, f266 6/6 (132/0), f268 276 PASS / 0 FAIL |
| g2048 anchor | `59ca1526611c4622` rc=0 MATCH |
| Surface/GL negative control — flappycow | rc=0, `13cf47464d9787f4`, 507 colors / 118,251 nondom — **byte-identical to baseline binary** (`fa88902f` re-run: rc=0, same sha). The skeleton-light Surface/GL destruction hazard did NOT recur |
| Canvas/game negative control — tictactoe (emmanuelmess) | rc=1, `b5a7a35d5fe0564b` — byte-identical to baseline binary re-run (pre-existing blank face, NOT a regression; its frontier is the libGDX surface family, unchanged) |
| View negative control — opencalc, gmdice | anchors byte-identical x3 (in the 18/18) |
| rc-truth | captured immediately after each engine call (CONT-22 audit law) |

---

## 7. NEXT FIRST DIVERGENCE (directive §14 — what replaces the removed one)

The pump-side starvation is fixed (law-correct, regression-free) but
composition #2 still never runs. The wake-up work the runner needs is **not
in the handler queue** — only 13 trampoline tasks dispatch in the whole 15 s
run. The stranded link is the **invalidation-delivery chain**:

```text
visibleEntries StateFlow emission (navigate during composition #1)
  -> produceState/LaunchedEffect collect coroutine          [dispatch never
     (kotlinx StateFlowImpl.collect first-emit-on-subscribe)  materializes as
                                                              a trampoline task]
  -> collector writes `value = it` (global snapshot write)
  -> GlobalSnapshotManager channel monitor -> sendApplyNotifications
  -> Recomposer apply-observer -> snapshotInvalidations
  -> workContinuation.resume -> runner wakes -> withFrameNanos #4
  -> recomposition #2 -> GameScreen composes                 [never reached]
```

Candidate layers for the next wave (ranked, with the correct instrument):

1. **Effect-coroutine dispatch never enqueued** — the LaunchedEffect/produceState
   coroutine's start rides the composition's effectCoroutineContext; if its
   first dispatch was consumed by an already-quiesced drain, the coroutine
   never starts. Instrument: un-renamed real-Compose oracle (CONT-12 dexes
   survive at `tmp/cont12_oracle_build/dex/`; needs the aapt2 link re-run —
   `scripts/cont12_oracle_res2.sh` artifacts partially survive) to trace
   `GlobalSnapshotManager.ensureStarted`, `LaunchedEffectImpl.onRemembered`,
   `StateFlowImpl.collect` by REAL name.
2. **StateFlow first-emit-on-subscribe lost** — kotlinx 1.9 BufferedChannel/
   updateState machinery mis-suspending inside the engine's continuation
   model.
3. **Channel monitor (ensureStarted) never started or never resumed** —
   `Channel<Unit>(1).trySend/consumeEach` semantics.

The oracle rebuild is the next wave's opening probe (name-level tracing);
dooz-only guessing is forbidden by the same discipline that falsified the
CONT-23 lifecycle hypothesis.

---

## 8. FINAL MATRIX (directive §17)

| Target | Family | Base First Divergence | Patch First Divergence | Real Draw | Meaningful Pixels | 3-run | Result |
|---|---|---|---|---|---|---|---|
| dooz 1.0.23 | Compose | F-277 pump quiescence strands future-due work (16ms strand removed-never-run) | 16ms strand RUNS ([F277-POLL]); next divergence = invalidation delivery (no collector dispatch) | NO | NO | d602648e x3 deterministic | PARTIAL — divergence moved one link deeper |
| itsfrz 1.0.5 | Compose | FragmentContainerView fm=null NPE (pre-Composer) | unchanged (fix inert) | NO | NO | d55056a8 x3 | BLOCKED (pre-Compose root; fragment host family R-NEW-331) |
| droidify 0.7.7 | Compose | DelayKt.runBlocking HALT-LOOP (pre-Composer) | unchanged (fix inert) | NO | NO | b5a7a35d x3 | BLOCKED (pre-Compose root; R-NEW-345 residual arm) |
| opencalc 3.2.0 | View (control) | — | — | YES (VISUALLY_VERIFIED) | YES | a976d2f9 x3 | regression PASS |
| gmdice 8 | View game (control) | — | — | YES | YES | f3b483fe x3 | regression PASS |
| flappycow | Surface/GL (control) | — | — | YES (507 colors) | YES | 13cf4746 == baseline | regression PASS |
| tictactoe (emmanuelmess) | Canvas/libGDX (control) | libGDX surface family (pre-existing) | unchanged | NO (pre-existing blank) | NO | b5a7a35d == baseline | regression PASS (no change) |
| g2048 | Canvas (control) | — | — | YES (FULLY_VERIFIED) | YES | 59ca1526 | regression PASS |

---

## 9. STATUS LEDGER (directive §16 vocabulary)

| item | status |
|---|---|
| HEAD/binary/APK truth lock | TESTED |
| Issues #383/#384/#385 read | OBSERVED |
| Compose corpus preflight (3 selected, 3 rejected with reasons) | OBSERVED |
| Baselines captured (3 targets, full evidence block) | TESTED |
| Root wording verification (slot-tracking -> corrected to F-277 scheduler) | OBSERVED |
| Upstream source read (Recomposer/AndroidUiDispatcher/GlobalSnapshotManager/NavHost/MessageQueue) | OBSERVED |
| MiniAndroid mismatch identified | OBSERVED |
| Root duplicate check (F-277 REUSED; no new root) | OBSERVED |
| Minimal generic fix implemented (poll-timeout parity) | IMPLEMENTED |
| Fix runtime effect ([F277-POLL] fires; 16ms strand runs) | TESTED |
| Fix produces Compose draw | **NOT YET — next divergence = invalidation delivery** |
| Skeleton pixels excluded from proof | OBSERVED (skeleton-light untouched, default OFF) |
| Framework chrome excluded | OBSERVED (verdict law: DEFAULT_BACKGROUND_ONLY; 1-color frames) |
| Meaningful pixels | **NOT ACHIEVED** |
| Screenshot SHAs recorded | TESTED |
| 3-run proof | TESTED (dooz d602648e x3, itsfrz d55056a8 x3, droidify b5a7a35d x3) |
| View negative control | PASS |
| Canvas/game negative control | PASS |
| Surface/GL negative control | PASS |
| No package-specific logic / no exception suppression / no fake object / no forced PC | OBSERVED (grep audit on the diff) |
| Root registry updated (F-277 evidence extended; R-NEW-331 + R-NEW-345 evidence extended) | IMPLEMENTED |
| Evidence artifact committed | this file |
| HEAD verified after commit | see commit log |

---

## 10. HONEST LIMITATIONS

1. The wave's fix does NOT produce Compose draw — the causal chain breaks at
   the invalidation-delivery link (§5, §7). Nothing in this wave claims
   "fixed".
2. itsfrz and droidify cannot exercise the Compose root at all (pre-Composer
   blockers) — the F-277 fix is therefore proven only on ONE Compose target
   (dooz) as a divergence-mover, and on ZERO targets as a visual mover.
   Per directive §9 this keeps the root at **PARTIAL / NOT GENERICALLY
   PROVEN** (it was already CLASSIFIED; no inflation this wave either way).
3. The 13-trampoline-task census (§5) is evidence the delivery chain never
   dispatches, but the exact L1/L2/L3 split needs the un-renamed oracle —
   recorded as the next wave's opening probe, not claimed as solved.
4. The tictactoe control is at a pre-existing blank (libGDX surface family);
   it serves as a no-regression control only, not a progress proof.
5. Blank-frame screenshot SHAs are not discriminative across targets
   (droidify == tictactoe blank); semantic trace markers were used for
   target identity.
