#!/usr/bin/env python3
"""S207 game-loop recipes v2 — with the decoded tap law on binary e6287d1a2c175cf0.
Visual grid ink centers: cols 287/539/791, rows 648/972/1296.
Tap law: tap_y = row_center + 112 lands that row (band [486,1620]); tap_x = col center.
cells: c0=(287,760) c1=(539,760) c2=(791,760) c3=(287,1040) c4=(539,1040)
       c5=(791,1040) c6=(287,1408) c7=(539,1408) c8=(791,1408)"""
import json, sys
from pathlib import Path
sys.path.insert(0, '/home/z/my-project/scripts')
from s207_gate import run_app, BASE, RUNS  # noqa: E402

C = {0: (287, 760), 1: (539, 760), 2: (791, 760),
     3: (287, 1040), 4: (539, 1040), 5: (791, 1040),
     6: (287, 1408), 7: (539, 1408), 8: (791, 1408)}
tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]

RECIPES = {
    # O wins 2-4-6: X@0 O@2 X@1 O@4 X@3 O@6
    'o_win': {
        'seq': ['X@0', 'O@2', 'X@1', 'O@4', 'X@3', 'O@6'],
        'taps': [(10, *C[0]), (14, *C[2]), (18, *C[1]),
                 (22, *C[4]), (26, *C[3]), (30, *C[6])],
        'frames': 36,
    },
    # Stalemate: X@0 O@4 X@2 O@5 X@3 O@6 X@7 O@1 X@8
    'stalemate': {
        'seq': ['X@0', 'O@4', 'X@2', 'O@5', 'X@3', 'O@6', 'X@7', 'O@1', 'X@8'],
        'taps': [(10, *C[0]), (14, *C[4]), (18, *C[2]), (22, *C[5]),
                 (26, *C[3]), (30, *C[6]), (34, *C[7]), (38, *C[1]),
                 (42, *C[8])],
        'frames': 48,
    },
    # X wins 2-4-6 then 6th tap -> restart, score persists
    'restart_after_win': {
        'seq': ['X@4', 'O@0', 'X@8', 'O@1', 'X@6', 'TAP@1'],
        'taps': [(10, *C[4]), (14, *C[0]), (18, *C[8]),
                 (22, *C[1]), (26, *C[6]), (30, *C[1])],
        'frames': 38,
    },
}

out = {}
for name, rc in RECIPES.items():
    runs = []
    for k in range(2):
        r = run_app(tapk, f's207_gl2_{name}_{k}', rc['taps'],
                    frames=rc['frames'], delay=250)
        runs.append(r)
        print(f"{name}#{k}: face={r['face_sha16']} uncaught={r['uncaught']}",
              flush=True)
    out[name] = {'seq': rc['seq'], 'runs': runs,
                 'deterministic_x2': runs[0]['face_sha16'] == runs[1]['face_sha16']
                 and runs[0]['face_sha16'] is not None}
(RUNS / 'S207_GAMELOOP_V2.json').write_text(json.dumps(out, indent=1))
print('WROTE S207_GAMELOOP_V2.json')
