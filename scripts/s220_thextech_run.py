#!/usr/bin/env python3
"""S220: TheXTech re-run on the post-isTaskRoot binary + frame-truth verdict.
GP-582 (comment 6807550504 §A): Launcher.onCreate calls isTaskRoot() BEFORE
super.onCreate and finish()es when false. Pre-fix the stub answered false ->
DESTROYED at ~6.4s virtual with 0 nodes / 0 draw ops / WINDOW_ROOT first
missing. Post-fix the root launch must answer true and proceed to
setContentView(R.layout.activity_launcher) -> initUiSetup() -> real UI."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/stuck_apks/ru.wohlsoft.thextech.fdroid.apk'
RUNS = BASE / 'evidence/s220/runs'
RUNS.mkdir(parents=True, exist_ok=True)

TAG = 's220_thextech_startgame'
store = RUNS / f'store_{TAG}'
store.mkdir(parents=True, exist_ok=True)
subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
               capture_output=True, timeout=300)
apps = store / 'data' / 'app'
dpkg = None
if apps.exists():
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith('.')
          and not d.name.endswith('.staging')
          and (d / 'base.apk').exists()]
    dpkg = ds[0] if ds else None
assert dpkg, "install failed"

rundir = RUNS / TAG
shutil.rmtree(rundir, ignore_errors=True)
console = RUNS / f'{TAG}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--frames', '20', '--frame-delay', '250']
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, cwd=str(BASE),
                   timeout=600)
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

# The discriminator chain (GP's demanded instrument points):
marks = {}
for name, pat in [
    ('isTaskRoot_calls', r'isTaskRoot'),
    ('setContentView', r'setContentView'),
    ('activity_finish', r'\bfinish\b'),
    ('DESTROYED', r'DESTROYED'),
    ('initUiSetup', r'initUiSetup'),
    ('launcher_layout', r'activity_launcher'),
    ('first_missing_stage', r'first_missing_stage=(\w+)'),
    ('uncaught', r'uncaught exception|FATAL'),
]:
    m = re.findall(pat, log)
    marks[name] = m if name == 'first_missing_stage' else len(m)

shot = rundir / 'screenshot.png'
face = hashlib.sha256(shot.read_bytes()).hexdigest()[:16] if shot.exists() else None
sys.path.insert(0, str(BASE / 'scripts'))
from s220_frame_truth import classify_frame_truth
truth = classify_frame_truth(str(shot), log) if shot.exists() else {'verdict': 'NO_SHOT'}

out = {'wall_s': wall, 'face_sha16': face, 'marks': marks,
       'frame_truth': truth}
print(json.dumps(out, indent=1)[:1800])
(BASE / 'evidence/s220/S220_THEXTECH_STARTGAME.json').write_text(
    json.dumps(out, indent=1))
print('saved -> evidence/s220/S220_THEXTECH_STARTGAME.json')
