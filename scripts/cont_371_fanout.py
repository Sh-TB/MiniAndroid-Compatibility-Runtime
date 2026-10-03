#!/usr/bin/env python3
"""cont_371_fanout.py — #371 PHASE D/E: REAL NEW SOFTWARE FAN-OUT.

Contract (issue #371 final continuation): ≥2 NEW games/apps NOT among the
four canonical pixel goldens (2048/Snake Deluxe/MiniCraft/HelloWorld) and
NOT the chess/dooz determinism anchors. Per target:
  install (real install path) → hide/remove source APK → launch strictly by
  installed package identity (--package) → runtime trace/provenance
  (MINIANDROID_FILE_IO) → real asset/resource use → draw ops/state →
  screenshot + metrics + SHA → N cold runs → honest classification.

Modes:
  --screen  one run per candidate (select the fan-out targets)
  --final   N cold runs for the two chosen targets (default 3)
  --binary  optional path to an alternate binary (A/B causality, Phase E)
"""
import hashlib, json, math, os, shutil, subprocess, sys, time

BASE = '/home/z/my-project'
BIN = f'{BASE}/miniandroid/build/miniandroid'
OUT = f'{BASE}/run/cont371'

CANDIDATES = [
    # (name, kind, package, apk path)
    ('flappycow',  'game', None, 'tmp/flappycow/FlappyCow_release.apk'),
    ('tripeaks',   'game', None, 'upload/s65_apks/tripeaks_v1.2.1_vc4.apk'),
    ('klondike',   'game', None, 'upload/klondike_veldsoft_3.apk'),
    ('gmdice',     'game', None, 'upload/canonical_apks/de.duenndns.gmdice_8.apk'),
    ('tictactoedeluxe', 'game', None, 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'),
    ('ballbreak',  'game', None, 'upload/s105_apks/de.georgsieber.ballbreak_10.apk'),
    ('suntimes',   'app',  'com.forrestguice.suntimeswidget',
     'run/diff366/hidden_sources/com.forrestguice.suntimeswidget_135.apk'),
    ('stopwatch',  'app',  None, 'upload/canonical_apks/com.github.muellerma.stopwatch_6.apk'),
    ('notes_secuso', 'app', None, 'upload/notes_secuso_105.apk'),
    ('sudoku_secuso', 'app', None, 'upload/sudoku_secuso_101.apk'),
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


def resolve_pkg(apk):
    """Package name from the install output (no manifest re-parse here)."""
    r = subprocess.run([BIN, 'analyze', apk], capture_output=True, text=True,
                       timeout=180)
    for line in (r.stdout + r.stderr).splitlines():
        if 'package' in line.lower() and "='" in line:
            pass
    # analyze prints "[*] Package: com.x.y"
    for line in (r.stdout + r.stderr).splitlines():
        s = line.strip()
        if s.startswith('[*] Package:'):
            return s.split(':', 1)[1].strip()
    return None


def first_divergence(run_out):
    """First MISSING/ERROR api call or first FAILED file-io row."""
    api = os.path.join(run_out, 'api_calls.json')
    if os.path.exists(api):
        try:
            for rec in json.load(open(api)):
                st = rec.get('status')
                if st in ('MISSING', 'ERROR'):
                    return {'kind': 'API_' + st,
                            'where': f"{rec.get('class')}.{rec.get('method')}"
                                     f" caller={rec.get('caller')}"}
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
                        'where': f"{d.get('op')} path={d.get('path')} "
                                 f"subsystem={d.get('subsystem')} "
                                 f"caller={d.get('caller')}"}
    return None


def run_target(binary, name, kind, pkg, apk, runs=1, frames=40, tag=''):
    # tag isolates evidence per binary (A/B causality must never overwrite).
    if not tag:
        tag = sha256(binary)[:16]
    suffix = f'_{tag}'
    res = {'name': name, 'kind': kind, 'apk': apk, 'runs': []}
    store = f'{OUT}/store_{name}{suffix}'
    runroot = f'{OUT}/{name}{suffix}'
    shutil.rmtree(store, ignore_errors=True)
    shutil.rmtree(runroot, ignore_errors=True)
    os.makedirs(store, exist_ok=True)
    os.makedirs(runroot, exist_ok=True)

    src_sha = sha256(apk)
    ip = subprocess.run([binary, 'install', apk, '--data-root', store],
                        capture_output=True, text=True, timeout=300)
    if ip.returncode != 0:
        res['install'] = 'FAIL: ' + (ip.stderr or ip.stdout)[:200]
        return res
    res['install'] = 'OK'
    # Package identity straight from the install result (the store dir IS
    # named by the package — the same identity law pkginspect serves).
    try:
        pkg = json.JSONDecoder().raw_decode(
            ip.stdout[ip.stdout.index('{'):])[0]['package']
    except Exception:
        pkg = None
    res['nativeAbi'] = ('"nativePrimaryAbi": "' in ip.stdout and
                        ip.stdout.split('"nativePrimaryAbi": "')[1].split('"')[0])
    if pkg is None:
        pkg = resolve_pkg(apk)
    res['package'] = pkg
    inst = f'{store}/data/app/{pkg}/base.apk'
    if not os.path.exists(inst):
        res['install'] = f'FAIL: no base.apk for {pkg}'
        return res
    inst_sha = sha256(inst)
    res['identity'] = {'source_sha256': src_sha, 'installed_sha256': inst_sha,
                       'match': src_sha == inst_sha}

    # SOURCE HIDING: the source APK is removed from its run location —
    # the run addresses the package by identity only.
    hidden = f'{runroot}/hidden_source'
    try:
        shutil.move(apk, hidden)
        res['sourceHidden'] = True
    except Exception:
        res['sourceHidden'] = False

    try:
        for i in range(1, runs + 1):
            out = f'{runroot}/run{i}'
            os.makedirs(out, exist_ok=True)
            env = dict(os.environ,
                       MINIANDROID_FILE_IO=os.path.join(out, 'file_io.jsonl'))
            t0 = time.time()
            with open(f'{out}/run.log', 'w') as f:
                rp = subprocess.run(
                    [binary, 'run', '--package', pkg, '--data-root', store,
                     '--dump-view-tree', '--trace', '--dump-api-trace',
                     '--max-seconds', '110', '--frames', str(frames),
                     '-o', out],
                    stdout=f, stderr=subprocess.STDOUT, env=env, timeout=300)
                rc = rp.returncode
            dur = round(time.time() - t0, 1)
            ss = f'{out}/screenshot.png'
            m = pixel_metrics(ss) if os.path.exists(ss) else {'pixclass': 'NO_SCREENSHOT'}
            sha = sha256(ss) if os.path.exists(ss) else None
            verdict, owned, ops = frame_verdict(out)
            div = first_divergence(out)
            res['runs'].append({
                'run': i, 'rc': rc, 'seconds': dur,
                'pixels': m, 'screenshot_sha256': sha,
                'frame_verdict': verdict, 'app_owned_pixels': owned,
                'app_draw_ops': ops, 'first_divergence': div,
            })
    finally:
        # restore the source APK so later phases still have it
        if os.path.exists(hidden) and not os.path.exists(apk):
            shutil.move(hidden, apk)
    return res


def classify(run):
    """Honest classification per #371 PHASE D."""
    v = run.get('frame_verdict')
    px = run.get('pixels', {}).get('pixclass')
    ops = run.get('app_draw_ops') or 0
    if v == 'REAL_APP_CONTENT' and px == 'REAL_APP_UI' and ops > 0:
        return 'VERIFIED_REAL_APP_CONTENT'
    if ops > 0 or px == 'PARTIAL_MARGINAL':
        return 'OBSERVED'
    if px == 'WHITE_BLANK' or px == 'NO_SCREENSHOT':
        return 'BLOCKED'
    return 'PARTIAL'


def main():
    mode = '--screen'
    runs = 3
    binary = BIN
    chosen = None
    args = sys.argv[1:]
    if '--final' in args: mode = '--final'
    if '--screen' in args: mode = '--screen'
    if '--binary' in args:
        binary = args[args.index('--binary') + 1]
        args.remove('--binary'); args.remove(binary)
    if '--targets' in args:
        chosen = args[args.index('--targets') + 1].split(',')
    os.makedirs(OUT, exist_ok=True)
    if mode == '--screen':
        out_rows = []
        for name, kind, pkg, apk in CANDIDATES:
            if chosen and name not in chosen:
                continue
            path = f'{BASE}/{apk}'
            if not os.path.exists(path):
                out_rows.append({'name': name, 'error': 'APK missing'})
                continue
            r = run_target(binary, name, kind, pkg, path, runs=1)
            if r.get('runs'):
                r['classification'] = classify(r['runs'][0])
            out_rows.append(r)
            run0 = r.get('runs', [{}])[0] if r.get('runs') else {}
            cls = r.get('classification', r.get('install', '?'))
            print(f"{name:16s} {kind:5s} {str(cls):28s} "
                  f"px={run0.get('pixels', {}).get('pixclass')} "
                  f"ops={run0.get('app_draw_ops')} "
                  f"verdict={run0.get('frame_verdict')} "
                  f"div={json.dumps(run0.get('first_divergence'))[:90]}")
        tag = 'screen_' + os.path.basename(binary)[:16]
        json.dump(out_rows, open(f'{OUT}/{tag}.json', 'w'), indent=1)
        print('saved:', f'{OUT}/{tag}.json')
    else:
        targets = chosen or ['flappycow', 'suntimes']
        out_rows = []
        for name, kind, pkg, apk in CANDIDATES:
            if name not in targets:
                continue
            path = f'{BASE}/{apk}'
            r = run_target(binary, name, kind, pkg, path, runs=runs)
            for run in r.get('runs', []):
                run['classification'] = classify(run)
            out_rows.append(r)
            for run in r.get('runs', []):
                print(f"{name} run{run['run']}: {run['classification']} "
                      f"px={run['pixels']['pixclass']} ops={run['app_draw_ops']} "
                      f"sha={str(run['screenshot_sha256'])[:16]}")
        tag = 'final_' + os.path.basename(binary)[:16]
        json.dump(out_rows, open(f'{OUT}/{tag}.json', 'w'), indent=1)
        print('saved:', f'{OUT}/{tag}.json')


if __name__ == '__main__':
    main()
