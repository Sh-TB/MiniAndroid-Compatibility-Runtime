#!/usr/bin/env python3
"""CONT-87 registry update: F-NEW-395 re-grade + fix landing.

Honest two-part re-grade driven by fixture + real-APK decode:
1. The REGISTERED handler-match claim ("deferred raise misses the clinit
   frame's own catch-all") is DISPROVEN by evidence:
   - decode (scripts/cont87_decode_luu.py): Luu;.<clinit> try covers
     code-units 7..12 (the getMethod probe) — the forName invoke sits at
     unit 2, OUTSIDE the try; the engine's 'uncaught' verdict at pc=2 was
     correct DEX semantics, not a handler-search gap.
   - fixture com.probe.clinit1: in-frame catch-alls DO dispatch for both
     raise origins (R350-FORNAME CNFE @pc=9 -> handler @0x14; ARITH-LIT8
     @pc=9 -> handler @0x15).
2. The registered honesty defect ("clinit-result-OK-despite-throw") is
   CONFIRMED and FIXED (fixture fails pre-fix, passes post-fix):
   - execute_method_internal finalization: an unwind no longer reports
     COMPLETED_SUCCESS (marker COMPLETED_PARTIAL + halt_reason="unwind
     <type>"; SUCCESS clears stale markers).
   - ensure_class_initialized clinit call site reads the marker and routes
     the class into the registered F-NEW-215 erroneous state.
   - six active-use sites (sget/sget-object/sput/sput-object/new-instance/
     forName) skip the double-raise when THIS use triggered the failing
     clinit (clinit_exc_already_in_flight) — the original exception
     delivers at its covering handler exactly as before; later uses keep
     the F-NEW-215 NCDFE law.
"""
import json

REG = "canonical/root_cause_registry.json"
MIR = "root_registry.json"

d = json.load(open(REG))
rows = d["roots"]

def upsert(rid, patch):
    for r in rows:
        if r.get("id") == rid:
            r.update(patch)
            return r
    r = {"id": rid}
    r.update(patch)
    rows.append(r)
    return r

