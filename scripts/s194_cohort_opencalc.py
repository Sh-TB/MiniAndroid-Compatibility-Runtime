#!/usr/bin/env python3
"""S194: opencalc cohort-pin reproduction on the integrated binary.
S192/S193-KT pin: face sha16 = 479382e194be3803 (REAL_APP_CONTENT)."""
import hashlib, json, re, subprocess, shutil
from pathlib import Path
BASE = Path('/home/z/my-project')
BIN = BASE/'miniandroid/build/miniandroid'
OUT = BASE/'evidence/s194_intake'
def sha16(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()[:16]
apk = BASE/'upload/opencalculator_53.apk'
STORE = OUT/'store_opencalc'
RUNDIR = OUT/'runs'/'opencalc_int1'
shutil.rmtree(RUNDIR, ignore_errors=True)
r = subprocess.run([str(BIN),'install',str(apk),'--data-root',str(STORE)],
                   capture_output=True, text=True, timeout=120)
print('install rc:', r.returncode)
apps = STORE/'data'/'app'
dpkg = sorted(d.name for d in apps.iterdir()
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging') and (d/'base.apk').exists())[0]
cmd = [str(BIN),'run','--execution-mode','real-dalvik','--data-root',str(STORE),
       '-o',str(RUNDIR),'--package',dpkg,'--seconds','30','--trace']
log = OUT/'opencalc_int1.console.log'
with open(log,'wb') as cf:
    p = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT)
    try: p.wait(timeout=30); status=f'exit={p.returncode}'
    except subprocess.TimeoutExpired: p.kill(); p.wait(); status='killed-timeout'
text = log.read_text(errors='replace')
shot = RUNDIR/'screenshot.png'
face = sha16(shot) if shot.exists() else 'NO_SHOT'
out = {
 'status': status, 'binary': sha16(BIN),
 'face': face, 'published_pin': '479382e194be3803',
 'match': face.startswith('479382e1'),
 'uncaught': len(re.findall(r'UNCAUGHT|uncaught', text, re.I)),
 'default_bg_only': 'DEFAULT_BACKGROUND_ONLY' in text,
 'real_app_content': 'REAL_APP_CONTENT' in text,
 'log': str(log.relative_to(BASE)),
}
json.dump(out, open(OUT/'S194_OPENCALC_COHORT.json','w'), indent=1)
print(json.dumps(out, indent=1))
