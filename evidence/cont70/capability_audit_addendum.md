# CONT-70 capability-audit addendum (measured at wave binary ab3978b794c8fb6e)

Amends evidence/s58/capability_audit_v3.md. Two items re-measured this wave:

## Item 24 — Custom app fonts (assets TTF)?  PARTIAL → IMPLEMENTED (probe-proven)
The startup scan (FIX-4 + F-NEW-315) registers every APK-shipped TTF/OTF; the
API surface now closes the loop end-to-end: Typeface.createFromAsset resolves
the registered face by APK-entry name (AOSP failure law: RuntimeException
"Font asset not found"), Paint.setTypeface carries __font_face_idx__ into the
paint state, and the Canvas replay draws with the app face at the REAL paint
size. Probe: fixtures/font_probe (same-string two-face draw — ink geometries
336x58 vs 412x62 prove two distinct faces; the "NOFACE" fallback row did not
fire). Evidence: run/cont70/accept/font_probe5, F-NEW-372.

## Item 25 — Emoji rendering?  NOT TESTED → OBSERVED-PASS (pixel-proven)
TextShaper loads NotoColorEmoji (CBDT, strike=109) — "[TEXTSHAPER] READY ...
emoji=...NotoColorEmoji.ttf(strike=109)". Probe fixtures/emoji_probe draws
U+1F600 at 128px on a custom view: the emoji band contains 11,120 yellow
pixels (the glyph's face color) and 13,826 non-white pixels; the CJK control
band (好, wqy-zenhei) contains 0 yellow pixels. The color-emoji path renders
real CBDT strikes on the canvas-drawText lane. Evidence:
run/cont70/accept/emoji_probe (+ .err TEXTSHAPER READY row).

## Item 24b (new measurement) — opencalc display note (ANT-7)
The S58 "empty display" observation is launch-correct behavior: the display is
an EditText (WRAP_CONTENT, empty text at launch) in a ConstraintLayout; it
wraps to 52x199 at the right edge. No provable divergence without a real-
device reference; no fix shipped (honest no-bug-found).
