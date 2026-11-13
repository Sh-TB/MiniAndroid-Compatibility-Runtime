#!/usr/bin/env python3
"""S231 — the #582 GP-census cold-run batch, EXECUTED (the S228 script was
written but never run; the route-matrix comment was promised on #582 but never
posted).

Mandate: #582 comment 6821150791 §3/§4 — one compact cohort per ROUTE, three
cold runs per APK on ONE frozen binary + fresh data-root per run, first-
divergence capture, per-route status matrix.

Law compliance (S213/S214 default-deny):
  - run outputs -> .cache/s228_cold_runs/ (gitignored, untracked)
  - only the compact summary JSON is promoted into evidence/s228_census/
    (wave_evidence_registered prefix excludes it from the frozen snapshot)

Cohort (route diversity per mandate §3 — not 10 copies of libGDX):
  dooz      io.github.yamin8000.dooz_23   JNI-libs / Compose (smallest DYNAMIC lib)
  gomoku    com.traffar.gomoku_4          SDL2 route (libmain + SDL2, x86)
  rttt      org.kirkezz.rttt_3            SDL3 route (SDLActivity + RmlUi)
  ttt       com.emmanuelmess.tictactoe_3  libGDX route (libgdx + freetype + box2d)
  freebloks de.saschahlusiak.freebloks_184 JNI AI (libserver) + GL (libktx)
  tower3d   stack.tower3d_1               libGDX extra
  bouncy    com.dozingcatsoftware.bouncy  libGDX (standing golden pin)
  gmdice    de.duenndns.gmdice_8          PURE-DEX Canvas control (input transition)
"""
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BIN = BASE / 'miniandroid/build/miniandroid'
CACHE = BASE / '.cache/s228_cold_runs'
RUNS = CACHE / 'runs'
PROMOTE = BASE / 'evidence/s228_census'
RUNS.mkdir(parents=True, exist_ok=True)
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]

COHORT = [
    ('dooz',      'io.github.yamin8000.dooz_23.apk',  [(875, 1823, 6)], 12, 250),
    ('gomoku',    'com.traffar.gomoku_4.apk',         None,             12, 250),
    ('rttt',      'org.kirkezz.rttt_3.apk',           None,             12, 250),
    ('ttt',       'com.emmanuelmess.tictactoe_3.apk', [(539, 1040, 6)], 40, 250),
    ('freebloks', 'de.saschahlusiak.freebloks_184.apk', None,           12, 250),
    ('tower3d',   'stack.tower3d_1.apk',              None,             12, 250),
    ('bouncy',    'com.dozingcatsoftware.bouncy_43.apk', None,          12, 250),
    ('gmdice',    'de.duenndns.gmdice_8.apk',         [(576, 1836, 6)], 16, 250),
]

FRONTIER_PATTERNS = [
    ('UNCAUGHT',     r'(UNCAUGHT|uncaught exception)[^\n]*'),
    ('FIRST_DIVERGENCE', r'(first[-_ ]?divergence|FIRST-DIVERGENCE)[^\n]*'),
    ('APP_BOUNDARY', r'APP[-_ ]BOUNDARY[^\n]*'),
    ('ABI',          r'ABI[_ A-Z]+[^\n]*'),
    ('ELF',          r'\bELF[0-9]*[^\n]*'),
    ('ROUTE',        r'\bROUTE[^\n]*'),
    ('JNI_OnLoad',   r'JNI_OnLoad[^\n]*'),
    ('SURFACE',      r'SURFACE_[A-Z_]+[^\n]*'),
    ('GL',           r'\bGL_[A-Z_]+[^\n]*'),
    ('FATAL',        r'(FATAL|SIGSEGV|SIGABRT|abort)[^\n]*'),
]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


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
    for (x, y, fr) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    t0 = time.time()
    rc = 0
    try:
        with open(console, 'wb') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           cwd=str(BASE), timeout=900)
    except subprocess.TimeoutExpired:
        rc = 124
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'screenshot.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    png = shot.stat().st_size if shot and shot.exists() else 0
    verdict = ('OK' if png and png <= 800_000 else
               'NOISE-SUSPECT >800KB' if png > 1_048_576 else
               'NOISE >1MiB' if png else 'NO-SHOT')
    firsts = {}
    for tag, pat in FRONTIER_PATTERNS:
        m = re.search(pat, log, re.IGNORECASE)
        if m:
            firsts[tag] = m.group(0)[:220]
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
           'png_bytes': png, 'screenshot_verdict': verdict,
           'report': rep, 'firsts': firsts}
    print(json.dumps(rec), flush=True)
    return rec


def main():
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if not BIN.exists():
        raise SystemExit('binary missing — build first')
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True,
                          text=True, cwd=str(BASE)).stdout.strip()
    path = PROMOTE / 's231_cold_runs_batch.json'
    results = json.loads(path.read_text()) if path.exists() else {
        'binary_sha16': BIN_SHA, 'main_head': head,
        'mandate': '#582 comment 6821150791 §3/§4 (cold-run census)',
        'routing': '.cache/s228_cold_runs (untracked); compact JSON promoted only',
        'cohort': {}}
    results['binary_sha16'] = BIN_SHA
    results['main_head'] = head
    for name, apkname, taps, frames, delay in COHORT:
        if only and name != only:
            continue
        if name in results['cohort'] and len(results['cohort'][name]['runs']) >= 3:
            continue
        apks = list((BASE / 'upload/canonical_apks').glob(apkname))
        if not apks:
            apks = [BASE / 'upload' / apkname]
        apk = apks[0]
        rr = results['cohort'][name]['runs'] if name in results['cohort'] else []
        start_k = len(rr) + 1
        for k in range(start_k, 4):
            rr.append(one_run(name, apk, k, taps, frames, delay))
            # persist after EVERY run (the 600s tool cap can kill the
            # process between runs; per-run durability keeps the census)
            results['cohort'][name] = {
                'apk': apk.name,
                'apk_sha16': sha16(apk),
                'runs': rr,
                'face_stable_x3': len({r['face_sha16'] for r in rr}) == 1,
                'distinct_faces': len({r['face_sha16'] for r in rr}),
                'majority_face': rr[0]['face_sha16'],
            }
            path.write_text(json.dumps(results, indent=1))
        print(f"== {name}: {len(rr)} runs, stable={results['cohort'][name]['face_stable_x3']}",
              flush=True)
    print('S231 BATCH DONE', flush=True)


if __name__ == '__main__':
    main()
