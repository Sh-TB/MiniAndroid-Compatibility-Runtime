# GRAPHICS SOURCE REGISTRY — MiniAndroid permanent asset (S94)

> **This registry is permanent engineering infrastructure.**
> For EVERY future graphics problem: classify → look up here → inspect the
> upstream source AND tests → only then implement. Never reproduce behavior
> from memory. Never invent a replacement when a strong upstream
> implementation exists. Never treat GitHub stars as correctness.

- generated: 2026-09-24T09:32:27Z
- registry entries: **127**
- distinct GitHub-verified repositories: **122**
- deep-inspected (clone or pinned-SHA fetch): **65**
- identity-only verified: 57
- off-GitHub canonical references: 4
- unverified directive identities (recorded honestly, never substituted): 1
- semantic laws with fetched evidence: **48/48**

## Verification methods (no invented identities)

| Evidence | Method |
|---|---|
| repository identity + HEAD commit | `git ls-remote --symref https://github.com/<owner>/<repo>.git HEAD` |
| license | `raw.githubusercontent.com` fetch **at the pinned HEAD SHA** (sha256 recorded) |
| deep source mining | shallow clone + file harvest (sha256, symbol line hits) |
| large-repo source mining | pinned-SHA raw fetch with symbol line hits |
| AOSP-only repos | `android.googlesource.com ...?format=TEXT` (minikin, View.java) |

## Mirror / canonical policy

- One record per canonical repository identity. Seed entries listed in several
  families keep ONE record with multiple `families` (no double counting).
- `MIRROR_OF:` marks repos whose canonical upstream is off GitHub (AOSP
  googlesource, freedesktop, gnome). These are distinct codebases, not
  duplicates of anything else in this registry.
- `FORK_OF:` marks forks carrying downstream patches (JetBrains compose core,
  LineageOS native frameworks).
- Identity migrations are recorded in `identity_history` — never silently
  substituted (notofonts/noto-emoji→googlefonts/noto-emoji;
  facebookarchive/screenshot-tests-for-android→facebook/...; renderdoc→baldurk).
- `android/graphics`, `google/android-codelabs`, `android/platform_frameworks_support`
  could not be verified and are recorded UNVERIFIED, per directive.

## Inspection status legend

- **DEEP_CLONE** — repository shallow-cloned; key files hashed + symbol line hits recorded
- **DEEP_FETCH** — provenance-pinned source files fetched with symbol line hits
- **IDENTITY_ONLY** — identity + license verified; not yet deep-read (future work)

## Priority families (lookup table)

| Failure family | First sources to consult |
|---|---|
| WRONG_COLOR | google/skia, aosp-mirror/platform_frameworks_base (BitmapFactory), bumptech/glide (Downsampler), pnggroup/libpng, webmproject/libwebp, mapbox/pixelmatch |
| WRONG_CLIP | aosp-mirror/platform_frameworks_base (Canvas), google/skia (SkCanvas), houstudio/cdroid (view/ninepatch), androidx/constraintlayout, facebook/yoga |
| ANIMATION_FROZEN | aosp-mirror/platform_frameworks_base (AnimationDrawable), libgdx/libgdx (AndroidGraphics), google/wuffs (GIF disposal), airbnb/lottie-android, godotengine/godot, python-pillow/Pillow |
| UNREADABLE_TEXT | harfbuzz/harfbuzz, google/minikin, freetype/freetype, unicode-org/icu, fribidi/fribidi, tesseract-ocr/tesseract, houstudio/cdroid (StaticLayout) |
| Surface / frame submission | aosp-mirror/platform_frameworks_base (SurfaceView), libgdx/libgdx, libsdl-org/SDL, LineageOS/android_frameworks_native (SurfaceFlinger), floooh/sokol, bkaradzic/bgfx |
| WebView visual readiness | chromium/chromium (AwContents), WebKit/WebKit (ImageLoader), web-platform-tests/wpt, electron/electron |
| Screenshot false-positive | mapbox/pixelmatch, JohannesBuchner/imagehash, takahirom/roborazzi, cashapp/paparazzi, ndtp/android-testify, pedrovgs/Shot |
| Vector / NinePatch | houstudio/cdroid, aosp-mirror/platform_frameworks_base, RazrFalcon/resvg, memononen/nanovg |
| Compose pipeline | androidx/androidx, JetBrains/skiko, JetBrains/compose-multiplatform-core |

## Law map (48 laws, all with fetched evidence)

