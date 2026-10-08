#!/usr/bin/env python3
"""CONT-23 registry update:
- F-NEW-265: extend verified_current — the W6 measure-pass death face is GONE at
  fa88902f; the frontier re-rooted to the composition/scheduler layer (pointer).
- F-NEW-277 (NEW, CLASSIFIED P0): RECOMPOSITION STARVATION at the frame-pump
  quiescence boundary — the destination-arriving applyChanges never runs.
No status inflation: no engine fix landed this wave (falsified trial reverted).
"""
import json

REG = '/home/z/my-project/root_registry.json'
with open(REG) as f:
    reg = json.load(f)

roots = reg['roots']
assert isinstance(roots, list), 'unexpected registry shape'

f265 = next(r for r in roots if r.get('id') == 'F-NEW-265')
addon = (" CONT-23 pointer 2026-10-08: the measure-pass DEATH FACE IS GONE at "
         "fa88902fdee6e982 — Lzs0.m (MeasureAndLayoutDelegate.measureAndLayout) "
         "executes x9 with ZERO exceptions (no SYNTH-EXC, no uncaught, "
         "run/cont23/dooz_mtrace); place-writer Lbt0.q0 executes x2; Lel0.I "
         "(isPlaced) TRUE x32 in the draw window and the walk descends into "
         "child nodes. The content frontier re-rooted to the composition/"
         "scheduler layer: 6 LayoutNodes attach, the first-frame applyChanges "
         "REMOVES the NavHost content subtree (UiApplier.remove -> "
         "removeAt(0,1) -> detach, runtime caller chain captured via "
         "MINIANDROID_CL_TRACE), the destination-arriving recomposition never "
         "runs because the frame-pump quiesces at tick 3 and the Recomposer "
         "runner never re-arms -> registered F-NEW-277. Lgl0.c "
         "(CanvasDrawScope.draw) still 0; anchor d602648e8e401895 unchanged.")
vc = f265.get('verified_current') or ''
if 'CONT-23 pointer' not in vc:
    f265['verified_current'] = vc + addon

