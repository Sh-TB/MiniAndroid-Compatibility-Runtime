#!/usr/bin/env python3
"""CONT-75 registry update — F-NEW-277 lever decode.

Changes (no id collisions, metadata recomputed):
  F-NEW-378  (NEW, CLASSIFIED, P0) coroutine cancellation naked-unwind
             kills the measure pass — dooz's current first divergence
             decoded to the exact throw site and propagation chain.
             CLASSIFIED under the fixture-first discipline (no blind fix).
  F-NEW-379  (NEW, CLASSIFIED, P2) R350-FORNAME kotlin-reflect
             ReflectionFactoryImpl ClassNotFoundException — third app
             evidence point (dooz) for CONT-73's shared finding.
  F-NEW-277  evidence update: the next lever is refined from the generic
             deriveStateLocked/workContinuation note to the concrete
             continuation-boundary cancellation-conversion law (F-NEW-378).
"""
import json
from collections import Counter

PATH = "/home/z/my-project/root_registry.json"
r = json.load(open(PATH))
roots = r["roots"]
by_id = {x["id"]: x for x in roots}
assert len(by_id) == len(roots), "duplicate ids in registry"
assert "F-NEW-378" not in by_id and "F-NEW-379" not in by_id

roots.append({
    "id": "F-NEW-378",
    "status": "CLASSIFIED",
    "priority": "P0",
    "title": (
        "COROUTINE CANCELLATION NAKED-UNWIND KILLS THE MEASURE PASS (dooz "
        "current first divergence at aabf7bb9, CONT-75 decode): dooz's "
        "R8-merged CancellationException (La; extends java.util.concurrent."
        "CancellationException) is thrown by a JobSupport completion-node "
        "invoke (La7;.m pc=32, instance-of-guarded conditional throw in an "
        "R8 synthetic lambda class: 2 synthetic fields e:I + f:Object, one "
        "direct lambda factory + one virtual interface impl) and then "
        "unwinds THROUGH the compose measure pass — Lzs.m dies with "
        "handler=NOT_FOUND at depth 17, Lt4.onMeasure (AndroidComposeView) "
        "answers 0x0 FAILED(no write-back), isPlaced stays false on the "
        "whole tree, APP_DRAW_OPS is missing, frame truth = "
        "DEFAULT_BACKGROUND_ONLY. The exception eventually lands in a "
        "typed catch (Llo.B, type=La;) after re-throw cycles through two "
        "catch-all handlers (Lse1.m, Let.a) — the coroutine machinery "
        "SURVIVES, but the measure pass is already dead."
    ),
    "layer": "coroutines/continuation-boundary + compose/measure-pass "
             "(dalvik_engine deferred-exception propagation)",
    "root_cause": (
        "Kotlin/ART law: a CancellationException is coroutine CONTROL FLOW, "
        "not an application failure. At the continuation boundary a "
        "cancellation must convert to the Job state machine (JobSupport "
        "finally -> resumeWith(Result.failure) / "
        "CancellableContinuationImpl.getCompletionExceptionOrNull) — it "
        "must never naked-unwind through frames that are not coroutine "
        "frames. MiniAndroid's deferred-exception propagation is faithful "
        "Dalvik frame-to-frame unwinding, but the coroutine-shade layer has "
        "NO continuation-boundary conversion, so a cancellation raised "
        "inside a completion-node invoke during the launch-frame "
        "composition travels into the measure pass that is running on the "
        "same thread stack (launch-frame inlined execution model) and "
        "kills it. Falsified alternative readings: (a) NOT the null-text "
        "ctor of the old F-NEW-265 chain — Lm7;.<init> never fires this "
        "run; (b) NOT F-NEW-270 (fixed) nor F-NEW-271 (fixed) — no "
        "ROOT-059 route and no F271-READ/WRITE rows; (c) the two later "
        "VirtualMachineError F084-HALT rows in the same log are the "
        "wall-clock-budget artifact, a DIFFERENT (non-)phenomenon."
    ),
    "evidence": (
        "CONT-75 (issue #364) at aabf7bb9, binary 1ef983a6ff71dade: "
        "[THROW-SITE] #1 'La; at La7;.m pc=32 depth=17 code[b17 245b 1f2d "
        "422 2c 2070 8f 34 <427 41f 35f 21f 58e] sz=90' — cu 0x0427 = "
        "throw v4, preceded by const-class/instance-of guard; #2/#3 are "
        "the catch-all re-throw cycles. crash.log: 6x EXC-UNWIND La; "
        "(Lzs.m depth17 -> Lte1.f 16 -> Lse1.s 15 -> Lg.q 13 -> Lg.h 12 "
        "-> Lat.a 10). [EXCEPTION] La7;.m pc=32 handler=NOT_FOUND. "
        "[DEX-MEASURE] Lt4.onMeasure -> 0x0 FAILED(no write-back). "
        "[F271-CLASS] La7; ifield e:I + f:Object. La; superclass decoded "
        "from the dooz dex directly: java.util.concurrent."
        "CancellationException. THROW-SITE diag is env-gated "
        "(MINIANDROID_THROW_TRACE=1) and wall-verified zero-drift (dooz "
        "31ddd4d5 x3 + opencalc f25b754c x3 MATCH, negatives 19/19 after "
        "the canonical probe prelude, reinstall 8/8, goldens 4/4)."
    ),
    "fanout": (
        "EVERY Kotlin-coroutine app whose first-frame composition is "
        "cancelled or whose frame-clock await fails during the launch "
        "frame (navigation-compose + collectAsState families — the F6 "
        "surface, same domain as F-NEW-277); any app that cancels a job "
        "while a measure/layout pass is in flight on the same stack."
    ),
    "fix_surface": (
        "NAMED, NOT IMPLEMENTED (fixture-first discipline): a "
        "continuation-boundary cancellation-conversion law — (1) at every "
        "suspend-point resume with a CancellationException-derived "
        "throwable inside an INACTIVE job context, convert to the Job "
        "state transition instead of an in-flight throwable; (2) "
        "JobSupport node invoke must wrap its throw with the "
        "invokeOnCompletion contract (the caller's try/finally in the "
        "coroutine machinery catches and records). Requires FIRST a "
        "minimal deterministic fixture (CancellableContinuation "
        "cancel-during-resume) proving the boundary gap in isolation; "
        "the fence shape (shadow-layer conversion vs interpreter-level "
        "boundary marker) is decided by that fixture."
    ),
    "upstream_source": (
        "kotlinx.coroutines JobSupport.kt (unifyState$throwOnCompletion, "
        "Node.invoke, invokeOnCompletion contract), "
        "CancellableContinuationImpl.kt (resumeWith(Result.failure), "
        "getCompletionExceptionOrNull), "
        "kotlinx/coroutines/CancelledCoroutine law in kotlin-stdlib "
        "intrinsics; R8 global-synthesis merging CancellationException "
        "into La;."
    ),
})

