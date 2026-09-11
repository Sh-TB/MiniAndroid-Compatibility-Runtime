# CLOSURE_QUEUE.md — MASTER MISSION: ROOT CLOSURE + REAL APK EXECUTION (S22)

Generated: 2026-09-12 · Baseline HEAD: 5a2b7d99 (= origin/main, ls-remote verified)
Scope law: this queue ranks the EXISTING inventory by what blocks real APK visual
execution (HelloWorld / TicTacToe / Game-2 corpus). No new root hunting; new
findings enter ACTIVE only if they block one of the three targets (Law 1).

## Queue state at generation

| Source | State |
|---|---|
| root_registry.json | 299 roots: 19 VERIFIED-FIXED, 45 VERIFIED-CORRECT, 103 PARTIAL, 72 UNPROVEN, 16 RESEARCHED-NOT-IMPLEMENTED, 42 NOT-APPLICABLE, 2 OBSERVED-FAIL |
| Battery | 91/92 at F-076 build (EXT-01/02 permanently fixed this session; GATE H = real pre-existing glyph-rendering gap, queued) |
| Corpus | 15/16 APKs restored + hash-verified (dooz d81292cd… exact); HelloWorldSelfAware fixture + author reference screenshot restored SHA-exact |
| Toolchain | aapt2 2.20-14304508 restored via bootstrap_toolchain.sh; runtime rebuilt clean |
| dooz baseline (this session, HEAD 5a2b7d99) | rc=0 ×3, uncaught=0 ×3, screenshot SHA 31ddd4d5b8e6 ×3 byte-identical, 0/2,073,600 non-white |
| GitHub | API rate-limited (no PAT in env after container reset); Issue #8/#9 reconcile state carried by local ledgers per S18–S21 |
| Push credentials | PAT absent from environment → final push may be blocked; PUSH_BLOCKED.json protocol if so |

## P0 — directly blocks real execution of the three targets

| Item | Source | Priority | Current status | Blocks target? | Action |
|---|---|---:|---|---|---|
| S22: parked Recomposer await-work continuation never wakes/redispatches | S21 report §7, worklog S21-MAIN | P0 | ROOT-CAUSED+FIXED as F-076 (guard stubbed nested coroutine starts); runner loop STARTS | dooz Compose family (Game-2-class) → pixels | WAVE 1: trace park→waiter→wake→resume→dispatch→handler→recomposer→frame |
| Frame pump: withFrameNanos → doFrame → Recomposer → measure/layout/draw chain still 0 frames | S21 | P0 | downstream of item 1 | all Compose targets | after item 1 wakes, implement generic frame scheduling law if trace proves it required |
| GATE H environmental failure (white=0 expected-image stage) | battery log | P0 | ENVIRONMENTAL (bisect-proven: reproduces with S21 fix stashed) | battery honesty only | re-diff golden generation vs runtime output; regenerate or fix stage harness |
| EXT-01/EXT-02 corpus stages | battery log | P0 | ENVIRONMENTAL (corpus restored 15/16 this session) | battery count only | re-run battery after corpus fetch completes; battery target 92/92 |

## P1 — generic capability required by the target APK family

| Item | Source | Priority | Current status | Blocks target? | Action |
|---|---|---:|---|---|---|
| 103 PARTIAL roots (registry) | root_registry.json | P1 | PARTIAL | subset blocks Compose draw/input | sweep for roots inside the live dooz/hello/tictactoe paths first; close only what the trace touches |
| HelloWorld chain law 9 audit (APK→parse→…→pixels, per-stage matrix) | mission law 9 | P1 | HelloWorld §28 26/26 PASS but pixels stage = golden-color APK only | no (already >0 on hello_color) | keep as regression oracle; extend per-stage metrics report |
| TicTacToe interaction 3-run determinism re-proof on current HEAD | mission law 10 | P1 | §29 8 checks PASS (S21) | no | re-run ×3 on this session's binary, record SHA/metrics |
| Game-2 selection + run from corpus (law 11) | corpus registry | P1 | dooz = Compose candidate (S22 frontier); View-based candidates (ChessClock, Stopwatch, uNote, MicroTimer) cheaper first | Game-2 matrix row | run best View-based candidate to visible output; dooz continues via WAVE 1 |

## P2 — important half-done work that raises regression/compatibility

| Item | Source | Priority | Current status | Blocks target? | Action |
|---|---|---:|---|---|---|
| 72 UNPROVEN + 16 RESEARCHED-NOT-IMPLEMENTED roots | root_registry.json | P2 | UNPROVEN/RESEARCHED | no (outside live paths) | triage after P0/P1; close-as-N/A only with evidence |
| Telegram (in matrix, ~20% focus) | law 23 | P2 | prior gates closed | no | keep as regression target only |
| 3 missing corpus APKs | apks.json | P2 | fetch pending (network) | EXT stages only | background fetch running |

## P3 — research/optimization/documentation

| Item | Source | Priority | Current status | Blocks target? | Action |
|---|---|---:|---|---|---|
| ASAN/UBSAN, profiler, computed-goto, ICC/lcms2 perf | law 26 | P3 | secondary | no | CONDITIONAL/BACKLOG unless a trace proves blocker |
| PUSH_BLOCKED.json refresh if PAT stays absent | git rules | P3 | file exists from earlier era | publish only | update at final push attempt |

## Execution order (this session)

```
WAVE 0  ✅ reconcile (HEAD=5a2b7d99, corpus 15/16, toolchain, dooz 3-run baseline)
WAVE 1  → S22 parked-resume dispatch trace (P0 item 1) — THE frontier
WAVE 2  → HelloWorld per-stage law-9 matrix refresh (non-white pixels already proven)
WAVE 3  → TicTacToe 3-run determinism re-proof
WAVE 4  → Game-2 (View-based corpus candidate first; dooz continues in WAVE 1)
WAVE 5+ → P0 leftovers (battery 92/92) then P2 triage
```
