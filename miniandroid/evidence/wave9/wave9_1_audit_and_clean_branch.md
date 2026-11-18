# WAVE-9.1 — Clean PR Scope & Repository Hygiene Audit (Issue #612)

## Task 1 — Commit-to-purpose classification (all 26 commits ahead of remote main `125f5690`)

| Commit | Subject (abridged) | Classification |
|---|---|---|
| b4660c52, fa5f97cf, 93721416, 5e7090e3, c5b919b4, f9ab6f28, a20a93cc | UUID messages (7 commits) | Platform checkpoint commits (not campaign work) |
| 51cc5bf1 | ISSUE-609 WAVE-1 Blockinger laws | Historical unrelated (different issue) |
| 4263eb6c | ISSUE-614..624 batch status | Historical unrelated (other issues) |
| 81f2dd6d | F-DROID-APK batch (9 apps) | Historical unrelated — **contains tracked screenshots + a downloaded APK** (see Task 2) |
| 4c7b0dc0 | WAVE-2 DEV=1 profile | Historical wave-2 build work (superseded, not needed by dev-so) |
| 3d0e6c12, 98babaae, 8e5daf6c | WAVE-3 pilot/checkpoint/report | Historical wave-3 (first extraction machinery) |
| a4d7aa12, 38211919, ab9c59e5, e455aee6 | WAVE-4 laws/ledger/evidence/report | Historical wave-4 |
| **97228c1a** | WAVE-4 P0 dalvik_engine split → 5 TUs | **Required precursor** (split creation) |
| **0a03944b** | WAVE-5 Phase 3 opcode TU 3-way | **Required precursor** (7-TU volatile set completed) |
| a4d38745, 9983941b | WAVE-5 evidence/final report | Historical wave-5 |
| b567ca9a | WAVE-6 memory profile | Historical wave-6 |
| **eac17a66** | WAVE-7 inline-budget ADOPTED | **Required precursor** (per-TU production flags mirrored by the PIC rules) |
| da5daa86, 4f34a77f | WAVE-9 integration + addendum | Required wave-9 implementation (superseded by clean branch) |

Note: `cfb11936` (wave-8) and `3e51caeb` (checkpoint) sit on LOCAL main above this branch's merge-base and are outside the compare; wave-8 evidence is carried as files, and `cfb11936` remains push-blocked (4 binaries >90 MB) and superseded.

## Task 2 — Binary artifact audit (26-commit range, 326 unique paths)

| Category | Findings | Disposition |
|---|---|---|
| >50 MB blobs | 4 (build_dev_so exes, 109–114 MB, wave-8 commit — outside this range's merge-base but in local main) | Proven push-blocking; excluded from clean branch |
| APKs tracked | 1: `download/batch614_624_evidence/de.tcrass.minos_10004.apk` (137 KB, hash-verified download evidence) | Downloaded binary — must not be tracked; excluded from clean branch |
| Screenshots/frames | 40 PNG + 2 PPM under `evidence/batch614…624/` | Session evidence, not build output; kept in history only |
| `.rej` files | 3 (`dalvik_engine.cpp.rej`, `dlopen_exec.{cpp,h}.rej`) | Generated junk from split tooling; **excluded from clean branch** |
| `.o`/`.a`/`.so` | 0 tracked | — |
| `.dex` binaries | 0 | — |
| Clean branch tip tree | 0 artifacts of any category above | Verified by name+size scan |
| Clean branch history | 0 blobs >50 MB | Verified via `rev-list --batch-check` |

Essential reproducibility evidence retained in the clean branch: wave-8 link-cost/benchmark/final-report JSONs+MD, wave-9 results/evidence/APK-identity/no-op records, `w8_gate.py` + `w9_bench.py` reproduction scripts. Nothing else was deleted anywhere; historical branches are untouched.

## Task 3 — Clean feature branch `wave9/dev-so-clean`

Based on **remote main `125f5690`**. Two reconstructed commits:
1. `832da025` — dalvik 7-TU split machinery at wave-7 state (11 source files + manifest + Makefile), minimal prerequisite of the dev-so integration; excludes the `.rej` files.
2. `1264fcb8` — opt-in dev-so targets (SONAME `libminiandroid_dalvik.so`, `$ORIGIN` RPATH, per-TU PIC rules mirroring production flags, staleness guard, PIC `.d` dep files) + `.gitignore` + compact evidence + scripts.

## Task 4 — Verification ON the clean branch (fresh runs, NOT inherited)

| Check | Result |
|---|---|
| merge-base vs origin/main | `125f5690` = remote main tip |
| ahead / behind | **2 / 0** (GitHub compare API: `ahead_by 2, behind_by 0, 23 files`) |
| Production static build (default `make all`) | rc=0 (234.7 s incl. legitimate checkout-mtime catch-up), `test-core` 3/3 PASS (12.4 s) |
| Monolith fallback LIVE (`DALVIK_SPLIT=0`) | build rc=0 (208.0 s), `test-core` 3/3 PASS (12.4 s), Guess run rc=0, screenshot `87fe2676…` IDENTICAL |
| Clean dev-so build (`dev-so-clean` → `dev-so`) | rc=0, 148.5 s, battery 3/3 |
| Opcode trace | 1 PIC compile + 1 `.so` relink + **0 test relinks**, PASS=3, 9.76 s |
| Interpreter trace | 1 + 1 + **0**, PASS=3, 21.98 s |
| Bridge trace | 1 + 1 + **0**, PASS=3, 43.9 s |
| Opcode cycle ×3 | median **9.85 s** [9.79–9.85] |
| Interpreter cycle ×3 | median **21.94 s** [21.52–22.31] (<30 MET; <15 NOT met — compile-bound) |
| Bridge cycle ×2 | median 40.98 s [39.48–42.48] (PARTIAL, known blocker) |
| dev-so no-op ×3 | 0.05 s class (<0.5 MET) |
| APK parity (original APKs, `miniandroid_dev`) | Guess `87fe2676…` SUCCESS; Dice `46b07062…`, TTT `d55056a8…` PARTIAL — all hashes IDENTICAL to canonical |

## Task 5 — PR readiness

- Branch pushed: `wave9/dev-so-clean` (only 2 commits; no force-push used anywhere; `wave9/dev-so-integration` left untouched for audit trail).
- Compare URL: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/compare/main...wave9/dev-so-clean
- GitHub compare API results (authoritative, saved as `evidence/wave9/github_compare_clean.json`): status `ahead`, ahead_by 2, behind_by 0, 23 files changed.
- PR creation via API remains blocked by token scope ("Resource not accessible by personal access token") — ready-to-use PR body: `download/wave9_pr_body_clean.md`.
- Issue #612 updated with the corrected branch and this evidence. Not merged; #612 stays open.

## Rollback

`make dev-so-clean` removes the dev path entirely (nothing else references it); production default `DALVIK_SPLIT=1` static and monolith `DALVIK_SPLIT=0` are independent of the block. Branch-level rollback: delete `wave9/dev-so-clean`; remote main was never modified.
