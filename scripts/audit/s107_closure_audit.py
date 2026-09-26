#!/usr/bin/env python3
"""S107 closure-wave audit — pixel-level re-verification of all 128 closed tickets.

Rules enforced (from the user's audit directive + project Constitution):
  - PNG exists / exit=0 / non-crash / hash exists  ->  NOT visual evidence by itself.
  - White / near-white / black / monochrome / background-only  ->  FAIL, not PASS.
  - Measure per screenshot: resolution, unique colors, entropy, non-background
    ratio, content bounding box, edge density, SHA.
  - Provenance: recorded SHA == local SHA; local run dir exists; run.log from
    the committed evidence tree.
  - 3-run rule: the wave produced only 2 runs -> nothing can be VERIFIED from
    wave evidence alone; content-bearing titles -> PENDING_3RUN.
Output: evidence/audit_s107/audit_table.json + contact sheets.
"""
import json, hashlib, math, re, sys
from pathlib import Path
from PIL import Image
import numpy as np

BASE = Path('/home/z/my-project')
EV = BASE / 'evidence/s107_games'
OUT = BASE / 'evidence/audit_s107'
OUT.mkdir(parents=True, exist_ok=True)
wave = json.load(open('/tmp/s107_wave_full.json'))

def sha256f(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def metrics(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    n = w * h
    a = np.asarray(im, dtype=np.int16)            # h,w,3
    flat = a.reshape(-1, 3)
    # exact unique colors
    packed = (flat[:, 0].astype(np.int32) << 16) | (flat[:, 1].astype(np.int32) << 8) | flat[:, 2]
    uq, ucnt = np.unique(packed, return_counts=True)
    ncols = int(len(uq))
    dom_idx = int(np.argmax(ucnt))
    dom = uq[dom_idx]
    dom_c = np.array([(int(dom) >> 16) & 255, (int(dom) >> 8) & 255, int(dom) & 255], dtype=np.int16)
    dom_frac = float(ucnt[dom_idx]) / n
    # entropy over 4-bit-quantized
    q = (flat[:, 0] >> 4) * 256 + (flat[:, 1] >> 4) * 16 + (flat[:, 2] >> 4)
    qv, qc = np.unique(q, return_counts=True)
    p = qc / n
    ent = float(-(p * np.log2(p)).sum())
    # non-background mask
    diff = np.abs(a - dom_c).max(axis=2)
    mask = diff > 8
    nonbg_ratio = float(mask.sum()) / n
    if mask.any():
        ys, xs = np.where(mask)
        bb = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    else:
        bb = None
    # edge density (sampled every 2 px)
    d1 = np.abs(a[:-2:2, :, :].astype(np.int16) - a[2::2, :, :].astype(np.int16)).max(axis=2)
    d2 = np.abs(a[:, :-2:2, :].astype(np.int16) - a[:, 2::2, :].astype(np.int16)).max(axis=2)
    edges = int((d1 > 48).sum()) + int((d2 > 48).sum())
    edge_density = edges / (n / 4)
    # bar detection
    top_black = float((a[:80, ::4].max(axis=2) == 0).mean()) if h >= 80 else float((a[:, ::4].max(axis=2) == 0).mean())
    bot_black = float((a[-80:, ::4].max(axis=2) == 0).mean()) if h >= 80 else 0.0
    # row profile of content: is content only in bars (top/bottom 80px)?
    rowc = mask.sum(axis=1)
    content_mid = float(rowc[80:-80].sum()) / max(1, int(mask.sum())) if mask.any() else 0.0
    return {
        'resolution': [w, h], 'unique_colors': ncols, 'entropy_q4': round(ent, 3),
        'dominant_color': [int(x) for x in dom_c], 'dominant_fraction': round(dom_frac, 4),
        'nonbg_ratio': round(nonbg_ratio, 5),
        'content_bbox': bb, 'edge_density': round(edge_density, 4),
        'top_black_bar': round(top_black, 3), 'bottom_black_bar': round(bot_black, 3),
        'content_share_outside_bars': round(content_mid, 3),
        'sha256': sha256f(path),
    }

def classify(m):
    """Visual verdict from measured metrics only."""
    nb = m['nonbg_ratio']
    colors = m['unique_colors']
    if colors == 1:
        return 'BLANK_MONOCHROME'
    if nb <= 0.002 and colors <= 8:
        return 'BACKGROUND_ONLY' if colors >= 3 else 'BLANK_SOLID'
    if nb <= 0.005:
        return 'NEAR_BLANK'
    if nb < 0.02 and colors < 30 and m['edge_density'] < 0.01:
        return 'NEAR_BLANK'
    return 'CONTENT_PRESENT'

rows = []
for it in wave:
    pkg = it['package']
    rec = {'number': it['number'], 'title': it['title'], 'package': pkg,
           'labels': it['labels'], 'closed_at': it['closed_at']}
    cm = it['comment']
    def grab(pat, cast=str):
        m = re.search(pat, cm)
        return cast(m.group(1)) if m else None
    rec['recorded'] = {
        'exit_code': grab(r'\| exit code \| (-?\d+) \|', int),
        'status': grab(r'\| run status \| (.*?) \|'),
        'errors': grab(r'\| error count \| (-?\d+) \|', int),
        'exc_hash': grab(r'\| exception-set hash \| `(.*?)` \|'),
        'shot_sha': grab(r'\| screenshot SHA \(first 16\) \| `(.*?)` \|'),
        'unique_colors': grab(r'\| unique framebuffer colors \| (-?\d+) \|', int),
        'deterministic': grab(r'\| deterministic across runs \| (.*?) \|'),
    }
    d1 = EV / f'{pkg}_run1'; d2 = EV / f'{pkg}_run2'
    rec['evidence_dir_exists'] = d1.exists()
    runs = []
    for i, d in enumerate((d1, d2), 1):
        if not d.exists():
            runs.append({'run': i, 'present': False}); continue
        shot = d / 'screenshot.png'
        r = {'run': i, 'present': True,
             'runlog_bytes': (d / 'run.log').stat().st_size if (d / 'run.log').exists() else 0,
             'lifecycle': (d / 'lifecycle_trace.json').exists()}
        if shot.exists():
            try:
                r.update(metrics(shot))
                r['verdict'] = classify(r)
            except Exception as e:
                r['verdict'] = 'METRICS_ERROR: ' + str(e)[:80]
        else:
            r['verdict'] = 'NO_SCREENSHOT'
        runs.append(r)
    rec['runs'] = runs
    ok = [r for r in runs if r.get('present') and r.get('sha256')]
    rec['sha_match_run1'] = bool(ok and rec['recorded']['shot_sha'] and
                                 ok[0]['sha256'][:16] == rec['recorded']['shot_sha'])
    verdicts = [r.get('verdict') for r in runs]
    rec['verdicts'] = verdicts
    content_runs = sum(1 for v in verdicts if v == 'CONTENT_PRESENT')
    if not rec['evidence_dir_exists']:
        rec['audit'] = 'INSUFFICIENT_EVIDENCE_NO_EVIDENCE_DIR'
    elif content_runs == 0:
        blanks = {v for v in verdicts if v and v.startswith(('BLANK', 'BACKGROUND', 'NEAR_BLANK'))}
        if 'NO_SCREENSHOT' in verdicts or 'METRICS_ERROR' in str(verdicts):
            rec['audit'] = 'INSUFFICIENT_EVIDENCE'
        else:
            rec['audit'] = 'REOPEN_' + ('/'.join(sorted(blanks)) if blanks else 'UNKNOWN')
    elif content_runs == 2 and rec['sha_match_run1']:
        rec['audit'] = 'PENDING_3RUN_CONTENT_BOTH'   # wave had only 2 runs -> cannot be VERIFIED
    elif content_runs >= 1:
        rec['audit'] = 'NON_REPRODUCIBLE_CONTENT_PARTIAL'
    else:
        rec['audit'] = 'UNKNOWN'
    rows.append(rec)
    m1 = runs[0]
    print(f"#{rec['number']:4d} {pkg[:36]:38s} {rec['audit']:38s} "
          f"colors={m1.get('unique_colors')} nb={m1.get('nonbg_ratio')} ent={m1.get('entropy_q4')} "
          f"shaOK={rec['sha_match_run1']}", flush=True)

json.dump(rows, open(OUT / 'audit_table.json', 'w'), indent=1)

import collections
c = collections.Counter(r['audit'] for r in rows)
print('\n== AUDIT SUMMARY ==')
for k, v in c.most_common():
    print(f'{v:4d}  {k}')
print('total:', len(rows))
