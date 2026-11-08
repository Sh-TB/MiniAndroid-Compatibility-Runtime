#!/usr/bin/env python3
"""S188-W18 smoke run: se.tube42.p9.android on the F-NEW-605 binary
(5ae795bfa58e9d77). Fast probe of the primitive-array critical family:
slot 222/223 (Get/ReleasePrimitiveArrayCritical) + 229 (NewDirectByteBuffer)
+ the direct-ByteBuffer return marshal. Verdict markers:
  [F-NEW-605] GetPrimitiveArrayCritical(oid=..) snapshot  — slots live
  [F-NEW-605] native direct-ByteBuffer return             — marshal live
  UNSUPPORTED JNIEnv slot 222                              — must be GONE
  Gdx2DPixmap load frontier — what replaces the old fault?
"""
import subprocess, sys, re, shutil, os
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w18'
RUNS = OUT / 'runs'
OUT.mkdir(parents=True, exist_ok=True)
RUNS.mkdir(parents=True, exist_ok=True)

pkg = 'se.tube42.p9.android'
apk = BASE / 'upload/stuck_apks/se.tube42.p9.android.apk'
tag = 'p9_w18smoke'
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
print('install rc=', r.returncode, 'dpkg=', dpkg)
if not dpkg:
    print((r.stdout[-500:] + r.stderr[-500:]).decode('utf-8', 'ignore'))
    sys.exit(1)

rundir = RUNS / tag
shutil.rmtree(rundir, ignore_errors=True)
console = OUT / f'{tag}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--seconds', str(SECS), '--trace']
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=SECS + 240)
log = console.read_text(errors='ignore')

markers = {
    'slot222_get': len(re.findall(r'GetPrimitiveArrayCritical.*snapshot', log)),
    'slot222_null': len(re.findall(r'not a\s+"?\s*live DEX primitive array', log)),
    'slot229_native_bb_ret': len(re.findall(r'native direct-ByteBuffer return', log)),
    'unsupported_222': len(re.findall(r'UNSUPPORTED JNIEnv slot 222', log)),
    'unsupported_any': len(re.findall(r'UNSUPPORTED JNIEnv slot', log)),
    'critical_write_commit': len(re.findall(r'commit', log)),
    'gdx2d_load': len(re.findall(r'Gdx2DPixmap', log)),
    'pixmap_error': len(re.findall(r'Error loading pixmap', log)),
    'frame_analysis': re.findall(r'FRAME_ANALYSIS.*', log)[:3],
    'route_decision': re.findall(r'\[ROUTE\] DECISION.*', log)[:2],
    'route_violation': len(re.findall(r'ROUTE_VIOLATION=[^0]', log)),
    'uncaught': len(re.findall(r'FATAL|Uncaught|uncaught exception', log)),
    'app_boundary': re.findall(r'APP BOUNDARY.*', log)[-3:],
    'guarded_fault': len(re.findall(r'guarded call fault', log)),
    'texture': len(re.findall(r'Texture|Pixmap', log)),
}
for k, v in markers.items():
    print(f'{k:26s} {v}')
print('--- log lines around pixmap/gdx2d ---')
for ln in log.splitlines():
    if ('Gdx2DPixmap' in ln or 'pixmap' in ln or 'F-NEW-605' in ln
            or 'slot 222' in ln or 'slot 223' in ln or 'slot 229' in ln):
        print(ln[:220])
