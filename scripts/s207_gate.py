#!/usr/bin/env python3
"""S207 gate — baseline-protection battery on the rebuilt post-C9 binary.
Expected pins per the S206 record (commit cad6467b): bouncy 98abca38
(RE-PINNED at S226: 8a6c24ac was the menu face over the DEFAULT theme
fill #303030; the F-BLANK-1 launch-theme law resolves the app's real
theme windowBackground (#000000, Theme.Black family) and the F-GLZ-2
under-lay compositor law keeps the menu above the GL surface — the face
changed exactly in the background fill, menu panel/buttons/text pixels
byte-identical 746-distinct-color face, 0 uncaught, verified visually),
unote 3b8dcb0a, dooz a0fae907, gmdice 3891679d rerun-identical,
microtimer 0-uncaught face b39665f6, tictactoe deterministic x3 face
7354c1b231cd581d (re-pinned by the C9-16/17 font-family law).
PHASE env: 'goldens' | 'fast' | 'all' (foreground chunks to survive the sandbox)."""
import hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
PHASE = os.environ.get('S207_PHASE', 'all')
import os
BIN = Path(os.environ.get('MINIANDROID_BIN') or
          BASE / 'miniandroid/build/miniandroid')  # S236 audit: env override, default unchanged
RUNS = BASE / 'evidence/s207/runs'
RUNS.mkdir(parents=True, exist_ok=True)
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
GATE = RUNS / 'S207_GATE.json'
OUT = {}
if GATE.exists():
    try:
        OUT.update(json.loads(GATE.read_text()))
    except Exception:
        pass
# Current binary identity LAST — the cached file's binary_sha16 must never
# mask the binary this gate is actually verifying (wave-2 fix: the old order
# let a stale cache row mislabel the gate record).
OUT['binary_sha16'] = BIN_SHA


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
    # WP10 §7 prevention (#587): size/noise policy — a screenshot above the
    # byte budget is colored-noise suspicion (uninitialized framebuffer bytes
    # compress badly), never silently accepted as evidence.
    if shot is not None:
        nbytes = shot.stat().st_size
        rec['screenshot_bytes'] = nbytes
        if nbytes > 1_048_576:
            rec['screenshot_verdict'] = 'NOISE >1MiB (canonical allowlist entry required)'
        elif nbytes > 800_000:
            rec['screenshot_verdict'] = 'NOISE-SUSPECT >800KB'
        else:
            rec['screenshot_verdict'] = 'OK'
    return rec


if PHASE in ('goldens', 'all'):
    GOLDENS = [
        ('bouncy', 'com.dozingcatsoftware.bouncy', '98abca38'),
        ('unote', 'app.varlorg.unote', '3b8dcb0a'),
        ('dooz', 'io.github.yamin8000.dooz', 'a0fae907'),
    ]
    golds = OUT.get('goldens', {})
    for name, pkg, pin in GOLDENS:
        if name in golds and golds[name].get('hold') and golds[name].get('binary') == BIN_SHA:
            print(f"golden {name}: cached HOLD", flush=True)
            continue
        apk = list((BASE / 'upload/canonical_apks').glob(f'{pkg}*.apk'))[0]
        r = run_app(apk, f's207_gold_{name}')
        r['pin'] = pin
        r['binary'] = BIN_SHA
        r['hold'] = bool(r['face_sha16'] and r['face_sha16'].startswith(pin))
        golds[name] = r
        print(f"golden {name}: {r['face_sha16']} vs {pin} -> "
              f"{'HOLD' if r['hold'] else 'BREAK'}", flush=True)
    OUT['goldens'] = golds
    GATE.write_text(json.dumps(OUT, indent=1))
    print('PHASE goldens DONE', flush=True)

if PHASE in ('fast', 'all'):
    GMDICE_TAPS = [(4, 540, 1200), (6, 540, 1200), (8, 540, 1200),
                   (10, 540, 1200), (12, 540, 1200)]
    gapk = list((BASE / 'upload/canonical_apks').glob('de.duenndns.gmdice*.apk'))[0]
    r1 = run_app(gapk, 's207_gmdice_r1', GMDICE_TAPS, frames=16)
    r2 = run_app(gapk, 's207_gmdice_r2', GMDICE_TAPS, frames=16)
    OUT['gmdice'] = {'r1': r1, 'r2': r2,
                     'rerun_identical': r1['face_sha16'] == r2['face_sha16']}
    print(f"gmdice: {r1['face_sha16']} / {r2['face_sha16']} "
          f"identical={OUT['gmdice']['rerun_identical']}", flush=True)

    MT_TAPS = [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)]
    mapk = list((BASE / 'upload/canonical_apks').glob('dubrowgn.microtimer*.apk'))[0]
    mt = run_app(mapk, 's207_mtm_spot', MT_TAPS, frames=14)
    OUT['microtimer'] = mt
    print(f"microtimer: uncaught={mt['uncaught']} face={mt['face_sha16']}", flush=True)

    t3 = []
    tapk = list((BASE / 'upload/canonical_apks').glob('com.emmanuelmess.tictactoe*.apk'))[0]
    for k in range(3):
        r = run_app(tapk, f's207_ttt{k}', frames=40, delay=250)
        t3.append(r)
        print(f"ttt{k}: face={r['face_sha16']} uncaught={r['uncaught']}", flush=True)
    OUT['tictactoe'] = {'runs': t3,
                        'deterministic_x3': len({r['face_sha16'] for r in t3}) == 1}
    GATE.write_text(json.dumps(OUT, indent=1))
    print('PHASE fast DONE', flush=True)

print('GATE', json.dumps({k: v for k, v in OUT.items() if k != 'goldens'})[:400])
print('GOLDENS', json.dumps(OUT.get('goldens', {}))[:400])
