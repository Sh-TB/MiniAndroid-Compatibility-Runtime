#!/usr/bin/env python3
"""Light-corpus rendering evidence analyzer.

For each run directory, reads the runtime-produced screenshot PNG(s) and
computes the honest rendering evidence the owner asked for:

    App | PNG | Non-white pixels | distinct colors | color breakdown | verdict

This tool only READS runtime output. It never fabricates, retouches, or
re-renders anything. If the runtime produced a blank image, the table says
so — that is the point.

Usage:
    python3 scripts/analyze_light_corpus.py <run_dir> [<run_dir> ...] [--json OUT]
"""
import argparse
import colorsys
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image


def classify_color(r, g, b):
    """Rough human-meaningful color class for a pixel."""
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    if l >= 0.92 and s <= 0.10:
        return "white"
    if l <= 0.10:
        return "black"
    if s <= 0.12:
        return "gray"
    deg = h * 360.0
    for name, lo, hi in (
        ("red", 345, 360), ("red", 0, 15),
        ("orange", 15, 45), ("yellow", 45, 70),
        ("green", 70, 165), ("cyan", 165, 195),
        ("blue", 195, 255), ("purple", 255, 290),
        ("magenta", 290, 345),
    ):
        if lo <= deg < hi:
            return name
    return "other"


def analyze_png(path: Path) -> dict:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = list(img.getdata())
    total = w * h
    classes = Counter(classify_color(*p) for p in px)
    distinct = len(set(px))
    non_white = total - classes.get("white", 0)
    top = [(c, n, round(100.0 * n / total, 2)) for c, n in classes.most_common(8)]
    # "real graphics" heuristics: meaningful non-white share AND more than a
    # trivial number of distinct colors AND some non-grayscale pixels.
    colored = sum(n for c, n in classes.items() if c not in ("white", "gray", "black", "other"))
    return {
        "png": str(path),
        "width": w,
        "height": h,
        "total_pixels": total,
        "non_white_pixels": non_white,
        "non_white_pct": round(100.0 * non_white / total, 2),
        "distinct_colors": distinct,
        "colored_pixels": colored,
        "colored_pct": round(100.0 * colored / total, 2),
        "top_color_classes": top,
        "sha256_framebuffer_png": hashlib.sha256(path.read_bytes()).hexdigest(),
        "verdict": (
            "REAL_RENDER" if non_white_pct_ok(non_white, total) and colored > 0 and distinct > 16
            else "SUSPICIOUS_NEAR_BLANK" if non_white < 0.005 * total
            else "RENDER_WITHOUT_COLOR" if colored == 0
            else "WEAK_RENDER"
        ),
    }


def non_white_pct_ok(non_white, total):
    return non_white > 0.01 * total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--json", dest="json_out", default=None)
    args = ap.parse_args()

    rows = []
    for d in args.dirs:
        run = Path(d)
        pngs = sorted(run.rglob("*.png"))
        if not pngs:
            rows.append({"run": str(run), "error": "NO_PNG_FOUND"})
            continue
        entry = {"run": str(run), "frames": []}
        for p in pngs:
            try:
                entry["frames"].append(analyze_png(p))
            except Exception as e:  # noqa: BLE001
                entry["frames"].append({"png": str(p), "error": repr(e)})
        rows.append(entry)

    # Human table
    print(f"{'App/Run':28s} {'PNG':40s} {'Size':10s} {'NonWhite':>9s} {'%':>6s} {'Colors':>7s} {'Colored%':>9s} {'Verdict':22s}")
    print("-" * 140)
    for row in rows:
        name = row.get("run", "?")
        if "error" in row:
            print(f"{name:28s} {row['error']}")
            continue
        for fr in row["frames"]:
            if "error" in fr:
                print(f"{name:28s} {fr['png']:40s} ERROR {fr['error']}")
                continue
            label = Path(row["run"]).name + "/" + Path(fr["png"]).name
            size = f"{fr['width']}x{fr['height']}"
            print(f"{Path(row['run']).name:28s} {Path(fr['png']).name:40s} {size:10s} "
                  f"{fr['non_white_pixels']:9d} {fr['non_white_pct']:5.1f}% {fr['distinct_colors']:7d} "
                  f"{fr['colored_pct']:8.1f}% {fr['verdict']:22s}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, indent=2))
        print(f"\nJSON evidence: {args.json_out}")


if __name__ == "__main__":
    main()
