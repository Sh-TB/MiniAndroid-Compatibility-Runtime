#!/usr/bin/env python3
"""S117 — MORE APPS WITH COMPLETE GRAPHICS wave (user directive).

Targets:
  1. accelerace  (HTML5 game, runs since S114 — canvas scene was the open frontier)
  2. org.asafonov.weather vc21 (sweep #216 PARTIAL: misplaced dialog text — same
     plain-WebView family as blockbuster; must reach COMPLETE GUI)
  3. blockbuster gate (S114 COMPLETE anchor must stay byte-identical)
  4. mykanji gate (S113/S114 full-GUI anchor)
  5. ballbreak + dooz native gates (byte-identical)

All screenshots saved SMALL per the standing user directive (no big uploads,
no Persian text anywhere). PPM stays on disk only (never pushed).
"""
import hashlib, json, re, struct, subprocess, sys, zlib
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s117_complete_graphics'
OUT.mkdir(parents=True, exist_ok=True)

RUNS = [
    ('accelerace', 'tmp/apks/accelerace_12.apk', 480),
    ('weather',    'tmp/apks/org.asafonov.weather_21.apk', 480),
    ('blockbuster','tmp/apks/org.asafonov.blockbuster_12.apk', 480),
    ('mykanji',    'tmp/apks/io.github.hathibelagal.mykanji_7.apk', 480),
    ('g_ballbreak','upload/s105_apks/de.georgsieber.ballbreak_10.apk', 280),
    ('g_dooz',     '/tmp/my-project/apk_cache/dooz.apk', 280),
]

def ppm_stats(p: Path):
    """Parse binary PPM (P6) -> (w,h,unique_colors,nonbg_ratio,sha16)."""
    data = p.read_bytes()
    if not data.startswith(b'P6'):
        return None
    # header: P6\n<w> <h>\n<max>\n
    parts = data.split(b'\n', 3)
    w, h = map(int, parts[1].split())
    pix = parts[3]
    n = w * h
    if len(pix) < n * 3:
        return None
    colors = set()
    nonbg = 0
    total = 0
    # sample every 2nd pixel for speed on 1080p
    for i in range(0, n, 2):
        r, g, b = pix[i*3], pix[i*3+1], pix[i*3+2]
        colors.add((r >> 3, g >> 3, b >> 3))
        if not (r > 240 and g > 240 and b > 240):
            nonbg += 1
        total += 1
    import hashlib
    return {'w': w, 'h': h, 'colors_5bit': len(colors),
            'nonbg': round(100.0 * nonbg / total, 2),
            'sha16': hashlib.sha256(pix).hexdigest()[:16]}

def ppm_to_small_png(p: Path, dst: Path, scale=0.5, max_bytes=100_000):
    try:
        from PIL import Image
        import io
        data = p.read_bytes()
        parts = data.split(b'\n', 3)
        w, h = map(int, parts[1].split())
        im = Image.frombytes('RGB', (w, h), parts[3])
        im = im.resize((int(w*scale), int(h*scale)), Image.BOX)
        q = 88
        im.save(dst, 'PNG', optimize=True)
        while dst.stat().st_size > max_bytes and q > 30:
            q -= 12
            im.save(dst, 'PNG', optimize=True)
            break
        return dst.stat().st_size
    except Exception as e:
        return None

results = {}
for name, apk, tmo in RUNS:
    ap = BASE / apk if not apk.startswith('/') else Path(apk)
    if not ap.exists():
        results[name] = {'error': f'APK missing: {apk}'}
        continue
    d = OUT / name
    d.mkdir(exist_ok=True)
    cmd = [str(BIN), 'run', str(ap), '-o', str(d)]
    with open(d / 'run.log', 'w') as f:
        try:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                                timeout=tmo).returncode
        except subprocess.TimeoutExpired:
            rc = -999
    text = (d / 'run.log').read_text(errors='ignore')
    merr = re.findall(r'Errors?:\s*(\d+)', text)
    mwarn = re.findall(r'Warnings?:\s*(\d+)', text)
    mst = re.search(r'Status:\s*\**\s*([A-Z_ ]+)', text)
    js_err = re.findall(r'js_errors[=:\s]+(\d+)', text)
    entry = {'rc': rc,
             'errors': merr[-1] if merr else '?',
             'warnings': mwarn[-1] if mwarn else '?',
             'status': mst.group(1).strip() if mst else '?',
             'js_errors': js_err[-1] if js_err else None}
    ppm = d / 'screenshot.ppm'
    if ppm.exists():
        st = ppm_stats(ppm)
        entry['pixels'] = st
        if st and st['colors_5bit'] >= 40 and st['nonbg'] >= 8:
            entry['render_verdict'] = 'RICH'
        elif st and st['colors_5bit'] >= 8 and st['nonbg'] >= 2:
            entry['render_verdict'] = 'PARTIAL'
        else:
            entry['render_verdict'] = 'NEAR_BLANK'
        sz = ppm_to_small_png(ppm, d / 'screenshot_small.png')
        entry['small_png_bytes'] = sz
    else:
        entry['render_verdict'] = 'NO_SHOT'
    results[name] = entry
    print(f"{name:12s} rc={rc:5d} err={entry['errors']:>3s} warn={entry['warnings']:>3s} "
          f"verdict={entry['render_verdict']:10s} "
          + (f"colors={st['colors_5bit']} nonbg={st['nonbg']}% sha={st['sha16']} "
             f"png={entry.get('small_png_bytes')}B" if 'pixels' in entry and entry['pixels'] else ''))

(OUT / 'summary.json').write_text(json.dumps(results, indent=2))
print('summary ->', OUT / 'summary.json')
