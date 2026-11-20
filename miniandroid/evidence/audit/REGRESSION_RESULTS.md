# REGRESSION RESULTS — baseline and after-change (2026-11-20 audit session)

## Environment
g++ 14.2.0, GNU Make, 2 vCPU / 4 GB / shared VM (steal 24-25 % of every window).
Commands and raw logs are committed under evidence/w24/RAW_LOGS/ and
evidence/audit/RAW_LOGS/.

## Build A/B (W24 candidate, run today, commit d8b8fbb9)
| run | wall | CPU | steal/window | binary sha16 |
|---|---:|---:|---:|---|
| base_a FASTPROFILE | 440.64 s rc0 | 535.6 | 220.9 s (25 %) | bfc0610db8578543 |
| cand_a FASTPROFILE+W24TIERS | 289.31 s rc0 | 426.7 | 138.5 s (24 %) | 32442d05a0e00528 |
| cand_b (rep) | 290.39 s rc0 | 430.2 | 139.9 s (24 %) | 32442d05a0e00528 (identical) |
| base_b (rep) | 350.39 s rc0 | 520.4 | 170.8 s (24.4 %) | bfc0610db8578543 (identical) |

Honest delta (matched-steal pair): **−17.3 % wall / −17.7 % CPU (−91.9 CPU-s)**,
parallel efficiency matched (0.739 vs 0.743). Candidate sits at the measured
effective-capacity floor (288.4 s).

## Correctness gates (all on the W24 candidate binary/codegen)
- Battery: **49 PASS / 0 FAIL** rc0 (181.34 s) — law tests s1xx-s23x incl.
  move/from16, lit8/lit16, const-string/jumbo laws (w15_dalvik_lit_from16 law test).
- 5-APK screenshot gate (pz/guess/np ×3 + dice + ttt): **11/11 sha16 hashes
  IDENTICAL** to the canonical recorded set (evidence/w23/gate_hashes_postsplit.txt);
  machine verdict ALL-IDENTICAL (w24_gate_verdict.txt). TicTacToe render parity
  re-proven (AUD-36).
- Incremental leaf edit on candidate config: 2.04 s rc0.
- Manifest parity: runs inside test-all (source manifest untouched by tiering).

## Fresh probes run during THIS audit (ABBA order, heaviest TU 31.3 s canonical)
| variant | rep1 | rep2 | verdict |
|---|---:|---:|---|
| A baseline (-g1 -O2) | 31.62 s | 33.87 s | reference |
| B -gsplit-dwarf | 33.80 s | 33.45 s | REJECTED (+4 %) |
| C -fno-var-tracking-assignments | 34.22 s | 31.85 s | REJECTED (no win) |
| D ggc-min-expand=1/heapsize=8192 | 102.48 s | 101.64 s | REJECTED (3× slower) |

## .DELETE_ON_ERROR integration test
Protected Makefile demo: failed recipe leaves NO partial target artifact
(behavior verified before enabling in the main Makefile); full no-op make
re-run after the edit returned rc0.

## APK identity note
Gate APKs are the original handoff APKs (upload/handoff_apks, 15 files);
no source-built substitutes were used as compatibility evidence. Counter/
OpenCalc/bouncy APKs are absent in this sandbox — their rows are BLOCKED,
not assumed-passing.
