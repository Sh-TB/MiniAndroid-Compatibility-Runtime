#!/usr/bin/env python3
"""S199 — the integrated-runtime application battery (reduced: 1 run per
app + the tictactoe 3-run block). Records depth markers honestly against
the S199 binary identity."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

OUT = BASE / 'evidence/s199'
COHORT = OUT / 'battery'
(COHORT / 'runs').mkdir(parents=True, exist_ok=True)
w2.OUT = COHORT
w2.RUNS = COHORT / 'runs'
w2.SECS = 30

BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]

APPS = {
    'microtimer': BASE / 'upload/canonical_apks/dubrowgn.microtimer_8.apk',
    'opencalc':   BASE / 'upload/opencalculator_53.apk',
    'chessclock': BASE / 'upload/chessclock_29.apk',
}


def apk_sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def run_app(name, apk, run_idx):
    tag = f'{name}_s199_r{run_idx}'
    store = w2.RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(w2.BIN), 'install', str(apk), '--data-root',
                        str(store)], capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    if not dpkg:
        return dict(app=name, tag=tag, status='INSTALL_FAIL')
    rundir = w2.RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = COHORT / f'{tag}.console.log'
    cmd = [str(w2.BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--seconds', str(w2.SECS), '--trace']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=w2.SECS + 240)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    depth = None
    face = None
    if shot and shot.exists():
        fc = COHORT / f'face_{tag}.jpg'
        shutil.copy(shot, fc)
        face = str(fc)
        try:
            from PIL import Image
            im = Image.open(shot).convert('RGB')
            cols = im.getcolors(maxcolors=1 << 24) or []
            total = im.width * im.height
            depth = {
                'unique_colors': len(cols),
                'bg_share': round(max(c for _, c in cols) / total, 4)
                if cols else None,
            }
        except Exception as e:
            depth = {'err': str(e)}
    return dict(
        app=name, tag=tag, status='OK', dpkg=dpkg, wall_s=wall,
        apk_sha256=apk_sha(apk), binary_sha16=BIN_SHA,
        uncaught=len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
        app_boundary=len(re.findall(r'APP BOUNDARY unwind', log)),
        frame_analysis=re.findall(r'FRAME_ANALYSIS state=(\S+)', log)[:3],
        depth=depth, face=face,
    )


def main():
    results = []
    only = sys.argv[1:] or list(APPS)
    for name in only:
        results.append(run_app(name, APPS[name], 1))
        print(json.dumps(results[-1], default=str)[:260], flush=True)
    (COHORT / 'S199_BATTERY.json').write_text(
        json.dumps({'binary_sha16': BIN_SHA, 'runs': results}, indent=1))
    print('BATTERY DONE', BIN_SHA)


if __name__ == '__main__':
    main()
