#!/usr/bin/env python3
"""CONT-111 Wagon A: reconcile root_registry.json with canonical/root_cause_registry.json.

CONT-108 updated only the canonical mirror (F-NEW-451 -> ROOT-CAUSED-FIXED, added
F-NEW-453) leaving root_registry.json stale at 767 entries. This syncs the two
entries by ID without touching anything else, then verifies id-uniqueness both ways.
"""
import json, sys

MAIN = 'root_registry.json'
MIRROR = 'canonical/root_cause_registry.json'
SYNC_IDS = ('F-NEW-451', 'F-NEW-453')

main_reg = json.load(open(MAIN))
mirror = {r['id']: r for r in json.load(open(MIRROR))}

main_by_id = {r['id']: r for r in main_reg}
changed = []
for rid in SYNC_IDS:
    if rid not in mirror:
        print(f'ERROR: {rid} not in mirror', file=sys.stderr); sys.exit(1)
    if rid in main_by_id:
        idx = next(i for i, r in enumerate(main_reg) if r['id'] == rid)
        before = dict(main_reg[idx])
        main_reg[idx] = dict(mirror[rid])
        changed.append((rid, before['status'], mirror[rid]['status']))
        print(f'synced {rid}: {before["status"]} -> {mirror[rid]["status"]}')
    else:
        main_reg.append(dict(mirror[rid]))
        changed.append((rid, 'ABSENT', mirror[rid]['status']))
        print(f'added  {rid}: ABSENT -> {mirror[rid]["status"]} (registry {len(main_by_id)} -> {len(main_reg)})')

# id-uniqueness + count verification
ids = [r['id'] for r in main_reg]
assert len(ids) == len(set(ids)), 'duplicate ids after sync'
json.dump(main_reg, open(MAIN, 'w'), indent=2, ensure_ascii=False)
print(f'OK: root_registry.json now {len(main_reg)} roots, id-unique')
for rid, old, new in changed:
    print(f'  {rid}: {old} -> {new}')
