#!/usr/bin/env python3
# cont99_registry_update.py — register the CONT-99 T1 outcome (F-NEW-402..406,
# the programmatic measure/layout input-layer laws) in root_registry.json and
# mirror it to canonical/root_cause_registry.json.
import json

PATH = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

with open(PATH) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
if isinstance(roots, dict):
    root_list = list(roots.values())
    dict_mode = True
else:
    root_list = roots
    dict_mode = False

n0 = len(root_list)
ids = {r.get("id") for r in root_list}
for f_new in ("F-NEW-402", "F-NEW-403", "F-NEW-404", "F-NEW-405", "F-NEW-406"):
    assert f_new not in ids, f"{f_new} already registered"

REGRESSION = (
    "wall 12/12 MATCH byte-identical (dooz 31ddd4d5b8e6d18e, opencalc "
    "f25b754c4565c38b, unote 90a67cc1ddda57b7, microtimer bbd350b6c14fbd52, x3); "
    "goldens 4/4; negatives 19/19; reinstall 5/5 identity ALL PASS; MG-310 7/7; "
    "MG-150 3/3; selftests 13/13; F-NEW-376 70/70; anchors sax1 PASS events=6/6, "
    "clock1 (0,0 1080x1920), clinit1 rows law-correct, swipe1 setup OK, c74esc "
    "containment OK, perf1 checksums byte-identical to the CONT-98 A/B "
    "(3688000/31744000/14534196240/14569628240)"
)
HONEST = (
    "reinstall 5/5 needed a container-fresh artifact repair: run/diff366/"
    "hidden_sources apks are container-transient and were consumed/wiped by an "
    "earlier battery step — repopulated from the canonical upload/ sources "
    "(identity shas proven in the PASS lines); the 5-FAIL interim was a "
    "sequence artifact, not a runtime regression. sax1/clinit1/swipe1/perf1 "
    "verdict rows print on stdout; the inherited battery script discards "
    "stdout (flagged at CONT-98) — rows captured via a direct stdout rerun "
    "this wave. PRE harness rows exit rc=0 with Status SUCCESS (paired, "
    "non-behavioral)."
)

