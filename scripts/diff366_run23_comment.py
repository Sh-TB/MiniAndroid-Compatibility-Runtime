#!/usr/bin/env python3
"""DIFFERENTIAL-366 — evidence-integrity correction comment (continuation §0).

Discloses the run1-only discrepancy that existed at first publication and
documents its closure via option A: the missing run2/run3 for microtimer and
dooz were EXECUTED and are byte-identical; all ledgers updated; no residue.
"""
import json, subprocess, sys

BODY = r"""
# EVIDENCE-INTEGRITY CORRECTION + CLOSURE (continuation §0 — option A)

**Disclosure.** The first publication of this ledger (row 18) claimed "4 working + 5 white,
runs 1–3 byte-identical each". That claim was **overbroad for 2 of the 11 pipeline apps**:
`docs/DIFFERENTIAL_EVIDENCE_INDEX.jsonl` listed only `run1` for **MicroTimer
`dubrowgn.microtimer`** (canonical working set) and **dooz `io.github.yamin8000.dooz`**
(Compose control) — their pipeline rows had `three_run=False`. The discrepancy is real and
was not hidden; this comment is the same-Issue correction record.

**Resolution — option A (execute the missing runs, make the stronger claim true).**
`scripts/diff366_run23.py` re-ran the canonical protocol on CURRENT HEAD
`9289177d`, same binary sha256-16 `4b2db3540575b1c4`, same per-app stores, source APKs
still hidden (`run/diff366/hidden_sources/`), `pkgaudit` live re-hash match before every run:

| App | identity (live = installed = source) | run1 | run2 | run3 | verdict | first divergence |
|---|---|---|---|---|---|---|
| MicroTimer | `79c6f730…fd19828` ✓ pkgaudit ✓ | `da73010a37dd0189…` | identical | identical | REAL_APP_CONTENT | none (working) — stable |
| dooz | `299eab21…1b362b` ✓ pkgaudit ✓ | `d602648e8e401895…` | identical | identical | DEFAULT_BACKGROUND_ONLY | COMPOSE (ComposeView not in class index) — stable |

All four new runs: screenshot SHA byte-identical to run1; rc consistent (microtimer rc=0 ×3,
dooz rc=1 ×3 — same as its run1); **no NONDETERMINISTIC divergence**. Per-run trace SHAs
recorded in `DIFFERENTIAL_WORKING_VS_WHITE.jsonl` (`trace_shas` field) and
`run/diff366/stage_matrices.json` (`_run23_closure`).

**Ledgers updated (contradiction removed, not edited around):**
- `docs/DIFFERENTIAL_WORKING_VS_WHITE.jsonl` — both rows now `reproducibility: 3-run
  byte-identical (run1/run2/run3)` + `three_run_shas` + `trace_shas`; closure note appended.
- `docs/DIFFERENTIAL_EVIDENCE_INDEX.jsonl` — both entries now `runs: [run1, run2, run3]`
  with per-run artifact lists.
- `docs/DIFFERENTIAL_WORKING_VS_WHITE.md` §10 — table now lists all 11 apps × 3 runs and
  carries the closure paragraph (what was overclaimed, why, how it was fixed).
- Artifacts committed: `evidence/diff366/final/{microtimer_dubrowgn.microtimer,
  dooz_io.github.yamin8000.dooz}/run2,run3/` (full artifact sets).

**Row 18 status (restated with exact evidence):** STATUS — VERIFIED (post-closure). RESULT —
4 working + 5 white + 2 controls, runs 1–3 byte-identical each, first divergence stable
everywhere. EVIDENCE — §10 table (11 rows), `three_run_shas`/`trace_shas` in the JSONL,
`run23` artifact directories, `scripts/diff366_run23.py` provenance.

Continuation item §0 is CLOSED by execution. The generic-fix campaign rows (§22) remain the
open frontier and are addressed by the continuation waves at the new HEAD.
"""

def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/366/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])

if __name__ == "__main__":
    main()
