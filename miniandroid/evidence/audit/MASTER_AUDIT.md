# MASTER AUDIT — Cross-Coder Achievement Audit (v2.4, 2026-11-21 (S19 mega-sweep — classified census queue CLOSED 227/234, family I grid/scroll laws))
v1 baseline: commit 9b953ce1 (2026-11-20). v2 continues it per Issue #635 §1-§9 — nothing replaced, everything reconciled.
v2.1 adds the S14 closure pass: BUG-7 dedupe, UBSan E-05 machine verification, BUILD_TESTS=ON peak-RSS measurement.
Base: origin/main 56ba5842; session HEAD: c59eba39 S18-cont-2 closeout — #635 progress comment body + poster preserved as evidence (token read at runtime from git credential, never stored)

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
17. **#632 D/E law families (S18-cont, AUD-54 phase 2 cont.)**: the two families the
    S18 closeout deliberately left ("defined-not-implemented") are now implemented on
    the LIVE inflater path — the D/E registry rows cite view_renderer.cpp lines, which
    BATCH 3 proved are NOT COMPILED, so the laws target layout_inflater.cpp instead.
    EIGHT laws, expectations fixed from the documented production laws BEFORE the run:
    family D s18_gravity_direction_laws_test — D1 fill_vertical keeps its 40px height,
    top-aligned (no stretch branch exists, :4853-4883; AOSP expects a stretched child);
    D2 fill_horizontal same on the vertical column's cross axis; D3 STRING "start" under
    RTL stays LTR-mapped (gravity_bits drops the 0x00800000 relative flag, :105-107, so
    the RTL flip law at :5022-5028 can never fire for XML-declared start; AOSP mirrors);
    D4 INT 0x00800003 under RTL DOES flip to x=60 — the defect is isolated to the string
    decoder; D5 DISPLAY_CLIP 0x11000000 placement-identical to a no-gravity control.
    Family E s18_linear_extras_laws_test — E1 no baseline branch: 30px/60px children
    both top-aligned (AOSP baselineAligned default would offset the 30px child);
    E2/E3 showDividers matches no decode case: silent vanish (warnings EMPTY, S17 A1
    law) and placement identical to the no-divider control on both axes. NEGATIVE-
    MUTATION VALIDATED (3 injections, RAW_LOGS/s18_de_mutations_2026-11-21.log):
    MUTATION-D relative-flag guard removal -> exactly D3 FAIL (D4/D5 untouched, as
    predicted); MUTATION-E (first, KEPT) the vg>=0 TOP branch centered -> D1 FAIL —
    a collateral catch that proved E1 guards a DIFFERENT branch (prediction corrected
    honestly, S18 wrong-field lesson class); MUTATION-E2 retargeted to the no-gravity
    else -> exactly E1 FAIL (tops 35/20). ALL REVERTED -> battery total=50 passed=50 failed=0 rc=0 (48 prior + 2 new D/E families; first run and post-mutation-revert run both green).
    Registry: 5 rows upgraded (D5/D6/E6/E7 newly settled — they carried S18-CLASS
    stamps in the classified queue; D4 upgraded IN PLACE from the S16 PARTIAL mark
    inside the 103 machine-checked rows) -> **118/234 settled HONESTLY, 116 classified
    remaining** (arithmetic computed by scripts/s18_de_upgrade_rows.py; no recount of
    already-marked rows). Ledger +AUD-60 (UNIT-TESTED, 66 rows) validator PASS.
    Track-A P1: batch-comment parentage RESOLVED — all 11 provenance comment IDs are
    comments on #632 itself (BATCH 2/3/4/5/6/7/8/B1/B2/10/11; TRACK_A_ISSUE_DIGEST.md
    table corrected — the earlier "3 comments" reading was a fetch truncation artifact).
