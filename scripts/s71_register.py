#!/usr/bin/env python3
"""s71_register.py — S71 registry updates (single source of truth).

1. R-NEW-389: OBSERVED-FAIL → ROOT-CAUSED-SEMANTIC (first-pixel-divergence
   proven at op level: drawText arg "" → "Touch to start" — ScoreView
   getString, F-136 collateral; controls cur×3/golden×3 deterministic;
   instrumentation render-neutral).
2. R-NEW-388: ROOT-CAUSED-NOT-FIXED → re-measured: generic RL anchor laws
   PROVEN on f14 (current binary); TriPeaks blocked at SplashActivity
   (app-specific path); demoted from foundation gap list.
3. A7: impact claim corrected (log-only, no pixel consumer on HEAD);
   classification split PARTIAL(parse)/TRUE-MISSING(identity consumer law).
4. NEW F-137 (P0): ancestry-dispatch root law — substring guards miss app
   subclasses; FIXED via framework_ancestor_for_dispatch + one fallthrough
   retry; battery 92/94 (2 environmental); FALSE-UNSERVED rows converted.
5. NEW F-138 (P1): bouncy splash-hint ScoreView HUD geometry — bitmap-font
   text drawn at (0,0) (ScoreView hint positioning is cosmetic follow-up).
"""
import json
from pathlib import Path

REG = Path("/home/z/my-project/root_registry.json")
rr = json.loads(REG.read_text())
roots = {r["id"]: r for r in rr["roots"]}


def setrec(rid, **kw):
    r = roots.get(rid)
    if r is None:
        r = {"id": rid}
        rr["roots"].append(r)
        roots[rid] = r
    r.update(kw)


