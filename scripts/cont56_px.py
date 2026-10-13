#!/usr/bin/env python3
# cont56_px.py — pixel-truth scoreboard for fresh runs (background, non-bg share,
# distinct colors in 24-bucket quantization, dark-glyph census, button-like regions).
import sys, glob, json
from PIL import Image
from collections import Counter

def bucket(c):
    return (c[0]//32, c[1]//32, c[2]//32)

def analyze(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()
    # sample grid for census (stride 4 both axes for speed)
    counts = Counter()
    dark_glyph = 0
    sampled = 0
    bg = Counter()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            c = px[x, y]
            sampled += 1
            counts[bucket(c)] += 1
            if c[0]+c[1]+c[2] < 240:
                dark_glyph += 1
            bg[bucket(c)] += 1
    bg_bucket = bg.most_common(1)[0][0]
    nonbg = sampled - bg[bg_bucket]
    # button-like BFS on a downscaled mask of non-bg pixels
    step = 4
    W2, H2 = w//step, h//step
    mask = [[False]*W2 for _ in range(H2)]
    for y in range(H2):
        for x in range(W2):
            c = px[x*step, y*step]
            if bucket(c) != bg_bucket:
                mask[y][x] = True
    seen = [[False]*W2 for _ in range(H2)]
    regions = []
    for y0 in range(H2):
        for x0 in range(W2):
            if mask[y0][x0] and not seen[y0][x0]:
                stack = [(x0, y0)]
                seen[y0][x0] = True
                pts = []
                while stack:
                    x, y = stack.pop()
                    pts.append((x, y))
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < W2 and 0 <= ny < H2 and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                bw = (max(xs)-min(xs)+1); bh = (max(ys)-min(ys)+1)
                fill = len(pts)/(bw*bh) if bw*bh else 0
                if 12 <= bw <= 105 and 12 <= bh <= 75 and len(pts) >= 45 and fill > 0.55:
                    regions.append(dict(w=bw*step, h=bh*step, fill=round(fill,2)))
    return dict(size=[w, h],
                bg_rgb=[bg_bucket[0]*32+16, bg_bucket[1]*32+16, bg_bucket[2]*32+16],
                nonbg_pct=round(100.0*nonbg/sampled, 1),
                distinct_buckets=len(counts),
                dark_glyph_pct=round(100.0*dark_glyph/sampled, 2),
                button_like=len(regions))

for pat in sys.argv[1:]:
    for p in sorted(glob.glob(pat)):
        print(p.split('run/cont56b/')[1] if 'run/cont56b/' in p else p, json.dumps(analyze(p)))
