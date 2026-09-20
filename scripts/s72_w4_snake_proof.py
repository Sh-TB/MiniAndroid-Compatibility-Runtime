#!/usr/bin/env python3
"""s72_w4_snake_proof.py — W4 target-game evidence: screenshot metrics +
determinism x3 + state-chain extraction. Constitution §052-058/§060-063."""
import sys, os, glob, json, hashlib
from PIL import Image
from collections import Counter

RUNS = [
    "/home/z/my-project/run/s72_w4_det1",
    "/home/z/my-project/run/s72_w4_det2",
    "/home/z/my-project/run/s72_w4_det3",
]

def metrics(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = list(img.getdata())
    nonwhite = sum(1 for p in px if p != (255, 255, 255))
    # luminance + entropy on grayscale
    gray = [0.2126*r + 0.7152*g + 0.0722*b for r, g, b in px]
    lum = sum(gray)/len(gray)
    hist = Counter(int(g) for g in gray)
    total = len(gray)
    import math
    ent = -sum((c/total) * math.log2(c/total) for c in hist.values() if c)
    dom = Counter(px).most_common(5)
    # content bounds (non-white)
    img_l = img.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            if img_l[x, y] != (255, 255, 255):
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    # game-state cells
    imgl = img.load()
    pink, blue = [], []
    for y in range(0, 780, 39):
        for x in range(0, 1080, 39):
            c = imgl[x+20, y+20]
            if c == (255, 64, 129): pink.append((x//39, y//39))
            elif c == (0, 0, 255): blue.append((x//39, y//39))
    return {
        "resolution": f"{w}x{h}",
        "nonwhite_px": nonwhite,
        "luminance": round(lum, 2),
        "entropy_bits": round(ent, 4),
        "dominant": [(f"#{r:02x}{g:02x}{b:02x}", c) for (r, g, b), c in dom],
        "content_bounds": [minx, miny, maxx, maxy],
        "snake_cells": sorted(pink),
        "food_cells": sorted(blue),
        "png_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16],
        "pixel_sha256": hashlib.sha256(img.tobytes()).hexdigest()[:16],
    }

frames = sorted(glob.glob(os.path.join(RUNS[0], "frames", "frame_*.png")))
print("== FRAME CHAIN (det1) ==")
for f in frames:
    m = metrics(f)
    print(f"{os.path.basename(f)}: nonwhite={m['nonwhite_px']} snake={m['snake_cells']} food={m['food_cells']}")

print("\n== FINAL FRAME x3 (determinism + metrics) ==")
finals = []
for r in RUNS:
    ff = sorted(glob.glob(os.path.join(r, "frames", "frame_*.png")))[-1]
    m = metrics(ff)
    finals.append(m["pixel_sha256"])
    print(f"{r}: {json.dumps(m, ensure_ascii=False)}")
print("\nDETERMINISM:", "BYTE-IDENTICAL x3" if len(set(finals)) == 1 else f"MISMATCH {finals}")
