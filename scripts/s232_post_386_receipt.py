#!/usr/bin/env python3
"""S232: post the wave-2 receipt on #386 (the historical-artifact queue)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S232 receipt (operator, main line) — the 964-report sanity queue EXECUTED: 2,216 violations -> 15 honest DEFERRED

**HEAD:** `6612b44d` (S232 wave 2, pushed). The wave-1 census (`evidence/s230/report_sanity_census.tsv`: 964 reports) is now processed end-to-end by a mechanical, self-verifying fixer.

## IMPLEMENTED — `tools/report_sanity_fix.py`

The mechanical counterpart of the S230 detector (`tools/report_sanity.py`): every action is re-measured by the repo's OWN detector and landed in a TSV ledger (per-file before/after violation counts), so the ledger is self-verifying. Modes: `--scan` (live repo scan), section-dedupe (this wave), `--sha` (provenance pass), `--offset/--limit` chunking (survives the constrained-CPU sandbox).

## FIXED (measured, not claimed)

| class | before | after | method |
|---|---|---|---|
| DUPLICATE_SCREENSHOT_EMBED | 717 (705 census + 12 post-census s211/s226 residuals) | **0** | later "Output Frame" sections embedding an already-embedded screenshot removed whole-section; kept sections byte-identical; distinct images never merged |
| MISSING_SCREENSHOT_SHA | 913 | **0** | the SHA256 provenance line derived from the ACTUAL retained file and appended to the kept section; **913/913 verified recorded-sha == on-disk sha** |
| MISSING_RUN_ID | 220 | **15** | run id derived from the report's OWN Session ID line (explicit provenance, not fabrication) for the 205 that carry one |

Live re-scan after the wave: **1,155 report.md files, 15 violations total** — all `MISSING_RUN_ID` on reports with no Session ID (recorded `DEFERRED_NO_SESSION_ID` with reasons in `evidence/s232/report_sanity_runid_ledger.tsv`; these 15 need the producing-session records, not a guess — no invented run ids).

## LEDGERS (evidence/s232/, registered in PATH_OWNERSHIP)

- `report_sanity_fix_ledger.tsv` — 964 rows (sections_removed, violations before/after, status per report)
- `report_sanity_sha_ledger.tsv` — 913 rows with the recorded sha + verification status
- `report_sanity_runid_ledger.tsv` — 220 rows (205 FIXED + 15 DEFERRED)
- `report_sanity_scan.tsv` — the wave's own live scan baseline

## PARTIAL (the remaining #386 queue, honest)

- The 15 DEFERRED run-id rows (above).
- The 45 PNG→JPEG `DEFERRED consumer:` rows from wave 1 stay deferred: their consumers are machine-generated registries (ARTIFACT_REGISTRY regenerates) — migrating them requires the registry regeneration pass, queued as the next mechanical wave.
- The contradictory-SUCCESS and APK-path-mismatch classes remain at 0 (W18 corrections landed them earlier); the detector now guards them continuously.

## POLICY (wave hygiene)

- The two new scripts converted to R11 repo-root discovery (the validator caught the machine-path literals — fixed, not allowlisted, since they are MAINTAINED tools).
- `evidence/s232` registered (approved_dirs + the wave exclusion pointer switched per the S231 amendment pattern); frozen snapshot re-baselined with two amendment rows (the s232 registration + the 14 gate-rerun screenshot/store additions from the pin-neutral reruns).
- Validator: **0 violations**, 5 pre-existing oversized-GIF warnings.
"""

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/386/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s232-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    out = json.loads(r.read().decode())
    print(f"posted #386 comment id={out['id']}")
