# CONT-23 — Cross-Family Graphical Progress: the measure/layout frontier decoded to the scheduler root

Wave: CONT-23 (Issue #384 continuation). Starting lineage verified and preserved:
HEAD `62809396`, binary **`fa88902fdee6e982`** reproduced byte-exactly.
Ending lineage: **the same byte-exact binary** — no engine source change shipped.
Registry: 585 → **586** rows (F-NEW-277 CLASSIFIED P0; F-NEW-265 `verified_current`
extended). Queue status honestly unchanged: no fix landed this wave; a fix
hypothesis was raised and falsified by its own probe (§2), and the real frontier
was decoded to a precise, evidence-backed root (§3-§5).

---

## 1. CONT-22 audit

Full file: `evidence/cont23/CONT22_AUDIT.md`. 10 claims audited at the byte-verified
binary: 9 TESTED (F-274/F-275 markers firing live; dooz 0 uncaught; anchors 18/18
×3; opencalc census; probe battery; sweep-harness exit-code fix; registry rows),
1 SUPERSEDED — the "dooz blocked at F-265 measure-pass" frontier description is
outdated: the W6 measure-pass death face is gone at fa88902f (`Lzs0.m` ×9, zero
exceptions; place-writers execute; the draw walk descends into placed children).

## 2. The falsified fix (audit layer at work — kept on the record)

Phase 1's first hypothesis, from a legitimate runtime observation (the dooz
prefix logs appeared to show no start/resume lifecycle dispatch), was: "the
engine never dispatches the AOSP start/resume transaction, so the
LifecycleRegistry never leaves CREATED, and lifecycle-gated content
(collectAsStateWithLifecycle, NavHost visibleEntries) stays suspended — a
generic Lifecycle-law root."

- **Implementation attempt**: a `run_activity_start_resume_transaction` helper
  in the DEX engine's launch driver + a dedicated probe APK
  (`fixtures/lifecycle_transaction_probe`) asserting the full AOSP API-29
  pre/post pairing (PreStarted → onStart → Started → PostStarted →
  PreResumed → onResume → Resumed → PostResumed).
- **Falsification**: the probe **PASSED 5/5 at the UNMODIFIED pre-fix binary**
  — the transaction already fires from the OUTER engine
  (`execution_engine.cpp`, FIND-G09-LC-001 law, comments there even cite the
  Compose RESUMED gate). My re-read of the prefix dooz log had miscounted the
  `[F058-DISPATCH]` rows (12 rows = 6 events × 2 observers, including
  PostStarted ins=2427 and PostResumed ins=1842 — the androidx dispatch runs).
- **Disposition**: the trial patch double-dispatched the transaction (probe
  trace ran the sequence twice) and was **reverted**; the tree was restored to
  byte-exact `fa88902fdee6e982`. **No registry root was created for the
  lifecycle gap** (no genuine defect). The probe is committed as a locked
  regression test for the existing law.

## 3. What actually blocks dooz pixels (the wave's real finding)

Full chain with runtime + source evidence: `evidence/cont23/FIRST_DIVERGENCES.md`.

1. Composition attaches 6 LayoutNodes (owner-field biography via
   `MINIANDROID_FIELD_TRACE=Lel0.r`).
2. The first doFrame drives ONE applyChanges whose change list REMOVES the
   NavHost-internal content subtree — runtime caller chain captured:
   `Ls21.Y (UiApplier.remove) → Lg21.a → Lv02.j(0,1) → Lel0.Q removeAt(0,1) →
   Lel0.M onChildRemoved → Lel0.h detach` — faithful to upstream ui-1.11.4 law.
3. The removed chain carried the NavHost's first-pass effects (the 3
   `"sx is cancelling"` CancellationExceptions = kotlinx JobSupport teardown).
4. dooz's destination content (GameScreen) is gated by navigation-compose
   2.9.8 NavHost: `backStackEntry = visibleEntries.lastOrNull()`; the entry
   list reaches the composition only via `collectAsState()`'s LaunchedEffect —
   i.e. a SECOND applyChanges on a later frame.
