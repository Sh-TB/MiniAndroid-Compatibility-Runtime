#!/usr/bin/env python3
"""cont65_mosaic.py — refresh the loaded-apps mosaic @ CONT-65.
Tiles: the capaudit capability-probe face (22/22) + the 11-app anchor wall
from the CONT-65 zero-drift regression + the F-358 string-law face."""
import json
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
OUT = os.path.join(BASE, "evidence/cont65/cont65_mosaic.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

REG = os.path.join(BASE, "run/cont65/regression")

TILES = [
    (os.path.join(BASE, "run/cont65/webpdiag/screenshot.png"),
     "CAPAUDIT probe: 22/22 capability rows"),
    (os.path.join(REG, "simplecalc_r1/screenshot.png"), "SimpleCalc: full pad + display"),
    (os.path.join(REG, "opencalc_r1/screenshot.png"),   "OpenCalc: full-width pad"),
    (os.path.join(REG, "tanana_r1/screenshot.png"),     "TananaCalc: preference text"),
    (os.path.join(REG, "csw_r1/screenshot.png"),        "ComposeStopwatch: title in view"),
    (os.path.join(REG, "tttdeluxe_r1/screenshot.png"),  "TicTacToe Deluxe: real board"),
    (os.path.join(REG, "flappycow_r1/screenshot.png"),  "FlappyCow: real game frame"),
    (os.path.join(REG, "g2048_r1/screenshot.png"),      "2048: REAL_APP_CONTENT"),
    (os.path.join(REG, "gmdice_r1/screenshot.png"),     "GM Dice: game + themed hint"),
    (os.path.join(REG, "unote_r1/screenshot.png"),      "uNote: real editor UI"),
    (os.path.join(REG, "dooz180_r1/screenshot.png"),    "Dooz @180s: Material3 + icons"),
    (os.path.join(BASE, "run/cont64/f352_det/screenshot.png"),
     "F-NEW-352 probe: 9/9 tint laws"),
]

TILE_W, TILE_H, PAD, LABEL_H = 360, 640, 10, 34

cols = 4
rows = (len(TILES) + cols - 1) // cols
W = cols * (TILE_W + PAD) + PAD
H = rows * (TILE_H + LABEL_H + PAD) + PAD
canvas = Image.new("RGB", (W, H), (18, 18, 22))
draw = ImageDraw.Draw(canvas)

for i, (path, label) in enumerate(TILES):
    r, c = divmod(i, cols)
    x = PAD + c * (TILE_W + PAD)
    y = PAD + r * (TILE_H + LABEL_H + PAD)
    if os.path.exists(path):
        im = Image.open(path).convert("RGB")
        im.thumbnail((TILE_W, TILE_H))
        ox = x + (TILE_W - im.width) // 2
        oy = y + (TILE_H - im.height) // 2
        canvas.paste(im, (ox, oy))
    else:
        draw.rectangle([x, y, x + TILE_W, y + TILE_H], outline=(90, 90, 90))
        draw.text((x + 8, y + TILE_H // 2), "MISSING: " + os.path.basename(path),
                  fill=(200, 120, 120))
    draw.text((x + 2, y + TILE_H + 6), label[:58], fill=(235, 235, 235))

canvas.save(OUT)
print("mosaic:", OUT, canvas.size)
meta = {
    "tiles": [t[1] for t in TILES],
    "sources": [t[0] for t in TILES],
    "gate": "36/36 anchor wall MATCH (11 apps x3 + dooz180 x3) zero drift",
    "battery": "capaudit 22/22 pixel rows PASS",
}
json.dump(meta, open(os.path.join(BASE, "evidence/cont65/cont65_mosaic.json"), "w"),
          indent=1)
