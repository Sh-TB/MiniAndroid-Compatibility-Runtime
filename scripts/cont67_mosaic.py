#!/usr/bin/env python3
"""cont67_mosaic.py — refresh the loaded-apps mosaic @ CONT-67.
Tiles: the 12 anchor faces (all unchanged at the F-NEW-363/364 binary) +
the 3-random-app generality evidence (chessclock FIXED face, klondike menu +
game faces, notes face) + the dooz playability test face."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
OUT = os.path.join(BASE, "evidence/cont67/cont67_mosaic.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

R67 = os.path.join(BASE, "run/cont67/regression")

TILES = [
    (os.path.join(BASE, "run/cont67/final_chessclock/screenshot.png"),
     "ChessClock 29 (random #1): FIXED face (F-NEW-363)"),
    (os.path.join(BASE, "run/cont67/klondike20/screenshot.png"),
     "Klondike (random #2): menu after 5s splash"),
    (os.path.join(BASE, "run/cont67/final_klondike_game/screenshot.png"),
     "Klondike: GAME face after New Game tap"),
    (os.path.join(BASE, "run/cont67/final_notes/screenshot.png"),
     "SecusoNotes (random #3): theme gate residual"),
    (os.path.join(R67, "opencalc_r1/screenshot.png"), "OpenCalc: unchanged"),
    (os.path.join(R67, "simplecalc_r1/screenshot.png"), "SimpleCalc: unchanged"),
    (os.path.join(R67, "microtimer_r1/screenshot.png"), "MicroTimer: unchanged"),
    (os.path.join(R67, "tanana_r1/screenshot.png"), "TananaCalc: unchanged"),
    (os.path.join(R67, "csw_r1/screenshot.png"), "ComposeStopwatch: unchanged"),
    (os.path.join(R67, "tttdeluxe_r1/screenshot.png"), "TicTacToe Deluxe: unchanged"),
    (os.path.join(R67, "g2048_r1/screenshot.png"), "2048: unchanged"),
    (os.path.join(R67, "gmdice_r1/screenshot.png"), "GM Dice: unchanged"),
    (os.path.join(R67, "unote_r1/screenshot.png"), "uNote: unchanged"),
    (os.path.join(R67, "flappycow_r1/screenshot.png"), "FlappyCow: unchanged"),
    (os.path.join(R67, "dooz180_r1/screenshot.png"), "Dooz @180s: unchanged"),
    (os.path.join(BASE, "run/cont67/capaudit/screenshot.png"),
     "CAPAUDIT probe: 22/22 PASS"),
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
        canvas.paste(im, (x + (TILE_W - im.width) // 2,
                          y + (TILE_H - im.height) // 2))
    else:
        draw.rectangle([x, y, x + TILE_W, y + TILE_H], outline=(90, 90, 90))
    draw.text((x + 2, y + TILE_H + 8), label, fill=(220, 220, 220))

canvas.save(OUT)
print("mosaic:", OUT, canvas.size)
