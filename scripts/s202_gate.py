#!/usr/bin/env python3
"""S202 gate — the Coder-3 font-wall patch (F-NEW-625 + F-NEW-612b) applied
on main (base f3499921 line). Battery:
  1. goldens x3 byte-pins (bouncy 8a6c24ac / unote 3b8dcb0a / dooz 31ddd4d5)
  2. gmdice 5-tap x2 rerun-identity
  3. microtimer spot (0 uncaught)
  4. tictactoe x3 boot determinism + the S202 claim face 3ca1db0cf92badc7
     + F-NEW-625 / F-NEW-612b / GDX-HOST law-line capture
"""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path
from PIL import Image

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
RUNS = BASE / 'evidence/s200/runs'
RUNS.mkdir(parents=True, exist_ok=True)
OUT = {'binary_sha16': BIN_SHA}

GOLDENS = [
    ('bouncy', 'com.dozingcatsoftware.bouncy', 'bouncy.apk', '8a6c24ac'),
    ('unote', 'app.varlorg.unote', 'app.varlorg.unote_30.apk', '3b8dcb0a'),
    ('dooz', 'io.github.yamin8000.dooz', 'io.github.yamin8000.dooz_23.apk',
     '31ddd4d5'),
]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_app(apk, tag, taps=None, frames=8, delay=250, trace=False):
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(apk), '--data-root', str(store)],
                   capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--frames', str(frames),
           '--frame-delay', str(delay)]
    if trace:
        cmd += ['--trace']
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=FRAMES_TIMEOUT)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    face_sha = sha16(shot) if shot and shot.exists() else None
    rec = {'wall_s': wall, 'face_sha16': face_sha,
           'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught',
                                      log))}
    if tag.startswith('ttt'):
        rec['law_lines'] = {
            'f625_extracts': re.findall(r'\[F-NEW-625\] install extract.*',
                                        log),
            'gdx_host': re.findall(r'\[GDX-HOST\].*', log)[:4],
            'f612b_restores': len(re.findall(r'\[F-NEW-612b\] restored', log)),
            'f612b_other': re.findall(r'\[F-NEW-612b\].*',
                                      log)[:6] if False else None,
            's2_native': re.findall(r'\[S2-NATIVE\].*', log)[:4],
        }
        if shot and shot.exists():
            face = RUNS / f'face_{tag}.png'
            shutil.copy(shot, face)
            im = Image.open(face).convert('RGB')
            w, h = im.size
            px = im.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
            small = px.resize((240, 240))
            colors = small.getcolors(240 * 240)
            nonwhite = sum(c for c, (r, g, b) in colors
                           if not (r > 245 and g > 245 and b > 245))
            rec['center_unique'] = len(colors)
            rec['center_nonwhite'] = nonwhite
    return rec


FRAMES_TIMEOUT = 900

# 1) goldens x3
golds = {}
for name, pkg, apk, pin in GOLDENS:
    r = run_app(BASE / 'upload/canonical_apks' / apk, f's202_gold_{name}')
    r['pin'] = pin
    r['hold'] = (r['face_sha16'] == pin)
    golds[name] = r
    print(f'golden {name}: {r["face_sha16"]} vs pin {pin} -> '
          f'{"HOLD" if r["hold"] else "BREAK"}', flush=True)
OUT['goldens'] = golds

# 2) gmdice x2
GMDICE_TAPS = [(4, 540, 1200), (6, 540, 1200), (8, 540, 1200),
               (10, 540, 1200), (12, 540, 1200)]
r1 = run_app(BASE / 'upload/canonical_apks/de.duenndns.gmdice_8.apk',
             's202_gmdice_r1', GMDICE_TAPS, frames=16)
r2 = run_app(BASE / 'upload/canonical_apks/de.duenndns.gmdice_8.apk',
             's202_gmdice_r2', GMDICE_TAPS, frames=16)
OUT['gmdice'] = {'r1': r1, 'r2': r2,
                 'rerun_identical': r1['face_sha16'] == r2['face_sha16']}
print(f"gmdice: {r1['face_sha16']} / {r2['face_sha16']}", flush=True)

# 3) microtimer spot
MT_TAPS = [(4, 270, 1200), (6, 540, 1200), (8, 810, 1200), (10, 540, 1400)]
mt = run_app(BASE / 'upload/canonical_apks/dubrowgn.microtimer_8.apk',
             's202_mtm_spot', MT_TAPS, frames=14)
OUT['microtimer'] = mt
print(f"microtimer: uncaught={mt['uncaught']} face={mt['face_sha16']}",
      flush=True)

# 4) tictactoe x3 boot determinism
TTT_CLAIM = '3ca1db0cf92badc7'
t3 = []
for i in (1, 2, 3):
    r = run_app(BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk',
                f's202_ttt_boot{i}', frames=40, delay=250, trace=True)
    t3.append(r)
    print(f"ttt boot{i}: face={r['face_sha16']} uncaught={r['uncaught']} "
          f"nonwhite={r.get('center_nonwhite')}", flush=True)
OUT['tictactoe'] = {
    'runs': t3, 'claim_face': TTT_CLAIM,
    'deterministic_x3': len({r['face_sha16'] for r in t3}) == 1,
    'matches_claim': t3[0]['face_sha16'] == TTT_CLAIM,
    'moved_off_frozen': t3[0]['face_sha16'] != 'fc0997a63f3b2dec',
}

OUT['all_hold'] = (all(g['hold'] for g in golds.values())
                   and OUT['gmdice']['rerun_identical']
                   and mt['uncaught'] == 0)
(BASE / 'evidence/s200/S202_GATE.json').write_text(json.dumps(OUT, indent=1))
print('GOLDENS+GMDICE+MT ALL_HOLD =', OUT['all_hold'])
print('TTT deterministic_x3 =', OUT['tictactoe']['deterministic_x3'],
      '| matches_claim =', OUT['tictactoe']['matches_claim'],
      '| moved_off_frozen =', OUT['tictactoe']['moved_off_frozen'])
