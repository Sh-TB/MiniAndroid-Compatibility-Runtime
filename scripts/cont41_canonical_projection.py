#!/usr/bin/env python3
"""CONT-41 — regenerate the canonical root_cause_registry.json projection
from root_registry.json (the single writable store). Projection law: read
model only. Appends the ids the store has and the projection lacks (the
CONT-38/39/40/41 waves), preserving the list shape."""
import json

store = json.load(open("root_registry.json"))
proj = json.load(open("canonical/root_cause_registry.json"))
have = {r.get("id") for r in proj}
added = 0
for r in store:
    if r.get("id") not in have:
        proj.append({k: r[k] for k in r if k != "roots"})  # flat row copy
        added += 1
json.dump(proj, open("canonical/root_cause_registry.json", "w"),
          ensure_ascii=False, indent=1)
print(f"canonical projection {len(proj)-added} -> {len(proj)} (+{added}) "
      f"store={len(store)} id-unique={len({r.get('id') for r in proj}) == len(proj)}")
