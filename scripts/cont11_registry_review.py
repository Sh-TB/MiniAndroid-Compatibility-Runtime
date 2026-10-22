#!/usr/bin/env python3
"""CONT-11: Full sweep of ALL registered problems (games + apps).
Goal: per-problem progress table + common-root families analysis."""
import json, collections, re, os

BASE = '/home/z/my-project'
with open(f'{BASE}/root_registry.json') as f:
    reg = json.load(f)

roots = reg['roots']
print(f"TOTAL ROOTS: {len(roots)}")

# --- 1. status distribution
by_status = collections.Counter(r.get('status', '?') for r in roots)
print("\n== BY STATUS ==")
for k, v in by_status.most_common():
    print(f"  {k}: {v}")

# --- 2. priority distribution
by_prio = collections.Counter(str(r.get('priority')) for r in roots)
print("\n== BY PRIORITY ==")
for k, v in by_prio.most_common():
    print(f"  {k}: {v}")

# --- 3. layer distribution
by_layer = collections.Counter(str(r.get('layer')) for r in roots)
print("\n== BY LAYER ==")
for k, v in by_layer.most_common():
    print(f"  {k}: {v}")

# --- 4. The OPEN problems (not fixed/verified)
OPEN_STATUSES = {'CLASSIFIED', 'OPEN', 'PARTIAL', 'PENDING', 'OBSERVED', 'BLOCKED', 'BLOCKED-BY-IDENTITY', 'SUPERSEDED'}
open_roots = [r for r in roots if r.get('status') in OPEN_STATUSES]
print(f"\n== OPEN/NON-FIXED ROOTS: {len(open_roots)} ==")

# print the most recent F-NEW roots (high numbered = newest frontier)
fnew = [r for r in roots if str(r.get('id','')).startswith('F-NEW')]
fnew.sort(key=lambda r: int(re.sub(r'\D','',r['id']) or 0), reverse=True)
print("\n== NEWEST 30 F-NEW ROOTS (id, status, title) ==")
for r in fnew[:30]:
    t = (r.get('title') or '')[:90]
    print(f"  {r['id']:14s} {r.get('status','?'):22s} {t}")

# --- 5. title-facing problems: scan for app/game names in titles
with open(f'{BASE}/docs/corpus/s82/title_registry.json') as f:
    titles = json.load(f)
print(f"\n== TITLE REGISTRY keys: {list(titles.keys())[:5] if isinstance(titles, dict) else 'list'} ==")
if isinstance(titles, dict):
    for k in list(titles.keys())[:3]:
        v = titles[k]
        print(f"  {k}: {str(v)[:200]}")
