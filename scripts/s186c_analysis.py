#!/usr/bin/env python3
"""S186c analysis: stuck-titles re-battery → completion matrix.
Groups first-uncaught signatures into law families, compares against the
S186 census (issue-era state, mostly 2026-09-22) with today's engine state,
and emits the family→law→next-move table for the report.
"""
import json, re
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s186_s107'
BAT = json.load(open(OUT / 'S186C_STUCK_BATTERY.json'))
CEN = json.load(open(OUT / 'S186_INCOMPLETE_CENSUS.json'))
CENROWS = {int(r['issue']): r for r in CEN['rows'] if r['bucket'] in
           ('EXECUTED_CRASHED', 'LOADED_PARTIAL', 'EXECUTED_PARTIAL')}

FAM_RULES = [
    ('Resources$NotFoundException', 'F-RES/resource-missing'),
    ('androidx/', 'F-ANDROIDX'),
    ('compose', 'F-COMPOSE'),
    ('SharedLibraryLoad', 'F-NATIVE-LOAD'),
    ('UnsatisfiedLinkError', 'F-NATIVE-LOAD'),
    ('IllegalStateException', 'F-STATE'),
    ('NullPointerException', 'F-NPE'),
    ('ClassNotFound', 'F-CLASS-MISSING'),
    ('NoClassDefFoundError', 'F-CLASS-MISSING'),
    ('VerifyError', 'F-VERIFY'),
]


def fam(sig):
    for pat, f in FAM_RULES:
        if pat in sig:
            return f
    return 'F-OTHER' if sig else '-'


rows = BAT['results']
matrix = []
for r in rows:
    issue = r['issue']
    pkg = r['pkg']
    c = CENROWS.get(issue, {})
    sig = r.get('first_uncaught', '') or ''
    # pull the exception class + unwound frame out of the trace line
    m = re.search(r'EXC-UNCAUGHT-TOP\].*?L([^;]+);', sig)
    exc_class = m.group(1).replace('/', '.') if m else (
        'no-uncaught' if r.get('uncaught_total', 0) == 0 else 'unknown')
    m2 = re.search(r'unwound L([^;]+)\;\.(\S+)', sig)
    frame = f"{m2.group(1)}.{m2.group(2)}" if m2 else ''
    matrix.append(dict(
        issue=issue, pkg=pkg, status=r.get('status'),
        issue_state=c.get('state', ''), issue_bucket=c.get('bucket', ''),
        face=r.get('face'), tier=r.get('tier'),
        colors=r.get('unique_colors'), nonbg=r.get('nonbg_share'),
        uncaught=r.get('uncaught_total'), exc_class=exc_class, frame=frame,
        family=fam(sig), sig=sig[:150]))

by_fam = defaultdict(list)
for r in matrix:
    by_fam[r['family'] if r['family'] != '-' else
           ('NO-UNCAUGHT' if r.get('uncaught') == 0 else 'OTHER')].append(r)

print(f"n={len(matrix)}")
print('\n== today tiers ==')
print(Counter(r.get('tier') for r in matrix).most_common())
print('\n== uncaught distribution ==')
print('0 uncaught:', sum(1 for r in matrix if r.get('uncaught') == 0),
      '/', len([r for r in matrix if r.get('status') == 'RAN']))
print('\n== families ==')
for f, rs in sorted(by_fam.items(), key=lambda kv: -len(kv[1])):
    print(f"{len(rs):3d}  {f}")
    for r in sorted(rs, key=lambda x: x['issue'])[:14]:
        print(f"     #{r['issue']:3d} {r['pkg'][:42]:42s} tier={r.get('tier','')[:9]:9s} "
              f"un={r.get('uncaught','')} exc={r['exc_class'][:44]:44s} {r['frame'][:40]}")

json.dump(dict(schema='s186c_matrix/v1', n=len(matrix), rows=matrix,
               families={f: len(rs) for f, rs in by_fam.items()}),
          open(OUT / 'S186C_COMPLETION_MATRIX.json', 'w'), indent=1)
print(f"\n-> {OUT}/S186C_COMPLETION_MATRIX.json")
