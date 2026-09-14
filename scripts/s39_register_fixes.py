#!/usr/bin/env python3
"""S39: update R-NEW-337 (root-caused+fixed), register R-NEW-338/339 (fixed),
R-NEW-340 (next frontier: content composition pump)."""
import json

REG = "/home/z/my-project/root_registry.json"
reg = json.load(open(REG))
roots = reg["roots"]
by_id = {r["id"]: r for r in roots}

# ---- R-NEW-337: ROOT-CAUSED + FIXED ----
r = by_id["R-NEW-337"]
r["status"] = "ROOT-CAUSED-FIXED"
r["root_cause"] = (
    "atomicfu-transformed kotlinx.coroutines runs ALL volatile state via "
    "sun.misc.Unsafe reflection (theUnsafe.objectFieldOffset(Class."
    "getDeclaredField(name)) -> getObjectVolatile/putObjectVolatile/"
    "compareAndSwapObject with the offset stored in static long fields, e.g. "
    "Loj0;.e/.f). The engine had NO shadow for getDeclaredField, "
    "java.lang.reflect.Field, or sun.misc.Unsafe — every call REC-MISS -> "
    "offsets 0, reads null. JobSupport (Loj0;) then read its own Active state "
    "(Lh20;=Empty{isActive=true}, heap-proven obj#505 fields=.e=1) as obj#0 "
    "null -> d0 pc=0 `state !is Incomplete` (instance-of Lmf0;) wrongly TRUE "
    "-> COMPLETING_ALREADY_COMPLETING sentinel (Lqi0;.y) -> "
    "makeCompletingOnce(T) threw ISE 'already complete or completing' on the "
    "FIRST composition (probe evidence: INSTANCEOF-DIAG obj=obj#0 class=-)."
)
r["fix"] = (
    "Implemented the full atomicfu-via-Unsafe contract in try_shadow_dispatch: "
    "Class.getDeclaredField/getDeclaredFields -> heap Field objects "
    "(declaring_class/field_name/field_type from dex_report_); "
    "Field.getName/getType/getDeclaringClass/getModifiers/setAccessible/get/"
    "set; Modifier.isStatic; Class.isAssignableFrom; Unsafe singleton "
    "(theUnsafe via Field.get) + objectFieldOffset (deterministic 8-aligned "
    "registry (class,field)<->offset), getObjectVolatile/getObject/"
    "putObjectVolatile/putOrderedObject/putObject (heap-backed via offset "
    "reverse map), compareAndSwapObject/Int/Long (heap CAS by object "
    "identity), getIntVolatile/putIntVolatile/getLongVolatile/putLongVolatile "
    "variants, arrayBaseOffset/arrayIndexScale. Post-fix: 30 offsets "
    "registered (Loj0;._state$volatile->40, _parentHandle$volatile->48, ...), "
    "ZERO 'already complete' ISE, dooz first composition completes. "
    "Regression: hello_smoke/hello_widgets byte-identical renders."
)

# ---- R-NEW-338 ----
r338 = {
    "id": "R-NEW-338",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "fg": True,
    "evidence": (
        "S39 OBSERVED (dooz23 run dooz23_r337fix stderr:242045): after "
        "R-NEW-337 fix, kotlinx.coroutines stack-trace sanitizer "
        "Lqi0;.Q(RuntimeException,String) threw NPE 'null array in "
        "Arrays.copyOfRange' — its getStackTrace() call dispatched through "
        "bridge_to_api with the RUNTIME exception class (R8-obfuscated, e.g. "
        "Lbd1;/Lwr;) and the M3-19 guard demanded class_name to contain "
        "Throwable/Exception/Error -> silently unmatched -> null trace -> "
        "copyOfRange(null,...) -> f060-copy-null synthetic NPE."
    ),
    "root_cause": (
        "Throwable.getStackTrace guard matched DECLARED-class name substrings "
        "instead of dispatching the INHERITED Throwable contract for any "
        "receiver class; R8 obfuscation hides Throwable ancestry in class "
        "names."
    ),
    "fix": (
        "Guard widened: getStackTrace/fillInStackTrace/getStackTraceDepth/"
        "setStackTrace dispatch for ANY receiver class (Thread excluded, "
        "keeps its own law). setStackTrace stores the sanitized array on the "
        "exception ('stack_trace' heap field); getStackTrace returns the "
        "stored sanitized array when present (round-trip), else builds real "
        "frames. Post-fix: zero copyOfRange NPEs in dooz23."
    ),
    "severity": "high",
    "commit": "S39-FIX",
}
if "R-NEW-338" not in by_id:
    roots.append(r338)
else:
    by_id["R-NEW-338"].update(r338)

# ---- R-NEW-339 ----
r339 = {
    "id": "R-NEW-339",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "fg": True,
    "evidence": (
        "S39 OBSERVED (dooz23 runs r338fix/r339c/r339d): AndroidComposeView "
        "(Lt4; extends ViewGroup) ctor threw ISE 'Required value was null.' "
        "at engine pc=415 (caller-PC forensics: THROWABLE-STACK-PC "
        "Lc91;.f caller_pc=415) — the Kotlin checkNotNull of the autofill "
        "chain: Lob;.b(View) -> View.getAutofillId() returned NULL (no "
        "ViewShadow handler) -> Lwd;.a (AutofillId holder) null -> Ld1;.e "
        "cast null -> branch to throw. Companion: the SECOND "
        "context.getSystemService(AutofillManager::class.java) in the same "
        "ctor needed dual-layer coverage (bridge_to_api + "
        "try_shadow_dispatch)."
    ),
    "root_cause": (
        "(a) View.getAutofillId unimplemented (AOSP: every view has a "
        "non-null AutofillId from its ctor on API 26+); (b) "
        "Context.getSystemService(Class) resolved only in the bridge layer — "
        "dispatch paths that enter via try_shadow_dispatch answered null."
    ),
    "fix": (
        "ViewShadow.getAutofillId: lazily creates ONE memoized AutofillId "
        "heap object per view (ViewNode.autofill_id_obj) with view_id field; "
        "same object every call. getSystemService(Class/Service-string) "
        "registry mirrored into try_shadow_dispatch ([R339-SVC] lines). "
        "Post-fix: zero ISE; view tree becomes REAL (C013-LEAFCHK: "
        "ComposeView Lho; children=1 = AndroidComposeView Lt4; attached; "
        "placeholder no longer drawn)."
    ),
    "severity": "high",
    "commit": "S39-FIX",
    "next": (
        "Frontier advanced: composition machinery survives; content nodes "
        "not yet composed (Lt4; children=0, framebuffer white = real draw "
        "path pending). Next probe: Recomposer frame pump — does the "
        "Choreographer frame callback / MonotonicFrameClock withFrameNanos "
        "chain dispatch so composition produces content nodes? (R-NEW-340 "
        "candidate.)"
    ),
}
if "R-NEW-339" not in by_id:
    roots.append(r339)
else:
    by_id["R-NEW-339"].update(r339)

json.dump(reg, open(REG, "w"), ensure_ascii=False, indent=1)
print(f"registry updated; total roots = {len(roots)}")
print("R-NEW-337 -> ROOT-CAUSED-FIXED")
print("R-NEW-338 -> ROOT-CAUSED-FIXED (registered)")
print("R-NEW-339 -> ROOT-CAUSED-FIXED (registered)")
