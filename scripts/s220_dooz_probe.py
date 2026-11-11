#!/usr/bin/env python3
"""S220: dooz New Game chain probe — the GP-discriminated state gate.

GP-582 (comment 6807083759): the board is gated by
AnimatedVisibility(isGameStarted && !isRollingDices). The chain to prove:
tap New game -> GameAction.NewGame -> scope.launch -> suspend settings
getters -> resetGame/prepareGame* -> StateFlow isGameStarted=true ->
dummyDiceRolling (5x100ms delay) -> isRollingDices=false -> GameBoard
composes -> LazyGrid cells -> board pixels.
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
RUNS = BASE / 'evidence/s220/runs'
RUNS.mkdir(parents=True, exist_ok=True)

TAG = sys.argv[1] if len(sys.argv) > 1 else 's220_dooz_ng'
taps = sys.argv[2] if len(sys.argv) > 2 else '875,1823@6'
frames = sys.argv[3] if len(sys.argv) > 3 else '24'

store = RUNS / f'store_{TAG}'
store.mkdir(parents=True, exist_ok=True)
subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
               capture_output=True, timeout=300)
apps = store / 'data' / 'app'
dpkg = None
for d in sorted(apps.iterdir()):
    if d.is_dir() and not d.name.startswith('.') and not d.name.endswith('.staging') \
            and (d / 'base.apk').exists():
        dpkg = d.name
assert dpkg, "install failed"

rundir = RUNS / TAG
shutil.rmtree(rundir, ignore_errors=True)
console = RUNS / f'{TAG}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--frames', frames, '--frame-delay', '250']
for t in taps.split(';'):
    cmd += ['--tap', t]
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, cwd=str(BASE),
                   timeout=900)
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

marks = {}
for name, pat in [
    ('tap_receipt', r'TAP|MotionEvent|ACTION_DOWN'),
    ('phase_b_click', r'PHASE-B|phase_b_click|CLICK-TEST'),
    ('newgame_action', r'NewGame|new_game|New game'),
    ('coroutine_dispatch', r'COROUTINE|Dispatchers|continuation'),
    ('delay_seen', r'\bdelay\b|Delay'),
    ('datastore', r'DataStore|dataStore'),
    ('stateflow', r'StateFlow|setState|isGameStarted|isRollingDices'),
    ('compose_recompose', r'recompos|Recompos'),
    ('animated_visibility', r'AnimatedVisibility'),
    ('lazygrid', r'LazyVerticalGrid|LazyGrid|LazyLayout'),
    ('gameboard', r'GameBoard|GameContent|GameScreen'),
    ('s36_aoob', r'S36-AOOB'),
    ('bw0_d', r'Lbw0;'),
    ('abort_flow', r'AbortFlow'),
    ('uncaught', r'uncaught exception|FATAL'),
    ('exc_unwind', r'EXC-UNWIND'),
]:
    marks[name] = len(re.findall(pat, log))

# per-frame pixel delta: which frames change (state -> visible frame evidence)
frame_hashes = {}
fdir = rundir / 'frames'
if fdir.exists():
    prev = None
    for f in sorted(fdir.glob('frame_*.png')):
        h = hashlib.sha256(f.read_bytes()).hexdigest()[:8]
        frame_hashes[f.name] = ('SAME' if h == prev else 'CHANGED')
        prev = h

shot = rundir / 'screenshot.png'
face = hashlib.sha256(shot.read_bytes()).hexdigest()[:16] if shot.exists() else None
sys.path.insert(0, str(BASE / 'scripts'))
from s220_frame_truth import classify_frame_truth
truth = classify_frame_truth(str(shot), log) if shot.exists() else {'verdict': 'NO_SHOT'}

out = {'wall_s': wall, 'face_sha16': face, 'marks': marks,
       'frame_changes': {k: v for k, v in frame_hashes.items() if v == 'CHANGED'},
       'n_frame_changes': sum(1 for v in frame_hashes.values() if v == 'CHANGED'),
       'frame_truth': truth}
print(json.dumps(out, indent=1)[:2200])
(BASE / f'evidence/s220/S220_DOOZ_{TAG.upper()}.json').write_text(
    json.dumps(out, indent=1))
print('saved')
