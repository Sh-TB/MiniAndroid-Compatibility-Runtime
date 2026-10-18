#!/usr/bin/env python3
"""CONT-87 bookkeeping reconciliation: close the four pre-existing
registry-validator debts (V1/V7/V8/V9) alongside the F-NEW-395 landing.
No root rows are touched by this script except the open_frontiers list —
which is re-derived from ACTUAL statuses (terminal rows leave the list)."""
import json
from collections import Counter

REG = "canonical/root_cause_registry.json"
d = json.load(open(REG))
rows = d["roots"]
n = len(rows)

# ── V1/V8: reconcile every total/count field with the actual row count ──
d["total"] = n
d["count"] = n
d["total_roots"] = n
d.setdefault("summary", {})["total_roots"] = n
d["summary"]["total"] = n

# ── status_counts + summary.by_status refreshed from the rows ──
sc = Counter(r.get("status", "UNCLASSIFIED") for r in rows)
d["status_counts"] = dict(sc)
d["summary"]["by_status"] = dict(sc)
d["summary"]["verified_fixed"] = sc.get("VERIFIED-FIXED", 0) + \
    sc.get("ROOT-CAUSED-FIXED", 0)

# ── V9: open_frontiers re-derived from actual statuses ──
TERMINAL = {
    "VERIFIED-FIXED", "ROOT-CAUSED-FIXED", "ROOT-CAUSED-CLOSED",
    "SUPERSEDED-BY-EVIDENCE", "NOT-APPLICABLE", "REJECTED_WITH_REASON",
    "ALREADY_FIXED_AND_TESTED", "ALREADY_TRACKED_OR_DUPLICATE",
    "STALE_OR_SUPERSEDED", "USED_BY_EXECUTION", "CLOSED",
}
open_frontiers = [
    r["id"] for r in rows
    if r.get("status") not in TERMINAL
]
d["summary"]["open_frontiers"] = open_frontiers
# the legacy top-level open_frontiers list (if present) gets the same truth
d["open_frontiers"] = open_frontiers

d["summary"]["last_updated"] = "2026-10-18T05:30:00Z"
d["summary"]["note"] = (
    "CONT-87 reconciliation: totals/status_counts/open_frontiers re-derived "
    "from the 702 rows (V1/V8/V9); F-NEW-395 ROOT-CAUSED-FIXED this wave."
)

json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)

import shutil
shutil.copy(REG, "root_registry.json")

print("rows:", n, "| open_frontiers:", len(open_frontiers))
print("top statuses:", dict(list(sc.items())[:8]))
