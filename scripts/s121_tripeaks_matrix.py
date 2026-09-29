#!/usr/bin/env python3
"""s121_tripeaks_matrix.py — tap->card mapping matrix (S121).

Each run: full launch, New Game tap @24 (lobby gate), ONE row tap @44,
56 frames. The deterministic deal is 3h 8c 7h 5d Kh 5h Ac Qh (bottom row,
left->right) with waste 6c and stock 23. Signals read from the HUD + waste
region (C3 vision — no game-state peeking):
  capture  -> Game Winings +1, waste card becomes the captured card
  miss     -> Game Winings -2, waste unchanged, remaining unchanged
  draw     -> only via stock taps (not used here)
Comparing which tap captured which card yields the absolute tap->slot delta.
"""
import os
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s65_apks/tripeaks_v1.2.1_vc4.apk"
OUT = f"{ROOT}/run/s121_tripeaks/matrix"
ROW_Y = 215
ROW_X = [172, 290, 401, 519, 644, 762, 880, 998]
NEW_GAME = (540, 188)


def run_engine(taps, n_frames, out_dir, frame_delay=250):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=600)
    return rc


def hud_winings(png):
    """Crop the 'Game Winings' numeric region (bottom-left HUD)."""
    return Image.open(png).convert("L").crop((0, 1720, 260, 1790)).tobytes()


def waste_crop(png):
    return Image.open(png).convert("RGB").crop((832, 348, 924, 464)).tobytes()


def remaining_crop(png):
    return Image.open(png).convert("L").crop((0, 1620, 340, 1680)).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    xs = [int(v) for v in sys.argv[1:]] or [290, 519, 644, 401]
    results = {}
    for x in xs:
        d = f"{OUT}/tap_{x}"
        run_engine([(NEW_GAME[0], NEW_GAME[1], 24), (x, ROW_Y, 44)], 56, d)
        pre = f"{d}/frames/frame_042.png"
        post = f"{d}/frames/frame_054.png"
        if not (os.path.exists(pre) and os.path.exists(post)):
            print(f"x={x}: FRAMES MISSING")
            continue
        w_pre, w_post = hud_winings(pre), hud_winings(post)
        cap = w_pre != w_post
        waste_changed = waste_crop(pre) != waste_crop(post)
        rem_changed = remaining_crop(pre) != remaining_crop(post)
        results[x] = {"winings_changed": cap, "waste_changed": waste_changed,
                      "remaining_changed": rem_changed}
        print(f"x={x}: winings_delta={cap} waste_changed={waste_changed} "
              f"remaining_changed={rem_changed}")
    print("\nVerdicts:")
    for x, r in results.items():
        if r["winings_changed"] and r["waste_changed"]:
            v = "CAPTURE"
        elif r["winings_changed"]:
            v = "MISS(-2)"
        else:
            v = "NO-EFFECT"
        print(f"tap x={x}: {v}")


if __name__ == "__main__":
    main()
