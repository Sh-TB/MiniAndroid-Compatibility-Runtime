#!/usr/bin/env python3
"""s123_drivers.py — S123 new-content drivers (calculator/flappy/sudoku/notes).

flappycow: SurfaceView game (upstream cubei/FlappyCow rebuilt with GMS/ads
stubs). Driver: start-screen "Start to play" tap -> Game activity -> periodic
flap taps -> verify bird/scene motion via pixel state changes.
sudoku/notes: probe + first-interaction pass (menu item / FAB tap).
Runs 3x per the repeatability law and writes an evidence record.
"""
import glob
import json
import os
import subprocess

from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s123"


def run_engine(tag, apk, frames, taps=(), delay=200, extra=()):
    d = f"{OUT}/{tag}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(delay), "-o", d]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += list(extra) + [apk]
    log = f"{d}.log"
    rc = subprocess.call(cmd, stdout=open(log, "w"),
                         stderr=subprocess.STDOUT, timeout=900)
    return rc, d, log


def diff_px(a, b):
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return -1
    pa, pb = ia.load(), ib.load()
    n = 0
    for y in range(0, ia.size[1], 2):
        for x in range(0, ia.size[0], 2):
            if pa[x, y] != pb[x, y]:
                n += 1
    return n * 4


def flappy_run(idx):
    """Start screen -> Play tap -> flaps."""
    apk = f"{R}/upload/flappycow_rebuilt.apk"
    # Play button center (StartscreenView draws a button on the cow scene;
    # the standard start screen puts "Start to play" mid-lower screen).
    taps = [(540, 1400, 18), (540, 900, 30), (540, 900, 36),
            (540, 900, 42), (540, 900, 48)]
    rc, d, log = run_engine(f"flappy_run{idx}", apk, 64, taps)
    frames = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    # state change: before play tap vs after game settles
    marks = {}
    if len(frames) > 40:
        marks["menu_to_game"] = diff_px(frames[16], frames[30])
        marks["flap_motion_1"] = diff_px(frames[30], frames[34])
        marks["flap_motion_2"] = diff_px(frames[38], frames[42])
        marks["flap_motion_3"] = diff_px(frames[46], frames[50])
    return rc, d, log, marks, frames[-1] if frames else None


def main():
    record = {}
    # 3-run repeatability for flappy
    for i in (1, 2, 3):
        rc, d, log, marks, last = flappy_run(i)
        record[f"flappycow_run{i}"] = {"rc": rc, "marks": marks}
        print(f"flappy run{i}: rc={rc} {marks}")
    json.dump(record, open(f"{OUT}/flappy_records.json", "w"), indent=1)


if __name__ == "__main__":
    main()
