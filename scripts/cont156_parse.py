#!/usr/bin/env python3
"""cont156_parse.py — CONT-156 corpus re-battery scorecard.
Face coverage per app (sampled non-white %), rc, exception counts;
comparison vs run/c154/scorecard_final.json verdicts; WHY table v2."""
import json, os, glob
from PIL import Image

BASE = 'run/c156/big'
rows = []
for log in sorted(glob.glob(f'{BASE}/*.log')):
    base = os.path.basename(log)[:-4]
    if base == 'battery':
        continue
    shot = f'{BASE}/{base}/screenshot.png'
    if not os.path.exists(shot):
        rows.append({'app': base, 'face_pct': None, 'rc': None, 'note': 'NO-SHOT'})
        continue
    im = Image.open(shot).convert('RGB')
    w, h = im.size
    px = im.load()
    nw = sum(1 for y in range(0, h, 4) for x in range(0, w, 4)
             if px[x, y] != (255, 255, 255))
    pct = 100.0 * nw / ((w // 4 + 1) * (h // 4 + 1))
    rc = None
    for line in open(log, errors='replace'):
        if line.startswith('rc='):
            rc = int(line.strip()[3:])
            break
    exc = 0
    for line in open(log, errors='replace'):
        if 'SYNTH-EXC' in line or 'Uncaught' in line:
            exc += 1
    rows.append({'app': base, 'face_pct': round(pct, 1), 'rc': rc,
                 'exceptions': exc,
                 'verdict': 'RENDER' if pct >= 50.0 else 'blank'})

render = [r for r in rows if r.get('verdict') == 'RENDER']
blank = [r for r in rows if r.get('verdict') == 'blank']
noshot = [r for r in rows if r.get('face_pct') is None]
print(f'total={len(rows)} render={len(render)} blank={len(blank)} no-shot={len(noshot)}')
print('--- BLANK apps ---')
for r in blank:
    print(f"  {r['app']}: {r['face_pct']}% rc={r['rc']} exc={r.get('exceptions')}")
print('--- NO-SHOT ---')
for r in noshot:
    print(f"  {r['app']}")

# compare vs c154
try:
    old = json.load(open('run/c154/scorecard_final.json'))
    oldmap = {}
    for r in old['rows']:
        nm = r.get('name') or r.get('apk', '').split('/')[-1].replace('.apk', '')
        oldmap[nm] = r.get('verdict')
    crossed, regressed = [], []
    for r in rows:
        o = oldmap.get(r['app'])
        if o in ('NO_ROOT', 'BLANK', 'blank', 'BOUNDARY') and r.get('verdict') == 'RENDER':
            crossed.append(r['app'])
        if o in ('RENDER',) and r.get('verdict') == 'blank':
            regressed.append(r['app'])
    print(f'--- CROSSED vs c154 ({len(crossed)}) ---')
    for a in crossed:
        print(f'  + {a}')
    print(f'--- REGRESSED vs c154 ({len(regressed)}) ---')
    for a in regressed:
        print(f'  - {a}')
except Exception as e:
    print('baseline compare skipped:', e)

json.dump({'rows': rows, 'render': len(render), 'blank': len(blank)},
          open(f'{BASE}/scorecard.json', 'w'), indent=1)
print(f"scorecard -> {BASE}/scorecard.json")
