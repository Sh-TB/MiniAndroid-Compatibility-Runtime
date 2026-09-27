#!/usr/bin/env python3
"""Build labeled contact sheets for all 128 S107-wave screenshots (run1), 4 sheets."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path('/home/z/my-project')
EV = BASE / 'evidence/s107_games'
OUT = BASE / 'evidence/audit_s107'
OUT.mkdir(parents=True, exist_ok=True)
rows = json.load(open(OUT / 'audit_table.json'))

TW, TH = 268, 470   # thumb size (1080x1920 / 4.03)
COLS = 4
PER_SHEET = 32

try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
except Exception:
    font = ImageFont.load_default()

VERDICT_COLOR = {
    'REOPEN_BLANK_MONOCHROME': (200, 30, 30),
    'REOPEN_BLANK_SOLID': (200, 30, 30),
    'REOPEN_NEAR_BLANK': (230, 120, 0),
    'REOPEN_BACKGROUND_ONLY': (230, 160, 0),
    'PENDING_3RUN_CONTENT_BOTH': (20, 130, 40),
}

for sheet_i in range(0, len(rows), PER_SHEET):
    chunk = rows[sheet_i:sheet_i + PER_SHEET]
    rows_n = (len(chunk) + COLS - 1) // COLS
    W = COLS * (TW + 8) + 8
    H = rows_n * (TH + 56) + 8
    sheet = Image.new('RGB', (W, H), (24, 24, 24))
    dr = ImageDraw.Draw(sheet)
    for k, r in enumerate(chunk):
        gy, gx = divmod(k, COLS)
        x0 = 8 + gx * (TW + 8)
        y0 = 8 + gy * (TH + 56)
        shot = EV / f"{r['package']}_run1/screenshot.png"
        if shot.exists():
            im = Image.open(shot).convert('RGB').resize((TW, TH))
            sheet.paste(im, (x0, y0))
        color = VERDICT_COLOR.get(r['audit'], (128, 128, 128))
        short = r['audit'].replace('REOPEN_', 'RE:').replace('PENDING_3RUN_CONTENT_BOTH', 'CONTENT?3RUN')
        label = f"#{r['number']} {r['package'][:30]}"
        dr.rectangle([x0, y0 + TH, x0 + TW, y0 + TH + 52], fill=(12, 12, 12), outline=color)
        dr.text((x0 + 4, y0 + TH + 3), label, fill=(240, 240, 240), font=font)
        dr.text((x0 + 4, y0 + TH + 26), short, fill=color, font=font)
    p = OUT / f'contact_sheet_{sheet_i // PER_SHEET + 1}.png'
    sheet.save(p)
    print(p, sheet.size, len(chunk), 'titles')
