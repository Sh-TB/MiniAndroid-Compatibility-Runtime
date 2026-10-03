#!/usr/bin/env python3
"""closeout_sun_ab.py — #371 A/B causality: BASE vs PATCH binaries.

Same APK, same store layout, same inputs, same capture rules. Evidence dirs
isolated per binary (no overwrites). BASE = 6a6ef5b2a69f1f9d (pre-wave HEAD),
PATCH = 1b744e2a213505ce (framework-enum accessor + meta-data/FileProvider
laws). Causal claim shape: BASE specific failure vs PATCH specific change.
"""
import hashlib, json, math, os, shutil, subprocess, sys, time
from pathlib import Path

BASE_DIR = Path('/home/z/my-project')
APK = BASE_DIR / 'tmp/closeout_apks/com.forrestguice.suntimeswidget_135.apk'
PKG = 'com.forrestguice.suntimeswidget'
RUN_CAP = 300
RUNS = 3

BINARIES = {
    'BASE_6a6ef5b2a69f1f9d': '/tmp/miniandroid_BASE.bin',
    'PATCH_1b744e2a213505ce': '/tmp/miniandroid_PATCH.bin',
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pixel_metrics(png):
    from PIL import Image
    im = Image.open(png).convert('RGB')
    w, h = im.size
    px = im.resize((min(w, 270), min(h, 480))).getdata()
    total = len(px)
    colors = {}
    for p in px:
        colors[p] = colors.get(p, 0) + 1
    bg = max(colors.values())
    return {'width': w, 'height': h, 'unique_colors': len(colors),
            'dominant_ratio': round(bg / total, 4)}


def frame_verdict(out):
    ts = out / 'run1' / 'trace_summary.json'
    if ts.exists():
        fa = json.load(open(ts)).get('frame_analysis') or {}
        return fa.get('verdict'), fa.get('app_owned_pixels'), fa.get('app_draw_ops')
    return None, None, None


def main():
    root = BASE_DIR / 'run/closeout/sun_ab'
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    report = {'apk_sha256': sha256(APK), 'arms': {}}

    for tag, binp in BINARIES.items():
        arm = root / tag
        arm.mkdir()
        store = arm / 'store'
        store.mkdir()
        src_sha = sha256(APK)
        tmp = f'/tmp/sunab_{tag}.apk'
        shutil.copy2(APK, tmp)
        ip = subprocess.run([binp, 'install', tmp, '--data-root', str(store)],
                            capture_output=True, text=True, timeout=RUN_CAP)
        if ip.returncode != 0:
            print(tag, 'INSTALL FAIL'); continue
        hid = arm / 'hidden_sources'
        hid.mkdir()
        shutil.move(tmp, hid / APK.name)
        runs = []
        for n in range(1, RUNS + 1):
            out = arm / f'run{n}'
            out.mkdir()
            env = dict(os.environ, MINIANDROID_FILE_IO=str(out / 'file_io.jsonl'))
            # Wizard drive-through: Next button (964,1855) tapped at frames
            # 5/15/25/35 — pages advance; after the last page the app
            # finishes WelcomeActivity and builds the MAIN screen (sun
            # graph — requires the time4j calculator chain).
            with open(out / 'run.log', 'w') as f:
                subprocess.run(
                    [binp, 'run', '--package', PKG, '--data-root', str(store),
                     '--dump-view-tree', '--trace', '--max-seconds', '110',
                     '--frames', '55',
                     '--tap', '964,1855@5', '--tap', '964,1855@15',
                     '--tap', '964,1855@25', '--tap', '964,1855@35',
                     '-o', str(out)],
                    stdout=f, stderr=subprocess.STDOUT, env=env,
                    timeout=RUN_CAP)
            ss = out / 'screenshot.png'
            v, owned, ops = frame_verdict(arm)
            m = pixel_metrics(ss) if ss.exists() else None
            runs.append({'run': n,
                         'screenshot_sha256': sha256(ss) if ss.exists() else None,
                         'metrics': m, 'verdict': v, 'owned': owned, 'ops': ops})
            print(f'{tag} run{n}: verdict={v} owned={owned} ops={ops} '
                  f'sha={runs[-1]["screenshot_sha256"][:16] if runs[-1]["screenshot_sha256"] else None}',
                  flush=True)
        shas = {r['screenshot_sha256'] for r in runs}
        report['arms'][tag] = {
            'binary_sha256_16': sha256(binp)[:16],
            'runs': runs,
            'byte_identical_x3': len(shas) == 1 and None not in shas,
        }
    (root / 'ab_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: {'verdicts': [r['verdict'] for r in v['runs']],
                          'identical': v['byte_identical_x3']}
                      for k, v in report['arms'].items()}, indent=1))


if __name__ == '__main__':
    main()
