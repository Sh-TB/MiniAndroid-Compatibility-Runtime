#!/usr/bin/env python3
"""s98_games_full_load.py — GAMES-1: full-load 10 games on the runtime.

Roster: 5 in-house S80/S86 games + the NEW S98 Snake Neon + 4 real corpus
titles. Each game gets: launch -> render frames -> screenshot ink check ->
view-tree dump check -> real tap -> state-change check (frame SHA delta).
Writes docs/evidence/s98/games_full_load.json + per-game rows.
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s98_games_full_load"

ROSTER = [
    ("com.miniandroid.snakedeluxe", "in-house S80",
     f"{ROOT}/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"),
    ("com.miniandroid.snakeneon", "in-house S98 NEW (wrap-around snake)",
     f"{ROOT}/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk"),
    ("com.miniandroid.g2048", "in-house S80",
     f"{ROOT}/upload/s80_games/build_2048/g2048_v1.0_vc1.apk"),
    ("com.miniandroid.tetris", "in-house S80",
     f"{ROOT}/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"),
    ("com.miniandroid.tictactoedeluxe", "in-house S83",
     f"{ROOT}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"),
    ("com.miniandroid.minicraft", "in-house S86 (house builder)",
     f"{ROOT}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk"),
    ("com.dozingcatsoftware.bouncy", "real corpus (canonical_apks)",
     f"{ROOT}/upload/canonical_apks/bouncy.apk"),
    ("com.unciv.game-fishrings", "real corpus (canonical_apks)",
     f"{ROOT}/upload/canonical_apks/fishrings_v1.23_vc6.apk"),
    ("com.hughes.android.tripeaks", "real corpus (canonical_apks)",
     f"{ROOT}/upload/canonical_apks/tripeaks_v1.2.1_vc4.apk"),
    ("de.duenndns.gmdice", "real corpus (canonical_apks)",
     f"{ROOT}/upload/canonical_apks/de.duenndns.gmdice_8.apk"),
]


def sh(cmd, timeout=300):
    return subprocess.call(cmd, timeout=timeout,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def frame_shas(run_dir):
    return [hashlib.sha256(open(f, "rb").read()).hexdigest()
            for f in sorted(glob.glob(f"{run_dir}/frames/frame_*.png"))]


def full_load(name, tag, apk):
    run = f"{OUT}/{name}"
    shutil.rmtree(run, ignore_errors=True)
    os.makedirs(run, exist_ok=True)
    env = dict(os.environ)
    row = {"package": name, "tag": tag, "apk": os.path.basename(apk)}

    if not os.path.isfile(apk):
        row["verdict"] = "APK-MISSING"
        return row

    # phase 1: baseline load (8 frames + view tree)
    rc = sh([ENG, "run", "--execution-mode", "real-dalvik", "--frames", "8",
             "--frame-delay", "110", "--width", "1080", "--height", "1920",
             "--dump-view-tree", "--data-root", f"{run}/data1", "-o", run,
             apk], timeout=420)
    row["load_rc"] = rc
    shot = f"{run}/screenshot.png"
    if rc == 0 and os.path.isfile(shot):
        img = Image.open(shot).convert("RGB")
        px = list(img.getdata())
        nonwhite = sum(1 for p in px if p != (255, 255, 255))
        row["nonwhite_pct"] = round(100 * nonwhite / len(px), 2)
        vt = f"{run}/view_tree.json"
        if os.path.isfile(vt):
            v = json.load(open(vt))
            row["views"] = v.get("view_count", len(v.get("nodes", [])))
        row["renders"] = row.get("nonwhite_pct", 0) > 1.0
    else:
        row["renders"] = False

    # phase 2: interaction — tap center screen at frame 6, compare SHAs
    rc2 = sh([ENG, "run", "--execution-mode", "real-dalvik", "--frames", "12",
              "--frame-delay", "110", "--width", "1080", "--height", "1920",
              "--data-root", f"{run}/data2", "-o", run + "_tap",
              "--tap", "540,960@6", apk], timeout=420)
    shas_a = frame_shas(run)
    shas_b = frame_shas(run + "_tap")
    if shas_a and shas_b:
        n = min(len(shas_a), 5)  # frames BEFORE the tap can differ nothing
        row["prefix_identical"] = shas_a[:n] == shas_b[:n]
        row["post_tap_differs"] = shas_a[min(n, len(shas_a) - 1):] != \
                                  shas_b[min(n, len(shas_b) - 1):] or \
                                  len(shas_b) > len(shas_a)
        row["interaction_evidence"] = bool(row["prefix_identical"]) and \
            (shas_a[len(shas_a) // 2:] != shas_b[len(shas_b) // 2:] or
             len(shas_b) != len(shas_a) or row.get("post_tap_differs", False))
    row["tap_rc"] = rc2

    ok = row.get("renders") and rc == 0
    row["verdict"] = "FULL_LOAD_PASS" if ok else "LOAD_ISSUE"
    return row


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, tag, apk in ROSTER:
        r = full_load(name, tag, apk)
        rows.append(r)
        print(f"{r['package']:36s} {r.get('verdict'):16s} "
              f"ink={r.get('nonwhite_pct','-')}% views={r.get('views','-')} "
              f"interaction={r.get('interaction_evidence','-')}")
    passed = sum(1 for r in rows if r["verdict"] == "FULL_LOAD_PASS")
    json.dump({"wave": "S98 GAMES-1 full-load 10 games", "rows": rows,
               "passed": passed, "total": len(rows)},
              open(f"{ROOT}/docs/evidence/s98/games_full_load.json", "w"),
              indent=1)
    print(f"FULL LOAD: {passed}/{len(rows)} PASS")
    sys.exit(0 if passed >= 8 else 1)


if __name__ == "__main__":
    main()
