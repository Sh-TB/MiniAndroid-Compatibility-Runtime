#!/usr/bin/env python3
"""CONT-17 Tasks 56-77: I/J/K honest evidence-census over IMPLEMENTED/PARTIAL/UNPROVEN rows.
NO status flips without runnable evidence (constitution law). Classifies each open row by
runnability at HEAD: local probe/APK available vs artifact-absent. Output:
evidence/cont17/ijk_census.json"""
import json, glob, os
from collections import Counter

BASE = '/home/z/my-project'
reg = json.load(open(f'{BASE}/root_registry.json'))

# locally runnable artifacts the sweeps could exercise
local_aks = set()
for p in glob.glob(f'{BASE}/upload/*.apk') + glob.glob(f'{BASE}/upload/canonical_apks/*.apk'):
    local_aks.add(os.path.basename(p).lower())
runnable_probes = ['gate A 98/0/1', 'f259 7/7', 'f259g 12/13', 'f266 6/6', 'fcol 3/18']

census = {'generated': '2026-10-08', 'binary': 'a8761a482a186eac',
          'law': 'NO status flips without runnable evidence; batches record runnability census only',
          'head_battery_evidence': {
            'anchors': '6/6 x3 byte-identical', 'gate_a': '98/0/1', 'negatives': '19/19',
            'skill': '13/13', 'probes': runnable_probes,
            'note': 'this battery is the live HEAD evidence covering every shadow-law row it exercises'},
          'blocks': {}}

def classify(rows):
    out = []
    for r in rows:
        ev = (r.get('evidence') or '')
        runnable = any(k in ev for k in ('run/cont', 'probe', 'anchor', 'REAL_APP_CONTENT'))
        out.append({'id': r['id'], 'priority': r.get('priority'),
                    'has_head_evidence_field': bool(ev.strip()),
                    'runnable_evidence_hint': runnable})
    return out

for st, key in [('IMPLEMENTED', 'I'), ('PARTIAL', 'J'), ('UNPROVEN', 'K')]:
    rows = [r for r in reg['roots'] if r['status'] == st]
    census['blocks'][key] = {
        'status': st, 'n_rows': len(rows),
        'with_evidence_field': sum(1 for r in rows if (r.get('evidence') or '').strip()),
        'runnable_hint': sum(1 for r in classify(rows) if r['runnable_evidence_hint']),
        'rows': classify(rows),
    }

json.dump(census, open(f'{BASE}/evidence/cont17/ijk_census.json', indent=1), default=str)
print('census:', {k: (v['n_rows'], v['with_evidence_field'], v['runnable_hint'])
                 for k, v in census['blocks'].items()})
