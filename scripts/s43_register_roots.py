#!/usr/bin/env python3
"""S43: register R-NEW-349/350/351/352 in root_registry.json.

R-NEW-349 (implemented): AOSP first-traversal ordering law — attach wave
  STRICTLY precedes measure for setContentView(View). Root-cause of the
  windowRecomposer ISE that killed dooz23 MainActivity.onCreate.
R-NEW-350 (implemented, env-gated MINIANDROID_R350_LAW=1): Class.forName
  overload law at the interpreter level (resolve app-DEX classes +
  initialize=true runs <clinit>) + Class.asSubclass identity law.
  Unblocked the protobuf-javalite MessageInfo chain (DataStore read).
R-NEW-351 (OBSERVED-FAIL): protobuf MessageSchema table builder
  (Llt0;.w) aput-oob length=1 index=1 during the FIRST real schema
  build — the new dooz23 frontier.
R-NEW-352 (OBSERVED-FAIL): microtimer Room getGeneratedImplementation
  retry loop under interpreter-level forName resolution (the reason
  R-NEW-350 is env-gated; A/B evidence attached).

Also refreshes R-NEW-348 (S42 hypothesis replaced by S43 ground truth:
NodeKind bits 7/22 = OnRemeasured/LayoutAware dispatch — c1/U0 are NOT
the root cause; the content-lambda milestone moved to the protobuf and
schema layers evidenced in R-NEW-349/350/351).
"""
import json

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG))
roots = d if isinstance(d, list) else d.get('roots', d.get('entries', []))
ids = {r.get('id') for r in roots}

