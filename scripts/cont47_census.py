#!/usr/bin/env python3
"""CONT-47: real census of plugins/apps.jsonl — the «چند داد برنامه» answer."""
import json, collections, sys

path = "/home/z/my-project/plugins/apps.jsonl"
rows = []
with open(path) as f:
    for ln, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            print(f"BAD-LINE {ln}: {e}", file=sys.stderr)

print(f"TOTAL={len(rows)}")
print("\n== load ==")
for k, v in collections.Counter(r.get("load", "?") for r in rows).most_common():
    print(f"  {k:12s} {v}")
print("\n== gate ==")
for k, v in collections.Counter(str(r.get("gate") or "?") for r in rows).most_common():
    print(f"  {k:8s} {v}")
print("\n== fam ==")
for k, v in collections.Counter(str(r.get("fam") or "?") for r in rows).most_common():
    print(f"  {k:8s} {v}")

# gates L0..L7 ladder: what counts as "کامل"
def ladder(g):
    return g if g else "?"
print("\n== gate ladder ==")
for g in ["L0","L1","L2","L3","L4","L5","L6","L7"]:
    n = sum(1 for r in rows if r.get("gate")==g)
    if n: print(f"  {g}: {n}")

# the highest-gate games (closest to کامل)
print("\n== TOP-20 by gate (deepest progress) ==")
def gk(r):
    g = r.get("gate") or "L0"
    try: return int(g[1:])
    except: return -1
for r in sorted(rows, key=gk, reverse=True)[:20]:
    print(f"  {r.get('i'):10s} {r.get('t','')[:38]:40s} gate={r.get('gate')} load={r.get('load')} n={str(r.get('n'))[:60]}")
