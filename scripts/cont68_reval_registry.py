#!/usr/bin/env python3
"""cont68_reval_registry.py — append F-NEW-369 (CLASSIFIED) from the CONT-68
closeout revalidation and reconcile count metadata. The writable store is
root_registry.json (canonical/root_cause_registry.json is its projection)."""
import json
import collections

P = 'root_registry.json'
d = json.load(open(P))

ids = [r.get('id') for r in d['roots']]
assert 'F-NEW-369' not in ids, 'F-NEW-369 already present'

row = {
    "id": "F-NEW-369",
    "status": "CLASSIFIED",
    "priority": "P3",
    "layer": "dalvik/first-launch init path (cold data sandbox)",
    "title": ("Privacy Friendly Memory FIRST-LAUNCH (cold data sandbox) diverges from the warm-launch acceptance face: on a wiped data root the app's first-run path executes "
              "ResIdAdapter.getResourceName where the engine answers REC-MISS for Ljava/util/LinkedList;.<init> (and List.iterator) on that path, the list stays null and the app NPEs "
              "('Iterator;.hasNext' on a null object reference) uncaught at SplashActivity.onCreate invoke_pc=17 -> white face 31ddd4d5b8e6d18e; every subsequent WARM launch is "
              "byte-deterministic real content c559b630dd8f0f0f (revalidation x5). Not a theme-family defect (0 theme ISE in the cold log; the createSubDecor guard passes for the correct "
              "semantic reason). Named levers: (a) decode why the first-run branch constructs LinkedList via a receiver-shape the interpreter misses on that path only; (b) decide whether "
              "the cold/warm split is app-faithful (real devices also persist first-run state) — the recorded CONT-68 acceptance x3 was taken on the S59-warm sandbox, which is now "
              "documented. Evidence: run/s60/reval_memory_r1.log (cold) vs reval_memory_r4..r6.log (warm) at binary a20998cf4d8a19cd."),
    "evidence": "run/s60/reval_memory_r{1,4,5,6}/; run/s60/reval_memory_r1.log; evidence/cont68/cont68_wave_evidence.json",
    "probe": "upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk",
    "verified_current": True,
}
d['roots'].append(row)

d['total_roots'] = len(d['roots'])
d['total'] = d['total_roots']
d['count'] = d['total_roots']
sc = collections.Counter(r['status'] for r in d['roots'])
d['status_counts'] = dict(sorted(sc.items()))
d['generated'] = '2026-10-15 13:20:00 (CONT-68 closeout revalidation: F-NEW-369 appended; counts reconciled to actual rows)'

json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print('appended F-NEW-369; total_roots =', d['total_roots'])
print('CLASSIFIED count =', sc['CLASSIFIED'])
