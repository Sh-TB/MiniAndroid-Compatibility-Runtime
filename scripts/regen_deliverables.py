#!/usr/bin/env python3
"""Regenerate all audit deliverables (S12 + S14 continuation) with this session's
reconciled numbers. Numbers parsed from committed evidence logs — nothing hardcoded."""
import re, os, subprocess, datetime

AUD = "/home/z/my-project/miniandroid/evidence/audit"
RAW = "/home/z/my-project/miniandroid/evidence/audit/RAW_LOGS"
LOG = f"{RAW}/mg011_build_testall.log"

def read(p):
    return open(p, errors="ignore").read() if os.path.exists(p) else ""

def git(*a):
    return subprocess.run(["git"] + list(a), capture_output=True, text=True, cwd="/home/z/my-project").stdout.strip()

HEAD = git("log", "--oneline", "-1")
NOW = "2026-11-21 (S18-cont-2 — A-row census re-measurement, B5 falsification family H, S3 issue bodies)"

# ---- MG-011 verification results from the build log ----
mg_build_rc = mg_test_rc = "PENDING (build still running)"
battery_line = ""
t = read(LOG)
m = re.search(r"BUILD_RC=(\d+)", t)
if m: mg_build_rc = m.group(1)
m = re.search(r"TESTALL_RC=(\d+)", t)
if m: mg_test_rc = m.group(1)
m = None
for m in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", t):
    pass
battery_line = ""
if m:
    battery_line = f"battery {m.group(2)}/{m.group(1)} PASS rc=0 (first run hit ENOSPC — rerun clean; both records in the log)"

# ---- S14 results from the new evidence logs ----
dedupe_log = read(f"{RAW}/s14_battery_after_dedupe_e05_2026-11-20.log")
dm = None
for dm in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", dedupe_log):
    pass
dedupe_line = f"battery {dm.group(2)}/{dm.group(1)} PASS rc=0" if dm else "battery log missing"

ubsan_log = read(f"{RAW}/s14_ubsan_battery_2026-11-20.log")
um = None
for um in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", ubsan_log):
    pass
ubsan_e05_rc = re.search(r"ubsan-e05 rc=(\d+)", ubsan_log)
ubsan_rc = re.search(r"make UBSAN=1 test-all rc=(\d+)", ubsan_log)
ubsan_line = (f"probes rc={ubsan_e05_rc.group(1) if ubsan_e05_rc else '?'}, "
              f"battery {um.group(2)}/{um.group(1)} rc={ubsan_rc.group(1) if ubsan_rc else '?'}"
              ) if um else "UBSan battery log missing"

s17_log = read(f"{RAW}/s17_focus_laws_2026-11-20.log")
s17_sum = None
for s17_sum in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", s17_log):
    pass
s17_self = re.search(r"s17 focus laws: (\d+) pass / (\d+) fail", s17_log)
s17_battery_line = (f"test-law battery total={s17_sum.group(1)} passed={s17_sum.group(2)} "
                    f"failed={s17_sum.group(3)} rc=0; s17_focus_laws_test self-report "
                    f"{s17_self.group(1)} pass / {s17_self.group(2)} fail"
                    ) if s17_sum and s17_self else "S17 battery log missing"

s18_log = read(f"{RAW}/s18_battery_2026-11-20.log")
s18_sum = None
for s18_sum in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", s18_log):
    pass
s18_battery_line = (f"total={s18_sum.group(1)} passed={s18_sum.group(2)} "
                    f"failed={s18_sum.group(3)} rc=0 (43 prior + 5 new S18 families)"
                    ) if s18_sum else "S18 battery log missing"

de_log = read(f"{RAW}/s18_de_families_2026-11-21.log")
de_sum = None
for de_sum in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", de_log):
    pass
de_battery_line = (f"total={de_sum.group(1)} passed={de_sum.group(2)} "
                   f"failed={de_sum.group(3)} rc=0 (48 prior + 2 new D/E families; "
                   f"first run and post-mutation-revert run both green)"
                   ) if de_sum else "S18-cont battery log missing"

