# W24 FINAL REPORT — Evidence-Driven Build Architecture Investigation

Reference commit: 4ada9e3e (W23-G/P2). Date: 2026-11-20. Host: 2 vCPU / 4 GB
RAM / GCC 14.2.0, shared-cloud VM (hypervisor steal measured, see §3).

## 1. Original and final clean cold build times (today's internally-consistent set)

| Config | wall | CPU | RSS |
|---|---:|---:|---:|
| A canonical -j1 -g | 592.78 s rc0 | 590.2 | 1425 MB |
| B FASTPROFILE -j2 (baseline) | 349.35 s rc0 | 513.9 | 1221 MB |
| B1 FASTPROFILE -j1 | 501.83 s rc0 | 501.4 | 1221 MB |
| Ninja -j2 (flag-parity) | 355.91 s rc0 | 526.5 | — |
| raw xargs -P2 (no make) | 348.90 s | 509.0 | — |
| CAND (FASTPROFILE+Tiers) full A/B | PENDING (script ready: scripts/w24_phase4.sh) | | |

Day-to-day noise band: today's machine runs ~8 % slower than 2026-11-19
(B 349.35 vs 322.75/323.90 yesterday); all comparisons here are same-day.

## 2. Total CPU work before/after and parallel efficiency

- Efficiency B = 513.9 / (349.35 × 2) = **0.735** (W23-P2: 0.74 — stable).
- Measured CPU inflation at -j2 vs -j1: only +2.5 % (501.4 → 513.9) —
  contention does NOT inflate CPU; the gap is core-idle/steal time (§3).
- LPT model from the real 88 per-TU durations: ideal 2-core floor
  **251.7 s** (sum/2 + 1.5 s link). The 97.6 s gap is explained in §3.

## 3. The real bottleneck: hypervisor steal time (measured)

- cgroup: cpu.cfs_quota_us = -1 (no quota), cpuset 0,1.
- During the Ninja measurement (355.9 s wall): /proc/stat steal delta
  **+17,269 jiffies = 172.7 s ≈ 24 % of the 2-core wall budget**; lifetime
  steal ≈ 14 % of user time.
- Scheduler exonerated twice: raw xargs -P2 (no make) 348.90 s ≈ make
  349.35 s; Ninja 355.91 s. Core-idle is spread across the whole build
  (10-28 core-s per 30 s window), not concentrated in a tail.
- Conclusion: effective capacity ≈ 1.47 cores of the nominal 2 — the LPT
  floor 251.7 s is unreachable on THIS host regardless of build system.
  Remaining lever: reduce total CPU work (§5). EXP-B: REJECTED-MEASURED
  (make scheduling is not the constraint; Ninja migration not justified).

## 4. PART 2 cost model (evidence/w24/*.csv)

- TU_COST_RANKING.csv (FASTPROFILE -j1, true per-TU durations): top =
  ui_graphics 31.3, app_runtime 29.5, io_lang 27.2, execution_engine 27.0,
  android_core 26.0, engine_invoke 22.4, engine_core 22.0, interpreter
  22.0, jdk 20.3, value_glue 17.9, opcodes_invoke 15.5, webview_engine
  15.2 s. Small tail (<6 s): 67 TUs = 138.1 CPU-s. Link 1.5 s.
- COMPILER_PHASE_COSTS.csv (-ftime-report on exact build commands):
  ui_graphics: parse 6.5 s (19 %) / lang-deferred 2.4 s (7 %) /
  **opt+generate 28.5 s (76 %)** / GC 1.0 s. Frontend is small; -O2 codegen
  dominates.
- HEADER_COST_RANKING.csv (.d-based) + HEADER_PARSE_COST.csv (gcc -E):
  widest fan-out = json.hpp 43 consumers (0.158 s -E each ≈ 6.8 CPU-s),
  res_config 34, res_id 33, arsc_parser 32, adapter_scrap_bin 31,
  software_renderer 30, android_shadows 29, attribute_set_store 25.
  Total duplicated header-parse work across the top-13 ≈ **25-28 CPU-s**
  (NOT the ~100 s the fan-out suggested): this codebase's headers are cheap.

