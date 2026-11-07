#!/usr/bin/env python3
"""S188-W12 T1: unwind-grade __cxa_throw probe on queens RunBundle bad_alloc.
LD_PRELOAD the W10 throw probe, run the 35s real-dalvik invocation, capture
the throw-site backtrace with maps offset symbolization.
"""
import json, re, subprocess, sys, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
SECS = 35
PKG = 'com.sidhant.queens'
STORE = BASE / f'evidence/s188_w2/runs/store_{PKG}'
APK = BASE / f'upload/stuck_apks/{PKG}.apk'
OUT = BASE / 'evidence/s188_w12'
RUNDIR = OUT / 'runs' / 'w12_f596_4'
LOG = OUT / 'w12_f596_4.console.log'
PROBE = '/tmp/w12_new_probe.so'

def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RUNDIR.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.rmtree(RUNDIR, ignore_errors=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(STORE)],
                   capture_output=True, timeout=120)
    apps = STORE / 'data' / 'app'
    dpkg = sorted(d.name for d in apps.iterdir()
                  if d.is_dir() and not d.name.startswith('.')
                  and not d.name.endswith('.staging')
                  and (d / 'base.apk').exists())[0]
    env = {'LD_PRELOAD': PROBE, 'PATH': '/usr/bin:/bin'}
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(RUNDIR),
           '--package', dpkg, '--seconds', str(SECS), '--trace']
    with open(LOG, 'wb') as cf:
        p = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT, env=env)
        try:
            p.wait(timeout=SECS)
            status = f'exit={p.returncode}'
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); status = 'killed-timeout'
    text = LOG.read_text(errors='replace')
    throws = re.findall(r'\[W10-CXA-THROW\].*', text)
    result = {
        'task': 'F-NEW-596 corrupt-box boundary run',
        'wave': 'S188-W12',
        'status': status,
        'binary_sha16': sha16(BIN),
        'throw_lines': len(throws),
        'throw_dump': throws[:80],
        'guarded_fault': re.findall(r'\[S2-NATIVE\] guarded call fault.*', text),
        'log': str(LOG.relative_to(BASE)),
    }
    (OUT / 'W12_T1_THROW_PROBE.json').write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k != 'throw_dump'}, indent=1))
    print('THROW SAMPLE:'); [print(l[:200]) for l in throws[:40]]

if __name__ == '__main__':
    main()