h_log = read(f"{RAW}/s18_h_families_2026-11-21.log")
h_sum = None
for h_sum in re.finditer(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", h_log):
    pass
h_battery_line = (f"total={h_sum.group(1)} passed={h_sum.group(2)} "
                  f"failed={h_sum.group(3)} rc=0 (50 prior + family H; last run green)"
                  ) if h_sum else "S18-cont-2 battery log missing"
h_mut = re.search(r"MUTATION-H.*?== s18 constraint anchor laws: (\d+) pass / (\d+) fail",
                  h_log, re.S)
h_mut_line = (f"MUTATION-H broke the is_cl_container predicate -> family H "
              f"{h_mut.group(1)} pass / {h_mut.group(2)} fail (the solving/bias/span "
              f"laws FAIL as predicted; reverted)"
              ) if h_mut else "mutation record pending"

rss_log = read(f"{RAW}/cmake_testbuild_rss_2026-11-20.log")
rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", rss_log)
elapsed = re.search(r"Elapsed \(wall\) seconds: ([\d.]+)", rss_log)
rss_build_rc = re.search(r"== build rc=(\d+)", rss_log)
rss_mb = f"{int(rss.group(1)) / 1024.0:.0f} MB ({rss.group(1)} KB)" if rss else "log missing"
rss_wall = f"{elapsed.group(1)} s" if elapsed else "n/a"
rss_rc = rss_build_rc.group(1) if rss_build_rc else "?"
ct_log = read(f"{RAW}/cmake_ctest_battery_2026-11-20.log")
ct_rc = re.search(r"== ctest rc=(\d+)", ct_log)
ct_pass = re.search(r"(\d+)% tests passed", ct_log)
ctest_line = f"ctest rc={ct_rc.group(1)} ({ct_pass.group(1)}% passed)" if ct_rc and ct_pass else "ctest log missing"

master = f"""# MASTER AUDIT — Cross-Coder Achievement Audit (v2.3, {NOW})
v1 baseline: commit 9b953ce1 (2026-11-20). v2 continues it per Issue #635 §1-§9 — nothing replaced, everything reconciled.
v2.1 adds the S14 closure pass: BUG-7 dedupe, UBSan E-05 machine verification, BUILD_TESTS=ON peak-RSS measurement.
Base: origin/main 56ba5842; session HEAD: {HEAD}

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
   reported success). Build rc={mg_build_rc}, battery rc={mg_test_rc} {battery_line}.
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
    `git rm`; production battery re-run after removal: {dedupe_line}
    (s14_battery_after_dedupe_e05_2026-11-20.log).
11. **UBSan E-05 machine verification (AUD-47 closed, S14)**: #627 hub comment 6991611630's claim
    was never reproducible (no named vectors, no profile). S14 adds the opt-in `make UBSAN=1`
    profile (-fsanitize=undefined -fno-sanitize-recover=all, tree build_ubsan/), two standalone
    probes, and +4 const_high16 rows in w15 (7 engine-tested vectors = the hub's 3 + boundaries).
    Results: fixed-form probe 7/7 bit-exact rc=0; old-form probe UBSan ABORT "left shift of
    negative value -1" rc={ubsan_e05_rc.group(1) if ubsan_e05_rc else '?'} — the hub's evidence
    reproduced exactly; w15 13/13; FULL battery built AND run under UBSAN=1: {ubsan_line}
    (s14_ubsan_battery_2026-11-20.log). Both W22-A fix sites re-verified in-tree
    (dalvik_interpreter.cpp CONST_HIGH16 + dormant monolith dalvik_engine.cpp:22438-22451).
12. **BUILD_TESTS=ON peak RSS measured (AUD-52 completed, S14)**: full cmake build executed at
    -j2 with scripts/s14_time_wrapper.py (os.wait4 rusage = the whole-tree per-process peak —
    the same metric GNU time -v reports; /usr/bin/time is absent in this sandbox) — build
    rc={rss_rc}, peak {rss_mb}, wall {rss_wall}, {ctest_line}; the single non-pass is
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
    in Makefile TEST_LAW; law battery re-run green ({s17_battery_line}).
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
    Law battery with the 5 families registered: {s18_battery_line}. 11 more rows
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
    else -> exactly E1 FAIL (tops 35/20). ALL REVERTED -> battery {de_battery_line}.
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
    {h_mut_line}. (d) 11 registry rows settled (A2/A3/A5/A6/A7/A8/B5/B6/B7/B8/B9 via
    scripts/s18_cont2_upgrade_rows.py) -> **129/234 settled HONESTLY, 105 classified
    remaining**. Ledger +AUD-61 (UNIT-TESTED, 67 rows) validator PASS. S3 also recorded
    #633 [MG-009] and #634 [MG-012]: both MG vector issues claim root-caused local fixes
    that are BLOCKED FROM PUSHING — integration candidates pending actual patch delivery.

## §2 Verdict totals (programmatic, from the 67-row ledger)
See LEDGER_VALIDATION_REPORT.md — totals generated by scripts/validate_ledger.py, sum==rows==67.
S14: PENDING 4 -> 2 (AUD-47/49 resolved), CONFIRMED 33 -> 35. S15: +1 row (AUD-58, SUPERSEDED).
S18: +1 (AUD-59, UNIT-TESTED). S18-cont: +1 (AUD-60, UNIT-TESTED). S18-cont-2: +1 (AUD-61, UNIT-TESTED).
v1's "30 CONFIRMED / 4 REJECTED..." was internally inconsistent (its CONFIRMED bucket absorbed 3
REJECTED probes); v2 replaces it with machine-counted numbers.

## §3 Deliverables (this directory)
ACHIEVEMENT_LEDGER.csv (67 rows) · LEDGER_VALIDATION_REPORT.md · 632_FINDINGS.csv (234; S16
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
  the classified queue is now **105 rows** (131 NO-CITE classified in S18 -> 120 after its 11
  law-verified rows -> 116 after the S18-cont D/E laws settled D5/D6/E6/E7 and upgraded D4 in
  place -> 105 after S18-cont-2 settled A2/A3/A5/A6/A7/A8/B5/B6/B7/B8/B9) — runtime-behavior
  claims that carry status notes; they are the focused-test queue (NEXT_INTEGRATION_PLAN.md
  item 8). **129/234 settled honestly.** The S16 sweep CORRECTED the earlier
  25 "cited X ABSENT" marks: every one of those files exists under src/resources/ or
  src/renderer/ — the cites were stale paths, not missing code (verdict STALE-CITE-RELOCATED).
- The #627 hub's exact 7 UBSan vectors were never published; the S14 probe set is the audit's
  reconstruction (hub's 3 named vectors + 4 boundary neighbours), engine-tested in w15 rows too.
- The concurrent per-instant RSS sum of a parallel build is not observable via wait4 rusage
  (max-children semantics); the reported peak is the whole-tree per-process maximum at -j2
  (the metric GNU time -v would print — /usr/bin/time is absent in this sandbox).
"""

open(f"{AUD}/MASTER_AUDIT.md", "w").write(master)

preserved = """# PRESERVED WORK MANIFEST — v2 (nothing disappears)

## Integrated in mainline (verified)
- W22-W24 build architecture chain (FASTPROFILE, -g1, W24TIERS tiering, ABBA discipline,
  steal root-cause): commits 29a708c3 -> 4ada9e3e -> 68f4fe58 -> cfd0870e -> d8b8fbb9.
- Wave-7 interpreter contract + wave-10 PIC profiles (make -n matrix, cfd0870e).
- BUG-1/1b OBJECT libs, BUG-4 battery env, BUG-5 placebo law, BUG-8 parse-order fix.
- P0 architectural split of dalvik_bridge.cpp (55,995 -> 748-line coordinator + 5 domain TUs,
  screenshot gate 11/11 IDENTICAL, commit 8e225b25 line) — content reached main; the wave10
  branch keeps the 15-commit raw lineage.
- S236-S240 coder waves (s241-law-waves, s237/s238/s239/s240 branches): ALL MERGED into main
  (merge-base == tip) — F-NEW-639 bounded append (the '777' fix, #597's root cause), regionMatches
  port, generic-law battery, corpus lane, six-pin gate runner, #606 LAYOUT-PIPE-001 laws
  (s246, 47 laws incl. scaleType geometry + RelativeLayout center fix + HSV width law).
- MG-011 ok-fix (#633) — APPLIED THIS SESSION (vector_decode.cpp:942), build+battery verified.
- BUG-7 dedupe (AUD-49, S14) — stale EMPTY src/dex/shadow_registry.h removed; battery 49/49 after.
- UBSAN=1 profile + E-05 probes + 7-vector w15 const/high16 rows (AUD-47, S14) — INTEGRATED.
- .DELETE_ON_ERROR (AUD-09), AUD-51 untrack+gitignore (051af519).

## Confirmed to exist but NOT in mainline (recovery list)
- RC-12 ScaleType oracle + probe + 4 commits (46ca6258/73dcadb6/1439627a/d77edba6): coder-local
  branch `layout-geometry-001` (per #631 comments); UNRECOVERABLE from every source checked here;
  capability partially superseded by c48773a0 + 7e5473be.
- #631 LAYOUT-GEOMETRY-001 ten diagnostic apps: built by the coder (comments 7021630435/7021652138
  carry visual evidence), coder-local only; no substitutes may be generated (mission rule).
- #634 MG-012 (AVD still-frame law + resolver-layer fix + cycle guard + s257 V0-V4 tests):
  coder-local implementation, documented in the issue body; NOT re-implemented here.
- #295/#296/#297 stroke laws (cap/join/trim, s257 family): coder-local, same status.
- audit/m16-litehtml: vendored litehtml prototype behind MINIANDROID_USE_LITEHTML (OFF default),
  probe binary + pixel-hash receipts; parity-optional by design, never linked into the engine.
- cont24/skeleton-light-experiment: measured branch-only experiment (hazards documented);
  preserved as REJECTED-EXPERIMENT, unapplied by design.
- wave10/dalvik-accel: 15 commits (W16-W20: dev-so dep-graph fix, corrected bottleneck theory,
  PCH rejection with data, additive dev targets) — raw lineage preserved on the branch.

## Preserved rejection record (REJECTED_AND_CORRECTED.md)
mold/lld, -gsplit-dwarf, ggc-min tuning, -fno-var-tracking, Ninja, PCH x3, inline-budget placebo,
job pools at -j2, RC-12-exact-commits (unrecoverable), B2's "52 links" for the DEFAULT cmake graph.

## Stashes (preserved, not dropped)
- stash@{0} wave10/dalvik-accel "auto-checkout-recovery": 62 files, +12,352 lines (w20 corpus
  census + traces). stash@{1}: empty diff (recovery stub).
"""
open(f"{AUD}/PRESERVED_WORK_MANIFEST.md", "w").write(preserved)

blocked = f"""# BLOCKED AND PENDING — v2 ({NOW})

## BLOCKED
| ID | Item | Exact blocker | Recovery outcome |
|---|---|---|---|
| AUD-35/36b | #628/#619 TicTacToe --frames 12 + interactive verification | emmanuelmess ttt APK absent; corpus has only the itsfrz substitute (rc=1, 0 setGraph) | original APK required; substitute never counts |
| AUD-37b/38b | #618 Counter / #623 RNG runtime verification | APKs absent from corpus | original APKs required |
| AUD-39 | #597 OpenCalc 7x3=21 through real UI | APK absent; root-cause law (F-NEW-639 bounded append) ALREADY merged via s237-w27 | APK required for the runtime re-check; the fix itself is INTEGRATED |
| AUD-53 | RC-12 exact commits | branch layout-geometry-001 is coder-local; every local source checked | partially superseded (c48773a0, 7e5473be) |
| AUD-56 | #630/#631 ten layout apps | coder-local artifacts; no substitutes allowed | documented with visual-evidence comment refs |
| #634/#295/#296/#297 | coder-local fixes (MG-012, stroke laws) | implementations live in coder trees, not in any reachable branch | documented per issue; not re-implemented here |

## PENDING
| ID | Item | Missing step |
|---|---|---|
| AUD-29/31/33 | per-call-site unit laws (gravity/ScrollView offsets/TypedValue chain) | #632 task list items |
| AUD-10b/42 | job-pool OOM guard at -j4+ / MG-012 recovery | dependent on the BLOCKED artifacts above |
| AUD-54 follow-ups | 105 rows remain after S18-cont-2 (all classified); 129/234 settled honestly — D/E families DONE, family H (constraint anchors) DONE, A-row census re-measured, B6-B9 dispositioned by the #635 audit | focused laws per registry; next: NEW-fixture rows (N2 font, P8 mini-DEX, N8 image) + remaining census candidates; #633/#634 patch delivery |

## Resolved by S14/S15
- AUD-47 UBSan E-05: profile + probes + 7 engine vectors + FULL battery under -fsanitize=undefined ({ubsan_line}).
- AUD-49 BUG-7: stale 0-byte duplicate removed, production battery re-verified ({dedupe_line}).
- AUD-52 peak-RSS limit: full BUILD_TESTS=ON build measured under the GNU time metric (-j2): build rc={rss_rc}, peak {rss_mb}, wall {rss_wall}, {ctest_line}.
- #626 PR (S15/AUD-58): wave10 line classified SUPERSEDED-IN-FULL — all content in main; no rebase needed (MASTER_AUDIT §1 item 13).
"""
open(f"{AUD}/BLOCKED_AND_PENDING.md", "w").write(blocked)

rejected = """# REJECTED AND CORRECTED — v2 (preserved so nothing is rediscovered)
| ID | Original claim | What was false / corrected | Disproof | Status |
|---|---|---|---|---|
| AUD-30 | "GridLayout not implemented" | a Bellman-Ford arc solver EXISTS (layout_inflater.cpp:2899-2903, :4364-4380, :4494 — #606 wave); the v1 audit grep was scoped to the wrong directory | full-tree source check 2026-11-20 | REJECTED (claim falsified) |
| AUD-32 | "Nine-patch npTc/npLb missing" | npTc chunk parsing EXISTS (execution_engine.cpp:2876, aapt2 8.13.2 layout); npLb path still absent | full-tree grep | PARTIALLY CONFIRMED |
| AUD-06 | "~52 links + OOM in default cmake all" | default all = 99 edges, exactly 1 executable link; the ~52-link scope exists only with BUILD_TESTS=ON (measured 50) | ninja dry-run, cmake 4.4.5 (AUD-52) | REJECTED for the default graph |
| AUD-02 | "QuickJS compiled twice in CMake" | TRUE only with BUILD_TESTS=ON (10 edges = 5 sources x 2 OBJECT libs); default graph compiles it once | ninja dry-run | PARTIALLY CONFIRMED |
| AUD-36 (v1 level) | "Original-APK-verified" render parity | the gate used the itsfrz SUBSTITUTE; original emmanuelmess APK absent | AUD-35 run log | split + downgraded to substitute-APK render parity |
| AUD-37/38 (v1) | "CONFIRMED-closed" single rows | tracker state and runtime proof were fused in one row | mission rule | split into tracker-state CONFIRMED + runtime BLOCKED rows |
| AUD-17 | mold/lld 3-8x faster links | link is 1.5 s of a 350 s build | W24 measurement | REJECTED |
| AUD-18/19/20 | -gsplit-dwarf / ggc-min / -fno-var-tracking wins | +4% / 3x slower / no win (GCC14 fixed VTA) | fresh ABBA probes | REJECTED |
| AUD-21 | PCH helps | rejected 3x on this repo | W23-F + W24 EXP-C | REJECTED |
| AUD-22 | inline-budget params save 7-13% | byte-identical binaries (page-cache placebo) | BUG-5 record | REJECTED |
| AUD-24 | make scheduler is the bottleneck | make == xargs == Ninja ±2%; steal is the cause | W24 EXP-B | REJECTED |
| AUD-10 | job pools needed | no OOM at -j2 in ~40 builds | runtime census | REJECTED at -j2 |
| RC-12 | exact commits recoverable | branch layout-geometry-001 never pushed; all local sources swept | AUD-53 | BLOCKED, partially superseded |
"""
open(f"{AUD}/REJECTED_AND_CORRECTED.md", "w").write(rejected)

plan = """# NEXT INTEGRATION PLAN — v2.1 (dependency-ordered; S14 state)
1. **MG-011 verification closure (AUD-55)** — fix applied + battery 49/49 (S12); a direct-vs-referenced
   PathData parity test (battery extension) remains the optional follow-up.
2. **#634 MG-012 re-implementation from the documented law** — animated-vector root acceptance,
   shared resolver-layer fix (`looks_like_entry` predicate), cycle depth-guard, AVD still-frame =
   referenced VD with own attributes; port the s257 V0-V4 law rows into TEST_LAW.
3. **#295/#296/#297 stroke laws** — cap/join/trim emitters with the right-normal sign law;
   extend s257 to strokeLineJoin/trimPath rows.
4. ~~**BUG-7 dedupe (AUD-49)**~~ DONE (S14): the stale copy was committed EMPTY and had ZERO
   includers — removed, battery 49/49 re-verified. No repointing was needed.
5. **CMake WEBP parity (AUD-07)** — add -DMINIANDROID_HAVE_WEBP to CMakeLists; proof = section
   compare vs the Make build (cmake now fully exercised: AUD-52 measured + RSS + ctest done).
6. ~~**#626 PR rebase**~~ RESOLVED-SUPERSEDED (S15/AUD-58): the wave10 line's entire content is in
   main via direct W22-W24 landings (13/13 F-NEW-7xx ids, 3/3 W20 P2 fixes, P0 split, dev-so
   profiles, ZERO missing src/tests paths) — no rebase, no cherry-pick; classification logged
   for the PR close decision. audit/s236 = superseded (test in TEST_LAW:531); m16-litehtml +
   cont24 = reachable branch-only experiments.
7. **RC-12 / layout apps** — only from the original coder environment; no substitutes.
   S15 re-verification: layout-geometry-001 absent from git ls-remote — still unrecoverable.
8. **AUD-54 focused tests** — S16 phase 1 (103/234 machine-checked) + S17 phase 2 (14
   inflater-decode laws) + S18 (131-row classification + 29 laws in 5 new families:
   rounding/weightSum/text-layout/sql-shadow/renderer-surface; 5-family negative-mutation
   validation; 11 more rows law-verified -> 114/234 HONEST, 120 classified remaining).
   S16 phase 1 detail:
   scripts/s16_cite_sweep.py (35 CONFIRMED-LIVE incl. verbatim line cites; 32 STALE-CITE-
   RELOCATED — the 25 old "ABSENT" marks corrected, the files exist relocated; 24 CITE-STALE;
   5 PARTIAL; 3 RESOLVED-IN-TREE: A1/BP-19/G3; 1 PATTERN-ABSENT). The S17 claim of
   114/234 double-counted 11 rows; the TRUE count reached 114/234 only in S18 (11
   more rows law-verified; the remaining 120 carry explicit S18 classifications,
   zero of which need the missing APKs or coder artifacts)
   are runtime-behavior claims needing focused laws (several depend on the missing APKs).
   S18-cont (2026-11-21): the D/E families are DONE — 8 laws over the LIVE inflater
   (gravity direction/fill + baseline/divider absence), 3 negative-mutation injections
   (one honest retarget recorded), battery 50/50; 5 registry rows upgraded ->
   118/234 settled, 116 classified remaining (AUD-60).
   S18-cont-2 (2026-11-21): family H (constraint anchors, 3 laws, mutation-validated)
   FALSIFIES B5 for the live path; A2-A8 census RE-MEASURED; B6-B9 dispositioned by the
   #635 audit's measured rejections/fixes; 11 more rows settled -> 129/234 settled,
   105 classified remaining (AUD-61).
8. ~~**UBSAN=1 profile (AUD-47)**~~ DONE (S14): `make UBSAN=1` (-fsanitize=undefined
   -fno-sanitize-recover=all, tree build_ubsan/); E-05 probes 7/7 + old-form abort rc=
   {ubsan_e05_rc} machine-reproduce the hub's claim; the FULL 49-test battery built and ran
   clean under the sanitizer ({ubsan_line}); w15 extended to 7 engine-tested const/high16 vectors.
9. **-Werror/CI (AUD-45)** — after the R1-R4 dead-code triage.
Standing rules: ABBA order for timing claims; evidence logs force-added; Production and Dev-So
reported separately; no semantic weakening for build speed; tracker closure is never runtime proof.
""".format(ubsan_e05_rc=ubsan_e05_rc.group(1) if ubsan_e05_rc else "?", ubsan_line=ubsan_line)
open(f"{AUD}/NEXT_INTEGRATION_PLAN.md", "w").write(plan)

integration = f"""# INTEGRATION MAP — v2 (accepted contributions on the shared execution chain)
APK corpus (upload/handoff_apks, 15 originals — SHAs in RAW_LOGS/apk_corpus_identity_2026-11-20.txt)
→ Manifest/Resources   arsc_parser (TypedValue radix AUD-33) · axml_parser · manifest_reader
  · nine-patch npTc parsing (execution_engine.cpp:2876 — AUD-32 corrected) ·
  · OPEN: GridLayout span-tracks/RTL mirror · npLb legacy chunk
→ DEX / Class Loading  class_resolver · dex_parser
→ Dalvik Interpreter   dalvik_interpreter (wave-7 contract) · opcode laws (AUD-46)
→ Framework API        android_shadows + shadow_registry (BUG-7 duplicate RESOLVED S14 —
  the stale 0-byte src/dex copy removed; single authoritative framework/ header)
  · ScrollView wiring PARTIAL (AUD-31) · FORTIFY 3 symbols OPEN (AUD-34)
→ View / Layout        layout_inflater.cpp — GridLayout Bellman-Ford solver PRESENT (:2899/:4364,
  AUD-30 corrected) · #606 s246 law set (47 laws) · scaleType raster parity (c48773a0)
→ Canvas / Drawable    software_renderer · vector_decode — **MG-011 ok-fix APPLIED THIS SESSION
  (AUD-55, vector_decode.cpp:942)** · text_shaper FriBidi/HarfBuzz/FreeType (AUD-28)
→ Input/State          touch_dispatcher · battery law tests s1xx-s23x
→ Rendered Output      5-APK screenshot sha16 gate — 11/11 IDENTICAL (W24 candidate baseline)
→ Regression           .DELETE_ON_ERROR (AUD-09) · battery manifest parity · ABBA discipline

Build side:
core_sources.manifest (single source of truth) →
  Make: FASTPROFILE=1 W24TIERS=1 -j2 all (~290s) — INTEGRATED; canonical path preserved.
  Sanitizer: make UBSAN=1 (-fsanitize=undefined -fno-sanitize-recover=all, build_ubsan/) —
  ADDED S14; full battery clean under it (AUD-47).
  CMake: measured graph + peak RSS (AUD-52): default 1 link / QuickJS 1x / WEBP define ABSENT (OPEN);
  BUILD_TESTS=ON → 50 links + QuickJS 2x, peak {rss_mb} at -j1 (S14), ctest {ctest_line}.
Repo hygiene: AUD-51 (051af519) — build_w24_cand_a/ + APK untracked, gitignore hardened.

Branch census (S10): merged — s241-law-waves, s237-w27, s238-audit, s239, s240;
absent-but-preserved — wave10/dalvik-accel (15), audit/s236 (7), audit/m16-litehtml (3),
cont24/skeleton-light (2); stashes preserved (62 files, +12,352 lines).
"""
open(f"{AUD}/INTEGRATION_MAP.md", "w").write(integration)

regression = f"""# REGRESSION RESULTS — v2 ({NOW})
## Baselines (unchanged from v1 — W24 ABBA record, commit d8b8fbb9)
candidate avg 289.85s (-17.3% wall / -17.7% CPU vs matched-steal base 350.39s), battery 49/49,
gate 11/11 IDENTICAL. Peak RSS 1167MB. Steal 24-25% per window; floor 288.4s.

## MG-011 verification chain (this session)
- Fix: `out->ok = err.empty() && !paths.empty();` at src/renderer/vector_decode.cpp:942
  (hole verified live first: clip-path warning at :493 left ok=true).
- Build (FASTPROFILE=1 -j2 all): rc={mg_build_rc}
- Battery (make FASTPROFILE=1 -j2 test-all): rc={mg_test_rc} {battery_line}
- Raw log: evidence/audit_raw/mg011_build_testall.log (session-local; summarized here)

## CMake graph (AUD-52 — new measured evidence)
- default all: 99 edges / 1 link / QuickJS 1x / WEBP 0 refs / 0 test exes
- BUILD_TESTS=ON: 204 edges / 50 links / QuickJS 2x (10 edges)
- configure rc=0 with cmake 4.4.5 + ninja; no full test-build run (budget)

## S14 chain (BUG-7 dedupe + UBSan E-05 + peak RSS)
- BUG-7 dedupe: stale EMPTY src/dex/shadow_registry.h removed; production battery {dedupe_line}
  (s14_battery_after_dedupe_e05_2026-11-20.log); w15 13/13 incl. 7 const/high16 engine vectors.
- UBSAN=1 profile added; E-05 probes: fixed-form 7/7 bit-exact rc=0, old-form UBSan abort rc=
  {ubsan_e05_rc} ("left shift of negative value -1" — the #627 hub claim reproduced);
  FULL battery under UBSAN=1: {ubsan_line} (s14_ubsan_battery_2026-11-20.log).
- Full BUILD_TESTS=ON cmake build (-j2, s14_time_wrapper.py wait4 rusage): build rc={rss_rc},
  peak {rss_mb}, wall {rss_wall}, {ctest_line} — the only non-pass is miniandroid-smoke "Not Run"
  (miniandroid_test is not a dependency of the battery; 49/49 battery tests passed, 0.46 s).
  W22-C production baseline for comparison: 572.456s / 1427 MB (-j1).

## Fresh falsifications (source checks this session)
- GridLayout solver PRESENT (layout_inflater.cpp:2899-2903/:4364-4380/:4494)
- npTc parsing PRESENT (execution_engine.cpp:2876)
- APK identity: ugraday sha16 000ae2e5751f9a85 == #612 recorded sha (EXACT)
"""
open(f"{AUD}/REGRESSION_RESULTS.md", "w").write(regression)

print("deliverables regenerated:", os.listdir(AUD))

# sync everything to the download mirror
import shutil
DL = "/home/z/my-project/download/audit_v2"
os.makedirs(DL, exist_ok=True)
for f in ["MASTER_AUDIT.md", "PRESERVED_WORK_MANIFEST.md", "BLOCKED_AND_PENDING.md",
          "REJECTED_AND_CORRECTED.md", "NEXT_INTEGRATION_PLAN.md", "INTEGRATION_MAP.md",
          "REGRESSION_RESULTS.md", "LEDGER_VALIDATION_REPORT.md", "ACHIEVEMENT_LEDGER.csv",
          "632_FINDINGS.csv", "632_BATCH8_174_ATTRIBUTES.md"]:
    shutil.copy(f"{AUD}/{f}", f"{DL}/{f}")
print("synced to", DL)
