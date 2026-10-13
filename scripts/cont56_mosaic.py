#!/usr/bin/env python3
# cont56_mosaic.py — honest mosaic of the loaded apps at the current HEAD binary.
from PIL import Image, ImageDraw, ImageFont
import os

OUT = "/home/z/my-project/evidence/cont56"
os.makedirs(OUT, exist_ok=True)

CELL_W, CELL_H, LABEL_H = 540, 960, 56
COLS = 3

apps = [
    ("SimpleCalc FULL PAD (display empty)", "/home/z/my-project/run/cont56c/simplecalc_run1/screenshot.png", "PARTIAL"),
    ("OpenCalc (pad compressed L45%)", "/home/z/my-project/run/cont56b/anchors/opencalc_run1/screenshot.png", "PARTIAL"),
    ("BMI REAL FORM (new!)", "/home/z/my-project/run/cont56c/bmi_run1/screenshot.png", "REAL-CONTENT"),
    ("tanana (fully white)", "/home/z/my-project/run/cont56c/tanana_run1/screenshot.png", "WHITE"),
    ("AlexCalc (androidx-nav, next)", "/home/z/my-project/run/cont56c/alex_run1/screenshot.png", "DARK"),
    ("Dooz 180s (compose draw)", "/home/z/my-project/run/cont56c/dooz180_run1/screenshot.png", "WHITE"),
    ("Chess (uniform dark)", "/home/z/my-project/run/cont56b/anchors/chess_run1/screenshot.png", "DARK"),
    ("MicroTimer", "/home/z/my-project/run/cont56b/anchors/microtimer_run1/screenshot.png", "ANCHOR"),
    ("UNote", "/home/z/my-project/run/cont56b/anchors/unote_run1/screenshot.png", "ANCHOR"),
]

rows = (len(apps) + COLS - 1) // COLS
W, H = COLS * CELL_W, rows * (CELL_H + LABEL_H)
canvas = Image.new("RGB", (W, H), (18, 18, 22))
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
except Exception:
    font = ImageFont.load_default()

for i, (label, path, status) in enumerate(apps):
    r, c = divmod(i, COLS)
    x0, y0 = c * CELL_W, r * (CELL_H + LABEL_H)
    color = {"REAL-CONTENT": (46, 204, 113), "PARTIAL": (241, 196, 15),
             "WHITE": (149, 165, 166), "DARK": (231, 76, 60),
             "ANCHOR": (52, 152, 219)}[status]
    draw.rectangle([x0, y0, x0 + CELL_W, y0 + LABEL_H], fill=color)
    draw.text((x0 + 10, y0 + 14), f"{label}  [{status}]", fill=(0, 0, 0), font=font)
    if os.path.exists(path):
        im = Image.open(path).convert("RGB").resize((CELL_W, CELL_H))
        canvas.paste(im, (x0, y0 + LABEL_H))
    else:
        draw.rectangle([x0, y0 + LABEL_H, x0 + CELL_W, y0 + LABEL_H + CELL_H], fill=(60, 60, 66))

out = f"{OUT}/cont56_mosaic.png"
canvas.save(out)
print(out, canvas.size)
