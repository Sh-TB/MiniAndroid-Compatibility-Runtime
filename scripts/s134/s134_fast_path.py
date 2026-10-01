#!/usr/bin/env python3
"""S134 FAST path (§35, ~30s/target): fingerprint every F-NEW-156/157 face APK
on the CURRENT-HEAD binary. Collect: APK SHA, runtime SHA, entry/lifecycle
fingerprint, first exception, first divergence, content-root status, tree
size, frame fingerprint (unique colors, dominant color), failure family.

Honest output: each target classified per the S134 §32 taxonomy. No status
inflation — OBSERVED evidence only.
"""
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
CACHE = Path('/tmp/my-project/apk_cache')
OUT = BASE / 'run/s134/fast'
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ('solitaire_71',      CACHE / 's82/de.tobiasbielefeld.solitaire_71.apk',          'F-NEW-156'),
    ('headingcalc_1',     CACHE / 'org.debian.eugen.headingcalculator_1.apk',        'F-NEW-156'),
    ('chessclock_29',     CACHE / 'com.chessclock.android_29.apk',                   'F-NEW-156'),
    ('simplestopwatch_26', CACHE / 'omegacentauri.mobi.simplestopwatch_26.apk',      'F-NEW-156'),
    ('boxcars_libgdx',    CACHE / 's82/com.rocket9labs.boxcars_104090.apk',          'F-NEW-157'),
]

def sha256(p: Path, n=16):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()[:n]

def png_stats(p: Path):
    try:
        from PIL import Image
        im = Image.open(p).convert('RGB')
        colors = im.getcolors(maxcolors=1 << 24)
        if not colors:
            return {'unique': -1}
        colors.sort(reverse=True)
        total = sum(c for c, _ in colors)
        return {
            'w': im.width, 'h': im.height,
            'unique': len(colors),
            'dominant': colors[0][1],
            'dominant_pct': round(100.0 * colors[0][0] / total, 2),
            'top5': [(c, rgb) for c, rgb in colors[:5]],
        }
    except Exception as e:
        return {'error': str(e)}

def classify(text: str, stats: dict, rc: int):
    """S134 §32 failure taxonomy mapping from run evidence."""
    first_exc = None
    m = re.search(r'\[EXCEPTION\]([^\n]*)', text) or re.search(r'Exception[^\n]*', text)
    if m:
        first_exc = m.group(0).strip()[:220]
    errs = re.findall(r'Errors:\s*(\d+)', text)
    status = re.search(r'Status:\s*\**\s*([A-Za-z_ ]+)', text)
    unique = stats.get('unique', -1)
    dom = stats.get('dominant')
    dom_pct = stats.get('dominant_pct', 0)
    fam = 'UNKNOWN'
    if first_exc and 'NullPointerException' in first_exc:
        fam = 'NPE_BOUNDARY'  # refined below by site
    elif unique <= 2 or dom_pct > 99.5:
        fam = 'TRUE_EMPTY_FRAME'
    elif unique > 2 and dom_pct > 90:
        fam = 'STATE_NONBLANK'
    else:
        fam = 'NONBLANK_MULTI'
    return {
        'first_exception': first_exc,
        'errors': int(errs[-1]) if errs else None,
        'status': status.group(1).strip() if status else None,
        'family': fam,
    }

results = {}
runtime_sha = sha256(BIN) if BIN.exists() else 'MISSING'
for name, apk, root in TARGETS:
    t0 = time.time()
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    rec = {'root': root, 'apk': str(apk), 'apk_sha16': sha256(apk) if apk.exists() else 'MISSING'}
    if not apk.exists():
        rec['family'] = 'APK_MISSING'
        results[name] = rec
        continue
    with open(d / 'run.log', 'w') as f:
        try:
            rc = subprocess.run([str(BIN), 'run', str(apk), '-o', str(d), '--data-root', str(d / 'data')],
                                stdout=f, stderr=subprocess.STDOUT, timeout=120).returncode
        except subprocess.TimeoutExpired:
            rc = -9
            f.write('\n[TIMEOUT 120s]\n')
    text = (d / 'run.log').read_text(errors='ignore')
    shot = d / 'screenshot.png'
    rec['rc'] = rc
    rec['runtime_sha16'] = runtime_sha
    rec['screenshot'] = str(shot) if shot.exists() else 'NONE'
    rec['png'] = png_stats(shot) if shot.exists() else {}
    rec.update(classify(text, rec['png'], rc))
    # lifecycle / boundary fingerprints from the log
    rec['reached_setContentView'] = 'setContentView' in text
    rec['onCreate_calls'] = len(re.findall(r'onCreate\b', text))
    rec['log_lines'] = len(text.splitlines())
    rec['secs'] = round(time.time() - t0, 1)
    # keep first 60 lines of exception context for MID triage
    exc_lines = [l for l in text.splitlines() if 'Exception' in l or 'at ' in l][:60]
    (d / 'exception_context.txt').write_text('\n'.join(exc_lines))
    results[name] = rec

(OUT / 'FAST_RESULTS.json').write_text(json.dumps(results, indent=1))
for k, v in results.items():
    print(k, '|', v.get('root'), '| rc=', v.get('rc'), '| fam=', v.get('family'),
          '| unique=', v.get('png', {}).get('unique'), '| dom%=', v.get('png', {}).get('dominant_pct'),
          '| exc=', str(v.get('first_exception'))[:110])
print('runtime_sha16:', runtime_sha)
