# MASTER AUDIT — Cross-Coder Achievement Audit (v2.1, 2026-11-20 (continuation session, S12+S14))
v1 baseline: commit 9b953ce1 (2026-11-20). v2 continues it per Issue #635 §1-§9 — nothing replaced, everything reconciled.
v2.1 adds the S14 closure pass: BUG-7 dedupe, UBSan E-05 machine verification, BUILD_TESTS=ON peak-RSS measurement.
Base: origin/main 56ba5842; session HEAD: bb2964c2 S15 — branch census corrected + PR #626 classified SUPERSEDED-IN-FULL (AUD-58; ledger 63->64 rows, validator PASS; re-based onto fca59025 after the recycle rolled local history back to d7fe7c6c — this commit supersedes the mis-parented 48e0b81a whose only delta was these same 16 files): (1) CENSUS CORRECTION (AUD-57): ls-remote re-run shows the four S10-'absent' coder lines NOW on the remote and fetched into the audit clone — wave10/dalvik-accel (= refs/pull/626/head 671d2577), audit/s236 (0f4e43b3), audit/m16-litehtml (951ea2bf), cont24/skeleton-light-experiment (d723a93e, old fork 534 ahead of main); wave9/dev-so-clean confirmed MERGED (PR #625 merged=True base=main, 1e5c8fb9 in main ancestry); layout-geometry-001 still ABSENT — RC-12/AUD-53 unrecoverability re-verified from the remote side. (2) PR #626 CLASSIFICATION (AUD-58, verdict SUPERSEDED / status INTEGRATED): the 15-commit wave10 line needs NO rebase and NO cherry-pick — every content piece is in main via the W22-W24 direct landings: ALL 13 F-NEW-7xx ids (709-723b) present in src/ incl. F-NEW-710 by-value signature verbatim at dalvik_engine_invoke.cpp:187-191; 3/3 W20 P2 fixes in main (cstdint in adapter_scrap_bin.h; 0 android_shadows.h refs in the 599-line dalvik_engine_tail.cpp; dev-so .d -include block Makefile:817-820); ZERO branch src/tests paths missing from main (git cat-file -e loop, 0 MISSING-IN-MAIN); P0 split + dev-so profiles + docs/dev-so-architecture.md (93L) further-evolved in main; law tests f709/f714/f716 + F-NEW rows in input_pipeline_law_test in the 49/49 battery. Rebasing would resurrect duplicate implementations against main's further-evolved P0/header-split architecture. (3) audit/s236 superseded (s236_port_laws_test in main + registered Makefile TEST_LAW:531; branch remainder = raw evidence); m16-litehtml + cont24 = reachable branch-only experiments, disposition unchanged. (4) Evidence: RAW_LOGS/s15_branch_classification_2026-11-20.md (census table, commit list, per-piece checks, verdicts); deliverables v2.2 regenerated + synced to download/audit_v2 (MASTER_AUDIT 64 rows + §1 item 13, NEXT_INTEGRATION_PLAN item 6 resolved, BLOCKED_AND_PENDING #626 -> resolved). (5) #635 progress comment posted (issuecomment-7046792357); the #626 PR-conversation comment was BLOCKED by the audit token's permissions (HTTP 403 on issues/626/comments — fine-grained PAT lacks Pull-requests conversation write; issue comments unaffected) — the full classification + close recommendation is public on #635; close decision left with the owner. Labels: AUD-58 SUPERSEDED-IN-FULL; AUD-57 CORRECTED; AUD-53 RE-VERIFIED; LEDGER 64-ROWS-VALIDATED.

## §1 What this session changed
1. **Ledger normalized** (S2): 50 rows -> **63 rows** (S15: +1 -> **64 rows**, AUD-58), one claim per row, canonical verdicts
   only (CONFIRMED/REJECTED/PARTIALLY CONFIRMED/BLOCKED/PENDING/SUPERSEDED), separate
   evidence-level and integration-status columns, machine-validated (LEDGER_VALIDATION_REPORT.md — PASS).
   Splits: AUD-10a/b, 15a/b, 25a/b, 36a/b, 37a/b, 38a/b. New rows AUD-51..57.
