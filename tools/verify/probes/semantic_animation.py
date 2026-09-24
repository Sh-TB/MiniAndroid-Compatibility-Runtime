#!/usr/bin/env python3
"""semantic_animation.py — S93 ANIMATION/GIF TRUTH (§10).

S93 §10 law: "GIF exists + frames exist + pixels changed" is NOT animation
success. Never collapse animation into one GIF_LOADED. The verdict set:

    ANIMATION_DECODED            distinct frames exist (>=2)
    ANIMATION_RENDERED           frames are nonblank and differ structurally
    ANIMATION_CONTENT_VERIFIED   a persistent expected object survives across
                                 frames (component structure stable)
    ANIMATION_GEOMETRY_VERIFIED  object motion matches the expected region /
                                 displacement law (frozen/teleport checked)
    ANIMATION_INTERACTION_VERIFIED   (wired via interaction probe evidence)

Detections (S93 §10): FROZEN, REPEATED_FRAME, SUSPECTED_WRONG_ORDER,
PLACEHOLDER_ANIMATION, NOISE, STATIC_OBJECT_MOVING_BG, OBJECT_LOST,
LARGE_AREA_FLASH.

Laws (each adversarially tested in tools/verify/adversarial_s93.py):
  L-S93-ANI-1  frame identity by perceptual hash (dHash 8x8) + pixel sha
  L-S93-ANI-2  object persistence: the contracted object region must keep
               structured content across frames — background-only change is
               not animation of the object
  L-S93-ANI-3  motion geometry: per-frame centroid/bbox of the object mask;
               displacement series must be non-zero for "animated" contracts
               and continuous (no unexplained teleports)
  L-S93-ANI-4  placeholder animation: every frame placeholder-class (uniform
               /<=2 colors) while the contract expects structured content
  L-S93-ANI-5  progression: frame N -> expected next state via trajectory
               continuity; single huge jump vs median step = suspected skip
               (honest UNKNOWN, never fabricated order proof)
"""
import hashlib

import numpy as np
from PIL import Image


# --- documented thresholds (S93 §7) -----------------------------------------
DHASH_BITS = 64
DHASH_DISTinct = 6          # hamming distance >= 6 => different frames
NONBLANK_STD = 6.0
SOLID_MAX_COLORS = 2
PERSIST_MIN_FRAMES = 0.5    # object present in >= 50% of frames
DISPLACEMENT_MIN_PX = 2.0   # total centroid travel for "animated" contracts
TELEPORT_FACTOR = 6.0       # step > median*factor and > 12px => suspected skip
NOISE_MAX_PERSIST = 0.3     # persistence below this with high deltas => noise
FLASH_DELTA_MIN = 0.30      # global changed ratio for large-area flash
BG_ONLY_OUTSIDE_MIN = 0.02  # outside-object changed ratio
BG_ONLY_INSIDE_MAX = 0.005  # inside-object changed ratio (static object)


