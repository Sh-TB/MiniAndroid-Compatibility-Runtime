#!/usr/bin/env python3
"""s73_screenshot_gate.py — S73 B3 screenshot quality gate for the
autonomous-snake evidence package (full metric set on key frames:
resolution, non-background px, entropy, luminance, dominant colors,
content bounds, SHA256). Metrics are DIAGNOSTIC, not success by
themselves (brief §23/§24) — success here = the full chain evidence."""
import json
import glob
import hashlib
import math
from collections import Counter
from PIL import Image

OUT = "/home/z/my-project/docs/evidence/s73_snake_autoplay"
KEY = {
    "frame_000.png": "LAUNCH (UI + panel, pre-START)",
    "frame_001.png": "START pressed state",
    "frame_034.png": "FOOD CAPTURED (growth 3->4, food (0,0)->(9,0))",
    "frame_089.png": "FINAL (autonomous session end, len 4)",
}


def metrics(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = list(img.getdata())
    nonbg = [p for p in px if p != (255, 255, 255)]
    gray = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in px]
    lum = sum(gray) / len(gray)
    hist = Counter(int(g) for g in gray)
    total = len(gray)
    ent = -sum((c / total) * math.log2(c / total) for c in hist.values() if c)
    dom = Counter(px).most_common(5)
    img_l = img.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            if img_l[x, y] != (255, 255, 255):
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
    return {
        "frame": path.split("/")[-1],
        "meaning": KEY[path.split("/")[-1]],
        "resolution": f"{w}x{h}",
        "non_background_px": len(nonbg),
        "entropy_bits": round(ent, 4),
        "luminance": round(lum, 2),
        "dominant_colors": [(f"#{r:02x}{g:02x}{b:02x}", c)
                            for (r, g, b), c in dom],
        "content_bounds": [minx, miny, maxx, maxy],
        "png_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "pixel_sha256": hashlib.sha256(img.tobytes()).hexdigest()[:16],
    }


def main():
    res = {}
    for name in KEY:
        p = f"{OUT}/run_01/frames/{name}"
        m = metrics(p)
        res[name] = m
        print(json.dumps(m)[:300])
    # GIF hash for provenance
    gif = f"{OUT}/snake_autoplay.gif"
    res["snake_autoplay.gif"] = {
        "png_sha256": hashlib.sha256(open(gif, "rb").read()).hexdigest(),
        "bytes": __import__("os").path.getsize(gif),
        "provenance": "GIF composed ONLY from real run_01 output frames "
                      "(50% NEAREST scale, 64-color quantize, 250ms/frame)",
    }
    with open(f"{OUT}/screenshot_metrics.json", "w") as f:
        json.dump(res, f, indent=1)
    print("saved screenshot_metrics.json")


if __name__ == "__main__":
    main()
