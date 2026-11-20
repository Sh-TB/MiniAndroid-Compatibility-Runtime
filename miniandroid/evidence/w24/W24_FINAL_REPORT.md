# W24 FINAL REPORT — Evidence-Driven Build Architecture Investigation

Reference commit: 4ada9e3e (W23-G/P2). Investigation: 2026-11-20 (two
sessions, same-day baseline sets internally consistent; ABBA ordering used
for every probe and the final A/B). Host: 2 vCPU / 4 GB RAM / GCC 14.2.0,
shared-cloud VM with measured hypervisor steal.

## 1. Original and final clean cold build times

| Config | wall | CPU | RSS | binary sha16 |
|---|---:|---:|---:|---|
| Canonical -j1 -g (today) | 592.78 s rc0 | 590.2 | 1425 MB | — |
| FASTPROFILE -j1 (per-TU ranking source) | 501.83 s rc0 | 501.4 | 1221 MB | — |
| Ninja -j2 (flag-parity) | 355.91 s rc0 | 526.5 | — | — |
| raw xargs -P2 (no make) | 348.90 s | 509.0 | — | — |
| FASTPROFILE -j2 BASE (base_b, matched steal) | 350.39 s rc0 | 520.4 | 1221 MB | bfc0610db8578543 |
| FASTPROFILE -j2 BASE (base_a, heavy-steal window) | 440.64 s rc0 | 535.6 | 1221 MB | bfc0610db8578543 |
| **FASTPROFILE -j2 + W24TIERS=1 CANDIDATE** | **289.85 s avg rc0** (289.31 / 290.39, ±0.4 %) | **428.5 avg** (426.7 / 430.2) | 1167 MB | 32442d05a0e00528 (BOTH reps byte-identical) |

Day-to-day noise: yesterday's BASE measured 349.35/322.75 — today's
base_b 350.39 matches ⇒ machine speed comparable; base_a's +26 % was a
high-steal window (§3). All deltas below use the matched-steal pair
(base_b vs cand) plus ABBA cross-checks.

## 2. Total CPU work before/after and parallel efficiency

- CPU work: 520.4 → 428.5 = **−91.9 CPU-s (−17.7 %)** from the tiering alone.
- Parallel efficiency (CPU/(wall×2)): base_b 0.743, cand 0.739 — MATCHED
  (steal-normalized), so the wall win is real work elimination, not
  scheduling luck.
- Wall: 350.39 → 289.85 = **−17.3 % (−60.5 s)**. vs canonical -j1: −51.1 %.
- Peak RSS: 1221 → 1167 MB (−54 MB).

## 3. The real bottleneck: hypervisor steal time (measured, root cause)

- cgroup: cpu.cfs_quota_us = -1 (no quota), cpuset 0,1.
- Steal deltas sampled per build (/proc/stat, w24_combo_steal.txt):
  base_a +220.9 s of steal in a 440 s window (25 % of the 2-core budget),
  base_b +170.8 s (24.4 %), cand_a +138.5 s (24 %), cand_b +139.9 s (24 %).
- Scheduler exonerated twice (raw xargs -P2 348.90 s ≈ make 349.35 s;
  Ninja flag-parity 355.91 s). Core-idle is spread across the whole build.
- Effective capacity ≈ 1.47-1.5 cores of the nominal 2. The LPT floor for
  500 CPU-s was 251.7 s; for the NEW 428.5 CPU-s workload the same-capacity
  floor is 428.5/(2×0.743) = 288.4 s — the candidate at 289.85 s is AT the
  machine's effective floor for this CPU work.

## 4. PART 2 cost model (evidence/w24/*.csv)

- TU_COST_RANKING.csv (both profiles, true -j1 durations): ui_graphics 31.3
  > app_runtime 29.5 > io_lang 27.2 > execution_engine 27.0 > android_core
  26.0 > engine_invoke 22.4 > engine_core 22.0 > interpreter 22.0 > jdk
  20.3 > value_glue 17.9 > opcodes_invoke 15.5 > webview_engine 15.2 s.
  Small tail (<6 s): 67 TUs = 138.1 CPU-s. Link 1.5 s.
- COMPILER_PHASE_COSTS.csv (-ftime-report, exact build commands):
  parse ~19 % / lang-deferred ~7 % / **opt+generate ~76 %** / GC ~3 %.
- HEADER_COST_RANKING.csv + HEADER_PARSE_COST.csv (gcc -E): widest fan-out
  json.hpp 43 consumers (0.158 s each ≈ 6.8 CPU-s); top-13 duplicated
  frontend work totals ~25-28 CPU-s — the fan-out numbers OVERSTATED it.

## 5. EXP-A: per-TU -O1 tiering — IMPLEMENTED, FULL A/B PASS

