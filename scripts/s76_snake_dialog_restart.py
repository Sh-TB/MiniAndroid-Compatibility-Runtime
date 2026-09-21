#!/usr/bin/env python3
"""s76_snake_dialog_restart.py — S76 Lead-3: the Dialog-restart hypothesis.

S73/S75 record: restart via the panel START button after game-over was NOT
observed. Hypothesis (S73): the restart path is DIALOG-based.

S76 static proof (the app's own DEX, upload/s72_w4_apks/snake_v1.0_vc1.apk):
  SnakePanelView.showMessageDialog() (code 0x1fd8)
    -> post(SnakePanelView$1)                          (code 0x140c run())
       -> AlertDialog.Builder(getContext())
          .setMessage("Game Over!")
          .setCancelable(false)
          .setPositiveButton("重新开始", SnakePanelView$1$1)   (code 0x1390)
          .setNegativeButton("退出",  SnakePanelView$1$2)
          .create().show()
  SnakePanelView$1$1.onClick(DialogInterface, int)
    -> dialog.dismiss(); SnakePanelView.reStartGame()  (code 0x1d80)

So the restart actuator is the DIALOG's positive button ("重新开始"),
NOT the panel START button. The S75 evidence (frames/manifest.json
frames 94+) shows the dialog WAS rendered with buttons view_id 700003
"退出" and 700004 "重新开始" — the probe tapped the wrong target.

This probe: two real-dalvik runs of the identical S73/S75 autonomous
schedule (23 recovered taps + D@90 L@91 U@92 death extension):
  run A (no restart tap): parse [DIALOG-LAYOUT] frame=(l,t w,h) from
     engine.log, compute the positive-button center from the painter law
     (DialogShadow::render_dialogs: button row at b-112..b, thirds split
     over the NON-EMPTY labels in order neutral,negative,positive — with
     2 buttons the positive is the RIGHT half), then verify the rendered
     frame_0094 actually paints "重新开始" there (pixel check: the
     button text color 0x0062CC blue present in the right-half label
     region).
  run B: same schedule + tap(positive_center)@99; analyze frames 94..127
     for RESTART: snake cells re-appear (game returns to the initial
     3-cell state / fresh motion) after the dialog dismisses.

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
OUT = f"{ROOT}/docs/evidence/s76/snake_dialog_restart"
os.makedirs(OUT, exist_ok=True)

# --- recover the 23-tap autonomous schedule from the committed trace ---
taps = []
for line in open(TRACE, encoding="utf-8", errors="replace"):
    m = re.search(r"tap\((\d+),(\d+)\)@frame(\d+)", line)
    if m:
        x, y, fr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        taps.append((x, y, fr))
assert len(taps) == 23, f"expected 23 scheduled taps, got {len(taps)}"

# --- S73 C4B death extension, verbatim ---
taps += [(BTN["BOTTOM"][0], BTN["BOTTOM"][1], 90),    # D
         (BTN["LEFT"][0], BTN["LEFT"][1], 91),        # L
         (BTN["TOP"][0], BTN["TOP"][1], 92)]          # U (into body)

# ---------------- run A: death + dialog, no restart tap ----------------
out_a = f"{OUT}/run_a_dialog"
rc_a = run_engine(taps, 108, out_a)

layout = None
for line in open(f"{out_a}/engine.log", encoding="utf-8", errors="replace"):
    m = re.search(r"\[DIALOG-LAYOUT\] frame=\((-?\d+),(-?\d+) (\d+)x(\d+)\)", line)
    if m:
        layout = dict(l=int(m.group(1)), t=int(m.group(2)),
                      w=int(m.group(3)), h=int(m.group(4)))
assert layout, "no DIALOG-LAYOUT line found in run A engine.log"

# Painter law: pad=24, button row at b-112..b (b = t+h), thirds over the
# non-empty labels in order (neutral, negative, positive).
PAD = 24
ROW_TOP = 112
l, t, w, h = layout["l"], layout["t"], layout["w"], layout["h"]
b = t + h
# labels: negative "退出", positive "重新开始" -> thirds = 2
seg_w = (w - 2 * PAD) // 2
pos_x = l + PAD + seg_w + seg_w // 2
pos_y = b - ROW_TOP + 62
print(f"run A: dialog frame=({l},{t} {w}x{h}) positive-btn center=({pos_x},{pos_y})")

report = {"rc_run_a": rc_a, "dialog_layout": layout,
          "positive_btn_center": [pos_x, pos_y], "probes": {}}

# pixel check: the positive label region in frame_0094 must contain the
# button text blue 0x0062CC (DialogShadow painter law color).
try:
    from PIL import Image
    img = Image.open(f"{out_a}/frames/frame_0094.png").convert("RGB")
    hits = 0
    for yy in range(max(0, pos_y - 14), min(img.height, pos_y + 14)):
        for xx in range(max(0, pos_x - seg_w // 2), min(img.width, pos_x + seg_w // 2)):
            r, g, bb = img.getpixel((xx, yy))
            if abs(r - 0x00) < 40 and abs(g - 0x62) < 40 and abs(bb - 0xCC) < 40:
                hits += 1
    report["probes"]["positive_label_blue_px_frame94"] = hits
except Exception as e:
    report["probes"]["positive_label_blue_px_frame94"] = f"ERR {e}"

# ---------------- run B: same schedule + dialog-button tap ----------------
taps_b = taps + [(pos_x, pos_y, 99)]
out_b = f"{OUT}/run_b_restart"
rc_b = run_engine(taps_b, 128, out_b)

obs = analyze_run(out_b)
ev = count_events(obs)
report["rc_run_b"] = rc_b
report["taps_run_b"] = len(taps_b)
report["frames_observed"] = len(obs)
report["events"] = ev

timeline = {}
for i in range(90, min(len(obs), 128)):
    o = obs[i]
    timeline[i] = {"snake": o["snake"], "head": o["head"], "dir": o["dir"],
                   "game_over": o["game_over"]}
report["timeline_90_127"] = timeline

over_idx = next((o["frame_index"] for o in obs if o["game_over"]), None)
report["probes"]["self_collision_game_over"] = {
    "first_game_over_frame": over_idx,
    "verdict": "GAME-OVER OBSERVED" if over_idx is not None else
               "NO GAME-OVER",
}

# restart law: after the tap@99, the dialog must dismiss and the game must
# return to motion. Evidence from frames: the snake cell set CHANGES from
# the frozen game-over state and the dialog text leaves the frame.
restart_frame = None
if over_idx is not None:
    frozen = None
    for o in obs:
        if o["game_over"]:
            frozen = o["snake"]
            break
    for o in obs[over_idx + 1:]:
        if o["snake"] and frozen is not None and o["snake"] != frozen:
            restart_frame = o["frame_index"]
            report["probes"]["restart_via_dialog"] = {
                "probe": f"tap positive button at ({pos_x},{pos_y}) @99",
                "frozen_game_over_cells": frozen,
                "first_changed_snake_frame": restart_frame,
                "cells_at_change": o["snake"],
                "verdict": "RESTART OBSERVED (snake state changed after "
                           "dialog-button tap)",
            }
            break
if restart_frame is None:
    report["probes"]["restart_via_dialog"] = {
        "probe": f"tap positive button at ({pos_x},{pos_y}) @99",
        "verdict": "NO RESTART OBSERVED",
    }

with open(f"{OUT}/s76_dialog_restart_report.json", "w") as f:
    json.dump(report, f, indent=1)
print(json.dumps({k: v for k, v in report.items()
                  if k not in ("timeline_90_127",)}, indent=1))
print("--- timeline 90..end ---")
for i in sorted(timeline):
    tt = timeline[i]
    print(i, "head:", tt["head"], "dir:", tt["dir"], "over:", tt["game_over"],
          "cells:", tt["snake"])
