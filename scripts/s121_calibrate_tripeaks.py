#!/usr/bin/env python3
"""s121_calibrate_tripeaks.py — vision-calibrate TriPeaks geometry from the
rendered deal frame (no hardcoding: measure card rects from pixels, S119 law).

Outputs: bottom-row face-up card x-centers, waste center, stock center,
pyramid rows y-bands — all in 1080x1920 screen space.
"""
import sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/run/s120_new_games/tripeaks_game3/frames/frame_040.png"

img = Image.open(SRC).convert("RGB")
W, H = img.size
px = img.load()

GREEN = (51, 170, 17)


def is_green(p, tol=28):
    return abs(p[0] - GREEN[0]) <= tol and abs(p[1] - GREEN[1]) <= tol \
        and abs(p[2] - GREEN[2]) <= tol


def is_brown(p):
    r, g, b = p
    return 60 <= r <= 130 and 30 <= g <= 80 and 10 <= b <= 55 and r > g > b


# 1) find the y-band of the bottom row: horizontal band with many card pixels
def col_profile(y):
    runs = []
    x = 0
    while x < W:
        p = px[x, y]
        if not is_green(p):
            runs.append((x, p))
        x += 2
    return runs

# scan rows for card density
print("== y-band scan (rows with >25% non-green) ==")
bands = []
for y in range(0, H, 4):
    n = sum(0 if is_green(px[x, y]) else 1 for x in range(0, W, 8))
    if n > (W // 8) * 0.25:
        bands.append(y)
# cluster
cl = []
for y in bands:
    if cl and y - cl[-1][-1] <= 8:
        cl[-1].append(y)
    else:
        cl.append([y])
centers = [(c[0], c[-1]) for c in cl]
print("dense bands:", centers)

# 2) bottom row: take the band whose center is between 150 and 320 (deal row)
row_band = None
for (a, b) in centers:
    if 140 <= (a + b) // 2 <= 330:
        row_band = (a, b)
        break
print("bottom row band:", row_band)

if row_band:
    ymid = (row_band[0] + row_band[1]) // 2
    # x-clusters of card pixels at ymid
    xs = [x for x in range(0, W, 2) if not is_green(px[x, ymid])]
    xcl = []
    for x in xs:
        if xcl and x - xcl[-1][-1] <= 10:
            xcl[-1].append(x)
        else:
            xcl.append([x])
    cards = [(c[0], c[-1], (c[0] + c[-1]) // 2) for c in xcl if c[-1] - c[0] > 40]
    print("bottom-row card x-runs (x0,x1,center):", cards)

# 3) waste + stock: scan the band below the row (y 330..520) for non-green
print("== waste/stock scan ==")
for y in range(row_band[1] + 20 if row_band else 340, 620, 8):
    xs2 = [x for x in range(0, W, 2) if not is_green(px[x, y])]
    if xs2:
        xcl2 = []
        for x in xs2:
            if xcl2 and x - xcl2[-1][-1] <= 10:
                xcl2[-1].append(x)
            else:
                xcl2.append([x])
        objs = [(c[0], c[-1], (c[0] + c[-1]) // 2,
                 'BROWN' if is_brown(px[(c[0] + c[-1]) // 2, y]) else 'card')
                for c in xcl2 if c[-1] - c[0] > 30]
        if objs:
            print(y, objs)

# 4) pyramid rows: face-down card color = brown-ish brick; detect bands above row
print("== pyramid bands (brown density) ==")
for y in range(0, row_band[0] if row_band else 300, 6):
    nb = sum(1 for x in range(0, W, 8) if is_brown(px[x, y]))
    if nb > 8:
        print(y, "brown px:", nb)
