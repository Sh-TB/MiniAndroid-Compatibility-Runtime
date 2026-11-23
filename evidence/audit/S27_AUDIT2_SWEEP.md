# S27-AUDIT-2 — the friend-method applied by the engine itself

**Date:** 2026-11-23 · **Base:** 7e96b97e0 (S27-AUDIT squash) · **Branch:** main

## Motivation

The external code audit (36 findings) found what the engine's own waves had
missed because it used a different lens: hostile-input boundary review plus
systematic tooling, instead of runtime-completion forensics. This wave
re-runs that lens FROM INSIDE the project, systematically, so the next
external reviewer finds less than the engine finds about itself first.

## 1. memcpy sweep (278 sites)

Harness: `scripts/s27_audit2_memcpy_sweep.py` (top-level-comma arg parser,
paren-aware multi-line join, guard-window classifier).

| class   | sites | verdict |
|---------|-------|---------|
| CONSTANT (literal / sizeof-only) | 129 | no free length |
| GUARDED (comparison involving the length var within 4 lines above) | 107 | bounded |
| FLAGGED (non-constant length, no nearby comparison) | 16 | manually reviewed |
| UNPARSED (args fully on following lines) | 26 | manually reviewed |

Classifier limitation found during verification: the 4-line guard window is
too short for some guards (e.g. `dex_parser.cpp:96`'s `size < sizeof(DexHeader)`
check sits 7 lines above the memcpy), so every FLAGGED and UNPARSED site was
reviewed by hand. Highlights:

- `manifest_reader.cpp:415` — `attr_ptr + sizeof(AxmlAttribute) > data +
  attr_array_end` guard BEFORE the copy: clean.
- `apk_parser.cpp:357` — EOCD read guarded by `eocd_offset + sizeof(eocd) >
  data.size() -> reject`: clean.
- `dex_parser.cpp:96` — header copy is preceded by `if (size < sizeof(DexHeader))
  return`: clean (the sweep's flag was a window artifact, recorded honestly).
- UNPARSED cluster (`dalvik_engine.cpp:1038..1050`,
  `dalvik_bridge_domain_ui_graphics.cpp:2522..3591`) — fixed-size (4/8-byte)
  register copies from `DalvikValue` union members: host-internal, clean.

**Verdict: 0 real findings across all 278 sites.**
Full table: `evidence/s27/s27_audit2_memcpy_sweep.csv`.

## 2. Parser fuzzing (6000 inputs, ASan + UBSan)

Harness: `tests/s27_audit2_fuzz_test.cpp`, standalone make target
`make test-audit2-fuzz` (NOT a battery member — the sanitizer runtime stays
out of the pinned production test groups). Seed-fixed (`0x527A27D2`,
mt19937) so every run is byte-reproducible. Seeds are semi-valid skeletons
(AXML chunk tree + UTF-16 string pool, DEX header + string pool, ARSC table
+ string pool); mutations mix bit flips, targeted header-field corruption,
byte blasts, truncation and padding, 1–3 per input. Contract (the gp_dex003
no-crash law, generalized): every input returns gracefully — a signal, a
hang, or an ESCAPEE C++ exception (`bad_alloc`, `length_error`, …) is a
FINDING and names its seed.

```
axml: 2000 iters — accepted 0 / rejected 2000 / ESCAPEE 0
dex : 2000 iters — accepted 965 / rejected 1035 / ESCAPEE 0
arsc: 2000 iters — accepted 917 / rejected 1083 / ESCAPEE 0
ALL CLEAN (0 escapee exceptions)
```

The DEX and ARSC arms accepted ~46% of mutations, so the fuzzers exercised
deep parse paths (string pools, type/proto/method tables, class defs, value
decoding) under ASan+UDSan, not just header rejection. **Verdict: the audit
fixes hold under systematic mutation; no new memory-safety bug surfaced.**

## 3. New law: setLength growth maps to the ART OOM contract (S27-A2)

Found by this wave (the audit had not named it):
`StringBuilder.setLength(n)` growth performed a real heap allocation of
`(n - size)` JVM chars with no cap — a hostile
`setLength(Integer.MAX_VALUE)` died with an UNCAUGHT `bad_alloc` (runtime
kill) where ART throws a catchable `java.lang.OutOfMemoryError`.

Fix (both engine copies, `dalvik_bridge_domain_android_core.cpp` and
`dalvik_engine.cpp`): growth requests whose byte size (2 bytes/char)
exceeds the R-NEW-169 heap budget (1 GiB) now `throw_deferred` an
`Ljava/lang/OutOfMemoryError;` with the ART-style message
("Failed to allocate a N-byte allocation") and skip the write-back — the
same contract shape the new-array OOM law established. Receipt tag:
`setlength-oom`.

## 4. Other classes verified clean

- `system(` / `popen(` (12 hits): production paths have NONE — the hits are
  the exp007_012 experiment harness (developer-supplied paths, offline tool)
  and removed-dependency comments; `exp004_main` was a
  `run_task1_base_system(` substring false positive.
- `resize(static_cast<size_t>)` (5 hits): apk_parser size is fenced by
  AUDIT-L4 (tellg fence + 512 MiB cap); the engine cache resizes are bounded
  by u16 bytecode indexes / table-validated ids; the two setLength sites
  became the §3 law.

## Gates

- `make test-audit2-fuzz` — ALL CLEAN (§2), under ASan+UBSan.
- Engine TU rebuild (`dalvik_engine.o`, `dalvik_bridge_domain_android_core.o`)
  + `s27_audit_laws_test` / `s25_laws_test` regression relink+run — recorded
  in the wave commit message.
- The full 54-test battery rerun is scheduled with the next production
  build (this wave deliberately did not touch the pinned battery groups).

## Artifacts

- `scripts/s27_audit2_memcpy_sweep.py` — the sweep harness
- `tests/s27_audit2_fuzz_test.cpp` — the fuzz battery (+ Makefile target)
- `evidence/s27/s27_audit2_memcpy_sweep.csv` — all 278 classified sites
- `evidence/s27/s27_audit2_fuzz.log` — the recorded fuzz run
- this report
