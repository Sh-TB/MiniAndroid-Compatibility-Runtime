#!/usr/bin/env python3
"""cont54_registry.py — CONT-54 registry update (636 -> 637).

F-NEW-326: ROOT-CAUSED-FIXED — the framework-boundary static resolution
law + the AOSP ViewGroup.getChildMeasureSpec spec law. Five support-lib
classes (DrawerLayout m@5133, NestedScrollView m@5251, ActionMenuView
m@7364, Toolbar m@8216, ar m@8737) carry method_ids naming THEIR OWN
class as the owner of getChildMeasureSpec(III)I while NO class in the
DEX declares it (DrawerLayout class_data jumps m@5124 -> m@5143); ART
resolves every such invoke through the super chain onto the framework
ViewGroup.getChildMeasureSpec. The engine's DEX-side resolver stopped at
the framework boundary and the bridge keyed on the app class answered
the STUBBED typed default (0) — the CONT-53 "-1/0" face; the drawer
child spec chain broke (spec 0x0). Also refreshes the F-NEW-309
next_wave frontier: the spec-0 face is RESOLVED (NavigationView now
receives wspec=0x80000390/hspec=0x40000780 and writes back 0x1920); the
NEW frontier is the menu-content render pipeline (NavigationMenuView's
DEX onMeasure dispatch / APP_PIXELS stage).
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-326" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 636, f"expected 636 roots, got {len(roots)}"

for r in roots:
    if r["id"] == "F-NEW-309":
        r["next_wave"] = (
            "CONT-54 UPDATE (binary 94d626170bc86331, HEAD d5bbf5d4+): the "
            "CONT-53 recorded next frontier (the v4 getChildMeasureSpec "
            "(III)I body answering -1/0) is ROOT-CAUSED and FIXED as "
            "F-NEW-326 — the method is UNDECLARED in the DEX (5 support-lib "
            "child-class-owned method_ids; DrawerLayout class_data gap "
            "m@5124->m@5143), ART resolves it onto the framework "
            "ViewGroup.getChildMeasureSpec, and the engine now implements "
            "both the resolution (framework-boundary retry after a STUBBED "
            "bridge dispatch) and the law (the exact AOSP spec-derivation "
            "switch). Solitaire POST: [R347-MEASURE] view=298 "
            "NavigationView dex_onmeasure=YES wspec=0x80000390 "
            "(AT_MOST|912) hspec=0x40000780 (EXACTLY|1920) -> 0x1920 — the "
            "spec-0 face is DEAD; NavigationMenuView (view=322) exists, "
            "addView'd (NavigationView.<init> pc=194) and attaches "
            "(UC009-ATTACH view=322). Screenshot face ba50a4d28ea62fe7 "
            "UNCHANGED x3 (honest). NEW frontier = the menu-content render "
            "pipeline: NavigationMenuView's own DEX onMeasure dispatch "
            "(DEFAULT-MEASURE view=322 overrides_onMeasure=1 flag=0 — the "
            "override exists but the DEX body has not been observed "
            "executing) and the RecyclerView/menu-adapter chain behind it "
            "(the APP_PIXELS stage)."
        )
        r["evidence"] = ("evidence/cont49/CONT49_RESULT.md; evidence/cont50/CONT50_RESULT.md; "
                         "evidence/cont51/CONT51_RESULT.md; evidence/cont52/CONT52_RESULT.md; "
                         "evidence/cont54/CONT54_RESULT.md")

roots.append({
    "id": "F-NEW-326",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "The framework-boundary static resolution law + the AOSP ViewGroup.getChildMeasureSpec spec law. Five support-lib classes (DrawerLayout m@5133, NestedScrollView m@5251, ActionMenuView m@7364, Toolbar m@8216, ar m@8737 — solitaire classes.dex, byte-level) carry method_ids naming THEIR OWN class as the owner of getChildMeasureSpec(III)I while NO class in the DEX declares it (DrawerLayout's class_data jumps m@5124 -> m@5143 — the id is undeclared); on a real device every such invoke resolves through the superclass chain onto the framework ViewGroup.getChildMeasureSpec. The engine's DEX-side resolver (local + F-074/F-280 super-walk) stopped at the framework boundary (class_info_index_ holds only APK classes) and the bridge keyed on the APP class identity answered the STUBBED typed default — the CONT-53 recorded '-1/0' face — so the DrawerLayout child-spec chain broke and the drawer measured 0x0.",
    "root_cause": "Two missing layers, both class-agnostic: (1) RESOLUTION — execute_invoke_static dispatched the bridge under the named (app-bundled) class only; ART's invoke-static resolution walks the FULL superclass chain past the DEX boundary into the framework to the class that actually declares the method (Dalvik spec: the method must be declared in the referenced class or one of its superclasses). (2) THE LAW — the engine had NO ViewGroup.getChildMeasureSpec implementation anywhere (only the S109 ROOT-042 container-side approximation without padding/UNSPECIFIED). FIX (minimal, generic, ART-faithful): (a) after the first bridge dispatch ends STUBBED (the typed-default tail — side-effect-free, so a retry cannot double-fire any handler), walk the superclass chain past the DEX boundary (nearest framework ancestor first, bounded 16 hops) and accept the first IMPLEMENTED framework law, else keep the original STUBBED answer byte-identically; (b) the exact AOSP ViewGroup.getChildMeasureSpec switch (EXACTLY/AT_MOST/UNSPECIFIED parent x dim>=0/MATCH(-1)/WRAP(-2), size=max(0,specSize-padding), in-place mode representation per the F-096b law) at a framework-exact guard. NO app knowledge, NO R8-name special-casing.",
    "next_wave": "Probe fnew326 (real aapt2/ECJ/D8; TWO variants from ONE source tree): fnew326_probe.apk 36c7cb1a183b006a (direct ViewGroup owner) + fnew326b_probe.apk eee1a164d1a74b60 (the method_id class_idx byte-rewritten to MyBox — the exact R8 artifact shape). PRE x3 on the unpatched binary ff261b1bc2940bc2: 12 FAIL / 1 PASS (N1 negative control; every row got=0x0 — the STUBBED default) on BOTH variants. POST x3 on 94d626170bc86331: 13/0 x3 on BOTH variants (the full AOSP matrix P1-P10 + N1 + the subclass-owner faces P11/P12 through the re-dispatch chain LinearLayout-STUBBED -> ViewGroup-law). Solitaire runtime: [F-NEW-326] static re-dispatch Toolbar.getChildMeasureSpec as ViewGroup fires; the law answers real specs (spec=0x40000438 pad=0 dim=-2 -> 0x80000438; spec=0x40000780 dim=-1 -> 0x40000780); [R347-MEASURE] view=298 NavigationView wspec=0x80000390 hspec=0x40000780 -> 0x1920 (the CONT-52/53 spec-0 face DEAD). Zero-drift gate on 94d626170bc86331: 15 canonical anchors/controls x3 byte-identical (dooz 31ddd4d5 incl.; BMI b52252c2, alex c8d69f81, notes eb5ebd55, sol ba50a4d2 held); probe battery == records (fnew309 8/0, fnew320 7/0, fnew322 5/0, fnew323 6/0, fnew324 3/0, fnew325 4/0); tananaev 294a68bd / simplecalc 68da25fd / csw dbf937eb refetched SHA-exact. NEW frontier in the F-NEW-309 row: the menu-content render pipeline.",
    "evidence": "evidence/cont54/CONT54_RESULT.md",
})

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print("registry updated: 636 -> 637 (F-NEW-326 appended ROOT-CAUSED-FIXED; F-NEW-309 next_wave refreshed)")
