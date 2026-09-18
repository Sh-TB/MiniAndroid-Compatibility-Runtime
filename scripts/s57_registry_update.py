#!/usr/bin/env python3
"""S57 registry sync: R-NEW-344 closure (F-086), stale-face reconciliation.

Per ROADMAP 3 CLOSURE §26/§27: every item ends in exactly one final state,
with evidence. No new IDs created; R-NEW-376 absorbs the v23 ctor-climb
observation as the same root-cause family (§37 alias rule).
"""
import json

PATH = '/home/z/my-project/root_registry.json'

with open(PATH) as f:
    reg = json.load(f)

roots = reg['roots']
by_id = {r['id']: r for r in roots}

def set_fields(root_id, **kw):
    r = by_id[root_id] if isinstance(root_id, str) else root_id
    for k, v in kw.items():
        r[k] = v
    r['last_updated'] = 'S57 2026-09-18'

# ── R-NEW-344: CLOSED — ROOT-CAUSED + FIXED (F-086) ─────────────────────
set_fields(
    'R-NEW-344',
    status='ROOT-CAUSED-FIXED',
    priority='P0',
    title=('dooz23 ScatterMap full-table probe spin: second grow computed '
           'newCapacity=15 instead of nextCapacity(15)=31 — ROOT-CAUSED as '
           'missing java.lang.Long bridge (F-086), fixed + regression-tested '
           'at S57'),
    evidence=(
        'S57 chain: (1) repro at HEAD 28b644b7 — HALT-LOOP in Lbw0;.d pc=28 '
        '(bytecode_size=671), blank frame 0/2073600, run/s57_r344_repro/; '
        '(2) androguard disasm of dooz23 (scripts/s57_andro_lbw0.py): the '
        'R8-inlined growth decision at Lbw0;.d pc=170-199 is '
        'Long.compare(size*32 ^ Long.MIN_VALUE, capacity*25 ^ Long.MIN_VALUE) '
        '+ if-gtz → f(Lmg1;.b(nextCapacity)=cap*2+1) at pc=494-506; the '
        'fall-through (pc=201-482) is convertMetadataForCleanup + same-cap '
        'refill (aput 0xFEFEFEFEFEFEFEFE at pc=235 — bit-exact vs S56); '
        '(3) bridge_to_api had NO Long.compare handler → STUBBED typed-zero '
        'exit returned 0 → if-gtz false → cleanup path; the cap-7 grow '
        'branches at pc=172 (capacity<=8 → pc=491) and never touches the '
        'compare, which is why only the SECOND grow failed; (4) fix F-086: '
        'Long.compare/compareUnsigned 64-bit law in the F-055 Long block; '
        '(5) post-fix: capacity field trace on obj#2658 shows 7 → 15 → 31 '
        '(run/s57_r344_proof2/), HALT-LOOP 0, F084-HALT-RETURN 0, '
        'aput-oob gone'),
    next_action=('CLOSED for R-NEW-344. Dooz v23 execution continues into '
                 'the R-NEW-376 ctor-climb family (Lgz1;.<init> depth=2048 '
                 'self-delegation face observed post-fix — same root cause '
                 'as the v18 frontier; no new ID created)'),
)

# ── F-086 registration (same S57 fix) ────────────────────────────────────
f086 = {
    'id': 'F-086',
    'status': 'IMPLEMENTED+TESTED',
    'priority': 'P0',
    'title': ('java.lang.Long 64-bit comparison bridge family (compare/'
              'compareUnsigned, OpenJDK Long.java law) — closes the '
              'STUBBED-typed-zero class for wide-arg static invokes'),
    'evidence': (
        'miniandroid/src/dex/dalvik_engine.cpp (F-055 Long block, S57): '
        'compare is signed 64-bit (-1/0/+1), compareUnsigned unsigned; '
        'regression tests/semantic_long_cmp_conv_test.cpp f086 group '
        '6/6 PASS (battery stage "semantic long/cmp/conv (expect 20)"), '
        'including the bit-exact dooz23 growth idiom '
        'compare(448^MIN, 375^MIN)==+1; post-fix runtime proof: '
        'Lbw0;.f capacity 7→15→31 on dooz23 (docs/evidence/s57_dooz23/)'),
    'first_seen': 'S57 2026-09-18',
    'last_updated': 'S57 2026-09-18',
}
if 'F-086' not in by_id:
    roots.append(f086)
