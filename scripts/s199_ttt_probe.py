#!/usr/bin/env python3
"""S199 P0 probe — tictactoe on the S199 integration binary (41fa84237a1b9e73).

One clean run, no taps: how deep does the launch go now that the S196
String-boundary family (F-NEW-588 replaceAll → AssetDescriptor.fileName,
F-NEW-589 Stack LIFO → AssetManager taskQueue, F-NEW-580/580b identity
normalization) is in? The S195 dying point was AssetManager.load pc=340
NPE String.equals(null).
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
APK = BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
OUT = BASE / 'evidence/s199'
RUNS = OUT / 'runs'
RUNS.mkdir(parents=True, exist_ok=True)

tag = 'ttt_s199_probe_r1'
store = RUNS / f'store_{tag}'
store.mkdir(parents=True, exist_ok=True)
SECS = 40

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
print('dpkg:', dpkg, 'install rc:', r.returncode)

rundir = RUNS / tag
shutil.rmtree(rundir, ignore_errors=True)
console = OUT / f'{tag}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--seconds', str(SECS), '--trace']
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=SECS + 240)
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

markers = {
    'binary_sha16': BIN_SHA,
    'wall_s': wall,
    'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
    'app_boundary': len(re.findall(r'APP BOUNDARY unwind', log)),
    'frame_analysis': re.findall(r'FRAME_ANALYSIS state=(\S+)', log)[:4],
    's186i_stubs': len(re.findall(r'\[S186I-STUB\]', log)),
    'f588_replaceAll': len(re.findall(r'\[F-NEW-588\]', log)),
    'f589_stack': len(re.findall(r'\[F-NEW-589\]', log)),
    'f582_alloc': len(re.findall(r'\[F-NEW-582\] allocateDirect', log)),
    'f582b_copy': len(re.findall(r'\[F-NEW-582b\]', log)),
    'f582_lookup': len(re.findall(r'\[F-NEW-582\] direct-buffer', log)),
    'npe_asset_load': len(re.findall(r'AssetManager;.load pc=\d+ exception', log)),
    'gdice': None,
}
exc = re.findall(r'\[EXCEPTION\] method=(\S+) exception=(\S+) msg="([^"]*)"', log)
markers['first_divergence'] = exc[0] if exc else None
shot = rundir / 'final_frame.png'
if not shot.exists():
    cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
    shot = cands[-1] if cands else None
if shot and shot.exists():
    import shutil as sh
    face = OUT / f'face_{tag}.jpg'
    sh.copy(shot, face)
    markers['face'] = str(face)
    # honest depth: unique colors / noise check
    try:
        from PIL import Image
        im = Image.open(shot).convert('RGB')
        cols = im.getcolors(maxcolors=1 << 24)
        n = len(cols) if cols else 0
        total = im.width * im.height
        markers['unique_colors'] = n
        if cols:
            bg_share = max(c for _, c in cols) / total
            markers['bg_share'] = round(bg_share, 4)
    except Exception as e:
        markers['depth_err'] = str(e)
print(json.dumps(markers, indent=1, default=str))
(OUT / f'{tag}.PROBE.json').write_text(json.dumps(markers, indent=1, default=str))
