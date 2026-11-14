#!/usr/bin/env python3
"""#595: post the REQUIRED initial plan + inventory before any audit work."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines()
         if l.startswith("password=")][0]

BODY = """## S236 pre-merge audit — initial plan and inventory (per the issue's required first response)

**Status: AUDIT STARTED — no merge, no reset/rebase/force-push, no main modification. All audit work happens on a disposable branch/worktree from the recorded baseline. This comment is the required pre-execution inventory; the evidence report follows separately. STOP-after-report is acknowledged.**

### 1. Exact baselines (recorded BEFORE any work)

| ref | SHA | state |
|---|---|---|
| local `main` HEAD | `74eb5efc` | 1 boundary-sweep commit (UUID message) on top of `ba184db9`, adding ONLY `scripts/post_pending_comment.py` (77 lines, benign) — LOCAL-ONLY, not pushed |
| pushed `origin/main` | `ba184db9` | the S235-1 closeout state, clean tree |
| backup tags | `audit/s236-baseline` = `ba184db9` (pushed), `audit/s236-baseline-head` = `74eb5efc` (pushed) | recoverable rollback references; `main` itself untouched |
| working tree | 0 dirty files, tree `5eb43891f82c` | recorded |

**Ancestry verified by DAG (not labels):** `100bc576` → `b9a099d2` → `6be77b40`; `ba184db9` → `100bc576`. S235-1 = `b9a099d2`+`100bc576` — matches the lane's g3 recovery comment exactly.

### 2. S236 candidate source commits — BLOCKED (honest)

**No S236 source commits exist in this repository** — checked all local refs (`git log --all`) and every remote branch (`cont24/skeleton-light-experiment`, `gh-pages`, `main`). The lane's g2/g3 builds (`974904497c6f862b` / `36aba58ae8294ae3` / `c506d0a2002c9758`) were local to the lane worktree and were wiped in the third recycle (the lane's own g3 comment); the lane's `S236` commit lives in the LANE's local repo, not here. Per the issue's gate #4/#5: direct-source audit is **BLOCKED** and nothing missing is converted to PASS. The audit candidate is therefore a **fresh comment-derived re-implementation on an audit branch** (the proven S235-1 precedent: laws re-implemented from the posted comment definitions, every port commit SHA recorded in the report).

### 3. Rule-level overlap inventory (main @ `74eb5efc` vs the S236 port set) — initial classification

| Rule | Main state (source-verified) | Initial class |
|---|---|---|
| F-NEW-655 `Activity.managedQuery` | **absent** (0 hits) | PENDING port |
| F-NEW-656 `UriMatcher` | **present** — `dalvik_engine.cpp:46446` "#371 PHASE B1" ctor/addURI/match with routing state | SUPERSEDED (verify extent) |
| F-NEW-657 declarer-keyed static cells | `resolved_field_declarer` exists but only in the field-hook path; the sget/sput storage-cell key construction needs the audit read | PARTIAL — audit decides |
| F-NEW-657b receiver-inclusive bridge args | **present** — `dalvik_engine.cpp:40192` "instance methods: args[0] is the receiver (EXP-071 Phase 8 law)"; the S235-1 cursor-adapter law already uses it | SUPERSEDED |
| F-NEW-658 `SQLiteDatabase.insert*` | **absent** (`insertOrThrow`/`insertWithOnConflict` 0 hits; the sqlite shadow covers SELECT/rawQuery from S232) | PENDING port |
| F-NEW-658b/c `ContentValues` mirror | present (`sqlite_shadow.cpp`, `android_shadows.cpp`) but the heap-String unbox (`__string_value__`) and copy-ctor flat-mirror semantics need the audit read | PARTIAL — audit decides |
| F-NEW-659/659b framework string ids | `android.R.*`/public.xml references exist; the GATE-A `Resources.getString` resolution table needs the audit read | PARTIAL — audit decides |
| F-NEW-660 `StringBuilder.indexOf/delete(int,int)` | `deleteCharAt` present (bounds-checked, `dalvik_engine.cpp:52601`); `indexOf` hit at `:88439` is another class's — the `AbstractStringBuilder` `indexOf(String[,from])`/`delete(int,int)` pair needs the audit read | PARTIAL — audit decides |
| F-NEW-661b ancestry-table unconditional consult | `is_subclass_of_impl` present (`dalvik_engine.cpp:2084`) as "a PURE function of the class tables" — whether the framework ancestry table is consulted unconditionally vs DEX-shadowed needs the audit read | PARTIAL — audit decides |
| F-NEW-662 `drawChild` save/clipRect/translate/restore | present in 3 files — the exact transform sequence needs the audit read | PARTIAL — audit decides |

