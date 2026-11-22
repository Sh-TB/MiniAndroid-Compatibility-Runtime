# S27-W2 — the androidx viewmodel initializer DSL law (#633/#634) — 2026-11-22

**Base: S27-W1 (`21b4ffdb`). Mission: the blocker NAMED at the end of S27-W1 — flip's `MainActivity.onCreate` died at `InitializerViewModelFactory.create pc=75` with the AOSP IAE `"No initializer set for given class androidx.lifecycle.SavedStateHandlesVM"` (LifecycleRegistry.sync → SavedStateHandleAttacher → SavedStateHandlesProvider lazy → APP BOUNDARY unwind, F-016 process death) — the content tree never attached and the S27-W1-rasterized coin face never painted.**

## 1. Root cause (bytecode + four probe runs)

The whole chain is REAL androidx bytecode. Dumping the classes (`tools/dump_method_bytecode.py` + the new `scripts/dex_dump_overloads.py` — find_method returns only the FIRST name match; the two `create` overloads needed a per-overload walker):

- `InitializerViewModelFactory.create(Class)` = the 5-insn `$default$create` bridge.
- `InitializerViewModelFactory.create(Class, CreationExtras)` (the pc=75 thrower): `iget initializers[]` → loop → `getClazz$lifecycle_viewmodel_release` → `Intrinsics.areEqual` → match ⇒ `getInitializer` → `Function1.invoke(extras)`; else the honest IAE.
- The DSL chain: `InitializerViewModelFactoryKt.viewModelFactory` → `new InitializerViewModelFactoryBuilder` → the inline `initializer` (`Reflection.getOrCreateKotlinClass` — RAN, minting the F-282 Class token obj#887) → `Builder.addInitializer` (iget list → `new ViewModelInitializer` → `List.add`) → `Builder.build()` → `new-array` → `InitializerViewModelFactory.<init>`.

**Four probe runs pinned the break**: `[S27-W2] create recv=o1082 model=SavedStateHandlesVM arr=1084 len=0` — the factory's array EXISTED with a present, authoritative `__array_length__=0` (F-NEW-268b) and a direct slot scan (`array[0..63]`) found NOTHING. The `viewModelFactory{}` DSL transfer chain (ArrayList backing store → `List.add` → `toTypedArray` → vararg) crossed three engine dispatch boundaries and answered EMPTY — the real loop faithfully iterated a zero-length array and threw the honest AOSP IAE. The elements themselves WERE constructed (the ctor ran — the F282 token trace shows the KClass arg flowing).

## 2. The law (S27-W2, implemented — 3 pieces in `try_recursive_invoke`)

1. **Law A — the construction record**: `ViewModelInitializer.<init>` records each element's oid into a bounded engine-side log (`s27w2_pending_initializers_`, deduped). The element identity is its OWN constructor — unconditional, real bytecode.
2. **Law B — Builder.build() materializes the REAL array**: `InitializerViewModelFactoryBuilder.build` allocates the true `[ViewModelInitializer` array (`__array_length__` = N, `array[i]` slots), constructs the factory on the heap with the array bound as the `initializers` field, returns it. The recorded elements are consumed (bounded, one-shot per build). Honest `[S27-W2] Builder.build materialized N recorded initializer(s)` line.
3. **The create() mirror law** (from the first build of this wave): at `InitializerViewModelFactory.create` with a real heap array, match each element's `clazz` Class-token descriptor (F-282/F-103 `__referent_desc` identity) against modelClass and invoke the matching `initializer` Function1 through this same real dispatch path (runtime-class-first, F-068). **No match → fall through: the REAL loop bytecode executes unchanged and the AOSP IAE stays honest.** Env-gated `MINIANDROID_S27W2_TRACE` diagnostics name every link (recv/model/array/len/match/lambda).

## 3. Measurement (final S27-W2 binary)

- flip probe run: `[S27-W2] Builder.build materialized 1 recorded initializer(s) → factory obj#1083 initializers array obj#1082` → `create ... arr=1082 len=1` → `initializer[0] clazz=SavedStateHandlesVM MATCH` → **`Function1.invoke ran real bytecode`** — SavedStateHandlesVM constructed through the app's own initializer lambda.
- **The F-016 process death is GONE**: the run now completes cleanly (RUN_END = F-NEW-200 stub-census only; the lone grep "uncaught" hit is the long-known benign deferred AppLocales NameNotFoundException synth, present in every earlier run too).
- **flip ×3: face `b270ff04` deterministic and UNCHANGED** — the verdict stays DEFAULT_BACKGROUND_ONLY with first_missing_stage=APP_DRAW_OPS because of the NEXT named blocker.
- **NEW named blocker (S27-W3)**: flip's `setContentView(activity_main)` RAN and its root (obj 406) was recorded and **linked under the activity view** (`[F023-PARENTLINK] setContentView(View) content view=406 linked under activity view=32`), but the render census tree never receives it — every frame walks `FitWindowsLinearLayout(854) → ContentFrameLayout(858) children=0`. The law for S27-W3: the content-view attachment must materialize as the ContentFrameLayout's child in the census/render tree (U007 inflate root → AppCompat decoration parent chain → the census walk).

## 4. Files

`src/dex/dalvik_engine_invoke.cpp` (the three law pieces + diagnostics), `src/dex/dalvik_engine_impl.h` (`s27w2_pending_initializers_`). Evidence: `evidence/s27/` (w2_probe..w2_probe4 — the root-cause chain, w2_v2_r1 — the full-law probe, w2_flip_r1..r3, w2_* wall, `s27w2_matrix.tsv`, battery `s27w2_law_battery.log`); builds `s27w2_build*.log`. New tool: `scripts/dex_dump_overloads.py`.

**Status vocabulary**: IMPLEMENTED + VERIFIED (the initializer DSL law — construction record + build materialization + create match, all real bytecode) / EXCEPTION GONE (F-016 process death eliminated) / UNCHANGED-FACE (b270ff04 ×3 — the S27-W3 census-tree attachment blocker) / NAMED-NEXT (content-view attachment law).
