#!/usr/bin/env python3
# cont44_b_census_evidence.py — CONT44-B DECODE 2 (F-NEW-307):
# extract the compose-draw-op attribution evidence from the dooz 180s PRE run.
import re

LOG = '/home/z/my-project/run/cont44/dooz180/run.log'
OUT = '/home/z/my-project/run/cont44/dooz180/census_evidence.txt'
lines = open(LOG, errors='replace').read().splitlines()
out = []
out.append('== per-frame compose draw dispatch (C013-ONDRAW) ==')
out += [l for l in lines if l.startswith('[C013-ONDRAW]')]
out.append('')
out.append('== frame-honesty kept-prior events (F298-KEEP) ==')
out += [l for l in lines if 'F298-KEEP' in l]
out.append('')
out.append('== wall-budget halts inside the draw window (WALL-STOP): %d total =='
           % sum(1 for l in lines if 'WALL-STOP' in l))
out += [l for l in lines if 'WALL-STOP' in l][:4]
out.append('')
out.append('== deferred F084 exception propagate ==')
out += [l for l in lines if 'SYNTH-EXC' in l and 'F084' in l][:2]
out.append('')
out.append('== compose root node geometry ==')
out += [l for l in lines if 'EXP092-RENDER' in l and 'Lt4;' in l][:2]
out += [l for l in lines if 'UC009-DRAW' in l][:2]
out.append('')
out.append('== final verdict line ==')
out += [l for l in lines if 'F-NEW-233 frame truth' in l]
open(OUT, 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
