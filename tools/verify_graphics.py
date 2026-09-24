#!/usr/bin/env python3
"""verify_graphics.py — S92 graphics-verification orchestrator.

Consumes ONLY real runtime evidence + the APK + an optional visual
contract, runs the probe suite, and emits a strict verdict.json
(S92 §23/§24/§38). It can also SELF-TEST (§40): feed it deliberately
defective evidence and require rejection before it may be trusted.

Usage:
  python3 tools/verify_graphics.py verify-run --run-dir DIR --apk APK \
      [--contract registry/visual_contracts/P.json] \
      [--package P] [--title T] [--runtime-sha SHA] \
      [--out registry/graphics_verdicts/P@sha8.json]

  python3 tools/verify_graphics.py selftest --run-dir GOOD_RUN --apk APK
      -> runs the §40 rejection battery on doctored copies of GOOD_RUN;
         exits nonzero unless ALL defective variants are REJECTED.
"""
import argparse
import copy
import json
import os
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))

from tools.verify.probes import asset_probe as ap_              # noqa: E402
from tools.verify.probes import geometry_probe as gp            # noqa: E402
from tools.verify.probes import graphics_common as gc           # noqa: E402
from tools.verify.probes import interaction_probe as ip         # noqa: E402
from tools.verify.probes import visual_probe as vp              # noqa: E402
from tools.verify.probes import verdict as vd                   # noqa: E402


# ---------------------------------------------------------------------------
# core verification of ONE run
# ---------------------------------------------------------------------------

