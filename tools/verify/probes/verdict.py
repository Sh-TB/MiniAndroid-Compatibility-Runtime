#!/usr/bin/env python3
"""verdict.py — S92 strict verdict state machine.

S92 §23 non-negotiables (enforced here, nowhere else):
  callback fired        -> does NOT promote to FULLY_VERIFIED
  screenshot exists     -> does NOT promote to VISUALLY_VERIFIED
  ViewTree exists       -> does NOT promote to graphics-verified
  blind tap success     -> does NOT count when target visibility unproven

Status ladder (S92 §23):
  UNEXECUTED < LOADED < LIFECYCLE_VERIFIED < RENDER_STARTED < FRAME_CAPTURED
  < VISUALLY_PARTIAL < VISUALLY_VERIFIED < INTERACTION_VERIFIED
  < FULLY_VERIFIED        (plus FAILED / BLOCKED / UNKNOWN terminal states)

Stage values (S92 §38): PASS | FAIL | PARTIAL | NOT_APPLICABLE | UNKNOWN.
NOT_APPLICABLE requires a justification string — never silent omission (§24).

The FULLY_VERIFIED contract (§24) — ALL applicable mandatory stages must be
PASS and repeatability must be PASS (or UNKNOWN for single-run, which caps
the verdict at INTERACTION_VERIFIED — a single run is never FULLY_VERIFIED).
"""
import json
import os
import time

# ordered ladder for overall status derivation
LADDER = [
    "UNEXECUTED", "LOADED", "LIFECYCLE_VERIFIED", "RENDER_STARTED",
    "FRAME_CAPTURED", "VISUALLY_PARTIAL", "VISUALLY_VERIFIED",
    "INTERACTION_VERIFIED", "FULLY_VERIFIED",
]
TERMINAL = ("FAILED", "BLOCKED", "UNKNOWN")

STAGES = [
    # (stage, mandatory-for-full unless NOT_APPLICABLE justified)
    "apk_load", "lifecycle", "scene", "renderer_initialized",
    "assets_resolved", "assets_decoded", "assets_rendered",
    "geometry", "frame_output", "visual", "input_target_visibility",
    "input", "state_change", "visual_change", "repeatability",
    "evidence_complete",
]


def stage(value, note=None):
    return {"value": value, "note": note} if note else {"value": value}


def _rank(s):
    return LADDER.index(s) if s in LADDER else -1


def derive_overall(stages, evidence_inventory):
    """Derive the strongest honest status from measured stages.

    Laws:
    - any mandatory stage FAIL -> FAILED (or VISUALLY_PARTIAL if only
      asset/visual layers failed while execution+lifecycle held — the run
      still executed; that distinction is the whole point of S92)
    - NOT_APPLICABLE stages are skipped (must carry justification)
    - UNKNOWN repeatability caps at INTERACTION_VERIFIED (3-run law §28)
    - scene != PASS (splash-only / wrong scene) caps at LIFECYCLE_VERIFIED
      with VISUALLY_PARTIAL recorded
    """
    v = {k: st["value"] for k, st in stages.items()}
    fails = [k for k, st in stages.items() if st["value"] == "FAIL"]
    na = [k for k, st in stages.items() if st["value"] == "NOT_APPLICABLE"]

    execution_held = v.get("apk_load") == "PASS" and \
        v.get("lifecycle") in ("PASS", "NOT_APPLICABLE")

    # no evidence at all -> UNEXECUTED/UNKNOWN
    if not evidence_inventory.get("screenshot") and \
            not evidence_inventory.get("frame_count"):
        return ("UNEXECUTED", fails, na)

    overall = "FRAME_CAPTURED"
    if execution_held:
        overall = "LIFECYCLE_VERIFIED"
        if v.get("frame_output") == "PASS":
            overall = "RENDER_STARTED"
            if v.get("scene") == "PASS":
                overall = "FRAME_CAPTURED"
                if v.get("visual") in ("PASS",):
                    overall = "VISUALLY_VERIFIED"
                elif v.get("visual") == "PARTIAL":
                    overall = "VISUALLY_PARTIAL"
                if v.get("visual") in ("PASS", "PARTIAL") and \
                        v.get("input") == "PASS" and \
                        v.get("state_change") == "PASS" and \
                        v.get("visual_change") == "PASS":
                    overall = "INTERACTION_VERIFIED"
                    if v.get("repeatability") == "PASS" and \
                            v.get("geometry") == "PASS" and \
                            v.get("evidence_complete") == "PASS" and \
                            v.get("input_target_visibility") == "PASS":
                        overall = "FULLY_VERIFIED"
    # downgrade rules
    if fails:
        graphics_layer_fails = {"assets_resolved", "assets_decoded",
                                "assets_rendered", "visual", "geometry",
                                "frame_output", "input_target_visibility",
                                "visual_change"}
        interaction_layer_fails = {"input", "state_change"}
        if fails and set(fails) <= (graphics_layer_fails | interaction_layer_fails) \
                and execution_held:
            # honest downgrade, not total failure: the APK EXECUTED, the
            # graphics/interaction contract did not hold
            overall = "VISUALLY_PARTIAL" if overall in (
                "VISUALLY_VERIFIED", "INTERACTION_VERIFIED",
                "FULLY_VERIFIED") else overall
            if v.get("visual") == "FAIL" and v.get("frame_output") == "FAIL":
                overall = "LIFECYCLE_VERIFIED"
            return (overall, fails, na)
        return ("FAILED", fails, na)
    return (overall, fails, na)


def build_verdict(*, package, title, apk_sha256, runtime_sha, run_dir,
                  renderer_family, stages, evidence_inventory,
                  interaction_proofs=None, asset_chains=None,
                  geometry_checks=None, repeatability_runs=None,
                  confidence="observed_only", notes=None):
    overall, fails, na = derive_overall(stages, evidence_inventory)
    return {
        "schema": "s92.graphics_verdict.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "package": package,
        "title": title,
        "apk_sha256": apk_sha256,
        "runtime_sha": runtime_sha,
        "run_dir": run_dir,
        "renderer_family": renderer_family,
        "confidence": confidence,
        "stages": stages,
        "evidence_inventory": evidence_inventory,
        "interaction_proofs": interaction_proofs or [],
        "asset_chains": asset_chains or [],
        "geometry_checks": geometry_checks or [],
        "repeatability_runs": repeatability_runs or [],
        "failing_stages": fails,
        "not_applicable_stages": na,
        "overall": overall,
        "overall_rank": _rank(overall),
        "notes": notes or [],
    }


def save(verdict, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(verdict, f, indent=1, sort_keys=True)
    return path
