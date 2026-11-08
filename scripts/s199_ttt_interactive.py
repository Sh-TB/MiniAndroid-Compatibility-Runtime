#!/usr/bin/env python3
"""S199 — tictactoe interactive capture (frames mode + taps).

The T-199 harness: time-driven capture (--frames advances the virtual
clock; F-117 taps schedule per frame). Board geometry: GLSurfaceView20
renders fullscreen 1080x1920; the tictactoe board is a 3x3 grid inside
it. Taps: 5 probing taps across plausible cell centers — the interaction
proof needs (a) frame content change after each tap, (b) X/O marks on
the board, (c) three independent runs with equivalent behavior.
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
APK = BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
OUT = BASE / 'evidence/s199'
RUNS = OUT / 'runs'
RUNS.mkdir(parents=True, exist_ok=True)

tag = sys.argv[1] if len(sys.argv) > 1 else 'ttt_s199_int_r1'
FRAMES = int(sys.argv[2]) if len(sys.argv) > 2 else 48
DELAY = int(sys.argv[3]) if len(sys.argv) > 3 else 250
# tap schedule: frame -> (x, y). Board 3x3 grid on a 1080x1920 GL surface.
# The board is likely centered; cell centers ~ x in {270,540,810},
# y in {560,960,1360} (square board centered vertically).
TAPS = [
    (6,   270, 560),
    (12,  810, 560),
    (18,  270, 960),
    (24,  810, 960),
    (30,  270, 1360),
]

store = RUNS / f'store_{tag}'
store.mkdir(parents=True, exist_ok=True)
r = subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
                   capture_output=True, timeout=300)
apps = store / 'data' / 'app'
dpkg = None
if apps.exists():
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith('.')
          and not d.name.endswith('.staging')
          and (d / 'base.apk').exists()]
    dpkg = ds[0] if ds else None
print('dpkg:', dpkg, 'rc:', r.returncode)

rundir = RUNS / tag
shutil.rmtree(rundir, ignore_errors=True)
console = OUT / f'{tag}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--frames', str(FRAMES),
       '--frame-delay', str(DELAY), '--trace']
for (fr, x, y) in TAPS:
    cmd += ['--tap', f'{x},{y}@{fr}']
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=FRAMES * DELAY // 1000 + 300)
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

res = {
    'binary_sha16': BIN_SHA, 'tag': tag, 'wall_s': wall,
    'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
    'app_boundary': len(re.findall(r'APP BOUNDARY unwind', log)),
    'frames_rendered': len(re.findall(r'GL_FRAME_PRESENT', log)) or
                       len(re.findall(r'FRAME_CAPTURE', log)),
    'vap_binds': len(re.findall(r'\[GLDBG\] vap', log)),
    'f589_stack': len(re.findall(r'\[F-NEW-589\]', log)),
}
shot = rundir / 'final_frame.png'
if not shot.exists():
    cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
    shot = cands[-1] if cands else None
if shot and shot.exists():
    face = OUT / f'face_{tag}.jpg'
    shutil.copy(shot, face)
    res['face'] = str(face)
frames_dir = rundir / 'frames'
if frames_dir.exists():
    res['frame_count'] = len(list(frames_dir.glob('frame_*.png')))
print(json.dumps(res, indent=1, default=str))
(OUT / f'{tag}.RESULT.json').write_text(json.dumps(res, indent=1, default=str))
