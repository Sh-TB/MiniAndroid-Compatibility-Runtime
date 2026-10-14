#!/usr/bin/env python3
"""cont26_registry.py — CONT-26 registry update.

Root accounting (directive §15) — dedup checked BEFORE classification:
- F-NEW-278 NEW ROOT-CAUSED-FIXED: multi-DEX class-annotation closure
  (F-087 index was DEX-0-only; third member of the EXP-095/S102 family).
- F-NEW-279 NEW ROOT-CAUSED-FIXED: Throwable suppressed-exception law
  (getSuppressed must never answer null — OpenJDK Java 7+ law).
- F-NEW-280 NEW ROOT-CAUSED-FIXED: exact-descriptor overload authority is
  a hierarchy law (S108 ROOT-019 cross-class extension, blocker-safe).
- F-NEW-277 (CLASSIFIED P0): evidence extended — A1 state re-verified at
  HEAD (16ms strand runs, quiescence EMPTY queue); oracle instrument
  rebuilt; invalidation-chain blockers at the oracle level fixed en route.
No root was classified before dedup; no duplicates found for any of the
three new roots (checked 'annotation', 'getSuppressed', 'Navigator.Name',
'overload', 'descriptor' across all 586 existing rows + titles + causes).
"""
import json

PATH = "/home/z/my-project/root_registry.json"
r = json.load(open(PATH))
roots = r["roots"]
by_id = {row.get("id"): row for row in roots}
assert "F-NEW-278" not in by_id, "dedup: F-NEW-278 exists"
assert "F-NEW-279" not in by_id, "dedup: F-NEW-279 exists"
assert "F-NEW-280" not in by_id, "dedup: F-NEW-280 exists"

roots.append({
    "id": "F-NEW-278",
    "status": "ROOT-CAUSED-FIXED",
    "title": "MULTI-DEX CLASS-ANNOTATION CLOSURE (F-087 index was DEX-0-only): "
             "Class.getAnnotation answered NULL for every class defined in classes2.dex+ "
             "even when a RUNTIME annotation (visibility=1) was present in the DEX — "
             "navigation-compose NavigatorProvider.getNameForNavigator("
             "Class.getAnnotation(@Navigator.Name)) threw IAE 'No @Navigator.Name "
             "annotation found for NavGraphNavigator' and rememberNavController/NavHost "
             "never composed (CONT-12 oracle com.probe.oracle12 face).",
    "priority": "P0",
    "layer": "dex/class-metadata + reflection",
    "root_cause": "PROVEN AT RUNTIME+DEX (2026-10-09, oracle APK 8,233,173 bytes, "
                  "binary e980887e39aee977): dalvik_engine.cpp populates class_annotations_ "
                  "only in the DEX-0 ingestion loop; inject_secondary_dex_classes() merged "
                  "ClassInfo, the superclass map (EXP-095) and the interface map (S102) but "
                  "NOT class_annotations_. scripts/cont26_dex_ann_scan.py (DEX "
                  "annotations_directory_item walk) proves the annotation IS in the binary: "
                  "Landroidx/navigation/NavGraphNavigator; → Navigator$Name vis=1 "
                  "value='navigation'; ComposeNavigator value='composable'. Upstream law: "
                  "ART copies runtime-visible annotations into the Class object at load time "
                  "regardless of which classesN.dex defines the class (libcore Class.java). "
                  "The engine's full F-087 proxy + accessor chain (F-087c element dispatch) "
                  "was already correct — only the index was DEX-0-only.",
    "fix": "inject_secondary_dex_classes(): third closure loop after the S102 interface "
           "block — merge cls.class_annotations into class_annotations_ for secondary-DEX "
           "classes (same dedup law: skip when the class already has an entry). Diagnostic "
           "[F087-MD-ANN] (always-on, one line). No app/package/R8-name knowledge.",
    "evidence": "RUNTIME oracle run at e980887e39aee977: '[F087] getAnnotation queried "
                "class=Landroidx/navigation/NavGraphNavigator; annotation=Landroidx/"
                "navigation/Navigator$Name; indexed=NO' → IAE → APP BOUNDARY. Post-fix at "
                "59a6b54897846c7a: '[F087-MD-ANN] class-annotation index extended by 361 "
                "secondary-DEX classes (total 698)'; the navigator IAE is GONE; the oracle "
                "advances to NavHost ViewModelStoreOwner face. Regression at final binary "
                "1ff06737f7b12ad4: 24/24 anchor+control runs x3 byte-identical, probe "
                "battery 0 unexpected FAIL. Tools: scripts/cont26_dex_ann_scan.py. "
                "Evidence: evidence/cont26/COMPOSE_INVALIDATION_ROOT.md.",
    "verified_current": "fix verified at binary 1ff06737f7b12ad4 (CONT-26 final): oracle "
                        "navigation chain passes @Navigator.Name lookup; full regression "
                        "green; dooz anchor d602648e8e401895 x3 byte-identical.",
})

