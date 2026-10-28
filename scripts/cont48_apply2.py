#!/usr/bin/env python3
"""cont48_apply2.py — fix the duplicate GAME-074 registry defect (two rows
share id GAME-074: org.secuso.privacyfriendlymemory + eu.quelltext.counting)
and apply the two remaining train evidence rows by exact pkg.
Structural fix: renumber the evidence-less eu.quelltext.counting row to the
next free GAME-0xx id. Evidence rows untouched."""
import json
from collections import Counter

BASE = "/home/z/my-project"
path = f"{BASE}/plugins/apps.jsonl"
rows = [json.loads(l) for l in open(path) if l.strip()]

# --- structural: duplicate-id repair ---
ids = [r["i"] for r in rows]
dups = [i for i, n in Counter(ids).items() if n > 1]
print("duplicate ids:", dups)
seen = set()
free = None
n = 1
def next_free():
    global n
    while f"GAME-{n:03d}" in set(ids):
        n += 1
    nid = f"GAME-{n:03d}"
    n += 1
    return nid

renumbered = None
for r in rows:
    if r["i"] in seen:
        # second occurrence: renumber (the counting row has no evidence)
        old = r["i"]
        r["i"] = next_free()
        renumbered = (old, r["i"], r.get("pkg"))
    seen.add(r["i"] if "i" in r else r.get("i"))
print("renumbered:", renumbered)

# --- evidence apply by exact pkg ---
TRAIN = {
    "org.secuso.privacyfriendlymemory":
        "CONT-48 deep 121f: face=DARK uniq32=22 nonwhite=0.979 sha=807a0ccaf9b30d99 (was uniq=6)",
    "jwtc.android.chess":
        "CONT-48 deep 121f: face=FLAT uniq32=55 nonwhite=0.001 sha=3f7e670759b7c6a8 (honest re-read: deep run stays blank-field)",
}
applied = []
for r in rows:
    p = str(r.get("pkg"))
    if p in TRAIN:
        r["ev"] = TRAIN[p]
        if r.get("load") == "NOT_TESTED":
            r["load"] = "OBSERVED"
            r["gate"] = r.get("gate") or "L1"
        applied.append((r["i"], p))
print("applied:", applied)

with open(path, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# --- final census ---
rows2 = [json.loads(l) for l in open(path) if l.strip()]
ids2 = [r["i"] for r in rows2]
c = Counter(str(r.get("load")) for r in rows2)
print("total:", len(rows2), "unique ids:", len(set(ids2)),
      "dup-free:", len(ids2) == len(set(ids2)))
print("load counts:", dict(c))
print("with-execution-evidence:",
      sum(v for k, v in c.items() if k not in ("NOT_TESTED", "BLOCKED-DOWNLOAD", "BLOCKED")))
