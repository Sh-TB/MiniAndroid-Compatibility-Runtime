**S14 closeout — AUD-47 / AUD-49 / AUD-52 closed (commit 04e2ef4e, follow-up to the v2 audit comment above)**

**1. AUD-49 (W23-BUG-7) — CLOSED, dedupe integrated.**
The stale `src/dex/shadow_registry.h` copy registered by W24 (68f4fe58) is committed EMPTY (0 bytes, `git show` verified); the authoritative `src/framework/shadow_registry.h` is 515 lines (md5 5d7bedd71ca1). Include census: 20+ includers ALL resolve to the framework header — zero references to the dex path, no Makefile/CMake references. Removed via `git rm` (repointing not needed); production battery re-run after removal: **49/49 PASS rc=0** (RAW_LOGS/s14_battery_after_dedupe_e05_2026-11-20.log, w15 13/13 rows).

**2. AUD-47 (#627 E-05) — CLOSED, machine-verified.**
Comment 6991611630's "UBSan run 7/7" was unreproducible as recorded (no named vectors, no sanitizer profile in the repo). This session added:
- `make UBSAN=1` opt-in profile (`-O1 -g1 -fsanitize=undefined -fno-sanitize-recover=all`, tree `build_ubsan/`; `-g1` after full `-g` DWARF ENOSPC'd the 4.6G disk at test #23 on the first attempt — codegen/sanitizer semantics unchanged);
- standalone probes `tests/w22_e05_ubshift_probe.cpp` (fixed form, 7 vectors) + `tests/w22_e05_ubshift_probe_oldform.cpp` (deliberate pre-W22-A signed shift) + a one-shot `make UBSAN=1 ubsan-e05` target;
- +4 `const_high16` rows in `w15_dalvik_lit_from16_law_test.cpp` — 7 engine-tested vectors total.

Results: fixed-form probe **7/7 bit-exact rc=0**; old-form probe UBSan abort **"left shift of negative value -1", rc=1** — the hub's evidence reproduced exactly; w15 13/13; and the **FULL 49-test battery built AND run under UBSAN=1: 49/49 PASS rc=0, zero UB findings** (RAW_LOGS/s14_ubsan_battery_2026-11-20.log). Both W22-A fix sites re-verified in-tree (`dalvik_interpreter.cpp` CONST_HIGH16 + dormant monolith `dalvik_engine.cpp:22438-22451`). Honest caveat: the hub's exact 7 vectors were never published; the probe set is the audit's reconstruction (the 3 named vectors 0x8000/0xABCD/0xFFFF + boundary neighbours 0x0000/0x0001/0x7FFF/0x8001).

**3. AUD-52 — COMPLETED, peak memory measured.**
`/usr/bin/time` is absent in the audit sandbox (first attempt collapsed rc=127 with all 50 ctest entries "Not Run" — recorded honestly, then redone with `scripts/s14_time_wrapper.py`, os.wait4 rusage = the whole-tree per-process peak, the metric GNU time reports). Full BUILD_TESTS=ON cmake 4.4.5+ninja build at -j2: **rc=0, peak 1235 MB (1264520 KB), wall 491.91 s** (W22-C production baseline 1427 MB at -j1; concurrent per-instant sum not observable — documented limitation). CTest on the same tree: **49/50** — the only non-pass is `miniandroid-smoke` "Not Run" (its `miniandroid_test` target is not a dependency of the battery; all 49 battery tests passed, 0.46 s total). Logs force-added per the BUG-3 law.

**4. Ledger state.**
AUD-47/49/52 rows rewritten from the committed logs: verdict totals now **CONFIRMED 35 / REJECTED 11 / PARTIALLY CONFIRMED 6 / BLOCKED 8 / PENDING 2 / SUPERSEDED 1 = 63 == rows**, independent validator PASS (`scripts/validate_ledger.py`). MASTER_AUDIT prose row-count fixed (stale "62 rows" the validator never checked) and deliverables v2.1 regenerated in `evidence/audit/`.

**Remaining open (unchanged, each with a named blocker):** coder-local artifacts (#634 MG-012, #295/#296/#297 stroke laws, RC-12 commits, #630/#631 layout apps — owner branch `layout-geometry-001` is coder-local); runtime claims blocked on missing original APKs (#597/#618/#623); AUD-10b (job pools at -j4+); AUD-42; #626 PR rebase; AUD-54 focused-test queue (25/234 file:line cites machine-checked so far).
