#!/usr/bin/env python3
"""DIFFERENTIAL-366 — Stage A: screen the S115 white-candidate population on
CURRENT HEAD (installed-identity mode), then finalize the 5 WHITE selections.

Law (issue #366): white candidates must be genuinely white/near-blank on
CURRENT HEAD; corrupt-fetch and PARTIAL-only faces are not eligible.
Every candidate runs through the SAME installed pipeline as the working apps:
install -> identity SHAs -> pkgaudit -> hide source -> run --package.
"""
import hashlib, json, math, os, shutil, subprocess, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
WORK = BASE / 'run/diff366'
APKDIR = BASE / 'tmp/diff366_apks'
HIDDEN = WORK / 'hidden_sources'
EVID = BASE / 'evidence/diff366/screen'
WORK.mkdir(parents=True, exist_ok=True)
HIDDEN.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)
STATE = WORK / 'screen_state.json'
RUN_CAP = 150

CANDIDATES = [
    ('t202', 'org.fossify.clock',            'F1-empty-viewtree'),
    ('t122', 'com.sidhant.triplematch',      'F1-empty-viewtree'),
    ('t148', 'com.forrestguice.suntimeswidget', 'F1-empty-viewtree'),
    ('t64',  'com.galaxyrio.sudokusolver',   'F2-empty-viewtree-rc1'),
    ('t88',  'com.fairytrick.fairymahjong',  'F2-empty-viewtree-rc1'),
    ('t109', 'com.game.asteroids_revenge',   'F3-libgdx-jni'),
    ('t75',  'com.yepgoryo.EggReturnsHome',  'F3-libgdx-jni'),
    ('t86',  'com.sidhant.blockblast',       'F4-lifecycleregistry'),
    ('t96',  'fr.arnaudguyon.spacevertex',   'F5-fragmentmanager'),
    ('t67',  'com.sanskritbasics.memory',    'F6-multidex'),
    ('t218', 'com.fpf.smartscan',            'F7-viewtree-owner'),
    ('t222', 'com.google.android.stardroid', 'F-other'),
]

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def pixel_metrics(png):
    """PNG decode without PIL — use screenshot.ppm when present (raw RGB)."""
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB')
    except Exception:
        return {'error': 'no-decoder'}
    w, h = im.size
    px = im.resize((min(w, 270), min(h, 480))).getdata()
    total = len(px)
    colors = {}
    for p in px:
        colors[p] = colors.get(p, 0) + 1
    bg = max(colors.values())
    nonbg = total - bg
    ent = -sum((c / total) * math.log2(c / total) for c in colors.values())
    m = {'width': w, 'height': h, 'unique_colors': len(colors),
         'dominant_ratio': round(bg / total, 4),
         'nonbg_ratio': round(nonbg / total, 4), 'entropy': round(ent, 3)}
    if m['nonbg_ratio'] >= 0.02 and m['unique_colors'] >= 64:
        m['pixclass'] = 'NONBLANK'
    elif m['nonbg_ratio'] >= 0.002 or m['unique_colors'] >= 24:
        m['pixclass'] = 'MARGINAL'
    else:
        m['pixclass'] = 'BLANK'
    return m

def get_candidate_apk(key, pkg):
    """APK from tmp/diff366_apks (already fetched)."""
    man = json.load(open(APKDIR / 'manifest.json'))
    rec = man.get(f'{key}_{pkg}', {})
    fn = rec.get('file')
    return (APKDIR / fn) if fn else None

