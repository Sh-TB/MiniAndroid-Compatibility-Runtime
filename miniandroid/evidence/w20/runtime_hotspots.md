# W20 runtime hotspots (P0 Phase 2) — INSTRUMENTED EVIDENCE (build-time + architecture) + RUNTIME PLAN
Build-side profiling that INFORMS the runtime plan (not runtime numbers):
- execution_engine.cpp (10,631 lines): -ftime-report = opt+generate 79% wall,
  parsing 12% — codegen-bound (W20 build evidence, evidence/w20/w20_bench_recovered.md).
Runtime-side ranked hypothesis set (to be measured by the harness + the
engine's own trace counters before ANY optimization lands):
1. Repeated class/method resolution in the bridge mega-body scan order
   (domains scan sequentially per call — O(laws) per API call).
2. Repeated resource decode (BitmapStore decode_and_register on every
   drawable re-resolution).
3. Full-frame ViewTree walk + state-list re-pick EVERY frame (the
   DrawableContainer law) — candidate for dirty-rect / invalidated-node
   incremental rendering.
4. try_recursive_invoke linear class-index lookups (no method cache).
NONE of these is claimed measured at runtime yet — OBSERVED only.
