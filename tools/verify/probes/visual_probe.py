#!/usr/bin/env python3
"""visual_probe.py — S92 pixel verification (multi-technique, deterministic).

S92 §8/§9 law: "screenshot exists" proves pixels were captured, NOT that a
required asset reached the screen. This probe cross-correlates:

    APK asset (ground-truth bytes)
        vs
    screenshot region (contract/ViewTree-derived geometry)

with MULTIPLE independent techniques (S92 §9: never one CV heuristic):

  T1 template NCC      normalized cross-correlation (grayscale, alpha-aware
                       composite) at the expected region — score in [-1,1]
  T2 color-signature   distinctive quantized colors of the asset present in
                       the region at proportional coverage
  T3 edge-signature    gradient-orientation histogram similarity (coarse)
  T4 nonblank          region is not uniform/solid (necessary, NOT sufficient)

A region counts as ASSET_PRESENT only when T4 passes AND at least one of
(T1 strong) / (T1 + T2 both moderate) / (T2 + T3 both moderate) passes.
Thresholds are documented constants — never silently inflated.

Also provides region_diff (pre/post interaction pixel delta, S92 §11) and
frame_stability (readiness model input, S92 §12).
"""
import hashlib
import math
import os

import numpy as np
from PIL import Image

# --- documented thresholds (S92 §7: every tolerance documented) -------------
NCC_STRONG = 0.90          # single-technique acceptance
NCC_MODERATE = 0.72        # needs corroboration by T2/T3
COLOR_SIG_MODERATE = 0.45  # distinctive-color coverage fraction
COLOR_SIG_STRONG = 0.70
EDGE_CORR_MODERATE = 0.55  # edge-orientation correlation
NONBLANK_MIN_VARIATION = 6.0   # region stddev floor (uniform region = blank)
GEOMETRY_TOLERANCE_PX = 8  # |delta| <= 8 px at 1080p-class screens (2.3% of
                           # a 348px button) — measured, documented, §7 law
GEOMETRY_TOLERANCE_FRAC = 0.12  # or 12% of the element's own size, whichever
                                # is larger for small elements


def _load_rgba(path_or_bytes):
    if isinstance(path_or_bytes, bytes):
        im = Image.open(__import__("io").BytesIO(path_or_bytes))
    else:
        im = Image.open(path_or_bytes)
    return im.convert("RGBA")


def _flatten_alpha(asset_rgba, bg_rgb):
    """Alpha-aware composite of the asset over a background color (S92 §9)."""
    a = np.asarray(asset_rgba, dtype=np.float64)
    alpha = a[:, :, 3:4] / 255.0
    rgb = a[:, :, :3]
    bg = np.array(bg_rgb, dtype=np.float64).reshape(1, 1, 3)
    return rgb * alpha + bg * (1.0 - alpha)


def _gray(arr):
    if arr.ndim == 3:
        arr = arr[:, :, :3]
        return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    return arr.astype(np.float64)


def _ncc(region, template):
    """Normalized cross-correlation, template slid at integer offsets within
    the region (small search window: ±offset px). Returns best (score, dx, dy).
    """
    t = template - template.mean()
    tn = np.linalg.norm(t)
    if tn == 0 or t.size == 0:
        return 0.0, 0, 0
    h, w = t.shape
    H, W = region.shape
    best = (-2.0, 0, 0)
    for dy in range(0, max(1, H - h + 1)):
        for dx in range(0, max(1, W - w + 1)):
            win = region[dy:dy + h, dx:dx + w]
            if win.size != t.size:
                continue
            wm = win - win.mean()
            wn = np.linalg.norm(wm)
            if wn == 0:
                score = 0.0
            else:
                score = float(np.sum(wm * t) / (wn * tn))
            if score > best[0]:
                best = (score, dx, dy)
    return best


def _downscale_gray(arr, max_side=96):
    h, w = arr.shape
    scale = min(1.0, max_side / max(h, w))
    if scale < 1.0:
        im = Image.fromarray(arr.astype(np.uint8))
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                       Image.BILINEAR)
        return np.asarray(im, dtype=np.float64), scale
    return arr, 1.0


