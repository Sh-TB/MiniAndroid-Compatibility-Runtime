#!/usr/bin/env python3
"""CONT-11 (local): FULL review of ALL registered problems at merged HEAD 276f7628.
Per-status breakdown + the true OPEN set (CLASSIFIED/PARTIAL/OPEN/BLOCKED/etc)
+ per-family common-root analysis + per-title batch state."""
import json, collections, re

BASE = '/home/z/my-project'
with open(f'{BASE}/root_registry.json') as f:
    roots = json.load(f)

print(f'TOTAL ROOTS: {len(roots)}')

FIXEDISH = {'ROOT-CAUSED-FIXED', 'ROOT_CAUSED_FIXED', 'VERIFIED-FIXED', 'ALREADY_FIXED_AND_TESTED',
            'ROOT-CAUSED-CLOSED', 'VERIFIED-CORRECT', 'NOT-APPLICABLE', 'IMPLEMENTED',
            'IMPLEMENTED+TESTED', 'VERIFIED', 'STALE_OR_SUPERSEDED', 'SUPERSEDED-BY-EVIDENCE',
            'DUPLICATE-SUPERSEDED', 'REJECTED_WITH_REASON', 'USED_BY_EXECUTION', 'INFRA-LANDED'}
TRULY_OPEN = {'CLASSIFIED', 'PARTIAL', 'BLOCKED', 'OBSERVED', 'TESTED', 'ROOT-CAUSED-PARTIAL'}

open_roots = [r for r in roots if r.get('status') not in FIXEDISH]
print(f'\nNOT-FIXED (all): {len(open_roots)}')
truly = [r for r in roots if r.get('status') in TRULY_OPEN]
print(f'TRULY OPEN ({TRULY_OPEN}): {len(truly)}')

print('\n== ALL TRULY-OPEN ROOTS (id / status / layer / title) ==')
for r in sorted(truly, key=lambda x: x['id']):
    t = (r.get('title') or '')[:110].replace('\n', ' ')
    print(f"  {r['id']:16s} {r.get('status','?'):20s} {str(r.get('layer'))[:28]:28s} {t}")

# summary.open_frontiers
with open(f'{BASE}/root_registry.json') as f:
    raw = json.load(f)
print('\n(roots is a plain list at this HEAD)')
