#!/usr/bin/env python3
"""cont57_registry.py — CONT-57 registry update (639 -> 640).

F-NEW-329: ROOT-CAUSED-FIXED — the native ConstraintLayout measure law had
three generic gaps: (1) GUIDELINE INVISIBILITY — anchor-target lookup and
the per-axis passes skipped GONE children entirely, and
layout_constraintGuide_percent/begin/end were never parsed, so every child
chained through a Guideline lost its anchor (opencalculator v53: guideline1
0.18/0.24 chain the whole display stack); (2) UNRESOLVED-ANCHOR
MATCH_CONSTRAINT — lp==0 with a missing anchor on the axis fell into
child_spec(...,0) which answers EXACTLY(0) (the display HSVs measured
52x0); AOSP degrades a one-anchor 0dp widget to WRAP; (3) BOTH-ANCHOR
MATCH_PARENT — lp==-1 with both edges resolved measured AT_MOST(span),
letting content-sized subtrees shrink inside their span (sliding_layout
measured 579/1080); AOSP fixes a both-anchored match_parent child to the
span. Plus the TYPED-FLOAT law: aapt2 compiles percent/bias as typed FLOAT
(0x04) with NO raw string — atof("") pinned both guidelines at Y=0.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-329" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 639, f"expected 639 roots, got {len(roots)}"

entry = {
    "id": "F-NEW-329",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "framework/measure-constraintlayout-guideline-dimension",
    "title": "The native ConstraintLayout measure law (F-148 subset) lost three generic families: (1) Guideline children — anchor-target lookup filtered visibility!=8 (Guidelines are ALWAYS flagged GONE-for-draw, and any GONE widget is a legal AOSP anchor target), the per-axis passes skipped GONE children before positioning, and layout_constraintGuide_percent/begin/end were never parsed — every child chained through a Guideline resolved to the no-anchor law; (2) UNRESOLVED-ANCHOR MATCH_CONSTRAINT — lp==0 with the axis's both-anchors condition false fell into child_spec(...,0), whose child_dim>=0 branch answers EXACTLY(0); AOSP degrades a one-anchor 0dp widget to WRAP; (3) BOTH-ANCHOR MATCH_PARENT — lp==-1 with both edges resolved measured AT_MOST(span), so content-sized subtrees shrank inside their span; AOSP fixes a both-anchored match_parent to the span. Plus the TYPED-FLOAT law: aapt2 compiles percent/bias as typed FLOAT 0x04 with NO raw string — atof(\"\") answered 0.0, pinning both guidelines at Y=0 even after (1) landed.",
    "root_cause": "Evidence chain (U007_LAYOUT_DEBUG=2/3 view-tree + spec dumps, opencalculator v53, binary 11e5fa2c3b4b5037): sliding_layout (SlidingUpPanelLayout lp=-1/0) measured 579x1920 with constraintLayout2=504 wide and TableLayout rows 0-wide (0dp+weight buttons 0x351); inputHSV/resultDisplayHSV measured 52x0; s132 AXML decode of res/Ok.xml (obfuscated layout name) proved the REAL layout chains inputHSV.top=parent, inputHSV.bottom=guideline1(percent 0.18), resultHSV.top=guideline1, resultHSV.bottom=guideline2, sliding_layout.top=resultHSV.bottom, sliding_layout.bottom=parent. Fix (layout_inflater.cpp + android_shadows.h ViewNode, one generic law set): (a) parse cl_guide_percent (typed FLOAT memcpy / FRACTION data/2^24 / raw-string fallback), cl_guide_begin/end (parse_dim_attr), and XML-set bias from typed FLOAT; (b) cl_name_to_id drops the visibility filter (GONE nodes remain anchor targets); (c) per-axis Guideline branch — never measured, never drawn, never wrap-content, edge = begin/end (negative = from far edge)/percent x content span (+ padding), orientation 0=HORIZONTAL fixes Y in the vertical pass, 1=VERTICAL fixes X in the horizontal pass; (d) dimension law both-anchors: lp==0 OR lp==-1 -> EXACTLY(span), lp>=1 -> EXACTLY(min(lp,span)), wrap -> AT_MOST(span); single/no-anchor: lp>=1 fixed, lp==0 degrades to WRAP (-2 path); (e) guidelines excluded from wrap-content aggregation. AOSP ground truth: Guideline.java position law, ConstraintLayout.java DimensionResolution (MATCH_PARENT maps to fixed-span under both anchors), ViewGroup GONE-anchor legality.",
    "next_wave": "OpenCalc face healed to a full calculator: guideline1 = 0.18x1920 = 346 EXACT AOSP math; inputHSV 1080x199 @(0,147), resultHSV 1080x153 @(0,346), sliding_layout 1080x1421 @(0,499), pad rows 1080-wide, 0dp+weight buttons 270x252 (were 0-wide). New gate face 0ae271c49d2bd61c x3 deterministic (re-pinned in cont37_regression.sh from a976d2f9fb675cb3). Zero drift elsewhere: 14 anchors/controls x3 = 42/42 byte-identical (dooz/micro/unote/gmdice/tanana/ttt/flappy/g2048/simplecalc/csw/bmi/alex/notes), probe battery == records (21 probes incl. f259g 84/7 + fnew302 48/24 documented), fnew328 4/0, fnew322 5/0. Remaining OpenCalc legs recorded: the srcCompat vector-drawable decode (point/backspace/exponent ImageButtons draw as plain boxes; 0/554 drawable paths resolve — the F-NEW-309 family), the menu icon. Next roots: BMI Spinner selected-item content law (fields 817-wide draw empty), tanana glyph leg (F-NEW-308), alex content text, dooz Compose tap bridge (F-NEW-267).",
    "evidence": [
        "evidence/cont57/opencalc_before.png (pre-fix face, binary 11e5fa2c3b4b5037)",
        "evidence/cont57/opencalc_fixed_full.png (post-fix gate face 0ae271c49d2bd61c)",
        "evidence/cont57/CONT57_APP_MOSAIC.png (before/after + 13 standing faces; uploaded h.uguu.se/vuQSHepf.png + tmpfiles.org/wWAOKxl3jbzH)",
        "run/cont56c/oc_dump2_stderr.txt (U007=2 pre-fix tree: sliding 579x1920, HSVs 52x0, buttons 0-wide)",
        "run/cont56c/oc_post2_err.txt (U007=2 post-fix tree: sliding 1080x1421 @y499, buttons 270x252)",
        "run/cont56c/gate_anchors.log + gate_cont37.log (42/42 + opencalc re-pin x3)",
        "scripts/s132_axml_dump.py res/Ok.xml decode (guideline percent chain ground truth)",
    ],
}

roots.append(entry)
reg["count"] = len(roots) if isinstance(reg, dict) and "count" in reg else None
if isinstance(reg, dict) and "count" in reg:
    reg["count"] = len(roots)

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print(f"registry: 639 -> {len(roots)} (F-NEW-329 appended)")