- Probes (ABBA ×2): bridge domains −37..−44 %, cold small TUs −18..−23 %.
- Implemented: `make FASTPROFILE=1 W24TIERS=1 all` — TIER1 (7 heavy cold
  TUs) + TIER2 (48 cold small TUs); renderer/audio/touch hot paths and the
  wave-7 interpreter contract untouched; -O1 appended last.
- BUG-8 found+fixed (this wave): the tier lists used ':=' BEFORE BUILDDIR
  was defined (line 166) — target lists captured empty prefixes at parse
  time and the tiering silently no-op'd on a fresh checkout; block moved
  after the DEV=1 override (scripts/w24_move_tiers.py).
- Full-build A/B (ABBA): **−17.3 % wall, −17.7 % CPU, binary byte-identical
  across candidate reps**; RSS also −54 MB (-O1 TUs use less memory).
- Runtime verification: battery **49 PASS / 0 FAIL** (181.34 s) on the
  candidate binary; 5-APK gate on CANDIDATE codegen (dev tree rebuilt at
  candidate flags incl. explicit tier-1 PIC rules): **11/11 screenshot
  sha16 hashes ALL-IDENTICAL** to the canonical recorded set.

## 6. Performance targets (PART 6, measured not asserted)

- Target 1 (<280 s): MISS today by 10 s (289.85). The candidate CPU work
  (428.5 s) at this host's matched efficiency (0.74) has a floor of
  ~288 s — **the build now sits AT the effective-capacity floor**.
- Target 2 (<250 s): MISS — would need CPU ≤ 368 (−60 CPU-s more) or
  ≥3 effective cores. Steal (~24 % of every window) is not schedulable.
- Remaining limitation: CPU-work on cold TUs (~95 CPU-s of tier-2 headroom
  left at -O2; further cuts = hot-path risk) + host steal. NOT scheduling
  (exonerated ×2), NOT storage, NOT memory capacity (RSS 1167 MB of 4 GB).

## 7. EXP-B / EXP-C / EXP-D verdicts

- EXP-B scheduling: REJECTED-MEASURED (make ≈ xargs ≈ Ninja within ±2 %;
  idle is steal, not dispatch). Ninja migration not justified.
- EXP-C headers/templates: PCH REJECTED-MEASURED (third time — 151 MB gch;
  apkparse +40 % slower, net zero-to-negative). BUG-7 REGISTERED: two
  DIFFERING shadow_registry.h copies (src/dex stale duplicate of
  src/framework authoritative).
- EXP-D: ccache warm 25.40 s stands (W23-E); sccache BLOCKED (no rust);
  mold/lld REJECTED (link 1.5 s of 350); C++20 modules REJECTED; CMake
  flag-parity FINDING: CMake builds WITHOUT -DMINIANDROID_HAVE_WEBP.
- Incremental (developer loop, candidate config): leaf edit **2.04 s**;
  header cascades measured: engine_types (18 consumers) 308.12 s -j1,
  REAL shadow_registry (29 consumers) 278.75 s -j2.

## 8. Correctness evidence chain (PART 5)

1. Source manifest untouched (tiers are FLAG changes only; manifest parity
   check runs inside test-all).
2. Battery: 49/49 PASS rc0 at candidate flags (w24_cand_testall.log).
3. Gate: 11/11 screenshot hashes identical on candidate codegen
   (w24_gate_hashes_cand.txt vs evidence/w23/gate_hashes_postsplit.txt;
   machine verdict ALL-IDENTICAL in w24_gate_verdict.txt).
4. Reproducibility: candidate reps byte-identical (32442d05 == 32442d05);
   base reps identical (bfc0610d == bfc0610d).
5. Canonical path untouched: `make all` / `make FASTPROFILE=1 all` behave
   exactly as before (no-tiers make -n verified per-TU, incl. the wave-10
   PIC defaults and the wave-7 interpreter contract).

## 9. Label summary / rejected experiments and reasons

PART1/2 baselines+cost model: TESTED. EXP-A tiers: IMPLEMENTED + TESTED
(full ABBA + battery + gate PASS). EXP-B Ninja: REJECTED-MEASURED.
EXP-C PCH: REJECTED-MEASURED. EXP-D sccache: BLOCKED; mold/lld/modules:
REJECTED-MEASURED. Steal root-cause: OBSERVED + MEASURED. BUG-7, BUG-8,
CMake-parity: REGISTERED (BUG-8 FIXED+VERIFIED).

## 10. How to use

- Fast build: `make FASTPROFILE=1 W24TIERS=1 -j2 all` (~290 s on this VM
  class; ~275-280 s on a non-stealing host, since −92 CPU-s × matched
  efficiency).
- Prior fast path (`FASTPROFILE=1` only) unchanged and preserved as
  fallback; canonical `make all` untouched.
- Evidence: evidence/w24/ (7 deliverables + RAW_LOGS/ incl. combo logs,
  steal samples, gate hashes + verdict, testall log — force-added per the
  BUG-3 law).
