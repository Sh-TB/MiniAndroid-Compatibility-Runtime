## WAVE 3 CHECKPOINT 4 — Reversible Dalvik pilot extraction + full equivalence proof (TESTED)

**Commit:** `98babaae` · **Parent:** `3d0e6c12` · **Safety ref:** `safety/pre-dalvik-wave3-5e7090e3`

### Symbol/dependency map (recorded before extraction)
Candidate family audited from the actual committed source (correcting the Wave-2 awk estimate): `DalvikValue::to_string` (dalvik_engine.cpp:595–611) and `DalvikValue::to_json` (613–653) — **41 lines total, the smallest independent family**.
- Fields touched: `type, int_val, long_val, float_val, double_val, bool_val, string_val, class_desc, object_id, ref_id` — all declared in `DalvikValue` (dex/dalvik_engine.h)
- Deps: `DalvikType` enum (header) + nlohmann::json; **NO anonymous-namespace helpers, NO static/global state** (verified by reading both bodies)
- Callers: header-declared API call sites only → moving the definitions cannot change call semantics
- Semantic risks: namespace mismatch (class is `miniandroid::dalvik::DalvikValue`) — handled by defining in the same namespace in the glue TU

### The extraction (one small commit, fully reversible)
1. `src/dex/dalvik_value_glue.cpp` — new TU, verbatim bodies, dependency map documented in its header comment, definitions inside `namespace miniandroid::dalvik`
2. `dalvik_engine.cpp` — the two bodies wrapped in `#ifndef MINIANDROID_DALVIK_MODULAR` (monolithic fallback preserved verbatim inside the guards)
3. Glue TU added to `core_sources.manifest` (76 sources, shared by Make + CMake): in monolithic mode it compiles **EMPTY** → the paired `#ifdef`/`#ifndef` guards make duplicate definitions impossible in any mode
4. `make DALVIK_MODULAR=1` / `make` — one-command switch; a **mode stamp** (`build/dalvik_mode_N.stamp`) forces `dalvik_engine.o` + `dalvik_value_glue.o` to rebuild on a mode flip (make tracks timestamps, not flags — a stale mixed-mode link would otherwise produce duplicate symbols)

### Equivalence matrix — six independent binaries, ONE screenshot SHA-256
Original Guess APK (`000ae2e5…`), same command, production/declared flags:

| Binary | Mode | Graph | Status | Screenshot SHA-256 |
|---|---|---|---|---|
| build/miniandroid (pre-edit, checkpoint 3) | mono | Make | SUCCESS ✅ | `87fe26766fc48d06c59d4c15` |
| build/miniandroid post-edit | mono | Make | SUCCESS ✅ | `87fe26766fc48d06c59d4c15` |
| build/miniandroid | **modular** | Make | SUCCESS ✅ | `87fe26766fc48d06c59d4c15` |
| build/miniandroid (stamp flip back) | mono restored | Make | SUCCESS ✅ | `87fe26766fc48d06c59d4c15` |
| cmake Release | mono | CMake | SUCCESS ✅ | `87fe26766fc48d06c59d4c15` |
| cmake Debug + `-DMINIANDROID_DALVIK_MODULAR` | **modular** | CMake | SUCCESS ✅ | `87fe26766fc48d06c59d4c15` |

**Byte-identical rendering across both build modes, both build graphs, and the mode round-trip.**

### Test evidence
- ODR: `nm -C` → exactly **1** `T miniandroid::dalvik::DalvikValue::to_json` definition in every mode/graph (plus a normal GCC `-O2` cold-clone, not a duplicate)
- `make DALVIK_MODULAR=1 test-core` → simple_test + s130_laws_test + gp582_engine_probe_test PASS, rc=0
- `make check-source-parity` → `[PARITY-OK] 76 core sources manifest-parity` (real_layout.cpp remains documented-dormant)
- No registration/static-init regressions observed (default Application binding + all 1228 DEX classes + EXP088 dispatch traces identical in modular run)
- L2 differential: the runtime screenshot diff IS the differential test (deterministic app output identical across modes); test-law was run at baseline (mono) and covered by test-core in modular mode

### Build cost of the pilot (honest)
The pilot proves the **mechanism** (guards, switch, equivalence protocol), not compile-time movement — 41 lines cannot move a 216 s TU. Mode round-trips measured: mono post-edit build 195.7 s; modular link-only 7.0 s (engine already guarded); mono restore 192.5 s; CMake mono full build 418.3 s; CMake modular (Debug) 204.3 s. Family-scale extraction (the ~73 K lines of law-families) still requires the `dalvik_detail` internal-interface step and must land as separate commits, each gated by THIS exact equivalence protocol (six-binary screenshot-hash matrix).

**Rollback:** `git revert 98babaae` (single commit) or `git checkout safety/pre-dalvik-wave3-5e7090e3 -- src/dex/dalvik_engine.cpp src/dex/dalvik_value_glue.cpp core_sources.manifest Makefile && make -j1 all`

**Next/final:** consolidated wave report.
