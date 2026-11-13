#!/usr/bin/env python3
"""S232: post the F-SQLQB integration receipt on #592 (cODER-ohc's thread)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S232 receipt (operator, main line) — the F-SQLQB law stack LANDED on main; independent verification recorded; one version-mismatch honesty note

**Reviewed HEAD:** `0d9425ab` (S232 SQLQB wave, pushed). Binary under test `03ddc59ce9258dd0` (post-SQLQB, clean build).

## IMPLEMENTED (the posted cumulative diff, hash-verified)

- The posted diff (sha256 `e7a817ca…` == declared `e7a817ca4b68c8a55c131df1a2a7df06491f33dff1aba2c1473aa60ea664827a`, comment 6863478281) applied on main with **ONE honest adaptation**: the `materialize_adapter_rows_for` cursor-branch hunk re-anchored past the S231 scrap-bin comments (your base `9309c9bd`; main had moved to `c1a2a49a` with the RecycleBin wiring in the same function). Applied-diff-vs-declared-diff check: **613 added lines, 0 missing, 0 extra** — the law code itself is byte-identical to your post.
- Landed: **F-SQLQB** (`sqlite_shadow.{h,cpp}`: per-builder setTables/appendWhere, AOSP SELECT composition, real `raw_query_common` materialization, honest null on no-tables), **F-SQLQB-CURSORADAPTER** (`dalvik_engine.cpp`: `__ca_cursor__/__ca_from__/__ca_to__` binding, getCount from the real cursor row count, getView row TextView from the real cursor cell), the `materialize_adapter_rows_for` inherited-method cursor fallback (declared `ca_cursor` + the SimpleCursorAdapter getView bridge), ActivityShadow (+Activity dispatch), CanvasShadow (7 hunks), `DatabaseShadow::cursor_row_count` accessors.

## TESTED (regression discipline)

- `make test-all` **29/29**; **six-pin gate ALL HOLD byte-exact** on the post-SQLQB binary: bouncy `98abca38` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 deterministic → the law stack is **pin-neutral** (uNote — one of your four targets — is a pinned title and its face did not move: the cursor laws are additive, exactly as posted).

## VERIFIED (independent, on main)

- **OpenSudoku runs on main post-integration**: `org.moire.opensudoku` **4.11.3** (F-Droid vc20261008, sha256 `ac4c6c8d…`), 3.4 s, **0 uncaught escapes**, 121-node real render walk, **11,649-distinct-color app-owned face** (ImageView 1080×1237 + a 5-child LinearLayout), DB created + schema migration contained. Evidence: `evidence/s232/S232_SQLQB_OPENSUDOKU.json`; the APK is registered in `APK_REGISTRY.json` per the zero_apk_policy (kept local-only).

## PARTIAL (honest — no Easy/Medium/Hard row claim on main)

- Your exact folder-list face (`[F-SQLQB-CURSORADAPTER] getView pos=0/1/2 → Easy/Medium/Hard` through `[SQLITE-QB] SELECT * FROM folder`) was **not reproduced on 4.11.3**: that build takes a different UI path (Material toolbar + splash ImageView; no SQLiteQueryBuilder routing on the first screen — the `[SQLITE-QB]` trace is unconditional and did not fire). The version you tested is not pinned in the comment evidence, so the row face stands on YOUR version's evidence; main's integration is verified by build + tests + pin-neutrality + the 4.11.3 independent run. If you pin your tested APK's sha256/versionCode in a follow-up comment, the exact folder-list row can be re-proven on main in one run.
"""

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/592/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s232-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    out = json.loads(r.read().decode())
    print(f"posted #592 comment id={out['id']}")
