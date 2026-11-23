# REPOSITORY SIZE AUDIT — S-SLIM (2026-11-23)

Mission: eliminate repository growth at its root + one coherent enforceable
policy. READ-ONLY toward runtime source; no history rewrite performed.
Base: `bb2e4873` → final commit **`01aa254f`** (branch main). Safety
checkpoint: tag `pre-slim-20261123`. Toolchain: g++ 14.2.0, GNU Make 4.4.1,
git 2.x, 2 vCPU / 3 GB RAM sandbox, single-repo layout (no nested repos),
2 stashes preserved untouched.

## 1. The answer to "why is GitHub over 1 GB"

Measured separately (the checkout is NOT the history):

| metric | before S-SLIM | after S-SLIM |
|---|---|---|
| git working tree (incl. untracked) | 5.5 GB | ~1.7 GB |
| tracked files | 17,956 | 17,507 |
| tracked checkout bytes (path-summed) | 339.1 MB | **259.6 MB** |
| `.git` directory | 1.3 GB | **1.2 GB** |
| loose objects | 5,631 / 138.7 MiB | 0 (gc-packed) |
| size-pack (compressed history) | 1.06 GiB | **1.13 GiB** (packed incl. new commits) |
| policy violations | **4,279** | **0** |
| duplicate >100 KiB groups tracked | 22+15 | 0 unresolved (2 documented pairs) |

Root cause, proven by blob accounting over all history:
**total blob bytes in history = 6.77 GB, of which 4.77 GB are `build_*` tree
payloads** — 3 production binaries (~33.7 MB each: build_w24b, build_fast,
build_p2a) plus **~50 test executables of ~32.5 MB each under
build_fast/tests/** committed by an auto-add session. APK/DEX/so payloads are
~0.01 GB (the S153 purge already removed those). This is recurrence #2 of the
same incident class documented in .gitignore S153 (2026-11-02, "repo was
~600 MB+ … git filter-repo purged … 1437 commits").

## 2. What was physically cleaned (no history touched)

Full decision ledger: `evidence/audit/EVIDENCE_RETENTION_DECISIONS.md`;
every untracked byte has a SHA-256 row in
`evidence/audit/S_SLIM_UNTRACK_SHAS.txt` (452 rows). Categories:

1. scratch residue deleted: make_out4-12.txt, s203_out*, 3 × `.rej` inside
   `src/`, w_s241_androguard.json;
2. raw exhaust untracked (keep-local): api/view_tree/run.log/crash.log/
   screenshot.ppm/frames/exp031_5 trees in the batch61x evidence dirs
   (~12 MB) + 4 × gmon.out (~19.7 MB) + s195_audit raw GitHub API dumps
   (~25.4 MB, the S230/S231 no-giant-export law);
3. run-store residue untracked: 93 *.db/-wal/-shm capture files;
4. byte-identical duplicates untracked keep-first (zero information loss,
   sha256 ledgered): issue612 ftime ×11, s207 ttt ×2, frozenbubble ×5,
   docs gifs ×3, docs MessageSchema twin (pinned s44 tree restored complete);
5. §20 zero-APK law: download/batch614_624_evidence/de.tcrass.minos_10004.apk
   untracked (corpus copy kept on disk — runtime evidence dependency);
6. dormant source copy: evidence/cont11/w8/fnew511_dalvik_engine_candidate.cpp
   (3.5 MB; content verified in main per AUD-58);
7. stale local caches deleted (not repo content): 6.7 GB disposable build
   tree, 2.4 GB stale `_ma_local_backup`, 410 MB /tmp copies, 1.9 GB
   non-canonical APK caches (stuck/fdroid/s151/cont73) — recorded here;
   the canonical corpus (upload/handoff_apks, apk_cache, canonical_apks) is
   UNTOUCHED.

## 3. Policy consolidation — ONE authority

CONSTITUTION_V2 §172 is the single normative authority (matrix:
`evidence/audit/POLICY_CONFLICT_MATRIX.csv` — 17 rules KEEP/MERGE/REWRITE/
REMOVE verdicts). The executable arm is `tools/policy_validator.py`; the
one-time grandfather pass (`allowlist-json` → POLICY_ALLOWLIST.json with
reason/owner/expiry) cleared 1,553 historical machine-path records + 6
oversize images + duplicate mappings, and the stale-entry filter guarantees
fixed violations are never allowlisted. PATH_OWNERSHIP: file-like junk pruned
from approved_dirs, wave-evidence prefixes registered, the evidence frozen
snapshot refreshed to the post-cleanup census (5,994 files) and
`wave_evidence_registered` re-pointed at `evidence/s27` — **the next wave
fails FROZEN_SNAPSHOT_DRIFT by design until it registers its evidence dir**.
SIZE_BUDGET re-adopted from post-cleanup measurements with +10% headroom
(miniandroid 66.7 MB < 78.3; evidence 101.5 < 140.9; scripts 11.4 < 13.2;
docs 46.0 < 55.2; upstream 23.4 < 27.0). .gitignore: 481 lines of
per-campaign session names → ~120 grouped stable rules built on the doctrine
*directory-level ignores + tracked-file immunity + explicit `git add -f`
promotion*.

## 4. Guards installed (growth cannot silently return)

1. **pre-commit hook installed locally** + committed installer
   `tools/hooks/pre-commit-policy.sh` — it ran during this very mission and
   BLOCKED two bad staging rounds (47 and 198 violations), proving it works;
2. **`.github/workflows/policy.yml` recreated** (was missing — the
   enforcement gap that let 4,279 violations accumulate): validator +
   `tests/policy_validator_law_test.py` + hygiene self-test on push/PR;
3. validator law test PASS (positive baseline + all 8 negative classes);
   hygiene checker self-test 22/22;
4. size budgets + default-deny directories + frozen-area drift + image
   policy + duplicate rejection — all enforced in the same gate.

## 5. Validation results (post-cleanup)

| gate | result |
|---|---|
| policy validator (main repo) | 0 violations, 4 warnings |
| validator law test | PASS |
| hygiene checker self-test | 22/22 |
| clean shallow clone of final tree | built with `-g0` profile (disk-constrained sandbox; debug-info is behavior-neutral) |
| law battery in the clone | **54/54 PASS** |
| test-core / test-hostile in the clone | 4/4 and 3/3 PASS |
| check-source-parity in the clone | PARITY-OK, 88 core sources |
| APK/DEX/SO tracked | 0 |
| secret scan | 0 real secrets (the 5 hits are the documented `git credential fill` token-read law scripts + a stats dict key) |
| APK corpus (upload/handoff_apks, apk_cache) | preserved on disk, untracked |
| canonical evidence | untouched; +12 IMAGE baseline entries pin bytes |

The first clone attempt failed at test-law 50/54 — the four font/texture law
tests (s243/s244/s245/s106_text2) failed because the clone predated the final
amend that restored the tracked `runtime/data/fonts/DroidSansMono.ttf`; after
restoring that file the same four tests pass (113/0 and 15/0 for the two
largest) and the battery is 54/54. This incident is itself a positive result:
the font-discovery law tests caught a missing tracked font within minutes —
exactly the regression wall the dedup map preserves.

## 6. The owner decision this mission CANNOT take: history rewrite

The 1.13 GiB pack is 4.77 GB of compressed build-tree blobs. Deleting files
today does NOT shrink history. The designed, previously-used remedy is a
one-time `git filter-repo` strip of `miniandroid/build*/` blobs (S153 did
exactly this in 2026-11-02). This mission explicitly does NOT rewrite
history (acceptance condition). Ready recipe, awaiting explicit owner
authorization:

```
git filter-repo --invert-paths --path-glob 'miniandroid/build_*' \
                --path miniandroid/build_w24b --path miniandroid/build_fast \
                --path miniandroid/build_p2a --force
