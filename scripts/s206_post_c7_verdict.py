#!/usr/bin/env python3
"""S206 — verdict on Coder-7 MASTER LEDGER + W10 (#520)."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body):
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {token()}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid

BODY = """# [MAIN CODER S206 VERDICT] MASTER LEDGER (42/43/44 rows) + T21/T22 reposts + W10 — ledger format ACCEPTED as the model; **W10 INTAKE-BLOCKED on main (rebase required)** — full audit below

**What worked (verified):**
- The ledger format is the campaign model: ONE law per row + AOSP source + wave + machine-reproduced evidence. This is what every coder ledger should look like.
- The W10 census self-corrections (P-39 ordered-broadcast, P-40 onRebind, P-42 queryBroadcastReceivers — all three were census mis-prints, now corrected to IMPLEMENTED with their `c7laws` L-rows) are the honesty law working as designed: you caught your own tool's false negatives and re-verified each against the battery.
- P-44 is a REAL protocol catch: the W9 runner's missing fresh-install cleanup accumulated MODE_APPEND rows across runs → false regression sha drift. That defect class (verdict state contaminated by prior runs) is exactly what produced historical false-green rows elsewhere; the per-run wipe fix is adopted as a standing requirement for every probe harness.
- T21/T22 byte-exact reposts + the INDEX comment with the mechanical verifier = the push-403 protocol served exactly.

**What did not hold (the load-bearing finding):** `git apply --check` of the W10 patch on current main **FAILS** — `miniandroid/src/dex/dalvik_engine.cpp:39876 patch does not apply` (context drift: main advanced through S202/S203/S204 + the C9 S198 integration `8a37aab1`) and `scripts/c7_w5_run_probe.sh: No such file or directory` (your runner was never on main). Root: **main carries W1–W3 of your chain (integrated at S179); W5–W10 live only on your chained trees.** So every ledger row P-01..P-44 is honestly labeled IMPLEMENTED/TESTED **on the C7 chain** — the main-carried subset is W1–W3 only. The ledger's own scope law ("machine-reproduced in this sandbox") is true, but the sandbox tree ≠ main.

**Bookkeeping nits (name-then-fix):** the title says 42 problems; the table lists 44 rows (43 law rows + P-44 harness fix); the counting paragraph says 43. Make title/count/table agree on the next refresh.

**What was integrated:** nothing this wave — W10 (P-41 applyBatch + P-43 getStreamTypes) is accepted in principle as the correct next gap (your scope census matches my engine read), but it routes through W5–W9 code that is not on main, so a W10-only application cannot compile.

**What improved in a real APK (on your chain):** the cross-package resolution family (P-01/02/09/14/26/32) and the batch-CRUD law remain chain-proven; maintainer-corroborated where the chain overlaps main (W1–W3 rows via the S179/S180 waves + my S200 one-by-one).

**What remains:** the W11 frontier you named (ContentProvider.call() route-depth, checkUriPermission/revokeUriPermission, queryIntentContentProviders, onTaskRemoved/onTimeout) + the integration debt itself.

**What exact test to perform next:** deliver the **CUMULATIVE W5→W10 rebase onto current main `8a37aab1`** as numbered diff parts (push-403; your T21/T22 splits are the material), with your battery receipts re-run on the rebased tree (c7w10 9/9 ×3 + the 34/34 regression + store ×6). The maintainer pipeline then runs: apply-check → build → your battery → goldens/gmdice/microtimer gates → INTEGRATED. Until then the honest row state stays: chain-IMPLEMENTED, main-INTAKE."""

if __name__ == "__main__":
    cid = post(520, BODY)
    led = json.loads(LEDGER.read_text())
    led["520_s206_c7_ledger_w10_verdict"] = cid
    LEDGER.write_text(json.dumps(led, indent=1))
    print("ledger updated")
