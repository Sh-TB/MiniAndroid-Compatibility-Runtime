#!/usr/bin/env python3
"""cont158_mosaic.py — CONT-158 game mosaic tiles artifact.
Every tile = the REAL final screenshot of a real run (binary b7b193b5 family,
F-NEW-497 post-capture drain state). Labels: app, face16, rc, distinct colors,
kind. English labels (PIL has no RTL shaper — CONT-157 precedent: numbers are
the shared language). No staged rendering."""
import json, os, hashlib
from PIL import Image, ImageDraw

BASE = 'run/c158/battery'
OUT = 'run/c158/cont158_mosaic.png'
TILE_W, TILE_H = 216, 384   # 1080x1920 scaled
COLS = 5
ORDER = ['dooz','dooz_top','bouncy','bouncy_top','tictactoe','gmdice','fishrings',
         'memory','tower3d','tripeaks','chess','chessclock','flappycow','klondike',
         'sudoku','g2048','snake','tetris','stopwatch','opencalc']
REF = {'stopwatch','opencalc'}

rows = {r['app']: r for r in json.load(open('run/c158/battery/scorecard.json'))['rows']}

n = len(ORDER)
rows_n = (n + COLS - 1) // COLS
LH = 34  # label strip height
W = COLS * (TILE_W + 8) + 8
H = rows_n * (TILE_H + LH + 8) + 8 + 28
canvas = Image.new('RGB', (W, H), (18, 18, 22))
d = ImageDraw.Draw(canvas)
d.text((8, 5), 'CONT-158 game battery mosaic — binary b7b193b541735991 (F-NEW-497) — 18 games + 2 ref tools — real run faces', fill=(200, 200, 210))

for i, app in enumerate(ORDER):
    r = rows[app]
    cx = 8 + (i % COLS) * (TILE_W + 8)
    cy = 28 + 8 + (i // COLS) * (TILE_H + LH + 8)
    shot = f'{BASE}/{app}/screenshot.png'
    if os.path.exists(shot):
        im = Image.open(shot).convert('RGB').resize((TILE_W, TILE_H))
        canvas.paste(im, (cx, cy))
    else:
        d.rectangle([cx, cy, cx + TILE_W, cy + TILE_H], fill=(60, 0, 0))
    face = r.get('face16', 'NO-SHOT')[:8]
    kind = r.get('kind', '?')
    pct = r.get('nonwhite_pct', 0)
    colors = r.get('distinct_colors', 0)
    col = (110, 220, 130) if kind == 'content' else ((230, 200, 90) if kind == 'partial' else (220, 90, 90))
    d.text((cx + 2, cy + TILE_H + 2), f"{app}{'*' if app in REF else ''} f={face}", fill=col)
    d.text((cx + 2, cy + TILE_H + 17), f"nw={pct}% c={colors} {kind[:9]}", fill=(150, 150, 160))

d.text((8, H - 20), "* = reference tool row (honestly labeled, not a game). green=content, yellow=partial, red=uniform/white", fill=(140, 140, 150))
canvas.save(OUT)
print('mosaic ->', OUT, canvas.size)
