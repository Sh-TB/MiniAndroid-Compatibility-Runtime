#!/usr/bin/env python3
"""s120_new_games.py — NEW non-HTML5 games sweep (S120).

User directive: run NEW games (not re-confirmations), different programming
stacks, somewhat heavier. Candidates from the corpus that were never actually
PLAYED before (S115 verdicts were blank/stub for most):
  tripeaks (card solitaire), fishrings (card game w/ AI), bouncy (physics),
  gmdice (dice), opmt (scarecrow games), dooz Compose (Jetpack Compose stack).
Pipeline per game: probe run (30 frames, no taps) -> pixel metrics -> visual
frame saved -> click-test dispatch report.
"""
import json
import math
import os
import subprocess
import sys
from collections import Counter
from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s120_new_games"
APKS = {
    "tripeaks": f"{R}/upload/s65_apks/tripeaks_v1.2.1_vc4.apk",
    "fishrings": f"{R}/upload/s65_apks/fishrings_v1.23_vc6.apk",
    "bouncy": f"{R}/upload/canonical_apks/bouncy.apk",
    "gmdice": f"{R}/upload/canonical_apks/de.duenndns.gmdice_8.apk",
    "opmt": f"{R}/upload/canonical_apks/opmt_v0.1.2_vc1.apk",
    "dooz_compose": f"{R}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk",
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
    # background = most common color
    bg, bgc = colors.most_common(1)[0]
    nonbg = n - bgc
    ent = 0.0
    for c in colors.values():
        p = c / n
        ent -= p * math.log2(p)
    return {
        "size": [w, h],
        "unique_colors_sampled": len(colors),
        "non_bg_ratio": round(nonbg / n, 5),
        "entropy_bits": round(ent, 2),
        "top_color": list(bg),
    }


def run_one(name, apk, frames=30, extra=None):
    d = f"{OUT}/{name}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", "250", "-o", d]
    if extra:
        cmd += extra
    cmd += [apk]
    log = f"{d}.log"
    try:
        rc = subprocess.call(cmd, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                             timeout=420)
    except subprocess.TimeoutExpired:
        rc = -2
    frames_dir = f"{d}/frames"
    last = None
    if os.path.isdir(frames_dir):
        fr = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
        if fr:
            # find last complete PNG
            for f in reversed(fr):
                try:
                    Image.open(f"{frames_dir}/{f}").verify()
                    last = f"{frames_dir}/{f}"
                    break
                except Exception:
                    continue
    m = metrics(last) if last else None
    # error count from report.md / crash.log
    errs = None
    rep = f"{d}/report.md"
    if os.path.exists(rep):
        for line in open(rep, errors="ignore"):
            if "errors" in line.lower() and ":" in line:
                errs = line.strip()[:120]
                break
    rec = {"game": name, "rc": rc, "metrics": m, "last_frame": last, "report": errs}
    print(json.dumps(rec, indent=1))
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    picks = sys.argv[1:] or list(APKS)
    results = {}
    for name in picks:
        apk = APKS.get(name)
        if not apk or not os.path.exists(apk):
            print(f"{name}: APK MISSING ({apk})")
            continue
        results[name] = run_one(name, apk)
    json.dump(results, open(f"{OUT}/s120_sweep.json", "w"), indent=1)


if __name__ == "__main__":
    main()
