#!/usr/bin/env python3
"""S225 #582 native-cohort census — 3 cold runs per cohort APK on ONE frozen
binary + ONE frozen corpus, first-divergence capture per run.

Per the #582 census comment (6821150791): three cold runs, fresh data root
per run, single causal trace, preserve the FIRST failure, no later stage
overwrites it. Output: evidence/s225/census.json + per-run console logs +
screenshots."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s225/census_runs'
OUT = BASE / 'evidence/s225/census.json'
RUNS.mkdir(parents=True, exist_ok=True)

COHORT = {
    # tag: (apk file, frames, taps-or-None)
    'gomoku':   ('com.traffar.gomoku_4.apk', 12, None),
    'rttt':     ('org.kirkezz.rttt_3.apk', 12, None),
    'freebloks': ('de.saschahlusiak.freebloks_184.apk', 12, None),
    'tower3d':  ('stack.tower3d_1.apk', 12, None),
    'bouncy':   ('com.dozingcatsoftware.bouncy_43.apk', 12, None),
    'ttt':      ('com.emmanuelmess.tictactoe_3.apk', 12, None),
}

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


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_cold(apk, tag):
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                   capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--frames', '12', '--frame-delay', '250']
    t0 = time.time()
    try:
        with open(console, 'wb') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           cwd=str(BASE), timeout=560)
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
    # first-divergence / frontier lines: keep the FIRST match of each pattern
    firsts = {}
    for pat in FRONTIER_PATTERNS:
        m = re.search(pat, log, re.IGNORECASE)
        if m:
            firsts.setdefault(pat.split('[')[0].strip('_- ')[:12] or pat[:10],
                              m.group(0)[:200])
    return {'rc': rc, 'wall_s': wall, 'pkg': dpkg,
            'face_sha16': sha16(shot) if shot else None,
            'png_bytes': png,
            'uncaught': len(re.findall(r'uncaught exception|UNCAUGHT', log)),
            'app_boundary': len(re.findall(r'APP[-_ ]BOUNDARY', log)),
            'in_flight': len(re.findall(r'in-flight exception', log)),
            'frontier_firsts': firsts}


def main():
    binary_sha16 = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
    out = {'binary_sha16': binary_sha16, 'protocol': 'real-dalvik, 12 frames, '
           'frame-delay 250, cold install per run, fresh store per run',
           'runs': {}}
    for tag, (apk, frames, taps) in COHORT.items():
        path = BASE / 'upload/canonical_apks' / apk
        runs = []
        for i in range(3):
            r = run_cold(path, f'{tag}_r{i}')
            r['apk_sha16'] = sha16(path)
            runs.append(r)
            print(f"{tag} r{i}: rc={r['rc']} face={r['face_sha16']} "
                  f"png={r['png_bytes']} uncaught={r['uncaught']} "
                  f"appb={r['app_boundary']} wall={r['wall_s']}s")
        out['runs'][tag] = {
            'apk': apk, 'apk_sha16': runs[0]['apk_sha16'],
            'identical': len({r['face_sha16'] for r in runs}) == 1,
            'runs': runs}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print('WROTE', OUT, 'binary', binary_sha16)


if __name__ == '__main__':
    main()
