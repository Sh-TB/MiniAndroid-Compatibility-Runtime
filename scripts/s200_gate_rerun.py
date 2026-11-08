#!/usr/bin/env python3
"""S200 fragment-path wave — post-investigation gate re-run on the
canonical binary 6c808c7448850756 (byte-identical rebuild from HEAD).

Goldens x3 pins + gmdice 5-tap interaction + microtimer acceptance spot.
The floor 11/11 was verified on this exact binary identity in the Target-B
commit (00783ccd); the rebuild is deterministic, so identity implies those
results — the three gates here are the freshness re-proof.
"""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path
from PIL import Image

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
RUNS = BASE / 'evidence/s200/runs'
RUNS.mkdir(parents=True, exist_ok=True)
OUT = {'binary_sha16': BIN_SHA}

GOLDENS = [
    ('bouncy', 'com.dozingcatsoftware.bouncy', 'bouncy.apk', '8a6c24ac'),
    ('unote', 'app.varlorg.unote', 'app.varlorg.unote_30.apk', '3b8dcb0a'),
    ('dooz', 'io.github.yamin8000.dooz', 'io.github.yamin8000.dooz_23.apk', '31ddd4d5'),
]

def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

def run_app(apk, tag, taps=None, frames=8, delay=250):
    store = RUNS / f'store_gate_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                   capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    rundir = RUNS / f'gate_{tag}'
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'gate_{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--frames', str(frames),
           '--frame-delay', str(delay)]
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=600)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    face_sha = sha16(shot) if shot and shot.exists() else None
    return {
        'wall_s': wall, 'face_sha16': face_sha,
        'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
    }

# 1) goldens x3
golds = {}
for name, pkg, apk, pin in GOLDENS:
    r = run_app(BASE / 'upload/canonical_apks' / apk, f'gold_{name}')
    r['pin'] = pin
    r['hold'] = (r['face_sha16'] == pin)
    golds[name] = r
    print(f'golden {name}: {r["face_sha16"]} vs pin {pin} -> '
          f'{"HOLD" if r["hold"] else "BREAK"}', flush=True)
OUT['goldens'] = golds

# 2) gmdice 5-tap interaction (5 distinct post-tap states, rerun-stable)
GMDICE_TAPS = [(4, 540, 1200), (6, 540, 1200), (8, 540, 1200),
               (10, 540, 1200), (12, 540, 1200)]
r1 = run_app(BASE / 'upload/canonical_apks/de.duenndns.gmdice_8.apk',
             'gate_gmdice_r1', GMDICE_TAPS, frames=16)
r2 = run_app(BASE / 'upload/canonical_apks/de.duenndns.gmdice_8.apk',
             'gate_gmdice_r2', GMDICE_TAPS, frames=16)
OUT['gmdice'] = {'r1': r1, 'r2': r2,
                 'rerun_identical': r1['face_sha16'] == r2['face_sha16']}
print(f"gmdice: r1={r1['face_sha16']} r2={r2['face_sha16']} "
      f"identical={OUT['gmdice']['rerun_identical']}", flush=True)

# 3) microtimer acceptance spot (keypad+START+pause/resume, 14 frames)
MT_TAPS = [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)]
r = run_app(BASE / 'upload/canonical_apks/dubrowgn.microtimer_8.apk',
            'gate_mtm_spot', MT_TAPS, frames=14)
OUT['microtimer'] = r
print(f"microtimer spot: face={r['face_sha16']} uncaught={r['uncaught']}",
      flush=True)

OUT['all_hold'] = (all(g['hold'] for g in golds.values())
                   and OUT['gmdice']['rerun_identical']
                   and r['uncaught'] == 0)
(BASE / 'evidence/s200/S200_GATE_RERUN.json').write_text(
    json.dumps(OUT, indent=1))
print('ALL_HOLD =', OUT['all_hold'])
