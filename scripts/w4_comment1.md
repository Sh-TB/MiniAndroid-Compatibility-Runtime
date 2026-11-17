## WAVE 4 CHECKPOINT — Phase 0/1/2 complete: measured why 202 s is spent in optimization (TESTED)

**Commit:** `c5b919b4` · **Safety ref:** tag `safety/pre-dalvik-wave4-c5b919b4` created · working tree clean · Wave-3 commits + `DALVIK_MODULAR` switch verified intact.

### Phase 1 — pass-cost attribution (exact production command, same machine, g++ 14.2.0)

Exact production rule for `dalvik_engine.o` discovered: **`-O2 -g0`** (the Makefile already forces `-g0` on the heavy TUs — full `-g` does not fit this 4 GB host: `-O2 -g` run was **OOM-killed, cc1plus at 3,093 MB peak**; `-O2 -g1` fits at 190.1 s). Baseline reproduction: **219.7–222.0 s** wall, peak 2,871 MB, obj 9.20 MB.

Toggle deltas (identical command + one disabled pass each):

| Disabled pass | Wall | Δ vs 222.0 s | Share |
|---|---:|---:|---:|
| **`-fno-ipa-cp`** (interprocedural constant prop + cloning) | 170.2 s | **−51.8 s (−23%)** | biggest |
| **`-fno-ipa-sra`** (interprocedural scalar replacement) | 185.8 s | **−36.2 s (−16%)** | |
| **`-fno-ipa-cp-clone`** (function cloning alone) | 185.9 s | **−36.1 s (−16%)** | |
| `-fno-unroll-loops` | 205.8 s | −16.2 s (−7%) | |
| `-fno-inline-functions` | 213.3 s | −8.7 s (−4%) | NOT dominant |
| `-fno-tree-vectorize` | 215.7 s | −6.3 s (−3%) | |
| `-fno-ipa-icf` | 216.8 s | −5.2 s (−2%) | |

**Verdict: the cost is interprocedural specialization (IPA-CP/SRA/clone ≈ −88 s combined), NOT classic inlining/vectorization.** It is driven by function size fan-out — and the size distribution explains why (compiler-truth text sizes from a `-g1` build, 973 symbols):

### The structural discovery: the TU is 60% ONE function

Corrected family map (comment/string-stripping parser + `nm`/`addr2line` cross-check, `evidence/issue612_audit/wave4_family_map.json`, `wave4_symbol_map.json`):
- `dalvik_engine.cpp` = 94,204 lines, **227 top-level definitions** in `namespace miniandroid::dalvik` (91,310 lines covered; NO anonymous namespaces — the Wave-2 "73K lines of free functions in anonymous namespaces" description was inaccurate: 152 header-declared methods + 28 free functions, 20 of them static)
- **`DalvikExecutionEngine::bridge_to_api` spans lines 38595–93789 = 55,195 lines (~60% of the file), generating 1.09 MB of object text** (largest symbol by far; next: `fetch_decode_execute` 199 KB, `try_recursive_invoke` 135 KB)
- The other ~36 K lines: opcode handlers (`execute_*`), view/layout dispatch, engine lifecycle/wiring, 3 small tail helpers

This is why NO flag combination can reach the target: `-Og` 63.4 s, `-O1` OOM-killed (3,125 MB), `-O0 -g0` (DEV) 36.3 s — the MONOLITH cannot go under 30 s by profile alone.

### Phase 2 — profile table (same source, same machine)

| Flags | Wall | Peak MB | obj | rc |
|---|---:|---:|---:|---|
| `-O2 -g0` (production) | 219.7–222.0 s | 2,871 | 9.20 MB | 0 |
| `-O2 -g1` | 190.1 s | 3,019 | 32.99 MB | 0 |
| `-O2 -g` | killed | 3,093+ | — | OOM |
| `-O1` (+`-g`) | killed | 3,125 | — | OOM |
| `-Og` (+`-g`) | 63.4 s | 2,647 | 10.45 MB | 0 |
| `-O0 -g0` (DEV) | 36.3 s | 2,605 | 21.90 MB | 0 |

### Phase 3 plan (next checkpoint)

Mechanical, semantics-preserving split driven by the verified map — one monster TU (`dalvik_bridge.cpp` = `bridge_to_api`), one rule-handler TU (`dalvik_opcodes.cpp` = interpreter loop + `execute_*` handlers — the "Dalvik rules" area), one core TU (lifecycle/wiring + tail helpers), one small internal header declaring the 28 shared free functions, with `DALVIK_SPLIT=0/1` one-command fallback to the original monolith and the Wave-3 equivalence protocol (battery + Guess screenshot-hash) as the gate. Per-function optimization attributes NOT needed unless measurements demand them (avoid semantic risk).
