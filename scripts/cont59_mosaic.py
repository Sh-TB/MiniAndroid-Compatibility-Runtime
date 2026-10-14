#!/usr/bin/env python3
"""cont59_mosaic.py — refresh the loaded-apps mosaic from the latest gate faces."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
GATE = os.path.join(BASE, "run/cont37/regression")

# app label -> (gate run dir, honest state)
TILES = [
    ("opencalc",   "opencalc_r1",   "OpenCalc: full pad + display (F-NEW-329)"),
    ("simplecalc", "simplecalc_r1", "SimpleCalc: full pad + display 0 (F-NEW-305/336)"),
    ("tanana",     "tanana_r1",     "TananaCalc: real preference text (F-NEW-336)"),
    ("bmi",        None,            "BMI: real form + spinner entries text (F-NEW-331..337)"),
    ("alex",       None,            "AlexCalc: androidx-nav chain (frontier)"),
    ("gmdice",     "gmdice_r1",     "GM Dice: game + hint line (F-NEW-337b)"),
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
    if run:
        p = os.path.join(GATE, run, "screenshot.png")
        if os.path.exists(p):
            return p
    if name == "bmi":
        p = os.path.join(BASE, "run/cont59_bmi_final/screenshot.png")
        if os.path.exists(p):
            return p
    if name == "alex":
        p = os.path.join(BASE, "run/cont37/regression/alex_r1/screenshot.png")
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
d.text((PAD, 10), f"MiniAndroid runtime — loaded-apps mosaic @ CONT-59 (binary c0162daeaee55a10, HEAD 4b9a3281)", fill=(240, 240, 240))

missing = []
for i, tile in enumerate(TILES):
    name, run, label = tile
    x = PAD + (i % cols) * (TW + PAD)
    y = 46 + PAD + (i // cols) * (TH + LABEL + PAD)
    p = face_for(tile)
    if p is None:
        missing.append(name)
        d.rectangle([x, y, x + TW, y + TH], fill=(60, 30, 30))
        d.text((x + 8, y + TH // 2), f"{name}: face missing", fill=(255, 160, 160))
    else:
        img = Image.open(p).convert("RGB").resize((TW, TH))
        mosaic.paste(img, (x, y))
    d.text((x, y + TH + 6), label[:64], fill=(200, 200, 200))

out = os.path.join(BASE, "evidence/cont59/CONT59_APP_MOSAIC.png")
mosaic.save(out)
print("saved", out, "missing:", missing)
