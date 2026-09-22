# PIXEL PROVENANCE (canonical) — S82-GFX-REVOLUTION

## Instrument

`MINIANDROID_GFX_PROVENANCE=<path.json>` env on any run writes a small
JSON (Git-friendly):

```
{ "instrument": "MINIANDROID_GFX_PROVENANCE",
  "events": [ { origin, resid, path, ASSET_FOUND, RESOURCE_RESOLVED,
                DECODED, BITMAP_CREATED, VIEW_RECEIVED, DRAW_CALLED,
                width, height, color_type, src_density, dst{...},
                FAILURE? } ],
  "frame_census": [ { frame, total_px, nonwhite_px, unique_colors,
                      top_colors_rgb } ],
  "screenshot": { path, SCREENSHOT_CAPTURED, nonwhite_px, unique_colors } }
```

Origins: `imageview-direct` (AXML src path), `imageview-resid` (resid
chain), `background-bitmap`, `bitmapfactory-decode` (BitmapFactory.decode*
family), `canvas-drawBitmap` (CanvasShadow replay: BITMAP_RESOLVED +
REPLAYED bits).

## Divergence-read rules (§6 law, restated as executable predicates)

- `DECODED=1, DRAW_CALLED=0` → do NOT touch the decoder; the fault is in
  view wiring/paint stage.
- `DRAW_CALLED=1, nonwhite_px≈0` → canvas→surface fault (composition).
- `SCREENSHOT_CAPTURED=1 but flat` → capture/composition audit.
- Never blame the previous stage without its bit recorded.

## Fixture ladder (golden probes, §5)

| fixture | level | asserts |
|---|---|---|
| l0_solid | L0 | ColorDrawable bg + TextView + Button |
| l1_quadrant | L1 | RGBA PNG quadrants r/g/b/k + alpha checker |
| l2_colortypes | L2 | PNG color types 0/2/3/4/6 + palette tRNS |
| l3_density | L3 | mdpi..xxxhdpi variant pick + scale |
| l4_xmldrawables | L4 | shape/gradient/layer-list/selector bg |
| l5_canvas | L5 | drawRect fill/stroke, drawPath, drawText, save/clip/restore |
| l6_glsurface | L6 | GLSurfaceView clear color (today: expected FAIL — frontier) |

Build: `python3 scripts/s82gfx_gen_fixtures.py` +
`scripts/build/build_fixture_apk.sh` (ECJ+D8+aapt2, no Android SDK).
Run+assert: `python3 scripts/s82gfx_run_ladder.py` →
`run/s82gfx/LADDER_VERDICT.json`.

Status at HEAD: 6/7 PASS (l6 = documented F-NEW-157 frontier).