if not any(r.get('id') == 'F-NEW-277' for r in roots):
    roots.append({
        "id": "F-NEW-277",
        "status": "CLASSIFIED",
        "title": "RECOMPOSITION STARVATION AT THE FRAME-PUMP QUIESCENCE BOUNDARY "
                 "(dooz F6 content frontier, CONT-23): the Compose Recomposer "
                 "runner's withFrameNanos await loop never re-arms after the "
                 "launch-frame pump quiesces, so the recomposition that would "
                 "insert the navigation destination content (NavHost "
                 "visibleEntries -> collectAsState LaunchedEffect -> "
                 "applyChanges #2) never executes and the app shows NavHost "
                 "chrome (3 LayoutNodes) with zero app draw ops forever.",
        "priority": "P0",
        "layer": "runtime/frame-clock + compose/recomposer-scheduling",
        "root_cause":
            "ROOT (runtime-decoded at fa88902fdee6e982, evidence "
            "run/cont23/): (1) composition attaches 6 LayoutNodes "
            "(field-trace Lel0.r biography); (2) the first doFrame's "
            "applyChanges runs ONE recomposition whose change list REMOVES "
            "the NavHost-internal content subtree (runtime chain "
            "Ls21.Y -> Lg21.a -> Lv02.j(0,1) -> Lel0.Q removeAt(0,1) -> "
            "Lel0.M onChildRemoved -> Lel0.h detach — faithful to upstream "
            "UiApplier.remove/LayoutNode.removeAt/detach, ui 1.11.4); (3) "
            "dooz's real content (GameScreen via navigation-compose 2.9.8 "
            "NavHost) arrives only when the visibleEntries StateFlow value "
            "reaches the composition through collectAsState's LaunchedEffect "
            "— a SECOND applyChanges on a later frame; (4) the engine's "
            "launch-frame pump (pump_compose_frames, bound=8) quiesces at "
            "tick 3 with the last frame-clock callback REMOVED (the handler "
            "path won per the upstream AndroidUiDispatcher 'whichever comes "
            "first' law) and the Recomposer runner never re-posts its "
            "withFrameNanos callback ([CHOREO] rows end; [PARK-DRAIN] park "
            "work_units=1 cycles at a frozen 300ms stamp) — so no tick 4, "
            "no recomposition #2, no destination content, no app-owned "
            "pixels (frame truth DEFAULT_BACKGROUND_ONLY). Upstream laws: "
            "AndroidUiDispatcher.android.kt one-MessageQueue dispatch "
            "(handler trampoline + Choreographer arm, whichever first; the "
            "winner must run the continuations); Recomer runRecomposeAndApplyChanges "
            "awaits withFrameNanos EVERY loop iteration; AOSP MessageQueue "
            "nativePollOnce wakes at next-message-when (the F-NEW-197 idle "
            "law the engine already models).",
        "evidence":
            "SOURCE-FIRST: upstream/s43 (ui 1.11.4 LayoutNode/UiApplier/"
            "MeasureAndLayoutDelegate), navigation-compose/runtime 2.9.8 "
            "sources (dl.google.com, the dooz-pinned family) NavHost.kt "
            "backStackEntry gate + collectAsState law; dooz app source "
            "(github.com/yamin8000/Dooz) MainActivity/GameScreen "
            "collectAsStateWithLifecycle + hiltViewModel. RUNTIME: "
            "run/cont23/dooz_mtrace (72,936 METHOD-IN rows), dooz_ft_owner "
            "(6 attaches/3 detaches), dooz_cl/cl2 (applier remove caller "
            "chain), dooz_after_long (120s: 3 ticks then quiescence, "
            "DEFERRED-UI-PENDING, park cycles), GRAPHICAL_PROGRESS.md "
            "before/after table (all deltas 0). FALSIFICATION: the "
            "'lifecycle gap' hypothesis was disproven by the "
            "lifecycle_transaction_probe (5/5 PASS at the unmodified "
            "binary — the G09 start/resume transaction already fires); a "
            "trial DEX-engine patch that double-dispatched the transaction "
            "was reverted, restoring byte-exact fa88902f.",
        "probe":
            "MINIANDROID_FIELD_TRACE=Lel0;.r (attach/detach biography), "
            "MINIANDROID_CL_TRACE (caller frames), MINIANDROID_DRAW_WINDOW_TRACE, "
            "[CHOREO]/[F100-STATE]/[CHOREO-PUMP] rows; "
            "fixtures/lifecycle_transaction_probe (locks the G09 start/resume "
            "law, 5/5 PASS).",
        "fanout":
            "every Compose app whose destination/state content arrives through "
            "a flow collect + recomposition cycle after the launch frame "
            "(navigation-compose, collectAsState/WithLifecycle families — the "
            "F6 family surface); every virtual-time-driven re-arm of the "
            "Recomposer runner.",
        "date": "2026-10-08",
        "next_fix_surface":
            "Re-arm the Recomposer runner's frame-clock await when the pump "
            "quiesces with parked dispatcher work (honor [PARK-DRAIN] "
            "work_units and the deferred queue at the quiescence boundary) "
            "WITHOUT breaking the F-115b frozen launch-frame law — anchor "
            "18/18 byte-identical is the hard gate; candidate: extend the "
            "quiescence law to run the parked AndroidUiDispatcher "
            "continuations (the handler-arm winner) before declaring "
            "quiescence, keeping the virtual clock frozen.",
    })
    print('F-NEW-277 registered (CLASSIFIED P0)')
else:
    print('F-NEW-277 already present — no duplicate')

reg['total_roots'] = len(roots)
if 'total' in reg:
    reg['total'] = len(roots)
with open(REG, 'w') as f:
    json.dump(reg, f, indent=1)
print('total roots:', len(roots))
