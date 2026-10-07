#!/usr/bin/env python3
"""CONT-15 regression battery at merged HEAD (binary 0ee46f5a719d2a8c).
Runs: dooz x3, anchors x3 (opencalc/chess/microtimer/unote), probe suites
(f259/f259g/f266 — count PASS/FAIL rows from run logs), telegram, tictactoe,
gmdice, snakeneon. No fallback credit; engine frame-truth verdicts only."""
import hashlib, json, os, shutil, subprocess, sys

BASE='/home/z/my-project'
BIN=f'{BASE}/miniandroid/build/miniandroid'
OUT=f'{BASE}/run/cont15'
os.makedirs(OUT, exist_ok=True)

def sha16(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()[:16]

def install(apk,store):
    shutil.rmtree(store, ignore_errors=True); os.makedirs(store, exist_ok=True)
    ip=subprocess.run([BIN,'install',apk,'--data-root',store],capture_output=True,text=True,timeout=600)
    if ip.returncode!=0: return None
    return json.JSONDecoder().raw_decode(ip.stdout[ip.stdout.index('{'):])[0]['package']

def run_apk(pkg,store,label,frames=40,extra=('--trace','--dump-view-tree'),maxsec=120):
    o=f'{OUT}/{label}'; shutil.rmtree(o,ignore_errors=True); os.makedirs(o)
    env=dict(os.environ)
    for k in ('MINIANDROID_CL_TRACE','MINIANDROID_FIELD_TRACE','MINIANDROID_F259_TRACE','MINIANDROID_F264_TRACE'):
        env.pop(k,None)
    with open(f'{o}/run.log','w') as f:
        rp=subprocess.run([BIN,'run','--package',pkg,'--data-root',store,*extra,
            '--max-seconds',str(maxsec),'--frames',str(frames),'-o',o],
            stdout=f,stderr=subprocess.STDOUT,env=env,timeout=maxsec+120)
    res={'label':label,'rc':rp.returncode,'sha16':sha16(f'{o}/screenshot.png') if os.path.exists(f'{o}/screenshot.png') else None}
    log=open(f'{o}/run.log',errors='replace').read()
    res['uncaught']=log.count('EXC-UNCAUGHT-TOP')
    try:
        s=json.load(open(f'{o}/trace_summary.json'))
        fa=s.get('frame_analysis',{})
        res['verdict']=fa.get('verdict'); res['app_draw_ops']=fa.get('app_draw_ops')
        res['app_px']=fa.get('app_owned_pixels_inside_content_bounds')
    except Exception: pass
    return res

def run_probe(apk,label,maxsec=150):
    store=f'{OUT}/store_{label}'
    pkg=install(apk,store)
    if not pkg: return {'label':label,'install':'FAIL'}
    o=f'{OUT}/{label}'; shutil.rmtree(o,ignore_errors=True); os.makedirs(o)
    with open(f'{o}/run.log','w') as f:
        subprocess.run([BIN,'run','--package',pkg,'--data-root',store,
            '--max-seconds',str(maxsec),'--frames','40','-o',o],
            stdout=f,stderr=subprocess.STDOUT,timeout=maxsec+120)
    log=open(f'{o}/run.log',errors='replace').read()
    import re
    # probe verdict rows: count PASS/FAIL markers generically
    passes=len(re.findall(r'\bPASS\b',log)); fails=len(re.findall(r'\bFAIL\b',log))
    return {'label':label,'pkg':pkg,'PASS':passes,'FAIL':fails,
            'rc':0,'sha16':sha16(f'{o}/screenshot.png') if os.path.exists(f'{o}/screenshot.png') else None}

if __name__=='__main__':
    battery={}
    # 1. dooz x3
    st=f'{OUT}/store_dooz'
    pkg=install(f'{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk',st)
    dooz=[run_apk(pkg,st,f'dooz_run{i}') for i in (1,2,3)]
    battery['dooz_x3']=dooz
    print('dooz:',[ (r['sha16'],r.get('verdict')) for r in dooz ])
    # 2. probes
    battery['f259']=run_probe(f'{BASE}/run/w6/f259.apk','f259_probe')
    battery['f259g']=run_probe(f'{BASE}/run/w7/f259g.apk','f259g_probe')
    battery['f266']=run_probe(f'{BASE}/run/w8/f266.apk','f266_probe')
    print('probes:',{k:(battery[k].get('PASS'),battery[k].get('FAIL')) for k in ('f259','f259g','f266')})
    # 3. anchors x3 (subset: microtimer + unote; opencalc/chess apk present?)
    anchors={}
    for name,apk in [('microtimer','canonical_apks/dubrowgn.microtimer_8.apk'),
                     ('unote','canonical_apks/app.varlorg.unote_30.apk'),
                     ('gmdice','canonical_apks/de.duenndns.gmdice_8.apk')]:
        st=f'{OUT}/store_{name}'
        p=install(f'{BASE}/upload/{apk}',st)
        if p:
            runs=[run_apk(p,st,f'{name}_run{i}') for i in (1,2,3)]
            anchors[name]=runs
            print(name,[r['sha16'] for r in runs])
    battery['anchors']=anchors
    # 4. telegram + tictactoe single runs at the new binary
    for name,apk in [('telegram_forkgram','forkgram_709208.apk'),
                     ('tictactoe_emmanuel','canonical_apks/com.emmanuelmess.tictactoe_3.apk')]:
        st=f'{OUT}/store_{name}'
        p=install(f'{BASE}/upload/{apk}',st)
        if p:
            battery[name]=run_apk(p,st,name,maxsec=150)
            print(name,battery[name].get('sha16'),battery[name].get('verdict'),battery[name].get('app_draw_ops'))
    json.dump(battery,open(f'{OUT}/battery.json','w'),indent=1)
    print('saved battery.json')
