#!/usr/bin/env python3
"""cont12_f517_registry.py — CONT-12 wave registry update.
1. F-NEW-514: decode addendum + status ROOT-CAUSED-FIXED (the census face's
   actual first killer = the missing Class.getConstructors law, F-NEW-517).
2. F-NEW-517: new ROOT-CAUSED-FIXED row (the generic constructor-reflection
   law). Registry stays id-unique; main == mirror untouched (single file).
"""
import json, sys

REG = "/home/z/my-project/root_registry.json"
doc = json.load(open(REG))
roots = doc if isinstance(doc, list) else doc.get("roots", doc.get("registry"))
assert isinstance(roots, list), "unexpected registry shape"

F514 = """NEXT FACE (loading census, issue #387): WindowInsetsCompat.toWindowInsetsCompat(View,WindowInsets) NPE — Object.getClass on null at the class-identity dispatch (census 16-title Object.getClass umbrella survivors: nononsenseapps.notepad, app.simple.peri, eu.faircode.netguard + cluster). CL-TRACE (peri): the crashing static call arrives with a truncated arg window (a0=i0 only; the WindowInsets arg absent) from ThemeKt.PeristyleTheme after GapComposer.consume(LocalView) — the compose composition-locals chain (LocalView.current) and/or the static invoke arg extraction at that call site. Upstream body: new-instance → insets.getClass() (Impl-table dispatch) → Impl34 ctor; the NULL is the WindowInsets slot."""

F517_ADDENDUM = """
CONT-12 DECODE + FIX (F-NEW-517 landed first — the face's ACTUAL first killer was NOT the WindowInsets arg window): at binary b0620f75, run/cont12/peri pinned the real kill chain end-to-end — SavedStateViewModelFactory_androidKt.findMatchingConstructor reads modelClass.constructors (→ Class.getConstructors) under the Kotlin null-check intrinsic ("getConstructors(...)"): the engine had NO Class.getConstructors/getDeclaredConstructors handler → typed-null → Intrinsics.checkNotNullExpressionValue NPE → ViewModel creation died BOTH at MainComposeActivity.onCreate (onResume → viewModel()) AND inside the first composition (TagsKt.Folder → viewModel() → GapComposer catch-all → "Error was captured in composition.") → 0 content ops → DEFAULT_BACKGROUND_ONLY b5a7a35d. The toWindowInsetsCompat M3-19-CYCLE row (depth=46, lifetime_calls=2) was present but NON-KILLING — a presentation-level event inside the error path of the same composition, not the root. FIX: F-NEW-517 (Class.getConstructors/getDeclaredConstructors OpenJDK law — public-only vs all-declared, full Constructor record contract: class_desc/__reflect_class/__reflect_name/__reflect_ret/__reflect_mods/__reflect_params). VERIFY: peri b5a7a35d (blank, 0 draw ops) → 4b1637d6ba3226ea REAL_APP_CONTENT — the Setup screen renders (Allow Files Access / Ignore Battery Optimization / Allow Media Access / Post Notifications rows with Granted/Not Granted states + Continue), 497 draw ops replayed, ZERO uncaught at the 300s budget (8 F084 wall-clock halts at 90s, face budget-stable ×2 both budgets); anchors 6/6 ×2 byte-identical zero drift (opencalc 63020bc7 / chess a0319686 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176@300s); negatives 19/19; skill selftest 13/13. Cluster residual honestly re-attributed: notepad + netguard do NOT share this root — notepad = F-NEW-515 family (content-provider IAE) + 2 NPE pins; netguard = Service-Context-null f141 family (getPackageInfo/newWakeLock/obtainStyledAttributes on null Context) — both stay with their registered rows."""

def upd():
    hit = 0
    for x in roots:
        if x.get("id") == "F-NEW-514":
            assert x["title"].startswith("NEXT FACE"), "F-NEW-514 shape drift"
            x["title"] = F514 + F517_ADDENDUM
            x["status"] = "ROOT-CAUSED-FIXED"
            x["layer"] = "framework/reflection-constructors"
            hit += 1
        if x.get("id") == "F-NEW-517":
            sys.exit("F-NEW-517 ALREADY EXISTS — id collision")
    assert hit == 1, f"F-NEW-514 not found exactly once (hit={hit})"
    roots.append({
        "id": "F-NEW-517",
        "title": "Class.getConstructors/getDeclaredConstructors had NO engine law → typed-null → Kotlin null-check intrinsic NPE in androidx SavedStateViewModelFactory_androidKt.findMatchingConstructor → ViewModel creation died at onCreate AND inside first composition (peri face: 0 draw ops, DEFAULT_BACKGROUND_ONLY b5a7a35d). CONT-12 decode (run/cont12/peri, binary b0620f75, stack THROWABLE-STACK #1 findMatchingConstructor caller_pc=48, msg=\"getConstructors(...) must not be null\" ×2 paths). FIX (OpenJDK Class.java law): getDeclaredConstructors = ALL declared ctors in DEX table order (private included); getConstructors = PUBLIC only (ACC_PUBLIC 0x1; ctors are never inherited); records mint the FULL Constructor contract the Constructor-side laws already consume (class_desc=referent FIX-M3-012b newInstance shim, __reflect_class F-029 identity, __reflect_name=\"<init>\", __reflect_ret=\"V\", __reflect_mods raw DEX flags → Constructor.getModifiers R-NEW-380, __reflect_params comma-joined → Constructor.getParameterTypes S60); NEVER null (Kotlin intrinsic demand — empty array for synthetic tokens). VERIFY: peri → REAL_APP_CONTENT 4b1637d6 (Setup screen, 497 ops, 0 uncaught @300s), anchors 6/6 ×2 zero drift, negatives 19/19 (probe store regenerated run/gatea/probe_store — the s41 harness path law), selftest 13/13. Serves every Hilt/ViewModel app — the recurring root of the census 16-title Object.getClass umbrella's peri row.",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "framework/reflection-constructors"
    })

upd()
ids = [x["id"] for x in roots]
assert len(ids) == len(set(ids)), "id collision after update"
json.dump(roots, open(REG, "w"), indent=1, ensure_ascii=False)
print(f"registry OK: {len(roots)} roots, F-NEW-514 → ROOT-CAUSED-FIXED, F-NEW-517 registered")