roots.append({
    "id": "F-NEW-279",
    "status": "ROOT-CAUSED-FIXED",
    "title": "THROWABLE SUPPRESSED-EXCEPTION LAW GAP (OpenJDK Java 7+): getSuppressed() "
             "had NO handler → generic stub answered NULL → Kotlin's "
             "Intrinsics.checkNotNullExpressionValue threw NPE 'getSuppressed(...) must "
             "not be null' INSIDE compose's exception-attach path, converting every "
             "caught-then-annotated compose exception into an uncaught NPE "
             "(GapComposer.doCompose catch-all → tryAttachComposeStackTrace → "
             "JDK7PlatformImplementations.getSuppressed).",
    "priority": "P1",
    "layer": "runtime/throwable-family",
    "root_cause": "PROVEN AT RUNTIME (2026-10-09, oracle at e980887e39aee977): the engine "
                  "had zero getSuppressed/addSuppressed handling (grep audit) — the UC-CM-001 "
                  "typed stub answered null for the ()[Ljava/lang/Throwable; proto; kotlin "
                  "jvm Intrinsics asserted non-null per the OpenJDK law (Throwable.java: "
                  "EMPTY_THROWABLE_ARRAY when none — NEVER null) and the NPE propagated from "
                  "inside the exception handler itself → APP BOUNDARY. Every Kotlin "
                  "exception-inspection path through ExceptionsKt.getSuppressedExceptions "
                  "shares the family.",
    "fix": "Throwable-family law in dalvik_engine.cpp: getSuppressed() returns a heap "
           "'[Ljava/lang/Throwable;' array — the recorded '__suppressed__' list when "
           "present, else a zero-length array (never null); addSuppressed(t) appends "
           "(self-suppression ignored, upstream law). Array-object pattern mirrors the "
           "R-NEW-464 getParameterTypes law.",
    "evidence": "RUNTIME oracle run at e980887e39aee977: THROWABLE-MSG NPE "
                "'getSuppressed(...) must not be null' caller=Intrinsics at "
                "JDK7PlatformImplementations.getSuppressed ← ComposeStackTraceKt."
                "tryAttachComposeStackTrace ← GapComposer.doCompose catch-all. Post-fix "
                "(59a6b548): the face is GONE. Evidence: evidence/cont26/"
                "COMPOSE_INVALIDATION_ROOT.md.",
    "verified_current": "fix verified at binary 1ff06737f7b12ad4: full regression green "
                        "(24/24 byte-identical + probe battery).",
})

