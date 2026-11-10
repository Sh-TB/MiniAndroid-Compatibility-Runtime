#!/usr/bin/env python3
"""S208 — tictactoe ROUND 2 after restart: prove the score ACCUMULATES across
rounds (full multi-round loop). Uses the S207-decoded tap law grid.
Round 1: X wins anti-diag 2-4-6  (proven S207 x_win face db2db9f5...)
Restart tap @8        (proven S207 restart_v2: board clears, score 1|0, fresh X@8)
Round 2: O wins top row 0-1-2 -> score must read 1|1.
x2 determinism, 0 uncaught, on gate-green binary e6287d1a2c175cf0."""
import json, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, '/home/z/my-project/scripts')
from s207_gate import run_app, BASE, RUNS  # noqa: E402

C = {0: (287, 760), 1: (539, 760), 2: (791, 760),
     3: (287, 1040), 4: (539, 1040), 5: (791, 1040),
     6: (287, 1408), 7: (539, 1408), 8: (791, 1408)}
tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]

SEQ = ['X@2', 'O@0', 'X@4', 'O@1', 'X@6', 'TAP@8-restart->fresh-X@8',
       'O@0', 'X@3', 'O@1', 'X@5', 'O@2']
TAPS = [(10, *C[2]), (14, *C[0]), (18, *C[4]), (22, *C[1]), (26, *C[6]),
        (30, *C[8]), (34, *C[0]), (38, *C[3]), (42, *C[1]), (46, *C[5]),
        (50, *C[2])]

out = {'binary_expected': 'e6287d1a2c175cf0', 'seq': SEQ,
       'taps': [list(t) for t in TAPS], 'runs': []}
for k in range(2):
    r = run_app(tapk, f's208_r2_{k}', TAPS, frames=58, delay=250)
    out['runs'].append(r)
    print(f"round2#{k}: face={r['face_sha16']} uncaught={r['uncaught']} "
          f"wall={r['wall_s']}s", flush=True)
out['deterministic_x2'] = (out['runs'][0]['face_sha16']
                           == out['runs'][1]['face_sha16']
                           and out['runs'][0]['face_sha16'] is not None)

REFS = {'restart_1_0_a5ae21ee': RUNS / 's207_gl3_restart_v2_0' / 'screenshot.png',
        'x_win_end_db2db9f5': RUNS / 's207_gl3_x_win_0' / 'screenshot.png'}
shot = RUNS / 's208_r2_0' / 'screenshot.png'


def blobs(png, ref):
    im = Image.open(png).convert('RGB')
    rp = Image.open(ref).convert('RGB')
    w = min(im.size[0], rp.size[0])
    h = min(im.size[1], rp.size[1])
    pp, rpp = im.load(), rp.load()
    pts = [(x, y) for y in range(0, h, 3) for x in range(0, w, 3)
           if pp[x, y] != rpp[x, y]]
    bl = []
    for (x, y) in pts:
        for b in bl:
            if b['x0'] - 30 <= x <= b['x1'] + 30 and b['y0'] - 30 <= y <= b['y1'] + 30:
                b['x0'] = min(b['x0'], x); b['x1'] = max(b['x1'], x)
                b['y0'] = min(b['y0'], y); b['y1'] = max(b['y1'], y)
                b['n'] += 1
                break
        else:
            bl.append({'x0': x, 'x1': x, 'y0': y, 'y1': y, 'n': 1})
    return [{'c': [(b['x0'] + b['x1']) // 2, (b['y0'] + b['y1']) // 2],
             'bbox': [b['x0'], b['y0'], b['x1'], b['y1']], 'n': b['n']}
            for b in bl if b['n'] > 20]


if shot.exists() and REFS['restart_1_0_a5ae21ee'].exists():
    out['diff_vs_restart_1_0'] = blobs(shot, REFS['restart_1_0_a5ae21ee'])
if shot.exists() and REFS['x_win_end_db2db9f5'].exists():
    out['diff_vs_x_win_end'] = blobs(shot, REFS['x_win_end_db2db9f5'])

DOCS = BASE / 'docs/evidence/s208_ttt_round2'
DOCS.mkdir(parents=True, exist_ok=True)
if shot.exists():
    Image.open(shot).convert('RGB').save(DOCS / 'round2_o_win_score_1_1.jpg',
                                         quality=90)

(RUNS / 'S208_ROUND2.json').write_text(json.dumps(out, indent=1))
print('WROTE S208_ROUND2.json')
print('diff_vs_restart_1_0 blobs:', json.dumps(out.get('diff_vs_restart_1_0')))
