#!/usr/bin/env python3
"""CONT-117 wagon: reconcile root_registry.json with canonical/root_cause_registry.json
for the 2 stale IDs left by CONT-116 (same pattern CONT-111 fixed for CONT-108).
Mirror (canonical/) is the authoritative fresh copy; main gets its entries synced by ID.
Nothing else touched; id-uniqueness verified both ways afterwards."""
import json, sys

MAIN = 'root_registry.json'
MIRROR = 'canonical/root_cause_registry.json'
SYNC_IDS = ('F-NEW-465', 'F-NEW-449')

main = json.load(open(MAIN))
mirror = json.load(open(MIRROR))
mi = {r['id']: r for r in main}
mr = {r['id']: r for r in mirror}

for rid in SYNC_IDS:
    if rid not in mi:
        print(f'ERROR: {rid} not in main', file=sys.stderr); sys.exit(1)
    if rid not in mr:
        print(f'ERROR: {rid} not in mirror', file=sys.stderr); sys.exit(1)
    print(f'{rid}: status {mi[rid].get("status")} -> {mr[rid].get("status")}')
    mi[rid] = mr[rid]

# preserve original list order in main
out = [mi[r['id']] for r in main]
json.dump(out, open(MAIN, 'w'), indent=1, ensure_ascii=False)

# verify both ways
m2 = json.load(open(MAIN))
ids_main = [r['id'] for r in m2]
ids_mir = [r['id'] for r in json.load(open(MIRROR))]
assert len(ids_main) == len(set(ids_main)) == 780, 'main not 780 id-unique'
assert len(ids_mir) == len(set(ids_mir)) == 780, 'mirror not 780 id-unique'
mi2 = {r['id']: r for r in m2}
mr2 = {r['id']: r for r in json.load(open(MIRROR))}
diff = [k for k in set(mi2) | set(mr2) if mi2.get(k) != mr2.get(k)]
print(f'post-sync: main=780 id-unique, mirror=780 id-unique, differing_ids={len(diff)}')
print('main==mirror:', len(diff) == 0)
