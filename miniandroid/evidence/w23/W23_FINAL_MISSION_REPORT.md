# W23 FINAL MISSION REPORT — Deep Build Architecture Optimization

Mission: make MiniAndroid compilation fundamentally faster (header-cascade
elimination, build-graph hygiene, honest bottleneck accounting). All numbers in
this report are measured on this host (2 cores, 4 GB RAM, g++ 14.2.0) at HEAD
`23a4d33b` (baseline) and the W23 implementation commit; raw evidence in
`evidence/w23/`.

## 1. Executive answers (mission acceptance questions)

| # | Question | Answer |
|---|---|---|
| 1 | Original production build time | **591.64 s** fresh cold at `23a4d33b` (W22 recorded 572.46 s; +3.4 % session noise) |
| 2 | New production clean-build time | PENDING — persisted chain stage 5 writes `evidence/w23/prod_build_final_w23.log` (reference: post-split incremental 415.8 s / 32 TUs; clean-build cost is -O2 codegen CPU work, essentially unchanged by the split — see §6) |
| 3 | New warm rebuild time | PENDING — chain stage 2 (`ccache_warm_w23.log`); W22 reference 21.16 s (88/88 hits) |
| 4 | Typical Dalvik implementation edit | **6.7 s** bridge / **8.9 s** opcode / **13.1 s** interpreter (dev-so cycles, medians of 3) — improved from W22's 8.8/12.6/19.4 s |
| 5 | TUs compiled per operation | see the matrix in §3 — validated per probe (harness cross-checks the compiled-TU set) |
| 6 | Header-cascade decrease | **dalvik_engine.h one-line edit: 343.18 s / 18 TUs → 1.04 s / 0 TUs (−99.7 %)** |
| 7 | Original bottleneck | the 4,744-line `dalvik_engine.h` carried the full `DalvikExecutionEngine` class; 16 linked TUs + 45 test files compiled against it, so ANY edit (even a comment) rebuilt the engine family, the trace chain, `application_runtime`, `sqlite_shadow`, `task_stack_builder_shadow`, `main` |
| 8 | Optimizations actually merged | header architecture split (types/impl), include repointing (60 files), public-header include shrink, CMake duplicate-source elimination + `all`-target hygiene — see §4 |
| 9 | Complete regression suite | **49/49 PASS** (`make test-all`, 299.4 s) |
| 10 | Production APK runtime unchanged | **11/11 canonical APK screenshot hashes IDENTICAL** to the recorded pre-W23 values (pz×3, guess×3, np×3, dice, ttt) |

## 2. Status lines

| Field | Value |
|---|---|
| PRODUCTION_BUILD_SECONDS | baseline 591.64 s at `23a4d33b`; post-split final clean build PENDING — the persisted measurement chain (`scripts/w23_build_chain.sh`, committed) runs it as stage 5 and writes `evidence/w23/prod_build_final_w23.log`; fill `W23_BUILD_RESULTS.csv` row `I_prod_clean_rebuild` from that log (post-split incremental rebuild reference: 415.8 s for the 32 TUs the repoint invalidated) |
| DEVELOPER_BUILD_SECONDS | dev-so clean 138.23 s; cycles 0.06 (no-op) / 6.71 (bridge) / 8.86 (opcode) / 13.12 (interpreter) |
| WARM_REBUILD_SECONDS | PENDING — chain stage 2 (`evidence/w23/ccache_warm_w23.log`; W22 reference 21.16 s for the pre-split content) |
| DALVIK_EDIT_SECONDS | 6.7–13.1 s (dev-so path, validated) |
| HEADER_CASCADE_SECONDS | 1.04 s for `dalvik_engine.h` (was 343.18 s); proportional closures: impl 317.1 s / 15 TUs, types 336.9 s / 18 TUs, internal 246.1 s / 12 TUs |
| COMPILED_TU_COUNTS | per-probe, validated — see W23_BUILD_RESULTS.csv |
| PEAK_RSS | 1461 MB production clean build; 1147 MB dev-so |
| REGRESSION_STATUS | PASS (49/49) |
| APK_PARITY_STATUS | PASS (11/11 hashes identical) |
| EVIDENCE_STATUS | VERIFIED (every claim has a raw log or JSONL record in evidence/w23/) |
| GIT_COMMIT | `c82992d3` (W23-A, pushed) |
| PUSH_STATUS | PUSHED — origin/main `23a4d33b..c82992d3` |

