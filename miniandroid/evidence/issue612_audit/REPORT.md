# ISSUE-612 WAVE-2 — Modular Architecture & Fast Developer Feedback

**Date:** 2026-11-17 · **Host:** 2 vCPU / 4 GB RAM · **Binary:** production `build/miniandroid` untouched

## Phase 1 — Architectural audit (measured, not assumed)

### Root cause of the "4-minute change"

| Cost component | Measured | Note |
|---|---:|---|
| `dex/dalvik_engine.cpp` @ `-O2` | **216.24 s** | peak RSS ≈ 2.9 GB (cc1plus); THE dominant cost |
| `dex/dalvik_engine.cpp` @ `-O0 -g0` | **35.8–38.5 s** | frontend (parse/sema) dominated, not codegen |
| `dex/dalvik_engine.cpp` @ `-O0` + PCH probe | 36.4 s | **PCH rejected** — cost is the TU's own 94K lines, not headers |
| Full binary link, cold cache | ~56 s | first link after compile storms |
| Full binary link, warm cache | **1.27 s** | the linker is NOT the problem |

A one-line law change inside `dalvik_engine.cpp` therefore costs **216 s (production -O2) or 38 s (dev -O0)** — exactly the reported "4 minutes".

### Per-TU compile cost (pass A, `-O0 -g0`, real Makefile flags; full table `tu_cost_O0g0.json`)

| TU | s | | TU | s |
|---|---:|---|---|---:|
| dex/dalvik_engine.cpp | 35.79 | | main.cpp | 5.76 |
| runtime/execution_engine.cpp | 10.65 | | exp004_main.cpp | 4.03 |
| runtime/application_runtime.cpp | 8.38 | | resources/layout_inflater.cpp | 3.91 |
| webview/webview_engine.cpp | 6.93 | | dex/trace_exporter.cpp | 3.71 |
| framework/android_shadows.cpp | 5.88 | | resources/resource_parser.cpp | 3.37 |

At `-O2` only dalvik_engine was measured exhaustively (216.24 s); the remaining production `-O2` costs scale similarly (≈5–7× their `-O0` time).

### Header fan-out (who includes whom)

- `framework/android_shadows.h` → **18 TUs** (the wide-coupling header; any edit recompiles ~18 units)
- `dex/dalvik_engine.h` → **4 TUs** ✓ (good encapsulation already)
- `dalvik_engine.cpp` itself includes 56 headers

### Largest functions / classes (production code)

| Function | Lines |
|---|---:|
| `framework/android_shadows.cpp: CollectionShadow::dispatch` | **4,449** |
| `runtime/execution_engine.cpp: stage_execute_application_real_dalvik` | **2,056** |
| `framework/android_shadows.cpp: ActivityShadow::dispatch` | 1,360 |
| `framework/android_shadows.cpp: IntentShadow::dispatch` | 773 |
| `dex/dalvik_engine.cpp: DalvikExecutionEngine::*` methods (total) | **20,954 of 94,194** |

`dalvik_engine.cpp` structure: ~**73 K lines are FREE FUNCTIONS** (the per-law families `f141-*`, `w18-*`, `S67`, `F275-*`, …) living in anonymous namespaces starting at lines 64, 932, 4421, 7181 …; only 49 top-level `static` symbols. **A mechanical "move methods" split addresses only 22% of the file; the real Wave-3 boundary work is the free-function law families.**

## Delivered this wave (Phases 3/4/6/7 — additive, production untouched)

1. **`make DEV=1` profile** (`-O0 -g0`, separate `build_dev/` object tree — flags are not timestamped by make, so a dev build can no longer poison the production `build/` tree).
2. **Manifest-filtered module targets**: `make module MODULE=<m>` builds only `core_sources.manifest` sources of that module (dormant/broken sources excluded, matching the main build exactly).
3. **L0 component test**: `make DEV=1 mutf8_component` → links ONLY `dex/mutf8.o` (production implementation, no duplicate), **24 checks PASS in 0.4 s**. Documents real production laws: ULEB128 5-byte/0x0F discipline, SLEB128 sign-extension, MUTF-8 encoded-NUL, CESU-8 surrogate combine, declared/decoded cross-check (mismatch also clears `stream_ok`).
4. **`dev.py` driver (Phase 7 interface)**: `build module`, `test component`, `test module`, `test affected`, `run-apk`, `test regression`, `timings`.

## Phase 9 — Experiments (real edits, reverted afterwards; DEV=1)

| Exp | Change | Measured | Target | Verdict |
|---|---|---:|---|---|
| F | no-change rebuild ×3 | **0.02 s** (median) | <1 s | ✅ |
| L0 | mutf8 component change → test loop | **0.41 s** | <5 s | ✅ |
| D | framework component (android_shadows.o) | **6.8 s + 1.3 s link** | <15 s | ✅ |
| A | dalvik arithmetic-law touch (TU @ -O0) | **38.5 s** (+ link) | <30 s | ❌ needs the Wave-3 split |
| B/C | register / reflection laws | same TU as A — identical cost | <30 s | ❌ same reason |
| E | shared header (`android_shadows.h`, 18-TU fan-out) | **98.4 s** (-j1, includes A's dalvik rebuild) | — | ⚠️ measured; fan-out reduction is Wave-3 |

Production-profile reference: the same A-change costs **216 s + link** at `-O2` — the dev loop is ~6× faster today, and the split makes it ~1.5 s (law-family TU ≈ 10 s compile + 1.3 s link).

## Findings (audit byproducts)

1. **`src/resources/real_layout.cpp` is a broken dormant TU** (`AxmlNode`/`ResolvedValue`/`parse()` signature drifted from current headers) — not in `core_sources.manifest`, not linked; module targets now skip it. Proposed for the `DORMANT_SOURCES` whitelist or a repair.
2. **`-O2 -g` OOM family extends beyond CONT-37/39**: `build/resources/real_layout.o` died during an experiment pass; the CONT-37 `-g0` precedent should be audited for every heavy TU.
3. **ccache is not installable** on this host (apt blocked) — rejected for now; the `build_dev/` separation + incremental targets cover the same need.
4. **`-j2` is unsafe while the dalvik TU compiles** (2.9 GB peak at `-O2`, ~1.2 GB at `-O0`, 4 GB host) — `dev.py` uses `-j2` only for non-dalvik modules.

## Wave-3 split roadmap (Phase 2, incremental, one boundary per session)

1. **`dex/dalvik_detail.h`** — internal interface declaring the shared law-family helpers; anonymous-namespace helpers migrate to `namespace dalvik_detail` (explicit internal interface, no duplicate global state).
2. First extraction: **JSON/diagnostic glue** (`DalvikValue::to_json` family, ~1 K lines, lowest coupling) → `dex/dalvik_json_glue.cpp`. Validate: both TUs compile, link, one real APK re-run byte-compares status.
3. Then, by measured independence: **resource/asset law family** → **exception-handling family** → **opcode dispatch** (the 4.4 K-line core, last, behind a stable dispatch-table interface).
4. End state: law change → 1 TU of ~10-24 K lines ≈ **10 s compile + 1.3 s link + component test**, meeting the <30 s acceptance target with the production profile available on demand.

Phase 10 guardrails honored: no production behavior change (profile-gated), no existing test removed, experiments reverted (0 dirty), manifest remains the single source of truth, clean-build reproducibility preserved (`build/` untouched by DEV builds).
