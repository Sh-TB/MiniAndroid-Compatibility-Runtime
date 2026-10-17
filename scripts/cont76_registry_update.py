#!/usr/bin/env python3
"""cont76_registry_update.py — CONT-76 closure-wave registry updates.

1. F-NEW-378: decode COMPLETE (AbortFlowException identity + throw-site
   contract + faithful-containment proof); engine-side boundary-conversion
   fix REJECTED with reason; lever re-pointed to F-NEW-277 runner re-arm.
2. F-NEW-379: REJECTED as the content blocker of all three cited apps
   (fresh current-HEAD runs: the kotlin-stdlib Reflection <clinit> catches
   the CNFE in its own handler and completes OK in every app).
3. MG-310: dedicated fence BUILT + GREEN 7/7 (JLS 12.4.1 laws locked).
4. MG-150: dedicated fence BUILT + GREEN 3/3 (current hit-test semantics
   locked; transform-map delta = named frontier).
5. MG-147: note CORRECTED — single-pointer model is a documented boundary;
   multi-pointer fencing requires a runtime feature (rejected as fence).
"""
import json
import sys

ROOT = "/home/z/my-project"
P1 = f"{ROOT}/root_registry.json"
P2 = f"{ROOT}/canonical/root_cause_registry.json"


def main():
    r = json.load(open(P1))
    roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
    ids = [x.get("id") for x in roots]
    assert len(ids) == len(set(ids)), "duplicate root ids"

    by_id = {x["id"]: x for x in roots if "id" in x}

    # ── F-NEW-378 ────────────────────────────────────────────────────────
    f378 = by_id["F-NEW-378"]
    f378["title"] = (
        "FLOW-ABORT CONTROL FLOW DECODED THROUGH THE MEASURE PASS (dooz "
        "current first divergence, CONT-76 decode-complete; supersedes the "
        "CONT-75 'cancellation naked-unwind' framing): the thrown La; is "
        "kotlinx.coroutines AbortFlowException(owner) — dex-verified message "
        "'Flow was aborted, no more elements needed', extends "
        "java.util.concurrent.CancellationException, empty fillInStackTrace; "
        "Lr50; is FlowCollector.emit(Object,Continuation). The throw site "
        "La7;.m branch-1 is the first()/take()-family abort collector shape: "
        "store the emitted value into the result holder (Ltb1;->e) then "
        "throw AbortFlowException(this). The unwind through the compose "
        "measure frames is FAITHFUL ART behavior and the machinery's own "
        "typed catch (Llo.B) contains it — the exception never escapes the "
        "engine. The REAL divergence is upstream state (why a flow abort "
        "fires while the collection is nested inside the measure pass) — "
        "the F-NEW-277 runner-re-arm domain.")
    f378["status"] = "CLASSIFIED"
    f378["fix_surface"] = (
        "RESOLVED THIS WAVE (CONT-76): the named 'continuation-boundary "
        "cancellation-conversion' ENGINE law is REJECTED with reason — the "
        "dex machinery already contains the AbortFlowException at its own "
        "typed catch (Llo.B terminal); a boundary conversion would SWALLOW "
        "legal control flow (violates the no-swallow red line) and the "
        "unwind is faithful. The engine is not the diverging layer. The "
        "real lever is F-NEW-277 (runner re-arm): make the parked "
        "awaitFrame/awaitWorkAvailable continuation resume so the stale "
        "collect-during-measure state never arises. Fixture requirement "
        "for that lever: the existing dooz repro + the CONT-75 throw-site "
        "diag.")
    f378["verified_current"] = (
        "CONT-76 (scripts/cont76_decode_la7.py + cont76_decode_family.py, "
        "androguard direct dex decode at aabf7bb9 APK "
        "io.github.yamin8000.dooz_23.apk): La; fields/ctor decoded "
        "(<init>(Lr50;) = AbortFlowException(owner), message string "
        "verified in the dex, fillInStackTrace empty); La7.m full "
        "disassembly (packed-switch e:I 3 branches: float-consumer / "
        "abort-throw / Liu;.h(Z,Continuation)); Lzs.m full disassembly "
        "(kotlin-stdlib continuation machine — literal 'call to resume "
        "before invoke with coroutine', COROUTINE_SUSPENDED check "
        "Lwr;->e, direct delegate call Lr50;.m). CONT-75 run evidence "
        "run/cont75/dooz_cfd: [EXC-UNWIND] chain depth 17..10, terminal "
        "typed catch Llo.B (La;).")
    f378["date"] = "2026-10-17"

    # ── F-NEW-379 ────────────────────────────────────────────────────────
    f379 = by_id["F-NEW-379"]
    f379["status"] = "REJECTED_WITH_REASON"
    f379["title"] = (
        "R350-FORNAME kotlin-reflect ReflectionFactoryImpl CNFE — REJECTED "
        "as a content blocker (CONT-76 fresh current-HEAD A/B): the CNFE is "
        "the kotlin-stdlib Reflection.<clinit>'s OWN intentional fallback "
        "path (try impl-class, catch ClassNotFoundException, fall back to "
        "the base ReflectionFactory). All three cited apps catch it in the "
        "class's own handler and <clinit> completes OK — the apps proceed "
        "past it; their blank blockers are elsewhere.")
    f379["fix_surface"] = (
        "NO SHIM REQUIRED (rejected): fresh runs at HEAD "
        "ae558af8/binary 1ef983a6ff71dade show — dooz Lub1;.<clinit> "
        "catch-all @0xe (CONT-75), Guandan "
        "Lkotlin/jvm/internal/Reflection;.<clinit> deferred handler @0xe "
        "typed CNFE -> result=OK (run/cont76/guandan, face "
        "4e58f3a378891497 == CONT-73 record), AndStatus2048 Lk00;.<clinit> "
        "deferred handler @0xe -> result=OK (run/cont76/andstatus, splash "
        "31ddd4d5b8e6d18e == record). Guandan's real blocker: empty "
        "composition (AndroidComposeView children=0, compose root measured "
        "1080x1920, dark surface 1 color 8,36,26 = F-NEW-277/378 family). "
        "AndStatus2048's real blocker candidate: NPE "
        "Ljava/lang/Object;.getClass on null in Lt60;.getValue / Ll90;.u "
        "pc=160 (kotlin delegate chain) — named for the next decode, "
        "separate from kotlin-reflect.")
    f379["date"] = "2026-10-17"

    # ── MG-310 / MG-150 / MG-147 live in the micro-gap registry ─────────
    mgp = f"{ROOT}/docs/MICRO_GAP_REGISTRY.json"
    mg = json.load(open(mgp))
    mg310 = mg["tickets"]["MG-310"]
    mg310["STATUS"] = "FENCE_GREEN"
    mg310["NOTE"] = (
        "dedicated fence BUILT + GREEN 7/7 (CONT-76): fixtures/"
        "mg310_clinit_fence (com.probe.mg310, apk 741e3942c2048933) locks "
        "JLS 12.4.1 — active-use init (L1), compile-time-constant read does "
        "NOT init (L2, engine [CLASS_INIT] rows=0), superclass-first order "
        "in app rows AND engine rows (L3/L3b), once-only init (L4), "
        "default-value-before-write 'nullx' (L5); "
        "scripts/cont76_fence_mg310.py; evidence/cont76/mg310_fence.json")
    mg150 = mg["tickets"]["MG-150"]
    mg150["STATUS"] = "FENCE_GREEN_FRONTIER_NAMED"
    mg150["NOTE"] = (
        "dedicated fence BUILT + GREEN 3/3 (CONT-76): fixtures/"
        "mg150_hittest_fence (com.probe.mg150, apk 131ffbad6940c40e) locks "
        "current semantics — translation get/set readbacks 300/200 (GEOM), "
        "tap inside LAYOUT bounds reaches the button (CLICK count=1), tap "
        "inside TRANSLATED-visual bounds only does NOT (documented "
        "deviation; AOSP inverse-maps through the render transform — "
        "delta = named frontier shared with F-NEW-359's rotation record; "
        "hit-test + render consumption must land as ONE coherent law); "
        "scripts/cont76_fence_mg150.py; evidence/cont76/mg150_fence.json")
    mg147 = mg["tickets"]["MG-147"]
    mg147["NOTE"] = (
        "CORRECTED (CONT-76): multi-pointer IDs are NOT implemented — "
        "touch_dispatcher.h documents the SINGLE-pointer model as an "
        "explicit boundary ('single active gesture'); the old note "
        "('implemented in input pipeline') was stale. A multi-pointer "
        "fence requires a runtime feature (gesture model + injection CLI), "
        "not a test — REJECTED as a fence this loop; recorded as a "
        "runtime-feature frontier")
    mg["generated_by"] = "cont76_registry_update.py"
    with open(mgp, "w") as f:
        json.dump(mg, f, indent=1)

    r["summary"] = r.get("summary") or {}
    with open(P1, "w") as f:
        json.dump(r, f, indent=1)

    # mirror to canonical (id-for-id projection)
    c = json.load(open(P2))
    croots = c["roots"] if isinstance(c, dict) and "roots" in c else c
    cmap = {x["id"]: x for x in croots if "id" in x}
    for rid in ("F-NEW-378", "F-NEW-379"):
        if rid in cmap:
            cmap[rid].clear()
            cmap[rid].update(by_id[rid])
    with open(P2, "w") as f:
        json.dump(c, f, indent=1)

    print("registry updated: F-NEW-378 decode-complete+fix-rejected, "
          "F-NEW-379 REJECTED_WITH_REASON, MG-310 FENCE_GREEN, "
          "MG-150 FENCE_GREEN_FRONTIER_NAMED, MG-147 note corrected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