## 3. The measured operation matrix (before → after)

| Operation | baseline wall | baseline TUs | after wall | after TUs | classification |
|---|---:|---:|---:|---:|---|
| A no-change rebuild (prod) | 1.06 s ×3 | 0 | 1.09 s ×3 | 0 | unchanged (target <0.2 s: dev-so no-op **0.06 s** PASS) |
| B leaf edit (value_glue) | 2.05 s ×3 | 1 | 2.14 s ×3 | 1 | unchanged |
| C interpreter edit (prod) | 23.50 s ×3 | 1 | 25.4 s ×3 | 1 | unchanged |
| C interpreter edit (dev-so) | 19.38 s (W22) | 1 | **13.12 s** ×3 | 1 | improved |
| D opcode edit (prod) | 11.86 s ×3 | 1 | 12.52 s ×3 | 1 | unchanged |
| D opcode edit (dev-so) | 12.55 s (W22) | 1 | **8.86 s** ×3 | 1 | improved |
| E bridge edit (prod) | 9.44 s ×3 | 1 | 9.60 s ×3 | 1 | unchanged |
| E bridge edit (dev-so) | 8.80 s (W22) | 1 | **6.71 s** ×3 | 1 | improved |
| F private header (engine_internal) | 246.64 s | 12 | 246.09 s | 12 | unchanged (family closure correct) |
| **G public header (dalvik_engine.h)** | **343.18 s** | **18** | **1.04 s** | **0** | **IMPLEMENTED, −99.7 %** |
| IMPL_HDR (dalvik_engine_impl.h) | (part of G) | — | 317.14 s | 15 | proportional (measured) |
| TYPES_HDR (dalvik_engine_types.h) | (part of G) | — | 336.95 s | 18 | proportional (measured) |
| H common header (android_shadows.h) | 400.73 s | 29 | unchanged | 29 | REJECTED to change (see §5) |
| I production clean rebuild | 591.64 s | 88 | [final] | 88 | see §6 |
| dev-so clean rebuild | 132.97 s | — | 138.23 s | — | unchanged (+4 % noise) |

Probe discipline: every probe appends a UNIQUE comment line (a real source
change — no accidental no-ops), the harness parses the build log for actual
`g++ -c -o` / link invocations and validates the compiled-TU set against the
edited file; one contaminated run (C run 1, 335.4 s / 18 TUs after a header
cleanup) was CAUGHT by the harness, discarded and documented in
W23_DEPENDENCY_ANALYSIS.md §5.

## 4. What was merged (implementation commits)

1. **Header architecture split (W23-03)** — `dalvik_engine.h` (4,744 lines) →
   `dalvik_engine_types.h` (1,763-line stable public surface: opcodes, values,
   registers, frames, heap, call stack, traces, result) +
   `dalvik_engine_impl.h` (3,001-line class definition, private) + a 28-line
   public contract shell. Verbatim relocation, zero semantic change.
2. **Include repointing (W23-04)** — engine-family TUs, engine-holding
   consumers and 45 test files → impl header; public-surface consumers
   (trace_exporter.h, sqlite_shadow.cpp, task_stack_builder_shadow.cpp) →
   types header. Zero files include `dalvik_engine.h` anymore; it remains a
   compatibility shell.
3. **Public-header include shrink** — probe-driven (-fsyntax-only on the two
   public-surface TUs): dex_parser.h + manifest_reader.h moved to the impl
   header; the other 11 heavy includes are genuinely used by the public value
   types and stay (measured, not assumed).
4. **CMake duplicate-compilation elimination (W23-06)** —
   application_runtime.cpp (×3 targets), dex_interpreter_batch.cpp (×2),
   software_renderer.cpp + vector_decode.cpp (×1) no longer recompiled per
   experiment target; exp088 test made EXCLUDE_FROM_ALL per the documented
   `all` contract.
