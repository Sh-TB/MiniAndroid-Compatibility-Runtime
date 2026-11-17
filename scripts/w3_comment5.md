# ISSUE-612 WAVE 3 — FINAL REPORT

**Date:** 2026-11-17 · **Baseline:** `5e7090e3` · **Final:** `98babaae` · **Safety ref:** tag `safety/pre-dalvik-wave3-5e7090e3` (never force-updated)

## Success criterion

> MiniAndroid executes one simple, original, prebuilt Android APK through the normal runtime path and displays its genuine expected first screen. A meaningful interaction should work where supported.

**MET (TESTED / OBSERVED)** — Guess (UgadaY 0.15), the simplest already-considered candidate, executed through the normal `run` path on production binaries: genuine first screen rendered byte-deterministically, and a canonical click drove the app's own dalvik `onClick` to a visible state change.

## §11 deliverables, with evidence labels

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Safety tag + baseline SHA | **TESTED** | tag `safety/pre-dalvik-wave3-5e7090e3` → `5e7090e3`, created before any change |
| 2 | Reproduced Production + DEV benchmarks | **TESTED** | dalvik TU `-O2` 219.28 s (Wave-2's 216.24 s reproduced), `-O0 -g0` 47.10 s w/ `-ftime-report` (35.8–38.5 s without); commands, obj sizes, peak RSS in `evidence/issue612_audit/wave3/benchmarks.json` |
| 3 | Compiler phase breakdown | **TESTED** | `-ftime-report`: `-O2` → parsing 11.5 s (5%), **opt+generate 201.8 s (93%)**; `-O0` → parsing 11.2 s (25%), opt+generate 29.1 s (64%). Raw reports committed. Wave-2's "frontend-dominated" claim CORRECTED (it held only at -O0) |
| 4 | Dalvik symbol/dependency map | **TESTED** (pilot family) + **PARTIAL** (global) | pilot family fully mapped (41 lines, zero file-local state, deps listed in `dalvik_value_glue.cpp` header); global map: only 20,954 of 94,194 lines are class methods, ~73 K are anonymous-namespace law families — next-family boundaries require the `dalvik_detail` internal-interface step (documented, not done this wave) |
| 5 | Reversible pilot extraction | **TESTED** | `DalvikValue::to_string/to_json` → `dex/dalvik_value_glue.cpp` behind `DALVIK_MODULAR=0/1`; monolithic fallback preserved verbatim; one-command switch with mode stamp |
| 6 | Make + CMake parity | **TESTED** | BOTH graphs build both modes through the shared `core_sources.manifest` (76 sources, `[PARITY-OK]`): Make mono/modular + CMake Release mono (418.3 s) + CMake Debug modular (204.3 s); `cmake` installed via pip (system apt blocked — recorded) |
| 7 | Component + integration tests | **TESTED** | baseline: `make test` 5/5, `make test-core` 3/3, `make test-law` 37 PASS; modular mode: `make DALVIK_MODULAR=1 test-core` 3/3 PASS; L0 mutf8 component test 24 checks |
| 8 | APK provenance + SHA-256 | **TESTED** | `ru.zxalexis.ugaday` 0.15/15 · F-Droid https://f-droid.org/packages/ru.zxalexis.ugaday/ · upstream https://github.com/zxalexis/guess · SHA-256 `000ae2e5751f9a85c331d6205881d3db5dc81a00d10522485d9026b0494f8c3d` · original prebuilt artifact, never rebuilt/patched |
| 9 | Complete runtime trace | **TESTED** | every chain stage logged: ZIP/resources → manifest → default Application → DEX (1228 classes) → class/superclass resolution (1278 entries) → field resolution (`etInput` EditText) → `Activity.onCreate` dispatch → 7-view inflate → 3-frame render → `Status: SUCCESS ✅` (stub census 12 IMPLEMENTED / 2 STUBBED / 0 MISSING) — `evidence/wave3_guess/run1/console.log` |
| 10 | Screenshot + SHA-256 | **TESTED** | `run1/screenshot.png` SHA-256 `87fe26766fc48d06c59d4c15…`; visually verified genuine screen (title "Guess the number (1 – 100)", EditText, blue "Put the number" button) |
| 11 | Interaction + state change | **OBSERVED** | `--click-test` canonical DOWN/UP pipeline → app's own `onClick` bytecode executed → ViewTree text `'   '` → `'Invalid number'`; interaction screenshot `204f8970cb238b5d39c5…` (≠ baseline hash — real rendered state change) |
| 12 | Before/after build time + peak RAM | **OBSERVED** | production incremental rebuild 245.8 s (mixed-tree repair run); pilot round-trips: mono 195.7 s / modular link 7.0 s / mono-restore 192.5 s; peak cc1plus RSS 2.87 GB (unchanged); **no build-time claim is made from the 41-line pilot** — family-scale movement is the follow-up |
| 13 | Remaining blockers | see list | below |
| 14 | Exact rollback command | **TESTED** (switch round-trip already exercised both modes) | `git revert 98babaae` — or `git checkout safety/pre-dalvik-wave3-5e7090e3 -- src/dex/dalvik_engine.cpp src/dex/dalvik_value_glue.cpp core_sources.manifest Makefile && make -j1 all` |
| 15 | Commit + comment links | **TESTED** | commits `3d0e6c12` (APK evidence), `98babaae` (pilot); comments 1–5 on this issue |

## Remaining blockers / honest limits

1. **The 4-minute dalvik TU remains 4 minutes at -O2** — the pilot proves the extraction MECHANISM; actual cost movement requires family-scale extraction (~73 K lines) gated on a small `dalvik_detail` internal interface, one family per commit, each with the six-binary equivalence protocol. **PENDING.**
2. **2 stubbed calls** in the Guess stub census (per-call truth in `api_trace.json`) — the SUCCESS is stubby-bounded and labeled as such.
3. **CMake parity in modular Release** was exercised as Debug+modular (204.3 s); modular+Release through CMake builds the same manifest path but was not separately run — **PARTIAL**.
4. `resources/real_layout.cpp` remains a broken dormant TU (documented, not linked; Wave-2 finding, unchanged).
5. EditText inset callbacks (`REC-MISS` ×3) and framework `TextAppearance 0x103003e` law-table warning — non-fatal, recorded for a future wave.

## Determinism note (§3 L)

Runs 1 and 3 (identical commands) produced **byte-identical screenshots**; run 2 differs only by the intended click interaction. No nondeterminism observed across six binaries / three graphs.

## Architecture notes for the next agent

- Monolithic fallback is the DEFAULT and lives verbatim inside `#ifndef MINIANDROID_DALVIK_MODULAR` guards in `dalvik_engine.cpp`; the modular twin lives in `dalvik_value_glue.cpp` under the mirrored `#ifdef`, in the same namespace (`miniandroid::dalvik`), in the shared manifest, so both build graphs stay one-definition-clean in both modes.
- The mode stamp (`$(BUILDDIR)/dalvik_mode_N.stamp`) is why a mode flip cannot silently mix objects — make tracks timestamps, not flags.
- DEV=1 builds (`-O0 -g0`) go to `build_dev/`; production `build/` is never touched by dev loops.
- Temporary downloads: none this wave (the APK came from the existing verified handoff set); no APK binaries are committed.
