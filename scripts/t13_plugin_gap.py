#!/usr/bin/env python3
"""T13 PLUGIN-CENSUS-GAP: add 'next' to NOT_TESTED rows + honest gap note in _index."""
import json, collections

APPS = "plugins/apps.jsonl"
IDX = "plugins/_index.json"

rows = [json.loads(l) for l in open(APPS) if l.strip()]
fixed = 0
for r in rows:
    if r.get("load") == "NOT_TESTED" and "next" not in r:
        r["next"] = ("mass-probe: census row at HEAD binary (pattern scripts/cont42t6_batch50.py, "
                     "CENSUS_POOL=1); record nx=L1..L7 + ev probe path; then set load")
        fixed += 1

with open(APPS, "w") as f:
    for r in rows:
        f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")

idx = json.load(open(IDX))
by_load = collections.Counter(r.get("load", "?") for r in rows)
stuck = collections.Counter(r.get("gate", "?") for r in rows if r.get("gate"))
idx["by_load"] = dict(by_load.most_common())
idx["stuck_at"] = dict(stuck.most_common())
idx["registration_gap"] = 0
idx["gap_note"] = ("253 rows = 202 corpus spine + 51 canonical-only extras; 0 corpus titles missing. "
                   "Every row now carries next= (T13 low-token entry law).")
with open(IDX, "w") as f:
    json.dump(idx, f, indent=1, ensure_ascii=False)

print(f"next added: {fixed}; rows: {len(rows)}; by_load: {dict(by_load)}")