| Law | Family | Source | File | Reuse |
|---|---|---|---|---|
| L-S94-DENSITY-1 | resource-density | aosp-mirror/platform_frameworks_base | `graphics/java/android/graphics/BitmapFactory.java` | PORT_ALGORITHM |
| L-S94-DENSITY-2 | resource-density | bumptech/glide | `library/src/main/java/com/bumptech/glide/load/resource/bitmap/Downsampler.java` | PORT_TEST |
| L-S94-CLIP-1 | geometry-clip | aosp-mirror/platform_frameworks_base | `graphics/java/android/graphics/Canvas.java` | PORT_ALGORITHM |
| L-S94-CLIP-2 | geometry-clip | google/skia | `src/core/SkCanvas.cpp` | REFERENCE_ONLY |
| L-S94-DRAW-1 | view-tree | aosp-mirror/platform_frameworks_base | `core/java/android/view/View.java` | PORT_ALGORITHM |
| L-S94-TREE-1 | view-tree | aosp-mirror/platform_frameworks_base | `core/java/android/view/ViewRootImpl.java` | REFERENCE_ONLY |
| L-S94-SURFACE-1 | surface | aosp-mirror/platform_frameworks_base | `core/java/android/view/SurfaceView.java` | REFERENCE_ONLY |
| L-S94-SURFACE-2 | surface | libgdx/libgdx | `backends/gdx-backend-android/src/com/badlogic/gdx/backends/android/AndroidGraphics.java` | PORT_ALGORITHM |
| L-S94-SURFACE-3 | surface | libsdl-org/SDL | `src/video/SDL_video.c` | REFERENCE_ONLY |
| L-S94-SURFACE-4 | surface | LineageOS/android_frameworks_native | `services/surfaceflinger/SurfaceFlinger.cpp` | REFERENCE_ONLY |
| L-S94-FRAME-1 | frame-loop | godotengine/godot | `main/main.cpp` | REFERENCE_ONLY |
| L-S94-FRAME-3 | frame-loop | floooh/sokol | `sokol_gfx.h` | REFERENCE_ONLY |
| L-S94-FRAME-4 | frame-loop | bkaradzic/bgfx | `src/bgfx.cpp` | REFERENCE_ONLY |
| L-S94-FRAME-5 | frame-loop | google/filament | `filament/src/Renderer.cpp` | REFERENCE_ONLY |
| L-S94-FRAME-6 | frame-loop | urho3d/urho3d | `Source/Urho3D/Graphics/Renderer.cpp` | REFERENCE_ONLY |
| L-S94-ANIM-1 | animation | aosp-mirror/platform_frameworks_base | `graphics/java/android/graphics/drawable/AnimationDrawable.java` | PORT_ALGORITHM |
| L-S94-ANIM-3 | animation | airbnb/lottie-android | `lottie/src/main/java/com/airbnb/lottie/LottieDrawable.java` | PORT_ALGORITHM |
| L-S94-GIF-1 | animation-gif | python-pillow/Pillow | `src/PIL/GifImagePlugin.py` | PORT_TEST |
| L-S94-GIF-2 | animation-gif | golang/go | `src/image/gif/reader.go` | PORT_TEST |
| L-S94-GIF-3 | animation-gif | FFmpeg/FFmpeg | `libavcodec/gifdec.c` | REFERENCE_ONLY |
| L-S94-GIF-4 | animation-gif | google/wuffs | `release/c/wuffs-v0.4.c` | ADAPT |
| L-S94-NINEPATCH-1 | drawable-ninepatch | aosp-mirror/platform_frameworks_base | `graphics/java/android/graphics/drawable/NinePatchDrawable.java` | PORT_ALGORITHM |
| L-S94-RIPPLE-1 | drawable-ripple | material-components/material-components-android | `lib/java/com/google/android/material/ripple/RippleUtils.java` | REFERENCE_ONLY |
| L-S94-LAYOUT-1 | layout | androidx/constraintlayout | `constraintlayout/constraintlayout/src/main/java/androidx/constraintlayout/widget/ConstraintLayout.java` | REFERENCE_ONLY |
| L-S94-LAYOUT-2 | layout | facebook/yoga | `yoga/YGNode.cpp` | ADAPT |
| L-S94-SHAPE-1 | text-shaping | harfbuzz/harfbuzz | `src/hb-ot-shape.cc` | ADAPT |
| L-S94-TEXT-4 | text-layout | google/minikin | `libs/minikin/Layout.cpp` | PORT_ALGORITHM |
| L-S94-TEXT-3 | text-render | libass/libass | `libass/ass_render.c` | REFERENCE_ONLY |
| L-S94-TEXT-2 | text-render | ImageMagick/ImageMagick | `MagickCore/annotate.c` | REFERENCE_ONLY |
| L-S94-BIDI-1 | text-bidi | unicode-org/icu | `icu4c/source/common/ubidi.cpp` | ADAPT |
| L-S94-GLYPH-2 | font-raster | freetype/freetype | `src/base/ftobjs.c` | PORT_ALGORITHM |
| L-S94-GLYPH-3 | font-raster | freetype/freetype | `src/smooth/ftgrays.c` | REFERENCE_ONLY |
| L-S94-GLYPH-1 | font-raster | ocornut/imgui | `imgui.cpp` | REFERENCE_ONLY |
| L-S94-PNG-1 | image-codec | google/skia | `src/codec/SkPngCodec.cpp` | REFERENCE_ONLY |
| L-S94-DECODE-1 | image-codec | nothings/stb | `stb_image.h` | REFERENCE_ONLY |
| L-S94-DECODE-2 | image-codec | mozilla/mozjpeg | `jdapistd.c` | REFERENCE_ONLY |
| L-S94-WEB-2 | web-rendering | chromium/chromium | `android_webview/java/src/org/chromium/android_webview/AwContents.java` | REFERENCE_ONLY |
| L-S94-WEB-3 | web-rendering | WebKit/WebKit | `Source/WebCore/loader/ImageLoader.cpp` | REFERENCE_ONLY |
| L-S94-WEB-4 | web-rendering | electron/electron | `docs/api/browser-window.md` | REFERENCE_ONLY |
| L-S94-DIFF-1 | visual-diff | mapbox/pixelmatch | `index.js` | PORT_ALGORITHM |
| L-S94-DIFF-2 | visual-diff | JohannesBuchner/imagehash | `imagehash/__init__.py` | PORT_TEST |
| L-S94-SCREENSHOT-1 | screenshot-testing | takahirom/roborazzi | `roborazzi/src/main/java/com/github/takahirom/roborazzi/Roborazzi.kt` | PORT_TEST |
| L-S94-SCREENSHOT-2 | screenshot-testing | cashapp/paparazzi | `paparazzi/src/main/java/app/cash/paparazzi/Paparazzi.kt` | PORT_TEST |
| L-S94-SCREENSHOT-3 | screenshot-testing | ndtp/android-testify | `Library/src/main/java/dev/testify/ScreenshotRule.kt` | PORT_TEST |
| L-S94-OCR-1 | text-verify | tesseract-ocr/tesseract | `src/api/baseapi.cpp` | ADAPT |
| L-S94-SVG-1 | vector | RazrFalcon/resvg | `crates/resvg/src/render.rs` | ADAPT |
| L-S94-VECTOR-1 | vector | memononen/nanovg | `src/nanovg.c` | REFERENCE_ONLY |
| L-S94-CDROID-1 | android-ui-reference | houstudio/cdroid | `src/gui/view/view.h` | PORT_ALGORITHM_WITH_LICENSE_GATE (LICENSE=LGPL-2.1-or-later, sha256 6da7ddf4...: use as behavioral reference or dynamic-link; static port requires LGPL compliance) |

