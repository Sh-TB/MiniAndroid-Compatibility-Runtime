#!/usr/bin/env python3
"""S200-T03 — WHY does the FreeType family miss the real libgdx-freetype.so
symbols? Live dispatch capture on the canonical binary.

Probes (all env-gated, bounded, zero behavior change):
  MINIANDROID_W18_FT_TRACE=1  — try_recursive_invoke entries for the FT family
  MINIANDROID_W10_JNI_TRACE=1 — every find_symbol query + registered candidates
Extract the [W18-FT-RI] / [W10-JNI] / [W18-FT-BRIDGE] rows and the app verdict.
"""
import hashlib, json, re, shutil, subprocess, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
RUNS = BASE / 'evidence/s200/runs'
RUNS.mkdir(parents=True, exist_ok=True)

TAG = 'ft_miss'
store = RUNS / f'store_{TAG}'
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
print('package:', dpkg)

rundir = RUNS / f'run_{TAG}'
shutil.rmtree(rundir, ignore_errors=True)
console = RUNS / f'run_{TAG}.console.log'
cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
       '--data-root', str(store), '-o', str(rundir),
       '--package', dpkg, '--frames', '10', '--frame-delay', '250']
env = {'PATH': '/usr/bin:/bin', 'HOME': '/home/z',
       'MINIANDROID_W18_FT_TRACE': '1',
       'MINIANDROID_W10_JNI_TRACE': '1'}
t0 = time.time()
with open(console, 'wb') as cf:
    subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                   cwd=str(BASE), timeout=600, env=env)
wall = round(time.time() - t0, 1)
log = console.read_text(errors='ignore')

out = {
    'binary_sha16': hashlib.sha256(BIN.read_bytes()).hexdigest()[:16],
    'tag': TAG, 'wall_s': wall,
    'console_bytes': len(log),
}
ft_ri = [l for l in log.splitlines() if '[W18-FT-RI]' in l]
jni = [l for l in log.splitlines() if '[W10-JNI]' in l]
ft_br = [l for l in log.splitlines() if '[W18-FT-BRIDGE]' in l]
out['ft_ri_rows'] = ft_ri[:80]
out['ft_ri_count'] = len(ft_ri)
out['jni_rows'] = jni[:120]
out['jni_count'] = len(jni)
out['ft_bridge_rows'] = ft_br[:40]
out['ft_bridge_count'] = len(ft_br)

# verdict lines
verdict = [l for l in log.splitlines()
           if re.search(r'uncaught|APP BOUNDARY|FATAL|Exception|error', l, re.I)]
out['verdict_rows'] = verdict[:25]

outp = BASE / f'evidence/s200/ttt_{TAG}.RESULT.json'
outp.write_text(json.dumps(out, indent=1))
print('ft_ri:', len(ft_ri), ' jni:', len(jni), ' ft_bridge:', len(ft_br))
print('wrote', outp)
for l in ft_ri[:15]:
    print(' RI|', l)
for l in jni[:25]:
    print('JNI|', l)