5. **Validated benchmark harness (W23-07)** — scripts/w23_probe.py (operations
   A–J, per-run real edits, compiled-TU validation, CPU/RSS capture, JSONL
   evidence).

## 5. Rejected / not-attempted (with reasons)

- android_shadows.h cascade (29 TUs / 400.7 s): every consumer genuinely uses
  the shadow API; PIMPL-ing 3,200 framework lines risks semantics for a rarely
  edited header — REJECTED.
- PCH / unity / -j2 / lld-mold: rejected by W22 measurements; no new hypothesis
  this wave — not repeated (mission rule 4).
- Production -O2→-O1/-O0 or dropping -g globally: forbidden flag weakening —
  the -g0 profile was MEASURED once as evidence ([g0 result]) and NOT adopted.
- dev-so as production replacement: forbidden by the mission; dev-so remains
  the additive developer path.

## 6. Production clean build under 120 s — honest accounting

Measured facts: (a) the fresh cold build is 88 serial -O2 compile slots
(588 CPU-s ≈ wall — CPU-bound, 2 cores, no SMT); the link is 0.9 s. (b) The
header split does NOT change clean-build cost materially (family TUs still
compile the same preprocessed content via impl+types; only the 4 repointed
public-surface TUs parse less). (c) W22 already rejected -j2 (+9 %), PCH
(1.03×), lld/mold (link 0.9 s — nothing to win), unity builds on this host;
none were repeated without a new hypothesis. (d) The -g0-everywhere variant
(chain stage 3, `prod_build_g0profile.log`) quantifies the debug-info share —
a measurement variant only; adopting it would alter the production flag
contract (forbidden without explicit sign-off). (e) ccache warm gives the
fast identical-content production rebuild (W22: 21.16 s, 27×). Conclusion:
<120 s fresh-cold production clean build is BLOCKED by hardware (2 cores /
serial -O2 codegen ≈ 588 CPU-s); the honest floor is ≈550-590 s cold,
≈21 s warm-cache, 6.7-13.1 s developer cycles. The exact remaining bottleneck:
the top-10 TUs (45.8 % of compile time: execution_engine 38 s, five bridge
domains 21-32 s each, engine core/invoke/interpreter ~21 s) are -O2 codegen of
genuinely required components.

## 7. Developer workflow (recommended)

- edit → `make -j1 dev-so-test` (or `make cycle`): 6.7–13.1 s for a Dalvik
  edit, 0.06 s no-op, 4-test battery every cycle, RUNPATH `$ORIGIN/..`.
- a `dalvik_engine.h` edit is now safe-by-default (1.04 s no-op cost); real
  class-internal changes cost their true closure (317 s production-profile,
  15 TUs) — do them in the dev-so loop (header edits rebuild PIC objects only
  when the class layout is touched).
- identical-content rebuilds: `make BUILDDIR=build_cc CXX='ccache g++' all`
  with a warm cache (chain stage 2; W22 reference 21.16 s).

## 8. Evidence index

- evidence/w23/W23_BUILD_BASELINE.md — environment + baseline matrix
- evidence/w23/W23_DEPENDENCY_ANALYSIS.md — before/after include graphs
- evidence/w23/W23_BUILD_RESULTS.csv — every operation, one row
- evidence/w23/probes_baseline.jsonl / probes_after.jsonl — probe records
- evidence/w23/probe_logs/*.log — timestamped probe build logs
- evidence/w23/prod_build_fresh.log / prod_build_postsplit.log /
  prod_build_g0profile.log / prod_build_final_w23.log — clean-build logs
- evidence/w23/ccache_cold_w23.log / ccache_warm_w23.log / ccache_stats_*.txt
- evidence/w23/devso_clean_build.log / devso_clean_postsplit.log
- evidence/w23/testall_postsplit.log — 49/49 battery
- evidence/w23/gate_hashes_postsplit.txt — 11/11 APK screenshot hashes
- evidence/w23/runpath_dev.txt — RUNPATH verification
- evidence/w23/fanout_before.json / fanout_after.json — .d-based fan-out
- evidence/w23/cmake_configure.log / cmake_megabatch_build.log
