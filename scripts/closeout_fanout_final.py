#!/usr/bin/env python3
"""closeout_fanout_final.py — #371 FINAL CLOSEOUT Phase D formal evidence.

DECLARED targets (pre-registered before this verification run):
  games: tripeaks, gmdice          apps: sudoku_secuso, stopwatch
  random corpus pick (seed 20261004): fishrings
Per target: install → hide source APK → N cold runs by installed identity →
screenshot SHA + pixel metrics + frame verdict per run → restore source.
"""
import hashlib, json, math, os, shutil, subprocess, time

BASE = '/home/z/my-project'
BIN = f'{BASE}/miniandroid/build/miniandroid'
OUT = f'{BASE}/run/closeout/fanout_final'
RUNS = 3

TARGETS = [
    ('tripeaks',      'game', 'upload/s65_apks/tripeaks_v1.2.1_vc4.apk'),
    ('gmdice',        'game', 'upload/canonical_apks/de.duenndns.gmdice_8.apk'),
    ('sudoku_secuso', 'app',  'upload/sudoku_secuso_101.apk'),
    ('stopwatch',     'app',  'upload/canonical_apks/com.github.muellerma.stopwatch_6.apk'),
    ('fishrings',     'random', 'upload/canonical_apks/fishrings_v1.23_vc6.apk'),
]


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
    ent = -sum((c / total) * math.log2(c / total) for c in colors.values()) if total else 0.0
    return {'width': w, 'height': h, 'unique_colors': len(colors),
            'dominant_ratio': round(bg / total, 4),
            'nonbg_ratio': round((total - bg) / total, 4),
            'entropy': round(ent, 3)}


def frame_verdict(out):
    ts = os.path.join(out, 'trace_summary.json')
    if os.path.exists(ts):
        fa = json.load(open(ts)).get('frame_analysis') or {}
        return fa.get('verdict'), fa.get('app_owned_pixels'), fa.get('app_draw_ops')
    return None, None, None


def main():
    os.makedirs(OUT, exist_ok=True)
    tag = sha256(BIN)[:8]
    report = {'binary_sha16': tag, 'runs': RUNS, 'targets': []}
    for name, kind, apk in TARGETS:
        print(f'== {name} ({kind}) ==', flush=True)
        t = {'name': name, 'kind': kind, 'apk': apk}
        store = f'{OUT}/store_{name}_{tag}'
        runroot = f'{OUT}/{name}_{tag}'
        shutil.rmtree(store, ignore_errors=True)
        shutil.rmtree(runroot, ignore_errors=True)
        os.makedirs(store)
        os.makedirs(runroot)
        src_sha = sha256(f'{BASE}/{apk}')
        ip = subprocess.run([BIN, 'install', f'{BASE}/{apk}', '--data-root', store],
                            capture_output=True, text=True, timeout=300)
        pkg = json.JSONDecoder().raw_decode(
            ip.stdout[ip.stdout.index('{'):])[0]['package']
        inst = f'{store}/data/app/{pkg}/base.apk'
        t['identity'] = {'package': pkg,
                         'source_sha256': src_sha,
                         'installed_sha256': sha256(inst),
                         'match': src_sha == sha256(inst)}
        hidden = f'{runroot}/hidden_source.apk'
        shutil.move(f'{BASE}/{apk}', hidden)
        t['source_hidden'] = True
        try:
            t['runs'] = []
            for i in range(1, RUNS + 1):
                out = f'{runroot}/run{i}'
                os.makedirs(out, exist_ok=True)
                env = dict(os.environ,
                           MINIANDROID_FILE_IO=os.path.join(out, 'file_io.jsonl'))
                with open(f'{out}/run.log', 'w') as f:
                    subprocess.run(
                        [BIN, 'run', '--package', pkg, '--data-root', store,
                         '--dump-view-tree', '--trace', '--max-seconds', '110',
                         '--frames', '40', '-o', out],
                        stdout=f, stderr=subprocess.STDOUT, env=env, timeout=240)
                ss = f'{out}/screenshot.png'
                v, owned, ops = frame_verdict(out)
                run_rec = {
                    'run': i,
                    'screenshot_sha256': sha256(ss) if os.path.exists(ss) else None,
                    'pixels': pixel_metrics(ss) if os.path.exists(ss) else None,
                    'frame_verdict': v,
                    'app_owned_pixels': owned,
                    'app_draw_ops': ops,
                }
                t['runs'].append(run_rec)
                print(f"  run{i}: verdict={v} ops={ops} sha={run_rec['screenshot_sha256'][:16] if run_rec['screenshot_sha256'] else None}", flush=True)
            shas = [r['screenshot_sha256'] for r in t['runs']]
            verdicts = [r['frame_verdict'] for r in t['runs']]
            t['byte_identical_x3'] = len(set(shas)) == 1 and shas[0] is not None
            t['verdict_stable_x3'] = len(set(verdicts)) == 1
        finally:
            shutil.move(hidden, f'{BASE}/{apk}')
        report['targets'].append(t)
        with open(f'{OUT}/fanout_final_{tag}.json', 'w') as f:
            json.dump(report, f, indent=1)
    print('=== FAN-OUT FINAL SUMMARY ===')
    for t in report['targets']:
        shas = [r['screenshot_sha256'][:16] for r in t.get('runs', [])]
        print(t['name'], '→', 'identical_x3' if t.get('byte_identical_x3') else shas,
              [r['frame_verdict'] for r in t.get('runs', [])])


if __name__ == '__main__':
    main()
