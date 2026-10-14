#!/usr/bin/env python3
"""cont64_mosaic.py — refresh the loaded-apps mosaic @ CONT-64 W1.
Tiles: the 6 user apps + dooz180 from the CONT-64 survey runs at HEAD
e3475812-era binary + the anchor wall from run/cont63/regression."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
OUT = os.path.join(BASE, "evidence/cont64/cont64_mosaic.png")

C64 = os.path.join(BASE, "run/cont64")
C63 = os.path.join(BASE, "run/cont63/regression")

TILES = [
    (os.path.join(C64, "dooz180/screenshot.png"),   "Dooz @180s: icons render (F-NEW-351)"),
    (os.path.join(C64, "opencalc/screenshot.png"),  "OpenCalc: full-width pad"),
    (os.path.join(C64, "simplecalc/screenshot.png"),"SimpleCalc: full pad + display"),
    (os.path.join(C64, "tanana/screenshot.png"),    "TananaCalc: preference text"),
    (os.path.join(C64, "bmi/screenshot.png"),       "BMI: dark-theme form"),
    (os.path.join(C64, "alex/screenshot.png"),      "AlexCalc: blue-bar (frontier)"),
    (os.path.join(C63, "csw_r1/screenshot.png"),    "ComposeStopwatch: title in view"),
    (os.path.join(C63, "tttdeluxe_r1/screenshot.png"), "TicTacToe Deluxe: real board"),
    (os.path.join(C63, "flappycow_r1/screenshot.png"), "FlappyCow: real game frame"),
    (os.path.join(C63, "g2048_r1/screenshot.png"),  "2048: REAL_APP_CONTENT"),
    (os.path.join(C63, "gmdice_r1/screenshot.png"), "GM Dice: game + themed hint"),
    (os.path.join(C63, "unote_r1/screenshot.png"),  "uNote: real editor UI"),
    ("run/cont64/f352_det/screenshot.png",          "F-NEW-352 probe: 9/9 tint laws"),
]

TILE_W, TILE_H, PAD, LABEL_H = 360, 640, 10, 34
COLS = 4
ROWS = (len(TILES) + COLS - 1) // COLS
W = COLS * (TILE_W + PAD) + PAD
H = ROWS * (TILE_H + LABEL_H + PAD) + PAD + 44

img = Image.new("RGB", (W, H), (24, 24, 28))
d = ImageDraw.Draw(img)
d.text((PAD, 8), "MiniAndroid CONT-64 W1 — loaded-app wall (HEAD e3475812-era)", fill=(230, 230, 235))

y0 = 44
for idx, (path, label) in enumerate(TILES):
    r, c = divmod(idx, COLS)
    x = PAD + c * (TILE_W + PAD)
    y = y0 + r * (TILE_H + LABEL_H + PAD)
    d.text((x, y), label, fill=(200, 205, 215))
    try:
        t = Image.open(path).convert("RGB").resize((TILE_W, TILE_H))
        img.paste(t, (x, y + LABEL_H))
    except Exception as e:
        d.rectangle([x, y + LABEL_H, x + TILE_W, y + LABEL_H + TILE_H],
                    outline=(120, 40, 40), width=2)
        d.text((x + 8, y + LABEL_H + 8), "MISSING: " + os.path.basename(path), fill=(220, 90, 90))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print("mosaic:", OUT, img.size)
