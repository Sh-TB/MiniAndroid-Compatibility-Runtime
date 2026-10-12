#!/usr/bin/env python3
"""cont56_mosaic.py — build the labeled mosaic of the app faces loaded at
CONT-56 Phase A (one face per app, the x1 runs), plus the anchor controls.
Output: evidence/cont56/CONT56_APP_MOSAIC.png (3 columns)."""
from PIL import Image, ImageDraw, ImageFont

R = "/home/z/my-project"
TILES = [
    ("run/cont56/simplecalc_r1/screenshot.png", "SimpleCalc - FULL PAD VISIBLE"),
    ("run/cont56/opencalc_r1/screenshot.png",   "OpenCalculator - pad visible, left-compressed"),
    ("run/cont56/bmi_r1/screenshot.png",        "BMI Calculator - real form fields + button"),
    ("run/cont56/dooz180_r1/screenshot.png",    "Dooz (180s) - real Scaffold, top bar + FAB"),
    ("run/cont56/dooz_r1/screenshot.png",       "Dooz (15s gate) - honest keep-empty"),
    ("run/cont56/tanana_r1/screenshot.png",     "tananaev Calculator - app bar + rows attached"),
    ("run/cont56/alex_r1/screenshot.png",       "AlexCalc - app bar face"),
    ("run/cont56/gate/unote_r1/screenshot.png", "uNote - anchor"),
    ("run/cont56/gate/micro_r1/screenshot.png", "microtimer - anchor"),
    ("run/cont56/gate/gmdice_r1/screenshot.png","GameMasterDice - anchor"),
    ("run/cont56/gate/ttt_r1/screenshot.png",   "TicTacToe Deluxe - anchor"),
    ("run/cont56/gate/flappy_r1/screenshot.png","FlappyCow - anchor"),
    ("run/cont56/gate/g2048_r1/screenshot.png", "2048 - anchor"),
    ("run/cont56/gate/csw_r1/screenshot.png",   "composeStopwatch - anchor"),
]
COLS = 3
TW, TH = 300, 533          # tile thumb size (1080x1920 -> 300x533)
PAD, LABEL_H = 10, 34

font = None
for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
    try:
        font = ImageFont.truetype(p, 15); break
    except Exception:
        pass

cells = []
for path, label in TILES:
    try:
        im = Image.open(f"{R}/{path}").convert("RGB").resize((TW, TH))
    except Exception as e:
        im = Image.new("RGB", (TW, TH), (255, 0, 255))
    cells.append((im, label, path))

rows = (len(cells) + COLS - 1) // COLS
W = COLS * (TW + PAD) + PAD
H = rows * (TH + LABEL_H + PAD) + PAD + 46
mosaic = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(mosaic)
d.text((PAD + 4, 10), f"MiniAndroid runtime — app faces loaded at HEAD 5c9d72e8 (CONT-56 Phase A, binary 1f81036989a12a7d, all anchors x3 byte-exact 45/45)", fill=(240, 240, 240), font=font)

y0 = 46
for i, (im, label, path) in enumerate(cells):
    cx = PAD + (i % COLS) * (TW + PAD)
    cy = y0 + (i // COLS) * (TH + LABEL_H + PAD)
    mosaic.paste(im, (cx, cy))
    d.text((cx + 2, cy + TH + 6), label, fill=(150, 220, 255), font=font)

mosaic.save(f"{R}/evidence/cont56/CONT56_APP_MOSAIC.png")
print("saved", f"{R}/evidence/cont56/CONT56_APP_MOSAIC.png", mosaic.size)
