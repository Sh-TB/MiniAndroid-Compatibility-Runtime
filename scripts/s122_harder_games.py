#!/usr/bin/env python3
"""s122_harder_games.py — S122 wave: TWO HARDER games (user directive).

User (fa): "دوتا بازی سختر رو هم امتحان بکن" — try two harder games too.
Picks (heavier + different programming stacks, never played before):
  chess     : jwtc.android.chess 10.6.0 (vc298) — full chess rules engine + AI,
              custom board View, MenuPreferences stack. Heaviest logic game.
  klondike  : eu.veldsoft.free.klondike (vc3) — FULL Klondike solitaire
              (52-card tableau+foundation+stock rules engine), heavier than
              the S120 tripeaks deal-capture loop.

Pipeline per game: probe run (60 frames, no taps) -> pixel metrics -> visual
frame -> report errors. Full-load gate before any autoplay is designed.
"""
import json
import math
import os
import subprocess
from collections import Counter

from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s122_harder"
APKS = {
    "chess": f"{R}/upload/chess_jwtc_298.apk",
    "klondike": f"{R}/upload/klondike_veldsoft_3.apk",
}


def metrics(png):
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    colors = Counter()
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            colors[px[x, y]] += 1
    n = sum(colors.values())
    bg, bgc = colors.most_common(1)[0]
    ent = 0.0
    for c in colors.values():
        p = c / n
        ent -= p * math.log2(p)
    return {
        "size": [w, h],
        "unique_colors_sampled": len(colors),
        "non_bg_ratio": round((n - bgc) / n, 5),
        "entropy_bits": round(ent, 2),
        "top_color": list(bg),
    }


def run_one(name, apk, frames=60, extra=None):
    d = f"{OUT}/{name}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", "250", "-o", d]
    if extra:
        cmd += extra
    cmd += [apk]
    log = f"{d}.log"
    try:
        rc = subprocess.call(cmd, stdout=open(log, "w"),
                             stderr=subprocess.STDOUT, timeout=600)
    except subprocess.TimeoutExpired:
        rc = -2
    frames_dir = f"{d}/frames"
    last = None
    if os.path.isdir(frames_dir):
        fr = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
        for f in reversed(fr):
            try:
                Image.open(f"{frames_dir}/{f}").verify()
                last = f"{frames_dir}/{f}"
                break
            except Exception:
                continue
    m = metrics(last) if last else None
    errs = None
    rep = f"{d}/report.md"
    if os.path.exists(rep):
        for line in open(rep, errors="ignore"):
            if "errors" in line.lower() and ":" in line:
                errs = line.strip()[:120]
                break
    rec = {"game": name, "rc": rc, "metrics": m, "last_frame": last,
           "report": errs}
    print(json.dumps(rec, indent=1))
    return rec


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    picks = sys_picks = __import__("sys").argv[1:] or ["chess", "klondike"]
    results = {}
    for name in picks:
        apk = APKS.get(name)
        if not apk or not os.path.exists(apk):
            print(f"{name}: APK MISSING")
            continue
        results[name] = run_one(name, apk)
    json.dump(results, open(f"{OUT}/s122_probe.json", "w"), indent=1)
