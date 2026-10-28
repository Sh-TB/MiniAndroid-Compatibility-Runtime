#!/usr/bin/env python3
"""cont49_repair.py — repair the S124-era corrupted pkg rows ("…" placeholder)
using DIRECT CONT-49 train evidence (APK on disk + engine report.md Package +
title match). Laws:
  - only rows whose title unambiguously matches the APK (5 of 9; the other 4
    have no disk-APK provenance and stay flagged as structural debt)
  - pkg repaired; prior evidence string preserved; CONT-49 run appended as
    corroborating re-run; load state UNCHANGED (no invented promotions)
  - GAME-106 Notes left untouched: title says billthefarmer, disk APK is
    Secuso's — provenance not established, honest deferral."""
import json

BASE = "/home/z/my-project"
path = f"{BASE}/plugins/apps.jsonl"

TRAIN = {
    "GAME-102": ("app.varlorg.unote",
                 "face=DARK uniq32=29 nonwhite=1.000 sha=7481e9b468eaa376 rc=0"),
    "GAME-103": ("dubrowgn.microtimer",
                 "face=BLUE uniq32=37 nonwhite=0.442 sha=bbd350b6c14fbd52 rc=0"),
    "GAME-104": ("com.github.muellerma.stopwatch",
                 "face=FLAT uniq32=1 sha=31ddd4d5b8e6d18e rc=1 F-016 exception-honest"),
    "GAME-105": ("com.chessclock.android",
                 "face=DARK uniq32=32 nonwhite=0.975 sha=fe3ae1167c9e968c rc=0"),
    "GAME-110": ("com.darkempire78.opencalculator",
                 "face=BLUE uniq32=127 nonwhite=0.591 sha=63020bc7334048fe rc=1 "
                 "F-016 exception-honest (629 uncaught; T9 pin 7e33aad was under "
                 "DEBUG_DRAWABLES timing — variance honestly noted, no drift claim)"),
}

rows = [json.loads(l) for l in open(path) if l.strip()]
repaired = []
for r in rows:
    if r.get("i") in TRAIN:
        pkg, evidence = TRAIN[r["i"]]
        old = r.get("pkg")
        r["pkg"] = pkg
        r["ev"] = str(r.get("ev") or "") + f"; CONT-49 121f re-run: {evidence}"
        repaired.append((r["i"], old, pkg, r.get("load")))

with open(path, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("repaired:", len(repaired))
for x in repaired:
    print("  *", x)
# verify: no more ambiguous … rows except the 4 deferred
left = [(r["i"], r.get("t")) for r in rows if str(r.get("pkg")) == "…"]
print("remaining … rows (deferred, no provenance):", left)