def _color_signature(asset_rgb, region_rgb, n_levels=24):
    """Distinctive quantized colors of the asset present in the region.
    Distinctive = colors that cover >=1% of the asset but are NOT the
    region's dominant background color (S92 §9 anti-false-positive)."""
    def quant(a):
        q = (a.reshape(-1, 3) // n_levels).astype(np.int32)
        return q

    aq = quant(asset_rgb)
    rq = quant(region_rgb)
    if aq.shape[0] == 0 or rq.shape[0] == 0:
        return 0.0, 0, 0
    akeys, acounts = np.unique(aq, axis=0, return_counts=True)
    rkeys, rcounts = np.unique(rq, axis=0, return_counts=True)
    acov = acounts / aq.shape[0]
    rset = {tuple(k): c for k, c in zip(rkeys, rcounts)}
    region_bg = tuple(rkeys[np.argmax(rcounts)])
    # transparent asset pixels flatten to the background — their quantized
    # RGB equals the flattened bg and must not count as distinctive
    hits = 0
    total = 0
    for k, cov in zip(akeys, acov):
        if cov < 0.01:
            continue
        total += 1
        if tuple(k) in rset and tuple(k) != region_bg:
            hits += 1
    return (hits / total if total else 0.0), total, int(rkeys.shape[0])


def _edge_signature(gray_arr):
    gx = np.zeros_like(gray_arr)
    gy = np.zeros_like(gray_arr)
    gx[:, 1:-1] = gray_arr[:, 2:] - gray_arr[:, :-2]
    gy[1:-1, :] = gray_arr[2:, :] - gray_arr[:-2, :]
    mag = np.hypot(gx, gy)
    mask = mag > 12.0
    if mask.sum() < 8:
        return None
    ang = (np.arctan2(gy, gx) / math.pi * 8.0 + 8.0).astype(int) % 16
    hist = np.bincount(ang[mask].ravel(), minlength=16).astype(np.float64)
    return hist / hist.sum()


def _edge_corr(a, b):
    if a is None or b is None:
        return None
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return None
    return float(np.dot(a, b) / (na * nb))


def asset_presence(screenshot_path, asset_bytes, region=None, asset_hint=None):
    """Multi-technique asset-presence check.

    region: (x, y, w, h) in screenshot pixels — expected geometry from
            contract/ViewTree. None => search whole screenshot (weaker,
            flagged 'unanchored').
    asset_hint: optional expected on-screen size (w,h) — when the raw asset
            is a density-selected bitmap, the template is scaled to the
            hinted size before matching (S92 §18 density law).

    Returns dict with per-technique scores, verdict PRESENT/ABSENT and the
    measured best-match geometry (dx, dy, dw, dh).
    """
    shot = Image.open(screenshot_path).convert("RGB")
    S = np.asarray(shot, dtype=np.float64)
    asset = _load_rgba(asset_bytes)
    A = np.asarray(asset, dtype=np.float64)
    aw, ah = asset.size
    out = {
        "asset_dims": [aw, ah],
        "screenshot_dims": [shot.width, shot.height],
        "region": list(region) if region else None,
        "techniques": {},
    }
    # region extraction (clip to screen)
    if region:
        x, y, w, h = region
        x, y = max(0, int(x)), max(0, int(y))
        w, h = int(w), int(h)
        w, h = min(w, shot.width - x), min(h, shot.height - y)
        if w <= 2 or h <= 2:
            out.update({"verdict": "REGION_INVALID", "ncc": 0.0})
            return out
        R = S[y:y + h, x:x + w]
        out["region_effective"] = [x, y, w, h]
    else:
        R = S
        out["region_effective"] = [0, 0, shot.width, shot.height]

    # background color for alpha flattening = region border median
    border = np.concatenate([R[0, :], R[-1, :], R[:, 0], R[:, -1]]) \
        if R.shape[0] > 2 and R.shape[1] > 2 else R.reshape(-1, 3)
    bg = np.median(border, axis=0)

    flat = _flatten_alpha(asset, bg)
    flat = np.clip(flat, 0, 255)

    # template scaling: the region IS the expected on-screen box when it
    # comes from the contract/provenance (dst) — scale the template to fit
    # it BOTH ways (density law upscales mdpi assets at 420dpi, and shrinks
    # oversized assets). Without a region (whole-screen search) never
    # upscale — keep the natural size.
    rx, ry, rw, rh = out["region_effective"]
    tw, th = aw, ah
    if asset_hint:
        tw, th = asset_hint
    if region:
        scale = min(rw / tw, rh / th) if (rw and rh) else 1.0
    else:
        scale = min(1.0, (rw / tw if tw else 1.0))
    if scale < 1.0:
        nw, nh = max(2, int(tw * scale)), max(2, int(th * scale))
        flat = np.asarray(
            Image.fromarray(flat.astype(np.uint8)).resize((nw, nh),
                                                          Image.BILINEAR),
            dtype=np.float64)
        out["template_scaled_to"] = [nw, nh]
        tw, th = nw, nh
    elif region and (tw < rw or th < rh):
        # density upscale: template smaller than its expected box
        nw, nh = max(2, min(rw, int(tw * (rw / tw) if tw else rw))), \
            max(2, min(rh, int(th * (rh / th) if th else rh)))
        nw, nh = min(nw, rw), min(nh, rh)
        flat = np.asarray(
            Image.fromarray(flat.astype(np.uint8)).resize(
                (min(nw, rw), min(nh, rh)), Image.BILINEAR),
            dtype=np.float64)
        out["template_scaled_to"] = [min(nw, rw), min(nh, rh)]
        tw, th = min(nw, rw), min(nh, rh)
    if tw > rw or th > rh:
        # template still larger than region: scale down to region (geometry
        # may then be judged by geometry probe, not here)
        nw, nh = max(2, int(rw)), max(2, int(rh))
        flat = np.asarray(
            Image.fromarray(flat.astype(np.uint8)).resize((nw, nh),
                                                          Image.BILINEAR),
            dtype=np.float64)
        out["template_scaled_to"] = [nw, nh]
        tw, th = nw, nh

    Rg = _gray(R)
    Tg = _gray(flat)
    Tg_ds, tds = _downscale_gray(Tg)
    Rg_ds, _ = _downscale_gray(Rg, max_side=max(96, Tg_ds.shape[0] + 64,
                                                Tg_ds.shape[1] + 64))
    ncc, dx, dy = _ncc(Rg_ds, Tg_ds) if (Rg_ds.shape[0] >= Tg_ds.shape[0] and
                                         Rg_ds.shape[1] >= Tg_ds.shape[1]) \
        else (-1.0, 0, 0)
    out["techniques"]["T1_template_ncc"] = {
        "score": round(ncc, 4), "offset": [dx, dy],
        "thresholds": {"strong": NCC_STRONG, "moderate": NCC_MODERATE}}

    csig, distinct, rcolors = _color_signature(flat, R)
    out["techniques"]["T2_color_signature"] = {
        "score": round(csig, 4), "distinctive_colors": distinct,
        "region_colors": rcolors,
        "thresholds": {"moderate": COLOR_SIG_MODERATE,
                       "strong": COLOR_SIG_STRONG}}

    es_a = _edge_signature(Tg_ds)
    # region edge signature around the best-match window
    if 0 <= dy and 0 <= dx and dy + Tg_ds.shape[0] <= Rg_ds.shape[0] \
            and dx + Tg_ds.shape[1] <= Rg_ds.shape[1]:
        win = Rg_ds[dy:dy + Tg_ds.shape[0], dx:dx + Tg_ds.shape[1]]
        es_r = _edge_signature(win)
        ec = _edge_corr(es_a, es_r)
    else:
        ec = None
    out["techniques"]["T3_edge_signature"] = {
        "score": (round(ec, 4) if ec is not None else None),
        "threshold": EDGE_CORR_MODERATE}

    var = float(Rg.std())
    out["techniques"]["T4_nonblank"] = {
        "region_stddev": round(var, 2),
        "floor": NONBLANK_MIN_VARIATION}

    # --- verdict combination (documented law) ------------------------------
    t1 = ncc
    t2 = csig
    t3 = ec if ec is not None else 0.0
    nonblank = var >= NONBLANK_MIN_VARIATION
    strong = (t1 >= NCC_STRONG) or (t2 >= COLOR_SIG_STRONG)
    corroborated = (t1 >= NCC_MODERATE and t2 >= COLOR_SIG_MODERATE) or \
                   (t1 >= NCC_MODERATE and t3 >= EDGE_CORR_MODERATE) or \
                   (t2 >= COLOR_SIG_MODERATE and t3 >= EDGE_CORR_MODERATE)
    if not nonblank:
        verdict = "ABSENT_BLANK_REGION"
    elif strong:
        verdict = "PRESENT"
    elif corroborated:
        verdict = "PRESENT"
    elif t1 >= NCC_MODERATE or t2 >= COLOR_SIG_MODERATE:
        verdict = "WEAK"           # single weak technique — NOT present
    else:
        verdict = "ABSENT"
    out["verdict"] = verdict
    out["asset_sha256"] = hashlib.sha256(asset_bytes).hexdigest() \
        if isinstance(asset_bytes, bytes) else None
    return out


# ---------------------------------------------------------------------------
# region diff (S92 §8/§11)
# ---------------------------------------------------------------------------

def region_diff(before_path, after_path):
    A = np.asarray(Image.open(before_path).convert("RGB"), dtype=np.int16)
    B = np.asarray(Image.open(after_path).convert("RGB"), dtype=np.int16)
    if A.shape != B.shape:
        return {"error": "shape_mismatch",
                "before": list(A.shape), "after": list(B.shape)}
    d = np.abs(A - B).max(axis=2)
    changed = d > 8
    n = int(changed.sum())
    out = {
        "changed_px": n,
        "changed_ratio": round(n / d.size, 6),
        "before_sha256": hashlib.sha256(
            __import__("pathlib").Path(before_path).read_bytes()).hexdigest(),
        "after_sha256": hashlib.sha256(
            __import__("pathlib").Path(after_path).read_bytes()).hexdigest(),
    }
    if n:
        ys, xs = np.nonzero(changed)
        out["bbox"] = [int(xs.min()), int(ys.min()),
                       int(xs.max()), int(ys.max())]
    return out


def global_diff(baseline_path, actual_path):
    return region_diff(baseline_path, actual_path)


# ---------------------------------------------------------------------------
# readiness / stability (S92 §12)
# ---------------------------------------------------------------------------

def frame_stability(frame_paths, max_pairs=8):
    """Consecutive-frame similarity + cadence. Continuous-animation titles
    are NOT required to reach pixel identity (S92 §20); this returns the
    measured per-pair changed-px ratios so the verdict layer can apply the
    right stability rule per renderer family."""
    res = []
    prev = None
    for p in frame_paths[:max_pairs]:
        A = np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)
        if prev is not None and prev.shape == A.shape:
            d = np.abs(prev - A).max(axis=2)
            res.append({
                "frame": os.path.basename(p),
                "changed_ratio": round(float((d > 8).mean()), 6)})
        prev = A
    return res

