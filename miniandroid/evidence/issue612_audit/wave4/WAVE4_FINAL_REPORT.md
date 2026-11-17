# ISSUE-612 WAVE 4 — FINAL REPORT (Dalvik fast iteration)

**Baseline:** `c5b919b4` · **Final:** `97228c1a` · **Safety ref:** tag `safety/pre-dalvik-wave4-c5b919b4`
**Session cut off mid-wave — gates measurement is PARTIAL; see honest-status table.**

## What was achieved

### P0 structural result: the 94K-line TU is split and equivalent (TESTED)
`dalvik_engine.cpp` (94,204 lines) → 5 verbatim-range TUs + one linker-driven internal header:

| TU | Lines | Content |
|---|---:|---|
| `dalvik_engine_core.cpp` | 9,476 | lifecycle/wiring + stateful helper single-definitions |
| `dalvik_engine_invoke.cpp` | 12,091 | invoke/recursive dispatch + view dispatch |
| `dalvik_opcodes.cpp` | 16,967 | interpreter loop + execute_* rule handlers |
| `dalvik_bridge.cpp` | 55,384 | **bridge_to_api — ONE function, 55,195 lines (~60% of the file)** |
| `dalvik_engine_tail.cpp` | 600 | framework helpers + result report |

`dalvik_engine_internal.h`: F-107a trivial tables block (187–589), IEEE bit/conv law helpers (21553–21586), BridgeCensus family (38357–38417), C9 png/display block (38470–38549, de-anon'd + inline), 4 stateful helpers (de-static'd, single definitions in core), 8 cross-TU declarations, 2 extern variables — every addition linker-driven and reviewed.
`DALVIK_SPLIT=0/1` one-command fallback (monolith kept in repo, dormant in split mode, mode stamp forces rebuild on flip). Wave-3's `DALVIK_MODULAR` switch unchanged.

### Equivalence proof (TESTED)
- Guess APK (original, SHA-256 `000ae2e5…`) on the split binary: **SUCCESS ✅, screenshot SHA-256 `87fe26766fc48d06c59d4c15` — byte-identical to ALL six wave-3 binaries (7th independent binary)**
- `make test` 5/5 PASS · `make test-core` 3/3 PASS · `test-law` 36 PASS / 0 FAIL · `check-source-parity` OK (80 sources)

### Phase 1/2 findings (TESTED, commit `ab9c59e5`)
- Production dalvik rule is `-O2 -g0` = **219.7–222.0 s** (reproduced); pass attribution: **IPA-CP −23%, IPA-SRA −16%, ipa-cp-clone −16%, unroll −7%, inline −4%, vectorize −3%, ICF −2%** → the cost is interprocedural specialization driven by the monster function
- `-O2 -g` is **impossible on this host** (OOM at 3,093 MB) — the Makefile's `-g0` is load-bearing; `-O1` OOM; `-Og` 63.4 s; `-O0 -g0` (DEV) 36.3 s → **no flag combination gets the monolith under 30 s — the split was mandatory**

### The bridge TU and the host memory ceiling (TESTED)
`dalvik_bridge.o` is the ONLY TU that exceeds the host cc1plus ceiling at `-O2` (OOM kill at ~3,030 MB across plain/-fno-ipa-cp/-fno-ipa-sra/GGC-tuned variants). It compiles with `-Og -g0`: **2,124 MB peak, 38.9 s** (CONT-37 precedent extended, documented in the Makefile). Runtime impact on the Guess workload: mono `-O2` median 0.9 s vs split `-Og`-bridge 1.0 s (**+1.3 % = noise**).

## Honest status vs the wave-4 targets

| Gate | Target | Measured | Status |
|---|---:|---|---|
| Ordinary rule edit (opcodes TU, `-O2`) | <30 s | full split rebuild 133.8 s ⇒ opcodes ≈ 48 s + link | **PARTIAL — not met at -O2** |
| Ordinary rule edit (opcodes TU, DEV `-O0`) | <30 s | projected ≈ 7 s compile + 1.3 s link + test ≈ 12–15 s (**projected, not yet measured end-to-end**) | **PENDING** |
| Bridge TU edit | <30 s | 38.9 s (-Og) + link | PARTIAL |
| No-op build | <1 s | not formally measured (session cut) | PENDING |
| Component/integration test | <5 / <15 s | batteries observed running (test-law ≈ tens of s) | PENDING (5-rep script written: `scripts/w4_gates.py`) |
| Full production build | measure | split full rebuild 133.8 s incremental; clean-build total ≈ sum of parts | PARTIAL |
| `DALVIK_SPLIT=0` fallback build | works | switch + stamp implemented; round-trip not yet executed | **PENDING** (exact command documented) |

**Root cause of the remaining >30 s at `-O2`:** the opcodes TU is still ~17 K lines (≈48 s at `-O2`). The wave's P0 is achievable in the DEV profile (-O0 per-TU ≈ 7 s) and by further splitting opcodes into 2–3 TUs (~8 K lines each ≈ 15–25 s at `-O2`) — that is the precise next step, gated on the same equivalence protocol (screenshot-hash + batteries).

## Rollback
- Split: `git revert 97228c1a` — or `make DALVIK_SPLIT=0` after `git checkout safety/pre-dalvik-wave4-c5b919b4 -- core_sources.manifest` is NOT needed (manifest switch is built in).
- Safety tag: `safety/pre-dalvik-wave4-c5b919b4` (never force-updated).

## Next-session checklist (from saved files)
1. Run `python3 -I scripts/w4_gates.py` (5-rep gates; script is saved and working — it was cut by the session time budget, not by an error).
2. Measure the DEV end-to-end loop: edit `dalvik_opcodes.cpp` → `make DEV=1 -j1 all` → `make test-core` (expect <30 s).
3. Split `dalvik_opcodes.cpp` further (cut at the same verified brace-depth-2 boundaries near 27866/31964) if -O2 gate must hit <30 s.
4. Execute the `make DALVIK_SPLIT=0` round-trip once and record it.
5. Commits this wave: `ab9c59e5` (phase 0-2 evidence), `97228c1a` (the split).
