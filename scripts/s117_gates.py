#!/usr/bin/env python3
"""S117 gate check — verify the fresh HEAD rebuild reproduces the S114/S111
anchor baselines before any engine change (ballbreak 25e72190, dooz 84c6d4a5,
breakout 568342fb)."""
import hashlib, json, re, subprocess
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'tmp/s117_baseline/gates'
OUT.mkdir(parents=True, exist_ok=True)

GATES = {
    'breakout':  (BASE / 'tmp/apks/breakout.apk',                                    '568342fb901a75ab'),
    'ballbreak': (BASE / 'tmp/apks/de.georgsieber.ballbreak_10.apk',                  '25e72190ba1920ed'),
    'dooz':      (BASE / 'tmp/apks/io.github.yamin8000.dooz_23.apk',                  '84c6d4a5'),
}

results = {}
for name, (apk, want) in GATES.items():
    if not apk.exists():
        results[name] = {'error': 'apk missing'}
        continue
    outdir = OUT / name
    outdir.mkdir(parents=True, exist_ok=True)
    log = outdir / 'run.log'
    with open(log, 'w') as f:
        rc = subprocess.run([str(BIN), 'run', str(apk), '-o', str(outdir)],
                            stdout=f, stderr=subprocess.STDOUT, timeout=280).returncode
    text = log.read_text(errors='ignore')
    shots = sorted(outdir.glob('screenshot.png'))
    sha = hashlib.sha256(shots[0].read_bytes()).hexdigest()[:16] if shots else 'none'
    m = re.search(r'Errors:\s*(\d+)', text)
    mst = re.search(r'Status:\s*\**\s*([A-Z_ ]+)', text)
    results[name] = {
        'rc': rc, 'sha16': sha, 'want': want,
        'match': sha.startswith(want[:8]),
        'errors': int(m.group(1)) if m else -1,
        'status': mst.group(1).strip() if mst else '?',
    }
print(json.dumps(results, indent=1))

