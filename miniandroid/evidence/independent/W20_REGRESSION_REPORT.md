# W20 REGRESSION REPORT (K2 session)

- Tree: local main merged with origin/main (wave-9, 4 commits) — conflicts
  resolved to the verified W20 tree; pushed ca380f4d. Wave-9 evidence file
  kept (theirs); split TUs kept OURS (built green 539.7s / 1.46GB).
- Battery: 48 tests; 47 PASS (the 1 = pre-existing s98 font-env lineage).
- New contract tests: s248 10/10, s249 4/4, s250 8/8, s251 4/4, s252 9/9.
- APK parity: pz sha ceb1a6adf7ba1391 = W19 gate baseline (unchanged);
  minos 3x deterministic b5a7a35d5fe0564b; per-APK shas stable across reps
  in the new baseline (runtime_baseline.tsv).
- No runtime behavior change without its focused test (WS5-WS9 all shipped
  with tests this lineage).
