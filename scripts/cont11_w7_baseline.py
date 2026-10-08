#!/usr/bin/env python3
"""CONT-11 W7 — dooz baseline x3 + draw-window trace (canvas-bridge frontier).
Canonical harness: install -> run --frames N --dump-view-tree --trace.
Verdict: screenshot sha16 anchor + app_draw_ops + uncaught + DRAWWIN sequence."""
import hashlib, json, os, shutil, subprocess, sys

BASE='/home/z/my-project'
BIN=f'{BASE}/miniandroid/build/miniandroid'
APK=f'{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
OUT=f'{BASE}/run/w7'
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

def clean_env(env):
    for k in list(env):
        if k.startswith('MINIANDROID_'): env.pop(k)
    return env

def run_once(pkg,tag,frames=40,extra_env=None):
    out=f'{OUT}/dooz_{tag}'
    shutil.rmtree(out,ignore_errors=True); os.makedirs(out,exist_ok=True)
    env=clean_env(dict(os.environ))
    if extra_env: env.update(extra_env)
    with open(f'{out}/run.log','w') as f:
        rp=subprocess.run([BIN,'run','--package',pkg,'--data-root',STORE,
            '--dump-view-tree','--trace','--max-seconds','120','--frames',str(frames),'-o',out],
            stdout=f,stderr=subprocess.STDOUT,env=env,timeout=300)
    ss=f'{out}/screenshot.png'
    res={'tag':tag,'rc':rp.returncode,'sha16':sha16(ss) if os.path.exists(ss) else None}
    log=open(f'{out}/run.log',errors='replace').read()
    res['uncaught']=log.count('EXC-UNCAUGHT-TOP')
    res['drawwin_lines']=log.count('[DRAWWIN-IN]')
    for line in log.splitlines():
        if 'app_draw_ops' in line:
            res['ops_line']=line.strip()[:180]
        if 'C013-ONDRAW' in line:
            res.setdefault('ondraw_rows',[]).append(line.strip()[:180])
        if 'UC009-DRAW' in line:
            res.setdefault('uc009_rows',[]).append(line.strip()[:150])
        if 'VERDICT' in line.upper() and 'verdict' not in res:
            res['verdict_line']=line.strip()[:180]
    return res

if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True)
    pkg=install()
    print('package:',pkg,'binary:',sha16(BIN))
    results=[]
    for tag in ['base1','base2','base3']:
        r=run_once(pkg,tag); results.append(r); print(json.dumps(r)[:400])
    # draw-window trace run (fewer frames, bounded log)
    t=run_once(pkg,'drawwin',frames=6,
               extra_env={'MINIANDROID_DRAW_WINDOW_TRACE':'1'})
    results.append(t); print('DRAWWIN:',json.dumps(t)[:600])
    json.dump({'binary':sha16(BIN),'apk_sha256':hashlib.sha256(open(APK,'rb').read()).hexdigest(),
               'results':results}, open(f'{OUT}/w7_baseline_summary.json','w'), indent=1)
    print('summary -> run/w7/w7_baseline_summary.json')
