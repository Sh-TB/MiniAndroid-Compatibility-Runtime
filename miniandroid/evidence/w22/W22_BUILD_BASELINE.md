# W22 BUILD BASELINE & BOTTLENECK PROFILE (Workstream B, Phases B1/B2)

Mission: MAIN CODER — 50% knowledge integration + 50% build-time reduction.
This file records the reproducible baseline and the measured bottleneck at
W22 audit HEAD `98a77072` (parent `fd160507`, origin/main at measurement time).

## Environment (measured)

| Field | Value |
|---|---|
| HEAD | 98a77072 (working tree clean at baseline; knowledge-integration edits landed after) |
| Compiler | g++ (Debian 14.2.0-19) 14.2.0 |
| Build system | GNU Make 4.4.1 (production Makefile contract; CMakeLists present, cmake binary absent on host) |
| CPU / RAM | 2 cores, no SMT; 4.0 GB total RAM, ~3.2 GB available |
| Disk | 7.2 GB free |
| ccache / ninja / cmake / mold / lld | all ABSENT on host at Phase 0 (ccache installed portable 4.10.2 during B3) |
| Production flags | `-std=c++17 -Wall -Wextra -g -O2 -MMD -MP` + per-TU contract overrides (dalvik split parts `-g0`, interpreter `-g0 + inline budget`, monolith `-g0`) |

## B1 baseline matrix

| Operation | Wall | CPU | Peak RSS | Note |
|---|---:|---:|---:|---|
| Full fresh production build | **572.46 s** | 556.5+13.4 s | 1427 MB | 88 compile slots + 0.9 s link; rc=0; binary sha256 `f0633a4183e7f3e…` |
| No-op rebuild (×3) | **1.07 s** median (1.05–1.32) | ~1.1 s | 33 MB | zero TUs recompiled |
| Link-only relink | **2.03–2.10 s** | ~2.05 s | 163 MB | link is 0.16–0.37 % of the build |
| Leaf edit, smallest TU (dalvik_value_glue.cpp, 103 lines) | **2.17 s** | 2.19 s | 163 MB | 1 TU + relink |
| Leaf edit, mid TU (class_resolver.cpp, 517 lines) | **4.42 s** | 4.31 s | 226 MB | 1 TU + relink |
| Bridge domain TU edit (dalvik_bridge_domain_io_lang.cpp, 10 181 lines) | **28.55 s** | 28.45 s | 1140 MB | repeats 27.0/27.7/28.4 s — tight spread |
| **Central header edit (dalvik_engine.h, 4744 lines)** | **335.75 s** | 327.0 s | 1427 MB | **the reported “~4-minute small change” reproduced** |

Cross-session consistency: W21 measured a fresh production build at 555.6 s and
a webview-law incremental at 330.3 s; W20-P2 measured clean 572.7 s, ordinary
edit 25.9 s, prod header cascade 401.8 s. The W22 numbers sit inside the same
family; the header cascade improved from 401.8 s to 335.75 s since W20 because
the `android_shadows.h` direct include was removed from `dalvik_engine_tail.cpp`
(fan-out 18→17, W20-P2 item 3) and the dalvik split part set changed.

Raw logs: `evidence/w22/prod_build_fresh.log` (timestamped per line),
`evidence/w22/b1_experiments.jsonl`, `evidence/w22/b1_logs/*`.

## B2 bottleneck profile (per-TU compile slots, start-to-start deltas)

Top 10 of 88 compile slots (start-to-start; warnings stream inside the slot):

| TU | seconds | % of 570.5 s compile total |
|---|---:|---:|
| src/runtime/execution_engine.cpp | 38.01 | 6.7 % |
| src/dex/dalvik_bridge_domain_ui_graphics.cpp | 32.45 | 5.7 % |
| src/dex/dalvik_bridge_domain_app_runtime.cpp | 29.78 | 5.2 % |
| src/dex/dalvik_bridge_domain_io_lang.cpp | 28.12 | 4.9 % |
| src/dex/dalvik_bridge_domain_android_core.cpp | 25.08 | 4.4 % |
| src/dex/dalvik_engine_core.cpp | 22.04 | 3.9 % |
| src/dex/dalvik_engine_invoke.cpp | 21.39 | 3.7 % |
| src/dex/dalvik_bridge_domain_jdk.cpp | 21.28 | 3.7 % |
| src/runtime/application_runtime.cpp | 20.64 | 3.6 % |
| src/dex/dalvik_interpreter.cpp | 20.43 | 3.6 % |

Findings (answers the mission's “top three actual time consumers and why”):

1. **The cost is broad, not monolithic.** No single TU exceeds 40 s at this
   tree (post-P0-split, post-wave-7 inline budgets). The top 10 TUs are 45.8 %
   of the compile total; the remaining 78 slots average ≈3.9 s each and
   contribute ≈310 s. Both the `-O2` codegen tier and the long tail matter.
2. **Header cascade, not compile size, is the dev-loop killer.** Editing
   `dalvik_engine.h` rebuilds every dex-family TU (17–28 slots ≈ 336 s) plus
   the full `-rdynamic` relink — one comment line costs 335.75 s while a
   leaf/domain TU costs 2–29 s. This matches #627 C-04's include-graph analysis
   (`dalvik_engine.h` has 9+ direct includers across the dex family).
3. **Linking is NOT a bottleneck** (0.9 s final link; 2.1 s full relink) —
   this is the measured basis for rejecting lld/mold adoption.

Raw profile tool: `scripts/w22_tu_profile.py` (start-to-start slot deltas;
verifies total 570.5 s vs the 572.5 s wall).

## Reproduce

```bash
cd /home/z/my-project/miniandroid
python3 ../scripts/w22_build_run.py --log evidence/w22/prod_build_fresh.log \
    --out evidence/w22/build_bench.jsonl make -j1 --output-sync all   # ~572 s
python3 ../scripts/w22_tu_profile.py                                 # per-TU slots
bash ../scripts/w22_b1_fast.sh            # no-op / link-only / leaf / domain
bash ../scripts/w22_b1_leaf_header.sh     # leaf probes + header cascade (~6 min)
```
