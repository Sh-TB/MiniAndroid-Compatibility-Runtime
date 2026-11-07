#!/usr/bin/env python3
"""S188 resume verify: confirm the three promotion milestones hold on the
freshly rebuilt binary (sandbox recycle wiped build/, make -j2 re-created it).

Milestones from W2/W2b evidence:
  com.sidhant.queens      — Flutter lane promotion: libflutter.so dlopen ok +
                            JNI_OnLoad 0x10004 + FlutterJNI natives registered
  eu.veldsoft.no.thanks   — W2b harness-truth fix: settled face = real main
                            menu (B_STRUCTURED, 563 colors at W2b)
  com.simondalvai.ball2box— Godot lane: GodotApp.onCreate chain clean,
                            0 uncaught
Goldens were already verified byte-exact (s188_golden_check.py).
"""
import json, subprocess, hashlib, re, shutil
from pathlib import Path
from PIL import Image
from collections import Counter

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w2'
RUNS = OUT / 'runs'
SECS = 35
TARGETS = ['com.sidhant.queens', 'eu.veldsoft.no.thanks',
           'com.simondalvai.ball2box']
APKS = BASE / 'upload/stuck_apks'


def depth(path):
    im = Image.open(path).convert('RGB')
    im.thumbnail((540, 960))
    px = list(im.getdata())
    n = len(px)
    cc = Counter(px)
    bg = cc.most_common(1)[0]
    bg_share = bg[1] / n
    nonbg = 1 - bg_share
    uc = len(cc)
    if nonbg >= 0.01 and uc >= 60:
        tier = 'B_STRUCTURED'
    else:
        tier = 'FLAT_TWO_TONE_OR_BLANK'
    return dict(unique_colors=uc, bg_share=round(bg_share, 4),
                nonbg_share=round(nonbg, 4), tier=tier)


results = {}
for pkg in TARGETS:
    apk = APKS / f'{pkg}.apk'
    store = RUNS / f'store_{pkg}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                       capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    if not dpkg:
        results[pkg] = dict(status='INSTALL_FAIL')
        continue
    rundir = RUNS / f'resume_{pkg}'
    shutil.rmtree(rundir, ignore_errors=True)
    console = OUT / f'resume_{pkg}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--seconds', str(SECS), '--trace']
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=SECS + 240)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    d = depth(shot) if shot and shot.exists() else dict(error='no screenshot')
    uncaught = len(re.findall(r'Uncaught|uncaught exception|FATAL', log))
    marks = {}
    if pkg == 'com.sidhant.queens':
        marks['dlopen_flutter_ok'] = bool(re.search(
            r'load flutter.*dlopen ok|dlopen.*libflutter.*ok', log, re.I)) or \
            ('JNI_OnLoad' in log and 'flutter' in log.lower())
        marks['jni_onload'] = bool(re.search(r'JNI_OnLoad.*0x10004', log))
        marks['natives'] = (re.search(
            r'RegisterNatives.*?(\d+)/(\d+)', log) or [None]) and \
            (re.findall(r'RegisterNatives[^\n]*', log)[:2])
    if pkg == 'com.simondalvai.ball2box':
        marks['godot_oncreate_clean'] = ('Godot' in log and uncaught == 0)
    results[pkg] = dict(status='OK', dpkg=dpkg, uncaught=uncaught,
                        route_lines=[l for l in log.splitlines()
                                     if l.startswith('[ROUTE] DECISION')][:1],
                        **marks, **d)
    print(json.dumps(results[pkg], ensure_ascii=False))

out = BASE / 'evidence/s188_w2/S188_RESUME_VERIFY.json'
out.write_text(json.dumps(results, indent=1))
print('written', out)
