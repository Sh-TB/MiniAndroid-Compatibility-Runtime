# WAVE-8 Experiment Matrix (labels honest; reps stated)

Env: g++ 14.2.0 · ld.bfd 2.44 · 2 CPUs · 4 GB cgroup · offline · -j1. Each experiment
isolated; production build untouched throughout.

| # | Configuration | Result | Label |
|---|---|---|---|
| A | Current static dev/test build (baseline, reproduced) | interpreter gate 23.9 s compile + 12.5 s test = 36.4 s; ld RSS 563 MB | TESTED (reproduced) |
| B | Static link + `-Wl,--strip-debug` | gp582: 5.03 s vs 4.78 s full-debug — SLOWER (ld merges debug before discard) | TESTED → REJECTED (measured) |
| C | Shared-library dev path (PIC dalvik set → libminiandroid_dalvik.so, stable set static) | interpreter loop 20.7–21.1 s ×3; opcode 9.6–9.8 s ×2; .so relink 0.18 s ×7; battery 3/3 PASS; 3-APK hashes IDENTICAL to canonical | TESTED → ADOPTED (isolated build_dev_so/) |
| C-1 | Non-PIC .so from existing objects | `R_X86_64_TPOFF32` (TLS) hard error; -z notext insufficient | TESTED → BLOCKED (factual) |
| D | Alternative linkers (gold/lld/mold) | `find / -name ld.gold -o -name ld.lld -o -name mold` → zero hits; apt blocked (not root) | BLOCKED (offline evidence) |
| E | Partitioned static archives for test links | not built — superseded by C (archive member extraction cannot avoid the debug-merge cost; C removes it entirely) | SUPERSEDED |
| F | ccache | binary absent, no root | BLOCKED (offline, evidence in w7/w8) |

Cold/warm: C's one-time cost = 114.6 s PIC recompiles (cold); warm loops are the numbers
above. Benchmark JSON: `wave8_benchmarks.json` (raw loop triples). Parity:
`wave8_runtime_parity.json`.

## Fair-comparison notes

Same compiler, flags (production-equivalent + -fPIC for the volatile set), source state, and
4 GB limit across A and C. Loop timings = fresh-process wall for compile+link+tests, no
parallelism (memory rule). Fastest-run-only never reported; medians shown in the JSON.
