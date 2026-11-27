# FINAL CLEANUP VERIFICATION — post-execution proof (2026-11-27)

Executed set under verification: 384 file removals (E1: 379-file byte-identical
`upstream/s43/ui_android_src/` twin; E2: 5 NOISE-face screenshots under the
codified noise law), all SHA-recorded in `SHA256SUMS.txt` before removal.
Zero production source, test, fixture, font, asset, or registry file touched.

## 1. Source safety

| gate | result |
|---|---|
| `make check-source-parity` (after deletions) | **[PARITY-OK] 88 core sources manifest-parity** |
| test sources referencing deleted paths | **zero** (grep over `miniandroid/tests/` + `tests/`; the single `evidence_retention_test.py` match is a synthetic temp-dir fixture string, not a real path) |
| binary identity | `./build/miniandroid version` → v0.0.6.2 / Commit `96878de83…` (unchanged lineage) |

## 2. Full battery re-run (post-cleanup, this session)

| suite | result |
|---|---|
| law battery | **55/55 PASS** — 53 direct runs + 2 rebuilt after an environment ENOSPC event (`s27_audit_laws_test` ALL PASS 7/7; `s98_prefs_law_test` 15/15 — both failures were `No space left on device` on their `/tmp` fixture dirs, never assertion failures) |
| test-core | **4/4 PASS** |
| test-hostile | **3/3 PASS** |
| **total** | **62/62** |

Environment honesty: the sandbox rootfs twice hit 100% during the battery
BUILD (55 exes × ~111 MB debug-info link ≈ 6 GB). The established S239-class
recovery was applied each time (regenerable `build/tests` freed, results
persisted in logs, affected pieces rebuilt and re-run). The two "failed" rows
in the first pass were compile/`/tmp` ENOSPC artifacts and are individually
re-verified green above.

## 3. Canonical APK regression vs pre-cleanup baseline

| run | hash | vs baseline |
|---|---|---|
| pz (`name.livitski.games.puzzle.android_2`, canonical tap) | `35c4e53b14561b2f` | **IDENTICAL** to the pre-cleanup canonical wall |
| S182 9-title reconciliation (same session) | 4 byte-identical faces, 6/9 REAL | runtime behavior unchanged by the cleanup |

## 4. Fresh-clone verification (honest scope)

- `git clone --depth 1 -b main` from GitHub at `96878de83`: **succeeded**.
- Inside the fresh clone: `make check-source-parity` → **[PARITY-OK] 88 core sources**.
- The full clone BUILD was aborted at 0-free-disk (this sandbox cannot hold
  two build trees); the clone itself plus clone-internal parity pass, and the
  complete build+battery executed in the primary tree on the identical source
  bytes, constitute the buildability evidence. The cleanup commit deletes only
  non-source files, so the transfer holds; a full fresh-clone build remains
  disk-blocked in THIS sandbox, not source-blocked.

## 5. Size measurement (checkout vs history, separately)

| metric | before | after executed set |
|---|---|---|
| tracked files | 17,510 | 17,126 |
| tracked bytes | ~339 MB | **~320 MB (−19,142,103 B measured: E1 3,330,229 + E2 15,811,874)** |
| git pack | 1.06 GiB | 1.06 GiB (unchanged by design — see HISTORY_SIZE_ANALYSIS.md §3-4; rewrite is owner-gated) |

## 6. Verdict

**CLEANUP VERIFIED — NO SOURCE DAMAGE.** Production source inventory intact,
62/62 battery green, canonical hashes identical, fresh-clone parity green.
All executed deletions are evidence-backed, SHA-recorded, and reversible from
the ledger (blob IDs remain in git history; `ui_android_src` is regenerable
from its tracked sources.jar).
