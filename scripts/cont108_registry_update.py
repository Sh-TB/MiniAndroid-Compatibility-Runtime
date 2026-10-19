#!/usr/bin/env python3
"""CONT-108 registry update: F-NEW-451 closed via F-NEW-453; F-NEW-453 new."""
import json

MAIN = "canonical/root_cause_registry.json"
MIRROR = "canonical/root_cause_registry.json"  # same file: canonical IS the mirror target name used by prior waves

reg = json.load(open(MAIN))
if isinstance(reg, dict):
    roots = reg["roots"]
else:
    roots = reg

ids = {r.get("id") for r in roots}
assert "F-NEW-451" in ids and "F-NEW-453" not in ids

now = "2026-10-19"
for r in roots:
    if r.get("id") == "F-NEW-451":
        r["status"] = "ROOT-CAUSED-FIXED"
        r["root_cause"] = (
            "DOWNSTREAM DECODE COMPLETE (CONT-108). The keypad-only/blank face under "
            "AOSP-true umanoPanelHeight (F-NEW-450, 41dp->108px) was NOT a text/drawable "
            "law: the app-bundled androidx ConstraintLayout solver writes a DEGENERATE "
            "setMeasuredDimension(0,0) on the engine for EVERY incoming spec ([F453-SMD] "
            "probe: 20 writes all 0x0, incl. EXACTLY 1080x1421; byte-identical behavior on "
            "the pre-107 binary). The SlidingUpPanelLayout fork (Kotlin rewrite with "
            "LayoutWeightParams) then laid BOTH children at identical zero-size rects "
            "([F453-LAY]: keypad rect=(0,108 0,108), panel rect=(0,108 0,108) — top=d(t), "
            "bottom=top+measured=0) and its coverage law i() ('hide the main content when "
            "the panel rect covers it') compared two IDENTICAL degenerate rects -> "
            "coverage TRUE -> child0.setVisibility(INVISIBLE) ([P1-1-VIS] view=738 0->4) "
            "-> the render walk prunes the INVISIBLE subtree (F-NEW-168) -> blank face. "
            "Pre-107 the same degenerate geometry existed but d(t)=10497 kept the rects "
            "outside the compared band order and the render walk's EXP-095 heuristic "
            "measure re-derived real keypad geometry (48-node tree with full keypad), "
            "masking the disease; F-450's correct 108px collapsed d(t) to 108, flipping "
            "the coverage test and un-masking it. First-divergence marker from CONT-107 "
            "(MainActivity.getDrawable 0x7f08007f below_shadow not reached + object-id "
            "shift) is a downstream symptom of the same degenerate pass, not the root."
        )
        r["fix"] = (
            "F-NEW-453 (this wave): (1) degenerate self-report gate in the engine measure "
            "bridge — a DEX chain whose total write is 0x0 while the incoming spec is "
            "EXACTLY(w,h) w,h>0 on a VISIBLE MATCH_PARENT ViewGroup routes to the "
            "R-NEW-440 canonical container law (AOSP CL-anchor law) instead of honoring "
            "the ART-impossible write; (2) canonical answers that are themselves 0x0 "
            "under a demanding spec fall through to the EXACTLY default law (spec size) "
            "instead of committing a poisoned dex_measured store; (3) at the R-NEW-438 "
            "native takeover the stale degenerate dex_measured/valid store is "
            "invalidated so DEX getMeasuredWidth/Height readbacks consume the "
            "authoritative native result. Probe-free final binary cac0ee70d8c951b4: "
            "opencalc face 13d2d6d836f75e7f -> d5f3c7b5e9936ae6 = FULL KEYPAD rendered "
            "(AC..= grid + digits + icons), WANT re-pinned x3 with adjudication."
        )
        r["evidence"] = (
            "run/c108/ (oc_probe, oc_probe2, oc_probe3, oc_fix1, oc_fix2, oc_pre_probe, "
            "oc_pre_probe2 = pre/post A/B with [F453-SMD]/[F453-LAY]/[F453-MEASURE] "
            "decode probes + androguard disassembly scripts c108_scan_*.py + "
            "run/c108/oc_supl_onmeasure_v2.txt onMeasure/onLayout/i()/h() decode + "
            "oc_mainactivity_scan.txt + oc_getdrawable_all.txt + res/9t.xml umano attrs "
            "41dp + res/MB.xml below_shadow decode); battery: "
            "evidence/cont108/evidence.json"
        )
        r["verified_current"] = (
            "at binary cac0ee70d8c951b4 (probe-free): wall 11 rows x3 = 33/33 MATCH "
            "(opencalc d5f3c7b5e9936ae6 re-pinned; tanana afe0bd8d->10174486 IMPROVEMENT "
            "re-pinned: the grey-200 fill face now renders the real notification-settings "
            "preference text; csw d3c26b73->5c4a0172 build-lineage face flip bracketed to "
            "be fix-independent: prewt@44bbcb21+probes (no CONT-108 fix code) reproduces "
            "5c4a0172 — F-NEW-443 build-lineage precedent, compose draw frontier stays "
            "the named open gap) + goldens 4/4 + gatea negatives/reinstall rc=0 + "
            "MG-310 7/7 + MG-150 3/3 + selftest 13/13 + F-376 70/70 + probes c106a "
            "([F447-NPE] parity) / c106b2 dim=147 / c106b 11/11 / c104i 4/4 / c74esc "
            "5/5 all terminal"
        )
        r["date"] = now

