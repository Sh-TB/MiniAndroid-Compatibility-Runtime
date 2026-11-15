#!/usr/bin/env python3
"""The S239 group receipt -> #588 (hub) + the SQLQB faces receipt -> #592."""
import json, subprocess, urllib.request
CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B588 = """## S239 wave-stack audit receipt (main-coder) — the 30-issue sweep + the 7-row content-face battery + the first real LAW-001 corpus step

**main = `b3cd8548`** (origin/main verified via ls-remote; fast-forward over 3ad1d4eb).

### 1. The 30-issue id sweep (#558..#589)
Every open transfer/wave issue's law ids were grepped against main (`s239_audit_sweep.py`, the verdict JSON rides the commit). Verdict classes:
- **id-present**: the majority of the flagged families (F-NEW-660/658/659 family, R-NEW-4xx, EXP-0xx…).
- **id-absent but content PRESENT** (the repo's established naked-comment pattern — the false-missing set, disambiguated by content checks): `F-NEW-629 getSupportFragmentManager` (13 content hits), `F-NEW-631/635` (implemented under other ids — the S238 audit's findings), `F720` (the dooz post-nav zombie probe, dalvik_engine.cpp:28730), the W17-W20 `F-C4-6xx` blocks (the content faces live in the engine without their issue ids).
- **content-face rows landed this wave** (below) so the flagged set now carries REAL bridge-level proof, not just source greps.

### 2. The s239 battery (tests/s239_wave_stack_audit_test.cpp, TEST_LAW) — 7/7 PASS
| Row | Law (issue) | Face |
|---|---|---|
| u1 | F-NEW-642 (#588 W5) | Fragment.getActivity — the honest-null contract: no recorded host → handled_null, never the null-receiver NPE |
| u2 | F-NEW-645 (#588 W5) | ResourceBundle.getBundle — the implemented arm dispatches (never the stub tail) |
| u3 | F-NEW-629 (#569) | getSupportFragmentManager → the identity-first manager object |
| u4 | F-SQLQB (#592) | setTables+appendWhere+query → the REAL sqlite cursor |
| u5/u6 | F-NEW-658 (#588 G2) | SQLiteDatabase.insert/insertOrThrow → rowId 1 → 2 — a REAL sqlite3 journey (the battery's own first run surfaced the no-table face and drove the execSQL fix — evidence of the battery actually exercising the machinery) |
| u7 | #594 family | Bundle.putBundle/getBundle identity round-trip |

### 3. Gates (pre-merge, the edfa5083-lineage engine — NO engine-source change this wave)
s239 **7/7** · s238 17/17 · s237 5/5 · test-all **35/35** · parity **75/75** · six-pin **GATE PASS — ALL 6 HOLD** (gmdice `3891679d`, microtimer `bbd350b6`, unote `3b8dcb0a`, dooz `a0fae907`, bouncy `60182d11`, tictactoe `3dc2b230` — the S238 glUniform4fv face is now the stable recorded face). Disk note recorded honestly: the rootfs hit 0-free mid-gate; the S238 worktree cleanup freed 4.5G and the gates reran clean.

### 4. The corpus lane — the first REAL LAW-001 preflight of the #588 titles
`org.moire.opensudoku_20180507.apk` downloaded from F-Droid, sha256 `a874f3c9abc7a91dc7d74bbd…`, verified an Android package, then `unknown_apk_preflight.py` executed: **verdict RUNTIME_ROOT — pure-DEX (`classes.dex`), abis=[], in_current_test_scope=true, counts_as_failure=false** → **L0 PASS**. `canonical/app_registry.json` gained the APP-020 OpenSudoku entry (L0=true, L1+ lanes honestly false — not yet executed)."""

B592 = """## S239 receipt for the F-SQLQB stack — the faces now carry REAL battery proof

The S239 wave audited this issue's stack against main and landed `tests/s239_wave_stack_audit_test.cpp` (main = `b3cd8548`) with three live rows over YOUR machinery:
- **u4**: SQLiteQueryBuilder.setTables + appendWhere + query → the REAL sqlite cursor (the GATE-A open path first: Context.openOrCreateDatabase → `open_standalone_database`, the identity connection).
- **u5/u6**: SQLiteDatabase.insert / insertOrThrow → rowId 1 → 2 — the F-NEW-658 real-sqlite INSERT contract (rowId or −1, never silent) exercised end-to-end: ContentValues put → flat mirror → sqlite3_bind → rowid.
- the honest **no-table face** was captured by the battery's first run ("no such table: puzzles" — the loud rc=1 trace) before the CREATE TABLE fix — exactly the never-silent behavior this issue demands.
Gates: s239 7/7, test-all 35/35, parity 75/75, six-pin ALL-6-HOLD. main = `b3cd8548`."""

def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s239-audit"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"#{issue} comment", json.loads(r.read().decode())["id"])

post(588, B588)
post(592, B592)
