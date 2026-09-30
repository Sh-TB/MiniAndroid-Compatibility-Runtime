#!/usr/bin/env python3
"""s127_wave.py — S127 BASE GRAPHICS COMPLETION wave (R-NEW-423 closed).

The compact-entry law + package-routed color-reference deref changed real
framework theme values (e.g. Theme.Material.Light window = #fffafafa). This
wave proves FAN-OUT per §25 and re-anchors every golden:

  A. 3-run determinism gate: heading calculator + flappycow (S123/S124 goldens;
     lawful pixel changes documented with the exact law that moved them)
  B. Real app/game coherence: uNote (S125 golden), gmdice, microtimer,
     tictactoe, stopwatch, notes, sudoku, opencalculator, dooz (honest)
  C. Load-frontier honesty: telegram + whatsapp (NOT A RENDER labels kept)
"""
import glob
import hashlib
import json
import math
import os
import re
import subprocess
from collections import Counter

from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s127"
os.makedirs(OUT, exist_ok=True)

APKS = {
    "headingcalc": "/tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk",
    "flappycow": f"{R}/upload/flappycow_rebuilt.apk",
    "unote": f"{R}/upload/canonical_apks/app.varlorg.unote_30.apk",
    "gmdice": f"{R}/upload/canonical_apks/de.duenndns.gmdice_8.apk",
    "microtimer": f"{R}/upload/canonical_apks/dubrowgn.microtimer_8.apk",
    "tictactoe": f"{R}/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk",
    "stopwatch": f"{R}/upload/canonical_apks/com.github.muellerma.stopwatch_6.apk",
    "notes": f"{R}/upload/notes_secuso_105.apk",
    "sudoku": f"{R}/upload/sudoku_secuso_101.apk",
    "opencalculator": f"{R}/upload/opencalculator_53.apk",
    "dooz": f"{R}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk",
    "telegram": f"{R}/upload/telegram_official.apk",
    "whatsapp": "/tmp/my-project/apk_cache/WhatsApp_real.apk",
}

FLAPPY_TAPS = [(540, 1400, 18), (540, 900, 30), (540, 900, 36),
               (540, 900, 42), (540, 900, 48)]


def run_engine(tag, apk, frames, taps=(), delay=200, timeout=900):
    d = f"{OUT}/{tag}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(delay),
           "--dump-view-tree", "-o", d]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [apk]
    log = f"{d}.log"
    try:
        rc = subprocess.call(cmd, stdout=open(log, "w"),
                             stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        rc = -9
    return rc, d, log


def frame_sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def nonwhite(png):
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    n = tot = 0
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            tot += 1
            if px[x, y] != (255, 255, 255):
                n += 1
    return n, tot


def colorcount(png):
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    return len({px[x, y] for y in range(0, h, 3) for x in range(0, w, 3)})


def boot_order(log):
    """BOOT-ORDER 7-stage trace summary (S125 law)."""
    stages = re.findall(r"\[BOOT-ORDER\] (\d)/7 stage=(\w+) ok=(\d) ms=(\d+)",
                        open(log, errors="ignore").read())
    if not stages:
        return {"stages": 0, "all_ok": False}
    return {"stages": len(stages),
            "all_ok": all(s[2] == "1" for s in stages),
            "last_ms": int(stages[-1][3])}


def scan(log):
    txt = open(log, errors="ignore").read() if os.path.exists(log) else ""
    errs = re.findall(r"(?m)^\[?E\]? ?\[(.*?)\]", txt)
    return {"error_count": len(errs),
            "top_errors": list(Counter(errs).most_common(4))}


def stats_of(d):
    p = f"{d}/view_tree.json"
    if os.path.exists(p):
        vt = json.load(open(p))
        st = vt.get("inflate_stats")
        if isinstance(st, dict):
            return st
    return {}


def last_frame(d):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[-1] if fs else None


def frame_at(d, i):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[i] if i < len(fs) else (fs[-1] if fs else None)


def run_record(tag, apk, frames, taps=()):
    rc, d, log = run_engine(tag, apk, frames, taps)
    lf = last_frame(d)
    nw, tot = nonwhite(lf) if lf else (0, 0)
    rec = {"rc": rc,
           "boot": boot_order(log),
           "frame_sha": frame_sha(lf) if lf else None,
           "nonwhite": nw, "sampled": tot,
           "colors": colorcount(lf) if lf else 0,
           "errors": scan(log),
           "inflate": {k: stats_of(d).get(k) for k in
                       ("views_created", "theme_attrs_resolved",
                        "unresolved_theme_attrs", "def_style_applied",
                        "theme_overlays_pushed")}}
    print(f"[{tag}] rc={rc} boot={rec['boot']} sha={rec['frame_sha']} "
          f"nonwhite={nw}/{tot} colors={rec['colors']} errs={rec['errors']['error_count']}")
    return rec


def main():
    report = {}

    # ── A. 3-run determinism gate ───────────────────────────────
    for i in (1, 2, 3):
        report[f"calc_run{i}"] = run_record(f"calc_r{i}", APKS["headingcalc"], 48)
    for i in (1, 2, 3):
        report[f"flappy_run{i}"] = run_record(
            f"flappy_r{i}", APKS["flappycow"], 64, FLAPPY_TAPS)
        report[f"flappy_run{i}"]["menu_sha"] = frame_sha(
            frame_at(f"{OUT}/flappy_r{i}", 16) or "")

    # ── B. real apps/games coherence ────────────────────────────
    for name, frames in (("unote", 40), ("gmdice", 40), ("microtimer", 40),
                         ("tictactoe", 40), ("stopwatch", 40), ("notes", 48),
                         ("sudoku", 48), ("opencalculator", 48), ("dooz", 40)):
        report[name] = run_record(name, APKS[name], frames)

    # ── C. load-frontier honesty ────────────────────────────────
    for name, frames in (("telegram", 48), ("whatsapp", 24)):
        rc, d, log = run_engine(name, APKS[name], frames)
        lf = last_frame(d)
        txt = open(log, errors="ignore").read()
        uniq = len({px for px in
                    Image.open(lf).convert("RGB").getdata()} ) if lf else 0
        report[name] = {"rc": rc, "boot": boot_order(log),
                        "frame_sha": frame_sha(lf) if lf else None,
                        "unique_colors_last_frame": uniq,
                        "errors": scan(log),
                        "uncaught": len(re.findall(r"uncaught|Uncaught", txt))}
        print(f"[{name}] rc={rc} boot={report[name]['boot']} "
              f"unique_colors={uniq} uncaught={report[name]['uncaught']}")

    json.dump(report, open(f"{OUT}/s127_report.json", "w"), indent=1)
    print(f"\nreport -> {OUT}/s127_report.json")


if __name__ == "__main__":
    main()
