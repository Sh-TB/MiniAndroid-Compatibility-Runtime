# EXP — GRAPHICS/IMAGE END-TO-END PIPELINE (UNIFIED_011.2, §13/§14/§15)

Campaign: UNIFIED_011.2 — full-repository validation campaign
Target APK: **simplestopwatch** (omegacentauri.mobi.simplestopwatch, SHA-verified
`b3ec1a5ec24ce53b…` from the F-Droid corpus cache) — a REAL APK whose
`activity_stop_watch.xml` puts `android:src="@drawable/lock|settings|menu"`
on three `ImageButton`s.

## Pipeline trace (§13 required layers), PASS/FAIL per layer

| # | Layer | Status | Evidence |
|---|-------|--------|----------|
| 1 | resource reference (android:src="@drawable/lock") | PASS | AXML attribute parsed by AxmlParser; `act_stop_watch` layout contains ImageButtons with src refs |
| 2 | ARSC lookup | PASS | `[U007-RES] ResourceRuntime loaded: … named_ids=67 types=9` |
| 3 | drawable path | PASS (after fix) | `layout_inflater.cpp:615` `drawable_path_for_name()` → `res/drawable-hdpi-v4/lock.png` (highest-density match) |
| 4 | decoder | PASS | `renderer::PNGDecoder` (libpng 1.6.48, CAMPAIGN-010 R1 lineage, 12/12 fixture suite) |
| 5 | Bitmap/Drawable object | PARTIAL | Real decoders exist; no `Bitmap` heap object model — pixels passed straight to draw call (documented gap, safe) |
| 6 | ViewShadow state | FIXED | **§14 finding confirmed**: `src_drawable_path` (AXML path) vs `image_drawable_path` (runtime API path) — the render stage checked ONLY `image_drawable_path`, so XML-src images were silently dropped |
| 7 | render dispatch | FIXED | `stage_render_frame` now consumes `src_drawable_path` fallback + runtime resid resolution chain |
| 8 | Canvas.drawBitmap | PASS | `SoftwareCanvas::draw_image` alpha-blend (EXP-088 A4) |
| 9 | framebuffer | PASS | EXP-092 framebuffer pipeline unchanged |
| 10 | PNG screenshot | PASS | libpng encoder, 3/3 deterministic |

## Root cause (before)

`ExecutionEngine::stage_render_frame` had exactly two image branches:

1. `image_drawable_path` non-empty → extract + PNG decode + draw_image
   (populated only by the EXP-088 A4 attr capture and the UNIFIED_007
   conversion — NOT by the standard `LayoutInflater` XML path)
2. `image_resource_id != 0` → gray "IMG" placeholder box

The standard inflation path stores XML `android:src` into
`ViewNode::src_drawable_path` (layout_inflater.cpp:661) — a field NO render
code ever read. Result: simplestopwatch rendered three **blank blue buttons**
(ssw_frame_before_full.png).

Additionally the runtime `setImageResource(resid)` chain was dead:
`resource_drawable_paths_` was **read but never populated anywhere**, so
runtime-set images could never resolve to APK assets either.

## Fix (after)

1. `DalvikExecutionEngine::populate_resource_drawable_paths(entry_names)` —
   populates the R-field-name → APK-entry map from the real res/ listing with
   AOSP-style density preference (xxxhdpi > xxhdpi > xhdpi > hdpi > mdpi >
   plain > mipmap). Called once per run from `stage_render_frame`.
2. Render dispatch fallback: `image_drawable_path` → `image_resource_id`
   resolution chain → `src_drawable_path` (AXML). Decode by magic bytes:
   PNG / JPEG (FFD8FF) / WebP (RIFF…WEBP). Placeholder "IMG?" only when the
   path resolved but decode failed; legacy "IMG" when nothing resolved.
3. Renderer still consumes only resolved paths — no APK ZIP knowledge leaked
   into the render layer (§16 modularity boundary preserved).

## Evidence

| File | Meaning |
|------|---------|
| ssw_buttons_before.png | 3 blank blue ImageButtons (crop 650,1780–1080,1920, 2×) — SHA `d495e3cb2ccf6c11` full frame |
| ssw_buttons_after.png | lock / settings-gear / menu icons rendered — full frame SHA `2a12587a0acf196c…` |
| ssw_frame_before_full.png | full 1080x1920 frame before fix (930,980 nonwhite px) |
| ssw_frame_after_full.png | full frame after fix (916,815 nonwhite px; the −14,165 delta is the WHITE icon pixels replacing blue background inside the buttons) |

Determinism: 3/3 runs → identical `2a12587a0acf196cb9a52a521d6a7bc7d72e2d21dfa71eba41a694dbaa3d8c1b`.

Baseline policy (§28/§30): the change was NOT chosen by intuition — the after
frame matches the real app (a stopwatch does show lock/settings/menu buttons).
The matrix anchor moved from `d495e3cb2ccf6c11` to `2a12587a0acf196c` with the
reason recorded in `scripts/u011_test_matrix.py`.

## Reproduce

```bash
cd miniandroid && make -j$(nproc)
python3 scripts/download_test_apks.sh          # SHA-verified external cache
python3 scripts/u011_test_matrix.py --binary build/miniandroid \
        --apk-dir <cache> --out run/e2e_imgres
# expect: simplestopwatch BASELINE_MATCH (2a12587a0acf196c…),
#         telegram_v12 BASELINE_MATCH (088ea640…, unchanged by design R1)
```

## Remaining known gaps (deferred, with reasons)

- `setImageBitmap/setImageDrawable/setImageURI` still discard object state
  (android_shadows.cpp:1331) — the runtime has no Bitmap pixel model to copy
  from; faking one would be dishonest. Deferred until a Bitmap heap object
  lands.
- FAB (FloatingActionButton) is not matched by the `is_image_view` check
  (it subclasses ImageView under a different class name string).
- VectorDrawable / StateListDrawable / NinePatch rendering: XML drawables
  resolve to paths but decode as "IMG?" placeholders (no vector renderer).
- APUT auto-grow semantics (writes past array end extend `__array_length__`)
  differ from real Dalvik AIOOBE — unchanged this campaign (regression risk).
