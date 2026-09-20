# FOUNDATION_GAP_MATRIX — canonical (S69; S68 base, W1/W2 kills + F-135 recorded)
# Order: fan-out-first (snowball law). Statuses: PROVEN PARTIAL IMPLEMENTED TESTED OBSERVED RESEARCHED BLOCKED UNTESTED

## P0 — smallest primitive × most consumers (silent-wrongness)

| ID | Area | Fan-out | Current implementation | Upstream law | Test coverage | Real APK consumers | Known failure | Next generic fix |
|---|---|---|---|---|---|---|---|---|
| A1 | ?attr at inflate | every Material/AppCompat app | FIXED S68 W2 (F-131..F-134): theme service (activity>application theme), inflate pre-pass resolves TYPE_ATTRIBUTE once, style-item ?attr hook, typed-INT background branch | TypedValue TYPE_ATTRIBUTE + ContextThemeWrapper.obtainStyledAttributes | f51 3/3 EXACT (app attr / framework accent LIGHT flavor / textColorPrimary state-list) | OPMT family, all Material apps | styles silently dropped | DONE |
| A2 | getDimensionPixelSize | every programmatic layout from dimens | FIXED S67: ARSC-first + complexToDimensionPixelSize + args[1] law | TypedValue.complexToDimensionPixelSize | f32 PASS | gmdice/TriPeaks dims | 100dp returned 24px/100px before fix | DONE; monitor fallback loudness |
| A3 | non-PNG drawable silent drop | image-heavy apps | FIXED S68 W1 (F-129): renderer::decode_image_bytes ONE magic-detecting decoder (PNG/JPEG/WebP; GIF/XML EXPLICIT-UNSUPPORTED named); 3 duplicated switch blocks deduped | BitmapFactory magic-based decoder dispatch | f50 5/5 (JPEG/WebP/palette/gray exact; GIF = 0xCC named placeholder) | image-heavy apps | drawable exists, renders nothing | DONE |
| A4 | INVISIBLE drawn | visibility-dependent UIs | FIXED S67 (A4+F-124): XML enum space mapped + own-content gate | View.draw SKIP_DRAW law | f06 PASS | corpus-wide | XML-invisible views drew black | DONE (child-of-invisible-parent still renders per AOSP) |
| A5 | Paint.setARGB unhandled | custom drawing | FIXED S67: handler → paint_color_ | AOSP Paint.setARGB | f08 R8 PASS | canvas apps | shapes drew black | DONE |
| A6 | Canvas text ASCII-only | custom text views | FIXED S68 W1 (F-130): paint textSize set → TextShaper (FreeType/HarfBuzz/FriBidi — same engine as TextView; §14 one-shaping-engine law); no size → legacy byte-identical path | Canvas.drawText → TextShaper | f49 3/3 (Persian joined 1858 px + spaced + ASCII regression) | canvas-drawing apps | Persian invisible on Canvas path (0 px → 1858 px) | DONE |
| A7 | manifest label/icon | every APK | label REFERENCE → "@0x…"; icon unparsed | PackageParser label/icon resolve | queued | corpus-wide | launcher identity wrong | resolve through ARSC |
| A9 | Canvas.getWidth hardcoded | coordinate math | FIXED S68 W1 (F-127): canvas_w_/h_ plumbed from the real framebuffer at replay | Canvas.getWidth returns surface w | f48/f08 byte-stable | custom views | wrong aspect math | DONE |
| A10 | Theme.* / Resources.getSystem | themed apps | FIXED S68 W2 (F-131/F-132): bag_value over activity theme + 22-attr framework defaults table (AOSP-generated) + flavor law | ResourcesImpl + ThemeImpl | f51 2/3 rows EXACT framework values | themed apps | Theme.getColor always black | DONE (5 attrs DEFERRED-BY-CONTRACT, recorded) |
| F-121 | input→pending-work→render | all navigation | FIXED S67: probe drains pending intent/finish before re-render | AOSP Looper message→traversal law | f27 PASS | TriPeaks/FishRings nav | nav clicks recorded changed_px=0 | DONE |
| F-122 | Color.rgb/argb/parseColor | every custom-drawing app | FIXED S67: static factory law | AOSP Color.java | f08 R2-stroke PASS | canvas apps | colors returned 0 → invisible | DONE |
| F-123 | drawRoundRect arg order | cards/rounded UIs | FIXED S67: (l,t,r,b,rx,ry,PAINT) + real radius raster | AOSP Canvas.drawRoundRect | f08 R9 PASS | Compose cards | paint read from rx slot → black squares | DONE |
| F-124 | visibility XML enum space | every XML app | FIXED S67: {0,1,2}→{0,4,8} mapping | ViewProps VIEW_VISIBILITY_VALUES | f06 PASS | corpus-wide | invisible→1 → drawn | DONE |
| F-135 | Double/Float isNaN·isInfinite·compare | 694 static sites × 7 APKs (bouncy 141, dooz 217, fishrings 24, tictactoe 28…) | FIXED S69: NaN=(v!=v), isInfinite=abs>MAX, compare=canonical-bits ordering (NaN>+Inf, −0.0<+0.0) | OpenJDK Double.java:1031/1048/1538, Float.java:631 (fetched, SHA'd) | f52_nanlaw 9/9 rows EXACT | bouncy NaN flips 480× STUB→IMPL, frames byte-stable; fishrings/tripeaks chains byte-identical | NaN guards took the wrong side silently | DONE |

## P1 — missing foundation (degrade loudly or registered)

| ID | Area | Fan-out | Status | Next generic fix |
|---|---|---|---|---|
| B1 | canvas matrix (scale/rotate/skew/concat) | games/animation | FIXED S68 W1 (F-125): full 2D Affine2D, pre-concat law, save/restore snapshots matrix+clip; rotate/skew → polygon via winding rasterizer; stroke × sqrt|det|; f08 metamorphic asserts (scale doubled coords, rotate moved) | SkCanvas matrix law | f08 R5/R7 updated asserts PASS | games/animation | DONE |
| B2 | clipRect enforcement | clipping everywhere | FIXED S68 W1 (F-126): per-op clip SNAPSHOT (root cause: clip read at replay time was post-restore) + intersect law + view-bounds clip in SoftwareCanvas | Canvas clip stack law | f08 R6 asserts (inside teal / outside WHITE) PASS | clipping everywhere | DONE (245 leak px → 0) |
| B3 | BitmapFactory + Canvas.drawBitmap | image-drawing apps | FIXED S68 W1 (F-127/F-128): BitmapShadow (21st shadow) + BitmapStore; decodeResource/ByteArray/File, createBitmap family, eraseColor/getPixels; drawBitmap (l,t)/(src,dst)/(int[]) + affine per-pixel for rotated dst; nearest per FilterBitmap=false | BitmapFactory + Canvas.drawBitmap src/dst law | f48 5/5 EXACT | image-drawing apps | DONE |
| B4 | saveLayer/restoreToCount | alpha compositing | PARTIAL S68: state snapshot honored (save/restore/restoreToCount/getSaveCount work); layer ISOLATION DEFERRED-BY-CONTRACT (warned honestly) | SkCanvas saveLayer | f08 byte-stable | alpha compositing | offscreen layer compositor when a consumer demands it |
| B5 | setX/setTranslationX/AbsoluteLayout | drag/animation | missing | node translation field + renderer offset |
| B6 | ScrollView scrolling | scrolling apps | missing (no scrollY) | scroll offset + draw translation + clip |
| B7 | circle stroke model | UI polish | PARTIAL (inner/t discarded) | ring raster like roundRect |
| B8 | Paint.setTextSize (Canvas) | custom text | FIXED S68 W1 (F-130): consumed at replay via TextShaper when set | Paint text contract | f49 PASS | custom text | DONE |
| B9/B10 | italic synthesis; fallback faces | styled/non-Latin text | missing | synthetic oblique + per-codepoint fallback chain |
| B12 | @android: framework ids | published apps | unresolvable | static id table for common framework resources |
| C1/C2 | RL programmatic + render-without-measure | TriPeaks class | PARTIAL (R-NEW-388 residual) | measure-before-render law at render entry |
| C5/C6 | dirty tracking | whole engine | whole-tree re-measure; invalidate no-op | dirty-region model (perf, not correctness yet) |
| C9 | ViewTree export fields | evidence | lacks alpha/padding | add fields (evidence integrity) |
| D1-D7 | dead code/build drift | hygiene | registered | remove view_renderer/real_layout/api_dispatcher stub; fix CMake libs |

## Counts (honest, cumulative through S68 W1+W2)

- base contracts inspected: 61 (S67) + 14 new S68 contract families (canvas state/transform/clip/bitmap/text, Bitmap store, theme service, image formats) = 75
- generic fixes shipped: S67 7 + S68 10 (F-125 matrix, F-126 clip, F-127 drawBitmap/dims, F-128 BitmapShadow, F-129 decode dedup, F-130 Canvas text, F-131 theme service, F-132 framework defaults, F-133 inflate pre-pass, F-134 activity theme)
- micro-fixtures: 19 (S67) + 4 (S68: f48/f49/f50/f51) = 23; verifier verdicts: 21/21 PASS; determinism ×3 byte-identical for every new fixture
- real APK cross-validations: canonical corpus 9/9 byte-stable vs BEFORE-state (fishrings/gmdice/stopwatch/microtimer/unote/bouncy/dooz23 + OPMT + TriPeaks), battery 92/94 (EXT-01/02 environmental only)
- remaining P0 registered but NOT implemented: A7 (manifest label/icon) — law known, no code; R-NEW-388 (TriPeaks RL geometry wiring) — registered, next wave
- remaining P1/P2: see above (B4 layer isolation, B5/B6, B7, B9/B10, B12, C/D families)
