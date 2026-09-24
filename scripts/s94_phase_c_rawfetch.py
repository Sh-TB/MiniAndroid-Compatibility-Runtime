#!/usr/bin/env python3
"""S94 Phase C-2: targeted raw fetches at provenance-pinned HEAD SHAs.

For repos too large to clone, fetch specific known files from
raw.githubusercontent.com at the EXACT SHA verified in Phase A, and record:
status, bytes, sha256, symbol line hits, plus curated law notes.

GOOGLSOURCE repos (minikin) are fetched from android.googlesource.com with
?format=TEXT (base64), which works unauthenticated.

Output: run/s94/source_mining/rawfetch_results.json
"""
import base64
import concurrent.futures as cf
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/z/my-project/run/s94/source_mining")
UA = {"User-Agent": "miniandroid-s94-miner/1.0"}

# repo -> {"law_note": ..., "files": [ {path, symbols, alts} ], "readme_only": bool}
TARGETS = {
    "google/skia": {
        "family_note": "2D rasterizer: clip stack, premul, codecs",
        "files": [
            {"path": "src/core/SkCanvas.cpp", "symbols": ["clipRect", "saveLayer", "onDrawRect"],
             "law": "L-S94-CLIP-2: SkCanvas holds an MCRec clip stack; clipRect intersects; saveLayer bounds the layer effect region"},
            {"path": "src/codec/SkPngCodec.cpp", "symbols": ["onGetPixels", "premultiply", "readRows"],
             "law": "L-S94-PNG-1: PNG decode applies premultiplication during swizzle; partial scanline decode states explicit"},
            {"path": "src/codec/SkGifCodec.cpp", "symbols": ["onGetPixels", "disposal"],
             "law": "L-S94-GIF-4: GIF codec frame decode with disposal-aware accumulation",
             "alts": ["third_party/libgifcodec/SkGifCodec.cpp"]},
        ],
    },
    "aosp-mirror/platform_frameworks_base": {
        "family_note": "Android view/canvas/bitmap/drawable/animation semantic laws",
        "files": [
            {"path": "graphics/java/android/graphics/BitmapFactory.java",
             "symbols": ["decodeResourceStream", "inScaled", "inDensity", "inSampleSize"],
             "law": "L-S94-DENSITY-1: bitmap density scaling is decided at decode time via inDensity/inTargetDensity; decodeResourceStream resolves density from Resources, not at draw time"},
            {"path": "graphics/java/android/graphics/Canvas.java",
             "symbols": ["clipRect", "saveLayer", "quickReject", "getSaveCount"],
             "law": "L-S94-CLIP-1: Canvas clip is a saved stack state; clipRect intersects with current clip; draws outside clip are discarded at raster time"},
            {"path": "graphics/java/android/view/View.java",
             "symbols": ["draw(Canvas", "onDraw(", "dispatchTouchEvent", "getHitRect", "setVisibility"],
             "law": "L-S94-DRAW-1: View.draw() orchestrates background->content->children->fade->scrollbars; invisible views never reach onDraw and never receive touch dispatch"},
            {"path": "core/java/android/view/SurfaceView.java",
             "symbols": ["updateSurface", "setZOrderMediaOverlay", "surfaceCreated", "mHaveSurface"],
             "law": "L-S94-SURFACE-1: SurfaceView content lives on a separate window layer behind/above; view drawing and surface frames are independent submission paths"},
            {"path": "core/java/android/view/ViewRootImpl.java",
             "symbols": ["performTraversals", "performMeasure", "performLayout", "performDraw"],
             "law": "L-S94-TREE-1: measure/layout/draw traversals are rooted in ViewRootImpl; a frame is only scheduled when dirty flags demand it"},
            {"path": "graphics/java/android/graphics/drawable/NinePatchDrawable.java",
             "symbols": ["draw(", "ninePatch", "getPadding", "onStateChange"],
             "law": "L-S94-NINEPATCH-1: NinePatchDrawable delegates patch scaling to NinePatch.draw with padding derived from patch guide pixels"},
            {"path": "graphics/java/android/graphics/drawable/AnimationDrawable.java",
             "symbols": ["selectDrawable", "setFrame", "run(", "scheduleSelf"],
             "law": "L-S94-ANIM-1: AnimationDrawable advances frames via scheduled self-messages with per-frame durations; frame index->drawable selection is selectDrawable"},
            {"path": "core/java/android/webkit/WebView.java",
             "symbols": ["postVisualStateCallback", "onDraw", "setWebContentsDebuggingEnabled"],
             "law": "L-S94-WEB-1: WebView visual readiness is a first-class callback (postVisualStateCallback), not implied by loadUrl or page finish",
             "alts": ["core/java/android/webkit/WebView.java"]},
        ],
    },
    "androidx/androidx": {
        "family_note": "Compose rendering pipeline (LayoutNode measure/layout/draw)",
        "files": [
            {"path": "compose/ui/ui/src/androidMain/kotlin/androidx/compose/ui/platform/AndroidComposeView.android.kt",
             "symbols": ["dispatchDraw", "CanvasHolder", "onMeasure"],
             "law": "L-S94-COMPOSE-1: Compose draws through AndroidComposeView.dispatchDraw into a CanvasOwner; composition existing does not imply a submitted frame"},
            {"path": "compose/ui/ui/src/commonMain/kotlin/androidx/compose/ui/node/LayoutNode.kt",
             "symbols": ["measure", "layout", "draw", "zIndex"],
             "law": "L-S94-COMPOSE-2: LayoutNode separates measure/layout/draw passes; nodes exist in composition before any pixel is drawn"},
        ],
    },
    "freetype/freetype": {
        "family_note": "Glyph rasterization laws",
        "files": [
            {"path": "src/base/ftobjs.c", "symbols": ["FT_Load_Glyph", "FT_Render_Glyph"],
             "law": "L-S94-GLYPH-2: glyph loading and rasterization are separate steps (FT_Load_Glyph -> FT_Render_Glyph); missing glyph yields .notdef"},
            {"path": "src/smooth/ftgrays.c", "symbols": ["gray_hline", "gray_convert_glyph"],
             "law": "L-S94-GLYPH-3: anti-aliased rasterization is coverage-based (aa scanline cells), not binary"},
        ],
    },
    "bumptech/glide": {
        "family_note": "Density/sample-size decode laws + tests",
        "files": [
            {"path": "library/src/main/java/com/bumptech/glide/load/resource/bitmap/Downsampler.java",
             "symbols": ["inSampleSize", "getRoundedSampleSize", "decodeStream", "inTargetDensity", "inScaled"],
             "law": "L-S94-DENSITY-2: target density scaling happens through BitmapFactory.Options inDensity/inTargetDensity pairs, sample size is power-of-2 rounding"},
            {"path": "library/src/test/java/com/bumptech/glide/load/resource/bitmap/DownsamplerTest.java",
             "symbols": ["downsample", "inSampleSize"],
             "law": "READY_TEST: density selection expectations exist upstream and can be ported as fixtures"},
        ],
    },
    "facebook/fresco": {
        "family_note": "Decode producer pipeline",
        "files": [
            {"path": "imagepipeline/src/main/java/com/facebook/imagepipeline/producers/DecodeProducer.java",
             "symbols": ["DecodeProducer", "onNewResult", "bitmapDecoder"],
             "law": "L-S94-PIPE-1: decode is a producer stage with progressive intermediate results; decode-only state is explicitly distinguishable from render"},
        ],
    },
    "coil-kt/coil": {
        "family_note": "Kotlin image loader decode boundary",
        "files": [
            {"path": "coil-base/src/main/java/coil/decode/BitmapFactoryDecoder.kt",
             "symbols": ["decode", "BitmapFactory", "inSampleSize"],
             "law": "L-S94-PIPE-2: decode returns ImageSource->Drawable result or throws DecodeException; size resolution is a separate DecodeUtils step",
             "alts": ["coil-core/src/commonMain/kotlin/coil3/decode/BitmapFactoryDecoder.kt",
                      "coil-core/src/androidMain/kotlin/coil3/decode/BitmapFactoryDecoder.android.kt"]},
        ],
    },
    "square/picasso": {
        "family_note": "Bitmap hunter fit/center-crop semantics",
        "files": [
            {"path": "src/main/java/com/squareup/picasso/BitmapHunter.java",
             "symbols": ["hunt", "calculateInSampleSize", "transform"],
             "law": "L-S94-FIT-1: fit()/centerCrop() transform applied AFTER decode with measured target dims; decode-only results are re-scaled to fit"},
        ],
    },
    "unicode-org/icu": {
        "family_note": "Bidi reference algorithms",
        "files": [
            {"path": "icu4c/source/common/ubidi.cpp", "symbols": ["ubidi_setPara", "getLevels"],
             "law": "L-S94-BIDI-1: paragraph level resolution precedes reordering; visual order is produced from logical via level maps"},
            {"path": "icu4j/main/classes/core/src/com/ibm/icu/text/Bidi.java", "symbols": ["setPara", "getVisualRun"],
             "law": "L-S94-BIDI-1b: Java-side identical contract (cross-language consistency evidence)"},
        ],
    },
    "google/brotli": {
        "family_note": "Compression decoder (asset path)",
        "files": [
            {"path": "c/dec/decode.c", "symbols": ["BrotliDecoderDecompressStream", "DecodeMetaBlockLength"],
             "law": "L-S94-CMP-1: streaming decode with explicit state machine; partial input is legal but not complete output"},
        ],
    },
    "chromium/chromium": {
        "family_note": "WebView draw/readiness implementation",
        "files": [
            {"path": "android_webview/java/src/org/chromium/android_webview/AwContents.java",
             "symbols": ["onDraw", "isReadyToDraw", "requestDraw", "didDraw"],
             "law": "L-S94-WEB-2: AwContents.onDraw only paints when compositor has content; readiness callbacks separate from page load finished",
             "alts": ["android_webview/java/src/org/chromium/android_webview/AwContents.java"]},
        ],
    },
    "WebKit/WebKit": {
        "family_note": "ImageLoader + test runner",
        "files": [
            {"path": "Source/WebCore/loader/ImageLoader.cpp", "symbols": ["updateFromElement", "notifyFinished"],
             "law": "L-S94-WEB-3: DOM image element existence is decoupled from decoded image availability; load events drive repaint"},
            {"path": "Tools/Scripts/run-webkit-tests", "symbols": ["expected", "diff"],
             "law": "READY_TEST: layout-test runner with expected/actual/diff semantics"},
        ],
    },
    "web-platform-tests/wpt": {
        "family_note": "Web conformance corpus (PORT_TEST)",
        "files": [
            {"path": "README.md", "symbols": ["web-platform-tests"],
             "law": "READY_TEST corpus: rendering-adjacent suites (css, html/canvas) provide expected/actual semantics"},
        ],
    },
    "electron/electron": {
        "family_note": "WebView embedding readiness",
        "files": [
            {"path": "docs/api/browser-window.md", "symbols": ["ready-to-show"],
             "law": "L-S94-WEB-4: 'ready-to-show' is the explicit first-paint readiness event for embedded web contents"},
            {"path": "docs/api/web-contents.md", "symbols": ["did-finish-load", "paint"],
             "law": "L-S94-WEB-4b: did-finish-load != painted (separate paint events)"},
        ],
    },
    "flutter/flutter": {
        "family_note": "Engine frame/text pipeline (post-merge location)",
        "files": [
            {"path": "engine/src/lib/ui/text/paragraph.cc", "symbols": ["Layout", "GetLineMetrics", "BreakText"],
             "law": "L-S94-TEXT-1: text layout is multi-stage (shaping, breaking, painting); line metrics are first-class outputs",
             "alts": ["engine/src/lib/ui/text/paragraph.cc"]},
            {"path": "engine/src/shell/platform/android/io/flutter/embedding/android/FlutterView.java",
             "symbols": ["dispatchDraw", "FlutterRenderer", "onSizeChanged"],
             "law": "L-S94-SURFACE-2: FlutterView forwards frames from a RenderSurface; view invalidation and frame arrival are distinct",
             "alts": ["engine/src/shell/platform/android/io/flutter/embedding/android/FlutterView.java"]},
        ],
    },
    "libgdx/libgdx": {
        "family_note": "Android backend frame lifecycle (S94 directive emphasis)",
        "files": [
            {"path": "backends/gdx-backend-android/src/com/badlogic/gdx/backends/android/AndroidGraphics.java",
             "symbols": ["onDrawFrame", "surfaceChanged", "resume(", "pause(", "render("],
             "law": "L-S94-SURFACE-3: GLSurfaceView.Renderer.onDrawFrame is the frame submission point; surface lifecycle callbacks gate render loop start/stop"},
        ],
    },
    "godotengine/godot": {
        "family_note": "Deterministic frame loop",
        "files": [
            {"path": "main/main.cpp", "symbols": ["iteration", "Main::setup", "display"],
             "law": "L-S94-FRAME-1: fixed-step iteration loop separates physics/render ticks; frame advance is explicit"},
        ],
    },
    "libsdl-org/SDL": {
        "family_note": "Surface/window framebuffer abstraction",
        "files": [
            {"path": "src/video/SDL_video.c", "symbols": ["SDL_CreateWindowFramebuffer", "SDL_UpdateWindowSurface"],
             "law": "L-S94-SURFACE-4: window framebuffer create/update/present are explicit distinct calls"},
        ],
    },
    "material-components/material-components-android": {
        "family_note": "Ripple/material drawable laws",
        "files": [
            {"path": "lib/java/com/google/android/material/ripple/RippleUtils.java",
             "symbols": ["sanitizeRippleDrawableColor", "RippleDrawable"],
             "law": "L-S94-RIPPLE-1: ripple color sanitization and state sets defined centrally; ripple is a state-driven drawable"},
        ],
    },
    "androidx/constraintlayout": {
        "family_note": "Constraint solving layout",
        "files": [
            {"path": "constraintlayout/constraintlayout/src/main/java/androidx/constraintlayout/widget/ConstraintLayout.java",
             "symbols": ["onMeasure", "onLayout", "measureChildren"],
             "law": "L-S94-LAYOUT-1: constraint solver produces measure results then layout pass; solver output must match placed bounds"},
        ],
    },
    "JetBrains/skiko": {
        "family_note": "Skia bindings frame/redraw",
        "files": [
            {"path": "skiko/src/commonMain/kotlin/org/jetbrains/skiko/SkiaLayer.kt",
             "symbols": ["drawScene", "needRedraw", "onRender"],
             "law": "L-S94-COMPOSE-3: skia layer redraw is explicitly scheduled (needRedraw); frame submission tied to onRender callback",
             "alts": ["skiko/src/commonMain/kotlin/org/jetbrains/skiko/SkiaLayer.kt"]},
        ],
    },
    "JetBrains/compose-multiplatform-core": {
        "family_note": "JB fork of androidx compose (delta evidence)",
        "files": [
            {"path": "compose/ui/ui/src/androidMain/kotlin/androidx/compose/ui/platform/AndroidComposeView.android.kt",
             "symbols": ["dispatchDraw"],
             "law": "FORK evidence: JB carries androidx pipeline with patches; canonical remains androidx/androidx",
             "alts": ["compose/ui/ui/src/androidMain/kotlin/androidx/compose/ui/platform/AndroidComposeView.android.kt"]},
        ],
    },
    "LineageOS/android_frameworks_native": {
        "family_note": "SurfaceFlinger frame composition (AOSP native stand-in)",
        "files": [
            {"path": "services/surfaceflinger/SurfaceFlinger.cpp",
             "symbols": ["commit", "composite", "onMessageReceived"],
             "law": "L-S94-SURFACE-5: committed layers are composited into a presented frame; buffer availability gates frame submission"},
        ],
    },
    "googlefonts/fonttools": {
        "family_note": "Font introspection oracle",
        "files": [
            {"path": "Lib/fontTools/ttLib/ttFont.py", "symbols": ["TTFont", "getGlyphSet"],
             "law": "READY_TEST oracle: glyph coverage/metrics checks for font-resolution laws"},
        ],
    },
    "googlefonts/noto-emoji": {
        "family_note": "Emoji font + build/flag reference images",
        "files": [
            {"path": "png/emoji_u1f600.png", "symbols": [],
             "law": "READY_REFERENCE_IMAGE: canonical emoji raster for glyph-rendering fixtures"},
        ],
    },
    "python-pillow/Pillow": {
        "family_note": "GIF disposal semantics + tests",
        "files": [
            {"path": "src/PIL/GifImagePlugin.py", "symbols": ["disposal", "_seek", "frame"],
             "law": "L-S94-GIF-1: disposal methods (0/1/2/3) defined with explicit restore-to-background semantics in _seek"},
            {"path": "Tests/test_file_gif.py", "symbols": ["disposal"],
             "law": "READY_TEST: GIF disposal/offset test expectations"},
        ],
    },
    "golang/go": {
        "family_note": "image/gif reference decoder + tests",
        "files": [
            {"path": "src/image/gif/reader.go", "symbols": ["disposal", "readFrame", "decode"],
             "law": "L-S94-GIF-2: block-based GIF decode with disposal field propagation per frame"},
            {"path": "src/image/gif/reader_test.go", "symbols": ["disposal", "delay"],
             "law": "READY_TEST: gif golden tests incl. disposal"},
        ],
    },
    "nothings/stb": {
        "family_note": "stb_image decode contract",
        "files": [
            {"path": "stb_image.h", "symbols": ["stbi_load", "stbi_info", "stbi__convert_format"],
             "law": "L-S94-DECODE-1: decode returns component-forced outputs; info() separates metadata from full decode"},
        ],
    },
    "FFmpeg/FFmpeg": {
        "family_note": "GIF/APNG demux+decode reference",
        "files": [
            {"path": "libavcodec/gifdec.c", "symbols": ["gif_read_image", "disposal_method"],
             "law": "L-S94-GIF-3: frame rect + disposal parsed per frame; transparency index handled explicitly"},
        ],
    },
    "ImageMagick/ImageMagick": {
        "family_note": "Toolkit text/image ops",
        "files": [
            {"path": "MagickCore/annotate.c", "symbols": ["AnnotateImage", "RenderType"],
             "law": "L-S94-TEXT-2: text annotation resolves font metrics then renders per-type; missing font falls through explicit path"},
        ],
    },
    "mozilla/mozjpeg": {
        "family_note": "JPEG decode scanline contract",
        "files": [
            {"path": "jdapistd.c", "symbols": ["jpeg_read_scanlines"],
             "law": "L-S94-DECODE-2: scanline-oriented decode; partial decode states observable"},
        ],
    },
    "googleprojectzero/SkCodecFuzzer": {
        "family_note": "Codec fuzz harness",
        "files": [
            {"path": "README.md", "symbols": ["SkCodec"],
             "law": "READY_FUZZER: fuzz entry for codec robustness porting"},
        ],
    },
    "cocos2d/cocos2d-x": {
        "family_note": "Engine main loop drawScene",
        "files": [
            {"path": "cocos2d/CCDirector.cpp", "symbols": ["drawScene", "mainLoop"],
             "law": "L-S94-FRAME-2: drawScene per frame: clear -> visit(scene) -> swap buffers; animation advance tied to delta"},
        ],
    },
    "floooh/sokol": {
        "family_note": "Minimal gfx frame contract",
        "files": [
            {"path": "sokol_gfx.h", "symbols": ["sg_begin_pass", "sg_end_pass", "sg_commit"],
             "law": "L-S94-FRAME-3: begin_pass/end_pass/commit frame contract; pass without commit never presents"},
        ],
    },
    "bkaradzic/bgfx": {
        "family_note": "Multi-backend frame API",
        "files": [
            {"path": "src/bgfx.cpp", "symbols": ["bgfx::frame", "submit"],
             "law": "L-S94-FRAME-4: frame() pumps the renderer; view submits accumulate until frame boundary"},
        ],
    },
    "google/filament": {
        "family_note": "PBR engine frame lifecycle",
        "files": [
            {"path": "filament/src/Renderer.cpp", "symbols": ["beginFrame", "render", "endFrame"],
             "law": "L-S94-FRAME-5: beginFrame/render/endFrame triple defines submission; swapchain is explicit"},
        ],
    },
    "servo/servo": {
        "family_note": "Compositor frame output",
        "files": [
            {"path": "components/compositing/compositor.rs", "symbols": ["composite", "send_buffers"],
             "law": "L-S94-WEB-5: layout output -> compositor buffers -> presented frame; DOM existence insufficient"},
        ],
    },
    "libass/libass": {
        "family_note": "HarfBuzz+FreeType text rendering consumer",
        "files": [
            {"path": "libass/ass_render.c", "symbols": ["render_event", "glyph", "ass_shaper"],
             "law": "L-S94-TEXT-3: shaping then glyph render pipeline with explicit font fallback chain"},
        ],
    },
    "ocornut/imgui": {
        "family_note": "Font atlas baking",
        "files": [
            {"path": "imgui.cpp", "symbols": ["CalcTextSize", "ImFontAtlas", "AddGlyph"],
             "law": "L-S94-GLYPH-1: glyphs rasterized into atlas; text measurement from atlas metrics; missing glyphs replaced explicitly"},
        ],
    },
    "tesseract-ocr/tesseract": {
        "family_note": "OCR as text-readability oracle",
        "files": [
            {"path": "src/api/baseapi.cpp", "symbols": ["Recognize", "GetUTF8Text"],
             "law": "READY_TEST oracle: independent OCR pass can verify rendered text readability (UNREADABLE_TEXT cross-check)"},
        ],
    },
    "KhronosGroup/WebGL": {
        "family_note": "WebGL conformance suite",
        "files": [
            {"path": "README.md", "symbols": ["conformance"],
             "law": "READY_TEST: conformance suites as GLES behavior contract"},
        ],
    },
    "urho3d/urho3d": {
        "family_note": "Engine renderer",
        "files": [
            {"path": "Source/Urho3D/Graphics/Renderer.cpp", "symbols": ["Render", "Update"],
             "law": "L-S94-FRAME-6: view update vs render separation",
             "alts": ["Source/Urho3D/Graphics/Renderer.cpp"]},
        ],
    },
    "axmolengine/axmol": {
        "family_note": "Cocos fork active engine",
        "files": [
            {"path": "cocos/CCDirector.cpp", "symbols": ["drawScene", "mainLoop"],
             "law": "L-S94-FRAME-2b: same drawScene contract (fork continuity)",
             "alts": ["cocos/2d/CCDirector.cpp", "cocos/platform/CCDirector.cpp"]},
        ],
    },
    "defold/defold": {
        "family_note": "Engine render script frame",
        "files": [
            {"path": "engine/render/src/render.cpp", "symbols": ["RenderRenderScript", "RenderListDispatch"],
             "law": "L-S94-FRAME-7: render script dispatch builds render list then dispatches to renderer",
             "alts": ["engine/render/src/render.cpp"]},
        ],
    },
    "korlibs/korge": {
        "family_note": "Kotlin multiplatform engine",
        "files": [
            {"path": "korge/src/korlibs/korge/view/Views.kt", "symbols": ["render", "update"],
             "law": "L-S94-FRAME-8: Views loop: update -> render each frame",
             "alts": ["korge/src/korlibs/korge/view/Views.kt"]},
        ],
    },
    "maplibre/maplibre-gl-native": {
        "family_note": "Glyph atlas + texture pipeline",
        "files": [
            {"path": "src/mbgl/text/glyph_atlas.cpp", "symbols": ["addGlyphs", "texture"],
             "law": "L-S94-GLYPH-4: glyph rasters uploaded to atlas texture; explicit rect allocation per glyph",
             "alts": ["src/mbgl/text/glyph_atlas.cpp"]},
        ],
    },
    "puppeteer/puppeteer": {
        "family_note": "Headless screenshot readiness",
        "files": [
            {"path": "README.md", "symbols": ["screenshot"],
             "law": "READY_TEST harness: networkidle/waitFor semantics for web visual readiness"},
        ],
    },
    "reandroid/ARSCLib": {
        "family_note": "ARSC parse/build oracle",
        "files": [
            {"path": "README.md", "symbols": ["ARSC"],
             "law": "READY_TEST oracle for resource-table resolution laws"},
        ],
    },
    "androguard/androguard": {
        "family_note": "AXML/ARSC oracle (named in DO_NOT_REINVENT)",
        "files": [
            {"path": "README.md", "symbols": ["AXML"],
             "law": "READY_TEST oracle for AXML/ARSC diffs"},
        ],
    },
    "mesa3d/mesa": {
        "family_note": "OFF_GITHUB (gitlab.freedesktop.org) CPU raster reference",
        "files": [],
        "readme_only": True,
    },
    "cairo/cairo": {
        "family_note": "OFF_GITHUB compositing model reference",
        "files": [],
        "readme_only": True,
    },
    "google/minikin": {
        "family_note": "OFF_GITHUB (googlesource) Android text layout",
        "files": [
            {"path": "libs/minikin/Layout.cpp", "symbols": ["doLayout", "layoutLine", "MinikinPaint"],
             "law": "L-S94-TEXT-4: Minikin layout: font collection fallback per codepoint; shaping via HarfBuzz; measured advances drive layout",
             "googlesource": "platform/frameworks/minikin"},
        ],
    },
    "android/graphics": {
        "family_note": "UNVERIFIED identity from directive - no fetch",
        "files": [],
        "readme_only": False,
    },
    "google/android-codelabs": {
        "family_note": "UNVERIFIED identity from directive - no fetch",
        "files": [],
        "readme_only": False,
    },
    "android/platform_frameworks_support": {
        "family_note": "UNVERIFIED identity from directive - no fetch",
        "files": [],
        "readme_only": False,
    },
    "facebook/shimmer-android": {
        "family_note": "Shimmer drawable (verify live identity of archived seed entry)",
        "files": [
            {"path": "shimmer/src/main/java/com/facebook/shimmer/ShimmerFrameLayout.java",
             "symbols": ["onDraw", "ShimmerDrawable"],
             "law": "L-S94-ANIM-2: shimmer draws gradient mask derived from animation fraction; draw with alpha only",
             "alts": ["shimmer/src/main/java/com/facebook/shimmer/ShimmerFrameLayout.java"]},
        ],
    },
}


