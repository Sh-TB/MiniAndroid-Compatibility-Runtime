#!/usr/bin/env python3
"""S210 — dooz post-nav zombie diagnostic on Main (binary e6287d1a2c175cf0).

Same SHA-pinned APK + recipe as the S208 ng2 run (tap (875,1823)@8,
frames=12, delay=100) but with MINIANDROID_S36_TRACE=1: the bounded AOOB
evidence probe logs the ARRAY OBJECT (id, class, len, idx, caller) for the
first 8 out-of-bounds hits — the zombie-array identifier.

Output: evidence/s210/runs/s210_dooz_s36/ + s210_dooz_s36.console.log
        evidence/s210/S210_DOOZ_S36.json
"""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s207/runs'
OUT = BASE / 'evidence/s210'
RUN = OUT / 'runs/s210_dooz_s36'
STORE = RUNS / 'store_s210_dooz_s36'
APK = BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'

def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

def main():
    STORE.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(STORE)],
                   capture_output=True, timeout=300)
    apps = STORE / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    shutil.rmtree(RUN, ignore_errors=True)
    console = OUT / 's210_dooz_s36.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(RUN),
           '--package', dpkg, '--frames', '12', '--frame-delay', '100',
           '--tap', '875,1823@8']
    t0 = time.time()
    import os
    env = os.environ.copy()
    env['MINIANDROID_S36_TRACE'] = '1'
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=900, env=env)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = RUN / 'screenshot.png'
    face = sha16(shot) if shot.exists() else None
    s36 = re.findall(r'\[S36-AOOB\][^\n]*', log)
    uncaught = len(re.findall(r'uncaught at caller', log))
    rec = {'wall_s': wall, 'face_sha16': face, 'uncaught_escapes': uncaught,
           's36_oob_lines': s36,
           'apk_sha16': sha16(APK), 'binary_sha16': sha16(BIN)}
    (OUT / 'S210_DOOZ_S36.json').write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1)[:3000])

if __name__ == '__main__':
    main()
