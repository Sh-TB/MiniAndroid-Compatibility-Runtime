#!/usr/bin/env python3
"""s122_klondike_session.py — agent-play session for Klondike solitaire
(eu.veldsoft.free.klondike vc3, S122 harder-games wave).

Stage A: tap "New Game" -> the table deals.
Stage B: agent taps a stock/waste/tableau move sequence.
Honest evidence: every state change read from rendered frames.
"""
import json
import os
import subprocess
import sys

from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s122_klondike_session"
APK = f"{R}/upload/klondike_veldsoft_3.apk"


def run_engine(taps, n_frames, out_dir, frame_delay=250):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    log = f"{out_dir}.log"
    rc = subprocess.call(cmd, stdout=open(log, "w"),
                         stderr=subprocess.STDOUT, timeout=600)
    return rc


def stage_of(png):
    """Classify the rendered stage from pixel evidence (menu vs table)."""
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    # menu rows are the blue (100,150,200)-family buttons at top
    blue = 0
    for y in range(0, 460, 4):
        for x in range(0, w, 8):
            r, g, b = px[x, y]
            if 90 <= r <= 130 and 140 <= g <= 170 and 190 <= b <= 215:
                blue += 1
    # table cards are white-ish blocks in the upper third
    white = 0
    for y in range(120, 700, 6):
        for x in range(0, w, 6):
            r, g, b = px[x, y]
            if r > 235 and g > 235 and b > 235:
                white += 1
    return {"blue_menu_px": blue, "white_card_px": white,
            "stage": "menu" if blue > 300 else ("table" if white > 200 else "?")}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    # Stage A: tap New Game at (540, 64) on frame 8
    rc = run_engine([(540, 64, 8)], 80, f"{OUT}/new_game")
    last = None
    fd = f"{OUT}/new_game/frames"
    for f in sorted(os.listdir(fd), reverse=True):
        if f.endswith(".png"):
            last = f"{fd}/{f}"
            break
    st = stage_of(last) if last else {}
    print(json.dumps({"rc": rc, "last": last, "stage": st}, indent=1))
