#!/usr/bin/env python3
"""FINAL CAMPAIGN item 21 wave A — append frame-truth law roots to registries."""
import json

NEW = [
    {
        "id": "F-NEW-174", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "renderer/frame-truth",
        "title": "False-SUCCESS family: no-root success + synthetic fallback + color-stats verdict (item 21 P0-2/P0-3/P0-6)",
        "law": "AUTHORITATIVE frame requires correlated proof: valid window content root -> MEASURE -> LAYOUT -> DRAW -> app-owned draw ops -> app pixels. Synthetic api::View renderer is non-authoritative (legacy demo only); real-render exception = honest failure with framebuffer discard; 'nonwhite' is never the truth signal.",
        "evidence": "WhatsApp: OLD frame had 45px fake band (synthetic path) + false verdict; NEW: NO_ROOT verdict, 1-color white frame, synthetic_suppressed=true. stopwatch_6 same. Old dooz 'REAL_APP_CONTENT' was 989 placeholder px (b4b4b4/d8d8d8).",
        "implementation": "execution_engine.cpp: FrameRenderCensus ledger; RENDER_OK CONFIRMED gated on app_draw_ops; synthetic path suppressed in REAL_DALVIK; catch discards framebuffer + records RENDER_FAIL; capture verdict law NO_ROOT/RENDER_EXCEPTION/DEFAULT_BACKGROUND_ONLY/SYSTEM_CHROME_ONLY/PARTIAL_RENDER_BUDGET/VIEWTREE_NO_APP_PIXELS/REAL_APP_CONTENT + first_missing_stage; SUCCESS downgraded when verdict lacks app content (REAL_DALVIK).",
    },
    {
        "id": "F-NEW-175", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "renderer/frame-truth",
        "title": "Diagnostic placeholders out of the authoritative frame (item 21 P0-5/P1-9)",
        "law": "AUTHORITATIVE frame = real app/system rendering only. Grey 'custom view (not rendered)' boxes, 'IMG?', 'IMG' labels are DIAGNOSTIC pixels: recorded in the census (UNRENDERED regions), never painted. The screen-blankness gate (nw<5000) is removed from authoritative rendering.",
        "evidence": "dooz OLD golden ba8a95eb2278594f = 3 colors incl. 0xB4/0xD8 placeholder px (false REAL_APP_CONTENT 989px); NEW d602648e8e401895 x3 = white + DEFAULT_BACKGROUND_ONLY. simplestopwatch OLD dominant 909090 = dialog-dimmed placeholder box (93% of screen); NEW real content pixels byte-identical, verdict REAL_APP_CONTENT app_ops=5.",
        "implementation": "Placeholder paint sites -> frame_census_.diag_regions records; deferred second-chance onDraw/surface replay UN-GATED (real content only); decode failures recorded UNRENDERED + provenance.",
    },
    {
        "id": "F-NEW-176", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "renderer/window-root",
        "title": "Render-root heuristics removed: setParams/SmsView/PhoneView (item 21 P0-1)",
        "law": "AOSP ViewRootImpl: render ONLY the window-attached Decor/content hierarchy. One root law (effective_content_root_) for render + tap + swipe + dialogs + capture. A detached/orphan node never becomes the render root because of setParams, class-name shape, or newer object id.",
        "evidence": "Zero app-class-name render branches remain (grep SmsView/PhoneView/last_set_params_view in render path = none). Goldens deterministic; orphan visibility now flows through the fragment-host chain (phase 4).",
        "implementation": "EXP-090/EXP-094 block deleted; swipe root switched to effective_content_root_ (21-P1-7); dialog decor routing unchanged (R-NEW-394).",
    },
    {
        "id": "F-NEW-177", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "lifecycle/honesty",
        "title": "HOST_SHORTCUT lifecycle fallback removed from REAL_DALVIK (item 21 P0-4)",
        "law": "Lifecycle events must be consequences of real bytecode execution. Missing DEX lifecycle = PARTIAL_SUCCESS + LIFECYCLE FAILURE event with first_missing_stage=DEX_LIFECYCLE. No C++ onCreate/onStart/onResume synthesis (fake evidence + double-execution hazard).",
        "evidence": "Legacy path keeps its documented HOST_SHORTCUT demo lifecycle; REAL_DALVIK path has zero host lifecycle calls.",
        "implementation": "Fallback calls removed; honesty event emitted; null_bundle consumer note.",
    },
    {
        "id": "F-NEW-178", "status": "ROOT-CAUSED-FIXED", "priority": "P0",
        "layer": "renderer/completeness",
        "title": "Silent ViewTree truncation -> budgets with explicit exhaustion (item 21 P0-7)",
        "law": "Fixed MAX_NODES=500 / depth>20 silent skips are forbidden. Budgets are env-configurable (MINIANDROID_RENDER_MAX_NODES default 200000, MINIANDROID_RENDER_MAX_DEPTH default 128); exhaustion records nodes_visited/nodes_skipped_depth/depth_max/unreachable_children + budget_exhausted and the frame verdict becomes PARTIAL_RENDER_BUDGET, never clean SUCCESS. Cycle detection (visited set) unchanged.",
        "evidence": "Acceptance run MINIANDROID_RENDER_MAX_NODES=3 on simplestopwatch: visited=3 stranded=1 budget_exhausted=true verdict=PARTIAL_RENDER_BUDGET status!=SUCCESS.",
        "implementation": "Walk loop rewritten; census fields; first-divergence on exhaustion.",
    },
    {
        "id": "F-NEW-179", "status": "IMPLEMENTED", "priority": "P0",
        "layer": "renderer/frame-pump",
        "title": "Per-frame canonical pump for Compose/WebView/Choreographer (item 21 P0-8)",
        "law": "The one canonical pump (pump_compose_frames) runs at EVERY frame boundary in --frames sequences: virtual clock advance -> Choreographer callbacks -> Handler queue -> resumed Compose work -> WebView JS/rAF tick -> render -> capture. Compose recomposition / rAF must never starve after frame 0.",
        "evidence": "microtimer --frames 5 x3: frame_003 da73010a37dd0189 BYTE-IDENTICAL x3 (deterministic). Compose animation >=3-frame acceptance rides on R-NEW-381 (composition stagnation) — queued to phase 13.",
        "implementation": "stage_frame_sequence loop: pump_compose_frames(1) inserted after the clock advance, before the drain.",
    },
    {
        "id": "F-NEW-180", "status": "ROOT-CAUSED-FIXED", "priority": "P1",
        "layer": "renderer/geometry",
        "title": "Geometry truth batch: +30px offset, translation order, scroll-clip inheritance, 40px onDraw gate, drew_real honesty, PNG capture law (items 21 P1-1/3/4/5/6/8)",
        "law": "AOSP: content geometry from the authoritative window chain (no magic 30px status-bar offset); translation applies AFTER layout bounds and accumulates through off_tx/ty with off_sx/sy scrolls applied ONCE at the draw origin; the nearest scrolling ancestor clip propagates through every descendant until a nearer scroll replaces it; any visible custom view executes onDraw regardless of size; drew_real/app_draw_ops mean real canvas ops (empty text view = honestly blank); requested-PNG failure = CAPTURE_FAILURE (PPM auxiliary only; screenshot_path only on real success).",
        "evidence": "headingcalc 823 colors / 466,062 px EXACT post-fix (heuristic-layout children shifted by the removed fake inset only); simplestopwatch/dooz/microtimer goldens deterministic; laws130 51/51 after every rebuild.",
        "implementation": "cursor_y+=30 removed; measured push passes PURE layout geometry (deltas in off_*, applied once at the child origin); clip_* inherited + draw-space outside-check; 40px gates removed; drew_real only on real text; PNG failure law + screenshot_path move.",
    },
]

def main():
    total_added = 0
    with open("canonical/root_cause_registry.json") as f:
        reg = json.load(f)
    ids = {r.get("id") for r in reg["roots"]}
    for item in NEW:
        if item["id"] in ids:
            print("skip (exists):", item["id"])
            continue
        item.setdefault("source_authority", "AOSP frameworks/base (View.java, ViewRootImpl, PhoneWindow, ScrollView, TextView)")
        item.setdefault("campaign", "final-generic-runtime-compat-v2 item 21 wave A")
        reg["roots"].append(item)
        ids.add(item["id"])
        total_added += 1
    reg["total"] = len(reg["roots"])
    with open("canonical/root_cause_registry.json", "w") as f:
        json.dump(reg, f, indent=1)
    print("added", total_added, "roots; total", reg["total"])

if __name__ == "__main__":
    main()
