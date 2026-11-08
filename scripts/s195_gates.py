#!/usr/bin/env python3
"""S195 AUDIT — regression gates on the S195-integration binary
31be843614e67bab (W18 line + C3 S197 + S198a + S198b ports): goldens x3
+ floor 11 + p9/halma spot (the LIBGDX EGL family must not regress)."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

OUT = BASE / 'evidence/s195_audit/gates'
(OUT / 'runs').mkdir(parents=True, exist_ok=True)
w2.OUT = OUT
w2.RUNS = OUT / 'runs'
w2.SECS = 40

BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
print('binary:', BIN_SHA, flush=True)

GOLDEN_PINS = {
    'com.dozingcatsoftware.bouncy': '8a6c24ac',
    'app.varlorg.unote': '3b8dcb0a',
    'io.github.yamin8000.dooz': '31ddd4d5',
}
APKS = {
    'com.dozingcatsoftware.bouncy': BASE / 'upload/canonical_apks/bouncy.apk',
    'app.varlorg.unote': BASE / 'upload/canonical_apks/app.varlorg.unote_30.apk',
    'io.github.yamin8000.dooz': BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk',
    'se.tube42.p9.android': BASE / 'upload/stuck_apks/se.tube42.p9.android.apk',
    'app.halma': BASE / 'upload/stuck_apks/app.halma.apk',
}


def run_tag(apk, tag):
    store = w2.RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(w2.BIN), 'install', str(apk), '--data-root',
                        str(store)], capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith('.')
          and not d.name.endswith('.staging') and (d / 'base.apk').exists()]
    if not ds:
        return dict(tag=tag, status='INSTALL_FAIL')
    rundir = w2.RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = OUT / f'{tag}.console.log'
    cmd = [str(w2.BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', ds[0], '--seconds', str(w2.SECS), '--trace']
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=w2.SECS + 240)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        c = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = c[-1] if c else None
    face = None
    if shot and shot.exists():
        from PIL import Image
        face = hashlib.sha256(Image.open(shot).convert('RGB').tobytes()).hexdigest()[:16]
    return dict(tag=tag, pkg=ds[0], status='OK', face_sha16=face,
                frame_analysis=re.findall(r'FRAME_ANALYSIS state=(\S+)', log)[:2],
                uncaught=len(re.findall(r'FATAL|uncaught exception', log)),
                route_violation=len(re.findall(r'ROUTE_VIOLATION=[^0]', log)))


results = {'binary_sha16': BIN_SHA, 'goldens': [], 'spots': []}
# goldens x3 (face pin byte-exact law)
for pkg, pin in GOLDEN_PINS.items():
    for i in (1, 2, 3):
        row = run_tag(APKS[pkg], f'g_{pkg.split(".")[-1]}_r{i}')
        row['pin'] = pin
        row['pin_holds'] = bool(row.get('face_sha16', '').startswith(pin))
        results['goldens'].append(row)
        print(f"GOLDEN {pkg} r{i}: face={row.get('face_sha16')} "
              f"pin_holds={row['pin_holds']} uncaught={row.get('uncaught')}",
              flush=True)

# p9/halma spot x1 each (EGL family no-regression)
for pkg in ('se.tube42.p9.android', 'app.halma'):
    row = run_tag(APKS[pkg], f'spot_{pkg.split(".")[-1]}')
    results['spots'].append(row)
    print(f"SPOT {pkg}: frame={row.get('frame_analysis')} "
          f"uncaught={row.get('uncaught')}", flush=True)

(OUT / 'S195_GATES.json').write_text(json.dumps(results, indent=1))
holds = [r for r in results['goldens'] if r['pin_holds']]
print(f"GATES: goldens {len(holds)}/9 pin-holds; spots "
      f"{[(r['pkg'], r.get('frame_analysis')) for r in results['spots']]}")
