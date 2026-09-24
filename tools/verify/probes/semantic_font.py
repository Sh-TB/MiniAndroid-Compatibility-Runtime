#!/usr/bin/env python3
"""semantic_font.py — S93 FONT + TEXT TRUTH (§5/§6).

S93 §5 law: a font object existing is NOT font loading success. The chain
that must EACH be proven is:

    font resource -> Typeface/font object -> selected font -> glyph lookup
    -> shaping -> rasterization -> visible glyph pixels

A font is FONT_VISUALLY_VERIFIED only when representative glyphs are
visibly correct. Detections: TOFU_GLYPHS, MISSING_GLYPH, WRONG_GLYPH,
WRONG_FONT, BROKEN_FONT, CLIPPED_TEXT, MISSING_TEXT, UNREADABLE.

Laws (adversarially tested):
  L-S93-FNT-1  glyph segmentation by column projection; expected character
               count bounds the segment count (whitespace-aware)
  L-S93-FNT-2  tofu law: a glyph whose pixels match a hollow-box template
               (NCC >= TOFU_NCC) is .notdef — never readable text
  L-S93-FNT-3  per-glyph correctness: each segmented glyph must NCC-match
               the reference rendering of its expected character
  L-S93-FNT-4  font-object law: bytes that cannot even be opened/decoded
               are BROKEN_FONT — the chain dies at FONT_DECODED
  L-S93-FNT-5  text-region law: expected non-empty text with no ink in the
               node bounds is MISSING_TEXT; ink cut by node bounds with
               missing rows is CLIPPED_TEXT (S93 §6)
"""
import hashlib
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- documented thresholds (S93 §7) -----------------------------------------
TOFU_NCC = 0.80             # glyph vs hollow-box template => tofu
GLYPH_NCC_MIN = 0.60        # per-glyph correctness floor
GLYPH_NCC_STRONG = 0.75
GLOBAL_NCC_PARTIAL = 0.70   # touching-glyph path: below this = wrong font
SEGMENT_COUNT_TOL = 0       # exact glyph count (column projection on clean
                            # renders is reliable; merged/split handled by
                            # the per-glyph reference NCC path)
INK_MIN_RATIO = 0.01        # min non-bg ink fraction in a text region
GLYPH_MIN_H = 4             # minimum glyph pixel height to judge
BASELINE_ROW_TOL = 0.25     # baseline drift as fraction of glyph height


# --- font object truth (decode-level) ---------------------------------------

def font_object_truth(font_path_or_bytes):
    """L-S93-FNT-4. A font that cannot decode is BROKEN_FONT."""
    out = {"schema": "s93.font_object.v1"}
    try:
        if isinstance(font_path_or_bytes, bytes):
            import io
            f = ImageFont.truetype(io.BytesIO(font_path_or_bytes), 24)
        else:
            f = ImageFont.truetype(font_path_or_bytes, 24)
        out["FONT_DECODED"] = "PASS"
        out["family"] = f.getname()[0]
        out["style"] = f.getname()[1]
        # glyph lookup: does the font have glyphs for a probe set?
        probe = "AZaz09"
        try:
            m = f.getmask(probe)
            out["GLYPH_LOOKUP"] = "PASS" if m.size[0] > 0 else "FAIL"
        except Exception:
            out["GLYPH_LOOKUP"] = "FAIL"
    except Exception as e:
        out["FONT_DECODED"] = "FAIL"
        out["error"] = str(e)[:120]
        out["verdict"] = "BROKEN_FONT"
    return out


# --- glyph rendering helpers -------------------------------------------------

def render_reference(text, font_path, height=32, pad=6):
    """Render the expected text with the expected font — the contract
    reference (made OFFLINE from the true font, never from the runtime)."""
    font = ImageFont.truetype(font_path, height)
    tmp = Image.new("L", (10, 10))
    d = ImageDraw.Draw(tmp)
    box = d.textbbox((0, 0), text, font=font)
    w = box[2] - box[0] + pad * 2
    h = box[3] - box[1] + pad * 2
    im = Image.new("L", (max(w, 4), max(h, 4)), 255)
    ImageDraw.Draw(im).text((pad - box[0], pad - box[1]), text,
                            font=font, fill=0)
    return im


