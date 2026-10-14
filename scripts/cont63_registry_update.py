#!/usr/bin/env python3
"""cont63_registry_update.py — CONT-63 W1: register F-NEW-351 (the compose
DrawCache vector-icon face: BlendMode.CLEAR painted black squares + the
ImageBitmap wrapper-unwrap + the BlendMode enum family), repair the
pre-existing validator staleness (V6 reconciliation count, V8 legacy
counters, V9 open_frontiers superseded rows), and keep every counter
coherent with len(roots)."""
import json, sys

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
roots = d["roots"]
ids = [r.get("id") for r in roots]
assert "F-NEW-351" not in ids, "F-NEW-351 already registered — no inflation"

row = {
    "id": "F-NEW-351",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "framework/canvas-blendmode + compose/drawcache + framework/enum-synthesis",
    "title": "COMPOSE DrawCache VECTOR-ICON FACE: every material icon rendered as a SOLID BLACK SQUARE (dooz v23 top-bar settings/about + FAB games + undo) — three stacked links, all generic: (1) DrawCache.clear() = drawRect(Color.Black, BlendMode.CLEAR) recorded a NORMAL fill (no blend-mode law) and painted the 63x63 icon cache SOLID BLACK (the squares); (2) Paint.setBlendMode had NO handler and the android.graphics.BlendMode enum family was ABSENT from the framework-enum synthesis table (BlendMode.CLEAR sget answered NULL — the blend never recorded); (3) Canvas(bitmap-target)/drawBitmap bitmap args did not resolve compose ImageBitmap WRAPPER objects (BitmapStore miss -> 'bitmap-unresolved' -> the rendered cache never composited).",
    "root_cause": "MEASURED (run/cont63/drawwin180 + MINIANDROID_CANVAS_OP_TRACE ops.txt + [DRAW-CALLER] correlation + CL-TRACE Ly3;.p/Ly3;.b caller chains + ARG-TRACE Ly3;.b): the compose icon draw = VectorComposition.draw -> DrawCache.drawCachedImage -> ImageBitmap(w,h,config) + Canvas(cacheImage) -> cacheScope { clear() { drawRect(Black, BlendMode.Clear) } ; with(root) { scale(rootScale, pivot=Zero) { draw() } } } -> prepareToDraw -> drawInto -> target.drawImage(cacheImage, alpha, colorFilter) (upstream/s43 ui_android vector/DrawCache.kt:104 + Vector.kt:163). The engine's op trace shows per icon: [ROUNDRECT container][RECT 63x63 ff000000 = the CLEAR rect painted black][PATH tone 4d000000][PATH main ff000000] and the drawImage landed 'RecordingCanvas.drawBitmap(bitmap-unresolved) accepted_not_reproduced' — black cache never composited, so the face = the black squares. The path rasterizer itself was PROVEN correct (fixtures/fnew351_probe rows R1-R9,RA pre-fix: triangle/circles/two-tone-alpha/paint-reuse/viewport-scale all pixel-exact — the rasterizer was never the defect).",
    "law": "AOSP/Skia: (a) BlendMode.kClear = dst REPLACED with transparent (the composite result is independent of dst — set_pixel's src-over law cannot express it; a fully-transparent source is a no-op by construction) — FrameBuffer gained the clear_pixel REPLACE primitive; (b) android.graphics.BlendMode = a 19-member enum (CLEAR..REDUCE, API 29 decl order) — every member synthesizes with its AOSP ordinal like the existing PorterDuff/Config tables; (c) Bitmap-consuming APIs (Canvas bind + drawBitmap family) resolve their arg through the R-NEW-360 wrapper-probe law: a non-BitmapStore object walks its object-ref fields (bounded 2 levels) for a resolvable Bitmap (compose AndroidImageBitmap and any app wrapper share the shape); (d) Paint.setBlendMode records the ordinal per paint (sync_shared_state parity for bitmap-target sub-recorders).",
    "fix": "ALL GENERIC (no app/compose/R8-name knowledge; grep audit clean): canvas_shadow.{h,cpp} — DrawOp.blend_mode snapshot + paint_blendmode_ map + setBlendMode handler; DRAW_RECT/DRAW_PATH replay ERASE branches via FrameBuffer.clear_pixel (REPLACE, never blended) honoring the op clip; resolve_bitmap_arg() at the Canvas <init>/setBitmap bind + all three drawBitmap object-overload arms; sync_shared_state mirrors paint_blendmode_; bounded drawBitmap-unresolved arg_fields diagnostic. dalvik_engine.cpp — the FULL BlendMode ordinal table (19 rows) + Bitmap$Config RGBA_F16/HARDWARE rows. renderer/software_renderer.h — FrameBuffer::clear_pixel.",
    "probe": "fixtures/fnew351_probe (real aapt2/ECJ/D8, apk sha16 c6d93226107c081c) — 14 rows x3 deterministic (screenshot b235bb24717cedae): R1 triangle rasterizer; R2 ANTI-SQUARE circle; R3 two-tone tone-alpha; R4 BlendMode.SRC_OVER no-corruption; R5 two-contour single drawPath; R6 path rewind reuse; R7 the compose transform pattern (translate+scale 2.75 + 24-unit disc); R8 paint color-switch reuse; R9 quadTo circle; RA addPath winding; RB interface-dispatch wrapper scale replica; RC direct-scale control (documented RD overlay); RD BlendMode.CLEAR view erase (cleared half WHITE, kept half RED); RE bitmap-target CLEAR through Canvas(Bitmap) + getPixel readback + alpha-faithful composite. scripts/cont63_verify_f351.py = the pixel battery (14/14 x3).",
    "evidence": "evidence/cont63/fnew351_evidence.json; run/cont63/{drawwin180, optrace, optrace2, cltrace, clscale, argscale, f351_det1..3, dooz180_f351, regression}; the live dooz op-trace (ops.txt seq 23-26 = the per-icon op stream) + [DRAW-CALLER] 1239/1239 drawRect correlation + CL-TRACE caller chains (Ly3;.p <- Lgi;.O <- Lp00;.F <- Lf22;.e <- Lj22;.e = VectorPainter.e; Ly3;.b <- Las0;.x <- Le22;.i <- Lf22;.e = the DrawScope root scale).",
    "fanout": "every compose app that draws ANY material icon or vector painter (the Icons.* family corpus-wide); every Canvas consumer using blend modes; every wrapper-carried bitmap handoff (image-loader libraries); the drawBitmap-unresolved family (the diagnostic now names the escaping wrapper shape).",
    "verified_current": "at binary a00f331a07dfa961 (clean rebuild over the recovery commit 63b2075d): anchors 33/33 x3 byte-identical ZERO DRIFT (csw d3c26b73ee21e571, dooz15 31ddd4d5b8e6d18e, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622, gmdice 3891679dff449331, microtimer 55343bbec712618d, opencalc f25b754c4565c38b, simplecalc 341b9cec89d8f182, tanana afe0bd8dd4d09ca6, tttdeluxe af6094295ecb50e3, unote 90a67cc1ddda57b7); dooz180 face INTENTIONALLY re-pinned 4f32f50fd55ccf90 -> c94da5a928ea213b x3 (the icons render: settings gear, undo arrow, games glyph, info disc — pixel census of the settings box: white 2262 / black 1707 glyph pixels vs the pre-fix solid 3969-black square); negatives 19/19; reinstall 8/8; multiapp ALL PASS; skill 13/13; probe 14/14 x3.",
    "honest_limits": "the colorFilter TINT application at drawBitmap is NOT modeled (the icons render with their intrinsic vector paint colors — visually correct for the monochrome material-icon family; a tint-color-mismatch face would surface in a multi-colored-tint app); the Info icon renders as a full disc (the two-tone layer split renders but the 'i' counter contrast depends on the tone-alpha blend — recorded, not suppressed); the remaining 2 drawBitmap-unresolved rows on dooz15 carry arg_fields=(none) — a NULL/never-materialized bitmap producer, named by the diagnostic, NOT hidden (a follow-up decode, not a regression).",
    "date": "2026-10-14",
}
roots.append(row)
d["total"] = len(roots)
d["count"] = len(roots)
d["total_roots"] = len(roots)
if "summary" in d:
    d["summary"]["total_roots"] = len(roots)
    of = [f for f in d["summary"].get("open_frontiers", [])
          if f not in ("R-NEW-303", "R-NEW-381")]
    d["summary"]["open_frontiers"] = of
json.dump(d, open(REG, "w"), indent=1)

# V6: reconciliation MD count coherence
p = "/home/z/my-project/docs/BASE_COMPLETION_RECONCILIATION.md"
md = open(p).read()
import re
m = re.search(r"root_registry\.json \((\d+) roots\)", md)
if m and int(m.group(1)) != len(roots):
    md = md.replace(f"root_registry.json ({m.group(1)} roots)",
                    f"root_registry.json ({len(roots)} roots)")
    open(p, "w").write(md)
    print("V6: reconciliation MD count ->", len(roots))
else:
    print("V6: already coherent =", m.group(1) if m else "no marker")
print("registry rows:", len(roots), "| F-NEW-351 appended; counters synced; open_frontiers cleaned")
