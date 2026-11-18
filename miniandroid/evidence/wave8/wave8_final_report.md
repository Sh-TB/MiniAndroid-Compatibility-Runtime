# WAVE-8 Final Report — the static relink bottleneck is eliminated
Base: eac17a66 (Wave-7). All numbers fresh-process measured this session; scripts persisted
(`scripts/w8_sodev.py`, `w8_loop.py`, `w8_gate.py`); rollback: `rm -rf build_dev_so/`.

## The 8 required answers

1. **Why does the static link take 12.4 s?** Every test exe links all 82 core objects raw and
   each carries **103.6 MB of DWARF vs 8.2 MB of code** (116 MB exe). `test-core` = 3 exes ×
   ~4.2 s ≈ 12.5 s, almost all of it debug-section merging in ld.bfd (ld RSS 563 MB).
   `--strip-debug` does NOT help — measured slower (5.03 s vs 4.78 s), because ld merges the
   debug data before discarding it.
2. **Can a shared development library avoid the repeated relink? YES — measured.** The 7
   volatile dalvik TUs recompiled -fPIC (one-time 114.6 s; PIC overhead ≈ 0: interpreter
   21.5 s vs 21.8 s) into `libminiandroid_dalvik.so`; relink = **0.18 s**; test exes never
   relink per engine edit. Non-PIC .so is factually impossible (`R_X86_64_TPOFF32` TLS
   relocation). Runtime proof: 3 original APKs, screenshot hashes IDENTICAL to canonical
   (Guess rc=0 `87fe2676…`; Dice/TicTacToe PARTIAL-unchanged, hashes byte-identical);
   battery 3/3 PASS on the .so path.
3. **Which object/archive boundaries are useful?** Exactly two: volatile dalvik set
   (dynamic .so) vs stable runtime (static, keeps debug). Archives (option E) superseded:
   member extraction cannot avoid the debug-merge cost; the .so removes it entirely.
4. **Can the offline environment support a faster linker?** No: `find /` for
   gold/lld/mold = zero hits; apt blocked (not root). Documented BLOCKED, not attempted further.
5. **New measured interpreter edit→test:** **20.7–21.1 s (×3, median 21.04 s)** vs 36.4 s
   baseline — **−42%**, target <30 s MET; the <15 s stretch target remains PARTIAL: the loop
   is now 99% compiler (20.8 s PIC compile of the interpreter TU itself).
6. **New compile and link RSS:** interpreter cc1plus 1,070–1,123 MB; bridge (PIC) 2,155 MB
   (fits 4 GB); ld test-link 563 MB; .so link ~130 MB-class (0.18 s). All < 4 GB ✓.
7. **Does production still use the original validation path? YES** — production static build
   untouched (build/, same flags), monolith fallback re-verified in WAVE-7 (`DALVIK_SPLIT=0`
   rc=0) and unchanged since; the .so path is an isolated `build_dev_so/` experiment.
8. **Status ledger:** shared-lib dev path IMPLEMENTED+TESTED (isolated); strip-debug
   REJECTED (measured slower); non-PIC .so BLOCKED (TLS); alternative linkers BLOCKED
   (offline); archives SUPERSEDED; ccache BLOCKED; Makefile wiring of the dev-so targets
   PENDING (adoption recipe documented; opt-in only); interpreter <15 s and bridge <30 s
   PARTIAL (blockers: interpreter TU compile cost; 55K-line bridge function at 2,155 MB).

## Final success metric (source edit → trustworthy runtime result)

| Loop | Static (before) | .so dev path (after) |
|---|---:|---:|
| Opcode | 12.8–17.5 s | **9.6–9.8 s** (target <10 MET) |
| Interpreter | 36.4 s | **20.7–21.1 s** |
| Bridge | ~56 s | ~40.6 s (compile-bound) |
| .so relink per engine edit | (12.5 s test relinks) | 0.18 s |

## Reproduction & rollback

- One-time build: `python3 -I scripts/w8_sodev.py` (creates `build_dev_so/` from existing
  objects + PIC recompiles; nothing else modified).
- Loop benchmark: `python3 -I scripts/w8_loop.py`. Gate timing: `scripts/w8_gate.py`.
- Rollback: `rm -rf build_dev_so/` (production tree never changed this wave).

## Next highest-value steps

1. Wire `dev-so` targets into the Makefile (opt-in, SONAME-stamp dependency hygiene).
2. Apply the same .so treatment to the DEV -O0 path (potential DEV loop ≈ 9.5 s compile +
   0.2 s + tests → likely <15 s stretch target).
3. Interpreter <15 s requires attacking the 20.8 s interpreter compile itself (hot/cold
   separation without semantic change — Phase-5 constraints remain).