def run_one(key, pkg, family):
    rec = {'key': key, 'package': pkg, 'family': family}
    apk = get_candidate_apk(key, pkg)
    if not apk or not apk.exists():
        rec.update(verdict='APK_UNAVAILABLE')
        return rec
    rec['source_sha256'] = sha256(apk)
    rec['source_bytes'] = apk.stat().st_size
    store = WORK / f'stores/store_{key}'
    if store.exists():
        shutil.rmtree(store)
    store.mkdir(parents=True)
    out = EVID / f'{key}_{pkg}'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    # install
    ip = subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                        capture_output=True, text=True, timeout=RUN_CAP)
    rec['install_rc'] = ip.returncode
    if ip.returncode != 0:
        rec.update(verdict='INSTALL_FAIL',
                   install_err=(ip.stdout + ip.stderr)[-400:])
        return rec
    installed = store / 'data/app' / pkg / 'base.apk'
    if not installed.exists():
        rec.update(verdict='INSTALL_NO_BASEAPK')
        return rec
    rec['installed_sha256'] = sha256(installed)
    rec['sha_match'] = rec['installed_sha256'] == rec['source_sha256']
    # pkgaudit
    pa = subprocess.run([str(BIN), 'pkgaudit', '--package', pkg,
                         '--data-root', str(store)],
                        capture_output=True, text=True, timeout=120)
    try:
        rec['pkgaudit'] = json.loads(pa.stdout)
    except Exception:
        rec['pkgaudit_raw'] = (pa.stdout + pa.stderr)[-300:]
    # hide source (out of the runtime's reachable tree)
    hid = HIDDEN / apk.name
    if hid.exists():
        hid.unlink()
    shutil.move(str(apk), str(hid))
    rec['source_hidden'] = str(hid)
    # run installed-identity mode
    cmd = [str(BIN), 'run', '--package', pkg, '--data-root', str(store),
           '--dump-view-tree', '--trace', '--max-seconds', '100',
           '-o', str(out)]
    env = dict(os.environ, MINIANDROID_FILE_IO=str(out / 'file_io.jsonl'))
    try:
        with open(out / 'run.log', 'w') as f:
            rp = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                                env=env, timeout=RUN_CAP)
        rec['run_rc'] = rp.returncode
    except subprocess.TimeoutExpired:
        rec['run_rc'] = 'TIMEOUT'
    # collect
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
        except Exception as e:
            rec['view_count_err'] = str(e)
    ts = out / 'trace_summary.json'
    if ts.exists():
        try:
            t = json.load(open(ts))
            fa = t.get('frame_analysis') or {}
            rec['trace'] = {
                'first_divergence': t.get('first_divergence'),
                'renderer_family': t.get('renderer_family'),
                'lifecycle': t.get('lifecycle'),
                'app_draw_ops': fa.get('app_draw_ops'),
                'app_owned_pixels': fa.get('app_owned_pixels'),
                'auth_root_valid': fa.get('auth_root_valid'),
                'last_exception': (t.get('last_exception') or '')[:160],
            }
        except Exception as e:
            rec['trace_err'] = str(e)
    cl = out / 'crash.log'
    if cl.exists() and cl.stat().st_size > 60:
        txt = cl.read_text(errors='replace')
        errs = [l for l in txt.splitlines() if l.startswith('Message:')][:3]
        rec['crash_first'] = ' | '.join(errs)[:300]
    # verdict: pixel class first, trace as tiebreak
    pc = (rec.get('pixels') or {}).get('pixclass', 'NO_SHOT')
    rec['verdict'] = pc
    return rec

def main():
    only = sys.argv[1:] or None
    state = json.load(open(STATE)) if STATE.exists() else {}
    for key, pkg, family in CANDIDATES:
        if only and key not in only and pkg not in only:
            continue
        if state.get(key, {}).get('verdict') and not only:
            print(f"[skip] {key} {pkg} -> {state[key]['verdict']}")
            continue
        print(f'[screen] {key} {pkg} ({family})')
        r = run_one(key, pkg, family)
        state[key] = r
        STATE.write_text(json.dumps(state, indent=1))
        px = r.get('pixels') or {}
        print(f"  -> {r['verdict']}  colors={px.get('unique_colors')} "
              f"nonbg={px.get('nonbg_ratio')} views={r.get('view_count')} "
              f"div={str((r.get('trace') or {}).get('first_divergence'))[:60]} "
              f"drawops={(r.get('trace') or {}).get('app_draw_ops')}")
    STATE.write_text(json.dumps(state, indent=1))
    print('\n=== SCREEN SUMMARY (CURRENT HEAD) ===')
    for k, v in sorted(state.items()):
        print(f"{k} {v['package']:42s} {v['verdict']:10s} "
              f"views={v.get('view_count')} sha_match={v.get('sha_match')}")

if __name__ == '__main__':
    main()
