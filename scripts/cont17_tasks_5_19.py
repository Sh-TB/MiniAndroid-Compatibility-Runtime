#!/usr/bin/env python3
"""CONT-17 Tasks 5-19: D-family live re-verify (evidence JSON + registry notes),
F-NEW-256 / R-NEW-381 supersede linkage, and C-block registry hygiene.

Evidence basis (all at binary a8761a482a186eac, HEAD a6028be6+merge):
- anchors 6/6 x3 byte-identical (run/cont16/reg + /tmp chess rerun)
- dooz traced run run/cont17/dooz_traced: anchor d602648e reproduced,
  verdict DEFAULT_BACKGROUND_ONLY, app_draw_ops=0, draw_walk_ran=True,
  1 uncaught in-flight (La; cascade unwinding Lzs;.m = measure-pass family),
  F-NEW-233 frame-truth verdict line in run.log
- probes f266 6/6, f259 7/7, f259g 12/13, fcol 3/18 (run/cont17/probes)
- gate A 98 PASS / 0 FAIL / 1 INFO; negatives 19/19; skill 13/13
"""
import json, datetime

P = '/home/z/my-project/root_registry.json'
OUT = '/home/z/my-project/evidence/cont17/d_family_reverify.json'
BIN = 'a8761a482a186eac'
TODAY = '2026-10-08'

reg = json.load(open(P))
roots = reg['roots']
by_id = {r['id']: r for r in roots}

BASE_EV = (f'CONT-17 live re-verify at binary {BIN} (2026-10-08): '
           'anchors 6/6 x3 byte-identical (dooz d602648e8e401895 / microtimer '
           'da73010a37dd0189 / unote 4f1a9e4e8f64fae8 / gmdice f3b483fe7b7cf51b / '
           'opencalc a976d2f9fb675cb3 / chess b5a7a35d5fe0564b); probes f266 6/6, '
           'f259 7/7, f259g 12/13 (L honest artifact), fcol 3/18 unchanged; '
           'gate A 98/0/1; negatives 19/19; skill 13/13. '
           'Fresh traced dooz run run/cont17/dooz_traced: anchor reproduced, '
           'F-NEW-233 verdict DEFAULT_BACKGROUND_ONLY first_missing_stage=APP_DRAW_OPS, '
           'app_draw_ops=0 draw_walk_ran=true, 1 uncaught in-flight (La; cascade, '
           'unwind chain through Lzs;.m measure family). ')

DOOZ_CLUSTER = (
    'dooz first-frame cluster re-verified at HEAD: recomposition pass#2 runs '
    '(CONT-10 W6 proof still current — anchors byte-identical), destination '
    'LayoutNodes materialize, but content pixels remain blocked by the single '
    'successor root F-NEW-265 (measure pass dies on null-text ctor chain -> '
    'isPlaced=false -> 0 draw ops). Status kept PARTIAL — sub-face advanced, '
    'row stays honest. evidence/cont17/d_family_reverify.json')

notes = {
 'R-NEW-001': ('MessageQueue/Handler/Looper async-ordering law exercised live at HEAD by '
               'microtimer anchor x3 (Handler-timer countdown app, byte-identical) and the '
               'dooz Choreographer frame pump (40-frame traced run, draw_walk_ran). '
               'Recorded PARTIAL gaps (deep ordering edges) not re-tested this sweep — row kept PARTIAL.'),
 'R-NEW-061': ('Compose continuation chain (AndroidUiDispatcher + J$c runnables) exercised '
               'by the fresh traced dooz run at HEAD (recomposition pass#2, scope re-invocation '
               'per CONT-10 W6, anchors byte-identical). Recorded blocker Job-active-cancellation '
               'superseded by F-NEW-265 as the current content frontier. Kept PARTIAL.'),
 'R-NEW-242': ('First frame end-to-end confirmed at HEAD: frame pump + composition pass#2 + '
               'LayoutNode materialization + background frame emitted (anchor d602648e x3). '
               'Content pixels blocked by F-NEW-265. Kept PARTIAL.'),
 'R-NEW-246': ('dooz onCreate rc=0 + ComposeView children>=1 re-confirmed by the fresh traced '
               'run (view tree emitted, AndroidComposeView present; verdict line F-NEW-233 in '
               'run.log). Frame 0-content-pixels arm now owned by F-NEW-265. Kept PARTIAL.'),
 'R-NEW-259': ('Composition lifecycle sub-face advanced past its recorded gap R-NEW-279: '
               'lifecycle chain exception-free at HEAD (single in-flight exception is the '
               'measure-pass cascade, not lifecycle). Kept PARTIAL with F-NEW-265 pointer.'),
 'R-NEW-260': ('F-057 view-node duality owner-walk law exercised by every anchor run at HEAD '
               '(6/6 x3 byte-identical — all View-shadow apps walk owners). hello_color '
               'regression-watch unchanged (not in anchor set). Kept PARTIAL (watch).'),
 'R-NEW-279': ('dooz full lifecycle callback chain exception-free re-confirmed at HEAD: '
               'fresh traced run shows lifecycle-complete with exactly 1 in-flight exception '
               '(measure cascade Lzs;.m family — not lifecycle). Kept PARTIAL with F-NEW-265 pointer.'),
 'R-NEW-285': ('Recomposer creation + MonotonicFrameClock fold confirmed live at HEAD '
               '(frame-driven recomposition pass#2 with reader ops per CONT-9/10 lineage; '
               'anchors byte-identical). Job-active-cancellation face re-classified SETUP-phase '
               '(CONT-9 W5, suppression stays refuted). Kept PARTIAL; successor root F-NEW-265.'),
}

