#!/usr/bin/env python3
"""S88 §0 RECON — registry real-state numbers. READ-ONLY."""
import json, collections, sys

R = json.load(open('/home/z/my-project/docs/evidence/canonical/registry.json'))
T = R['titles']

def dist(key):
    return dict(collections.Counter(str(t.get(key)) for t in T))

print('=== REGISTRY', R['wave'], '| titles:', len(T), '===')
print('type:', dist('type'))
print('status:', dist('status'))
print('level:', dist('level'))
print('proven:', dist('proven'))
print('launched:', dist('launched'))
print('rendered:', dist('rendered'))
print('interacted:', dist('interacted'))
print('state_changed:', dist('state_changed'))
print('last_success_stage:', dist('last_success_stage'))

# artifact kinds
ak = collections.Counter((t.get('artifact_kind') or 'NONE') for t in T)
print('artifact_kind:', dict(ak))

# remaining/divergence summary (top 12)
rem = collections.Counter()
for t in T:
    r = (t.get('remaining') or t.get('first_divergence') or '')
    rem[r[:90]] += 1
print('--- top remaining/divergence (12) ---')
for k, v in rem.most_common(12):
    print(f'{v:3d}  {k}')

# waves by session field
wv = collections.Counter(str(t.get('session'))[:4] for t in T)
print('session prefix:', dict(wv))

# OPEN root causes
try:
    rc = json.load(open('/home/z/my-project/docs/evidence/canonical/registry.json'))
except Exception:
    pass
