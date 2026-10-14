#!/usr/bin/env python3
"""CONT-14 audit — PHASE 0 baseline: dooz x3 at current HEAD.
Canonical harness (same protocol as scripts/cont10_baseline.py):
install -> run --frames N --dump-view-tree --trace.
Verdict: screenshot sha16 anchor + app_draw_ops + uncaught count."""
import hashlib, json, os, shutil, subprocess, sys

BASE='/home/z/my-project'
BIN=f'{BASE}/miniandroid/build/miniandroid'
APK=f'{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
OUT=f'{BASE}/run/cont14'
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
    for k in ('MINIANDROID_CL_TRACE','MINIANDROID_FIELD_TRACE','MINIANDROID_METHOD_TRACE','MINIANDROID_F259_TRACE'):
        env.pop(k,None)
    with open(f'{out}/run.log','w') as f:
        rp=subprocess.run([BIN,'run','--package',pkg,'--data-root',STORE,
            '--dump-view-tree','--trace','--max-seconds','120','--frames',str(frames),'-o',out],
            stdout=f,stderr=subprocess.STDOUT,env=env,timeout=300)
    ss=f'{out}/screenshot.png'
    res={'tag':tag,'rc':rp.returncode,'sha16':sha16(ss) if os.path.exists(ss) else None}
    log=open(f'{out}/run.log',errors='replace').read()
    res['uncaught']=log.count('EXC-UNCAUGHT-TOP')
    for line in log.splitlines():
        if 'app_draw_ops' in line or 'APP DRAW OPS' in line:
            res['ops_line']=line.strip()[:200]
    # compose materialization probes in trace
    res['layoutnode_mentions']=log.count('LayoutNode')
    vt=f'{out}/view_tree.txt'
    if os.path.exists(vt):
        res['viewtree_head']=[l for l in open(vt,errors='replace').read().splitlines()[:6]]
    return res

if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True)
    pkg=install()
    print('package:',pkg)
    print('binary_sha16:',sha16(BIN))
    print('apk_sha16:',sha16(APK))
    results=[run_once(pkg,tag) for tag in ['run1','run2','run3']]
    for r in results: print(json.dumps(r,indent=1)[:600])
    json.dump({'binary_sha16':sha16(BIN),'apk_sha16':sha16(APK),'package':pkg,'runs':results},
              open(f'{OUT}/dooz_baseline_x3.json','w'),indent=1)
    print('saved', f'{OUT}/dooz_baseline_x3.json')
