# WAVE-10 Final Report — Dalvik compiler acceleration: interpreter <15 s, bridge <30 s

Branch: `wave10/dalvik-accel` — stacked on the verified wave-9 clean branch `wave9/dev-so-clean`
(`1e5c8fb9`), which is **not yet merged** (remote main still `125f5690`; wave-9 PR not yet opened
due to token scope). The wave-10 branch therefore carries wave-9's commits as an explicit
dependency; a PR from this branch includes them until wave-9 merges.

## Result — all Phase-7 gates MET (fresh ×5 harness on the accepted configuration)

| Gate | Required | Wave-9 baseline | Wave-10 measured (×5) | Status |
|---|---|---|---|---|
| Opcode edit-to-test | <10 s | 9.85 s median | **8.18 s median** [7.82–8.21] @ -O1 | **MET** |
| Interpreter edit-to-test | <15 s | 21.94 s median | **12.26 s median** [12.07–12.35] @ -O1 | **MET** (-44%) |
| Bridge edit-to-test | <30 s | 40.98 s median | **25.51 s median** [25.37–26.81] @ -O0 | **MET** (-38%) |
| No-op | <0.5 s | 0.05 s | **0.04 s** [0.04–0.04] | **MET** |
| Test-exe relinks after engine edit | 0 | 0 | **0** (every trace and run) | **MET** |
| Peak RSS | <4 GB | 2,129 MB | **2,185–2,886 MB** observed (max: production monolith build) | **MET** |
| Runtime parity | PASS | 3 APKs identical | **3 APKs ×3 reps identical + final combined-profile gate identical** | **PASS** |
| Production fallback | PASS | verified | **prod static 3/3, monolith LIVE 3/3, clean dev-so rc=0** | **PASS** |

Every individual run is recorded in the benchmark JSONs (no cherry-picking; medians computed
from all five runs).

## How it was done (attribution-driven, not guesswork)

Phase 1 (`-ftime-report` ×5, `-fsyntax-only`, `-E`, per-phase memory) proved both TUs are
**optimization/codegen bound** (75–77%), dominated by GCC's `callgraph functions expansion`
(inlining expansion: 63% interpreter / 50% bridge) and, for the bridge, `callgraph ipa passes`
(25%). Inline-cap candidates (round 1: I1–I5, I8) moved the needle ≤3% — the giant function
bodies themselves dominate that stage, so no parameter tuning reaches the targets. The accepted
change is a **dev-path-only speed profile**: the dev-so PIC rules compile the interpreter at
`-O1` (12.0 s, RSS unchanged 1,074 MB) and the bridge/opcode at `-O1`/`-O0` (25.5/8.2 s), while
**production per-TU rules are byte-identical to wave-9** (interpreter `-O2` + wave-7 budget,
bridge `-Og`). Bridge `-O1` was measured and **rejected: cc1plus is OOM-killed** by the 4 GB
cgroup — an honest blocker, not a tuning miss.

## Why the runtime results stay trustworthy

The dev .so executes the actual APKs used for acceptance. At the reduced optimization levels the
runtime results are unchanged: battery 3/3 after every transition, and all three APK screenshot
SHA-256s are **identical to canonical and stable across repetitions** (Guess `87fe2676…` SUCCESS;
DiceRoller `46b07062…` PARTIAL; TicTacToe `d55056a8…` PARTIAL — preserved, not upgraded; matching
screenshots are not claimed as interaction evidence). Production correctness is additionally
protected by the untouched production rules, the live monolith fallback (3/3), and the static
split build (3/3).

## What was explicitly NOT done (and why)

- No linker work (wave-9 measured 0.20–0.22 s — not a bottleneck).
- No global downgrades (mission rule); no semantics-affecting flags (`-fno-exceptions`/`-rtti`).
- No bridge dispatch-arm extraction (wave-6 ud2/SIGILL history; not attempted speculatively).
- No PCH/header diet (preprocess is 0.5 s; parse share too small to justify the fragility).

## Remaining limitations

1. The dev-so path's interpreter/bridge/opcode objects now compile with reduced optimization —
   a deliberate, parity-proven trade for developer feedback latency; production binaries are
   unaffected.
2. Bridge `-O1`/`-O2` in the dev path remain OOM-blocked on this 4 GB host (measured); reaching
   bridge <30 s at higher optimization would require the wave-6-proven arm-extraction approach
   or a memory headroom increase — both out of scope this wave.
3. Interpreter/bridge cycles are compile-bound (~99% of cycle); further gains require source
   splitting of the giant functions, which needs proven semantic boundaries.

## Deliverables

`wave10_compiler_attribution.md` · `wave10_interpreter_benchmarks.json` ·
`wave10_bridge_benchmarks.json` · `wave10_runtime_parity.json` · `wave10_build_safety.md` ·
`wave10_experiment_matrix.md` · this report — under `miniandroid/evidence/wave10/`, plus raw
sweep/harness JSONs and the reproduction scripts (`scripts/w10_*.py`).

## Rollback

`make dev-so-clean` removes the dev path; `git revert <wave-10 commit>` restores wave-9 flags
exactly. Production artifacts and flags were never modified.
