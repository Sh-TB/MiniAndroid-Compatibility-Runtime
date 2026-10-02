#!/usr/bin/env python3
"""F-NEW-228 wave — registry reconciliation.

1. F-NEW-228: OBSERVED -> IMPLEMENTED+TESTED (AOSP TableLayout super.measureVertical
   weight-pass port: LEG-A row-wrap, LEG-B/B2 participation+vertical force, LEG-C
   resolved-excess, mTotalLength vertical-axis fix). 3-run proof banked.
2. Registers F-NEW-229 (CL MATCH_PARENT spec law — attempted, reverted, OBSERVED).
3. Registers F-NEW-230 (golden provenance/config-recording process law — 4 banked
   goldens unreproducible at HEAD with default configs).
"""
import json

P = "/home/z/my-project/root_registry.json"
r = json.load(open(P))
roots = r["roots"]

for x in roots:
    if x.get("id") == "F-NEW-228":
        x["status"] = "IMPLEMENTED+TESTED"
        x["law"] = (
            "AOSP TableLayout extends LinearLayout and its onMeasure→measureVertical "
            "CALLS super.measureVertical (TableLayout.java android-14 L470-476), so the "
            "LinearLayout weight pass RUNS for table rows; findLargestCells (L527-529) "
            "forces every visible TableRow's layoutParams.height=WRAP_CONTENT before "
            "super.measureVertical, so a weighted row's first-pass main-axis base is its "
            "CONTENT height (never the match-parent inflation); TableLayout.onMeasure "
            "enforces VERTICAL (L433-437) even though its orientation field is never "
            "XML-set; LinearLayout.measureVertical weight block (L978-1040): "
            "remainingExcess is computed against the RESOLVED container size "
            "(resolveSizeAndState caps AT_MOST at min(content, spec)) — a wrap container "
            "never expands weighted children, only an EXACTLY container distributes "
            "positive excess; share = childWeight*remainingExcess/remainingWeightSum with "
            "sequential decrement (L1011-1014); base = lp.height==0 ? share : "
            "measuredHeight+share (L1019-1025); mTotalLength accumulates the weighted "
            "child's MAIN-axis measurement (measured_height for vertical containers)."
        )
        x["fix"] = (
            "miniandroid/src/resources/layout_inflater.cpp measure phase: "
            "LEG-A — TableLayout rows with lp_height==-1 measure WRAP on the main axis "
            "(findLargestCells port); LEG-B — the TableLayout/TableRow exclusion removed "
            "from the measure-phase weight pass (TableLayout.java L474 super.measureVertical); "
            "LEG-B2 — main_horiz forced false for TableLayout inside the weight block "
            "(orientation field is never set; the default-horizontal law misrouted the "
            "weight pass to the WIDTH axis: rows received EXACTLY(width) shares + "
            "EXACTLY(screen) cross heights, measured 0x1920); LEG-C — resolved-excess law "
            "(EXACTLY distributes; AT_MOST resolves min(content,spec) so it never expands); "
            "mTotalLength fix — vertical weighted children add measured_HEIGHT (the old "
            "measured_width poisoned total_length: rows added 1038/945 widths instead of "
            "126 heights → negative excess → rows collapsed to 0)."
        )
        x["before"] = (
            "opencalc rows (VSTACK): 712 h=126; 731/738 h=0 (clip); 743 h=1057 at y=161; "
            "748 h=1056 at y=1218; 753 h=1056 at y=2274 OFF-SCREEN (1920 screen); "
            "screenshot ae07c6804b5071d0 = 91.3% #6fa8dc display + 8.2% #303030, NO "
            "number-pad buttons visible."
        )
        x["after"] = (
            "opencalc rows (VSTACK): 712 h=126 at y=32; 731 h=351 at y=161; 738 h=352 at "
            "y=512; 743 h=352 at y=864; 748 h=352 at y=1216; 753 h=352 at y=1568 — "
            "1568+352=1920 exactly fills the screen; screenshot e364b001ee7abd66 = 64.7% "
            "#303030 button field + 34.5% #6fa8dc display; button glyphs draw (250 unique "
            "colors). RESIDUAL (F-NEW-229): rows measure 462 wide (CL MATCH_PARENT spec "
            "gap upstream shrinks SlidingUpPanelLayout 1080→579→TableLayout 504)."
        )
        x["test"] = (
            "laws130 51/51 PASS; goldens ×3 byte-identical: dooz d602648e8e401895, "
            "microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8; ssw (omegacentauri), "
            "headingcalc, secuso, whatsapp frames byte-identical to the HEAD baseline "
            "(their BANKED goldens are stale-config — F-NEW-230); opencalc ×3 "
            "e364b001ee7abd66 deterministic (rc=0)."
        )
        x["current"] = (
            "IMPLEMENTED+TESTED ×3-run on HEAD+patch; row heights AOSP-equal; width "
            "residual tracked as F-NEW-229 (CL MATCH_PARENT spec law)."
        )
        break
else:
    raise SystemExit("F-NEW-228 not found")

