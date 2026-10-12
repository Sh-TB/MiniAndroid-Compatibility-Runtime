#!/usr/bin/env python3
"""cont57_mosaic.py — CONT-57 mosaic: the OpenCalc BEFORE/AFTER healing pair
(F-NEW-329 ConstraintLayout guideline + dimension laws) plus the standing
app-face tiles. Output: evidence/cont57/CONT57_APP_MOSAIC.png."""
from PIL import Image, ImageDraw, ImageFont

R = "/home/z/my-project"
TILES = [
    ("run/cont56c/oc_dump2/screenshot.png",        "OpenCalc BEFORE - pad compressed 45%, display gone"),
    ("run/cont37/regression/opencalc_r1/screenshot.png", "OpenCalc AFTER F-NEW-329 - FULL pad + display areas"),
    ("run/cont56/simplecalc_r1/screenshot.png",    "SimpleCalc - FULL PAD VISIBLE"),
    ("run/cont56/bmi_r1/screenshot.png",           "BMI Calculator - real form fields + button"),
    ("run/cont56/dooz180_r1/screenshot.png",       "Dooz (180s) - real Scaffold, top bar + FAB"),
    ("run/cont56/dooz_r1/screenshot.png",          "Dooz (15s gate) - honest keep-empty"),
    ("run/cont56/tanana_r1/screenshot.png",        "tananaev Calculator - app bar + rows attached"),
    ("run/cont56/alex_r1/screenshot.png",          "AlexCalc - app bar face"),
    ("run/cont56/gate/unote_r1/screenshot.png",    "uNote - anchor"),
    ("run/cont56/gate/micro_r1/screenshot.png",    "microtimer - anchor"),
    ("run/cont56/gate/gmdice_r1/screenshot.png",   "GameMasterDice - anchor"),
    ("run/cont56/gate/ttt_r1/screenshot.png",      "TicTacToe Deluxe - anchor"),
    ("run/cont56/gate/flappy_r1/screenshot.png",   "FlappyCow - anchor"),
    ("run/cont56/gate/g2048_r1/screenshot.png",    "2048 - anchor"),
    ("run/cont56/gate/csw_r1/screenshot.png",      "composeStopwatch - anchor"),
]
COLS = 3
TW, TH = 300, 533
PAD, LABEL_H = 10, 34

font = None
for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
    try:
        font = ImageFont.truetype(p, 14)
        break
    except Exception:
        pass

cells = []
for path, label in TILES:
    try:
        im = Image.open(f"{R}/{path}").convert("RGB").resize((TW, TH))
        cells.append((im, label))
    except Exception as e:
        print("skip", path, e)

rows = (len(cells) + COLS - 1) // COLS
W = COLS * (TW + PAD) + PAD
H = rows * (TH + LABEL_H + PAD) + PAD + 40
canvas = Image.new("RGB", (W, H), (24, 24, 28))
d = ImageDraw.Draw(canvas)
d.text((PAD + 4, 10), "MiniAndroid runtime - app faces at CONT-57 (binary 93110eacb3a1cf41, F-NEW-329)",
       fill=(240, 240, 240), font=font)

y0 = 40
for i, (im, label) in enumerate(cells):
    r, c = divmod(i, COLS)
    x = PAD + c * (TW + PAD)
    y = y0 + r * (TH + LABEL_H + PAD)
    canvas.paste(im, (x, y))
    color = (120, 220, 140) if ("AFTER" in label or "FULL" in label or "real" in label) else (200, 200, 200)
    d.text((x + 2, y + TH + 4), label, fill=color, font=font)

out = f"{R}/evidence/cont57/CONT57_APP_MOSAIC.png"
canvas.save(out)
print("mosaic:", out, canvas.size)
