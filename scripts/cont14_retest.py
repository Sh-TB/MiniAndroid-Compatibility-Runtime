#!/usr/bin/env python3
"""CONT-14 audit — corpus retest: tictactoe_emmanuel + forkgram(Telegram) + gmdice + bouncy.
Canonical harness: install -> run --frames N --dump-view-tree --trace."""
import hashlib, json, os, shutil, subprocess, sys

BASE='/home/z/my-project'
BIN=f'{BASE}/miniandroid/build/miniandroid'
OUT=f'{BASE}/run/cont14'

APKS={
 'tictactoe_emmanuel': f'{BASE}/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk',
 'telegram_forkgram':  f'{BASE}/upload/forkgram_709208.apk',
 'gmdice':             f'{BASE}/upload/canonical_apks/de.duenndns.gmdice_8.apk',
}

def sha16(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()[:16]

def install(apk,store):
    shutil.rmtree(store, ignore_errors=True); os.makedirs(store, exist_ok=True)
    ip=subprocess.run([BIN,'install',apk,'--data-root',store],capture_output=True,text=True,timeout=600)
    if ip.returncode!=0: return None,(ip.stderr or ip.stdout)[:200]
    return json.JSONDecoder().raw_decode(ip.stdout[ip.stdout.index('{'):])[0]['package'], None

def run_once(pkg,store,tag,frames=40,maxsec=150):
    out=f'{OUT}/{tag}'
    shutil.rmtree(out,ignore_errors=True); os.makedirs(out,exist_ok=True)
    env=dict(os.environ)
    for k in ('MINIANDROID_CL_TRACE','MINIANDROID_FIELD_TRACE','MINIANDROID_METHOD_TRACE','MINIANDROID_F259_TRACE'):
        env.pop(k,None)
    with open(f'{out}/run.log','w') as f:
        rp=subprocess.run([BIN,'run','--package',pkg,'--data-root',store,
            '--dump-view-tree','--trace','--max-seconds',str(maxsec),'--frames',str(frames),'-o',out],
            stdout=f,stderr=subprocess.STDOUT,env=env,timeout=maxsec+120)
    ss=f'{out}/screenshot.png'
    res={'tag':tag,'rc':rp.returncode,'screenshot_sha16':sha16(ss) if os.path.exists(ss) else None,
         'apk_sha16':None}
    log=open(f'{out}/run.log',errors='replace').read()
    res['uncaught']=log.count('EXC-UNCAUGHT-TOP')
    try:
        s=json.load(open(f'{out}/trace_summary.json'))
        fa=s.get('frame_analysis',{})
        res['verdict']=fa.get('verdict')
        res['app_draw_ops']=fa.get('app_draw_ops')
        res['first_missing_stage']=fa.get('first_missing_stage')
        res['activity']=s.get('activity')
        fe=s.get('first_failure_event',{})
        res['first_failure']=str(fe.get('state'))[:180]
    except Exception as e:
        res['trace_summary_err']=str(e)[:80]
    # exception census by top class
    excs=[]
    for line in log.splitlines():
        if 'EXC-UNCAUGHT-TOP' in line:
            excs.append(line[:160])
    res['exc_head']=excs[:4]
    return res

if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True)
    allres={}
    for name,apk in APKS.items():
        store=f'{OUT}/store_{name}'
        pkg,err=install(apk,store)
        if not pkg:
            allres[name]={'install_fail':err,'apk_sha16':sha16(apk)}; continue
        r=run_once(pkg,store,name+'_run1')
        r['apk_sha16']=sha16(apk)
        r['package']=pkg
        allres[name]=r
        print(json.dumps({k:r.get(k) for k in ('tag','rc','screenshot_sha16','verdict','app_draw_ops','uncaught','first_missing_stage')},indent=1))
    json.dump(allres,open(f'{OUT}/corpus_retest.json','w'),indent=1)
    print('saved', f'{OUT}/corpus_retest.json')
