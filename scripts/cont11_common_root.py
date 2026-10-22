#!/usr/bin/env python3
"""CONT-11: Quantitative common-root analysis over ALL 566 registry roots.
Groups every root into families by title/layer keywords, then shows:
  - family sizes, fix rates
  - the 'common root' verdict: how many problems funnel through how many families
Outputs docs/CONT11_COMMON_ROOT_ANALYSIS.jsonl + .md"""
import json, collections, re

BASE = '/home/z/my-project'
with open(f'{BASE}/root_registry.json') as f:
    reg = json.load(f)
roots = reg['roots']

FIXED = {'ROOT-CAUSED-FIXED', 'ROOT_CAUSED-FIXED', 'VERIFIED-FIXED', 'PROVEN-FIXED',
         'FIXED-VERIFIED', 'FIXED-S75', 'PARTIAL-FIX', 'ROOT-CAUSED-CLOSED',
         'ROOT-CAUSED-REMEASURED-GENERIC-OK'}
GOOD = FIXED | {'VERIFIED-CORRECT', 'NOT-APPLICABLE', 'IMPLEMENTED', 'IMPLEMENTED+TESTED',
                'VERIFIED', 'VERIFIED_3RUN', 'SUPERSEDED-BY-EVIDENCE', 'USED_BY_EXECUTION'}

FAMILIES = [
    ('F1 collections/iterator shadows', ['iterator', 'collection', 'list', 'map', 'set', 'arraylist', 'hashmap', 'deque', 'treeset', 'vector', 'hashtable', 'addall', 'toarray', 'enumeration', 'cursor', 'remove']),
    ('F2 DEX interpreter/register', ['dex', 'register', 'invoke', 'instance-of', 'instanceof', 'const-string', 'field', 'iget', 'iput', 'sget', 'class-init', 'clinit', 'static', 'method', 'reflection', 'forname', 'class token', 'descriptor', 'bytecode']),
    ('F3 Compose runtime chain', ['compose', 'snapshot', 'recomposition', 'slot', 'changelist', 'change-list', 'navigation', 'navhost', 'materiali', 'composer', 'applier', 'subcompose', 'derived']),
    ('F4 renderer / frame-truth', ['render', 'frame', 'canvas', 'draw', 'pixel', 'framebuffer', 'screenshot', 'surface', 'layoutnode', 'viewtree', 'window', 'bitmap', 'graphic']),
    ('F5 native/JNI/ABI', ['native', 'jni', 'dlopen', 'so ', 'elf', 'abi', 'arm', 'libprobe', 'linker']),
    ('F6 framework/platform services', ['service', 'broadcast', 'intent', 'provider', 'contentresolver', 'cursor transport', 'package', 'activity', 'lifecycle', 'context', 'sharedpref', 'notification', 'webview', 'resource', 'asset']),
    ('F7 IO/serialization/json', ['io ', 'file', 'stream', 'reader', 'writer', 'json', 'serial', 'parcel', 'bundle', 'stringwriter', 'buffer']),
    ('F8 concurrency/virtual-time', ['thread', 'concurrent', 'schedul', 'timer', 'virtual time', 'atomic', 'executor', 'coroutine', 'cancel']),
]

def classify(r):
    text = (str(r.get('title') or '') + ' ' + str(r.get('layer') or '')).lower()
    for fam, kws in FAMILIES:
        for kw in kws:
            if kw in text:
                return fam
    return 'F0 other/registry-mechanics'

fam_stats = collections.defaultdict(lambda: collections.Counter())
fam_roots = collections.defaultdict(list)
for r in roots:
    fam = classify(r)
    fam_stats[fam]['total'] += 1
    if r.get('status') in FIXED:
        fam_stats[fam]['fixed'] += 1
    elif r.get('status') in GOOD:
        fam_stats[fam]['good'] += 1
    else:
        fam_stats[fam]['open'] += 1
        fam_roots[fam].append(r)

print(f"{'FAMILY':45s} {'total':>6s} {'fixed':>6s} {'good':>6s} {'open':>6s}")
totals = collections.Counter()
for fam, st in sorted(fam_stats.items(), key=lambda x: -x[1]['total']):
    print(f"{fam:45s} {st['total']:6d} {st['fixed']:6d} {st['good']:6d} {st['open']:6d}")
    for k in ('total', 'fixed', 'good', 'open'):
        totals[k] += st[k]
print(f"{'TOTAL':45s} {totals['total']:6d} {totals['fixed']:6d} {totals['good']:6d} {totals['open']:6d}")

# list ALL open roots with family
print("\n== OPEN ROOTS BY FAMILY ==")
for fam in sorted(fam_roots, key=lambda f: -len(fam_roots[f])):
    print(f"\n--- {fam} ({len(fam_roots[fam])} open) ---")
    for r in fam_roots[fam][:50]:
        t = (r.get('title') or '')[:100]
        print(f"  {r['id']:14s} {r.get('status','?'):22s} {t}")

# save jsonl
out = {'generated': 'CONT-11', 'families': {}}
for fam, st in fam_stats.items():
    out['families'][fam] = dict(st)
with open(f'{BASE}/docs/CONT11_COMMON_ROOT_ANALYSIS.json', 'w') as f:
    json.dump(out, f, indent=1)
print("\nsaved docs/CONT11_COMMON_ROOT_ANALYSIS.json")
