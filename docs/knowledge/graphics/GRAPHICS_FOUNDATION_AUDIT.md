# GRAPHICS FOUNDATION AUDIT — S83-GFX-BASE (§4)

Status: CANONICAL audit of the MiniAndroid graphics surface at HEAD
`4df34d30` (+S83 work). Every class named in the S83 §4 list is classified:

```text
IMPLEMENTED      — semantics reproduced, pixel-tested
PARTIAL          — core semantics real, named gaps listed
STUB             — object exists, methods accepted-not-reproduced
NO-OP            — call accepted, zero pixel effect
WRONG_SEMANTICS  — produces pixels but violates the AOSP law
MISSING          — no handling at all (generic path)
```

Evidence basis: source read of the listed TUs + S82 ladder pixel evidence +
battery/verifier gates. Audit is frozen as
`docs/audit/GRAPHICS_FOUNDATION_AUDIT.json` (machine copy, same statuses).

## 1. Per-class classification

| # | Class / layer | TU | Status | Named gaps |
|---|---------------|----|--------|------------|
| 1 | Bitmap | framework/bitmap_shadow.cpp (+BitmapStore) | PARTIAL | single real config (ARGB_8888); no per-bitmap density; no copy(); createScaledBitmap nearest-only (bilinear honestly registered) |
| 2 | BitmapFactory | framework/bitmap_shadow.cpp | IMPLEMENTED | decode{File,Stream,ByteArray,Resource,ResourceStream} via one magic-based entry; GIF explicit unsupported (no silent drop) |
| 3 | Drawable (base) | — | MISSING | no Drawable base shadow; per-drawable behavior lives ad hoc in engine/inflater (see 3a–3h) |
| 3a | ColorDrawable | execution_engine + canvas/engine capture | PARTIAL | object color map + XML solid; no alpha-composited setColorFilter/tint path |
| 3b | BitmapDrawable | engine render (fit-draw) | PARTIAL | gravity/tile modes not modeled (FIT_CENTER only) |
| 3c | ShapeDrawable/GradientDrawable | layout_inflater apply_shape_background | PARTIAL | rect/oval solid+gradient+corners+stroke real; ring/line + dash DETECTED-NOT-RENDERED |
| 3d | LayerDrawable | layout_inflater layer-list | PARTIAL | XML layer-list stacks (l4 PASS); code-instantiated LayerDrawable missing |
| 3e | StateListDrawable | framework/state_list.cpp + BgStateItem | IMPLEMENTED | pressed/enabled/selected + wildcard pick; render-side ARSC select (l4 PASS) |
| 3f | NinePatchDrawable | — | MISSING | .9.png decodes as plain PNG (stretch markers painted = WRONG when consumed) |
| 3g | VectorDrawable | — | MISSING | vector XML not inflated; vector icon family invisible (fanout suspected) |
| 3h | InsetDrawable/ClipDrawable/RotateDrawable | — | MISSING | (discovered during audit; common in real UIs) |
| 4 | View / ViewGroup | framework/android_shadows.cpp ViewShadow + renderer/view_renderer.cpp | PARTIAL | measure/layout (linear/relative/frame/scroll), bg/image/text, visibility, padding real; child z-order = insertion order; view-alpha/scaleType not modeled; clipChildren honored only implicitly |
| 5 | View lifecycle | engine (R-NEW-302 law) | PARTIAL | requestLayout/invalidate set layout_dirty; draw order = single re-render pass; onDraw dispatch via CanvasShadow only for custom views |
| 6 | ImageView | engine + view_renderer | PARTIAL | resid→select_file→decode→FIT_CENTER (shared law fn); CENTER/CENTER_CROP/CENTER_INSIDE/FIT_XY/FIT_START/FIT_END/MATRIX unimplemented; setColorFilter/tint no-op |
| 7 | TextView | engine + fonts/text_shaper | IMPLEMENTED | HarfBuzz+FreeType shaping, colors, size, bold/italic, gravity; bitmap-font fallback |
| 8 | Canvas | framework/canvas_shadow.cpp (record-replay) | PARTIAL | see §2 Canvas detail |
| 9 | BaseCanvas / RecordingCanvas | canvas_shadow (RenderNode model) | PARTIAL | Compose RenderNode record+replay real; saveLayer isolation absent |
| 10 | Paint | canvas_shadow (PaintShadow) | PARTIAL | color/alpha/style/strokeWidth/textSize/fakeBold/filterBitmap real; Shader/ColorFilter/Xfermode/typeface-align MISSING |
| 11 | Matrix (android.graphics.Matrix) | — | MISSING | no shadow; canvas affine is internal (Affine2D); drawBitmap(bitmap,Matrix,paint) unhandled |
| 12 | Path | canvas_shadow | IMPLEMENTED | moveTo/lineTo/quadTo/cubicTo/close/addRect/Oval/Circle/RoundRect + FillType (flattened; WINDING/EVEN_ODD) |
| 13 | Region | — | MISSING | clip is float-rect only |
| 14 | Color | dalvik_engine constants + engine maps | IMPLEMENTED | parseColor/constants |
| 15 | ColorStateList | framework/state_list.cpp | PARTIAL | text color state objects real; general CSR-from-XML inflation limited |
| 16 | ColorFilter / Shader / Xfermode | — | MISSING | PorterDuff enum ordinals exist for switch dispatch; no pixel effect |
| 17 | Typeface | fonts/text_shaper (FreeType) | PARTIAL | real shaping; Typeface.create/Style objects accepted, family selection limited |
| 18 | Surface | — | MISSING | no buffer contract object |
| 19 | SurfaceView / SurfaceHolder | dalvik_engine (mapped to View) | STUB | hierarchy placement only; no surface lifecycle |
| 20 | TextureView | dalvik_engine (mapped to View) | STUB | same |
| 21 | GLSurfaceView | — | MISSING→WRONG_SEMANTICS | plain-View fallback unwinds libGDX createGLSurfaceView (F-NEW-157); l6 white |
| 22 | EGL | — | MISSING | no egl* surface chain |
| 23 | GLES20 | gles/gles20_bridge.cpp + PortableGL | PARTIAL | real GL dispatch into PGL software framebuffer (C-function shaders; GLSL not parsed — documented frontier) |
| 24 | Framebuffer | renderer/software_renderer.cpp FrameBuffer | PARTIAL | flat RGBA8888 array + blend; alpha channel NOT preserved (blend out = opaque) → blocks translucent surface semantics |
| 25 | Renderer (pipeline) | renderer/view_renderer + engine inline stage_render_frame | PARTIAL | two render consumers (engine mega-render + ViewRenderer); shared law fns prevent drift; composition inline |
| 26 | Screenshot | PNGWriter ← FrameBuffer | IMPLEMENTED | consumer-only: reads pixels, never mutates semantics |
| 27 | Text runtime | renderer/bitmap_font_data.h + fonts/text_shaper | IMPLEMENTED | ASCII bitmap font + HarfBuzz shaping path |

