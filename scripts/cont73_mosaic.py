#!/usr/bin/env python3
"""cont73_mosaic.py — 10-tile evidence mosaic for the CONT-73 triage rows."""
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
    ("A1 Memory eu.quelltext 35295a57 REAL",        "eu.quelltext.memory"),
    ("A2 ChessClock fe3ae116 == record",            "com.chessclock.android"),
    ("A3 Ball2Box ARM-only 48-gray (MISMATCH)",     "com.simondalvai.ball2box"),
    ("A4 OpenSurge ARM-only refusal (MISMATCH)",    "org.opensurge2d.surgeengine"),
    ("A5 Guandan APP_DRAW_OPS gap (blank)",         "page.codeberg.lanticy.guandan"),
    ("B6 PFSudoku be640e39 REAL",                   "org.secuso.privacyfriendlysudoku"),
    ("B7 PFMemory 3a3ba873 == TRUE-COLD record",    "org.secuso.privacyfriendlymemory"),
    ("B8 PFDame 70033bc0 REAL",                     "org.secuso.privacyfriendlydame"),
    ("B9 PFSolitaire aa53f6f1 REAL",                "org.secuso.privacyfriendlysolitaire"),
    ("B10 AndStatus2048 NO_ROOT kotlin-reflect",    "org.andstatus.game2048"),
]

TW, TH, HH = 300, 533, 46
COLS = 5
rows = (len(TILES) + COLS - 1) // COLS
W, H = COLS * TW, rows * (TH + HH)
M = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(M)

for i, (label, pkg) in enumerate(TILES):
    cx, cy = (i % COLS) * TW, (i // COLS) * (TH + HH)
    p = f"{BASE}/run/cont73/triage/{pkg}/screenshot.png"
    d.rectangle([cx, cy, cx + TW, cy + HH], fill=(30, 34, 44))
    d.text((cx + 6, cy + 6), label, fill=(240, 240, 240), font=FONT)
    if os.path.exists(p):
        im = Image.open(p).convert("RGB").resize((TW - 4, TH - 4))
        M.paste(im, (cx + 2, cy + HH + 2))
    else:
        d.text((cx + 8, cy + HH + 40), "MISSING", fill=(255, 90, 90), font=FONT)

OUT = f"{BASE}/evidence/cont73/cont73_mosaic.png"
M.save(OUT)
h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
print("mosaic:", OUT, h, f"{os.path.getsize(OUT)//1024}KB")
