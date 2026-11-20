# REJECTED AND CORRECTED — v2 (preserved so nothing is rediscovered)
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
