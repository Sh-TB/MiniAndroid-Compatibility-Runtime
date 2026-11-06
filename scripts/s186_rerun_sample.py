#!/usr/bin/env python3
"""S186: re-run representative s107 titles on the CURRENT engine (post-S183b laws).
Exact s182 battery invocation law: install -> discover_pkg -> run real-dalvik
--data-root -o --max-seconds --frames 5 --trace --package <pkg>.
A/B question: do B1 host-native + framework-superclass laws change s107 verdicts?"""
import json, os, subprocess, hashlib, sys
from pathlib import Path
from PIL import Image

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s186_s107'
RUNS = OUT / 'reruns'
RUNS.mkdir(parents=True, exist_ok=True)

SAMPLE = [
    ('bouncy',     BASE / 'upload/fdroid_batch/com.dozingcatsoftware.bouncy_43.apk', 40),
    ('ricochlime', BASE / 'upload/fdroid_batch/com.adilhanney.ricochlime_1140003.apk', 40),
]

def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]

def discover_pkg(apk, store):
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), "install", str(apk), "--data-root", str(store)],
                   capture_output=True, timeout=300)
    apps = store / "data" / "app"
    if apps.exists():
        ds = [d.name for d in apps.iterdir() if d.is_dir() and not d.name.endswith('.staging')]
        if ds:
            return ds[0]
    return None

rows = []
for name, apk, secs in SAMPLE:
    if not BIN.exists():
        rows.append(dict(name=name, error='binary missing')); continue
    store = RUNS / f"store_{name}"
    pkg = discover_pkg(apk, store)
    if not pkg:
        rows.append(dict(name=name, error='INSTALL_FAIL')); continue
    rundir = RUNS / name
    console = RUNS / f"{name}.err"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(secs), "--frames", "5",
           "--trace", "--package", pkg]
    with open(console, 'w') as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, timeout=secs + 120)
    shot = rundir / 'screenshot.png'
    face = sha16(shot) if shot.exists() else None
    if face:
        im = Image.open(shot).convert('RGB'); im.thumbnail((540, 960))
        im.save(OUT / f'S186_{name}_face.jpg', 'JPEG', quality=70)
    text = console.read_text(errors='replace')
    uncaught = len([l for l in text.splitlines() if 'Uncaught' in l or 'UNCAUGHT' in l])
    rows.append(dict(name=name, pkg=pkg, face=face, uncaught_lines=uncaught,
                     gdx_host=text.count('[GDX-HOST]'),
                     err_tail=text.splitlines()[-10:]))
    print(name, pkg, face, 'uncaught:', uncaught)

json.dump(dict(schema='s186_rerun/v1', binary='post-S183b main (104.8MB build)', rows=rows),
          open(OUT / 'S186_RERUN.json', 'w'), indent=1)
print('done')
