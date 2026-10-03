#!/usr/bin/env python3
"""CONT-M1 — regenerate the canonical root_cause_registry.json PROJECTION
from the single writable store root_registry.json (s125 schema, projection
law: read model only, no hand-editing). Resolves the 492/516-vs-535 lag the
continuation §5 M1 flagged: the projection had not been regenerated after
waves R-NEW-443..462 / F-NEW-222..233 landed in the writable store.
"""
import json
from collections import Counter
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
rr = json.load(open('root_registry.json'))
roots = rr['roots']
root_stats = Counter(r.get('status', '?') for r in roots)
proj = {
    '_projection_of': 'root_registry.json',
    '_law': ('root_registry.json is the single writable store; this file is a '
             'generated read model (ROADMAP SS3: no duplicate canonical '
             'registries).'),
    'generated': NOW,
    'total': len(roots),
    'total_roots': len(roots),
    'status_counts': dict(root_stats),
    'roots': [{
        'id': r.get('id'),
        'title': r.get('title') or r.get('name'),
        'status': r.get('status'),
        'priority': r.get('priority'),
        'layer': r.get('layer') or r.get('area'),
    } for r in roots],
}
with open('canonical/root_cause_registry.json', 'w') as f:
    json.dump(proj, f, indent=1)
print('projection regenerated:', len(roots), 'roots; statuses:', dict(root_stats))
# verify identity against the writable store
check = json.load(open('canonical/root_cause_registry.json'))
assert check['total'] == len(roots), 'projection drift'
ids_store = [r['id'] for r in roots]
ids_proj = [r['id'] for r in check['roots']]
assert ids_store == ids_proj, 'id order drift'
print('identity verified: projection == writable store (id-for-id)')
