#!/usr/bin/env python3
"""s58_mosaic.py — build the S58 evidence mosaic (4x4 grid of faces)."""
from PIL import Image, ImageDraw
import os, hashlib

BASE = "/home/z/my-project"
TILES = [
    ("simplecalc COMPLETE (display 0 + full panel)", f"{BASE}/run/cont67/regression/simplecalc_r1/screenshot.png"),
    ("opencalc 180s: full panel, display EMPTY",      f"{BASE}/run/s58/opencalc180/screenshot.png"),
    ("BMI: real form (2 fields + Calculate)",         f"{BASE}/run/s58/bmi/screenshot.png"),
    ("tanana: real settings face (glyphs paint)",     f"{BASE}/run/cont67/regression/tanana_r1/screenshot.png"),
    ("unote: dark list + action bar",                 f"{BASE}/run/cont67/regression/unote_r1/screenshot.png"),
    ("alex: real face (anchor c8d69f81 x2 runs)",     f"{BASE}/run/s58/alex/screenshot.png"),
    ("dooz180: Material3 Scaffold face",              f"{BASE}/run/s58/dooz180_check/screenshot.png"),
    ("dooz15s: honest blank (anchor 31ddd4d5)",       f"{BASE}/run/cont67/regression/dooz_r1/screenshot.png"),
    ("capaudit 22/22 (RTL+bold/italic+media)",        f"{BASE}/run/s58/capaudit_r1/screenshot.png"),
    ("fnew260 getModifiers 11/11",                    f"{BASE}/run/s58/fnew260_run/screenshot.png"),
    ("fnew262 bridge returns 11/11",                  f"{BASE}/run/s58/fnew262_run/screenshot.png"),
    ("tripeaks: DEFAULT_BACKGROUND_ONLY (honest)",    f"{BASE}/run/s58/tripeaks/screenshot.png"),
    ("g2048",                                         f"{BASE}/run/cont67/regression/g2048_r1/screenshot.png"),
    ("flappycow",                                     f"{BASE}/run/cont67/regression/flappycow_r1/screenshot.png"),
    ("gmdice",                                        f"{BASE}/run/cont67/regression/gmdice_r1/screenshot.png"),
    ("csw composeStopwatch",                          f"{BASE}/run/cont67/regression/csw_r1/screenshot.png"),
]

TW, TH = 540, 960
COLS, ROWS = 4, 4
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
        draw.text((cx+16, cy+TH//2), "anchor " + label.split("(")[-1], fill=(200, 200, 120))
        missing.append(label)
    draw.text((cx+8, cy+TH+6), label[:64], fill=(230, 230, 230))

out = f"{BASE}/evidence/s58/s58_mosaic.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
mosaic.save(out, optimize=True)
h = hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]
print("mosaic:", out, "sha16:", h, "missing_tiles:", missing)
