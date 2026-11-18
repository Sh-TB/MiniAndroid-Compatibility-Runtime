# WAVE-10 Compiler Attribution — why interpreter and bridge compiles cost what they cost

## Method

The exact Makefile PIC compile commands (dev-so rules, `make --no-print-directory -n -B`) were instrumented, not approximated:

- `-ftime-report` ×5 per TU (GCC 14.2.0, Debian 14.2.0-19) — note: `-ftime-report` instrumentation itself adds ~3–4 s, so its wall times (interpreter 24.77–26.49 s, bridge 45.95–47.30 s) are higher than the clean-cycle compile times (21.4 s / 40.3 s measured in wave-9). Phase *shares* are what matter.
- `-fsyntax-only` ×2 (parse + semantics + template instantiation only).
- `-E` preprocess volume ×1.
- Per-phase memory from `-ftime-report`'s fourth column.
- Phase separation requested by the mission: preprocessing → parsing → optimization → code generation → assembly → linking → test execution. GCC's phase table maps: preprocessing + parsing (+ template instantiation) = front end; "phase opt and generate" = optimization + code generation; assembly/link/test are measured separately by the cycle harness (link 0.20–0.22 s, battery 0.04–0.05 s — negligible, unchanged from wave-9).

## Measured breakdown (median of 5)

| Phase (GCC -ftime-report) | Interpreter | Bridge |
|---|---|---|
| Wall (with instrumentation) ×5 | 24.77 / 24.87 / 25.00 / 25.16 / 26.49 | 45.95 / 46.24 / 46.38 / 46.75 / 47.30 |
| `-fsyntax-only` (parse+semantics) ×2 | 5.52 / 5.47 | 8.19 / 8.03 |
| Preprocess (`-E`) | 0.50 s, 229,685 lines, 7.1 MB | 0.55 s, 272,088 lines, 8.7 MB |
| **phase parsing** | 3.77 s (18%) | 5.75 s (14%) |
| **phase lang. deferred** (templates) | 1.50 s (7%) — template instantiation 2.71 s | 3.26 s (8%) — template instantiation 4.42 s |
| **phase opt and generate** | **16.08 s (75%)** | **30.81 s (77%)** |
| → callgraph functions expansion (inlining expansion) | **13.46 s (63%)** | **19.80 s (50%)** |
| → callgraph ipa passes | 2.35 s (11%) | **9.80 s (25%)** |
| → RTL PRE | 3.59 s (17%) | (not in top passes) |
| → integrated RA + LRA (bridge) | ~0.6 s | 2.37 s + 1.77 s |
| → garbage collection | 0.82 s | 1.86 s |
| → tree CFG cleanup / SSA incremental | 0.26 s | 1.14 s + 2.08 s |

## Conclusion (evidence, not line-count guessing)

1. **Both TUs are optimization/code-generation bound** (~75–77%), not preprocessing (0.5 s) or parsing bound (5.5/8.1 s).
2. The single largest component in BOTH is **`callgraph functions expansion` — the inlining/integration stage**: 63% of the interpreter's total time and 50% of the bridge's. The wave-7 inline-budget params already cut this stage once (35.9 → 21.8 s); *further* caps attack exactly this bucket.
3. The bridge additionally pays **25% in `callgraph ipa passes`** (inter-procedural analysis over the 55K-line translation unit) — `-fno-ipa-*` toggles are the second lever.
4. RTL `PRE` costs 17% on the interpreter — a candidate toggle if inline caps alone are insufficient.
5. Garbage collection is modest (0.8/1.9 s) — GGC tuning helps the bridge marginally, matching wave-6's memory observation.
6. Header diet / PCH are **not** justified: preprocessing is 0.5 s and parse+templates 5.5/8.1 s — even a perfect PCH saves under 20% of the bridge budget and less for the interpreter; the same effort in inline caps saves 3–5× more.

## Candidate flags implied (tested in the sweep, adopted only with full parity)

- Interpreter: tighter `--param inline-unit-growth / large-function-growth / max-inline-insns-auto` (attacks the 13.5 s bucket), then `-fno-tree-pre` if needed.
- Bridge: same inline caps + `-fno-ipa-cp -fno-ipa-sra -fno-ipa-pure-const` (attacks the 9.8 s IPA bucket), GGC env tuning for RSS/time.
- Raw data: `evidence/wave10/w10_attribution_raw.json` (all 5 phase tables per TU).
