#!/usr/bin/env python3
"""cont156_registry.py — CONT-156 Train 1+2 registry updates.
F-NEW-485 CLASSIFIED -> ROOT-CAUSED-FIXED (F-NEW-486 landed).
F-NEW-481 addendum: the replay-leg lever census (holder web + live counts).
Both files (main + canonical mirror) updated, id-unique verified."""
import json, sys

ROWS = [
    {
        "id": "F-NEW-486",
        "title": "F-NEW-486 — the WindowMetrics shadow family: WindowManager.getCurrentWindowMetrics/getMaximumWindowMetrics (API 30+) + WindowMetrics.getBounds/getWindowInsets — the generic fix for F-NEW-485 (framework-window)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework-window",
        "evidence": {
            "root": "WindowManager.getCurrentWindowMetrics had NO engine shadow -> answered null -> Kotlin checkNotNull NPE in AppLayout.updateMeasurementSDK30 (aat, F-NEW-485). AOSP law: a real device NEVER returns null; WindowMetrics carries the window Rect + Insets.",
            "fix": "dalvik_engine.cpp after the getDefaultDisplay handler: getCurrentWindowMetrics/getMaximumWindowMetrics -> get_or_create_singleton('Landroid/view/WindowMetrics;') seeded with mBounds=Rect(0,0,1080,1920) (device-profile law, identical to Display.getMetrics) + mWindowInsets=Insets(0,0,0,0); getBounds/getWindowInsets dispatch on the WindowMetrics receiver (never null, AOSP law).",
            "verify": "aat ch.bailu.aat_45: killer signature ABSENT (zero 'must not be null' lines, zero updateMeasurementSDK30 NPE), face 99.3% non-white (was 0% WINDOW_ROOT blank) — aat crossed to RENDER. Zero-drift wall 9/9 MATCH at binary 2dc7f5b4ff8731d2 (incl. the 2 CONT-155 re-based anchors unote 7481e9b4 / opencalc 63020bc7); negatives 19/19 (after gate-A probe prelude); skill selftest 13/13.",
            "run": "run/c156/t3_aat.log, run/c156/t3_aat_face/screenshot.png"
        },
    },
    {
        "id": "F-NEW-481",
        "title": "F-NEW-481 — dooz-family draw frontier: the compose lambda-replay leg never executes; root-chain kind-4 walk over the frozen early chain is the only draw path (49-app APP_DRAW_OPS cohort) — CONT-156 Train 1 lever census addendum",
        "status": "PARTIAL",
        "priority": "P0",
        "layer": "compose-draw",
        "evidence": {
            "census_binary": "d7d3d61a76129682 (CONT-156 deterministic rebuild #10, byte-identical)",
            "holder_web": "Lpz0;.N:Loz0; is the ONLY typed holder (bound in pz0.<init> pc=52-64, the single write site); Loz0;.g:Lpz0; back-ref; Lpz0;.r1 (pc=126) creates FRESH Loz0; — the replay lambda body. Tools: cont156_holder_xref.py (typed-holder + new-instance + store-track), cont156_loz_probe.py.",
            "live_counts": "dooz v23 5-frame run: Lt4;.dispatchDraw=6, Lel0;.i=6, Lpz0;.<init>=41 (2 early + 39 late), Lpz0;.r1=2 (only via Lxk0;.k0/Lug0;.k0), Lpz0;.k1=0, Lem1;.g/Lff;.g/Lsc0;.g=0 (layer callbacks NEVER run), Loz0;.7834/.834=0, Lgl0;.c=0 (the REAL content draw never fires), framework RenderNode path UNUSED (beginRecording/drawRenderNode=0), Lrh1;.a=0 (the sole static caller of the abstract record trigger La00;.k0 — dead upstream), Lkz0;.d=0 in this build (root getter is Lkz0;.c, 201 runs).",
            "choreographer": "HEALTHY — Lh9;.doFrame fires per frame (cb=1182 re-post loop); the earlier frame-pump starvation hypothesis is RETRACTED (runnables_fired=0 measures the FRAME-SEQ re-pump, not the Choreographer leg).",
            "sharpened_law": "The record trigger chain (rh1.a -> La00;.k0 -> i1 -> r1) is app-internal and dies upstream of k0; only the 2 initial layer nodes record; the 39 late pz0 scopes never record; M0's kind-4 walk over the frozen early chain always fails -> h1 overlay only -> blank face.",
            "next_lever": "Generic engine-side levers still open: (a) deliver layer-invalidation to the registered callbacks (em1/ff/sc0 shapes), (b) make the draw pass query late scope chains — both require an engine-visible registry of live pz0-family scopes (heap census law) or a name-dispatched record pass mirroring the existing dispatchDraw/onLayout name-dispatch law.",
            "run": "run/c156/t1_em1g.log (census), run/c156/t2_kz0d.log, run/c155/train2_gate_census.md (prior)"
        },
    },
]

def load(path):
    with open(path) as f:
        return json.load(f)

def save(path, doc):
    with open(path, 'w') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')

def upsert(roots, row):
    for i, r in enumerate(roots):
        if r.get('id') == row['id']:
            merged = dict(r)
            for k, v in row.items():
                if k == 'evidence' and isinstance(v, dict) and isinstance(r.get('evidence'), dict) and k in r:
                    ev = dict(r['evidence']); ev.update(v); merged[k] = ev
                else:
                    merged[k] = v
            roots[i] = merged
            return 'updated'
    roots.append(row)
    return 'added'

paths = ['root_registry.json', 'canonical/root_cause_registry.json']
for p in paths:
    doc = load(p)
    roots = doc['roots'] if isinstance(doc, dict) and 'roots' in doc else doc
    for row in ROWS:
        res = upsert(roots, row)
        print(f'{p}: {row["id"]} {res}')
    ids = [r.get('id') for r in roots]
    assert len(ids) == len(set(ids)), 'id uniqueness broken'
    if isinstance(doc, dict) and 'roots' in doc:
        doc['roots'] = roots
    save(p, doc)
    print(f'{p}: total={len(roots)} saved')
