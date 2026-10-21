#!/usr/bin/env python3
# cont154_parse.py — parse big-corpus battery into scorecard + WHY census
import glob, json, os, re, gzip, hashlib
from collections import Counter, OrderedDict

BASE = '/home/z/my-project/run/c154'

# --- parse battery.log into per-app blocks (last complete block per app wins) ---
blocks = OrderedDict()
cur = None
for line in open(os.path.join(BASE, 'battery.log'), errors='replace'):
    line = line.rstrip('\n')
    m = re.match(r'^== WAGON (\d+) (\S+) apk=(\S+) ==', line)
    if m:
        if cur and cur.get('rc') is not None:
            blocks[cur['name']] = cur
        cur = OrderedDict(idx=int(m.group(1)), name=m.group(2), apk=m.group(3),
                          rc=None, face='NO_SCREENSHOT', png=False,
                          uncaught=0, boundary=0, key=[])
        continue
    if cur is None:
        continue
    m = re.match(r'^rc=(\d+)$', line)
    if m:
        cur['rc'] = int(m.group(1)); continue
    m = re.match(r'^face=([0-9a-f]+|NO_SCREENSHOT)$', line)
    if m:
        cur['face'] = m.group(1); continue
    m = re.match(r'^uncaught_or_synthexc=(\d+) boundary=(\d+) png=(\w+)$', line)
    if m:
        cur['uncaught'] = int(m.group(1)); cur['boundary'] = int(m.group(2))
        cur['png'] = m.group(3) == 'yes'; continue
    if line.startswith('  KEY: '):
        cur['key'].append(line[7:]); continue
if cur and cur.get('rc') is not None:
    blocks[cur['name']] = cur

rows = []
exc_class_re = re.compile(r'([\w.$]+(?:Exception|Error))')
synth_re = re.compile(r'SYNTH-EXC\s+(?:\[[^\]]*\]\s*)?([\w.$]+)')
for name, cur in blocks.items():
    logf = os.path.join(BASE, name + '.log')
    data = ''
    if os.path.exists(logf):
        data = open(logf, errors='replace').read()
    rc = cur['rc']; face = cur['face']; png = cur['png']
    uncaught = cur['uncaught']; boundary = cur['boundary']
    # first exception class: prefer KEY lines, then synth in full log, then generic
    exc_cls = None
    for k in cur['key']:
        m = synth_re.search(k)
        if m: exc_cls = m.group(1); break
        m = re.match(r'(?:Uncaught|uncaught).*?([\w.$]+(?:Exception|Error))', k)
        if m: exc_cls = m.group(1); break
    if exc_cls is None:
        m = synth_re.search(data)
        if m: exc_cls = m.group(1)
        else:
            m2 = exc_class_re.search(data)
            exc_cls = m2.group(1) if m2 else None
    # engine stage reach markers
    stage = 0
    if 'stage=load_apk ok=1' in data: stage = 1
    if 'stage=' in data:
        st = re.findall(r'\[(?:BOOT-ORDER)\] (\d+)/7 stage=([\w_]+)', data)
        if st:
            stage = max(int(n) for n, _ in st)
    if rc == 0 and png and uncaught == 0: cls = 'CLEAN'
    elif rc == 0 and png and uncaught > 0: cls = 'RC0_RENDER+EXC'
    elif rc == 0 and not png: cls = 'RC0_BLANK_FACE'
    elif rc == 1: cls = 'EXC_CRASH'
    elif rc == 124: cls = 'TIMEOUT'
    elif rc == 139: cls = 'SIGSEGV'
    elif rc == 137: cls = 'KILLED'
    elif rc is None: cls = 'INCOMPLETE'
    else: cls = f'RC_OTHER({rc})'
    rows.append(OrderedDict(
        name=name, apk=cur['apk'], rc=rc, cls=cls, png=png, face=face,
        uncaught=uncaught, boundary=boundary, stage=stage,
        exc_class=exc_cls, key=cur['key'][:2]))

census_rc = Counter(r['cls'] for r in rows)
census_exc = Counter(r['exc_class'] for r in rows if r['exc_class'] and r['cls'] in ('EXC_CRASH',))
stage_max = max((r['stage'] for r in rows), default=0)

out = OrderedDict(
    total_apps=len(rows),
    classification=dict(census_rc),
    crash_exception_census=census_exc.most_common(15),
    max_boot_stage=stage_max,
    rows=rows)
with open(os.path.join(BASE, 'scorecard.json'), 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print(f'TOTAL NEW-CORPUS APPS TESTED: {len(rows)}')
for k, v in census_rc.most_common():
    print(f'  {k}: {v}')
print('TOP CRASH EXCEPTION CLASSES:')
for k, v in census_exc.most_common(12):
    print(f'  {v}x {k}')

# merge with canonical c129 scorecard for grand total
c129 = os.path.join('/home/z/my-project/run/c129', 'scorecard.json')
if os.path.exists(c129):
    d = json.load(open(c129))
    canon = d.get('rows') or d.get('apps') or []
    print(f'\nCANONICAL (c129) rows: {len(canon)}')
    grt = len(rows) + len(canon)
    print(f'GRAND TOTAL APPS TESTED: {grt}')
    ccls = Counter()
    for a in canon:
        c = a.get('classification') or a.get('cls') or a.get('category')
        ccls[str(c)] += 1
    for k, v in ccls.most_common():
        print(f'  canon {k}: {v}')
