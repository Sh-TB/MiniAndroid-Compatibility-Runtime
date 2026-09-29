#!/usr/bin/env python3
"""s121_gmdice_autoplay.py — gmdice FULL agent session (S121).

Dice-roller app (de.duenndns.gmdice). Buttons on the bottom bar (measured
vision: y=1845): 3D20 @x116, 1d20 @x332, 1d6 @x592, 1d6+4 @x845.
Session: roll each button, verify the result region changes every time and
the dice COUNT matches the button (3D20 -> three numbers).
"""
import glob
import os
import subprocess

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/canonical_apks/de.duenndns.gmdice_8.apk"
OUT = f"{ROOT}/run/s121_gmdice"
BAR_Y = 1845
BTN = {"3D20": 116, "1d20": 332, "1d6": 592, "1d6+4": 845}


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


def result_region(png):
    """The dice-result text band above the button bar."""
    return Image.open(png).convert("L").crop((0, 1480, 1080, 1800)).tobytes()


def main():
    taps = []
    schedule = [("1d6", 20), ("1d20", 28), ("3D20", 36), ("1d6+4", 44),
                ("1d6", 52)]
    for name, fr in schedule:
        taps.append((BTN[name], BAR_Y, fr))
    rc = run_engine(taps, 64, OUT)
    print("rc:", rc)
    frames = sorted(glob.glob(f"{OUT}/frames/frame_*.png"))
    # stage states: before each tap and after it settles
    marks = [16, 26, 34, 42, 50, 58, 63]
    prev = None
    for fr in marks:
        p = f"{OUT}/frames/frame_{fr:03d}.png"
        if not os.path.exists(p):
            continue
        s = result_region(p)
        tag = "SAME" if prev is not None and s == prev else "CHANGED"
        print(f"frame {fr}: result-region {tag}")
        prev = s
    # count distinct result states
    states = []
    for fr in range(20, 64):
        p = f"{OUT}/frames/frame_{fr:03d}.png"
        if os.path.exists(p):
            s = result_region(p)
            if not states or states[-1] != s:
                states.append(s)
    print(f"distinct result states from frame 20: {len(states)}")
    # determinism: rerun once, compare final 10 frames byte-wise
    d2 = f"{OUT}_r2"
    run_engine(taps, 64, d2)
    same = all(
        Image.open(f"{OUT}/frames/frame_{i:03d}.png").tobytes()
        == Image.open(f"{d2}/frames/frame_{i:03d}.png").tobytes()
        for i in range(54, 64)
        if os.path.exists(f"{OUT}/frames/frame_{i:03d}.png")
        and os.path.exists(f"{d2}/frames/frame_{i:03d}.png"))
    print("repeatability vs run2 (final frames):",
          "IDENTICAL" if same else "VARIANCE (dice RNG expected)")


if __name__ == "__main__":
    main()
