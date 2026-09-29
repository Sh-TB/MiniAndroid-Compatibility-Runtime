#!/usr/bin/env python3
"""s119_calibrate2.py — exact button bboxes by color scan in REAL pixels."""
from PIL import Image

R = "/home/z/my-project/run"


def bbox_of(png, pred, step=3):
    img = Image.open(png).convert("RGB")
    W, H = img.size
    px = img.load()
    xs, ys = [], []
    for y in range(0, H, step):
        for x in range(0, W, step):
            if pred(px[x, y]):
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys), len(xs))


# snake-deluxe frame: find the bright blue START button
fsd = f"{R}/s80_sd_autoplay/final_run/frames/frame_119.png"
img = Image.open(fsd).convert("RGB")
px = img.load()
# sample a horizontal line every 60px to find distinct hues
for y in range(1000, 1920, 60):
    row = [px[x, y] for x in range(60, 1020, 120)]
    uniq = {}
    for c in row:
        uniq[c] = uniq.get(c, 0) + 1
    top = sorted(uniq.items(), key=lambda kv: -kv[1])[:3]
    print("y=%d" % y, top)
