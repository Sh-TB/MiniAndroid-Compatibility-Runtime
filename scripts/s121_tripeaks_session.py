#!/usr/bin/env python3
"""s121_tripeaks_session.py — the definitive full TriPeaks session (S121).

Full load + agent play with GENEROUS tap spacing (12 frames apart — the
main-run hint says tight 4-frame taps get dropped by the app's own input
handling). Sequence (deterministic deal: 3h 8c 7h 5d Kh 5h Ac Qh, waste 6c,
stock 23):
  New Game @24        -> deal
  tap 7h  @44         -> capture (winings +1, waste 6c->7h)
  tap 8c  @56         -> capture if the app chains +-1 (8 on 7)
  tap 5d  @68         -> capture if chaining further
  draw    @80         -> Cards Remaining 23->22
  draw    @92         -> 22->21
  (post-draw captures attempted at @104/@116 against the drawn waste card)
Reads: waste card region, Game Winings digits, Cards Remaining digits,
row slot occupancy — all vision-only.
"""
import os
import subprocess

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s65_apks/tripeaks_v1.2.1_vc4.apk"
OUT = f"{ROOT}/run/s121_tripeaks/session"
ROW_Y = 215
ROW_X = [172, 290, 401, 519, 644, 762, 880, 998]
NEW_GAME = (540, 188)
STOCK = (526, 404)


def run_engine(taps, n_frames, out_dir, frame_delay=250):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=900)
    return rc


def winings(png):
    return Image.open(png).convert("L").crop((250, 1710, 430, 1780)).tobytes()


def remaining(png):
    return Image.open(png).convert("L").crop((320, 1670, 440, 1730)).tobytes()


def waste(png):
    return Image.open(png).convert("RGB").crop((832, 348, 924, 464)).tobytes()


def stage(png):
    return {
        "waste": hash(waste(png)),
        "winings": hash(winings(png)),
        "remaining": hash(remaining(png)),
    }


def main():
    taps = [
        (NEW_GAME[0], NEW_GAME[1], 24),
        (401, ROW_Y, 44),    # 7h
        (290, ROW_Y, 56),    # 8c
        (519, ROW_Y, 68),    # 5d
        (STOCK[0], STOCK[1], 80),
        (STOCK[0], STOCK[1], 92),
        (401, ROW_Y, 104),   # post-draw attempt
        (290, ROW_Y, 116),   # post-draw attempt
    ]
    rc = run_engine(taps, 130, OUT)
    print("rc:", rc)
    marks = [24, 40, 46, 50, 52, 58, 62, 70, 74, 82, 86, 94, 98, 106, 110,
             118, 122, 129]
    base = None
    for fr in marks:
        p = f"{OUT}/frames/frame_{fr:03d}.png"
        if not os.path.exists(p):
            continue
        s = stage(p)
        tag = ""
        if base is None:
            base = s
        for k in ("waste", "winings", "remaining"):
            if s[k] != base[k]:
                tag += f" {k}:CHANGED"
        print(f"frame {fr}: {tag.strip() or 'baseline-like'}")
    # stage-frame hashes for the record
    import json
    rec = {"taps": taps, "rc": rc, "stages": {fr: stage(
        f"{OUT}/frames/frame_{fr:03d}.png") for fr in marks
        if os.path.exists(f"{OUT}/frames/frame_{fr:03d}.png")}}
    with open(f"{OUT}/session_record.json", "w") as f:
        json.dump(rec, f, indent=1)
    print("WROTE", f"{OUT}/session_record.json")


if __name__ == "__main__":
    main()
