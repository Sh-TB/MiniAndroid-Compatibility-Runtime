#!/usr/bin/env python3
"""s92_registry_reclassify.py — S92 §32/§33: apply the S91-claim audit to
the canonical registry WITHOUT deleting history.

For each of the 12 GIF-claimed titles the canonical record gains:
  s92_reclassification: {previous_status, fresh_verdict, reclassified_to,
                         reason, verdict_file, run_dir, session: "S92"}
The record's status field moves to the S92 verdict level, but the
strongest public promotion levels (VISUALLY_VERIFIED and above) are only
candidate_* until the §29 human-review gate — a verifier alone cannot
bestow the strongest public level.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

REGISTRY = os.path.join(REPO, "docs", "evidence", "canonical",
                        "registry.json")
AUDIT = os.path.join(REPO, "run", "s92pilot",
                     "REPEATABILITY_AND_CLAIMS.json")

PROMOTE_GATE = ("candidate_VISUALLY_VERIFIED",
                "candidate_INTERACTION_VERIFIED")


def main():
    audit = json.load(open(AUDIT))["s91_claim_audit"]
    reg = json.load(open(REGISTRY))
    titles = reg.get("titles")
    container = titles if isinstance(titles, list) else None
    if container is None:
        raise SystemExit("registry.json layout changed — no titles[] list")
    by_pkg = {t.get("package"): t for t in container}
    changed = 0
    for a in audit:
        t = by_pkg.get(a["package"])
        if t is None:
            print("WARN: no canonical record for", a["package"])
            continue
        target = a["reclassification"]
        if target in PROMOTE_GATE:
            status = target  # candidate_ prefix: §29 gate visible in-place
        else:
            status = target
        t["status"] = status
        t["s92_reclassification"] = {
            "previous_status": a["previous_status"],
            "fresh_verdict": a["fresh_verdict"],
            "reason": a["reason"],
            "verdict_file": os.path.relpath(a["evidence"]["verdict"], REPO),
            "run_dir": os.path.relpath(a["evidence"]["run_dir"], REPO),
            "session": "S92",
            "human_review": "PENDING (S92 §29 gate before public promotion)",
        }
        changed += 1
    with open(REGISTRY, "w") as f:
        json.dump(reg, f, indent=1, sort_keys=True)
    print(f"reclassified {changed}/{len(audit)} canonical records")


if __name__ == "__main__":
    main()
