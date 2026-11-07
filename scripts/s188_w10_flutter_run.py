#!/usr/bin/env python3
"""S188-W10 Flutter-lane run: queens with F-NEW-590 (static-field reads +
direct-buffer snapshots). Mirrors the W9 35s real-dalvik invocation and
collects the census/divergence deltas into evidence/s188_w10/W10_RUN.json.

Usage: python3 scripts/s188_w10_flutter_run.py [secs]
"""
import json, re, subprocess, sys, shutil, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 35
PKG = 'com.sidhant.queens'
STORE = BASE / f'evidence/s188_w2/runs/store_{PKG}'
APK = BASE / f'upload/stuck_apks/{PKG}.apk'
OUT = BASE / 'evidence/s188_w10'
RUNDIR = OUT / 'runs' / 'w10_gl1'
LOG = OUT / 'w10_gl1.console.log'

def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RUNDIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(RUNDIR, ignore_errors=True)

    # install into the (already-populated) W2 store; idempotent
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(STORE)],
                   capture_output=True, timeout=120)

    apps = STORE / 'data' / 'app'
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith('.')
              and not d.name.endswith('.staging')
              and (d / 'base.apk').exists()]
        dpkg = ds[0] if ds else None
    if not dpkg:
        print(json.dumps({'error': 'INSTALL_FAIL'}))
        return

    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(STORE), '-o', str(RUNDIR),
           '--package', dpkg, '--seconds', str(SECS), '--trace']
    with open(LOG, 'wb') as cf:
        p = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=SECS)
            status = f'exit={p.returncode}'
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            status = 'killed-timeout'
    text = LOG.read_text(errors='replace')

    def count(pat):
        return len(re.findall(pat, text))

    slots = re.findall(r'UNSUPPORTED slot census: total=(\d+)((?: \S+=\d+)*)', text)
    census = []
    for total, rest in slots:
        d = {'total': int(total)}
        for m in re.finditer(r'(env\d+|vm\d+)=(\d+)', rest):
            d[m.group(1)] = int(m.group(2))
        census.append(d)
    f590_static = re.findall(r'\[F-NEW-590\] static (\S+) -> DEX storage', text)
    f590_buffers = re.findall(
        r'\[F-NEW-590\] GetDirectBufferAddress\(oid=(\d+)\) snapshotted cap=(\d+)', text)
    f590_unres = re.findall(
        r'\[F-NEW-590\] GetStaticFloatField\((\S+)\) unresolvable', text)
    result = {
        'wave': 'S188-W10 F-NEW-590 queens run',
        'secs': SECS,
        'status': status,
        'binary_sha16': sha16(BIN),
        'slot_census_at_exit': census[-1] if census else None,
        'f590_static_dex_hits': sorted(set(f590_static)),
        'f590_buffer_snapshots': f590_buffers[:8],
        'f590_unresolvable_statics': sorted(set(f590_unres)),
        'counts': {
            'run_bundle_fault': count(r'nativeRunBundleAndSnapshotFromLibrary.*fault'),
            'dispatch_platform_fault': count(r'nativeDispatchPlatformMessage.*fault'),
            'guarded_call_faults': count(r'\[S2-NATIVE\] guarded call fault'),
            'jni_unsupported_lines': count(r'\[JNI-UNSUPPORTED\]'),
            'impeller_accepted': count(r'Using the Impeller rendering backend'),
            'frames_rendered': None,
        },
        'log': str(LOG.relative_to(BASE)),
    }
    fm = re.search(r'Frames Rendered: (\d+)', text)
    if fm:
        result['counts']['frames_rendered'] = int(fm.group(1))
    (OUT / 'W10_RUN.json').write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))

if __name__ == '__main__':
    main()
