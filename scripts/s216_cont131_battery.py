#!/usr/bin/env python3
"""S216 cont131 POST battery on the integration line (the receipt flow):
 1. golden x3   - default-geometry no-tap dooz, expect a0fae907 byte-exact x3
                  + [VSYNC-KEEPALIVE] ticks>0, choreo rows, byte-inert.
 2. tap x2      - the #573 recipe (765,1830)@6 + (540,960)@10, 16 frames;
                  expect the POST chain (a0fae907x6 -> 29e39938 -> 85b05db9x2
                  -> 47d241aex7), [AWAIT-UP-GATE-SOFT]=1, 0 hard/0 backstop,
                  poison=0, [F-NEW-298-KEEP]>0.
 3. oob trace   - tap run + the S211 aput-oob frame-locals dump env armed
                  -> capture v-registers at the Lbw0;.a OOB instant
                  (CONT-132 forensics: the c-mask value at the wild aput).
Every console log kept in evidence/s216/cont131/ for the lane receipt.
"""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s216/cont131'
RUNS.mkdir(parents=True, exist_ok=True)
APK = list((BASE / 'upload/canonical_apks').glob('io.github.yamin8000.dooz*.apk'))[0]
OUT = {'binary_sha16': hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_dooz(tag, taps=None, frames=16, delay=250, extra_env=None, timeout=1100,
             reuse_store=False):
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    already = ((store / 'data' / 'app').exists()
               and any((store / 'data' / 'app').iterdir()))
    if not (reuse_store and already):
        subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
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
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    env = dict(__import__('os').environ)
    env.update(extra_env or {})
    t0 = time.time()
    try:
        with open(console, 'wb') as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           cwd=str(BASE), timeout=timeout, env=env)
        rc = 0
    except subprocess.TimeoutExpired:
        rc = 124
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    faces = {}
    if rundir.exists():
        for p in sorted(rundir.glob('**/*.png')):
            faces[p.name] = sha16(p)
    rec = {
        'rc': rc, 'wall_s': wall,
        'final_face_sha16': sha16(rundir / 'screenshot.png')
        if (rundir / 'screenshot.png').exists() else None,
        'faces': faces,
        'uncaught': len(re.findall(r'uncaught exception|FATAL', log)),
        'gate_soft': len(re.findall(r'AWAIT-UP-GATE-SOFT', log)),
        'gate_hard': len(re.findall(r'AWAIT-UP-GATE. scoped render window', log)),
        'gate_hard_backstop': len(re.findall(r'HALT\(hard\)|VirtualMachineError', log)),
        'poison_throws': len(re.findall(r'could not provide TextLayoutResult', log)),
        'vsync_ticks': len(re.findall(r'\[VSYNC-KEEPALIVE\]', log)),
        'keep_rows': len(re.findall(r'\[F-NEW-298-KEEP\]', log)),
        'clock_arms': len(re.findall(r'\[F-NEW-277-CLOCK\]', log)),
        'aput_oob': len(re.findall(r'aput-oob', log)),
        'oob_dumps': len(re.findall(r'dump_frame_locals_diag|OOB-LOCALS', log)),
        'newgame_clicked': len(re.findall(r'onNewGameClicked', log)),
        'onClick': len(re.findall(r'onClick', log)),
        'dice_hits': len(re.findall(r'\U0001F3B2', log)),
        'parent_cancel': len(re.findall(r'Parent job is Cancelling', log)),
        'events': log.count('[UI-EVENT]'),
        'up_dispatched': len(re.findall(r'action=1 result=DISPATCHED', log)),
        'down_dispatched': len(re.findall(r'action=0 result=DISPATCHED', log)),
        'choreo': len(re.findall(r'doFrame', log)),
    }
    (RUNS / f'{tag}.rec.json').write_text(json.dumps(rec, indent=1))
    return rec, log


def main(stage):
    if stage == 'golden':
        faces = []
        for i in (1, 2, 3):
            r, _ = run_dooz(f'g{i}', frames=5)
            faces.append(r['final_face_sha16'])
            print(f"golden r{i}: {r['final_face_sha16']} soft={r['gate_soft']} "
                  f"hard={r['gate_hard']} vsync={r['vsync_ticks']} "
                  f"choreo={r['choreo']} wall={r['wall_s']}s", flush=True)
        OUT['golden'] = faces
        OUT['golden_hold'] = all(f and f.startswith('a0fae907') for f in faces)
        print(f"GOLDEN: {faces} hold={OUT['golden_hold']}", flush=True)
    elif stage == 'tap':
        taps = [(6, 765, 1830), (10, 540, 960)]
        for i in (1, 2):
            r, log = run_dooz(f'tap{i}', taps=taps, reuse_store=True)
            OUT[f'tap{i}'] = {k: v for k, v in r.items() if k != 'faces'}
            uniq = list(dict.fromkeys(r['faces'].values()))
            print(f"tap{i}: chain={uniq} soft={r['gate_soft']} hard={r['gate_hard']} "
                  f"poison={r['poison_throws']} uncaught={r['uncaught']} "
                  f"vsync={r['vsync_ticks']} keep={r['keep_rows']} "
                  f"oob={r['aput_oob']} onClick={r['onClick']} "
                  f"cancel={r['parent_cancel']} wall={r['wall_s']}s", flush=True)
    elif stage == 'trace':
        taps = [(6, 765, 1830), (10, 540, 960)]
        env = {'MINIANDROID_LOOP_LOCALS_DIAG': '1'}
        r, log = run_dooz('taptrace', taps=taps, frames=10, extra_env=env)
        OUT['trace'] = {k: v for k, v in r.items() if k != 'faces'}
        # extract the OOB dump lines
        dumps = [ln for ln in log.splitlines()
                 if ('dump_frame_locals_diag' in ln or 'OOB-LOCALS' in ln
                     or 'aput-oob' in ln)]
        (RUNS / 'taptrace.oob_lines.txt').write_text('\n'.join(dumps[-80:]))
        print(f"trace: oob={r['aput_oob']} dumps={r['oob_dumps']} "
              f"onClick={r['onClick']} cancel={r['parent_cancel']} "
              f"wall={r['wall_s']}s", flush=True)
    json.dump(OUT, open(RUNS / 'cont131_battery.json', 'w'), indent=1)


if __name__ == '__main__':
    main(__import__('sys').argv[1] if len(__import__('sys').argv) > 1 else 'golden')
