#!/usr/bin/env python3
"""S188-W14 verification runs on the F-NEW-586 binary (67873b2bd21e9363):
1. se.tube42.p9.android  — pinned contract test: libgdx.so must dlopen OK
   now that glCopyTexImage2D/glCopyTexSubImage2D are exported.
2. app.halma             — regression: libgdx dlopen was OK, must stay OK.
Outputs land in evidence/s188_w14/.
"""
import json, sys, shutil
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w14'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)

RESULTS = {}
for pkg in ('se.tube42.p9.android', 'app.halma'):
    print('==', pkg, flush=True)
    apk = BASE / f'upload/stuck_apks/{pkg}.apk'
    shutil.rmtree(w2.RUNS / f'store_{pkg}', ignore_errors=True)
    r = w2.run_one(pkg, str(apk))
    log = (w2.OUT / f'{pkg}.console.log').read_text(errors='ignore')
    gdx = [l for l in log.splitlines() if 'gdx' in l and
           ('S2-NATIVE' in l or 'loadLibrary' in l)][:4]
    RESULTS[pkg] = dict(
        status=r.get('status'), tier=r.get('tier'),
        uncaught=r.get('uncaught_marks'),
        route_decision=r.get('route_decision'),
        gdx_lines=gdx,
        dlopen_ok=any('LOADED' in l for l in gdx),
    )
    print('  dlopen_ok=', RESULTS[pkg]['dlopen_ok'],
          'tier=', r.get('tier'), flush=True)
(w2.OUT / 'W14_GDX_VERIFY.json').write_text(json.dumps(RESULTS, indent=1))
print(json.dumps(RESULTS, indent=1))
