#!/usr/bin/env python3
"""S202 supplemental probes:
  P1: dooz pin invocation (--max-seconds 40 --frames 5) -> EXACT 31ddd4d5b8e6d18e
  P2: force F-NEW-625 leg (b): install, then DELETE the sibling .so files
      (the S200 broken state), then run -> 625 completes the dir + logs
      `[F-NEW-625] install extract lib/x86_64/libgdx-freetype.so (870496 bytes)`.
  P3: tictactoe frame sweep (8/20/60) -> does any frame reproduce the
      Coder-3 claim face 3ca1db0cf92badc7?
"""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
RUNS = BASE / 'evidence/s200/runs'
RUNS.mkdir(parents=True, exist_ok=True)
OUT = {}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_pkg(store, tag, frames, delay=250, max_seconds=None, taps=None,
            timeout=900):
    apps = store / 'data' / 'app'
    dpkg = None
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
    if max_seconds:
        cmd += ['--max-seconds', str(max_seconds)]
    for (fr, x, y) in (taps or []):
        cmd += ['--tap', f'{x},{y}@{fr}']
    with open(console, 'wb') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       cwd=str(BASE), timeout=timeout)
    log = console.read_text(errors='ignore')
    shot = rundir / 'final_frame.png'
    if not shot.exists():
        cands = sorted(rundir.glob('**/*.png')) if rundir.exists() else []
        shot = cands[-1] if cands else None
    return {'face': sha16(shot) if shot and shot.exists() else None,
            'log': log,
            'uncaught': len(re.findall(r'FATAL|uncaught exception|Uncaught',
                                       log))}


# P1 dooz pin invocation
store = RUNS / 'store_s202_dooz_pin'
store.mkdir(parents=True, exist_ok=True)
subprocess.run([str(BIN), 'install',
                str(BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'),
                '--data-root', str(store)], capture_output=True, timeout=300)
r = run_pkg(store, 's202_dooz_pin', frames=5, max_seconds=40,
            timeout=600)
OUT['dooz_pin'] = {'face': r['face'], 'pin': '31ddd4d5',
                   'exact': r['face'] == '31ddd4d5b8e6d18e',
                   'uncaught': r['uncaught']}
print('P1 dooz pin:', OUT['dooz_pin'], flush=True)

# P2 force 625 leg (b)
store2 = RUNS / 'store_s202_625_forced'
shutil.rmtree(store2, ignore_errors=True)
store2.mkdir(parents=True)
subprocess.run([str(BIN), 'install',
                str(BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'),
                '--data-root', str(store2)], capture_output=True, timeout=300)
libdir = next((store2 / 'data' / 'app').glob('*/lib/x86_64'))
removed = []
for leaf in ('libgdx-freetype.so', 'libgdx-box2d.so'):
    p = libdir / leaf
    if p.exists():
        p.unlink()
        removed.append(leaf)
r2 = run_pkg(store2, 's202_625_forced', frames=40)
log2 = r2['log']
OUT['f625_forced'] = {
    'removed': removed,
    'extract_lines': re.findall(r'\[F-NEW-625\] install extract.*', log2),
    'bind_lines': re.findall(r'\[F-NEW-625\] nativeLibraryDir.*', log2),
    'gdx_host': re.findall(r'\[GDX-HOST\].*LOADED.*', log2)[:2],
    'abi_error': len(re.findall(r'different primary ABI', log2)),
    'restored': len(re.findall(r'\[F-NEW-612b\] restored', log2)),
    'face': r2['face'],
}
print('P2 f625 forced:', json.dumps(OUT['f625_forced'], indent=1)[:800],
      flush=True)

# P3 tictactoe frame sweep
OUT['ttt_sweep'] = {}
for fr in (8, 20, 60):
    rs = run_pkg(RUNS / 'store_s202_ttt_boot1', f's202_ttt_f{fr}', frames=fr)
    OUT['ttt_sweep'][fr] = rs['face']
    print(f'P3 ttt frames={fr}: face={rs["face"]}', flush=True)
OUT['ttt_sweep']['claim'] = '3ca1db0cf92badc7'
OUT['ttt_sweep']['claim_hit'] = any(
    v == '3ca1db0cf92badc7' for k, v in OUT['ttt_sweep'].items()
    if k != 'claim')

(BASE / 'evidence/s200/S202_PROBES.json').write_text(json.dumps(OUT, indent=1))
print('P1 exact:', OUT['dooz_pin']['exact'],
      '| P2 extract fired:', bool(OUT['f625_forced']['extract_lines']),
      '| P3 claim_hit:', OUT['ttt_sweep']['claim_hit'])
