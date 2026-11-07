#!/usr/bin/env python3
"""S188-W10 ts dimension-chain run (F-NEW-595): tranquilstopwatch after the
measure-answer family default-ON flip. Collects the DEX-MEASURE answers,
the frame verdict tier and the draw-op census into
evidence/s188_w10/W10_TS_DIMENSION.json.

Usage: python3 scripts/s188_w10_ts_dimension.py [secs]
"""
import json, re, subprocess, sys, shutil
from pathlib import Path
from PIL import Image
from collections import Counter

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
PKG = 'tibarj.tranquilstopwatch'
STORE = BASE / f'evidence/s188_w2/runs/store_com.sidhant.queens'  # any store works; ts installs its own
STORE = BASE / f'evidence/s188_w10/store_{PKG}'
APK = BASE / 'upload/stuck_apks/tibarj.tranquilstopwatch.apk'
OUT = BASE / 'evidence/s188_w10'
RUNDIR = OUT / 'runs' / 'w10_ts'
LOG = OUT / 'w10_ts.console.log'


def depth(path):
    im = Image.open(path).convert('RGB')
    im.thumbnail((540, 960))
    px = list(im.getdata())
    n = len(px)
    cc = Counter(px)
    bg = cc.most_common(1)[0]
    nonbg = 1 - bg[1] / n
    uc = len(cc)
    tier = 'B_STRUCTURED' if (nonbg >= 0.01 and uc >= 60) else 'FLAT'
    return dict(unique_colors=uc, bg_share=round(bg[1] / n, 4),
                nonbg_share=round(nonbg, 4), tier=tier)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    STORE.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(STORE)],
                   capture_output=True, timeout=300)
    shutil.rmtree(RUNDIR, ignore_errors=True)
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(RUNDIR),
           '--package', PKG, '--seconds', str(SECS), '--trace']
    # F-NEW-595: the measure-answer family runs OPT-IN (MINIANDROID_MCM_LAW=1)
    # — the default-ON flip collapsed blackjack's B face (W10_BATTERY.json)
    # and was reverted battery-verified; this run evidences the law's gain.
    env = {'MINIANDROID_MCM_LAW': '1'}
    env.update({k: v for k, v in __import__('os').environ.items()
                if k.startswith('MINIANDROID_W10')})
    with open(LOG, 'wb') as cf:
        p = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT, env=env)
        try:
            p.wait(timeout=SECS + 60)
            status = f'exit={p.returncode}'
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            status = 'killed-timeout'
    text = LOG.read_text(errors='replace')

    def count(pat):
        return len(re.findall(pat, text))

    # measure answers: (class, result) pairs — the row carries the hex
    # spec annotations: "... spec_w=NNN (0x...) spec_h=NNN (0x...) -> WxH "
    measures = re.findall(
        r'\[DEX-MEASURE\] (\S+?);\.onMeasure spec_w=\S+ \(0x\S+\) '
        r'spec_h=\S+ \(0x\S+\) -> (\S+)', text)
    zerod = {}
    nonzero = {}
    for cls, res in measures:
        if res in ('0x0', '0x0 '):
            zerod[cls] = zerod.get(cls, 0) + 1
        else:
            nonzero.setdefault(cls, res)
    verdict = re.search(r'verdict=(\w+), first_missing_stage=(\w+)', text)
    shot = None
    for cand in [RUNDIR / 'screenshot.png', RUNDIR / 'final_frame.png']:
        if cand.exists():
            shot = cand
    if shot is None and RUNDIR.exists():
        cands = sorted(RUNDIR.glob('**/*.png'))
        shot = cands[-1] if cands else None
    result = {
        'wave': 'S188-W10 ts dimension chain (F-NEW-595 measure-answer family default-ON)',
        'secs': SECS,
        'status': status,
        'binary': '504c5288022b8660',
        'measure_zero_answers': zerod,
        'measure_nonzero_answers': nonzero,
        'verdict': verdict.group(1) if verdict else None,
        'first_missing_stage': verdict.group(2) if verdict else None,
        'app_draw_ops': count(r'app_draw_ops'),
        'uncaught': count(r'Uncaught|uncaught exception'),
        'route_violation': count(r'ROUTE_VIOLATION'),
        'screenshot': str(shot.relative_to(BASE)) if shot else None,
        'depth': depth(shot) if shot else None,
        'log': str(LOG.relative_to(BASE)),
    }
    (OUT / 'W10_TS_DIMENSION.json').write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main()
