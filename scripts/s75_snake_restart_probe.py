#!/usr/bin/env python3
"""s75_snake_restart_probe.py — S75 CLOSURE WAVE: re-run the S73 C4B
death+restart probe at HEAD c67230be (the queued honest open: "restart via
START after game-over NOT observed").

Differences from S73 C4B: the S73 controller iterated live (iter_04
engine.log held the tap schedule); run/ artifacts died with the container
reset. The IDENTICAL 23-tap schedule is recoverable from the committed
run_01 gameplay_trace.json 'input' fields (tap(x,y)@frame) — same source
the S73 report describes ("three independent full runs of the identical
23-tap schedule"). Everything else is the S73 C4B design verbatim:
extend the autoplay schedule with D@90 -> L@91 -> U@92 (head re-enters the
body), then START@99 as the restart attempt; 108 frames.

All observations from rendered frames only; the app's DEX is authoritative.
"""
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s73_snake_controller import analyze_run, count_events, run_engine, BTN

ROOT = "/home/z/my-project"
TRACE = f"{ROOT}/docs/evidence/s73_snake_autoplay/run_01/gameplay_trace.json"
OUT = f"{ROOT}/docs/evidence/s75/snake_restart_probe"
os.makedirs(OUT, exist_ok=True)

# --- recover the 23-tap autonomous schedule from the committed trace ---
taps = []
for line in open(TRACE, encoding="utf-8", errors="replace"):
    m = re.search(r"tap\((\d+),(\d+)\)@frame(\d+)", line)
    if m:
        x, y, fr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        taps.append((x, y, fr))
assert len(taps) == 23, f"expected 23 scheduled taps, got {len(taps)}"

# --- S73 C4B death + restart extension, verbatim ---
taps += [(BTN["BOTTOM"][0], BTN["BOTTOM"][1], 90),    # D
         (BTN["LEFT"][0], BTN["LEFT"][1], 91),        # L
         (BTN["TOP"][0], BTN["TOP"][1], 92),          # U (into body)
         (BTN["START"][0], BTN["START"][1], 99)]      # restart attempt

rc = run_engine(taps, 108, OUT)
obs = analyze_run(OUT)
ev = count_events(obs)

report = {"rc": rc, "taps_total": len(taps), "frames": len(obs),
          "head_at_c67230be": "S75 re-run of S73 C4B at HEAD c67230be",
          "events": ev, "probes": {}}

timeline = {}
for i in range(88, min(len(obs), 108)):
    o = obs[i]
    timeline[i] = {"snake": o["snake"], "food": o["food"],
                   "dir": o["dir"], "game_over": o["game_over"]}
report["timeline_88_107"] = timeline

over_idx = next((o["frame_index"] for o in obs if o["game_over"]), None)
report["probes"]["self_collision_game_over"] = {
    "predicted_head_reentry": "(5,10) occupied at tick start (frame 93)",
    "first_game_over_frame": over_idx,
    "verdict": "GAME-OVER OBSERVED" if over_idx is not None else
               "NO GAME-OVER (snake survived — record honestly)",
}

restart_frame = None
if over_idx is not None:
    for o in obs[over_idx + 1:]:
        if o["snake"] and ((11, 10) in o["snake"] or (10, 10) in o["snake"]
                           or o["head"] in ((11, 10), (10, 10))):
            restart_frame = o["frame_index"]
            report["probes"]["restart"] = {
                "probe": "tap START@99 after game over",
                "restart_frame": restart_frame,
                "snake": o["snake"],
                "verdict": "RESTART OBSERVED",
            }
            break
if restart_frame is None:
    report["probes"]["restart"] = {
        "probe": "tap START@99",
        "verdict": "NO RESTART OBSERVED",
    }

with open(f"{OUT}/s75_restart_report.json", "w") as f:
    json.dump(report, f, indent=1)
print(json.dumps({k: v for k, v in report.items() if k != "timeline_88_107"},
                 indent=1))
print("--- timeline 88..107 ---")
for i in sorted(timeline):
    t = timeline[i]
    print(i, "snake:", t["snake"], "dir:", t["dir"], "over:", t["game_over"])