setrec(
    "R-NEW-389", status="ROOT-CAUSED-SEMANTIC", priority="P1",
    title="bouncy 81-px top-band divergence — ROOT-CAUSED: F-136 collateral "
          "(splash hint now renders), NOT nondeterminism",
    evidence="S71 FIRST PIXEL DIVERGENCE (op level, docs/foundation/s71/"
             "R-NEW-389_ROOT_CAUSE.md): canvas op trace (MINIANDROID_CANVAS_"
             "OP_TRACE, render-neutral) differs in exactly ONE field between "
             "b88e09d9 golden build and F-136 build: drawText text content "
             '"" -> "Touch to start" (ScoreView.java:226 getString(R.string.'
             "touch_to_start_message)). Controls: current-source x3 + "
             "golden-source x3 byte-identical (4f41dda2 / 53177d4a); "
             "comment-only probe x1 from S70. Prior 'dispatch-identical' "
             "observation explained: trace records register NAMES as "
             "arguments (dalvik_engine.cpp:14451 arg_names), so string "
             "content was invisible; ViewTree identical because ScoreView "
             "draws via Canvas, not TextViews. Direction: toward fidelity "
             "(AOSP would render the string). Bounds F-136 collateral to "
             "1 string draw site.",
)
setrec(
    "R-NEW-388", status="ROOT-CAUSED-REMEASURED-GENERIC-OK", priority="P2",
    title="TriPeaks geometry — generic RL anchor laws PROVEN on f14 (current "
          "binary); game screen blocked at SplashActivity (app-specific path)",
    evidence="S71 re-measure (docs/foundation/s71/R-NEW-388_REMEASURE.md): "
             "f14_relative fixture on current binary — alignParentRight "
             "x=780, centerInParent (340,760), below=/margin chain y=300, "
             "no (0,0) collapse; S66 wiring-gap claim stale for HEAD. "
             "Fresh canonical runs never reach GameActivity (ViewTree = "
             "splash RelativeLayout+WebView only). TriPeaks card geometry "
             "demoted from foundation list until splash navigation is "
             "crossed; upstream law unchanged (AOSP RL measure rules).",
)
setrec(
    "A7", status="ROOT-CAUSED-NOT-FIXED", priority="P2",
    title="Manifest label/icon — identity consumer law missing (label raw "
          "in parse, zero runtime consumers, icon unparsed)",
    evidence="S71 chain (docs/foundation/s71/A7_CONTRACT_CHAIN.md): "
             "application_label captured raw (manifest_reader.cpp:477/:822), "
             "never ARSC-resolved, ZERO consumers (rg: parser+header only); "
             "getApplicationInfo returns bare singleton (dalvik_engine.cpp:"
             "24768, guard itself Context/Activity-substring = ancestry "
             "case); icon never parsed; NO title-bar surface on HEAD -> the "
             "S66 'raw @0x in pixels' impact claim corrected: raw string "
             "surfaces in engine.log only. Generic contract = manifest "
             "reference resolve at consume time (PackageParser + "
             "resolveReference law) + getApplicationLabel/labelRes/icon "
             "consumer law. Fixture path f53_manifest_label unchanged; "
             "bundles with F-137 ancestry + DRAWABLE-LAW (icon).",
)
setrec(
    "F-137", status="ROOT-CAUSED-FIXED", priority="P0",
    title="ANCESTRY-DISPATCH root law — substring guards miss app subclasses "
          "(Application/Activity/Service receivers fell to type-default stub)",
    fg=True,
    first_seen="S71 W5 forensic classification: 22 ANCESTRY-ROOT records "
               "(6 FALSE-UNSERVED, rank #1 family by trace-window coupling "
               "194 APIs)",
    evidence="UPSTREAM: AOSP hierarchy Application/Service extend Context; "
             "Activity extends ContextThemeWrapper extends Context "
             "(docs/upstream/aosp/CONTEXT_STRING_LAW.md pin + AOSP class "
             "declarations). FIX (no guard sites touched): "
             "framework_ancestor_for_dispatch() walks class_to_superclass_ "
             "(DEX) + built-in platform table, single retry at the bridge "
             "stub fallthrough (dalvik_engine.cpp:30507-30530). PROOF: "
             "gmdice GameMasterDice.getResources STUBBED->IMPLEMENTED x5, "
             "unote NoteMain.getWindow ->IMPLEMENTED, dooz App."
             "getApplicationContext ->IMPLEMENTED + App.getClass x2 "
             "IMPLEMENTED (<unknown>.getClass 14->12); MultiDexApplication."
             "getApplicationInfo chain fires (Application->Context). "
             "Battery 92/94 (EXT-01/02 = missing external fixture APK in "
             "fresh container, environmental). Pixels: 5/6 apps "
             "byte-identical pre/post; dooz new sha 736592d0 x3 "
             "deterministic with exactly the predicted conversions. "
             "TRUE-MISSING ancestry rows (setTitle/setTheme/"
             "setShowWhenLocked/setTurnScreenOn) still need method laws — "
             "predicted by classification, unchanged by design.",
)
setrec(
    "F-138", status="REGISTERED", priority="P1",
    title="ScoreView hint HUD geometry — bitmap-font text drawn at (0,0) "
          "(legacy text path, text_size=0)",
    fg=True,
    first_seen="S71 R-NEW-389 op-trace forensics (canvas op #1)",
    evidence="bouncy ScoreView hint 'Touch to start' renders at (0,0) via "
             "the legacy bitmap-font path (op trace text_size=0, matrix "
             "identity); on-device it positions per ScoreView layout. "
             "Cosmetic positioning + real text-shaping for the HUD surface; "
             "separate from R-NEW-389 (root-caused) — do not bundle with "
             "string-law work.",
)
rr["total"] = len(rr["roots"])
REG.write_text(json.dumps(rr, indent=1))
print(f"registry updated: {rr['total']} roots")
for rid in ("R-NEW-389", "R-NEW-388", "A7", "F-137", "F-138"):
    r = roots[rid]
    print(f"  {rid}: {r['status']}")
