#!/usr/bin/env python3
"""CONT-18f: register F-NEW-267 (Compose tap hit-test gap) in root_registry.json.

Evidence-first: registered from LIVE runtime evidence at the reproduced
CONT-18 binary 8ee839e718877216 (this container):
  run/cont18f/tap1/run.log  -> [F117-TAP] frame 15 DOWN (540,960) target=0
  run/cont18f/tap1/screenshot.png sha16 d602648e8e401895 == dooz anchor
  (byte-identical pre/post tap = the tap consumed zero state)
plus the recorded T-01 face run/cont18/t01_run_tap1 (committed evidence doc).
No status inflation: CLASSIFIED (root-caused, no fix attempted this wave).
"""
import json, hashlib

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG))
ids = [r.get('id') for r in d['roots']]
assert 'F-NEW-267' not in ids, 'F-NEW-267 already present'

row = {
    "id": "F-NEW-267",
    "status": "CLASSIFIED",
    "title": (
        "COMPOSE TAP HIT-TEST GAP: the canonical TouchDispatcher hit-test walks the "
        "ViewShadow tree only; when the walk lands on a Compose host view "
        "(AndroidComposeView/AbstractComposeView family) there is no bridge into the "
        "materialized Compose node tree (LayoutNode bounds from the measure pass), so "
        "every Compose-owned interactive surface is tap-dead (target=0). This gates "
        "CONT-18 T-09/T-10: the dooz GAME screen (game-mode button on the materialized "
        "main-menu tree) is unreachable by scripted taps, so the F-084-halt-before-"
        "null-text causal-order trace cannot run on live games. Generic law surface "
        "(AOSP): ComposeView.onTouchEvent -> Owner.hitTest -> hitTest over placed "
        "LayoutNodes honoring Modifier pointerInput/clickable semantics; minimal "
        "engine bridge = at the Compose-host ViewShadow, resolve the Compose root "
        "node from the heap (UiApplier root chain) and hit-test placed node bounds "
        "depth-first (topmost placed node containing the point wins), then schedule "
        "the click through the SAME PerformClick HandlerShadow law pipeline (no input "
        "bypass). HARD DEPENDENCY: F-NEW-265 (measure pass dies mid-flight -> "
        "isPlaced=false) must be resolved first or node bounds are unavailable."
    ),
    "priority": "P1",
    "layer": "framework/input+compose-bridge",
    "evidence": (
        "evidence/cont18/CONT18_F217_FIRST_DIVERGENCE.md sec.4 (recorded face "
        "run/cont18/t01_run_tap1: [F117-TAP] DOWN (540,960) target=0); LIVE "
        "reproduction this wave at binary 8ee839e718877216: "
        "run/cont18f/tap1/run.log '[F117-TAP] frame 15 DOWN (540,960) target=0', "
        "screenshot sha16 d602648e8e401895 == dooz anchor (byte-identical pre/post "
        "tap = zero state consumed, no interactive surface reachable); the tap "
        "pipeline itself is exonerated (F-117/R-NEW-394/S129 dialog+swipe laws all "
        "green on View-tree apps: negatives 19/19)."
    ),
    "probe": (
        "PENDING (next wave): scripted-tap probe on a materialized Compose tree "
        "(synthetic Compose APK with a known clickable node at a known placed "
        "bound); positive = target!=0 + PerformClick -> DEX onClick; negative = "
        "tap outside all placed bounds stays target=0."
    ),
    "verified_current": (
        "registered at binary 8ee839e718877216 (clean rebuild reproduces the "
        "recorded CONT-18 binary byte-identically); anchors 18/18 x3 MATCH at the "
        "same binary (no drift while registering)."
    ),
}

d['roots'].append(row)
d['total_roots'] = len(d['roots'])
d['total'] = len(d['roots'])
json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registered F-NEW-267; total rows =', len(d['roots']))
