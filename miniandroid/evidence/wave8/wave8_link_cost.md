# WAVE-8 Link Cost Analysis — why the static test relink costs 12.5 s
Measured: 2026-11-18, HEAD eac17a66 (verify scripts: `scripts/w8_gate.py`, fresh-process
`getrusage(RUSAGE_CHILDREN)` per measurement).

## The test binary inventory (exact)

| Binary | Size | Content |
|---|---:|---|
| build/tests/gp582_engine_probe_test | 116.0 MB | **103.6 MB .debug_\*** (56.3 info + 18.3 loclists + 17.8 str + 7.7 line) vs 8.2 MB .text |
| build/tests/simple_test | 115.7 MB | same profile |
| build/tests/s130_laws_test | 114.5 MB | same profile |
| build/miniandroid (main) | 120.2 MB | same profile |

- Link inputs: EVERY test exe links **all 82 core objects + 5 quickjs objects + thunk** raw
  (no archives) — Makefile rule `$(BUILDDIR)/tests/%: … $(CORE_OBJECTS) $(QUICKJS_OBJECTS) …`.
- Symbols in one test exe: 17,508.
- Linker: GNU ld 2.44 (ld.bfd); peak ld RSS 563 MB (fresh-process rusage of `make test-core`).
- Relink behavior: always a complete relink — one changed core object marks every test exe
  out-of-date. `test-core` = 3 exes × ~4.2 s ≈ 12.5 s (reproduced: 12.51 s, CPU 12.50 s).

## Where the time goes (measured decomposition)

1. **Debug-section merging dominates**: 103.6 MB of DWARF vs 8.2 MB code. ld merges
   .debug_info/.debug_loclists/.debug_str across 82 objects — that is most of the 4.2 s/exe.
2. **--strip-debug at link is COUNTERPRODUCTIVE**: gp582 relink A/B — full debug **4.78 s**,
   `--strip-debug` **5.03 s** (ld still merges debug internally before discarding; only the
   write shrinks). Measured, not assumed → debug *separation at link time does not pay*.
3. Archive scanning / symbol resolution: not the bottleneck (objects are linked raw; symbol
   count is small).

## The fix that actually works (adopted in build_dev_so/)

Move the 7 volatile dalvik TUs into `libminiandroid_dalvik.so` (PIC, **0.18 s relink**) and
keep tests static against the stable set: engine edits then require **zero test-exe relinks**
and the .so relink is 0.18 s. Full detail + rollback: `wave8_build_architecture.md`.
