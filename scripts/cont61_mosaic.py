#!/usr/bin/env python3
"""cont61_mosaic.py — refresh the loaded-apps mosaic @ CONT-61 (F-NEW-344:
the compose text intrinsic leg — dooz title/button glyphs + csw title
recovered). Reuses the cont60 layout; tiles come from the fresh W1 gate
runs (run/cont37/regression, the 4436cc61 binary) + the BMI fix face."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
GATE = os.path.join(BASE, "run/cont37/regression")

TILES = [
    ("opencalc",   "opencalc_r1",   "OpenCalc: icons + themed window (F341/342)"),
    ("bmi",        None,            "BMI: rows aligned to XML truth (F340)"),
    ("simplecalc", "simplecalc_r1", "SimpleCalc: full pad + display 0"),
    ("tanana",     "tanana_r1",     "TananaCalc: real preference text (F336)"),
    ("gmdice",     "gmdice_r1",     "GM Dice: game + themed hint (F337b)"),
    ("dooz",       "dooz180_r1",    "Dooz @180s: title+button GLYPHS (F344)"),
    ("csw",        "csw_r1",        "ComposeStopwatch: title in view (F344)"),
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
d.text((PAD, 10), "MiniAndroid runtime — loaded-apps mosaic @ CONT-61 W1 "
                  "(F-NEW-344 compose text; HEAD 4436cc61)", fill=(240, 240, 240))
y = PAD + 46
for r in range(rows):
    x = PAD
    for c in range(cols):
        i = r * cols + c
        if i >= len(TILES):
            break
        name, run, label = TILES[i]
        p = face_for(TILES[i])
        if p:
            im = Image.open(p).convert("RGB").resize((TW, TH))
            mosaic.paste(im, (x, y))
        else:
            d.rectangle([x, y, x + TW, y + TH], fill=(40, 40, 48))
        d.text((x + 4, y + TH + 8), f"{i+1}. {label}", fill=(210, 210, 210))
        x += TW + PAD
    y += TH + LABEL + PAD
out = os.path.join(BASE, "evidence/cont61/CONT61_APP_MOSAIC.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
mosaic.save(out)
print("saved", out, mosaic.size)
