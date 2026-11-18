# WAVE-8 Incremental Rebuild Map — per edit type (before → after)

Baseline measured this session (fresh-process): no-op `make all` 1.07 s-class behavior
reproduced via gate runs; production static path untouched.

| Edit | Static path (before) | Dev .so path (after) |
|---|---|---|
| opcode impl `.cpp` | 1 compile (9.6–17.5 s) + **3 test relinks (12.5 s)** + run | 1 PIC compile (9.6 s) + .so relink 0.18 s + run 0.02 s → **9.8 s total** |
| interpreter impl | 1 compile (21.8 s) + 3 test relinks + run → 36.4 s | 1 PIC compile (20.8 s) + 0.18 s + 0.02 s → **21.0 s total** |
| bridge impl | 1 compile (43.7 s) + 3 test relinks | 1 PIC compile (40.3 s @ 2155 MB) + 0.18 s → **~40.6 s** |
| stable core object (framework etc.) | 1 compile + 3 test relinks | 1 compile + affected test exe relink (~5 s, debug intact) |
| `dalvik_engine_internal.h` | 7 compiles (158 s) + 3 test relinks | 7 PIC compiles + 0.18 s .so (test exes untouched) |
| test source `.cpp` | 1 test relink | same (test exe relink, small delta) |
| Makefile | full re-eval, stamps guard | unchanged |
| no-op | ~1.07 s | ~1.07 s (build_dev_so scripts are explicit-step; no graph) |

## Unnecessary work found & fixed

1. **Proven unnecessary**: every engine edit relinked all 3 test exes (12.5 s) even though
   only the runtime code changed — fixed by the .so boundary (zero test relinks per engine
   edit). This was the single largest avoidable term.
2. No unnecessary recompilation found: dep-file/stamp machinery already correct (wave-5/7
   evidence re-confirmed: per-TU edits rebuild exactly 1 TU).

## Targets vs measured (honest)

| Target | Measured | Status |
|---|---|---|
| Opcode edit→test <10 s | 9.6–9.8 s (×2) | MET |
| Interpreter <15 s (stretch) / <30 s | 20.7–21.1 s (×3) — compile-bound (20.5–20.9 s) | <30 MET; <15 PARTIAL (blocker = interpreter TU compile cost itself) |
| Bridge <30 s | ~40.6 s | PARTIAL (unchanged blocker: 55K-line function compile at -Og 2155 MB) |
| No-op <0.5 s | ~1.07 s | PARTIAL (make overhead; make-independent loop scripts show 0.02 s test step) |
| Peak RSS <4 GB | 2155 MB (bridge PIC), ld 563 MB | MET |
| No unnecessary full relink per ordinary edit | zero test-exe relinks per engine edit | MET |
| No runtime regression | 3-APK hashes identical + battery 3/3 | MET |
