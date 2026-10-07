#!/usr/bin/env python3
"""CONT-17 Task 20: backfill null-title/layer registry rows from knowledge_graph.json
(bounded to rows whose title is null/empty). Writes evidence/cont17/title_backfill.json."""
import json

P = '/home/z/my-project/root_registry.json'
KG = '/home/z/my-project/docs/foundation/knowledge_graph.json'
OUT = '/home/z/my-project/evidence/cont17/title_backfill.json'

reg = json.load(open(P))
kg = json.load(open(KG))

# knowledge_graph: collect entries keyed by failure id
entries = {}
def walk(o):
    if isinstance(o, dict):
        if 'failure' in o and isinstance(o.get('failure'), str) and o['failure'].strip():
            entries.setdefault(o['failure'], o)
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(kg)

backfilled, still_null = [], 0
for r in reg['roots']:
    if r.get('title'):
        continue
    rid = r['id']
    e = entries.get(rid)
    if not e:
        still_null += 1
        continue
    cause = (e.get('root_cause') or e.get('observed') or '').strip()
    if not cause:
        still_null += 1
        continue
    title = f"{rid}: {cause[:220]}"
    if r.get('layer') is None and e.get('method'):
        pass  # layer stays None — no evidence, do not invent
    r['title'] = title
    backfilled.append({'id': rid, 'title': title})

json.dump({'backfilled': backfilled, 'still_null': still_null},
          open(OUT, 'w'), indent=1)
json.dump(reg, open(P, 'w'), indent=1)
print(f"backfilled {len(backfilled)} titles; still null: {still_null}")
for b in backfilled[:10]:
    print(' ', b['id'], '->', b['title'][:90])
