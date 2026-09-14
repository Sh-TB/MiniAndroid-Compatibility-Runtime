#!/usr/bin/env python3
"""S42: register R-NEW-347 (implemented) + R-NEW-348 (new frontier).
R-NEW-347 = the AOSP attach-on-add + real-DEX measure chain (5 generic laws,
evidence-locked, regression-clean). R-NEW-348 = the compose 1.11.4
composition-capabilities gate that still blocks the content lambda."""
import json, sys

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG))
roots = d if isinstance(d, list) else d.get('roots', d.get('entries', []))
ids = {r.get('id') for r in roots}

r347 = {
    "id": "R-NEW-347",
    "title": "dooz23 first-frame chain (compose BOM 2026.06.01 / runtime 1.11.4): AndroidComposeView never attached, never DEX-measured, View.measure void, File path/name family missing — content composition started but root stayed 0x0",
    "status": "implemented",
    "priority": "P0",
    "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: any compose app; File/String laws general JVM",
    "observed": "S42 run_a: UC009 attach wave ran BEFORE the AndroidComposeView existed (created lazily during first onMeasure via ensureCompositionCreated -> La72;.a pc=112 addView into the already-attached ComposeView) -> pending onReadyForComposition request (Lt4;->n0) stored but NEVER consumed (Lt4;.onAttachedToWindow pc 640-662 is the ONLY consumer) -> content lambda never ran. Post-attach-fix (run_b): composition started (ComposerImpl Lxk0; live, slot ops), but Lt4; measured 0x0: (1) F10 DEX onMeasure hook skipped containers; (2) overrides_on_measure flag never set on the invoke-direct ctor path; (3) View.measure(I I)V was silent-void so AbstractComposeView.onMeasure's child.measure() never measured AndroidComposeView (DEX Lr;.i: getChildAt(0) -> child.measure(childSpec) -> setMeasuredDimension(child.measuredWidth+padding)); (4) getMeasuredWidth/Height had NO implementation; (5) the DataStore file-name lambda (Lg8;.a) hit File.getName()==null -> uncaught NPE killed the pass (run_i: SIOOBE from lastIndexOf garbage; run_k: File(null, \"datastore/settings.preferences_pb\") path capture empty).",
    "root_cause": "Six stacked generic gaps vs AOSP/OpenJDK contracts (all fixed, zero class hacks): (1) AOSP ViewGroup.addViewInner child-attach law missing; (2) UC009/attach one-shot guard missing (double-dispatch window); (3) F10 real-DEX onMeasure law excluded containers + invoke-direct ctor path never recorded overrides_on_measure; (4) AOSP View.measure(final) contract missing (measure -> onMeasure dispatch -> default getDefaultSize fallback) + getMeasuredWidth/Height accessors missing; (5) java.io.File name-component law missing (getName/getPath/getParent/getParentFile/isAbsolute/getAbsolutePath); (6) java.io.File constructor path-assembly law missing (incl. OpenJDK File(null, child) degradation) + String.lastIndexOf(int[,int]) law missing (fromIndex<0 -> -1).",
    "fix": "All six laws implemented (S42, commits S42/S42-fix2): ViewShadow pending_child_attaches_ queue + record/consume (android_shadows.h/cpp); engine dispatch_attached_subtree_from() + bridge_to_api pending-consume + UC009 one-shot guard (dalvik_engine.h/cpp); F10 hook extended to containers by overrides_on_measure (layout_inflater.cpp); receiver-based View.measure law BEFORE try_shadow_dispatch + View.onMeasure default write-through + dex/measured one-store sync + getMeasuredWidth/Height accessors; File name-component + ctor path-assembly laws; String.lastIndexOf law. Evidence: [R347-ATTACH] parent=888 attached -> pending child-attach child=1512/1513; [R347-ATTACH] onAttachedToWindow dispatched view=1512/1513 class=Lt4;; [R347-MEASURE] view=1512 class=Lt4; dex_onmeasure=YES (real compose measure world ran); [R347-FILE-CTOR] path=\"datastore/settings.preferences_pb\"; [R347-FILE] getName -> \"settings.preferences_pb\"; [R347-LILO] lastIndexOf(46,22) -> 8; substring -> \"preferences_pb\" (DataStore file chain complete). Regression: gmdice 108922 / microtimer 65090 / unote 14850 nonwhite EXACT S41 goldens.",
    "severity": "high",
    "commit": "S42",
    "next": "R-NEW-348: composition pass (44 ComposerImpl calls) terminates at Lpz0;.c1 -> U0(Z)Lwt0; null bail — compose 1.11.4 composition-capabilities orchestration (Lqz0;.g = capability bits 128|0x400000; root-node Lkz0;.d composer != querying composer -> null) — the app content lambda ({ Content() } -> Dooz composables) is still never invoked; that gate is the exact next frontier."
}
r348 = {
    "id": "R-NEW-348",
    "title": "dooz23: compose 1.11.4 composition-capabilities gate — Lpz0;.c1() aborts via U0(Z)Lwt0;==null before ever invoking the app content lambda",
    "status": "OBSERVED-FAIL",
    "priority": "P0",
    "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: compose runtime 1.11.x apps",
    "observed": "S42 run_l/run_m with R-NEW-347 fixed: chain Ls7;.i(ComposeViewContext) runs (RET-TRACE: returns Le12; obj#232 = COROUTINE_SUSPENDED sentinel — outer wrapper suspends, inner composeInitial ran synchronously per runtime 1.11.4 sources fetched from Google Maven); ComposerImpl Lxk0; executed ~44 real calls (K0 composer wiring, m0(J), Z0, slot ops S(IILjava/util/Map;Lf90;Lf90;), l1, l0, c1, U0(Z)x2) then TRUE QUIESCENCE — zero io.github.yamin8000.dooz composables executed (only MainActivity lifecycle dispatches); root LayoutNode (Lel0;) empty -> Lt4;.onMeasure dex_onmeasure=YES but 0x0 -> blank frame (nonwhite=0).",
    "root_cause_hypothesis": "Lpz0;.c1()V (DEX ground truth): U0(Z)Lwt0; = find-owning-composition via root LayoutNode (Lpz0;->s : Lel0; -> .I : Lkz0; -> .d composer / .f composition) — returned null twice (root node's stored composer != querying composer; parent-walk S0() -> null). c1 bails to Lje1;.B(Lyn1;, Lyn1;, Lf90;) and the pass ends. c1 is gated by Lqz0;.g(I)Z = capability mask test (bits 128 | 0x400000) on Lwt0;->h/.g flags — the compose 1.11.4 composition-services/capabilities orchestration.",
    "next": "(1) Identify Lwt0;/Lkz0;/Lje1; against runtime 1.11.4 sources (already at /tmp/s42/runtime_src, ui 1.11.4 at /tmp/s42/ui_src): map ControlledComposition capability flags (bits 128, 0x400000) and the composition-services registration path — WHO must set Lkz0;->d (owner's composer) and WHEN; (2) verify the owner (AndroidComposeView Owner) wiring: Lkz0;.d is set at composition creation — probe whether our run created TWO composers (one from the suspended Ls7;.i wrapper, one from composeInitial) making the root-node lookup mismatch; (3) implement the missing generic law(s) in the capabilities/orchestration path; (4) then the content lambda { Content() } should finally invoke the Dooz composables.",
    "evidence": "/tmp/s42/run_l + run_m stderr: [RET-TRACE] Ls7;.i -> obj#232 Le12; ; Lxk0; call chain tail ...c1() -> U0(Z)x2 -> silence; screenshot nonwhite=0",
    "discovered": "S42"
}
if 'R-NEW-347' not in ids:
    roots.append(r347)
if 'R-NEW-348' not in ids:
    roots.append(r348)
if isinstance(d, list):
    json.dump(roots, open(REG, 'w'), indent=1, ensure_ascii=False)
else:
    for k in ('roots', 'entries'):
        if k in d:
            d[k] = roots
            break
    json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print("registry roots:", len(roots))