2. **False-green corrections** (the audit's own): AUD-30 (GridLayout) FALSIFIED by source — the
   Bellman-Ford solver EXISTS (layout_inflater.cpp:2899-2903, :4364-4380); AUD-32 (nine-patch)
   downgraded to PARTIALLY (npTc parsing EXISTS at execution_engine.cpp:2876; npLb absent);
   AUD-06/01/02 re-measured with cmake 4.4.5 (below); AUD-36/37/38 tracker-state rows split from
   runtime rows (tracker closure is NOT runtime proof).
3. **#632 fully extracted** (S3): 234 findings, one row each (632_FINDINGS.csv), original wording
   preserved, statuses: 190 LIVE / 20 RETRACTED-BY-AUTHOR / 14 DEAD-CODE-RESCOPED / 10 PLAN-SWEEP.
   Reconciliation: title says 194; delta +40 = the registry author's own retraction counter
   (batch 3: "Running total: 40"). NEW-18/19/20 never published (numbering gap).
4. **RC-12 recovery closed** (S4): 4 commits unrecoverable after a full sweep (cat-file x4, 26
   remote refs, 2 PR refs, tags, stashes, 0 dangling commits, worktrees, upload/ artifacts);
   the owning branch `layout-geometry-001` is coder-local only; capability PARTIALLY SUPERSEDED
   by mainline c48773a0 + 7e5473be (scaleType laws in the battery). AUD-53.
5. **MG-011 recovered and INTEGRATED** (S5): `out->ok = err.empty() && !paths.empty();` applied at
   vector_decode.cpp:942 — the hole was verified live first (clip-path warning at :493 still
   reported success). Build rc=PENDING (build still running), battery rc=PENDING (build still running) .
6. **CMake measured** (S9): default all = 99 edges / 1 link / QuickJS 1x / WEBP define absent;
   BUILD_TESTS=ON = 204 edges / **50 links** / QuickJS 2x. AUD-06's blocked measurement is done;
   claims B19/B22 confirmed WITH their condition (BUILD_TESTS=ON), false for the default graph.
7. **S7 forensics** (AUD-51, commit 051af519): build_w24_cand_a/ + APK untracked, .gitignore
   hardened, evidence SHAs preserved, no history rewrite.
8. **Branch census** (S10): merged into main: s241-law-waves (S236-S240), s237-w27, s238-audit,
   s239, s240. At census time absent: wave10/dalvik-accel (15 commits — largest unmerged coder
   line), audit/s236 (7), audit/m16-litehtml (3), cont24/skeleton-light (2). 2 stashes preserved.
   S15 correction: all four lines ARE on the remote now (see item 13).
9. **APK identity census** (S8): 15-corpus SHAs recorded; ugraday matches #612's recorded sha;
   TicTacToe substitute documented; #597/#618/#623 APKs absent -> claims stay BLOCKED.
10. **BUG-7 dedupe (AUD-49 closed, S14)**: the stale src/dex/shadow_registry.h copy was committed
    EMPTY (0 bytes; the W24 registration's "two DIFFERING copies" has degenerated); include census:
    20+ includers ALL resolve to src/framework/ (zero references to the dex path). Removed with
    `git rm`; production battery re-run after removal: battery 49/49 PASS rc=0
    (s14_battery_after_dedupe_e05_2026-11-20.log).
11. **UBSan E-05 machine verification (AUD-47 closed, S14)**: #627 hub comment 6991611630's claim
    was never reproducible (no named vectors, no profile). S14 adds the opt-in `make UBSAN=1`
    profile (-fsanitize=undefined -fno-sanitize-recover=all, tree build_ubsan/), two standalone
    probes, and +4 const_high16 rows in w15 (7 engine-tested vectors = the hub's 3 + boundaries).
    Results: fixed-form probe 7/7 bit-exact rc=0; old-form probe UBSan ABORT "left shift of
    negative value -1" rc=0 — the hub's evidence
    reproduced exactly; w15 13/13; FULL battery built AND run under UBSAN=1: probes rc=0, battery 49/49 rc=0
    (s14_ubsan_battery_2026-11-20.log). Both W22-A fix sites re-verified in-tree
    (dalvik_interpreter.cpp CONST_HIGH16 + dormant monolith dalvik_engine.cpp:22438-22451).
12. **BUILD_TESTS=ON peak RSS measured (AUD-52 completed, S14)**: full cmake build executed at
    -j2 with scripts/s14_time_wrapper.py (os.wait4 rusage = the whole-tree per-process peak —
    the same metric GNU time -v reports; /usr/bin/time is absent in this sandbox) — build
    rc=0, peak 1235 MB (1264520 KB), wall 491.91 s, ctest rc=8 (98% passed); the single non-pass is
    miniandroid-smoke "Not Run" (its miniandroid_test target is not a dependency of the battery;
    all 49 battery tests passed, 0.46 s total). W22-C production baseline for comparison:
    1427 MB (-j1). Logs: cmake_testbuild_rss_2026-11-20.log + cmake_ctest_battery_2026-11-20.log.
13. **Branch census corrected + PR #626 classified (AUD-57 correction + AUD-58, S15)**: ls-remote
    re-run shows the four census-"absent" lines NOW on the remote and fetched into the audit
    clone (wave10/dalvik-accel = refs/pull/626/head, audit/s236, audit/m16-litehtml,
    cont24/skeleton-light-experiment); wave9/dev-so-clean confirmed MERGED (PR #625
    merged=True, base=main, 1e5c8fb9 in main ancestry); layout-geometry-001 still ABSENT
    (RC-12/AUD-53 re-verified unrecoverable from the remote side). PR #626 (15 commits,
    stacked on wave9) classified **SUPERSEDED-IN-FULL**: all 13 F-NEW-7xx ids (709-723b)
    present in main src incl. the F-NEW-710 by-value signature verbatim
    (dalvik_engine_invoke.cpp:187-191); 3/3 W20 P2 fixes in main (cstdint in
    adapter_scrap_bin.h, 0 android_shadows.h refs in the 599-line dalvik_engine_tail.cpp,
    dev-so .d -include block at Makefile:817-820); ZERO branch src/tests paths missing from
    main; s236_port_laws_test in main's TEST_LAW:531; P0 split + dev-so profiles +
    docs/dev-so-architecture.md (93L) all in main (further-evolved). NO rebase, NO cherry-pick
    — rebasing would resurrect duplicates against main's architecture. Evidence:
    RAW_LOGS/s15_branch_classification_2026-11-20.md.
14. **#632 cite re-sweep (S16, AUD-54 phase 1)**: every finding's claim mechanically re-checked
    against the CURRENT tree with scripts/s16_cite_sweep.py — **103/234 rows machine-checked**
    (was 25). Verdicts: 35 CONFIRMED-LIVE (incl. C3/P1 confirmed VERBATIM at the cited lines
    android_shadows.cpp:11189 / 9785-9790), 32 STALE-CITE-RELOCATED (the 25 old "cited X
    ABSENT" marks CORRECTED — every "absent" file exists under src/resources/ or
    src/renderer/; the cites were stale paths, not missing code), 24 CITE-STALE (line refs
    from an older tree state; pattern status recorded), 5 PARTIAL, 3 RESOLVED-IN-TREE
    (A1 build dirs untracked; BP-19 battery behind -DBUILD_TESTS=ON; G3 Kahn topological
    sort NOW in layout_inflater.cpp:3223/3511), 3 PATH-AS-CITED-ABSENT (evidence fixtures),
    1 PATTERN-ABSENT (F2 row_h). 131 rows remain NO-CITE — runtime-behavior claims that
    need focused laws (the AUD-54 focused-test queue). Full per-row detail in 632_FINDINGS.csv.

## §2 Verdict totals (programmatic, from the 64-row ledger)
See LEDGER_VALIDATION_REPORT.md — totals generated by scripts/validate_ledger.py, sum==rows==64.
S14: PENDING 4 -> 2 (AUD-47/49 resolved), CONFIRMED 33 -> 35. S15: +1 row (AUD-58, SUPERSEDED).
v1's "30 CONFIRMED / 4 REJECTED..." was internally inconsistent (its CONFIRMED bucket absorbed 3
REJECTED probes); v2 replaces it with machine-counted numbers.

## §3 Deliverables (this directory)
ACHIEVEMENT_LEDGER.csv (64 rows) · LEDGER_VALIDATION_REPORT.md · 632_FINDINGS.csv (234; S16
source_check sweep on 103 rows) · 632_BATCH8_174_ATTRIBUTES.md · MASTER_AUDIT.md ·
INTEGRATION_MAP.md · REJECTED_AND_CORRECTED.md · BLOCKED_AND_PENDING.md ·
REGRESSION_RESULTS.md · PRESERVED_WORK_MANIFEST.md · NEXT_INTEGRATION_PLAN.md · RAW_LOGS/
(cmake_graph_measurement.md + cmake_testbuild_rss + cmake_ctest_battery,
s14_battery_after_dedupe_e05 + s14_ubsan_battery, s15_branch_classification, apk corpus
census, 632_registry_snapshot, untrack SHAs, b567 probes, tracker index)

## §4 Honest limits
- #295/#296/#297 and #634 fixes remain coder-local (branch layout-geometry-001 / local trees);
  not re-implemented here — MG-011 was, because the mission allows a one-line fix backed by tests.
- #632 per-finding checks: 103/234 claims machine-checked by the S16 sweep (source_check col);
  the 131 remaining NO-CITE rows are runtime-behavior claims and carry status notes — they are
  the focused-test queue (NEXT_INTEGRATION_PLAN.md item 8). The S16 sweep CORRECTED the earlier
  25 "cited X ABSENT" marks: every one of those files exists under src/resources/ or
  src/renderer/ — the cites were stale paths, not missing code (verdict STALE-CITE-RELOCATED).
- The #627 hub's exact 7 UBSan vectors were never published; the S14 probe set is the audit's
  reconstruction (hub's 3 named vectors + 4 boundary neighbours), engine-tested in w15 rows too.
- The concurrent per-instant RSS sum of a parallel build is not observable via wait4 rusage
  (max-children semantics); the reported peak is the whole-tree per-process maximum at -j2
  (the metric GNU time -v would print — /usr/bin/time is absent in this sandbox).
