#!/usr/bin/env python3
"""S200 gate — gmdice 5-tap interactive regression on the current binary.

Reproduces the standing proof (S188→S199: '5 taps → 5 distinct result
states, rerun identical') with the S121 tap schedule:
  (592,1845)@20 (332,1845)@36? no — @28, (116,1845)@36, (845,1845)@44,
  (592,1845)@52; 60 frames @250ms; fresh store per run.
Gate: every tap changes the dice region (5 state transitions), the five
post-tap regions are pairwise distinct, and a second fresh run reproduces
the identical region-hash sequence (deterministic-execution law).
"""
import hashlib, json, shutil, subprocess, sys, time
from pathlib import Path
from PIL import Image, ImageChops

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/canonical_apks/de.duenndns.gmdice_8.apk'
OUT = BASE / 'evidence/s200'
RUNS = OUT / 'runs'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
PKG = 'de.duenndns.gmdice'
TAPS = [(20, 592, 1845), (28, 332, 1845), (36, 116, 1845),
        (44, 845, 1845), (52, 592, 1845)]
DICE_BOX = (200, 1600, 880, 1800)  # result text area under 'Roll it!'
# (S200 calibration: taps hit 46/47/48/49 and frames change at
# y=1671-1752 — the result label; the top half of the screen stays empty
# in this headless build.)


def sha16b(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def one_run(tag):
    store = RUNS / f'store_{tag}'
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
                   capture_output=True, timeout=300)
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', PKG, '--frames', '60', '--frame-delay', '250',
           '--trace']
    for (fr, x, y) in TAPS:
        cmd += ['--tap', f'{x},{y}@{fr}']
    console = RUNS / f'{tag}.console.log'
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=300)
    log = console.read_text(errors='ignore')
    uncaught = len(__import__('re').findall(
        r'FATAL|uncaught exception|Uncaught exception', log))
    fr = rundir / 'frames'
    out = {'tag': tag, 'binary': BIN_SHA, 'uncaught': uncaught,
           'tap_hits': [], 'post_hashes': [], 'transitions': []}
    for i, (tfr, x, y) in enumerate(TAPS):
        pre = fr / f'frame_{tfr-1:03d}.png'
        post = fr / f'frame_{tfr:03d}.png'
        if not (pre.exists() and post.exists()):
            out['transitions'].append(None)
            continue
        a = Image.open(pre).convert('L').crop(DICE_BOX)
        b = Image.open(post).convert('L').crop(DICE_BOX)
        hist = ImageChops.difference(a, b).histogram()
        changed_px = sum(hist[30:])
        out['tap_hits'].append(changed_px)
        out['transitions'].append(changed_px > 200)
        out['post_hashes'].append(
            hashlib.sha256(b.tobytes()).hexdigest()[:16])
    return out


r1 = one_run('mtm_gate_gmdice_r1')
r2 = one_run('mtm_gate_gmdice_r2')
res = {
    'binary_sha16': BIN_SHA,
    'apk_sha16': sha16b(APK),
    'r1': r1, 'r2': r2,
    'five_transitions': all(r1['transitions']),
    'five_distinct': len(set(r1['post_hashes'])) == 5,
    'rerun_identical': r1['post_hashes'] == r2['post_hashes'],
}
res['verdict'] = ('PASS' if (res['five_transitions'] and res['five_distinct']
                             and res['rerun_identical']) else 'FAIL')
pf = OUT / 'S200_GMDICE_GATE.json'
existing = json.loads(pf.read_text()) if pf.exists() else {}
existing[f'gmdice_{BIN_SHA[:16]}'] = res
pf.write_text(json.dumps(existing, indent=1))
print(json.dumps(res, indent=1))
