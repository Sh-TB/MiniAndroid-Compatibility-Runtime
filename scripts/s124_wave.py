#!/usr/bin/env python3
"""s124_wave.py — S124 THEME-BASE wave (user directive fa).

Directive: every app carries a theme/template structure; build the loading
base on the ORIGINAL framework law; never label a black/white frame as
"rendered"; test WhatsApp/Telegram load progress.

Parts:
  A. REGRESSION GATE on the S123 goldens (deterministic 3-run byte-compare):
     - heading calculator (themed app flagship, S123 VERIFIED_3RUN)
     - flappycow (start screen 100% + G08-LAUNCH chain)
  B. THEME-ENGINE ACTIVITY MATRIX (the new base in action on themed apps):
     - opencalculator / sudoku / notes probes: inflate stats now carry
       theme_attrs_resolved / def_style_applied / theme_overlays_pushed.
  C. LOAD-FRONTIER RETEST (honest labels): telegram official + WhatsApp
     official — quantify exceptions/pixels vs the S123 baseline.
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
OUT = f"{R}/run/s124"
os.makedirs(OUT, exist_ok=True)

APKS = {
    "headingcalc": "/tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk",
    "flappycow": f"{R}/upload/flappycow_rebuilt.apk",
    "opencalculator": f"{R}/upload/opencalculator_53.apk",
    "sudoku": f"{R}/upload/sudoku_secuso_101.apk",
    "notes": f"{R}/upload/notes_secuso_105.apk",
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


def scan(log):
    txt = open(log, errors="ignore").read() if os.path.exists(log) else ""
    errs = re.findall(r"(?m)^\[?E\]? ?\[(.*?)\]", txt)
    uncaught = len(re.findall(r"uncaught|Uncaught", txt))
    theme_base = re.findall(r"\[S124-THEME\] base_theme .*resid=0x([0-9a-f]+) valid=(\d) keys=(\d+)", txt)
    overlay = len(re.findall(r"OVERLAY", txt))
    return {
        "error_count": len(errs),
        "top_errors": list(Counter(errs).most_common(6)),
        "uncaught_mentions": uncaught,
        "theme_base": theme_base[:2],
        "overlay_resolutions": overlay,
        "log_bytes": len(txt),
    }


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


def part_a():
    rec = {}
    # heading calculator x3 (probe; S123 golden determinism law)
    for i in (1, 2, 3):
        rc, d, log = run_engine(f"calc_r{i}", APKS["headingcalc"], 48)
        lf = last_frame(d)
        nw, tot = nonwhite(lf) if lf else (0, 0)
        rec[f"calc_run{i}"] = {
            "rc": rc, "last_frame": os.path.basename(lf) if lf else None,
            "frame_sha": frame_sha(lf) if lf else None,
            "nonwhite": nw, "sampled": tot,
            "errors": scan(log),
            "inflate": {k: stats_of(d).get(k) for k in
                        ("views_created", "theme_attrs_resolved",
                         "unresolved_theme_attrs", "def_style_applied",
                         "theme_overlays_pushed", "styles_applied")},
        }
        print(f"[A] calc run{i}: rc={rc} sha={rec[f'calc_run{i}']['frame_sha']} "
              f"nonwhite={nw} inflate={rec[f'calc_run{i}']['inflate']}")
    # flappycow x3 (menu render + play tap chain)
    for i in (1, 2, 3):
        rc, d, log = run_engine(f"flappy_r{i}", APKS["flappycow"], 64, FLAPPY_TAPS)
        fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
        menu = fs[16] if len(fs) > 16 else (fs[-1] if fs else None)
        last = fs[-1] if fs else None
        rec[f"flappy_run{i}"] = {
            "rc": rc,
            "menu_sha": frame_sha(menu) if menu else None,
            "last_sha": frame_sha(last) if last else None,
            "menu_nonwhite": nonwhite(menu)[0] if menu else 0,
            "menu_to_game_px": (lambda a, b: sum(
                1 for y in range(0, 1920, 4) for x in range(0, 1080, 4)
                if Image.open(a).convert("RGB").load()[x, y] !=
                Image.open(b).convert("RGB").load()[x, y]) * 16
            ) if menu and last else 0,
            "errors": scan(log),
        }
        print(f"[A] flappy run{i}: rc={rc} menu_sha={rec[f'flappy_run{i}']['menu_sha']} "
              f"menu->game px={rec[f'flappy_run{i}']['menu_to_game_px']}")
    return rec


def part_b():
    rec = {}
    for name in ("opencalculator", "sudoku", "notes"):
        rc, d, log = run_engine(f"{name}_probe", APKS[name], 48)
        lf = last_frame(d)
        nw, tot = nonwhite(lf) if lf else (0, 0)
        rec[name] = {
            "rc": rc, "last_frame": os.path.basename(lf) if lf else None,
            "frame_sha": frame_sha(lf) if lf else None,
            "nonwhite": nw, "sampled": tot,
            "errors": scan(log),
            "inflate": {k: stats_of(d).get(k) for k in
                        ("views_created", "theme_attrs_resolved",
                         "unresolved_theme_attrs", "def_style_applied",
                         "theme_overlays_pushed", "styles_applied")},
        }
        print(f"[B] {name}: rc={rc} sha={rec[name]['frame_sha']} "
              f"nonwhite={nw} inflate={rec[name]['inflate']}")
    return rec


def part_c():
    rec = {}
    for name, frames in (("telegram", 64), ("whatsapp", 48)):
        rc, d, log = run_engine(f"{name}_load", APKS[name], frames, timeout=1200)
        lf = last_frame(d)
        nw, tot = nonwhite(lf) if lf else (0, 0)
        rec[name] = {
            "rc": rc, "last_frame": os.path.basename(lf) if lf else None,
            "frame_sha": frame_sha(lf) if lf else None,
            "nonwhite": nw, "sampled": tot,
            "errors": scan(log),
        }
        print(f"[C] {name}: rc={rc} sha={rec[name]['frame_sha']} nonwhite={nw} "
              f"errors={rec[name]['errors']['error_count']} "
              f"uncaught={rec[name]['errors']['uncaught_mentions']}")
    return rec


if __name__ == "__main__":
    record = {"A_regression": part_a(), "B_theme_matrix": part_b(),
              "C_load_frontier": part_c()}
    json.dump(record, open(f"{OUT}/s124_records.json", "w"), indent=1)
    print("WROTE", f"{OUT}/s124_records.json")
