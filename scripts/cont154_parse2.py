#!/usr/bin/env python3
# cont154_parse2.py — honest classification: render evidence first, rc second + REC-MISS worklist
import glob, json, os, re
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
        cur = OrderedDict(idx=int(m.group(1)), name=m.group(2), apk=m.group(3),
                          rc=None, png=False, uncaught=0, boundary=0, key=[])
        continue
    if cur is None: continue
    m = re.match(r'^rc=(\d+)$', line)
    if m: cur['rc'] = int(m.group(1)); continue
    m = re.match(r'^uncaught_or_synthexc=(\d+) boundary=(\d+) png=(\w+)$', line)
    if m:
        cur['uncaught'] = int(m.group(1)); cur['boundary'] = int(m.group(2))
        cur['png'] = m.group(3) == 'yes'; continue
    if line.startswith('  KEY: '): cur['key'].append(line[7:]); continue
if cur and cur.get('rc') is not None:
    blocks[cur['name']] = cur

synth_re = re.compile(r'SYNTH-EXC\s+(?:\[[^\]]*\]\s*)?([\w.$]+)')
exc_class_re = re.compile(r'([\w.$]+(?:Exception|Error))')

rows = []
recmiss = Counter()          # missing method law census
recmiss_apps = {}            # method -> set of apps
caught = 0                   # EXC-PROPAGATE caught events
for name, cur in blocks.items():
    logf = os.path.join(BASE, name + '.log')
    data = open(logf, errors='replace').read() if os.path.exists(logf) else ''
    rc = cur['rc']; png = cur['png']
    # render evidence from EXP092 framebuffer copy lines
    nw = None; tot = None
    for m in re.finditer(r'\[EXP092-COPY\] framebuffer_ has (\d+) non-white pixels out of (\d+) total', data):
        nw = int(m.group(1)); tot = int(m.group(2))
    if nw is None:
        m = re.search(r'\[EXP092-COPY\] fb has (\d+) non-white pixels out of (\d+) total', data)
        if m: nw = int(m.group(1)); tot = int(m.group(2))
    render_frac = (nw / tot) if (nw is not None and tot) else 0.0
    rendered = png and (render_frac > 0.01)
    blank = png and not rendered
    # exceptions: first and last
    excs = synth_re.findall(data)
    first_exc = excs[0] if excs else None
    last_exc = excs[-1] if excs else None
    # REC-MISS census
    for m in re.finditer(r'\[REC-MISS\] ([\w/$.;]+) caller=', data):
        meth = m.group(1)
        recmiss[meth] += 1
        recmiss_apps.setdefault(meth, set()).add(name)
    caught += len(re.findall(r'\[EXC-PROPAGATE\][^\n]*caught at', data))
    # classification
    if rendered and rc == 0 and not excs: cls = 'A_FULL_CLEAN'
    elif rendered and rc == 0: cls = 'B_RENDER_EXC_SEEN'
    elif rendered and rc != 0: cls = 'C_RENDER_RC1'
    elif blank and rc == 0: cls = 'D_BLANK_RC0'
    elif blank: cls = 'E_BLANK_RC1'
    elif not png and rc == 0: cls = 'F_NOPNG_RC0'
    else: cls = 'G_NO_RENDER_RC1'
    rows.append(OrderedDict(
        name=name, apk=cur['apk'], rc=rc, cls=cls, png=png,
        nonwhite=nw, total=tot, render_frac=round(render_frac, 4),
        uncaught=cur['uncaught'], first_exc=first_exc, last_exc=last_exc))

cls_census = Counter(r['cls'] for r in rows)
out = OrderedDict(total=len(rows), classification=dict(cls_census),
                  caught_exception_events=caught, rows=rows)
json.dump(out, open(os.path.join(BASE, 'scorecard2.json'), 'w'), indent=1, ensure_ascii=False)

print(f'NEW-CORPUS APPS: {len(rows)}')
for k, v in sorted(cls_census.items()):
    print(f'  {k}: {v}')
print(f'EXC-PROPAGATE caught events (app handlers WORKING): {caught}')
print('\nTOP REC-MISS (engine missing laws) by distinct apps:')
for meth, cnt in recmiss.most_common(30):
    print(f'  {len(recmiss_apps[meth])} apps / {cnt}x  {meth}')
json.dump({m: sorted(a) for m, a in recmiss_apps.items()},
          open(os.path.join(BASE, 'recmiss_map.json'), 'w'), indent=1)