def verify_run(run_dir, apk_path, contract=None, package=None, title=None,
               runtime_sha=None, out_path=None, quiet=False):
    re_ = gc.RunEvidence(run_dir)
    if not re_.exists:
        v = {"overall": "UNEXECUTED",
             "note": f"run dir missing: {run_dir}"}
        return v
    nodes = gc.view_nodes(re_.view_tree)
    family, signals = gc.classify_renderer_family(nodes, re_.provenance,
                                                  re_.report_json)
    package = package or (re_.report_json or {}).get("package") or \
        (contract or {}).get("package") or "unknown"
    title = title or (contract or {}).get("title") or package
    apk_sha = gc.sha256_file(apk_path) if apk_path and \
        os.path.isfile(apk_path) else None
    inv = re_.evidence_inventory()

    stages = {}
    notes = []

    # --- execution / lifecycle ---------------------------------------------
    rc = (re_.report_json or {}).get("exit_code")
    app_classes = [n.get("class") for n in nodes
                   if n.get("class") and not
                   n.get("class", "").startswith(("Landroid/", "Ljava/",
                                                  "Landroidx/", "Lkotlin"))]
    # lifecycle evidence: the app inflated a UI (ViewTree non-empty) and at
    # least one frame rendered. Apps built purely on framework views have no
    # app-owned view classes — that is NOT a lifecycle failure.
    lifecycle_ok = bool(nodes) and (
        bool(re_.screenshot) or bool(re_.frames))
    lifecycle_note = None
    if not lifecycle_ok:
        lifecycle_note = ("no ViewTree / no frames — activity never "
                          "inflated a UI")
    elif not app_classes:
        lifecycle_note = ("framework-view-only UI (no app-owned view "
                          "classes); lifecycle from inflation + frames")
    stages["apk_load"] = vd.stage("PASS" if apk_sha or re_.screenshot
                                  else "FAIL")
    stages["lifecycle"] = vd.stage(
        "PASS" if lifecycle_ok else "FAIL", lifecycle_note)

    # --- scene (§13) --------------------------------------------------------
    fq = None
    if re_.screenshot:
        fq = gp.frame_quality(re_.screenshot)
        # S92 §13 law: BLANK/splash-only/nearly-blank FAILS the scene gate;
        # SPARSE content is legitimate for minimal apps (recorded as note,
        # the deeper truth lives in the asset/geometry/interaction stages).
        cls = fq.get("class")
        scene_val = "FAIL" if cls == "BLANK_OR_NEARLY_BLANK" else "PASS"
        stages["scene"] = vd.stage(scene_val, f"screenshot class={cls}")
    else:
        stages["scene"] = vd.stage("FAIL", "no screenshot captured")

    # --- renderer init / frame output ---------------------------------------
    prov = re_.provenance or {}
    gl_events = [e for e in prov.get("events", [])
                 if e.get("origin") == "glsurfaceview-frame"]
    canvas_events = [e for e in prov.get("events", [])
                     if e.get("origin", "").startswith("canvas")]
    img_events = [e for e in prov.get("events", [])
                  if e.get("origin") and
                  e.get("origin") != "glsurfaceview-frame"]
    frame_output_na = False
    if gl_events:
        stages["renderer_initialized"] = vd.stage(
            "PASS", "GLSurfaceView frame chain present")
        presented = all(e.get("BUFFER_PRESENTED") for e in gl_events)
        stages["frame_output"] = vd.stage("PASS" if presented else "FAIL")
    elif fq and fq.get("non_background_frac", 0) > 0.005:
        stages["renderer_initialized"] = vd.stage(
            "PASS", f"family={family}; signals={signals}")
        stages["frame_output"] = vd.stage("PASS")
    elif img_events or canvas_events:
        stages["renderer_initialized"] = vd.stage(
            "PASS", f"family={family}; draw events recorded")
        # draw events but blank frame -> RENDER_OUTPUT_FAIL (§14)
        stages["frame_output"] = vd.stage(
            "FAIL", "draw events recorded but frame blank/absent")
    else:
        stages["renderer_initialized"] = vd.stage(
            "UNKNOWN", f"no provenance events; family={family}")
        stages["frame_output"] = vd.stage(
            "PASS" if (fq and fq.get("class") != "BLANK_OR_NEARLY_BLANK")
            else "FAIL")

    # --- asset chains (§4/§6) ------------------------------------------------
    chains, asset_rollup = ap_.asset_chains(apk_path, contract, re_, run_dir)
    for k in ("assets_resolved", "assets_decoded", "assets_rendered"):
        st = asset_rollup[k]
        stages[k] = vd.stage(st["value"], st.get("note"))

    # --- geometry (§7) --------------------------------------------------------
    geom_results, geom_rollup, geom_counts = gp.check_geometry(
        re_.view_tree, contract)
    stages["geometry"] = vd.stage(geom_rollup)
    if re_.screenshot:
        pres_checks = [c for c in chains if c.get("PIXELS_FOUND") in
                       ("PASS", "PARTIAL", "FAIL")]
        tri = gp.triangulate(
            view_tree_ok=bool(nodes),
            pixels_ok=any(c.get("PIXELS_FOUND") == "PASS"
                          for c in pres_checks),
            provenance_ok=bool(img_events or canvas_events or gl_events))
    else:
        tri = "NO_EVIDENCE"

    # --- overall visual (asset + geometry + frame triangulated) --------------
    asset_vals = [stages[k]["value"] for k in
                  ("assets_resolved", "assets_decoded", "assets_rendered")]
    has_asset_contract = any(v != "NOT_APPLICABLE" for v in asset_vals)
    if "FAIL" in asset_vals or geom_rollup == "FAIL":
        visual_val = "FAIL"
    elif "PARTIAL" in asset_vals or geom_rollup == "PARTIAL":
        visual_val = "PARTIAL"
    elif not has_asset_contract and geom_rollup == "NOT_APPLICABLE":
        # no asset/geometry contract: lean on frame output + triangulation,
        # never on "screenshot exists" alone (S92 0.2 law)
        visual_val = "PASS" if stages["frame_output"]["value"] == "PASS" \
            and tri != "RENDER_OUTPUT_FAIL" else "FAIL"
    else:
        visual_val = "PASS" if stages["scene"]["value"] == "PASS" else "FAIL"
    stages["visual"] = vd.stage(visual_val)

    # --- interaction (§10/§11) ----------------------------------------------
    targets = (contract or {}).get("interaction_targets", [])
    proofs = ip.interaction_proofs(re_, contracts_targets=targets)
    if proofs:
        unverified = [p for p in proofs
                      if p["verdict"] == "INTERACTION_TARGET_UNVERIFIED"]
        proven = [p for p in proofs
                  if p["verdict"] == "INTERACTION_VISUALLY_PROVEN"]
        nochg = [p for p in proofs
                 if p["verdict"] == "INTERACTION_NO_VISUAL_CHANGE"]
        if unverified and not proven:
            stages["input_target_visibility"] = vd.stage(
                "FAIL", "blind tap on unproven target (S92 §10 law)")
            stages["input"] = vd.stage("PARTIAL",
                                       "dispatch recorded but target "
                                       "unverified")
            stages["state_change"] = vd.stage("UNKNOWN")
            stages["visual_change"] = vd.stage("FAIL")
        else:
            stages["input_target_visibility"] = vd.stage(
                "PASS" if not unverified else "PARTIAL")
            stages["input"] = vd.stage("PASS" if (proven or nochg)
                                       else "FAIL")
            stages["state_change"] = vd.stage(
                "PASS" if proven or nochg else "UNKNOWN",
                "runtime frames manifest records dispatch+state"
                if proven or nochg else None)
            stages["visual_change"] = vd.stage(
                "PASS" if proven else
                ("FAIL" if nochg and not proven else "UNKNOWN"))
    else:
        for k in ("input_target_visibility", "input", "state_change",
                  "visual_change"):
            interactive = _has_interactive_target(targets, nodes)
            stages[k] = vd.stage(
                "NOT_APPLICABLE" if not interactive else "UNKNOWN",
                None if not interactive else
                "run drove no interaction; interactive targets exist")

    # --- repeatability (§28) --------------------------------------------------
    stages["repeatability"] = vd.stage(
        "UNKNOWN", "single run; 3-run law not yet applied")

    # --- evidence completeness (§39) ------------------------------------------
    required_ev = ["screenshot", "view_tree"]
    complete = all(inv.get(k) for k in required_ev)
    stages["evidence_complete"] = vd.stage(
        "PASS" if complete else "PARTIAL",
        None if complete else f"missing evidence: "
        f"{[k for k in required_ev if not inv.get(k)]}")

    verdict = vd.build_verdict(
        package=package, title=title, apk_sha256=apk_sha or "",
        runtime_sha=runtime_sha or "", run_dir=run_dir,
        renderer_family=family, stages=stages, evidence_inventory=inv,
        interaction_proofs=proofs, asset_chains=chains,
        geometry_checks=geom_results, confidence=(contract or {}).get(
            "confidence", "observed_only"),
        notes=notes + [{"frame_quality": fq, "triangulation": tri,
                        "renderer_signals": signals}] if notes else
        [{"frame_quality": fq, "triangulation": tri,
          "renderer_signals": signals}])

    if out_path:
        vd.save(verdict, out_path)
    if not quiet:
        print(json.dumps({
            "package": verdict["package"],
            "overall": verdict["overall"],
            "failing_stages": verdict["failing_stages"],
            "family": family,
        }, indent=1))
    return verdict