5. The second applyChanges never runs: the launch-frame pump quiesces at tick 3
   (`[CHOREO-PUMP] 3 frame(s) fired (bound=8)`, last frame-clock callback
   REMOVED per the upstream AndroidUiDispatcher "whichever comes first" law),
   `[PARK-DRAIN] park depth=0 work_units=1` cycles at a frozen virtual stamp,
   and the Recomposer runner never re-arms its `withFrameNanos` await.
   Even a 120 s / 60-frame run shows exactly 3 ticks.
6. Result: the drawn tree stays at the 3-node chrome; `Lgl0.c`
   (CanvasDrawScope.draw) = 0; frame truth DEFAULT_BACKGROUND_ONLY; anchor
   `d602648e8e401895` unchanged ×5.

**Root registered: F-NEW-277 (CLASSIFIED, P0) — Recomposition starvation at the
frame-pump quiescence boundary** (layer: runtime/frame-clock +
compose/recomposer-scheduling). The fix surface (recorded in the registry):
re-arm the parked AndroidUiDispatcher continuations at the quiescence boundary
without breaking the F-115b frozen-launch-frame law; the 18/18 anchor suite is
the hard gate.

## 4. Tests

- `fixtures/lifecycle_transaction_probe` (+ `scripts/cont23_build_probe.sh`):
  the new locked regression test for the start/resume transaction law — 5/5
  PASS at fa88902f (`run/cont23/lctx_probe`); it FAILS if the G09 pairing
  regresses (the exact failure mode that would silently starve future
  lifecycle-aware targets).
- Probe battery re-run at the canonical toolchain: fcol 20/20, f259 7/7,
  f259g 12/13 (same known-honest F259-L row), f266 6/6, f268 — identical to
  the recorded green state.
- Anchors ×3: 18/18 MATCH.

## 5. Runtime before/after (same params, same binary)

Honest table (see `evidence/cont23/GRAPHICAL_PROGRESS.md`): every dooz metric
delta is 0 — composition extents, measure counts, placement counts, draw ops,
pixels, screenshot sha, exit status. The wave's movement is in the FRONTIER:
F-265's measure-pass death face resolved as a live fact, the content-loss
mechanism decoded to the applier remove + NavHost gate, and the starvation
root pinned with pump-level evidence.

## 6. Cross-family confirmation and libGDX

- The F-277 root is F6-family (Compose) with an explicit cross-family fanout
  prediction: any app whose content arrives via flow-collect + recomposition
  after the launch frame (navigation/collectAsState families). No fix landed,
  so no cross-family improvement is claimable this wave; the fanout is
  testable the moment the starvation fix lands.
- libGDX (P10 family: tictactoe/bouncy) was NOT touched: the Compose frontier
  consumed the investigation budget, and per the mission's honesty clause no
  speculative second fix was attempted. The P10 evidence of record stands
  (bouncy: GL20Renderer/EGL native init; tictactoe:
  preserveEGLContextOnPause/onResume faces).

## 7. Regression

Zero engine source changes shipped → zero regression risk by construction, and
the full gate was run anyway (anchors 18/18 ×3, probe battery, family sweep
with rc-truth: all 5 targets rc=1 PARTIAL SUCCESS per the engine's own law,
uncaught census identical to CONT-22: dooz 0, stopwatch 0, opencalc 4,
telegram 9, forkgram 9 family-internal).

## 8. Remaining blockers

1. **F-NEW-277 (P0)** — the recomposition-starvation root; the next wave's
   fix target with the highest expected cross-family yield.
2. Telegram-engine UI-init faces (F4, family-internal, 9 each).
3. libGDX surface/input + native ABI family (P10, 2 targets).
4. opencalc layout-engine nulls (ConstraintLayout.onLayout ×3, single-target).
5. F-NEW-276 data-path duplication (P2; visible this wave as the dooz
   DataStore path duplication — app-survivable, logged).

