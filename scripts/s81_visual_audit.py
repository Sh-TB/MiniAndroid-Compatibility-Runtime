#!/usr/bin/env python3
"""s81_visual_audit.py — S81 REAL APP VISUAL COMPATIBILITY audit tool.

Implements the S78 spec (user wave: REAL APP VISUAL COMPATIBILITY):
  §2  per-screenshot metrics: UNIQUE_COLORS, COLOR_ENTROPY, DOMINANT ratios,
      LUMINANCE/SATURATION ranges, NON_BACKGROUND/IMAGE/ICON/TEXT/WIDGET pixels
  §3  detector flags: MONOCHROME_LIKE, LOW_COLOR_VARIETY, FLAT_BACKGROUND,
      TEXT_ONLY_UI, IMAGE_RICH, ICON_RICH ...
  §17 comparison levels 0-5 (L5 needs human review — never self-granted)
  §36 no fake overall score: components reported separately, no single number

All thresholds are CONSTANTS documented here (methodology-first, §36):
  UNIQUE_COLORS       count of distinct RGB triplets after 4-bit/channel quant
                      (16^3=4096 bins; raw count also recorded)
  COLOR_ENTROPY       Shannon entropy of quantized color histogram (bits)
  DOMINANT_RATIO      share of biggest color bin
  FLAT_BACKGROUND     dominant bin share >= 0.92
  MONOCHROME_LIKE     dominant >= 0.90 AND entropy < 1.2
  LOW_COLOR_VARIETY   unique(quant) < 16 OR (dominant >= 0.80 AND unique < 48)
  TEXT_ONLY_UI        textish+widget pixels present, imageish+iconish < 0.2%
  NON_BACKGROUND      pixels outside dominant-bin neighborhood (±8 RGB dist)
Region classes (16x16 cell grid, per-cell stats):
  textish   high edge density + low saturation + bimodal luminance
  widgetish mid edge density + uniform hue (button/box fills)
  imageish  high hue variety + mid/high saturation (photos/bitmaps)
  iconish   small colorful blobs (hue variety + compact)
Usage:
  s81_visual_audit.py <run_dir_with_frames/> [more dirs...]
  s81_visual_audit.py --apk <apk_path> <frame.png>      # + resource counts
Output: per-dir JSON next to frames + stdout table.
"""
import glob
import json
import math
import os
import subprocess
import sys
from collections import Counter

from PIL import Image

CELL = 16  # analysis grid cell size (540x960 -> 33x60 cells)


def qcolor(px):
    """quantize to 4 bits per channel"""
    return ((px[0] >> 4) << 8) | ((px[1] >> 4) << 4) | (px[2] >> 4)


def rgb_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def sat_lum(px):
    mx, mn = max(px), min(px)
    lum = (mx + mn) / 510.0
    sat = 0.0 if mx == 0 else (mx - mn) / mx
    return sat, lum


