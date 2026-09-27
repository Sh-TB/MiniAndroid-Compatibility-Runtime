#!/usr/bin/env python3
"""S113 pixel-metrics audit — full-GUI render law (no blank/jumbled passes)."""
import json, sys, hashlib
from PIL import Image

def metrics(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    colors = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c = px[x, y]
            colors[c] = colors.get(c, 0) + 1
    total = sum(colors.values())
    sorted_c = sorted(colors.items(), key=lambda kv: -kv[1])
    bg = sorted_c[0][0]
    bg_ratio = sorted_c[0][1] / total
    # non-background ratio (channel distance > 8)
    nonbg = sum(v for c, v in colors.items()
                if abs(c[0]-bg[0])+abs(c[1]-bg[1])+abs(c[2]-bg[2]) > 24)
    # pink-button band detection (rows with many non-bg pinkish pixels)
    import math
    entropy = -sum((v/total) * math.log2(v/total) for v in colors.values())
    return {
        "resolution": [w, h],
        "unique_colors": len(colors),
        "entropy_bits": round(entropy, 3),
        "dominant_color": "#%02x%02x%02x" % bg,
        "bg_ratio": round(bg_ratio, 4),
        "nonbg_ratio": round(nonbg / total, 4),
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16],
    }

if __name__ == "__main__":
    out = {}
    for p in sys.argv[1:]:
        out[p] = metrics(p)
    print(json.dumps(out, indent=1))
