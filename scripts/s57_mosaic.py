#!/usr/bin/env python3
"""s57_mosaic.py — build the S57 evidence mosaic (8 tiles) with labels."""
from PIL import Image, ImageDraw, ImageFont
import os

TILES = [
    ("run/s57/random3/fishrings_run1/screenshot.png",  "fishrings  a341e3ad (REAL content x3)"),
    ("run/s57/random3/klondike_run1/screenshot.png",   "klondike   1dd1c435 (26.3% content x3)"),
    ("run/s57/random3/notes_run1/screenshot.png",      "notes_secuso  eb5ebd55 (UI bar x3)"),
    ("run/s57/anchors/chess_run1/screenshot.png",      "chess      b5a7a35d x3"),
    ("run/s57/anchors/opencalc_run1/screenshot.png",   "opencalc   a976d2f9 x3"),
    ("run/s57/anchors/microtimer_run1/screenshot.png", "microtimer da73010a x3"),
    ("run/s57/anchors/unote_run1/screenshot.png",      "unote      4f1a9e4e x3"),
    ("run/s57/anchors/dooz_run1/screenshot.png",       "dooz  d602648e (blank honest; F084 loop FIXED)"),
]
TW, TH = 324, 576  # scale 1080x1920 -> 0.3
COLS, ROWS = 4, 2
LABEL_H = 34
W, H = COLS * TW, ROWS * (TH + LABEL_H)
canvas = Image.new("RGB", (W, H), (18, 18, 24))
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
except Exception:
    font = ImageFont.load_default()

for i, (path, label) in enumerate(TILES):
    cx, cy = (i % COLS) * TW, (i // COLS) * (TH + LABEL_H)
    if os.path.exists(path):
        im = Image.open(path).convert("RGB").resize((TW - 4, TH - 4))
        canvas.paste(im, (cx + 2, cy + 2))
    else:
        draw.text((cx + 10, cy + TH // 2), "MISSING: " + path, fill=(255, 80, 80), font=font)
    draw.text((cx + 6, cy + TH + 2), label, fill=(230, 230, 230), font=font)

out = "/home/z/my-project/evidence/s57/s57_mosaic.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
canvas.save(out)
print("saved", out, canvas.size)
