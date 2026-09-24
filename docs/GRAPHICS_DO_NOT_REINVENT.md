# GRAPHICS DO NOT REINVENT — S94 permanent table

> Companion to `docs/development/DO_NOT_REINVENT.md` (general) and
> `docs/GRAPHICS_SOURCE_REGISTRY.md` (full identity + evidence).
> Rule: before writing >~50 LOC for a graphics subsystem, STOP and search this
> table + the registry. If a strong upstream implementation exists, adapt/port
> it; only implement in-house when a documented technical incompatibility exists.

## The table

| Problem | Do NOT reinvent | Primary source (verified) | Secondary sources | Reuse class | MiniAndroid status |
|---|---|---|---|---|---|
| 2D rasterization (clip stack, layers, AA) | Skia internals | google/skia (`src/core/SkCanvas.cpp`, clip MCRec stack) | cairo (off-GitHub), houstudio/cdroid view/canvas | REFERENCE_ONLY | engine must obey clip law; verifier measures it (L-S93-IMG-5) |
| PNG decode | PNG decoders | pnggroup/libpng (`pngrutil.c`, `png_handle_tRNS`) | google/wuffs, python-pillow/Pillow | DIRECT_REUSE | **CLOSED** — libpng wired since UNIFIED_011.1 |
| JPEG decode | JPEG decoders | libjpeg-turbo/libjpeg-turbo (`jdmarker.c`) | mozilla/mozjpeg | DIRECT_REUSE | **CLOSED** — linked |
| WebP decode | WebP decoders | webmproject/libwebp (`src/dec/vp8_dec.c`) | google/wuffs | DIRECT_REUSE | linked; add conformance tests |
| GIF decode + disposal semantics | GIF compositor | google/wuffs (`wuffs_gif__decoder`, disposal), python-pillow/Pillow (`GifImagePlugin._seek`), golang/go (`image/gif/reader.go`) | FFmpeg (`gifdec.c`), libgd | ADAPT / PORT_TEST | OPEN — MiniAndroid GIF compositor minimal; S93 proves 12 GIF titles need exact disposal |
| Density selection at decode | Density algorithms | aosp-mirror/platform_frameworks_base (`BitmapFactory.decodeResourceStream`, inDensity/inTargetDensity), bumptech/glide (`Downsampler`) | facebook/fresco, coil-kt/coil | PORT_ALGORITHM + PORT_TEST | OPEN — Fish Rings C5 DENSITY_MISMATCH measured (S92 §16); WRONG_COLOR wave |
| Text shaping | Shapers | harfbuzz/harfbuzz (`hb_ot_shape_internal`; 3058 test files) | libass, servo | ADAPT | OPEN (R4) — POC proven (FriBidi+HarfBuzz+FreeType), not wired |
| Android text layout + font fallback per codepoint | Fallback logic | google/minikin (`Layout.cpp` via googlesource) | harfbuzz, freetype | PORT_ALGORITHM | OPEN — UNREADABLE_TEXT law needed (simplestopwatch) |
| Glyph rasterization | Rasterizer | freetype/freetype (`ftobjs.c`, `ftgrays.c` coverage AA) | imgui font atlas | ADAPT | OPEN (R4) |
| Bidi | Bidi algorithm | fribidi/fribidi (project-proven), unicode-org/icu (`ubidi.cpp`) | — | DIRECT_REUSE / conformance oracle | POC proven (exp101) |
| Text readability verification | OCR oracle | tesseract-ocr/tesseract (`baseapi.cpp`) | — | ADAPT | OPEN — S93 UNREADABLE_TEXT currently heuristic-only; OCR cross-check planned |
| Android View/drawable semantics in C++ | View/Drawable/NinePatch/Ripple/AnimationDrawable/StaticLayout | houstudio/cdroid (`src/gui/**`, 266 test files) | aosp-mirror/platform_frameworks_base | PORT_ALGORITHM — LICENSE IS LGPL-2.1 (sha-pinned): behavioral reference / dynamic link; static port needs LGPL compliance | NEW — primary C++ semantic reference discovered by S94 |
| NinePatch semantics | Patch stretch/padding | aosp-mirror/platform_frameworks_base (`NinePatchDrawable.java`), houstudio/cdroid (`ninepatch*.cc`, cts tests) | facebook/fresco | PORT_ALGORITHM | OPEN |
| Vector / SVG rasterization | SVG rasterizer | RazrFalcon/resvg (golden-PNG suite) | memononen/nanosvg, Tencent/tgfx | ADAPT | PLANNED (R5) — named in DO_NOT_REINVENT |
| Canvas 2D API semantics | Canvas emulation | memononen/nanovg (`nvgScissor`, `nvgFill`), canvg | skia | REFERENCE_ONLY | reference for Canvas emulation |
| Layout engines | Flexbox solver | facebook/yoga (`CalculateLayout`; gentest 43 fixtures) | google/flexbox-layout, androidx/constraintlayout | ADAPT | PARTIAL (R3) — adapter differential-tested 10/10 <8px; wiring pending |
| Visual diff | Pixel diff with AA detection | mapbox/pixelmatch (`colorDelta`, `antialias`, `maxDelta`) | kornelski/dssim, OpenImageIO/oiio, opencv/opencv | PORT_ALGORITHM | OPEN — reduce WRONG_COLOR false positives |
| Perceptual frame identity | Hashing | JohannesBuchner/imagehash (dHash/pHash/…) | — | PORT_TEST | S93 L-S93-ANI-1 already uses dHash+color-hash; cross-checked |
| Screenshot testing workflow | Record/verify harnesses | takahirom/roborazzi (record/verify), cashapp/paparazzi (layoutlib JVM), ndtp/android-testify (baseline/exclusion), pedrovgs/Shot, facebook/screenshot-tests-for-android | americanexpress/jest-image-snapshot | PORT_TEST | verifier workflow mirrors these; adopt exclusion semantics |
| Surface / frame submission | Surface lifecycle laws | aosp-mirror/platform_frameworks_base (`SurfaceView.updateSurface`), libgdx/libgdx (`AndroidGraphics.onDrawFrame`), libsdl-org/SDL, LineageOS/android_frameworks_native (SurfaceFlinger commit/composite) | floooh/sokol, bkaradzic/bgfx, google/filament | REFERENCE_ONLY | OPEN for GLSurfaceView/libGDX titles |
| Frame loops (game engines) | Fixed-step loops | godotengine/godot (`Main::iteration`), cocos2d-x/axmol (`drawScene`), urho3d, defold, korlibs/korge, hajimehoshi/ebiten | — | REFERENCE_ONLY | timing oracle for ANIMATION_FROZEN discrimination |
| Lottie animation | Vector animation runtime | Samsung/rlottie (integrated), airbnb/lottie-android (`setProgress`→frame) | lottie-web | DIRECT_REUSE | **CLOSED** — rlottie integrated |
| WebView visual readiness | Readiness model | chromium/chromium (`AwContents.onDraw`, `isReadyToDraw`), WebKit/WebKit (`ImageLoader`), electron (`ready-to-show`), web-platform-tests/wpt | servo, gecko-dev | REFERENCE_ONLY | OPEN — DOM-exists ≠ pixels-correct; readiness callbacks first-class |
| Compose rendering pipeline | LayoutNode laws | androidx/androidx (`LayoutNode.kt`, `AndroidComposeView.android.kt`), JetBrains/skiko (`SkiaLayer.needRedraw`) | JetBrains/compose-multiplatform-core | REFERENCE_ONLY | corpus demand 21 Compose titles |
| GLES translation | ES->backend | google/angle | KhronosGroup/WebGL conformance | PORT_TEST | OPEN (R9/R10) — PortableGL first per DO_NOT_REINVENT |
| CPU GL/Vulkan | Software renderer | google/swiftshader, mesa3d/mesa (off-GitHub) | — | REFERENCE_ONLY | reference |
| Compression (assets) | Brotli | google/brotli (`c/dec/decode.c`) | — | DIRECT_REUSE | available |
| AXML/ARSC parsing (oracle) | Resource parsers | reandroid/ARSCLib, androguard/androguard, iBotPeaches/Apktool, skylot/jadx | — | PORT_TEST (diff oracle) | PARTIAL (R6) — keep custom runtime, diff-test against oracles |
| APK frame/gpu inspection | Tooling | google/agi, renderdoc (baldurk/renderdoc), apitrace, Genymobile/scrcpy | — | REFERENCE_ONLY | diagnostics only |
| Map-style glyph atlas | Atlas allocation | maplibre/maplibre-gl-native (`glyph_atlas`) | imgui atlas | REFERENCE_ONLY | future BitmapFont upgrade path |

## S94 additions to the anti-registry (stop re-attempting)

1. Do NOT invent GIF disposal semantics — port from wuffs/Pillow/golang (three independent references agree).
2. Do NOT guess density behavior — BitmapFactory inDensity/inTargetDensity + Downsampler tests define it.
3. Do NOT hand-roll shaping/fallback — HarfBuzz/Minikin define behavior; FreeType defines .notdef (tofu) semantics.
4. Do NOT invent visual-diff thresholds — pixelmatch threshold/antialias/maxDelta semantics are the portable contract.
5. Do NOT write View/Drawable/NinePatch/Ripple semantics from memory — CDroid (C++) + AOSP (Java) implement and test them.
6. Do NOT treat `DOM exists` / `loaded=true` / `draw called` as pixel truth — see L-S94-WEB-2/3/4.
7. Do NOT accept `frame nonblank` as `frame submitted` — SurfaceFlinger/sokol/bgfx/filament all define explicit present boundaries.

## Evidence discipline

`PROVEN` requires: source inspected (file hash + symbol hits recorded) + license checked +
port/adapt attempted + test executed (ported test where possible) + MiniAndroid integration
measured. Anything less stays `PARTIAL`/`RESEARCH` and must be labeled so.
