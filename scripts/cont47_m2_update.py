#!/usr/bin/env python3
"""CONT-47 M2 strict registry update: 5 newly-unlocked trains, exact-pkg law.
One label per row; sha16 face + honest class in the note."""
import json

ROWS = {
    "org.asafonov.weather": ("3700fb5b4449dbec", "RENDERED (189 uniq, nonwhite=1.0)"),
    "com.itsfrz.tictactoe": ("d5a4e46e3a10d401", "FLAT (uniq=1)"),
    "com.joeld.minesweeper": ("4cfe98899146f6dc", "FLAT (uniq=1)"),
    "com.sidhant.puzzle": ("395a9d9f910445e2", "FLAT (uniq=1)"),
    "de.georgsieber.ballbreak": ("c623631d892b5854", "RENDERED (206 uniq, nonwhite=1.0)"),
}

path = "/home/z/my-project/plugins/apps.jsonl"
rows = [json.loads(l) for l in open(path) if l.strip()]
hit = 0
for r in rows:
    pkg = str(r.get("pkg") or "")
    if pkg in ROWS and str(r.get("load")) in ("NOT_TESTED",):
        sha, cls = ROWS[pkg]
        r["load"] = "OBSERVED"
        r["gate"] = "L1"
        r["ev"] = f"CONT-47 M2 train 121f face={sha} {cls}"
        r["next"] = "L2+ interactive/probe wave"
        hit += 1
        print(f"row {r.get('i')} {r.get('t')} <- {pkg} OBSERVED {sha} {cls}")
with open(path, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("applied:", hit, "/ 5 expected")