def _dhash(arr_gray):
    im = Image.fromarray(arr_gray.astype(np.uint8)).resize((9, 8),
                                                           Image.BILINEAR)
    g = np.asarray(im, dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


def _hamming(a, b):
    return bin(a ^ b).count("1")


def _load_rgb(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float64)


def _gray(a):
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def _frame_stats(a):
    g = _gray(a)
    return {
        "sha256": hashlib.sha256(
            np.ascontiguousarray(a.astype(np.uint8))).hexdigest()[:16],
        "dhash": _dhash(g),
        "chash": tuple(int(c) for c in
                       (a.reshape(-1, 3).mean(axis=0) // 32)),
        "std": round(float(g.std()), 2),
        "colors": int(np.unique((a.reshape(-1, 3).astype(np.int64) // 24),
                                axis=0).shape[0]),
    }


def _object_track(frame_arr, region, bg):
    """Centroid + bbox of non-bg content inside region (or whole frame)."""
    x, y, w, h = region
    H, W = frame_arr.shape[:2]
    x, y, w, h = max(0, int(x)), max(0, int(y)), int(w), int(h)
    w, h = min(w, W - x), min(h, H - y)
    if w <= 2 or h <= 2:
        return None
    R = frame_arr[y:y + h, x:x + w]
    mask = (np.abs(R - bg.reshape(1, 1, 3)).max(axis=2) > 20)
    if mask.sum() < 8:
        return {"present": False, "area": int(mask.sum())}
    ys, xs = np.nonzero(mask)
    return {
        "present": True,
        "area": int(mask.sum()),
        "centroid": [round(float(xs.mean()) + x, 2),
                     round(float(ys.mean()) + y, 2)],
        "bbox": [int(xs.min()) + x, int(ys.min()) + y,
                 int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1],
    }


def animation_truth(frame_paths, object_region=None, expect_motion=True,
                    contract=None, expected_direction="any"):
    """S93 §10 animation truth vector over ordered frames.

    frame_paths: ordered frame image paths (runtime frames/ or GIF decode).
    object_region: (x,y,w,h) semantic object to track (contract/board/HUD);
                   None => track dominant non-bg content of the full frame.
    expect_motion: contract says the object should move/change position.
    """
    out = {"schema": "s93.animation_truth.v1", "frame_count":
           len(frame_paths)}
    if len(frame_paths) < 2:
        out.update({
            "ANIMATION_DECODED": "FAIL", "ANIMATION_RENDERED": "UNKNOWN",
            "ANIMATION_CONTENT_VERIFIED": "UNKNOWN",
            "ANIMATION_GEOMETRY_VERIFIED": "NOT_APPLICABLE",
            "detections": ["INSUFFICIENT_FRAMES"],
            "verdict": "ANIMATION_DECODED" if frame_paths else "FAILED",
        })
        return out

    frames = [_load_rgb(p) for p in frame_paths]
    stats = [_frame_stats(a) for a in frames]
    out["frame_signatures"] = [{k: s[k] for k in ("sha256", "std", "colors")}
                               for s in stats]

    # L-S93-ANI-1 frame identity: structure hash (dHash) OR coarse color
    # hash (uniform color flips are invisible to dHash)
    def _distinct_prev(s):
        return all(
            _hamming(s["dhash"], d) >= DHASH_DISTinct or
            max(abs(s["chash"][k] - c[k]) for k in range(3)) >= 2
            for d, c in zip(distinct, chashes))

    distinct = [stats[0]["dhash"]]
    chashes = [stats[0]["chash"]]
    for s in stats[1:]:
        if _distinct_prev(s):
            distinct.append(s["dhash"])
            chashes.append(s["chash"])
    distinct_count = len(distinct)
    out["distinct_frames"] = distinct_count
    decoded = distinct_count >= 2

    # structural continuity: mean consecutive dHash distance. Real motion
    # keeps neighboring frames structurally similar (<=~10 bits); random
    # noise is bit-uniform (~32). One signal of two required for NOISE.
    hd = [_hamming(stats[i]["dhash"], stats[i - 1]["dhash"])
          for i in range(1, len(stats))]
    mean_hd = float(np.mean(hd)) if hd else 0.0
    out["mean_consecutive_dhash_dist"] = round(mean_hd, 1)

    # diffs
    diffs = []
    for i in range(1, len(frames)):
        if frames[i].shape == frames[i - 1].shape:
            d = (np.abs(frames[i] - frames[i - 1]).max(axis=2) > 8)
            diffs.append({
                "pair": [i - 1, i],
                "changed_ratio": round(float(d.mean()), 6),
            })
        else:
            diffs.append({"pair": [i - 1, i], "changed_ratio": 1.0,
                          "note": "shape_change"})
    out["frame_diffs"] = diffs
    mean_changed = float(np.mean([d["changed_ratio"] for d in diffs])) \
        if diffs else 0.0

    # L-S93-ANI-4 placeholder animation
    placeholders = [s["colors"] <= SOLID_MAX_COLORS and s["std"] < NONBLANK_STD
                    for s in stats]
    if decoded and all(placeholders):
        out.update({
            "ANIMATION_DECODED": "PASS", "ANIMATION_RENDERED": "FAIL",
            "ANIMATION_CONTENT_VERIFIED": "FAIL",
            "ANIMATION_GEOMETRY_VERIFIED": "NOT_APPLICABLE",
            "detections": ["PLACEHOLDER_ANIMATION"],
            "verdict": "PLACEHOLDER_ANIMATION",
        })
        return out

    # L-S93-ANI-2/3 object persistence + motion
    bg = np.median(np.concatenate(
        [frames[0][0, :], frames[0][-1, :], frames[0][:, 0],
         frames[0][:, -1]]), axis=0)
    region = object_region if object_region else \
        (0, 0, frames[0].shape[1], frames[0].shape[0])
    tracks = [_object_track(a, region, bg) for a in frames]
    present = [t is not None and t.get("present") for t in tracks]
    persistence = float(sum(present)) / len(present)
    out["object_tracks"] = [
        {"present": t.get("present", False),
         "centroid": t.get("centroid"),
         "area": t.get("area")} if t else {"present": False}
        for t in tracks]

    centroids = [t["centroid"] for t in tracks
                 if t and t.get("present") and t.get("centroid")]
    travel = 0.0
    steps = []
    for i in range(1, len(centroids)):
        d = float(np.hypot(centroids[i][0] - centroids[i - 1][0],
                           centroids[i][1] - centroids[i - 1][1]))
        steps.append(d)
        travel += d
    out["object_travel_px"] = round(travel, 2)

    detections = []
    rendered = decoded and all(s["std"] >= NONBLANK_STD for s in stats)

    # FROZEN: nothing changes at all
    frozen = mean_changed < 1e-6 and distinct_count == 1

    # REPEATED_FRAME: long identical runs then jumps (A A A B B B)
    repeated = False
    if not frozen:
        same_run = 1
        max_run = 1
        for i in range(1, len(stats)):
            if _hamming(stats[i]["dhash"], stats[i - 1]["dhash"]) == 0 and \
                    stats[i]["chash"] == stats[i - 1]["chash"]:
                same_run += 1
                max_run = max(max_run, same_run)
            else:
                same_run = 1
        repeated = max_run >= 3 and distinct_count >= 2 and \
            distinct_count <= max(2, len(stats) // 3)

    # NOISE: structurally discontinuous frames (bit-random neighbors) AND
    # large pixel churn — never one signal alone (S93 §30)
    noise = (not frozen) and mean_hd >= 20.0 and mean_changed >= 0.30

    # LARGE_AREA_FLASH: huge global deltas, object structure unstable
    flash = (not frozen) and mean_changed >= FLASH_DELTA_MIN and \
        persistence < 0.5

    # STATIC_OBJECT_MOVING_BG: outside-object region changes, object static
    bg_only = False
    if object_region and not frozen:
        ins = []
        outs = []
        for i in range(1, len(frames)):
            if frames[i].shape != frames[i - 1].shape:
                continue
            d = (np.abs(frames[i] - frames[i - 1]).max(axis=2) > 8)
            x, y, w, h = [int(v) for v in object_region]
            inside = d[y:y + h, x:x + w]
            outside = d.copy()
            outside[y:y + h, x:x + w] = False
            ins.append(float(inside.mean()))
            outs.append(float(outside.mean()))
        if ins and outs and float(np.mean(outs)) >= BG_ONLY_OUTSIDE_MIN and \
                float(np.mean(ins)) <= BG_ONLY_INSIDE_MAX:
            bg_only = True
            detections.append("STATIC_OBJECT_MOVING_BG")

    # OBJECT_LOST: object present early, gone later
    object_lost = False
    if object_region and present:
        first_half = present[:max(1, len(present) // 2)]
        last_half = present[len(present) // 2:] or [False]
        if all(first_half) and not any(last_half):
            object_lost = True
            detections.append("OBJECT_LOST")

    # L-S93-ANI-5 progression / suspected skip / direction contract
    suspected_skip = False
    if steps and len(steps) >= 3:
        med = float(np.median(steps))
        if med > 0.5:
            for i, s in enumerate(steps):
                if s > med * TELEPORT_FACTOR and s > 12.0:
                    suspected_skip = True
                    detections.append(
                        {"SUSPECTED_SKIP": {"step": i, "px": round(s, 1)}})

    # monotonic-direction contract: reversal of travel direction after
    # progress is frame-order corruption the runtime cannot hide
    direction_broken = False
    if expected_direction == "monotonic" and len(centroids) >= 3:
        dxs = [centroids[i][0] - centroids[i - 1][0]
               for i in range(1, len(centroids))]
        moves = [d for d in dxs if abs(d) > 1.0]
        if moves:
            sign0 = 1 if moves[0] > 0 else -1
            for d in moves[1:]:
                if (1 if d > 0 else -1) != sign0:
                    direction_broken = True
                    detections.append("SUSPECTED_WRONG_ORDER")
                    break
    if direction_broken:
        suspected_skip = True

    if expect_motion and travel < DISPLACEMENT_MIN_PX and not frozen and \
            not bg_only:
        detections.append("NO_OBJECT_MOTION")

    content_v = "PASS" if persistence >= PERSIST_MIN_FRAMES and not noise \
        and not object_lost and not frozen else "FAIL"
    if noise:
        detections.append("NOISE")
    if flash and not noise:
        detections.append("LARGE_AREA_FLASH")
    if repeated:
        detections.append("REPEATED_FRAME")
    if frozen:
        detections.append("FROZEN")

    geom_v = "PASS" if (travel >= DISPLACEMENT_MIN_PX or not expect_motion) \
        and not suspected_skip and not frozen else "FAIL"
    if frozen:
        geom_v = "FAIL"

    if frozen:
        verdict = "FROZEN"
    elif noise or flash:
        verdict = "NOISE" if noise else "LARGE_AREA_FLASH"
    elif placeholders and not rendered:
        verdict = "PLACEHOLDER_ANIMATION"
    elif object_lost or bg_only:
        verdict = "ANIMATION_RENDERED"   # rendered but semantically broken
    elif decoded and rendered and content_v == "PASS" and geom_v == "PASS":
        verdict = "ANIMATION_GEOMETRY_VERIFIED"
    elif decoded and rendered and content_v == "PASS":
        verdict = "ANIMATION_CONTENT_VERIFIED"
    elif decoded and rendered:
        verdict = "ANIMATION_RENDERED"
    elif decoded:
        verdict = "ANIMATION_DECODED"
    else:
        verdict = "SINGLE_FRAME"
    # temporal corruption caps the ladder: repeated/placeholder frames can
    # never claim content- or geometry-verified animation
    if repeated and verdict in ("ANIMATION_CONTENT_VERIFIED",
                                "ANIMATION_GEOMETRY_VERIFIED"):
        verdict = "ANIMATION_RENDERED"

    out.update({
        "ANIMATION_DECODED": "PASS" if decoded else "FAIL",
        "ANIMATION_RENDERED": "PASS" if rendered else "FAIL",
        "ANIMATION_CONTENT_VERIFIED": content_v,
        "ANIMATION_GEOMETRY_VERIFIED": geom_v,
        "persistence": round(persistence, 3),
        "detections": detections,
        "verdict": verdict,
    })
    return out
