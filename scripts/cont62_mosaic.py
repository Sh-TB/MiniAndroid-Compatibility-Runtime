#!/usr/bin/env python3
"""cont62_mosaic.py — 3x2 mosaic of CONT-62 W1 screenshots (merged binary)."""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = "/home/z/my-project"
tiles = [
    ("run/cont62/f345_det3/screenshot.png",
     "F345 probe: bitmap-canvas NOW COMPOSITES (was 0px)"),
    ("run/cont62/regression/simplecalc_r3/screenshot.png", "Simple Calculator"),
    ("run/cont62/regression/opencalc_r3/screenshot.png", "OpenCalculator"),
    ("run/cont62/regression/tanana_r3/screenshot.png", "Tanana Calculator"),
    ("run/cont62/regression/csw_r3/screenshot.png", "Compose Stopwatch"),
    ("run/cont62/regression/g2048_r3/screenshot.png", "2048"),
]
CW, CH, LBL, PAD, HDR = 380, 676, 34, 12, 56
cols, rows = 3, 2
W = cols * CW + (cols + 1) * PAD
H = HDR + rows * (CH + LBL) + (rows + 1) * PAD
m = Image.new("RGB", (W, H), (16, 18, 24))
d = ImageDraw.Draw(m)
try:
    f_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    f_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except Exception:
    f_h = f_l = ImageFont.load_default()
d.text((PAD, 16), "MiniAndroid CONT-62 W1 — F-NEW-345 bitmap-target Canvas fixed — anchors 33/33 zero-drift",
       fill=(240, 240, 240), font=f_h)
for i, (rel, label) in enumerate(tiles):
    r, c = divmod(i, cols)
    x = PAD + c * (CW + PAD)
    y = HDR + PAD + r * (CH + LBL + PAD)
    p = os.path.join(BASE, rel)
    im = Image.open(p).convert("RGB").resize((CW, CH), Image.LANCZOS)
    m.paste(im, (x, y))
    d.rectangle([x, y + CH, x + CW, y + CH + LBL], fill=(28, 32, 44))
    d.text((x + 6, y + CH + 8), label, fill=(200, 210, 230), font=f_l)
out = os.path.join(BASE, "evidence/cont62/cont62_mosaic.png")
m.save(out, optimize=True)
print("mosaic:", out, os.path.getsize(out), "bytes")
