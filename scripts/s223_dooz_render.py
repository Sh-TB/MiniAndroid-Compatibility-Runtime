#!/usr/bin/env python3
"""S223: dooz complete-render attempt — the S222 frame-bridge cadence (complete-render config)
applied to the real NewGame chain probe, with frame-truth verification of the FINAL frame."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
RUNS = BASE / 'evidence/s223/runs'
RUNS.mkdir(parents=True, exist_ok=True)

TAG = sys.argv[1] if len(sys.argv) > 1 else 's223_dooz_render'
taps = sys.argv[2] if len(sys.argv) > 2 else '875,1823@6'
frames = sys.argv[3] if len(sys.argv) > 3 else '30'

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
env = dict(**__import__('os').environ)
env['MINIANDROID_S222_FRAME_BRIDGE'] = '1'   # the complete-render cadence (S222 law)
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--frames', frames, '--frame-delay', '250']
for t in taps.split(';'):
    cmd += ['--tap', t]
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, cwd=str(BASE),
                   timeout=2400, env=env)
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

shot = rundir / 'screenshot.png'
sha = hashlib.sha256(shot.read_bytes()).hexdigest()[:16] if shot.exists() else 'NO_SHOT'
png_bytes = shot.stat().st_size if shot.exists() else 0

# frame-truth on the final frame
try:
    sys.path.insert(0, str(BASE / 'scripts'))
    from s220_frame_truth import verify_frame  # noqa
    ft = verify_frame(shot)
except Exception:
    ft = {'verdict': 'VERIFY_ERROR', 'metrics': {'png_bytes': png_bytes}}

# the chain marks the S220 probe grades
marks = {}
for name, pat in [
    ('tap_receipt', r'tap_receipt|TAP-RECEIPT|click.*dispatched|CLICK-DISPATCH'),
    ('newgame_action', r'NewGame|newGame|GameAction'),
    ('compose_recompose', r'recompos|Recomposer'),
    ('gameboard', r'GameBoard|LazyGrid|gameboard'),
    ('ise_storm', r'InlineDensity|MultiParagraph'),
    ('app_boundary', r'APP.?BOUNDARY'),
    ('bridge', r'S222.*BRIDGE|FRAME-BRIDGE'),
]:
    marks[name] = len(re.findall(pat, log))

out = {
    'tag': TAG, 'wall_s': wall, 'face_sha16': sha, 'png_bytes': png_bytes,
    'frame_truth': ft, 'marks': marks,
}
json.dump(out, open(RUNS / f'{TAG}.json', 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:2000])
