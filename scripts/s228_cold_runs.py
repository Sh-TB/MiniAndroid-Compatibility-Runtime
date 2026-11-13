#!/usr/bin/env python3
"""S228 — cold-run discriminating experiments for the #582 GP census mandate
(comment 6821150791 §4): three cold runs per cohort APK on ONE frozen binary,
fresh data-root per run, first-divergence capture, per-route status matrix.

Cohort (route diversity per mandate §3):
  io.github.yamin8000.dooz_23   — JNI-libs / Compose (smallest DYNAMIC lib)
  com.traffar.gomoku_4          — SDL2 route (libmain + SDL2, x86)
  org.kirkezz.rttt_3            — SDL3 route (SDLActivity + RmlUi)
  com.emmanuelmess.tictactoe_3  — libGDX route (libgdx + freetype + box2d)
  de.saschahlusiak.freebloks_184— JNI AI (libserver) + GL (libktx)
  de.duenndns.gmdice_8          — pure-DEX Canvas control (state transition)
  stack.tower3d_1               — libGDX extra (single probe)
"""
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s228_census/runs'
RUNS.mkdir(parents=True, exist_ok=True)
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]

COHORT = [
    ('dooz',      'io.github.yamin8000.dooz_23.apk',  3, None, 12, 250),
    ('gomoku',    'com.traffar.gomoku_4.apk',         3, None, 12, 250),
    ('rttt',      'org.kirkezz.rttt_3.apk',           3, None, 12, 250),
    ('ttt',       'com.emmanuelmess.tictactoe_3.apk', 3, None, 12, 250),
    ('freebloks', 'de.saschahlusiak.freebloks_184.apk', 3, None, 12, 250),
    ('tower3d',   'stack.tower3d_1.apk',              3, None, 12, 250),
    ('bouncy',    'com.dozingcatsoftware.bouncy_43.apk', 3, None, 12, 250),
    ('gmdice',    'de.duenndns.gmdice_8.apk',         3, None, 12, 250),
]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


FRONTIER_PATTERNS = [
    r'first[-_ ]?divergence[^\n]*',
    r'APP[-_ ]BOUNDARY[^\n]*',
    r'\[FRONTIER\][^\n]*',
    r'UNCAUGHT[^\n]*',
    r'uncaught exception[^\n]*',
    r'ABI[_ A-Z]*[^\n]*',
    r'ELF[0-9]*[^\n]*',
    r'ROUTE[^\n]*',
    r'NativeLoader[^\n]*',
    r'JNI_OnLoad[^\n]*',
    r'GL_[A-Z_]+[^\n]*',
    r'SURFACE_[A-Z_]+[^\n]*',
]


def one_run(name, apk, k, taps, frames, delay):
    store = RUNS / f'store_{name}_{k}'
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir(parents=True)
    inst = subprocess.run([str(BIN), 'install', str(apk),
                           '--data-root', str(store)],
                          capture_output=True, text=True, timeout=300)
    appdir = store / 'data' / 'app'
    dpkg = None
    if appdir.exists():
        ds = sorted(d.name for d in appdir.iterdir()
                    if d.is_dir() and not d.name.startswith('.')
                    and not d.name.endswith('.staging')
                    and (d / 'base.apk').exists())
        dpkg = ds[0] if ds else None
    rundir = RUNS / f'{name}_{k}'
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{name}_{k}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg or '', '--frames', str(frames),
           '--frame-delay', str(delay)]
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    t0 = time.time()
    try:
        with open(console, 'wb') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           cwd=str(BASE), timeout=900)
        rc = 0
    except subprocess.TimeoutExpired:
        rc = 124
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'screenshot.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    png = shot.stat().st_size if shot and shot.exists() else 0
    firsts = {}
    for pat in FRONTIER_PATTERNS:
        m = re.search(pat, log, re.IGNORECASE)
        if m:
            firsts.setdefault(pat.split('[')[0].strip('_- ')[:12] or pat[:10],
                              m.group(0)[:200])
    rep = {}
    rmd = rundir / 'report.md'
    if rmd.exists():
        txt = rmd.read_text(errors='replace')
        m = re.search(r'\*\*Status:\*\* \*\*(\w+)\*\*', txt)
        if m:
            rep['status'] = m.group(1)
    rec = {'run': f'{name}_{k}', 'install_rc': inst.returncode,
           'package': dpkg, 'rc': rc, 'wall_s': wall,
           'face_sha16': sha16(shot) if shot else None,
           'png_bytes': png, 'report': rep, 'frontier_firsts': firsts}
    print(json.dumps(rec), flush=True)
    return rec


def main():
    if not BIN.exists():
        raise SystemExit('binary missing — build first')
    results = {'binary_sha16': BIN_SHA,
               'mandate': '#582 comment 6821150791 §4',
               'cohort': {}}
    for name, apkname, runs, taps, frames, delay in COHORT:
        apks = list((BASE / 'upload/canonical_apks').glob(apkname))
        if not apks:
            apks = [BASE / 'upload' / apkname]
        apk = apks[0]
        rr = []
        for k in range(1, runs + 1):
            rr.append(one_run(name, apk, k, taps, frames, delay))
        results['cohort'][name] = {
            'apk': apk.name,
            'apk_sha16': sha16(apk),
            'runs': rr,
            'face_stable': len({r['face_sha16'] for r in rr}) == 1,
        }
        results['cohort'][name]['majority_face'] = rr[0]['face_sha16']
        (RUNS.parent / 's228_batch.json').write_text(json.dumps(results, indent=1))
        print(f"== {name}: {len(rr)} runs, stable={results['cohort'][name]['face_stable']}",
              flush=True)
    (RUNS.parent / 's228_batch.json').write_text(json.dumps(results, indent=1))
    print('S228 BATCH DONE', flush=True)


if __name__ == '__main__':
    main()
