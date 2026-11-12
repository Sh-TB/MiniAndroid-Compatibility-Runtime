#!/usr/bin/env python3
"""S224: #585 immediate-batch item 2 — reproduce the EXEC-candidate apps (#19 FishRings,
#20 TriPeaks, #23 OPMT) on the current binary; Stage A (cold run) + Stage B (first divergence)."""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s224/runs'
RUNS.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ('fishrings', BASE / 'upload/canonical_apks/fishrings_v1.23_vc6.apk', '12'),
    ('tripeaks', BASE / 'upload/canonical_apks/tripeaks_v1.2.1_vc4.apk', '12'),
    ('opmt', BASE / 'upload/canonical_apks/opmt_v0.1.2_vc1.apk', '12'),
]

def classify_frame(png):
    from PIL import Image
    im = Image.open(png).convert('RGB')
    cols = im.getcolors(10000000)
    cols.sort(reverse=True)
    total = sum(c for c, _ in cols)
    top_share = cols[0][0] / total if total else 1.0
    return {'distinct': len(cols), 'top_rgb': cols[0][1], 'top_share': round(top_share, 4),
            'top2': cols[1][1] if len(cols) > 1 else None}

results = {}
for tag, apk, frames in TARGETS:
    if not apk.exists():
        results[tag] = {'verdict': 'APK_MISSING'}
        continue
    store = RUNS / f'store_{tag}'
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir(parents=True)
    r = subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                       capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    for d in sorted(apps.iterdir()):
        if d.is_dir() and not d.name.startswith('.') and not d.name.endswith('.staging') \
                and (d / 'base.apk').exists():
            dpkg = d.name
    if not dpkg:
        results[tag] = {'verdict': 'INSTALL_FAILED'}
        continue
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{tag}.console.log'
    t0 = time.time()
    try:
        with open(console, 'wb') as cf:
            subprocess.run([str(BIN), 'run', '--execution-mode', 'real-dalvik',
                            '--data-root', str(store), '-o', str(rundir),
                            '--package', dpkg, '--frames', frames, '--frame-delay', '250'],
                           stdout=cf, stderr=subprocess.STDOUT, cwd=str(BASE), timeout=420)
        wall = round(time.time() - t0, 1)
    except subprocess.TimeoutExpired:
        wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'screenshot.png'
    face = hashlib.sha256(shot.read_bytes()).hexdigest()[:16] if shot.exists() else 'NO_SHOT'
    ft = classify_frame(shot) if shot.exists() else {}
    # Stage B: first divergence markers
    marks = {}
    for name, pat in [
        ('app_boundary', r'APP.?BOUNDARY|uncaught at caller'),
        ('uncaught', r'uncaught exception|FATAL'),
        ('missing_api', r'MISSING.*api|api.*MISSING|STUBBED'),
        ('first_exception', r'SYNTH-EXC|THROWABLE-MSG'),
        ('lifecycle', r'onCreate|onResume|onStart'),
        ('draw_ops', r'F-NEW-297|app_draw_ops'),
    ]:
        marks[name] = len(re.findall(pat, log))
    # the first exception line verbatim (first divergence seed)
    m = re.search(r'\[SYNTH-EXC\][^\n]*|\[THROWABLE-MSG\][^\n]*', log)
    first_exc = m.group(0)[:160] if m else None
    st = 'UNKNOWN'
    sm = re.search(r'Status: ([A-Z ]+)', log)
    if sm: st = sm.group(1).strip()
    results[tag] = {'wall_s': wall, 'face_sha16': face, 'frame_truth': ft,
                    'status': st, 'marks': marks, 'first_exception': first_exc}
    print(tag, json.dumps(results[tag], default=str)[:240])

json.dump(results, open(RUNS / 's224_exec_batch.json', 'w'), indent=1, default=str)
print("saved s224_exec_batch.json")
