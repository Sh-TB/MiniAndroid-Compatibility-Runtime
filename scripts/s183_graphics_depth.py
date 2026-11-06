#!/usr/bin/env python3
"""S183 — honest graphics-depth census over every face we have called REAL_APP_CONTENT.

The user's charge: "you call a flat colored page + one font 'full load'". This
script computes HONEST graphics-depth tiers for every title measured on the
current binary (S180 battery, S181 minimal, S182 minimal2 + S180 reshoot):

  TIER-A RICH      : >= 1% non-background pixels AND >= 400 unique colors AND
                     visible smooth-gradient (image-like) content
  TIER-B STRUCTURED: >= 1% non-background pixels AND >= 60 unique colors
                     (multi-color UI: boards, tiles, buttons, cards)
  TIER-C TEXT_ON_FLAT: everything else (single bg color + glyph text) — the
                     "دو رنگ + یک فونت" class the user called out

Metrics per face:
  unique_colors, bg_share (dominant color share of whole frame),
  nonbg_share (1 - bg_share), ink_share (pixels far from dominant color),
  edge_density (neighbor-diff rate over luminance), grad_share (smooth
  mid-gradient pixel share = image/asset-likeness)
"""
import json, os, sys
from PIL import Image

BASE = "/home/z/my-project"
SETS = [
    ("s180", f"{BASE}/evidence/s180_battery/S180_BATTERY.json", f"{BASE}/run_s180_battery"),
    ("s181", f"{BASE}/evidence/s181_minimal/S181_MINIMAL.json", f"{BASE}/run_s181_minimal"),
    ("s182", f"{BASE}/evidence/s182_minimal2/S182_BATTERY.json", f"{BASE}/run_s182_minimal2"),
]
PNG_OVERRIDE = {
    "dooz": f"{BASE}/run_s166_trains/s182_dz/screenshot.png",
    "tg":   f"{BASE}/run_s166_trains/s182_tg/screenshot.png",
}

def load_rows(path):
    d = json.load(open(path))
    if isinstance(d, list):
        return d
    # dict keyed by tag
    out = []
    for k, v in d.items():
        if isinstance(v, dict) and "verdict" in v:
            v = dict(v); v.setdefault("tag", k); out.append(v)
    return out

def metrics(png):
    im = Image.open(png).convert("RGB")
    im = im.resize((im.width // 4, im.height // 4))  # 270x480 — plenty for census
    w, h = im.size
    px = list(im.getdata())
    total = w * h
    from collections import Counter
    c = Counter(px)
    top_col, top_n = c.most_common(1)[0]
    bg_share = top_n / total
    unique = len(c)
    # ink = pixels whose channel distance from bg > 60
    ink = 0
    grad = 0
    for p, n in c.items():
        d = max(abs(p[0]-top_col[0]), abs(p[1]-top_col[1]), abs(p[2]-top_col[2]))
        if d > 60:
            ink += n
        elif 15 < d <= 60:
            grad += n  # smooth mid-gradient = images/anti-aliased assets
    ink_share = ink / total
    grad_share = grad / total
    # edge density on luminance grid
    gray = [0.299*r+0.587*g+0.114*b for r, g, b in px]
    edges = 0
    for y in range(h):
        row = y * w
        for x in range(1, w):
            if abs(gray[row+x] - gray[row+x-1]) > 25:
                edges += 1
        if y:
            for x in range(w):
                if abs(gray[row+x] - gray[row+x-w]) > 25:
                    edges += 1
    edge_density = edges / (2 * w * h)
    return dict(unique_colors=unique, bg_share=round(bg_share, 4),
                nonbg_share=round(1-bg_share, 4), ink_share=round(ink_share, 4),
                grad_share=round(grad_share, 4), edge_density=round(edge_density, 5))

def tier(m):
    if m["nonbg_share"] >= 0.01 and m["unique_colors"] >= 400 and m["grad_share"] >= 0.02:
        return "A_RICH"
    if m["nonbg_share"] >= 0.01 and m["unique_colors"] >= 60:
        return "B_STRUCTURED"
    return "C_TEXT_ON_FLAT"

rows_out = []
seen = {}
for sname, jpath, rdir in SETS:
    if not os.path.exists(jpath):
        print(f"!! missing {jpath}", file=sys.stderr); continue
    for r in load_rows(jpath):
        tag = r.get("tag") or r.get("title")
        verd = r.get("verdict") or r.get("class")
        if isinstance(verd, list):
            verd = verd[0] if verd else None
        png = PNG_OVERRIDE.get(tag) or os.path.join(rdir, tag, "screenshot.png")
        if tag in seen:
            continue  # first set wins (s180 is the canonical battery)
        if verd != "REAL_APP_CONTENT":
            seen[tag] = verd
            continue
        seen[tag] = verd
        if not os.path.exists(png):
            rows_out.append(dict(tag=tag, set=sname, verdict=verd, error="no screenshot"))
            continue
        m = metrics(png)
        t = tier(m)
        rows_out.append(dict(tag=tag, set=sname, verdict=verd, tier=t, **m))

rows_out.sort(key=lambda r: (r.get("tier", "Z"), -(r.get("nonbg_share") or 0)))
print(f"{'tag':24s} {'tier':14s} {'uniq':>5s} {'nonbg%':>7s} {'ink%':>6s} {'grad%':>6s} {'edges':>7s}")
for r in rows_out:
    if "error" in r:
        print(f"{r['tag']:24s} MISSING {r['error']}"); continue
    print(f"{r['tag']:24s} {r['tier']:14s} {r['unique_colors']:5d} {100*r['nonbg_share']:7.2f} {100*r['ink_share']:6.2f} {100*r['grad_share']:6.2f} {r['edge_density']:7.3f}")

tally = {}
for r in rows_out:
    t = r.get("tier", "MISSING")
    tally[t] = tally.get(t, 0) + 1
print("\nTALLY:", json.dumps(tally, indent=1))
json.dump(dict(schema="s183_graphics_depth/v1", rows=rows_out, tally=tally),
          open(f"{BASE}/evidence/s183_audit1112/S183_GRAPHICS_DEPTH.json", "w"), indent=1)
print("saved evidence/s183_audit1112/S183_GRAPHICS_DEPTH.json")
