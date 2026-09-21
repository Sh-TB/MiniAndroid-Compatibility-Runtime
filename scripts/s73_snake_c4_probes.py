#!/usr/bin/env python3
"""s73_snake_c4_probes.py — S73 C4 explicit game-law probes via REAL input:
1. REVERSE-REJECTION: tap LEFT while moving RIGHT → app's own guard must
   reject (direction unchanged, observed in rendered frames).
2. WALL / GAME-OVER: no steering → snake runs into the right wall →
   app declares game over (observed: panel stops drawing the snake).
3. RESTART: tap START after game over → fresh snake (observed).
Every observation comes from rendered frames; the game logic stays
authoritative (controller never patches it).
"""
import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s73_snake_controller import analyze_run, count_events, run_engine

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s73_snake_c4"
os.makedirs(OUT, exist_ok=True)

# START@1; LEFT@5 (reverse of R — expect REJECTION); no steering → wall
# death; START@30 (restart after game over).
TAPS = [(98, 839, 1), (220, 999, 5), (98, 839, 30)]
rc = run_engine(TAPS, 40, OUT)
obs = analyze_run(OUT)
ev = count_events(obs)

report = {"rc": rc, "taps": [f"({x},{y})@{f}" for x, y, f in TAPS],
          "frames": len(obs), "events": ev, "probes": {}}

# --- probe 1: reverse rejection (frames 6-8 must still move RIGHT)
dirs_6_8 = [obs[i]["dir"] for i in (6, 7, 8) if i < len(obs)]
heads_5_8 = [obs[i]["head"] for i in (5, 6, 7, 8) if i < len(obs)]
rejected = all(d == "R" for d in dirs_6_8)
report["probes"]["reverse_rejection"] = {
    "probe": "tap LEFT@5 while moving RIGHT",
    "observed_dirs_frames_6_8": dirs_6_8,
    "observed_heads_5_8": heads_5_8,
    "rejected": rejected,
    "verdict": "REJECTED (app reverse-guard held)" if rejected
               else "NOT REJECTED",
}

# --- probe 2: wall game-over (no steering: snake runs right into x=19 wall)
over_idx = next((o["frame_index"] for o in obs if o["game_over"]), None)
last_snake_frame = max(o["frame_index"] for o in obs if o["snake"])
report["probes"]["wall_game_over"] = {
    "probe": "no steering after START — snake runs into right wall",
    "last_frame_with_snake": last_snake_frame,
    "first_game_over_frame": over_idx,
    "head_before_death": obs[last_snake_frame]["head"],
    "verdict": "GAME-OVER OBSERVED at wall" if over_idx else
               "NO GAME-OVER OBSERVED",
}

# --- probe 3: restart (START@30 → fresh snake at start cells)
post = [o for o in obs if o["frame_index"] >= 31 and o["snake"]]
restart = False
restart_detail = None
if post:
    first = post[0]
    if (11, 10) in first["snake"] or first["head"] in ((10, 10), (11, 10)):
        restart = True
        restart_detail = {"frame": first["frame_index"],
                          "snake": first["snake"]}
report["probes"]["restart"] = {
    "probe": "tap START@30 after game over",
    "observed": restart, "detail": restart_detail,
    "verdict": "RESTART OBSERVED" if restart else "NO RESTART OBSERVED",
}

with open(f"{OUT}/c4_probe_report.json", "w") as f:
    json.dump(report, f, indent=1)
print(json.dumps(report, indent=1))
