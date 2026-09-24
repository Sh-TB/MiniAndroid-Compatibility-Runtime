#!/usr/bin/env python3
"""semantic_verdict.py — S93 loaded-state chain, failure taxonomy, hierarchy.

S93 §1: "loaded" is never one boolean. Every important asset carries a
15-state chain; the deepest HONEST state is reported (each state requires
its own evidence — provenance nodes, bounds, pixel truth, interaction
proofs, repeatability):

    DISCOVERED -> REFERENCED -> RESOLVED -> OPENED -> DECODED -> INFLATED
    -> BOUND -> LAID_OUT -> DRAWN -> FRAME_SUBMITTED -> VISIBLE
    -> SEMANTICALLY_CORRECT -> INTERACTABLE -> STATE_TRANSITION_VERIFIED
    -> VISUALLY_VERIFIED

S93 §19: every failed visual title gets a root category from the taxonomy;
UNKNOWN is a research target, never a dumping ground.

S93 §25: strict non-implication hierarchy — DECODED never implies RENDERED,
RENDERED never implies VISUALLY_VERIFIED, VISUALLY_VERIFIED never implies
INTERACTION_VERIFIED, INTERACTION_VERIFIED never implies FULLY_VERIFIED.
"""
import time

# --- S93 §1 loaded-state chain ----------------------------------------------
LOADED_CHAIN = [
    "DISCOVERED", "REFERENCED", "RESOLVED", "OPENED", "DECODED",
    "INFLATED", "BOUND", "LAID_OUT", "DRAWN", "FRAME_SUBMITTED",
    "VISIBLE", "SEMANTICALLY_CORRECT", "INTERACTABLE",
    "STATE_TRANSITION_VERIFIED", "VISUALLY_VERIFIED",
]

# provenance event names (MiniAndroid GfxProvenance / S92) -> chain states
_PROV_STATE_MAP = {
    "ASSET_FOUND": "OPENED",
    "RESOURCE_RESOLVED": "RESOLVED",
    "DECODED": "DECODED",
    "BITMAP_CREATED": "DECODED",
    "VIEW_RECEIVED": "BOUND",
    "DRAW_CALLED": "DRAWN",
    "RENDERER_BOUND": "BOUND",
    "SURFACE_CREATED": "DRAWN",
    "DRAW_SUBMITTED": "FRAME_SUBMITTED",
    "FRAMEBUFFER_UPDATED": "FRAME_SUBMITTED",
    "BUFFER_PRESENTED": "FRAME_SUBMITTED",
}


def asset_loaded_state(asset=None, provenance_events=None, view_node=None,
                       screenshot_region_valid=False, image_truth=None,
                       interaction_proof=None, state_transition_proof=None,
                       repeatable=False):
    """Deepest honest loaded-state for one asset + the full trail.

    image_truth: verdict dict from probes.semantic_image.image_truth.
    interaction_proof / state_transition_proof: S92 §10/§11 proof dicts.
    """
    events = [e.get("event", "") for e in (provenance_events or [])]
    state_idx = 0
    if asset:
        state_idx = max(state_idx, 1)          # DISCOVERED
    trail = {"DISCOVERED": bool(asset)}
    for ev in events:
        st = _PROV_STATE_MAP.get(ev)
        if st and st in LOADED_CHAIN:
            trail[st] = True
            state_idx = max(state_idx, LOADED_CHAIN.index(st) + 1)
    # INFLATED: decoded AND view received (drawable inflated into view)
    if trail.get("DECODED") and trail.get("BOUND"):
        trail["INFLATED"] = True
    if view_node:
        trail["REFERENCED"] = True
        state_idx = max(state_idx, 2)
        x, y, w, h = (view_node.get("x", 0), view_node.get("y", 0),
                      view_node.get("width", 0), view_node.get("height", 0))
        if w > 0 and h > 0:
            trail["LAID_OUT"] = True
            state_idx = max(state_idx, LOADED_CHAIN.index("LAID_OUT") + 1)
    if screenshot_region_valid and (trail.get("DRAWN") or view_node):
        trail["FRAME_SUBMITTED"] = True
        state_idx = max(state_idx, LOADED_CHAIN.index("FRAME_SUBMITTED") + 1)
    if image_truth:
        v = image_truth.get("verdict")
        content = image_truth.get("content", {}).get("value")
        if content == "PASS" or v in ("VISUALLY_VERIFIED", "UNANCHORED"):
            trail["VISIBLE"] = True
            state_idx = max(state_idx, LOADED_CHAIN.index("VISIBLE") + 1)
        if v == "VISUALLY_VERIFIED":
            trail["SEMANTICALLY_CORRECT"] = True
            state_idx = max(state_idx,
                            LOADED_CHAIN.index("SEMANTICALLY_CORRECT") + 1)
    if interaction_proof and interaction_proof.get("target_proved") and \
            interaction_proof.get("callback_fired"):
        trail["INTERACTABLE"] = True
        state_idx = max(state_idx, LOADED_CHAIN.index("INTERACTABLE") + 1)
    if state_transition_proof and state_transition_proof.get("proved"):
        trail["STATE_TRANSITION_VERIFIED"] = True
        state_idx = max(state_idx,
                        LOADED_CHAIN.index("STATE_TRANSITION_VERIFIED") + 1)
    if trail.get("SEMANTICALLY_CORRECT") and repeatable:
        trail["VISUALLY_VERIFIED"] = True
        state_idx = LOADED_CHAIN.index("VISUALLY_VERIFIED") + 1
    deepest = LOADED_CHAIN[state_idx - 1] if state_idx else "DISCOVERED"
    missing = [s for s in LOADED_CHAIN[:state_idx] if not trail.get(s)]
    return {"deepest_state": deepest,
            "chain_index": state_idx,
            "trail": {s: bool(trail.get(s)) for s in LOADED_CHAIN},
            "missing_within_reached": missing}


