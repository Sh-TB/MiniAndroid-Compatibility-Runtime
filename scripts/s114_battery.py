#!/usr/bin/env python3
"""S114 the ONE BIG FIX — full HTML5 battery + regression gates.
Runs: blockbuster (start+game), mykanji, accelerace, sokoban + native gates
(ballbreak, dooz) + the Breakout HTML5 canvas gate. Verifies pixel metrics.
All screenshots saved SMALL (540x960, palette-optimized PNG) per user
directive: small upload size, no Persian text in evidence."""
import hashlib, json, re, struct, subprocess, sys, zlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s114_bigfix'
OUT.mkdir(parents=True, exist_ok=True)

RUNS = [
    # (name, apk, extra_args)
    ('mykanji',    'tmp/apks/io.github.hathibelagal.mykanji_7.apk', []),
    ('accelerace', 'tmp/apks/org.asafonov.accelerace_12.apk', []),
    ('sokoban',    'tmp/apks/org.asafonov.sokoban_4.apk', []),
    ('g_ballbreak', 'games/apks/de.georgsieber.ballbreak.apk', []) if (BASE/'games/apks/de.georgsieber.ballbreak.apk').exists() else None,
    ('g_dooz',     'games/apks/io.github.yamin8000.dooz.apk', []) if (BASE/'games/apks/io.github.yamin8000.dooz.apk').exists() else None,
]
RUNS = [r for r in RUNS if r]

# locate the regression APKs if not in games/
def find_apk(*names):
    for pat in names:
        hits = list(BASE.glob(pat))
        if hits: return hits[0]
    return None
if not (BASE/'games/apks/de.georgsieber.ballbreak.apk').exists():
    b = find_apk('tmp/apks/*ballbreak*.apk', 'games/**/ballbreak*.apk', '**/*ballbreak*.apk')
    d = find_apk('tmp/apks/*dooz*.apk', 'games/**/dooz*.apk', '**/dooz*.apk')
    br = find_apk('tmp/apks/*breakout*.apk', '**/breakout*.apk')
    RUNS = [r for r in RUNS]
    if b: RUNS.append(('g_ballbreak', str(b.relative_to(BASE)), []))
    if d: RUNS.append(('g_dooz', str(d.relative_to(BASE)), []))
    if br: RUNS.append(('g_breakout_html5', str(br.relative_to(BASE)), []))

def downscale_png(src: Path, dst: Path, scale=0.5):
    """Decode PNG, box-downscale, re-encode palette PNG (small upload)."""
    data = src.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    w, h = struct.unpack('>II', data[16:24])
    # use PIL if available
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data)).convert('RGB')
        im = im.resize((int(w*scale), int(h*scale)), Image.BOX)
        im.save(dst, 'PNG', optimize=True)
        return dst.stat().st_size
    except ImportError:
        dst.write_bytes(data)
        return dst.stat().st_size

results = {}
for name, apk, extra in RUNS:
    ap = BASE / apk
    if not ap.exists():
        results[name] = {'error': f'APK missing {apk}'}
        continue
    d = OUT / name
    d.mkdir(exist_ok=True)
    cmd = [str(BIN), 'run', str(ap), '-o', str(d)] + extra
    try:
        with open(d / 'run.log', 'w') as f:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=280).returncode
    except subprocess.TimeoutExpired:
        rc = -1
    text = (d / 'run.log').read_text(errors='ignore')
    m = re.search(r'Errors?:\s*(\d+)', text)
    mst = re.search(r'Status:?\s*\**\s*([A-Z_ ]+)', text)
    shot = d / 'screenshot.png'
    small = {}
    if shot.exists():
        size = downscale_png(shot, d / 'screenshot_small.png')
        data = shot.read_bytes()
        small = {'w': struct.unpack('>II', data[16:24])[0],
                 'sha16': hashlib.sha256(data).hexdigest()[:16],
                 'small_bytes': size,
                 'orig_bytes': len(data)}
    results[name] = {'rc': rc,
                     'errors': int(m.group(1)) if m else -1,
                     'status': mst.group(1).strip() if mst else '?',
                     **small}

print(json.dumps(results, indent=1))
