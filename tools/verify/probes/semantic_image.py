#!/usr/bin/env python3
"""semantic_image.py — S93 IMAGE TRUTH (multi-metric, adversarially tested).

S93 §0/§1 law: a resource can be technically "loaded" while the user-visible
result is WRONG. This module never answers "loaded=true"; it answers the
S93 questions:

    WHAT was supposed to appear?        (asset bytes + contract)
    WHAT actually appeared?             (screenshot region pixels)
    WHERE should it appear?             (expected region)
    WHERE did it appear?                (measured content bbox)
    DID the correct pixels appear?      (content vector below)

The verdict is derived from a VECTOR (S93 §14), never from one metric:

    identity, decode, geometry, position, alpha, color, edges,
    texture/detail, content, temporal, interaction, provenance

New S93 laws (each adversarially tested in tools/verify/adversarial_s93.py):

  L-S93-IMG-1  SOLID/TWO-COLOR PLACEHOLDER: a nonblank region with no
               structure (<=2 distinct quantized colors AND near-zero edge
               density) is a PLACEHOLDER, not an image, whenever the
               expected asset itself is structured. (S93 §9 "two color
               attack" — entropy/color-count alone are FORBIDDEN as sole
               evidence; this law uses structure-vs-expectation.)
  L-S93-IMG-2  SHAPE TRUTH: connected-component layout of the expected
               asset (component count, fill ratio, centroid, aspect) must
               match the observed region's component layout. Blue circle in
               a 96x96 transparent canvas rendered as a blue 96x96
               rectangle => fill ratio 0.785 vs 1.0 => FAIL.
  L-S93-IMG-3  SPATIAL COLOR LAYOUT: 4x4 dominant-color grid of the
               flattened asset vs the observed region. A photograph
               replaced by two flat rectangles cannot pass.
  L-S93-IMG-4  ALPHA TRUTH: where the asset is transparent (alpha<64) the
               observed region must show the background, not opaque asset
               color. Opaque replacement of a transparent asset => FAIL.
  L-S93-IMG-5  POSITION/GEOMETRY with semantic tolerance (S93 §8):
               EXACT > NEAR_EXACT > GEOMETRICALLY_CORRECT > PARTIAL >
               WRONG_POSITION / WRONG_SCALE / CLIPPED / MISSING.
  L-S93-IMG-6  REGION-BASED VERIFICATION (S93 §15): per-region sub-verdicts;
               90% correct background + 10% missing button = FAIL overall.
               The missing button stays visible in the verdict.

Values are restricted to PASS | FAIL | PARTIAL | NOT_APPLICABLE | UNKNOWN
(S92 §38 machine-readable law)."""
import hashlib

import numpy as np
from PIL import Image
from scipy import ndimage

# --- documented thresholds (S93 §7 law: every tolerance documented) ---------
GRID = 4                       # spatial color layout grid (GRID x GRID)
SOLID_MAX_COLORS = 2           # distinct quantized colors => placeholder-class
EDGE_DENSITY_MIN = 0.004       # fraction of strong-gradient pixels in region
EDGE_DENSITY_MIN_STRUCTURED_ASSET = 0.01
COMPONENT_COUNT_TOL = 1        # |components - expected| <= 1 (anti-noise)
FILL_RATIO_TOL = 0.15          # |fill ratio delta| tolerance
CENTROID_TOL_FRAC = 0.20       # centroid offset as fraction of side
LAYOUT_MATCH_MIN = 0.60        # 4x4 grid dominant-color match fraction
ALPHA_LEAK_MAX = 0.10          # opaque-pixel fraction allowed in transparent
                               # asset zones (anti opaque-replacement)
POS_NEAR_EXACT_PX = 4          # center delta for NEAR_EXACT
POS_CORRECT_FRAC = 0.12        # or 12% of asset size (S92 §7 heritage)
SCALE_TOL = 0.15               # measured/expected linear scale tolerance
CLIP_SHADOW_MIN = 0.97         # content bbox touching region border on a
                               # side with asset content beyond => CLIPPED
CC_CONNECTIVITY = 1            # 4-connectivity for component labeling


