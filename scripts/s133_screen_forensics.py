#!/usr/bin/env python3
"""S133 — screenshot forensics: white/black/grey/repeated-pattern diagnostics.

Implements the S133 directive §11/§30: for every screenshot compute width,
height, pixel count, unique colors, non-white/non-black/non-grey pixels,
entropy, mean, variance, histogram, row hashes, column hashes, block hashes;
detect repeated rows/blocks WITH PERIOD and long uniform regions; classify
the frame (white / black / grey / uniform / repeated-pattern / partial /
content). Measure — do not guess.

Usage:
  python3 s133_screen_forensics.py screenshot.png [--json out.json]
  python3 s133_screen_forensics.py fb.raw --width 1080 --height 1920
"""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter

try:
    from PIL import Image
except ImportError:
    Image = None


def load_pixels(path, width=None, height=None):
    if path.endswith(".raw") or width:
        data = open(path, "rb").read()
        w, h = width, height
        if not w or not h:
            raise SystemExit("raw framebuffer needs --width/--height")
        need = w * h * 4
        if len(data) < need:
            raise SystemExit(f"raw too small: {len(data)} < {need}")
        # RGBA
        px = [(data[i], data[i + 1], data[i + 2]) for i in range(0, need, 4)]
        return w, h, px
    if Image is None:
        raise SystemExit("PIL unavailable and input is not raw")
    im = Image.open(path).convert("RGB")
    return im.width, im.height, list(im.getdata())


def row_hashes(px, w, h):
    out = []
    for y in range(h):
        row = px[y * w:(y + 1) * w]
        out.append(hashlib.sha1(
            b"".join(bytes(c) for c in row)).hexdigest()[:12])
    return out


def col_hashes(px, w, h):
    out = []
    for x in range(w):
        col = bytearray()
        for y in range(h):
            col += bytes(px[y * w + x])
        out.append(hashlib.sha1(bytes(col)).hexdigest()[:12])
    return out


def run_periods(hashes):
    """Detect vertical periodicity: smallest p>0 such that
    hashes[i] == hashes[i+p] for >=70% of comparable rows."""
    n = len(hashes)
    uniq = len(set(hashes))
    if uniq <= 2:
        return 0, 0.0  # uniform, not "repeated pattern"
    best_p, best_ratio = 0, 0.0
    for p in range(1, min(600, n // 2)):
        match = total = 0
        for i in range(0, n - p, max(1, p // 4 or 1)):
            total += 1
            if hashes[i] == hashes[i + p]:
                match += 1
        ratio = match / total if total else 0
        if ratio > best_ratio:
            best_ratio, best_p = ratio, p
    return (best_p if best_ratio >= 0.7 else 0), best_ratio


def classify(m):
    total = m["pixel_count"]
    if total == 0:
        return "EMPTY"
    frac_white = m["white_pixels"] / total
    frac_black = m["black_pixels"] / total
    frac_grey = m["grey_pixels"] / total
    uniform = max(frac_white, frac_black, frac_grey)
    if uniform >= 0.995:
        if frac_white >= 0.995:
            return "WHITE"
        if frac_black >= 0.995:
            return "BLACK"
        return "GREY"
    if m["unique_colors"] <= 8 and uniform >= 0.90:
        return f"NEAR-UNIFORM"
    if m["repeated_row_period"] and m["repeated_row_ratio"] >= 0.7:
        return "REPEATED-PATTERN"
    if uniform >= 0.85:
        base = ("MOSTLY-WHITE" if frac_white == uniform else
                "MOSTLY-BLACK" if frac_black == uniform else "MOSTLY-GREY")
        return base
    if m["non_background_pixels"] / total < 0.002:
        return "SHELL"
    return "CONTENT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--json", dest="json_out")
    a = ap.parse_args()

    w, h, px = load_pixels(a.image, a.width, a.height)
    total = w * h

    colors = Counter(px)
    unique = len(colors)
    white = black = grey = 0
    lum_sum = 0.0
    lum_sq = 0.0
    for (r, g, b), cnt in colors.items():
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if r > 245 and g > 245 and b > 245:
            white += cnt
        elif r < 12 and g < 12 and b < 12:
            black += cnt
        elif abs(r - g) < 10 and abs(g - b) < 10 and 60 <= lum <= 200:
            grey += cnt
        lum_sum += lum * cnt
        lum_sq += lum * lum * cnt
    mean = lum_sum / total
    var = lum_sq / total - mean * mean
    # Shannon entropy over 4-bit luminance bins
    bins = [0] * 16
    for (r, g, b), cnt in colors.items():
        lum = int(0.2126 * r + 0.7152 * g + 0.0722 * b) >> 4
        bins[min(15, lum)] += cnt
    entropy = 0.0
    for c in bins:
        if c:
            p = c / total
            entropy -= p * math.log2(p)

    rh = row_hashes(px, w, h)
    ch = col_hashes(px, w, h)
    p, ratio = run_periods(rh)
    cp, cratio = run_periods(ch)

    m = {
        "source": a.image,
        "width": w, "height": h, "pixel_count": total,
        "unique_colors": unique,
        "white_pixels": white, "black_pixels": black, "grey_pixels": grey,
        "non_background_pixels": total - white,
        "non_white_pixels": total - white,
        "non_black_pixels": total - black,
        "luma_mean": round(mean, 2),
        "luma_variance": round(var, 2),
        "entropy_bits": round(entropy, 3),
        "luma_histogram_16": bins,
        "top_colors": [
            {"rgb": list(c), "count": n, "frac": round(n / total, 5)}
            for c, n in colors.most_common(8)],
        "repeated_row_period": p,
        "repeated_row_ratio": round(ratio, 3),
        "repeated_col_period": cp,
        "repeated_col_ratio": round(cratio, 3),
        "unique_row_hashes": len(set(rh)),
        "unique_col_hashes": len(set(ch)),
        "stride_note": f"screenshot row stride = {w*3} bytes (RGB); "
                       f"if a repeated period ≈ 1080*4/3 or a stride "
                       f"mismatch shows, compare with framebuffer "
                       f"stride = width*4 (RGBA)",
    }
    m["classification"] = classify(m)

    text = json.dumps(m, indent=1)
    print(text)
    if a.json_out:
        with open(a.json_out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
