#!/usr/bin/env python3
"""S188 first-renders wave: run zero-uncaught-but-FLAT titles under the S186i hybrid
binary, capture screenshot + console + route diagnostics, classify per S183/S188.
S185 law: run dirs (run_*) and *.err stay out of git; evidence = verdict JSONL + face JPG <=100KB.
"""
import json, subprocess, hashlib, traceback, sys, time
from pathlib import Path
from PIL import Image
from collections import Counter

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
OUT = BASE / 'evidence/s188/first_renders'
RUNS = OUT / 'runs'
MAN = json.load(open(BASE / 'evidence/s186_s107/S186C_STUCK_APK_MANIFEST.json'))['results']
SECS = 40
TARGETS = sys.argv[1:] or ['com.sidhant.queens', 'io.github.hathibelagal.mykanji',
                           'com.simondalvai.ball2box', 'foehnix.widget']


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
                nonbg_share=round(nonbg, 4), grad_share=round(grad_share, 4), tier=tier)


ROUTE_KEYS = ['VIEWTREE', 'ADAPTER', 'LISTVIEW', 'GDX-HOST', 'GLES', 'EGL', 'SDL',
              'INFLATE', 'BITMAP', 'WEBVIEW', 'SURFACE', 'DRAW', 'LAYOUT', 'COMPOSE',
              'FRAGMENT', 'Native library', 'dlopen']


def run_one(res):
    issue, pkg = res['issue'], res['pkg']
    try:
        apk = Path(res['path'])
        store = RUNS / f'run_store_{pkg}'
        store.mkdir(parents=True, exist_ok=True)
        apps = store / 'data' / 'app'
        subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                       capture_output=True, timeout=300)
        dpkg = None
        if apps.exists():
            ds = [d.name for d in apps.iterdir()
                  if d.is_dir() and not d.name.endswith('.staging')]
            dpkg = ds[0] if ds else None
        if not dpkg:
            return dict(issue=issue, pkg=pkg, status='INSTALL_FAIL')
        rundir = RUNS / f'run_{pkg}'
        console = RUNS / f'{pkg}.err'
        cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
               '--data-root', str(store), '-o', str(rundir),
               '--max-seconds', str(SECS), '--frames', '5',
               '--trace', '--package', dpkg]
        t0 = time.time()
        with open(console, 'w') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           timeout=SECS + 150)
        text = console.read_text(errors='replace')
        r = dict(issue=issue, pkg=pkg, dpkg=dpkg, status='RAN', max_seconds=SECS,
                 binary=BIN_SHA, runtime_s=round(time.time() - t0, 1))
        shot = rundir / 'screenshot.png'
        if shot.exists():
            r['face'] = sha16(shot)
            r.update(depth(shot))
            im = Image.open(shot).convert('RGB'); im.thumbnail((540, 960))
            im.save(OUT / f'S188_{pkg}_face.jpg', 'JPEG', quality=70)
        else:
            r['tier'] = 'NO_SHOT'
        r['uncaught_total'] = text.count('UNCAUGHT')
        first = ''
        for ln in text.splitlines():
            if 'UNCAUGHT' in ln:
                first = ln[:260]; break
        r['first_uncaught'] = first
        # route diagnostics: marker counts + first occurrence of each marker
        marks = {}
        lines = text.splitlines()
        for k in ROUTE_KEYS:
            hits = [i for i, ln in enumerate(lines) if k in ln]
            if hits:
                marks[k] = {'count': len(hits), 'first': lines[hits[0]][:160]}
        r['route_marks'] = marks
        # viewtree-ish summary lines
        vt = [ln[:200] for ln in lines if 'view' in ln.lower() and ('tree' in ln.lower()
              or 'attach' in ln.lower() or 'child' in ln.lower())][:8]
        if vt:
            r['view_lines'] = vt
        return r
    except Exception as e:
        return dict(issue=issue, pkg=pkg, status='ERROR',
                    err=f'{type(e).__name__}: {e}'[:200],
                    tb=traceback.format_exc()[-400:])


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    outj = OUT / 'S188_FIRST_RENDERS.jsonl'
    done = set()
    if outj.exists():
        for ln in outj.read_text().splitlines():
            if ln.strip():
                done.add(json.loads(ln)['pkg'])
    by_pkg = {r['pkg']: r for r in MAN}
    for pkg in TARGETS:
        if pkg in done:
            print(f'skip {pkg} (done)'); continue
        res = by_pkg.get(pkg)
        if not res:
            print(f'NO MANIFEST ROW for {pkg}'); continue
        print(f'=== running {pkg} (issue {res["issue"]}) ===', flush=True)
        r = run_one(res)
        with open(outj, 'a') as f:
            f.write(json.dumps(r) + '\n')
        print(json.dumps({k: r.get(k) for k in
            ('pkg', 'status', 'tier', 'unique_colors', 'nonbg_share', 'uncaught_total',
             'face', 'binary')}), flush=True)


if __name__ == '__main__':
    main()
