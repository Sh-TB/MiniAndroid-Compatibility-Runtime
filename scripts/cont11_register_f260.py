#!/usr/bin/env python3
"""cont11_register_f260.py — CONT-11 W7 registry update (evidence-first, no inflation).

1. Refine F-NEW-256: the compose DRAW-path frontier diagnosis advanced from
   "AndroidCanvas bridge never constructed" (W6, superseded as the primary root)
   to the proven final link: isPlaced=false gate skips all content (see F-NEW-260).
2. Register F-NEW-260 CLASSIFIED: compose measure/place lifecycle never completes
   for applier-inserted nodes -> LayoutNode.isPlaced=false -> InnerNodeCoordinator
   performDraw gate skips every content node -> CanvasDrawScope.draw 0 invocations
   -> 0 canvas ops. Runtime-proven chain, upstream 1.11.4 anchors included.
"""
import json, sys

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG))
roots = d['roots']

def find(rid):
    for r in roots:
        if isinstance(r, dict) and r.get('id') == rid:
            return r
    return None

assert find('F-NEW-260') is None, 'F-NEW-260 already registered (no duplicates)'

f256 = find('F-NEW-256')
assert f256 is not None, 'F-NEW-256 missing'
f256['title'] = (
    "Compose real-content frontier \u2014 REFINED CONT-11: the draw pipeline executes structurally "
    "(dispatchDraw -> root.draw -> coordinator chain L0/M0/T0/h1 per frame, canvas bridge HEALTHY: "
    "Ly3;.a adopt + Ly3;.f translate run inside the draw window); the content draw never fires because "
    "head(Nodes.Draw)=T0(4) resolves empty and the children walk stops at the upstream isPlaced gate \u2014 "
    "root moved to F-NEW-260 (measure/place lifecycle never completes for applier-inserted nodes). "
    "W6's 'Ljt1; never constructed' was the text-path symptom (Lj7;.e = android.text.Layout.draw), not the root."
)
f256['root_cause'] = (
    "SUPERSEDED-IN-PART by F-NEW-260 (CONT-11): W6's 'AndroidCanvas bridge never constructed' was a "
    "downstream symptom. Runtime proof (run/w7, binary aed46450c103f2ea): per frame Lt4;.dispatchDraw runs, "
    "canvasHolder adopts the platform canvas (Ly3;.a), Lel0;.i -> Lpz0;.L0 runs with P==null (upstream-normal "
    "plain-draw path; r1=reuseLayer called 2x with drawBlock=NULL, Luc0;=GraphicsLayerOwnerLayer legitimately "
    "never built for graphicsLayer-free UI), M0 -> T0(4)=head(Nodes.Draw) -> null -> h1 -> children loop "
    "(count=1, child=o6128) -> gate child.I()=isPlaced == FALSE -> child.i never called. "
    "Lgl0;.c (CanvasDrawScope.draw) = 0 invocations in 85,838-entry METHOD-TRACE. Upstream map verified "
    "against ui-1.11.4/ui-android-1.11.4 sources (upstream/s43)."
)
f256['evidence'] = 'evidence/cont11/CONT11_W7_DRAW_ROOT_CAUSE.md'
f256['verified_current'] = (
    'CONT-11 W7 baseline x3 anchor d602648e8e401895 zero-drift at binary aed46450c103f2ea; '
    'C013-ONDROW dispatched=YES ops=0 every frame; verdict honestly DEFAULT_BACKGROUND_ONLY retained'
)

f260 = {
    "id": "F-NEW-260",
    "title": (
        "Compose measure/place lifecycle never completes for applier-inserted LayoutNodes \u2014 "
        "MeasurePassDelegate.isPlaced (Lbt0;.w) stays false (89 reads via Lel0;.I, ZERO place-pass writes; "
        "writers Lbt0;.q0/.r0 never execute), so InnerNodeCoordinator.performDraw's upstream gate "
        "if (layoutNode.isPlaced) child.draw(canvas, graphicsLayer) skips every content node "
        "(child o6128: I()=FALSE) \u2192 CanvasDrawScope.draw (Lgl0;.c) 0 invocations \u2192 0 canvas ops "
        "\u2192 dooz framebuffer background-only."
    ),
    "status": "CLASSIFIED",
    "priority": "P0",
    "layer": "framework/compose-layout",
    "root_cause": (
        "CLASSIFIED with the complete runtime-proven chain (no fix attempted this wave per "
        "evidence-first discipline): (1) W6 fixes materialize destination nodes via applier inserts "
        "(Lel0;.B/Lv02;.c, o6128..o6225); (2) the measure/place pass never reaches the inserted subtree "
        "\u2014 upstream AndroidComposeView.dispatchDraw calls measureAndLayout() before root.draw, and the "
        "engine's faithful dispatch of the APK bytecode does run a measure pass, but the place-pass writers "
        "of Lbt0;.w (q0/r0) never execute on the new nodes; (3) draw-time gate Lug0;.h1 children loop: "
        "count=1, isPlaced(o6128)=FALSE -> subtree skipped; (4) content driver Lgl0;.c=0. "
        "Upstream anchors: LayoutNode.kt:826 isPlaced; NodeCoordinator.drawBlock 'if (layoutNode.isPlaced) "
        "{draw} else {skip \u2014 invalidated when finally placed}'; AndroidComposeView.dispatchDraw "
        "measureAndLayout() ordering. Fix surface (next wave): engine-side measure+place scheduling for "
        "applier-inserted subtrees (generic 'node inserted -> request layout -> measure+place before next "
        "draw' law); no app-specific or R8-specific code."
    ),
    "evidence": "evidence/cont11/CONT11_W7_DRAW_ROOT_CAUSE.md",
    "probe": "pending next wave (synthetic measure/place probe: insert node via applier, assert isPlaced flips and draw lambdas fire)",
    "verified_current": (
        "run/w7 traces at binary aed46450c103f2ea: METHOD-TRACE Lgl0;.c=0; DRAW_WINDOW 430 rows/6 frames; "
        "FIELD-TRACE Lbt0;.w: get x89 / put-init x1 / place-writers x0; Lug0;.h1 children count=1 (o2007); "
        "Lel0;.I(6128)=FALSE; baseline anchors x3 zero-drift"
    ),
}
roots.append(f260)
d['total'] = len(roots)
d['count'] = len(roots)

json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry updated: F-NEW-256 refined, F-NEW-260 registered CLASSIFIED P0; total roots =', d['total'])
