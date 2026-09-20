#!/usr/bin/env python3
"""build_failure_index.py — §5 failure index (machine-readable, queryable).

Converts root_registry.json (372 investigation roots) into the campaign's
failure-record schema:
  {failure, apk, package, source_commit, runtime_commit, method, api,
   root_cause, expected, observed, pixel_diff, reproducible, evidence}
Fields unavailable in the registry are recorded as null — no invented data.
Cross-links every F- law from the session worklogs where the evidence string
carries them.
"""
import json
import re
import time
from pathlib import Path

ROOT = Path("/home/z/my-project")
REG = ROOT / "root_registry.json"
OUT = ROOT / "docs" / "foundation" / "failure_index.json"

RUNTIME_COMMIT = None
try:
    RUNTIME_COMMIT = subprocess_head()
except Exception:
    pass


def subprocess_head():
    import subprocess
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def main():
    reg = json.loads(REG.read_text())
    records = []
    for r in reg.get("roots", []):
        ev = r.get("evidence", "") or ""
        if not isinstance(ev, str):
            ev = json.dumps(ev, ensure_ascii=False)
        f_laws = sorted(set(re.findall(r"F-\d+[a-z]?", ev)))
        # apk mentions (canonical names)
        apk = None
        m = re.search(r"(dooz|tripeaks|fishrings|opmt|bouncy|stopwatch|"
                      r"microtimer|unote|gmdice|tictactoe|telegram)",
                      ev, re.I)
        if m:
            apk = m.group(1).lower()
        rec = {
            "failure": r.get("id"),
            "status": r.get("status"),
            "priority": r.get("priority"),
            "apk": apk,
            "source_commit": None,       # registry carries no source pin
            "runtime_commit": r.get("commit"),
            "method": None,
            "api": None,
            "root_cause": ev or None,
            "expected": None,
            "observed": r.get("missing") or None,
            "pixel_diff": None,
            "reproducible": None,
            "evidence_next": r.get("next") or None,
            "f_laws": f_laws,
        }
        records.append(rec)

    OUT.write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_head": RUNTIME_COMMIT,
        "source": "root_registry.json (372-root investigation registry)",
        "schema_note": "null = not recorded in the registry — never invented",
        "status_vocabulary": reg.get("summary", {}).get("status_vocabulary"),
        "count": len(records),
        "failures": records,
    }, indent=1))
    print(f"failure_index: {len(records)} records")


if __name__ == "__main__":
    main()
