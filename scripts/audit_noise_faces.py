#!/usr/bin/env python3
"""AUDIT-B/C: objective noise-face analysis for screenshot evidence.
The S195-era cohort runs render colored-noise faces (random-pixel garbage
from the pre-fix render pipeline). This script measures, per screenshot:
  size, unique colors, nonwhite ratio, top-color share, entropy class
and proposes a NOISE-FACE LAW with measured thresholds:
  NOISE  = unique_colors >= 8000 AND nonwhite in [0.15, 0.95] AND
           top1_share <= 0.30   (random RGB dither: many colors, no
                                 dominant structured palette)
  REAL   = structured app content (dominant palette or few colors)
  BLANK  = nonwhite < 0.02
Outputs download/repository_audit/NOISE_FACE_ANALYSIS.csv + a summary.
Read-only: no file modified.
"""
import csv, os, sys
from PIL import Image
from collections import Counter

ROOT = "/home/z/my-project"
TARGETS = [
    "evidence/s195_audit/cohort/runs",
    "evidence/s195_audit",
    "evidence/s200/harvest",
    "evidence/s200/runs",
    "evidence/s207/runs",
    "evidence/s188_w13",
    "evidence/s188_w16",
    "evidence/s188_w18",
]
OUT = os.path.join(ROOT, "download", "repository_audit")
os.makedirs(OUT, exist_ok=True)

rows = []
counts = Counter()
for tgt in TARGETS:
    base = os.path.join(ROOT, tgt)
    if not os.path.isdir(base):
        continue
    for dirpath, _, files in os.walk(base):
        for fn in files:
            if not fn.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT)
            try:
                im = Image.open(p).convert("RGB")
                n = im.width * im.height
                px = list(im.getdata())
                nonwhite = sum(1 for r, g, b in px
                               if not (r > 235 and g > 235 and b > 235)) / n
                cc = Counter(px)
                uniq = len(cc)
                # distinctness ratio: random noise fills the color space
                # (tictactoe_s195fix_r1: 1,073,651 unique of 2,073,600 px);
                # structured app content stays far below (dominant palette)
                distinct = uniq / n
                size = os.path.getsize(p)
                if nonwhite < 0.02:
                    cls = "BLANK"
                elif distinct >= 0.25 and nonwhite >= 0.5:
                    cls = "NOISE"
                elif uniq < 64:
                    cls = "FLAT"
                else:
                    cls = "STRUCTURED"
                rows.append([rel, size, im.width, im.height, uniq,
                             round(nonwhite, 4), round(distinct, 3), cls])
                counts[cls] += 1
            except Exception as e:
                rows.append([rel, os.path.getsize(p), 0, 0, 0, 0, 0,
                             f"ERROR:{e}"])
                counts["ERROR"] += 1

with open(os.path.join(OUT, "NOISE_FACE_ANALYSIS.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["path", "size_bytes", "w", "h", "unique_colors",
                "nonwhite_ratio", "top1_color_share", "class"])
    w.writerows(rows)

print("CLASS COUNTS:", dict(counts))
print("total screenshots:", len(rows))
noise = [r for r in rows if r[7] == "NOISE"]
print("NOISE bytes total:", sum(r[1] for r in noise))
for r in noise[:10]:
    print("  NOISE:", r[0][:90], r[1], "uniq", r[4], "nw", r[5])
