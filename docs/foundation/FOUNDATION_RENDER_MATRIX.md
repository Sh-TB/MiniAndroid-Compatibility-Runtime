# FOUNDATION_RENDER_MATRIX — canonical (S67, updated as evidence lands)

Live path: CanvasShadow (record-then-replay) → SoftwareCanvas → FrameBuffer →
libpng RGB. Canvas ops below verified against the f08_canvasops DEX-driven probe
(pixel assertions in scripts/foundation/verify_foundation.py) + S66 canvas_probe.

| Canvas op | Status | Evidence |
|---|---|---|
| drawColor / drawARGB / drawRGB | PROVEN | f08 R1; S66 T2..T9 |
| drawRect (fill) | PROVEN | f08 R1 (255,0,0 exact) |
| drawRect (stroke) | PARTIAL | 4 thin rects, not Skia stroking; FILL_AND_STROKE→STROKE |
| drawCircle (fill) | PROVEN | f08 R2 disc exact |
| drawCircle (stroke) | PARTIAL | outer band model; inner/t discarded (canvas_shadow.cpp:240) |
| drawLine | PROVEN | f08 R3 (Bresenham-lite, no AA/caps) |
| drawPath | PROVEN (S66) | scanline fill, winding+even-odd |
| drawOval / drawArc | PROVEN (S66) | 4-cubic Bézier; start/sweep + useCenter |
| drawRoundRect | PROVEN (radius rasterized S67) | f08 R9: brown center + rounded corner probe; was plain-rect v1 |
| drawText | PARTIAL | ASCII 32..126 bitmap only (A6: non-ASCII → space glyph silently); TextView path uses full FriBidi/HarfBuzz/FreeType |
| drawPosText / drawPoint | NO-OP | warn_noop "accepted_not_reproduced" |
| drawBitmap (Canvas DEX path) | NO-OP | ImageView/bg path exists separately; BitmapFactory.* absent (B3) |
| drawPaint | PROVEN | full-view fill; Shader/ColorFilter ignored |
| translate | PROVEN | f08 R4 purple at translated coords |
| scale / rotate / skew / concat | NO-OP | f08 R5/R7: no pixels at scaled/rotated geometry (B1 — no matrix exists) |
| clipRect | NO-OP | f08 R6: 245 leak px beyond clip box (B2 — no clip stack) |
| save / restore | PARTIAL | translation-only stack |
| saveLayer / restoreToCount | NO-OP | no offscreen layers (B4) |
| Paint.setColor / setAlpha / setStyle / setStrokeWidth | PROVEN | f08 + S66 |
| Paint.setARGB | PROVEN (S67 fix) | f08 R8 (0,0,200) exact; was unhandled→black (A5) |
| Paint.setTextSize (Canvas path) | NO-OP | recorded, never read (B8); TextView path honors textSize |
| Paint.setTextAlign / setTypeface / setAntiAlias / setFakeBoldText / setUnderlineText / setFlags | NO-OP | silently accepted |
| Canvas.getWidth/getHeight | WRONG | hardcoded 1080×1920 (A9) |

Color statics: Color.rgb/argb/parseColor PROVEN (S67 F-122; were REC-MISS→0→invisible).

Framebuffer/capture: RGBA stride=width, blend src-over α→255 (opaque), libpng RGB
(alpha dropped), 1:1 identity capture — raw PPM SHA == PNG pixel SHA (S66 §1/§10).
