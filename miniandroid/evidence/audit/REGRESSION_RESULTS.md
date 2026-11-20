# REGRESSION RESULTS — v2 (2026-11-20 (continuation session, S12+S14))
## Baselines (unchanged from v1 — W24 ABBA record, commit d8b8fbb9)
candidate avg 289.85s (-17.3% wall / -17.7% CPU vs matched-steal base 350.39s), battery 49/49,
gate 11/11 IDENTICAL. Peak RSS 1167MB. Steal 24-25% per window; floor 288.4s.

## MG-011 verification chain (this session)
- Fix: `out->ok = err.empty() && !paths.empty();` at src/renderer/vector_decode.cpp:942
  (hole verified live first: clip-path warning at :493 left ok=true).
- Build (FASTPROFILE=1 -j2 all): rc=PENDING (build still running)
- Battery (make FASTPROFILE=1 -j2 test-all): rc=PENDING (build still running) 
- Raw log: evidence/audit_raw/mg011_build_testall.log (session-local; summarized here)

## CMake graph (AUD-52 — new measured evidence)
- default all: 99 edges / 1 link / QuickJS 1x / WEBP 0 refs / 0 test exes
- BUILD_TESTS=ON: 204 edges / 50 links / QuickJS 2x (10 edges)
- configure rc=0 with cmake 4.4.5 + ninja; no full test-build run (budget)

## S14 chain (BUG-7 dedupe + UBSan E-05 + peak RSS)
- BUG-7 dedupe: stale EMPTY src/dex/shadow_registry.h removed; production battery battery 49/49 PASS rc=0
  (s14_battery_after_dedupe_e05_2026-11-20.log); w15 13/13 incl. 7 const/high16 engine vectors.
- UBSAN=1 profile added; E-05 probes: fixed-form 7/7 bit-exact rc=0, old-form UBSan abort rc=
  <re.Match object; span=(1587, 1601), match='ubsan-e05 rc=0'> ("left shift of negative value -1" — the #627 hub claim reproduced);
  FULL battery under UBSAN=1: probes rc=0, battery 49/49 rc=0 (s14_ubsan_battery_2026-11-20.log).
- Full BUILD_TESTS=ON cmake build (-j2, s14_time_wrapper.py wait4 rusage): build rc=0,
  peak 1235 MB (1264520 KB), wall 491.91 s, ctest rc=8 (98% passed) — the only non-pass is miniandroid-smoke "Not Run"
  (miniandroid_test is not a dependency of the battery; 49/49 battery tests passed, 0.46 s).
  W22-C production baseline for comparison: 572.456s / 1427 MB (-j1).

## Fresh falsifications (source checks this session)
- GridLayout solver PRESENT (layout_inflater.cpp:2899-2903/:4364-4380/:4494)
- npTc parsing PRESENT (execution_engine.cpp:2876)
- APK identity: ugraday sha16 000ae2e5751f9a85 == #612 recorded sha (EXACT)
