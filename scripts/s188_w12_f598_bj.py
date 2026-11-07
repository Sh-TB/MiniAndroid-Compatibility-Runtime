#!/usr/bin/env python3
"""S188-W12 T8: blackjack F-NEW-598 MCM-input diag run."""
import json, os, re, subprocess, hashlib, shutil
from pathlib import Path
BASE = Path('/home/z/my-project')
BIN = BASE/'miniandroid/build/miniandroid'
OUT = BASE/'evidence/s188_w12'
def sha16(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()[:16]
bj = [p for p in (BASE/'upload/stuck_apks').glob('*.apk') if 'blackjack' in p.name.lower()][0]
STORE = BASE/f'evidence/s188_w2/runs/store_{bj.stem}'
subprocess.run([str(BIN),'install',str(bj),'--data-root',str(STORE)], capture_output=True, timeout=120)
dpkg = sorted(d.name for d in (STORE/'data'/'app').iterdir()
              if d.is_dir() and not d.name.startswith('.') and not d.name.endswith('.staging')
              and (d/'base.apk').exists())[0]
RUNDIR = OUT/'runs'/'w12_f598_bj'; shutil.rmtree(RUNDIR, ignore_errors=True)
LOG = OUT/'w12_f598_bj.console.log'
env = dict(os.environ); env['MINIANDROID_MCM_LAW']='1'; pass
cmd=[str(BIN),'run','--execution-mode','real-dalvik','--data-root',str(STORE),
     '-o',str(RUNDIR),'--package',dpkg,'--seconds','30','--trace']
with open(LOG,'wb') as cf:
    p=subprocess.Popen(cmd,stdout=cf,stderr=subprocess.STDOUT,env=env)
    try: p.wait(timeout=30); status=f'exit={p.returncode}'
    except subprocess.TimeoutExpired: p.kill(); p.wait(); status='killed-timeout'
text = LOG.read_text(errors='replace')
f598 = re.findall(r'\[F-NEW-598\].*', text)
out = {'status': status, 'binary': sha16(BIN), 'diag': f598[:32],
       'log': str(LOG.relative_to(BASE))}
json.dump(out, open(OUT/'W12_T8_F598_BJ_DIAG.json','w'), indent=1)
print(f'status={status} diag_lines={len(f598)}')
for l in f598[:20]: print(l[:190])
