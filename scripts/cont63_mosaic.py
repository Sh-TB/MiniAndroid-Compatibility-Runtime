#!/usr/bin/env python3
"""cont63_mosaic.py — refresh the loaded-apps mosaic @ CONT-63 W1 (F-NEW-351:
the material icons render — dooz settings gear / undo arrow / games glyph /
info disc replace the four black squares). Tiles from the fresh regression
runs at binary a00f331a07dfa961."""
import os
from PIL import Image, ImageDraw

BASE = "/home/z/my-project"
REG = os.path.join(BASE, "run/cont63/regression")
OUT = os.path.join(BASE, "evidence/cont63/cont63_mosaic.png")

TILES = [
    ("dooz180", "dooz180_r1", "Dooz @180s: ICONS RENDER (F-NEW-351)"),
    ("opencalc", "opencalc_r1", "OpenCalc: full-width pad (theme laws)"),
    ("simplecalc", "simplecalc_r1", "SimpleCalc: full pad + display 0"),
    ("tanana", "tanana_r1", "TananaCalc: real preference text (F344 fan-out)"),
    ("bmi", None, "BMI: dark-theme form (windowBackground laws)"),
    ("csw", "csw_r1", "ComposeStopwatch: title in view (F344)"),
    ("tttdeluxe", "tttdeluxe_r1", "TicTacToe Deluxe: real board"),
    ("flappycow", "flappycow_r1", "FlappyCow: real game frame"),
    ("g2048", "g2048_r1", "2048: REAL_APP_CONTENT"),
    ("gmdice", "gmdice_r1", "GM Dice: game + themed hint"),
    ("microtimer", "microtimer_r1", "MicroTimer: real UI"),
    ("unote", "unote_r1", "uNote: real editor UI"),
    ("f351probe", None, "F-NEW-351 probe: 14/14 vector laws"),
]

def face_for(name, run):
    if name == "bmi":
        return os.path.join(BASE, "run/cont63/bmi/screenshot.png")
    if name == "f351probe":
        return os.path.join(BASE, "run/cont63/f351_det1/screenshot.png")
    return os.path.join(REG, run, "screenshot.png")

TILE_W, TILE_H, PAD, LABEL_H = 360, 640, 10, 34
COLS = 4
ROWS = (len(TILES) + COLS - 1) // COLS
W = COLS * (TILE_W + PAD) + PAD
H = ROWS * (TILE_H + LABEL_H + PAD) + PAD + 40
mosaic = Image.new("RGB", (W, H), (24, 26, 32))
draw = ImageDraw.Draw(mosaic)
draw.text((PAD, 12),
          "MiniAndroid @ CONT-63 W1 (binary a00f331a07dfa961) — F-NEW-351: "
          "compose material icons render as real vectors",
          fill=(240, 240, 245))

for i, (name, run, label) in enumerate(TILES):
    col, row = i % COLS, i // COLS
    x = PAD + col * (TILE_W + PAD)
    y = 40 + row * (TILE_H + LABEL_H + PAD)
    p = face_for(name, run)
    if os.path.exists(p):
        im = Image.open(p).convert("RGB").resize((TILE_W, TILE_H), Image.LANCZOS)
        mosaic.paste(im, (x, y))
    else:
        draw.rectangle([x, y, x + TILE_W, y + TILE_H], outline=(200, 60, 60))
    draw.text((x + 2, y + TILE_H + 4), label, fill=(200, 205, 215))

mosaic.save(OUT)
print("mosaic:", OUT, mosaic.size)
