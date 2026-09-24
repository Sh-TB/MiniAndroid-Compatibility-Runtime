"""S94 Phase A input: curated canonical GitHub graphics-source candidates.

Policy (recorded in GRAPHICS_SOURCE_REGISTRY):
- One record per canonical repository identity. Repos listed in several S94
  seed families keep ONE record with multiple `families`.
- relationship: CANONICAL | MIRROR_OF:<upstream> | FORK_OF:<repo> | ARCHIVED
  Mirrors of an upstream NOT otherwise in this list still count as distinct
  codebases (e.g. aosp-mirror/* - AOSP canonical is googlesource, not GitHub).
- Seed entries from the S94 directive carry `seed: true`.
- Questionable identities (android/graphics, google/android-codelabs,
  android/platform_frameworks_support) are verified, never silently substituted.
"""

# (owner/repo, families, priority, relationship, seed, note)
REPOS = [
    # ---- P0 Android / rendering core (seed) ----
    ("google/skia", "2d-rendering,text-raster,image-codec,canvas", "P0", "MIRROR_OF:skia.googlesource.com/skia", True, "Flutter/Android use it; clip/premul/codec laws"),
    ("google/angle", "gles-translation,vulkan", "P0", "MIRROR_OF:chromium.googlesource.com/angle/angle", True, "GLES->backend translation; ES contract tests"),
    ("google/swiftshader", "cpu-gpu,rasterizer", "P0", "MIRROR_OF:swiftshader.googlesource.com (dev moved to chromium)", True, "CPU GL/Vulkan; software renderer reference"),
    ("google/gfxstream", "virtualized-gfx,gles", "P0", "CANONICAL", True, "Android emulator guest->host graphics streaming"),
    ("aosp-mirror/platform_frameworks_base", "android-framework,view,drawable,text,animation", "P0", "MIRROR_OF:android.googlesource.com/platform/frameworks/base", True, "View/Canvas/BitmapFactory/NinePatch/AnimationDrawable laws"),
    ("androidx/androidx", "jetpack-compose,android-framework", "P0", "CANONICAL", True, "Compose LayoutNode draw pipeline; Appears in 2 seed families"),
    ("google/minikin", "text-layout,shaping", "P0", "MIRROR_OF:android.googlesource.com/platform/frameworks/minikin", True, "Android text layout engine; hyphenation, font fallback"),
    ("unicode-org/icu", "unicode-i18n,bidi", "P0", "CANONICAL", True, "Unicode/bidi/break iteration"),
    ("harfbuzz/harfbuzz", "text-shaping", "P0", "CANONICAL", True, "Shaping contract + in-house shaping tests; behdad/harfbuzz redirects here"),
    ("freetype/freetype", "font-raster", "P0", "MIRROR_OF:gitlab.freedesktop.org/freetype/freetype", True, "Glyph rasterization, hinting"),
    # ---- P0 visual verification (seed) ----
    ("cashapp/paparazzi", "screenshot-testing,layoutlib", "P0", "CANONICAL", True, "JVM screenshot tests via layoutlib"),
    ("takahirom/roborazzi", "screenshot-testing,robolectric", "P0", "CANONICAL", True, "Robolectric screenshot capture; record/verify mode"),
    ("pedrovgs/Shot", "screenshot-testing", "P0", "CANONICAL", True, "Screenshot + comparison Android lib"),
    ("facebookarchive/screenshot-tests-for-android", "screenshot-testing", "P0", "ARCHIVED", True, "FB screenshot tests; verify archived state"),
    ("ndtp/android-testify", "screenshot-testing", "P0", "CANONICAL", True, "Screenshot testing with region exclusion/baselines"),
    ("mapbox/pixelmatch", "visual-diff", "P0", "CANONICAL", True, "Perceptual pixel diff with anti-aliasing detection"),
    ("opencv/opencv", "image-processing,visual-diff", "P0", "CANONICAL", True, "matchTemplate/SSIM/absdiff primitives"),
    ("garris/BackstopJS", "visual-regression,web", "P0", "CANONICAL", True, "Scenario-based visual regression for web"),
    ("americanexpress/jest-image-snapshot", "visual-diff,screenshot-testing", "P0", "CANONICAL", True, "jest toMatchImageSnapshot (pixelmatch wrapper)"),
    ("JohannesBuchner/imagehash", "perceptual-hash", "P0", "CANONICAL", True, "aHash/dHash/pHash/wHash reference"),
    # ---- P0 image codecs / asset decoding (seed) ----
    ("pnggroup/libpng", "image-codec,png", "P0", "CANONICAL", True, "Reference PNG implementation + pngtest"),
    ("libjpeg-turbo/libjpeg-turbo", "image-codec,jpeg", "P0", "CANONICAL", True, "SIMD JPEG; already linked in MiniAndroid"),
    ("webmproject/libwebp", "image-codec,webp", "P0", "CANONICAL", True, "WebP decode; lossy/lossless/alpha"),
    ("AOMediaCodec/libavif", "image-codec,avif", "P0", "CANONICAL", True, "AV1 Image File Format reference"),
    ("strukturag/libheif", "image-codec,heif", "P0", "CANONICAL", True, "HEIF/AVIF container"),
    ("google/wuffs", "image-codec,verify", "P0", "CANONICAL", True, "Verifiable decoders: GIF/BMP/WEBP/NIE; disposal semantics in source"),
    ("ImageMagick/ImageMagick", "image-processing", "P0", "CANONICAL", True, "General image toolkit"),
    ("libvips/libvips", "image-processing", "P0", "CANONICAL", True, "Streaming image processing"),
    ("mozilla/mozjpeg", "image-codec,jpeg", "P0", "CANONICAL", True, "JPEG encoder/decoder fork"),
    ("googleprojectzero/SkCodecFuzzer", "fuzzing,image-codec", "P0", "CANONICAL", True, "Fuzz harness for Skia codecs"),
    # ---- P0 Android image/resource loading (seed) ----
    ("bumptech/glide", "image-loading,android", "P0", "CANONICAL", True, "Downsampler density/inSampleSize laws + huge test suite"),
    ("coil-kt/coil", "image-loading,android", "P0", "CANONICAL", True, "Kotlin-first image loading"),
    ("facebook/fresco", "image-loading,android", "P0", "CANONICAL", True, "Pipelines, decode regions, purgeable bitmaps"),
    ("square/picasso", "image-loading,android", "P0", "CANONICAL", True, "Classic loader; fit/center-crop semantics"),
    ("skydoves/landscapist", "image-loading,compose", "P0", "CANONICAL", True, "Compose image loading"),
    ("wasabeef/glide-transformations", "image-loading,transform", "P0", "CANONICAL", True, "GPU/Bitmap transformation catalog"),
    ("google/brotli", "compression", "P0", "CANONICAL", True, "Brotli (asset/compression)"),
    ("android/graphics", "android-graphics", "P0", "UNKNOWN_IDENTITY", True, "S94 directive: verify identity before recording"),
    ("google/android-codelabs", "android-samples", "P0", "UNKNOWN_IDENTITY", True, "S94 directive: verify identity before recording"),
    ("android/platform_frameworks_support", "android-framework,support-lib", "P0", "UNKNOWN_IDENTITY", True, "Historic support-library mirror; verify"),
    # ---- Fonts / text (seed §4; dupes collapsed to families) ----
    ("googlefonts/fonttools", "font-tooling", "P0", "CANONICAL", True, "TTFont introspection; glyph metrics"),
    ("notofonts/noto-fonts", "fonts", "P0", "ARCHIVED", True, "Noto umbrella (split into per-family repos)"),
    ("notofonts/noto-emoji", "fonts,emoji", "P0", "CANONICAL", True, "Emoji font + build/flag tests"),
    ("liberationfonts/liberation-fonts", "fonts", "P0", "CANONICAL", True, "Metric-compatible Liberation fonts"),
    ("googlefonts/noto-cjk", "fonts,cjk", "P0", "CANONICAL", True, "CJK font + build checks"),
    # ---- Android view / layout / drawable (seed §5) ----
    ("google/flexbox-layout", "layout,android", "P0", "CANONICAL", True, "Flexbox measure/layout on Android"),
    ("androidx/constraintlayout", "layout,android", "P0", "CANONICAL", True, "ConstraintLayout solver + widgets"),
    ("airbnb/epoxy", "recyclerview,android", "P0", "CANONICAL", True, "RecyclerView composition"),
    ("airbnb/lottie-android", "animation,android", "P0", "CANONICAL", True, "Vector animation; composition/progress->frame law"),
    ("facebookarchive/shimmer-android", "animation,android", "P0", "ARCHIVED", True, "Shimmer drawable; verify archived"),
    ("houstudio/cdroid", "android-ui,rendering", "P0", "CANONICAL", True, "S94 MANDATORY DEEP DIVE: View/TextView/Drawable/NinePatch"),
    ("material-components/material-components-android", "android-ui,material", "P0", "CANONICAL", True, "Material drawables/ripples/buttons"),
    ("google/accompanist", "compose,android", "P0", "CANONICAL", True, "Compose utilities (permissions/pager/drawable painter)"),
    ("android/compose-samples", "compose,samples", "P0", "CANONICAL", True, "Official compose samples"),
    ("android/nowinandroid", "compose,samples", "P0", "CANONICAL", True, "Official app sample"),
    # ---- Compose / Skia / declarative (seed §6, deduped) ----
    ("JetBrains/compose-multiplatform", "compose-multiplatform", "P1", "CANONICAL", True, "CMP top repo"),
    ("JetBrains/compose-multiplatform-core", "compose-multiplatform", "P1", "FORK_OF:androidx/androidx (JB patches)", True, "JetBrains patched compose core"),
    ("JetBrains/skiko", "skia,kotlin", "P1", "CANONICAL", True, "Skia bindings for Compose MP"),
    ("chrisbanes/tivi", "compose,sample-app", "P1", "CANONICAL", True, "Real compose app"),
    # ---- Game / canvas / surface / GL (seed §7) ----
    ("libgdx/libgdx", "game-engine,android-backend", "P0", "CANONICAL", True, "AndroidGraphics: SurfaceView+GLSurfaceView frame lifecycle"),
    ("godotengine/godot", "game-engine,rendering", "P0", "CANONICAL", True, "Frame loop + RenderingServer"),
    ("libsdl-org/SDL", "platform-layer,surface", "P0", "CANONICAL", True, "Surface/swapchain abstraction"),
    ("cocos2d/cocos2d-x", "game-engine", "P0", "CANONICAL", True, "2D engine, GL frame loop"),
    ("korlibs/korge", "game-engine,kotlin", "P0", "CANONICAL", True, "Kotlin multiplatform game engine"),
    ("defold/defold", "game-engine", "P0", "CANONICAL", True, "Lua engine; render script"),
    ("urho3d/urho3d", "game-engine", "P0", "CANONICAL", True, "C++ engine"),
    ("axmolengine/axmol", "game-engine", "P0", "CANONICAL", True, "Cocos2d-x fork, active"),
    ("floooh/sokol", "graphics-backend", "P1", "CANONICAL", True, "Minimal GL header backends; frame contract"),
    ("bkaradzic/bgfx", "graphics-backend", "P1", "CANONICAL", True, "Abstraction over GL/Vulkan/D3D"),
    ("google/filament", "pbr-rendering,android", "P1", "CANONICAL", True, "Real-time PBR on Android; SwapChain/Engine/Renderer"),
    # ---- WebView / browser rendering (seed §8) ----
    ("flutter/engine", "declarative-ui,skia", "P1", "ARCHIVED", True, "Merged into flutter/flutter; historical pipeline source"),
    ("chromium/chromium", "web-rendering", "P0", "CANONICAL", True, "Blink/compositor/WebView readiness laws"),
    ("WebKit/WebKit", "web-rendering", "P0", "CANONICAL", True, "WebCore + MAC port; visual readiness"),
    ("servo/servo", "web-rendering,rust", "P1", "CANONICAL", True, "Modular layout/paint/compositor"),
    ("web-platform-tests/wpt", "web-tests", "P0", "CANONICAL", True, "Web conformance tests (PORT_TEST)"),
    ("mozilla/gecko-dev", "web-rendering", "P2", "MIRROR_OF:hg.mozilla.org/mozilla-central", True, "Read-only git mirror of Gecko"),
    ("electron/electron", "web-embedding", "P1", "CANONICAL", True, "Chromium embedding; ready-to-show semantics"),
    ("tauri-apps/tauri", "web-embedding", "P2", "CANONICAL", True, "System webview embedding"),
    ("flutter/flutter", "declarative-ui,skia", "P0", "CANONICAL", True, "Framework; engine merged here"),
    ("ionic-team/capacitor", "web-embedding,android", "P2", "CANONICAL", True, "Android WebView embedding"),
    # ---- Extensions: codecs / test oracles ----
    ("nothings/stb", "image-codec,single-header", "P1", "CANONICAL", False, "stb_image: decode semantics w/ test images"),
    ("FFmpeg/FFmpeg", "image-video-codec", "P2", "CANONICAL", False, "GIF/APNG/VP8 demux+decode; fate tests"),
    ("uclouvain/openjpeg", "image-codec,jpeg2000", "P3", "CANONICAL", False, "JP2 codec"),
    ("python-pillow/Pillow", "image-codec,tests", "P1", "CANONICAL", False, "GifImagePlugin disposal semantics + Tests/"),
    ("golang/go", "image-codec,stdlib-tests", "P1", "CANONICAL", False, "image/gif reader/writer + disposal tests"),
    ("image-rs/image", "image-codec,rust", "P3", "CANONICAL", False, "Rust image codecs + tests"),
    ("libgd/libgd", "image-codec,gif", "P3", "CANONICAL", False, "GD GIF suite"),
    # ---- Extensions: visual diff / perceptual ----
    ("reg-viz/reg-suit", "visual-regression", "P2", "CANONICAL", False, "Visual regression workflow bot"),
    ("kornelski/dssim", "visual-diff,ssim", "P2", "CANONICAL", False, "DSSIM perceptual metric (Rust)"),
    ("OpenImageIO/oiio", "image-processing", "P2", "CANONICAL", False, "oiiotool image compare"),
    # ---- Extensions: 2D rasterizers / vector ----
    ("RazrFalcon/resvg", "svg,rasterizer", "P1", "CANONICAL", False, "SVG rasterizer + HUGE golden-PNG test suite"),
    ("memononen/nanosvg", "svg,rasterizer", "P2", "CANONICAL", False, "Single-header SVG parser/rasterizer"),
    ("memononen/nanovg", "canvas,gl", "P2", "CANONICAL", False, "Canvas-like vector GL renderer"),
    ("Tencent/tgfx", "2d-rendering,vector", "P2", "CANONICAL", False, "Production 2D engine (WeChat)"),
    ("Samsung/rlottie", "animation,vector", "P1", "CANONICAL", False, "Already linked in MiniAndroid for Lottie"),
    ("servo/webrender", "gpu-rasterizer", "P2", "CANONICAL", False, "WR: batched GPU rasterization"),
    ("mesa3d/mesa", "gl,cpu-rasterizer", "P3", "MIRROR_OF:gitlab.freedesktop.org/mesa/mesa", False, "llvmpipe/swrast software GL"),
    ("cairo/cairo", "2d-rendering", "P2", "MIRROR_OF:gitlab.freedesktop.org/cairo/cairo", False, "Compositing model reference"),
    ("raysan5/raylib", "game-2d,textures,text", "P3", "CANONICAL", False, "Simple 2D + font texture rendering"),
    # ---- Extensions: text/font extras ----
    ("fribidi/fribidi", "bidi", "P1", "CANONICAL", False, "FriBidi: project-proven bidi stage"),
    ("silnrsi/graphite", "text-shaping", "P3", "CANONICAL", False, "Graphite shaping engine"),
    ("libass/libass", "text-render,subtitle", "P3", "CANONICAL", False, "HarfBuzz+FreeType consumer; glyph events"),
    ("GNOME/pango", "text-layout", "P2", "MIRROR_OF:gitlab.gnome.org/GNOME/pango", False, "Text layout/line breaking reference"),
    ("fontforge/fontforge", "font-tooling", "P3", "CANONICAL", False, "Font inspection tooling"),
    # ---- Extensions: layout ----
    ("facebook/yoga", "layout-engine", "P1", "CANONICAL", False, "Flexbox engine; adapter already differential-tested in project"),
    # ---- Extensions: UI frameworks / atlas ----
    ("ocornut/imgui", "ui,font-atlas", "P2", "CANONICAL", False, "Immediate mode + baked font atlas"),
    ("avaloniaui/avalonia", "ui,skia", "P3", "CANONICAL", False, "Skia-based cross-platform UI; hit testing"),
    # ---- Extensions: resource/AXML/ARSC ----
    ("androguard/androguard", "apk-analysis", "P1", "CANONICAL", False, "AXML/ARSC/dex oracle (named in DO_NOT_REINVENT)"),
    ("reandroid/ARSCLib", "arsc,android-resources", "P1", "CANONICAL", False, "ARSC parse/build library"),
    ("iBotPeaches/Apktool", "apk-analysis", "P2", "CANONICAL", False, "Resource decode/rebuild"),
    ("skylot/jadx", "apk-analysis", "P2", "CANONICAL", False, "dex->java; resource decode"),
    # ---- Extensions: GPU/frame tooling ----
    ("KhronosGroup/Vulkan-Samples", "vulkan,samples", "P3", "CANONICAL", False, "Frame lifecycle samples"),
    ("KhronosGroup/WebGL", "webgl,conformance", "P2", "CANONICAL", False, "WebGL conformance suite (PORT_TEST)"),
    ("apitrace/apitrace", "frame-tracing", "P3", "CANONICAL", False, "GL frame tracing/replay"),
    ("renderdoc/renderdoc", "graphics-debugger", "P3", "CANONICAL", False, "Frame capture/dissection"),
    ("google/agi", "android-gpu-profiler", "P3", "CANONICAL", False, "Android GPU Inspector; frame capture"),
    ("Genymobile/scrcpy", "screen-capture,android", "P3", "CANONICAL", False, "Device display capture pipeline"),
    # ---- Extensions: automation / screenshot harnesses ----
    ("puppeteer/puppeteer", "browser-automation", "P2", "CANONICAL", False, "Headless screenshot + readiness events"),
    # ---- Extensions: glyph atlas / map rendering ----
    ("maplibre/maplibre-gl-native", "map-rendering,glyph-atlas", "P3", "CANONICAL", False, "SDF glyph atlas + texture rendering"),
    # ---- Extensions: OCR (text readability oracle) ----
    ("tesseract-ocr/tesseract", "ocr,text-verify", "P2", "CANONICAL", False, "Independent text-readability oracle"),
    # ---- Extensions: web canvas ----
    ("canvg/canvg", "canvas,web", "P3", "CANONICAL", False, "JS canvas 2D semantics implementation"),
    # ---- Extensions: fixtures / samples ----
    ("godotengine/godot-demo-projects", "fixtures,game-engine", "P3", "CANONICAL", False, "READY_FIXTURE goldens"),
    # ---- Extensions: android views extras ----
    ("facebook/litho", "android-ui", "P3", "CANONICAL", False, "Async layout+draw yoga consumer"),
    ("chrisbanes/PhotoView", "android-ui,imageview", "P2", "CANONICAL", False, "Matrix zoom/hit semantics on ImageView"),
    # ---- Extensions: game loop ----
    ("hajimehoshi/ebiten", "game-engine,go", "P3", "CANONICAL", False, "Deterministic 2D game loop"),
    # ---- Extra: native android framework (frame submission) ----
    ("aosp-mirror/platform_frameworks_native", "android-framework,surfaceflinger", "P1", "MIRROR_OF:android.googlesource.com/platform/frameworks/native", False, "libgui/Surface/EGL frame submission laws"),
]

assert len(REPOS) == len(set(r[0] for r in REPOS)), "duplicate repo identities"
assert len(REPOS) == len(set(r[0].lower() for r in REPOS)), "duplicate repo identities (case)"