roots.append({
    "id": "F-NEW-379",
    "status": "CLASSIFIED",
    "priority": "P2",
    "title": (
        "R350-FORNAME CLASSNOTFOUND: kotlin.reflect.jvm.internal."
        "ReflectionFactoryImpl — the kotlin-reflect runtime is absent from "
        "the runtime's classpath, so every app whose <clinit> does "
        "Class.forName(\"kotlin.reflect.jvm.internal.ReflectionFactoryImpl\") "
        "takes a deferred CNFE. CONT-73's ten-app triage named this as the "
        "SHARED candidate root of BOTH blank candidates (Guandan, "
        "AndStatus2048); CONT-75 confirms a THIRD evidence point: dooz's "
        "Lub1;.<clinit> pc=3 throws the same deferred CNFE (caught by its "
        "own catch-all at 0xe)."
    ),
    "layer": "class-path / kotlin-reflect availability (R350-FORNAME "
             "shadow)",
    "root_cause": (
        "kotlin-reflect (kotlin.reflect.full / kotlin-stdlib reflection "
        "impl) is not packaged with the runtime and app APKs that "
        "reference it carry only the API stubs; ART would answer the same "
        "CNFE, so this is an AVAILABILITY gap, not a resolution bug — but "
        "the deferred-CNFE delivery is legal (caught by the app's own "
        "catch-all) and apps differ in whether they proceed. The blank "
        "correlation (Guandan + AndStatus2048 both blank AND both hit "
        "this) makes it a named candidate, NOT a proven cause — the "
        "kotlin-reflect clinit failure may be benign in both apps with a "
        "different shared blocker still ahead (fixture-first: a fixture "
        "must isolate what the app does AFTER the caught CNFE)."
    ),
    "evidence": (
        "CONT-73 triage: shared finding rows for Guandan + AndStatus2048 "
        "(both NO_ROOT/WINDOW_ROOT blanks). CONT-75 dooz: [SYNTH-EXC] "
        "R350-FORNAME (deferred) CNFE kotlin.reflect.jvm.internal."
        "ReflectionFactoryImpl method=Lub1;.<clinit> pc=3 -> deferred "
        "handler @0xe catch-all — dooz renders splash only (F-NEW-378 "
        "chain), so this CNFE is NOT dooz's content blocker. Third "
        "independent sighting consistent with the honest-miss note in "
        "F-NEW-369's oracle evidence."
    ),
    "fanout": (
        "Apps embedding kotlin-reflect (DI/metadata-driven frameworks, "
        "serialization, some Compose tooling paths); currently 3 corpus "
        "apps show the CNFE."
    ),
    "fix_surface": (
        "NAMED, NOT IMPLEMENTED: (a) cheapest — bundle a kotlin-reflect "
        "shim providing ReflectionFactoryImpl with the subset of "
        "callByName/typeOf the corpus uses; (b) honest-loud — keep the "
        "CNFE but record a R350-FORNAME census row per app so triage can "
        "correlate. Fixture first: a two-app A/B (app that proceeds past "
        "the caught CNFE vs one that does not) to prove causality before "
        "any shim."
    ),
    "upstream_source": (
        "kotlin.reflect.jvm.internal.ReflectionFactoryImpl (kotlin-reflect "
        "jar), kotlin.reflect.internal.ReflectionFactory (kotlin-stdlib "
        "entry), Class.forName semantics JLS 12.4.2."
    ),
})

