# W21 RUNTIME PERFORMANCE BASELINE — 15 original APKs x 5 measured reps

Binary: `build/miniandroid` sha256-16 `f2083d06e5a6e89a` @ commit `c1602b754ddf5d00`.
Workload: `run --max-seconds 35 --frames 30 --execution-mode real-dalvik`, fresh
data-root per APK, cold rep1 + warm reps2-5 (W20-K2-identical config).
Per-run wall + CPU + peak RSS via `scripts/w21_runner.py` (getrusage(RUSAGE_CHILDREN)
per fresh process — the fields W20-K2 could not capture: /usr/bin/time is absent
on this host). Host: 2 CPUs, no swap; measured nproc in every JSONL.

| APK | n | median s | min | max | cold | median CPU s | median RSS KB | sha16 | rc | vs W20-K2 sha | W20-K2 median s | delta s |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|
| HelloWorldToast-1.3.0-android | 5 | 4.55 | 4.51 | 4.91 | 4.57 | 4.21 | 57804 | acdd9f05dc9c7ece | 1 | cold:IDENTICAL warm:IDENTICAL | 5.96 | -1.41 |
| HelloWorldToast-1.4.0-android | 5 | 4.58 | 4.54 | 4.9 | 4.54 | 4.2 | 57860 | acdd9f05dc9c7ece | 1 | cold:IDENTICAL warm:IDENTICAL | 5.79 | -1.21 |
| com.attenomy.janken_1 | 5 | 6.08 | 6.05 | 6.3 | 6.22 | 5.76 | 116772 | d602648e8e401895 | 1 | cold:IDENTICAL warm:IDENTICAL | 7.88 | -1.8 |
| com.farmerbb.notepad_122 | 5 | 4.71 | 4.64 | 7.52 | 7.52 | 4.41 | 134128 | 31ddd4d5b8e6d18e | 1 | cold:IDENTICAL warm:IDENTICAL | 6.37 | -1.65 |
| com.itsfrz.tictactoe_5 | 5 | 6.55 | 6.47 | 6.74 | 6.47 | 6.17 | 169188 | d55056a8928a26ff | 1 | cold:IDENTICAL warm:IDENTICAL | 9.23 | -2.67 |
| com.ivylopez.authsrng_6 | 5 | 6.92 | 6.75 | 7.15 | 7.11 | 6.52 | 365072 | b5a7a35d5fe0564b | 1 | cold:IDENTICAL warm:IDENTICAL | 9.24 | -2.33 |
| com.minar.randomix_42 | 5 | 4.42 | 4.38 | 5.95 | 5.95 | 4.07 | 124876 | 31ddd4d5b8e6d18e,b5a7a35d5fe0564b | 1 | cold:IDENTICAL warm:IDENTICAL | 5.71 | -1.29 |
| de.tcrass.minos_10004 | 5 | 4.76 | 4.75 | 4.94 | 4.75 | 4.42 | 66444 | b5a7a35d5fe0564b | 1 | cold:IDENTICAL warm:IDENTICAL | 6.3 | -1.54 |
| dk.cocode.chess_5022 | 5 | 60.03 | 60.03 | 60.04 | 60.03 | 59.69 | 888188 | d602648e8e401895 | 124 | cold:IDENTICAL warm:IDENTICAL | 60.03 | 0.0 |
| io.github.herrerad85.tallybook_94 | 5 | 12.72 | 12.32 | 12.97 | 12.32 | 12.28 | 508092 | c558255f7e3f9ee8 | 1 | cold:IDENTICAL warm:IDENTICAL | 17.24 | -4.52 |
| name.livitski.games.puzzle.android_2 | 5 | 5.78 | 5.7 | 5.9 | 5.78 | 5.41 | 75444 | 6375a3a3813af176 | 0 | cold:IDENTICAL warm:IDENTICAL | 7.42 | -1.63 |
| org.blockinger.game_14 | 5 | 4.76 | 4.73 | 4.76 | 4.76 | 4.41 | 77684 | 34d7ac0cf77898d8 | 0 | cold:IDENTICAL warm:IDENTICAL | 6.08 | -1.32 |
| org.ecos.logic.flip_a_coin_3 | 5 | 5.98 | 5.84 | 6.07 | 5.84 | 5.62 | 230732 | b270ff040b3601dc | 1 | cold:IDENTICAL warm:IDENTICAL | 7.96 | -1.97 |
| ru.zxalexis.ugaday_15 | 5 | 4.77 | 4.7 | 4.86 | 4.7 | 4.44 | 99460 | 87fe26766fc48d06 | 0 | cold:IDENTICAL warm:IDENTICAL | 6.2 | -1.43 |
| tech.gaskell.diceroller_1_debug | 5 | 6.67 | 6.65 | 6.9 | 6.9 | 6.3 | 148968 | 0de952bf75f89409 | 1 | cold:IDENTICAL warm:IDENTICAL | 7.8 | -1.13 |

**Screenshot regression check vs W20-K2**: 15/15 APKs byte-IDENTICAL; differing: none.

Raw per-run TSV: `evidence/w21/runtime_baseline.tsv` (header + 75 rows). Runner JSONL per run: `evidence/w21/runtime_perf/<apk>_rN/runner.json`; full stdout logs `<apk>_rN/run.log`.
