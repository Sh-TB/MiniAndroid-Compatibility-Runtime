#!/usr/bin/env python3
"""S193 [C8] wave-10 live A/B (S188 rule 10): install + 30 s run of the four
wave-9 live titles on the CURRENT tree (base d3a8d0ec + waves 8+9 + wave 10),
extracting (api_rows / uncaught) per title — the same metric shape the S192
wave-9 A/B published (klondike 494/33, tower3d 9214/63, microtimer 1052/19,
tri-peaks 19/2)."""
import json, shutil, subprocess, sys
from pathlib import Path

BASE = Path('/home/z/my-project/work/miniandroid')
BIN = BASE / 'miniandroid/build/miniandroid'
APKS = Path('/home/z/my-project/upload/canonical_apks')
RUNS = BASE / 'evidence/s193_c8/ab_runs'
SECS = 30

TITLES = [
    ("eu.veldsoft.free.klondike", "klondike_veldsoft_3.apk"),
    ("stack.tower3d", "stack.tower3d_1.apk"),
    ("dubrowgn.microtimer", "dubrowgn.microtimer_8.apk"),
    ("eu.veldsoft.tri.peaks", "tripeaks_v1.2.1_vc4.apk"),
]

results = []
for pkg, apk in TITLES:
    store = RUNS / f'store_{pkg}'
    if store.exists():
        shutil.rmtree(store)
    store.mkdir(parents=True)
    apps = store / 'data' / 'app'
    subprocess.run([str(BIN), 'install', str(APKS / apk),
                    '--data-root', str(store)],
                   capture_output=True, timeout=300)
    dpkg = None
    if apps.exists():
        ds = [d.name for d in apps.iterdir()
              if d.is_dir() and not d.name.endswith('.staging')]
        dpkg = ds[0] if ds else None
    if not dpkg:
        results.append({"pkg": pkg, "status": "INSTALL_FAIL"})
        continue
    rundir = RUNS / f'run_{pkg}'
    console = RUNS / f'{pkg}.err'
    with open(console, 'w') as cf:
        subprocess.run([str(BIN), 'run', '--execution-mode', 'real-dalvik',
                        '--data-root', str(store), '-o', str(rundir),
                        '--max-seconds', str(SECS), '--frames', '5',
                        '--trace', '--package', dpkg],
                       stdout=cf, stderr=subprocess.STDOUT,
                       timeout=SECS + 240)
    text = console.read_text(errors='replace')
    uncaught = text.count('UNCAUGHT')
    api_rows = 0
    aj = rundir / 'api_calls.json'
    if aj.exists():
        try:
            data = json.loads(aj.read_text())
            api_rows = len(data) if isinstance(data, list) else len(
                data.get('calls', data.get('rows', [])))
        except Exception:
            api_rows = -1
    results.append({"pkg": pkg, "api_rows": api_rows,
                    "uncaught": uncaught})
    print(json.dumps(results[-1]))

out = RUNS / 'ab_summary.json'
out.write_text(json.dumps(results, indent=1))
print("A/B COMPLETE →", out)