# F-NEW-277 evidence refinement
x = by_id["F-NEW-277"]
x["evidence"] = str(x.get("evidence", "")) + (
    " CONT-75 pointer 2026-10-17: the next lever is now CONCRETE — the "
    "dooz launch-frame composition is being killed by a coroutine "
    "cancellation that naked-unwinds through the measure pass (F-NEW-378: "
    "La;=CancellationException thrown at La7;.m pc=32, Lzs.m "
    "handler=NOT_FOUND depth 17, Lt4.onMeasure FAILED no-write-back). The "
    "deriveStateLocked/workContinuation wake-up note remains valid for the "
    "post-fix runner re-arm, but the FIX ORDER changes: the continuation-"
    "boundary cancellation-conversion law (F-NEW-378) comes FIRST — a "
    "runner that wakes into a cancellation still dies."
)

r["summary"]["total_roots"] = len(roots)
r["summary"]["total"] = len(roots)
by_status = Counter(x["status"] for x in roots)
r["summary"]["by_status"] = dict(by_status)
open_ids = [x["id"] for x in roots if x["status"] not in (
    "ROOT-CAUSED-FIXED", "SUPERSEDED-BY-EVIDENCE", "CLOSED", "NOT_APPLICABLE",
    "REJECTED", "FIXED")]
r["summary"]["open_frontiers"] = open_ids
r["summary"]["last_updated"] = (
    "CONT-75: F-NEW-378 CLASSIFIED P0 (coroutine cancellation naked-unwind "
    "kills the measure pass — dooz current first divergence fully decoded: "
    "La;=CancellationException, throw site La7;.m pc=32, Lzs.m "
    "handler=NOT_FOUND, Lt4.onMeasure FAILED no-write-back; fixture-first, "
    "no blind fix) + F-NEW-379 CLASSIFIED P2 (R350-FORNAME kotlin-reflect "
    "CNFE, third app evidence point: dooz Lub1.<clinit> after CONT-73's "
    "Guandan+AndStatus2048) + F-NEW-277 lever refined to the continuation-"
    "boundary conversion law. MINIANDROID_THROW_TRACE env-gated diag added "
    "(THROW-SITE rows with engine-decoded bytecode window); wall dooz/"
    "opencalc zero drift, negatives 19/19, reinstall 8/8, goldens 4/4. "
    "Registry 683->685."
)

json.dump(r, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry updated: 683 ->", len(roots))
print("F-NEW-378 CLASSIFIED P0, F-NEW-379 CLASSIFIED P2 registered")

cp = "/home/z/my-project/canonical/root_cause_registry.json"
import shutil
shutil.copyfile(PATH, cp)
print("mirrored to", cp)
