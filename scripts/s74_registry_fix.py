#!/usr/bin/env python3
"""S74 registry hygiene: back-register F-120 (S66 button-gravity law, cited in
S70_REPORT/S67_RECON but absent from root_registry.json — found by the new S74
validator) and repair the stale summary totals (roots list = 396, summary said
372). Append-only in spirit: no existing entry is modified."""
import json, collections

P = "/home/z/my-project/root_registry.json"
d = json.load(open(P))
ids = {x.get("id") for x in d["roots"]}
if "F-120" not in ids:
    d["roots"].append({
        "id": "F-120",
        "status": "VERIFIED-CORRECT",
        "priority": "P2",
        "title": "Button default gravity law (TextView/Button gravity per AOSP)",
        "fg": True,
        "first_seen": "S66 visual forensics (289e33d3)",
        "session": "S74-backreg",
        "evidence": "Law named and applied since S66 (S67_RECON: HEAD 289e33d3 'F-120 button-gravity law'); cited among grep-verified upstream oracle laws in docs/foundation/S70_REPORT.md section 2 (the oracle file itself pins F-135/F-136 records). Back-registered by the S74 compatibility-graph validator, which now fails on generic LAW-F* knowledge records missing from this registry.",
    })
    print("F-120 back-registered")
else:
    print("F-120 already present")
n = len(d["roots"])
d["total"] = n
d["summary"]["total_roots"] = n
d["summary"]["last_updated"] = "S74 2026-09-21"
d["summary"]["note"] = (d["summary"].get("note", "") + " | S74: repaired stale summary totals (was 372 vs actual roots list); back-registered F-120 (S66 law) after validator gap detection.").strip(" |")
json.dump(d, open(P, "w"), indent=1)
print("registry now:", n, "roots; summary.total_roots =", d["summary"]["total_roots"])