def _has_interactive_target(targets, nodes):
    if targets:
        return True
    return bool(gc.clickable_nodes(nodes))


# ---------------------------------------------------------------------------
# §40 self-test battery — the verifier must REJECT known-bad evidence
# ---------------------------------------------------------------------------

def _make_defect_run(good_run, tmp, defect):
    """Create a doctored copy of a good run with one deliberate defect."""
    d = os.path.join(tmp, defect)
    shutil.copytree(good_run, d)
    shot = os.path.join(d, "screenshot.png")
    im = Image.open(shot).convert("RGB")
    A = np.asarray(im).copy()

    if defect == "blanked_asset_region":
        # case: image drawn-but-not-presented / decoded-but-not-drawn —
        # the target region of the FIRST ImageView-like node is wiped
        vt = gc.load_json(os.path.join(d, "view_tree.json")) or {}
        nodes = gc.view_nodes(vt)
        target = None
        for n in nodes:
            if n.get("image_resource_id") or "ImageView" in n.get("class", ""):
                target = n
                break
        if target is None and nodes:
            target = nodes[-1]
        x, y, w, h = gc.node_bounds(target)
        A[max(0, y):y + h, max(0, x):x + w] = 255
    elif defect == "shifted_geometry":
        # case B: icon rendered at wrong coordinates — bounds shifted in
        # the evidence the verifier relies on
        vt = gc.load_json(os.path.join(d, "view_tree.json")) or {}
        for n in gc.view_nodes(vt):
            if n.get("width", 0) > 0:
                n["x"] = n.get("x", 0) + 240
        with open(os.path.join(d, "view_tree.json"), "w") as f:
            json.dump(vt, f)
        with open(shot, "wb") as f:
            Image.fromarray(A).save(f, "PNG")
        return d
    elif defect == "blind_tap_no_target":
        # case A/E: manifest claims a click dispatched, ViewTree target
        # is INVISIBLE (visibility=2) -> §10 must reject
        vt = gc.load_json(os.path.join(d, "view_tree.json")) or {}
        for n in gc.view_nodes(vt):
            if n.get("clickable") or n.get("has_click_listener"):
                n["visibility"] = 2
        with open(os.path.join(d, "view_tree.json"), "w") as f:
            json.dump(vt, f)
        fdir = os.path.join(d, "frames")
        if os.path.isdir(fdir):
            mf = os.path.join(fdir, "manifest.json")
            if os.path.isfile(mf):
                with open(mf) as fh:
                    man = json.load(fh)
                for ent in (man.get("frames") or
                            man.get("interactions") or []):
                    ent["dispatched"] = True
                with open(mf, "w") as fh:
                    json.dump(man, fh)
        with open(shot, "wb") as f:
            Image.fromarray(A).save(f, "PNG")
        return d
    else:
        raise SystemExit(f"unknown defect {defect}")
    with open(shot, "wb") as f:
        Image.fromarray(A).save(f, "PNG")
    return d


