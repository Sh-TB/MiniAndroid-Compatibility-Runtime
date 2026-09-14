#!/usr/bin/env python3
"""S39: register R-NEW-337 — dooz v23 first-measure Compose composition death
(JobSupport.makeCompletingOnce sees already-completing job on FIRST composition)."""
import json, sys

REG = "/home/z/my-project/root_registry.json"
ENTRY = {
    "id": "R-NEW-337",
    "status": "OBSERVED-FAIL",
    "priority": "P1",
    "fg": True,
    "evidence": (
        "S39 OBSERVED (dooz v23 newer variant io.github.yamin8000.dooz_23.apk, "
        "run /tmp/s38_runs/dooz23_vtree2, stderr 242k lines): ComposeView (Lho; view=624) "
        "first onMeasure -> ensureCompositionCreated chain dies on real kotlinx.coroutines "
        "bytecode: stack #10 Lr;.onMeasure -> #9 Lr;.g -> #8 Lr;.j -> #7 Lr;.k -> #5/#6 "
        "Lxo0;.a/Lyo0;.a -> #4 Lh62;.e -> #3 Lxz1;.I -> #2/#1 Ls;.h0/.g -> #0 Loj0;.T "
        "(JobSupport.makeCompletingOnce) pc=49 THROWS IllegalStateException "
        "\"Job Lkp1;@828 is already complete or completing, but is being completed with "
        "Lwl;@856\" (4 occurrences in log). Lkp1;.T/.M/.d0 all F074-super-dispatch to "
        "ancestor Loj0; (receiver o828 preserved): T=makeCompletingOnce, M=state read, "
        "d0=tryMakeCompleting(state,proposedUpdate) -> returned already-completing sentinel "
        "-> real code threw. Catch-all in Lr;.g catches then its own catch body rethrows; "
        "uncaught at MainActivity.onCreate invoke_pc=317 -> APP BOUNDARY unwind (status "
        "downgraded). Layout continues (Lho; rect 1080x1920 laid out, LIFEWIN-CLOSE "
        "dispatched) but C013-ONDRAW dispatched=NO ops=0 -> inline placeholder -> EMPTY "
        "GREY SCREEN (screenshot: only corner text 'ho'). KEY FACT: this is the FIRST "
        "composition creation (first measure pass, no earlier measure in log) — the job "
        "o828 was 'already complete or completing' before any prior composition attempt, "
        "so its JobSupport state was completed/corrupted between creation (onCreate) and "
        "first measure. Earlier SGET trace: Loj0;.e read as 0 by method=P and <init>."
    ),
    "root_cause": "",
    "fix": "",
    "severity": "high",
    "commit": "S39-NEW",
    "next": (
        "(1) Field-write trace on Loj0; instance o828 between object creation and throw: "
        "who wrote the state field (Loj0;.e/_state slot) and with what value — expect "
        "either a premature makeCompleting/complete call from engine re-dispatch or "
        "dual-store corruption (R-NEW-335 family: state read from wrong store). "
        "(2) Identify Lkp1;/Lwl;/Ls; via APK mapping (kp1 may be Recomposer's "
        "LazyStandaloneCoroutine; Ls;.g/h0 = startCoroutineCancellable family). "
        "(3) Check whether engine ran the coroutine start path TWICE (duplicate "
        "Ls;.g entries for same receiver in api_trace/lifecycle_trace). "
        "(4) Fix-law candidates: honor JobSupport state machine exactly — if "
        "tryMakeCompleting returns already-completing sentinel on a job the engine "
        "itself completed, the completion was duplicated engine-side; trace and remove "
        "the duplicate dispatch at its source (preferred) vs masking sentinel in T "
        "(rejected: hides real state bug)."
    ),
}

reg = json.load(open(REG))
roots = reg["roots"]
assert not any(r.get("id") == "R-NEW-337" for r in roots), "R-NEW-337 already registered"
roots.append(ENTRY)
json.dump(reg, open(REG, "w"), ensure_ascii=False, indent=1)
print(f"R-NEW-337 registered; total roots = {len(roots)}")