for rid, note in notes.items():
    r = by_id.get(rid)
    if not r:
        print('MISS', rid); continue
    r['evidence'] = (BASE_EV + note)[:2900]
    r['verified_current'] = True
    r['date'] = TODAY
    if not r.get('title'):
        r['title'] = f'(title backfilled CONT-17) {rid} — live re-verified at HEAD, see evidence'

for rid, ptr in [
  ('F-NEW-256', 'SUPERSEDED-BY-EVIDENCE: the W6 theory (AndroidCanvas bridge never '
   'constructed) was re-rooted by CONT-11 W7 with full runtime proof — draw machinery '
   'EXONERATED (dispatchDraw/coordinator walk/canvas.translate live); the tree is unplaced '
   'because the MEASURE pass dies (F-NEW-265: null-text CharSequence into Lm7.<init> -> '
   'getClass-check throw -> deferred-throw cascade -> Lel0.Y null-Throwable -> onMeasure '
   'death -> isPlaced=false). Follow F-NEW-265.'),
  ('R-NEW-381', 'SUPERSEDED-BY-EVIDENCE: dooz v23 first-frame 0-ops face re-rooted to '
   'F-NEW-265 (measure death -> isPlaced=false), proven by CONT-11 W7 dispatchDraw/canvas. '
   'translate live-census + fresh traced dooz run at a8761a482a186eac (app_draw_ops=0, '
   'draw_walk_ran=true, verdict line in run.log). Follow F-NEW-265.'),
]:
    r = by_id.get(rid)
    if not r:
        print('MISS', rid); continue
    r['status'] = 'SUPERSEDED-BY-EVIDENCE'
    r['evidence'] = (BASE_EV + ptr)[:2900]
    r['verified_current'] = True
    r['date'] = TODAY

# --- Task 14: baseline_head repair ---
reg['baseline_head'] = 'a6028be6'
reg['note'] = (reg.get('note', '') + ' | CONT-17 2026-10-08: baseline_head refreshed to '
               'merged-HEAD a6028be6 (CONT-15 W9 + CONT-16 fix batch); D-family live '
               're-verify + supersede linkage; F-NEW-256/R-NEW-381 -> SUPERSEDED-BY-EVIDENCE '
               '-> F-NEW-265; odd statuses normalized with per-row evidence quotes.')[:2900]

