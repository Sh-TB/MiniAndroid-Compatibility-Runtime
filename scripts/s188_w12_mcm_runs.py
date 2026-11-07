#!/usr/bin/env python3
"""S188-W12 T9: F-NEW-595 default-ON candidate re-trial on the W12 binary
(F-NEW-596 fixed the arena UAF that tainted every W10 run). ts + blackjack.
"""
import json, os, re, subprocess, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s188_w12'

def sha16(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()[:16]

def run(apk, pkg, secs, logname, rundir):
    STORE = BASE / f'evidence/s188_w2/runs/store_{pkg}'
    if not STORE.exists():
        STORE = BASE / f'evidence/s188_w2/runs/store_com.simondalvai.ball2box'  # never used
    subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(STORE)],
                   capture_output=True, timeout=120)
    apps = STORE / 'data' / 'app'
    dpkg = sorted(d.name for d in apps.iterdir()
                  if d.is_dir() and not d.name.startswith('.')
                  and not d.name.endswith('.staging') and (d/'base.apk').exists())[0]
    RUNDIR = OUT / 'runs' / rundir
    import shutil
    shutil.rmtree(RUNDIR, ignore_errors=True)
    LOG = OUT / logname
    env = dict(os.environ)
    env['MINIANDROID_MCM_LAW'] = '1'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik', '--data-root', str(STORE),
           '-o', str(RUNDIR), '--package', dpkg, '--seconds', str(secs), '--trace']
    with open(LOG, 'wb') as cf:
        p = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT, env=env)
        try:
            p.wait(timeout=secs)
            status = f'exit={p.returncode}'
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); status = 'killed-timeout'
    text = LOG.read_text(errors='replace')
    return text, status, LOG

def face_stats(text):
    return {
        'f595_resolve': re.findall(r'\[F-NEW-595\] resolve .*', text)[:12],
        'uncaught': len(re.findall(r'uncaught', text, re.I)),
        'frames': (re.search(r'Frames Rendered: (\d+)', text) or [None, '0'])[1] if re.search(r'Frames Rendered: (\d+)', text) else '0',
        'exactly0_content': len(re.findall(r'EXACTLY\(0\)', text)),
        'dex_measure': len(re.findall(r'\[DEX-MEASURE\]', text)),
    }

results = {}
# ts: 40s
ts_apk = BASE / 'upload/stuck_apks/tibarj.tranquilstopwatch.apk'
text, status, log = run(ts_apk, 'tibarj.tranquilstopwatch', 40, 'w12_ts_mcm.console.log', 'w12_ts_mcm')
results['ts'] = {'status': status, **face_stats(text)}
results['ts']['log'] = str(log.relative_to(BASE))

# blackjack: 30s
bj_apk = None
for cand in (BASE / 'upload/stuck_apks').glob('*.apk'):
    if 'blackjack' in cand.name.lower():
        bj_apk = cand
        break
if bj_apk:
    bj_pkg = bj_apk.stem
    text2, status2, log2 = run(bj_apk, bj_pkg, 30, 'w12_bj_mcm.console.log', 'w12_bj_mcm')
    results['blackjack'] = {'status': status2, **face_stats(text2)}
    results['blackjack']['log'] = str(log2.relative_to(BASE))

results['binary_sha16'] = sha16(BIN)
json.dump(results, open(OUT/'W12_T9_MCM_RETRIAL.json','w'), indent=1)
print(json.dumps(results, indent=1))
