#!/usr/bin/env python3
"""cont11_verify_f264.py — pixel-truth verification of the F-NEW-264 probe.

Expected (probe design):
  R1 red compositing      : fb(110,130) == (204,34,34)  and fb(105,125) same
  R2 translated green rect: fb(135,145) == (34,170,68)  (bitmap(30..40,20..30))
  R2 negative (no misplace): fb(105,125) stays RED (rect NOT at bitmap 0..10)
  R4 no-pollution         : fb(600,900) == (48,48,48)   (0xFF303030 bg)
  R3 readback text        : white glyph pixels on the two F264 lines
"""
import sys
from PIL import Image

png = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/run/cont11/f264_run1/screenshot.png"
im = Image.open(png).convert("RGB")
W, H = im.size
sx, sy = W / 1080.0, H / 1920.0   # screenshots may be downscaled

def px(x, y):
    return im.getpixel((int(x * sx), int(y * sy)))

def near(a, b, tol=6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))

rows = []
def check(name, ok, detail):
    rows.append((name, ok, detail))

r1a = px(110, 130); r1b = px(105, 125)
check("R1 red composites at (110,130)", near(r1a, (204, 34, 34)), str(r1a))
check("R1 red composites at (105,125)", near(r1b, (204, 34, 34)), str(r1b))
r2 = px(135, 145)
check("R2 translated rect green (135,145)", near(r2, (34, 170, 68)), str(r2))
r2n = px(105, 125)
check("R2 rect NOT misplaced at (105,125)", near(r2n, (204, 34, 34)), str(r2n))
r4 = px(600, 900)
check("R4 no view pollution (600,900)", near(r4, (48, 48, 48), 4), str(r4))

# R3: white glyph pixels present in the two text bands (y 225..340)
band = im.crop((0, int(215 * sy), int(560 * sx), int(345 * sy)))
white = sum(1 for p in band.getdata()
            if p[0] > 200 and p[1] > 200 and p[2] > 200)
check("R3 readback text rendered (white glyph px > 40)", white > 40,
      f"white_px={white}")

fails = [r for r in rows if not r[1]]
for name, ok, detail in rows:
    print(("PASS " if ok else "FAIL ") + f"{name:44s} {detail}")
print(f"--- {len(rows)-len(fails)}/{len(rows)} PASS")
sys.exit(1 if fails else 0)
