#!/usr/bin/env python3
"""s83_campaign.py — S83 graphics-base validation campaign.

Runs the user-mandated validation corpus:
  * 20+ games (in-house 4 + real F-Droid games from the S82 cache)
  * 10+ simple apps (Level 0/1 best-effort)
  * 2 random high-level apps (newsblur, timelimit)
Each APK: engine run -> real PNG frames -> visual audit (S81 instrument)
-> honest LEVEL. Output: run/s83_campaign/report.json + JPG evidence.

Law: EXECUTED != VISUALLY_COMPATIBLE. No fake scores (S83 §42).
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
OUT = f"{ROOT}/run/s83_campaign"
S82 = "/tmp/my-project/apk_cache/s82"
CORPUS = "/tmp/my-project/apk_cache/corpus"
os.makedirs(OUT, exist_ok=True)

GAMES = [
    (f"{ROOT}/upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk",
     "Snake Deluxe", "in-house S80"),
    (f"{ROOT}/upload/s83_games/build_tetris/tetris_v1.0_vc1.apk",
     "Mini Tetris", "in-house S80"),
    (f"{ROOT}/upload/s83_games/build_g2048/g2048_v1.0_vc1.apk",
     "2048", "in-house S80"),
    (f"{ROOT}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
     "TicTacToe Deluxe", "in-house S83 NEW"),
    (f"{CORPUS}/dooz.apk", "Dooz (tic-tac-toe)", "real"),
    (f"{CORPUS}/tictactoeclassic.apk", "TicTacToe Classic", "real"),
    (f"{S82}/com.sidhant.queens_93.apk", "Queens", "real game"),
    (f"{S82}/cos.premy.mines_16.apk", "Mines (premy)", "real game"),
    (f"{S82}/eu.veldsoft.no.thanks_1.apk", "No Thanks!", "real game"),
    (f"{S82}/eu.quelltext.memory_7.apk", "Memory", "real game"),
    (f"{S82}/crypto.o0o0o0o0o.games.blackjack_4.apk", "Blackjack", "real game"),
    (f"{S82}/com.vayunmathur.games.solitaire_20260804.apk",
     "Solitaire (vayunmathur)", "real game"),
    (f"{S82}/de.tobiasbielefeld.solitaire_71.apk", "Solitaire (tobiasb.)",
     "real game"),
    (f"{S82}/org.secuso.privacyfriendlybattleship_101.apk", "Battleship",
     "real game"),
    (f"{S82}/com.jeffliu.balancetheball_4.apk", "Balance the Ball", "real game"),
    (f"{S82}/com.simondalvai.ball2box_69.apk", "Ball2Box", "real game"),
    (f"{S82}/app.halma_15.apk", "Halma", "real game"),
    (f"{S82}/com.astroloop.game_4.apk", "Astroloop", "real game"),
    (f"{S82}/si.palcka.tarok_203.apk", "Tarok", "real game"),
    (f"{S82}/page.codeberg.lanticy.guandan_7.apk", "Guandan", "real game"),
    (f"{S82}/com.rocket9labs.boxcars_104090.apk", "Boxcars", "real game"),
    (f"{S82}/com.bupkis.tirailleur_13.apk", "Tirailleur", "real game"),
    (f"{S82}/com.eightsines.firestrike.opensource_2000.apk", "Firestrike",
     "real game"),
]

APPS = [
    (f"{ROOT}/upload/canonical_apks/app.varlorg.unote_30.apk", "uNote", "L0/L1"),
    ("/tmp/my-project/apk_cache/omegacentauri.mobi.simplestopwatch_26.apk",
     "Simple Stopwatch", "L0/L1"),
    (f"{ROOT}/upload/canonical_apks/dubrowgn.microtimer_8.apk", "MicroTimer",
     "L0/L1"),
    ("/tmp/my-project/apk_cache/com.chessclock.android_29.apk", "Chess Clock",
     "L0/L1"),
    ("/tmp/my-project/apk_cache/org.billthefarmer.notes_139.apk",
     "Notes (billthefarmer)", "L0/L1"),
    ("/tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk",
     "Heading Calculator", "L0/L1"),
    (f"{ROOT}/upload/canonical_apks/de.duenndns.gmdice_8.apk", "gmdice",
     "L0/L1"),
    (f"{S82}/com.best.deskclock_2036.apk", "DeskClock", "L0/L1"),
    (f"{S82}/com.bnyro.clock_24.apk", "Bnyro Clock", "L0/L1"),
    (f"{S82}/se.tube42.p9.android_11.apk", "P9 (tube42)", "L0/L1 mandatory"),
]

HIGH = [
    (f"{S82}/com.newsblur_289.apk", "NewsBlur", "HIGH random"),
    (f"{S82}/io.timelimit.android.aosp.direct_231.apk", "TimeLimit",
     "HIGH random"),
]


def run_app(apk, label, frames=8, delay=300, timeout=420):
    tag = os.path.basename(apk).replace(".apk", "")[:44]
    out = f"{OUT}/{tag}"
    os.makedirs(out, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(delay),
           "-o", out, apk]
    log = f"{out}.log"
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = -1
    errors = "?"
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":")[1].strip()
    frames_l = sorted(glob.glob(f"{out}/frames/frame_*.png"))
    item = {"apk": os.path.basename(apk), "label": label, "rc": rc,
            "errors": errors, "frames": len(frames_l)}
    if frames_l:
        m = audit_frame(frames_l[-1])
        lvl, name = level_of(m)
        m["LEVEL"] = lvl
        m["LEVEL_NAME"] = name
        m.update(apk_resource_counts(apk))
        item["visual"] = m
        item["final_frame"] = frames_l[-1]
    return item


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = {"games": [], "apps": [], "high": []}
    groups = []
    if which in ("all", "games"):
        groups.append(("games", GAMES))
    if which in ("all", "apps"):
        groups.append(("apps", APPS))
    if which in ("all", "high"):
        groups.append(("high", HIGH))
    for gname, lst in groups:
        for apk, label, kind in lst:
            if not os.path.exists(apk):
                print(f"MISSING {label} ({apk})")
                results[gname].append({"apk": os.path.basename(apk),
                                       "label": label, "kind": kind,
                                       "rc": -2, "errors": "APK-MISSING",
                                       "frames": 0})
                continue
            r = run_app(apk, label)
            r["kind"] = kind
            v = r.get("visual", {})
            results[gname].append(r)
            print(f"[{gname}] rc={r['rc']:<3} L{v.get('LEVEL','-')} "
                  f"{v.get('LEVEL_NAME','NO-FRAME'):<22} "
                  f"uniq={v.get('UNIQUE_COLORS','-'):<5} "
                  f"{label:<26} {','.join(v.get('FLAGS', []))[:70]}")
    with open(f"{OUT}/report.json", "w") as f:
        json.dump({"campaign": "S83 graphics-base validation",
                   "results": results}, f, indent=1)
    n = sum(len(v) for v in results.values())
    ok = sum(1 for v in results.values() for r in v if r.get("frames"))
    print(f"\nreport: {OUT}/report.json  ({ok}/{n} produced frames)")


if __name__ == "__main__":
    main()
