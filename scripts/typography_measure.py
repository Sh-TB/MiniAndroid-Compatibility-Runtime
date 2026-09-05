#!/usr/bin/env python3
"""
typography_measure.py — GOLDEN-01 typography measurement (G31–G48, Rule 10).

Measures per-line ink geometry from the trusted reference screenshot and the
MiniAndroid screenshot:

  - background (modal gray)
  - line bands (ink row clusters, gap = 1.2% of image height)
  - per-band bbox / width / height / ink count
  - per-line ink width and relative width  (width / image width)
  - text block relative height            (block bbox height / image height)
  - monospace advance via column-profile autocorrelation (primary line)
  - baseline-to-baseline spacing: band bottoms of descender-free lines
    (reference lines 1–3 end in a baseline: no descenders)
  - ink pixel count and relative ink area

All values are also expressed in FONT EM units using a candidate advance/em
ratio so the textSize / line-spacing laws can be checked quantitatively.

Usage:
  typography_measure.py <ref.png> <mini.png> [--json out.json]
"""
import json
import sys

import numpy as np
from PIL import Image


def bands_from_rows(rows, gap):
    bands = []
    start = prev = rows[0]
    for y in rows[1:]:
        if y - prev > gap:
            bands.append((start, prev))
            start = y
        prev = y
    bands.append((start, prev))
    return bands


def analyze(path, label, sysbar_frac=0.0):
    im = Image.open(path).convert("L")
    a = np.asarray(im, dtype=np.uint8)
    h, w = a.shape
    hist = np.bincount(a[::3, ::3].ravel(), minlength=256)
    bg = int(hist.argmax())
    ink = np.abs(a.astype(np.int16) - bg) > 60
    ylimit = int(h * (1.0 - sysbar_frac))
    ink[ylimit:, :] = False            # exclude platform system bar strip
    rows = np.where(ink.any(axis=1))[0]
    gap = max(4, int(round(h * 0.008)))
    bands = bands_from_rows(rows.tolist(), gap)
    out = {"label": label, "path": path, "w": w, "h": h, "bg": bg,
           "ink_total": int(ink.sum()), "sysbar_excluded_frac": sysbar_frac,
           "bands": [], "lines": []}
    cols_all = np.where(ink.any(axis=0))[0]
    y0 = int(bands[0][0]) if bands else 0
    y1 = int(bands[-1][1]) if bands else 0
    x0 = int(cols_all[0]) if len(cols_all) else 0
    x1 = int(cols_all[-1]) if len(cols_all) else 0
    out["block_bbox"] = [x0, y0, x1, y1]
    out["block_width"] = x1 - x0 + 1
    out["block_height"] = y1 - y0 + 1
    out["rel_block_width"] = out["block_width"] / w
    out["rel_block_height"] = out["block_height"] / h
    out["cx"] = (x0 + x1) / 2 / w
    out["cy"] = (y0 + y1) / 2 / h

    for bi, (by0, by1) in enumerate(bands):
        sub = ink[by0:by1 + 1, :]
        cols = np.where(sub.any(axis=0))[0]
        lx0, lx1 = int(cols[0]), int(cols[-1])
        rec = {
            "band": bi, "y0": int(by0), "y1": int(by1),
            "height": int(by1 - by0 + 1),
            "x0": lx0, "x1": lx1, "width": int(lx1 - lx0 + 1),
            "ink": int(sub.sum()),
            "rel_width": (lx1 - lx0 + 1) / w,
        }
        # monospace advance: autocorrelation of the column profile with
        # harmonic collapse (a 2x-period peak is only trusted if its half-
        # lag also shows strong periodicity).
        prof = sub.sum(axis=0).astype(np.float64)
        prof = prof - prof.mean()
        if prof.size > 16 and lx1 - lx0 > 8:
            n = prof.size
            f = np.fft.rfft(prof, 2 * n)
            ac = np.fft.irfft(f * np.conj(f))[:n]
            ac /= ac[0] if ac[0] else 1
            lo = max(4, int(n * 0.06))
            hi = max(lo + 4, int(n * 0.55))
            seg = ac[lo:hi]
            if seg.size:
                lag = int(seg.argmax()) + lo
                # harmonic collapse: while a half-lag peak is nearly as good,
                # prefer the shorter period (2x harmonics are common).
                for div in (4, 3, 2):
                    h2 = lag // div
                    if h2 >= lo and ac[h2] >= 0.55 * ac[lag]:
                        lag = h2
                        break
                if ac[lag] > 0.25:      # confident periodicity
                    rec["advance_px"] = float(lag)
                    rec["advance_conf"] = float(ac[lag])
        out["lines"].append(rec)

    # baseline-to-baseline: use band bottoms of consecutive bands (bands with
    # descenders are still bottoms — caller knows which lines have them).
    bottoms = [r["y1"] for r in out["lines"]]
    tops = [r["y0"] for r in out["lines"]]
    out["top_to_top"] = [tops[i + 1] - tops[i] for i in range(len(tops) - 1)]
    out["bottom_to_bottom"] = [bottoms[i + 1] - bottoms[i]
                               for i in range(len(bottoms) - 1)]
    return out


def main():
    ref = analyze(sys.argv[1], "reference_phone", sysbar_frac=0.07)
    mini = analyze(sys.argv[2], "miniandroid")
    print(json.dumps({"reference": ref, "miniandroid": mini}, indent=1))
    if "--json" in sys.argv:
        outp = sys.argv[sys.argv.index("--json") + 1]
        with open(outp, "w") as f:
            json.dump({"reference": ref, "miniandroid": mini}, f, indent=1)
        print("wrote", outp, file=sys.stderr)


if __name__ == "__main__":
    main()