## 2. Canvas detail (the most load-bearing PARTIAL)

Real (pixel-tested): drawColor/ARGB/RGB, drawRect, drawRoundRect (RRect law),
drawCircle, drawOval, drawArc, drawLine, drawPath (contours + fill rules),
drawText (size/bold/affine), drawBitmap (src/dst crop-scale, nearest,
filterBitmap flag), drawPaint, full affine matrix (translate/scale/rotate/skew/
concat/setMatrix + pre-concat law), save/restore (matrix+clip snapshots),
per-op clip snapshot at record time, clipRect.

Gaps (S83 targets):
- `drawPoints / drawLines / drawPosText` — accepted then NO-OP (warn_noop)
- `clipPath` — deferred NO-OP
- `saveLayer/saveLayerAlpha` — state honored, NO layer isolation (alpha/clip
  inside a layer leaks to the base surface = WRONG_SEMANTICS vs AOSP)
- `drawBitmap(bitmap, Matrix, paint)` — overload unresolved (Matrix MISSING)
- Paint alpha × view alpha × drawable alpha composited only partially

## 3. Architecture facts (record before touching)

1. Draw path: app DEX bytecode → CanvasShadow records DrawOps (per onDraw)
   → `replay()` rasterizes into the view's FrameBuffer region. UI widgets
   (non-custom views) are painted by the engine's inline frame stage, NOT via
   CanvasShadow — two consumers, shared law functions.
