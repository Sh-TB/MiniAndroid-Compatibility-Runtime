#!/usr/bin/env python3
"""W15 Coder-4 battery: 4APP track + frontier apps + golden anchors.
Protocol law (S186i): fresh store per title, real-dalvik, --frames 5 --trace,
face = sha16(screenshot.png), uncaught from console. Clean OUT dir per run
(store-temperature law from W13/W14).
Usage: w15_battery.py <tag> <binary> [names...]
"""
import json, os, subprocess, hashlib, sys, re, shutil
from pathlib import Path

BASE = Path('/home/z/my-project')
APKS = BASE / 'apk_cache'
OUTROOT = BASE / 'macr/evidence/w15'

COHORT = [
    # (name, apk file, pkg, max_seconds)
    ('tb',        'net.thunderbird.android_33.apk',        'net.thunderbird.android', 60),
    ('nc',        'com.nextcloud.client_350000290.apk',    'com.nextcloud.client', 60),
    ('tk',        'com.keylesspalace.tusky_145.apk',       'com.keylesspalace.tusky', 60),
    ('cb',        'org.connectbot_11101000.apk',           'org.connectbot', 40),
    ('itsfrz',    'com.itsfrz.tictactoe_5.apk',            'com.itsfrz.tictactoe', 60),
    ('pfdicer',   'org.secuso.privacyfriendlydicer_101.apk','org.secuso.privacyfriendlydicer', 60),
    ('sunpiano',  'code.alimiracle.sunpiano_2.apk',        'code.alimiracle.sunpiano', 60),
    ('bouncy',    'com.dozingcatsoftware.bouncy_43.apk',   'com.dozingcatsoftware.bouncy', 40),
    ('unote',     'app.varlorg.unote_3.apk',               'app.varlorg.unote', 40),
    ('dooz',      'io.github.yamin8000.dooz_12.apk',       'io.github.yamin8000.dooz', 120),
    ('opencalc',  'com.darkempire78.opencalculator_53.apk','com.darkempire78.opencalculator', 40),
    ('microtimer','dubrowgn.microtimer_9.apk',             'dubrowgn.microtimer', 40),
]


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


def run_one(binpath, name, apk, pkg, secs, outdir):
    store = outdir / f'store_{name}'
    rundir = outdir / name
    if store.exists():
        shutil.rmtree(store)          # fresh-store law
    if rundir.exists():
        shutil.rmtree(rundir)         # clean OUT law (store-temperature)
    store.mkdir(parents=True)
    r = subprocess.run([str(binpath), 'install', str(APKS / apk),
                        '--data-root', str(store)],
                       capture_output=True, timeout=600)
    ds = [d.name for d in (store / 'data' / 'app').iterdir()
          if d.is_dir() and not d.name.endswith('.staging')] \
        if (store / 'data' / 'app').exists() else []
    if not ds:
        return dict(name=name, error='INSTALL_FAIL')
    pkg_real = ds[0]
    console = outdir / f'{name}.err'
    cmd = [str(binpath), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--max-seconds', str(secs), '--frames', '5',
           '--trace', '--package', pkg_real]
    with open(console, 'w') as cf:
        try:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           timeout=secs + 180)
        except subprocess.TimeoutExpired:
            pass
    text = console.read_text(errors='replace')
    shot = rundir / 'screenshot.png'
    face = sha16(shot) if shot.exists() else None
    uncaught = len(re.findall(r'EXC-UNCAUGHT-TOP', text))
    verdict = None
    m = re.search(r'FRAME_ANALYSIS state=(\w+)', text)
    if m:
        verdict = m.group(1)
    px = None
    m = re.search(r'has (\d+) non-white pixels', text)
    if m:
        px = int(m.group(1))
    # first uncaught stack (top 5 frames)
    stacks = re.findall(r'EXC-UNCAUGHT-TOP.*?(?=\[TRACE\]|EXC-UNCAUGHT-TOP|$)',
                        text, re.S)
    first_stack = None
    if stacks:
        lines = [l.strip() for l in stacks[0].splitlines() if l.strip()][:6]
        first_stack = lines
    return dict(name=name, pkg=pkg_real, face=face, uncaught=uncaught,
                verdict=verdict, nonwhite_px=px,
                first_stack=first_stack, console=str(console))


def main():
    tag = sys.argv[1]
    binpath = Path(sys.argv[2])
    only = sys.argv[3:] if len(sys.argv) > 3 else None
    outdir = OUTROOT / tag
    outdir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, apk, pkg, secs in COHORT:
        if only and name not in only:
            continue
        print(f'=== {name} ({apk}) ===', flush=True)
        try:
            res = run_one(binpath, name, apk, pkg, secs, outdir)
        except Exception as e:
            res = dict(name=name, error=str(e))
        results[name] = res
        print(json.dumps({k: res.get(k) for k in
                          ('name', 'face', 'uncaught', 'verdict',
                           'nonwhite_px', 'error')}), flush=True)
    # face JPEG strip (<=100KB law)
    from PIL import Image
    for name, res in results.items():
        shot = outdir / name / 'screenshot.png'
        if shot.exists():
            try:
                im = Image.open(shot).convert('RGB')
                im.thumbnail((360, 640))
                im.save(outdir / f'W15_{tag}_{name}_face.jpg', 'JPEG', quality=65)
            except Exception:
                pass
    report = dict(tag=tag, binary=str(binpath),
                  binary_sha16=sha16(binpath), results=results)
    json.dump(report, open(outdir / 'BATTERY.json', 'w'), indent=1)
    print('saved', outdir / 'BATTERY.json')


if __name__ == '__main__':
    main()
