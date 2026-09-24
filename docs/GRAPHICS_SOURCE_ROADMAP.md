# GRAPHICS SOURCE ROADMAP — S94

> Priorities: P0 = directly blocking current MiniAndroid graphics; P1 = high
> fan-out future graphics; P2 = important compatibility; P3 = specialized;
> P4 = research/reference. Fan-out numbers are measured corpus counts
> (148-title canonical registry; S91 demand map; S93 metrics), never guesses.

## P0 — directly blocking current graphics

> **S95 UPDATE (2026-09-24)** — the P0 wave EXECUTED against real APKs; the
> canonical result table is `docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md` §3.
> Status deltas: Density/vector WRONG_COLOR — hotdeath FAIL→PASS, bouncy +
> urlchecker WRONG_COLOR eliminated (L-S95-VECTOR-1/ADAPTIVE-1);
> WRONG_CLIP — root cause was MEASURE (Button 48dip law, L-S95-BTNMIN-1),
> bobball 4×→0, dodge partial; ANIMATION_FROZEN — REFUTED as a harness tap
> miss (both games animate, 3 deterministic runs); UNREADABLE_TEXT — theme
> layers fixed (L-S95-DEFTHEME-1/TXTCLR-1/ICONBTN-1), simplestopwatch
> remaining flags reduce to ONE named gap: app-level programmatic UI
> (custom-view onDraw + setTextColor scheme application) — promoted to P1.
> New P1 entries: (1) programmatic UI color-scheme execution
> (simplestopwatch, [C013-ONDRAW] dispatched=NO evidence); (2) LinearLayout
> weight-distribution measure bug (dodge menu panel ~1645px children).

| Gap | Source(s) | Algorithm/contract | Implementation availability | Test availability | MiniAndroid status | Measured fan-out |
|---|---|---|---|---|---|---|
| Density selection at decode (WRONG_COLOR wave) | aosp-mirror/platform_frameworks_base `BitmapFactory.java`; bumptech/glide `Downsampler.java` | inDensity × inTargetDensity pairs; power-of-2 inSampleSize | upstream proven; port = decoder options + resolver wiring | glide test suite; build density fixture table | **PARTIAL (S95)** — density law wired into decode_image_bytes; vector/adaptive gap closed; s95_vector battery stage green | WRONG_COLOR eliminated on 3/4 mapped titles (hotdeath PASS; bouncy, urlchecker color-fail 3×→0); simplestopwatch moved to placeholder/scheme taxonomy |
| GIF disposal semantics (12 GIF titles) | google/wuffs `wuffs_gif__decoder`; python-pillow/Pillow `_seek`; golang/go `image/gif/reader.go`; FFmpeg `gifdec.c` | disposal 0–3 restore semantics per frame | wuffs = drop-in candidate; port = compositor rework | wuffs test corpus 437 files; Pillow test_file_gif.py; golang reader_test.go | OPEN — compositor minimal | 12 GIF VERIFIED-INTERACTIVE titles + all animated-drawable APKs |
| Canvas clip stack correctness (WRONG_CLIP wave) | aosp-mirror/platform_frameworks_base `Canvas.java`; google/skia `SkCanvas.cpp`; houstudio/cdroid view/canvas | clip stack intersect semantics; quickReject | AOSP/Skia behavior spec; CDroid = C++ reference | Skia ClipStackTest; CDroid cts tests | **OBSERVED (S95)** — S93 clip flags on bobball/dodge/bouncy traced to MEASURE gaps (Button minHeight), not clip semantics; clip-stack obedience remains covered by battery law tests | bobball 4×→0, dodge partial (1 of 2 causes fixed), urlchecker residual 1 node |
| UNREADABLE_TEXT law | harfbuzz/harfbuzz (`hb_ot_shape_internal`); google/minikin `Layout.cpp`; freetype/freetype `ftobjs.c`; tesseract-ocr/tesseract | shaping→glyph IDs→positions→raster; .notdef = tofu; OCR cross-check | R4 POC proven (FriBidi+HarfBuzz+FreeType) not wired | harfbuzz in-house 3058 test files; tesseract Recognize | **PARTIAL (S95)** — theme default-color laws fixed (dark default theme, textColorPrimary, ImageBtn fill); remaining = programmatic scheme execution (P1) | simplestopwatch residual flags single-root-caused; urlchecker 3 floor-artifact flags documented (visual evidence readable) |
| AnimationDrawable timing (ANIMATION_FROZEN) | aosp-mirror/platform_frameworks_base `AnimationDrawable.java`; libgdx/libgdx `AndroidGraphics.java` | scheduleSelf per-frame durations; onDrawFrame submission | behavior spec + C++ port | CDroid cts_animationdrawable_test.cc; lottie-android tests | **REFUTED (S95)** — frozen evidence was a harness tap miss; engine postDelayed/invalidation/frame machinery proven correct (6/2 unique frames ×3 runs) | 0 real engine cases remain from the S93 map |

