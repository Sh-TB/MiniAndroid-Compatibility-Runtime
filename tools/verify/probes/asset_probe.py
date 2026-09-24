#!/usr/bin/env python3
"""asset_probe.py — S92 asset provenance cross-check (§4, §6).

For every required asset, reconcile THREE independent layers:

  L1 APK ground truth:    res/** bytes exist + decode (PIL) + dims
  L2 runtime provenance:  gfx_provenance.json chain bits
                          (ASSET_FOUND/RESOURCE_RESOLVED/DECODED/
                           BITMAP_CREATED/VIEW_RECEIVED/DRAW_CALLED)
  L3 screen pixels:       visual_probe.asset_presence in the expected region

Failure taxonomy (S92 §6 — each root-cause category stays distinct):
  ASSET_MISSING_IN_APK, DECODE_FAILURE, DIMENSION_MISMATCH,
  RESOLVED_WRONG_VARIANT, BOUND_BUT_NEVER_DRAWN, DRAWN_BUT_NEVER_PRESENTED
  (draw called, pixels absent), NEVER_BOUND, NEVER_REFERENCED,
  PIXEL_PRESENCE_FAIL, ALPHA_LOST, DENSITY_MISMATCH.
"""
import hashlib
import io
import json

from PIL import Image

from . import graphics_common as gc
from . import visual_probe as vp
from .visual_probe import GEOMETRY_TOLERANCE_PX as GEOM_TOL_PX

# S92 §18 density law inputs. MiniAndroid device densityDpi = 420
# (miniandroid/src/runtime/execution_engine.cpp:416, MINIANDROID_DENSITY
# override). Expected on-screen box for a density-bucketed asset:
#   expected_px = decoded_px * (RUNTIME_DENSITY_DPI / src_bucket_density)
# A mismatch here is the user-reported "icon present but wrong size" class.
RUNTIME_DENSITY_DPI = 420


def expected_display_box(decoded_w, decoded_h, src_density):
    if not src_density:
        return decoded_w, decoded_h   # DENSITY_NONE / unknown: no law
    s = RUNTIME_DENSITY_DPI / float(src_density)
    return (round(decoded_w * s), round(decoded_h * s))


def decode_asset(data):
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
        return {"decoded": True, "dims": list(im.size),
                "mode": im.mode,
                "fully_transparent": _alpha_all_zero(im)}
    except Exception as e:
        return {"decoded": False, "error": str(e)[:120]}


def _alpha_all_zero(im):
    if im.mode not in ("RGBA", "LA"):
        return False
    a = im.getchannel("A")
    lo, hi = a.getextrema()
    return hi == 0


