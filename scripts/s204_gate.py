#!/usr/bin/env python3
"""S204 gate — full regression battery on the F-NEW-630 binary 4f5c5b9a11a8b9d2.
Bases: bouncy re-pin 90c18ddf (S203 record), unote 3b8dcb0a, dooz plain a0fae907,
gmdice rerun-identical (standing 3891679d), microtimer 0-uncaught (b39665f6),
tictactoe NEW face (board now draws) deterministic x3 + clean center."""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s204/runs'
RUNS.mkdir(parents=True, exist_ok=True)
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
OUT = {'binary_sha16': BIN_SHA}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_app(apk, tag, taps=None, frames=8, delay=250):
    store = RUNS / f'store_{tag}'
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
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--frames', str(frames),
           '--frame-delay', str(delay)]
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=900)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'screenshot.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    rec = {'wall_s': wall, 'face_sha16': sha16(shot) if shot else None,
           'uncaught': len(re.findall(r'uncaught exception|FATAL', log))}
    return rec


GOLDENS = [
    ('bouncy', 'com.dozingcatsoftware.bouncy', 'com.dozingcatsoftware.bouncy_43.apk', '90c18ddf'),
    ('unote', 'app.varlorg.unote', 'app.varlorg.unote_30.apk', '3b8dcb0a'),
    ('dooz', 'io.github.yamin8000.dooz', 'io.github.yamin8000.dooz_23.apk', 'a0fae907'),
]
# resolve actual apk filenames
golds = {}
for name, pkg, apk_hint, pin in GOLDENS:
    cands = list((BASE / 'upload/canonical_apks').glob(f'{pkg}*.apk'))
    apk = cands[0] if cands else BASE / 'upload/canonical_apks' / apk_hint
    r = run_app(apk, f's204_gold_{name}')
    r['pin'] = pin
    r['hold'] = bool(r['face_sha16'] and r['face_sha16'].startswith(pin))
    golds[name] = r
    print(f"golden {name}: {r['face_sha16']} vs {pin} -> "
          f"{'HOLD' if r['hold'] else 'BREAK'}", flush=True)
OUT['goldens'] = golds

GMDICE_TAPS = [(4, 540, 1200), (6, 540, 1200), (8, 540, 1200),
               (10, 540, 1200), (12, 540, 1200)]
gapk = list((BASE / 'upload/canonical_apks').glob('de.duenndns.gmdice*.apk'))[0]
r1 = run_app(gapk, 's204_gmdice_r1', GMDICE_TAPS, frames=16)
r2 = run_app(gapk, 's204_gmdice_r2', GMDICE_TAPS, frames=16)
OUT['gmdice'] = {'r1': r1, 'r2': r2,
                 'rerun_identical': r1['face_sha16'] == r2['face_sha16']}
print(f"gmdice: {r1['face_sha16']} / {r2['face_sha16']}", flush=True)

MT_TAPS = [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)]
mapk = list((BASE / 'upload/canonical_apks').glob('dubrowgn.microtimer*.apk'))[0]
mt = run_app(mapk, 's204_mtm_spot', MT_TAPS, frames=14)
OUT['microtimer'] = mt
print(f"microtimer: uncaught={mt['uncaught']} face={mt['face_sha16']}", flush=True)

t3 = []
tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]
for k in range(3):
    r = run_app(tapk, f's204_ttt{k}', frames=40, delay=250)
    t3.append(r)
    print(f"ttt{k}: face={r['face_sha16']} uncaught={r['uncaught']}", flush=True)
OUT['tictactoe'] = {'runs': t3,
                    'deterministic_x3': len({r['face_sha16'] for r in t3}) == 1}
(RUNS / 'S204_GATE.json').write_text(json.dumps(OUT, indent=1))
print('WROTE S204_GATE.json')
