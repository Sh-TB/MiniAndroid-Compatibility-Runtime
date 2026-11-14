#!/usr/bin/env python3
"""S235: register evidence/s235 as the new wave-evidence area.

The S234 amendment pattern: switch wave_evidence_registered to the new wave
dir (the validator excludes it from the frozen evidence snapshot), add the
approved_dirs entry, re-baseline frozen_snapshot.evidence with the s234 wave
files back inside, and append the amendment row. Run AFTER evidence/s235's
files exist and the six-pin gate rerun has regenerated its s207 children.
"""
import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REG = BASE / "docs" / "PATH_OWNERSHIP.json"

def tracked_files():
    out = subprocess.run(["git", "-C", str(BASE), "ls-files"],
                         capture_output=True, text=True, check=True)
    return [l for l in out.stdout.splitlines() if l]

reg = json.loads(REG.read_text())
if any(a == "evidence/s235" for a in reg["approved_dirs"]):
    print("already registered — nothing to do")
else:
    # 1. approved_dirs entry (the s234 pattern)
    idx = reg["approved_dirs"].index("evidence/s234")
    reg["approved_dirs"].insert(idx + 1, "evidence/s235")
    # 2. wave exclusion switch
    reg["wave_evidence_registered"] = {
        "path": "evidence/s235",
        "owner": "S235 (#588 runtime-lane integration: F-NEW-639..650)",
        "approved_in": "#588 lane wave receipt flow (S235-0/S235-1 commits)",
        "expected_classes": "json, txt, md",
        "note": "registered at wave start (S214 default-deny law); "
                "JSON law record + battery log, no screenshots",
    }
    # 3. frozen snapshot re-baseline: s234 files back inside, s235 outside
    files = tracked_files()
    members = sorted(
        f for f in files
        if f.startswith("evidence/")
        and not f.startswith("evidence/s235/"))
    sha = hashlib.sha256("\n".join(members).encode()).hexdigest()
    reg["frozen_snapshot"]["evidence"] = {
        "tracked_file_count": len(members),
        "snapshot_sha256": sha,
    }
    # 4. amendment row
    reg["frozen_snapshot_amendments"].append({
        "area": "evidence",
        "date": "2026-11-14",
        "wave": "S235 (#588 runtime-lane integration F-NEW-639..650)",
        "reason": "evidence/s235 registered as the new wave evidence area "
                  "(the lane-law battery record + gate rerun note); wave "
                  "exclusion switched from evidence/s234; snapshot "
                  "count+sha re-baselined with the s234 wave files back "
                  "inside and the s235 wave files outside; the six-pin "
                  "gate rerun regenerated the s207 run children in place "
                  "(pin-neutrality proof, byte-exact pins)",
        "ledger": "evidence/s235/S235_LANE_INTEGRATION.json",
    })
    REG.write_text(json.dumps(reg, indent=1) + "\n")
    print(f"registered; frozen evidence re-baselined: {len(members)} files")