ids = {x.get("id") for x in roots}
if "F-NEW-229" not in ids:
    roots.append({
        "id": "F-NEW-229",
        "status": "OBSERVED",
        "priority": "P1",
        "layer": "layout/constraintlayout-match-parent-spec",
        "title": "CL MATCH_PARENT SPEC LAW: a ConstraintLayout child with "
                 "width/height=MATCH_PARENT and NO anchors on that axis falls back to "
                 "child_spec → AT_MOST(available), so content-less subtrees shrink-wrap "
                 "instead of filling the parent. AOSP ConstraintLayout.onMeasure resolves "
                 "MATCH_PARENT children EXACTLY against the parent's resolved dimension.",
        "law": "AOSP ConstraintLayout (androidx) onMeasure: a child with "
               "MATCH_PARENT dimension is measured with EXACTLY(parent available − "
               "margins) on that axis (CL treats MATCH_PARENT as fill-constraints), "
               "regardless of anchor completeness on that axis.",
        "evidence": "opencalc res/9t.xml: SlidingUpPanelLayout lp=-1/0dp with only "
                    "vertical constraints (constraintBottom_toBottomOf=parent, "
                    "constraintTop_toBottomOf=@7F0901BD); real CL fills width=1080; "
                    "MiniAndroid CL-branch fallback gives AT_MOST(1080) → 612 measured "
                    "579x1920 → 646 504x1920 → TableLayout 504x1920 → rows 462 wide "
                    "([U007-SPEC] view 612 spec=1080/AT_MOST; [U007-SPEC-OUT] content="
                    "579x1920 -> 579x1920). F-NEW-228's weight pass then distributes the "
                    "shrunken width (buttons at 115px pitch in a 462px band).",
        "fix": "ATTEMPTED + REVERTED 2026-10-02: adding EXACTLY(avail) for lp==-1 in the "
               "CL-branch fallback produced NO opencalc change (612 is not routed through "
               "the edited measure branch — the CL routing of the SlidingUpPanelLayout "
               "chain needs its own trace first) — reverted per the no-unproven-change "
               "gate. The fix must land where the spec is actually produced (trace with "
               "U007_LAYOUT_DEBUG=3 + per-branch attribution).",
        "test": "after the real fix: opencalc rows 1038 wide, buttons 259px pitch, "
                "dooz/microtimer/unote/ssw goldens byte-identical, laws130 51/51.",
        "fanout": "every ConstraintLayout-based APK with match_parent children lacking "
                  "explicit anchors on one axis (common in AppCompat layouts).",
        "aff": "opencalc (button width), any CL app with the same shape.",
    })

if "F-NEW-230" not in ids:
    roots.append({
        "id": "F-NEW-230",
        "status": "OBSERVED",
        "priority": "P1",
        "layer": "evidence/golden-provenance",
        "title": "GOLDEN PROVENANCE/CONFIG GAP: four banked golden SHAs are not "
                 "reproducible at HEAD with default configs — ssw f48ae6d467d1e746 "
                 "(omegacentauri.mobi.simplestopwatch_26: HEAD+baseline produce "
                 "0297e27f4e217286 = 99.4% black, time text collapsed via BigTextView "
                 "0dp+weight wrap-measure=0), headingcalc be1cea9cf994b26a (HEAD produces "
                 "4d462461006fe7fe with IDENTICAL code to the banking commit), secuso "
                 "eb5ebd559cad1028 (HEAD produces 31ddd4d5b8e6d18e = 100% WHITE), "
                 "whatsapp 31ddd4d5b8e6d18e (the golden itself IS a pure-white frame). "
                 "The worklog's 'goldens x3 byte-identical' gates were run with configs/"
                 "flows not recorded in the registry (screen size, click flows, run "
                 "duration, APK path variants).",
        "law": "Evidence law (CONSTITUTION V2): a golden gate must carry the FULL "
               "reproduction command (APK sha256 + screen WxH + flags + flow + frame "
               "index). A golden that cannot be reproduced from the registry is not "
               "evidence — it is a lead. 31ddd4d5b8e6d18e (pure white) being banked as "
               "the whatsapp gate also violates the blank-frame law (FRAME_CAPTURE_TRUTH).",
        "evidence": "scripts/f228_regress.sh matrix 2026-10-02: dooz/microtimer/unote "
                    "MATCH@1920 ×3; ssw/headingcalc/secuso/whatsapp DRIFT equally on the "
                    "HEAD baseline binary AND the F-NEW-228 patch binary (patch-neutral); "
                    "muellerma.stopwatch_6 vs omegacentauri.simplestopwatch_26 APK-mapping "
                    "error found and corrected in the process.",
        "fix": "Re-bank the 4 goldens with a recorded reproduction block (apk sha256, "
               "WxH, flags, flow steps, frame index); add a golden_repro field to the "
               "registry schema; whitelist-blank-frame gate (a 100%-single-color golden "
               "must be rejected at banking time).",
        "test": "every banked golden reproduces ×3 from its registry repro block on a "
                "clean checkout.",
        "fanout": "all 8+ regression-gated APKs; any future session re-running the gate.",
        "aff": "evidence infrastructure.",
    })

r["total_roots"] = len(roots)
r["count"] = len(roots)
from collections import Counter
r["status_counts"] = dict(Counter(x.get("status", "?") for x in roots))
r["generated"] = "2026-10-02"
json.dump(r, open(P, "w"), indent=1, ensure_ascii=False)
print("registry updated:", len(roots), "roots;",
      "F-NEW-228 =", next(x["status"] for x in roots if x.get("id") == "F-NEW-228"))
