#!/usr/bin/env python3
"""cont49_apply.py — apply CONT-49 train evidence to plugins/apps.jsonl.
STRICT laws (continuing cont48_apply2.py precedent):
  - exact pkg match only (from report.md Package line)
  - only rows with load==NOT_TESTED and no prior execution evidence string
    are upgraded -> OBSERVED (first-evidence law)
  - evidence string carries sha16 + face class + rc + F-016 honesty note
  - untouched: pkg dups, pkg-less rows, anything already evidenced
Zero-log: no run artifacts in git; this script + registry diff only."""
import json, re
from collections import Counter

BASE = "/home/z/my-project"
SUM = f"{BASE}/run/cont49/trains/summary.txt"
path = f"{BASE}/plugins/apps.jsonl"

# --- parse train results ---
trains = {}
for ln in open(SUM):
    m = re.match(r"TRAIN\|([^|]+)\|rc=(\d+)\|sha=([0-9a-f]*)\|(.+?)\|pkg=(.*)$", ln.strip())
    if not m:
        continue
    label, rc, sha, face, pkg = m.groups()
    trains[pkg.strip()] = dict(label=label, rc=int(rc), sha=sha, face=face.strip())

print("train rows parsed:", len(trains))

# --- registry ---
rows = [json.loads(l) for l in open(path) if l.strip()]
applied, skipped_dup, skipped_evid = [], [], []
seen_pkg_first = set()
for r in rows:
    p = str(r.get("pkg") or "")
    if p not in trains:
        continue
    t = trains[p]
    if p in seen_pkg_first:
        skipped_dup.append((r.get("i"), p))
        continue
    seen_pkg_first.add(p)
    if str(r.get("load")) != "NOT_TESTED" or r.get("ev"):
        skipped_evid.append((r.get("i"), p, r.get("load")))
        continue
    honest = "F-016 exception-honest(rc=1)" if t["rc"] != 0 else "rc=0"
    r["ev"] = (f"CONT-49 121f train: face={t['face']} sha={t['sha']} {honest}")
    r["load"] = "OBSERVED"
    applied.append((r["i"], p, t["face"][:40], t["sha"]))

# --- write back (only if changes) ---
if applied:
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("applied:", len(applied))
for a in applied:
    print("  +", a)
print("skipped (already evidenced):", len(skipped_evid))
print("skipped (pkg dup):", len(skipped_dup))

# --- post counts ---
rows2 = [json.loads(l) for l in open(path) if l.strip()]
ld = Counter(str(r.get("load") or "NOT_TESTED") for r in rows2)
print("post load state:", dict(ld))
