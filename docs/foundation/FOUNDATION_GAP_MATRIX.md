# FOUNDATION_GAP_MATRIX — canonical (S67)
# Order: fan-out-first (snowball law). Statuses: PROVEN PARTIAL IMPLEMENTED TESTED OBSERVED RESEARCHED BLOCKED UNTESTED

## P0 — smallest primitive × most consumers (silent-wrongness)

| ID | Area | Fan-out | Current implementation | Upstream law | Test coverage | Real APK consumers | Known failure | Next generic fix |
|---|---|---|---|---|---|---|---|---|
| A1 | ?attr at inflate | every Material/AppCompat app | mis-queried as resid | LayoutInflater.obtainStyledAttributes ViewStyle law | f-wave queued | OPMT family | styles silently dropped | add theme-attr branch in apply_element_attrs reusing resolve_theme_attr_value |
| A2 | getDimensionPixelSize | every programmatic layout from dimens | FIXED S67: ARSC-first + complexToDimensionPixelSize + args[1] law | TypedValue.complexToDimensionPixelSize | f32 PASS | gmdice/TriPeaks dims | 100dp returned 24px/100px before fix | DONE; monitor fallback loudness |
| A3 | non-PNG drawable silent drop | image-heavy apps | no decode attempt, no placeholder (execution_engine.cpp:2322-2373) | magic-based decoder dispatch | queued | FishRings family | drawable exists, renders nothing | route by magic; loud placeholder + trace on undecodable |
| A4 | INVISIBLE drawn | visibility-dependent UIs | FIXED S67 (A4+F-124): XML enum space mapped + own-content gate | View.draw SKIP_DRAW law | f06 PASS | corpus-wide | XML-invisible views drew black | DONE (child-of-invisible-parent still renders per AOSP) |
| A5 | Paint.setARGB unhandled | custom drawing | FIXED S67: handler → paint_color_ | AOSP Paint.setARGB | f08 R8 PASS | canvas apps | shapes drew black | DONE |
| A6 | Canvas text ASCII-only | custom text views | space glyph for non-ASCII, silent | Canvas.drawText → TextShaper | queued (A6 probe in f08 R10) | canvas-drawing apps | Persian invisible on Canvas path | route Canvas.drawText through fonts::TextShaper |
| A7 | manifest label/icon | every APK | label REFERENCE → "@0x…"; icon unparsed | PackageParser label/icon resolve | queued | corpus-wide | launcher identity wrong | resolve through ARSC |
| A9 | Canvas.getWidth hardcoded | coordinate math | hardcoded 1080×1920 | Canvas.getWidth returns surface w | queued | custom views | wrong aspect math | bind to framebuffer dims |
| A10 | Theme.* / Resources.getSystem | themed apps | stub black / missing | ResourcesImpl + ThemeImpl | queued | themed apps | Theme.getColor always black | implement resolveAttribute over theme bag |
| F-121 | input→pending-work→render | all navigation | FIXED S67: probe drains pending intent/finish before re-render | AOSP Looper message→traversal law | f27 PASS | TriPeaks/FishRings nav | nav clicks recorded changed_px=0 | DONE |
| F-122 | Color.rgb/argb/parseColor | every custom-drawing app | FIXED S67: static factory law | AOSP Color.java | f08 R2-stroke PASS | canvas apps | colors returned 0 → invisible | DONE |
| F-123 | drawRoundRect arg order | cards/rounded UIs | FIXED S67: (l,t,r,b,rx,ry,PAINT) + real radius raster | AOSP Canvas.drawRoundRect | f08 R9 PASS | Compose cards | paint read from rx slot → black squares | DONE |
| F-124 | visibility XML enum space | every XML app | FIXED S67: {0,1,2}→{0,4,8} mapping | ViewProps VIEW_VISIBILITY_VALUES | f06 PASS | corpus-wide | invisible→1 → drawn | DONE |

## P1 — missing foundation (degrade loudly or registered)

| ID | Area | Fan-out | Status | Next generic fix |
|---|---|---|---|---|
| B1 | canvas matrix (scale/rotate/skew/concat) | games/animation | NO-OP pixel-proven (f08) | real matrix stack at replay; full evidence first (architecture risk) |
| B2 | clipRect enforcement | clipping everywhere | NO-OP pixel-proven (f08 R6: 245 leak px) | clip stack intersect in SoftwareCanvas |
| B3 | BitmapFactory + Canvas.drawBitmap | image-drawing apps | missing | BitmapFactory.decode* over existing PNG/WebP/JPEG decoders |
| B4 | saveLayer/restoreToCount | alpha compositing | NO-OP | offscreen layer compositor |
| B5 | setX/setTranslationX/AbsoluteLayout | drag/animation | missing | node translation field + renderer offset |
| B6 | ScrollView scrolling | scrolling apps | missing (no scrollY) | scroll offset + draw translation + clip |
| B7 | circle stroke model | UI polish | PARTIAL (inner/t discarded) | ring raster like roundRect |
| B8 | Paint.setTextSize (Canvas) | custom text | recorded-never-read | consume at replay via TextShaper |
| B9/B10 | italic synthesis; fallback faces | styled/non-Latin text | missing | synthetic oblique + per-codepoint fallback chain |
| B12 | @android: framework ids | published apps | unresolvable | static id table for common framework resources |
| C1/C2 | RL programmatic + render-without-measure | TriPeaks class | PARTIAL (R-NEW-388 residual) | measure-before-render law at render entry |
| C5/C6 | dirty tracking | whole engine | whole-tree re-measure; invalidate no-op | dirty-region model (perf, not correctness yet) |
| C9 | ViewTree export fields | evidence | lacks alpha/padding | add fields (evidence integrity) |
| D1-D7 | dead code/build drift | hygiene | registered | remove view_renderer/real_layout/api_dispatcher stub; fix CMake libs |

## Counts (honest, this session)

- base contracts inspected: 61 (render 24, layout 26, resource 24, runtime 17 — see matrices)
- generic fixes shipped: 7 (F-121, F-122, F-123, F-124, A2 two-layer, A4 gate, C3)
- micro-fixtures built+run: 19; verifier verdicts: 17/17 PASS (post-fix), determinism 6/6 ×3
- real APK cross-validations: 4 byte-match vs S66 records (TicTacToe, FishRings, OPMT, TriPeaks-lobby) + miniandroid_test 4/4
- remaining P0 registered but NOT implemented this session: A1, A3, A6, A7, A9, A10 (each has law + plan, no code — honest)
- remaining P1/P2: see above (B/C/D families)
