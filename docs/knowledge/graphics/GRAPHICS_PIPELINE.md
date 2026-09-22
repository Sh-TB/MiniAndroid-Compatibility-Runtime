# GRAPHICS PIPELINE (canonical) — S82-GFX-REVOLUTION

HEAD at writing: aef6c1acee14

## The real pipeline (as implemented; single source of truth)

```
APK zip
  └─ res/ (aapt2-linked resources.arsc + binary AXML + drawables)
        │
        ├─ XML-LAYOUT path: LayoutInflater (arcs → ViewShadow tree)
        │     bg color / bg drawable / src drawable → node fields
        └─ PROGRAMMATIC path: DEX bytecode → shadow dispatch
              setBackgroundColor(I)      → ViewNode.bg_color        (CM-020)
              setBackgroundResource(I)   → ViewNode.bg_resource_id  (F-NEW-158)
              setBackground(Drawable)    → ColorDrawable map → bg_color
              setImageResource(I)        → ViewNode.image_resource_id
              BitmapFactory.decode*      → BitmapStore
              Canvas.draw*               → CanvasShadow op list

RENDER (stage_render_frame, every frame):
  window bg (theme windowBackground) → per-node tree walk:
     bg laws: state-list pick (G06 §5) > shape (F-053) > programmatic color
              > bitmap bg (F-NEW-158) > Button face fallback
     image laws: ImageView path/densities → decode_image_bytes →
                 density scale + FIT_CENTER (G04 §4/§12)
     custom views: real onDraw bytecode replay (CAMPAIGN 013)
     dialogs: rendered on top (CAMPAIGN 013 B1)
  → FrameBuffer → framebuffer_ copy → screenshot.png (+ .ppm fallback)

GL/EGL: ABSENT (F-NEW-157 family). SurfaceView/GLSurfaceView/TextureView
produce no pixels today — documented frontier, P9 is the live probe.
```

## Evidence-bit chain (§6 law) — every bit is instrumented

ASSET_FOUND → RESOURCE_RESOLVED → DECODED → BITMAP_CREATED →
VIEW_RECEIVED → DRAW_CALLED → CANVAS_WRITTEN → SURFACE_UPDATED →
COMPOSITED → SCREENSHOT_CAPTURED

Instrument: `MINIANDROID_GFX_PROVENANCE=<out.json>` (see
PIXEL_PROVENANCE.md).

## Software renderer law

Deterministic CPU framebuffer (no GPU dependency). One framebuffer, one
compositor (stage_render_frame), one capture (stage_capture_output).
libpng (color types 0/2/3/4/6 + tRNS), libjpeg, libwebp codecs behind ONE
format-detecting decoder (`decode_image_bytes`).
