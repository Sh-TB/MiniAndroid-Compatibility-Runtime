#!/usr/bin/env python3
"""S188 W2: FIRST RENDERS on the alley-law runtime.

User directive: test a few simple clock apps and very very simple games
(open-source preferred). Every run now starts with a ROUTE DECISION
(S188 route_law): the runtime knows which alley the app takes BEFORE
execution. Honest tiering per S183/S186i. UNOBSERVED != PASS.

Titles (all F-Droid open source):
  clocks : com.justdeax.composeStopwatch (COMPOSE), tibarj.tranquilstopwatch
           (VIEW), com.qwde.ccm (GODOT)
  games  : eu.quelltext.memory (HTML5-packaged), cos.premy.mines (WEBVIEW),
           eu.veldsoft.no.thanks (COMPOSE), com.sidhant.queens (WEBVIEW),
           com.simondalvai.ball2box (GODOT), xyz.deepdaikon.quinb (VIEW+media),
           org.secuso.privacyfriendlybattleship (VIEW),
           crypto.o0o0o0o0o.games.blackjack (HTML5-packaged)
"""
import json, subprocess, hashlib, sys, re
from pathlib import Path
from PIL import Image
from collections import Counter

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w2'
RUNS = OUT / 'runs'
SECS = 40
TITLES = [
    'com.justdeax.composeStopwatch', 'tibarj.tranquilstopwatch', 'com.qwde.ccm',
    'eu.quelltext.memory', 'cos.premy.mines', 'eu.veldsoft.no.thanks',
    'com.sidhant.queens', 'com.simondalvai.ball2box', 'xyz.deepdaikon.quinb',
    'org.secuso.privacyfriendlybattleship', 'crypto.o0o0o0o0o.games.blackjack',
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


def run_one(pkg, apk):
    tag = pkg
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                       capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in apps.iterdir()
              if d.is_dir() and not d.name.endswith('.staging')]
        dpkg = ds[0] if ds else None
    if not dpkg:
        return dict(pkg=pkg, status='INSTALL_FAIL',
                    install_tail=(r.stdout[-400:] + r.stderr[-400:]).decode('utf-8','ignore'))
    rundir = RUNS / tag
    console = OUT / f'{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--seconds', str(SECS), '--trace']
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=SECS + 240)
    log = console.read_text(errors='ignore')
    route_lines = [l for l in log.splitlines()
                   if l.startswith('[ROUTE') or 'ROUTE_VIOLATION' in l
                   or 'ROUTE_SURPRISE' in l]
    shot = rundir / 'final_frame.png'
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
    uncaught = len(re.findall(r'FATAL|Uncaught|uncaught exception', log))
    return dict(pkg=pkg, status='OK', dpkg=dpkg,
                screenshot=str(shot) if shot else None,
                face=str(face.name) if face else None,
                route_decision=[l for l in route_lines if 'DECISION' in l or 'NO_PROFILE' in l],
                route_violation=[l for l in route_lines if 'VIOLATION' in l],
                route_surprise=[l for l in route_lines if 'SURPRISE' in l],
                uncaught_marks=uncaught, **d)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    titles = TITLES
    if len(sys.argv) > 1:
        titles = sys.argv[1:]  # chunked runs: pass a subset of titles
    man = json.load(open(BASE / 'evidence/s186_s107/S186C_STUCK_APK_MANIFEST.json'))
    rows = man if isinstance(man, list) else man.get('results', [])
    paths = {r['pkg']: r['path'] for r in rows
             if r.get('status') in ('OK', 'CACHED') and r.get('path')}
    results = []
    for pkg in titles:
        apk = paths.get(pkg)
        if not apk or not Path(apk).exists():
            results.append(dict(pkg=pkg, status='NO_APK'))
            print(pkg, 'NO_APK'); continue
        try:
            res = run_one(pkg, apk)
        except subprocess.TimeoutExpired:
            res = dict(pkg=pkg, status='RUN_TIMEOUT')
        except Exception as e:
            res = dict(pkg=pkg, status='ERROR', error=repr(e)[:300])
        results.append(res)
        print(json.dumps({k: res.get(k) for k in
                          ('pkg', 'status', 'tier', 'unique_colors',
                           'nonbg_share', 'face')}))
    out_json = OUT / 'W2_FIRST_RENDERS.json'
    merged = {}
    if out_json.exists():
        for prev in json.load(open(out_json)):
            merged[prev['pkg']] = prev
    for res in results:
        merged[res['pkg']] = res
    allres = list(merged.values())
    base = json.load(open(BASE / 'evidence/s186_s107/S186I_BATTERY.json'))
    base_tiers = {r['pkg']: r['tier'] for r in base['results']}
    for res in results:
        res['s186i_tier'] = base_tiers.get(res['pkg'])
        if res.get('tier') and res['s186i_tier'] and res['tier'] != res['s186i_tier']:
            res['tier_change'] = f"{res['s186i_tier']} -> {res['tier']}"
    with open(OUT / 'W2_FIRST_RENDERS.json', 'w') as f:
        json.dump(allres, f, indent=1)
    print('\nsaved', OUT / 'W2_FIRST_RENDERS.json')


if __name__ == '__main__':
    main()
