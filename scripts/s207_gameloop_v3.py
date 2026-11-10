#!/usr/bin/env python3
"""S207 recipes v3 — corrected X-win + restart-after-win.
X wins the 2-4-6 ANTI-diagonal: X@2 O@0 X@4 O@1 X@6 -> red line + score 1|0.
restart_v2: same 5 moves, then 6th tap @8 -> GameData.getEnded() -> restart()
(board clears, score persists 1|0, tap lands as fresh X@8)."""
import json, sys
from pathlib import Path
sys.path.insert(0, '/home/z/my-project/scripts')
from s207_gate import run_app, BASE, RUNS  # noqa: E402

C = {0: (287, 760), 1: (539, 760), 2: (791, 760),
     3: (287, 1040), 4: (539, 1040), 5: (791, 1040),
     6: (287, 1408), 7: (539, 1408), 8: (791, 1408)}
tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]

RECIPES = {
    'x_win': {
        'seq': ['X@2', 'O@0', 'X@4', 'O@1', 'X@6'],
        'taps': [(10, *C[2]), (14, *C[0]), (18, *C[4]), (22, *C[1]), (26, *C[6])],
        'frames': 32,
    },
    'restart_v2': {
        'seq': ['X@2', 'O@0', 'X@4', 'O@1', 'X@6', 'TAP@8-after-win'],
        'taps': [(10, *C[2]), (14, *C[0]), (18, *C[4]), (22, *C[1]),
                 (26, *C[6]), (30, *C[8])],
        'frames': 38,
    },
}

out = {}
for name, rc in RECIPES.items():
    runs = []
    for k in range(2):
        r = run_app(tapk, f's207_gl3_{name}_{k}', rc['taps'],
                    frames=rc['frames'], delay=250)
        runs.append(r)
        print(f"{name}#{k}: face={r['face_sha16']} uncaught={r['uncaught']}",
              flush=True)
    out[name] = {'seq': rc['seq'], 'runs': runs,
                 'deterministic_x2': runs[0]['face_sha16'] == runs[1]['face_sha16']
                 and runs[0]['face_sha16'] is not None}
(RUNS / 'S207_GAMELOOP_V3.json').write_text(json.dumps(out, indent=1))
print('WROTE S207_GAMELOOP_V3.json')
