#!/usr/bin/env python3
"""S216 dooz probe — the full-run battery on the soft-stop binary.
Steps:
  1. no-tap golden  -> expect a0fae907 HOLD (the soft-stop law is byte-inert)
  2. tap run x2     -> New game (875,1823) pressed at frames 1 and 3, frames=16
     capture: per-frame faces, AWAIT-UP-GATE SOFT/HARD lines, poison throws
     (MultiParagraphLayoutCache / TextLayoutResult), dice corpus, board markers
  3. traced tap run -> MINIANDROID_T67_LABEL_TRACE + T68 + PTE for the
     CONT-131 resumption decode
All console logs land in evidence/s216/ for the coder-lane reconciliation.
"""
import hashlib, json, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s216/runs'
RUNS.mkdir(parents=True, exist_ok=True)
APK = list((BASE / 'upload/canonical_apks').glob('io.github.yamin8000.dooz*.apk'))[0]
OUT = {'binary_sha16': hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_dooz(tag, taps=None, frames=8, delay=250, extra_env=None):
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
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
    env = dict(**{k: v for k, v in __import__('os').environ.items()})
    env.update(extra_env or {})
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=1200, env=env)
    wall = round(time.time() - t0, 1)
    log = console.read_text(errors='ignore')
    faces = {}
    if rundir.exists():
        for p in sorted(rundir.glob('**/*.png')):
            faces[p.name] = sha16(p)
    rec = {
        'wall_s': wall,
        'final_face_sha16': sha16(rundir / 'screenshot.png')
        if (rundir / 'screenshot.png').exists() else None,
        'faces': faces,
        'uncaught': len(re.findall(r'uncaught exception|FATAL', log)),
        'gate_soft': len(re.findall(r'SOFT draw-window stop', log)),
        'gate_hard': len(re.findall(r'AWAIT-UP-GATE. scoped render window', log)),
        'gate_hard_backstop': len(re.findall(r'HALT\(hard\)|VirtualMachineError', log)),
        'poison_throws': len(re.findall(r'could not provide TextLayoutResult', log)),
        'density_poison': len(re.findall(r'density=0\.000000', log)),
        'pte_dispatch': len(re.findall(r'PTE-DISPATCH', log)),
        't67_entries': len(re.findall(r'T67-ENTRY', log)),
        't68_entries': len(re.findall(r'T68-ENTRY', log)),
        'dice_hits': len(re.findall(r'🎲', log)),
        'newgame_clicked': len(re.findall(r'onNewGameClicked', log)),
        'events': log.count('[UI-EVENT]'),
        'up_dispatched': len(re.findall(r'action=1 result=DISPATCHED', log)),
        'down_dispatched': len(re.findall(r'action=0 result=DISPATCHED', log)),
    }
    (RUNS / f'{tag}.rec.json').write_text(json.dumps(rec, indent=1))
    return rec, log


PIN = 'a0fae907'


def main(stage):
    if stage == 'gold':
        g, glog = run_dooz('s216_gold_dooz')
        g['pin'] = PIN
        g['hold'] = bool(g['final_face_sha16'] and
                         g['final_face_sha16'].startswith(PIN))
        json.dump({'golden': g}, open(RUNS / 'S216_GOLD_ONLY.json', 'w'),
                  indent=1)
        print(f"golden: {g['final_face_sha16']} vs {PIN} -> "
              f"{'HOLD' if g['hold'] else 'BREAK'} soft={g['gate_soft']} "
              f"hard={g['gate_hard']} poison={g['poison_throws']} "
              f"uncaught={g['uncaught']} wall={g['wall_s']}s", flush=True)
    elif stage == 'tap':
        taps = [(1, 875, 1823), (3, 875, 1823)]
        r, log = run_dooz('s216_tap1', taps=taps, frames=16)
        json.dump({'tap1': r}, open(RUNS / 'S216_TAP1.json', 'w'), indent=1)
        print(f"tap1: soft={r['gate_soft']} hard={r['gate_hard']} "
              f"poison={r['poison_throws']} uncaught={r['uncaught']} "
              f"down={r['down_dispatched']} up={r['up_dispatched']} "
              f"newgame={r['newgame_clicked']} dice={r['dice_hits']} "
              f"wall={r['wall_s']}s", flush=True)
        uniq = sorted(set(r['faces'].values()))
        print(f"faces: {len(r['faces'])} pngs unique={uniq}", flush=True)
    elif stage == 'trace':
        taps = [(1, 875, 1823), (3, 875, 1823)]
        r, log = run_dooz('s216_tap_trace', taps=taps, frames=6,
                          extra_env={'MINIANDROID_T67_LABEL_TRACE': '1',
                                     'MINIANDROID_T68_NODE_TRACE': '1',
                                     'MINIANDROID_PTE_TRACE': '1'})
        json.dump({k: v for k, v in r.items() if k != 'faces'},
                  open(RUNS / 'S216_TRACE.json', 'w'), indent=1)
        print(f"trace: t67={r['t67_entries']} t68={r['t68_entries']} "
              f"pte={r['pte_dispatch']} soft={r['gate_soft']} "
              f"down={r['down_dispatched']} up={r['up_dispatched']} "
              f"newgame={r['newgame_clicked']}", flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'gold')
