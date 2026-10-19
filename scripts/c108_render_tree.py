#!/usr/bin/env python3
"""Extract the LAST full EXP092-RENDER tree from a stderr log and print it."""
import re, sys

path = sys.argv[1]
trees = []  # each tree starts at a depth-0 render line
cur = []
for line in open(path, errors='replace'):
    m = re.match(r'\[EXP092-RENDER\] node=(\d+) class=(\S+) text="(.*?)" children=(\d+) depth=(\d+) pos=\((-?\d+),(-?\d+)\) size=\((\d+)x(\d+)\)', line)
    if m:
        d = int(m.group(5))
        if d == 0:
            if cur: trees.append(cur)
            cur = []
        cur.append(m.groups())
if cur: trees.append(cur)
tree = trees[-1] if trees else []
print(f'{path}: {len(trees)} trees; last tree nodes={len(tree)}')
for n, cls, txt, ch, d, x, y, w, h in tree:
    print(f'{"  "*int(d)}node={n} {cls} text={txt!r} ch={ch} pos=({x},{y}) size={w}x{h}')
