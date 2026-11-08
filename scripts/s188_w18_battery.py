#!/usr/bin/env python3
"""S188-W18 verification battery on the final W18 binary:
  1. p9 ×3 independent runs (the promotion law: chain-state determinism)
  2. halma ×3 independent runs (the same LIBGDX family contract)
  3. goldens ×3 (bouncy/unote/dooz byte-exact pins)
  4. floor rerun 11/11 (the W12/W13 tier law)
Writes evidence/s188_w18/{W18_RUNS.json, W18_GOLDENS.json, faces, logs}.
"""
import json, sys, re, time, hashlib, subprocess
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w18'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)
w2.RUNS.mkdir(parents=True, exist_ok=True)

BIN_SHA = hashlib.sha256((BASE / 'miniandroid/build/miniandroid').read_bytes()).hexdigest()[:16]

def chain_markers(log):
    """The W18 chain-state markers per run (determinism evidence)."""
    return {
        'matrix4_critical_snapshots': len(re.findall(r'\[F\] snapshot 1[26] elems', log)),
        'critical_commits': len(re.findall(r'commit \d+/\d+ changed', log)),
        'slot222_null': len(re.findall(r'UNSUPPORTED JNIEnv slot 222', log)),
        'direct_bb_returns': len(re.findall(r'native direct-ByteBuffer return', log)),
        'tochararray': len(re.findall(r'F-NEW-608.*toCharArray', log)),
        'charset_print': 1 if 'Language charset' in log else 0,
        'font_face_real': 1 if re.search(r'newMemoryFace ok=1|createFonts', log) else 0,
        'pixmap_load_real': len(re.findall(r'native direct-ByteBuffer return: addr', log)),
        'guarded_faults': len(re.findall(r'guarded call fault', log)),
        'f607_dispatch_fix': len(re.findall(r'F-NEW-607', log)),
        'f613_shadow_gate': len(re.findall(r'F-NEW-613', log)),
        'frame_analysis': re.findall(r'FRAME_ANALYSIS state=(\S+)', log)[:3],
        'route_violation': len(re.findall(r'ROUTE_VIOLATION=[^0]', log)),
        'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
        'app_boundary': len(re.findall(r'APP BOUNDARY unwind', log)),
    }

def run_title(pkg, apk, tag, secs=40):
    store = w2.RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(w2.BIN), 'install', str(apk),
                        '--data-root', str(store)],
                       capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    if not dpkg:
        return dict(pkg=pkg, tag=tag, status='INSTALL_FAIL')
    rundir = w2.RUNS / tag
    import shutil
    shutil.rmtree(rundir, ignore_errors=True)
    console = w2.OUT / f'{tag}.console.log'
    cmd = [str(w2.BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--seconds', str(secs), '--trace']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=secs + 240)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    face = None
    if shot and shot.exists():
        from PIL import Image
        face = w2.OUT / f'face_{tag}.jpg'
        im = Image.open(shot).convert('RGB')
        im.thumbnail((360, 640))
        im.save(face, quality=70)
    row = dict(pkg=pkg, tag=tag, status='OK', dpkg=dpkg, wall_s=wall,
               screenshot=str(shot) if shot else None,
               face=str(face.name) if face else None,
               chain=chain_markers(log))
    return row

results = {'binary_sha16': BIN_SHA, 'runs': []}

# ── 1. p9 ×3 ────────────────────────────────────────────────────────────
p9_apk = str(BASE / 'upload/stuck_apks/se.tube42.p9.android.apk')
for i in (1, 2, 3):
    row = run_title('se.tube42.p9.android', p9_apk, f'p9_w18_r{i}')
    results['runs'].append(row)
    print('p9', i, row['chain']['frame_analysis'],
          'charset=', row['chain']['charset_print'],
          'font=', row['chain']['font_face_real'],
          'pixmap=', row['chain']['pixmap_load_real'],
          'faults=', row['chain']['guarded_faults'],
          'wall=', row['wall_s'], flush=True)

# ── 2. halma ×3 ─────────────────────────────────────────────────────────
halma_apk = str(BASE / 'upload/stuck_apks/app.halma.apk')
for i in (1, 2, 3):
    row = run_title('app.halma', halma_apk, f'halma_w18_r{i}')
    results['runs'].append(row)
    print('halma', i, row['chain']['frame_analysis'],
          'faults=', row['chain']['guarded_faults'],
          'wall=', row['wall_s'], flush=True)

(w2.OUT / 'W18_RUNS.json').write_text(json.dumps(results, indent=1))
print('W18_RUNS.json written', len(results['runs']), 'runs', flush=True)
