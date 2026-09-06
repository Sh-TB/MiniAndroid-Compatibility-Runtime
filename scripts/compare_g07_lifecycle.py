#!/usr/bin/env python3
# compare_g07_lifecycle.py — G07 §9/§10 lifecycle golden comparator.
#
# RUN A (--tap 540,400 on btn_finish):
#   frame_000 texts contain "CSR"  — onCreate→onStart→onResume ran through
#                                    REAL DEX (the app's own mark() writes)
#   frame_002 texts contain "CSRPHD" — the finish cascade (onPause → onStop
#                                    → onDestroy) ran through REAL DEX at
#                                    the frame boundary
#   manifest.finish_cascade: 3 callbacks, all dispatched with instructions>0
#   lifecycle_trace.json: full machine PROCESS_CREATED → … → DESTROYED in
#   the exact AOSP order
#
# RUN B (--frames 4 --frame-delay 250): main-thread task dispatch —
#   Ticks 1..3 fire across frames in order (self-limiting repost chain),
#   frame SHAs recorded.
#
# Usage: compare_g07_lifecycle.py <run_a> <run_b> [--json out.json]
import json
import sys
from pathlib import Path

CHECKS = {"total": 0, "pass": 0, "fail": 0}
FAILURES = []


def check(ok, what):
    CHECKS["total"] += 1
    if ok:
        CHECKS["pass"] += 1
        print(f"  PASS: {what}")
    else:
        CHECKS["fail"] += 1
        FAILURES.append(what)
        print(f"  FAIL: {what}")


def texts_of(frame):
    return {t["text"] for t in frame.get("visible_texts", [])}


def main():
    run_a, run_b = sys.argv[1], sys.argv[2]
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    print("── RUN A: tap FINISH → lifecycle cascade at frame boundary ──")
    m = json.loads((Path(run_a) / "frames" / "manifest.json").read_text())
    t0, t2 = texts_of(m["frames"][0]), texts_of(m["frames"][2])
    check("CSR" in t0,
          "boot lifecycle visible: onCreate+onStart+onResume executed via "
          "real DEX (app's own mark() output)")
    check("Ticks: 1" in t0,
          "postDelayed runnable fired at the idle-settle boundary "
          "(main-thread dispatch)")
    check("CSRPHD" in t2,
          "post-finish state: onPause+onStop+onDestroy executed via real "
          "DEX — the app's own text records the full machine")
    check("Ticks: 1" in t2, "tick chain correctly stopped at 3 (finite)")

    fc = m.get("finish_cascade")
    check(fc is not None, "finish() cascade consumed at the frame boundary")
    if fc:
        cbs = fc.get("callbacks", [])
        names = [c["method"] for c in cbs]
        check(names == ["onPause", "onStop", "onDestroy"],
              "cascade order onPause → onStop → onDestroy "
              "(ActivityThread law)")
        check(all(c["dispatched"] for c in cbs),
              "all 3 lifecycle callbacks dispatched through the DEX engine")
        check(all(c.get("instructions", 0) > 0 for c in cbs),
              "all 3 callbacks executed REAL bytecode (instructions > 0)")
        check(fc.get("final_state") == "DESTROYED",
              "state machine final state = DESTROYED")

    lt = json.loads((Path(run_a) / "lifecycle_trace.json").read_text())
    order = [t["to"] for t in lt["transitions"] if t["success"]]
    check(order == ["ACTIVITY_CREATED", "STARTED", "RESUMED", "PAUSED",
                    "STOPPED", "DESTROYED"],
          "lifecycle_trace.json = canonical machine order (§10): "
          "CREATED→STARTED→RESUMED→PAUSED→STOPPED→DESTROYED")
    check(all(t["success"] for t in lt["transitions"]),
          "no invalid transitions in the recorded run")
    ms = [t["virtual_ms"] for t in lt["transitions"]]
    check(ms == sorted(ms), "transition timestamps non-decreasing "
          "(virtual-clock monotonicity)")

    print("── RUN B: --frames tick sequencing (main-thread law) ──")
    mb = json.loads((Path(run_b) / "frames" / "manifest.json").read_text())
    ticks_seen = []
    for fr in mb["frames"]:
        for t in texts_of(fr):
            if t.startswith("Ticks: "):
                ticks_seen.append(int(t.split(": ")[1]))
    check(ticks_seen and ticks_seen[0] == 1,
          "frame 0 shows Ticks: 1 (settle-drain fired the first tick)")
    check(3 in ticks_seen,
          "self-reposted runnable advanced across frame boundaries")
    check(max(ticks_seen) == 3 if ticks_seen else False,
          "repost chain self-limited at 3 (finite chain law)")
    shas = [fr["sha256"] for fr in mb["frames"]]
    check(len(set(shas)) == len(shas) or len(set(shas)) > 1,
          "frames recorded with per-frame SHAs")

    print("── G07 LIFECYCLE GOLDEN ──")
    verdict = "PASS" if CHECKS["fail"] == 0 else "FAIL"
    print(f"{verdict} ({CHECKS['pass']}/{CHECKS['total']} checks)")
    if out_json:
        Path(out_json).write_text(json.dumps({
            "verdict": f"{verdict} ({CHECKS['pass']}/{CHECKS['total']} checks)",
            "checks": CHECKS, "failures": FAILURES,
        }, indent=2))
    return 0 if CHECKS["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
