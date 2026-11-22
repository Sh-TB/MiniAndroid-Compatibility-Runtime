# S27-W1 — the VectorDrawable rasterization law (#633/#634) — 2026-11-22

**Base: S26-W1 tip (`2603311c` + the local auto-snapshot `fc9b19a5`). Mission: flip's vector paint blocker — the last [P1-2-IMAGE-BLOCKED] on the interactive wall.**

## 1. The blocker, root-caused

flip's coin face (`org.ecos.logic.flip_a_coin_3`, MainActivity, view 569, contentDescription "head") sets a `Landroid/graphics/drawable/VectorDrawable;` via setImageDrawable — the engine's R-NEW-360 probe found no bitmap field → `[P1-2-IMAGE-BLOCKED]` ×1/run. The pieces ALREADY in place: the C9-3 intrinsic law resolves the vector entry (`res/Qp.xml`, intrinsic 525×525 at density 420), the TypedArray.getValue law (F-CSW-4) lets androidx's own vector parser run, and the renderer paints direct-BitmapStore pixels through the g04 fit-rect + draw_image pipeline (execution_engine.cpp image law). The GAP was only the pixel bridge: the parsed vector wrapper carried intrinsic dims but NO pixels.

The vectors themselves (dumped from the APK with exp067_axml_parser): `res/Qp.xml` + `res/Qp1.xml` — `<vector 200dp×200dp viewport 512×512 autoMirrored>` with 3 fill-only `<path>` children (fillColor `#fffd9a0c` rim circle r=247.83, `#ffd2cfce` face circle r=189, `#ff8c8484` glyph) using M/m + arc (a) + H/V/C/Z pathData. No gradients, no groups, no strokes — a fill rasterizer covers them exactly.

## 2. The law (S27-W1, implemented — 3 pieces)

1. **`src/framework/vector_raster.{h,cpp}` (NEW)**: `vector_rasterize(root, w, h, rgba, stats)` — viewport→bounds aspect-preserving centered mapping; pathData parser (M m L l H h V v C c S s Q q T t A a Z z; arcs via W3C endpoint parameterization → ≤90° cubic slices; 16 fixed segments per curve — fully deterministic); even-odd scanline fill (AOSP default nonZero — identical for the recorded non-self-intersecting contours; the deviation is NAMED in the header); over-composite in document order; straight-alpha RGBA (StoredBitmap premultiplied-OFF contract); honest `VectorRasterStats` (paths/painted/skipped/contours/first_skip).
2. **C9-3 vector branch** (dalvik_bridge_domain_app_runtime.cpp): after the intrinsic fields, the SAME parsed AXML rasterizes ONCE at the intrinsic size (capped 2048) → `heap.allocate("Landroid/graphics/Bitmap;")` + `BitmapStore::store(oid, w, h, rgba, "vector-decode:<entry leaf>")` → bound as the wrapper's **"bitmap"** field (the R-NEW-360 probe's FIRST probe name). Honest `[S27-W1] vector rasterized <path> <w>x<h> paths=P/N contours=C bmp_oid=<oid>` (or SKIPPED with the reason) — no invented pixels anywhere.
3. **Two downstream acceptances**: `route_bitmap_object` treats `vector-decode:` provenance as pipeline-reached (it IS the pixels; no zip re-decode of an XML), and the renderer's image branch prefers the direct-pixel draw when the node's bound bitmap is vector-decoded — otherwise the path-decode branch would raster-decode `res/Qp.xml` as PNG and fail. Both keep the raster path untouched for every other resource kind.

## 3. Measurement (final S27-W1 binary)

- **flip ×3 (both attempts)**: `[S27-W1] vector rasterized` ×2/run (Qp + Qp1), `[P1-2-IMAGE] setImageDrawable view=569 → real pipeline (S27-W1 vector-decoded pixels)` ×1/run, deterministic face `b270ff04` ×3. The image pipeline is REACHED end-to-end; the frame-level verdict stays DEFAULT_BACKGROUND_ONLY with first_missing_stage=APP_DRAW_OPS — because of the NEW named blocker below.
- **NEW named blocker (S27-W2)**: flip's MainActivity.onCreate dies at `Landroidx/lifecycle/viewmodel/InitializerViewModelFactory;.create pc=75` — `IllegalArgumentException: "No initializer set for given class androidx.lifecycle.SavedStateHandle..."` — via LifecycleRegistry.sync → SavedStateHandleAttacher.onStateChanged → SavedStateHandlesProvider.performRestore → kotlin SynchronizedLazyImpl (F-016 uncaught, APP BOUNDARY unwind). The content tree never attaches (ContentFrameLayout children=0 — the coin views are shadow-nodes but never join the render tree) — the vector pixels are bound but the app dies before painting them. **The S27-W2 law: the androidx viewmodel initializer DSL** — InitializerViewModelFactory must record the app's `initializer<T> { }` lambdas (addInitializer/ctor varargs) and answer create(modelClass) by RUNNING the registered lambda through real bytecode.

## 4. Files

`src/framework/vector_raster.h`, `src/framework/vector_raster.cpp` (NEW; `core_sources.manifest` + Makefile), `src/dex/dalvik_bridge_domain_app_runtime.cpp` (C9-3 branch), `src/framework/android_shadows.cpp` (route acceptance), `src/runtime/execution_engine.cpp` (direct-pixel preference). Evidence: `evidence/s27/` (flip_r1..r3 first attempt, flip_v2_r1..r3 final, wall_*, s27_build.log, s27_build2.log, `s27w1_matrix.tsv`); battery `evidence/s27/s27w1_law_battery.log`.

**Status vocabulary**: IMPLEMENTED (vector rasterization law, deterministic) / REACHED (the image pipeline end-to-end, first time for a VectorDrawable) / UNCHANGED-FACE (b270ff04 — the app dies at the S27-W2 viewmodel-initializer blocker before painting) / NAMED-NEXT (InitializerViewModelFactory.create law).
