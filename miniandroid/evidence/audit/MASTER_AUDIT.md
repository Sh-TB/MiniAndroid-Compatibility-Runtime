# MASTER AUDIT — Cross-Coder Achievement Audit (v2.1, 2026-11-20 (continuation session, S12+S14))
v1 baseline: commit 9b953ce1 (2026-11-20). v2 continues it per Issue #635 §1-§9 — nothing replaced, everything reconciled.
v2.1 adds the S14 closure pass: BUG-7 dedupe, UBSan E-05 machine verification, BUILD_TESTS=ON peak-RSS measurement.
Base: origin/main 56ba5842; session HEAD: 3f9a3f6c S17 housekeeping — #635 progress comment body + poster preserved as evidence (comment issuecomment-7047804487; token read at runtime from git credential, never stored)

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
15. **#632 focused laws (S17, AUD-54 phase 2)**: tests/s17_focus_laws_test.cpp — 14 pinning
    laws over the inflater DECODE layer (attribute -> node flag/px), the layer no earlier test
    drove end-to-end. Built on the real LayoutInflater::inflate_element (made public for the
    law battery; behavior unchanged) + measure_layout, with hand-built AxmlElements — no APK
    needed. Pins: rel-rule decode coexistence (G2 decode), toRightOf name capture (G4 decode),
    dp/px/dip one-multiplication + round-half-away law (L3/M1: 20dp->53, 8px, 12dip->32),
    sp -> scaledDensity law (M2: 10sp @font-scale 1.3 -> 34 — S16's M2 CONFIRMED-LIVE mark was
    a literal-grep miss, CORRECTED), weight-0 MATCH_PARENT NOT weighted (E3 claim refuted),
    sole weight-1 0dp child = full excess (AOSP G04 §9 port confirmed), silent attr drops with
    ZERO diagnostics (NEW-33/35/37: paddingStart/alpha/translationX vanish), both-anchor
    vertical law = EXACTLY span (D2 mask-overlap defect absent on the inflater path),
    forward-reference resolution via the Kahn order (G3: B.left == A.right). NEGATIVE-
    MUTATION CHECKED: 3 pins flipped -> exactly 3 FAILs -> reverted -> 14/14 PASS. Registered
    in Makefile TEST_LAW; law battery re-run green (test-law battery total=43 passed=43 failed=0 rc=0; s17_focus_laws_test self-report 14 pass / 0 fail).
    9 NO-CITE rows settled by laws (E3, G3, L3, M1, M2, NEW-33, NEW-35, NEW-37, D2), 2 more
    partially pinned (G2/G4 decode layers). RAW_LOGS/s17_focus_laws_2026-11-20.md.
    S18 ARITHMETIC CORRECTION: S17's "131 -> 120 remaining / 114/234 settled"
    double-counted the 11 rows it upgraded (they were already inside S16's 103
    machine-marked rows, never in the 131 NO-CITE queue). True pre-S18 state:
    103/234 marked, 131 NO-CITE. See item 16.
16. **#632 classification + law expansion (S18, AUD-54 phase 2 cont.)**: every one of the
    131 NO-CITE rows now carries an explicit S18 classification (84 TESTABLE-NO-APK,
    28 UNVERIFIABLE, 6 DUPLICATE, 5 NEEDS-EXTERNAL-ORACLE, 4 ALREADY-RESOLVED,
    3 TESTABLE-WITH-NEW-FIXTURE, 1 NEEDS-IMAGE-FIXTURE; ZERO rows actually need the
    missing APKs or coder artifacts — not inferred from earlier tests' APK usage).
    FIVE new law families implemented on the real execution path — 29 laws, all green:
    A rounding/floor/physical-units (M3, 7 laws, expectations pre-computed),
    B weightSum override + fallback + sequential exhaustion (E2, 4 laws),
    C text layout single-source-of-truth (N2/N3/N4 + NEW-23 first-strong, 8 laws),
    F sqlite shadow contract (SQL-4/5/6, 6 laws — BLOB NOT surfaced and WAL-does-
    not-stick CONFIRMED-LIVE), G framebuffer surface (O4 WHITE-init + O5 raw-bypass,
    4 laws — O4 defect pinned). NEGATIVE-MUTATION VALIDATED per family (5 mutations:
    floor removal, weight_sum override removal, ellipsis glyph, row-count under-report,
    init color — every family's laws flipped to FAIL, all reverted; one ineffective
    first injection and one wrong-field law FIX documented honestly in the log).
    Law battery with the 5 families registered: total=48 passed=48 failed=0 rc=0 (43 prior + 5 new S18 families). 11 more rows
    law-verified (M3/E2/N2/N3/N4/NEW-23/SQL-4/SQL-5/SQL-6/O4/O5) -> 114/234 settled
    HONESTLY, 120 remain classified. RAW_LOGS/s18_methodology_2026-11-20.md.

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