# --- S93 §19 failure taxonomy ------------------------------------------------
FAILURE_TAXONOMY = [
    "RESOURCE_NOT_FOUND", "RESOURCE_WRONG_CONFIG", "DECODE_FAILED",
    "DECODED_BUT_NOT_BOUND", "BOUND_BUT_NOT_LAID_OUT", "WRONG_DENSITY",
    "WRONG_SIZE", "WRONG_POSITION", "WRONG_SCALE", "WRONG_ALPHA",
    "WRONG_COLOR", "WRONG_CLIP", "WRONG_DRAW_ORDER", "MISSING_GLYPH",
    "WRONG_FONT", "UNREADABLE_TEXT", "PLACEHOLDER_CONTENT",
    "ANIMATION_FROZEN", "ANIMATION_WRONG_FRAME", "ANIMATION_WRONG_GEOMETRY",
    "SURFACE_NOT_PRESENTED", "WEBVIEW_NOT_VISUALLY_READY",
    "COMPOSE_LAYOUT_FAILURE", "NATIVE_RENDER_FAILURE",
    "INTERACTION_TARGET_MISMATCH", "STATE_CHANGED_WITHOUT_EXPECTED_PIXELS",
    "EXPECTED_PIXELS_WITHOUT_EXPECTED_STATE", "UNKNOWN",
]


def classify_failures(image_truths=None, animation_truth=None,
                      font_truths=None, text_truths=None,
                      provenance_events=None, interaction_proof=None):
    """Map semantic-vector failures to §19 root categories with evidence.
    Every returned category cites the vector that produced it."""
    cats = []
    prov = [e.get("event", "") for e in (provenance_events or [])]

    for name, it in (image_truths or {}).items():
        v = it.get("verdict")
        if v in ("VISUALLY_VERIFIED", "UNANCHORED", None):
            continue
        if v == "PLACEHOLDER":
            cats.append({"asset": name, "category": "PLACEHOLDER_CONTENT",
                         "evidence": it.get("content", {}).get("reasons", [])})
        elif v == "OPAQUE_REPLACEMENT":
            cats.append({"asset": name, "category": "WRONG_ALPHA",
                         "evidence": it.get("content", {}).get("reasons", [])})
        elif v == "MISSING":
            cats.append({"asset": name,
                         "category": "DECODED_BUT_NOT_BOUND" if decoded
                         else "RESOURCE_NOT_FOUND",
                         "evidence": ["expected region blank",
                                      f"provenance_decoded={decoded}"]})
        elif v == "WRONG_POSITION":
            cats.append({"asset": name, "category": "WRONG_POSITION",
                         "evidence": it.get("geometry", {})})
        elif v == "WRONG_GEOMETRY":
            cls = it.get("geometry", {}).get("tolerance_class", "")
            cats.append({"asset": name,
                         "category": "WRONG_DENSITY" if "density" in
                         str(it.get("geometry", {})).lower() else "WRONG_SCALE",
                         "evidence": it.get("geometry", {})})
        elif v == "VISUALLY_PARTIAL" and it.get("geometry", {}).get(
                "tolerance_class") == "CLIPPED":
            cats.append({"asset": name, "category": "WRONG_CLIP",
                         "evidence": it.get("geometry", {}).get("clip")})
        elif v == "WRONG_CONTENT":
            cats.append({"asset": name, "category": "WRONG_COLOR",
                         "evidence": it.get("content", {}).get("reasons", [])})
        elif v == "REGION_INVALID":
            cats.append({"asset": name, "category": "BOUND_BUT_NOT_LAID_OUT",
                         "evidence": ["invalid region geometry"]})

    if animation_truth:
        dets = animation_truth.get("detections", [])
        v = animation_truth.get("verdict")
        if v == "FROZEN":
            cats.append({"asset": "animation", "category": "ANIMATION_FROZEN",
                         "evidence": dets})
        elif "SUSPECTED_WRONG_ORDER" in str(dets) or "SUSPECTED_SKIP" in \
                str(dets):
            cats.append({"asset": "animation",
                         "category": "ANIMATION_WRONG_FRAME",
                         "evidence": dets})
        elif v in ("PLACEHOLDER_ANIMATION", "NOISE", "LARGE_AREA_FLASH"):
            cats.append({"asset": "animation", "category":
                         "PLACEHOLDER_CONTENT", "evidence": dets})
        elif animation_truth.get("verdict") != "NOT_APPLICABLE" and \
                animation_truth.get("ANIMATION_GEOMETRY_VERIFIED") == "FAIL":
            cats.append({"asset": "animation",
                         "category": "ANIMATION_WRONG_GEOMETRY",
                         "evidence": dets})

    for name, ft in (font_truths or {}).items():
        v = ft.get("verdict")
        if v == "BROKEN_FONT":
            cats.append({"asset": name, "category": "DECODE_FAILED",
                         "evidence": [ft.get("error", "font decode failed")]})
        elif v == "UNREADABLE":
            cats.append({"asset": name, "category": "MISSING_GLYPH",
                         "evidence": ft.get("detections", [])})
        elif v == "WRONG_FONT":
            cats.append({"asset": name, "category": "WRONG_FONT",
                         "evidence": ft.get("detections", [])})

    for name, tt in (text_truths or {}).items():
        v = tt.get("verdict")
        if v == "MISSING_TEXT":
            cats.append({"asset": name, "category": "UNREADABLE_TEXT",
                         "evidence": [tt.get("note", "no ink in node")]})
        elif v == "CLIPPED_TEXT":
            cats.append({"asset": name, "category": "WRONG_CLIP",
                         "evidence": [tt.get("note", "ink beyond bounds")]})
        elif v == "UNREADABLE":
            cats.append({"asset": name, "category": "UNREADABLE_TEXT",
                         "evidence": tt.get("glyph_truth", {})})

    if interaction_proof:
        ip = interaction_proof
        if ip.get("callback_fired") and not ip.get("expected_pixels_changed"):
            cats.append({"asset": ip.get("target", "interaction"),
                         "category": "STATE_CHANGED_WITHOUT_EXPECTED_PIXELS",
                         "evidence": [ip.get("note", "")]})
        if ip.get("target_proved") is False:
            cats.append({"asset": ip.get("target", "interaction"),
                         "category": "INTERACTION_TARGET_MISMATCH",
                         "evidence": [ip.get("note", "")]})

    return cats


