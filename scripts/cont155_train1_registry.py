#!/usr/bin/env python3
"""cont155_train1_registry.py — TRAIN 1: F-NEW-481 evidence addendum (draw-entry
enumeration map). Syncs canonical/root_cause_registry.json + root_registry.json,
verifies id-uniqueness + main==mirror."""
import json, sys

ADD = (" CONT-155 TRAIN 1 ADDENDUM (dooz v23, binary f6b272ea, tools cont155_methxref.py"
       " instruction-aligned xref + cont151_disasm_regs): (4) whole-dex census proves"
       " Lel0;.i has EXACTLY 2 call sites: Lt4;.dispatchDraw unit46 (per-frame view draw"
       " pass — const-string 'AndroidOwner:draw' + Trace.beginSection, calls getRoot EVERY"
       " frame then el0.i{root,canvas}) and Lug0;.h1 unit27 (overlay). (5) REFUTATION of"
       " clause (3)'s 'scope list snapshotted at first layout': the ROOT is re-read every"
       " frame — the stale link is deeper: el0.i receiver chain is this.I(Lkz0;) -> kz0.d"
       " (Lpz0;) -> L0 (single scope, no recursion, 70 insns: guard Lc31;.P -> nanos->ms"
       " math -> Ldi;.f -> M0 -> Ldi;.f). (6) M0 has exactly 2 callers: Lpz0;.L0 unit61 and"
       " Loz0;.a unit24 — Loz0; is a LAMBDA class (extends Lgk0;, fields I f + Lpz0; g):"
       " created inside Lpz0;.r1 unit65 capturing the CURRENT pz0 (v10), then r1 calls"
       " oz0.a() (units 231-241/327-334). r1 callers: i1/k1 internal + LAYER callbacks"
       " Lem1;.g/pc56, Lff;.g/pc46, Lsc0;.g/pc124 — all share the law: iget-boolean Lwt0;.e"
       " gate -> Llo;.T -> layer field .t (Lpz0;) -> r1(t): drawn pz0 = layer's FROZEN .t."
       " (7) LIVE FIELD-TRACE Loz0;.g (run/c155/t1_oz0g.log): 41 events ALL from"
       " Loz0;.<init>, zero rebinds; EARLY captures 2356->2061, 2721->2717 AND LATE"
       " captures 6311->6309, 6461->6459, 6487->6485, 7864->7862, 8983->8981 ... 9247->9245"
       " — late draw lambdas ARE created with correct late captures, but T0 census shows"
       " the 2 early lambdas replayed ~54x each and the ~39 late lambdas invoked ZERO"
       " times. (8) TRAIN 2 single question: r1 creates late lambdas AND calls oz0.a() in"
       " the same method, so a late r1 call must return early — both replay sites sit"
       " behind the Z M flag; gate census targets Lpz0;.M / Lc31;.P / Lwt0;.e on late"
       " layers. Evidence: run/c155/train1_draw_entry_decoded.md")

for path in ('canonical/root_cause_registry.json', 'root_registry.json'):
    with open(path) as f:
        reg = json.load(f)
    roots = reg['roots'] if isinstance(reg, dict) and 'roots' in reg else reg
    hit = False
    for row in roots:
        if isinstance(row, dict) and row.get('id') == 'F-NEW-481':
            if ADD[:60] in row.get('evidence', ''):
                print(f'{path}: addendum already present, skip')
            else:
                ev = row.get('evidence', '')
                row['evidence'] = ev + ADD
                print(f'{path}: F-NEW-481 evidence +{len(ADD)} chars')
            hit = True
    if not hit:
        print(f'{path}: F-NEW-481 NOT FOUND', file=sys.stderr); sys.exit(1)
    ids = [r['id'] for r in roots if isinstance(r, dict) and 'id' in r]
    assert len(ids) == len(set(ids)), f'{path}: id not unique!'
    with open(path, 'w') as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)

a = json.load(open('canonical/root_cause_registry.json'))
b = json.load(open('root_registry.json'))
assert json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False), 'main != mirror'
print('main==mirror OK, id-unique OK')
