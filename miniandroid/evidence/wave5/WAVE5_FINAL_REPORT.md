# ISSUE-612 WAVE 5 — FINAL REPORT (Dalvik incremental build acceleration & verification)

**Start:** `f9ab6e28` era (wave-4 final `e455aee6`) · **Wave-5 commits:** `0a03944b` (opcode decomposition), `a4d38745` (evidence) · **Safety tags:** `safety/pre-dalvik-wave3-5e7090e3`, `safety/pre-dalvik-wave4-c5b919b4` — both preserved.

## Phase 3 — Opcode TU decomposition (TESTED, commit `0a03944b`)

The wave-4 opcode TU (16,967 lines, ~48 s) was decomposed **3-way with dependency evidence** — every cut at verified brace-depth-2, and the 7-TU build linked **first try with zero undefined symbols**, proving the boundaries need no new cross-TU plumbing (all references already resolve via `dalvik_engine.h` + `dalvik_engine_internal.h`):

| New TU | Lines | Content | -O2 compile |
|---|---:|---|---:|
| `dalvik_interpreter.cpp` | 6,112 | `fetch_decode_execute` (the interpreter loop) | ~34 s |
| `dalvik_opcodes.cpp` | 4,286 | new-instance / instance-of / field / static ops + `resolve_field` | ~5-6 s |
| `dalvik_opcodes_invoke.cpp` | 6,757 | invoke family + control flow + `build_invoke_args` + shadow dispatch + framework glue | ~10 s |

Manifest/Makefile/CMakeLists/mode-stamps updated to 7 parts; `DALVIK_SPLIT=0` fallback list extended and **verified by round-trip** (below).

## Phase 1/2/6 — Gates and baselines (5 repetitions each, median / min–max / variance; RAM + rc recorded)

