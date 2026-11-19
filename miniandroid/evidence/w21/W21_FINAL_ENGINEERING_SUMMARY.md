# W21 FINAL ENGINEERING SUMMARY

Commits (in order): c1602b75 (Phase 0+3) -> 695df54f (Phase 4 + audit + s235 fix) ->
0d6734f2 (Phase 2 + Options field law) -> (this commit: Phase 5-8 artifacts).
Remote: origin/main; rollback tag w20-k2-rollback-568a9380. No force-push/reset.

## ACCEPTED (with reproducible evidence)
1. W20-K history + source integrity proven (audit MD §1): 8d2583b7 on origin/main;
   671d2577 NOT a commit ancestor (wave10/dalvik-accel tip) — content equivalence
   proven by diff; W20-P2 markers verified; CMake parity loss FOUND AND FIXED.
2. WS5-WS9 accepted with contract tests + fresh 48/48 battery (s235 harness gap
   fixed with the coder's own law; s98 mis-attribution corrected — it PASSES).
3. WS4B CLOSED: 2048 board-interactive on real swipes (4 directions, x3
   deterministic, default-off byte-identical) — five stacked root causes fixed with
   shared CSS/W3C/DOM laws (float layout, translate transforms, W3C implicit touch
   capture, cascade invalidation, hit-chain correctness).
4. SolitaireCG + Frozen Bubble VERIFIED with the ORIGINAL F-Droid APKs that match
   the coder's pinned hashes byte-for-byte; coder's crash absent; board face =
   coder's receipt hash; Frozen Bubble false-final-field IAE fixed (0 exceptions,
   37,988-color GL render x3 deterministic).
5. 15x5 runtime baseline with CPU + peak RSS per run (W20-K2's missing fields):
   W21_RUNTIME_BASELINE.csv/md; 15/15 screenshot shas byte-identical vs W20-K2
   (per-phase); chess = CPU-bound at the 60s cap (888MB RSS).
6. Full production build re-measured with real instrumentation: 555.6s wall,
   peak RSS 1,462,816 KB = 1.46 GB (matches the W20-K claim; that claim had NO
   committed build log — recorded as missing evidence).
7. test-all certified 48/48 (wall 288.4s, measured).

## MEASURED-BUT-NOT-IMPLEMENTED (honest scope)
- Runtime optimization: gprof (-pg build, chess/tallybook/minos/HelloWorldToast)
  shows the top hotspot is per-invoke/instruction container churn (set dtors 34.8%
  + map clear 13.7% + HeapObject copies 4.2%) and periodic whole-heap clones — NOT
  any of the three mission hypotheses (A partially supported at ~5.5%, B/C not in
  the top-10). Per the evidence-first law, NO optimization was implemented in W21;
  the ranked measured plan for the next session is in W21_RUNTIME_HOTSPOT_REPORT.md
  and W21_RUNTIME_OPTIMIZATION_RESULTS.csv.

## PENDING (not finished, why)
- GitHub issue comments (#627/#612): NOT posted this session — the remaining step
  budget went to closing WS4B + the two APK verifications; the comment texts should
  be assembled from the deliverables below (all committed + pushed).
- Game-over/restart flow for 2048 (inline <a> hit-testing gap + no multi-gesture
  CLI), a2048_25 boot blocker (3 NPEs), DrawPortraitCards REC-MISS arm,
  cross-run localStorage board persistence — recorded in the playability/APK
  reports.
- The optimization implementation + 5-rep acceptance pass (next session, plan ready).

## Deliverable index (all under miniandroid/evidence/w21/ unless noted)
W21_W20K_INTEGRATION_AUDIT.md, W21_W20K_TEST_EVIDENCE.csv,
W21_PLAYABILITY_2048_REPORT.md, W21_APK_VALIDATION_REPORT.md,
W21_RUNTIME_BASELINE.csv/.md, W21_RUNTIME_TRACE_SUMMARY.md,
W21_RUNTIME_HOTSPOT_REPORT.md, W21_RUNTIME_OPTIMIZATION_RESULTS.csv,
W21_BUILD_TIME_COMPARISON.csv (all also mirrored to download/w21/),
plus raw evidence: runtime_baseline.tsv, runtime_perf/, gprof/, apk_src/,
a2048_probe/, solcg_3041_runs/, frozenbubble_*, w21_testall_final.log,
w21_baseline_run.log, runner JSONs.