def asset_chains(apk_path, contract, run_evidence, run_dir):
    """Build per-asset chain records; returns (chains, stage_rollup).

    stage rollup: assets_resolved / assets_decoded / assets_rendered
    values for the verdict state machine.
    """
    apk_assets = {a["path"]: a for a in gc.apk_assets(apk_path)}
    prov_events = (run_evidence.provenance or {}).get("events", []) \
        if run_evidence else []
    shot = run_evidence.screenshot if run_evidence else None

    required = (contract or {}).get("required_assets", [])
    chains = []
    any_resolved = any_decoded = any_rendered = False
    any_required = len(required) > 0
    resolved_n = decoded_n = rendered_n = 0

    for req in required:
        res_path = req.get("path")
        rec = {
            "asset": req.get("name") or res_path,
            "resource_path": res_path,
            "confidence": req.get("confidence", "apk_verified"),
        }
        data = gc.apk_extract_asset(apk_path, res_path) if apk_path else None
        if data is None:
            rec.update({"APK": "FAIL",
                        "FAILURE": "ASSET_MISSING_IN_APK"})
            chains.append(rec)
            continue
        rec["APK"] = "PASS"
        rec["apk_sha256"] = hashlib.sha256(data).hexdigest()
        dec = decode_asset(data)
        rec["decode"] = dec
        if not dec["decoded"]:
            rec["FAILURE"] = "DECODE_FAILURE"
            chains.append(rec)
            continue
        rec["DECODED"] = "PASS"
        if dec["fully_transparent"]:
            rec["FAILURE"] = "ALPHA_FULLY_TRANSPARENT"
            chains.append(rec)
            continue
        # provenance linkage: find events whose path/resid matches
        ev_match = _match_event(rec, req, prov_events)
        rec["provenance_event"] = ev_match
        drawn = bool(ev_match) and any(
            ev_match.get(k) for k in ("DRAW_CALLED", "BITMAP_CREATED"))
        bound = bool(ev_match) and ev_match.get("VIEW_RECEIVED", False)
        rec["BOUND_TO_VIEW"] = "PASS" if bound else \
            ("FAIL" if prov_events else "UNKNOWN")
        rec["DRAW_CALLED"] = "PASS" if drawn else \
            ("FAIL" if bound else "UNKNOWN")
        # density law: expected on-screen box from src bucket density (§18)
        dims = dec.get("dims") or [0, 0]
        src_d = (ev_match or {}).get("src_density") or 0
        exp_box = expected_display_box(dims[0], dims[1], src_d)
        if src_d:
            rec["expected_display_box"] = list(exp_box)
            rec["density_law"] = {
                "src_density": src_d,
                "runtime_density": RUNTIME_DENSITY_DPI,
                "note": "expected_px = decoded_px * runtime/src"}
            dst = (ev_match or {}).get("dst") or {}
            if isinstance(dst, dict) and dst.get("w") and dst.get("h"):
                tol = max(GEOM_TOL_PX,
                          int(0.12 * max(exp_box[0], exp_box[1], 1)))
                dd = [dst.get("w") - exp_box[0], dst.get("h") - exp_box[1]]
                rec["DENSITY_CHECK"] = "PASS" if all(abs(d) <= tol
                                                     for d in dd) \
                    else "FAIL"
                if rec["DENSITY_CHECK"] == "FAIL":
                    rec["FAILURE"] = "DENSITY_MISMATCH"
        # pixel presence (L3) in the expected region; priority:
        #   contract expected_bounds (non-zero) -> this run's provenance
        #   dst_region (non-zero) -> density-law box at provenance x,y
        region = req.get("expected_bounds") or []
        if len(region) == 4 and not region[2] and not region[3]:
            region = []
        if not region and ev_match:
            dr = ev_match.get("dst_region") or []
            if len(dr) == 4 and dr[2] and dr[3]:
                region = dr
        if not region and src_d and ev_match:
            d = ev_match.get("dst") or {}
            region = [d.get("x", 0), d.get("y", 0), exp_box[0], exp_box[1]]
        if shot:
            pres = vp.asset_presence(
                shot, data, region=region,
                asset_hint=req.get("expected_size"))
            rec["pixel_presence"] = {
                "verdict": pres.get("verdict"),
                "techniques": pres.get("techniques"),
                "region": pres.get("region_effective"),
            }
            present = pres.get("verdict") == "PRESENT"
            rec["PIXELS_FOUND"] = "PASS" if present else \
                ("PARTIAL" if pres.get("verdict") == "WEAK" else "FAIL")
            if not present:
                rec["FAILURE"] = ("PIXEL_PRESENCE_FAIL" if drawn else
                                  "DRAWN_BUT_NEVER_PRESENTED" if drawn else
                                  "BOUND_BUT_NEVER_DRAWN" if bound else
                                  "NEVER_BOUND")
        else:
            rec["PIXELS_FOUND"] = "UNKNOWN"
        if bound:
            any_resolved = True
            resolved_n += 1
        if dec["decoded"]:
            decoded_n += 1
            any_decoded = True
        if rec.get("PIXELS_FOUND") == "PASS":
            rendered_n += 1
            any_rendered = True
        chains.append(rec)

    rollup = {
        "assets_resolved": _stage(any_required, resolved_n, required),
        "assets_decoded": _stage(any_required, decoded_n, required),
        "assets_rendered": _stage(any_required, rendered_n, required),
        "counts": {
            "required": len(required), "resolved": resolved_n,
            "decoded": decoded_n, "rendered": rendered_n,
        },
    }
    return chains, rollup


def _stage(any_required, n_pass, required):
    if not any_required:
        return {"value": "NOT_APPLICABLE",
                "note": "contract lists no required assets"}
    if n_pass == 0:
        return {"value": "FAIL"}
    if n_pass < len(required):
        return {"value": "PARTIAL",
                "note": f"{n_pass}/{len(required)} assets"}
    return {"value": "PASS"}


def _pick_best_event(events):
    """Prefer the most complete provenance record for one asset path:
    DRAW_CALLED=true with non-zero dst beats pre-layout 0x0 records."""
    def score(ev):
        dst = ev.get("dst") or {}
        nonzero = 1 if (dst.get("w", 0) and dst.get("h", 0)) else 0
        return (1 if ev.get("DRAW_CALLED") else 0, nonzero,
                dst.get("w", 0) or 0)
    return max(events, key=score) if events else None


def _match_event(rec, req, prov_events):
    """Match an asset to its most complete provenance event by resource
    path / name / resid. Multiple render passes produce several records;
    the best (drawn, non-zero dst) one is the binding evidence."""
    cands = []
    name = (req.get("name") or "").lower()
    for ev in prov_events:
        p = (ev.get("path") or "").lower()
        if name and (name in p or
                     (ev.get("resid") and ev.get("resid") == req.get("resid"))):
            cands.append(ev)
    if not cands:
        return None
    ev = _pick_best_event(cands)
    ev = dict(ev)
    dst = ev.get("dst") or {}
    if dst:
        ev["dst_region"] = [dst.get("x", 0), dst.get("y", 0),
                            dst.get("w", 0), dst.get("h", 0)]
    ev["matched_from"] = len(cands)
    return ev
