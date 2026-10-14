#!/usr/bin/env python3
"""CONT-18h regression battery — run the five DEX-behavior probes at HEAD.

Usage: python3 scripts/cont18h_regression.py [outdir]

Probes (fresh install per probe, no MINIANDROID_* env):
  fcol  (K1..K18  collection laws)   run/w7/fcol.apk
  f259  (F259-A..G iterator laws)    run/w7/f259.apk
  f259g (F259-H..O grandparent laws) run/w7/f259g.apk
  f266  (F266-A..F null laws)        run/w8/f266.apk
  f268  (F268/A-L exception laws)    run/cont18g/f268.apk

Row harvest: generic `NAME|PASS/FAIL|detail` scan of each probe's run.log.
Output: <outdir>/probe_report.json + a one-line summary per probe.
"""
import json, os, re, shutil, subprocess, sys, hashlib

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"

PROBES = {
    'fcol':  f'{BASE}/run/w7/fcol.apk',
    'f259':  f'{BASE}/run/w7/f259.apk',
    'f259g': f'{BASE}/run/w7/f259g.apk',
    'f266':  f'{BASE}/run/w8/f266.apk',
    'f268':  f'{BASE}/run/cont18g/f268.apk',
}

def sha16(p):
    if not os.path.exists(p):
        return None
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

def run_probe(name, apk, out):
    store = f'{out}/store_{name}'
    shutil.rmtree(store, ignore_errors=True)
    os.makedirs(store, exist_ok=True)
    r = subprocess.run([BIN, 'install', apk, '--data-root', store],
                       capture_output=True, text=True, timeout=600)
    pkg = None
    try:
        js = r.stdout[r.stdout.index('{'):]
        pkg = json.JSONDecoder().raw_decode(js)[0].get('package')
    except Exception:
        pass
    if not pkg:
        return {'label': name, 'install': 'FAIL'}
    o = f'{out}/{name}'
    shutil.rmtree(o, ignore_errors=True)
    os.makedirs(o)
    env = {k: v for k, v in os.environ.items() if not k.startswith('MINIANDROID_')}
    with open(f'{o}/run.log', 'w') as f:
        subprocess.run([BIN, 'run', '--package', pkg, '--data-root', store,
                        '--max-seconds', '150', '--frames', '40', '-o', o],
                       stdout=f, stderr=subprocess.STDOUT, timeout=280, env=env)
    log = open(f'{o}/run.log', errors='replace').read()
    rows = {}
    for m in re.finditer(r'([A-Za-z0-9_$-]+)\|(PASS|FAIL)\|([^\n]{0,110})', log):
        rows[m.group(1)] = (m.group(2), m.group(3))
    p = sum(1 for v in rows.values() if v[0] == 'PASS')
    f = sum(1 for v in rows.values() if v[0] == 'FAIL')
    return {'label': name, 'pkg': pkg, 'PASS': p, 'FAIL': f,
            'rows': rows, 'sha16': sha16(f'{o}/screenshot.png')}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else f'{BASE}/run/cont18h/reg'
    os.makedirs(out, exist_ok=True)
    report = {}
    for name, apk in PROBES.items():
        if not os.path.exists(apk):
            report[name] = {'label': name, 'apk': 'MISSING'}
            continue
        rep = run_probe(name, apk, out)
        report[name] = rep
        print(f"{name}: PASS={rep.get('PASS')} FAIL={rep.get('FAIL')}")
    with open(f'{out}/probe_report.json', 'w') as f:
        json.dump(report, f, indent=1)
    print('binary:', sha16(BIN))
    print('report:', f'{out}/probe_report.json')
