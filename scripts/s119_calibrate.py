#!/usr/bin/env python3
"""s119_calibrate.py — measure CURRENT button geometry from rendered frames.

Root cause (S119): the S80/S98 drivers hard-coded tap coordinates measured at
S80/S98 time; since then the engine's layout laws evolved (correctly), so
buttons moved and the stale taps miss. ONE recalibration pass, vision-derived
from the CURRENT frames — the same pattern the ttt driver already uses.
"""
import json
from PIL import Image

R = "/home/z/my-project/run"


def bands(png, pred, step_y=4, step_x=10, min_hits=25):
    """y-bands where pred(pixel) is frequent; returns list of (y0,y1)."""
    img = Image.open(png).convert("RGB")
    W, H = img.size
    px = img.load()
    rows = []
    for y in range(0, H, step_y):
        hits = sum(1 for x in range(0, W, step_x) if pred(px[x, y]))
        rows.append((y, hits))
    bands = []
    for y, h in rows:
        if h >= min_hits:
            if bands and y - bands[-1][1] <= step_y * 2:
                bands[-1][1] = y
            else:
                bands.append([y, y])
    return bands


def xcenters(png, y, pred, tol_gap=40):
    img = Image.open(png).convert("RGB")
    W, _ = img.size
    px = img.load()
    xs = [x for x in range(0, W, 4) if pred(px[x, y])]
    cl = []
    for x in xs:
        if cl and x - cl[-1][-1] <= tol_gap:
            cl[-1].append(x)
        else:
            cl.append([x])
    return [sum(c) // len(c) for c in cl]


# 1) 2048: button bar = warm grey #8B7D77-ish tiles row near bottom
f2048 = f"{R}/s80_2048_autoplay/cycle_30/frames/frame_104.png"


def p2048_btn(p):
    r, g, b = p
    return 120 <= r <= 165 and 105 <= g <= 150 and 95 <= g + 10 and abs(r - g) < 30 and abs(g - b) < 30 and b < 150

b2048 = bands(f2048, p2048_btn, min_hits=40)
print("2048 button bands:", b2048)
if b2048:
    y = (b2048[-1][0] + b2048[-1][1]) // 2
    print("2048 btn x centers @y=%d:" % y, xcenters(f2048, y, p2048_btn))

# 2) snake-deluxe: START = bright blue #2E5BFF-ish wide button
fsd = f"{R}/s80_sd_autoplay/final_run/frames/frame_119.png"


def psd_start(p):
    r, g, b = p
    return b > 200 and 40 < r < 110 and 60 < g < 140

bsd = bands(fsd, psd_start, min_hits=30)
print("snake-deluxe START bands:", bsd)
if bsd:
    y = (bsd[-1][0] + bsd[-1][1]) // 2
    print("snake START x centers:", xcenters(fsd, y, psd_start))

# direction buttons = slate grey #3A4A5A-ish
def psd_dir(p):
    r, g, b = p
    return 45 <= r <= 85 and 60 <= g <= 100 and 75 <= b <= 115

bdir = bands(fsd, psd_dir, min_hits=25)
print("snake-deluxe dir bands:", bdir)
if bdir:
    for (y0, y1) in bdir:
        yc = (y0 + y1) // 2
        print(f"  dir y={yc}:", xcenters(fsd, yc, psd_dir))

# 3) snake-neon: direction bar dark slate with cyan labels
fsn = f"{R}/s98_snakeneon_autoplay/final/frames/frame_119.png"


def psn_bar(p):
    r, g, b = p
    return 35 <= r <= 75 and 40 <= g <= 80 and 55 <= b <= 95

bsn = bands(fsn, psn_bar, min_hits=30)
print("snake-neon bar bands:", bsn)

def psn_cyan(p):
    r, g, b = p
    return g > 180 and b > 150 and r < 120

if bsn:
    y = (bsn[-1][0] + bsn[-1][1]) // 2
    print("snake-neon btn x centers @y=%d:" % y, xcenters(fsn, y, psn_cyan))

# 4) tetris: control buttons slate #3A4A5A-ish
ftet = f"{R}/s80_tet_autoplay/cycle_02/frames/frame_105.png"


def ptet_btn(p):
    r, g, b = p
    return 50 <= r <= 90 and 62 <= g <= 102 and 80 <= b <= 120

btet = bands(ftet, ptet_btn, min_hits=30)
print("tetris button bands:", btet)
if btet:
    for (y0, y1) in btet[-2:]:
        yc = (y0 + y1) // 2
        print(f"  tetris y={yc}:", xcenters(ftet, yc, ptet_btn))

# 5) minicraft (already PASS — record for completeness)
print("minicraft: PASS at current geometry (driver probes at runtime)")
