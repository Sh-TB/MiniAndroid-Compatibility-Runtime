#!/usr/bin/env python3
"""cont101_registry_update.py — register the CONT-101 batch roots
(F-NEW-416..422) in both registry copies (root_registry.json and the
canonical mirror). One entry per independent root, statuses reflect the
POST evidence (probe rows + raster oracle)."""
import json, shutil

SRC = 'root_registry.json'
DST = 'canonical/root_cause_registry.json'

DIR99 = "#364 CONT-99 (comment 6248236077)"
DIR = ("#364 CONT-101 batch wave (T5/T6/T7 executed as three separate "
       "fixture-first task units; zero new comments after 6252294570)")

def root(rid, status, prio, title, layer, rc, fix, ev, links):
    return {
        "id": rid, "status": status, "priority": prio, "title": title,
        "layer": layer, "directive": DIR,
        "root_cause": rc, "fix": fix, "evidence": ev,
        "related": links,
        "binary_after": "ac0d40244b8e0516",
        "probe_apks": {
            "c99tx": "2427b960562dc8b1",
            "c99zo": "6c8a1745b464a027",
            "c99cv": "b60c665a25aafe1f",
        },
    }

roots = [
    root(
        "F-NEW-416", "ROOT-CAUSED-FIXED", "P0",
        "Paint metrics family answered null/stubs — getFontMetrics() minted no "
        "FontMetrics object (c99tx onCreate NPE 'field Paint$FontMetrics;.top on "
        "a null object reference', app-boundary death) and ascent()/descent()/"
        "getTextSize() fell to generic defaults",
        "runtime/graphics-paint-jni",
        "AOSP Paint.java/Paint.cpp JNI: metrics come from the same font engine "
        "that measures and draws. The Paint bridge had NO metrics accessors — "
        "the no-arg getFontMetrics() returned null and the receiver overload "
        "never filled fields; every app touching font metrics (baseline math, "
        "custom vertical centering, LineHeightSpan) died or mislaid out.",
        "dalvik_engine.cpp: Paint ascent/descent/getFontMetrics/getFontMetricsInt/"
        "getTextSize served from fonts::TextShaper::font_metrics (the G36 law: "
        "ascent<0<descent, descent−ascent = line height) at the paint's recorded "
        "__text_size_px__ (F-NEW-226 store). getFontMetrics(fm) fills and returns "
        "the RECEIVER (AOSP identity); no-arg allocates; Int form CEILs in "
        "magnitude into Paint$FontMetricsInt (android-14 Paint.cpp). "
        "F-NEW-416b: TextView.getPaint() mint now carries the view's RECORDED "
        "text size instead of an unconditional 42.0f. Shaper-unavailable → zeros "
        "with a LOUD stderr line (never silent invented values).",
        "POST rows: ascent=-45 descent=12 top=-45 bottom=12 leading=0 meas48=216 "
        "meas24=108 (24px exactly half of 48px — proportional ✓); "
        "TXVPAINT tv1 size=48 ascent=-45 descent=12; probe run "
        "run/cont101/post/tx; fixture fixtures/cont99_tx_probe V2-C99TX "
        "(2427b960562dc8b1)",
        ["F-NEW-226", "F-NEW-227", "G36"],
    ),
    root(
        "F-NEW-417", "ROOT-CAUSED-FIXED", "P1",
        "TextView line-state getter family missing (getLineHeight, getMaxLines, "
        "getEllipsize, getIncludeFontPadding) and the setters were uncaptured — "
        "rows answered generic stubs",
        "runtime/view-property-shadows",
        "AOSP TextView.java: maxLines/ellipsize/includeFontPadding are first-class "
        "state with constructor defaults (mMaxMode=LINES mMaximum=9999, "
        "mEllipsize=null, mIncludeFontPadding=true); getLineHeight = "
        "paint.getFontMetricsInt(null) = descent−ascent (G36). The engine had "
        "none of the getters and no capture for the TextView setters (only the "
        "StaticLayout$Builder variants existed).",
        "dalvik_engine.cpp F-NEW-417: set/getMaxLines (heap __max_lines__ + "
        "ViewNode.max_lines), set/getEllipsize (enum OBJECT identity round-trip "
        "on the heap; ordinal decoded into ViewNode.ellipsize_mode 1..4), "
        "set/getIncludeFontPadding (heap + ViewNode.include_font_pad), "
        "getLineHeight (G36 at the view's recorded size via TextShaper). "
        "F-NEW-417b: dual-write heap + ViewShadow ViewNode — one source of "
        "truth, two consumers (getter identity + renderer draw law).",
        "POST rows: tv3 maxLines=1 ell=END; others maxLines=9999 ell=@0(null) "
        "ifp=true; lineH=57/38/33/57/43/38 per view size (G36 ✓); probe "
        "run/cont101/post/tx",
        ["F-NEW-416", "F-NEW-421", "G36", "G47"],
    ),
    root(
        "F-NEW-418", "ROOT-CAUSED-FIXED", "P0",
        "ViewGroup child-order laws broken: bringToFront() was a silent no-op "
        "(PHASE2 raster identical to PHASE1) and indexOfChild() answered 0 for "
        "EVERY child (generic-stub first-child answers)",
        "runtime/viewgroup-order",
        "AOSP View.bringToFront → parent.bringChildToFront: remove + re-add at "
        "the END of the children array (paint order = array order → moved child "
        "paints LAST = on top) + requestLayout/invalidate. AOSP "
        "ViewGroup.indexOfChild: array identity scan, -1 when absent. The engine "
        "had neither: overlapping-sibling z-order control (drag layers, badge "
        "overlays, popup-ish stacking in real apps) was impossible and index "
        "reads were silently wrong.",
        "android_shadows.cpp F-NEW-418: indexOfChild (identity scan, -1 absent); "
        "bringToFront (reorder receiver's parent children vector to the end + "
        "layout_dirty); bringChildToFront (the ViewGroup-side AOSP entry). The "
        "renderer draws ViewNode.children in array order, so the reorder flips "
        "the raster exactly per AOSP.",
        "POST: PHASE1 order=A,B,C,D idxA=0/idxB=1/idxC=2; PHASE2 order=B,C,D,A "
        "idxA=3; raster Q1 (200,200)=RED Q2 (300,300)=RED (A over B/C) Q3 "
        "(400,400)=BLUE Q4 yellow — 9/9 oracle rows OK; probe "
        "run/cont101/post/zo1+zo2; fixture fixtures/cont99_zo_probe V1-C99ZO "
        "(6c8a1745b464a027)",
        ["F-NEW-408", "S130"],
    ),
    root(
        "F-NEW-419", "ROOT-CAUSED-FIXED", "P1",
        "View elevation Z-state never round-tripped: setElevation was a silent "
        "no-op and getElevation answered 0 unconditionally",
        "runtime/view-property-shadows",
        "AOSP View.setElevation stores mRenderNode elevation (Z = elevation + "
        "translationZ) and getElevation answers it; ViewCompat/CardView shadows "
        "and Compose modifiers read it back. The View setter fell into the "
        "canvas-shadow silent-bool family and no getter existed (c99zo ZOEL "
        "row: setElevation(20) then getElevation()==0).",
        "android_shadows.h ViewNode.elevation field + android_shadows.cpp "
        "setElevation capture / getElevation answer (the same state-block as "
        "getX/getY F-NEW-411). Rendering-level Z-sorted draw order stays the "
        "named frontier (recorded, not claimed): the STATE contract is what "
        "app bookkeeping depends on.",
        "POST ZOEL: elevC=20.000000 elevA=0.000000 (round-trip ✓); probe "
        "run/cont101/post/zo2",
        ["F-NEW-411", "F-NEW-418"],
    ),
    root(
        "F-NEW-420", "ROOT-CAUSED-FIXED", "P1",
        "Canvas.quickReject answered false unconditionally — even under an "
        "EMPTY clipRect (AOSP: everything is rejected)",
        "runtime/graphics-canvas",
        "AOSP Canvas.quickReject(l,t,r,b[,RectF]): true when the rect does not "
        "intersect the CURRENT clip (empty clip ⇒ reject everything). The "
        "engine had no handler → the generic default answered false, so app "
        "culling guards (onDraw quickReject checks, RenderNode rejections) "
        "drew what AOSP skips (c99cv emptyclip row: clipRect(0,0,0,10) then "
        "quickReject(0,0,100,100)==false).",
        "canvas_shadow.cpp F-NEW-420: quickReject (float 4-arg + RectF forms) "
        "bakes the query rect with the CURRENT matrix into op space (same as "
        "clipRect), intersects with clip_ when active; no-clip boundary: only "
        "degenerate rects reject (device rect not tracked in op space — "
        "documented honest boundary).",
        "POST: emptyclip quickReject=true clipBoundsNull=true sc=2 (all 5 "
        "frames); raster R1..R5 5/5 (save/restore/clip/saveLayer/sibling "
        "no-leak unchanged); probe run/cont101/post/cv; fixture "
        "fixtures/cont99_cv_probe V1-C99CV (b60c665a25aafe1f)",
        ["S68", "S83", "F-NEW-298"],
    ),
    root(
        "F-NEW-421", "ROOT-CAUSED-FIXED", "P0",
        "TextView draw law drew ONE line with no word wrap, no ellipsis marker "
        "and no own-bounds clip — text overflowed or was silently cut at the "
        "box edge (AOSP Layout wrap + TruncateAt + drawChild clip law)",
        "renderer/text-layout",
        "AOSP TextView.onDraw draws a Layout: text WRAPS at the view's content "
        "width, maxLines caps the line count, ellipsize truncates the visible "
        "tail with the … marker (TruncateAt END/START/MIDDLE), and "
        "ViewGroup.drawChild clips every child to its own bounds. Pre-fix: a "
        "single line was laid out at pen_x=left+padL — a 48-char 'E…' string "
        "crossed the 320px box (no marker), sentences painted one clipped "
        "line, and glyph ink could land outside the view box.",
        "view_renderer.cpp draw_text_into rewritten as the F-NEW-421 law: "
        "greedy word wrap at content width (+ char hard-break for overlong "
        "words, '\\n' hard breaks), maxLines cap from ViewNode.max_lines "
        "(F-NEW-417), ellipsize END/START/MIDDLE with U+2026 (MARQUEE = static "
        "END first-frame boundary, recorded), per-line gravity, G47 "
        "includeFontPadding block positioning (above=|top| vs |ascent| — "
        "equal for the primary face, so the default render is unchanged), and "
        "a per-glyph child-bounds clip (the S130 law at the blit level).",
        "POST oracle ALL GREEN: tv1 ink(29..74, right 276) inside 300x100; tv3 "
        "ellipsis ink right=317<=318 INSIDE the box; tv4 wrapped to two lines "
        "ink(245..337) inside the 100px box; gaps pure-bg; tv5 box-relative "
        "inkTop == tv1 (top==ascent font law); battery wall 12/12 "
        "byte-identical + goldens 4/4 + negatives 19/19 + reinstall 8/8 + "
        "MG-310 7/7 + MG-150 3/3 + selftests 13/13 + F-NEW-376 70/70 + "
        "anchors OK (zero drift); probe run/cont101/post/tx",
        ["F-NEW-416", "F-NEW-417", "G47", "S130"],
    ),
    root(
        "F-NEW-422", "ROOT-CAUSED-FIXED", "P0",
        "Arabic/RTL (and every other FreeSerif-covered script) rendered "
        "blank/tofu: the only script fallbacks were emoji + CJK, and the "
        "primary face (DroidSansMono) carries ZERO Arabic glyphs",
        "fonts/script-fallback",
        "AOSP fonts.xml defines a fallback chain per script; the engine "
        "implemented only the emoji (NotoColorEmoji) and CJK (WenQuanYi) arms "
        "of it. Arabic codepoints shaped to .notdef on the primary face and "
        "nothing claimed them (c99tx PRE tv6 '\\u0633\\u0644\\u0627\\u0645 "
        "\\u062f\\u0646\\u06cc\\u0627' = no ink) — the whole Persian/Arabic "
        "app family (the user's own corpus language) rendered empty text. "
        "kFaceFallback (FreeSerif, wide coverage incl. Arabic joined forms) "
        "was already loaded but no reshaping arm consumed it.",
        "text_shaper.cpp F-NEW-422: a third fallback arm in shape() — for "
        "remaining .notdef clusters after emoji+CJK, re-shape the visual "
        "sequence with the fallback face's hb_font (Arabic init/medi/fina "
        "joining comes from the fallback GSUB via HarfBuzz, NOT a charmap "
        "swap) and claim clusters that yield real glyphs (emoji claim pattern); "
        "ShapedGlyph.use_fallback/fallback_gid + the grayscale raster path "
        "draws them from kFaceFallback; fallback_available_ guards the "
        "real-face case (alias → arm off). FriBidi RTL reorder was already "
        "correct.",
        "POST: tv6 RTL ink EXISTS ink=(top486,bot522,left0,right131) — real "
        "joined Arabic glyphs; all other rows unchanged (zero drift on Latin "
        "text); battery zero drift everywhere; probe run/cont101/post/tx",
        ["R-NEW-398", "MG-083", "MG-085", "G32"],
    ),
]

data = json.load(open(SRC))
known = {r['id'] for r in data}
added = 0
for r in roots:
    if r['id'] not in known:
        data.append(r)
        added += 1
json.dump(data, open(SRC, 'w'), indent=1, ensure_ascii=False)
shutil.copy(SRC, DST)
print(f"registry {len(data)-added} -> {len(data)} (+{added}); mirrored to {DST}")
