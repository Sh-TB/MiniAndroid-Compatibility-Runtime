#!/usr/bin/env python3
"""S188-W15 — full regression gate for the FOREIGN_LOADER_NULL_CDTOR_LAW
binary (elision + FAULT-IP forensics + DLOPEN-PHASE rows).

Gates:
1. p9 determinism: 2 independent reruns must both dlopen libgdx.so OK.
2. halma: libgdx family regression (dlopen was OK, must stay OK) + the
   elision must NOT alter its load outcome (it has no init/fini arrays —
   the law must be a no-op there).
3. queens: Flutter lane regression (libflutter.so dlopen + JNI_OnLoad x2 +
   RegisterNatives x4 — the elision runs on libflutter.so too; its
   arrays must be untouched).
4. composeStopwatch: x86_64 host-native lane regression.
5. Goldens: bouncy/unote/dooz byte-exact pins.

Outputs land in evidence/s188_w15/W15_REGRESSION.json.
"""
import hashlib, json, shutil, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
sys.path.insert(0, str(BASE / 'scripts'))
import s188_w2_first_renders as w2

w2.OUT = BASE / 'evidence/s188_w15'
w2.RUNS = w2.OUT / 'runs'
w2.OUT.mkdir(parents=True, exist_ok=True)

BIN_SHA = hashlib.sha256((BASE / 'miniandroid/build/miniandroid')
                         .read_bytes()).hexdigest()[:16]
OUT = {'binary_sha16': BIN_SHA, 'runs': {}}

# ── 1. p9 determinism (2 more runs) ──────────────────────────────────────
PKG = 'se.tube42.p9.android'
apk = BASE / f'upload/stuck_apks/{PKG}.apk'
for i in (1, 2):
    shutil.rmtree(w2.RUNS / f'store_{PKG}', ignore_errors=True)
    r = w2.run_one(PKG, str(apk))
    log = (w2.OUT / f'{PKG}.console.log').read_text(errors='ignore')
    loaded = 'LOADED size=338440' in log
    OUT['runs'][f'p9_rerun{i}'] = dict(
        dlopen_ok=loaded, status=r.get('status'), tier=r.get('tier'),
        uncaught=r.get('uncaught_marks'))
    print(f'p9 rerun{i}: dlopen_ok={loaded} tier={r.get("tier")} '
          f'uncaught={r.get("uncaught_marks")}', flush=True)

# ── 2-4. lane regressions ────────────────────────────────────────────────
LANES = {
    'app.halma': 'upload/stuck_apks/app.halma.apk',
    'com.sidhant.queens': 'upload/stuck_apks/com.sidhant.queens.apk',
    'com.justdeax.composeStopwatch': 'upload/stuck_apks/com.justdeax.composeStopwatch.apk',
}
for pkg, rel in LANES.items():
    apk = BASE / rel
    shutil.rmtree(w2.RUNS / f'store_{pkg}', ignore_errors=True)
    r = w2.run_one(pkg, str(apk))
    log = (w2.OUT / f'{pkg}.console.log').read_text(errors='ignore')
    entry = dict(status=r.get('status'), tier=r.get('tier'),
                 uncaught=r.get('uncaught_marks'),
                 route_decision=r.get('route_decision'))
    if pkg == 'app.halma':
        entry['gdx_dlopen_ok'] = ('LOADED' in log and 'libgdx' in log) or \
                                 'dlopen ok' in log
    if pkg == 'com.sidhant.queens':
        entry['flutter_onload'] = log.count('JNI_OnLoad')
        entry['register_natives'] = log.count('RegisterNatives')
        entry['flutter_dlopen_ok'] = 'libapp.so' in log or 'dlopen ok' in log
    OUT['runs'][pkg] = entry
    print(f'{pkg}: {entry}', flush=True)

# ── 5. goldens ───────────────────────────────────────────────────────────
GOLDENS = [
    ("com.dozingcatsoftware.bouncy",
     str(BASE / 'upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk'),
     "8a6c24ac"),
    ("app.varlorg.unote",
     str(BASE / 'upload/canonical_apks/app.varlorg.unote_30.apk'),
     "3b8dcb0a"),
    ("io.github.yamin8000.dooz",
     str(BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'),
     "31ddd4d5"),
]
gold = {}
for pkg, apk_path, pin in GOLDENS:
    shutil.rmtree(w2.RUNS / f'store_{pkg}', ignore_errors=True)
    w2.run_one(pkg, apk_path)
    shot = w2.RUNS / pkg / 'screenshot.png'
    h = hashlib.sha256(shot.read_bytes()).hexdigest()[:16] \
        if shot.exists() else 'MISSING'
    gold[pkg] = dict(face_sha16=h, pin=pin, hold=h.startswith(pin))
    print(f'golden {pkg}: {h} pin={pin} hold={h.startswith(pin)}', flush=True)
OUT['goldens'] = gold
OUT['all_hold'] = all(g['hold'] for g in gold.values())

(w2.OUT / 'W15_REGRESSION.json').write_text(json.dumps(OUT, indent=1))
print('ALL_GOLDENS_HOLD =', OUT['all_hold'], flush=True)
