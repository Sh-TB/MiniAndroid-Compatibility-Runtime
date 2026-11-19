# W23 BUILD BASELINE (reproduced before any change)

Mission: W23 — Deep Build Architecture Optimization.
Everything in this file was measured on the W22-F tree at `origin/main`
`23a4d33b`, working tree clean except W23 bench comment lines appended by the
probe harness (comment-only, no semantic change).

## Environment (re-measured this session)

| Field | Value |
|---|---|
| HEAD | 23a4d33b (origin/main, clean) |
| Compiler | g++ (Debian 14.2.0-19) 14.2.0 |
| Build system | GNU Make 4.4.1; cmake binary restored portable 3.28.6 during W23 (sandbox recycle wiped it) |
| CPU / RAM | 2 cores, 4041 MB total, ~3066 MB available, no swap |
| Disk | 6.2 GB free |
| ccache | restored portable 4.10.2 (was absent after sandbox recycle) |
| Production flags | `-std=c++17 -Wall -Wextra -g -O2 -MMD -MP` + per-TU contract overrides (split parts `-g0`, interpreter `-g0`+inline budget) |

## W23-01 baseline matrix (this session, before any W23 change)

| Operation | Wall | CPU (u+s) | Peak RSS | Compiles | Links | vs W22 |
|---|---:|---:|---:|---:|---:|---|
| Fresh production clean build (`rm -rf build; make -j1 --output-sync all`) | **591.64 s** | 567.4+20.7 | 1461 MB | 88 | 1 | W22 572.46 s (+3.4 % session noise) |
| dev-so clean build (`make -j1 dev-so`) | **132.97 s** | 124.5+8.2 | 1147 MB | — | — | W22 126.5 s (+5 %) |
| No-op rebuild (×3) | **1.06 s** median (1.04–1.10) | — | — | 0 | 0 | W22 1.07 s ✓ |
| Leaf edit (dalvik_value_glue.cpp) ×3 | **2.05 s** median | — | — | 1 | 1 | W22 2.17 s ✓ |
| Opcode edit (dalvik_opcodes.cpp) ×3 | **11.86 s** median | — | — | 1 | 1 | — (new probe) |
| Bridge edit (dalvik_bridge.cpp) ×3 | **9.44 s** median | — | — | 1 | 1 | W22 8.80 s ✓ |
| Interpreter edit (dalvik_interpreter.cpp) ×3 | **23.50 s** median | — | — | 1 | 1 | W22 20.43 s slot ✓ |
| Private header edit (dalvik_engine_internal.h) ×1 | see probes_baseline.jsonl | | | | | |
| Public header edit (dalvik_engine.h) ×1 | see probes_baseline.jsonl | | | | | |
| Common header edit (android_shadows.h) ×1 | see probes_baseline.jsonl | | | | | |

Raw logs: `evidence/w23/prod_build_fresh.log` (timestamped),
`evidence/w23/devso_clean_build.log`, `evidence/w23/build_bench.jsonl`,
`evidence/w23/probe_logs/*.log`, per-probe records in
`evidence/w23/probes_baseline.jsonl` (each record validates: rc, compiled-TU
set, link count, edited-TU-recompiled check).

Binary sha256 (fresh build, HEAD 23a4d33b): `749ecde7a4626e892a0d6f01c7b7c934…`

## Ground-truth include fan-out (from the fresh build's gcc -MMD .d files)

Computed by `scripts/w23_fanout_from_d.py` over `build/**/*.d` (the compiler's
own dependency closure for the 88 linked slots — not a text approximation).

| Header | fan-out (linked TUs) | estimated cascade (W22 slot weights) |
|---|---:|---:|
| src/framework/shadow_registry.h | 29 | 163.9 s |
| nlohmann/json.hpp (all spellings) | 22 (18+16 via two spellings) | 306.0 s |
| src/dex/dex_parser.h | 19 | 294.3 s |
| src/dex/class_resolver.h | 18 | 290.4 s |
| src/dex/c7_package_index.h | 17 | 286.5 s |
| src/dex/../apk/manifest_reader.h | 17 | 286.5 s |
| src/dex/../api/android_stubs.h | 17 | 286.5 s |
| **src/dex/dalvik_engine.h** | **16** | **282.6 s** |
| src/dex/dalvik_engine_internal.h | 12 | 216.2 s |
| src/framework/android_shadows.h | 13 | 101.5 s |
| src/dex/dalvik_bridge_frame.h | 6 | 140.6 s |

Reading: the engine.h cascade is the union of (a) the 12+ engine-family TUs,
(b) `application_runtime.cpp` (direct), (c) the trace chain
(`trace_exporter.h` → `execution_engine.cpp`). The 13 project headers included
by `dalvik_engine.h` reach MORE TUs than engine.h itself (dex_parser.h 19 >
engine.h 16) because dex-family headers are consumed outside the engine family
too — the split must therefore cut at the CLASS boundary (the only
engine-internal content), not merely reshuffle includes.

## Interpretation

1. The W22 numbers reproduce within noise (+3–5 %); the W23 baseline is valid.
2. The header cascade remains the dev-loop killer; a comment-line edit to
   `dalvik_engine.h` costs ≈336 s (re-measured this session, see probes file).
3. Clean-build cost is real -O2 codegen work spread over 88 slots (top-10 =
   45.8 %); the link is 0.9 s — linking and flags are NOT the clean-build
   bottleneck on 2 cores.
