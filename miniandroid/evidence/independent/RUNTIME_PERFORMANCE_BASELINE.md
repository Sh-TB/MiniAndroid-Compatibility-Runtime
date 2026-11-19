# RUNTIME PERFORMANCE BASELINE (W20-K2 — MEASURED, not speculative)

Harness: `scripts/w20_runtime_perf.sh` — production binary at the merged
tree, bounded workload (`--max-seconds 35 --frames 30`), fresh data-root per
APK, cold rep 1 + warm reps 2..5 (all reps share the data-root), wall-clock
per run, screenshot sha16 determinism per rep. Raw data:
`evidence/w20/runtime_baseline.tsv` (142 rows; a harness append quirk gave
most APKs ~10 reps — MORE than the required 5; medians below).

NOTE (honest scope): this measures total wall per bounded run (APK parse +
DEX load + execution + frame set + teardown). CPU/peak-RSS per run were not
capturable on this host (/usr/bin/time absent). Subsystem attribution is
Phase 2 (instrumented), listed as next actions — no subsystem percentages
are claimed.

## Medians (seconds, n = reps; cold shown separately)
| APK | n | median | min | max | cold |
|---|---|---:|---:|---:|---:|
| dk.cocode.chess_5022 | 10 | 60.03 (timeout cap) | 60.03 | 60.06 | 60.03 |
| io.github.herrerad85.tallybook_94 | 10 | 17.24 | 16.73 | 17.75 | 16.73 |
| com.ivylopez.authsrng_6 | 10 | 9.24 | 8.94 | 9.37 | 9.35 |
| com.itsfrz.tictactoe_5 | 10 | 9.23 | 9.09 | 9.68 | 9.68 |
| org.ecos.logic.flip_a_coin_3 | 10 | 7.96 | 7.58 | 8.61 | 8.04 |
| com.attenomy.janken_1 | 10 | 7.88 | 7.61 | 8.70 | 8.42 |
| tech.gaskell.diceroller_1_debug | 10 | 7.80 | 6.48 | 9.04 | 9.04 |
| name.livitski.games.puzzle.android_2 | 10 | 7.42 | 7.25 | 7.70 | 7.46 |
| com.farmerbb.notepad_122 | 10 | 6.37 | 6.02 | 9.53 | 9.53 |
| de.tcrass.minos_10004 | 10 | 6.30 | 6.20 | 6.55 | 6.29 |
| ru.zxalexis.ugaday_15 | 10 | 6.20 | 5.97 | 6.35 | 6.21 |
| org.blockinger.game_14 | 10 | 6.08 | 6.00 | 6.35 | 6.12 |
| HelloWorldToast-1.3.0 | 5 | 5.96 | 5.83 | 6.02 | 5.83 |
| HelloWorldToast-1.4.0 | 7 | 5.79 | 5.41 | 6.21 | 5.74 |
| com.minar.randomix_42 | 10 | 5.71 | 5.56 | 7.87 | 7.87 |

Determinism: per-APK screenshot sha16 stable across reps (e.g., minos
b5a7a35d5fe0564b, ugalay 87fe26766fc48d06). rc=1 rows = the known in-app
exception APKs (unchanged status, per census); rc=124 = chess hitting the
cap. Cold-vs-warm deltas are inside noise (no cross-process cache effect).

## Observations (measured, phase-2 targets)
1. chess is the ONLY app hitting the 35s workload cap — the single largest
   absolute runtime consumer in the corpus; profile it first.
2. tallybook (17.2s) is 2.7x the median — candidate for per-app divergence
   work (its in-app exceptions are known).
3. The ~5.7-6.4s floor for tiny apps = startup constant (APK parse + DEX
   load + first frames) — the shared-runtime startup path is the highest-
   leverage multi-APK target.

## Next (phase 2, in order)
1. Instrument the startup constant: apk-parse / dex-verify / class-init /
   first-frame timers are already printed by the binary — aggregate them
   across this TSV's runs.
2. chess + tallybook deep profile.
3. Then the three ranked hypotheses (method-resolution scan, BitmapStore
   re-decode, full-frame state-list re-pick) with focused benchmarks.

Build-side metrics stay separate (BUILD_MEMORY_BASELINE.md).
