#!/usr/bin/env python3
"""S207 tap-law decisive probes: replicate the exact S206 two-tap run and
measure BOTH pieces' ink centers vs the no-tap reference; then probe row3."""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, '/home/z/my-project/scripts')
from s207_gate import run_app, BASE, RUNS  # noqa: E402
from PIL import Image  # noqa: E402

tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]
ref = Image.open(RUNS / 's207_ttt0' / 'screenshot.png').convert('RGB')

def ink_blobs(png):
    """Connected-ish ink blobs (diff vs ref), each with center + bbox."""
    im = Image.open(png).convert('RGB')
    rw, rh = im.size
    rp, pp = ref.load(), im.load()
    pts = [(x, y) for y in range(0, rh, 3) for x in range(0, rw, 3)
           if pp[x, y] != rp[x, y]]
    blobs = []
    for (x, y) in pts:
        for b in blobs:
            if b['x0'] - 30 <= x <= b['x1'] + 30 and b['y0'] - 30 <= y <= b['y1'] + 30:
                b['x0'] = min(b['x0'], x); b['x1'] = max(b['x1'], x)
                b['y0'] = min(b['y0'], y); b['y1'] = max(b['y1'], y)
                b['n'] += 1
                break
        else:
            blobs.append({'x0': x, 'x1': x, 'y0': y, 'y1': y, 'n': 1})
    return [{'c': [(b['x0'] + b['x1']) // 2, (b['y0'] + b['y1']) // 2],
             'bbox': [b['x0'], b['y0'], b['x1'], b['y1']], 'n': b['n']}
            for b in blobs if b['n'] > 20]

out = {}
for name, taps, frames in [
    ('q_s206_replica', [(10, 540, 760), (16, 250, 480)], 22),
    ('q_row3', [(12, 539, 1408)], 20),
    ('q_r1c1_after_anchor', [(12, 539, 760), (18, 287, 760)], 26),
]:
    r = run_app(tapk, f's207_{name}', taps, frames=frames, delay=250)
    shot = RUNS / f's207_{name}' / 'screenshot.png'
    blobs = ink_blobs(shot) if shot.exists() else None
    out[name] = {'taps': taps, 'face': r['face_sha16'],
                 'uncaught': r['uncaught'], 'blobs': blobs}
    print(f"{name}: taps={taps}")
    for b in (blobs or []):
        print(f"   ink c={b['c']} bbox={b['bbox']} n={b['n']}", flush=True)
(RUNS / 'S207_TAPLAW.json').write_text(json.dumps(out, indent=1))
print('WROTE S207_TAPLAW.json')