# --- Task 15: vocabulary normalization (evidence-quoted, no history erased) ---
NORM = {
 'VF-NEW-001': ('ROOT-CAUSED-FIXED', 'ROOT_CAUSED-FIXED (underscore typo) normalized to canonical ROOT-CAUSED-FIXED'),
 'VF-NEW-002': ('ROOT-CAUSED-FIXED', 'ROOT_CAUSED-FIXED (underscore typo) normalized to canonical ROOT-CAUSED-FIXED'),
 'A7':          ('ROOT-CAUSED-FIXED', 'FIXED-S75 (wave-local label) normalized to ROOT-CAUSED-FIXED — S75 fix evidence retained in row'),
 'R-NEW-352':   ('ROOT-CAUSED-FIXED', 'PROVEN-FIXED normalized to ROOT-CAUSED-FIXED (proof evidence retained)'),
 'R-NEW-450':   ('VERIFIED-FIXED', 'VERIFIED_3RUN normalized to VERIFIED-FIXED (3-run evidence retained)'),
 'R-NEW-404':   ('ROOT-CAUSED-FIXED', 'FIXED-VERIFIED normalized to ROOT-CAUSED-FIXED'),
 'R-NEW-389':   ('ROOT-CAUSED-FIXED', 'ROOT-CAUSED-SEMANTIC normalized to ROOT-CAUSED-FIXED (semantic-law evidence retained); bouncy 81-px band close-out note per T-52'),
 'R-NEW-388':   ('ROOT-CAUSED-FIXED', 'ROOT-CAUSED-REMEASURED-GENERIC-OK normalized to ROOT-CAUSED-FIXED (remeasure evidence retained)'),
 'R-NEW-340':   ('PARTIAL', 'PARTIAL-FIX normalized to PARTIAL — recomposer re-post arm remains open (T-13 / task 50); delivered arm evidence retained'),
}
for rid, (new_status, why) in NORM.items():
    r = by_id.get(rid)
    if not r:
        print('MISS', rid); continue
    r['status'] = new_status
    r['evidence'] = ((r.get('evidence') or '') + f' [CONT-17 normalization {TODAY}: {why}]')[:2900]
    r['date'] = TODAY

# --- Task 17: R-NEW-456 BLOCKED note verify ---
r = by_id.get('R-NEW-456')
if r:
    r['evidence'] = ((r.get('evidence') or '') +
        ' [CONT-17 2026-10-08: BLOCKED note re-verified current — blocker unchanged, row kept BLOCKED]')[:2900]
    r['date'] = TODAY

# --- Task 19: CLASSIFIED trio pointers ---
for rid, ptr in [
  ('F-NEW-250', 'next action: serializerOrNull chain probe at HEAD (task 51)'),
  ('F-NEW-256', 'SUPERSEDED — see this row\'s status flip; follow F-NEW-265'),
  ('F-NEW-265', 'next action: ARM-1/2/3 decomposition (tasks 86-88), single highest-ROI root'),
]:
    r = by_id.get(rid)
    if r:
        r['evidence'] = ((r.get('evidence') or '') + f' [CONT-17 pointer {TODAY}: {ptr}]')[:2900]
        r['date'] = TODAY

# refresh status_counts
from collections import Counter
reg['status_counts'] = dict(sorted(Counter(x['status'] for x in roots).items(), key=lambda kv: -kv[1]))
reg['total_roots'] = len(roots)
reg['total'] = len(roots)
reg['generated'] = TODAY

json.dump(reg, open(P, 'w'), indent=1)

# --- evidence JSON for the sweep ---
ev = {
 'binary': BIN, 'head': 'a6028be6+merge', 'date': TODAY,
 'anchors': {'dooz': 'd602648e8e401895', 'microtimer': 'da73010a37dd0189',
             'unote': '4f1a9e4e8f64fae8', 'gmdice': 'f3b483fe7b7cf51b',
             'opencalc': 'a976d2f9fb675cb3', 'chess': 'b5a7a35d5fe0564b'},
 'dooz_traced_run': {
   'dir': 'run/cont17/dooz_traced', 'screenshot_sha16': 'd602648e8e401895',
   'verdict': 'DEFAULT_BACKGROUND_ONLY', 'first_missing_stage': 'APP_DRAW_OPS',
   'app_draw_ops': 0, 'draw_walk_ran': True, 'uncaught_in_flight': 1,
   'unwind_chain_head': 'La; unwound Lzs;.m invoke_pc=0x4a depth=17 [measure family]'},
 'probes': {'f266': '6/6', 'f259': '7/7', 'f259g': '12/13 (L honest artifact)', 'fcol': '3/18 unchanged'},
 'gates': {'gate_a': '98 PASS / 0 FAIL / 1 INFO', 'negatives': '19/19', 'skill': '13/13'},
 'reverified_keep_partial': list(notes.keys()),
 'superseded': {'F-NEW-256': '-> F-NEW-265', 'R-NEW-381': '-> F-NEW-265'},
 'normalized': {k: v[0] for k, v in NORM.items()},
}
json.dump(ev, open(OUT, 'w'), indent=1)
print('registry rows touched:', len(notes) + 2 + len(NORM) + 2)
print('new status_counts:', json.dumps(reg['status_counts']))
print('evidence ->', OUT)
