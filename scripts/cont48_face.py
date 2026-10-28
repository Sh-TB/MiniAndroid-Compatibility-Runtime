#!/usr/bin/env python3
"""cont48_face.py — PNG face classification (matches cont47 classifier law).
Prints: face=<CLASS> uniq32=<N> nonwhite=<ratio> med=<r,g,b>"""
import sys, colorsys

try:
    from PIL import Image
    import numpy as np
except Exception:
    print("face=NO-PIL")
    sys.exit(0)

path = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    im = Image.open(path).convert("RGB")
except Exception:
    print("face=NO-PNG")
    sys.exit(0)

im = im.resize((270, 480))
a = np.asarray(im).astype(int)
nonwhite = (a.sum(axis=2) < 720).mean()

# uniq32 buckets (quantize to 32 levels per channel)
b = (a >> 3).astype(np.uint32)
packed = (b[:, :, 0] << 10) | (b[:, :, 1] << 5) | b[:, :, 2]
uniq = len(np.unique(packed))

if nonwhite < 0.005:
    print(f"face=FLAT uniq32={uniq} nonwhite={nonwhite:.3f}")
    sys.exit(0)

med = [int(x) for x in np.median(a[a.sum(axis=2) < 720].reshape(-1, 3), axis=0)]
r, g, bl = [x / 255.0 for x in med]
h, s, v = colorsys.rgb_to_hsv(r, g, bl)
hue = int(h * 360)

if s < 0.12 and v < 0.5:
    cls = "DARK"
elif s < 0.12:
    cls = "GREY"
elif hue < 15 or hue >= 345:
    cls = "RED"
elif hue < 45:
    cls = "ORANGE"
elif hue < 70:
    cls = "YELLOW"
elif hue < 170:
    cls = "GREEN"
elif hue < 260:
    cls = "BLUE"
else:
    cls = "PURPLE"
print(f"face={cls} uniq32={uniq} nonwhite={nonwhite:.3f} med={med}")