roots.append({
    "id": "F-NEW-280",
    "status": "ROOT-CAUSED-FIXED",
    "title": "EXACT-DESCRIPTOR OVERLOAD AUTHORITY IS A HIERARCHY LAW (S108 ROOT-019 "
             "cross-class extension): invoke resolution accepted a same-name "
             "different-descriptor method from the runtime class instead of continuing "
             "into the superclass chain — AppCompatActivity.onCreate's "
             "delegate.onCreate(Landroid/os/Bundle;)V resolved to the WRONG overload "
             "ac.a(Landroid/view/Window$Callback;) (wrapWindowCallback), the null "
             "saved-state Bundle flowed into the callback slot, and "
             "WindowCallbackWrapper.<init> threw IAE 'Window callback may not be null' "
             "at the FIRST MainActivity.onCreate invoke → white screen "
             "(com.simplemobiletools.calculator face).",
    "priority": "P0",
    "layer": "dex/invoke-resolution",
    "root_cause": "PROVEN AT RUNTIME (2026-10-09, simplecalc vc8 sha "
                  "68da25fd9fdf54b4, binary e980887e39aee977): MINIANDROID_ARG_TRACE "
                  "shows ac.a invoked twice — first as (Callback)Callback with the live "
                  "activity obj#12 (correct wrap), then the u.onCreate call site "
                  "resolve of (Landroid/os/Bundle;)V mis-dispatched into the same-name "
                  "(Callback)Callback overload with p2=NULL → IAE at "
                  "Landroid/support/v7/view/n;.<init> pc=9 → APP BOUNDARY. Disassembly "
                  "(scripts/cont26_dex_method_disasm.py): class ac declares ONLY "
                  "a(Callback); the a(Bundle)V override lives in superclass aa. The "
                  "engine's own S108 ROOT-019 law already stated the correct semantics "
                  "but the strict skip was default-OFF (recorded bogus-descriptor "
                  "blocker: wanted descriptors that exist NOWHERE — hard-filtering "
                  "selected nothing and ctors never ran, v6.q→u.<init> family). "
                  "Upstream law: JVMS 5.4.5 / dalvik invoke resolution selects by "
                  "(name, proto) and walks the hierarchy — never falls to a "
                  "differently-shaped same-name method.",
    "fix": "Blocker-safe middle path in try_recursive_invoke(): when the call site "
           "carries a concrete descriptor and the runtime class has NO exact (name, "
           "descriptor, non-empty-code) match, run the F-074 super-walk for the EXACT "
           "match FIRST (try_recursive_invoke_on_super with the descriptor); only when "
           "no ancestor declares it either does the legacy lenient selection run "
           "unchanged. The recorded bogus-descriptor family keeps byte-identical "
           "behavior (bogus descriptors match locally nowhere AND up-chain nowhere). "
           "Diagnostic [F280-SUPERWALK] env-gated (MINIANDROID_F280_TRACE).",
    "evidence": "RUNTIME simplecalc at e980887e39aee977: IAE 'Window callback may not "
                "be null' x2 chains (first wrap with obj#12 OK, second mis-resolved "
                "wrap with null kills onCreate). Post-fix at 1ff06737f7b12ad4: the IAE "
                "is GONE (0 log occurrences); Simple Calculator advances through full "
                "AppCompat delegate startup, theme resolution, setContentView, real "
                "Toolbar measure/layout (Toolbar.onMeasure/onLayout dispatch); NEXT "
                "divergence = Toolbar constructor context/int[] fields never "
                "initialized ([V6-CTX-FALLBACK] ctor-context MISSING) → aput-null NPE "
                "in Toolbar.onMeasure pc=152 → PARTIAL (divergence moved, honestly "
                "reported). Regression: 24/24 byte-identical + probe battery green at "
                "1ff06737f7b12ad4. Evidence: evidence/cont26/"
                "SIMPLE_CALCULATOR_ANDROIDX_ROOT.md.",
    "verified_current": "fix verified at binary 1ff06737f7b12ad4 (CONT-26 final): "
                        "cross-target proof on a SECOND independent APK family — the "
                        "full anchor+control suite x3 byte-identical proves the "
                        "hierarchy walk is neutral where the law was never reachable.",
})

# F-NEW-277 evidence extension
row277 = by_id["F-NEW-277"]
ev = row277.get("evidence")
ev = ev if isinstance(ev, str) else json.dumps(ev, ensure_ascii=False)
row277["evidence"] = ev + (
    " CONT-26 pointer 2026-10-09: A1 state re-verified live at HEAD binary "
    "e980887e39aee977 — [F277-POLL] fires once (advance to virtual_ms=16), the "
    "16ms View.post strand (Runnable 2670, Ld4;) now RUNS (dequeued at "
    "ready_at=16ms), pump quiesces at tick=5 with an EMPTY queue; "
    "recomposition #2 still never starts. The CONT-12 un-renamed real-Compose "
    "oracle (com.probe.oracle12) was REBUILT from surviving artifacts (AARs + "
    "rclasses + dexes; size-exact 8,233,173 bytes vs the recorded build) as the "
    "name-level instrument; two generic oracle-path roots (F-NEW-278 "
    "multi-DEX annotations, F-NEW-279 getSuppressed) fixed en route to the "
    "invalidation chain. Evidence: evidence/cont26/COMPOSE_INVALIDATION_ROOT.md.")

r["status_counts"] = r.get("status_counts", {})
json.dump(r, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry updated: %d roots" % len(roots))
