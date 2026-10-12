#!/usr/bin/env python3
"""cont52_registry.py — CONT-52 registry update (634 -> 635).

F-NEW-324: ROOT-CAUSED-FIXED — the super-dispatch BOUNDARY law: when the
declaring class of an invoke-super is a DEX-defined INTERMEDIATE that does
not define the method (NavigationView.onMeasure → invoke-super f.onMeasure
where f = ScrimInsetsFrameLayout is a DEX class with NO onMeasure whose
super is the FrameLayout boundary), the bridge received the DEX declaring
class name and every shadow keyed by a framework name silently missed —
the FrameLayout.onMeasure measure law never ran, setMeasuredDimension was
never reached, and the engine recorded [DEX-MEASURE] NavigationView.onMeasure
"FAILED(no write-back)" on every pass → the drawer menu measured 0x0.
Also refreshes the F-NEW-309 next_wave frontier: with the bridge now firing,
the upstream divergence is the child spec the DrawerLayout measure chain
hands NavigationView (wspec=0x0/hspec=0x0 at the R347-MEASURE face).
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-324" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 634, f"expected 634 roots, got {len(roots)}"

for r in roots:
    if r["id"] == "F-NEW-309":
        r["next_wave"] = (
            "CONT-52 UPDATE (binary b5998a50a679c2e3, HEAD 67c537b0): the "
            "NavigationView.onMeasure FAILED(no write-back) face is "
            "ROOT-CAUSED and FIXED as F-NEW-324 — the invoke-super bridge "
            "received the DEX declaring class (f = ScrimInsetsFrameLayout, "
            "a DEX class with no onMeasure whose super is the FrameLayout "
            "boundary) so the FrameLayout.onMeasure measure law never ran; "
            "the fix walks the DEX superclass chain to the first NON-DEX "
            "ancestor and passes THAT boundary class to the bridge (the "
            "R-NEW-345 framework-declaring case untouched). Probe "
            "fnew324_probe (4f06d7f711067013): PRE face = [DEX-MEASURE] "
            "Leaf.onMeasure FAILED(no write-back) + the Leaf FrameLayout "
            "bridge 0 rows (P1's value face was masked by the View.measure "
            "fallback — the honest judgment surface is the bridge-log "
            "face); POST = S109-VG-MEASURE FrameLayout children_measured=1 "
            "for the DEX-intermediate leaf x3, rows 3/0 x3. Solitaire POST: "
            "the FrameLayout bridge now executes FOR the NavigationView "
            "receiver (obj#298, children_measured=1); NEW first divergence "
            "recorded for the next wave: the measure chain UPSTREAM of the "
            "NavigationView hands it spec 0x0/0x0 (R347-MEASURE view=298 "
            "wspec=0x0 hspec=0x0) — the DrawerLayout child-spec computation "
            "(NavigationView LP width/height as seen by DEX) is the decode; "
            "frame verdict still DEFAULT_BACKGROUND_ONLY / APP_PIXELS."
        )
        r["evidence"] = ("evidence/cont49/CONT49_RESULT.md; evidence/cont50/CONT50_RESULT.md; "
                         "evidence/cont51/CONT51_RESULT.md; evidence/cont52/CONT52_RESULT.md")

roots.append({
    "id": "F-NEW-324",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "The invoke-super BOUNDARY law: when the declaring class is a DEX-defined INTERMEDIATE that does not define the method, the bridge received the DEX declaring class name and every shadow keyed by a framework name silently missed. Solitaire face: NavigationView.onMeasure (DEX) does invoke-super f.onMeasure where f = ScrimInsetsFrameLayout is a DEX class with NO onMeasure whose super is FrameLayout — the FrameLayout.onMeasure measure law never ran, setMeasuredDimension was never reached, and the engine recorded [DEX-MEASURE] NavigationView.onMeasure 'FAILED(no write-back)' on EVERY pass (3x in one run) → the NavigationView node never entered the render tree (drawer menu 0x0).",
    "root_cause": "ART/JVMS super resolution walks the receiver's class chain: a DEX intermediate without the method passes the resolution PAST the DEX chain onto the first FRAMEWORK ancestor. execute_invoke_super's bridge call passed declaring_class (the R-NEW-345 law: correct when the declaring class IS a framework class — RecyclerView.onMeasure's super → ViewGroup hits the bridge; wrong when the declaring class is a DEX intermediate — bridge class_name='Landroid/support/design/internal/f;' matches no shadow). PROBE-FIRST proof: fixtures/fnew324_probe (Leaf extends Mid [DEX, no onMeasure] extends FrameLayout) — PRE: [DEX-MEASURE] Leaf.onMeasure FAILED(no write-back) and the Leaf FrameLayout bridge executed 0 times (S109-VG-MEASURE rows: only the Direct control's LinearLayout bridge fired); the P1 value face (measured=100x60 PASS) is masked by the View.measure fallback — the bridge-log face is the honest judgment surface. FIX (minimal, generic, ART-faithful): in execute_invoke_super's bridge arm, when declaring_class is DEX-defined, walk superclass_of up to the FIRST non-DEX ancestor and pass THAT as the bridge class; framework declaring classes are untouched (P2 control face).",
    "next_wave": "Probe fnew324_probe APK 4f06d7f711067013: PRE = Leaf DEX-MEASURE FAILED(no write-back) + 0 FrameLayout bridge rows for the DEX-intermediate leaf; POST = S109-VG-MEASURE FrameLayout obj#13 spec=100x60 children_measured=1 (the super chain really ran through the DEX intermediate) x3, rows 3/0 x3. Solitaire POST: the FrameLayout bridge executes FOR the NavigationView receiver (obj#298 children_measured=1, spec faces 0x0/0x1920); zero-drift gate 33/33 anchors x3 + support x2 (BMI/alex/notes MATCH). NEW frontier recorded in the F-NEW-309 row: the upstream child-spec the DrawerLayout chain hands NavigationView (R347-MEASURE view=298 wspec=0x0 hspec=0x0).",
    "evidence": "evidence/cont52/CONT52_RESULT.md",
})

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

ids = {r["id"] for r in roots}
print(f"registry 634 -> {len(roots)} (F-NEW-324 appended ROOT-CAUSED-FIXED; F-NEW-309 next_wave refreshed)")
print("unique-ID check:", "OK" if len(ids) == len(roots) else "COLLISION")
