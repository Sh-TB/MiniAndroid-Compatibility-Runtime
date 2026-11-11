#!/usr/bin/env python3
"""S214 gate — full 6-pin battery on the C7 W5->W11 rebase binary.
Standing pins (S212/S213 records): bouncy 8a6c24ac, unote 3b8dcb0a, dooz a0fae907,
gmdice 3891679d rerun-identical x2 uncaught=0, microtimer b39665f6 uncaught=0,
ttt 7354c1b2 deterministic x3 uncaught=0.
Run parameters == s207_gate.py exactly (the runner that produced the pins)."""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s214/runs'
RUNS.mkdir(parents=True, exist_ok=True)
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
OUT = {'binary_sha16': BIN_SHA,
       'base_commit': '4bf69d81 (C7 landed) + S214 diagnostics: F-NEW-632 SF-ORDER probe + NOISE-FENCE + CAPTURE-SIZE law, all env-gated/log-only default-neutral'}
GATE = RUNS / 'S214_GATE.json'


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
    # S214 noise heuristic (the >800KB gate law): a face PNG that big is
    # either legit rich content (app_draw_ops>0) or uninit-memory noise.
    if shot:
        nb = shot.stat().st_size
        rec['png_bytes'] = nb
        rec['noise_suspect'] = bool(nb > 800 * 1024)
        rec['noise_fence_fired'] = 'NOISE-FENCE' in log
    return rec


PINS = {'bouncy': '8a6c24ac', 'unote': '3b8dcb0a', 'dooz': 'a0fae907'}
golds = {}
for name, pkg in [('bouncy', 'com.dozingcatsoftware.bouncy'),
                  ('unote', 'app.varlorg.unote'),
                  ('dooz', 'io.github.yamin8000.dooz')]:
    apk = list((BASE / 'upload/canonical_apks').glob(f'{pkg}*.apk'))[0]
    r = run_app(apk, f's214_gold_{name}')
    r['pin'] = PINS[name]
    r['hold'] = bool(r['face_sha16'] and r['face_sha16'].startswith(PINS[name]))
    golds[name] = r
    print(f"golden {name}: {r['face_sha16']} vs {PINS[name]} -> "
          f"{'HOLD' if r['hold'] else 'BREAK'}", flush=True)
OUT['goldens'] = golds
GATE.write_text(json.dumps(OUT, indent=1))

GMDICE_TAPS = [(4, 540, 1200), (6, 540, 1200), (8, 540, 1200),
               (10, 540, 1200), (12, 540, 1200)]
gapk = list((BASE / 'upload/canonical_apks').glob('de.duenndns.gmdice*.apk'))[0]
r1 = run_app(gapk, 's214_gmdice_r1', GMDICE_TAPS, frames=16)
r2 = run_app(gapk, 's214_gmdice_r2', GMDICE_TAPS, frames=16)
OUT['gmdice'] = {'r1': r1, 'r2': r2,
                 'rerun_identical': r1['face_sha16'] == r2['face_sha16'],
                 'pin': '3891679d', 'hold': r1['face_sha16'].startswith('3891679d')}
print(f"gmdice: {r1['face_sha16']} / {r2['face_sha16']}", flush=True)
GATE.write_text(json.dumps(OUT, indent=1))

MT_TAPS = [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)]
mapk = list((BASE / 'upload/canonical_apks').glob('dubrowgn.microtimer*.apk'))[0]
mt = run_app(mapk, 's214_mtm_spot', MT_TAPS, frames=14)
OUT['microtimer'] = dict(mt, pin='b39665f6',
                         hold=mt['face_sha16'].startswith('b39665f6'))
print(f"microtimer: uncaught={mt['uncaught']} face={mt['face_sha16']}", flush=True)
GATE.write_text(json.dumps(OUT, indent=1))

t3 = []
tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]
for k in range(3):
    r = run_app(tapk, f's214_ttt{k}', frames=40, delay=250)
    t3.append(r)
    print(f"ttt{k}: face={r['face_sha16']} uncaught={r['uncaught']}", flush=True)
OUT['tictactoe'] = {'runs': t3, 'pin': '7354c1b2',
                    'deterministic_x3': len({r['face_sha16'] for r in t3}) == 1,
                    'hold': all(r['face_sha16'].startswith('7354c1b2') for r in t3)}
GATE.write_text(json.dumps(OUT, indent=1))

all_hold = (all(g['hold'] for g in OUT['goldens'].values())
            and OUT['gmdice']['hold'] and OUT['gmdice']['rerun_identical']
            and OUT['microtimer']['hold'] and OUT['tictactoe']['hold'])
OUT['ALL_PINS_HOLD'] = all_hold
GATE.write_text(json.dumps(OUT, indent=1))
print(f"S214 GATE RESULT: ALL_PINS_HOLD={all_hold}")
