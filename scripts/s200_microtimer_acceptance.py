#!/usr/bin/env python3
"""S200 P0 Target A — microtimer (dubrowgn.microtimer) ACCEPTANCE TEST.

Written BEFORE any runtime change (S200 directive step 4). Declared core
feature (from upstream source, MainActivity.kt):
  1. keypad duration entry (digits/00/backspace/clear) -> lblInput label
  2. START -> Room/SQLite INSERT + TimerControl row added to layoutAlarms
  3. countdown ticks via Handler.postDelayed -> row label decreases
  4. per-row PAUSE / RESUME -> SQLite UPDATE + button swap
  5. per-row DELETE -> row removed + SQLite DELETE
  6. app restart -> loadAlarms restores rows from SQLite (persistence)

Gates S200 §4.1 A–M. Phases:
  probe    : fresh store, taps '1'@4 '0'@6 START@8, 14 frames — proves the
             createTimer path works and pins the TimerControl row geometry
             from the real view-tree dump (no guessed coordinates for rows)
  full     : fresh store, entry + start + pause@geom + resume@geom,
             34 frames — gates E/F/G/H
  persist  : SAME store as full, zero taps, 10 frames — gate I (SQLite)
  repeat   : full ×3 fresh stores — gate L (three clean independent runs)

Usage: s200_microtimer_acceptance.py <phase> [tag]
  phases: probe | full | persist | repeat | all
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/canonical_apks/dubrowgn.microtimer_8.apk'
OUT = BASE / 'evidence/s200'
RUNS = OUT / 'runs'

BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()
APK_SHA = hashlib.sha256(APK.read_bytes()).hexdigest()

# keypad geometry from the S200 boot-probe view tree (1080x1920, all ids
# verified: 2131034154='1' 2131034152='0' 2131034165=btnStart)
TAP_1 = (184, 1178, 2131034154)
TAP_0 = (539, 1808, 2131034152)
TAP_START = (895, 1808, 2131034165)
PKG = 'dubrowgn.microtimer'


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def install(store):
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), 'install', str(APK),
                        '--data-root', str(store)],
                       capture_output=True, timeout=300)
    return r.returncode


def run_frames(store, tag, frames, taps, dump_tree=True, delay=250):
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', PKG, '--frames', str(frames),
           '--frame-delay', str(delay), '--trace']
    for (x, y, fr) in taps:
        cmd += ['--tap', f'{x},{y}@{fr}']
    if dump_tree:
        cmd += ['--dump-view-tree']
    console = RUNS / f'{tag}.console.log'
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=frames * 2 + 300)
    wall = round(time.time() - t0, 1)
    return rundir, console, wall


def analyze(tag, rundir, console, taps_expected, row_geom=None):
    log = console.read_text(errors='ignore') if console.exists() else ''
    res = {'tag': tag, 'binary_sha16': BIN_SHA[:16], 'apk_sha16': APK_SHA[:16]}
    res['uncaught'] = len(re.findall(
        r'FATAL|uncaught exception|Uncaught exception', log))
    res['app_boundary'] = len(re.findall(r'APP BOUNDARY unwind', log))
    res['rc_line_errors'] = len(re.findall(r'^Errors: [1-9]', log, re.M))
    # gate E: tap delivery — F117-TAP target ids
    taps = re.findall(r'\[F117-TAP\] frame (\d+) DOWN \((\d+),(\d+)\) target=(\d+)', log)
    res['taps'] = [{'frame': int(f), 'xy': (int(x), int(y)), 'target': int(t)}
                   for f, x, y, t in taps]
    res['tap_targets_expected'] = taps_expected
    res['tap_targets_actual'] = [t['target'] for t in res['taps']]
    # frames present
    fr = sorted((rundir / 'frames').glob('frame_*.png')) if (rundir / 'frames').exists() else []
    res['frames_n'] = len(fr)
    res['frame_paths'] = [str(p) for p in fr]
    # view tree
    vt = rundir / 'view_tree.json'
    if vt.exists():
        d = json.loads(vt.read_text())
        res['view_count'] = d.get('view_count')
        res['row_geom'] = row_geom or find_timer_row(d)
    return res


def find_timer_row(vt):
    """Locate the TimerControl row via its RoTimeControl child INSIDE the
    ScrollView (y < 900; the input-row RoTimeControl sits at y=937).
    Row class is R8-minified (Lk/g;) so match structurally, not by name.
    Returns row info + child frames; tap targets use object_id (the ids
    the F117-TAP trace reports)."""
    nodes = {n['object_id']: n for n in vt['nodes']}
    rows = []
    for n in vt['nodes']:
        if 'RoTimeControl' not in n['class']:
            continue
        if (n.get('y') or 0) >= 900:   # input-row label, not a timer row
            continue
        row = nodes.get(n.get('parent_id'))
        if not row:
            continue
        kids = row.get('children', [])
        rows.append({
            'row_obj': row['object_id'],
            'row': {'x': row.get('x'), 'y': row.get('y'),
                    'w': row.get('width'), 'h': row.get('height')},
            'label_text': next((nodes[tk].get('text')
                                for tk in (n.get('children') or [])
                                if 'TextView' in nodes[tk]['class']), None),
            'children': [{'cls': nodes[k]['class'].split('/')[-1].rstrip(';'),
                          'obj': k,
                          'android_id': nodes[k].get('android_view_id'),
                          'text': nodes[k].get('text', ''),
                          'x': nodes[k].get('x'), 'y': nodes[k].get('y'),
                          'w': nodes[k].get('width'),
                          'h': nodes[k].get('height')}
                         for k in kids],
            'clickable_objs': [k for k in kids if nodes[k].get('has_click_listener')],
        })
    return rows


# ── pixel analysis ──────────────────────────────────────────────────────
def region_sig(png, box):
    from PIL import Image
    im = Image.open(png).convert('RGB').crop(box)
    cols = im.getcolors(200000) or []
    cols.sort(reverse=True)
    return {'n_colors': len(cols),
            'top': [c[1] for c in cols[:4]],
            'nonbg_px': sum(cnt for cnt, c in cols
                            if cnt < len(cols[0][0] * 0)) or sum(1 for cnt, c in cols if cnt < 3000)}


def pixels_changed(png_a, png_b, box, thresh=200):
    from PIL import Image, ImageChops
    a = Image.open(png_a).convert('L').crop(box)
    b = Image.open(png_b).convert('L').crop(box)
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    hist = diff.histogram()
    changed = sum(hist[30:])
    return {'changed_px': changed, 'bbox': bbox,
            'changed': changed > thresh}


PHASE = sys.argv[1] if len(sys.argv) > 1 else 'probe'
TAG = sys.argv[2] if len(sys.argv) > 2 else None
OUT.mkdir(parents=True, exist_ok=True)
RUNS.mkdir(parents=True, exist_ok=True)
REPORT = OUT / 'MICROTIMER_ACCEPTANCE.json'
report = json.loads(REPORT.read_text()) if REPORT.exists() else {}

if PHASE == 'probe':
    tag = TAG or 'mtm_probe_r1'
    store = RUNS / f'store_{tag}'
    shutil.rmtree(store, ignore_errors=True)
    rc = install(store)
    taps = [(184, 1178, 4), (539, 1808, 6), (895, 1808, 8)]
    rundir, console, wall = run_frames(store, tag, 14, taps)
    res = analyze(tag, rundir, console, [2131034154, 2131034152, 2131034165])
    res['wall_s'] = wall
    res['install_rc'] = rc
    # input-row label region: [126,937 538x123] from boot viewtree
    # label shows "00:00:10" between tap1/tap2 and START clears it again
    fr = rundir / 'frames'
    if (fr / 'frame_007.png').exists() and (fr / 'frame_003.png').exists():
        res['label_after_digits'] = pixels_changed(
            fr / 'frame_003.png', fr / 'frame_007.png', (126, 937, 664, 1060))
    # countdown: row region after START — compare frame_010 vs frame_013
    if (fr / 'frame_010.png').exists() and (fr / 'frame_013.png').exists():
        res['countdown_change'] = pixels_changed(
            fr / 'frame_010.png', fr / 'frame_013.png', (0, 0, 1080, 400))
    # gate H partial: row exists?
    res['row_found'] = bool(res.get('row_geom'))
    report['probe'] = res
    print(json.dumps(res, indent=1, default=str)[:3000])

elif PHASE == 'full':
    tag = TAG or 'mtm_full_r1'
    geom = report.get('probe', {}).get('row_geom') or []
    if not geom:
        sys.exit('run probe first — full phase needs the row geometry')
    row = geom[0]
    # clickable children sorted by x: leftmost = delete, rightmost = pause
    kids = sorted(row['children'], key=lambda c: c['x'])
    del_obj = row['clickable_objs'][0]
    pause_obj = row['clickable_objs'][-1]
    pb = [c for c in kids if c['obj'] == pause_obj][0]
    db = [c for c in kids if c['obj'] == del_obj][0]
    px, py = pb['x'] + pb['w'] // 2, pb['y'] + pb['h'] // 2
    dx, dy = db['x'] + db['w'] // 2, db['y'] + db['h'] // 2
    # entry -> start -> run -> PAUSE@16 (freeze) -> RESUME@24 (continue)
    # -> DELETE@31 (row removed + SQLite DELETE)
    taps = [(184, 1178, 4), (539, 1808, 6), (895, 1808, 8),
            (px, py, 16), (px, py, 24), (dx, dy, 31)]
    store = RUNS / f'store_{tag}'
    shutil.rmtree(store, ignore_errors=True)
    install(store)
    rundir, console, wall = run_frames(store, tag, 34, taps)
    res = analyze(tag, rundir, console, [134, 147, 148, pause_obj, pause_obj,
                                         del_obj], row_geom=None)
    res['wall_s'] = wall
    res['pause_tap'] = (px, py)
    res['delete_tap'] = (dx, dy)
    fr = rundir / 'frames'
    ROWBOX = (231, 0, 849, 126)   # countdown label region of the timer row
    if (fr / 'frame_010.png').exists() and (fr / 'frame_014.png').exists():
        res['countdown_running'] = pixels_changed(
            fr / 'frame_010.png', fr / 'frame_014.png', ROWBOX)
    if (fr / 'frame_018.png').exists() and (fr / 'frame_021.png').exists():
        res['countdown_paused'] = pixels_changed(
            fr / 'frame_018.png', fr / 'frame_021.png', ROWBOX)
    if (fr / 'frame_026.png').exists() and (fr / 'frame_030.png').exists():
        res['countdown_resumed'] = pixels_changed(
            fr / 'frame_026.png', fr / 'frame_030.png', ROWBOX)
    # row removed after delete@31: final view tree must have NO timer row
    res['row_after_delete'] = bool(res.get('row_geom'))
    report.setdefault('full', {})[tag] = res
    print(json.dumps(res, indent=1, default=str)[:3000])

elif PHASE == 'persist':
    """Self-contained persistence proof on a FRESH store:
    run A: entry+start (row created, SQLite INSERT), 12 frames
    run B: SAME store, ZERO taps, 10 frames — onCreate->loadAlarms must
           restore the row from the Room/SQLite database."""
    tag = TAG or 'mtm_persist'
    store = RUNS / f'store_{tag}'
    shutil.rmtree(store, ignore_errors=True)
    install(store)
    # run A: create a timer
    rundirA, consA, wallA = run_frames(
        store, tag + '_A', 12,
        [(184, 1178, 4), (539, 1808, 6), (895, 1808, 8)])
    # run B: cold restart, no interaction
    rundirB, consB, wallB = run_frames(store, tag + '_B', 10, [])
    res = analyze(tag + '_B', rundirB, consB, [])
    res['wall_A_s'] = wallA
    res['wall_B_s'] = wallB
    res['restored_row'] = bool(res.get('row_geom'))
    res['restored_label'] = (res.get('row_geom') or [{}])[0].get(
        'label_text') if res.get('row_geom') else None
    # SQLite file evidence + content
    dbs = sorted(set(store.glob('**/databases/*')) | set(store.glob('**/*.db')))
    res['db_files'] = [{'path': str(p.relative_to(store)), 'sha16': sha16(p),
                        'bytes': p.stat().st_size}
                       for p in dbs if p.is_file()]
    import sqlite3 as sq
    for p in dbs:
        if p.is_file() and p.suffix in ('.db', '.sqlite'):
            try:
                con = sq.connect(f'file:{p}?mode=ro', uri=True)
                tables = [r[0] for r in con.execute(
                    "select name from sqlite_master where type='table'")]
                res.setdefault('sqlite_tables', tables)
                if 'alarm' in tables:
                    res['sqlite_rows'] = list(con.execute(
                        'select * from alarm'))
                con.close()
            except Exception as e:
                res.setdefault('sqlite_error', str(e))
    report.setdefault('persist', {})[tag] = res
    print(json.dumps(res, indent=1, default=str)[:3000])

elif PHASE == 'repeat':
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    runs = []
    for i in range(1, n + 1):
        sys.argv = ['x', 'full', f'mtm_full_rep{i}']
        # rerun full logic inline (avoid argv juggling): call itself
        subprocess.run(['python3', __file__, 'full', f'mtm_full_rep{i}'],
                       cwd=str(BASE), check=True)
    report = json.loads(REPORT.read_text())
    fulls = report['full']
    sigs = {}
    for t, r in fulls.items():
        sigs[t] = (r['tap_targets_actual'], r['row_found'],
                   r.get('countdown_running', {}).get('changed', None) if r.get('countdown_running') else None,
                   r.get('countdown_paused', {}).get('changed', None) if r.get('countdown_paused') else None,
                   r.get('countdown_resumed', {}).get('changed', None) if r.get('countdown_resumed') else None)
    report['repeat_signatures'] = sigs
    print(json.dumps(sigs, indent=1, default=str))

REPORT.write_text(json.dumps(report, indent=1, default=str))
print('REPORT ->', REPORT)