entries = [
    {
        "id": "F-NEW-402",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "CONT-99 T1 View.setPadding was not implemented (silent generic-stub no-op): programmatic padding vanished and every padded container laid out children at the raw content origin",
        "layer": "framework/view-shadow",
        "directive": "#364 CONT-99 T1 (comment 6248236077) — View measurement and layout contract",
        "root_cause": "no View.setPadding/setPaddingRelative bridge existed anywhere (grep: zero sites) — the DEX call fell to the generic stub, so ViewNode padding_left/top/right/bottom stayed 0 and the inflater measure/layout laws computed content boxes at the raw origin (c99lay PRE: chip1 at (0,0) instead of the lawful (30,20); frame children unshifted by the 30px padding). The getPadding* getters were also absent, so DEX content-box math read lying zeros.",
        "fix": "framework/android_shadows.cpp ViewShadow dispatch: setPadding/setPaddingRelative write the node's four padding fields and raise layout_dirty (AOSP View.java padding law; setPaddingRelative maps start->left / end->right, the runtime's only LTR direction); getPaddingLeft/getPaddingStart/getPaddingTop/getPaddingRight/getPaddingEnd/getPaddingBottom answer the LIVE node padding.",
        "evidence": {
            "wave": "CONT-99",
            "fixture": "fixtures/cont99_lay_probe (real aapt2/ECJ/D8; apk run/cont99/c99lay.apk sha16 80e9399319060b70, V2-C99LAY)",
            "paired_ab": "PRE binary e51d7a643e6817ba (frozen CONT-98 baseline): chip1 l=0 t=0; POST binary 4dd92ae1371569e4: chip1 l=30 t=20 (bar padding 20 + child margin 10), frame child at +30/+30.",
            "rows_fixed": "chip1 (0,0)->(30,20); chip2 (50,0)->(100,20); inner (0,250)->(480,310) combined with F-NEW-404; PHASE2 padL getter row added",
            "regression": REGRESSION,
            "honest_notes": HONEST,
        },
        "issue": "#364 CONT-99 T1",
    },
    {
        "id": "F-NEW-403",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "CONT-99 T1 LayoutParams live-state law: post-addView public-field stores (lp.leftMargin = ..) were invisible to every measure/layout pass (attach-time-only sync + dropped LP identity)",
        "layer": "framework/params-sync",
        "directive": "#364 CONT-99 T1 (comment 6248236077) — layout params contract",
        "root_cause": "three coupled defects: (1) the addView/setLayoutParams enrich synced lp VALUES once at attach time but never recorded the LP identity on the node, so View.getLayoutParams (ROOT-055) materialized a FRESH object and every post-addView field store landed on an untracked, unmirrored object; (2) no traversal-entry refresh existed (AOSP ViewGroup laws read the LIVE mLayoutParams every pass); (3) the untracked mutation therefore never reached ViewNode lp_margin_*/layout_weight/lp_gravity (c99lay PRE: chip margins 10/20 lost, chip2 at 50 instead of 100).",
        "fix": "(1) dalvik_engine addView/setLayoutParams enrich records node->layout_params_object = lp_id (AOSP addView -> child.setLayoutParams: the view OWNS that exact object; ROOT-055 now answers it). (2) Traversal-entry LIVE-STATE refresh (execution_engine frame stage before measure_layout): every node whose LP heap object carries the lp_bridge authority stamp (set by the LP <init> bridge / LayoutHelper factory / setMargins bridge) has width/height/gravity/margins/weight re-read into the node mirror each pass. XML-path LP objects (real generateLayoutParams DEX, F-NEW-309) are deliberately NOT stamped — the inflater-written node lp_* stays authoritative.",
        "evidence": {
            "wave": "CONT-99",
            "fixture": "fixtures/cont99_lay_probe",
            "paired_ab": "PRE: chip2 l=50 (margin lost); POST: chip1 l=30, chip2 l=100 (margins from the post-addView field stores live every pass).",
            "rows_fixed": "chip1/chip2 margins; PHASE3 btn 300x80 (setLayoutParams identity + refresh)",
            "regression": REGRESSION,
            "honest_notes": HONEST + " MINIANDROID_C99_LPTRACE=1 env-gated per-node refresh trace kept for forensics (zero-cost off).",
        },
        "issue": "#364 CONT-99 T1",
    },
    {
        "id": "F-NEW-404",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "CONT-99 T1 LayoutParams(w, h, gravity) ctor dropped the gravity argument: every programmatic FrameLayout child with a gravity ctor laid out top-left",
        "layer": "framework/params-ctor",
        "directive": "#364 CONT-99 T1 (comment 6248236077) — FrameLayout gravity placement",
        "root_cause": "the generic LP <init> bridge handled (w,h), (w,h,weight F), (w,h,l,t,r,b) and (source) but NOT the 3-int (w,h,gravity) variant — under the engine's receiver-first args convention it arrives as argc=4 (args[0]=this), and the old code read no gravity slot at all, so FrameLayout.LayoutParams(120, 80, Gravity.CENTER) materialized gravity=0 (NO_GRAVITY) and the FrameLayout placement law answered the top-left default (c99lay PRE: inner at (0,250) instead of the lawful (480,310)).",
        "fix": "dalvik_engine LP <init> bridge: argc==4 with an INT32 tail sets the gravity heap field (the FLOAT-tail weight ctor keeps its own branch — dispatch by ARG TYPE, not count); the addView enrich transfers it into lp_gravity, which the FrameLayout placement law (R-NEW-302 axis-masked gravity resolution) already consumes.",
        "evidence": {
            "wave": "CONT-99",
            "fixture": "fixtures/cont99_lay_probe",
            "paired_ab": "PRE: inner l=0 t=250 (top-left of the padded frame); POST: inner l=480 t=310 = frame + padding 30 + centered in the 1080-60 x 200-60 content box; leaf centered by the container gravity at inner+(40,20).",
            "rows_fixed": "inner; leaf (both gravity rows)",
            "regression": REGRESSION,
            "honest_notes": HONEST,
        },
        "issue": "#364 CONT-99 T1",
    },
    {
        "id": "F-NEW-405",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "CONT-99 T1 MarginLayoutParams.setMargins(l,t,r,b) was a silent generic-stub no-op",
        "layer": "framework/params-ctor",
        "directive": "#364 CONT-99 T1 (comment 6248236077) — margins contract",
        "root_cause": "no setMargins bridge existed; the DEX call fell to the generic stub, so the 4 margin heap fields were never written and no ViewNode mirror update happened (any programmatic setMargins call was silently dropped).",
        "fix": "dalvik_engine bridge_to_api: setMargins on *LayoutParams receivers writes leftMargin/topMargin/rightMargin/bottomMargin on the LP heap object, stamps the lp_bridge authority bit, then reverse-looks-up the owning node via its recorded layout_params_object (F-NEW-403 identity) and re-writes the full lp mirror (set_layout_params) for immediate visibility — AOSP MarginLayoutParams.setMargins law, layout reads lp live.",
        "evidence": {
            "wave": "CONT-99",
            "fixture": "fixtures/cont99_lay_probe (margins via the setMargins bridge share the F-NEW-403/405 refresh path; the probe exercises the direct-field-store face of the same law)",
            "paired_ab": "same as F-NEW-403 rows (chip margins) — the bridge shares the sync law",
            "regression": REGRESSION,
            "honest_notes": HONEST,
        },
        "issue": "#364 CONT-99 T1",
    },
    {
        "id": "F-NEW-406",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": "CONT-99 T1 DEX float-bit register law at iput: stores into declared-float fields left raw IEEE-754 bits as INT32 (weight 1.0f read back as 1.06535e9 — 0px+weight children collapsed)",
        "layer": "dex/field-store",
        "directive": "#364 CONT-99 T1 (comment 6248236077) — measure weight contract",
        "root_cause": "DEX float registers carry raw IEEE-754 BITS in int registers (const/high16 v0, 0x3f800000 IS the literal 1.0f — no conversion instruction runs along that path). execute_iput stored the register DalvikValue as-is, so a declared-float field held INT32 bits; float readers then VALUE-cast (1065353216 -> 1.06535e9) or missed the field entirely. c99lay PRE: LinearLayout.LayoutParams.weight read 1.06535e9 (LPTRACE wt_type=1/INT32 wt=1.06535e9), the G04 §9 weight law computed garbage shares and the 0px+weight children collapsed to 0/full-width.",
        "fix": "execute_iput store boundary: a store into a field whose declared type is F with an INT32 register BIT-CASTS the bits into FLOAT32 (memcpy semantics — the DEX verifier requires float registers for F fields, so no genuine-int store exists); symmetric D + INT64 -> FLOAT64 law. Readers (LP enrich, F-NEW-403 refresh, LayoutHelper sync) then see the true float.",
        "evidence": {
            "wave": "CONT-99",
            "fixture": "fixtures/cont99_lay_probe",
            "paired_ab": "PRE (LPTRACE): wt_type=1 wt=1.06535e9, colE w=0/colF w=0 (or 1080/0 pre-identity); POST: wt_type=3 wt=1.0/3.0, colE (0,450,270,150) colF (270,450,810,150) — the exact AOSP 1:3 share of 1080.",
            "rows_fixed": "colA/colB/colC/colD (mixed match_parent row already AOSP-correct once weights stopped corrupting); colE/colF (clean 1:3 weight row)",
            "regression": REGRESSION,
            "honest_notes": HONEST + " scope: instance-field iput law (the static sput face is a named residual if any static float store shows the same bit-carrying pattern; no corpus caller today). perf1 checksums byte-identical proves the hot-path addition is behavior-neutral.",
        },
        "issue": "#364 CONT-99 T1",
    },
]

if dict_mode:
    for e in entries:
        roots[e["id"]] = e
else:
    root_list.extend(entries)

out = {"roots": root_list} if dict_mode else root_list
with open(PATH, "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
with open(MIRROR, "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(f"registry {n0} -> {n0 + len(entries)} roots (F-NEW-402..406 registered)")
