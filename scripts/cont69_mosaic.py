#!/usr/bin/env python3
"""cont69_mosaic.py — build the CONT-69 evidence mosaic (4x5 grid).

Row 1-2: the collection-law family faces (memory cold/warm before-after,
notes, llk probe, TSP, gate A) + the wall controls.
Row 3-5: the recorded wall anchors at the CONT-69 binary.
"""
from PIL import Image, ImageDraw, ImageFont
import os, hashlib

BASE = "/home/z/my-project"
FONT = None
for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    if os.path.exists(p):
        FONT = ImageFont.truetype(p, 17)
        break

TILES = [
    # ── the CONT-69 story: memory cold first-launch BEFORE/AFTER + warm ──
    ("memory COLD before (F-NEW-369 white 31ddd4d5)", f"{BASE}/run/s69/cold1/screenshot.png"),
    ("memory COLD after x3 (REAL 3a3ba873, 21.4% nonbg)", f"{BASE}/run/s69/coldfix_r2/screenshot.png"),
    ("memory WARM after x3 (record c559b630 intact)", f"{BASE}/run/s69/warmfix1/screenshot.png"),
    ("notes after x3 (record d0a40904 intact)",       f"{BASE}/run/s69/notes_r1/screenshot.png"),
    # ── probes ──
    ("llk probe 8/8 (subList/copy/NSEE laws)",        f"{BASE}/run/s69/llk_det1/screenshot.png"),
    ("TSP theme probe 7/7 (record values)",           f"{BASE}/run/s69/tsp_run1/screenshot.png"),
    ("gate A probe 98/1/0",                           f"{BASE}/run/gatea/negative/gatea_run0/screenshot.png"),
    ("BMI control (f45d6c66 x3)",                     f"{BASE}/run/s69/regression/ctrl_bmi_r1/screenshot.png"),
    # ── the 12-row wall (all MATCH x3 at binary 6e475854) ──
    ("dooz15s (31ddd4d5)",                            f"{BASE}/run/s60/regression/dooz_r1/screenshot.png"),
    ("dooz180 (c94da5a9)",                            f"{BASE}/run/s60/regression/dooz180_r1/screenshot.png"),
    ("opencalc (f25b754c)",                           f"{BASE}/run/s60/regression/opencalc_r1/screenshot.png"),
    ("simplecalc (2ac5d8d0)",                         f"{BASE}/run/s60/regression/simplecalc_r1/screenshot.png"),
    ("tanana (afe0bd8d)",                             f"{BASE}/run/s60/regression/tanana_r1/screenshot.png"),
    ("unote (90a67cc1)",                              f"{BASE}/run/s60/regression/unote_r1/screenshot.png"),
    ("bouncy (dd0c1425 menu face)",                   f"{BASE}/run/s69/regression/ctrl_bouncy_r1/screenshot.png"),
    ("klondike20 (a77038da real menu)",               f"{BASE}/run/s69/regression/ctrl_klondike20_r1/screenshot.png"),
    ("g2048 (59ca1526)",                              f"{BASE}/run/s60/regression/g2048_r1/screenshot.png"),
    ("flappycow (13cf4746)",                          f"{BASE}/run/s60/regression/flappycow_r1/screenshot.png"),
    ("gmdice (3891679d)",                             f"{BASE}/run/s60/regression/gmdice_r1/screenshot.png"),
    ("csw (d3c26b73)",                                f"{BASE}/run/s60/regression/csw_r1/screenshot.png"),
]

TW, TH = 540, 960
COLS = 4
ROWS = (len(TILES) + COLS - 1) // COLS
mosaic = Image.new("RGB", (COLS*TW, ROWS*(TH+40)), (18, 18, 22))
draw = ImageDraw.Draw(mosaic)

missing = []
for i, (label, path) in enumerate(TILES):
    cx, cy = (i % COLS) * TW, (i // COLS) * (TH + 40)
    if path and os.path.exists(path):
        im = Image.open(path).convert("RGB").resize((TW, TH))
        mosaic.paste(im, (cx, cy))
    else:
        draw.rectangle([cx, cy, cx+TW-1, cy+TH-1], fill=(40, 40, 48))
        if FONT:
            draw.text((cx+16, cy+TH//2), "MISSING: " + label[:40], fill=(200, 200, 120), font=FONT)
        missing.append(label)
    if FONT:
        draw.text((cx+8, cy+TH+6), label[:62], fill=(230, 230, 230), font=FONT)

out = f"{BASE}/evidence/cont69/cont69_mosaic.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
mosaic.save(out, optimize=True)
h = hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]
print("mosaic:", out, "sha16:", h, f"({len(TILES)} tiles)", "missing:", missing)
