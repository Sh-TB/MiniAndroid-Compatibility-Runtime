#!/usr/bin/env python3
"""Normalize two stderr logs (strip ms / engine pointers / addresses) and print
the first N semantic divergences with line numbers."""
import re, sys

def norm(path):
    out = []
    with open(path, errors='replace') as f:
        for ln, line in enumerate(f, 1):
            s = line.rstrip('\n')
            s = re.sub(r'ms=\d+', 'ms=X', s)
            s = re.sub(r'0x7f[0-9a-f]{6,}', 'PTR', s)
            s = re.sub(r'hs=0x[0-9a-f]+', 'hs=P', s)
            out.append((ln, s))
    return out

a = norm(sys.argv[1])
b = norm(sys.argv[2])
n_show = int(sys.argv[3]) if len(sys.argv) > 3 else 12
shown = 0
i = j = 0
while i < len(a) and j < len(b) and shown < n_show:
    if a[i][1] == b[j][1]:
        i += 1; j += 1; continue
    # try to resync: look ahead small window
    win = 12
    ka = next((k for k in range(i, min(i+win, len(a))) if a[k][1] == b[j][1]), None)
    kb = next((k for k in range(j, min(j+win, len(b))) if b[k][1] == a[i][1]), None)
    if ka is not None and (kb is None or ka - i <= kb - j):
        print(f'--- ONLY-IN-A near a:{a[i][0]}..{ka} (context {a[i][1][:110]!r})')
        for k in range(i, ka):
            print(f'  A:{a[k][0]} {a[k][1][:150]}')
        shown += 1; i = ka; continue
    if kb is not None and (ka is None or kb - j < ka - i):
        print(f'--- ONLY-IN-B near b:{b[j][0]}..{kb} (context {b[j][1][:110]!r})')
        for k in range(j, kb):
            print(f'  B:{b[k][0]} {b[k][1][:150]}')
        shown += 1; j = kb; continue
    print(f'--- MISMATCH a:{a[i][0]} vs b:{b[j][0]}')
    print(f'  A: {a[i][1][:170]}')
    print(f'  B: {b[j][1][:170]}')
    shown += 1; i += 1; j += 1
if shown == 0:
    print('SEMANTICALLY IDENTICAL')
