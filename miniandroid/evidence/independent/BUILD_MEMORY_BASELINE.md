# BUILD MEMORY BASELINE (two-host, two-era — never compared across)

## HISTORICAL (independent coder host — preserved verbatim, NOT current)
g++ 8.3.0, GNU Make 4.2.1, 2 CPUs, ~2.09GB RAM, no swap, no ccache/ninja/cmake, ~457MB free disk.
| TU | lines | isolated compile | peak RSS | result |
|---|---|---|---|---|
| dalvik_interpreter.cpp | 6,300 | 6.85s | 849MB | PASS |
| android_shadows.cpp | 11,904 | 5.22s | 551MB | PASS |
| dalvik_engine_invoke.cpp | 12,091 | 8.02s | 874MB | PASS |
| dalvik_bridge.cpp | 55,398 | 43.2s | 1,823MB | **OOM at -O2** |
Header fan-outs measured: dalvik_engine.h 14/98 TUs, android_shadows.h 27/98.
This bottleneck was STRUCTURALLY SOLVED by the P0 split (C-02) + W20 dependency
fixes (C-04), on THIS lineage.

## CURRENT W20 host (g++ 14.2.0, GNU Make 4.4.1, 4GB cgroup)
| operation | wall | peak RSS |
|---|---|---|
| full production build (all -j1) | 539.7s | 1.46GB |
| unchanged incremental | 1.0s | ~34MB |
| single domain TU (dev -O0) | 9.1s | ~1.08GB (prod -O2) |
| ordinary source edit | 25.9s | ~1.10GB |
| production header cascade (TRUE, post-F1) | 401.8s (28 TUs) | 1.46GB |
| test-all (48 tests) | ~234s | ~0.78GB |
Pre-split regression observed this wave: the 55K monolith at -O2 OOM-killed
cc1plus at 3.09GB on THIS host too — the split is load-bearing, keep it.
