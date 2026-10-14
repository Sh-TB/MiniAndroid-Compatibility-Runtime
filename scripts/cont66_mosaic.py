#!/usr/bin/env python3
"""cont66_mosaic.py — refresh the loaded-apps mosaic @ CONT-66.
Tiles: the 9 unchanged anchors + the 2 XML-true re-pinned faces (microtimer,
simplecalc post F-NEW-360/361) + the fixed BMI form + the fresh survey strip."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
OUT = os.path.join(BASE, "evidence/cont66/cont66_mosaic.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

R65 = os.path.join(BASE, "run/cont65/regression")
R66 = os.path.join(BASE, "run/cont66/regression")
R66S = os.path.join(BASE, "run/cont66/survey")

TILES = [
    (os.path.join(R66S, "simplecalc/screenshot.png"),
     "SimpleCalc: display 0 @40sp + 16dp pad (F-NEW-360)"),
    (os.path.join(R66S, "opencalc/screenshot.png"),
     "OpenCalc: full pad + overflow menu"),
    (os.path.join(BASE, "run/cont66/bmi_fix/screenshot.png"),
     "BMI: form inset 42px, XML-true (F-NEW-360)"),
    (os.path.join(R66, "microtimer_r1/screenshot.png"),
     "MicroTimer: axis margins 2.5dp (F-NEW-361)"),
    (os.path.join(R66, "tanana_r1/screenshot.png"),     "TananaCalc: unchanged"),
    (os.path.join(R66, "csw_r1/screenshot.png"),        "ComposeStopwatch: unchanged"),
    (os.path.join(R66, "tttdeluxe_r1/screenshot.png"),  "TicTacToe Deluxe: unchanged"),
    (os.path.join(R66, "flappycow_r1/screenshot.png"),  "FlappyCow: unchanged"),
    (os.path.join(R66, "g2048_r1/screenshot.png"),      "2048: unchanged"),
    (os.path.join(R66, "gmdice_r1/screenshot.png"),     "GM Dice: unchanged"),
    (os.path.join(R66, "unote_r1/screenshot.png"),      "uNote: unchanged"),
    (os.path.join(R66, "dooz180_r1/screenshot.png"),    "Dooz @180s: unchanged"),
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
        draw.text((x + 8, y + 8), "MISSING: " + os.path.basename(path), fill=(255, 90, 90))
    draw.text((x + 4, y + TILE_H + 8), label, fill=(230, 230, 230))

canvas.save(OUT)
print("mosaic:", OUT, canvas.size)