def _load_rgba(data):
    if isinstance(data, bytes):
        return Image.open(__import__("io").BytesIO(data)).convert("RGBA")
    return Image.open(data).convert("RGBA")


def _region(arr, region):
    x, y, w, h = [int(v) for v in region]
    H, W = arr.shape[:2]
    x, y = max(0, x), max(0, y)
    w, h = min(w, W - x), min(h, H - y)
    if w <= 2 or h <= 2:
        return None, None
    return arr[y:y + h, x:x + w], (x, y, w, h)


def _bg_median(R):
    border = np.concatenate([R[0, :], R[-1, :], R[:, 0], R[:, -1]])
    return np.median(border, axis=0)


def _quant(rgb, levels=24):
    return (rgb.reshape(-1, 3).astype(np.int64) // levels)


def _edge_density(gray):
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
    gy[1:-1, :] = gray[2:, :] - gray[:-2, :]
    mag = np.hypot(gx, gy)
    return float((mag > 24.0).mean())


def _components(mask):
    """Connected components of a boolean mask -> list of dicts
    (area, bbox, fill_ratio, centroid), sorted by area desc, min area 0.5%."""
    lab, n = ndimage.label(mask, structure=None if CC_CONNECTIVITY == 1
                           else np.ones((3, 3)))
    if n == 0:
        return []
    out = []
    min_area = max(4, int(0.005 * mask.size))
    for sl in ndimage.find_objects(lab):
        if sl is None:
            continue
        area = int((lab[sl] > 0).sum())
        if area < min_area:
            continue
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        ys, xs = np.nonzero(lab[sl])
        out.append({
            "area": area,
            "bbox": [int(sl[1].start), int(sl[0].start),
                     int(w), int(h)],
            "fill_ratio": round(area / float(max(1, w * h)), 4),
            "centroid": [round(float(xs.mean() / max(1, w)), 4),
                         round(float(ys.mean() / max(1, h)), 4)],
        })
    out.sort(key=lambda c: -c["area"])
    return out


def _shape_truth(asset_comps, obs_comps):
    """L-S93-IMG-2. Compare component layout; returns (score, reasons)."""
    if not asset_comps:
        return 1.0, ["asset has no structured components (flat asset)"]
    reasons = []
    na, no = len(asset_comps), len(obs_comps)
    if abs(na - no) > COMPONENT_COUNT_TOL:
        reasons.append(f"component_count asset={na} observed={no}")
    a0, o0 = asset_comps[0], (obs_comps[0] if obs_comps else None)
    if o0 is None:
        return 0.0, reasons + ["no observed components"]
    if abs(a0["fill_ratio"] - o0["fill_ratio"]) > FILL_RATIO_TOL:
        reasons.append(
            f"fill_ratio asset={a0['fill_ratio']} observed={o0['fill_ratio']}")
    dcent = float(np.hypot(a0["centroid"][0] - o0["centroid"][0],
                           a0["centroid"][1] - o0["centroid"][1]))
    if dcent > CENTROID_TOL_FRAC:
        reasons.append(f"centroid_offset={dcent:.3f}")
    aasp = a0["bbox"][2] / max(1, a0["bbox"][3])
    oasp = o0["bbox"][2] / max(1, o0["bbox"][3])
    if abs(aasp - oasp) > 0.25:
        reasons.append(f"aspect asset={aasp:.2f} observed={oasp:.2f}")
    score = 1.0 - min(1.0, len(reasons) * 0.5)
    return score, reasons


def _dominant(cell):
    k = _quant(cell)
    if k.shape[0] == 0:
        return None
    idx = np.bincount(k[:, 0] * 65536 + k[:, 1] * 256 + k[:, 2]).argmax()
    return int(idx)


def _spatial_layout(asset_rgb, obs_rgb):
    """L-S93-IMG-3. 4x4 dominant-color grid match fraction."""
    h, w = asset_rgb.shape[:2]
    oh, ow = obs_rgb.shape[:2]
    hits = 0
    total = 0
    for gy in range(GRID):
        for gx in range(GRID):
            acell = asset_rgb[gy * h // GRID:(gy + 1) * h // GRID,
                              gx * w // GRID:(gx + 1) * w // GRID]
            ocell = obs_rgb[gy * oh // GRID:(gy + 1) * oh // GRID,
                            gx * ow // GRID:(gx + 1) * ow // GRID]
            if acell.size == 0 or ocell.size == 0:
                continue
            akey = _dominant(acell)
            okey = _dominant(ocell)
            total += 1
            if akey is not None and akey == okey:
                hits += 1
    return hits / total if total else 0.0


def _geometry_verdict(expected_box, measured_box, clipped):
    """L-S93-IMG-5 semantic tolerance (S93 §8)."""
    if measured_box is None:
        return "MISSING", {}
    ex, ey, ew, eh = expected_box
    mx, my, mw, mh = measured_box
    dcx = abs((mx + mw / 2) - (ex + ew / 2))
    dcy = abs((my + mh / 2) - (ey + eh / 2))
    scale_w = mw / max(1.0, float(ew))
    scale_h = mh / max(1.0, float(eh))
    m = {
        "center_delta_px": [round(dcx, 1), round(dcy, 1)],
        "scale": [round(scale_w, 3), round(scale_h, 3)],
    }
    if clipped:
        return "CLIPPED", m
    if dcx > max(POS_NEAR_EXACT_PX, ew * POS_CORRECT_FRAC) or \
            dcy > max(POS_NEAR_EXACT_PX, eh * POS_CORRECT_FRAC):
        return "WRONG_POSITION", m
    if abs(scale_w - 1.0) > SCALE_TOL or abs(scale_h - 1.0) > SCALE_TOL:
        return "WRONG_SCALE", m
    if dcx <= POS_NEAR_EXACT_PX and dcy <= POS_NEAR_EXACT_PX and \
            abs(scale_w - 1.0) <= SCALE_TOL and abs(scale_h - 1.0) <= SCALE_TOL:
        return "EXACT", m
    return "GEOMETRICALLY_CORRECT", m


def image_truth(screenshot_path, asset_bytes, region=None, hint=None,
                contract=None):
    """Full image-truth vector for one expected visual asset.

    region: expected on-screen box (x,y,w,h) — from contract/ViewTree.
            None => unanchored whole-screen search (confidence downgraded).
    hint:   expected on-screen pixel size (w,h) when density-scaled.
    contract: optional dict {asset, expected_bounds, tolerance,
            expected_visibility, requires_original_font-...} (S93 §8).

    Returns the S93 §14 vector; each field PASS/FAIL/PARTIAL/
    NOT_APPLICABLE/UNKNOWN (+note); verdict in
    {VISUALLY_VERIFIED, DECODED_ONLY, WRONG_CONTENT, WRONG_GEOMETRY,
     PLACEHOLDER, OPAQUE_REPLACEMENT, MISSING, REGION_INVALID, UNANCHORED}.
    """
    from probes.visual_probe import (_ncc, _downscale_gray, _gray,
                                     _flatten_alpha)
    out = {"schema": "s93.image_truth.v1",
           "asset_sha256": hashlib.sha256(asset_bytes).hexdigest()}
    shot = np.asarray(Image.open(screenshot_path).convert("RGB"),
                      dtype=np.float64)
    asset = _load_rgba(asset_bytes)
    A = np.asarray(asset, dtype=np.float64)
    aw, ah = asset.size

    # --- identity (decode-side truth from bytes) ---------------------------
    out["identity"] = {"value": "PASS", "note": f"png/asset {aw}x{ah}",
                       "dims": [aw, ah]}

    # --- decode: a decodable RGBA proves decode only (S93 §1 law) ----------
    out["decode"] = {"value": "PASS", "note": "RGBA decode ok"}

    # --- region extraction ---------------------------------------------------
    R_full = shot
    anchored = region is not None
    if region:
        R, eff = _region(shot, region)
        if R is None:
            out["verdict"] = "REGION_INVALID"
            out["geometry"] = {"value": "FAIL", "note": "region invalid"}
            return out
        out["region"] = list(eff)
    else:
        R = R_full
        out["region"] = None
    bg = _bg_median(R)
    page_bg = _bg_median(shot)   # screenshot-level background: region borders
                                 # lie when the content fills the region

    # --- observed structure --------------------------------------------------
    Rg = _gray(R)
    obs_nonbg = (np.abs(R - page_bg.reshape(1, 1, 3)).max(axis=2) > 20)
    obs_comps = _components(obs_nonbg)
    obs_colors = np.unique(_quant(R), axis=0)
    n_obs_colors = int(obs_colors.shape[0])
    e_density = _edge_density(Rg)
    region_std = float(Rg.std())

    flat = np.clip(_flatten_alpha(asset, page_bg), 0, 255)

    # --- content vector ------------------------------------------------------
    reasons = []
    content_fail_kind = None

    # ink bboxes: measured (observed, region-local) and expected (contract)
    def _union_bbox(comps):
        if not comps:
            return None
        xs = [c["bbox"][0] for c in comps]
        ys = [c["bbox"][1] for c in comps]
        xe = [c["bbox"][0] + c["bbox"][2] for c in comps]
        ye = [c["bbox"][1] + c["bbox"][3] for c in comps]
        return [min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys)]

    measured_ink = _union_bbox(obs_comps)
    alpha_mask = A[:, :, 3] > 32
    asset_comps = _components(alpha_mask)
    asset_ink = _union_bbox(asset_comps)
    asset_structured = bool(asset_ink) or float(A[:, :, :3].std()) > 24.0

    rh, rw = R.shape[0], R.shape[1]
    cscale = (min(rw / aw, rh / ah) if (rw and rh) else 1.0) if anchored \
        else min(1.0, (shot.shape[1] / aw if aw else 1.0))
    expected_ink = None
    if anchored and asset_ink:
        expected_ink = [asset_ink[0] * cscale, asset_ink[1] * cscale,
                        asset_ink[2] * cscale, asset_ink[3] * cscale]

    nonbg_ratio = float(obs_nonbg.mean())

    # L-S93-IMG-4 alpha truth FIRST (most specific opaque-replacement law)
    trans_frac = float((A[:, :, 3] < 64).mean())
    alpha_note = f"transparent_fraction={trans_frac:.3f}"
    alpha_v = "NOT_APPLICABLE"
    region_uniform = region_std < 6.0
    if trans_frac >= 0.05 and R.shape[0] == A.shape[0] and \
            R.shape[1] == A.shape[1] and nonbg_ratio >= 0.5 and \
            not region_uniform:
        trans_mask = A[:, :, 3] < 64
        leak = float((np.abs(R - flat).max(axis=2) > 48)[trans_mask].mean())
        alpha_v = "FAIL" if leak > ALPHA_LEAK_MAX else "PASS"
        if leak > ALPHA_LEAK_MAX:
            content_fail_kind = "OPAQUE_REPLACEMENT"
            reasons.append(f"alpha_leak={leak:.3f}")

    # L-S93-IMG-1 solid/two-color placeholder (solid NON-BACKGROUND region)
    is_placeholder = (n_obs_colors <= SOLID_MAX_COLORS and
                      e_density < EDGE_DENSITY_MIN and nonbg_ratio >= 0.5)
    if asset_structured and content_fail_kind is None and is_placeholder:
        content_fail_kind = "PLACEHOLDER"
        reasons.append(
            f"solid/two-color region colors={n_obs_colors} "
            f"edge_density={e_density:.5f} nonbg={nonbg_ratio:.2f}")

    # blank-region law: MISSING, or WRONG_POSITION if the asset is provably
    # rendered somewhere else on screen. A uniform NON-page-background block
    # is never "blank" — it is a solid replacement (placeholder path below).
    region_uniform = region_std < 6.0
    uniform_is_page_bg = False
    if region_uniform:
        uc = R.reshape(-1, 3).mean(axis=0)
        uniform_is_page_bg = bool(
            np.abs(uc - page_bg).max() < 24)
    blank = region_uniform and uniform_is_page_bg
    found_elsewhere = None
    if anchored and blank and asset_structured:
        Sg_ds, _ = _downscale_gray(_gray(shot), max_side=160)
        Tg_nat, _ = _downscale_gray(_gray(np.clip(
            _flatten_alpha(asset, _bg_median(shot)), 0, 255)), max_side=48)
        if Sg_ds.shape[0] >= Tg_nat.shape[0] and \
                Sg_ds.shape[1] >= Tg_nat.shape[1]:
            sncc, _, _ = _ncc(Sg_ds, Tg_nat)
        else:
            sncc = -1.0
        if sncc >= 0.85:
            found_elsewhere = {"unanchored_ncc": round(sncc, 4)}

    # L-S93-IMG-2 shape truth (scale-tolerant component-layout comparison)
    if asset_structured and content_fail_kind is None and not blank:
        s_score, s_reasons = _shape_truth(asset_comps, obs_comps)
        if s_score < 1.0:
            reasons.extend(s_reasons)
        if s_score == 0.0:
            content_fail_kind = "WRONG_CONTENT"

    # template ink crop (shared by layout + NCC): asset flattened, cropped
    # to its own ink bbox — the content, not the surrounding canvas
    if asset_ink:
        ax, ay, aw2, ah2 = asset_ink
        Tcrop = flat[ay:ay + ah2, ax:ax + aw2]
    else:
        Tcrop = flat

    # L-S93-IMG-3 spatial color layout — ink-window to ink-window (scale-
    # tolerant): the asset ink crop resized to the measured ink box vs the
    # observed ink box pixels. Grids must describe the CONTENT, not the
    # surrounding canvas, or scale differences poison the comparison.
    if measured_ink and measured_ink[2] >= 4 and measured_ink[3] >= 4 and \
            asset_ink:
        Tl = np.asarray(Image.fromarray(
            Tcrop.astype(np.uint8)).resize(
                (max(2, int(measured_ink[2])),
                 max(2, int(measured_ink[3]))), Image.BILINEAR),
            dtype=np.float64)
        Rl = R[measured_ink[1]:measured_ink[1] + measured_ink[3],
               measured_ink[0]:measured_ink[0] + measured_ink[2]]
        layout = _spatial_layout(Tl, Rl)
    else:
        layout = 0.0
    if asset_structured and content_fail_kind is None and not blank and \
            layout < LAYOUT_MATCH_MIN:
        reasons.append(f"spatial_layout={layout:.2f}<{LAYOUT_MATCH_MIN}")
        content_fail_kind = "WRONG_CONTENT"

    # content NCC: template (already ink-cropped) scaled to the MEASURED ink
    # bbox (scale-tolerant; geometry, not content, judges size)
    if measured_ink and measured_ink[2] >= 4 and measured_ink[3] >= 4:
        tw = max(2, int(measured_ink[2]))
        th = max(2, int(measured_ink[3]))
        Tg = np.asarray(Image.fromarray(
            Tcrop.astype(np.uint8)).resize((tw, th), Image.BILINEAR),
            dtype=np.float64)
    else:
        Tg = Tcrop
    Tg_ds, _ = _downscale_gray(_gray(Tg))
    Rg_ds, _ = _downscale_gray(Rg, max_side=max(96, Tg_ds.shape[0] + 64,
                                                Tg_ds.shape[1] + 64))
    if Rg_ds.shape[0] >= Tg_ds.shape[0] and Rg_ds.shape[1] >= Tg_ds.shape[1]:
        ncc, dx, dy = _ncc(Rg_ds, Tg_ds)
    else:
        ncc, dx, dy = -1.0, 0, 0
    out["ncc"] = round(ncc, 4)

    # L-S93-IMG-5c clipping law: content cut, not scaled — one edge aligned
    # with the expected box, the opposite dimension falling short. A content
    # box that merely fills the region is NOT clipped.
    clipped = False
    clip_meta = {}
    if measured_ink and expected_ink and not blank:
        mx_, my_, mw_, mh_ = measured_ink
        ex_, ey_, ew_, eh_ = expected_ink
        tol = max(POS_NEAR_EXACT_PX, min(ew_, eh_) * POS_CORRECT_FRAC)
        aligned_top = abs(my_ - ey_) <= tol
        aligned_left = abs(mx_ - ex_) <= tol
        short_h = eh_ - mh_
        short_w = ew_ - mw_
        if (aligned_top and short_h > tol) or \
                (aligned_left and short_w > tol):
            clipped = True
            clip_meta = {"short_h": int(short_h), "short_w": int(short_w),
                         "aligned_top": aligned_top,
                         "aligned_left": aligned_left}

    geo, geo_m = _geometry_verdict(expected_ink or [0, 0, aw * cscale,
                                                    ah * cscale],
                                   measured_ink, clipped)
    if measured_ink:
        rx, ry = (out["region"][0], out["region"][1]) if anchored else (0, 0)
        geo_m["measured_ink_box_abs"] = [measured_ink[0] + rx,
                                         measured_ink[1] + ry,
                                         measured_ink[2], measured_ink[3]]
    if found_elsewhere:
        geo = "WRONG_POSITION"
        geo_m["found_elsewhere"] = found_elsewhere
    out["geometry"] = {
        "value": {"EXACT": "PASS", "NEAR_EXACT": "PASS",
                  "GEOMETRICALLY_CORRECT": "PASS", "PARTIAL": "PARTIAL",
                  "WRONG_POSITION": "FAIL", "WRONG_SCALE": "FAIL",
                  "CLIPPED": "FAIL", "MISSING": "FAIL"}[geo],
        "tolerance_class": geo, **geo_m}

    # --- combine content verdict (multi-metric, never single) ---------------
    if content_fail_kind == "PLACEHOLDER":
        content_v, verdict = "FAIL", "PLACEHOLDER"
    elif content_fail_kind == "OPAQUE_REPLACEMENT":
        content_v, verdict = "FAIL", "OPAQUE_REPLACEMENT"
    elif blank:
        content_v = "FAIL"
        verdict = "WRONG_POSITION" if found_elsewhere else "MISSING"
    elif content_fail_kind == "WRONG_CONTENT":
        content_v, verdict = "FAIL", "WRONG_CONTENT"
    elif clipped:
        # right content family, right place, incomplete: honest partial.
        # Gate with the VISIBLE-PART NCC (crop the template to the visible
        # sub-box) so "clipped" can never excuse wrong content.
        vis_v = "PARTIAL"
        if asset_ink and measured_ink:
            ex_, ey_, _, _ = expected_ink
            sx = int(max(0, measured_ink[0] - ex_))
            sy = int(max(0, measured_ink[1] - ey_))
            sw = int(min(Tcrop.shape[1] - sx, measured_ink[2]))
            sh = int(min(Tcrop.shape[0] - sy, measured_ink[3]))
            if sw >= 4 and sh >= 4:
                Tvis = Tcrop[sy:sy + sh, sx:sx + sw]
                Tvis_r = np.asarray(Image.fromarray(
                    Tvis.astype(np.uint8)).resize(
                        (max(2, int(measured_ink[2])),
                         max(2, int(measured_ink[3]))), Image.BILINEAR),
                    dtype=np.float64)
                Tv_ds, _ = _downscale_gray(_gray(Tvis_r))
                Rv = R[measured_ink[1]:measured_ink[1] + measured_ink[3],
                       measured_ink[0]:measured_ink[0] + measured_ink[2]]
                Rv_ds, _ = _downscale_gray(
                    _gray(Rv), max_side=max(96, Tv_ds.shape[0] + 64,
                                            Tv_ds.shape[1] + 64))
                if Rv_ds.shape == Tv_ds.shape:
                    wm = Rv_ds - Rv_ds.mean()
                    tm = Tv_ds - Tv_ds.mean()
                    dn = np.linalg.norm(wm) * np.linalg.norm(tm)
                    vis_ncc = float(np.sum(wm * tm) / dn) if dn else 0.0
                    out["visible_part_ncc"] = round(vis_ncc, 4)
                    if vis_ncc < 0.60:
                        vis_v = "FAIL"
        if vis_v == "FAIL":
            content_v, verdict = "FAIL", "WRONG_CONTENT"
        else:
            content_v, verdict = "PARTIAL", "VISUALLY_PARTIAL"
        geo_m["clip"] = clip_meta
        out["geometry"]["clip"] = clip_meta
    else:
        strong = ncc >= 0.90
        corroborated = (ncc >= 0.72 and layout >= LAYOUT_MATCH_MIN) or \
            (ncc >= 0.72 and e_density >= EDGE_DENSITY_MIN)
        structure_ok = (not asset_structured) or (layout >= LAYOUT_MATCH_MIN)
        if strong or (corroborated and structure_ok):
            content_v, verdict = "PASS", None
        elif ncc >= 0.72 or layout >= LAYOUT_MATCH_MIN:
            content_v, verdict = "PARTIAL", None
        else:
            content_v, verdict = "FAIL", "WRONG_CONTENT"

    # --- fill the vector -----------------------------------------------------
    out["color"] = {"value": "PASS" if n_obs_colors > SOLID_MAX_COLORS
                    or not asset_structured else "FAIL",
                    "distinct_colors": n_obs_colors}
    out["edges"] = {"value": "PASS" if e_density >= EDGE_DENSITY_MIN
                    or not asset_structured else "FAIL",
                    "edge_density": round(e_density, 5)}
    out["texture"] = {"value": "PASS" if region_std >= 6.0
                      or not asset_structured else "FAIL",
                      "region_stddev": round(region_std, 2)}
    out["content"] = {"value": content_v, "reasons": reasons[:8],
                      "spatial_layout": round(layout, 4),
                      "components": {"asset": len(asset_comps),
                                     "observed": len(obs_comps)}}
    out["alpha"] = {"value": alpha_v, "note": alpha_note}
    out["position"] = out["geometry"]
    out["text"] = {"value": "NOT_APPLICABLE",
                   "note": "use semantic_text for text-bearing surfaces"}
    out["temporal"] = {"value": "NOT_APPLICABLE",
                       "note": "use semantic_animation for animated assets"}
    out["interaction"] = {"value": "NOT_APPLICABLE",
                          "note": "use interaction probe"}
    out["provenance"] = {"value": "UNKNOWN" if not contract
                         else contract.get("confidence", "UNKNOWN"),
                         "note": "PROVENANCE_UNKNOWN unless contract links "
                                 "resource->decode->draw evidence"}
    if not anchored and verdict is None:
        verdict = "UNANCHORED"
    out["verdict"] = verdict or (
        "VISUALLY_VERIFIED" if content_v == "PASS" and
        out["geometry"]["value"] == "PASS" else
        "WRONG_GEOMETRY" if content_v == "PASS" else "VISUALLY_PARTIAL")
    return out


# ---------------------------------------------------------------------------
# L-S93-IMG-6 region partition (S93 §15)
# ---------------------------------------------------------------------------

def region_partition(screenshot_path, regions):
    """Per-region evidence over named screen partitions.

    regions: {name: [x,y,w,h]}. Each region gets nonblank/structure stats.
    Aggregation law: the aggregate is FAIL if ANY region fails its own
    expectation — a missing button can never be averaged away.
    """
    from probes.visual_probe import _gray
    shot = np.asarray(Image.open(screenshot_path).convert("RGB"),
                      dtype=np.float64)
    out = {}
    for name, box in (regions or {}).items():
        R, eff = _region(shot, box)
        if R is None:
            out[name] = {"region": list(box), "value": "FAIL",
                         "reason": "region_invalid"}
            continue
        Rg = _gray(R)
        bg = _bg_median(R)
        nonbg = float((np.abs(R - bg.reshape(1, 1, 3)).max(axis=2)
                       > 20).mean())
        out[name] = {
            "region": list(eff),
            "value": "PASS" if Rg.std() >= 6.0 or nonbg >= 0.02
            else "FAIL",
            "stddev": round(float(Rg.std()), 2),
            "nonbg_ratio": round(nonbg, 4),
            "reason": None if (Rg.std() >= 6.0 or nonbg >= 0.02)
            else "blank_or_uniform_region",
        }
    out["aggregate"] = {
        "value": "FAIL" if any(v.get("value") == "FAIL"
                               for k, v in out.items() if k != "aggregate")
        else "PASS",
        "failed_regions": [k for k, v in out.items()
                           if k != "aggregate" and v.get("value") == "FAIL"],
    }
    return out
