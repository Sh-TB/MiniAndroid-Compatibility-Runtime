#!/usr/bin/env python3
"""CONT-17 Tasks 23-26: SP-4..8 renderer-authority audit + DEEP-AUDIT legacy
reachability + view_tree_lifecycle_owner cross-check + traversal-order cross-check.
All findings cite file:line in the authoritative tree."""
import json

OUT = '/home/z/my-project/evidence/cont17/renderer_authority_audit.json'

audit = {
 'generated': '2026-10-08', 'binary': 'a8761a482a186eac',
 'task_23_SP4_8_renderer_authority': {
   'selection_law': 'S135 §14 — runtime semantics ONLY',
   'sites': [
     {'family': 'OPENGL_GLES', 'trigger': 'GL frame actually presented (surface created)',
      'site': 'src/runtime/execution_engine.cpp:5221-5228'},
     {'family': 'COMPOSE', 'trigger': 'choreographer composition pump has pending callbacks (recomposition pump active)',
      'site': 'src/runtime/execution_engine.cpp:6195-6198'},
     {'family': 'CLASSIC_CANVAS', 'trigger': 'default view walk when no authoritative family has claimed (guarded by current_renderer_family().empty() — first claim wins, never downgrades)',
      'site': 'src/runtime/execution_engine.cpp:2925-2929'},
     {'family': 'WEBVIEW', 'trigger': 'live WebView engine (S135 §14 comment at :2921)'},
   ],
   'forbidden_heuristics_census': {
     'package_or_app_names': 'NOT USED at any selection site (audited :2925/:5221/:6195)',
     'class_name_guesses': 'NOT USED — GL/Compose/WebView triggers are runtime state, not names',
     'newest_object_id_or_last_setParams': 'NOT USED',
     'diagnostic_placeholder_or_demo_renderer': 'diag_owned_pixels counted SEPARATELY from app_owned_pixels; diagnostic pixels can never satisfy the verdict',
   },
   'authority_accounting': {
     'app_draw_ops_increment_sites': ['execution_engine.cpp:3942 (drew_bg — AOSP View.draw drawBackground law)', ':4010 (SurfaceView ops)', ':4054/:4319/:4431/:4509/:4591 (onDraw/text/image family)', ':4127 (custom-view text routing)'],
     'verdict_law': '21-P0-6 pixel ownership + correlated proof; app_content_proof() = auth_root_valid && draw_walk_ran && app_draw_ops>0 (execution_engine.h:411)',
     'masquerade_guard': 'pre-walk framebuffer snapshot frame_baseline_ (execution_engine.h:413-416) — pipeline fills can never count as app content',
     'verdict': 'PASS — only app-owned ops increment; framework/background/fallback cannot satisfy the gate',
   },
 },
 'task_24_deep_audit_legacy_reachability': {
   'authoritative_binary': 'build/miniandroid <- src/main.cpp (Makefile default target)',
   'classification': [
     {'path': 'ApplicationRuntime + RenderPipeline (src/runtime/application_runtime.*, src/renderer/software_renderer.h:422)', 'class': 'LEGACY/TEST-ONLY — reachable ONLY via the experimental megabatch target (exp007_012_megabatch_main.cpp, Makefile:145-146), NOT the authoritative binary; 11 RenderPipeline refs confined to application_runtime.cpp'},
     {'path': 'software_renderer primitives (raster backend used by the engine draw walk)', 'class': 'AUTHORITATIVE — included by execution_engine.cpp:16; the ONE framebuffer owner is ExecutionEngine::framebuffer_ with the census + snapshot laws'},
     {'path': 'synthetic api::View', 'class': 'DEAD — no such class in the authoritative path; src/api/android_stubs.h is forward-declarations only'},
   ],
   'exactly_one_authoritative_owner': True,
   'verdict': 'PASS — legacy paths are DEAD/TEST-ONLY in build/miniandroid; zero dual-owner risk',
 },
 'task_25_view_tree_lifecycle_owner_crosscheck': {
   'engine_law': 'src/framework/android_shadows.cpp:3095-3125',
   'crosscheck_vs_lifecycle_2.11.0': [
     'set(decor, owner) BEFORE any content attaches — MATCHES ViewTreeLifecycleOwner.set contract',
     'walk climbs view->parent reading getTag(key) with checkNotNull ISE "ViewTreeLifecycleOwner not found" — ISE face REPRODUCED historically (R-NEW-379 dooz v23 ComposeView.onAttachedToWindow)',
     'key name-resolved from the app\'s OWN resources.arsc — no hardcoded id, no package name (law-consistent)',
     'owner stored = the engine Activity object implementing the app-DEX LifecycleOwner interface — the walk\'s terminal hop',
   ],
   'verdict': 'LAW CONSISTENT — window-canonical: one set on the decor counterpart before content; runtime proof = every Compose title executes past onAttachedToWindow at HEAD (dooz/gmdice anchors x3)',
 },
 'task_26_traversal_order_crosscheck_vs_viewrootimpl': {
   'engine_laws': [
     'R-NEW-302: addView/removeView/removeAllViews -> requestLayout (android_shadows.cpp:3933/:3947/:4562) — tree change raises relayout for the next stage',
     'S67 F-NEW-198: view-tree dump runs TWICE by law — early pass + end-of-window pass, second overwrites (execution_engine.cpp:5250-5262)',
   ],
   'aosp_law': 'ViewRootImpl.requestLayoutDuringLayout: a requestLayout DURING the layout traversal re-runs layout in the same frame (mLayoutRequested stays true through performTraversals)',
   'known_bounded_divergence': 'the engine honors requestLayout at STAGE granularity (next frame stage), not intra-traversal — a child raising requestLayout mid-layout gets its relayout next stage, not a same-traversal second pass',
   'fan_out_observed': 'no corpus face attributed to this divergence at HEAD (all anchors green); recorded honestly, not fixed',
   'verdict': 'PARTIAL — cross-check done, one bounded divergence documented',
 },
}
json.dump(audit, open(OUT, 'w'), indent=1)
print('audit ->', OUT)