## P1 — high fan-out future graphics

| Gap | Source(s) | Contract | Tests available | Status | Measured fan-out |
|---|---|---|---|---|---|
| Layout wiring (Yoga R3) | facebook/yoga `YGNode.cpp` | CalculateLayout outputs = placed bounds | gentest 43 fixture sets + 73 test files | adapter ready; render-stage wiring pending | every LinearLayout/FrameLayout-relative title in corpus (measure/layout stage) |
| Visual diff AA-awareness | mapbox/pixelmatch `index.js` | threshold, antialias, maxDelta | 28 test files | S92/S93 pixel probe upgrade | reduces WRONG_COLOR/WRONG_CLIP false positives across all screenshot comparisons |
| Region-exclusion golden gates | ndtp/android-testify `ScreenshotRule.kt` | baseline + exclude regions | testify samples | verifier region partition exists (S93 §21) | all region-partitioned titles |
| WebView visual readiness | chromium `AwContents.java`; WebKit `ImageLoader.cpp`; electron `ready-to-show`; wpt | readiness callbacks; DOM≠pixels | WPT corpus; LayoutTests | OPEN — readiness model to build | WebView titles: 83 in S91 demand map |
| Screenshot production determinism | cashapp/paparazzi; takahirom/roborazzi | record/verify separation | both test suites | repeatability gate exists (S93 3-run) | all 148 canonical titles |
| NinePatch engine support | aosp `NinePatchDrawable.java`; houstudio/cdroid `ninepatch*.cc` | patch stretch + padding→layout | CDroid cts_ninepatchdrawable_test.cc | OPEN | buttons/backgrounds across corpus |

## P2 — important compatibility

| Gap | Source(s) | Note | Fan-out |
|---|---|---|---|
| Bidi conformance | unicode-org/icu `ubidi.cpp`; fribidi/fribidi | RTL titles; Persian corpus work (S90) | RTL/locale-split titles |
| ConstraintLayout solver parity | androidx/constraintlayout `ConstraintLayout.java` | measure/layout consistency law | titles using constraint widgets |
| Ripple/state drawables | material-components `RippleUtils.java`; CDroid `rippledrawable.cc` | press feedback laws | material UI titles |
| ARSC/AXML diff oracles | reandroid/ARSCLib; androguard; Apktool; jadx | R6 policy already recorded | all resource-heavy APKs |
| JPEG2000/AVIF/HEIF decode | uclouvain/openjpeg; AOMediaCodec/libavif; strukturag/libheif | modern-format APKs | rare-format corpus tail |
| SurfaceFlinger presentation model | LineageOS/android_frameworks_native `SurfaceFlinger.cpp` | commit/composite framing for verifier | frame-submission evidence |

## P3 — specialized

| Area | Source(s) |
|---|---|
| PBR/3D engines | google/filament; godotengine/godot |
| Multi-backend gfx abstraction | floooh/sokol; bkaradzic/bgfx |
| Kotlin game engines | korlibs/korge; hajimehoshi/ebiten |
| Map rendering/glyph atlas | maplibre/maplibre-gl-native |
| Immediate-mode UI + atlas | ocornut/imgui |
| Engine forks/demos | axmolengine/axmol; defold/defold; urho3d/urho3d; godotengine/godot-demo-projects |
| Frame/GPU inspection tools | google/agi; baldurk/renderdoc; apitrace; Genymobile/scrcpy |
| Cross-platform UI (Skia) | avaloniaui/avalonia; JetBrains/skiko |

## P4 — research/reference

cairo (compositing model, off-GitHub), mesa3d/mesa (CPU rasterizers, off-GitHub), servo/webrender (batched GPU raster), servo/servo (compositor), mozilla/gecko-dev (mirror reference), ImageMagick/libvips/OpenImageIO (toolkits), ImageMagick annotate.c (text rendering), libass (subtitle text pipeline), graphite (complex script shaping), fontforge (font tooling), canvg (canvas semantics), KhronosGroup/Vulkan-Samples, google/gfxstream (virtualized gfx), googleprojectzero/SkCodecFuzzer (fuzz harness port).

## Sequencing rationale

1. **P0 density + GIF + clip + text + animation** cover every S93 failure category with a measured count of 8 traced titles; each has upstream tests ready to port (§23 requirement).
2. **P1 items** are the highest measured fan-out (83 WebView titles, 148 screenshot comparisons, all layout-bearing titles).
3. P2/P3/P4 are ordered by corpus demand evidence from the S91 400-method/200-class demand map.
