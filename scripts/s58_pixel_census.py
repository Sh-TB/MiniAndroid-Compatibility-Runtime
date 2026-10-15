#!/usr/bin/env python3
"""s58_pixel_census.py — 24-bucket color quantization census + button/region scan.
Usage: s58_pixel_census.py <png> [<png> ...]
Prints: size, bg color, non-bg share, distinct bucketed colors, dark-glyph share,
button-like regions (BFS, 50..420 x 50..300, fill>0.55, size>=180).
"""
import sys, json
from collections import Counter, deque
from PIL import Image

def bucket(c):
    return (c[0] // 32, c[1] // 32, c[2] // 32)

def analyze(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    # background = border-mode color (sample 4 corners + edges)
    edge = [px[0, 0], px[w-1, 0], px[0, h-1], px[w-1, h-1],
            px[w//2, 0], px[w//2, h-1], px[0, h//2], px[w-1, h//2]]
    bg = Counter(edge).most_common(1)[0][0]
    buckets = Counter()
    nonbg = 0
    dark = 0
    grid = [[False]*w for _ in range(0)]  # not building full grid; sample-based
    step = 2  # sample every 2nd pixel for census speed, BFS uses separate scan
    total = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            c = px[x, y]
            total += 1
            b = bucket(c)
            buckets[b] += 1
            if b != bucket(bg):
                nonbg += 1
            if c[0]+c[1]+c[2] < 240:
                dark += 1
    # button-like region scan on full grid (downscaled to 1/2)
    sw, sh = w//2, h//2
    sim = im.resize((sw, sh))
    sp = sim.load()
    sbg = bucket(bg)
    isfg = [[bucket(sp[x, y]) != sbg for x in range(sw)] for y in range(sh)]
    seen = [[False]*sw for _ in range(sh)]
    regions = []
    for y0 in range(sh):
        for x0 in range(sw):
            if isfg[y0][x0] and not seen[y0][x0]:
                q = deque([(x0, y0)]); seen[y0][x0] = True
                minx=maxx=x0; miny=maxy=y0; cnt=0
                while q:
                    x, y = q.popleft(); cnt += 1
                    if x<minx: minx=x
                    if x>maxx: maxx=x
                    if y<miny: miny=y
                    if y>maxy: maxy=y
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0<=nx<sw and 0<=ny<sh and isfg[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx]=True; q.append((nx,ny))
                bw, bh = (maxx-minx+1)*2, (maxy-miny+1)*2
                if 50 <= bw <= 420 and 50 <= bh <= 300 and cnt >= 180:
                    fill = cnt / max(1, ((bw//2)*(bh//2)))
                    if fill > 0.55:
                        regions.append({"x": minx*2, "y": miny*2, "w": bw, "h": bh,
                                        "fill": round(fill, 2)})
    out = {
        "png": path.split("/")[-1], "size": f"{w}x{h}",
        "bg_rgb": list(bg),
        "nonbg_share": round(nonbg/total, 4),
        "dark_glyph_share": round(dark/total, 4),
        "distinct_buckets": len(buckets),
        "top_buckets": [[list(k), v] for k, v in buckets.most_common(6)],
        "button_like_regions": regions[:24],
        "n_button_like": len(regions),
    }
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(analyze(p)))