# registry flips for the audited PENDING rows
P = '/home/z/my-project/root_registry.json'
reg = json.load(open(P))
TODAY = '2026-10-08'
flips = {
 'F-NEW-210': ('VERIFIED-CORRECT', 'SP-4..8 authority audit complete — evidence/cont17/renderer_authority_audit.json (selection = runtime semantics only; app_draw_ops guards audited; masquerade guard = frame_baseline_ snapshot; exactly one authoritative owner)'),
 'F-NEW-209': ('VERIFIED-CORRECT', 'SP-2/3/12 chain + white-family separation + capability matrix — evidence/cont17/success_chain_microtimer.json + success_corpus.json (families = renderer_family from runtime evidence)'),
 'F-NEW-198': ('VERIFIED-CORRECT', 'DEEP-AUDIT legacy reachability — legacy ApplicationRuntime/RenderPipeline = TEST-ONLY (megabatch target only); software_renderer primitives = authoritative backend; api::View = DEAD; two-pass view-tree dump law confirmed at execution_engine.cpp:5250'),
 'F-NEW-205': ('VERIFIED-CORRECT', 'view_tree_lifecycle_owner window-canonical cross-check — LAW CONSISTENT (android_shadows.cpp:3095; R-NEW-379 ISE face historically reproduced; key from app resources.arsc)'),
 'F-NEW-206': ('PARTIAL', 'traversal-order cross-check — one known bounded divergence: requestLayout honored at stage granularity vs AOSP same-traversal second pass; no corpus face at HEAD; recorded honestly'),
}
for rid, (st, ev) in flips.items():
    for r in reg['roots']:
        if r['id'] == rid:
            r['status'] = st
            r['evidence'] = ev
            r['date'] = TODAY
            break
from collections import Counter
reg['status_counts'] = dict(sorted(Counter(x['status'] for x in reg['roots']).items(), key=lambda kv: -kv[1]))
json.dump(reg, open(P, 'w'), indent=1)
print('registry flips:', {k: v[0] for k, v in flips.items()})
print('PENDING count now:', reg['status_counts'].get('PENDING'))