upsert("F-NEW-395", {
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P2",
    "title": "Class-init honesty law: an exception unwinding OUT of <clinit> now marks the class erroneous (registered handler-match claim disproven; registered honesty defect confirmed and fixed)",
    "layer": "dex/exceptions",
    "root_cause": (
        "TWO claims were registered; evidence split them. (a) DISPROVEN — "
        "'deferred raise misses the clinit frame's own catch-all': decode of "
        "org.andstatus.game2048_47 (scripts/cont87_decode_luu.py) shows "
        "Luu;.<clinit>'s try covers code-units 7..12 (the "
        "getMethod(\"onSpinWait\") probe) while the forName invoke sits at "
        "unit 2 — OUTSIDE the try — so the engine's 'uncaught (deferred "
        "frame unwind + propagate)' verdict at pc=2 was correct DEX "
        "semantics; fixture com.probe.clinit1 further proves in-frame "
        "catch-alls dispatch for BOTH raise origins (CNFE @pc=9 -> handler "
        "@0x14; ARITH @pc=9 -> handler @0x15). (b) CONFIRMED — the honesty "
        "state machine: halted_on_return_ is set by BOTH normal return and "
        "exception unwind, so execute_method_internal reported "
        "COMPLETED_SUCCESS for an unwound clinit; ensure_class_initialized "
        "then recorded result=OK, the class stayed poison-marked "
        "INITIALIZED, F-NEW-215 never armed, and the raw exception "
        "'teleported' to a LATER invoke site (AndStatus2048's CNFE surfaced "
        "inside MyMainActivity.onCreate at a confusing pc)."
    ),
    "fix": (
        "Three generic sites, zero app/package conditionals: (1) "
        "execute_method_internal finalization writes an unambiguous marker "
        "when the frame exited via unwind (COMPLETED_PARTIAL + "
        "halt_reason=\"unwind <type>\"); COMPLETED_SUCCESS clears stale "
        "markers so a nested run's caught exception cannot poison the "
        "caller. (2) The <clinit> call site in ensure_class_initialized "
        "reads the marker and routes the class through the registered "
        "F-NEW-215 erroneous path ([CLASS_INIT] FAILED + "
        "failed_clinit_classes_ evidence='unwind <type>'). (3) The six "
        "active-use sites (sget/sget-object/sput/sput-object/new-instance/"
        "forName) guard their NCDFE re-raise with "
        "clinit_exc_already_in_flight() — the TRIGGERING use delivers the "
        "clinit's own exception at its covering handler (pre-fix "
        "app-visible behavior preserved byte-for-byte; EXC-PROPAGATE "
        "delivery unchanged); LATER uses keep the F-NEW-215 NCDFE law."
    ),
    "evidence": (
        "Fixture-first A/B on com.probe.clinit1 (run/cont87/): pre-fix "
        "(d22b36be55764348) clinit_pre.stderr shows [CLASS_INIT] result=OK "
        "for ClinitThrow (uncaught deferred ARITH) and UT2 re-running the "
        "clinit (s=42 readable, erroneous law dead); post-fix "
        "(caa24290aad77ca9) clinit_post3.stderr shows [F-NEW-395] "
        "CLINIT-UNWIND -> [CLASS_INIT] result=FAILED -> [F-NEW-215] "
        "CLINIT-FAILED evidence='unwind Ljava/lang/ArithmeticException;' -> "
        "first use delivers the original AE via EXC-PROPAGATE at its "
        "covering handler (row C87-UT main-caught:AE, IDENTICAL to pre-fix) "
        "-> second use NCDFE (row C87-UT2 main-caught:NoClassDefFoundError, "
        "was clinit-ok s=42). Controls unchanged: C87-CC caught:CNFE + "
        "C87-AC caught:AE (in-frame catch law intact). Real-APK decode: "
        "scripts/cont87_decode_luu.py (try start=7 count=6, forName at "
        "unit 2). Intermediate honest null: first fix attempt (consuming "
        "the in-flight unwind at the clinit call site) double-raised — "
        "NCDFE re-raise at the ADVANCED pc escaped the app's covering try "
        "and killed the boot (clinit_post2.stderr) — superseded by the "
        "in-flight guard."
    ),
    "test": (
        "Full battery at caa24290aad77ca9, zero drift: wall 12/12 "
        "(cont70_wall_sweep), goldens 4/4 (user_golden_gate), negatives "
        "19/19 (s41_gatea_negative + gate_a_probe rebuilt 27011c4204d7598d), "
        "reinstall 8/8 (s41_gatea_reinstall), MG-310 7/7, MG-150 3/3, "
        "c72priv 12-OK/0-BAD, selftests 13/13, F-NEW-376 fault injection "
        "70/70, c74esc fence 5/5 OK, clock1 4/4 PASS, swipe1 law rows "
        "correct (e2 residual named), as2048_47 boot 0 uncaught (face "
        "default-splash class unchanged)."
    ),
    "named_residuals": [
        "JVMS 5.5 wraps a non-Error clinit throw in "
        "ExceptionInInitializerError on FIRST use; this engine's registered "
        "active-use answer delivers the original exception at the covering "
        "handler (triggering use) and NCDFE (later uses). EIIE modeling "
        "absent engine-wide — named, not hidden.",
        "The F-NEW-215 re-raise searches the try table at the ADVANCED pc "
        "(opcode end); moot at the triggering use (guard skips it) but a "
        "try ending exactly at the use instruction would miss the handler "
        "— micro-residual, recorded.",
        "The registered handler-match claim is retracted: the real-APK try "
        "region genuinely did not cover the forName call; on-device the "
        "app never depended on it (forName of a shipped framework class "
        "never throws — the F-NEW-394 bridge already restored that law).",
    ],
})

# registry counter discipline: F-NEW-395 already existed — no inflation.
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)

# mirror to the root-level registry
import shutil
shutil.copy(REG, MIR)

print("roots:", len(rows))
for r in rows:
    if r.get("id") == "F-NEW-395":
        print("F-NEW-395 ->", r["status"])