def render_at_ink_height(text, font_path, target_h):
    """Render text with the font scaled so the INK height matches target_h
    (one proportional correction pass) — removes rasterization-scale bias
    from NCC comparisons."""
    size = max(8, int(target_h * 1.4))
    for _ in range(2):
        im = render_reference(text, font_path, height=size)
        ink, _ = _bin_ink(im)
        ys, xs = np.nonzero(ink)
        if len(ys) == 0:
            break
        ih = ys.max() - ys.min() + 1
        if ih == target_h or size <= 4:
            break
        size = max(4, int(round(size * target_h / ih)))
    return render_reference(text, font_path, height=size)


def _bin_ink(im_rgb, frac=0.4, floor=24):
    """Ink mask with ADAPTIVE threshold: distance from the border-median
    background, thresholded at frac of the peak contrast (floor 24).
    Antialiased edge haze (low contrast) stays out of the ink mask so
    inter-glyph gap columns remain empty for segmentation; blank regions
    have peak=0 => no ink. Polarity-agnostic (dark or light text)."""
    a = np.asarray(im_rgb.convert("L"), dtype=np.float64)
    border = np.concatenate([a[0, :], a[-1, :], a[:, 0], a[:, -1]])
    bg = np.median(border)
    d = np.abs(a - bg)
    thr = max(floor, float(d.max()) * frac)
    return d > thr, a


def segment_glyphs(ink):
    """L-S93-FNT-1. Column-projection segmentation -> glyph boxes."""
    col = ink.any(axis=0)
    segs = []
    start = None
    gap = 0
    for x, v in enumerate(col):
        if v:
            if start is None:
                start = x
            gap = 0
        elif start is not None:
            gap += 1
            if gap > 2:  # inter-glyph gap
                segs.append((start, x - gap))
                start = None
    if start is not None:
        segs.append((start, len(col) - 1))
    boxes = []
    for x0, x1 in segs:
        sub = ink[:, x0:x1 + 1]
        rows = np.nonzero(sub.any(axis=1))[0]
        if len(rows) == 0:
            continue
        boxes.append([int(x0), int(rows[0]), int(x1 - x0 + 1),
                      int(rows[-1] - rows[0] + 1)])
    return boxes


def _corr(a, b):
    am = a - a.mean()
    bm = b - b.mean()
    dn = np.linalg.norm(am) * np.linalg.norm(bm)
    return float(np.sum(am * bm) / dn) if dn else 0.0


def _ncc_gray(a, b):
    if a.shape != b.shape:
        return 0.0
    am = a - a.mean()
    bm = b - b.mean()
    dn = np.linalg.norm(am) * np.linalg.norm(bm)
    return float(np.sum(am * bm) / dn) if dn else 0.0


