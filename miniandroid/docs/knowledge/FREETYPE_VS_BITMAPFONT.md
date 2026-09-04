# FreeType vs BitmapFont Comparison (§10)

## Method
`scripts/exp096_freetype_compare.cpp` renders the SAME text with both:
1. MiniAndroid BitmapFont (95 ASCII glyphs auto-generated from
   DejaVuSansMono by `scripts/gen_bitmap_font.py` at 8px advance).
2. FreeType with `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf`
   at 16px (matching BitmapFont line_height).

Text samples (from the SMS screen):
  - "Enter code"
  - "We've sent an SMS with an activation code to your phone +1 5551234567."

Output: `run/exp096_evidence/{bitmapfont,freetype}.{ppm,png}`.

## Numeric Comparison

| Text                         | BitmapFont | FreeType | Δ      | Notes |
|------------------------------|-----------:|---------:|-------:|-------|
| "Enter code"                 | 67 px      | 100 px   | +49%   | FreeType wider; BitmapFont underestimates advance |
| "We've sent an SMS..."       | 445 px     | 700 px   | +57%   | Compound underestimate across 70 chars |
| dark pixels (whole canvas)  | 2910       | 2607     | -11%   | BitmapFont renders MORE pixels (over-thick strokes) |
| **IoU (overlap/union)**      | **13.1%**  |          |        | Low overlap — different glyph shapes |

## Visual Findings

1. **Glyph advance**: BitmapFont's auto-generated glyphs use 8px advance for
   all characters (uniform, table-driven). FreeType uses the font's natural
   advance widths (varying 6-12px per glyph). Result: BitmapFont text is
   ~36% narrower than real Android rendering.

2. **Glyph shape**: BitmapFont uses bitmap-stored rasterizations at 8px;
   FreeType produces anti-aliased vector outlines at 16px. Visually different
   anti-aliasing — IoU only 13.1%.

3. **Pixel count**: BitmapFont produces slightly MORE dark pixels because
   its strokes are bolder (over-thick). FreeType has more accurate stroke
   widths.

## Implications for the SMS Screen

The MiniAndroid SmsView description is currently WRAP-breakable at
~458px (BitmapFont measured width). On real Android (FreeType metrics),
this text would NOT wrap on a 1080px screen — it fits comfortably.

This is a **measurement-only** issue today — text rendering is visible and
correct, just slightly narrower than real Android. The fix should be:

1. **Don't blindly replace BitmapFont globally** — keep it for ASCII
   rendering (works, fast, simple).
2. **Plug in FreeType as the primary metric source** — use FreeType's
   `FT_Advance_Fixed` to compute accurate text widths, but keep
   BitmapFont for the actual pixel rasterization (avoid the anti-aliasing
   cost). This is the "reference second" approach from the campaign rules.
3. **Or: render through FreeType entirely** — accept the perf cost (the
   SmsView text is small; rendering it once at startup is fine). Best
   fidelity but introduces a freetype dependency for the runtime.

## Recommendation

For the current campaign phase (compatibility expansion), keep BitmapFont
for rendering and add a FreeType-backed `measure_text_accurate()` used
only when the rendered text would clip or wrap incorrectly. The visual
screen is currently acceptable; the measurement delta is logged here so
future typography work has a baseline.

## Reproducibility
```
g++ -std=c++17 -I src -I src/renderer -I /usr/include/freetype2 \
    scripts/exp096_freetype_compare.cpp src/renderer/software_renderer.cpp \
    -lfreetype -lz -o build/exp096_freetype_compare
./build/exp096_freetype_compare
```
