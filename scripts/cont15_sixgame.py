#!/usr/bin/env python3
"""CONT-15 PHASE 13 — six-game claim live re-validation at merged HEAD.
Games: 2048, mini-tetris, minicraft, snake-deluxe, snake-neon, tictactoe-deluxe."""
import hashlib, json, os, shutil, subprocess

BASE='/home/z/my-project'
BIN=f'{BASE}/miniandroid/build/miniandroid'
OUT=f'{BASE}/run/cont15/sixgame'
os.makedirs(OUT, exist_ok=True)

GAMES={
 'g2048':            f'{BASE}/upload/s83_games/g2048_v1.0_vc1.apk',
 'tetris':           f'{BASE}/upload/s83_games/build_tetris/tetris_v1.0_vc1.apk',
 'minicraft':        f'{BASE}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk',
 'snake_deluxe':     f'{BASE}/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk',
 'snakeneon':        f'{BASE}/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk',
 'tictactoe_deluxe': f'{BASE}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk',
}

def sha16(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()[:16]

def install(apk,store):
    shutil.rmtree(store, ignore_errors=True); os.makedirs(store, exist_ok=True)
    ip=subprocess.run([BIN,'install',apk,'--data-root',store],capture_output=True,text=True,timeout=300)
    if ip.returncode!=0: return None
    return json.JSONDecoder().raw_decode(ip.stdout[ip.stdout.index('{'):])[0]['package']

results={}
for name,apk in GAMES.items():
    if not os.path.exists(apk):
        results[name]={'BLOCKED':'APK-ABSENT'}; continue
    st=f'{OUT}/store_{name}'
    pkg=install(apk,st)
    if not pkg:
        results[name]={'BLOCKED':'INSTALL-FAIL'}; continue
    runs=[]
    for i in (1,2,3):
        o=f'{OUT}/{name}_run{i}'; shutil.rmtree(o,ignore_errors=True); os.makedirs(o)
        with open(f'{o}/run.log','w') as f:
            subprocess.run([BIN,'run','--package',pkg,'--data-root',st,'--trace','--dump-view-tree',
                '--max-seconds','120','--frames','40','-o',o],stdout=f,stderr=subprocess.STDOUT,timeout=240)
        r={'sha16':sha16(f'{o}/screenshot.png') if os.path.exists(f'{o}/screenshot.png') else None}
        try:
            s=json.load(open(f'{o}/trace_summary.json'))
            fa=s.get('frame_analysis',{})
            r['verdict']=fa.get('verdict'); r['ops']=fa.get('app_draw_ops')
            r['px']=fa.get('app_owned_pixels_inside_content_bounds')
        except Exception: pass
        runs.append(r)
    results[name]={'apk_sha16':sha16(apk),'pkg':pkg,'runs':runs}
    print(name,apk.split('/')[-1],sha16(apk),[(r['sha16'],r.get('verdict'),r.get('ops')) for r in runs])

json.dump(results,open(f'{OUT}/sixgame.json','w'),indent=1)
print('saved')