Duplicate/conflict findings so far: **656 and 657b are already on main** — the port set must NOT re-add them (the S235-1 wave's functional g1/g2 coverage is the reason). This table is the seed of ledger B; every PARTIAL row gets a source read + focused test during the audit.

### 4. Available / missing baseline artifacts

- **Present:** S235 evidence (`evidence/s235/S235_LANE_INTEGRATION.json`), the six-pin gate JSON + runs, the 17/17 battery, test-all logs, parity, the sandbox-boundary control proof (laws-free binary at `6be77b40`).
- **Missing/BLOCKED:** all lane-side raw artifacts (g2/g3 build trees, logs, binaries) — lost in the lane's recycles; only the posted comments remain. Audit evidence classes for the port therefore start at IMPLEMENTED/TESTED, never OBSERVED-on-lane-build.

### 5. Test commands and expected resources

- Port battery (new, `tests/s236_*_test.cpp` rows): build ~10 min per iteration (`-j1`, OOM-bounded — the 4 GB cgroup law), runs seconds.
- `make test-all` (31 TUs + new): ~12 min. `check-source-parity`: <1 min.
- Six-pin gate (`S207_PHASE=all python3 scripts/s207_gate.py`): ~20-25 min per pass; ×3 clean passes ≈ 70 min.
- Per-app chain runs (Chess/OpenSudoku/gmdice, fresh+seeded roots): ~1-3 min each.
- Total estimated: **2.5-4 h** including repeats and first-divergence captures.

### 6. Risk-ranked dependency map

- **HIGH blast radius:** 657 (static-cell keying — every class), 661b (ancestry consult — every class resolution), 662 (drawChild — every view composite), 659 (Resources.getString — every app's string lookup).
- **MEDIUM:** 658b/c (shared ContentValues path), 660 (core StringBuilder ops), 658 (provider INSERT path shared by any content app).
- **LOW:** 655 (legacy managedQuery forward), 656/657b (already on main — no change).
- Known environment confounder (pre-existing, control-proven): the two GL pins (bouncy/ttt) moved at the sandbox recycle boundary — reproduced byte-exact on a laws-free control binary; recorded in S207_GATE.json + evidence/s235. The audit treats them as known-drift baselines, NOT as S236 regressions, and re-proves neutrality with controls against the untouched baseline if they move again.

### 7. Blockers

1. No S236 source commits reachable (see §2) — the candidate is comment-derived; classification stays honest.
2. The GL pin drift is pre-existing at the boundary — gates use the control-proof disposition, and the S235-2 re-pin wave remains a separate follow-up.
3. The boundary sweep has one remaining leak (this turn it absorbed `scripts/post_pending_comment.py`) — recorded only; the ignore-list fix is post-approval work since it would modify main.

### 8. Execution order (after this comment)

Worktree + `audit/s236` branch from `audit/s236-baseline-head`; port in 4 small groups, one commit each: **G1** content/sqlite (655, 658, 658b/c) → **G2** resources/strings (659/659b, 660) → **G3** engine static identity (657) → **G4** render/ancestry (661b, 662); focused test rows after each group; then the full battery + parity + six-pin ×3 + the per-app execution-chain verification (Chess, OpenSudoku, gmdice) + the 2380-row/onDraw reproduction from a clean db; any break gets a first-divergence trace AND a control run against the untouched baseline before it is called a regression. The evidence report (machine + human readable, artifact SHAs, rollback reference, minimal proposed merge sequence) is posted here, and the audit STOPS — no merge until the separate explicit approval this issue requires."""

req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/595/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOKEN}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s236-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    c = json.loads(r.read().decode())
print(f"plan posted: comment id {c['id']} at {c['created_at']}")
