# Upstream Implementation Inventory & Provenance Taxonomy (S61)

Canonical map of where Android/JVM behavior comes from, which
implementation layer it lives in, and how the campaign classifies every
source of truth. Provenance classes (law, §15):

**MOTHER** — the authoritative upstream implementation.
**DERIVED** — MiniAndroid code implementing upstream semantics.
**EXTRACTED** — API surface extracted from upstream without behavior.
**REFERENCE** — third-party implementations used for comparison.
**COMPATIBILITY** — runtime-provided stand-ins with documented deltas.
**ANALYSIS** — tooling that inspects bytecode/APKs without executing.
**TEST ORACLE** — golden fixtures used to verify behavior.
**RESEARCH ONLY** — exploratory tooling; not part of the runtime.

## 1. Implementation layers (bootclasspath / APEX / framework inventory)

| Layer | Artifact | Provenance | Role |
|-------|----------|------------|------|
| API surface (compile-time) | `tools/android-34.jar` | **EXTRACTED** (AOSP android-34 API stubs, Apache-2.0) | Compile fixture APKs against API 34 signatures. **NOT an implementation** — it contains no method bodies; the runtime must supply behavior. |
| DEX interpreter (behavior) | `miniandroid/src/dex/dalvik_engine.cpp` | **DERIVED** (AOSP ART / libdex semantics; per-opcode laws) | The compatibility runtime itself. |
| Framework View semantics | `src/runtime/execution_engine.cpp` + `src/framework/*_shadow.cpp` | **DERIVED** (AOSP frameworks/base View.java / ViewGroup.java / LayoutInflater laws) | measure/layout/draw/touch dispatch laws. |
| java.* / util.* behavior | dalvik_engine bridges + Collection/Atomic/Locks shadows | **DERIVED** (OpenJDK + libcore laws; S60: getDeclaredConstructor contract, unmodifiable views, Long.toString radix) | Core-class compatibility. |
| android.* stubs at run time | bridge_to_api + shadow registry | **COMPATIBILITY** | Classes absent from app DEX answer via bridges/shadows; documented deltas only (no silent fakes). |
| Reference oracles | `upstream/robolectric-oracle`, `upstream/paparazzi-oracle`, `tools/android-34.jar` | **REFERENCE** | Semantic comparison targets (Robolectric/android-all behavior; Paparazzi render contract). Not executable inside MiniAndroid; used for law extraction. |
| AOSP sources | fetched per-session for each law (tagged) | **MOTHER** | Every engine law cites the upstream file + tag in its comment block. |

## 2. This session's upstream law extractions (SOURCE → SEMANTIC CONTRACT → MINIANDROID TARGET)

### 2.1 R8 minification vs identity laws (F-108, S61)
- **SOURCE**: AOSP `AbstractComposeView` / `AndroidComposeView`
  (frameworks/base + androidx compose ui-android); R8 output of dooz v23
  (DEX ground truth: `scripts/s61_r381_dex_truth.py`).
- **SEMANTIC CONTRACT**: package-prefix identity is not a contract —
  obfuscation renames `Landroidx/compose/ui/platform/ComposeView;` →
  `Lho;`, `AndroidComposeView` → `Lt4;` (0 androidx/compose class names
  survive; 21 androidx names kept only for Parcelizer/serialization).
  The SURVIVING identity is the DEX hierarchy: `Lt4; → ViewGroup`,
  `Lho; → Lr; → ViewGroup`, and the dispatchDraw override contract.
- **MINIANDROID TARGET**: draw-path gates keyed on
  `chain_overrides_method(class, "dispatchDraw")` for non-framework
  classes (F-108), replacing the name-prefix gates.

### 2.2 Class initialization cost model (AOSP ClassLinker::EnsureInitialized)
- **SOURCE**: AOSP `ClassLinker::EnsureInitialized` semantics (init on
  first ACTIVE use, re-entrancy guard, super-first).