r349 = {
    "id": "R-NEW-349",
    "title": "dooz23 onCreate death: eager measure inside setContentView(View) dispatched real DEX AbstractComposeView.onMeasure on an UNATTACHED tree — windowRecomposer checkPrecondition(isAttachedToWindow) threw ISE before any composition existed",
    "status": "implemented",
    "priority": "P0",
    "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: every app whose setContentView(View) tree contains DEX onMeasure overrides",
    "observed": "S43 baseline (d5073b4d + R-NEW-347): stderr L242810 [THROWABLE-MSG] ISE \"Cannot locate windowRecomposer; View Lho;@960 is not attached to a window\" thrown from Log0;.b pc=2 (WindowRecomposer.android.kt:288) during the U007 eager measure; L242833 [U007-MEASURE] completes; L242834 APP-BOUNDARY escape at MainActivity.onCreate invoke_pc=306; the S42 attach wave fired only LATER (L242916+). Chain: Ljm;.setContentView -> measure_layout -> custom_view_measure_hook_ -> DEX Lr;.onMeasure (AbstractComposeView) -> Lr;.g ensureCompositionCreated -> Log0;.b windowRecomposer -> require(isAttachedToWindow)=FALSE.",
    "root_cause": "ORDERING violation of the AOSP ViewRootImpl.performTraversals first-traversal law: dispatchAttachedToWindow (whole tree, mAttachInfo stored BEFORE onAttachedToWindow per view) MUST precede performMeasure — on AOSP no measure pass ever observes an unattached view. The engine ran the eager measure INLINE inside ActivityShadow.setContentView while the content tree's attach state was still false; compose relies on the AOSP order (ensureCompositionCreated runs from onMeasure only because AOSP guarantees attach-first).",
    "fix": "(1) ViewShadow.record_pending_setcontent_attach_measure(parent, root) + consume (android_shadows.h/cpp): the shadow (no interpreter access) RECORDS instead of measuring. (2) Engine bridge consume (dalvik_engine.cpp): on setContentView -> dispatch_attached_subtree_from(content_root) [attach wave, mark-first + DEX onAttachedToWindow, one-shot guarded] THEN measure_layout(root) [the U007 measure, now on an attached tree]. Evidence run_r349: [R349-ORDER] deferred attach+measure root=960 -> [R347-ATTACH] onAttachedToWindow view=960 Lho; -> child=1241 Lt4; created+attached DURING the wave (ensureCompositionCreated from the AOSP attach path) -> measure done; windowRecomposer ISE count 1 -> 0. Regression: battery 90/92 (only pre-existing EXT-01/02 external-fixture gaps); gmdice 108922 -> 1,745,009 nonwhite (16x); unote 14,850 -> 236,521 (16x); ChessClock screenshot SHA e4a2d7c9... byte-identical golden; microtimer 1,042,368 (A/B-verified equal to S42 baseline after the SCOPE fix below).",
    "severity": "high",
    "commit": "S43",
    "next": "SCOPE NOTE: an S43 draft also drained pending_child_attaches after setContentView — that fired DEX onAttachedToWindow for XML-inflated trees (microtimer RoTimeControl) before their post-inflate field setup, a lateinit ISE escaped onCreate and the app went white (A/B-proven). The landed law drains pending-child-attaches at addView/addViewInLayout ONLY; the R349 attach wave starts from the recorded content root only."
}
r350 = {
    "id": "R-NEW-350",
    "title": "protobuf-javalite MessageInfo chain dead: 3-arg Class.forName(String,Z,ClassLoader) silently void + Class.asSubclass unimplemented -> defaultInstanceMap never populated -> UOE 'No factory is available for message type' / bare ISE killed the DataStore theme read",
    "status": "implemented",
    "priority": "P0",
    "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: any DataStore/protobuf-lite app",
    "observed": "S43 baseline: runBlocking{settings.getTheme()} (MainActivity.onCreate) -> DataStore read -> Las0;.<init> Class.forName('androidx.datastore.preferences.protobuf.DescriptorMessageInfoFactory') CNFE (EXPECTED javalite fallback, correctly caught) -> composite factory Lzr0;=[Lyb0;->b(GeneratedMessageInfoFactory), fallback] -> Lyb0;.b isSupported TRUE ([R350-IAA] recv=Lbc0; arg=Ly81; -> TRUE) -> Lyb0;.a asSubclass SILENT-NULL -> Lbc0;.d received NULL Class ([R350-SHAPE] a0k8=NULL_REF) -> forName silent -> defaultInstanceMap.get x2 NULL -> dynamicMethod(GET_DEFAULT_INSTANCE) NULL -> bare ISE -> RuntimeException('Unable to get message info for y81') x23 -> escaped MainActivity.onCreate invoke_pc=0xc1.",
    "root_cause": "Two stacked host-class gaps: (1) java.lang.Class.forName overloads — the 3-arg form was dispatched by the interpreter (idx=6825, [R350-FN2] proof) but never reached the bridge forName branch (zero [R350-FN]/[R350-BR] logs, zero CNFE) — silently void, so initialize=true NEVER ran the message class <clinit> and defaultInstanceMap stayed empty; (2) java.lang.Class.asSubclass(Class) implemented NOWHERE — OpenJDK law: returns the SAME Class reference when assignable, else CCE; its silent-void null poisoned every downstream step (Lbc0;.d(null) -> getName/getClassLoader/forName on null).",
    "fix": "(1) Class.forName OVERLOAD LAW at the interpreter level in execute_invoke_static BEFORE try_recursive_invoke/bridge (same pre-emption pattern as the R-NEW-347 View.measure law): dotted-name -> L-descriptor -> class_info_index_ resolve -> ensure_class_initialized when the initialize flag is set (both overloads carry it in args[1]) -> make_class CLASS_REF; unknown name -> deferred ClassNotFoundException (real law). (2) Class.asSubclass law in the Class bridge next to cast: null-target -> NPE; assignable (is_subclass_of on the L-FORM referent — the first attempt wrongly used the dotted form and answered CCE for Ly81; asSubclass Lbc0;) -> SAME reference identity; else deferred CCE. ENABLING GATE: the forName interpreter law is DEFAULT-OFF (MINIANDROID_R350_LAW=1) because unconditionally-ON it starved microtimer's Room initDb retry loop (see R-NEW-352); dooz23 evidence runs enable it. Evidence (dooz, MINIANDROID_R350_LAW=1): windowRecomposer ISE 0; 'Unable to get message info' 23 -> 0; [R350-ASSUB] Ly81; asSubclass Lbc0; -> SAME reference; Ly81;.<clinit> result=OK + defaultInstanceMap.put; the run advances into the FIRST real MessageSchema build (R-NEW-351).",
    "severity": "high",
    "commit": "S43",
    "next": "R-NEW-351: the schema-table builder AIOOBE is now the frontier inside the first real DataStore parse; microtimer interaction documented as R-NEW-352."
}
r351 = {
    "id": "R-NEW-351",
    "title": "dooz23 FIRST real protobuf schema build dies: MessageSchema table builder Llt0;.w aput-oob 'length=1; index=1' — the int[] field table sized from the parsed MessageInfo is 1 short for the writer loop",
    "status": "OBSERVED-FAIL",
    "priority": "P0",
    "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: any DataStore/protobuf-lite app (every read/write needs the schema)",
    "observed": "S43 run (MINIANDROID_R350_LAW=1, post R-NEW-349/350): chain advances past the factory (isSupported TRUE, asSubclass SAME-reference, defaultInstance registered via <clinit>, [R337-UNSAFE] objectFieldOffset Ly81;.preferences_ -> 280) into Llt0;.w (MessageSchema ctor, DEX size 1009B) — aput v1, v11, v7 at byte 0x772 (pc unit 953) throws ArrayIndexOutOfBoundsException length=1 index=1; the exception unwinds 20 frames through the compose-coroutine machinery and escapes MainActivity.onCreate. nonwhite=2 (the first non-white pixels ever recorded for dooz23 — the render stack painted something).",
    "root_cause_hypothesis": "The int[] table at the aput was new-array'd with a size derived from the MessageInfo (Lta1;) contents — the objects array (filled-new-array {v2,v3} [Ljava/lang/Object; = field-name + field-type, LENGTH 2 in DEX law) and/or the schema-string counts. The filled-new-array handler's arg extraction was audited (UNIFIED_011.2 FNA-FIX is correct in HEAD), so the suspicion is upstream: either the info-string counts (MUTF-8 NUL handling verified CORRECT — 0xC0 0x80 decodes to a real 0x00 byte, so split('\\u0000') should work) or a table-builder loop bound vs the objects-array length mismatch inside Llt0;.w needs a per-instruction trace. protobuf MessageSchema.kt/java sources are the next oracle (github.com/protocolbuffers/protobuf + the javalite jar).",
    "next": "(1) Dump Llt0;.w fully (1009B) and the Lta1; ctor to map which array (v11 rebinding) the aput targets and where its size comes from; (2) probe the objects array the engine built at Ly81;.c case 3 (filled-new-array {v2,v3}) — verify heap length == 2; (3) validate against protobuf MessageSchema field-table law (fields_count*3 / *2 sizing visible at 0x2f2/0x2fa); (4) close -> the DataStore theme read completes -> runBlocking unblocks -> the compose content lambda composes for real.",
    "evidence": "/tmp/s43_sweep/dooz_on.log [SYNTH-EXC] aput-oob method=Llt0;.w pc=953 + [R337-UNSAFE] offset 280 caller=Llt0;.w; crash.log 38 EXC (all one AIOOBE unwind); nonwhite=2/2073600",
    "discovered": "S43"
}
r352 = {
    "id": "R-NEW-352",
    "title": "microtimer Room initDb retry loop under interpreter-level forName resolution — 50k re-visits of the SAME forName invoke starve the run budget (the reason R-NEW-350 is env-gated MINIANDROID_R350_LAW=1)",
    "status": "OBSERVED-FAIL",
    "priority": "P1",
    "app": "dubrowgn.microtimer_8 — general: Room getGeneratedImplementation users",
    "observed": "S43 A/B (stash->rebuild->run vs unstash->rebuild->run, hash-pinned APK): S42 baseline renders 1,042,368 nonwhite rc=0 with the BRIDGE-level forName resolving Database_Impl ([M3-REFLECT] Class.forName 'dubrowgn.microtimer.db.Database_Impl' -> ...); with the interpreter-level forName law ON, MainActivity.onCreate re-visits the forName invoke (pc_units=266) 50001x (HALT-LOOP guard), a lateinit ISE (Lm/c; via La/e;.n 'lateinit property ... has not been initialized') escapes at invoke_pc=266 and the frame goes white rc=1.",
    "root_cause_hypothesis": "Under interpreter-level resolution the forName return (CLASS_REF + ensure_class_initialized) reaches Room's getGeneratedImplementation differently than under bridge-level resolution — the app's own code then retries the SAME invoke in a loop instead of proceeding. The retry loop's back-edge and the differing post-forName step (getDeclaredConstructor/newInstance path) need a frame-level trace; the interpreter law also bypasses the try_recursive_invoke layer where the M3-19 active-cycle guard would have stubbed re-entrant repeats at near-zero cost.",
    "next": "(1) Trace the loop body between two forName visits (move-result -> checkNotNull -> getDeclaredConstructor -> newInstance -> which branch jumps back); (2) compare the S42 bridge-path result shape (was ensure_class_initialized actually reached? was the return CLASS_REF or a stale value?) against the interpreter-law result; (3) either restore loop-progress semantics (why did the S42 path leave the app green) or make the interpreter law idempotent-cheap and re-enable it by default.",
    "evidence": "/tmp/s43_sweep/mt_ab.log (baseline green, bridge forName resolve) vs /tmp/s43_sweep/mt7.log (50k [R350-FN2]+[R350-FORNAME] pairs, HALT-LOOP) — A/B discipline: identical APK sha, identical flags except the law gate",
    "discovered": "S43"
}
r348_refresh = {
    "status": "SUPERSEDED-BY-EVIDENCE",
    "root_cause_hypothesis": "S43 GROUND TRUTH (replaces the S42 'composition-services' hypothesis): the Lqz0;.g capability bits are compose-ui NodeKind flags — bit 7 (0x80) = Nodes.OnRemeasured (MeasuredSizeAwareModifierNode), bit 22 (0x400000) = Nodes.LayoutAware (ui/commonMain/.../node/NodeKind.kt); Lpz0;.c1/U0 = the OnRemeasured dispatch over the NodeCoordinator chain (a NORMAL null-chain path, not the blocker — c1 dispatches the OnRemeasured class and an empty chain falls through to Lje1;.B legitimately). The content-lambda milestone was BLOCKED further upstream by R-NEW-349 (attach-before-measure ordering) and then by the protobuf DataStore chain (R-NEW-350/351); the invokeComposable contract itself is confirmed from 1.11.4 sources (jvmAndAndroidMain Expect: composable as Function2<Composer,Int,Unit> -> realFn(composer, 1); DEX map: Lr90;=Function2, Lj90;=ComposableLambda (abstract h(Object,Object)Object), Lom;=ComposableLambdaImpl wrapper, Lrr0;=MainActivity content lambda)."
}

if 'R-NEW-349' not in ids:
    roots.append(r349)
if 'R-NEW-350' not in ids:
    roots.append(r350)
if 'R-NEW-351' not in ids:
    roots.append(r351)
if 'R-NEW-352' not in ids:
    roots.append(r352)
for r in roots:
    if r.get('id') == 'R-NEW-348':
        r.update(r348_refresh)

json.dump(d, open(REG, 'w'), indent=2, ensure_ascii=False)
print("registry roots now:", len(roots))
