**S15 — branch census corrected + PR #626 classified (commit to follow, ledger now 64 rows, AUD-58)**

**1. Census correction (AUD-57).** The S10 census had marked four coder lines "absent". A fresh
`git ls-remote --heads` shows all four **now on the remote** and fetched into the audit clone:
`wave10/dalvik-accel` (= `refs/pull/626/head`), `audit/s236`, `audit/m16-litehtml`,
`cont24/skeleton-light-experiment`. `wave9/dev-so-clean` is confirmed **merged** (PR #625
`merged=True`, base=main, `1e5c8fb9` in main ancestry). `layout-geometry-001` remains absent —
RC-12 (AUD-53) unrecoverability **re-verified from the remote side**.

**2. PR #626 — SUPERSEDED-IN-FULL (AUD-58, verdict SUPERSEDED / status INTEGRATED).**
The 15-commit wave10 line (stacked on wave9: W11→W20 P2 + WAVE-10/10.1 + FINAL-INTEGRATION)
needs **no rebase and no cherry-pick** — every content piece is already in main via the direct
W22–W24 landings:

- **F-NEW id matrix**: all 13 ids (709, 710×6, 711, 712×2, 713×4, 714, 717, 718, 719×2, 721,
  722, 723, 723b) present in main `src/`; the F-NEW-710 by-value fix **verbatim** at
  `dalvik_engine_invoke.cpp:187-191`.
- **W11–W14 law tests in main**: f709/f714/f716 test files + the F-NEW rows in
  `input_pipeline_law_test.cpp`.
- **W20 P2's three fixes**: ① `<cstdint>` present in `adapter_scrap_bin.h`; ② 0
  `android_shadows.h` refs in the 599-line `dalvik_engine_tail.cpp`; ③ the dev-so `.d`
  `-include` block at `Makefile:817-820` with the exact placement comment.
- **P0 split + dev-so + docs**: main has its own further-evolved landing (5 domain TUs, refined
  by W22-C/W23 measurements) plus `docs/dev-so-architecture.md` (93 lines).
- **Zero missing code**: every src/tests path the branch touches exists in main
  (`git cat-file -e` loop → 0 MISSING-IN-MAIN); the remaining delta is branch-only
  `scripts/`+`evidence/` working artifacts.
- **audit/s236**: superseded too — `tests/s236_port_laws_test.cpp` is in main and registered in
  `Makefile` TEST_LAW (line 531); the branch remainder is raw evidence only.
- **m16-litehtml / cont24**: reachable flag-gated/branch-only experiments — disposition
  unchanged, reachability documented.

Rebasing would resurrect duplicate implementations against main's further-evolved P0/header-split
architecture — classification and recommendation logged in
`evidence/audit/RAW_LOGS/s15_branch_classification_2026-11-20.md`; the close decision stays with
the owner.

**3. Ledger.** AUD-57 corrected, AUD-53 re-verified, AUD-58 appended → **64 rows**, independent
validator PASS; deliverables regenerated (MASTER_AUDIT §1 item 13, NEXT_INTEGRATION_PLAN item 6
resolved, BLOCKED_AND_PENDING updated).

**Remaining open (unchanged):** coder-local artifacts (#634 MG-012, #295/#296/#297, RC-12, #630/#631
apps — owner branch absent from remote); missing original APKs (#597/#618/#623); AUD-10b/42;
AUD-54 focused-test queue (25/234 cites machine-checked).