def selftest(good_run, apk_path, contract=None, package=None):
    """§40: verifier must PASS the good run and REJECT every defect.
    Returns dict; exits nonzero on failure of the battery itself."""
    results = {}
    good = verify_run(good_run, apk_path, contract=contract,
                      package=package, quiet=True)
    results["good_run_overall"] = good.get("overall")
    results["good_run_accepted"] = str(good.get("overall")) in (
        "VISUALLY_VERIFIED", "INTERACTION_VERIFIED", "FULLY_VERIFIED",
        "VISUALLY_PARTIAL")
    rejects = {}
    with tempfile.TemporaryDirectory(prefix="s92_selftest_") as tmp:
        for defect in ("blanked_asset_region", "shifted_geometry",
                       "blind_tap_no_target"):
            d = _make_defect_run(good_run, tmp, defect)
            c2 = contract
            if defect == "shifted_geometry":
                # geometry check needs contract with expected bounds;
                # build observed contract from the GOOD run so the defect
                # shows as a delta
                c2 = contract or _observed_contract(good_run, apk_path,
                                                    package)
            v = verify_run(d, apk_path, contract=c2, package=package,
                           quiet=True)
            rejected = v.get("overall") in ("VISUALLY_PARTIAL", "FAILED") \
                or bool(v.get("failing_stages"))
            rejects[defect] = {
                "overall": v.get("overall"),
                "failing_stages": v.get("failing_stages"),
                "REJECTED": bool(rejected)}
    results["reject_battery"] = rejects
    results["ALL_REJECTED"] = all(r["REJECTED"] for r in rejects.values())
    results["BATTERY_OK"] = bool(results["ALL_REJECTED"])
    print(json.dumps(results, indent=1))
    return results


def _observed_contract(good_run, apk_path, package):
    sys.path.insert(0, REPO)
    from tools.build_visual_contract import build_contract
    return build_contract(apk_path, package or "selftest", package or
                          "selftest", run_dir=good_run)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    vr = sub.add_parser("verify-run")
    vr.add_argument("--run-dir", required=True)
    vr.add_argument("--apk", required=True)
    vr.add_argument("--contract", default=None)
    vr.add_argument("--package", default=None)
    vr.add_argument("--title", default=None)
    vr.add_argument("--runtime-sha", default=None)
    vr.add_argument("--out", default=None)
    st = sub.add_parser("selftest")
    st.add_argument("--run-dir", required=True)
    st.add_argument("--apk", required=True)
    st.add_argument("--contract", default=None)
    st.add_argument("--package", default=None)
    a = p.parse_args()
    contract = gc.load_json(a.contract) if a.contract else None
    if a.cmd == "verify-run":
        verify_run(a.run_dir, a.apk, contract=contract,
                   package=a.package, title=a.title,
                   runtime_sha=a.runtime_sha, out_path=a.out)
    else:
        res = selftest(a.run_dir, a.apk, contract=contract,
                       package=a.package)
        sys.exit(0 if res.get("BATTERY_OK") else 2)


if __name__ == "__main__":
    main()