# --- S93 §25 hierarchy --------------------------------------------------------

HIERARCHY = [
    "NOT_RUN", "DISCOVERED", "RESOURCE_RESOLVED", "DECODED", "RENDERED",
    "FRAME_CAPTURED", "VISUALLY_PARTIAL", "VISUALLY_VERIFIED",
    "INTERACTION_VERIFIED", "STATE_TRANSITION_VERIFIED", "FULLY_VERIFIED",
]


def derive_s93_level(image_truths=None, animation_truth=None,
                     font_truths=None, text_truths=None, stages=None):
    """S93 aggregate level for a title under the §25 non-implication rules.
    Combines with (never replaces) the S92 12-state machine verdict."""
    sem_fail = []
    sem_partial = False
    FAIL_VERDICTS = {"PLACEHOLDER", "OPAQUE_REPLACEMENT", "MISSING",
                     "WRONG_POSITION", "WRONG_GEOMETRY", "WRONG_CONTENT",
                     "REGION_INVALID"}
    for name, it in (image_truths or {}).items():
        v = it.get("verdict")
        if v in FAIL_VERDICTS:
            sem_fail.append(("image", name, v))
        elif v == "VISUALLY_PARTIAL":
            sem_partial = True
    av = (animation_truth or {}).get("verdict")
    if av in ("FROZEN", "NOISE", "LARGE_AREA_FLASH",
              "PLACEHOLDER_ANIMATION"):
        sem_fail.append(("animation", "animation", av))
    elif av in ("ANIMATION_DECODED", "ANIMATION_RENDERED",
                "ANIMATION_CONTENT_VERIFIED"):
        sem_partial = True
    for name, ft in (font_truths or {}).items():
        if ft.get("verdict") in ("BROKEN_FONT", "UNREADABLE", "WRONG_FONT"):
            sem_fail.append(("font", name, ft.get("verdict")))
    for name, tt in (text_truths or {}).items():
        if tt.get("verdict") in ("MISSING_TEXT", "CLIPPED_TEXT",
                                 "UNREADABLE"):
            sem_fail.append(("text", name, tt.get("verdict")))
    level = "SEMANTIC_FAIL" if sem_fail else (
        "SEMANTIC_PARTIAL" if sem_partial else "SEMANTIC_PASS")
    return {"s93_level": level,
            "semantic_failures": sem_fail}


def empty_s93_block():
    return {"schema": "s93.semantic_verdict.v1",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                           time.gmtime())}
