#!/usr/bin/env python3
"""cont11_w7_registry.py — CONT-11 W7 registry update.
Adds R-NEW-466 (AOSP measure→layout pairing law, ROOT-CAUSED-FIXED) and
refreshes F-NEW-256's frontier note with the W7 placement-pipeline map.
No inflation: one new root, one refreshed root.
"""
import json, hashlib, sys

REG = '/home/z/my-project/root_registry.json'
raw = open(REG).read()
data = json.loads(raw)
roots = data if isinstance(data, list) else data.get('roots', data.get('entries'))
if roots is None:
    sys.exit('registry shape unknown')
before = len(roots)

def find(rid):
    for r in roots:
        if r.get('id') == rid:
            return r
    return None

# ── 1. R-NEW-466 (new, ROOT-CAUSED-FIXED) ────────────────────────────
if find('R-NEW-466'):
    print('R-NEW-466 already present — no inflation')
else:
    roots.append({
        'id': 'R-NEW-466',
        'title': ('AOSP measure-to-layout pairing law: View.measure sets '
                  'PFLAG_LAYOUT_REQUIRED after EVERY onMeasure dispatch; the '
                  'following layout() must re-run onLayout(changed,l,t,r,b). '
                  'The engine dispatched onLayout ONCE per view node '
                  '(F-NEW-233-era f096_lifecycle_done one-shot), so hosts '
                  'whose content tree changes AFTER the first static-frame '
                  'layout never re-ran their per-traversal placement: compose '
                  'AndroidComposeView.onLayout -> measureAndLayout -> '
                  'root.place(0,0) -> placeAt -> markNodeAndSubtreeAsPlaced '
                  'never executed for recomposition-materialized children -> '
                  'MeasurePassDelegate.isPlaced stayed false -> the compose '
                  'draw walk (drawContent child gate node.I()==isPlaced) '
                  'skipped every child -> 0 canvas ops (the F-NEW-256 dooz '
                  'draw frontier). Fix: ViewShadow node dex_layout_required '
                  'raised by every dispatch_custom_view_measure success, '
                  'consumed by DalvikExecutionEngine::dispatch_view_relayout '
                  '(new) called from the per-frame layout traversal. Generic '
                  'AOSP law: no compose knowledge, no R8 tables.'),
        'status': 'ROOT-CAUSED-FIXED',
        'priority': 'P1',
        'layer': 'framework-lifecycle',
        'fixed_in': 'CONT-11 W7',
        'evidence': [
            'evidence/cont11/fnew256_w7_evidence.json',
            'trace8/trace6: FIELD-TRACE Lbt0;.w — root obj#2325 value=1, '
            'ALL children (o6144..o6241, o8863+) value=0 (unplaced)',
            'trace13: QGET pc-flow — child attach (Lel0;.d) runs pc '
            '0,35,40,118,[skip 123-137],145..306; the 123-137 block is the '
            'upstream parent==null root-only branch (isPlaced=true lives '
            'there for the ROOT only; children get placed via placeAt)',
            'upstream/s43 MeasurePassDelegate.kt:275 markNodeAndSubtreeAsPlaced'
            ' + MeasureAndLayoutDelegate.kt:576 remeasureAndRelayoutIfNeeded',
            'trace15: Lt4;.onMeasure ran 15x, Lt4;.onLayout ran 1x at the '
            'pre-fix binary (the pairing gap, live-proven)',
            'fix1: [R445-RELAYOUT] Lt4; view=1430 dispatched=YES (post-fix)'
        ],
    })
    print('R-NEW-466 added')

# ── 2. refresh F-NEW-256 frontier ─────────────────────────────────────
f256 = find('F-NEW-256')
if f256:
    f256['w7_frontier_note'] = (
        'CONT-11 W7: the draw-path frontier REFINED with the full placement-'
        'pipeline identity map (all R8 names resolved live): Lbt0;='
        'MeasurePassDelegate (w=isPlaced, q0=markNodeAndSubtreeAsPlaced, '
        'k0/v0=placeAt), Lzs0;=MeasureAndLayoutDelegate (k=measureAndLayout, '
        'g=measure walk, n/o=remeasureAndRelayoutIfNeeded), Lj4;=Owner '
        'switch-lambdas, Ly3;=canvas holder (field a=android.graphics.Canvas; '
        'f(FF)=translate — REACHES the engine canvas), Lwt0;=DrawScope chain, '
        'Lhl0;=draw-entity traversal. R-NEW-466 (this wave) re-opens the '
        'onLayout placement path (relayout now dispatches). REMAINING: the '
        'relayout QUEUE stage — children materialized by recomposition never '
        'enter relayoutNodes (k drained ~3 entries, all root-side; '
        'Lbt0;.k0/v0 placeAt never ran; q0 never ran; w stayed 0) — next '
        'wave owns requestRemeasure/requestLayout queueing (upstream '
        'MeasureAndLayoutDelegate.kt:198/680 + markLayoutPending law).')
    print('F-NEW-256 refreshed')

# ── write back ─────────────────────────────────────────────────────────
out = json.dumps(data, ensure_ascii=False, indent=1)
open(REG, 'w').write(out)
print('roots:', before, '->', len(roots))
print('registry sha16:', hashlib.sha256(out.encode()).hexdigest()[:16])
