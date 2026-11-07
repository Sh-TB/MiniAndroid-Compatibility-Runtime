#!/usr/bin/env python3
"""S188 W8 frontier-1: queens JNIEnv slot census — the exact demand list.

Runs com.sidhant.queens (Flutter lane, libflutter dlopen OK since W2) and
extracts the [MINIANDROID-JNI] UNSUPPORTED slot census the F-NEW-584
instrumentation prints at exit. Ground truth for which JNI slots the
Dart VM actually needs.
"""
import json, subprocess, shutil, re
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w8'
RUNS = BASE / 'evidence/s188_w2/runs'
SECS = 45
PKG = 'com.sidhant.queens'

store = RUNS / f'store_{PKG}'
store.mkdir(parents=True, exist_ok=True)
apps = store / 'data' / 'app'
dpkg = [d.name for d in sorted(apps.iterdir())
        if d.is_dir() and not d.name.startswith('.')
        and (d / 'base.apk').exists()][0]
rundir = RUNS / 'w8_queens_census'
shutil.rmtree(rundir, ignore_errors=True)
console = OUT / 'queens_slot_census.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--seconds', str(SECS), '--trace']
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=SECS + 240)
log = console.read_text(errors='ignore')

hits = re.findall(r'UNSUPPORTED (JNIEnv|JavaVM) slot (\d+) invoked', log)
census_line = re.search(r'UNSUPPORTED slot census: (.*)', log)
detail = {}
for kind, slot in hits:
    k = f'{kind}{slot}'
    detail[k] = detail.get(k, 0) + 1
res = dict(
    pkg=PKG, secs=SECS,
    per_hit_rows=len(hits),
    detail=detail,
    census_line=(census_line.group(1).strip() if census_line else None),
    natives=[l for l in log.splitlines() if 'RegisterNatives' in l][:4],
    flutter_load=[l for l in log.splitlines() if 'dlopen' in l.lower() and 'flutter' in l.lower()][:3],
    jni_onload=[l for l in log.splitlines() if 'JNI_OnLoad' in l][:3],
)
(OUT / 'QUEENS_SLOT_CENSUS.json').write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1)[:1800])