18. **S18-cont-2 — census re-measurement + B5 falsification + S3**: a sandbox recycle had
    rewound the local branch to c5a1efa6 with a partial tree; restored by hard reset to
    origin/main d878c4c8 (untracked new evidence survived; tree verified against the pushed
    state). (a) S3: #635/#633/#634 bodies fetched and archived
    (RAW_LOGS/s3_issue_bodies_2026-11-21.md; digest section added) — #635's §1 dispositions
    provide EXTERNAL measured evidence: ggc-min REJECTED-measured (3x slower, GC thrash),
    -fno-var-tracking-assignments REJECTED-measured (no win; GCC14 fixed VTA),
    .DELETE_ON_ERROR FIXED in-tree (grep-verified on the restored tree), Make-path peak RSS
    1221 MB / 4 GB across ~40 full builds (OOM NOT observed). (b) A-row hygiene census
    RE-MEASURED (RAW_LOGS/s18_a_census_2026-11-21.log): A2 tracked evidence/ = 55.61 MB /
    1287 files (claim 45.67/1185 — HOLDS, grown with the law logs); A3 37 root logs /
    4.83 MB (HOLDS); A5 .gitignore exactly 645 bytes with NO build_* exclusion (HOLDS
    verbatim); A6 src/ 16.10 MB / 214 files but src share = 16.9% of the 95.24 MB tracked
    repo — the '>99% non-source' figure SUPERSEDED (directionally true at ~83%); A7
    build_p2a/build_dev/build_cc ABSENT (SUPERSEDED-by-cleanup); A8 database 7.15 MB /
    third_party 4.36 MB (HOLDS). (c) Family H s18_constraint_law_test 3/3 — B5 FALSIFIED
    for the live path: the claim ("ConstraintLayout classified as FrameLayout, no
    constraint solving") cites view_renderer.cpp:70 (DEAD per BATCH 3); the engine
    implements the F-148 ConstraintLayout law (layout_inflater.cpp:3502-3531 — per-axis
    topological anchors, MATCH_CONSTRAINT spans, bias 0.5); expectations fixed from that
    documented law BEFORE the run: H1 anchor solving (B.top = A.bottom = 60), H2 bias
    centering (left = 0 + 0.5*400 = 200), H3 MATCH_CONSTRAINT span (EXACTLY 800).
    MUTATION-H broke the is_cl_container predicate -> family H 0 pass / 3 fail (the solving/bias/span laws FAIL as predicted; reverted). (d) 11 registry rows settled (A2/A3/A5/A6/A7/A8/B5/B6/B7/B8/B9 via
    scripts/s18_cont2_upgrade_rows.py) -> **129/234 settled HONESTLY, 105 classified
    remaining**. Ledger +AUD-61 (UNIT-TESTED, 67 rows) validator PASS. S3 also recorded
    #633 [MG-009] and #634 [MG-012]: both MG vector issues claim root-caused local fixes
    that are BLOCKED FROM PUSHING — integration candidates pending actual patch delivery.
19. **S19 mega-sweep — the classified census queue CLOSED (227/234)**: branch restored
    AGAIN after a second recycle rewind (hard reset to c59eba39, tree verified). (a) The
    true open queue was 96, not 105 — 9 rows (E8/Q1/Q2/Q3/Q5/Q6/Q7 and 2 more) were
    ALREADY resolved inside their own S18-CLASS notes (ALREADY-RESOLVED/DUPLICATE).
    (b) One self-measuring sweep (scripts/s19_census_sweep.py, log
    RAW_LOGS/s19_census_sweep_2026-11-21.log, per-row uniqueness pre-flight — the
    S18-cont-2 lesson) settled **92 rows with fresh measured evidence**: 19
    DORMANT-RESCOPE (every view_renderer.cpp-cited row — the Makefile itself lists it in
    DORMANT_SOURCES :624-626, "documented dormant — not linked", skipped by the parity
    loop); 30 CENSUS-CONFIRMED (B8: app-class hardcodings in 4 live TUs; B9:
    **253 distinct MINIANDROID_* env vars** vs the 3 the claim named; SQL-7/SQL-8
    verified at src/storage/; NEW-8 largest TU 5.03 MB; NEW-3 weight-milli
    lround(f*1000); J2/NEW-5 resample_nearest live; G5/I4/NEW-40/K3/N5/O9/J11/NEW-17/
    NEW-30/NEW-41/NEW-43/NEW-44/NEW-45/NEW-46/NEW-47/NEW-48/N8 absences at 0 grep hits;
    NEW-16 depth cap live; Q4 uncapped extract cache live; NEW-10 6 EXISTS guards);
    8 LAW-REFUTED (H1/F4/F6 grid — the #606 Bellman-Ford law, margins carry the gaps;
    I5 HSV horizontal UNSPEC; G6 cycle fallback; NEW-42 CL sizing core per family H;
    NEW-39 baseline/divider per the DE laws; NEW-11 gravity laws in-battery);
    10 CENSUS-PARTIAL refinements with counts (J3/J10/M4/O8/P5/P6/P7/P8/H3/K5);
    2 RESOLVED-DOC (SWEEP-S2 -> the batch-8 doc; NEW-9 -> #635's retraction-justified
    disposition); 22 PLAN-ACK (R-1..R-5/REUSE-TOTAL/R3-R5/R8/S1/S3-S9/NEW-13/25/31 —
    proposal rows, not factual claims); 1 BLOCKED-EXTERNAL (NEW-6 GitHub indexing).
    (c) Family I s19_grid_scroll_laws_test 3/3 — I1 margins-carry-the-gaps (F4
    falsified: track = max(child+margins), root 110 not 100), I2 columnCount honored
    (2x2 tracks = 160x80), I3 HONESTLY RETARGETED: my root-wrap expectation was
    falsified by the engine's AOSP-correct window-frame answer (root = 1080); the law
    was retargeted to the content-UNSPEC assertion (child = 3000, root = 1080),
    mirroring s246 H1.3. MUTATION-I dropped the grid margins from the track law -> family I 2 pass / 1 fail (I1 FAIL exactly as predicted at 100x100; I2/I3 unaffected; reverted; markers in src/ = 0). Full battery total=52 passed=52 failed=0 rc=0 (51 prior + family I; final post-revert run green). (d) Remaining
    queue: **7 rows** (NEW-2/12/14/24/26/28/32 — content-check class, decisive grep
    evidence unavailable). **227/234 settled honestly.** Ledger +AUD-62 (UNIT-TESTED,
    68 rows) validator PASS.

## §2 Verdict totals (programmatic, from the 68-row ledger)
See LEDGER_VALIDATION_REPORT.md — totals generated by scripts/validate_ledger.py, sum==rows==68.
S14: PENDING 4 -> 2 (AUD-47/49 resolved), CONFIRMED 33 -> 35. S15: +1 row (AUD-58, SUPERSEDED).
S18: +1 (AUD-59, UNIT-TESTED). S18-cont: +1 (AUD-60, UNIT-TESTED). S18-cont-2: +1 (AUD-61, UNIT-TESTED).
S19: +1 (AUD-62, UNIT-TESTED).
v1's "30 CONFIRMED / 4 REJECTED..." was internally inconsistent (its CONFIRMED bucket absorbed 3
REJECTED probes); v2 replaces it with machine-counted numbers.

