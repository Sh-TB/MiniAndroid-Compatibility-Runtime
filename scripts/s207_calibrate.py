#!/usr/bin/env python3
"""S207 tap-cell calibration: ONE tap per run at 6 probe points, then locate
where the piece actually landed (which 3x3 cell center region has ink).
Ground truth anchors from S206: (540,760)=center, (250,480)=topleft."""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, '/home/z/my-project/scripts')
from s207_gate import run_app, BASE, RUNS  # noqa: E402
from PIL import Image  # noqa: E402

tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]

# probe points: assumed row1 (y=480) cols, center (540,760), row3 (y=1040) ends
PROBES = {
    'p_r1_c1': (250, 480),
    'p_r1_c2': (540, 480),
    'p_r1_c3': (830, 480),
    'p_center': (540, 760),
    'p_r3_c1': (250, 1040),
    'p_r3_c3': (830, 1040),
}

# reference: the no-tap gate face for ink-diff
ref = Image.open(RUNS / 's207_ttt0' / 'screenshot.png').convert('RGB')

def ink_cells(png):
    """Split the board region into 3x3, count non-white px per cell region."""
    im = Image.open(png).convert('RGB')
    w, h = im.size
    # board bounding box: find black-ish grid pixels rows/cols
    px = im.load()
    cols = [x for x in range(w) if any(px[x, y][0] < 60 and px[x, y][1] < 60 and px[x, y][2] < 60 for y in range(300, h - 300, 7))]
    if not cols:
        return None
    return None  # not needed; use fixed thirds of the detected grid

def cell_ink(png):
    im = Image.open(png).convert('RGB')
    rw, rh = im.size
    rp = ref.load()
    pp = im.load()
    # diff vs ref: pixels that changed from the no-tap face
    diff = Image.new('L', im.size, 0)
    dp = diff.load()
    for y in range(0, rh, 2):
        for x in range(0, rw, 2):
            if pp[x, y] != rp[x, y]:
                dp[x, y] = 255
    bbox = diff.getbbox()
    if not bbox:
        return None, None
    # assume 3x3 grid: use bbox of the change to assign nearest cell via thirds
    # grid geometry from anchors: cols 250/540/830 rows 480/760/1040 are CENTERS of a 940-wide board? just report bbox center
    cx, cy = (bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2
    return (cx, cy), bbox

out = {}
for name, (x, y) in PROBES.items():
    r = run_app(tapk, f's207_cal_{name}', [(12, x, y)], frames=20, delay=250)
    shot = RUNS / f's207_cal_{name}' / 'screenshot.png'
    center, bbox = cell_ink(shot) if shot.exists() else (None, None)
    out[name] = {'tap': [x, y], 'face': r['face_sha16'], 'uncaught': r['uncaught'],
                 'ink_center': center, 'ink_bbox': list(bbox) if bbox else None}
    print(f"{name}: tap=({x},{y}) -> ink_center={center} bbox={list(bbox) if bbox else None} "
          f"uncaught={r['uncaught']}", flush=True)
(RUNS / 'S207_CALIBRATION.json').write_text(json.dumps(out, indent=1))
print('WROTE S207_CALIBRATION.json')