Full law statements, symbol line hits and file hashes: `run/s94/source_mining/source_to_law.json`, `findings.jsonl`.

## VERIFIED (GitHub) (122)

| ID | Repository | Families | P | License | Inspection | Files | HEAD SHA |
|---|---|---|---|---|---|---|---|
| GFX-SRC-001 | [google/skia (MIRROR_OF)](https://github.com/google/skia) | 2d-rendering, text-raster, image-codec… | P0 | BSD-style(1-clause-candi | DEEP_FETCH | 2 | 53eae7263a |
| GFX-SRC-002 | [google/angle (MIRROR_OF)](https://github.com/google/angle) | gles-translation, vulkan | P0 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | 25621abe9b |
| GFX-SRC-003 | [google/swiftshader (MIRROR_OF)](https://github.com/google/swiftshader) | cpu-gpu, rasterizer | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | 1e80438d2b |
| GFX-SRC-004 | [google/gfxstream](https://github.com/google/gfxstream) | virtualized-gfx, gles | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | ebe5b424e1 |
| GFX-SRC-005 | [aosp-mirror/platform_frameworks_base (MIRROR_OF)](https://github.com/aosp-mirror/platform_frameworks_base) | android-framework, view, drawable… | P0 | Apache-2.0 | DEEP_FETCH | 8 | 1cdfff555f |
| GFX-SRC-006 | [androidx/androidx](https://github.com/androidx/androidx) | jetpack-compose, android-framework | P0 | Apache-2.0 | DEEP_FETCH | 2 | 60b8e3cca8 |
| GFX-SRC-008 | [unicode-org/icu](https://github.com/unicode-org/icu) | unicode-i18n, bidi | P0 | MIT | DEEP_FETCH | 1 | e86daaca40 |
| GFX-SRC-009 | [harfbuzz/harfbuzz](https://github.com/harfbuzz/harfbuzz) | text-shaping | P0 | UNCLASSIFIED | DEEP_CLONE | 43 | 873dbc1e32 |
| GFX-SRC-010 | [freetype/freetype (MIRROR_OF)](https://github.com/freetype/freetype) | font-raster | P0 | FOUND:docs/FTL.TXT | DEEP_FETCH | 2 | d333439633 |
| GFX-SRC-011 | [cashapp/paparazzi](https://github.com/cashapp/paparazzi) | screenshot-testing, layoutlib | P0 | Apache-2.0 | DEEP_CLONE | 40 | 42514978f1 |
| GFX-SRC-012 | [takahirom/roborazzi](https://github.com/takahirom/roborazzi) | screenshot-testing, robolectric | P0 | Apache-2.0 | DEEP_CLONE | 7 | c97214ed09 |
| GFX-SRC-013 | [pedrovgs/Shot](https://github.com/pedrovgs/Shot) | screenshot-testing | P0 | Apache-2.0 | DEEP_CLONE | 24 | e102d797d8 |
| GFX-SRC-014 | [facebook/screenshot-tests-for-android (ARCHIVED)](https://github.com/facebook/screenshot-tests-for-android) | screenshot-testing | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | e098fd7fdb |
| GFX-SRC-015 | [ndtp/android-testify](https://github.com/ndtp/android-testify) | screenshot-testing | P0 | MIT | DEEP_CLONE | 41 | b36c378f4a |
| GFX-SRC-016 | [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) | visual-diff | P0 | UNCLASSIFIED | DEEP_CLONE | 1 | b2800051f2 |
| GFX-SRC-017 | [opencv/opencv](https://github.com/opencv/opencv) | image-processing, visual-diff | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | aa5546b3e4 |
| GFX-SRC-018 | [garris/BackstopJS](https://github.com/garris/BackstopJS) | visual-regression, web | P0 | MIT | IDENTITY_ONLY | 0 | a11d365778 |
| GFX-SRC-019 | [americanexpress/jest-image-snapshot](https://github.com/americanexpress/jest-image-snapshot) | visual-diff, screenshot-testing | P0 | Apache-2.0 | DEEP_CLONE | 5 | c7e3056b03 |
| GFX-SRC-020 | [JohannesBuchner/imagehash](https://github.com/JohannesBuchner/imagehash) | perceptual-hash | P0 | BSD-style(1-clause-candi | DEEP_CLONE | 14 | 7a405c9a27 |
| GFX-SRC-021 | [pnggroup/libpng](https://github.com/pnggroup/libpng) | image-codec, png | P0 | UNCLASSIFIED | DEEP_CLONE | 4 | 964b413594 |
| GFX-SRC-022 | [libjpeg-turbo/libjpeg-turbo](https://github.com/libjpeg-turbo/libjpeg-turbo) | image-codec, jpeg | P0 | Zlib | DEEP_CLONE | 4 | 2a8bd381b4 |
| GFX-SRC-023 | [webmproject/libwebp](https://github.com/webmproject/libwebp) | image-codec, webp | P0 | BSD-style(1-clause-candi | DEEP_CLONE | 16 | f4c34a1d45 |
| GFX-SRC-024 | [AOMediaCodec/libavif](https://github.com/AOMediaCodec/libavif) | image-codec, avif | P0 | BSD-style(2-clause-candi | IDENTITY_ONLY | 0 | 58020e054c |
| GFX-SRC-025 | [strukturag/libheif](https://github.com/strukturag/libheif) | image-codec, heif | P0 | LGPL | IDENTITY_ONLY | 0 | 5c7b41f3cc |
| GFX-SRC-026 | [google/wuffs](https://github.com/google/wuffs) | image-codec, verify | P0 | Apache-2.0 | DEEP_CLONE | 1 | f31d952b62 |
| GFX-SRC-027 | [ImageMagick/ImageMagick](https://github.com/ImageMagick/ImageMagick) | image-processing | P0 | UNCLASSIFIED | DEEP_FETCH | 1 | 06a4557775 |
| GFX-SRC-028 | [libvips/libvips](https://github.com/libvips/libvips) | image-processing | P0 | LGPL-2.1-or-later | IDENTITY_ONLY | 0 | 2f397a4a31 |
| GFX-SRC-029 | [mozilla/mozjpeg](https://github.com/mozilla/mozjpeg) | image-codec, jpeg | P0 | Zlib | DEEP_FETCH | 1 | 0826579077 |
| GFX-SRC-030 | [googleprojectzero/SkCodecFuzzer](https://github.com/googleprojectzero/SkCodecFuzzer) | fuzzing, image-codec | P0 | Apache-2.0 | DEEP_FETCH | 1 | 1ffd5b2012 |
| GFX-SRC-031 | [bumptech/glide](https://github.com/bumptech/glide) | image-loading, android | P0 | Apache-2.0 | DEEP_FETCH | 1 | 166f0a20fb |
| GFX-SRC-032 | [coil-kt/coil](https://github.com/coil-kt/coil) | image-loading, android | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | 1277b063c9 |
| GFX-SRC-033 | [facebook/fresco](https://github.com/facebook/fresco) | image-loading, android | P0 | MIT | IDENTITY_ONLY | 0 | 53dc796565 |
| GFX-SRC-034 | [square/picasso](https://github.com/square/picasso) | image-loading, android | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | e94d6116e3 |
| GFX-SRC-035 | [skydoves/landscapist](https://github.com/skydoves/landscapist) | image-loading, compose | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | fc89c8093e |
| GFX-SRC-036 | [wasabeef/glide-transformations](https://github.com/wasabeef/glide-transformations) | image-loading, transform | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | d950f0c33f |
| GFX-SRC-037 | [google/brotli](https://github.com/google/brotli) | compression | P0 | MIT | DEEP_FETCH | 1 | 11017d7812 |
| GFX-SRC-038 | [android/graphics](https://github.com/android/graphics) | android-graphics | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | 01240b7759 |
| GFX-SRC-040 | [android/platform_frameworks_support](https://github.com/android/platform_frameworks_support) | android-framework, support-lib | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | a9ac247af2 |
| GFX-SRC-041 | [googlefonts/fonttools](https://github.com/googlefonts/fonttools) | font-tooling | P0 | MIT | DEEP_FETCH | 1 | 03a3c8ed9e |
| GFX-SRC-042 | [notofonts/noto-fonts (ARCHIVED)](https://github.com/notofonts/noto-fonts) | fonts | P0 | UNCLASSIFIED | IDENTITY_ONLY | 0 | ffebf8c1ee |
| GFX-SRC-043 | [googlefonts/noto-emoji](https://github.com/googlefonts/noto-emoji) | fonts, emoji | P0 | UNCLASSIFIED | IDENTITY_ONLY | 0 | 06121655d0 |
| GFX-SRC-044 | [liberationfonts/liberation-fonts](https://github.com/liberationfonts/liberation-fonts) | fonts | P0 | UNCLASSIFIED | IDENTITY_ONLY | 0 | 49e1358e40 |
| GFX-SRC-045 | [googlefonts/noto-cjk](https://github.com/googlefonts/noto-cjk) | fonts, cjk | P0 | NO_LICENSE_FILE_IN_STAND | IDENTITY_ONLY | 0 | f8d157532f |
| GFX-SRC-046 | [google/flexbox-layout](https://github.com/google/flexbox-layout) | layout, android | P0 | Apache-2.0 | DEEP_CLONE | 13 | 366b461fd0 |
| GFX-SRC-047 | [androidx/constraintlayout](https://github.com/androidx/constraintlayout) | layout, android | P0 | Apache-2.0 | DEEP_FETCH | 1 | 9cd4b5a407 |
| GFX-SRC-048 | [airbnb/epoxy](https://github.com/airbnb/epoxy) | recyclerview, android | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | e45bd3a61f |
| GFX-SRC-049 | [airbnb/lottie-android](https://github.com/airbnb/lottie-android) | animation, android | P0 | Apache-2.0 | DEEP_CLONE | 4 | 05ea92e903 |
| GFX-SRC-050 | [facebookarchive/shimmer-android (ARCHIVED)](https://github.com/facebookarchive/shimmer-android) | animation, android | P0 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | 32b784bd98 |
| GFX-SRC-051 | [houstudio/cdroid](https://github.com/houstudio/cdroid) | android-ui, rendering | P0 | LGPL-2.1-or-later | DEEP_CLONE | 58 | da89e06bc0 |
| GFX-SRC-052 | [material-components/material-components-android](https://github.com/material-components/material-components-android) | android-ui, material | P0 | Apache-2.0 | DEEP_FETCH | 1 | 60ff09436d |
| GFX-SRC-053 | [google/accompanist](https://github.com/google/accompanist) | compose, android | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | 12ec3408fc |
| GFX-SRC-054 | [android/compose-samples](https://github.com/android/compose-samples) | compose, samples | P0 | UNCLASSIFIED | IDENTITY_ONLY | 0 | 0bbd72d698 |
| GFX-SRC-055 | [android/nowinandroid](https://github.com/android/nowinandroid) | compose, samples | P0 | Apache-2.0 | IDENTITY_ONLY | 0 | a49ed253d7 |
| GFX-SRC-056 | [JetBrains/compose-multiplatform](https://github.com/JetBrains/compose-multiplatform) | compose-multiplatform | P1 | Apache-2.0 | IDENTITY_ONLY | 0 | 62ab13f07c |
| GFX-SRC-057 | [JetBrains/compose-multiplatform-core (FORK_OF)](https://github.com/JetBrains/compose-multiplatform-core) | compose-multiplatform | P1 | Apache-2.0 | DEEP_FETCH | 1 | 7284d0b5df |
| GFX-SRC-058 | [JetBrains/skiko](https://github.com/JetBrains/skiko) | skia, kotlin | P1 | Apache-2.0 | DEEP_FETCH | 1 | 12d12006ca |
| GFX-SRC-059 | [chrisbanes/tivi](https://github.com/chrisbanes/tivi) | compose, sample-app | P1 | Apache-2.0 | IDENTITY_ONLY | 0 | a0c62c2c76 |
| GFX-SRC-060 | [libgdx/libgdx](https://github.com/libgdx/libgdx) | game-engine, android-backend | P0 | Apache-2.0 | DEEP_FETCH | 1 | 84c2497ac8 |
| GFX-SRC-061 | [godotengine/godot](https://github.com/godotengine/godot) | game-engine, rendering | P0 | MIT | DEEP_FETCH | 1 | ca871ccc9c |
| GFX-SRC-062 | [libsdl-org/SDL](https://github.com/libsdl-org/SDL) | platform-layer, surface | P0 | UNCLASSIFIED | DEEP_FETCH | 1 | 34d66a4d39 |
| GFX-SRC-063 | [cocos2d/cocos2d-x](https://github.com/cocos2d/cocos2d-x) | game-engine | P0 | NO_LICENSE_FILE_IN_STAND | IDENTITY_ONLY | 0 | 7a5282a301 |
| GFX-SRC-064 | [korlibs/korge](https://github.com/korlibs/korge) | game-engine, kotlin | P0 | MIT | IDENTITY_ONLY | 0 | bd2bbaad6e |
| GFX-SRC-065 | [defold/defold](https://github.com/defold/defold) | game-engine | P0 | UNCLASSIFIED | DEEP_FETCH | 1 | a4ae60f9cd |
| GFX-SRC-066 | [urho3d/urho3d](https://github.com/urho3d/urho3d) | game-engine | P0 | NO_LICENSE_FILE_IN_STAND | DEEP_FETCH | 1 | e0ce107356 |
| GFX-SRC-067 | [axmolengine/axmol](https://github.com/axmolengine/axmol) | game-engine | P0 | MIT | IDENTITY_ONLY | 0 | 0c1b62c62b |
| GFX-SRC-068 | [floooh/sokol](https://github.com/floooh/sokol) | graphics-backend | P1 | Zlib | DEEP_FETCH | 1 | 2e75443dbd |
| GFX-SRC-069 | [bkaradzic/bgfx](https://github.com/bkaradzic/bgfx) | graphics-backend | P1 | BSD-style(1-clause-candi | DEEP_FETCH | 1 | ae6bc904d5 |
| GFX-SRC-070 | [google/filament](https://github.com/google/filament) | pbr-rendering, android | P1 | Apache-2.0 | DEEP_FETCH | 1 | a5e4a836aa |
| GFX-SRC-071 | [flutter/engine (ARCHIVED)](https://github.com/flutter/engine) | declarative-ui, skia | P1 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | ae5c3603d0 |
| GFX-SRC-072 | [chromium/chromium](https://github.com/chromium/chromium) | web-rendering | P0 | BSD-style(1-clause-candi | DEEP_FETCH | 1 | 078db04964 |
| GFX-SRC-073 | [WebKit/WebKit](https://github.com/WebKit/WebKit) | web-rendering | P0 | FOUND:Source/WebCore/LIC | DEEP_FETCH | 2 | d9fb479bd0 |
| GFX-SRC-074 | [servo/servo](https://github.com/servo/servo) | web-rendering, rust | P1 | MPL-2.0 | IDENTITY_ONLY | 0 | 5f3f3ebdd4 |
| GFX-SRC-075 | [web-platform-tests/wpt](https://github.com/web-platform-tests/wpt) | web-tests | P0 | BSD-style(1-clause-candi | DEEP_FETCH | 1 | e35344a20f |
| GFX-SRC-076 | [mozilla/gecko-dev (MIRROR_OF)](https://github.com/mozilla/gecko-dev) | web-rendering | P2 | UNCLASSIFIED | IDENTITY_ONLY | 0 | 5836a06272 |
| GFX-SRC-077 | [electron/electron](https://github.com/electron/electron) | web-embedding | P1 | MIT | DEEP_FETCH | 2 | db6cb2d99d |
| GFX-SRC-078 | [tauri-apps/tauri](https://github.com/tauri-apps/tauri) | web-embedding | P2 | MIT | IDENTITY_ONLY | 0 | 023fe7f596 |
| GFX-SRC-079 | [flutter/flutter](https://github.com/flutter/flutter) | declarative-ui, skia | P0 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | 911600f57d |
| GFX-SRC-080 | [ionic-team/capacitor](https://github.com/ionic-team/capacitor) | web-embedding, android | P2 | MIT | IDENTITY_ONLY | 0 | 145560ee59 |
| GFX-SRC-081 | [nothings/stb](https://github.com/nothings/stb) | image-codec, single-header | P1 | MIT | DEEP_FETCH | 1 | 2c980bb598 |
| GFX-SRC-082 | [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | image-video-codec | P2 | LGPL-2.1-or-later | DEEP_FETCH | 1 | 5253641e62 |
| GFX-SRC-083 | [uclouvain/openjpeg](https://github.com/uclouvain/openjpeg) | image-codec, jpeg2000 | P3 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | 8314119b06 |
| GFX-SRC-084 | [python-pillow/Pillow](https://github.com/python-pillow/Pillow) | image-codec, tests | P1 | UNCLASSIFIED | DEEP_FETCH | 2 | 8960fe0b29 |
| GFX-SRC-085 | [golang/go](https://github.com/golang/go) | image-codec, stdlib-tests | P1 | BSD-style(1-clause-candi | DEEP_FETCH | 2 | 41fd3e5b1b |
| GFX-SRC-086 | [image-rs/image](https://github.com/image-rs/image) | image-codec, rust | P3 | MIT | IDENTITY_ONLY | 0 | 075e65d618 |
| GFX-SRC-087 | [libgd/libgd](https://github.com/libgd/libgd) | image-codec, gif | P3 | UNCLASSIFIED | IDENTITY_ONLY | 0 | b8ccbeedd8 |
| GFX-SRC-088 | [reg-viz/reg-suit](https://github.com/reg-viz/reg-suit) | visual-regression | P2 | MIT | DEEP_FETCH | 1 | 5c09c8eb1e |
| GFX-SRC-089 | [kornelski/dssim](https://github.com/kornelski/dssim) | visual-diff, ssim | P2 | GPL-3.0 | DEEP_FETCH | 1 | 0e44c9b7fe |
| GFX-SRC-090 | [OpenImageIO/oiio](https://github.com/OpenImageIO/oiio) | image-processing | P2 | Apache-2.0 | DEEP_FETCH | 1 | 3722a2d4da |
| GFX-SRC-091 | [RazrFalcon/resvg](https://github.com/RazrFalcon/resvg) | svg, rasterizer | P1 | MIT | DEEP_CLONE | 25 | 75b6bbadd7 |
| GFX-SRC-092 | [memononen/nanosvg](https://github.com/memononen/nanosvg) | svg, rasterizer | P2 | UNCLASSIFIED | DEEP_CLONE | 2 | 239e102ec2 |
| GFX-SRC-093 | [memononen/nanovg](https://github.com/memononen/nanovg) | canvas, gl | P2 | UNCLASSIFIED | DEEP_CLONE | 2 | ce3bf745eb |
| GFX-SRC-094 | [Tencent/tgfx](https://github.com/Tencent/tgfx) | 2d-rendering, vector | P2 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | c2a7171619 |
| GFX-SRC-095 | [Samsung/rlottie](https://github.com/Samsung/rlottie) | animation, vector | P1 | UNCLASSIFIED | IDENTITY_ONLY | 0 | 683bbaa39d |
| GFX-SRC-096 | [servo/webrender](https://github.com/servo/webrender) | gpu-rasterizer | P2 | MPL-2.0 | IDENTITY_ONLY | 0 | e1c924ebad |
| GFX-SRC-099 | [raysan5/raylib](https://github.com/raysan5/raylib) | game-2d, textures, text | P3 | UNCLASSIFIED | IDENTITY_ONLY | 0 | cb95b8fba7 |
| GFX-SRC-100 | [fribidi/fribidi](https://github.com/fribidi/fribidi) | bidi | P1 | LGPL-2.1-or-later | DEEP_CLONE | 3 | 4c914a92e9 |
| GFX-SRC-101 | [silnrsi/graphite](https://github.com/silnrsi/graphite) | text-shaping | P3 | LGPL-2.1-or-later | IDENTITY_ONLY | 0 | ca8d821e60 |
| GFX-SRC-102 | [libass/libass](https://github.com/libass/libass) | text-render, subtitle | P3 | UNCLASSIFIED | DEEP_FETCH | 1 | f61db567e6 |
| GFX-SRC-103 | [GNOME/pango (MIRROR_OF)](https://github.com/GNOME/pango) | text-layout | P2 | UNCLASSIFIED | IDENTITY_ONLY | 0 | 8e74c27c11 |
| GFX-SRC-104 | [fontforge/fontforge](https://github.com/fontforge/fontforge) | font-tooling | P3 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | 606b33dcdd |
| GFX-SRC-105 | [facebook/yoga](https://github.com/facebook/yoga) | layout-engine | P1 | MIT | DEEP_CLONE | 59 | a8b4817143 |
| GFX-SRC-106 | [ocornut/imgui](https://github.com/ocornut/imgui) | ui, font-atlas | P2 | MIT | DEEP_FETCH | 1 | 623ba46120 |
| GFX-SRC-107 | [avaloniaui/avalonia](https://github.com/avaloniaui/avalonia) | ui, skia | P3 | NO_LICENSE_FILE_IN_STAND | IDENTITY_ONLY | 0 | c423071d33 |
| GFX-SRC-108 | [androguard/androguard](https://github.com/androguard/androguard) | apk-analysis | P1 | FOUND:LICENCE | DEEP_FETCH | 1 | a06d033c0d |
| GFX-SRC-109 | [reandroid/ARSCLib](https://github.com/reandroid/ARSCLib) | arsc, android-resources | P1 | Apache-2.0 | DEEP_FETCH | 1 | b9c2266bd0 |
| GFX-SRC-110 | [iBotPeaches/Apktool](https://github.com/iBotPeaches/Apktool) | apk-analysis | P2 | Apache-2.0 | IDENTITY_ONLY | 0 | 57690eee61 |
| GFX-SRC-111 | [skylot/jadx](https://github.com/skylot/jadx) | apk-analysis | P2 | Apache-2.0 | IDENTITY_ONLY | 0 | 2fb1b16386 |
| GFX-SRC-112 | [KhronosGroup/Vulkan-Samples](https://github.com/KhronosGroup/Vulkan-Samples) | vulkan, samples | P3 | Apache-2.0 | IDENTITY_ONLY | 0 | 177edebf0c |
| GFX-SRC-113 | [KhronosGroup/WebGL](https://github.com/KhronosGroup/WebGL) | webgl, conformance | P2 | MIT | DEEP_FETCH | 1 | 714857a284 |
| GFX-SRC-114 | [apitrace/apitrace](https://github.com/apitrace/apitrace) | frame-tracing | P3 | MIT | IDENTITY_ONLY | 0 | 9b3f2d1ced |
| GFX-SRC-115 | [baldurk/renderdoc](https://github.com/baldurk/renderdoc) | graphics-debugger | P3 | MIT | IDENTITY_ONLY | 0 | 54f92c222a |
| GFX-SRC-116 | [google/agi](https://github.com/google/agi) | android-gpu-profiler | P3 | Apache-2.0 | IDENTITY_ONLY | 0 | d08ae4f585 |
| GFX-SRC-117 | [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) | screen-capture, android | P3 | Apache-2.0 | IDENTITY_ONLY | 0 | 19c1261d2e |
| GFX-SRC-118 | [puppeteer/puppeteer](https://github.com/puppeteer/puppeteer) | browser-automation | P2 | Apache-2.0 | DEEP_FETCH | 1 | 15684eb7f1 |
| GFX-SRC-119 | [maplibre/maplibre-gl-native](https://github.com/maplibre/maplibre-gl-native) | map-rendering, glyph-atlas | P3 | BSD-style(1-clause-candi | IDENTITY_ONLY | 0 | d695deef12 |
| GFX-SRC-120 | [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) | ocr, text-verify | P2 | Apache-2.0 | DEEP_FETCH | 1 | 8ae6810143 |
| GFX-SRC-121 | [canvg/canvg](https://github.com/canvg/canvg) | canvas, web | P3 | MIT | DEEP_FETCH | 1 | d63883331e |
| GFX-SRC-122 | [godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects) | fixtures, game-engine | P3 | MIT | DEEP_FETCH | 1 | a3b5c11311 |
| GFX-SRC-123 | [facebook/litho](https://github.com/facebook/litho) | android-ui | P3 | Apache-2.0 | DEEP_FETCH | 1 | 55e28e5893 |
| GFX-SRC-124 | [chrisbanes/PhotoView](https://github.com/chrisbanes/PhotoView) | android-ui, imageview | P2 | Apache-2.0 | IDENTITY_ONLY | 0 | 565505d5cb |
| GFX-SRC-125 | [hajimehoshi/ebiten](https://github.com/hajimehoshi/ebiten) | game-engine, go | P3 | Apache-2.0 | IDENTITY_ONLY | 0 | dd52507294 |
| GFX-SRC-900 | [LineageOS/android_frameworks_native (FORK_OF)](https://github.com/LineageOS/android_frameworks_native) | android-framework, surfaceflinger, surface | P2 | Apache-2.0 | DEEP_FETCH | 1 | 9568531f9b |

## OFF-GITHUB canonical (4)

Canonical upstream NOT on GitHub — links preserved, not counted in the GitHub distinct count.

| ID | Repository | Families | P | License | Inspection | Files | HEAD SHA |
|---|---|---|---|---|---|---|---|
| GFX-SRC-007 | [google/minikin (MIRROR_OF)](https://github.com/google/minikin) | text-layout, shaping | P0 | UNKNOWN | DEEP_FETCH | 1 |  |
| GFX-SRC-097 | [mesa3d/mesa (MIRROR_OF)](https://github.com/mesa3d/mesa) | gl, cpu-rasterizer | P3 | UNKNOWN | IDENTITY_ONLY | 0 |  |
| GFX-SRC-098 | [cairo/cairo (MIRROR_OF)](https://github.com/cairo/cairo) | 2d-rendering | P2 | UNKNOWN | IDENTITY_ONLY | 0 |  |
| GFX-SRC-126 | [aosp-mirror/platform_frameworks_native (MIRROR_OF)](https://github.com/aosp-mirror/platform_frameworks_native) | android-framework, surfaceflinger | P1 | UNKNOWN | IDENTITY_ONLY | 0 |  |

## UNVERIFIED directive identity (1)

Seed directive listed these; GitHub has no such repo at that identity. Recorded honestly; never substituted.

| ID | Repository | Families | P | License | Inspection | Files | HEAD SHA |
|---|---|---|---|---|---|---|---|
| GFX-SRC-039 | [google/android-codelabs](https://github.com/google/android-codelabs) | android-samples | P0 | UNKNOWN | IDENTITY_ONLY | 0 |  |

## Maintenance law

1. Every new graphics source must be added here (and to `GRAPHICS_SOURCE_REGISTRY.json`) with identity verification, license evidence, and inspection status.
2. If a repository moves: update the entry, keep the old reference in `identity_history`, record the migration date.
3. `IDENTITY_ONLY` entries are queued future deep-mining work — they count as verified identities but NOT as inspected sources.
4. License gates reuse: `SAFE_PORT_WITH_ATTRIBUTION` < `COPY_REQUIRES_NOTICE` < `REFERENCE_ONLY`. Never copy from `REFERENCE_ONLY` sources.
5. The registry feeds `tools/source_lookup.py` — keep families in sync with the failure taxonomy.

