#!/usr/bin/env python3
"""S216 FULL 6-PIN GATE on the CONT-132-fixed binary (chunked per-pin driver).
Usage: s216_gate.py <pin>   with pin in: bouncy unote dooz gmdice microtimer ttt
Writes evidence/s216/S216_GATE.json incrementally (one key per pin)."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s216/gate_runs'
RUNS.mkdir(parents=True, exist_ok=True)
GATE = BASE / 'evidence/s216/S216_GATE.json'

PINS = {
    'bouncy': ('com.dozingcatsoftware.bouncy', '8a6c24ac8a7d718e', None, 8, 250),
    'unote': ('app.varlorg.unote', '3b8dcb0adbbc17a9', None, 8, 250),
    'dooz': ('io.github.yamin8000.dooz', 'a0fae9072313e2d1', None, 5, 250),
    'gmdice': ('de.duenndns.gmdice', '3891679dff449331', None, 16, 250),
    'microtimer': ('dubrowgn.microtimer', 'b39665f68f3938e6',
                   [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)],
                   14, 250),
    'ttt': ('com.emmanuelmess.tictactoe', '7354c1b231cd581d', None, 40, 250),
}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_app(apk, tag, taps=None, frames=8, delay=250, timeout=560):
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
    try:
        with open(console, 'wb') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           cwd=str(BASE), timeout=timeout)
        rc = 0
    except subprocess.TimeoutExpired:
        rc = 124
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'screenshot.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    png_bytes = shot.stat().st_size if shot and shot.exists() else 0
    noise_suspect = png_bytes > 800 * 1024
    return {'rc': rc, 'wall_s': wall,
            'face_sha16': sha16(shot) if shot else None,
            'png_bytes': png_bytes, 'noise_suspect': noise_suspect,
            'uncaught': len(re.findall(r'uncaught exception|FATAL', log)),
            'in_flight': len(re.findall(r'in-flight exception', log))}


def main(pin):
    pkg, want, taps, frames, delay = PINS[pin]
    apk = list((BASE / 'upload/canonical_apks').glob(f'{pkg}*.apk'))[0]
    out = json.load(open(GATE)) if GATE.exists() else {
        'binary_sha16': hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]}
    if pin == 'gmdice':
        r1 = run_app(apk, 's216_gmdice_r1', taps, frames, delay)
        r2 = run_app(apk, 's216_gmdice_r2', taps, frames, delay)
        out['gmdice'] = {'r1': r1, 'r2': r2,
                         'rerun_identical': r1['face_sha16'] == r2['face_sha16'],
                         'hold': r1['face_sha16'] == want}
        print(f"gmdice: {r1['face_sha16']} / {r2['face_sha16']} "
              f"identical={r1['face_sha16'] == r2['face_sha16']} want={want}")
    elif pin == 'ttt':
        runs = [run_app(apk, f's216_ttt{i}', taps, frames, delay) for i in range(3)]
        det = len({r['face_sha16'] for r in runs}) == 1
        out['ttt'] = {'runs': runs, 'deterministic_x3': det,
                      'hold': det and runs[0]['face_sha16'] == want}
        for i, r in enumerate(runs):
            print(f"ttt{i}: face={r['face_sha16']} uncaught={r['uncaught']}")
        print(f"ttt: det_x3={det} want={want}")
    elif pin == 'microtimer':
        r = run_app(apk, 's216_mt', taps, frames, delay)
        r['hold'] = r['face_sha16'] == want
        out['microtimer'] = r
        print(f"microtimer: face={r['face_sha16']} uncaught={r['uncaught']} want={want}")
    else:
        r = run_app(apk, f's216_gold_{pin}', taps, frames, delay)
        r['pin'] = want
        r['hold'] = bool(r['face_sha16'] and r['face_sha16'].startswith(want[:8]))
        out[pin] = r
        print(f"{pin}: face={r['face_sha16']} want={want} "
              f"hold={r['hold']} wall={r['wall_s']}s png={r['png_bytes']}")
    GATE.write_text(json.dumps(out, indent=1))
    # summary line
    holds = []
    for k, v in out.items():
        if k == 'binary_sha16':
            continue
        if k == 'gmdice':
            holds.append(f"gmdice={v['hold']}/{v['rerun_identical']}")
        elif k == 'ttt':
            holds.append(f"ttt={v['hold']}")
        else:
            holds.append(f"{k}={v['hold']}")
    print('GATE-STATE:', ' '.join(holds))


if __name__ == '__main__':
    main(sys.argv[1])
