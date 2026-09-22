#!/usr/bin/env python3
"""s80_ladder_sweep.py — S80 full app-list ladder sweep at HEAD.

Runs every runnable APK in the inventory through the real engine (12 frames
each), records rc / errors / render nonwhite / load status. Boundaries
(WebView apps, no-Activity apps, Compose frontier) are pre-classified and
reported as-is, not "bugs". Output: run/s80_ladder/sweep_report.json +
console table.
"""
import glob
import json
import os
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s80_ladder"
os.makedirs(OUT, exist_ok=True)

# inventory: (apk_path, label, preclass)
APKS = [
    ("upload/s72_w4_apks/snake_v1.0_vc1.apk", "Snake (AndroidGameSnake)", "real game"),
    ("upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk", "Snake Deluxe (S80)", "real game"),
    ("upload/s80_games/build_tetris/tetris_v1.0_vc1.apk", "Mini Tetris (S80)", "real game"),
    ("upload/s80_games/build_2048/g2048_v1.0_vc1.apk", "2048 (S80)", "real game"),
    ("upload/canonical_apks/app.varlorg.unote_30.apk", "uNote", None),
    ("apk_cache/com.chessclock.android_29.apk", "Chess Clock", None),
    ("upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk", "TicTacToe (emmanuelmess)", None),
    ("upload/canonical_apks/com.github.muellerma.stopwatch_6.apk", "Stopwatch (muellerma)", "no-Activity boundary"),
    ("upload/canonical_apks/de.duenndns.gmdice_8.apk", "gmdice", None),
    ("upload/canonical_apks/dooz_23_toplevel.apk", "Dooz", "Compose boundary"),
    ("upload/canonical_apks/dubrowgn.microtimer_8.apk", "MicroTimer", None),
    ("apk_cache/nl.hansdezwart.bgclock_2.apk", "BGClock", "WebView boundary"),
    ("apk_cache/omegacentauri.mobi.simplestopwatch_26.apk", "Simple Stopwatch", None),
    ("apk_cache/org.billthefarmer.notes_139.apk", "Notes (billthefarmer)", None),
    ("apk_cache/org.debian.eugen.headingcalculator_1.apk", "Heading Calculator", None),
    ("apk_cache/rkr.simplekeyboard.inputmethod_145.apk", "Simple Keyboard", None),
]
# extra APKs from other waves (resolve if present)
extras = [
    ("upload/canonical_apks/fishrings_v1.23_vc6.apk", "fishrings", None),
    ("upload/canonical_apks/opmt_v0.1.2_vc1.apk", "OPMT", None),
    ("upload/canonical_apks/tripeaks_v1.2.1_vc4.apk", "tripeaks", None),
    ("upload/canonical_apks/bouncy.apk", "bouncy", None),
    ("upload/real_apps/telegram_v12.apk", "Telegram v12", "heavy app"),
]
for p, label, pc in extras:
    if os.path.exists(p):
        APKS.append((p, label, pc))
    else:
        # search
        hits = glob.glob(f"{ROOT}/upload/**/{os.path.basename(p)}", recursive=True)
        if hits:
            APKS.append((hits[0], label, pc))
        else:
            print(f"SKIP (missing): {label} ({p})")

# also check common cache locations for missing extras
cache_hits = glob.glob(f"{ROOT}/apk_cache/*.apk")
for c in cache_hits:
    name = os.path.basename(c)
    if "telegram" in name.lower():
        APKS.append((c, f"Telegram ({name})", "heavy app"))


def nonwhite(png):
    im = Image.open(png).convert("RGB")
    px = im.load()
    n = 0
    for y in range(0, im.height, 4):
        for x in range(0, im.width, 4):
            r, g, b = px[x, y]
            if r < 245 or g < 245 or b < 245:
                n += 1
    return n * 16  # scale back (sampled every 4th px both axes)


def sweep(apk, label, preclass):
    tag = os.path.basename(apk).replace(".apk", "")[:40]
    out = f"{OUT}/{tag}"
    os.makedirs(out, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "12", "--frame-delay", "250", "-o", out, apk]
    log = f"{OUT}/{tag}.log"
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=300)
        except subprocess.TimeoutExpired:
            rc = -1
    errors = warnings = "?"
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":")[1].strip()
        if line.startswith("Warnings:"):
            warnings = line.split(":")[1].strip()
    frames = sorted(glob.glob(f"{out}/frames/frame_*.png"))
    nw = nonwhite(frames[-1]) if frames else 0
    status = ("LOAD_OK" if rc == 0 and errors == "0" and nw > 1000
              else "LOAD_OK_DARK" if rc == 0 and errors == "0"
              else "ENGINE_ERR" if rc == 0 else f"RC_{rc}")
    return {
        "apk": os.path.basename(apk), "label": label,
        "preclass": preclass, "rc": rc, "errors": errors,
        "frames": len(frames), "nonwhite_last": nw,
        "status": status,
    }


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    results = []
    for apk, label, preclass in APKS:
        if not os.path.exists(apk):
            print(f"MISSING {label}")
            continue
        if only and only.lower() not in label.lower():
            continue
        r = sweep(apk, label, preclass)
        results.append(r)
        print(f"{r['status']:<14} {r['label']:<28} rc={r['rc']} "
              f"err={r['errors']} frames={r['frames']} nonwhite={r['nonwhite_last']}")
    with open(f"{OUT}/sweep_report.json", "w") as f:
        json.dump({"generated": "S80 ladder sweep at HEAD", "results": results},
                  f, indent=1)
    print(f"\nreport: {OUT}/sweep_report.json")


if __name__ == "__main__":
    main()
