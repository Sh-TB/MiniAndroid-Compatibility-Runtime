#!/usr/bin/env python3
"""S188 W7: verify F-NEW-582 (two-arg nextInt(origin,bound) OpenJDK law)
on tibarj.tranquilstopwatch — the W6 residual ×3 f086-nextint-bound IAE.

Baseline (W6 evidence, ts_w6d): uncaught = 3, all f086-nextint-bound IAE
"(bound must be positive)" from Lu3/a;.c (ThreadLocalRandom bridge).
Expected post-law: IAE 0, uncaught 0 (or new honest frontier), W7-TLR rows
showing the real (origin, bound) pairs. Goldens must hold.
"""
import json, os, subprocess, hashlib, sys, re
from pathlib import Path
from PIL import Image
from collections import Counter

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w7'
RUNS = OUT / 'runs'
SECS = 40

TARGETS = [
    # (tag, apk, env)
    ('ts_w7c', BASE / 'upload/stuck_apks/tibarj.tranquilstopwatch.apk',
     {'MINIANDROID_W7_TRACE': '1'}),
    ('ts_w7d', BASE / 'upload/stuck_apks/tibarj.tranquilstopwatch.apk', {}),
]


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


def depth(path):
    im = Image.open(path).convert('RGB')
    im.thumbnail((540, 960))
    px = list(im.getdata())
    n = len(px)
    cc = Counter(px)
    uc = len(cc)
    bg = cc.most_common(1)[0]
    bg_share = bg[1] / n
    nonbg = 1 - bg_share
    p2 = im.load()
    gsum = gcnt = 0
    w, h = im.size
    for y in range(0, h - 1, 3):
        for x in range(0, w - 1, 3):
            a, b = p2[x, y], p2[x, y + 1]
            d = abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])
            gsum += d; gcnt += 1
    grad_share = (gsum / gcnt / 255) if gcnt else 0
    if nonbg >= 0.01 and uc >= 400 and grad_share >= 0.02: tier = 'A_RICH'
    elif nonbg >= 0.01 and uc >= 60: tier = 'B_STRUCTURED'
    elif uc <= 3 or nonbg < 0.01: tier = 'FLAT_TWO_TONE_OR_BLANK'
    else: tier = 'C_TEXT_ON_FLAT'
    return dict(unique_colors=uc, bg_share=round(bg_share, 4),
                nonbg_share=round(nonbg, 4), grad_share=round(grad_share, 4),
                tier=tier)


def run_one(tag, apk, extra_env):
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(extra_env)
    r = subprocess.run([str(BIN), 'install', str(apk),
                        '--data-root', str(store)],
                       capture_output=True, timeout=300, env=env)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in apps.iterdir()
              if d.is_dir() and not d.name.endswith('.staging')
              and not d.name.startswith('.')]
        dpkg = ds[0] if ds else None
    if not dpkg:
        return dict(tag=tag, status='INSTALL_FAIL',
                    install_tail=(r.stdout[-300:] + r.stderr[-300:]).decode('utf-8', 'ignore'))
    rundir = RUNS / tag
    console = OUT / f'{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--seconds', str(SECS), '--trace']
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=SECS + 240, env=env)
    log = console.read_text(errors='ignore')
    f086_bound = len(re.findall(r'f086-nextint-bound', log))
    f086_range = len(re.findall(r'f086-nextint-range', log))
    w7_rows = re.findall(r'\[W7-TLR\] nextInt\(origin=(-?\d+), bound=(-?\d+)\) caller=(\S+)', log)
    res_rows = re.findall(r'\[RES\] getInteger resid=0x([0-9a-f]+) -> (-?\d+)( \((?:UNRESOLVED)\))?', log)
    shot = rundir / 'screenshot.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    d = depth(shot) if shot and shot.exists() else dict(error='no screenshot')
    face = None
    if shot and shot.exists():
        face = OUT / f'face_{tag}.jpg'
        im = Image.open(shot).convert('RGB')
        im.thumbnail((360, 640))
        im.save(face, quality=70)
        if face.stat().st_size > 100_000:
            im2 = Image.open(shot).convert('RGB')
            im2.thumbnail((240, 426))
            im2.save(face, quality=55)
    # uncaught per F-016 honesty from the trace summary
    uncaught = None
    ts = rundir / 'trace_summary.json'
    if ts.exists():
        try:
            t = json.load(open(ts))
            ff = (t.get('first_failure_event') or {}).get('state', '')
            m = re.search(r'(\d+) uncaught in-flight', ff)
            uncaught = int(m.group(1)) if m else 0
            verdict = (t.get('first_failure_event') or {}).get('state', '')
        except Exception:
            verdict = 'trace_summary_unreadable'
    else:
        verdict = 'no trace_summary'
    return dict(tag=tag, status='OK', dpkg=dpkg,
                uncaught_inflight=uncaught, verdict=verdict[:220],
                f086_nextint_bound=f086_bound, f086_nextint_range=f086_range,
                w7_trace_rows=w7_rows[:12], w7_trace_count=len(w7_rows),
                getinteger_rows=res_rows[:10],
                screenshot=str(shot) if shot else None,
                face=face.name if face else None,
                **d)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or [t for t, _, _ in TARGETS]
    results = []
    for tag, apk, env in TARGETS:
        if tag not in only:
            continue
        print(f'== {tag}', flush=True)
        row = run_one(tag, apk, env)
        results.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != 'w7_trace_rows'},
                         indent=1)[:1200], flush=True)
        for tr in row.get('w7_trace_rows', [])[:12]:
            print('   W7-TLR', tr)
    Path(OUT / 'W7_RUNS.json').write_text(json.dumps(results, indent=1))
    print('written', OUT / 'W7_RUNS.json')


if __name__ == '__main__':
    main()
