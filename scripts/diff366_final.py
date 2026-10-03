#!/usr/bin/env python3
"""DIFFERENTIAL-366 — Stage B: canonical 9-app pipeline on CURRENT HEAD.

4 WORKING (opencalc, unote, microtimer, chess; dooz = Compose control)
5 WHITE (S115 population, distinct root families):
  org.fossify.clock / com.sidhant.blockblast / com.game.asteroids_revenge
  fr.arnaudguyon.spacevertex / com.sanskritbasics.memory

Per app: SOURCE APK -> SOURCE SHA -> INSTALL -> PACKAGE IDENTITY ->
INSTALLED SHA -> pkgaudit -> HIDE SOURCE -> run --package (x3 for the
3-run set) -> artifacts + metrics. All generic; no per-app code paths.
"""
import hashlib, json, math, os, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
WORK = BASE / 'run/diff366'
HIDDEN = WORK / 'hidden_sources'
APKSTAGE = BASE / 'tmp/diff366_apks'
FIN = BASE / 'evidence/diff366/final'
for d in (WORK, HIDDEN, FIN):
    d.mkdir(parents=True, exist_ok=True)
STATE = WORK / 'final_state.json'
RUN_CAP = 170

APPS = [
    # name, package, source apk (staged), family, role, three_run
    ('opencalc', 'com.darkempire78.opencalculator',
     APKSTAGE / 'opencalculator_53.apk', 'appcompat-xml', 'WORKING', True),
    ('unote', 'app.varlorg.unote',
     APKSTAGE / 'app.varlorg.unote_30.apk', 'appcompat-xml', 'WORKING', True),
    ('microtimer', 'dubrowgn.microtimer',
     APKSTAGE / 'dubrowgn.microtimer_8.apk', 'programmatic-view', 'WORKING', False),
    ('chess', 'jwtc.android.chess',
     APKSTAGE / 'chess_jwtc_298.apk', 'custom-view-game', 'WORKING', True),
    ('bouncy', 'com.dozingcatsoftware.bouncy',
     APKSTAGE / 'bouncy.apk', 'custom-view-game', 'WORKING', True),
    ('dooz', 'io.github.yamin8000.dooz',
     APKSTAGE / 'io.github.yamin8000.dooz_23.apk', 'compose', 'CONTROL', False),
    ('fossifyclock', 'org.fossify.clock',
     APKSTAGE / 'org.fossify.clock_10.apk', 'appcompat-startup', 'WHITE', True),
    ('blockblast', 'com.sidhant.blockblast',
     APKSTAGE / 'com.sidhant.blockblast_43.apk', 'compose', 'WHITE', True),
    ('asteroids', 'com.game.asteroids_revenge',
     APKSTAGE / 'com.game.asteroids_revenge_100242.apk', 'godot-native-jni', 'WHITE', True),
    ('spacevertex', 'fr.arnaudguyon.spacevertex',
     APKSTAGE / 'fr.arnaudguyon.spacevertex_29.apk', 'glsurface-clinit', 'WHITE', True),
    ('memory', 'com.sanskritbasics.memory',
     APKSTAGE / 'com.sanskritbasics.memory_34.apk', 'androidx-view', 'WHITE', True),
]

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def pixel_metrics(png):
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB')
    except Exception as e:
        return {'error': str(e)}
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
        m['pixclass'] = 'REAL_APP_UI_CANDIDATE'
    elif m['nonbg_ratio'] >= 0.002 or m['unique_colors'] >= 24:
        m['pixclass'] = 'PARTIAL_MARGINAL'
    else:
        m['pixclass'] = 'WHITE_BLANK'
    return m

def stage_apk(apk):
    """bring back from hidden_sources if needed; return staged path"""
    if apk.exists():
        return apk
    hid = HIDDEN / apk.name
    if hid.exists():
        shutil.copy2(str(hid), str(apk))
        return apk
    raise FileNotFoundError(apk)

def hide_source(apk, name):
    hid = HIDDEN / apk.name
    if hid.exists():
        hid.unlink()
    shutil.move(str(apk), str(hid))
    return str(hid)

def collect_run(out: Path, rec):
    ss = out / 'screenshot.png'
    if ss.exists():
        rec['screenshot_sha256'] = sha256(ss)
        rec['pixels'] = pixel_metrics(ss)
    vt = out / 'view_tree.json'
    if vt.exists():
        try:
            v = json.load(open(vt))
            rec['view_count'] = v.get('view_count')
            rec['content_root_id'] = v.get('content_root_id')
            rec['top_classes'] = [n.get('class') for n in (v.get('nodes') or [])[:8]]
        except Exception as e:
            rec['view_err'] = str(e)
    ts = out / 'trace_summary.json'
    if ts.exists():
        try:
            t = json.load(open(ts))
            fa = t.get('frame_analysis') or {}
            rec['frame'] = {
                'verdict': fa.get('verdict'),
                'first_missing_stage': fa.get('first_missing_stage'),
                'renderer_family': t.get('renderer_family'),
                'lifecycle_final': t.get('lifecycle'),
                'app_draw_ops': fa.get('app_draw_ops'),
                'app_owned_pixels': fa.get('app_owned_pixels'),
                'auth_root_valid': fa.get('auth_root_valid'),
                'measure_ran': fa.get('measure_ran'),
                'layout_ran': fa.get('layout_ran'),
                'draw_walk_ran': fa.get('draw_walk_ran'),
                'inflation_failed': fa.get('inflation_failed'),
                'render_exception': fa.get('render_exception'),
                'nodes_visited': fa.get('nodes_visited'),
                'window_background_px': fa.get('window_background_px'),
                'dominant_color': fa.get('dominant_color'),
                'dominant_pct': fa.get('dominant_pct'),
            }
            rec['trace_first_divergence'] = t.get('first_divergence')
            rec['trace_last_exception'] = (t.get('last_exception') or '')[:200]
        except Exception as e:
            rec['trace_err'] = str(e)
    cl = out / 'crash.log'
    if cl.exists() and cl.stat().st_size > 60:
        lines = [l for l in cl.read_text(errors='replace').splitlines()
                 if l.startswith('Message:')]
        rec['crash_first'] = lines[0][:220] if lines else None
        rec['crash_count'] = len(lines)
    lt = out / 'lifecycle_trace.json'
    if lt.exists():
        try:
            ltj = json.load(open(lt))
            rec['lifecycle_final_state'] = ltj.get('final_state')
            rec['lifecycle_transitions'] = len(ltj.get('transitions') or [])
        except Exception:
            pass
    fi = out / 'file_io.jsonl'
    if fi.exists():
        ops = {}
        try:
            for line in fi.read_text().splitlines():
                if line.strip():
                    o = json.loads(line).get('op')
                    ops[o] = ops.get(o, 0) + 1
        except Exception:
            pass
        rec['file_io_ops'] = ops