def fetch_raw(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def locate_symbols(text, symbols):
    lines = text.splitlines()
    hits = {}
    for sym in symbols:
        idxs = [i + 1 for i, l in enumerate(lines) if sym in l][:10]
        if idxs:
            hits[sym] = idxs
    return hits


def mine_repo(repo, spec, recs_by_repo):
    rec = recs_by_repo.get(repo, {})
    out = {"repository": repo, "family_note": spec.get("family_note", ""), "files": []}
    for f in spec.get("files", []):
        attempts = [f["path"]] + [a for a in f.get("alts", []) if a != f["path"]]
        got = None
        used = None
        for a in attempts:
            if f.get("googlesource"):
                gs = f["googlesource"]
                for branch in ("main", "master"):
                    url = f"https://android.googlesource.com/{gs}/+/refs/heads/{branch}/{a}?format=TEXT"
                    data = fetch_raw(url)
                    if data:
                        got = base64.b64decode(data)
                        used = f"googlesource:{gs}@{branch}:{a}"
                        break
                if got:
                    break
            else:
                sha = rec.get("head_sha")
                if not sha:
                    break
                url = f"https://raw.githubusercontent.com/{repo}/{sha}/{a}"
                data = fetch_raw(url)
                if data:
                    got, used = data, f"{repo}@{sha[:12]}:{a}"
                    break
        entry = {"path": f["path"], "law": f.get("law", ""), "symbols": f.get("symbols", [])}
        if got is None:
            entry.update({"status": "NOT_FOUND", "attempts": attempts})
        else:
            text = got.decode("utf-8", "replace")
            entry.update({
                "status": "OK", "fetch_source": used, "bytes": len(got),
                "sha256": hashlib.sha256(got).hexdigest(),
                "symbol_line_hits": locate_symbols(text, f.get("symbols", [])),
                "head_excerpt": text[:240].strip().replace("\n", " | ")[:240],
            })
        out["files"].append(entry)
    if spec.get("readme_only") and not out["files"]:
        sha = rec.get("head_sha")
        data = fetch_raw(f"https://raw.githubusercontent.com/{repo}/{sha}/README.md") if sha else None
        if data:
            out["readme"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                             "head_excerpt": data.decode("utf-8", "replace")[:240].strip()}
        else:
            out["readme"] = {"status": "NOT_FOUND"}
    return out


def main():
    repos_doc = json.loads((BASE / "repositories.json").read_text())
    recs_by_repo = {r["repository"]: r for r in repos_doc["repositories"]}
    results = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(mine_repo, repo, spec, recs_by_repo): repo
                for repo, spec in TARGETS.items()}
        for fut in cf.as_completed(futs):
            r = fut.result()
            results.append(r)
            ok = sum(1 for f in r["files"] if f.get("status") == "OK")
            print(f"  {r['repository']:44s} files_ok={ok}/{len(r['files'])}", flush=True)
    results.sort(key=lambda r: r["repository"])
    doc = {"generated_at": datetime.now(timezone.utc).isoformat(),
           "fetch_method": "raw.githubusercontent.com at Phase-A pinned HEAD SHA; googlesource ?format=TEXT for minikin",
           "results": results}
    (BASE / "rawfetch_results.json").write_text(json.dumps(doc, indent=1))
    ok = sum(1 for r in results for f in r["files"] if f.get("status") == "OK")
    nf = sum(1 for r in results for f in r["files"] if f.get("status") == "NOT_FOUND")
    print(f"DONE fetched_ok={ok} not_found={nf}")


if __name__ == "__main__":
    main()
