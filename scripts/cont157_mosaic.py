#!/usr/bin/env python3
"""cont157_mosaic.py — the کاشی موزایکی (mosaic tile) of the three target
apps' execution at the CONT-157 binary: dooz before/after the draw-path
laws, opencalc, telegram. 2x2 grid, per-tile face16 + nonwhite% + note.
Labels in English (PIL has no RTL shaper for Persian); the ledger text
carries the Persian explanation."""
import hashlib
from PIL import Image, ImageDraw, ImageFont

TILE_W, TILE_H = 360, 640
PAD = 12
HEAD = 34

def tile(path, title, note, border):
    im = Image.open(path).convert('RGB')
    face = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]
    w, h = im.size
    px = im.load()
    nw = sum(1 for y in range(0, h, 4) for x in range(0, w, 4)
             if px[x, y] != (255, 255, 255))
    pct = 100.0 * nw / ((w // 4 + 1) * (h // 4 + 1))
    im = im.resize((TILE_W, TILE_H), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, TILE_W - 1, TILE_H - 1], outline=border, width=4)
    try:
        f1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
        f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    d.rectangle([0, 0, TILE_W, 52], fill=(20, 24, 34))
    d.text((8, 4), title, font=f1, fill=(255, 255, 255))
    d.text((8, 28), f"face={face}  nonwhite={pct:.1f}%", font=f2, fill=(180, 220, 255))
    d.rectangle([0, TILE_H - 26, TILE_W, TILE_H], fill=(20, 24, 34))
    d.text((8, TILE_H - 22), note[:58], font=f2, fill=(255, 230, 150))
    return im, face, pct

W = TILE_W * 2 + PAD * 3
H = (TILE_H + HEAD) * 2 + PAD * 3
mosaic = Image.new('RGB', (W, H), (12, 14, 20))
d = ImageDraw.Draw(mosaic)
f0 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)

tiles = [
    tile('run/c157/targets/dooz/screenshot.png',
         'dooz BEFORE  (pre F-NEW-494/495/496)',
         'ops=0 — uniform (250,250,250) background fill', (160, 60, 60)),
    tile('run/c157/dooz_60/screenshot.png',
         'dooz AFTER — draw path alive',
         'ops 0->1947; measure 1x1->1080x1920', (60, 170, 90)),
    tile('run/c157/wall_opencalc/screenshot.png',
         'opencalc — RENDER',
         'full keypad; anchor 63020bc7 MATCH', (60, 170, 90)),
    tile('run/c157/wall_telegram/screenshot.png',
         'telegram — partial (UPP-001)',
         'Disable btn; exceptions 19->13', (200, 160, 60)),
]

faces = {}
pos = [(PAD, PAD + HEAD), (PAD * 2 + TILE_W, PAD + HEAD),
       (PAD, PAD * 2 + HEAD + TILE_H), (PAD * 2 + TILE_W, PAD * 2 + HEAD + TILE_H)]
for (im, face, pct), (x, y) in zip(tiles, pos):
    mosaic.paste(im, (x, y))
d.text((PAD, PAD + 6), 'CONT-157 mosaic — dooz / opencalc / telegram execution tiles (binary 22578fcb03e0cd15)',
       font=f0, fill=(255, 255, 255))

out = 'run/c157/cont157_mosaic.png'
mosaic.save(out)
import os
print(f'{out}: {os.path.getsize(out)} bytes, {W}x{H}')
