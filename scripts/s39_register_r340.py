#!/usr/bin/env python3
"""S39 round 2: register R-NEW-340 (frame-pump ordering — fixed; residual
recomposer suspension recorded as NEXT frontier)."""
import json

REG = "/home/z/my-project/root_registry.json"
reg = json.load(open(REG))
roots = reg["roots"]
by_id = {r["id"]: r for r in roots}

r340 = {
    "id": "R-NEW-340",
    "status": "PARTIAL-FIX",
    "priority": "P1",
    "fg": True,
    "evidence": (
        "S39 OBSERVED (dooz23 runs r339f/r340): (a) F-050 launch frame pump "
        "ran at log:242402 with pending_cb=0 -> quiescence at tick=0; (b) the "
        "Recomposer posted its Choreographer.FrameCallback DURING onCreate at "
        "log:242620 ([CHOREO] postFrameCallback cb=757 class=Lh9;) — after "
        "the pump; (c) no second pump existed -> withFrameNanos never "
        "resumed -> zero content nodes (white frame). FIX APPLIED: "
        "post-lifecycle pump in stage_capture_output (max_frames=16) -> "
        "[CHOREO] doFrame tick fired, runnable id=1231 (Lrx; resume "
        "machinery) drained, Recomposer job machinery advanced (Lkp1; "
        "o1050/o1316 state reads, .Q(ZLkj0;) await path) — DEEPEST Compose "
        "execution yet recorded for dooz23."
    ),
    "root_cause": (
        "Frame-pump ordering: the only pump ran before onCreate's "
        "composition posted its first FrameCallback; AOSP vsync is a "
        "continuous process, the runtime pumped once."
    ),
    "fix": (
        "stage_capture_output now pumps up to 16 frame ticks right before "
        "capture (last-frame law). First pump tick fires the posted "
        "callback and resumes the Recomposer; residual gap (NEXT): after "
        "the resumed recomposition pass, the Recomposer suspends WITHOUT "
        "posting another frame callback (no [CHOREO] postFrameCallback "
        "after the resume; quiescence at tick=1) — the next suspension is "
        "not frame-gated or the re-post path is dropped."
    ),
    "severity": "high",
    "commit": "S39-FIX2",
    "next": (
        "(1) Trace the resumed recomposition pass to its next suspension "
        "point: which suspend function does Lkp1;.Q(ZLkj0;) land on after "
        "the resume — another withFrameNanos (would re-post) or "
        "CancellableContinuation suspended on a Latch/Mutex that never "
        "completes? (2) Check AndroidUiDispatcher dispatch semantics: "
        "Compose's Recomposer 'runRecomposition' loop re-arms via "
        "dispatcher.dispatch — verify [QUEUE] enqueue follows the resume. "
        "(3) Candidate fix: bounded outer pump loop (repeat pump while "
        "progress, mirroring AOSP continuous vsync) vs fixing the missed "
        "re-post at its source."
    ),
}
if "R-NEW-340" not in by_id:
    roots.append(r340)
else:
    by_id["R-NEW-340"].update(r340)

json.dump(reg, open(REG, "w"), ensure_ascii=False, indent=1)
print(f"R-NEW-340 registered; total roots = {len(roots)}")
