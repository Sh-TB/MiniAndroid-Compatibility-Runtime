#!/usr/bin/env python3
# cont154_registry.py — add F-NEW-481 row + F-NEW-480 evidence addendum (both registry files)
import json

ROW = {
    "id": "F-NEW-481",
    "title": "F-NEW-481 — draw-loop scope snapshot staleness: Lxk0;.V is bound ONCE at <init> and never rebound (128 events, zero rebinds); draw loop iterates early scopes while capable nodes populate late scope instances -> generic fix target for the 49-app APP_DRAW_OPS cohort",
    "status": "CLASSIFIED",
    "priority": "P0",
    "layer": "compose-draw",
    "evidence": "CONT-154 (dooz v23, binary f6b272ea, MINIANDROID_FIELD_TRACE='Lxk0;.V', run/c154/dooz_vtrace.log, 128 events): (1) EVERY put to Lxk0;.V is from Lxk0;.<init> — binds: obj#2717.V=2708, obj#6459.V=6457, obj#6479.V=6475, obj#6482.V=6470, obj#6485.V=6466, ... NO put from any other method, NO rebind of any instance after construction; (2) gets come from Lxk0;.S0 (chain-root resolver, law: S0 = ((Lwt0;)this.V).e per TRAIN 10 decode) AND from Lxk0;.e; (3) CRITICAL REFINEMENT of TRAIN 10's 'draw loop never queries the late scopes': S0 DOES run on LATE instances (obj#6459, obj#6485 — .V gets at late objects) — the late scopes ARE queried by SOMETHING; the blank face therefore follows from the DRAW LOOP (Lel0;.i -> Lpz0;.L0 -> M0 -> T0) receiving ONLY the EARLY receiver objects (2717/2061 — census F-NEW-480 TRAIN 7: receiver distribution 2717 x54, 2061 x54, 2708 x30, NULL x12, zero late objects) — i.e. the draw loop iterates a scope list snapshotted at first layout; Lxk0; instances created by later layout passes (6459/6479/6482/6485...) whose V-chains carry the bit-4-capable nodes (F-NEW-480 TRAIN 9: 20/69 g-puts with bit 0x4 all on late instances) never become draw-loop receivers; (4) V one-time-bind is upstream-faithful Compose shape (scope captured at composition); the engine-missed piece is the INVALIDATION that should re-enumerate scopes for the draw loop after late layout passes. NEXT LEVER (single question): the scope enumeration ABOVE Lel0;.i (Lho1;.d / Lt4;.getRoot per TRAIN 10) — does the app push new scopes into a list the draw loop should re-read each frame (engine-missed invalidation -> generic fix), or does the app itself only ever pass the early list (upstream state)? COVERAGE LAW: the same APP_DRAW_OPS first_missing_stage covers 49/94 new-corpus apps (CONT-154 scorecard_final.json) — one generic fix targets the whole cohort.",
    "opened": "CONT-154"
}

for path in ('root_registry.json', 'canonical/root_cause_registry.json'):
    d = json.load(open(path))
    roots = d if isinstance(d, list) else d.get('roots', d.get('rows'))
    assert roots is not None, path
    # update F-NEW-480 evidence addendum
    for r in roots:
        if r.get('id') == 'F-NEW-480':
            if 'CONT-154 V-TRACE' not in r['evidence']:
                r['evidence'] += (" || CONT-154 V-TRACE (128 events, run/c154/dooz_vtrace.log): V is ONE-TIME-BOUND at Lxk0;.<init>, never rebound — "
                                  "but S0 DOES get .V on LATE instances (6459/6485): late scopes are queried by some walk; "
                                  "the draw loop still receives only early receivers (2717/2061). Promoted to F-NEW-481 "
                                  "(draw-loop scope snapshot staleness + missing invalidation).")
    # id-unique check + append
    ids = {r.get('id') for r in roots}
    assert ROW['id'] not in ids, f"duplicate {ROW['id']} in {path}"
    roots.append(ROW)
    if isinstance(d, list):
        json.dump(d, open(path, 'w'), indent=2, ensure_ascii=False)
    else:
        json.dump(d, open(path, 'w'), indent=2, ensure_ascii=False)
    print(path, '-> roots now', len(roots))
