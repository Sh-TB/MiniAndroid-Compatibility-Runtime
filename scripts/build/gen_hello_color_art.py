#!/usr/bin/env python3
"""
scripts/build/gen_hello_color_art.py — deterministic fixture art for hello_color.

Writes res/drawable/hello_art.png: a fixed geometric composition
(color quadrants + white diagonal band + dark ring). No randomness, no
clock: identical invocations produce identical bytes, so the fixture
APK stays byte-deterministic (§28 law). The PNG is frozen in the
fixture tree after generation; this script is the provenance record.
"""
from PIL import Image, ImageDraw

W = H = 256
OUT = ("/home/z/my-project/MiniAndroid-Compatibility-Runtime/"
       "miniandroid/tests/fixtures/hello_color/res/drawable/hello_art.png")

im = Image.new("RGB", (W, H), (13, 71, 161))  # #0D47A1 deep blue base
d = ImageDraw.Draw(im)

# color quadrants (inset 16px)
q = 16
d.rectangle([q, q, W // 2 - 1, H // 2 - 1], fill=(255, 82, 82))     # red
d.rectangle([W // 2, q, W - q - 1, H // 2 - 1], fill=(255, 235, 59))   # yellow
d.rectangle([q, H // 2, W // 2 - 1, H - q - 1], fill=(0, 200, 83))     # green
d.rectangle([W // 2, H // 2, W - q - 1, H - q - 1], fill=(64, 196, 255))  # light blue

# white diagonal STRIPES (sparse, deterministic — quadrants stay visible)
for i in range(-H, W + H, 48):
    d.line([i, 0, i + H, H], fill=(255, 255, 255), width=14)

# dark ring border (8px)
ring = (26, 35, 126)
d.rectangle([0, 0, W - 1, H - 1], outline=ring, width=8)

im.save(OUT, "PNG", optimize=False)
import hashlib
data = open(OUT, "rb").read()
print("wrote", OUT, len(data), "bytes, sha256", hashlib.sha256(data).hexdigest()[:16])