2. The framebuffer is a single flat RGBA array per frame; screenshots are
   written from it (renderer-produces / screenshot-reads — §23 OK).
3. There is NO RasterSurface object with stride/format/dirty/present
   semantics; FrameBuffer is a bare pixel vector (§7 target).
4. GL is a parallel island (PGL backend) with no Android-side surface
   lifecycle: GLSurfaceView construction path unwinds real apps (F-NEW-157).
5. Provenance instrument (gfx_provenance.h) covers image chain bits
   ASSET_FOUND→DRAW_CALLED + frame census; VIEW_BOUND/MEASURED/LAYOUT/
   SURFACE_WRITTEN/COMPOSITED bits and FIRST_DIVERGENCE auto-derivation are
   S83 §33/§34 targets.

## 4. S83 priority derived from this audit

```text
P0  RasterSurface + framebuffer alpha law + composition separation
P0  Canvas: drawPoints/drawLines, clipPath, saveLayer isolation, bitmap-matrix
P0  Bitmap: density + copy() + config honesty
P1  Drawable: VectorDrawable, NinePatchDrawable, code-LevelDrawable, ImageView scale types
P1  View alpha + ColorStateList generalization
P2  Paint shader/colorfilter/xfermode (pixel-tested minimal set)
P3  Surface/GLSurfaceView/EGL software lifecycle (F-NEW-157 frontier)
P4  libGDX/SDL family unlock (depends on P3)
```

Every implementation step must land with: SOURCE law → fixture → pixel
golden → regression (battery 26/26 + verifier 26/26 + ladder) — per the
S83 §38 no-speculative-patch rule.

## 5. Wave-1 outcome (S83-GFX-BASE, same day)

Machine-canonical statuses now live in `docs/audit/GRAPHICS_FOUNDATION_AUDIT.json`
(updated in place with evidence fields). Delta vs the table above:

| Class | Was | Now | Evidence |
|-------|-----|-----|----------|
| Canvas | PARTIAL | IMPLEMENTED | drawPoints/Lines/PosText rasterized; clipPath scanline spans; saveLayer real offscreen isolation; drawBitmap(Matrix,paint) — l5b_canvas2 pixel pins |
| Matrix | MISSING | IMPLEMENTED | matrix_shadow.cpp real heap-object law; l5b matrix_rotate_gray |
| VectorDrawable | MISSING | IMPLEMENTED | vector_inflater.cpp; l4c_vector (viewport/even-odd/arc pins) |
| NinePatchDrawable | MISSING | IMPLEMENTED | marker-driven stretch (1:1 static zones, expanding patch) — l4d_ninepatch positional pins |
| GLSurfaceView | WRONG_SEMANTICS | PARTIAL | gl_surface_shadow.cpp renderer lifecycle + GL10/GLES11→PortableGL; l6_glsurface PASS (app bytecode glClearColor/glClear pixel-exact). libGDX AndroidGraphics chain still open (F-NEW-157 ADVANCED) |
| EGL | MISSING | PARTIAL | EGL object model + state-honest statics + swapBuffers present law |
| LocaleList/Locale | MISSING | IMPLEMENTED | locale_insets_shadow.cpp — F-NEW-159 ROOT-CAUSED-FIXED; fanout 35/35 signature-eliminated |
| WindowInsetsController | MISSING | IMPLEMENTED | AOSP appearance bit law (cur&~mask)|(values&mask) |
| Provenance | chain bits | + FIRST_DIVERGENCE auto-derivation | §34: derived in finalize() from recorded bits only (C7), never hand-claimed |

Regression after the wave: ladder 10/10 (3 new fixtures), battery 26/26 rc=0,
pixel goldens 24/24, fanout F-NEW-159 35/35 advanced (no status inflation —
all remain onCreate-boundary with named per-title next roots).

Still-open foundation gaps (next waves): RasterSurface stride/format/dirty/present
object (C6) + framebuffer alpha preservation; Bitmap density/copy/config honesty;
code-level LayerDrawable + Inset/Clip/Rotate drawables; ImageView scale types;
view alpha; Paint Shader/ColorFilter/Xfermode; Region; SurfaceView/TextureView
real surface lifecycle; GLSL parsing frontier.