## §3 Deliverables (this directory)
ACHIEVEMENT_LEDGER.csv (68 rows) · LEDGER_VALIDATION_REPORT.md · 632_FINDINGS.csv (234; S16
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
  the classified census queue is CLOSED for grep/census-level work: **7 rows remain**
  (131 NO-CITE classified in S18 -> 11 settled by its law families -> 4 by the S18-cont
  D/E laws (D5/D6/E6/E7, D4 upgraded in place) -> 11 by S18-cont-2 (A2-A8/B5-B9) -> 9
  found resolved-in-note -> **92 by the S19 mega-sweep**) — the 7 left (NEW-2/12/14/24/
  26/28/32) need content-level checks, not greps (NEXT_INTEGRATION_PLAN.md item 8).
  **227/234 settled honestly.** The S16 sweep CORRECTED the earlier
  25 "cited X ABSENT" marks: every one of those files exists under src/resources/ or
  src/renderer/ — the cites were stale paths, not missing code (verdict STALE-CITE-RELOCATED).
- The #627 hub's exact 7 UBSan vectors were never published; the S14 probe set is the audit's
  reconstruction (hub's 3 named vectors + 4 boundary neighbours), engine-tested in w15 rows too.
- The concurrent per-instant RSS sum of a parallel build is not observable via wait4 rusage
  (max-children semantics); the reported peak is the whole-tree per-process maximum at -j2
  (the metric GNU time -v would print — /usr/bin/time is absent in this sandbox).
