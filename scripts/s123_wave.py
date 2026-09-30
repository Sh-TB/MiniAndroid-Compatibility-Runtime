#!/usr/bin/env python3
"""s123_wave.py — S123 wave probes (user directive fa).

New content per directive:
  - calculator app  : com.darkempire78.opencalculator vc53 (F-Droid)
  - flappy game     : flappycow rebuilt from upstream source (cubei/FlappyCow,
                      SurfaceView game; GMS/ads stubs at build time — gameplay
                      code untouched)
  - one more game   : org.secuso.privacyfriendlysudoku vc101 (F-Droid)
  - one more app    : org.secuso.privacyfriendlynotes vc105 (F-Droid)
Messaging load-progress tests (user: "خیلی مهم"):
  - forkgram 12.10.8.0 (S115 anchor: rc=0, 0 errors, tree-built, NO pixels)
  - official Telegram latest (S119 anchor: Dialogs page render)
Pipeline per app: probe run (48-64 frames) -> pixel metrics -> error scan.
"""
import json
import math
import os
import subprocess
from collections import Counter

from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s123"

APKS = {
    "opencalculator": (f"{R}/upload/opencalculator_53.apk", 48),
    "flappycow": (f"{R}/upload/flappycow_rebuilt.apk", 48),
    "sudoku": (f"{R}/upload/sudoku_secuso_101.apk", 48),
    "notes": (f"{R}/upload/notes_secuso_105.apk", 48),
    "forkgram": (f"{R}/upload/forkgram_709208.apk", 64),
    "telegram": (f"{R}/upload/telegram_official.apk", 64),
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
    }


def scan_errors(log_path):
    if not os.path.exists(log_path):
        return {"log": "missing"}
    txt = open(log_path, errors="ignore").read()
    import re
    errs = re.findall(r"(?m)^\[?E\]? ?\[(.*?)\]", txt)
    uncaught = len(re.findall(r"uncaught|Uncaught", txt))
    rc = re.search(r"exit code[=: ]+(\d+)|rc[=: ]+(\d+)", txt)
    return {
        "log_bytes": len(txt),
        "error_tags": errs[:8],
        "error_count": len(errs),
        "uncaught_mentions": uncaught,
        "rc": (rc.group(1) or rc.group(2)) if rc else None,
    }


def run_one(name, apk, frames):
    d = f"{OUT}/{name}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", "200", "-o", d, apk]
    log = f"{d}.log"
    try:
        rc = subprocess.call(cmd, stdout=open(log, "w"),
                             stderr=subprocess.STDOUT, timeout=900)
    except subprocess.TimeoutExpired:
        rc = -2
    shot = f"{d}/screenshot.png"
    m = metrics(shot) if os.path.exists(shot) else {"error": "no screenshot"}
    return {"app": name, "rc": rc, "metrics": m,
            "errors": scan_errors(log)}


def main():
    results = {}
    for name, (apk, frames) in APKS.items():
        print(f"=== probe {name}")
        results[name] = run_one(name, apk, frames)
        print(json.dumps(results[name], indent=1)[:600])
    json.dump(results, open(f"{OUT}/probe_results.json", "w"), indent=1)
    print("saved", f"{OUT}/probe_results.json")


if __name__ == "__main__":
    main()
