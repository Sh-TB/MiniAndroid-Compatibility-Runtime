#!/usr/bin/env python3
"""S206 gate — full regression battery on the C9-rebased binary (HEAD 45d019fc +
S198 rebased phase-3 parts 1-4). Pins = the S204 records: bouncy 8a6c24ac,
unote 3b8dcb0a, dooz a0fae907, gmdice rerun-identical (standing 3891679d),
microtimer 0-uncaught face b39665f6, tictactoe no-tap face f1157d7eba20bedf
deterministic x3 + center-tap interaction."""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s206/runs'
RUNS.mkdir(parents=True, exist_ok=True)
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
OUT = {'binary_sha16': BIN_SHA, 'base': '0979678e + S198 rebased phase-3 parts 1-4'}


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
    ('bouncy', 'com.dozingcatsoftware.bouncy', '8a6c24ac'),
    ('unote', 'app.varlorg.unote', '3b8dcb0a'),
    ('dooz', 'io.github.yamin8000.dooz', 'a0fae907'),
]
golds = {}
for name, pkg, pin in GOLDENS:
    apk = list((BASE / 'upload/canonical_apks').glob(f'{pkg}*.apk'))[0]
    r = run_app(apk, f's206_gold_{name}')
    r['pin'] = pin
    r['hold'] = bool(r['face_sha16'] and r['face_sha16'].startswith(pin))
    golds[name] = r
    print(f"golden {name}: {r['face_sha16']} vs {pin} -> "
          f"{'HOLD' if r['hold'] else 'BREAK'}", flush=True)
OUT['goldens'] = golds

GMDICE_TAPS = [(4, 540, 1200), (6, 540, 1200), (8, 540, 1200),
               (10, 540, 1200), (12, 540, 1200)]
gapk = list((BASE / 'upload/canonical_apks').glob('de.duenndns.gmdice*.apk'))[0]
r1 = run_app(gapk, 's206_gmdice_r1', GMDICE_TAPS, frames=16)
r2 = run_app(gapk, 's206_gmdice_r2', GMDICE_TAPS, frames=16)
OUT['gmdice'] = {'r1': r1, 'r2': r2,
                 'rerun_identical': r1['face_sha16'] == r2['face_sha16']}
print(f"gmdice: {r1['face_sha16']} / {r2['face_sha16']} identical="
      f"{r1['face_sha16'] == r2['face_sha16']}", flush=True)

MT_TAPS = [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)]
mapk = list((BASE / 'upload/canonical_apks').glob('dubrowgn.microtimer*.apk'))[0]
mt = run_app(mapk, 's206_mtm_spot', MT_TAPS, frames=14)
OUT['microtimer'] = mt
print(f"microtimer: uncaught={mt['uncaught']} face={mt['face_sha16']}", flush=True)

tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]
t3 = []
for k in range(3):
    r = run_app(tapk, f's206_ttt{k}', frames=40, delay=250)
    t3.append(r)
    print(f"ttt{k}: face={r['face_sha16']} uncaught={r['uncaught']}", flush=True)
tap = run_app(tapk, 's206_ttt_tap', taps=[(10, 540, 760), (16, 250, 480)], frames=22)
OUT['tictactoe'] = {'runs': t3,
                    'deterministic_x3': len({r['face_sha16'] for r in t3}) == 1,
                    'tap': tap}
print(f"ttt tap: face={tap['face_sha16']} uncaught={tap['uncaught']}", flush=True)
(RUNS / 'S206_GATE.json').write_text(json.dumps(OUT, indent=1))
print('WROTE S206_GATE.json')
