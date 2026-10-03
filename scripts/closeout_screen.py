#!/usr/bin/env python3
"""closeout_screen.py — #371 FINAL CLOSEOUT screening pass.

One run per candidate (source APK hidden after install, launched by
installed package identity). Records pixel class + frame verdict +
first divergence to choose the closeout work order. Evidence isolated
per binary tag.
"""
import hashlib, json, math, os, shutil, subprocess, sys, time

BASE = '/home/z/my-project'
BIN = f'{BASE}/miniandroid/build/miniandroid'
OUT = f'{BASE}/run/closeout/screen'

CANDIDATES = [
    # (name, kind, apk path)
    ('tripeaks',        'game', 'upload/s65_apks/tripeaks_v1.2.1_vc4.apk'),
    ('gmdice',          'game', 'upload/canonical_apks/de.duenndns.gmdice_8.apk'),
    ('klondike',        'game', 'upload/klondike_veldsoft_3.apk'),
    ('ballbreak',       'game', 'tmp/closeout_apks/de.georgsieber.ballbreak_10.apk'),
    ('tictactoedeluxe', 'game', 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'),
    ('stopwatch',       'app',  'upload/canonical_apks/com.github.muellerma.stopwatch_6.apk'),
    ('sudoku_secuso',   'app',  'upload/sudoku_secuso_101.apk'),
    ('fishrings',       'app',  'upload/canonical_apks/fishrings_v1.23_vc6.apk'),
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
    nonbg = total - bg
    ent = -sum((c / total) * math.log2(c / total) for c in colors.values()) if total else 0.0
    m = {'width': w, 'height': h, 'unique_colors': len(colors),
         'dominant_ratio': round(bg / total, 4),
         'nonbg_ratio': round(nonbg / total, 4),
         'entropy': round(ent, 3)}
    if m['nonbg_ratio'] >= 0.02 and m['unique_colors'] >= 64:
        m['pixclass'] = 'REAL_APP_UI'
    elif m['nonbg_ratio'] >= 0.002 or m['unique_colors'] >= 24:
        m['pixclass'] = 'PARTIAL_MARGINAL'
    else:
        m['pixclass'] = 'WHITE_BLANK'
    return m


def frame_verdict(out):
    ts = os.path.join(out, 'trace_summary.json')
    if os.path.exists(ts):
        try:
            fa = json.load(open(ts)).get('frame_analysis') or {}
            return fa.get('verdict'), fa.get('app_owned_pixels'), fa.get('app_draw_ops')
        except Exception:
            pass
    return None, None, None


def first_divergence(run_out):
    api = os.path.join(run_out, 'api_calls.json')
    if os.path.exists(api):
        try:
            for rec in json.load(open(api)):
                st = rec.get('status')
                if st in ('MISSING', 'ERROR'):
                    return {'kind': 'API_' + st,
                            'where': f"{rec.get('class')}.{rec.get('method')} caller={rec.get('caller')}"}
        except Exception:
            pass
    fio = os.path.join(run_out, 'file_io.jsonl')
    if os.path.exists(fio):
        for line in open(fio, errors='replace'):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('result') == 'FAILURE':
                return {'kind': 'FILE_IO_FAILURE',
                        'where': f"{d.get('op')} path={d.get('path')} caller={d.get('caller')}"}
    return None


def run_target(name, kind, apk, tag):
    res = {'name': name, 'kind': kind, 'apk': apk}
    store = f'{OUT}/store_{name}_{tag}'
    runroot = f'{OUT}/{name}_{tag}'
    shutil.rmtree(store, ignore_errors=True)
    shutil.rmtree(runroot, ignore_errors=True)
    os.makedirs(store, exist_ok=True)
    os.makedirs(runroot, exist_ok=True)
    src_sha = sha256(f'{BASE}/{apk}')
    ip = subprocess.run([BIN, 'install', f'{BASE}/{apk}', '--data-root', store],
                        capture_output=True, text=True, timeout=300)
    if ip.returncode != 0:
        res['install'] = 'FAIL: ' + (ip.stderr or ip.stdout)[:160]
        return res
    try:
        pkg = json.JSONDecoder().raw_decode(
            ip.stdout[ip.stdout.index('{'):])[0]['package']
    except Exception:
        pkg = None
    res['package'] = pkg
    inst = f'{store}/data/app/{pkg}/base.apk'
    res['identity'] = {'source_sha16': src_sha[:16],
                       'installed_sha16': sha256(inst)[:16],
                       'match': src_sha == sha256(inst)}
    hidden = f'{runroot}/hidden_source'
    try:
        shutil.move(f'{BASE}/{apk}', hidden)
        res['sourceHidden'] = True
    except Exception:
        res['sourceHidden'] = False
    try:
        out = f'{runroot}/run1'
        os.makedirs(out, exist_ok=True)
        env = dict(os.environ, MINIANDROID_FILE_IO=os.path.join(out, 'file_io.jsonl'))
        with open(f'{out}/run.log', 'w') as f:
            rp = subprocess.run(
                [BIN, 'run', '--package', pkg, '--data-root', store,
                 '--dump-view-tree', '--trace', '--max-seconds', '100',
                 '--frames', '40', '-o', out],
                stdout=f, stderr=subprocess.STDOUT, env=env, timeout=240)
        ss = f'{out}/screenshot.png'
        m = pixel_metrics(ss) if os.path.exists(ss) else {'pixclass': 'NO_SCREENSHOT'}
        v, owned, ops = frame_verdict(out)
        res['run1'] = {'pixels': m, 'screenshot_sha16': sha256(ss)[:16] if os.path.exists(ss) else None,
                       'frame_verdict': v, 'app_owned_pixels': owned, 'app_draw_ops': ops,
                       'first_divergence': first_divergence(out)}
    finally:
        if os.path.exists(hidden) and not os.path.exists(f'{BASE}/{apk}'):
            shutil.move(hidden, f'{BASE}/{apk}')
    return res


def classify(run):
    if 'run1' not in run:
        return 'INSTALL_FAIL'
    v = run['run1'].get('frame_verdict')
    px = run['run1']['pixels'].get('pixclass')
    ops = run['run1'].get('app_draw_ops') or 0
    if v == 'REAL_APP_CONTENT' and px == 'REAL_APP_UI' and ops > 0:
        return 'VERIFIED_REAL_APP_CONTENT'
    if ops > 0 or px == 'PARTIAL_MARGINAL':
        return 'OBSERVED'
    if px in ('WHITE_BLANK', 'NO_SCREENSHOT'):
        return 'BLOCKED'
    return 'PARTIAL'


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    tag = sha256(BIN)[:8]
    results = []
    for name, kind, apk in CANDIDATES:
        print(f'== screening {name} ==', flush=True)
        try:
            r = run_target(name, kind, apk, tag)
        except Exception as e:
            r = {'name': name, 'kind': kind, 'error': str(e)[:200]}
        r['classification'] = classify(r)
        print(json.dumps(r, indent=1)[:900], flush=True)
        results.append(r)
    with open(f'{OUT}/screen_results_{tag}.json', 'w') as f:
        json.dump({'binary_tag': tag, 'targets': results}, f, indent=1)
    print('=== SUMMARY ===')
    for r in results:
        print(r['name'], '→', r.get('classification'))
