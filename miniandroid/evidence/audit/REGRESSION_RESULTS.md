# REGRESSION RESULTS — v2 (2026-11-20 (continuation session))
## Baselines (unchanged from v1 — W24 ABBA record, commit d8b8fbb9)
candidate avg 289.85s (-17.3% wall / -17.7% CPU vs matched-steal base 350.39s), battery 49/49,
gate 11/11 IDENTICAL. Peak RSS 1167MB. Steal 24-25% per window; floor 288.4s.

## MG-011 verification chain (this session)
- Fix: `out->ok = err.empty() && !paths.empty();` at src/renderer/vector_decode.cpp:942
  (hole verified live first: clip-path warning at :493 left ok=true).
- Build (FASTPROFILE=1 -j2 all): rc=0
- Battery (make FASTPROFILE=1 -j2 test-all): rc=0 battery 49/49 PASS rc=0 (first run hit ENOSPC — rerun clean; both records in the log)
- Raw log: evidence/audit_raw/mg011_build_testall.log (session-local; summarized here)

## CMake graph (AUD-52 — new measured evidence)
- default all: 99 edges / 1 link / QuickJS 1x / WEBP 0 refs / 0 test exes
- BUILD_TESTS=ON: 204 edges / 50 links / QuickJS 2x (10 edges)
- configure rc=0 with cmake 4.4.5 + ninja; no full test-build run (budget)

## Fresh falsifications (source checks this session)
- GridLayout solver PRESENT (layout_inflater.cpp:2899-2903/:4364-4380/:4494)
- npTc parsing PRESENT (execution_engine.cpp:2876)
- APK identity: ugraday sha16 000ae2e5751f9a85 == #612 recorded sha (EXACT)