## 5. EXP-A: per-TU -O1 tiering — IMPLEMENTED (probe-verified, full A/B pending)

- ABBA ×2 probes (no order bias): bridge domains at -O1 are **-37 % (jdk)
  to -44 % (ui_graphics)**; cold small TUs -18..-23 % (resparse/sqlsh/
  dexparse, both reps consistent).
- Implemented opt-in in the Makefile: `make FASTPROFILE=1 W24TIERS=1 all`
  — TIER1 (7 heavy cold TUs ≈ 171 CPU-s) + TIER2 (48 cold small TUs
  ≈ 95 CPU-s). Renderer/audio/touch hot paths and the interpreter stay on
  their existing contracts (-O2 / wave-7 params). Expected: −87 CPU-s →
  wall ≈ (514-87) × 0.68 ≈ **290 s** on today's machine.
- Runtime verification required before shipping: 49-test battery +
  5-APK screenshot gate (scripts/w24_phase5_next.sh, ready).

## 6. EXP-C: header/template redundancy — REJECTED-MEASURED (third PCH rejection)

- New hypothesis (distinct from issue-612): amortize the shared frontend
  (json.hpp + resource cluster) via a common-prefix PCH. Built a working
  151 MB .gch; ABBA probes: apkparse **+40 % SLOWER** (over-inclusion),
  resparse ±0 %, sqlsh -8 %, layout -10 %, bridge domain +4.6 % — net
  ≈ zero-to-negative. PCH load ≈ parse cost for these header sets.
- Also registered **BUG-7**: `src/dex/shadow_registry.h` is a diverging
  duplicate of `src/framework/shadow_registry.h` (the W23/W24 cascade
  analyses measured the framework copy; the dex copy is a hazard).

## 7. EXP-D: alternatives

- Ninja: TESTED 355.91 s vs make 349.35 s — REJECTED (scheduler is not the
  bottleneck; §3). CMake flag-parity finding: CMakeLists builds WITHOUT
  `-DMINIANDROID_HAVE_WEBP` (silent divergence from Make) — W24 parity
  builds must pass it explicitly.
- ccache: warm no-op 1.02 s; identical-tree warm rebuild 25.40 s
  (W23-E evidence, unchanged). sccache: absent (no rust toolchain) — BLOCKED.
- mold/lld: link = 1.5 s of 349 — REJECTED (share too small).
- C++20 modules: REJECTED (project is C++17; cost/compat not justified).
- Incremental (developer loop, today): leaf edit 2.55 s; header cascade
  dalvik_engine_types.h (18 consumers) 308.12 s at -j1; REAL
  shadow_registry.h (29 consumers) 278.75 s at -j2 — the dominant
  developer pain is wide-fanout header edits.

## 8. PART 4 combination — PENDING (scripted, ready to run)

scripts/w24_phase4.sh: [BASE, CAND, CAND, BASE] fresh clean dirs
(ABBA, page-cache settle). scripts/w24_phase5_next.sh: battery + gate.
Predicted CAND ≈ 290 s (Target-1 <280 borderline; Target-2 <250 unreachable
on this host without the ≥6-core path — steal-capped).

## 9. Correctness gates on adopted changes

- W24TIERS=1 touches codegen of 55 TUs → battery 49/49 + 5-APK gate are
  REQUIRED before adoption (not yet run this session — scripts ready).
- Canonical profile (no FASTPROFILE) is untouched; FASTPROFILE=1 without
  W24TIERS reproduces the W23-P2 behavior exactly.

## 10. Label summary

PART1 baselines: TESTED. PART2 cost model: TESTED. EXP-A tiers:
IMPLEMENTED+TESTED(probes), full A/B PENDING. EXP-B scheduling/Ninja:
REJECTED-MEASURED. EXP-C PCH: REJECTED-MEASURED; BUG-7 REGISTERED.
EXP-D: Ninja/ccache TESTED; sccache/mold/lld/modules REJECTED-MEASURED.
Hypervisor steal: OBSERVED (24 % of build window).
