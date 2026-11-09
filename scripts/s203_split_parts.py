#!/usr/bin/env python3
"""s203_split_parts.py — split /tmp/s203_v3.diff into 3 numbered, each
independently git-apply-able parts per the push-403 protocol."""
import re
from pathlib import Path

D = Path('/tmp/s203_v3.diff').read_text()
lines = D.splitlines(keepends=True)

# group: file headers + their hunks
files = []   # (header_lines, [hunk_lines...])
i = 0
hdr = []
while i < len(lines):
    l = lines[i]
    if l.startswith('diff --git'):
        if hdr:
            files.append((hdr, []))
        hdr = [l]
        # consume index/---/+++ preamble
        while i + 1 < len(lines) and not lines[i + 1].startswith('@@'):
            i += 1
            hdr.append(lines[i])
        files.append((hdr, []))
        hdr = []
    elif l.startswith('@@'):
        hunk = [l]
        m = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', l)
        on, nn = int(m.group(2)), int(m.group(4))
        body_o = body_n = 0
        i += 1
        while i < len(lines) and (body_o < on or body_n < nn):
            bl = lines[i]
            hunk.append(bl)
            if bl.startswith((' ', '\n')) or bl == '':
                body_o += 1
                body_n += 1
            elif bl.startswith('-'):
                body_o += 1
            elif bl.startswith('+'):
                body_n += 1
            i += 1
        files[-1][1].append(hunk)
        continue
    i += 1

# map hunks by their new-start line
H = {}
for fi, (hdr, hunks) in enumerate(files):
    for h in hunks:
        m = re.match(r'@@ -\d+,\d+ \+(\d+),\d+ @@', h[0])
        H[int(m.group(1))] = (fi, hdr, h)

parts = {
    1: [13824],                 # F-NEW-626d (612b restore opt-in)
    2: [14045],                 # F-NEW-626b (mint cursor law)
    3: [52561, 52677, 52895, 53014],  # F-NEW-626 family (view bulk)
    4: [436, 472, 522],         # F-NEW-626e probe infra (gles20)
}
starts = sorted(H)
print('hunk starts:', starts)

# assign each hunk to a part by membership ranges
ranges = {1: (13800, 13900), 2: (14000, 14100), 3: (52500, 53400),
          4: (400, 600)}
assigned = {p: [] for p in parts}
for s in starts:
    for p, (lo, hi) in ranges.items():
        if lo <= s <= hi:
            assigned[p].append(s)
            break
    else:
        print('UNASSIGNED hunk at', s)

for p in sorted(assigned):
    body = []
    hdr_used = None
    for s in assigned[p]:
        fi, hdr, h = H[s]
        body.append(h)
        hdr_used = hdr
    out = []
    out.extend(hdr_used)
    for h in body:
        out.extend(h)
    Path(f'/tmp/s203_part{p}.diff').write_text(''.join(out))
    n = len(''.join(out))
    print(f'part{p}: hunks={assigned[p]} bytes={n}')