## 9. Next highest-value root

**F-NEW-277.** Evidence ranking: (a) it is the direct, pinned blocker of the
F6 family's first REAL_APP_CONTENT target; (b) the fix surface is small and
bounded (the quiescence/re-arm boundary in `pump_compose_frames` + the
dispatcher's parked-work law), with a hard regression gate (frozen anchor
goldens) and a ready-made cross-family test surface (any navigation/flow-collect
Compose app); (c) everything downstream of it is already proven healthy at the
current binary (lifecycle RESUMED, measure pass, placement, draw walk, canvas
bridge) — the content exists one re-armed frame away.

## 10. Final answers

> **1. What was the exact first semantic divergence at the Dooz measure/layout frontier?**
> There is no longer one inside measure/layout: `Lzs0.m` (MeasureAndLayoutDelegate.measureAndLayout)
> runs ×9 with zero exceptions at fa88902f, place-writers execute, and the draw
> walk honors isPlaced=TRUE for the 3-node chrome. The first semantically
> decisive operation moved earlier in the pipeline: the first-frame applyChanges
> executes UiApplier.remove(0,1) on the NavHost content subtree (verified against
> the app's own recomposition semantics), and the recomposition that would
> re-insert the destination never runs.

> **2. Which upstream source law establishes the expected behavior?**
> ui-1.11.4 LayoutNode.kt removeAt/detach + UiApplier.android.kt remove (the
> removal path is upstream-legal); navigation-compose/runtime 2.9.8 NavHost.kt
> (`visibleEntries.lastOrNull()` gate + `collectAsState()` produceState law);
> runtime Recomposer.kt runRecomposeAndApplyChanges (per-frame await loop);
> AndroidUiDispatcher.android.kt one-MessageQueue dispatch law; AOSP
> MessageQueue nativePollOnce wake law.

> **3. What generic runtime code changed, and why is the fix not application-specific?**
> None shipped. The one candidate patch was falsified by its own probe (the
> law it implemented already exists in the outer engine) and reverted to the
> byte-exact prior binary; the registry received no root for it. The new
> F-NEW-277 entry records the fix surface for the next wave.

> **4. Did Dooz progress from measure/layout into placement, drawing, and meaningful app-owned pixels?**
> Placement: yes (2 place-writer executions; 3 nodes isPlaced=TRUE — the
> measure/place lifecycle is complete for the chrome tree). Drawing: no
> app-owned ops (CanvasDrawScope.draw = 0 — the chrome has no draw modifiers;
> the content that carries them is the removed subtree). Pixels: none (frame
> truth DEFAULT_BACKGROUND_ONLY, anchor unchanged).

> **5. Which independent target confirms the same fix?**
> Not yet claimable — no fix landed. The registered fanout prediction: any
> Compose target using navigation or flow-collect-driven content (the F6
> family surface); the wave's new lifecycle probe additionally locks the
> start/resume law such platforms stand on.

> **6. Did libGDX reach a real frame and demonstrate an input-driven state change, or what exact prerequisite/semantic root blocks it?**
> Unchanged from the record: bouncy/tictactoe block at GL/EGL native
> initialization (GL20Renderer init / preserveEGLContextOnPause faces) — the
> native-load prerequisite, before any frame submission or input dispatch. Not
> attacked this wave (no speculative fix; Compose frontier consumed the budget).

> **7. Which shared runtime root should be addressed next, and what evidence ranks it above the alternatives?**
> F-NEW-277 (recomposition starvation at the frame-pump quiescence boundary).
> Ranked by: direct causal pin to the F6 pixel frontier (pump-level trace
> evidence, 3-tick stall reproduced at 120 s); small bounded fix surface
> (quiescence/re-arm boundary) with the frozen-anchor suite as the regression
> gate; every downstream stage already proven healthy; explicit cross-family
> fanout to all flow-collect/navigation Compose apps.
