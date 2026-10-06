#!/usr/bin/env python3
"""CONT-10 W6 — dooz baseline x3 at current HEAD (fallback-free by construction).
Canonical harness: install -> run --frames N --dump-view-tree --trace.
Verdict: screenshot sha16 anchor + app_draw_ops + frame verdict."""
import hashlib, json, os, shutil, subprocess, sys

BASE='/home/z/my-project'
BIN=f'{BASE}/miniandroid/build/miniandroid'
APK=f'{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
OUT=f'{BASE}/run/w6'
STORE=f'{OUT}/store_dooz'

def sha16(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()[:16]

def install():
    shutil.rmtree(STORE, ignore_errors=True); os.makedirs(STORE, exist_ok=True)
    ip=subprocess.run([BIN,'install',APK,'--data-root',STORE],capture_output=True,text=True,timeout=300)
    if ip.returncode!=0: print('INSTALL FAIL',(ip.stderr or ip.stdout)[:300]); sys.exit(1)
    pkg=json.JSONDecoder().raw_decode(ip.stdout[ip.stdout.index('{'):])[0]['package']
    inst=f'{STORE}/data/app/{pkg}/base.apk'
    assert sha16(inst)==sha16(APK), 'installed apk identity mismatch'
    return pkg

def run_once(pkg,tag,frames=40):
    out=f'{OUT}/dooz_base_{tag}'
    shutil.rmtree(out,ignore_errors=True); os.makedirs(out,exist_ok=True)
    env=dict(os.environ)
    env.pop('MINIANDROID_CL_TRACE',None); env.pop('MINIANDROID_FIELD_TRACE',None)
    env.pop('MINIANDROID_METHOD_TRACE',None)
    with open(f'{out}/run.log','w') as f:
        rp=subprocess.run([BIN,'run','--package',pkg,'--data-root',STORE,
            '--dump-view-tree','--trace','--max-seconds','120','--frames',str(frames),'-o',out],
            stdout=f,stderr=subprocess.STDOUT,env=env,timeout=300)
    ss=f'{out}/screenshot.png'
    res={'tag':tag,'rc':rp.returncode,'sha16':sha16(ss) if os.path.exists(ss) else None}
    # app draw ops from trace
    for line in open(f'{out}/run.log',errors='replace'):
        if 'app_draw_ops' in line or 'APP DRAW OPS' in line:
            res['ops_line']=line.strip()[:160]
    log=open(f'{out}/run.log',errors='replace').read()
    res['uncaught']=log.count('EXC-UNCAUGHT-TOP')
    res['frames']=log.count('doFrame') if 'doFrame' in log else None
    # view tree summary
    vt=f'{out}/view_tree.txt'
    if os.path.exists(vt):
        res['viewtree_head']=[l for l in open(vt,errors='replace').read().splitlines()[:6]]
    return res

if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True)
    pkg=install()
    print('package:',pkg,'binary:',sha16(BIN))
    for tag in ['run1','run2','run3']:
        r=run_once(pkg,tag)
        print(json.dumps(r,indent=1)[:800])