new_root = {
    "id": "F-NEW-453",
    "title": "Degenerate DEX self-report (setMeasuredDimension(0,0)) survives the DEX readback and poisons umano/coverage layout laws",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0-CRITICAL",
    "layer": "VIEW",
    "date": now,
    "root_cause": (
        "AOSP View.measure contract (View.java): a MATCH_PARENT view measured under "
        "EXACTLY(w,h) MUST report (w,h); nothing in a completed onMeasure chain may "
        "report 0x0 under a positive EXACTLY spec. On the engine the app-bundled "
        "androidx ConstraintLayout solver (and other library containers) write "
        "setMeasuredDimension(0,0) for every spec (interpreter emulation of the solver "
        "is incomplete — zero child measure dispatches observed before the write). Two "
        "propagation legs made the poison visible: (a) the R347 DEX-measure path "
        "honored the write as valid; (b) the DEX getMeasuredWidth/Height readback "
        "shadow prefers dex_measured_* — so containers that READ their children's "
        "measured sizes (the SlidingUpPanelLayout fork's onLayout, i() coverage law) "
        "consumed degenerate geometry even where the native R-NEW-438 takeover had "
        "already fixed measured_*. The write-through law itself (R-NEW-347 one-store) "
        "is correct ART semantics; the gap is that a degenerate self-report was treated "
        "as authoritative instead of as incomplete emulation."
    ),
    "fix": (
        "Three-part law at binary cac0ee70d8c951b4: (1) F453-degenerate gate in the "
        "engine measure bridge — dex_measure_valid && 0x0 && EXACTLY>0 both axes && "
        "VISIBLE && MATCH_PARENT/unset lp => route to the R-NEW-440 canonical container "
        "law (measure_view_spec) instead of honoring the write; (2) canonical answers "
        "that are themselves 0x0 under a demanding spec are not committed — fall "
        "through to the EXACTLY default law (spec size); (3) at the R-NEW-438 native "
        "takeover the stale degenerate dex_measured/valid store is invalidated "
        "(dex_measure_valid=false) so DEX readbacks consume the authoritative native "
        "result. Legit EXACTLY-0 specs, GONE nodes, wrap-content containers and "
        "genuine custom views (compose F10, dooz23) keep their DEX answers."
    ),
    "evidence": (
        "A/B decode chain run/c108/: [F453-SMD] (solver writes 0x0 x20 incl. EXACTLY "
        "1080x1421, byte-identical pre/post), [F453-LAY] (fork lays both children at "
        "identical zero-size rects (0,108 0,108) post vs (0,10497 0,10497) pre), "
        "[P1-1-VIS] view=738 0->4 INVISIBLE at the fork's i() coverage law; androguard "
        "disassembly of SlidingUpPanelLayout onMeasure/onLayout/i()/h() + res/9t.xml "
        "umanoPanelHeight=41dp + res/Bu.xml display_background. Fix A/B: oc_fix1 "
        "(partial: bridge only — keypad 1080x1313 measured but layout still consumed "
        "stale 0) -> oc_fix2 (complete: full keypad face d5f3c7b5e9936ae6). Battery: "
        "evidence/cont108/evidence.json; WANT adjudications csw/tanana/opencalc in "
        "scripts/cont70_gate.sh."
    ),
    "verified_current": (
        "at binary cac0ee70d8c951b4 (probe-free rebuild): full battery green — wall 11 "
        "rows x3 33/33 MATCH, goldens 4/4, gatea negatives+reinstall rc=0, MG-310 7/7, "
        "MG-150 3/3, selftest 13/13, F-NEW-376 70/70, probes c106a/b2/b + c104i 4/4 + "
        "c74esc 5/5 terminal; opencalc keypad face restored; tanana settings text "
        "improvement; csw flip bracketed fix-independent"
    ),
    "verified_current_binary": "cac0ee70d8c951b4",
    "affected_apks": "opencalculator_53 (face fixed), tananaev.calculator_11 (content improvement), corpus class: app-bundled androidx containers",
    "fanout": "P0-HIGH",
}
roots.append(new_root)

ids2 = [r.get("id") for r in roots]
assert len(ids2) == len(set(ids2)), "id collision"
out = {"roots": roots} if isinstance(reg, dict) else roots
if isinstance(reg, dict):
    reg["roots"] = roots
json.dump(reg, open(MAIN, "w"), ensure_ascii=False, indent=1)
print("registry roots:", len(roots))
