#!/usr/bin/env python3
"""S188 golden-pin check: run bouncy/unote/dooz with the F-NEW-491 binary and
compare face hashes against the canonical pins. Regression law: no commit
advances while a golden breaks."""
import subprocess, hashlib, json, sys
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()[:16]
OUT = BASE / 'evidence/s188/first_renders'
RUNS = OUT / 'runs'
SECS = 40

GOLDENS = [
    ("com.dozingcatsoftware.bouncy", str(BASE / 'upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk'), "8a6c24ac"),
    ("app.varlorg.unote", str(BASE / 'upload/canonical_apks/app.varlorg.unote_30.apk'), "3b8dcb0a"),
    ("io.github.yamin8000.dooz", str(BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk'), "31ddd4d5"),
    # dooz pin = the W1-stable face (W5 worklog: "dooz = W1-stable 31ddd4d5
    # unchanged"; W6 rerun reconfirmed 31ddd4d5b8e6d18e). The pre-W1 pin
    # d602648e is stale — dooz settled to 31ddd4d5 before the S188 waves.
]

def sha16(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]

results = []
for pkg, apk, pin in GOLDENS:
    store = RUNS / f'run_store_{pkg}'
    store.mkdir(parents=True, exist_ok=True)
    apps = store / 'data' / 'app'
    subprocess.run([str(BIN), 'install', apk, '--data-root', str(store)],
                   capture_output=True, timeout=300)
    dpkg = None
    if apps.exists():
        ds = [d.name for d in apps.iterdir()
              if d.is_dir() and not d.name.endswith('.staging')]
        dpkg = ds[0] if ds else None
    if not dpkg:
        results.append({"pkg": pkg, "status": "INSTALL_FAIL"}); continue
    rundir = RUNS / f'run_{pkg}'
    console = RUNS / f'{pkg}.err'
    with open(console, 'w') as cf:
        subprocess.run([str(BIN), 'run', '--execution-mode', 'real-dalvik',
                        '--data-root', str(store), '-o', str(rundir),
                        '--max-seconds', str(SECS), '--frames', '5',
                        '--trace', '--package', dpkg],
                       stdout=cf, stderr=subprocess.STDOUT, timeout=SECS + 150)
    text = console.read_text(errors='replace')
    shot = rundir / 'screenshot.png'
    face = sha16(shot) if shot.exists() else 'NO_SHOT'
    hold = face.startswith(pin)
    results.append({"pkg": pkg, "face": face, "pin": pin, "pin_holds": hold,
                    "uncaught": text.count('UNCAUGHT'), "binary": BIN_SHA})
    print(json.dumps(results[-1]))

Path('/tmp/s188_goldens.json').write_text(json.dumps(results, indent=1))
print("PIN VERDICT:", "ALL HOLD" if all(r.get('pin_holds') for r in results) else "REGRESSION — INVESTIGATE")