- **MEASURED (dooz v23, S61 phase timers)**: 6,453 ensure-calls = 5,784
  warm + 42 framework-skip + **627 cold <clinit> executions**; cold-init
  chains dominate the composition's runtime (the static-graph build is
  real interpreted work). `initialized_classes_` marks BEFORE <clinit>
  (re-entrancy law verified: no repeated cold init of the same class).
- **MINIANDROID TARGET**: honest budgeting — first-frame composition on
  R8 Compose apps requires the cold-init volume to run; PerfKit
  (`MINIANDROID_PERF_PHASES=1`) now makes this visible per run.

### 2.3 Evidence-pipeline cost laws (F-107 family, S61)
- **SEMANTIC CONTRACT**: tracing/diagnostics must never tax execution
  (AOSP/ART keeps trace machinery out of the hot path; Linux ftrace
  precedent). Profiled facts (gprof + rdtsc phase timers, dooz v23):
  function-local statics with non-trivial destructors cost a guard +
  `__tcf_*` cleanup-thunk traffic (739M thunk entries ≈ 50% wall),
  `std::function` churn 464M manager calls, per-instruction trace
  (Clock::now ×2 + O(n) ring erase) a top-2 cost, per-invoke
  `all_methods()` copies ~40 KB each.
- **MINIANDROID TARGET**: F-107a (trivially-destructible tables),
  F-107b (batched FIFO caps), F-107b2 (trace caps opt-in via
  `MINIANDROID_TRACE_CAP`), F-107c (interface-closure index lookup),
  F-107c2 (non-copying method accessors), F-107d (in-place overload
  selection). Zero semantics change; goldens PASS.

## 3. Corpus provenance (source-backed law, §5)

Every corpus APK is fetched from F-Droid (open-source catalog) with the
package id + versionCode + SHA256 recorded in
`docs/corpus/spotlight_manifest.json`. The registry
`miniandroid/APK_REGISTRY.json` continues to govern the regression
subset. Decompilers are NOT used for open-source apps (source-first
law); DEX forensics is used for closed-source apps only (Telegram).


## S62 upstream law extractions (2026-09-19)

| Finding | SOURCE | ALGORITHM / SEMANTIC LAW | TEST | MiniAndroid target |
|---|---|---|---|---|
| androidx ColorSpace Rgb static init is a REAL compute workload | androidx.compose.ui.graphics ColorSpaces.kt / android.graphics.ColorSpace (R8-renamed in dooz v23 as Lug0;/Lqk;/Lbl;/Lnd1; chain) | <clinit> eagerly builds per-colorspace transfer tables: 1,04-sample loops invoking a 180-unit transfer function 1,024 times = 184K interpreted instructions from ONE 23-unit <clinit> | run/s62_lbl_trace M3 METHOD-TRACE + scripts/s62_clinit_costs.py (top-10 chains = 74% of class-init time) | R-NEW-381 face: composition volume is REAL work; the lever is interpreter constant costs, not semantic patches |
| androidx FragmentManager host attach contract | androidx fragment FragmentActivity/FragmentController/FragmentManager.ensureExecReady | ensureExecReady throws ISE "FragmentManager has not been attached to a host." when mHost == null; the attach leg (FragmentController.attachHost) must run before any transaction | 3 spotlight games + Telegram golden all die at the SAME ISE (run/s62_game_mines + probes; csearch cross-hit) | R-NEW-331: ensure the real attachHost leg executes on the activity's mFragments object when the superclass chain contains FragmentActivity |
| Interpreter constant-cost inventory (S62) | this engine, measured | insn.pre 0.026% + insn.post 0.084% (bookkeeping clean); sget-object 23.3ms/call cold trigger; tri.resolve 15.8µs + em.setup 22.7µs per invoke; DalvikValue = 2×std::string per register access | PERF-PHASE/PERF-OPS/PERF-CI + S62 bucket timers (env MINIANDROID_PERF_PHASES=1) | F-109a/c landed (marginal); F-110 lever registered (per-invoke constants + register value copy cost) |
