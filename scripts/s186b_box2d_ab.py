#!/usr/bin/env python3
"""S186b: box2d GATE-A completion A/B (SQLITE_RULE law #2).
bouncy (com.dozingcatsoftware.bouncy) renders on the post-S183b engine but
Box2D.<clinit> dies in SharedLibraryLoadRuntimeException because GATE A had no
host libgdx-box2d64.so (sandbox wiped tools/native_host). The libs are now
rebuilt from upstream sources (scripts/s183_build_gdx_host.sh, 266 JNI symbols).
A/B question: with the host lib present, does System.loadLibrary("gdx-box2d")
substitute the host build and does Box2D init go uncaught-free?
Invocation = exact s182 battery law (S186_RERUN.json protocol).
"""
import json, os, subprocess, hashlib
from pathlib import Path
from PIL import Image

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
APK = BASE / 'upload/fdroid_batch/com.dozingcatsoftware.bouncy_43.apk'
OUT = BASE / 'evidence/s186_s107'
RUN = OUT / 'reruns_box2d'
RUN.mkdir(parents=True, exist_ok=True)
SECS = 40


def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


def main():
    store = RUN / 'store_bouncy'
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), 'install', str(APK), '--data-root', str(store)],
                   capture_output=True, timeout=300)
    apps = store / 'data' / 'app'
    pkg = None
    if apps.exists():
        ds = [d.name for d in apps.iterdir() if d.is_dir() and not d.name.endswith('.staging')]
        pkg = ds[0] if ds else None
    if not pkg:
        print(json.dumps(dict(error='INSTALL_FAIL'), indent=2)); return
    rundir = RUN / 'bouncy'
    console = RUN / 'bouncy.err'
    cmd = [str(BIN), 'run', '--execution-mode', 'real-dalvik',
           '--data-root', str(store), '-o', str(rundir),
           '--max-seconds', str(SECS), '--frames', '5',
           '--trace', '--package', pkg]
    with open(console, 'w') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, timeout=SECS + 120)
    text = console.read_text(errors='replace')
    shot = rundir / 'screenshot.png'
    face = sha16(shot) if shot.exists() else None
    colors = None
    if face:
        im = Image.open(shot).convert('RGB')
        colors = len(set(im.getdata()))
        im.thumbnail((540, 960))
        im.save(OUT / 'S186b_bouncy_face.jpg', 'JPEG', quality=70)
    res = {
        'law': 'SQLITE_RULE #2 box2d GATE-A completion',
        'pkg': pkg,
        'face_sha16': face,
        'prior_face_sha16_s182_pin': 'dd0c14257fa1f2af',
        'prior_face_sha16_s186_rerun': 'dd0c14257fa1f2af',
        'unique_colors': colors,
        'gdx_host_substituted': 'GDX-HOST' in text,
        'gdx_box2d_substituted': ('GDX-HOST' in text and 'gdx-box2d' in text),
        'box2d_uncaught_remaining': text.count('SharedLibraryLoadRuntimeException'),
        'uncaught_total': text.count('UNCAUGHT'),
        'rc0': False,
    }
    # report lines of interest
    keep = []
    for ln in text.splitlines():
        if any(k in ln for k in ('GDX-HOST', 'G-4-LAZY', 'F-NEW-441',
                                 'SharedLibraryLoadRuntimeException',
                                 'Box2D', 'NATIVE-LOADED', 'UNCAUGHT')):
            keep.append(ln[:220])
    res['console_key_lines'] = keep[:60]
    (OUT / 'S186B_BOX2D_AB.json').write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != 'console_key_lines'}, indent=2))


if __name__ == '__main__':
    main()