| Gate | Target | Measured | Status |
|---|---:|---|---|
| No-op build | <1 s | **1.07 s** (1.03–1.08, var 0.0) | TESTED — at target, remainder is make's own scan |
| Ordinary opcode edit — field ops (-O2, incl. link) | <30 s | **12.79 s** (12.55–12.94) | ✅ MET |
| Ordinary opcode edit — invoke ops | <30 s | **17.51 s** (17.40–17.62) | ✅ MET |
| **Two opcode edits simultaneously** | <30 s | **26.35 s** (25.04–28.34) | ✅ MET |
| Engine invoke / engine core edit | <30 s | 23.2 s / 23.5 s | ✅ MET |
| Interpreter-loop edit | <30 s | 40.78 s (35.7–41.4) | PARTIAL — it is ONE 5,433-line function (can't split across TUs); covered by the DEV loop |
| Bridge TU edit | <30 s | 47.67 s (40.5–48.7) | PARTIAL — host cc1plus ceiling (-Og); covered by DEV loop |
| Header touch (`dalvik_engine_internal.h` fan-out) | measure | 158.21 s (146.8–167.6) | TESTED — rebuilds all 7 engine TUs |
| Link only | — | **2.16 s** | TESTED |
| Targeted test (`make test`, exe current/relink) | — | 0.03 s / 1.09 s | TESTED |
| **DEV `-O0` edit→test loop** | <15 s | **21.36 s** (20.0–21.5) | PARTIAL — 11.7 s of it is the static relink of the 115 MB test binary; the -O0 compile itself is 9.5 s |
| DEV entry (one-time) | — | 266.0 s (full -O0 tree into `build_dev/`) | TESTED |
| `DALVIK_SPLIT=0` monolith build | works | **215.1 s**, peak 2,869 MB, parity OK 82 | ✅ TESTED |
| `DALVIK_SPLIT=1` flip back | works | ~168 s (FS timeline 21:41:17→21:44:05; wrapper mis-reported 2.0 s — noted honestly) | ✅ TESTED |
| Clean production split build | measure | **504.3 s**, peak 2,126 MB, rc=0 | TESTED |
| `-j2` parallel probe (2 mid TUs) | no OOM | 27.8 s, 1,029 MB | TESTED — safe for mid TUs; avoid -j2 when bridge (-Og, 2.1 GB) is in the set |

**Wave-4 gates status now CLOSED:** all five repetitions ran; median/min/max/variance recorded with per-rep exit codes and RAM peaks in `evidence/wave5/wave5_gates.json`; the DEV O0 end-to-end loop and the `DALVIK_SPLIT=0/1` round-trip — the two wave-4 PENDING items — are now TESTED.

## Phase 4 — Build dependency findings (TESTED)

- **No production-object poisoning**: `DEV=1` builds into `build_dev/` (verified by object sizes: `build_dev/dex/dalvik_opcodes.o` 2.36 MB = -O0 vs `build/dex/dalvik_opcodes.o` 487 KB = -O2; production `make all` after DEV = 2.1 s no-op, correct). The wave-2 separation is real and works.
- **Dependency tracking correct**: header touch rebuilds exactly the 7 engine TUs (158.2 s) and nothing else; per-TU edits rebuild exactly one TU + relink (12.8–23.5 s observed = compile + 2.16 s link).
- **Mode stamps correct**: both flips forced exactly the affected set to rebuild (SPLIT=0 forced the monolith — 215 s; SPLIT=1 forced 7 parts — 168 s by FS timeline).
- **Known quirk**: `make test` re-runs only when the test exe relinks; the test exe statically links all 80 core objects (115 MB binary, ~11.7 s link). A shared core library would cut the DEV loop to ~10 s — future work, not done this wave.

## Phase 5 — Runtime equivalence (TESTED)

- Batteries: `make test` PASS, `test-core` 3/3, `test-law` 36 PASS / 0 FAIL, `check-source-parity` OK (82 sources).
- **Three APKs × two binaries (7-TU split vs wave-3 monolith -O2), screenshot hashes all IDENTICAL**:
  - Guess `ru.zxalexis.ugaday_15`: SUCCESS ✅ — `87fe26766fc48d06c59d4c15` (9th independent binary with this hash)
  - Tic-tac-toe `com.itsfrz.tictactoe_5`: PARTIAL SUCCESS — `d55056a8928a26ffeb15f66d` identical on BOTH binaries (pre-existing runtime gap, not a split regression)
  - Dice-roller `tech.gaskell.diceroller_1_debug`: PARTIAL SUCCESS — `46b07062ba6fe36ca8a6e42d` identical on BOTH binaries (same)

## Phase 6 — Acceptance summary

The P0 objective — an ordinary Dalvik rule change rebuildable and testable in <30 s without a monolith rebuild — is **MET at production -O2** for opcode field edits (12.8 s), opcode invoke edits (17.5 s), and even simultaneous edits to both opcode TUs (26.4 s), and in the DEV profile for every engine TU (21.4 s incl. test). Honest residuals: interpreter-loop edit 40.8 s and bridge edit 47.7 s at production profiles (both are single-giant-function TUs; both covered by the DEV loop), and the DEV <15 s stretch goal is 21.4 s due to the static test link.

## Rollback

- Wave-5 decomposition: `git revert 0a03944b` → returns to the wave-4 5-TU split (equivalence already proven for that state).
- Monolith fallback (verified): `make DALVIK_SPLIT=0 -j1 all` — 215 s, parity OK, identical Guess hash.
- Safety refs unchanged: `safety/pre-dalvik-wave3-5e7090e3`, `safety/pre-dalvik-wave4-c5b919b4`.

## Evidence files (committed)

`evidence/wave5/wave5_gates.json` (per-rep wall/rc/RAM + stats + compiler commands), `wave5_dev_loop.json`, `wave5_roundtrip_clean.json`, `wave5/guess7/`, `wave5/com.itsfrz.tictactoe_5/`, `wave5/tech.gaskell.diceroller_1_debug/` (screenshots + console logs). Scripts: `scripts/w5_gates.py`, `w5_dev_loop.py`, `w5_roundtrip.py`, generator `scripts/w4_split.py` (now emits 7 TUs).
