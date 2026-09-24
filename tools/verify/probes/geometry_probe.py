#!/usr/bin/env python3
"""geometry_probe.py — S92 geometry verification (§7, §14).

Cross-correlates ViewTree bounds (runtime), contract-expected bounds
(source/layout-derived), and screenshot-region pixel evidence.

Laws:
- "the image is present somewhere" is NOT acceptance: expected vs actual
  deltas are computed and gated by DOCUMENTED tolerance (§7)
- tolerance = max(GEOMETRY_TOLERANCE_PX, GEOMETRY_TOLERANCE_FRAC * size)
- ViewTree PASS + pixels FAIL  -> VISUAL_FAIL   (§14 triangulation)
- pixels PASS + ViewTree absent -> renderer-family investigation required
- DrawTrace(provenance) PASS + pixels absent -> RENDER_OUTPUT_FAIL

Also classifies full-screen blank/splash-only frames (§13).
"""
import numpy as np
from PIL import Image

from .visual_probe import GEOMETRY_TOLERANCE_FRAC, GEOMETRY_TOLERANCE_PX

BLANK_STDDEV_FLOOR = 6.0      # uniform frame
NEARLY_BLANK_CONTENT_FRAC = 0.005   # <0.5% non-background pixels


def check_geometry(view_tree, contract, screenshot_path=None):
    """For each contract element with expected_bounds, compare with the
    ViewTree node bounds (matched by resource id / class / text)."""
    nodes = view_tree.get("nodes", []) if view_tree else []
    results = []
    n_pass = n_fail = n_na = 0
    for el in (contract or {}).get("required_elements", []):
        exp = el.get("expected_bounds")
        if not exp:
            results.append({"element": el.get("name"), "value": "NOT_APPLICABLE",
                            "note": "no expected bounds in contract"})
            n_na += 1
            continue
        node = _find_node(nodes, el)
        if node is None:
            results.append({"element": el.get("name"), "value": "FAIL",
                            "expected_bounds": exp,
                            "failure": "ELEMENT_NOT_IN_VIEWTREE"})
            n_fail += 1
            continue
        if node.get("visibility", 0) != 0:
            results.append({"element": el.get("name"), "value": "FAIL",
                            "expected_bounds": exp,
                            "actual_bounds": _nb(node),
                            "failure": f"VISIBILITY_{node.get('visibility')}"})
            n_fail += 1
            continue
        act = _nb(node)
        tol = max(GEOMETRY_TOLERANCE_PX,
                  int(GEOMETRY_TOLERANCE_FRAC * max(exp[2], exp[3], 1)))
        deltas = [act[0] - exp[0], act[1] - exp[1],
                  act[2] - exp[2], act[3] - exp[3]]
        ok = all(abs(d) <= tol for d in deltas)
        results.append({
            "element": el.get("name"), "value": "PASS" if ok else "FAIL",
            "expected_bounds": exp, "actual_bounds": act,
            "delta_dxywh": deltas, "tolerance_px": tol,
            **({} if ok else {"failure": "GEOMETRY_DELTA_EXCEEDED"})})
        if ok:
            n_pass += 1
        else:
            n_fail += 1
    rollup = "NOT_APPLICABLE" if n_na and not (n_pass or n_fail) else \
        ("PASS" if n_fail == 0 and n_pass > 0 else
         ("PARTIAL" if n_pass and n_fail else
          ("FAIL" if n_fail else "NOT_APPLICABLE")))
    return results, rollup, {"pass": n_pass, "fail": n_fail, "na": n_na}


def _nb(node):
    return [node.get("x", 0), node.get("y", 0),
            node.get("width", 0), node.get("height", 0)]


def _find_node(nodes, el):
    rid = el.get("resource_id")
    cls = el.get("class")
    text = el.get("text")
    for n in nodes:
        if rid and n.get("android_view_id") == rid:
            return n
    for n in nodes:
        if text and n.get("text") == text:
            return n
    for n in nodes:
        if cls and cls in (n.get("class") or ""):
            return n
    return None


def frame_quality(screenshot_path, background=(255, 255, 255)):
    """§13 full/partial-screen detection: blank, nearly-blank, single-color,
    content bounds. Diagnostic layer — never sufficient alone (§13 law)."""
    im = Image.open(screenshot_path).convert("RGB")
    A = np.asarray(im, dtype=np.int16)
    gray = 0.2126 * A[:, :, 0] + 0.7152 * A[:, :, 1] + 0.0722 * A[:, :, 2]
    std = float(gray.std())
    nonbg = (np.abs(A - np.array(background)).max(axis=2) > 8)
    frac = float(nonbg.mean())
    out = {
        "dims": [im.width, im.height],
        "luminance_stddev": round(std, 2),
        "non_background_frac": round(frac, 6),
        "unique_colors_est": int(len(np.unique(
            (A // 8).reshape(-1, 3), axis=0))),
    }
    if std < BLANK_STDDEV_FLOOR or frac < NEARLY_BLANK_CONTENT_FRAC:
        out["class"] = "BLANK_OR_NEARLY_BLANK"
    elif frac < 0.02:
        out["class"] = "SPARSE_CONTENT"
    else:
        out["class"] = "CONTENT_PRESENT"
    if nonbg.any():
        ys, xs = np.nonzero(nonbg)
        out["content_bounds"] = [int(xs.min()), int(ys.min()),
                                 int(xs.max()), int(ys.max())]
    return out


def triangulate(view_tree_ok, pixels_ok, provenance_ok):
    """§14 ViewTree x DrawTrace x Pixels triangulation verdict."""
    if view_tree_ok and pixels_ok:
        return "STRONG_EVIDENCE"
    if view_tree_ok and provenance_ok and not pixels_ok:
        return "RENDER_OUTPUT_FAIL"
    if pixels_ok and not view_tree_ok:
        return "PIXELS_WITHOUT_VIEWTREE_INVESTIGATE_FAMILY"
    if view_tree_ok and not provenance_ok and not pixels_ok:
        return "VISUAL_FAIL"
    return "NO_EVIDENCE"
