#!/usr/bin/env python3
# cont154_parse3.py — final honest scorecard from sequential re-run (.out Status/Message is authoritative)
import json, os, re
from collections import Counter, OrderedDict

BASE = '/home/z/my-project/run/c154'
blocks = OrderedDict()
cur = None
for line in open(os.path.join(BASE, 'battery.log'), errors='replace'):
    line = line.rstrip('\n')
    m = re.match(r'^== WAGON (\d+) (\S+) apk=(\S+) ==', line)
    if m:
        if cur and cur.get('rc') is not None:
            blocks[cur['name']] = cur
        cur = OrderedDict(idx=int(m.group(1)), name=m.group(2), apk=m.group(3), rc=None)
        continue
    if cur is None: continue
    m = re.match(r'^rc=(\d+)$', line)
    if m: cur['rc'] = int(m.group(1)); continue
if cur and cur.get('rc') is not None:
    blocks[cur['name']] = cur

rows = []
for name, cur in blocks.items():
    outf = os.path.join(BASE, name + '.out')
    logf = os.path.join(BASE, name + '.log')
    out = open(outf, errors='replace').read() if os.path.exists(outf) else ''
    data = open(logf, errors='replace').read() if os.path.exists(logf) else ''
    m = re.search(r'^Status: (.+)$', out, re.M)
    status = m.group(1).strip() if m else 'NO_STATUS'
    m = re.search(r'^Message: (.+)$', out, re.M)
    msg = m.group(1).strip() if m else ''
    m = re.search(r'F-016 exception-honesty: (\d+) uncaught in-flight', msg)
    inflight = int(m.group(1)) if m else 0
    m = re.search(r'first_missing_stage=(\w+)', msg)
    fms = m.group(1) if m else None
    m = re.search(r'verdict=(\w+)', msg)
    verdict = m.group(1) if m else None
    # render evidence
    nw = tot = None
    for mm in re.finditer(r'\[EXP092-COPY\] (?:framebuffer_ has|fb has) (\d+) non-white pixels out of (\d+) total', data):
        nw = int(mm.group(1)); tot = int(mm.group(2))
    render_frac = (nw / tot) if (nw is not None and tot) else 0.0
    png = os.path.exists(os.path.join(BASE, name, 'screenshot.png'))
    rendered = png and render_frac > 0.01
    excs = re.findall(r'SYNTH-EXC\s+(?:\[[^\]]*\]\s*)?([\w.$]+)', data)
    rows.append(OrderedDict(
        name=name, apk=cur['apk'], rc=cur['rc'], status=status,
        uncaught_inflight=inflight, first_missing_stage=fms, verdict=verdict,
        png=png, nonwhite=nw, render_frac=round(render_frac, 4),
        rendered=rendered, first_exc=excs[0] if excs else None,
        n_synthexc=len(excs)))

cls_census = Counter(r['status'] for r in rows)
fms_census = Counter(r['first_missing_stage'] for r in rows if r['status'] != 'SUCCESS')
verdict_census = Counter(r['verdict'] for r in rows)
render_ct = sum(1 for r in rows if r['rendered'])
inflight0 = sum(1 for r in rows if r['uncaught_inflight'] == 0)
out = OrderedDict(total=len(rows), status=dict(cls_census),
                  rendered=render_ct, zero_inflight=inflight0,
                  first_missing_stage=dict(fms_census), verdict=dict(verdict_census),
                  rows=rows)
json.dump(out, open(os.path.join(BASE, 'scorecard_final.json'), 'w'), indent=1, ensure_ascii=False)

print(f'=== SEQUENTIAL RE-RUN: {len(rows)} apps ===')
print('Status census:', dict(cls_census))
print(f'RENDERED (non-white >1%): {render_ct}/{len(rows)}')
print(f'zero uncaught-in-flight: {inflight0}/{len(rows)}')
print('F-NEW-233 frame verdict:', dict(verdict_census))
print('first_missing_stage (PARTIAL apps):')
for k, v in fms_census.most_common():
    print(f'  {v}x {k}')
# SUCCESS apps list
print('SUCCESS apps:', [r['name'] for r in rows if r['status'].startswith('SUCCESS')])
