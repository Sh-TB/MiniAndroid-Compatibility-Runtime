#!/usr/bin/env python3
"""S115 — batch sweep of the 77 NEAR_BLANK reopened tickets at the S114 HEAD.

Assembly-line law (user directive): ONE run per ticket, fixed time budget,
NO per-ticket debugging. Classification by pixel metrics only.
Resumable: state file run/s115_sweep/state.json; skips finished tickets.
Wall-clock budget via argv[1] (seconds, default 540).
"""
import json, math, os, re, struct, subprocess, sys, time, urllib.request
from pathlib import Path

BASE = Path('/home/z/my-project')
BIN = BASE / 'miniandroid/build/miniandroid'
OUT = BASE / 'evidence/s115_sweep'
APKDIR = BASE / 'tmp/s115_apks'
STATE = BASE / 'run/s115_sweep/state.json'
BUDGET = int(sys.argv[1]) if len(sys.argv) > 1 else 540
RUN_CAP = 140          # per-app timeout cap (s)
FETCH_CAP = 75         # per-APK download cap (s)

OUT.mkdir(parents=True, exist_ok=True)
APKDIR.mkdir(parents=True, exist_ok=True)
STATE.parent.mkdir(parents=True, exist_ok=True)

# ---------- the 77 ----------
_reopened = json.load(open(BASE / 'evidence/audit_s107/reopened.json'))
TICKETS = {x['number']: x['package'] for x in _reopened if x['reason'] == 'NEAR_BLANK'}

# ---------- state ----------
state = json.load(open(STATE)) if STATE.exists() else {}
def save_state():
    STATE.write_text(json.dumps(state, indent=1))

# ---------- APK resolution ----------
LOCAL_DIRS = [BASE/'tmp/apks', BASE/'tmp/s115_apks', BASE/'upload/canonical_apks',
              BASE/'upload/foundation_apks', BASE/'upload/s105_apks',
              BASE/'evidence/s106_fresh/apks', BASE/'apk_cache']

def find_local(pkg):
    for d in LOCAL_DIRS:
        if not d.exists(): continue
        for f in sorted(d.glob(f'{pkg}*.apk')):
            return f
    return None

FDROID_META = {}
def fdroid_meta(pkg):
    if pkg in FDROID_META: return FDROID_META[pkg]
    try:
        req = urllib.request.Request(
            f'https://f-droid.org/api/v1/packages/{pkg}',
            headers={'User-Agent': 'miniandroid-sweep'})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        FDROID_META[pkg] = d.get('suggestedVersionCode')
    except Exception:
        FDROID_META[pkg] = None
    return FDROID_META[pkg]

def fetch_fdroid(pkg):
    code = fdroid_meta(pkg)
    if code is None: return None
    url = f'https://f-droid.org/repo/{pkg}_{code}.apk'
    dest = APKDIR / f'{pkg}_{code}.apk'
    if dest.exists() and dest.stat().st_size > 10000:
        return dest
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'miniandroid-sweep'})
        with urllib.request.urlopen(req, timeout=FETCH_CAP) as r, open(dest, 'wb') as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk: break
                f.write(chunk)
        return dest if dest.stat().st_size > 10000 else None
    except Exception:
        return None

# ---------- metrics ----------
def png_size(data):
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        w, h = struct.unpack('>II', data[16:24])
        return w, h
    return None, None

def metrics(path):
    try:
        from PIL import Image
        im = Image.open(path).convert('RGB')
        w, h = im.size
        px = im.load()
        colors = {}
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                c = px[x, y]
                colors[c] = colors.get(c, 0) + 1
        total = sum(colors.values())
        dom = max(colors.items(), key=lambda kv: kv[1])[0]
        nonbg = sum(v for c, v in colors.items()
                    if abs(c[0]-dom[0]) + abs(c[1]-dom[1]) + abs(c[2]-dom[2]) > 24)
        ent = -sum((v/total)*math.log2(v/total) for v in colors.values())
        m = {'res': [w, h], 'unique_colors': len(colors),
             'dominant': '#%02x%02x%02x' % dom,
             'nonbg_ratio': round(nonbg/total, 4), 'entropy': round(ent, 3)}
        # classification
        if m['nonbg_ratio'] >= 0.02 and m['unique_colors'] >= 64:
            m['class'] = 'NONBLANK'
        elif m['nonbg_ratio'] >= 0.002 or m['unique_colors'] >= 24:
            m['class'] = 'MARGINAL'
        else:
            m['class'] = 'BLANK'
        return m
    except Exception as e:
        return {'error': str(e)}

# ---------- main loop ----------
t0 = time.time()
order = sorted(TICKETS)
for n in order:
    key = str(n)
    if key in state and state[key].get('phase') == 'done':
        continue
    if time.time() - t0 > BUDGET:
        print(f'[BUDGET] stopping after {key} queue head; elapsed {time.time()-t0:.0f}s')
        break
    pkg = TICKETS[n]
    rec = {'ticket': n, 'package': pkg}
    apk = find_local(pkg) or fetch_fdroid(pkg)
    if apk is None:
        rec.update(phase='done', verdict='APK_UNAVAILABLE')
        state[key] = rec
        save_state()
        print(f'#{n} {pkg}: APK_UNAVAILABLE')
        continue
    run_dir = OUT / f't{n}_{pkg}'
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / 'run.log'
    t_run = time.time()
    try:
        with open(log, 'w') as f:
            rc = subprocess.run([str(BIN), 'run', str(apk), '-o', str(run_dir)],
                                stdout=f, stderr=subprocess.STDOUT,
                                timeout=RUN_CAP).returncode
    except subprocess.TimeoutExpired:
        rc = -9
        log.write_text((log.read_text(errors='ignore') if log.exists() else '')
                       + '\nTIMEOUT %ds' % RUN_CAP)
    rec['rc'] = rc
    rec['run_s'] = round(time.time() - t_run, 1)
    text = log.read_text(errors='ignore') if log.exists() else ''
    m = re.search(r'Errors?:\s*(\d+)', text)
    rec['errors'] = int(m.group(1)) if m else -1
    shots = sorted(run_dir.rglob('screenshot*.png'))
    if shots:
        rec['shot'] = shots[0].name
        rec.update(metrics(shots[0]))
        rec['verdict'] = rec.get('class', 'NO_SHOT')
    else:
        rec['verdict'] = 'NO_SHOT'
    rec['phase'] = 'done'
    state[key] = rec
    save_state()
    print(f"#{n} {pkg}: {rec['verdict']} rc={rc} errs={rec['errors']} "
          f"nonbg={rec.get('nonbg_ratio')} colors={rec.get('unique_colors')} "
          f"({rec['run_s']}s)")

# ---------- summary ----------
from collections import Counter
c = Counter(r.get('verdict', 'PENDING') for r in state.values())
print('SUMMARY:', dict(c))
save_state()
