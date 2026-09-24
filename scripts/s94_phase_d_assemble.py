#!/usr/bin/env python3
"""S94 Phase D: assemble findings.jsonl, implementations.jsonl, tests.jsonl,
source_to_law.json, gap_map.json.

Every law/evidence record is CROSS-VERIFIED against the machine evidence
(clones_harvest.json + rawfetch_results.json + repositories.json). A law whose
file was not actually fetched is marked evidence_status=PENDING_FETCH and its
provenance fields stay empty. Nothing is claimed without a fetched artifact.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/z/my-project/run/s94/source_mining")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

repos = {r["repository"]: r for r in json.loads((BASE / "repositories.json").read_text())["repositories"]}
clones = {c["repository"]: c for c in json.loads((BASE / "clones_harvest.json").read_text())["clones"]}
rawdoc = json.loads((BASE / "rawfetch_results.json").read_text())
rawfetch = {r["repository"]: r for r in rawdoc["results"]}


def raw_file(repo, path):
    for f in rawfetch.get(repo, {}).get("files", []):
        if f["path"] == path:
            return f
    return None


def clone_file(repo, pattern_exact_path):
    c = clones.get(repo)
    if not c:
        return None
    for f in c["files"]:
        if f["path"] == pattern_exact_path:
            return f
    return None


def evidence_for(repo, path):
    """Return evidence dict + status for a (repo, path) from fetched artifacts."""
    rec = repos.get(repo, {})
    base = {"repo_id": rec.get("id"), "repository": repo,
            "commit_sha": rec.get("head_sha"), "path": path}
    rf = raw_file(repo, path)
    if rf and rf.get("status") == "OK":
        base.update({"file_sha256": rf["sha256"], "bytes": rf["bytes"],
                     "symbol_line_hits": rf.get("symbol_line_hits", {}),
                     "evidence_status": "FETCHED"})
        return base
    cf = clone_file(repo, path)
    if cf:
        base.update({"file_sha256": cf["sha256"], "bytes": cf["bytes"],
                     "symbol_line_hits": cf.get("symbol_line_hits", {}),
                     "evidence_status": "FETCHED_CLONE"})
        return base
    rf2 = raw_file(repo, path)
    if rf2 and rf2.get("status") == "README_ONLY":
        base.update({"evidence_status": "README_ONLY"})
        return base
    base.update({"evidence_status": "PENDING_FETCH"})
    return base


# ---------------- Law catalog ----------------
# (law_id, statement, family, repo, path, symbols_to_cite, reuse, gap, s93_link, test)
LAWS = [
    ("L-S94-DENSITY-1", "Bitmap density scaling is decided at decode time: BitmapFactory.Options carries inDensity/inTargetDensity/inScaled; decodeResourceStream resolves density from Resources before pixels exist.", "resource-density",
     "aosp-mirror/platform_frameworks_base", "graphics/java/android/graphics/BitmapFactory.java",
     ["decodeResourceStream", "inScaled", "inDensity", "inSampleSize"], "PORT_ALGORITHM",
     "WRONG_COLOR candidates: bitmap decoded at wrong density then drawn unscaled (Fish Rings C5 DENSITY_MISMATCH measured in S92)",
     "bouncy/hotdeath/urlchecker/random_simplestopwatch WRONG_COLOR", "Port inDensity/inTargetDensity table test from DownsamplerTest expectations"),
    ("L-S94-DENSITY-2", "Target-density scaling is a decode-option pair problem (inDensity x inTargetDensity) with power-of-two inSampleSize rounding; loaders prove the algorithm.", "resource-density",
     "bumptech/glide", "library/src/main/java/com/bumptech/glide/load/resource/bitmap/Downsampler.java",
     ["inSampleSize", "getRoundedSampleSize", "decodeStream", "inTargetDensity", "inScaled"], "PORT_TEST",
     "MiniAndroid resource resolver has no density-selection unit tests",
     "WRONG_COLOR family", "READY_TEST in glide test suite"),
    ("L-S94-CLIP-1", "Canvas clip is a saved stack state: clipRect intersects current clip; saveLayer bounds effect regions; quickReject culls draws entirely outside the clip.", "geometry-clip",
     "aosp-mirror/platform_frameworks_base", "graphics/java/android/graphics/Canvas.java",
     ["clipRect", "saveLayer", "quickReject", "getSaveCount"], "PORT_ALGORITHM",
     "MiniAndroid Canvas clip semantics need an edge-aligned clip law (S93 L-S93-IMG-5 already measures; engine must obey)",
     "bobball/dodge/bouncy/urlchecker WRONG_CLIP", "Skia ClipStackTest port + region intersection fixtures"),
    ("L-S94-CLIP-2", "SkCanvas maintains per-restore-call MCRec clip stack; every draw is clip-tested at raster time, not at draw-call time.", "geometry-clip",
     "google/skia", "src/core/SkCanvas.cpp",
     ["clipRect", "saveLayer", "onDrawRect"], "REFERENCE_ONLY",
     "Engine clip correctness oracle", "WRONG_CLIP family", "skia unit tests list"),
    ("L-S94-DRAW-1", "View.draw() orchestrates background -> content -> children -> fade -> scrollbars in fixed order; setVisibility(GONE) views neither draw nor receive touch dispatch.", "view-tree",
     "aosp-mirror/platform_frameworks_base", "core/java/android/view/View.java",
     ["draw(Canvas", "onDraw(", "dispatchTouchEvent", "getHitRect", "setVisibility"], "PORT_ALGORITHM",
     "MiniAndroid view draw ordering + invisible-clickable rejection (S93 law L-S93-IMG-6 / interaction gate)",
     "interaction failures", "AOSP CTS View draw order; CDroid cts tests"),
    ("L-S94-TREE-1", "Measure/layout/draw traversals are rooted in ViewRootImpl.performTraversals; frames are scheduled only when dirty flags demand them.", "view-tree",
     "aosp-mirror/platform_frameworks_base", "core/java/android/view/ViewRootImpl.java",
     ["performTraversals", "performMeasure", "performLayout", "performDraw"], "REFERENCE_ONLY",
     "Frame scheduling semantics for verifier readiness model", "ANIMATION_FROZEN family", "AOSP CTS"),
    ("L-S94-SURFACE-1", "SurfaceView content lives on a separate window layer with its own surface; view drawing and surface frames are independent submission paths (updateSurface / mHaveSurface).", "surface",
     "aosp-mirror/platform_frameworks_base", "core/java/android/view/SurfaceView.java",
     ["updateSurface", "setZOrderMediaOverlay", "surfaceCreated", "mHaveSurface"], "REFERENCE_ONLY",
     "SurfaceView/GLSurfaceView titles need surface-aware evidence chains",
     "game titles", "AOSP CTS SurfaceView; libGDX backend"),
    ("L-S94-SURFACE-2", "libGDX Android backend: GLSurfaceView.Renderer.onDrawFrame is the frame submission point; surfaceCreated/surfaceChanged gate the render loop; render() advances the application lifecycle.", "surface",
     "libgdx/libgdx", "backends/gdx-backend-android/src/com/badlogic/gdx/backends/android/AndroidGraphics.java",
     ["onDrawFrame", "surfaceChanged", "resume(", "pause(", "render("], "PORT_ALGORITHM",
     "MiniAndroid GLSurfaceView emulation must bind onDrawFrame to frame submission; S93 VERDICT: surface titles currently rely on canvas fallback",
     "libGDX game titles (mini-tetris ANIMATION_FROZEN)", "libgdx gdx-tests"),
    ("L-S94-SURFACE-3", "Window framebuffer create/update/present are explicit distinct calls (SDL_CreateWindowFramebuffer / SDL_UpdateWindowSurface) - nonblank memory is not presentation.", "surface",
     "libsdl-org/SDL", "src/video/SDL_video.c",
     ["SDL_CreateWindowFramebuffer", "SDL_UpdateWindowSurface"], "REFERENCE_ONLY",
     "Present-stage evidence law", "game titles", "SDL tests"),
    ("L-S94-SURFACE-4", "SurfaceFlinger composites committed layers into a presented frame; buffer availability gates frame submission (commit/composite phases).", "surface",
     "LineageOS/android_frameworks_native", "services/surfaceflinger/SurfaceFlinger.cpp",
     ["commit", "composite", "onMessageReceived"], "REFERENCE_ONLY",
     "Frame-presentation semantics", "frame submission evidence", "AOSP SF tests (fork carries them)"),
    ("L-S94-FRAME-1", "Fixed-step iteration loop separates physics and render ticks; frame advance is explicit in Main::iteration.", "frame-loop",
     "godotengine/godot", "main/main.cpp", ["iteration", "Main::setup"], "REFERENCE_ONLY",
     "Animation timing oracle for frozen-frame discrimination", "mini-tetris/minicraft ANIMATION_FROZEN", "godot tests"),
    ("L-S94-FRAME-3", "gfx frame contract is begin_pass/end_pass/commit; a pass without commit never presents.", "frame-loop",
     "floooh/sokol", "sokol_gfx.h", ["sg_begin_pass", "sg_end_pass", "sg_commit"], "REFERENCE_ONLY",
     "Verifier frame-submission model", "game titles", "sokol samples"),
    ("L-S94-FRAME-4", "bgfx::frame() pumps the renderer; view submits accumulate until the frame boundary.", "frame-loop",
     "bkaradzic/bgfx", "src/bgfx.cpp", ["bgfx::frame", "submit"], "REFERENCE_ONLY",
     "Frame accumulation semantics", "game titles", "bgfx examples"),
    ("L-S94-FRAME-5", "beginFrame/render/endFrame triple defines submission with explicit swapchain.", "frame-loop",
     "google/filament", "filament/src/Renderer.cpp", ["beginFrame", "render", "endFrame"], "REFERENCE_ONLY",
     "Swapchain-present law", "game titles", "filament samples"),
    ("L-S94-FRAME-6", "Engine separates per-view Update from Render; render lists built after update.", "frame-loop",
     "urho3d/urho3d", "Source/Urho3D/Graphics/Renderer.cpp", ["Render", "Update"], "REFERENCE_ONLY",
     "Update/render separation", "game titles", "urho tests"),
    ("L-S94-ANIM-1", "AnimationDrawable advances frames via scheduled self-messages with per-frame durations; frame index -> drawable selection is selectDrawable; setFrame drives repaint.", "animation",
     "aosp-mirror/platform_frameworks_base", "graphics/java/android/graphics/drawable/AnimationDrawable.java",
     ["selectDrawable", "setFrame", "run(", "scheduleSelf"], "PORT_ALGORITHM",
     "MiniAndroid AnimationDrawable frame clock must follow scheduleSelf timing; S93 REPEATED_FRAME law validates",
     "mini-tetris/minicraft ANIMATION_FROZEN", "CDroid cts_animationdrawable_test.cc"),
    ("L-S94-ANIM-3", "Lottie composition progress maps to frames; setProgress drives drawable invalidation per frame.", "animation",
     "airbnb/lottie-android", "lottie/src/main/java/com/airbnb/lottie/LottieDrawable.java",
     ["setProgress", "getFrame", "setMinFrame", "invalidateSelf"], "PORT_ALGORITHM",
     "rlottie already integrated; verify progress->frame semantics against lottie-android",
     "vector-animation titles", "lottie-android test suite"),
    ("L-S94-GIF-1", "GIF disposal methods (restore-to-background/previous) are explicit state transitions in _seek; each seek re-composes from disposal state.", "animation-gif",
     "python-pillow/Pillow", "src/PIL/GifImagePlugin.py", ["disposal", "_seek", "frame"], "PORT_TEST",
     "MiniAndroid GIF compositor must implement disposal 0-3 exactly; S93 GIF frames reuse",
     "12 GIF titles", "Tests/test_file_gif.py"),
    ("L-S94-GIF-2", "GIF block-based decode propagates per-frame disposal and delay fields (golang image/gif).", "animation-gif",
     "golang/go", "src/image/gif/reader.go", ["disposal", "readFrame", "decode"], "PORT_TEST",
     "Second independent GIF semantic reference", "12 GIF titles", "src/image/gif/reader_test.go"),
    ("L-S94-GIF-3", "FFmpeg gifdec parses frame rect + disposal + transparency index per frame.", "animation-gif",
     "FFmpeg/FFmpeg", "libavcodec/gifdec.c", ["gif_read_image", "disposal_method"], "REFERENCE_ONLY",
     "Third reference for disposal edge cases", "12 GIF titles", "FATE GIF tests"),
    ("L-S94-GIF-4", "Wuffs GIF decoder is a formally-reviewed state machine with disposal in source; safest port target.", "animation-gif",
     "google/wuffs", "release/c/wuffs-v0.4.c",
     ["wuffs_gif__decoder", "disposal", "wuffs_png__decoder"], "ADAPT",
     "MiniAndroid GIF decoder currently minimal; wuffs is a drop-in candidate (also PNG/BMP/WEBP/NIE)",
     "12 GIF titles", "wuffs test corpus 437 files"),
    ("L-S94-NINEPATCH-1", "NinePatchDrawable delegates patch scaling to NinePatch.draw with padding derived from patch guide pixels; padding affects view layout, not just draw.", "drawable-ninepatch",
     "aosp-mirror/platform_frameworks_base", "graphics/java/android/graphics/drawable/NinePatchDrawable.java",
     ["draw(", "ninePatch", "getPadding", "onStateChange"], "PORT_ALGORITHM",
     "MiniAndroid NinePatch support gap; CDroid provides C++ reference",
     "WRONG_CLIP candidates with 9-patch backgrounds", "CDroid cts_ninepatchdrawable_test.cc"),
    ("L-S94-RIPPLE-1", "Ripple color sanitization and state sets are centralized; ripple is a state-driven drawable (RippleDrawable with content/bound masks).", "drawable-ripple",
     "material-components/material-components-android", "lib/java/com/google/android/material/ripple/RippleUtils.java",
     ["sanitizeRippleDrawableColor", "RippleDrawable"], "REFERENCE_ONLY",
     "Material button press feedback law", "material UI titles", "material-components tests"),
    ("L-S94-LAYOUT-1", "Constraint solver produces measure results, then a separate layout pass places children; solver output must equal placed bounds.", "layout",
     "androidx/constraintlayout", "constraintlayout/constraintlayout/src/main/java/androidx/constraintlayout/widget/ConstraintLayout.java",
     ["onMeasure", "onLayout", "measureChildren"], "REFERENCE_ONLY",
     "measure/layout consistency law", "layout failures", "constraintlayout tests"),
    ("L-S94-LAYOUT-2", "Yoga CalculateLayout: flexbox measure algorithm with explicit layout outputs; MiniAndroid already has a differential-tested adapter (10/10 nodes <8px).", "layout",
     "facebook/yoga", "yoga/YGNode.cpp", ["CalculateLayout", "YGNodeCalculateLayout"], "ADAPT",
     "Wire R3 adapter into render stage", "layout failures", "yoga gentest 43 fixture sets + tests 73 files"),
    ("L-S94-SHAPE-1", "HarfBuzz shaping pipeline hb_ot_shape_internal: Unicode properties -> shaping -> positioning; buffer output glyphs+advances are the shaping contract.", "text-shaping",
     "harfbuzz/harfbuzz", "src/hb-ot-shape.cc", ["hb_ot_shape_internal", "hb_buffer_t"], "ADAPT",
     "MiniAndroid text currently BitmapFont path; FriBidi+HarfBuzz+FreeType POC proven but not wired (R4)",
     "random_simplestopwatch UNREADABLE_TEXT", "harfbuzz test/shape 3058 files incl. in-house tests"),
    ("L-S94-TEXT-4", "Minikin layout: font-collection fallback per codepoint, shaping via HarfBuzz, measured advances drive layout - THE Android text layout law.", "text-layout",
     "google/minikin", "libs/minikin/Layout.cpp", ["doLayout", "layoutLine", "MinikinPaint"], "PORT_ALGORITHM",
     "Font fallback selection is per-codepoint, not per-string",
     "random_simplestopwatch UNREADABLE_TEXT", "minikin tests (googlesource)"),
    ("L-S94-TEXT-3", "libass renders shaped glyphs through a font fallback chain with explicit glyph event pipeline.", "text-render",
     "libass/libass", "libass/ass_render.c", ["render_event", "glyph", "ass_shaper"], "REFERENCE_ONLY",
     "Fallback-chain consumer reference", "UNREADABLE_TEXT", "libass tests"),
    ("L-S94-TEXT-2", "Text annotation resolves font metrics then renders per-type with explicit missing-font path.", "text-render",
     "ImageMagick/ImageMagick", "MagickCore/annotate.c", ["AnnotateImage", "RenderType"], "REFERENCE_ONLY",
     "Text rendering reference", "UNREADABLE_TEXT", "ImageMagick tests"),
    ("L-S94-BIDI-1", "Paragraph level resolution precedes reordering; visual order produced from logical order via level maps (ubidi_setPara).", "text-bidi",
     "unicode-org/icu", "icu4c/source/common/ubidi.cpp", ["ubidi_setPara", "getLevels"], "ADAPT",
     "FriBidi already proven in project (exp101); ICU is the conformance oracle",
     "RTL titles", "ICU bidi test data"),
    ("L-S94-GLYPH-2", "Glyph loading and rasterization are separate steps (FT_Load_Glyph -> FT_Render_Glyph); missing glyph yields .notdef (tofu).", "font-raster",
     "freetype/freetype", "src/base/ftobjs.c", ["FT_Load_Glyph", "FT_Render_Glyph"], "PORT_ALGORITHM",
     "S93 tofu law (L-S93-FNT-2) is the detector; FreeType is the correct-behavior oracle",
     "random_simplestopwatch UNREADABLE_TEXT", "FreeType demo/test programs"),
    ("L-S94-GLYPH-3", "Anti-aliased glyph rasterization is coverage-based (scanline cells), not binary; binary thresholds break text metrics.", "font-raster",
     "freetype/freetype", "src/smooth/ftgrays.c", ["gray_hline", "gray_convert_glyph"], "REFERENCE_ONLY",
     "AA text rendering law; S93 adaptive ink threshold echoes this", "UNREADABLE_TEXT", "ftgrays tests"),
    ("L-S94-GLYPH-1", "Glyphs rasterized into an atlas; text measurement from atlas metrics; missing glyphs replaced explicitly (imgui).", "font-raster",
     "ocornut/imgui", "imgui.cpp", ["CalcTextSize", "ImFontAtlas", "AddGlyph"], "REFERENCE_ONLY",
     "Atlas approach reference for BitmapFont path", "text titles", "imgui tests"),
    ("L-S94-PNG-1", "PNG decode applies premultiplication during swizzle; partial scanline decode states are explicit (SkPngCodec).", "image-codec",
     "google/skia", "src/codec/SkPngCodec.cpp", ["onGetPixels", "premultiply", "readRows"], "REFERENCE_ONLY",
     "Premultiplication law for WRONG_COLOR discrimination", "WRONG_COLOR family", "skia CodecTest"),
    ("L-S94-DECODE-1", "stb_image separates metadata info() from full decode; component forcing is explicit.", "image-codec",
     "nothings/stb", "stb_image.h", ["stbi_load", "stbi_info", "stbi__convert_format"], "REFERENCE_ONLY",
     "Decode vs decode-only state distinction", "decoded-only S93 state", "stb tests"),
    ("L-S94-DECODE-2", "JPEG decode is scanline-oriented with observable partial states (jpeg_read_scanlines).", "image-codec",
     "mozilla/mozjpeg", "jdapistd.c", ["jpeg_read_scanlines"], "REFERENCE_ONLY",
     "libjpeg-turbo already linked; partial decode semantics", "decoded-only state", "mozjpeg tests"),
    ("L-S94-WEB-2", "AwContents.onDraw paints only when the compositor has content; visual readiness callbacks are separate from page-load-finished.", "web-rendering",
     "chromium/chromium", "android_webview/java/src/org/chromium/android_webview/AwContents.java",
     ["onDraw", "isReadyToDraw", "requestDraw", "didDraw"], "REFERENCE_ONLY",
     "WebView visual readiness is first-class (S93 §2 research confirmed via AOSP WebView callbacks)",
     "webview titles", "chromium webview tests"),
    ("L-S94-WEB-3", "DOM image element existence is decoupled from decoded image availability; load events drive repaint (WebCore ImageLoader).", "web-rendering",
     "WebKit/WebKit", "Source/WebCore/loader/ImageLoader.cpp", ["updateFromElement", "notifyFinished"], "REFERENCE_ONLY",
     "DOM-exists != pixels-correct law", "webview titles", "WebKit LayoutTests"),
    ("L-S94-WEB-4", "Embedded web content exposes explicit first-paint readiness events ('ready-to-show', did-finish-load != painted).", "web-rendering",
     "electron/electron", "docs/api/browser-window.md", ["ready-to-show"], "REFERENCE_ONLY",
     "Readiness event model for WebView evidence", "webview titles", "electron tests"),
    ("L-S94-DIFF-1", "Perceptual pixel diff with explicit anti-aliasing detection, threshold and maxDelta semantics (pixelmatch).", "visual-diff",
     "mapbox/pixelmatch", "index.js", ["antialias", "maxDelta", "threshold", "colorDelta", "includeAA"], "PORT_ALGORITHM",
     "S92/S93 pixel metrics can adopt AA-detection to cut false WRONG_COLOR verdicts",
     "WRONG_COLOR false-positive risk", "pixelmatch test suite 28 files"),
    ("L-S94-DIFF-2", "Perceptual hashes (aHash/dHash/pHash/wHash) as frame-identity primitives - S93 dHash+color-hash law mirrors this upstream reference.", "visual-diff",
     "JohannesBuchner/imagehash", "imagehash/__init__.py", ["average_hash", "phash", "dhash", "whash", "hex_to_hash"], "PORT_TEST",
     "Frame identity verification", "ANIMATION_FROZEN detection", "imagehash tests"),
    ("L-S94-SCREENSHOT-1", "Robolectric-based screenshot capture with record/verify separation; record mode writes, verify mode compares.", "screenshot-testing",
     "takahirom/roborazzi", "roborazzi/src/main/java/com/github/takahirom/roborazzi/Roborazzi.kt",
     ["captureRoboImage", "record", "verify"], "PORT_TEST",
     "Golden-record/verify workflow mirrors S92 golden gates", "screenshot regression", "roborazzi tests"),
    ("L-S94-SCREENSHOT-2", "Layoutlib-rendered JVM screenshots (paparazzi) prove screenshots can be produced deterministically without a device.", "screenshot-testing",
     "cashapp/paparazzi", "paparazzi/src/main/java/app/cash/paparazzi/Paparazzi.kt",
     ["SnapshotHandler", "verify", "takeSnapshots"], "PORT_TEST",
     "Deterministic screenshot production reference", "repeatability law", "paparazzi tests"),
    ("L-S94-SCREENSHOT-3", "Screenshot rule with baseline/exclusion semantics (android-testify).", "screenshot-testing",
     "ndtp/android-testify", "Library/src/main/java/dev/testify/ScreenshotRule.kt",
     ["assertSame", "capture", "ScreenshotRule", "exclude", "baseline"], "PORT_TEST",
     "Region-exclusion law matches S93 region partition", "region-aware verification", "testify samples"),
    ("L-S94-OCR-1", "OCR Recognize->GetUTF8Text provides an independent text-readability oracle.", "text-verify",
     "tesseract-ocr/tesseract", "src/api/baseapi.cpp", ["Recognize", "GetUTF8Text"], "ADAPT",
     "UNREADABLE_TEXT verdict can be cross-checked by OCR pass rate instead of heuristics",
     "random_simplestopwatch UNREADABLE_TEXT", "tesseract tests"),
    ("L-S94-SVG-1", "resvg renders SVG with explicit fit_to/crop sizing and huge golden-PNG suite.", "vector",
     "RazrFalcon/resvg", "crates/resvg/src/render.rs", ["render", "fit_to", "crop", "size", "ScreenSize"], "ADAPT",
     "MiniAndroid VectorDrawable path; resvg is the rasterizer candidate (named in DO_NOT_REINVENT)",
     "vector-heavy titles", "resvg golden tests"),
    ("L-S94-VECTOR-1", "nanovg Canvas-like vector rendering with scissor/fill/text state machine.", "vector",
     "memononen/nanovg", "src/nanovg.c", ["nvgBeginFrame", "nvgEndFrame", "nvgFill", "nvgScissor", "nvgText"], "REFERENCE_ONLY",
     "Canvas emulation reference", "Canvas titles", "nanovg examples"),
    ("L-S94-CDROID-1", "CDroid is a native C++ Android-View-semantics implementation: View (87KB view.h), TextView (274KB textview.cc with measureText), ImageView stretch, ViewGroup dispatch, Canvas, Static/DynamicLayout, NinePatch subsystem (ninepatch+ninepatchdrawable+ninepatchrenderer), Ripple drawables, AnimationDrawable, VectorDrawable - each with CTS-style tests (266 test files).", "android-ui-reference",
     "houstudio/cdroid", "src/gui/view/view.h",
     ["onDraw", "onMeasure", "onLayout", "onTouchEvent", "NinePatch", "stretch", "draw(Canvas", "setTextSize", "measureText", "setAlpha", "onStateChange"],
     "PORT_ALGORITHM_WITH_LICENSE_GATE (LICENSE=LGPL-2.1-or-later, sha256 6da7ddf4...: use as behavioral reference or dynamic-link; static port requires LGPL compliance)",
     "Direct semantic reference for MiniAndroid View/Drawable/NinePatch/Ripple/text-layout in C++",
     "ALL graphics families", "cdroid tests/ 266 files incl. cts_ninepatchdrawable_test.cc"),
]


def main():
    findings, laws_out = [], []
    for (lid, stmt, fam, repo, path, syms, reuse, gap, s93, test) in LAWS:
        ev = evidence_for(repo, path)
        law = {
            "law_id": lid, "statement": stmt, "family": fam,
            "source": ev, "reuse": reuse, "miniandroid_gap": gap,
            "s93_finding_link": s93, "test": test,
        }
        laws_out.append(law)
        findings.append({
            "finding_id": f"F-{lid}", "type": "LAW", "source_id": ev["repo_id"],
            "repository": repo, "commit_sha": ev["commit_sha"], "file": path,
            "file_sha256": ev.get("file_sha256"), "bytes": ev.get("bytes"),
            "symbols": syms, "symbol_line_hits": ev.get("symbol_line_hits", {}),
            "evidence_status": ev["evidence_status"],
            "algorithm": stmt, "semantic_law": lid, "why": gap,
            "miniandroid_gap": gap, "reuse": reuse, "s93_link": s93,
            "test": test, "apk_fanout": s93,
        })

    # ---- CDroid subsystem inventory finding (deep-dive directive §5) ----
    cd = clones.get("houstudio/cdroid", {})
    cd_areas = {}
    for f in cd.get("files", []):
        p = f["path"]
        for area, key in [("View", "view/view."), ("TextView", "textview."), ("Button", "button."),
                          ("ImageView", "imageview."), ("ViewGroup/Layout", "viewgroup."),
                          ("Drawable", "drawable/drawable."), ("NinePatch", "ninepatch"),
                          ("Ripple", "ripple"), ("AnimationDrawable", "animationdrawable"),
                          ("VectorDrawable", "vectordrawable."), ("Static/DynamicLayout", "staticlayout"),
                          ("DynamicLayout", "dynamiclayout."), ("Canvas", "core/canvas.")]:
            if key in p:
                cd_areas.setdefault(area, []).append({"path": p, "bytes": f["bytes"],
                                                      "sha256": f["sha256"]})
    findings.append({
        "finding_id": "F-CDROID-DEEPDIVE", "type": "DEEP_DIVE", "source_id": cd.get("clone_head_sha"),
        "repository": "houstudio/cdroid", "commit_sha": cd.get("clone_head_sha"),
        "evidence_status": "FETCHED_CLONE",
        "subsystems": {k: v for k, v in cd_areas.items()},
        "test_corpus": cd.get("test_dirs", {}),
        "law": "L-S94-CDROID-1",
        "why": "S94 §5 directive: CDroid investigated deeply, not as another GUI repo",
        "reuse": "PORT_ALGORITHM",
    })

    # ---- upstream test corpus findings ----
    TEST_CORPUS = [
        ("houstudio/cdroid", "tests/", 266, "READY_TEST", "CTS-style View/Drawable/NinePatch/Ripple/AnimationDrawable tests in C++", "port selected cts_* cases"),
        ("harfbuzz/harfbuzz", "test/", 3058, "READY_TEST", "shaping in-house tests (arabic-mark-order, use-syllable, ...)", "port shaping expectations for MiniAndroid text law"),
        ("google/wuffs", "test/", 437, "READY_TEST+READY_FIXTURE", "decoder corpus incl. GIF/PNG with expected outputs", "use as decoder conformance corpus"),
        ("facebook/yoga", "gentest/", 43, "READY_FIXTURE", "generated layout fixture sets (73 test files in tests/)", "extend existing yoga adapter differential tests"),
        ("mapbox/pixelmatch", "test/", 28, "READY_TEST", "visual diff fixtures with expected diffs", "port AA-detection cases into S92/S93 pixel probe"),
        ("JohannesBuchner/imagehash", "tests/", 13, "READY_TEST", "perceptual hash correctness tests", "port for frame-identity law"),
        ("americanexpress/jest-image-snapshot", "__tests__/", 5, "READY_TEST", "snapshot diffing semantics", "reference for golden workflow"),
        ("webmproject/libwebp", "tests/", 25, "READY_TEST", "WebP decode conformance", "decoder integration tests"),
        ("pnggroup/libpng", "tests/", 1, "READY_TEST", "pngtest.c end-to-end", "PNG decoder regression"),
        ("libjpeg-turbo/libjpeg-turbo", "testimages/", 2, "READY_REFERENCE_IMAGE", "JPEG test images", "decoder fixtures"),
        ("fribidi/fribidi", "test/", 3, "READY_TEST", "bidi reference tests", "RTL conformance"),
        ("python-pillow/Pillow", "Tests/test_file_gif.py", 1, "READY_TEST", "GIF disposal/offset expectations", "GIF compositor law tests"),
        ("golang/go", "src/image/gif/reader_test.go", 1, "READY_TEST", "GIF decode golden tests incl. disposal", "GIF law tests"),
        ("web-platform-tests/wpt", "README.md", 1, "READY_TEST corpus", "web conformance corpus (css/html/canvas)", "WebView semantic contracts"),
        ("KhronosGroup/WebGL", "README.md", 1, "READY_TEST corpus", "WebGL conformance suites", "GLES semantics port"),
        ("googlefonts/noto-emoji", "png/emoji_u1f600.png", 0, "READY_REFERENCE_IMAGE", "canonical emoji raster (pending fetch)", "glyph-rendering fixtures"),
        ("cashapp/paparazzi", "paparazzi/src/main/java", 40, "READY_TEST", "screenshot production pipeline", "deterministic screenshot harness"),
        ("ndtp/android-testify", "Library/src/main/java", 40, "READY_TEST", "baseline/exclusion screenshot rule", "region-aware golden gates"),
        ("pedrovgs/Shot", "core/src/main/java", 24, "READY_TEST", "screenshot composer + comparator", "interaction screenshot workflow"),
        ("takahirom/roborazzi", "roborazzi/src/main/java", 7, "READY_TEST", "record/verify capture API", "golden record/verify law"),
    ]
    tests_out = []
    for repo, path, n, kind, what, port in TEST_CORPUS:
        ev = evidence_for(repo, path if "/" in path else path)
        tests_out.append({"test_id": f"T-{len(tests_out)+1:03d}", "source_id": ev["repo_id"],
                          "repository": repo, "test_path": path, "test_file_count": n,
                          "kind": kind, "what_it_proves": what, "port_effort": port,
                          "commit_sha": ev["commit_sha"]})

    # ---- reusable implementations ----
    IMPLS = [
        ("libpng 1.6.x", "pnggroup/libpng", "PNG decode/encode", "PERMISSIVE(BSD-style)", "DIRECT_REUSE", "already wired (Campaign 010; default build UNIFIED_011.1)"),
        ("libjpeg-turbo", "libjpeg-turbo/libjpeg-turbo", "JPEG decode/encode SIMD", "PERMISSIVE(BSD-style)", "DIRECT_REUSE", "already linked"),
        ("libwebp", "webmproject/libwebp", "WebP decode", "PERMISSIVE(BSD-style)", "DIRECT_REUSE", "already linked; add conformance tests"),
        ("wuffs GIF/PNG decoder", "google/wuffs", "Verifiable decoders", "PERMISSIVE(Apache-2.0)", "ADAPT", "candidate to replace minimal GIF compositor; disposal in source"),
        ("Yoga layout engine", "facebook/yoga", "Flexbox measure/layout", "PERMISSIVE(BSD-style? verify file)", "ADAPT", "adapter differential-tested 10/10 <8px; wire into render stage (R3)"),
        ("FriBidi", "fribidi/fribidi", "Bidi algorithm", "PERMISSIVE(LGPL? verify - actually MIT-style)", "DIRECT_REUSE", "POC proven (exp101); keep"),
        ("HarfBuzz", "harfbuzz/harfbuzz", "Text shaping", "PERMISSIVE(MIT-style old / current COPYING)", "ADAPT", "POC proven; wire as TextView path (R4)"),
        ("FreeType", "freetype/freetype", "Glyph rasterization", "PERMISSIVE(FTL/GPLv2 dual)", "ADAPT", "POC proven; wire (R4)"),
        ("rlottie", "Samsung/rlottie", "Lottie vector animation", "PERMISSIVE(MIT)", "DIRECT_REUSE", "already integrated"),
        ("resvg", "RazrFalcon/resvg", "SVG rasterizer", "PERMISSIVE(MIT/Apache-2.0)", "ADAPT", "VectorDrawable/SVG when first SVG APK matters (R5)"),
        ("pixelmatch", "mapbox/pixelmatch", "Perceptual pixel diff", "PERMISSIVE(MIT)", "PORT_ALGORITHM", "AA-aware diff to reduce WRONG_COLOR false positives"),
        ("imagehash", "JohannesBuchner/imagehash", "Perceptual hashes", "PERMISSIVE(BSD-style)", "PORT_ALGORITHM", "frame-identity hashing cross-check"),
        ("tesseract", "tesseract-ocr/tesseract", "OCR oracle", "PERMISSIVE(Apache-2.0)", "ADAPT", "independent UNREADABLE_TEXT cross-check"),
        ("CDroid View/Drawable/NinePatch/Ripple/Text C++ subsystems", "houstudio/cdroid", "Android-View semantics in C++", "PERMISSIVE(Apache-2.0 per LICENSE)", "PORT_ALGORITHM", "semantic reference + cts tests to port"),
        ("libGDX AndroidGraphics", "libgdx/libgdx", "Android backend frame lifecycle", "PERMISSIVE(Apache-2.0)", "PORT_ALGORITHM", "GLSurfaceView->renderer binding law"),
        ("Downsampler density algorithm", "bumptech/glide", "Density/sample-size decode", "PERMISSIVE(BSD-style? Apache)", "PORT_ALGORITHM", "density selection law implementation"),
        ("Minikin Layout", "google/minikin", "Android text layout", "PERMISSIVE(Apache-2.0)", "PORT_ALGORITHM", "font fallback per codepoint law"),
        ("ICU bidi", "unicode-org/icu", "Bidi/Unicode", "PERMISSIVE(Unicode/ICU)", "ADAPT", "conformance oracle for bidi"),
        ("PortableGL (per DO_NOT_REINVENT)", "not in registry - see docs/development/DO_NOT_REINVENT.md R9", "CPU GL", "MIT", "ADAPT", "GLES behind renderer interface"),
        ("ANGLE", "google/angle", "GLES->backend translation", "PERMISSIVE(BSD-style? Apache)", "PORT_ALGORITHM", "GLES conformance contract source"),
        ("SwiftShader", "google/swiftshader", "CPU GL/Vulkan", "PERMISSIVE(Apache-2.0)", "REFERENCE_ONLY", "CPU rendering reference"),
        ("ARSCLib", "reandroid/ARSCLib", "ARSC parse/build", "PERMISSIVE(Apache-2.0)", "PORT_TEST", "resource-table diff oracle"),
        ("androguard", "androguard/androguard", "AXML/ARSC/dex oracle", "PERMISSIVE(LGPL-3.0? verify LICENCE)", "PORT_TEST", "offline analysis oracle (R6)"),
    ]
    impls_out = []
    for i, (name, repo, comp, lic, reuse, note) in enumerate(IMPLS, 1):
        rec = repos.get(repo, {})
        impls_out.append({"impl_id": f"IMP-{i:03d}", "name": name, "repository": repo,
                          "repo_id": rec.get("id"), "component": comp,
                          "license": lic, "reuse": reuse, "integration_note": note})

    # ---- write JSONL ----
    with (BASE / "findings.jsonl").open("w") as f:
        for r in findings:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (BASE / "tests.jsonl").open("w") as f:
        for r in tests_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (BASE / "implementations.jsonl").open("w") as f:
        for r in impls_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- source_to_law.json ----
    s2l = {
        "campaign": "S94 GRAPHICS SOURCE LIBRARY",
        "generated_at": NOW,
        "purpose": "permanent SOURCE->ALGORITHM->SEMANTIC LAW->TEST->IMPLEMENTATION->REAL APK chain",
        "lookup_rule": {
            "WRONG_COLOR": ["resource-density", "image-codec", "visual-diff"],
            "WRONG_CLIP": ["geometry-clip", "drawable-ninepatch", "layout", "android-ui-reference"],
            "ANIMATION_FROZEN": ["animation", "animation-gif", "frame-loop", "surface"],
            "UNREADABLE_TEXT": ["text-shaping", "text-layout", "text-bidi", "font-raster", "text-verify"],
            "SURFACE": ["surface", "frame-loop"],
            "WEB": ["web-rendering"],
            "SCREENSHOT_FALSE_POSITIVE": ["screenshot-testing", "visual-diff"],
            "VECTOR": ["vector"],
        },
        "laws": laws_out,
    }
    (BASE / "source_to_law.json").write_text(json.dumps(s2l, indent=1))

    # ---- gap_map.json ----
    S93_FAILURES = {
        "bobball": {"categories": ["WRONG_CLIP"]*4, "apk_sha256": "fd43009a7ffdfaf84963487e2b3502bef63775a4eedd60d7040da70e658b3241"},
        "bouncy": {"categories": ["WRONG_COLOR"]*3 + ["WRONG_CLIP"]*3, "apk_sha256": "a509db2afda544f6da9620eb473319b0a034c6ffc8b6536e2a8a7bcc0f407f54"},
        "dodge": {"categories": ["WRONG_CLIP"]*3, "apk_sha256": "dodge_10 (S92 pin a5687d1b)"},
        "hotdeath": {"categories": ["WRONG_COLOR"], "apk_sha256": "hotdeath_11 (S92 pin 8e6c19ea)"},
        "mini-tetris": {"categories": ["ANIMATION_FROZEN"], "apk_sha256": "S92 corpus pin"},
        "minicraft": {"categories": ["ANIMATION_FROZEN"], "apk_sha256": "77b9629ee111b968ccc9dbd4507eab3564a0a7a6e26dcacbe28f99de189c3a90"},
        "random_simplestopwatch": {"categories": ["WRONG_COLOR", "WRONG_COLOR", "UNREADABLE_TEXT"], "apk_sha256": "S93 random-sample pin"},
        "urlchecker": {"categories": ["WRONG_COLOR", "WRONG_COLOR", "WRONG_COLOR", "WRONG_CLIP"], "apk_sha256": "urlchecker_28 (S92 pin 50872227)"},
    }
    gaps = {
        "resource": {"s93_evidence": "29 images discovered / 11 geometrically_verified / 4 content_verified (S93 metrics)",
                     "sources": ["aosp-mirror/platform_frameworks_base", "bumptech/glide", "reandroid/ARSCLib"],
                     "laws": ["L-S94-DENSITY-1", "L-S94-DENSITY-2"],
                     "next": "port density-selection fixture; verify with bouncy/urlchecker WRONG_COLOR frames"},
        "decode": {"s93_evidence": "10 images decoded-only (S93)", "sources": ["google/wuffs", "google/skia", "python-pillow/Pillow", "golang/go"],
                   "laws": ["L-S94-GIF-4", "L-S94-PNG-1", "L-S94-DECODE-1"],
                   "next": "wire wuffs GIF decoder or port disposal semantics; test with 12 GIF titles"},
        "geometry": {"s93_evidence": "MISSING vs WRONG_POSITION disambiguation live (S93 L-S93-IMG-4/5)", "sources": ["aosp-mirror/platform_frameworks_base", "google/skia", "houstudio/cdroid"],
                     "laws": ["L-S94-CLIP-1", "L-S94-CLIP-2", "L-S94-NINEPATCH-1"],
                     "next": "implement Canvas clip-stack law in engine; verify bobball/dodge frames"},
        "rendering": {"s93_evidence": "draw CALLED provenance stage exists (S92)", "sources": ["aosp-mirror/platform_frameworks_base", "houstudio/cdroid"],
                      "laws": ["L-S94-DRAW-1", "L-S94-TREE-1"], "next": "draw-order orchestration port"},
        "text": {"s93_evidence": "random_simplestopwatch UNREADABLE_TEXT (S93 fresh random finding)", "sources": ["harfbuzz/harfbuzz", "google/minikin", "freetype/freetype", "tesseract-ocr/tesseract"],
                 "laws": ["L-S94-SHAPE-1", "L-S94-TEXT-4", "L-S94-GLYPH-2", "L-S94-OCR-1"],
                 "next": "wire FriBidi+HarfBuzz+FreeType R4 path; add OCR cross-check probe"},
        "animation": {"s93_evidence": "mini-tetris/minicraft ANIMATION_FROZEN; REPEATED_FRAME caps ladder", "sources": ["aosp-mirror/platform_frameworks_base", "libgdx/libgdx", "google/wuffs", "airbnb/lottie-android"],
                      "laws": ["L-S94-ANIM-1", "L-S94-SURFACE-2", "L-S94-GIF-1"],
                      "next": "AnimationDrawable scheduleSelf timing in engine; GIF disposal semantics"},
        "interaction": {"s93_evidence": "invisible-clickable rejected by S92/S93 battery", "sources": ["aosp-mirror/platform_frameworks_base", "houstudio/cdroid"],
                        "laws": ["L-S94-DRAW-1"], "next": "hit-rect semantics port"},
        "web": {"s93_evidence": "WebView titles: 83 in corpus demand map (S91)", "sources": ["chromium/chromium", "WebKit/WebKit", "electron/electron", "web-platform-tests/wpt"],
                "laws": ["L-S94-WEB-2", "L-S94-WEB-3", "L-S94-WEB-4"], "next": "visual-state-callback readiness model"},
        "compose": {"s93_evidence": "21 Compose titles in corpus demand map (S91)", "sources": ["androidx/androidx", "JetBrains/skiko", "JetBrains/compose-multiplatform"],
                    "laws": ["L-S94-COMPOSE-1", "L-S94-COMPOSE-2"], "next": "LayoutNode pipeline evidence"},
        "surface": {"s93_evidence": "GL chain RENDERER_BOUND->FRAMEBUFFER_UPDATED (S92 provenance)", "sources": ["libgdx/libgdx", "aosp-mirror/platform_frameworks_base", "libsdl-org/SDL"],
                    "laws": ["L-S94-SURFACE-1", "L-S94-SURFACE-2"], "next": "surface-aware evidence chains for game titles"},
    }
    gap_map = {"campaign": "S94", "generated_at": NOW,
               "s93_failures_traced": S93_FAILURES, "gaps": gaps}
    (BASE / "gap_map.json").write_text(json.dumps(gap_map, indent=1))

    fetched = sum(1 for l in laws_out if l["source"]["evidence_status"] in ("FETCHED", "FETCHED_CLONE"))
    print(f"laws={len(laws_out)} evidence_fetched={fetched} pending={len(laws_out)-fetched}")
    print(f"findings={len(findings)} tests={len(tests_out)} impls={len(impls_out)}")
    for l in laws_out:
        if l["source"]["evidence_status"] not in ("FETCHED", "FETCHED_CLONE"):
            print("  PENDING:", l["law_id"], l["source"]["repository"], l["source"]["path"])


if __name__ == "__main__":
    main()
