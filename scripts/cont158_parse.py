#!/usr/bin/env python3
"""cont158_parse.py — CONT-158 game battery scorecard.
Per row: face16, rc, exceptions, sampled non-white %, distinct-color census
(CONT-157 law: uniform-fill faces are NOT real content even if non-white).
Comparison vs run/c156/canon baseline (face16 + rc) and known anchor faces."""
import json, os, glob, hashlib
from PIL import Image

BASE = 'run/c158/battery'
KNOWN = {  # last recorded states before this round (CONT-156/157 ledgers)
    'dooz':      ('31ddd4d5', 'draw-op boundary face (white)'),
    'dooz_top':  ('d602648e', 'uniform-fill white'),
    'bouncy':    (None, 'c156 canon battery'),
    'tictactoe': ('b5a7a35d', 'rc=1 shared boundary face'),
    'gmdice':    (None, 'c156 canon battery'),
    'fishrings': ('b5a7a35d', 'shared boundary face'),
    'memory':    (None, 'c156 canon battery'),
    'tower3d':   ('11a38a5a', 'c129 anchor'),
    'tripeaks':  ('b5a7a35d', 'shared boundary face'),
    'chess':     ('a0319686', 'c129 anchor'),
    'klondike':  ('31ddd4d5', 'draw-op boundary face (white)'),
    'sudoku':    ('be640e39', 'c129 anchor'),
    'stopwatch': ('31ddd4d5', 'draw-op boundary face (white)'),
    'opencalc':  ('63020bc7', 'full render (keypad)'),
}
REF_ROWS = {'stopwatch', 'opencalc'}

def face16(shot):
    return hashlib.sha256(open(shot, 'rb').read()).hexdigest()[:16]

def face_stats(shot):
    im = Image.open(shot).convert('RGB')
    w, h = im.size
    px = im.load()
    nw = 0; total = 0
    colors = {}
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            c = px[x, y]
            total += 1
            if c != (255, 255, 255):
                nw += 1
            colors[c] = colors.get(c, 0) + 1
    pct = 100.0 * nw / total
    top = max(colors.items(), key=lambda kv: kv[1])
    uniform = 100.0 * top[1] / total
    return round(pct, 1), len(colors), (top[0], round(uniform, 1))

def rc_of(log):
    for line in open(log, errors='replace'):
        if line.startswith('rc='):
            return int(line.strip()[3:].split()[0])
    return None

def exc_of(log):
    n = 0
    for line in open(log, errors='replace'):
        if 'SYNTH-EXC' in line or 'Uncaught' in line:
            n += 1
    return n

# c156 baseline faces (if run dir present)
c156 = {}
for log in glob.glob('run/c156/canon/*.log'):
    base = os.path.basename(log)[:-4]
    if base == 'battery':
        continue
    shot = f'run/c156/canon/{base}/screenshot.png'
    c156[base] = (face16(shot) if os.path.exists(shot) else 'NO-SHOT', rc_of(log))

rows = []
for app in 'dooz dooz_top bouncy bouncy_top tictactoe gmdice fishrings memory tower3d tripeaks chess chessclock flappycow klondike sudoku g2048 snake tetris stopwatch opencalc'.split():
    shot = f'{BASE}/{app}/screenshot.png'
    log = f'{BASE}/{app}.log'
    if not os.path.exists(shot):
        rows.append({'app': app, 'ref': app in REF_ROWS, 'face16': 'NO-SHOT', 'rc': rc_of(log)})
        continue
    pct, ncolors, (topc, topuni) = face_stats(shot)
    f16 = face16(shot)
    known = KNOWN.get(app, (None, ''))
    old = c156.get(app, ('?', '?'))
    same_as_c156 = (f16 == old[0])
    kind = ('uniform-fill' if topuni >= 98.0 else
            'white' if pct < 1.0 else
            'sparse' if pct < 15.0 else
            'content' if pct >= 50.0 else 'partial')
    changed = (known[0] is not None and f16 != known[0])
    verdict = ('STABLE' if not changed else 'ADVANCED-FACE-CHANGED' if pct >= 15.0 and kind == 'content' else
               'FACE-CHANGED' if changed else 'NO-KNOWN-BASE')
    rows.append({'app': app, 'ref': app in REF_ROWS, 'face16': f16, 'rc': rc_of(log),
                 'exc': exc_of(log), 'nonwhite_pct': pct, 'distinct_colors': ncolors,
                 'top_color': str(topc[0]), 'top_uniform_pct': topuni, 'kind': kind,
                 'known_face': known[0] or '-', 'known_state': known[1],
                 'same_face_as_c156': same_as_c156, 'verdict': verdict})

json.dump({'rows': rows}, open(f'{BASE}/scorecard.json', 'w'), indent=1)
games = [r for r in rows if not r['ref']]
refs = [r for r in rows if r['ref']]
def show(r):
    return (f"  {r['app']:<11} rc={str(r['rc']):<3} face={r['face16']:<16} "
            f"nonwhite={str(r.get('nonwhite_pct')):<6} colors={str(r.get('distinct_colors')):<5} "
            f"top={r.get('top_color','')}:{str(r.get('top_uniform_pct'))}% kind={r.get('kind','-'):<13} "
            f"exc={str(r.get('exc')):<4} c156same={r.get('same_face_as_c156')} verdict={r['verdict']}")
print(f"=== GAMES ({len(games)}) ===")
for r in games: print(show(r))
print(f"=== REFERENCE TOOLS ({len(refs)}) ===")
for r in refs: print(show(r))
content = [r for r in games if r.get('kind') == 'content']
blankish = [r for r in games if r.get('kind') in ('white', 'uniform-fill')]
print(f"games total={len(games)} content={len(content)} partial/sparse={len([r for r in games if r.get('kind') in ('partial','sparse')])} blank-ish={len(blankish)}")