else:
    set_fields(by_id['F-086'], **{k: v for k, v in f086.items() if k not in ('id',)})

# ── R-NEW-376: absorb the v23 alias observation (§37 — no new ID) ────────
set_fields(
    'R-NEW-376',
    evidence=(str(by_id['R-NEW-376'].get('evidence', '')) +
              ' | S57 ALIAS (v23, post-F-086): [RECURSION-LIMIT] frame '
              'dropped: Lgz1;.<init> depth=2048 caller=Lgz1;.<init> (×3) + '
              'Lbp1;.<init> ×1 — the same impossible-in-valid-DEX '
              'self-delegating ctor face on dooz v23; run/s57_r344_proof2/'),
    last_updated='S57 2026-09-18',
)

# ── Stale dooz faces: SUPERSEDED-BY-EVIDENCE (current-face pointers) ─────
supersede = {
    'R-NEW-025': ('S57: dooz ComposeView children=0 face (m9/CMM era) does '
                  'not reproduce at any post-S24 face; current v23 face is '
                  'the R-NEW-376 ctor-climb after R-NEW-344 fix — '
                  'superseded'),
    'R-NEW-323': ('S57: S24 NavHost restore-loop face does not appear in '
                  'current dooz v23 runs (post-F-086 run reaches '
                  'Recomposer/ControlledComposition + ctor-climb family) — '
                  'superseded by the S24-S56 progression'),
    'R-NEW-330': ('S57: S27 DepthSortedSet.remove face does not appear in '
                  'current dooz v23 runs — superseded by later layout/dispatch '
                  'laws (F-082/F-083 era)'),
    'R-NEW-333': ('S57: S34 NavHost content-state face does not appear in '
                  'current dooz v23 runs — superseded (the run is past the '
                  'NavHost/composition build stage)'),
    'R-NEW-335': ('S57: S37 ScatterSet storage face is an ALIAS of the '
                  'R-NEW-344 ScatterMap family — closed into R-NEW-344 '
                  '(ROOT-CAUSED-FIXED via F-086)'),
    'R-NEW-351': ('S57: Llt0;.w aput-oob "length=1; index=1" does not '
                  'reproduce in current dooz v23 runs (grep Llt0 → parser/'
                  'reflect lines only; the protobuf chain proceeds via '
                  'honest M3-REFLECT fallbacks) — NOT-REPRODUCIBLE, '
                  'superseded by the R-NEW-347/349/350 law chain'),
}
for rid, note in supersede.items():
    set_fields(
        rid,
        status='SUPERSEDED-BY-EVIDENCE',
        evidence=str(by_id[rid].get('evidence', '')) + ' | S57 CLOSURE: ' + note,
    )

# ── summary/frontier refresh ─────────────────────────────────────────────
reg['summary']['total_roots'] = len(roots)
reg['summary']['open_frontiers'] = ['R-NEW-376']
reg['summary']['last_updated'] = 'S57 2026-09-18'
reg['summary']['note'] = (
    'S57 ROADMAP-3-CLOSURE: R-NEW-344 ROOT-CAUSED-FIXED (F-086 '
    'Long.compare bridge law; 15→31 proven at the runtime boundary; '
    'regression-protected). Stale dooz faces R-NEW-025/323/330/333/335/351 '
    'closed SUPERSEDED-BY-EVIDENCE / NOT-REPRODUCIBLE against current-face '
    'runs. R-NEW-376 is the remaining dooz frontier (v18+v23 alias '
    'observations). R-NEW-352 stays BLOCKED on the R-NEW-350 default-ON '
    'decision (microtimer retry loop).')

with open(PATH, 'w') as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

print('registry updated:', len(roots), 'roots')
print('open_frontiers:', reg['summary']['open_frontiers'])
for rid in ('R-NEW-344', 'F-086', 'R-NEW-351', 'R-NEW-335'):
    print(rid, '→', by_id[rid]['status'] if rid in by_id else
          next(r['status'] for r in roots if r['id'] == rid))
