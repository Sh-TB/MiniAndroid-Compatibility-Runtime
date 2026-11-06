#!/usr/bin/env python3
"""S186: graphics-depth census of ALL s107_games faces (user: 'all white/black two-tone').
Reuses the S183 tier definitions. Output: evidence/s186_s107/S107_FACE_CENSUS.json"""
import json, os, glob
from PIL import Image
from collections import Counter

OUT = 'evidence/s186_s107'
os.makedirs(OUT, exist_ok=True)

def depth(path):
    im = Image.open(path).convert('RGB')
    im.thumbnail((540, 960))
    px = list(im.getdata())
    n = len(px)
    from collections import Counter as C
    cc = C(px)
    uc = len(cc)
    bg = cc.most_common(1)[0]
    bg_share = bg[1] / n
    nonbg = 1 - bg_share
    # gradient proxy: count distinct colors in non-bg
    colors_nonbg = len([c for c in cc if c != bg[0]])
    grad = 0
    w, h = im.size
    p2 = im.load()
    gsum = gcnt = 0
    for y in range(0, h - 1, 3):
        for x in range(0, w - 1, 3):
            a, b = p2[x, y], p2[x, y + 1]
            d = abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])
            gsum += d; gcnt += 1
    grad_share = (gsum / gcnt / 255) if gcnt else 0
    if nonbg >= 0.01 and uc >= 400 and grad_share >= 0.02: tier = 'A_RICH'
    elif nonbg >= 0.01 and uc >= 60: tier = 'B_STRUCTURED'
    elif uc <= 3 or nonbg < 0.01: tier = 'FLAT_TWO_TONE_OR_BLANK'
    else: tier = 'C_TEXT_ON_FLAT'
    return dict(unique_colors=uc, bg_share=round(bg_share, 4), nonbg_share=round(nonbg, 4),
                grad_share=round(grad_share, 4), tier=tier)

rows = []
for run in sorted(glob.glob('evidence/s107_games/*_run1')):
    pkg = os.path.basename(run)[:-5]
    shot = os.path.join(run, 'screenshot.png')
    if not os.path.exists(shot):
        rows.append(dict(package=pkg, tier='NO_SHOT')); continue
    try:
        d = depth(shot)
    except Exception as e:
        rows.append(dict(package=pkg, tier='ERROR', err=str(e)[:80])); continue
    d['package'] = pkg
    rows.append(d)

tiers = Counter(r.get('tier') for r in rows)
json.dump(dict(schema='s186_s107_census/v1', n=len(rows), tiers=dict(tiers), rows=rows),
          open(f'{OUT}/S107_FACE_CENSUS.json', 'w'), indent=1)
print('n =', len(rows))
for t, c in tiers.most_common(): print(f'{c:4d}  {t}')
