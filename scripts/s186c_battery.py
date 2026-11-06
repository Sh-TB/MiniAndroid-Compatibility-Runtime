#!/usr/bin/env python3
"""S186c: stuck-titles re-battery on the CURRENT engine (user directive:
"همشون رو اجرا بکن" — run them all). For every REAL-STUCK title (S186 census):
fresh store install → discover pkg → s182 invocation law (real-dalvik
--data-root -o --max-seconds 40 --frames 5 --trace --package).
Classify each face with the S183 tier definitions. Record uncaught exceptions
and first-exception family for the completion matrix. All JSON verdicts stay
in git; run dirs stay out (S186 evidence law).
"""
import json, subprocess, hashlib, traceback, sys, os
from pathlib import Path
from PIL import Image
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s186_s107'
RUNS = OUT / 'reruns_battery'
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
        dpkg = None
        if apps.exists():  # store reuse: same APK bytes → same install result
            ds = [d.name for d in apps.iterdir()
                  if d.is_dir() and not d.name.endswith('.staging')]
            dpkg = ds[0] if ds else None
        install_reused = dpkg is not None
        if not dpkg:
            subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                           capture_output=True, timeout=300)
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
        r = dict(issue=issue, pkg=pkg, dpkg=dpkg, status='RAN',
                 install_reused=install_reused, max_seconds=SECS)
        if shot.exists():
            r['face'] = sha16(shot)
            r.update(depth(shot))
            im = Image.open(shot).convert('RGB'); im.thumbnail((540, 960))
            im.save(OUT / f'S186C_{tag}_face.jpg', 'JPEG', quality=70)
        else:
            r['tier'] = 'NO_SHOT'
        r['uncaught_total'] = text.count('UNCAUGHT')
        # first uncaught exception line (family signature)
        first = ''
        for ln in text.splitlines():
            if 'UNCAUGHT' in ln:
                first = ln[:260]; break
        r['first_uncaught'] = first
        r['gdx_host'] = text.count('GDX-HOST')
        r['errors_metric'] = ''
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
    # resume support: per-run results appended to a partial JSONL; on restart
    # already-completed titles are skipped (2 concurrent engine processes OOM-
    # killed the 3 GB sandbox once — resume makes any death cheap).
    partial = OUT / 'S186C_STUCK_BATTERY.partial.jsonl'
    done = {}
    if partial.exists():
        for ln in partial.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                done[r['pkg']] = r
        print(f'resume: {len(done)} already completed')
    todo = [r for r in MAN['results'] if r['pkg'] not in done]
    # chunked-foreground mode: --start N --count M (sandbox reaps detached
    # processes between tool calls; chunks keep each Bash call under its cap)
    if '--start' in sys.argv:
        i = sys.argv.index('--start'); start = int(sys.argv[i + 1])
        cnt = int(sys.argv[sys.argv.index('--count') + 1]) if '--count' in sys.argv else 4
        todo = todo[start:start + cnt]
        print(f'chunk: start={start} count={cnt} -> {len(todo)} titles')
    results = []
    with partial.open('a') as pf:
        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = {ex.submit(run_one, r): r for r in todo}
            for fut in list(futures):
                pass  # keep dict ordered; iterate as completed below
            from concurrent.futures import as_completed
            for fut in as_completed(futures):
                r = fut.result()
                pf.write(json.dumps(r) + '\n'); pf.flush()
                print(f"[{r.get('status','?'):>7}] #{r['issue']} {r['pkg'][:40]:40s} "
                      f"face={str(r.get('face',''))[:16]} tier={r.get('tier','')} "
                      f"uncaught={r.get('uncaught_total','')}", flush=True)
                results.append(r)
    results += [done[p] for p in done if p not in {r['pkg'] for r in results}]
    tiers = Counter(r.get('tier') for r in results)
    man = dict(schema='s186c_stuck_battery/v1', engine='post-S186b (GATE-A box2d verified)',
               n=len(results), tiers=dict(tiers), results=results)
    (OUT / 'S186C_STUCK_BATTERY.json').write_text(json.dumps(man, indent=1))
    print('\nTIERS:', dict(tiers))
    print(f'-> {OUT}/S186C_STUCK_BATTERY.json')


if __name__ == '__main__':
    main()
