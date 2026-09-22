#!/usr/bin/env python3
"""s81_run_and_audit.py — S81: run every corpus APK at HEAD, then visual-audit
the final frame (§2 metrics + §3 flags + §17 level). Honest status per app:
EXECUTED != VISUALLY_COMPATIBLE (§1). Resource-side raster counts are joined
(§20/§26) so MISSING_IMAGES_SUSPECTED reflects APK-vs-screen evidence.
Output: run/s81_audit/<tag>/frames + run/s81_audit/s81_visual_report.json
"""
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, level_of, apk_resource_counts

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s81_audit"
os.makedirs(OUT, exist_ok=True)

APKS = [
    ("upload/s72_w4_apks/snake_v1.0_vc1.apk", "Snake (AndroidGameSnake)", "real game"),
    ("upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk", "Snake Deluxe (S80)", "real game"),
    ("upload/s80_games/build_tetris/tetris_v1.0_vc1.apk", "Mini Tetris (S80)", "real game"),
    ("upload/s80_games/build_2048/g2048_v1.0_vc1.apk", "2048 (S80)", "real game"),
    ("upload/canonical_apks/app.varlorg.unote_30.apk", "uNote", None),
    ("apk_cache/com.chessclock.android_29.apk", "Chess Clock", None),
    ("upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk", "TicTacToe (emmanuelmess)", None),
    ("upload/canonical_apks/de.duenndns.gmdice_8.apk", "gmdice", None),
    ("upload/canonical_apks/dooz_23_toplevel.apk", "Dooz", "Compose boundary"),
    ("upload/canonical_apks/dubrowgn.microtimer_8.apk", "MicroTimer", None),
    ("apk_cache/omegacentauri.mobi.simplestopwatch_26.apk", "Simple Stopwatch", None),
    ("apk_cache/org.billthefarmer.notes_139.apk", "Notes (billthefarmer)", None),
    ("apk_cache/org.debian.eugen.headingcalculator_1.apk", "Heading Calculator", None),
    ("apk_cache/rkr.simplekeyboard.inputmethod_145.apk", "Simple Keyboard", None),
    ("upload/canonical_apks/fishrings_v1.23_vc6.apk", "fishrings", None),
    ("upload/canonical_apks/opmt_v0.1.2_vc1.apk", "OPMT", None),
    ("upload/canonical_apks/tripeaks_v1.2.1_vc4.apk", "tripeaks", None),
    ("upload/canonical_apks/bouncy.apk", "bouncy", None),
]


def run_app(apk, label):
    tag = os.path.basename(apk).replace(".apk", "")[:44]
    out = f"{OUT}/{tag}"
    os.makedirs(out, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "8", "--frame-delay", "300", "-o", out, apk]
    log = f"{out}.log"
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=420)
        except subprocess.TimeoutExpired:
            rc = -1
    errors = "?"
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":")[1].strip()
    frames = sorted(glob.glob(f"{out}/frames/frame_*.png"))
    item = {"apk": os.path.basename(apk), "label": label, "rc": rc,
            "errors": errors, "frames": len(frames)}
    if frames:
        m = audit_frame(frames[-1])
        lvl, name = level_of(m)
        m["LEVEL"] = lvl
        m["LEVEL_NAME"] = name
        rcnt = apk_resource_counts(apk)
        m.update(rcnt)
        if rcnt.get("APK_RASTER_RESOURCES", 0) > 3 and \
           (m["IMAGE_PIXELS"] + m["ICON_PIXELS"]) < 0.002 * m["SCREEN_WIDTH"] * m["SCREEN_HEIGHT"]:
            m["FLAGS"] = m["FLAGS"] + ["MISSING_IMAGES_SUSPECTED",
                                       "IMAGE_DECODED_VS_RENDERED_GAP"]
        item["visual"] = m
        item["frame_paths"] = frames[-2:]
    return item


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    results = []
    for apk, label, pc in APKS:
        if not os.path.exists(apk):
            print(f"MISSING {label} ({apk})")
            continue
        if only and only.lower() not in label.lower():
            continue
        r = run_app(apk, label)
        v = r.get("visual", {})
        results.append(r)
        print(f"rc={r['rc']:<3} L{v.get('LEVEL','-')} {v.get('LEVEL_NAME','NO-FRAME'):<22}"
              f" uniq={v.get('UNIQUE_COLORS','-'):<5} dom={v.get('DOMINANT_COLOR_RATIO','-'):<7}"
              f" {r['label']:<28} {','.join(v.get('FLAGS', []))[:80]}")
    with open(f"{OUT}/s81_visual_report.json", "w") as f:
        json.dump({"generated": "S81 visual audit at HEAD", "results": results}, f, indent=1)
    print(f"\nreport: {OUT}/s81_visual_report.json")


if __name__ == "__main__":
    main()
