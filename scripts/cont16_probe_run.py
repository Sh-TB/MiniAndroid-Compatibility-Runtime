#!/usr/bin/env python3
"""CONT-16: run f266 + f259g + fcol probes at HEAD, report per-row verdicts.
Usage: python3 scripts/cont16_probe_run.py <outdir> [f266|f259g|fcol ...]
"""
import json, os, re, shutil, subprocess, sys

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"

def sha16(p):
    import hashlib
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16] if os.path.exists(p) else None

def install(apk, store):
    r = subprocess.run([BIN, 'install', apk, '--data-root', store],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        return None
    try:
        js = r.stdout[r.stdout.index('{'):]
        return json.JSONDecoder().raw_decode(js)[0]['package']
    except Exception:
        return None

def run_probe(apk, label, out):
    store = f'{out}/store_{label}'
    shutil.rmtree(store, ignore_errors=True); os.makedirs(store, exist_ok=True)
    pkg = install(apk, store)
    if not pkg:
        return {'label': label, 'install': 'FAIL'}
    o = f'{out}/{label}'
    shutil.rmtree(o, ignore_errors=True); os.makedirs(o)
    env = dict(os.environ)
    for k in list(env):
        if k.startswith('MINIANDROID_'):
            del env[k]
    with open(f'{o}/run.log', 'w') as f:
        subprocess.run([BIN, 'run', '--package', pkg, '--data-root', store,
                        '--max-seconds', '150', '--frames', '40', '-o', o],
                       stdout=f, stderr=subprocess.STDOUT, timeout=280, env=env)
    log = open(f'{o}/run.log', errors='replace').read()
    rows = {}
    for m in re.finditer(r'(F2?6?6?[A-Z]-?[A-Z0-9]*|F259-[A-Z]|F259g?-?[A-Z]?|K\d+|F266-[A-F])\|(PASS|FAIL)\|?(.*)', log):
        rows[m.group(1)] = (m.group(2), m.group(3)[:80])
    # generic fallback: any X|PASS/FAIL pattern
    if not rows:
        for m in re.finditer(r'([\w$-]+)\|(PASS|FAIL)\|([^\n]{0,90})', log):
            rows[m.group(1)] = (m.group(2), m.group(3))
    p = sum(1 for v in rows.values() if v[0] == 'PASS')
    f = sum(1 for v in rows.values() if v[0] == 'FAIL')
    return {'label': label, 'pkg': pkg, 'PASS': p, 'FAIL': f,
            'rows': rows, 'sha16': sha16(f'{o}/screenshot.png')}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else f'{BASE}/run/cont16'
    which = sys.argv[2:] or ['f266', 'f259g']
    os.makedirs(out, exist_ok=True)
    apks = {'f266': f'{BASE}/run/w8/f266.apk',
            'f259g': f'{BASE}/run/w7/f259g.apk',
            'f259': f'{BASE}/run/w7/f259.apk',
            'fcol': f'{BASE}/run/w7/fcol.apk'}
    res = {}
    for w in which:
        if not os.path.exists(apks[w]):
            res[w] = {'error': f'APK missing: {apks[w]}'}
            continue
        r = run_probe(apks[w], f'{w}_probe', out)
        res[w] = r
        print(f"== {w}: PASS={r.get('PASS')} FAIL={r.get('FAIL')}")
        for k, v in r.get('rows', {}).items():
            print(f"   {k}: {v[0]} {v[1]}")
    with open(f'{out}/probe_report.json', 'w') as fjs:
        json.dump(res, fjs, indent=1)
    print('saved', f'{out}/probe_report.json')
