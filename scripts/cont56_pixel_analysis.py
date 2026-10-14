#!/usr/bin/env python3
"""cont56_pixel_analysis.py — quantify WHAT IS VISIBLE in an app face.

Answers the standing user question with measurements, not claims:
  * how many non-background pixels (real content vs white page)
  * distinct color count (button fills / theme colors)
  * button-like region census (connected regions of a fill color, sized
    like a button, i.e. 60..400 px wide/tall at 1080x1920)
  * text-glyph estimate (dark pixel clusters in rows)
Usage: cont56_pixel_analysis.py <screenshot.png> [more.png ...]
"""
import sys, json
from PIL import Image

def analyze(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    # --- color census (coarse buckets to absorb anti-aliasing) ---
    from collections import Counter
    cnt = Counter()
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            r, g, b = px[x, y]
            cnt[(r // 24 * 24, g // 24 * 24, b // 24 * 24)] += 1
    sampled = sum(cnt.values())
    top = cnt.most_common(6)
    bg = top[0][0] if top else (0, 0, 0)
    bg_share = top[0][1] / sampled if sampled else 1.0
    nonbg = 1.0 - bg_share

    # --- button-like region census: flood-fill non-background rows on a
    # downscaled grid, count regions 60-400px wide/tall with a coherent fill ---
    small = im.resize((w // 4, h // 4))
    sw, sh = small.size
    sp = small.load()
    def isbg(c):
        return abs(c[0] - bg[0]) < 30 and abs(c[1] - bg[1]) < 30 and abs(c[2] - bg[2]) < 30
    seen = [[False] * sw for _ in range(sh)]
    regions = []
    for y in range(sh):
        for x in range(sw):
            if seen[y][x] or isbg(sp[x, y]):
                continue
            # BFS
            stack = [(x, y)]
            seen[y][x] = True
            minx = maxx = x; miny = maxy = y; size = 0
            while stack:
                cx, cy = stack.pop()
                size += 1
                minx = min(minx, cx); maxx = max(maxx, cx)
                miny = min(miny, cy); maxy = max(maxy, cy)
                for nx, ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                    if 0 <= nx < sw and 0 <= ny < sh and not seen[ny][nx] and not isbg(sp[nx, ny]):
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            bw = (maxx - minx + 1) * 4
            bh = (maxy - miny + 1) * 4
            fill = size / max(1, (maxx - minx + 1) * (maxy - miny + 1))
            if 50 <= bw <= 420 and 50 <= bh <= 300 and fill > 0.55 and size >= 180:
                regions.append({"x": minx*4, "y": miny*4, "w": bw, "h": bh,
                                "rgb": sp[(minx+maxx)//2, (miny+maxy)//2]})
    # --- dark glyph census (text presence) ---
    dark = sum(1 for y in range(0, h, 2) for x in range(0, w, 2)
               if sum(px[x, y]) < 240)
    return {"png": path.split("/")[-1], "size": f"{w}x{h}",
            "background_rgb": list(bg), "nonbg_share": round(nonbg, 4),
            "distinct_colors_bucketed": len(cnt),
            "dark_glyph_samples": dark,
            "button_like_regions": regions[:60],
            "button_like_count": len(regions)}

if __name__ == "__main__":
    out = [analyze(p) for p in sys.argv[1:]]
    print(json.dumps(out, indent=1))
