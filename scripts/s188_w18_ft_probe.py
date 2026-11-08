#!/usr/bin/env python3
"""S188-W18b probe: run p9 with MINIANDROID_W18_FT_TRACE=1 — an env-gated
probe in the runtime prints the newMemoryFace native call's marshalled args
(library, buffer oid, size, faceIndex) and the FT error code after the call.
This run also checks whether the persistent backing really carries the TTF
magic (0x00010000 for TTF) after the copy."""
import subprocess, os, re, shutil
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w18'
RUNS = OUT / 'runs'
pkg = 'se.tube42.p9.android'
apk = BASE / 'upload/stuck_apks/se.tube42.p9.android.apk'
tag = 'p9_w18ft'
store = RUNS / f'store_{tag}'
store.mkdir(parents=True, exist_ok=True)
SECS = 40

r = subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                   capture_output=True, timeout=300)
apps = store / 'data' / 'app'
dpkg = None
if apps.exists():
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith('.')
          and not d.name.endswith('.staging')
          and (d / 'base.apk').exists()]
    dpkg = ds[0] if ds else None
assert dpkg, 'install failed'

rundir = RUNS / tag
shutil.rmtree(rundir, ignore_errors=True)
console = OUT / f'{tag}.console.log'
env = dict(os.environ)
env['MINIANDROID_W18_FT_TRACE'] = '1'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--seconds', str(SECS)]
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=SECS + 240, env=env)
log = console.read_text(errors='ignore')
for ln in log.splitlines():
    if ('W18-FT' in ln or 'F-NEW-609' in ln or 'newMemoryFace' in ln
            or 'copyJni' in ln):
        print(ln[:200])
