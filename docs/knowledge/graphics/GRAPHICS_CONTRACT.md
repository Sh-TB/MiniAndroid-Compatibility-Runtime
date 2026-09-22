# GRAPHICS CONTRACT — S83-GFX-BASE (§5)

Status: CANONICAL. This document is the semantic law for MiniAndroid
graphics. Every graphics implementation change MUST state which contract
section it implements; every fixture MUST reference the section it pins.

Upstream references: AOSP `android.graphics` / `android.view` Javadoc +
`SkCanvas`/`SkPaint`/`SkSurface` semantics (Skia), used as SOURCE LAW per
S83 §27 (adopt semantics, not code).

## C1 Canvas state (android.graphics.Canvas)

```text
matrix       full 2D affine (a,b,c,d,e,f); draw ops map device = M ∘ geometry.
             translate/scale/rotate/skew/concat/setMatrix PRE-concatenate
             (SkCanvas: M' = M ∘ Op). rotate positive = CW in y-down space.
clip         device-space region; every draw intersects with it.
             clipRect nestable; clipPath supported (Region of path).
             clip state is part of save/restore snapshot.
alpha        canvas drawing has no global alpha; alpha enters via Paint
             (paint alpha × paint color alpha), layer alpha (saveLayer),
             and the drawable/view chains above Canvas.
save stack   save() snapshots matrix+clip; restore() pops; restoreToCount(n)
             pops to n; getSaveCount() answers the stack depth.
```

## C2 Paint state (android.graphics.Paint)

```text
color        32-bit ARGB; drawColor = premultiplied source-over of the color.
alpha        0..255 multiplies color alpha (effective = A_paint * A_color / 255).
style        FILL | STROKE | FILL_AND_STROKE (strokes centered on geometry).
strokeWidth  in current-transform units; device width scales by |det|^0.5.
shader       optional pattern source (BitmapShader/LinearGradient/...);
             when present it REPLACES paint color as the source.
colorFilter  optional post-source transform (PorterDuffColorFilter,
             LightingColorFilter, ColorMatrixColorFilter).
xfermode     blend equation (PorterDuff modes); default SRC_OVER.
typeface     family+style used by drawText; does not affect measurement of
             non-text ops. textSize in px (scaled by matrix).
```

Paint is INDEPENDENT of Canvas: the Canvas never mutates Paint state.
Replay/layers must not read "current paint" global state.

## C3 Bitmap (android.graphics.Bitmap)

```text
width/height pixel dimensions
config       ARGB_8888 (real), RGB_565 / ALPHA_8 / A_4444 explicitly
             unsupported with evidence (no silent ARGB_8888 reinterpret).
alpha        hasAlpha flag; decoded PNG/JPEG/WebP alpha preserved.
density      the density the bitmap was decoded for (BitmapFactory.Options
             density scaling contract); 0 = none.
rowBytes     >= width * 4 (stride may exceed the minimum).
pixels       non-premultiplied RGBA8888 internal store (documented).
lifetime     recycle() marks isRecycled(); access after recycle throws.
```

## C4 Drawable

```text
bounds       setBounds(l,t,r,b) — the ONLY geometry a drawable has.
state        int[] state set (pressed/enabled/selected/focused...);
             stateful drawables re-resolve on state change.
level        0..10000 (ProgressBar/ClipDrawable).
alpha        0..255 applied at draw (Drawable.setAlpha) — multiplies
             the drawable's own color alphas.
tint         optional PorterDuffColorFilter over the drawable.
visibility   setVisible(bool, restart) default true; not drawn when false.
draw(Canvas) every subclass MUST honor bounds+state+level+alpha+tint.
```

Per-class laws: ColorDrawable paints bounds; BitmapDrawable scales per
gravity/scaleType/tiling; ShapeDrawable/GradientDrawable per AOSP shape
models; LayerDrawable draws children back-to-front with per-layer insets;
StateListDrawable resolves state→child; NinePatchDrawable stretches the
9 patch regions from the .9.png layout markers; VectorDrawable scales the
viewport path geometry into bounds and fills paths.

## C5 View rendering lifecycle (android.view.View)

```text
invalidate()       → draw pass scheduled (no layout).
requestLayout()    → measure+layout+draw.
measure → layout → draw: parent passes MeasureSpec; layout assigns
                   l/t/r/b; draw = background → content (onDraw) →
                   children (dispatchDraw) → foreground/fading.
ViewGroup          children in insertion order (z), GONE children skipped;
                   clipChildren=true clips child drawing to parent bounds.
view alpha         View.setAlpha(0..1) multiplies the WHOLE view draw
                   (AOSP: per-view alpha via layer or paint alpha).
```

## C6 Surface / frame / present / capture (software model)

MiniAndroid's software surface model (the semantic analog of Skia's raster
surface + Android BufferQueue, single-buffered, deterministic):

```text
RasterSurface  width, height, stride (=width), format RGBA8888,
               alpha type (premul/OFF), owning buffer, clear value,
               current frame id, dirty region.
  getPixels / writePixels / clear / present / snapshot.
frame          begin (surface lock) → draw (Canvas ops land in the buffer)
               → present (buffer becomes the frame output; frame id+1).
composition    the window surface is composed from view surfaces/layers
               back-to-front BEFORE present. Even single-surface, the
               model keeps render-target ≠ screenshot.
capture        screenshot = read-only consumer of the presented buffer.
               Capture MUST NOT change how pixels were produced.
```

GL path (same contract, GL backend): GLSurfaceView owns a Surface;
EGL objects model display/config/context/surface; makeCurrent binds the
PGL software framebuffer; swapBuffers = present (surface pixels become
the frame output); capture reads the presented buffer.

## C7 Provenance chain (every frame, image-bearing or not)

```text
ASSET_FOUND → RESOURCE_RESOLVED → RESOURCE_SELECTED → DECODED →
BITMAP_CREATED → DRAWABLE_CREATED → VIEW_BOUND → MEASURED → LAYOUT →
DRAW_CALLED → CANVAS_MUTATED → SURFACE_WRITTEN → BUFFER_PRESENTED →
COMPOSITED → SCREENSHOT_CAPTURED
(+ GL: EGL_CREATED → CONTEXT_CURRENT → DRAW_SUBMITTED →
        FRAMEBUFFER_UPDATED → SWAP_BUFFERS)
```

FIRST_DIVERGENCE = the first chain bit that is 0 while all earlier bits
are 1 (auto-derived at frame finalize; never hand-claimed).

## C8 Honesty law

Nonblank ≠ rendered; rendered ≠ pixel-correct; launch success ≠ visual
success. Any semantic not implemented is EXPLICITLY UNSUPPORTED with a
registered blocker — never a silent fallback (S83 §42).
