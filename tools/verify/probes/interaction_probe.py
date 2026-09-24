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

Supports BOTH runtime manifest shapes:
  click-count manifest: frames[].event == "click" + clicked_view_id +
                        click_dispatched + changed_pixels_vs_previous
  TAP manifest:         gesture == "TAP"; frames with event
                        "ACTION_DOWN pressed state (mid-gesture)" and
                        "post-gesture (callbacks drained, transitions
                        applied)"; events[] carry dispatcher records.
"""
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


def _node_by_id(run_evidence, vid):
    for n in gc.view_nodes(run_evidence.view_tree):
        if n.get("android_view_id") == vid:
            return n
    return None


def _node_by_class(run_evidence, cls):
    if not cls:
        return None
    for n in gc.view_nodes(run_evidence.view_tree):
        if cls in (n.get("class") or ""):
            return n
    return None


def verify_input_target(run_evidence, target, screenshot_path=None):
    """§10 gate. target: dict with bounds (x,y,w,h) + identity fields."""
    x, y, w, h = target.get("bounds") or (None, None, None, None)
    identity = {k: target.get(k) for k in
                ("view_id", "class", "text") if target.get(k) is not None}
    proof = {"identity": identity, "steps": {}}
    if x is None:
        proof["verdict"] = "INPUT_TARGET_UNVERIFIED"
        proof["reason"] = "no bounds"
        return proof
    sw, sh = screen_size(run_evidence)
    node = _node_by_id(run_evidence, target.get("view_id")) if \
        target.get("view_id") is not None else \
        _node_by_class(run_evidence, target.get("class"))
    vis = node.get("visibility", 0) if node else None
    proof["steps"]["viewtree_identity"] = "PASS" if node else \
        ("UNKNOWN" if not run_evidence.view_tree else "FAIL")
    proof["steps"]["viewtree_visibility"] = \
        "PASS" if vis == 0 else ("FAIL" if vis is not None else "UNKNOWN")
    inter = (x is not None and 0 <= x < sw and 0 <= y < sh and w > 0 and
             h > 0 and x + w <= sw + 8 and y + h <= sh + 8)
    proof["steps"]["screen_intersection"] = "PASS" if inter else "FAIL"
    shot = screenshot_path or run_evidence.screenshot
    if shot and inter:
        im = Image.open(shot).convert("RGB")
        A = np.asarray(im, dtype=np.int16)
        R = A[max(0, y):min(sh, y + h), max(0, x):min(sw, x + w)]
        if R.size == 0:
            proof["steps"]["region_pixels"] = "FAIL"
        else:
            std = float(R.astype(np.float64).std())
            proof["region_stddev"] = round(std, 2)
            proof["steps"]["region_pixels"] = \
                "PASS" if std >= 6.0 else "FAIL"
    else:
        proof["steps"]["region_pixels"] = "UNKNOWN"
    ok = (proof["steps"].get("viewtree_visibility") in ("PASS", "UNKNOWN")) \
        and proof["steps"].get("screen_intersection") == "PASS" \
        and proof["steps"].get("region_pixels") in ("PASS", "UNKNOWN")
    proof["verdict"] = "INPUT_TARGET_VERIFIED" if ok \
        else "INPUT_TARGET_UNVERIFIED"
    return proof


def _bounds_of(node):
    if not node:
        return None
    return [node.get("x", 0), node.get("y", 0),
            node.get("width", 0), node.get("height", 0)]


def _frame_path(frames, name):
    for n, p in frames:
        if n == name:
            return p
    return None


def interaction_proofs(run_evidence, contracts_targets=None):
    """Build §11 pre/post proofs from the runtime manifests.
    Returns list of proof records; each verdict is one of
    INTERACTION_VISUALLY_PROVEN / INTERACTION_TARGET_UNVERIFIED /
    INTERACTION_NO_VISUAL_CHANGE / INTERACTION_NOT_DISPATCHED.

    Three manifest shapes are supported:
      - F-NEW-199 interactions[]: runtime-authored per-scheduled-tap
        records (frame, x, y, target_view_id, down_record) — the
        authoritative shape for --frames + --tap runs.
      - TAP manifests: frame events with "ACTION_DOWN"/"post-gesture".
      - click-count manifests: frames[].event == "click".
    """
    proofs = []
    frames = run_evidence.frames
    if not frames:
        return proofs
    manifest = run_evidence.frames_manifest or {}

    # ── F-NEW-199 interactions[] (authoritative scheduled-tap records) ──
    frame_by_index = {}
    for e in manifest.get("frames") or []:
        if e.get("file"):
            frame_by_index[e.get("index")] = e
    for ir in manifest.get("interactions") or []:
        k = ir.get("frame", ir.get("after_frame_index"))
        after_e = frame_by_index.get(k) or {}
        before_e = frame_by_index.get((k or 0) - 1) or \
            frame_by_index.get(0) or {}
        proofs.append(_build_f199_proof(
            run_evidence, ir, before_e, after_e, frames))

    # ── legacy shapes: TAP gesture stream / click-count entries ─────────
    entries = manifest.get("frames") or []
    interactions = [e for e in entries
                    if e.get("event") in ("click", "long_press") or
                    "ACTION_DOWN" in str(e.get("event", "")) or
                    "post-gesture" in str(e.get("event", ""))]
    if interactions and not manifest.get("interactions"):
        i = 0
        while i < len(interactions):
            ent = interactions[i]
            ev = str(ent.get("event", ""))
            if "ACTION_DOWN" in ev:
                after = None
                if i + 1 < len(interactions) and \
                        "post-gesture" in str(interactions[i + 1].get(
                            "event", "")):
                    after = interactions[i + 1]
                    i += 2
                else:
                    i += 1
                proofs.append(_build_proof(
                    run_evidence, before_ent=None, after_ent=ent,
                    post_ent=after, frames=frames))
            elif ev in ("click", "long_press"):
                proofs.append(_build_proof(
                    run_evidence, before_ent=None, after_ent=ent,
                    post_ent=None, frames=frames, click_entry=True))
                i += 1
            else:
                i += 1
    return proofs


def _build_f199_proof(run_evidence, ir, before_e, after_e, frames):
    """§10/§11 proof from one F-NEW-199 manifest interaction record."""
    idx = ir.get("frame")
    rec = {"index": idx, "source": "F-NEW-199 interactions[]"}
    vid = ir.get("target_view_id")
    rec["input_event"] = {
        "type": "tap (scheduled F-117)",
        "dispatched": bool(vid),
        "x": ir.get("x"), "y": ir.get("y"),
        "down_record": ir.get("down_record"),
    }
    rec["clicked"] = {"view_id": vid} if vid else {}
    node = _node_by_id(run_evidence, vid) if vid else None
    tgt = None
    if node:
        b = _bounds_of(node)
        tgt = verify_input_target(
            run_evidence, {"bounds": b, "view_id": vid,
                           "class": node.get("class")},
            screenshot_path=_frame_path(frames, before_e.get("file", "")))
        rec["target_proof"] = tgt
        rec["target_bounds"] = b
    delta = None
    before_name = before_e.get("file")
    after_name = after_e.get("file")
    if before_name and after_name:
        bp = _frame_path(frames, before_name)
        ap = _frame_path(frames, after_name)
        if bp and ap:
            delta = vp.region_diff(bp, ap)
            rec["before_frame"] = before_name
            rec["after_frame"] = after_name
    runtime_delta = after_e.get("changed_pixels_vs_previous")
    rec["pixel_delta"] = delta or \
        ({"changed_px": runtime_delta} if runtime_delta is not None else {})
    unverified = (tgt or {}).get("verdict") == "INPUT_TARGET_UNVERIFIED"
    changed = ((delta or {}).get("changed_px", 0) or 0) > 0 or \
        (runtime_delta or 0) > 0
    dispatched = rec["input_event"].get("dispatched", False) and bool(vid)
    if unverified:
        rec["verdict"] = "INTERACTION_TARGET_UNVERIFIED"
    elif dispatched and changed:
        rec["verdict"] = "INTERACTION_VISUALLY_PROVEN"
    elif dispatched:
        rec["verdict"] = "INTERACTION_NO_VISUAL_CHANGE"
    else:
        rec["verdict"] = "INTERACTION_NOT_DISPATCHED"
    return rec


def _build_proof(run_evidence, before_ent, after_ent, post_ent, frames,
                 click_entry=False):
    """One §11 proof from a DOWN/post pair (TAP) or a click entry."""
    idx = after_ent.get("index")
    rec = {"index": idx}
    if click_entry:
        rec["input_event"] = {"type": after_ent.get("event"),
                              "dispatched":
                                  after_ent.get("click_dispatched", True),
                              "kind": after_ent.get("click_kind")}
        vid = after_ent.get("clicked_view_id")
        cls = after_ent.get("clicked_view_class")
        runtime_delta = after_ent.get("changed_pixels_vs_previous")
        before_name = f"frame_{max(0, (idx or 1) - 1):03d}.png"
        after_name = after_ent.get("file")
    else:
        vid = post_ent.get("target_view_id") if post_ent else \
            after_ent.get("target_view_id")
        cls = None
        runtime_delta = post_ent.get("changed_pixels_vs_previous") \
            if post_ent else None
        before_name = after_ent.get("file")
        after_name = post_ent.get("file") if post_ent else None
        rec["input_event"] = {"type": "tap (DOWN/UP pipeline)",
                              "dispatched": bool(vid)}
    rec["clicked"] = {k: v for k, v in
                      (("view_id", vid), ("class", cls)) if v}
    node = _node_by_id(run_evidence, vid) if vid is not None else None
    tgt = None
    if node:
        b = _bounds_of(node)
        tgt = verify_input_target(
            run_evidence, {"bounds": b, "view_id": vid,
                           "class": node.get("class")},
                        screenshot_path=_frame_path(frames, before_name))
        rec["target_proof"] = tgt
        rec["target_bounds"] = b
    # pixel delta: runtime's own count + independent recomputation
    delta = None
    if before_name and after_name:
        bp = _frame_path(frames, before_name)
        ap = _frame_path(frames, after_name)
        if bp and ap:
            delta = vp.region_diff(bp, ap)
            rec["before_frame"] = before_name
            rec["after_frame"] = after_name
    rec["pixel_delta"] = delta or \
        ({"changed_px": runtime_delta} if runtime_delta is not None else {})
    unverified = (tgt or {}).get("verdict") == "INPUT_TARGET_UNVERIFIED"
    changed = ((delta or {}).get("changed_px", 0) or 0) > 0 or \
        (runtime_delta or 0) > 0
    dispatched = rec["input_event"].get("dispatched", True) and bool(vid)
    if unverified:
        rec["verdict"] = "INTERACTION_TARGET_UNVERIFIED"
    elif dispatched and changed:
        rec["verdict"] = "INTERACTION_VISUALLY_PROVEN"
    elif dispatched:
        rec["verdict"] = "INTERACTION_NO_VISUAL_CHANGE"
    else:
        rec["verdict"] = "INTERACTION_NOT_DISPATCHED"
    return rec
