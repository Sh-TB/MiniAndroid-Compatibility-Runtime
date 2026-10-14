#!/usr/bin/env python3
"""cont64_w2_registry.py — CONT-64 W2 registry: add F-NEW-352 (the Paint
color-filter draw-time tint law + the Bitmap.setPixels companion law)."""
import json

PATH = "/home/z/my-project/root_registry.json"
with open(PATH) as f:
    reg = json.load(f)

if any(r.get("id") == "F-NEW-352" for r in reg["roots"]):
    print("F-NEW-352 already present — no-op")
else:
    reg["roots"].append({
        "id": "F-NEW-352",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework/paint-colorfilter + renderer/porterduff-tint + framework/bitmap-setpixels",
        "title": (
            "PAINT COLOR-FILTER (draw-time tint) GAP + Bitmap.setPixels gap: "
            "Paint.setColorFilter(ColorFilter) had NO handler (the filter was "
            "swallowed — every tinted drawBitmap rendered as no-tint), "
            "PorterDuffColorFilter/BlendModeColorFilter ctors stored NOTHING "
            "(the framework-owned object allocated EMPTY, the color+mode args "
            "vanished), and Bitmap.setPixels(int[],off,stride,x,y,w,h) was "
            "absent (createBitmap'd bitmaps stayed zero-filled — only the "
            "MULTIPLY row's opaque-src alpha law produced pixels in the "
            "probe). Three generic links closed: (1) the ctor law captures "
            "__filter_color__/__filter_mode__ (the mode ordinal read from "
            "the synthesized enum object's ordinal field); (2) "
            "Paint.setColorFilter/getColorFilter record + return the filter "
            "object per paint (sync_shared_state parity for the F-NEW-345 "
            "sub-recorder); drawBitmap snapshots op.has_tint/tint_color/"
            "tint_mode with the [1..17] ordinal sanity gate (mode 0 CLEAR on "
            "a color filter = the honest no-tint, never erase); (3) the "
            "replay applies the per-pixel PorterDuff law on BOTH bitmap "
            "paths (affine inverse-map + the temp-buffer non-affine) — "
            "SRC=1, SRC_OVER=3, DST_OVER=4, SRC_IN=5, DST_IN=6, DST_OUT=8, "
            "SRC_ATOP=9, MULTIPLY=14, SCREEN=15 implemented; unknown modes = "
            "honest no-tint. Probe: fixtures/fnew352_probe (real aapt2/ECJ/"
            "D8, apk 485d9bccbb98035f) 9 pixel rows — T1 SRC_IN red/white->"
            "RED, T2 transparent->nothing, T3 SRC_ATOP half-alpha, T4 "
            "MULTIPLY red*blue->black, T5 no-filter control UNCHANGED, T6 "
            "BlendModeColorFilter green, T7 per-paint filter STATE (red vs "
            "blue in the same wave), T8 getColorFilter round-trip — 9/9 "
            "PASS, screenshot f6e3be95506ad8f9 x3 byte-identical. "
            "Regression: anchors 36/36 x3 ZERO DRIFT (11 rows x3 + dooz180 "
            "c94da5a928ea213b x3 — the tint law is render-neutral for "
            "untinted paths)."
        ),
        "last_updated": "CONT-64 W2",
    })
    reg["total_roots"] = len(reg["roots"])
    with open(PATH, "w") as f:
        json.dump(reg, f, indent=1, ensure_ascii=False)
    print("F-NEW-352 added; total roots:", reg["total_roots"])