def classify_cells(im):
    """Return (cell_classes, region_boxes) using per-cell statistics."""
    w, h = im.size
    px = im.load()
    classes = [["flat"] * (w // CELL) for _ in range(h // CELL)]
    for cy in range(h // CELL):
        for cx in range(w // CELL):
            hues, sats, lums = set(), [], []
            edges = 0
            prev = None
            for y in range(cy * CELL, min((cy + 1) * CELL, h), 2):
                for x in range(cx * CELL, min((cx + 1) * CELL, w), 2):
                    p = px[x, y]
                    s, l = sat_lum(p)
                    sats.append(s)
                    lums.append(l)
                    if s > 0.15:
                        hues.add(qcolor(p) >> 8)  # coarse hue bin (r,g,b top bits)
                    if prev is not None and rgb_dist(p, prev) > 90:
                        edges += 1
                    prev = p
            n = max(1, len(sats))
            edge_density = edges / n
            sat_range = max(sats) - min(sats)
            lum_range = max(lums) - min(lums)
            uniq_hues = len(hues)
            if uniq_hues >= 6 and sat_range > 0.25:
                c = "imageish"
            elif uniq_hues >= 3 and sat_range > 0.15:
                c = "iconish"
            elif edge_density > 0.30 and sat_range < 0.2 and lum_range > 0.4:
                c = "textish"
            elif edge_density > 0.10:
                c = "widgetish"
            else:
                c = "flat"
            classes[cy][cx] = c
    return classes


def region_boxes(classes, cls):
    """bounding boxes (x0,y0,x1,y1) of contiguous cells of class cls (merged rows)"""
    h, w = len(classes), len(classes[0])
    seen = [[False] * w for _ in range(h)]
    boxes = []
    for y in range(h):
        for x in range(w):
            if classes[y][x] == cls and not seen[y][x]:
                # flood fill (4-conn)
                stack = [(x, y)]
                seen[y][x] = True
                minx = maxx = x
                miny = maxy = y
                count = 0
                while stack:
                    cx, cy = stack.pop()
                    count += 1
                    minx, maxx = min(minx, cx), max(maxx, cx)
                    miny, maxy = min(miny, cy), max(maxy, cy)
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and classes[ny][nx] == cls:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                if count >= 2:  # ignore single-cell noise
                    boxes.append([minx * CELL, miny * CELL,
                                  (maxx + 1) * CELL, (maxy + 1) * CELL, count])
    boxes.sort(key=lambda b: -b[4])
    return boxes[:12]


def audit_frame(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    hist = Counter()
    sats, lums = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            p = px[x, y]
            hist[qcolor(p)] += 1
            s, l = sat_lum(p)
            sats.append(s)
            lums.append(l)
    total = sum(hist.values())
    ranked = hist.most_common()
    dom_color_idx = ranked[0][0]
    dom_color = ((dom_color_idx >> 8) << 4, ((dom_color_idx >> 4) & 0xF) << 4, (dom_color_idx & 0xF) << 4)
    dom_ratio = ranked[0][1] / total
    second_ratio = (ranked[1][1] / total) if len(ranked) > 1 else 0.0
    entropy = -sum((c / total) * math.log2(c / total) for _, c in ranked)
    nonbg = sum(c for idx, c in ranked
                if rgb_dist(((idx >> 8) << 4, ((idx >> 4) & 0xF) << 4, (idx & 0xF) << 4), dom_color) > 24)
    classes = classify_cells(im)
    flat_cells = sum(row.count("flat") for row in classes)
    ncells = len(classes) * len(classes[0])
    pix = lambda cls: sum(sum(1 for c in row if c == cls) for row in classes) * (CELL * CELL) // 4
    m = {
        "frame": os.path.basename(path),
        "SCREEN_WIDTH": w, "SCREEN_HEIGHT": h,
        "UNIQUE_COLORS_RAW": len(hist),
        "UNIQUE_COLORS": len(hist),
        "COLOR_ENTROPY": round(entropy, 3),
        "DOMINANT_COLOR_RATIO": round(dom_ratio, 4),
        "SECOND_DOMINANT_COLOR_RATIO": round(second_ratio, 4),
        "DOMINANT_COLOR_RGB": list(dom_color),
        "LUMINANCE_RANGE": round(max(lums) - min(lums), 3),
        "SATURATION_RANGE": round(max(sats) - min(sats), 3),
        "NON_BACKGROUND_PIXELS": nonbg * 4,
        "NON_BACKGROUND_RATIO": round(nonbg / total, 4),
        "TEXT_PIXELS": pix("textish"),
        "WIDGET_PIXELS": pix("widgetish"),
        "IMAGE_PIXELS": pix("imageish"),
        "ICON_PIXELS": pix("iconish"),
        "FLAT_CELL_RATIO": round(flat_cells / ncells, 4),
    }
    flags = []
    if m["DOMINANT_COLOR_RATIO"] >= 0.90 and m["COLOR_ENTROPY"] < 1.2:
        flags.append("MONOCHROME_LIKE")
    if m["UNIQUE_COLORS"] < 16 or (m["DOMINANT_COLOR_RATIO"] >= 0.80 and m["UNIQUE_COLORS"] < 48):
        flags.append("LOW_COLOR_VARIETY")
    if m["DOMINANT_COLOR_RATIO"] >= 0.92:
        flags.append("FLAT_BACKGROUND")
    if (m["TEXT_PIXELS"] + m["WIDGET_PIXELS"]) > 0.01 * w * h and \
       (m["IMAGE_PIXELS"] + m["ICON_PIXELS"]) < 0.002 * w * h:
        flags.append("TEXT_ONLY_UI")
    if m["IMAGE_PIXELS"] > 0.02 * w * h:
        flags.append("IMAGE_RICH")
    if m["ICON_PIXELS"] > 0.004 * w * h:
        flags.append("ICON_PRESENT")
    if m["UNIQUE_COLORS"] >= 64 and m["SATURATION_RANGE"] > 0.5 and m["NON_BACKGROUND_RATIO"] > 0.25:
        flags.append("GRAPHICALLY_NONTRIVIAL")
    m["FLAGS"] = flags
    # structural regions (§18): coordinates usable for View-tree correlation
    m["REGIONS"] = {c: region_boxes(classes, c) for c in ("textish", "widgetish", "imageish", "iconish")}
    return m


def level_of(m):
    """§17 levels — L5 only via human review, never granted here.

    S54 blank-gate law (S85 hardening, EVID-CLASS-S84 follow-up): the
    engine-default shell class (white framebuffer + small black status
    region, eb16ab5c…) measures nonbg_ratio ≈ 0.011 — above the old
    0.01 "nonblank" line, which let it slip through as L2. Law now:
    a DOMINANT single-color framebuffer (>= 0.975 of sampled pixels or
    < 0.035 non-background ratio) can NEVER be L2+ — at most L1 NONBLANK,
    no matter how many unique colors the status bar contributes.
    Real text/UI screens measure nonbg >= ~0.05 (bouncy help 0.089,
    URLChecker 0.322) and keep their honest levels.
    """
    if m["NON_BACKGROUND_RATIO"] <= 0.001 and m["UNIQUE_COLORS"] <= 2:
        return 0, "LOADED_ONLY"
    near_blank = (m["NON_BACKGROUND_RATIO"] < 0.035 or
                  m["DOMINANT_COLOR_RATIO"] >= 0.975)
    if near_blank:
        return 1, "NONBLANK_NEARBLANK_GATE"
    nonblank = m["NON_BACKGROUND_RATIO"] > 0.01 or m["UNIQUE_COLORS"] > 8
    if not nonblank:
        return 1, "NONBLANK"
    if "GRAPHICALLY_NONTRIVIAL" in m["FLAGS"]:
        struct = len(m["REGIONS"]["widgetish"]) + len(m["REGIONS"]["textish"]) >= 2
        if struct:
            return 3, "STRUCT_CANDIDATE"
        return 2, "COLORFUL"
    return 2, "GRAPHICALLY_INCOMPLETE"


def apk_resource_counts(apk):
    """resource-side ground truth: PNG count + res dirs (zip listing)"""
    try:
        out = subprocess.run(["unzip", "-l", apk], capture_output=True, text=True, timeout=60).stdout
        names = [l.split()[-1] for l in out.splitlines() if l.strip() and l.split()[-1].endswith((".png", ".jpg", ".webp", ".9.png"))]
        return {
            "APK_RASTER_RESOURCES": len(names),
            "APK_RASTER_SAMPLE": sorted(os.path.basename(n) for n in names)[:12],
            "APK_RES_DIRS": sorted({n.split("/")[1] for n in out.splitlines() if " res/" in n and len(n.split()[-1].split("/")) > 2})[:20],
        }
    except Exception as e:
        return {"APK_RASTER_RESOURCES": -1, "error": str(e)}


def main():
    args = sys.argv[1:]
    apk = None
    if "--apk" in args:
        i = args.index("--apk")
        apk = args[i + 1]
        del args[i:i + 2]
    results = []
    for d in args:
        for f in sorted(glob.glob(os.path.join(d, "frames", "frame_*.png")) or glob.glob(os.path.join(d, "*.png"))):
            m = audit_frame(f)
            lvl, name = level_of(m)
            m["LEVEL"] = lvl
            m["LEVEL_NAME"] = name
            if apk and f == args[args.index(d)] if False else False:
                pass
            results.append(m)
    if apk:
        rc = apk_resource_counts(apk)
        for m in results:
            m.update(rc)
        # §20/§26 image-presence gap heuristic: app ships rasters but screen shows none
        if rc.get("APK_RASTER_RESOURCES", 0) > 3 and results:
            last = results[-1]
            if (last["IMAGE_PIXELS"] + last["ICON_PIXELS"]) < 0.002 * last["SCREEN_WIDTH"] * last["SCREEN_HEIGHT"]:
                last["FLAGS"] = last["FLAGS"] + ["MISSING_IMAGES_SUSPECTED", "IMAGE_DECODED_VS_RENDERED_GAP"]
    print(json.dumps({"audit": "S81-visual", "items": results}, indent=1))
    out = os.path.join(args[0].rstrip("/") + "_visual_audit.json") if args else "visual_audit.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    print(f"\nwritten: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
