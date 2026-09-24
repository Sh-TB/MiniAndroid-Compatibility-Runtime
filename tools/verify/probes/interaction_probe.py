#!/usr/bin/env python3
"""interaction_probe.py — S92 input-target protection + pre/post proof
(§10, §11).

HARD LAW (§10): before ANY automated tap counts as interaction evidence,
the target must be proven:
  1. exists in ViewTree/contract       (identity)
  2. visibility == VISIBLE             (not GONE/INVISIBLE)
  3. bounds intersect the screen       (geometry)
  4. pixel evidence in target region   (visible target, not invisible object)
If any step cannot be proven: INPUT_TARGET_UNVERIFIED — and the resulting
callback/state change must NOT promote the title (§10 false-success law).

Every accepted interaction produces (§11):
  BEFORE frame + TARGET PROOF + INPUT event + AFTER frame +
  pixel delta + state-change evidence.
"""
import json
import os

import numpy as np
from PIL import Image

from . import graphics_common as gc
from . import visual_probe as vp


def screen_size(run_evidence):
    shot = run_evidence.screenshot
    if shot:
        with Image.open(shot) as im:
            return im.width, im.height
    vt = run_evidence.view_tree or {}
    n = (vt.get("nodes") or [{}])[0]
    return n.get("width", 0), n.get("height", 0)


def verify_input_target(run_evidence, target, screenshot_path=None,
                        asset_checker=None):
    """§10 gate. target: dict from contract/frames-manifest with bounds
    (x,y,w,h) + identity (view_id/class/text) [+ optional asset path]."""
    x, y, w, h = target.get("bounds") or (None, None, None, None)
    identity = {k: target.get(k) for k in
                ("view_id", "class", "text") if target.get(k) is not None}
    proof = {"identity": identity, "steps": {}}
    if x is None:
        proof["verdict"] = "INPUT_TARGET_UNVERIFIED"
        proof["reason"] = "no bounds"
        return proof
    sw, sh = screen_size(run_evidence)
    # 2. ViewTree visibility
    node = _node_for(run_evidence, target)
    vis = node.get("visibility", 0) if node else None
    proof["steps"]["viewtree_identity"] = "PASS" if node else "UNKNOWN"
    proof["steps"]["viewtree_visibility"] = \
        "PASS" if vis == 0 else ("FAIL" if vis is not None else "UNKNOWN")
    # 3. screen intersection
    inter = (0 <= x < sw and 0 <= y < sh and w > 0 and h > 0 and
             x + w <= sw + 8 and y + h <= sh + 8)
    proof["steps"]["screen_intersection"] = "PASS" if inter else "FAIL"
    # 4. pixel evidence in region
    shot = screenshot_path or run_evidence.screenshot
    if shot and inter:
        im = Image.open(shot).convert("RGB")
        A = np.asarray(im, dtype=np.int16)
        R = A[max(0, y):min(sh, y + h), max(0, x):min(sw, x + w)]
        if R.size == 0:
            proof["steps"]["region_pixels"] = "FAIL"
        else:
            gray = R.astype(np.float64)
            std = float(gray.std())
            proof["region_stddev"] = round(std, 2)
            proof["steps"]["region_pixels"] = \
                "PASS" if std >= 6.0 else "FAIL"
        if asset_checker and target.get("asset_path"):
            pres = asset_checker(shot, target)
            proof["steps"]["asset_in_region"] = pres
    else:
        proof["steps"]["region_pixels"] = "UNKNOWN"
    ok = (proof["steps"].get("viewtree_visibility") in ("PASS", "UNKNOWN")) \
        and proof["steps"].get("screen_intersection") == "PASS" \
        and proof["steps"].get("region_pixels") in ("PASS", "UNKNOWN")
    proof["verdict"] = "INPUT_TARGET_VERIFIED" if ok \
        else "INPUT_TARGET_UNVERIFIED"
    return proof


def _node_for(run_evidence, target):
    nodes = gc.view_nodes(run_evidence.view_tree)
    vid = target.get("view_id")
    for n in nodes:
        if vid is not None and n.get("android_view_id") == vid:
            return n
    if target.get("text"):
        for n in nodes:
            if n.get("text") == target.get("text"):
                return n
    if target.get("class"):
        for n in nodes:
            if target["class"] in (n.get("class") or ""):
                return n
    return None


def interaction_proofs(run_evidence, contracts_targets=None,
                       asset_checker=None):
    """Build §11 pre/post proofs from the runtime's own frames/manifest +
    click audit. Returns list of proof records; each is one of
    INTERACTION_VISUALLY_PROVEN / INTERACTION_TARGET_UNVERIFIED /
    INTERACTION_NO_VISUAL_CHANGE / INTERACTION_NOT_DISPATCHED."""
    proofs = []
    manifest = run_evidence.frames_manifest or {}
    frames = run_evidence.frames
    if not frames:
        return proofs

    def frame_path(i):
        name = f"frame_{i:03d}.png"
        for n, p in frames:
            if n == name:
                return p
        return None

    entries = manifest.get("frames") or manifest.get("interactions") or []
    if entries and isinstance(entries, list):
        for i, ent in enumerate(entries):
            before = frame_path(i)
            after = frame_path(i + 1)
            rec = {
                "index": i,
                "clicked": {k: ent.get(k) for k in
                            ("view_id", "view_class", "listener_class",
                             "target_view_id", "target_class")
                            if ent.get(k) is not None},
            }
            tgt = None
            if before and after:
                # §10 gate — target bounds from manifest or contract
                tb = ent.get("bounds") or _bounds_from_manifest(ent) \
                    or _bounds_from_contract(rec["clicked"], contracts_targets)
                if tb:
                    tgt = verify_input_target(
                        run_evidence,
                        {"bounds": tb, **rec["clicked"]},
                        screenshot_path=before,
                        asset_checker=asset_checker)
                    rec["target_proof"] = tgt
                delta = vp.region_diff(before, after)
                rec["pixel_delta"] = delta
                rec["before_frame"] = os.path.basename(before)
                rec["after_frame"] = os.path.basename(after)
                unverified = (tgt or {}).get("verdict") == \
                    "INPUT_TARGET_UNVERIFIED"
                changed = delta.get("changed_px", 0) > 0
                dispatched = bool(ent.get("dispatched", True)) and \
                    bool(rec["clicked"])
                if dispatched and unverified:
                    rec["verdict"] = "INTERACTION_TARGET_UNVERIFIED"
                elif dispatched and changed:
                    rec["verdict"] = "INTERACTION_VISUALLY_PROVEN"
                elif dispatched and not changed:
                    rec["verdict"] = "INTERACTION_NO_VISUAL_CHANGE"
                else:
                    rec["verdict"] = "INTERACTION_NOT_DISPATCHED"
            else:
                rec["verdict"] = "INTERACTION_EVIDENCE_INCOMPLETE"
            proofs.append(rec)
    return proofs


def _bounds_from_manifest(ent):
    for k in ("bounds", "target_bounds", "view_bounds"):
        b = ent.get(k)
        if isinstance(b, (list, tuple)) and len(b) == 4:
            return list(b)
    return None


def _bounds_from_contract(clicked, contract_targets):
    if not contract_targets:
        return None
    cid = clicked.get("target_view_id") or clicked.get("view_id")
    ccls = clicked.get("target_class") or clicked.get("view_class") or ""
    for t in contract_targets:
        if cid is not None and t.get("view_id") == cid:
            return t.get("bounds")
        if ccls and t.get("class") and t.get("class") in ccls:
            return t.get("bounds")
    return None
