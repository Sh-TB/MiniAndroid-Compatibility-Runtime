#!/usr/bin/env python3
"""S138 LIGHT TRAINS 11-30 — stats extraction for the 10-program standing queue
+ capability snapshot. One train per program (wagons), generic, no app knowledge."""
import json, hashlib, datetime

REG = 'docs/evidence/canonical/registry.json'
OUT_QUEUE = 'docs/PROGRAM_QUEUE.json'
OUT_CAP = 'evidence/s138_trains/train30_capability_snapshot.json'

reg = json.load(open(REG))
if isinstance(reg, dict):
    reg = reg.get('titles', reg)
by_pkg = {}
for t in reg:
    by_pkg.setdefault(t.get('package', ''), t)

# ---- the standing 10-program queue (user directive: 10 programs ALWAYS in the list)
QUEUE_PKGS = [
    'com.miniandroid.dooz', 'com.miniandroid.opencalc', 'com.miniandroid.chess',
    'com.miniandroid.microtimer', 'com.miniandroid.unote', 'com.miniandroid.tower3d',
    'com.miniandroid.g2048', 'com.miniandroid.tetris', 'com.miniandroid.snakedeluxe',
    'com.miniandroid.minicraft',
]
queue = []
for i, p in enumerate(QUEUE_PKGS, 1):
    t = by_pkg.get(p)
    if t:
        queue.append({
            'slot': i, 'package': p, 'title': t.get('title', p),
            'status': t.get('status', ''), 'level': t.get('level'),
            'level_name': t.get('level_name', ''), 'launched': t.get('launched'),
            'rendered': t.get('rendered'), 'interacted': t.get('interacted'),
            'state_changed': t.get('state_changed'), 'proven': t.get('proven', ''),
            'remaining': (t.get('remaining') or '')[:160],
        })
    else:
        queue.append({'slot': i, 'package': p, 'missing_from_registry': True})
json.dump({'generated': datetime.datetime.now().isoformat(timespec='seconds'),
           'law': '10-program standing queue — every train wave must advance ALL slots, not only dooz',
           'queue': queue}, open(OUT_QUEUE, 'w'), indent=1, ensure_ascii=False)

# ---- interaction & level stats (TRAIN-25 / TRAIN-27 inputs)
interacted = [t for t in reg if t.get('interacted')]
state_changed = [t for t in reg if t.get('state_changed')]
levels = {}
for t in reg:
    levels[t.get('level')] = levels.get(t.get('level'), 0) + 1
statuses = {}
for t in reg:
    statuses[t.get('status', '?')] = statuses.get(t.get('status', '?'), 0) + 1

# 3D answer: tower3d
t3d = by_pkg.get('com.miniandroid.tower3d', {})
dooz = by_pkg.get('com.miniandroid.dooz', {})

cap = {
    'generated': datetime.datetime.now().isoformat(timespec='seconds'),
    'titles_total': len(reg),
    'status_counts': statuses,
    'level_counts': {f'L{k}': v for k, v in sorted(levels.items(), key=lambda x: (x[0] is None, x[0]))},
    'rendered_total': sum(1 for t in reg if t.get('rendered')),
    'interacted_total': len(interacted),
    'interacted_packages': [t.get('package') for t in interacted][:40],
    'state_changed_total': len(state_changed),
    'state_changed_packages': [t.get('package') for t in state_changed][:40],
    'anchor_apps_6': ['opencalc 63020bc7', 'chess 3f7e6707', 'dooz 851cc176',
                      'microtimer bbd350b6', 'unote 7481e9b4', 'tower3d 11a38a5a'],
    'root_registry_roots': len(json.load(open('root_registry.json'))),
    'tower3d_3d_game': {k: t3d.get(k) for k in
                        ('status', 'level', 'level_name', 'interacted', 'state_changed', 'proven', 'notes')},
    'dooz_current': {k: dooz.get(k) for k in
                     ('status', 'level', 'level_name', 'interacted', 'state_changed', 'proven', 'remaining')},
}
json.dump(cap, open(OUT_CAP, 'w'), indent=1, ensure_ascii=False)
print('QUEUE:')
for q in queue:
    print(' ', q.get('slot'), q.get('package'), q.get('status', ''), 'L' + str(q.get('level', '?')),
          'int=' + str(q.get('interacted')), 'chg=' + str(q.get('state_changed')))
print('STATUS:', statuses)
print('LEVELS:', cap['level_counts'])
print('INTERACTED:', len(interacted), cap['interacted_packages'][:15])
print('STATE_CHANGED:', len(state_changed))
print('TOWER3D:', json.dumps(cap['tower3d_3d_game'], ensure_ascii=False)[:400])
print('DOOZ:', json.dumps(cap['dooz_current'], ensure_ascii=False)[:400])
