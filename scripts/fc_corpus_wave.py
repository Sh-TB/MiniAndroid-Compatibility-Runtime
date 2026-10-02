#!/usr/bin/env python3
"""FINAL CAMPAIGN PHASE 15 — corpus attack wave (no-fake-success census).
One honest run per corpus category-representative; records FrameRenderCensus
verdict + pixel counts. Flagship/multiwindow/custom goldens already run 3x
in the gate wave (dooz/ssw/headingcalc/microtimer/whatsapp).
"""
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
CACHE = "/tmp/my-project/apk_cache"
OUT = Path("/tmp/fc15")
OUT.mkdir(parents=True, exist_ok=True)

CORPUS = [
    # (tag, apk, category)
    ("bouncy",     f"{CACHE}/corpus/bouncy.apk",                     "game-physics"),
    ("ttc",        f"{CACHE}/corpus/tictactoeclassic.apk",           "game-board"),
    ("droidify",   f"{CACHE}/corpus/droidify.apk",                   "appclient-compose"),
    ("openlauncher", f"{CACHE}/corpus/openlauncher.apk",             "launcher-custom"),
    ("simplekeyboard", f"{CACHE}/corpus/simplekeyboardinputmethod.apk", "ime-custom"),
    ("tinymusic",  f"{CACHE}/corpus/tinymusicplayer.apk",            "media"),
    ("unote",      f"{CACHE}/app.varlorg.unote_30.apk",              "notes-indie"),
    ("gmdice",     f"{CACHE}/de.duenndns.gmdice_8.apk",              "dice-game"),
    ("chessclock", f"{CACHE}/com.chessclock.android_29.apk",         "utility-multiwindow"),
]

results = {}
for tag, apk, cat in CORPUS:
    if not Path(apk).exists():
        results[tag] = {"category": cat, "error": "APK missing"}
        continue
    d = OUT / tag
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    cmd = [ENG, "run", "--execution-mode", "real-dalvik", "--frames", "2",
           "--frame-delay", "200", "--data-root", str(d / "data"),
           "-o", str(d), apk]
    try:
        rc = subprocess.call(cmd, stdout=open(d / "run.log", "w"),
                             stderr=subprocess.STDOUT, timeout=420)
    except subprocess.TimeoutExpired:
        rc = -99
    txt = (d / "run.log").read_text(errors="ignore")
    verdicts = re.findall(r"capture_verdict=([A-Z_]+)", txt) or \
               re.findall(r'FRAME VERDICT[^:]*: "?([A-Z_]+)', txt)
    sha = hashlib.sha256(
        (d / "screenshot.png").read_bytes()).hexdigest()[:16] \
        if (d / "screenshot.png").exists() else None
    results[tag] = {"category": cat, "rc": rc, "sha16": sha,
                    "verdicts": verdicts[-2:] or None}
    print(f"[CORPUS] {tag:15s} {cat:20s} rc={rc} sha={sha} "
          f"verdict={verdicts[-1] if verdicts else None}")

(OUT / "corpus_results.json").write_text(json.dumps(results, indent=2))
print("done:", len(results))
