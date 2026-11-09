#!/usr/bin/env python3
"""S204 — tictactoe route probe on the canonical binary: where does the
board/DrawElements route stop? GL_DEBUG trace + typed-view census + dex-side
route classes."""
import json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s204/runs'
RUNS.mkdir(parents=True, exist_ok=True)
APK = BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
OUT = {}


def sha16(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16] if Path(p).exists() else None


def run(tag, frames, delay=250, taps=None, env_extra=None):
    store = RUNS / f'store_{tag}'
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
                   capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    dpkg = sorted([d.name for d in apps.iterdir()
                   if d.is_dir() and not d.name.startswith('.')])[0]
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f'{tag}.console.log'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--package', dpkg, '--frames', str(frames),
           '--frame-delay', str(delay)]
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    env = {'MINIANDROID_GL_DEBUG': '1'}
    if env_extra:
        env.update(env_extra)
    t0 = time.time()
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=900, env=env)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    rec = {
        'wall_s': round(time.time() - t0, 1),
        'face_sha16': sha16(shot),
        'uncaught': len(re.findall(r'uncaught exception|FATAL', log)),
        'draw_modes': {},
        'dele': len(re.findall(r'\[GLDBG\] DELE', log)),
        'dele_samples': re.findall(r'\[GLDBG\] DELE[^\n]*', log)[:4],
        'draw_samples': re.findall(r'\[GLDBG\] DRAW[^\n]*', log)[:14],
        'f626_seen': sorted(set(re.findall(r'\[F-NEW-626-SEEN\][^\n]*', log)))[:12],
        'f626_hits': len(re.findall(r'\[F-NEW-626\]', log)),
        'vbo_dump': re.findall(r'\[F-NEW-626e\] vertex dump[^\n]*', log)[:2],
        'taskFailed_tail': re.findall(r'taskFailed[^\n]*', log)[-4:],
        'synth_exc': re.findall(r'\[SYNTH|synthetic[^\n]*exc[^\n]*', log)[-3:],
    }
    for m in re.findall(r'\[GLDBG\] DRAW mode=(\d+) count=(\d+)', log):
        key = f"mode{m[0]} count{m[1]}"
        rec['draw_modes'][key] = rec['draw_modes'].get(key, 0) + 1
    return rec, log


r, log = run('s204_ttt_gl', frames=40)
OUT['ttt_gl'] = r
print(json.dumps(r, indent=1)[:3000])
(RUNS / 'S204_PROBE.json').write_text(json.dumps(OUT, indent=1))
