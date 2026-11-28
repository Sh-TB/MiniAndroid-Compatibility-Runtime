# NEXT_ACTIONS.md — prioritized global integration queue

Impact-ranked per LAW 7 (runtime correctness > multi-app > API compat > shared infra > app-specific).

## Queue

1. **Q1 — wave10 verified source fixes into main (SMALL, SAFE)**: cherry-pick 3 source fixes from PR #626: dev-so `.d` -include ordering (stale-relink bug), adapter_scrap_bin.h `<cstdint>`, engine_tail include removal (independently verified #627 patch). Retarget/clean the PR afterward. Files: miniandroid/Makefile, miniandroid/src/view/adapter_scrap_bin.h (path check), miniandroid/src/dex/dalvik_engine_tail.cpp.
2. **Q2 — s236 provider-law re-port (MEDIUM, HIGH APK VALUE)**: apply audit/s236's sqlite_shadow.cpp (+161) nearly verbatim; re-locate getXml/Instant/dedupe laws from monolith-era diffs into the split TUs; port s236_port_laws_test (635 lines); verify chess boot (uncaughts 12→0 target) + opensudoku.
3. **Q3 — re-implement #713 TableLayout column law** (the claimed fix is lost): AOSP findLargestCells + shrinkable distribution per the issue description; law test from scratch.
4. **Q4 — m16-litehtml opt-in adoption** (zero runtime risk, vendored dep + probe; defer decision).
5. **Q5 — compose host materialization design** (T280 CIP-1 + #712 census consolidation) — design-first, biggest UI unlock.
6. **Q6 — monolith fate decision** (verify DALVIK_SPLIT=0 buildable or delete mirror; standalone wave).
7. **Q7 — contribution feedback loop (LAW 5)**: post Mainline Integration Audit comments on #596 (s236 disposition), #626 (PR retarget), #713/#714 (lost commits, re-implement plan), #627 (S256 re-push request).

## Blocked / parked
- cont24/skeleton-light (534 commits) — catalog-only until a review wave.
- #618/#619/#620/#623 app campaigns — CLOSED; verify their deliverables against main in the next ledger pass (assumed integrated via campaign commits; not individually ancestry-checked yet).