git gc --aggressive --prune=now
# expected: pack 1.13 GiB -> ~0.3-0.45 GiB (all other content is compressible text)
# GitHub then needs a force-push of main + tag updates (remote-side action).
```

Until then, GitHub's reported size stays >1 GB even though every NEW commit
is policy-clean and the checkout is 259.6 MB.

## 7. Remaining PENDING (ordered)

1. owner decision on the history rewrite (§6) — the only path below 1 GB on GitHub;
2. merge `tools/check_repo_hygiene.py` into `policy_validator.py` (two-checker
   consolidation; both self-tests currently green; recipe = map its 22 cases
   onto validator checks 1-13);
3. per-area tracked_files/bytes refresh inside PATH_OWNERSHIP top_level
   entries (informational fields);
4. hooks are per-clone: every future workspace must run the documented
   `cp tools/hooks/pre-commit-policy.sh .git/hooks/pre-commit` (CI policy.yml
   is the backstop);
5. TEST_LAW_DEDUPLICATION_MAP.csv marks one MERGE-CANDIDATE
   (font_pipeline_probe → s243) for the next touch of that area.

## 8. Evidence index

- `evidence/audit/TRACKED_FILE_INVENTORY.csv` — 17,507 rows: path, bytes,
  sha256, blob, ext, category, last-commit, age (generator:
  `tools/slim_consolidation.py`, idempotent);
- `evidence/audit/DUPLICATE_AND_UNUSED_LEDGER.csv` — duplicate groups +
  452-row untrack ledger;
- `evidence/audit/POLICY_CONFLICT_MATRIX.csv` — 17-row verdict matrix;
- `evidence/audit/TEST_LAW_DEDUPLICATION_MAP.csv` — law/test families;
- `evidence/audit/EVIDENCE_RETENTION_DECISIONS.md` — per-class decisions;
- `evidence/audit/S_SLIM_UNTRACK_SHAS.txt` — SHA-256 of every removed blob;
- `/tmp/clone_g0.log` + `/tmp/slim_clone_build.log` — clone build logs
  (session-local; key results quoted in §5);
- commit `01aa254f` (branch main) — the entire consolidation in one reviewable
  diff; tag `pre-slim-20261123` — the recovery checkpoint.
