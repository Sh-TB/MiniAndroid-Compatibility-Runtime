#!/usr/bin/env python3
"""S188-W12 T16: ball2box Godot-lane run + GodotLib chain census."""
import json, re, subprocess, hashlib, shutil
from pathlib import Path
BASE = Path('/home/z/my-project')
BIN = BASE/'miniandroid/build/miniandroid'
OUT = BASE/'evidence/s188_w12'
PKG = 'com.simondalvai.ball2box'
STORE = BASE/f'evidence/s188_w2/runs/store_{PKG}'
APK = BASE/f'upload/stuck_apks/{PKG}.apk'
RUNDIR = OUT/'runs'/'w12_godot1'
LOG = OUT/'w12_godot1.console.log'
def sha16(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()[:16]
shutil.rmtree(RUNDIR, ignore_errors=True)
subprocess.run([str(BIN),'install',str(APK),'--data-root',str(STORE)],capture_output=True,timeout=120)
dpkg = sorted(d.name for d in (STORE/'data'/'app').iterdir()
              if d.is_dir() and not d.name.startswith('.') and not d.name.endswith('.staging')
              and (d/'base.apk').exists())[0]
cmd=[str(BIN),'run','--execution-mode','real-dalvik','--data-root',str(STORE),
     '-o',str(RUNDIR),'--package',dpkg,'--seconds','30','--trace']
with open(LOG,'wb') as cf:
    p=subprocess.Popen(cmd,stdout=cf,stderr=subprocess.STDOUT)
    try: p.wait(timeout=30); status=f'exit={p.returncode}'
    except subprocess.TimeoutExpired: p.kill(); p.wait(); status='killed-timeout'
text = LOG.read_text(errors='replace')
out = {
 'status': status, 'binary': sha16(BIN),
 'godotlib_lines': re.findall(r'.*GodotLib.*', text)[:14],
 'load_library': re.findall(r'\[S2-NATIVE\] (?:System\.)?load.*', text)[:10],
 'jni_unsupported_godot': [l for l in re.findall(r'\[JNI-UNSUPPORTED\].*', text) if 'odot' in l][:10],
 'oncreate_ok': bool(re.search(r'GodotApp.*onCreate|BOOT-ORDER.*execute_application ok=1', text)),
 'uncaught': len(re.findall(r'uncaught', text, re.I)),
 'log': str(LOG.relative_to(BASE)),
}
json.dump(out, open(OUT/'W12_T16_GODOT_RUN.json','w'), indent=1)
print(json.dumps({k:v for k,v in out.items() if k!='godotlib_lines'}, indent=1))
for l in out['godotlib_lines'][:14]: print(l[:160])
