#!/usr/bin/env python3
"""Main Coder — Phase B: fetch comments for high-signal issues (recently
updated, most-discussed, closed-with-content, and known hubs)."""
import json
import sys

sys.path.insert(0, "scripts")
from mc_phase_a import paginate  # noqa: E402
import mc_phase_a  # noqa: E402

OUT = "docs/project-intelligence/raw"

iss = json.load(open(f"{OUT}/issues_all.json"))
# high-signal selection: any issue with >=4 comments OR updated in the last
# 10 days OR in an explicit target list
targets = {707, 712, 713, 714, 715, 711, 716, 709, 710, 597, 627, 612, 626, 625, 596, 472}
sel = []
for i in iss:
    if i["n"] in targets or i["comments"] >= 4 or i["updated"] >= "2026-11-18":
        sel.append(i["n"])
print(f"fetching comments for {len(sel)} issues")

mc_phase_a.OUT = OUT
store = {}
for n in sel:
    try:
        cs = paginate(f"issues/{n}/comments")
        store[n] = [{
            "user": c["user"]["login"], "at": c["created_at"][:16],
            "len": len(c.get("body") or ""),
            "body": (c.get("body") or "")[:1200],
        } for c in cs]
    except Exception as e:
        print(f"  #{n}: {e}")
        store[n] = []
json.dump(store, open(f"{OUT}/comments_hot.json", "w"))
print(f"stored comments for {len(store)} issues, total {sum(len(v) for v in store.values())}")
