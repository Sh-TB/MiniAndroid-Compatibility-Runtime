#!/usr/bin/env python3
"""cont60_mosaic.py — refresh the loaded-apps mosaic @ CONT-60 (F-NEW-340/341/342)."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
GATE = os.path.join(BASE, "run/cont37/regression")

TILES = [
    ("opencalc",   "opencalc_r1",   "OpenCalc: icons + themed window (F-NEW-341/342)"),
    ("bmi",        None,            "BMI: rows aligned to XML truth (F-NEW-340)"),
    ("simplecalc", "simplecalc_r1", "SimpleCalc: full pad + display 0"),
    ("tanana",     "tanana_r1",     "TananaCalc: real preference text"),
    ("gmdice",     "gmdice_r1",     "GM Dice: game + themed hint (F-NEW-337b)"),
    ("dooz",       "dooz_r1",       "Dooz: Material3 scaffold (compose draw frontier)"),
    ("csw",        "csw_r1",        "ComposeStopwatch (gate anchor)"),
    ("tttdeluxe",  "tttdeluxe_r1",  "TicTacToe Deluxe: real board"),
    ("flappycow",  "flappycow_r1",  "FlappyCow: real game frame"),
    ("g2048",      "g2048_r1",      "2048: REAL_APP_CONTENT"),
    ("microtimer", "microtimer_r1", "MicroTimer: real UI"),
    ("unote",      "unote_r1",      "uNote: real editor UI"),
]

def face_for(tile):
    name, run, _ = tile
    if name == "bmi":
        p = os.path.join(BASE, "run/cont60/bmi_w1_fixed/screenshot.png")
        if os.path.exists(p):
            return p
    if run:
        p = os.path.join(GATE, run, "screenshot.png")
        if os.path.exists(p):
            return p
    return None

TW, TH, PAD, LABEL = 400, 711, 12, 34
cols = 4
rows = (len(TILES) + cols - 1) // cols
W = cols * TW + (cols + 1) * PAD
H = rows * (TH + LABEL) + (rows + 1) * PAD + 46
mosaic = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(mosaic)
d.text((PAD, 10), "MiniAndroid runtime — loaded-apps mosaic @ CONT-60 "
                  "(binary d99fe6e1596fed06, HEAD 80e342f8)", fill=(240, 240, 240))
y = PAD + 46
for r in range(rows):
    x = PAD
    for c in range(cols):
        i = r * cols + c
        if i >= len(TILES):
            break
        name, run, label = TILES[i]
        p = face_for(TILES[i])
        tile = Image.new("RGB", (TW, TH), (60, 60, 66))
        if p:
            im = Image.open(p).convert("RGB").resize((TW, TH))
            tile.paste(im, (0, 0))
        else:
            d2 = ImageDraw.Draw(tile)
            d2.text((10, TH // 2), "no face", fill=(200, 200, 200))
        mosaic.paste(tile, (x, y))
        d.text((x + 2, y + TH + 4), label, fill=(220, 220, 220))
        x += TW + PAD
    y += TH + LABEL + PAD

out = os.path.join(BASE, "evidence/cont60/CONT60_APP_MOSAIC.png")
mosaic.save(out)
print("mosaic saved:", out, mosaic.size)
