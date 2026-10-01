#!/usr/bin/env python3
"""S135 FIX — regenerate the 5 corrupted glyphs in bitmap_font_data.h.

Root cause (measured, S135): glyph_dot_bitmap is 16x 0xFF (solid block),
glyph_minus has 3 full rows, glyph_E/I/z corrupted the same way. The
failure mode: a generator that tight-crops the ink bbox before scaling
turns wide-flat glyphs ('-', '.', tops/bottoms of E/I/z) into an
all-ink cell (every bbox pixel < threshold => full 0xFF rows).

Method (this script): render the character on a FULL CELL at high
resolution (glyph drawn on a white cell, baseline preserved), downscale
the WHOLE CELL to 8x16 (LANCZOS), threshold luminance < 128. The cell
framing keeps stroke geometry — no tight-crop inversion is possible.
"""
from PIL import Image, ImageFont, ImageDraw

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
HEADER = "/home/z/my-project/miniandroid/src/renderer/bitmap_font_data.h"

# DejaVuSansMono advance/height ratio ~= 0.602; 8x16 cell ratio = 0.5.
# Render a big cell with the glyph horizontally centered; the runtime
# glyph box is 8 wide with the ink typically 6-7 px (advance < 8).
CELL_W, CELL_H = 96, 192          # 12x of 8x16
font = ImageFont.truetype(FONT, 128)

def render(ch):
    img = Image.new("L", (CELL_W, CELL_H), 255)
    d = ImageDraw.Draw(img)
    # center the glyph ink in the cell
    bbox = d.textbbox((0, 0), ch, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (CELL_W - w) // 2 - bbox[0]
    y = (CELL_H - h) // 2 - bbox[1]
    d.text((x, y), ch, font=font, fill=0)
    small = img.resize((8, 16), Image.LANCZOS)
    px = small.load()
    rows = []
    for r in range(16):
        val = 0
        for c in range(8):
            if px[c, r] < 140:
                val |= 0x80 >> c
        rows.append(val)
    return rows

import re
src = open(HEADER).read()
for ch in ['-', '.', 'E', 'I', 'z']:
    name = {'-': 'glyph_minus_bitmap', '.': 'glyph_dot_bitmap',
            'E': 'glyph_E_bitmap', 'I': 'glyph_I_bitmap',
            'z': 'glyph_z_bitmap'}[ch]
    rows = render(ch)
    assert all(v != 0xFF for v in rows), (ch, rows)
    m = re.search(r'static const uint8_t ' + name + r'\[16\] = \{.*?\};', src, re.S)
    assert m, name
    new = "static const uint8_t %s[16] = {\n" % name + "".join(
        "    0x%02X, // row %2d\n" % (v, i) for i, v in enumerate(rows)) + "};"
    src = src[:m.start()] + new + src[m.end():]
    print(repr(ch), "->", " ".join("%02X" % v for v in rows))

open(HEADER, "w").write(src)
print("patched", HEADER)
