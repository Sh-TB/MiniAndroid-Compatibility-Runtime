#!/usr/bin/env python3
"""S207 game-loop recipes — the three L-06 'what exact test to perform next'
items on tictactoe, x2 determinism each, on the gate-green binary e6287d1a2c175cf0.
Grid (from the S206 win-run coordinates): cols x=250/540/830, rows y=480/760/1040.
cell0=(250,480) cell1=(540,480) cell2=(830,480)
cell3=(250,760) cell4=(540,760) cell5=(830,760)
cell6=(250,1040) cell7=(540,1040) cell8=(830,1040)"""
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, '/home/z/my-project/scripts')
from s207_gate import run_app, BASE, RUNS, BIN  # noqa: E402

CELL = {0: (250, 480), 1: (540, 480), 2: (830, 480),
        3: (250, 760), 4: (540, 760), 5: (830, 760),
        6: (250, 1040), 7: (540, 1040), 8: (830, 1040)}
tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]

RECIPES = {
    # O wins the 2-4-6 diagonal: X@0 O@2 X@1 O@4 X@3 O@6
    'o_win': {
        'seq': ['X@0', 'O@2', 'X@1', 'O@4', 'X@3', 'O@6'],
        'taps': [(10, *CELL[0]), (14, *CELL[2]), (18, *CELL[1]),
                 (22, *CELL[4]), (26, *CELL[3]), (30, *CELL[6])],
        'frames': 36,
    },
    # Stalemate: X@0 O@4 X@2 O@5 X@3 O@6 X@7 O@1 X@8 (verified no line for either side)
    'stalemate': {
        'seq': ['X@0', 'O@4', 'X@2', 'O@5', 'X@3', 'O@6', 'X@7', 'O@1', 'X@8'],
        'taps': [(10, *CELL[0]), (14, *CELL[4]), (18, *CELL[2]),
                 (22, *CELL[5]), (26, *CELL[3]), (30, *CELL[6]),
                 (34, *CELL[7]), (38, *CELL[1]), (42, *CELL[8])],
        'frames': 48,
    },
    # X wins 2-4-6 (X@4 O@0 X@8 O@1 X@6) then 6th tap @1 -> restart, score persists
    'restart_after_win': {
        'seq': ['X@4', 'O@0', 'X@8', 'O@1', 'X@6', 'TAP@1-after-win'],
        'taps': [(10, *CELL[4]), (14, *CELL[0]), (18, *CELL[8]),
                 (22, *CELL[1]), (26, *CELL[6]), (30, *CELL[1])],
        'frames': 38,
    },
}

out = {}
for name, rc in RECIPES.items():
    runs = []
    for k in range(2):
        r = run_app(tapk, f's207_gl_{name}_{k}', rc['taps'],
                    frames=rc['frames'], delay=250)
        runs.append(r)
        print(f"{name}#{k}: face={r['face_sha16']} uncaught={r['uncaught']} "
              f"wall={r['wall_s']}s", flush=True)
    out[name] = {'seq': rc['seq'], 'runs': runs,
                 'deterministic_x2': runs[0]['face_sha16'] == runs[1]['face_sha16']
                 and runs[0]['face_sha16'] is not None}
(RUNS / 'S207_GAMELOOP.json').write_text(json.dumps(out, indent=1))
print('WROTE S207_GAMELOOP.json')
