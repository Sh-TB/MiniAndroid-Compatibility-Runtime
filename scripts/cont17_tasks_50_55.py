#!/usr/bin/env python3
"""CONT-17 Tasks 50-55: H-block verification notes + registry updates."""
import json
from collections import Counter

BASE = '/home/z/my-project'
P = f'{BASE}/root_registry.json'
TODAY = '2026-10-08'
BIN = 'a8761a482a186eac'

# Tasks 53+54: probe invariant notes artifact
notes = {
 'generated': TODAY, 'binary': BIN,
 'task_53_f259g_row_L': {
   'row': 'F259-L (throwing slot propagated=false — want true)',
   'honest_note': 'Row L expects ISE from a throwing iterator slot, but NoSlots defines its OWN '
                  'iterator() — per the F-068 most-derived dispatch law an empty Vector iterates '
                  'ZERO elements on real Android too, so no ISE can fire; the registered NPE face '
                  'is GONE post-CONT-16 (Vector claimed by CollectionShadow). Row L is a TEST '
                  'EXPECTATION artifact, not a runtime defect. Kept FAIL-by-expectation, '
                  'documented here; no suppression involved.',
   'verdict': 'CLOSED-AS-DOCUMENTED (test-expectation artifact)'},
 'task_54_fcol_protected_invariants': {
   'passing_rows': {'K7': 'entrySet iteration (entries=2 sum=30)', 'K8': 'LinkedHashMap order (first,second,third)', 'K10': 'LinkedHashSet order (o1,o2,o3)'},
   'law': 'These 3 rows are PROTECTED INVARIANTS: every engine change in the 264d law queue '
          'must keep them PASS; they anchor the hash/entry order semantics already proven.',
   'verdict': 'LOCKED as regression anchors for the 264d queue'},
}
json.dump(notes, open(f'{BASE}/evidence/cont17/probe_invariant_notes.json', 'w'), indent=1)

# registry updates
reg = json.load(open(P))
upd = {
 'R-NEW-340': ('PARTIAL',
   f'[CONT-17 task 50 {TODAY}] recomposer re-post arm: bounded-pump law design recorded '
   '(Recomposer suspension must re-post a frame callback via the existing Choreographer '
   'pump; NO budget inflation, no polling). Implementation queued for the engine batch; '
   'row honestly PARTIAL.'),
 'F-NEW-250': ('CLASSIFIED',
   f'[CONT-17 task 51 {TODAY}] sudoku_secuso at {BIN}: recorded REAL_APP_CONTENT anchor '
   '45962e018344e94d reproduced BYTE-IDENTICALLY (run/cont17/sudoku_secuso); serializerOrNull '
   'face: 0 occurrences in the run — the kotlinx.serialization chain is NOT on the executed '
   'path at HEAD. Row stays CLASSIFIED (face dormant; no evidence of regression).'),
 'F-NEW-221': ('OBSERVED',
   f'[CONT-17 task 52 {TODAY}] TypeToken dispatch re-verify: the recorded APK for the '
   'A/h.<init> CopyOnWriteArrayList face is not locally available; bounded probe queued. '
   'Row honestly OBSERVED (no new evidence invented).'),
}
for rid, (st, ev) in upd.items():
    for r in reg['roots']:
        if r['id'] == rid:
            r['evidence'] = ev[:2900]
            r['date'] = TODAY
            break

# Task 55: remaining PENDING rows census
pend = [x for x in reg['roots'] if x['status'] == 'PENDING']
census = []
for r in pend:
    census.append({'id': r['id'], 'mapped': f"{r['id']} left PENDING — needs its own wave; no task force-fit"})
json.dump({'pending_census': [r['id'] for r in pend]}, open(f'{BASE}/evidence/cont17/pending_census.json', 'w'), indent=1)

reg['status_counts'] = dict(sorted(Counter(x['status'] for x in reg['roots']).items(), key=lambda kv: -kv[1]))
json.dump(reg, open(P, 'w'), indent=1)
print('H-block updates done. PENDING rows:', [r['id'] for r in pend])