def run_app(name, pkg, apk, family, role, three_run, state):
    print(f'[{role}] {name} {pkg}')
    rec = state.setdefault(name, {'name': name, 'package': pkg,
                                  'family': family, 'role': role})
    src = stage_apk(apk)
    rec['source_apk'] = str(src)
    rec['source_sha256'] = sha256(src)
    rec['source_bytes'] = src.stat().st_size
    store = WORK / 'stores' / f'store_{name}'
    if store.exists():
        shutil.rmtree(store)
    store.mkdir(parents=True)
    ip = subprocess.run([str(BIN), 'install', str(src), '--data-root', str(store)],
                        capture_output=True, text=True, timeout=RUN_CAP)
    rec['install_rc'] = ip.returncode
    if ip.returncode != 0:
        rec['verdict'] = 'INSTALL_FAIL'
        rec['install_err'] = (ip.stdout + ip.stderr)[-300:]
        return False
    installed = store / 'data/app' / pkg / 'base.apk'
    rec['install_path'] = str(installed)
    rec['installed_sha256'] = sha256(installed)
    rec['sha_match'] = rec['installed_sha256'] == rec['source_sha256']
    pa = subprocess.run([str(BIN), 'pkgaudit', '--package', pkg,
                         '--data-root', str(store)],
                        capture_output=True, text=True, timeout=120)
    try:
        pj = json.loads(pa.stdout)
        rec['pkgaudit_live_sha'] = pj.get('liveBaseApkSha256')
        rec['main_activity'] = (pj.get('record') or {}).get('mainActivity')
    except Exception:
        rec['pkgaudit_raw'] = (pa.stdout + pa.stderr)[-200:]
    rec['source_hidden_to'] = hide_source(src, name)
    rec['source_hidden'] = True

    runs = [1, 2, 3] if three_run else [1]
    for r in runs:
        out = FIN / f'{name}_{pkg}' / f'run{r}'
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        cmd = [str(BIN), 'run', '--package', pkg, '--data-root', str(store),
               '--dump-view-tree', '--trace', '--max-seconds', '110',
               '-o', str(out)]
        env = dict(os.environ, MINIANDROID_FILE_IO=str(out / 'file_io.jsonl'))
        t0 = time.time()
        try:
            with open(out / 'run.log', 'w') as f:
                rp = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                                    env=env, timeout=RUN_CAP)
            rc = rp.returncode
        except subprocess.TimeoutExpired:
            rc = 'TIMEOUT'
        rr = {'run_rc': rc, 'wall_s': round(time.time() - t0, 1)}
        collect_run(out, rr)
        rec[f'run{r}'] = rr
        shas = [rec.get(f'run{i}', {}).get('screenshot_sha256') for i in runs if i <= r]
        print(f"  run{r}: rc={rc} sha={str(rr.get('screenshot_sha256'))[:16]} "
              f"pix={str((rr.get('pixels') or {}).get('pixclass'))[:22]} "
              f"views={rr.get('view_count')} "
              f"verdict={str((rr.get('frame') or {}).get('verdict'))[:24]}")
    rr1 = rec['run1']
    shaset = {rec.get(f'run{i}', {}).get('screenshot_sha256') for i in runs}
    rec['three_run_reproducible'] = (len(shaset) == 1) if three_run else None
    rec['verdict'] = (rr1.get('pixels') or {}).get('pixclass')
    STATE.write_text(json.dumps(state, indent=1))
    return True

def main():
    only = sys.argv[1:] or None
    state = json.load(open(STATE)) if STATE.exists() else {}
    for name, pkg, apk, family, role, three in APPS:
        if only and name not in only:
            continue
        if state.get(name, {}).get('run1') and not only:
            print(f'[skip] {name}')
            continue
        try:
            run_app(name, pkg, apk, family, role, three, state)
        except Exception as e:
            print(f'  ERR {name}: {e}')
            state.setdefault(name, {})['pipeline_error'] = str(e)
        STATE.write_text(json.dumps(state, indent=1))
    print('\n=== FINAL SUMMARY ===')
    for name, *_ in APPS:
        r = state.get(name)
        if not r:
            continue
        r1 = r.get('run1', {})
        print(f"{name:14s} {r['role']:8s} sha_match={r.get('sha_match')} "
              f"sha={str(r1.get('screenshot_sha256'))[:16]} "
              f"pix={str((r1.get('pixels') or {}).get('pixclass'))[:20]} "
              f"views={r1.get('view_count')} "
              f"3run={r.get('three_run_reproducible')}")

if __name__ == '__main__':
    main()
