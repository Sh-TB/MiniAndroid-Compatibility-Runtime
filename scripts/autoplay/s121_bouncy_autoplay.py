#!/usr/bin/env python3
"""s121_bouncy_autoplay.py — bouncy menu -> gameplay attempts (S121).

Menu buttons measured from the rendered frame (x=519 column):
  Start Game y606, High scores y798, Help y942, Preferences y1092, Quit y1278.
Each screen transition is a separate full launch (clean evidence per screen).
The game field is a custom View — the S120 frontier question is whether it
renders once the game activity starts.
"""
import os
import subprocess

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/canonical_apks/bouncy.apk"
OUT = f"{ROOT}/run/s121_bouncy"
BTN_X = 519


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


def screen_sig(png):
    return hash(Image.open(png).convert("RGB").tobytes())


def ink(png, y0, y1):
    img = Image.open(png).convert("L").crop((0, y0, 1080, y1))
    return sum(1 for v in img.getdata() if v > 40)


def probe(name, taps, frames=80):
    d = f"{OUT}/{name}"
    rc = run_engine(taps, frames, d)
    marks = [20, 26, 32, 44, 60, 79]
    prev = None
    out = []
    for fr in marks:
        p = f"{d}/frames/frame_{fr:03d}.png"
        if not os.path.exists(p):
            continue
        s = screen_sig(p)
        tag = "SAME" if s == prev else "CHANGED"
        prev = s
        out.append(f"f{fr}:{tag}")
    # custom-view band ink (game field region between the header/footer bars)
    last = f"{d}/frames/frame_{marks[-1]:03d}.png"
    band = ink(last, 200, 1700) if os.path.exists(last) else -1
    print(f"{name}: rc={rc} {' '.join(out)} gamefield_ink={band}")
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    probe("start_game", [(BTN_X, 606, 24)])
    probe("high_scores", [(BTN_X, 798, 24)])
    probe("help", [(BTN_X, 942, 24)])


if __name__ == "__main__":
    main()
