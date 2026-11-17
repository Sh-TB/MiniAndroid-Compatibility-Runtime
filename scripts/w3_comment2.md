## WAVE 3 CHECKPOINT 2 — Benchmarks reproduced + compiler-phase breakdown (measured)

**Commit:** `5e7090e3` · **Compiler:** g++ 14.2.0 · **Host:** 2 vCPU / 4 GB · **Cache:** warm page cache, no compiler cache (ccache unavailable)

**Reproduction of Wave-2 numbers on committed source** (`src/dex/dalvik_engine.cpp`, 94,194 lines, exact command line + full `-ftime-report` in `evidence/issue612_audit/wave3/`):

| Profile | Wall | Peak RSS | Object size |
|---|---:|---:|---:|
| `-O2` (production profile) | **219.28 s** (Wave-2 said 216.24 s — reproduced) | **2,870 MB** | 9.2 MB |
| `-O0 -g0` (DEV profile) | **47.10 s** with `-ftime-report` overhead; 35.8–38.5 s without | 2,870 MB (cumulative counter) | 21.9 MB |

**Compiler phase breakdown (`-ftime-report`, wall column):**

| Phase | `-O2` | `-O0` |
|---|---:|---:|
| parsing | 11.5 s (5%) | 11.2 s (25%) |
| lang. deferred | 4.8 s (2%) | 4.9 s (11%) |
| **opt and generate** | **201.8 s (93%)** | **29.1 s (64%)** |

**Correction to the Wave-2 report:** Wave-2 described the cost as "frontend-dominated" based on the -O0 comparison. The phase breakdown shows that at **-O2 the optimization/codegen passes are 93% of the cost** (202 s on a 9.2 MB object); parsing is only ~11 s in both profiles. Honest implication: a DEV-profile edit loop is legitimately ~6× cheaper because it skips optimization — that is a profile difference, NOT a build-system speedup, exactly as the issue warns. The structural fix (splitting the TU) reduces both phases proportionally: a 4-way split projects a one-law-change loop to ≈55 s at -O2 / ≈12 s at -O0.

Same-flags comparisons: all runs same machine, same compiler, same include set; object sizes and peak RSS recorded in `evidence/issue612_audit/wave3/benchmarks.json`; full raw reports at `ftime_report_dalvik_{O2,O0}.txt`.

**Next:** P0 original-APK execution (checkpoint 3), then the Dalvik pilot extraction with the corrected phase picture.
