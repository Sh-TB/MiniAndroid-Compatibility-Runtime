#!/usr/bin/env python3
"""#595: post the S236 pre-merge audit evidence report (STOP-after-report)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path("/home/z/my-project")
CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines()
         if l.startswith("password=")][0]

BODY = """## S236 pre-merge audit — evidence report (the STOP-after-report deliverable)

**Main is UNTOUCHED** (`origin/main = ba184db9`, local head `74eb5efc`). All audit work lives on the disposable branch **`audit/s236`** (pushed): commits `536cd5ac` (the G1+G2 port) + `a8644248` (the battery) + the evidence commit. Rollback: nothing to roll back on main; the branch is disposable. Candidate binary sha16 **`f76b6df780c6d468`**.

### Baseline vs candidate matrix

| Gate | Baseline (ba184db9 lineage) | Candidate (audit/s236) | Verdict |
|---|---|---|---|
| S236 port battery | n/a (new) | **12/12 ×3 consecutive clean runs** | PASS |
| test-all | 31/31 | **32/32** (the new battery included) | PASS, zero regressions |
| check-source-parity | 75/75 | **75/75** | PASS |
| six-pin gmdice | 3891679d | 3891679d ×2-identical ×3 passes | HOLD byte-exact |
| six-pin microtimer | b39665f6 | b39665f6 ×3, 0-uncaught | HOLD byte-exact |
| six-pin unote | 3b8dcb0a | 3b8dcb0a (2 fresh + 1 cached) | HOLD |
| six-pin dooz | a0fae907 | a0fae907 ×2 fresh + 1× `d602648e` — **the S232-documented known-flaky face**, pre-existing | HOLD with the recorded flakiness |
| six-pin bouncy | 60182d11 (the S235-1 sandbox-boundary drift face) | 60182d11 ×3 fresh — UNCHANGED | neutral (no S236 movement) |
| six-pin tictactoe | cd-class noise (the S235-1 boundary drift: 3360830-byte uninitialized capture) | `cd1c71df` ×3 deterministic = the SAME noise class (3360829 bytes, ~2.07M px/frame diff) | neutral (per-binary noise bytes, same phenomenon) |

### Per-rule evidence (the ledger, source-verified)

- **SUPERSEDED (already on main, proven by coverage rows):** F-NEW-656 (UriMatcher #371), 657b (receiver-inclusive args, EXP-071 at `dalvik_engine.cpp:40192`), 661b (framework tables in EVERY classification, S138+/TRAIN-31), 662 (C013 per-view replay + F-NEW-421 clip).
- **PORTED + focused-tested (the 12-row battery, artifact SHA in `evidence/s236/`):** 655 (r9: the resolver law REACHES — vanilla was not-handled), 657 (r1: the declarer-cell hand-Dalvik row), 658 (r2a-c: real INSERT rowIds 1,2 + the row read back), 658b (r3: the heap-String unbox), 659/659b (r5/r6/r7: `(Unknown)`/`Cancel`/the negative throw).
- **AUDIT FINDINGS (pre-existing gaps the coverage rows exposed — fixed in the candidate):** ① F-NEW-656c: the #371 UriMatcher segment law gated on `*` only — an AOSP `t1/#` rule **never matched** (r10 proves the fix); ② F-NEW-658c: the #371 copy-ctor copied only the engine-side store, NOT the static flat mirror `db.insert` reads (r4 proves the fix). Both are exactness fixes for named contracts — no behavior rewrites.

### Regressions / confounders / blockers

- **No previously passing behavior regressed on the candidate** — the four non-GL pins hold byte-exact ×3; bouncy/ttt carry the PRE-EXISTING sandbox-boundary drift (control-proven in the S235-1 record; unchanged by this port).
- **Confounder:** the ttt noise capture is per-binary nondeterministic in BYTES but deterministic per binary — the same 3.3MB noise class, characterized, not counted as a regression.
- **Blockers (PENDING, outside the S236 port set):** ① the chess 2380-row seed completes only ~1 insert/run on a FRESH root — reproduced on the candidate (`chess_pgn.db games=1`, the REAL row): the first-draw `_fieldColor` NPE storm interrupts the seeding — the traversal-order first-draw guard is the lane's NEXT named law; ② OpenSudoku's full row census needs a deeper dedicated run (the cursor value path itself is carried by the S232 laws + the 658c fix); ③ the S235-2 GL re-pin wave (root-cause the boundary capture divergence) remains a separate follow-up.

### Minimal proposed merge sequence (AWAITING the separate explicit approval)

1. `audit/s236` → `main` (the two commits, merge or fast-forward — 3 files + tests).
2. The evidence registration commit (`evidence/s236` in PATH_OWNERSHIP, the wave switch).
3. The receipts (#588 + #595 cross-links).

**Stopping here per the issue: no merge, no push to main, no further main modification.** Raw logs: `evidence/s236/` on `audit/s236` (build ×7, test-all, parity, gate passes 1-3, chain_results.json)."""

req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/595/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOKEN}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s236-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    c = json.loads(r.read().decode())
print(f"report posted: comment id {c['id']} at {c['created_at']}")
