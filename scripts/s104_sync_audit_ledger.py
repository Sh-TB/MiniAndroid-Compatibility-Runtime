#!/usr/bin/env python3
"""S104: sync docs/RESEARCH_500_AUDIT.json with the S104 ROOT-009 refresh
(R500-082/083/084/081 re-homed to ROOT-SWITCH-KEY-WIDENING; 082 L5)."""
import json

AUDIT = "/home/z/my-project/docs/RESEARCH_500_AUDIT.json"
UPD = {
    "R500-081": {"root_cluster": "ROOT-SWITCH-KEY-WIDENING", "evidence_level": "L2"},
    "R500-082": {"status": "REGRESSION_TESTED", "root_cluster": "ROOT-SWITCH-KEY-WIDENING",
                 "evidence_level": "L5"},
    "R500-083": {"root_cluster": "ROOT-SWITCH-KEY-WIDENING", "evidence_level": "L2"},
    "R500-084": {"status": "PARTIAL", "root_cluster": "ROOT-SWITCH-KEY-WIDENING",
                 "evidence_level": "L4"},
}
EVIDENCE_APPEND = {
    "R500-082": ("S104: root re-attributed to SWITCH-KEY-WIDENING (packed-switch key must "
                 "widen BYTE; was collapsing to 0 -> wrong branch). Commit 4feaaeda. "
                 "solitaire errors 12->0 (3/3 SHA 59fdbfcd60b86a23), battery 105/105. "
                 "Probe [S104-SW]: pre key=0/dest=5, post key=5/dest=11."),
    "R500-084": ("S104: shared root fixed by SWITCH-KEY-WIDENING (commit 4feaaeda); "
                 "lambda-specific corpus rerun pending -> PARTIAL."),
}
d = json.load(open(AUDIT))
for it in d["items"]:
    u = UPD.get(it["id"])
    if not u:
        continue
    it.update(u)
    if it["id"] in EVIDENCE_APPEND:
        ev = it.get("evidence")
        it["evidence"] = (ev + " | " if isinstance(ev, str) else "") + EVIDENCE_APPEND[it["id"]]
from collections import Counter
d["counts_by_status"] = dict(Counter(i["status"] for i in d["items"]))
json.dump(d, open(AUDIT, "w"), indent=1)
print("audit ledger synced:", d["counts_by_status"])
