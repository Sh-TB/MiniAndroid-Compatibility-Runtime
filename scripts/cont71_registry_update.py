#!/usr/bin/env python3
"""CONT-71 registry update: F-NEW-368/F-NEW-370 -> PARTIAL (laws implemented,
env-gated; activation decode complete); new frontier F-NEW-374 (per-container
DEX-measure trust law). Recomputes metadata; asserts id uniqueness."""
import json, sys

REG = "root_registry.json"
r = json.load(open(REG))

ev368 = ("evidence/cont71/cont71_evidence.json; run/s71/activation_f368only "
         "(delivery row 'deferred handler @0x53 type=Exception' + the app's own "
         "'Default behavior class null' LOG line = the app catch RAN; face "
         "6da289aa = the honest Law-A-only activation status); "
         "run/s71/activation_full (pair active: memory face c559b630 == record, "
         "opencalc 3e73a5ad = the honest divergence)")
ev370 = ("evidence/cont71/cont71_evidence.json; run/s71/lawA_trace + "
         "run/s71/lawB_warm (CoordinatorLayout answers 0x0 -> 1080x1920 with "
         "the resolve law); docs/UPSTREAM_SOURCE_MINING.jsonl rows U-04..U-06 "
         "(androidx CoordinatorLayout.java onMeasure + ViewGroup.java "
         "measureChildWithMargins + View.java resolveSizeAndState fetched and "
         "cited); run/s71/gate2..gate6 decode trail")

new374 = {
    "id": "F-NEW-374",
    "status": "CLASSIFIED",
    "priority": "P1",
    "layer": "dex/view-measure (per-container DEX-measure trust)",
    "title": ("PER-CONTAINER DEX-MEASURE TRUST LAW (CONT-71 named lever): the "
              "F-NEW-368 delivery + the F-NEW-370 measure laws (negotiation "
              "measureChildWithMargins + answer resolveSizeAndState family) are "
              "IMPLEMENTED behind MINIANDROID_F368_LAW=1 / MINIANDROID_MCM_LAW=1 "
              "and proven on the memory app (CoordinatorLayout chain completes, "
              "face c559b630 == record under the activated pair), but the SAME "
              "activation deterministically diverges opencalculator v53 "
              "(3e73a5ad, collapsed): the app's SlidingUpPanelLayout DEX "
              "onMeasure is incompletely emulated (R-NEW-441 family) and its "
              "child-measure results feed wrong-but-in-bounds specs "
              "(EXACTLY(105) from the drag-view read-back) plus a garbage "
              "out-of-display spec EXACTLY(1073740479) (spec-bounds gates now "
              "decline the OOB shape; the in-bounds wrong-spec shape remains). "
              "Decode: the DEX-measured child sizes change the panel's internal "
              "offset/measure math -> the panel slides its content off-view. "
              "Lever: a per-container DEX-measure trust discipline (which "
              "containers' completed DEX onMeasure answers are authoritative vs "
              "which fall back to the native law) — e.g. bounded activation "
              "proofs per container family with cross-family regression walls; "
              "NOT per-app gating. The default binary keeps ALL the CONT-71 "
              "laws OFF (byte-equivalent behavior; wall 39/39 MATCH proved)"),
    "evidence": ("run/s71/gate4 (738 answers 0x0 again after the OOB gate; "
                 "EXACTLY(105) in-bounds rows remain); run/s60/regression/"
                 "opencalc_r1 vs run/s71/regression/opencalc_r1 pixel metrics "
                 "(321287 vs 3096 sampled non-bg)"),
    "first_observed": "CONT-71",
}

found = 0
for root in r["roots"]:
    if root["id"] == "F-NEW-368":
        root["status"] = "PARTIAL"
        root["title"] = (
            "Deferred synthesized exceptions do not deliver to the SAME-FRAME "
            "catch — LAWS IMPLEMENTED (CONT-71, env-gated MINIANDROID_F368_LAW): "
            "the subtype-table extension (reflective + java.net + concurrent + "
            "android families, OpenJDK/AOSP documented parents) plus the "
            "in-frame delivery make the typed catch(Exception) at "
            "CoordinatorLayout.getResolvedLayoutParams pc=67 match (row "
            "'deferred handler @0x53 type=Ljava/lang/Exception;'; the app's own "
            "'Default behavior class null could not be instantiated' LOG line "
            "proves the app catch RAN). Activation status: F368-only -> memory "
            "blank 6da289aa (the completed onMeasure's children are unmeasured); "
            "F368+MCM pair -> memory face c559b630 == record (the full chain "
            "completes correctly) while opencalc diverges (F-NEW-374). Default "
            "binary keeps the law OFF pending the per-container trust lever.")
        root["evidence"] = ev368
        found += 1
    elif root["id"] == "F-NEW-370":
        root["status"] = "PARTIAL"
        root["priority"] = "P1"
        root["title"] = (
            "CoordinatorLayout.onMeasure DEX-COMPLETION measure chain — LAWS "
            "IMPLEMENTED (CONT-71, env-gated MINIANDROID_MCM_LAW) after full "
            "first-divergence decode vs the fetched androidx/AOSP sources: "
            "(1) ViewGroup.measureChildWithMargins had NO engine shadow — the "
            "child-negotiation call inside every real DEX container onMeasure "
            "silently no-op'd (children never measured); (2) "
            "View.resolveSizeAndState had NO engine shadow — the upstream "
            "answer law 'setMeasuredDimension(resolveSizeAndState(...))' "
            "answered 0 under EXACTLY specs (CoordinatorLayout 0x0). Both laws "
            "implemented (AOSP-verbatim math + F-NEW-328 LP-SOURCE + "
            "R-NEW-440 canonical child measure + ViewRootImpl spec-bounds "
            "gates); under the activated pair memory renders its record face. "
            "ACTIVATION BLOCKED by F-NEW-374 (opencalc SlidingUpPanelLayout "
            "incomplete-emulation divergence). Default OFF; the decode trail "
            "and the gated laws are the deliverable.")
        root["evidence"] = ev370
        found += 1

assert found == 2, f"expected both rows, found {found}"
ids = [x["id"] for x in r["roots"]]
assert len(ids) == len(set(ids)), "duplicate id"
r["roots"].append(new374)
r["total_roots"] = len(r["roots"])
r["count"] = len(r["roots"])
from collections import Counter
sc = Counter(x["status"] for x in r["roots"])
r["status_counts"] = dict(sc)
r["generated"] = "CONT-71 wave (F-NEW-368/370 PARTIAL laws-implemented + F-NEW-374 frontier)"
json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry roots:", r["total_roots"], "| F-NEW-368/370 -> PARTIAL | F-NEW-374 added")
