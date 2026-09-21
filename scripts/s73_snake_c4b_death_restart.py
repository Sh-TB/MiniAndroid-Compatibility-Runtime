#!/usr/bin/env python3
"""s73_snake_c4b_death_restart.py — S73 C4 probes part 2: self-collision
game-over + restart, via REAL taps appended to the exact S73 autonomous
autoplay schedule.

Design (from observed wrap law: walls wrap, so death = self-collision):
the autoplay run ends at frame 89 with len-4 snake on row 10 moving R.
Extend: D@90 → L@91 → U@92 makes the head re-enter (5,10) — a cell still
occupied by the body at tick start (predicted self-collision).
Then START@99 → observed restart (fresh snake) if the app ended.
All observations from rendered frames; app logic authoritative.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s73_snake_controller import analyze_run, count_events, run_engine, BTN
from s73_snake_finalize import taps_from_log

ROOT = "/home/z/my-project"
ITER = f"{ROOT}/run/s73_snake_auto/iter_04"
OUT = f"{ROOT}/run/s73_snake_c4b"
os.makedirs(OUT, exist_ok=True)

taps = taps_from_log(f"{ITER}/engine.log")
taps += [(BTN["BOTTOM"][0], BTN["BOTTOM"][1], 90),    # D
         (BTN["LEFT"][0], BTN["LEFT"][1], 91),        # L
         (BTN["TOP"][0], BTN["TOP"][1], 92),          # U (into body)
         (BTN["START"][0], BTN["START"][1], 99)]      # restart attempt
rc = run_engine(taps, 108, OUT)
obs = analyze_run(OUT)
ev = count_events(obs)

report = {"rc": rc, "taps_total": len(taps), "frames": len(obs),
          "events": ev, "probes": {}}

# timeline around the death attempt and restart attempt
timeline = {}
for i in range(88, min(len(obs), 108)):
    o = obs[i]
    timeline[i] = {"snake": o["snake"], "food": o["food"],
                   "dir": o["dir"], "game_over": o["game_over"]}
report["timeline_88_107"] = timeline

# game-over detection: snake disappears after having been present
over_idx = next((o["frame_index"] for o in obs if o["game_over"]), None)
report["probes"]["self_collision_game_over"] = {
    "predicted_head_reentry": "(5,10) occupied at tick start (frame 93)",
    "first_game_over_frame": over_idx,
    "verdict": "GAME-OVER OBSERVED" if over_idx is not None else
               "NO GAME-OVER (snake survived — record honestly)",
}

# restart: snake present again after game over with start-state cells
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

with open(f"{OUT}/c4b_report.json", "w") as f:
    json.dump(report, f, indent=1)
print(json.dumps({k: v for k, v in report.items() if k != "timeline_88_107"},
                 indent=1))
print("--- timeline 88..107 ---")
for i in sorted(timeline):
    t = timeline[i]
    print(f"frame {i}: snake={t['snake']} food={t['food']} "
          f"over={t['game_over']}")
