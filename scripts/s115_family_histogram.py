#!/usr/bin/env python3
"""S115 family histogram — first-uncaught-exception families across the 77 sweep logs."""
import json, re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path('/home/z/my-project')
state = json.load(open(BASE / 'run/s115_sweep/state.json'))

fam = Counter()
members = defaultdict(list)
for key, rec in sorted(state.items(), key=lambda kv: int(kv[0])):
    n, pkg = rec['ticket'], rec['package']
    log = BASE / 'evidence/s115_sweep' / f"t{n}_{pkg}" / 'run.log'
    text = log.read_text(errors='ignore') if log.exists() else ''
    if not text.strip():
        fam['NO_LOG'] += 1; members['NO_LOG'].append(n); continue
    # last uncaught / app-boundary line = the death cause
    un = re.findall(r'\[EXCEPTION\] method=(\S+) .*?exception=(\S+); msg="([^"]{0,90})"', text)
    boundary = re.findall(r'uncaught at caller (\S+)', text)
    first_exc = None
    m = re.search(r'\[EXCEPTION\] method=(\S+) .*?exception=(\S+); msg="([^"]{0,110})"', text)
    if m:
        first_exc = f'{m.group(2)} @ {m.group(1).split("/")[-1]} :: {m.group(3)[:60]}'
    keyf = boundary[-1] if boundary else (first_exc or ('EARLY-DEATH rc=%s' % rec.get('rc')))
    # normalize: keep exception type + caller class (strip method noise)
    fam[keyf] += 1
    members[keyf].append(n)

for k, v in fam.most_common(20):
    print(f'{v:3d}  {k[:120]}')
    if v <= 6:
        print(f'       tickets: {members[k]}')
json.dump({k: members[k] for k in members}, open(BASE/'run/s115_sweep/families.json','w'), indent=1)
