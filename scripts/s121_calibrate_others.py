#!/usr/bin/env python3
"""s121_calibrate_others.py — vision-calibrate gmdice / bouncy / opmt /
fishrings tap targets from their rendered frames (1080x1920 space)."""
import sys
from PIL import Image

R = "/home/z/my-project/run/s120_new_games"


def show_regions(png, label, pred, min_w=40):
    """Find x-clusters of pixels matching pred in each row band."""
    img = Image.open(png).convert("RGB")
    W, H = img.size
    px = img.load()
    print(f"== {label} ({png.split('/')[-3]}) ==")
    bands = []
    for y in range(0, H, 6):
        n = sum(1 for x in range(0, W, 8) if pred(px[x, y]))
        if n > 3:
            bands.append(y)
    cl = []
    for y in bands:
        if cl and y - cl[-1][-1] <= 12:
            cl[-1].append(y)
        else:
            cl.append([y])
    for b in cl:
        ymid = (b[0] + b[-1]) // 2
        xs = [x for x in range(0, W, 2) if pred(px[x, ymid])]
        xcl = []
        for x in xs:
            if xcl and x - xcl[-1][-1] <= 14:
                xcl[-1].append(x)
            else:
                xcl.append([x])
        objs = [(c[0], c[-1], (c[0] + c[-1]) // 2) for c in xcl
                if c[-1] - c[0] > min_w]
        if objs:
            print(f"y[{b[0]}..{b[-1]}] mid={ymid}: {objs}")


# gmdice: blue button bar at bottom (light blue ~ (111,168,220) family)
show_regions(f"{R}/gmdice_roll/frames/frame_029.png", "gmdice blue buttons",
             lambda p: 90 <= p[0] <= 150 and 150 <= p[1] <= 195
             and 200 <= p[2] <= 240, min_w=30)

# bouncy: light-blue buttons (~(100,180,220)) on purple panel
show_regions(f"{R}/bouncy/frames/frame_029.png", "bouncy buttons",
             lambda p: 70 <= p[0] <= 130 and 160 <= p[1] <= 200
             and 205 <= p[2] <= 245, min_w=60)

# opmt: blue rounded buttons on black
show_regions(f"{R}/opmt/frames/frame_029.png", "opmt buttons",
             lambda p: 60 <= p[0] <= 130 and 130 <= p[1] <= 190
             and 230 <= p[2] <= 255, min_w=60)

# fishrings: balls = saturated circles on black; detect per color
def ball(imgpx, W, H, pred):
    pts = [(x, y) for y in range(0, 900, 4) for x in range(0, W, 4)
           if pred(imgpx[x, y])]
    # cluster into balls
    balls = []
    for (x, y) in pts:
        for b in balls:
            if abs(b[0] * b[2] - x) < 40 and abs(b[1] * b[2] - y) < 40:
                b[0] += x; b[1] += y; b[2] += 1
                break
        else:
            balls.append([x, y, 1])
    return [(round(b[0] / b[2]), round(b[1] / b[2]), b[2]) for b in balls
            if b[2] > 4]


img = Image.open(f"{R}/fishrings/frames/frame_029.png").convert("RGB")
W, H = img.size
px = img.load()
print("== fishrings balls ==")
print("red:", ball(px, W, H, lambda p: p[0] > 190 and p[1] < 120 and p[2] < 120))
print("pink:", ball(px, W, H, lambda p: p[0] > 190 and p[1] < 120 and p[2] > 190))
print("blue:", ball(px, W, H, lambda p: p[0] < 130 and p[1] < 150 and p[2] > 190))
print("green:", ball(px, W, H, lambda p: p[0] < 160 and p[1] > 170 and p[2] < 160))
