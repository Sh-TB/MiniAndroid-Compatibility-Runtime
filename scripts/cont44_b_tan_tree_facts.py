#!/usr/bin/env python3
# cont44_b_tan_tree_facts.py — CONT44-B DECODE 1 (F-NEW-305):
# extract the authoritative view-tree facts + bar-geometry evidence from the
# tananaev PRE run.log into run/cont44/tan_pre/tree_facts.txt.
import re

LOG = '/home/z/my-project/run/cont44/tan_pre/run.log'
OUT = '/home/z/my-project/run/cont44/tan_pre/tree_facts.txt'
BAR = re.compile(r'OverlayLayout|ActionBarContainer|ContentFrameLayout|Toolbar;|ActionBarContextView')

lines = open(LOG, errors='replace').read().splitlines()
rend = [(i, l) for i, l in enumerate(lines) if l.startswith('[EXP092-RENDER]')]
out = []
out.append('== last-frame render tree (bar-family nodes) ==')
last_frame_start = max(i for i, l in rend if 'depth=0' in l)
for i, l in rend:
    if i >= last_frame_start and BAR.search(l):
        out.append(l)
out.append('')
out.append('== DEX-MEASURE results (F10/R-NEW-347 dispatch) ==')
out += [l for l in lines if l.startswith('[DEX-MEASURE]')]
out.append('')
out.append('== layout-path evidence ==')
out += [l for l in lines if '[S109-VG-MEASURE]' in l][:6]
out.append('')
out.append('== window bg + content id evidence ==')
out += [l for l in lines if 'EXT01-WINBG' in l][:2]
out += [l for l in lines if '0x1020002' in l][:2]
out.append('')
out.append('== ROOT-059 WindowInsets stub evidence ==')
out += [l for l in lines if 'ROOT-059' in l][:4]
out.append('')
out.append('== pixel bands (from cont44_b_tanpix2.py) ==')
out.append('y=0..219 rgb(225,225,225) 220px full-width band == rows container rect (0,0 1080x220)')
out.append('y=220..1919 rgb(250,250,250) == windowBackground 0xfffafafa')
out.append('dark pixels (<100 luma): 0 — row text never painted (separate issue)')
open(OUT, 'w').write('\n'.join(out) + '\n')
print('\n'.join(out[:14]))
print('... written', OUT)
