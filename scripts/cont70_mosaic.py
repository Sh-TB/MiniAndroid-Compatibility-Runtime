#!/usr/bin/env python3
"""cont70_mosaic.py — build the CONT-70 ant-army evidence mosaic (4x5 grid).

Story rows: the ANT improvements (bouncy complete menu, g2048/tttdeluxe
canvas-text real-size before/after, font probe two-face proof) + the wall
anchors at the CONT-70 binary.
"""
from PIL import Image, ImageDraw, ImageFont
import os, hashlib

BASE = "/home/z/my-project"
FONT = None
for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    if os.path.exists(p):
        FONT = ImageFont.truetype(p, 17)
        break

TILES = [
    # ── the ANT story ──
    ("bouncy BEFORE (dd0c1425, no top bar)",        f"{BASE}/evidence/cont70/before/bouncy_old_dd0c14257fa1f2af.png"),
    ("bouncy AFTER keys() law (1b87e9ef COMPLETE)", f"{BASE}/run/cont70/accept/v2_bouncy/screenshot.png"),
    ("g2048 BEFORE (59ca1526 tiny text)",           f"{BASE}/evidence/cont70/before/g2048_old_59ca1526611c4622.png"),
    ("g2048 AFTER real-size law (f43face0)",        f"{BASE}/run/cont70/wall_sweep/g2048_r1/screenshot.png"),
    ("tttdeluxe BEFORE (af609429 tiny text)",       f"{BASE}/evidence/cont70/before/tttdeluxe_old_af6094295ecb50e3.png"),
    ("tttdeluxe AFTER real-size law (db1d633d)",    f"{BASE}/run/cont70/wall_sweep/tttdeluxe_r1/screenshot.png"),
    ("font probe tiny-text era (canvas bug face)",  f"{BASE}/evidence/cont70/before/font_probe_tinytext.png"),
    ("font probe AFTER (serif vs system, 64px)",    f"{BASE}/run/cont70/accept/font_probe5/screenshot.png"),
    ("memory WARM (record c559b630 intact)",        f"{BASE}/run/cont70/accept/v2_mem/screenshot.png"),
    ("dooz 180s control (c94da5a9 x3 intact)",      f"{BASE}/run/cont70/regression/dooz180_r1/screenshot.png"),
    # ── the 12-row wall at the CONT-70 binary ──
    ("dooz15s (31ddd4d5)",                          f"{BASE}/run/cont70/wall_sweep/dooz_r1/screenshot.png"),
    ("csw (d3c26b73)",                              f"{BASE}/run/cont70/wall_sweep/csw_r1/screenshot.png"),
    ("flappycow (13cf4746)",                        f"{BASE}/run/cont70/wall_sweep/flappycow_r1/screenshot.png"),
    ("gmdice (3891679d)",                           f"{BASE}/run/cont70/wall_sweep/gmdice_r1/screenshot.png"),
    ("microtimer (bbd350b6)",                       f"{BASE}/run/cont70/wall_sweep/microtimer_r1/screenshot.png"),
    ("opencalc (f25b754c)",                         f"{BASE}/run/cont70/wall_sweep/opencalc_r1/screenshot.png"),
    ("simplecalc (2ac5d8d0)",                       f"{BASE}/run/cont70/wall_sweep/simplecalc_r1/screenshot.png"),
    ("tanana (afe0bd8d)",                           f"{BASE}/run/cont70/wall_sweep/tanana_r1/screenshot.png"),
    ("unote (90a67cc1)",                            f"{BASE}/run/cont70/wall_sweep/unote_r1/screenshot.png"),
    ("gate A probe 98/1/0",                         f"{BASE}/run/cont70/gatea_probe_ds/screenshot.png"),
]

TW, TH = 540, 960
COLS = 4
ROWS = (len(TILES) + COLS - 1) // COLS
mosaic = Image.new("RGB", (COLS*TW, ROWS*(TH+40)), (18, 18, 22))
draw = ImageDraw.Draw(mosaic)
for i, (label, path) in enumerate(TILES):
    r, c = divmod(i, COLS)
    x, y = c*TW, r*(TH+40)
    if os.path.exists(path):
        im = Image.open(path).convert("RGB").resize((TW, TH))
        mosaic.paste(im, (x, y+40))
    else:
        draw.rectangle([x, y+40, x+TW, y+40+TH], fill=(60, 30, 30))
        draw.text((x+12, y+TH//2), "MISSING: " + os.path.basename(path), fill=(255,120,120), font=FONT)
    draw.text((x+10, y+9), label, fill=(240, 240, 240), font=FONT)
out = f"{BASE}/evidence/cont70/cont70_mosaic.png"
mosaic.save(out)
h = hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]
print("mosaic:", out, "sha16:", h, "tiles:", len(TILES))
