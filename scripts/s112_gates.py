#!/usr/bin/env python3
"""S112 regression gates — breakout/ballbreak/dooz must stay byte-identical."""
import hashlib, json, re, subprocess
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s112_html5_generalization/gates'
OUT.mkdir(parents=True, exist_ok=True)

GATES = {
    'breakout': (BASE / 'tmp/apks/breakout.apk', '568342fb901a75ab'),
    'ballbreak': (BASE / 'upload/s105_apks/de.georgsieber.ballbreak_10.apk', 'fe797c19ba1920ed'),
    'dooz': (BASE / 'upload/canonical_apks/io.github.yamin8000.dooz_23.apk', 'a2ba4a49'),
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
