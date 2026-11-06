#!/usr/bin/env python3
"""S186i: full 41-title re-battery at CURRENT HEAD (post S186d/e/f/h laws:
File.toString, Object.equals+CHAR, ArrayDeque.descendingIterator, ARITY LAW).
User directive: real renders, not comments — "حداقل چند بازی و برنامه کامل اجرا بشه".
Fresh store per title, s182 invocation law, S183 tier classification,
per-title face JPG, resume-JSONL (2-core/3GB sandbox: run chunked foreground).
"""
import json, subprocess, hashlib, traceback, sys
from pathlib import Path
from PIL import Image
from collections import Counter

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s186_s107'
RUNS = OUT / 's186i_runs'
MAN = json.load(open(OUT / 'S186C_STUCK_APK_MANIFEST.json'))
SECS = 40


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


def run_one(res):
    issue, pkg = res['issue'], res['pkg']
    tag = pkg
    try:
        if res['status'] not in ('OK', 'CACHED'):
            return dict(issue=issue, pkg=pkg, status='NO_APK',
                        reason=res.get('reason', res.get('status')))
        apk = Path(res['path'])
        store = RUNS / f'store_{tag}'
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
        rundir = RUNS / tag
        console = RUNS / f'{tag}.err'
        cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
               '--data-root', str(store), '-o', str(rundir),
               '--max-seconds', str(SECS), '--frames', '5',
               '--trace', '--package', dpkg]
        with open(console, 'w') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           timeout=SECS + 150)
        text = console.read_text(errors='replace')
        shot = rundir / 'screenshot.png'
        r = dict(issue=issue, pkg=pkg, dpkg=dpkg, status='RAN', max_seconds=SECS)
        if shot.exists():
            r['face'] = sha16(shot)
            r.update(depth(shot))
            im = Image.open(shot).convert('RGB'); im.thumbnail((540, 960))
            im.save(OUT / f'S186I_{tag}_face.jpg', 'JPEG', quality=70)
        else:
            r['tier'] = 'NO_SHOT'
        r['uncaught_total'] = text.count('UNCAUGHT')
        first = ''
        for ln in text.splitlines():
            if 'UNCAUGHT' in ln:
                first = ln[:260]; break
        r['first_uncaught'] = first
        r['gdx_host'] = text.count('GDX-HOST')
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            if ln.strip() == 'Errors:' and i + 1 < len(lines):
                r['errors_metric'] = lines[i + 1].strip()
        return r
    except Exception as e:
        return dict(issue=issue, pkg=pkg, status='ERROR',
                    err=f'{type(e).__name__}: {e}'[:200],
                    tb=traceback.format_exc()[-400:])


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    partial = OUT / 'S186I_BATTERY.partial.jsonl'
    done = {}
    if partial.exists():
        for ln in partial.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                done[r['pkg']] = r
        print(f'resume: {len(done)} already completed')
    todo = [r for r in MAN['results'] if r['pkg'] not in done]
    if len(sys.argv) > 2:  # chunked-foreground: --start N --count M
        s, c = int(sys.argv[1]), int(sys.argv[2])
        todo = todo[s:s + c]
    results = list(done.values())
    for i, res in enumerate(todo):
        print(f'[{i+1}/{len(todo)}] {res["pkg"]} ...', flush=True)
        r = run_one(res)
        results.append(r)
        with open(partial, 'a') as f:
            f.write(json.dumps(r) + '\n')
        print(f"  -> {r.get('status')} uncaught={r.get('uncaught_total','-')} "
              f"tier={r.get('tier','-')} face={r.get('face','-')}", flush=True)
    # final JSON (only on full pass)
    if len(results) == len(MAN['results']):
        json.dump(dict(schema='s186i_battery/v1', engine='post-S186h HEAD',
                       n=len(results), results=results),
                  open(OUT / 'S186I_BATTERY.json', 'w'), indent=1)
        print('WROTE S186I_BATTERY.json')


if __name__ == '__main__':
    main()
