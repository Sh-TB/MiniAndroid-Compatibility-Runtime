#!/usr/bin/env python3
"""s132_register_wave1.py — S132 REUSE-PROOF WAVE canonical registration.

1. R-NEW-437 honesty correction + closure: the opencalculator frontier was
   misdiagnosed as "GridLayout bounds unassigned" — the APK's real
   activity_main (res/Ok.xml, decoded via scripts/s132_axml_dump.py) has NO
   GridLayout; the pad is TableLayout(id=tableLayout) → 8 TableRows → 34
   Buttons(ImageButtons) with layout_width=0dip + layout_weight.
2. New roots R-NEW-438..441 registered with their measured evidence.
3. R-NEW-437 closed ROOT-CAUSED-CLOSED (frontier: blank screen + 0 bounds
   → pad renders, buttons with real bounds/hit targets, 3-run SHA
   ed96091f1c86a497 deterministic).
4. reuse_registry Yoga entry: REJECTED for THIS root (existing implementation
   superior after local root fix) + honesty fix (no Yoga adapter exists in
   the tree; campaign-010 differential evidence was on a simple LL tree and
   the build directory is gone).
Idempotent.
"""
import json

ROOTS = "/home/z/my-project/root_registry.json"
REUSE = "/home/z/my-project/canonical/reuse_registry.json"

# ---------------------------------------------------------------- roots
with open(ROOTS) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) else reg

new_roots = [
    {
        "id": "R-NEW-438",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "fg": False,
        "title": "DEX onMeasure override emulation defeats the native container laws (incomplete-emulation law missing) — library containers collapse to 0x0 or skip child measure",
        "evidence": (
            "S132 oc_base: app-bundled androidx.ConstraintLayout.onMeasure answered 0x0 under "
            "EXACTLY(1080)xEXACTLY(1920) ([DEX-MEASURE]); SlidingUpPanelLayout.onMeasure returned a "
            "real size but its subtree stayed measured=0x0 — the native F-148 anchor walk never ran. "
            "Two-law fix in LayoutInflater::measure_node_raw arm1 (degenerate 0x0 result under "
            "non-degenerate specs → native law takes over) + arm2 (AOSP ViewGroup.onMeasure contract: "
            "a container result whose visible children are ALL unmeasured → native law)."
        ),
        "missing": "degenerate-result + child-contract gates on the DEX onMeasure hook",
        "next": "close via battery + goldens",
        "commit": "S132",
    },
    {
        "id": "R-NEW-439",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "fg": False,
        "title": "ConstraintLayout PARENT_ID sentinel: modern AGP compiles app:layout_constraint*_to*Of=\"parent\" as typed INT 0 without a raw string — the raw==\"parent\"-only capture dropped every parent anchor",
        "evidence": (
            "opencalculator v53 AXML: layout_constraintTop_toTopOf=INT(0) (scripts/s132_axml_dump.py); "
            "0dp TableLayout lost its top/bottom→parent span. Fix: cl_anchor maps is_int() && data==0 → "
            "\"parent\" (ConstraintLayout.LayoutParams.PARENT_ID = 0 law)."
        ),
        "missing": "INT-0 parent sentinel mapping in cl_anchor",
        "next": "close via battery + goldens",
        "commit": "S132",
    },
    {
        "id": "R-NEW-440",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "fg": False,
        "title": "Two competing measure laws: the engine's DEX measure bridge sized container subtrees with the primitive spec law (no anchors/weights/TableLayout rows) instead of the canonical inflater law; render/input roots also diverged (content_view_id unset on the appcompat delegate path)",
        "evidence": (
            "ONE CANONICAL MEASURE LAW refactor (R-NEW-440): measure_layout's law promoted to member "
            "measure_node_raw/measure_node with the shared M3 memo; new entry LayoutInflater::measure_view_spec; "
            "the engine's View.measure bridge delegates ViewGroup subtrees to it ([R440-CANONICAL] evidence). "
            "R-NEW-440b: effective_content_root_() — one render/input root law (Activity content root, else the "
            "S83 android.R.id.content node) shared by the draw walk, stage_tap and the long-press stage; "
            "fixes [F117-TAP] target=0 on the appcompat delegate path."
        ),
        "missing": "canonical delegation + shared content-root resolution",
        "next": "close via battery + goldens",
        "commit": "S132",
    },
    {
        "id": "R-NEW-441",
        "status": "PARTIAL",
        "priority": "P1",
        "fg": False,
        "title": "SlidingUpPanelLayout runtime-state family: View.getLeft/getTop/getRight/getBottom had NO bridge (umano dimChildToDimen cover test read degenerate bounds); F096 dispatched real-DEX onLayout with a degenerate 0x0 rect; layout weight shares computed 3x too tall for opencalculator rows",
        "evidence": (
            "FIXED: AOSP View bounds-getter law (answer from measured_left/top/right/bottom — "
            "umano SlidingUpPanelLayout.java L680-697 anchor); F096 traversal-order gate (no onMeasure/onLayout "
            "dispatch on a 0x0 frame — AOSP ViewRootImpl law); R-NEW-438 AT_MOST wrap-weight branch "
            "(LinearLayout.java measureHorizontal useExcessSpace law: weighted children measured WRAP so their "
            "cross size feeds the container). PARTIAL residue: opencalculator row weight shares 3x too tall "
            "(weight_sum capture suspected — rows ~1057px vs ~353px expected); display-write after tap blocked "
            "by the app's async layer (Lt1/a;.b IllegalStateException)."
        ),
        "missing": "weight_sum capture law; display async-write frontier",
        "next": "weight_sum law first (generic), then the async layer probe",
        "commit": "S132",
    },
]

