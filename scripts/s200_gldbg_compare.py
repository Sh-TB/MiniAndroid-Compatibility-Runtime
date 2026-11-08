#!/usr/bin/env python3
"""S200 Target-B — GLDBG side-by-side: dooz (renders) vs tictactoe (blank).

Isolates the FIRST divergence in the shared GLES pipeline: same binary,
same sb shader pair, same probe code. Extracts vap types/strides, sb_vert
data reads, sb_frag colors/textures, and face pixel outcome for both.
"""
import hashlib, json, re, shutil, subprocess, sys, time
from collections import Counter
from pathlib import Path
from PIL import Image

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
RUNS = BASE / 'evidence/s200/runs'

APPS = [
    ('dooz', 'io.github.yamin8000.dooz_23.apk'),
    ('ttt', 'com.emmanuelmess.tictactoe_3.apk'),
]

def run_app(tag, apk_name):
    apk = BASE / 'upload/canonical_apks' / apk_name
    store = RUNS / f'store_cmp_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                       capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    rundir = RUNS / f'cmp_{tag}'
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'cmp_{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--frames', '12', '--frame-delay', '250']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=600,
                       env={'MINIANDROID_GL_DEBUG': '1',
                            'PATH': '/usr/bin:/bin', 'HOME': '/home/z'})
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')

    res = {
        'dpkg': dpkg, 'wall_s': wall,
        'vap_attrib_rows': re.findall(r'\[GLDBG\] attrib idx.*', log)[:6],
        'vap_raw_first': re.findall(r'\[GLDBG\] vap RAW.*', log)[:6],
        'mat4': re.findall(r'\[GLDBG\] mat4 .*', log)[:4],
        'sbvert': re.findall(r'\[GLDBG\] sb_vert.*', log)[:6],
        'sbfrag': re.findall(r'\[GLDBG\] sb_frag.*', log)[:6],
        'draws': re.findall(r'\[GLDBG\] DRAW .*', log)[:8],
        'tex2d': re.findall(r'\[GLDBG\] tex2D .*', log)[:4],
        'draw_count': len(re.findall(r'\[GLDBG\] DRAW', log)),
        'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught', log)),
    }
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    if shot and shot.exists():
        im = Image.open(shot).convert('RGB')
        w, h = im.size
        px = im.load()
        census = Counter()
        n = 0
        for y in range(0, h, 3):
            for x in range(0, w, 3):
                p = px[x, y]
                if p != (255, 255, 255):
                    n += 1
                    census[(p[0]//32*32, p[1]//32*32, p[2]//32*32)] += 1
        res['face_nonwhite_sampled'] = n
        res['face_top_colors'] = census.most_common(5)
    return res

out = {'binary_sha16': BIN_SHA}
for tag, apk in APPS:
    print(f'=== running {tag} ({apk}) ===', flush=True)
    out[tag] = run_app(tag, apk)
    print(json.dumps(out[tag], indent=1)[:2400], flush=True)

(BASE / 'evidence/s200/GLDBG_DOOZ_VS_TTT.json').write_text(json.dumps(out, indent=1))
print('WROTE evidence/s200/GLDBG_DOOZ_VS_TTT.json')
