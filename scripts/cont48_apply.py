#!/usr/bin/env python3
"""cont48_apply.py — strict exact-package apply of CONT-48 train evidence to
plugins/apps.jsonl. ZERO-LOG law: evidence = face sha16 + classifier output,
run dirs untracked. Only rows whose pkg matches the train APK's real package
are touched. Honest: FLAT/blank faces recorded as-is."""
import json, re, sys

BASE = "/home/z/my-project"
rows = [json.loads(l) for l in open(f"{BASE}/plugins/apps.jsonl") if l.strip()]

# label -> (registry_id, real_pkg, summary_line)
TRAIN = {
    "klondike":        ("GAME-014", "eu.veldsoft.free.klondike",
        "CONT-48 deep 121f: face=DARK uniq32=76 nonwhite=1.000 sha=a77038da303ed1b4 (was FLAT)"),
    "secusomemory":    ("GAME-074", "org.secuso.privacyfriendlymemory",
        "CONT-48 deep 121f: face=DARK uniq32=22 nonwhite=0.979 sha=807a0ccaf9b30d99 (was uniq=6)"),
    "secusodame":      ("GAME-088", "org.secuso.privacyfriendlydame",
        "CONT-48 deep 121f: face=DARK uniq32=64 nonwhite=1.000 sha=70033bc03f0392ed (was uniq=15)"),
    "secusosolitaire": ("GAME-092", "org.secuso.privacyfriendlysolitaire",
        "CONT-48 deep 121f: face=DARK uniq32=65 nonwhite=1.000 sha=aa53f6f172621982 (was uniq=15)"),
    "opmt":            ("GAME-017", "one.scarecrow.games.OPMT",
        "CONT-48 deep 121f: face=GREEN uniq32=373 nonwhite=1.000 sha=548a2d91ef9892fb rc=0 (was 8-frame capture)"),
    "chessjwtc":       ("GAME-055", "jwtc.chess",
        "CONT-48 deep 121f: face=FLAT uniq32=55 nonwhite=0.001 sha=3f7e670759b7c6a8 (honest re-read: deep run stays blank-field)"),
    "andstatus2048":   ("GAME-077", "org.andstatus.game2048",
        "CONT-48 deep 121f: face=blank uniq32=1 nonwhite=1.000 sha=b5a7a35d5fe0564b (no change vs FLAT)"),
    "ball2box":        ("GAME-007", "com.simondalvai.ball2box",
        "CONT-48 deep 121f: face=blank uniq32=1 nonwhite=1.000 sha=b5a7a35d5fe0564b (no change vs FLAT)"),
    "forkgram":        ("APP-016", "org.forkgram.classic",
        "CONT-48 deep 121f: face=FLAT uniq32=18 nonwhite=0.001 sha=c2e071714e97a3af rc=1 (first execution evidence; telegram-fork heavy load)"),
}

by_id = {r["i"]: r for r in rows}
applied, missing = [], []
for label, (rid, pkg, note) in TRAIN.items():
    r = by_id.get(rid)
    if not r:
        missing.append(rid); continue
    if str(r.get("pkg")) != pkg:
        missing.append(f"{rid}:pkg-mismatch {r.get('pkg')}!={pkg}"); continue
    r["ev"] = note
    if r.get("load") == "NOT_TESTED":
        r["load"] = "OBSERVED"
        r["gate"] = r.get("gate") or "L1"
    applied.append(rid)

with open(f"{BASE}/plugins/apps.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter
c = Counter(str(r.get("load")) for r in rows)
print("APPLIED:", applied)
print("MISSING:", missing)
print("load counts:", dict(c))
print("with-execution-evidence (not NOT_TESTED/BLOCKED):",
      sum(v for k, v in c.items() if k not in ("NOT_TESTED", "BLOCKED-DOWNLOAD", "BLOCKED")))