by_id = {r.get("id"): r for r in roots}
for nr in new_roots:
    if nr["id"] in by_id:
        by_id[nr["id"]].update(nr)
    else:
        roots.append(nr)
        by_id[nr["id"]] = nr

# R-NEW-437: honesty correction + closure
r437 = by_id.get("R-NEW-437")
if r437:
    r437["title"] = (
        "[HONESTY-CORRECTED S132] opencalculator pad collapsed (34 buttons/8 rows bounds=0, "
        "blank screen) — TableLayout/TableRow/weight + ConstraintLayout MATCH_CONSTRAINT family; "
        "NOT GridLayout (the APK has no GridLayout — S131 probe misread the 76-node heap scan)"
    )
    r437["status"] = "ROOT-CAUSED-CLOSED"
    r437["evidence"] = (
        "S132 source-first: scripts/s132_axml_dump.py decoded res/Ok.xml — pad = TableLayout(id=tableLayout, "
        "0dp, top/bottom→parent) → 8 TableRows → 34 Buttons(0dp+weight, text captured 231x126 intrinsic). "
        "Fixes R-NEW-438/439/440 + R-NEW-441 arms. AFTER: pad renders (evidence/s132_reuse_wave/oc_after_pad_renders.jpg), "
        "buttons with real bounds (e.g. '5' at (280,161) 259x1057; row 685 buttons 205x126 at y=32), "
        "3-run screenshot SHA ed96091f1c86a497 deterministic; tap (409,689) → hit target=718 → PerformClick → "
        "real DEX XML_CLICK keyDigitPadMappingToDisplay DISPATCHED ([F117-TAP]/[G06-TOKEN] click_dispatched:true). "
        "BEFORE: blank window, 23472 nonwhite px → AFTER 2073600. Battery 122 stages ALL PASS; "
        "fan-out scan scripts/s132_corpus_scan.py: 12 corpus APKs exercise the weight family, bouncy+chess "
        "TableLayout — bouncy 3-run dd2dee85b51ae581 deterministic."
    )
    r437["next"] = "closed; visual row-height residue tracked under R-NEW-441"

if isinstance(reg, dict):
    reg.setdefault("meta", {})
    reg["meta"]["last_update"] = "S132 reuse-proof wave"
else:
    reg = roots

with open(ROOTS, "w") as f:
    json.dump(reg, f, indent=1)
print("roots registered:", [r["id"] for r in new_roots], "+ R-NEW-437 closed")

# ---------------------------------------------------------------- reuse registry
with open(REUSE) as f:
    reuse = json.load(f)
for c in reuse["candidates"]:
    if c.get("REUSE_CANDIDATE") == "yoga":
        c["status"] = "REJECTED_FOR_MC041_EXISTING_SUPERIOR"
        c["DECISION"] = "REJECTED → EXISTING IMPLEMENTATION SUPERIOR (for the measured root)"
        c["REASON"] = (
            "S132 source-first comparison (S132 directive items 1-11): opencalculator's real layout uses "
            "TableLayout/TableRow/weight + ConstraintLayout MATCH_CONSTRAINT — semantics Yoga does not model "
            "(no TableLayout rows, no CL anchors). The actual defects were LOCAL law gaps (R-NEW-438/439/440), "
            "fixed with ~150 LOC of AOSP-anchored law code instead of a ~40k LOC library + adapter. "
            "Honesty fix: no Yoga adapter exists in the current tree (campaign-010's f131606 was lost in the "
            "UNIFIED rebases; its 10/10 differential was on a simple LinearLayout tree). Yoga remains the "
            "candidate for a measured FlexboxLayout-class APK."
        )
        c["evidence"] = "docs/runtime/knowledge/campaign010/evidence/uc010_yoga_differential.txt (historical); S132 worklog"
reuse["counts"]["REJECTED_FOR_MC041_EXISTING_SUPERIOR"] = 1
with open(REUSE, "w") as f:
    json.dump(reuse, f, indent=1)
print("reuse_registry Yoga -> REJECTED_FOR_MC041_EXISTING_SUPERIOR")
