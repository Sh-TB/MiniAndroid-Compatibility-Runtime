#!/usr/bin/env python3
"""s119_calibrate3.py — final calibrated tap geometry for all native games."""
from PIL import Image

R = "/home/z/my-project/run"


def runs_at(png, y, pred, step=2, min_run=8):
    """contiguous x-runs matching pred at row y -> centers"""
    img = Image.open(png).convert("RGB")
    W, _ = img.size
    px = img.load()
    run, out = [], []
    for x in range(0, W, step):
        if pred(px[x, y]):
            run.append(x)
        else:
            if len(run) * step >= min_run:
                out.append((run[0] + run[-1]) // 2)
            run = []
    if len(run) * step >= min_run:
        out.append((run[0] + run[-1]) // 2)
    return out


# ---- snake-deluxe frame_119 ----
fsd = f"{R}/s80_sd_autoplay/final_run/frames/frame_119.png"
slate = lambda p: abs(p[0] - 51) < 20 and abs(p[1] - 65) < 20 and abs(p[2] - 85) < 20
white = lambda p: p[0] > 200 and p[1] > 200 and p[2] > 200
for name, y in [("TOP", 1510), ("LEFT/RIGHT", 1690), ("BOTTOM", 1810)]:
    print("sd", name, "y=%d white-runs:" % y, runs_at(fsd, y, white))
blue = lambda p: abs(p[0] - 37) < 25 and abs(p[1] - 99) < 25 and abs(p[2] - 235) < 25
print("sd START blue band:", runs_at(fsd, 1330, blue))

# ---- 2048 frame_104 ----
f2048 = f"{R}/s80_2048_autoplay/cycle_30/frames/frame_104.png"
for y in range(1760, 1880, 10):
    r = runs_at(f2048, y, white, min_run=6)
    if r:
        print("2048 y=%d white text runs:" % y, r)
        break
# board rect: tile color (light) vs bg
boardg = lambda p: 225 <= p[0] <= 245 and 220 <= p[1] <= 240 and 210 <= p[2] <= 232
for y in range(200, 1300, 40):
    r = runs_at(f2048, y, boardg, min_run=30)
    if r:
        print("2048 first tile-band y=%d runs:" % y, r[:6])
        break

# ---- tetris frame_105 ----
ftet = f"{R}/s80_tet_autoplay/cycle_02/frames/frame_105.png"
for y in range(1200, 1920, 10):
    r = runs_at(ftet, y, white, min_run=6)
    if len(r) >= 3:
        print("tetris y=%d white text runs:" % y, r)

# ---- snake-neon frame_119 ----
fsn = f"{R}/s98_snakeneon_autoplay/final/frames/frame_119.png"
cyan = lambda p: p[1] > 170 and p[2] > 140 and p[0] < 130
for y in range(1780, 1900, 8):
    r = runs_at(fsn, y, cyan, min_run=6)
    if len(r) >= 4:
        print("neon y=%d cyan label runs:" % y, r)
        break
