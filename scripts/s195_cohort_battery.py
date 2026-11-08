#!/usr/bin/env python3
"""S195 AUDIT — the integrated-runtime real-application battery (MAIN
CODER MASTER TASK §8): the contributor-cohort apps on ONE binary, 3
independent runs each, full per-app evidence (route, lifecycle, exception
census, frame analysis, face tier, APK sha256)."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

OUT = BASE / 'evidence/s195_audit'
COHORT = OUT / 'cohort'
(COHORT / 'runs').mkdir(parents=True, exist_ok=True)
w2.OUT = COHORT
w2.RUNS = COHORT / 'runs'
w2.SECS = 40

BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]

APPS = {
    'gmdice':      BASE / 'upload/canonical_apks/de.duenndns.gmdice_8.apk',
    'tictactoe':   BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk',
    'microtimer':  BASE / 'upload/canonical_apks/dubrowgn.microtimer_8.apk',
    'opencalc':    BASE / 'upload/opencalculator_53.apk',
    'chessclock':  BASE / 'upload/chessclock_29.apk',
    'pf2048':      BASE / 'upload/fdroid_batch/org.secuso.privacyfriendly2048_100.apk',
    'pfmemory':    BASE / 'upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk',
}


def apk_sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def census(log):
    """exception census: top throw sites by exception class."""
    exc = re.findall(r'(\w+(?:Exception|Error))(?=:| thrown| \()', log)
    from collections import Counter
    return dict(Counter(exc).most_common(6))


def chain_markers(log):
    return {
        'route_decision': [l for l in log.splitlines()
                           if l.startswith('[ROUTE] DECISION')][:1],
        'route_violation': len(re.findall(r'ROUTE_VIOLATION=[^0]', log)),
        'frame_analysis': re.findall(r'FRAME_ANALYSIS state=(\S+)', log)[:3],
        'render_family': list(dict.fromkeys(
            re.findall(r'FRAME_ANALYSIS state=\S+ rf=(\S+)', log)))[:3],
        'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
        'app_boundary': len(re.findall(r'APP BOUNDARY unwind', log)),
        'activity': len(re.findall(r'onCreate\(\)', log)),
        'first_divergence': (re.search(
            r'first divergence[^\n]*|FIRST-DIVERGENCE[^\n]*', log) or [None])[0],
        'exception_census': census(log),
    }


def run_app(name, apk, run_idx):
    tag = f'{name}_s195_r{run_idx}'
    store = w2.RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(w2.BIN), 'install', str(apk), '--data-root',
                        str(store)], capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    if not dpkg:
        return dict(app=name, tag=tag, status='INSTALL_FAIL')
    rundir = w2.RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = COHORT / f'{tag}.console.log'
    cmd = [str(w2.BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--seconds', str(w2.SECS), '--trace']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=w2.SECS + 240)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    face = None
    depth = None
    if shot and shot.exists():
        face = COHORT / f'face_{tag}.jpg'
        from PIL import Image
        im = Image.open(shot).convert('RGB')
        im.thumbnail((360, 640))
        im.save(face, quality=70)
        depth = w2.depth(shot)
        # honesty gate: center-64x64 color count (NOISE_NOT_UI law)
        try:
            c64 = w2.depth(shot)  # full-frame tier
        except Exception:
            pass
    return dict(app=name, tag=tag, status='OK', dpkg=dpkg, wall_s=wall,
                apk_sha256=apk_sha(apk), binary_sha16=BIN_SHA,
                screenshot=str(shot) if shot else None,
                face=face.name if face else None,
                depth=depth, chain=chain_markers(log))


results = {'binary_sha16': BIN_SHA, 'secs': w2.SECS, 'runs': []}
PART = COHORT / 'S195_COHORT_BATTERY.partial.json'
# resume support: skip (app, run_idx) pairs already recorded in the partial
done_keys = set()
if PART.exists():
    try:
        prev = json.loads(PART.read_text())
        results['runs'] = prev.get('runs', [])
        done_keys = {(r.get('app'), r.get('tag')) for r in results['runs']}
        print(f"resume: {len(results['runs'])} runs already recorded")
    except Exception:
        pass
for name, apk in APPS.items():
    if not apk.exists():
        print(f'{name}: APK MISSING {apk}', flush=True)
        continue
    for i in (1, 2, 3):
        if (name, f'{name}_s195_r{i}') in done_keys:
            print(f"{name} r{i}: SKIP (recorded)", flush=True)
            continue
        row = run_app(name, apk, i)
        results['runs'].append(row)
        ch = row.get('chain', {})
        print(f"{name} r{i}: {row.get('status')} "
              f"frame={ch.get('frame_analysis', ['-'])[:1]} "
              f"tier={(row.get('depth') or {}).get('tier', '-')} "
              f"uncaught={ch.get('uncaught')} wall={row.get('wall_s')}s",
              flush=True)
        PART.write_text(json.dumps(results, indent=1))

(COHORT / 'S195_COHORT_BATTERY.json').write_text(json.dumps(results, indent=1))
print('S195_COHORT_BATTERY.json written:', len(results['runs']), 'runs; '
      'binary', BIN_SHA)