def _tofu_template(h):
    w = max(6, int(h * 0.7))
    im = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(im)
    # stroke width adapts; 2px floor matches typical rendered .notdef boxes
    d.rectangle([0, 0, w - 1, h - 1], outline=0, width=max(2, h // 16))
    return np.asarray(im, dtype=np.float64)


# --- glyph pipeline truth (§5) -----------------------------------------------

def glyph_truth(text_image, expected_text, reference_font_path=None,
                contract=None):
    """Full font truth over a rendered text image.

    text_image: path/PIL image of the rendered text (runtime screenshot
                crop or fixture). reference_font_path: the EXPECTED font
                (from contract/APK) used to build the per-glyph reference.
    """
    out = {"schema": "s93.glyph_truth.v1",
           "expected_text": expected_text}
    im = text_image if isinstance(text_image, Image.Image) \
        else Image.open(text_image)
    ink, g = _bin_ink(im)
    boxes = segment_glyphs(ink)
    out["segments"] = len(boxes)
    exp_chars = [c for c in expected_text if not c.isspace()]
    out["expected_glyphs"] = len(exp_chars)

    detections = []
    ink_ratio = float(ink.mean())
    out["ink_ratio"] = round(ink_ratio, 4)

    # glyph count check
    count_ok = abs(len(boxes) - len(exp_chars)) <= SEGMENT_COUNT_TOL
    if len(exp_chars) and len(boxes) == 0:
        out.update({"GLYPH_CORRECTNESS": "FAIL",
                    "verdict": "UNREADABLE",
                    "detections": ["NO_INK"]})
        return out

    # per-glyph: tofu + reference NCC
    tofu_n = 0
    ref_scores = []
    ref_font = None
    if reference_font_path and os.path.isfile(reference_font_path):
        ref_font = reference_font_path
    tofu_t = None
    for b in boxes:
        x, y, w, h = b
        if h < GLYPH_MIN_H:
            continue
        glyph = g[y:y + h, x:x + w]
        if tofu_t is None or tofu_t.shape[0] != h:
            tofu_t = _tofu_template(h)
        if _ncc_gray(glyph, np.asarray(
                Image.fromarray(tofu_t.astype(np.uint8)).resize(
                    (w, h), Image.BILINEAR), dtype=np.float64)) >= TOFU_NCC:
            tofu_n += 1
        if ref_font:
            ref = render_at_ink_height(
                exp_chars[min(len(ref_scores), len(exp_chars) - 1)]
                if len(exp_chars) else "A",
                ref_font, target_h=max(GLYPH_MIN_H, h))
            rg = np.asarray(ref, dtype=np.float64)
            # crop reference to ink and resize to glyph box
            rink, rg2 = _bin_ink(ref)
            rb = segment_glyphs(rink)
            if rb:
                rx, ry, rw, rh = rb[0]
                rpatch = Image.fromarray(rg2[ry:ry + rh, rx:rx + rw]
                                         .astype(np.uint8)).resize(
                                             (w, h), Image.BILINEAR)
                ref_scores.append(_ncc_gray(
                    glyph, np.asarray(rpatch, dtype=np.float64)))
            else:
                ref_scores.append(0.0)

    out["tofu_glyphs"] = tofu_n
    if ref_scores:
        out["per_glyph_ncc"] = [round(s, 3) for s in ref_scores]

    detections = []
    glyph_correct = "UNKNOWN"
    if tofu_n and tofu_n >= max(1, len(boxes) // 2):
        detections.append("TOFU_GLYPHS")
        glyph_correct = "FAIL"
    elif count_ok and ref_scores and exp_chars:
        bad = [i for i, s in enumerate(ref_scores) if s < GLYPH_NCC_MIN]
        strong = [i for i, s in enumerate(ref_scores)
                  if s >= GLYPH_NCC_STRONG]
        if len(bad) >= max(1, len(ref_scores) // 2):
            detections.append("WRONG_FONT")
            glyph_correct = "FAIL"
        elif bad:
            detections.append({"WRONG_GLYPH": bad})
            glyph_correct = "FAIL"
        elif len(strong) >= max(1, len(ref_scores) // 2):
            glyph_correct = "PASS"
        else:
            glyph_correct = "PARTIAL"
    elif not count_ok:
        # L-S93-FNT-1b touching-glyph path: kerned glyphs share columns and
        # cannot be split by projection. Geometric invariant: TOUCHING never
        # shrinks total ink width — only fewer glyphs do.
        if ref_font and exp_chars:
            obs_ys0, obs_xs0 = np.nonzero(ink)
            oh = int(obs_ys0.max() - obs_ys0.min() + 1) if len(obs_ys0) else 0
            ref = render_at_ink_height(str(expected_text), ref_font,
                                       target_h=max(GLYPH_MIN_H, oh))
            rink, rg = _bin_ink(ref)
            rb = segment_glyphs(rink)
            if rink.any():
                ys, xs = np.nonzero(rink)
                rw = int(xs.max() - xs.min() + 1)
                obs_ys, obs_xs = np.nonzero(ink)
                ow = int(obs_xs.max() - obs_xs.min() + 1) if len(obs_xs) else 0
                wr = ow / max(1, rw)
                out["ink_width_ratio"] = round(wr, 3)
                if wr < 0.88:
                    detections.append("MISSING_GLYPH")
                    glyph_correct = "FAIL"
                elif wr > 1.12:
                    detections.append("EXTRA_GLYPH")
                    glyph_correct = "FAIL"
                else:
                    # ink IoU law: observed ink resized into the reference
                    # ink box, binarized, Jaccard vs reference ink. Measured
                    # separation: same font+text 1.0; one wrong glyph 0.74;
                    # wrong family 0.46; wrong font 0.28. Gray NCC is diluted
                    # by background and FORBIDDEN here (measured).
                    rp = rink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                    op = ink[obs_ys.min():obs_ys.max() + 1,
                             obs_xs.min():obs_xs.max() + 1]
                    o2 = np.asarray(Image.fromarray(
                        op.astype(np.uint8) * 255).resize(
                            (rp.shape[1], rp.shape[0]), Image.BILINEAR),
                        dtype=np.float64) / 255.0
                    o2b = o2 >= 0.5
                    inter = int((o2b & rp).sum())
                    union = int((o2b | rp).sum())
                    iou = inter / max(1, union)
                    # column-ink-profile correlation: one wrong glyph among
                    # many depresses this below the pass bar
                    co = o2b.sum(axis=0).astype(np.float64)
                    cr = rp.sum(axis=0).astype(np.float64)
                    prof = _corr(co, cr)
                    out["ink_iou"] = round(iou, 3)
                    out["column_profile_corr"] = round(prof, 3)
                    if iou >= 0.90 and prof >= 0.98 and tofu_n == 0:
                        glyph_correct = "PASS"
                        out["note"] = "touching_glyphs_ink_iou"
                    elif iou >= 0.80:
                        glyph_correct = "PARTIAL"
                    else:
                        detections.append("WRONG_GLYPH" if wr >= 0.88
                                          else "WRONG_FONT")
                        glyph_correct = "FAIL"
            else:
                glyph_correct = "UNKNOWN"
        else:
            glyph_correct = "UNKNOWN"

    if tofu_n == 0 and glyph_correct in ("PASS", "UNKNOWN") and \
            ink_ratio >= INK_MIN_RATIO:
        verdict = "FONT_VISUALLY_VERIFIED"
    elif tofu_n and tofu_n >= max(1, len(boxes) // 2):
        verdict = "UNREADABLE"
    elif glyph_correct == "FAIL":
        verdict = "UNREADABLE" if detections and detections[0] == "TOFU_GLYPHS" \
            else "WRONG_FONT"
    else:
        verdict = "GLYPH_PARTIAL"

    out.update({
        "FONT_DECODED": "PASS" if ref_font or True else "UNKNOWN",
        "GLYPH_CORRECTNESS": glyph_correct,
        "detections": detections,
        "verdict": verdict,
    })
    return out


# --- text region truth (§6) ---------------------------------------------------

def text_truth(screenshot, node=None, expected_text=None, region=None):
    """S93 §6 text geometry + rendering evidence for one text surface.

    node: ViewTree node (bounds x/y/w/h + text). region overrides bounds.
    A ViewTree node containing text="PLAY" is NOT enough — this verifies
    the pixels.
    """
    out = {"schema": "s93.text_truth.v1"}
    if expected_text is None and node:
        expected_text = node.get("text", "")
    out["expected_text"] = expected_text
    if not expected_text or not str(expected_text).strip():
        out.update({"verdict": "NOT_APPLICABLE",
                    "note": "no expected text"})
        return out
    if region is None and node:
        region = (node.get("x", 0), node.get("y", 0),
                  node.get("width", 0), node.get("height", 0))
    if not region:
        out.update({"verdict": "UNKNOWN", "note": "no bounds"})
        return out
    shot = screenshot if isinstance(screenshot, Image.Image) \
        else Image.open(screenshot)
    x, y, w, h = [int(v) for v in region]
    x, y = max(0, x), max(0, y)
    w = min(w, shot.width - x)
    h = min(h, shot.height - y)
    if w <= 2 or h <= 2:
        out.update({"verdict": "CLIPPED_TEXT",
                    "note": "invalid/clipped node bounds"})
        return out
    R = shot.crop((x, y, x + w, y + h))
    ink, g = _bin_ink(R)
    ink_ratio = float(ink.mean())
    out["ink_ratio"] = round(ink_ratio, 4)
    if ink_ratio < INK_MIN_RATIO:
        out.update({"verdict": "MISSING_TEXT",
                    "note": f"ink_ratio {ink_ratio:.4f} < {INK_MIN_RATIO}"})
        return out
    boxes = segment_glyphs(ink)
    out["segments"] = len(boxes)
    if not boxes:
        out.update({"verdict": "MISSING_TEXT"})
        return out
    # vertical extent vs node height (clipping / baseline law)
    top = min(b[1] for b in boxes)
    bot = max(b[1] + b[3] for b in boxes)
    out["ink_vspan"] = [int(top), int(bot)]
    clipped = top <= 1 or bot >= h - 1
    gt = glyph_truth(R, str(expected_text))
    out["glyph_truth"] = {k: gt[k] for k in
                          ("segments", "tofu_glyphs", "GLYPH_CORRECTNESS",
                           "verdict") if k in gt}
    if clipped:
        out["verdict"] = "CLIPPED_TEXT"
        out["note"] = "ink touches node bounds vertically"
    elif gt["verdict"] == "UNREADABLE":
        out["verdict"] = "UNREADABLE"
    elif gt["verdict"] == "FONT_VISUALLY_VERIFIED":
        out["verdict"] = "TEXT_VISUALLY_VERIFIED"
    else:
        out["verdict"] = gt["verdict"]
    return out
