#!/usr/bin/env python3
"""3-run confirmation for the 4 audit-suspected-valid S107 titles.
Downloads the F-Droid APK (cache was cleared), runs 3 independent runs on the
rebuilt HEAD runtime, and verifies content determinism per the visual rules."""
import json, os, re, subprocess, sys, hashlib, urllib.request
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/audit_s107/three_run'
APK_CACHE = Path('/tmp/s107_audit_apks')
OUT.mkdir(parents=True, exist_ok=True)
APK_CACHE.mkdir(parents=True, exist_ok=True)

FDROID = 'https://f-droid.org/repo'
FDROID_IDX = 'https://f-droid.org/api/v1/packages'
UA = {'User-Agent': 'miniandroid-s107-audit'}

TITLES = {
    'org.ucam.ssb22.pinyinfdroid': 166,
    'com.smorgasbork.hotdeath': 68,
    'org.bobstuff.bobball': 81,
    'com.dozingcatsoftware.bouncy': 121,
}

def fetch_fdroid_apk(package):
    cache = APK_CACHE / f'{package}.apk'
    if cache.exists() and cache.stat().st_size > 10000:
        return cache
    req = urllib.request.Request(f'{FDROID_IDX}/{package}', headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        idx = json.loads(r.read().decode())
    vcs = sorted(idx.get('packages', []), key=lambda p: p.get('versionCode', 0), reverse=True)
    if not vcs:
        return None
    vc, vname = vcs[0]['versionCode'], vcs[0].get('versionName', '')
    url = f'{FDROID}/{package}_{vc}.apk'
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r, open(cache, 'wb') as f:
        f.write(r.read())
    (APK_CACHE / f'{package}.ver').write_text(f'{vname} (vc {vc})')
    return cache

def px_metrics(path):
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert('RGB')
    a = np.asarray(im, dtype=np.int16)
    flat = a.reshape(-1, 3)
    packed = (flat[:, 0].astype(np.int32) << 16) | (flat[:, 1].astype(np.int32) << 8) | flat[:, 2]
    uq, ucnt = np.unique(packed, return_counts=True)
    dom = uq[int(np.argmax(ucnt))]
    dom_c = np.array([(int(dom) >> 16) & 255, (int(dom) >> 8) & 255, int(dom) & 255], dtype=np.int16)
    nb = float((np.abs(a - dom_c).max(axis=2) > 8).sum()) / (a.shape[0] * a.shape[1])
    return {'unique_colors': int(len(uq)), 'nonbg_ratio': round(nb, 5),
            'sha': hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]}

def main():
    assert BIN.exists(), 'runtime binary missing'
    summary = {}
    for pkg, issue in TITLES.items():
        apk = fetch_fdroid_apk(pkg)
        if apk is None:
            summary[pkg] = {'error': 'download failed'}
            continue
        runs = []
        for i in (1, 2, 3):
            d = OUT / f'{pkg}_run{i}'
            d.mkdir(parents=True, exist_ok=True)
            with open(d / 'run.log', 'w') as f:
                try:
                    rc = subprocess.run([str(BIN), 'run', str(apk), '-o', str(d)],
                                        stdout=f, stderr=subprocess.STDOUT, timeout=180).returncode
                except subprocess.TimeoutExpired:
                    rc = -1; f.write('\nTIMEOUT')
            text = (d / 'run.log').read_text(errors='ignore')
            m = re.search(r'Errors: (\d+)', text)
            s = re.search(r'Status: ([A-Z ]+?)(?:\s*[⚠✅]|$)', text)
            shot = d / 'screenshot.png'
            r = {'rc': rc, 'errors': int(m.group(1)) if m else -1,
                 'status': s.group(1).strip() if s else '?',
                 'apk_version': (APK_CACHE / f'{pkg}.ver').read_text() if (APK_CACHE / f'{pkg}.ver').exists() else '?'}
            r.update(px_metrics(shot) if shot.exists() else {'sha': 'NO-SHOT'})
            runs.append(r)
            print(f'{pkg} run{i}: {r["status"]} errors={r["errors"]} colors={r.get("unique_colors")} nb={r.get("nonbg_ratio")} sha={r.get("sha")}', flush=True)
        shas = {x.get('sha') for x in runs}
        errs = {x['errors'] for x in runs}
        content = all(x.get('nonbg_ratio', 0) > 0.01 and x.get('unique_colors', 0) > 20 for x in runs)
        verdict = 'VERIFIED_3RUN' if (len(shas) == 1 and len(errs) == 1 and content) else \
                  'SEMANTICALLY_STABLE' if content and len(errs) == 1 else 'NON_REPRODUCIBLE'
        summary[pkg] = {'issue': issue, 'runs': runs, 'verdict': verdict,
                        'apk_version': runs[0].get('apk_version')}
        print(f'  -> {verdict}', flush=True)
    json.dump(summary, open(OUT / 'three_run_summary.json', 'w'), indent=1)
    print(json.dumps({k: v.get('verdict') for k, v in summary.items()}, indent=1))

if __name__ == '__main__':
    main()
