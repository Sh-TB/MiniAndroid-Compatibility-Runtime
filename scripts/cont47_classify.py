#!/usr/bin/env python3
"""cont47_classify.py — classify every fanout train's face: non-white px,
non-white ratio, dominant color -> WHITE / RENDERED / DIALOG etc.
Produces run/cont47/faces.json (census rows only; ZERO-LOG law)."""
import json, os, glob
from PIL import Image
import numpy as np

OUT = "/home/z/my-project/run/cont47/fanout"
faces = {}
for d in sorted(glob.glob(os.path.join(OUT, "*"))):
    if not os.path.isdir(d):
        continue
    label = os.path.basename(d)
    shot = os.path.join(d, "screenshot.png")
    if not os.path.exists(shot):
        faces[label] = {"face": "NO-SHOT"}
        continue
    try:
        im = Image.open(shot).convert("RGB")
        a = np.asarray(im)
        h, w, _ = a.shape
        nonwhite = (a < 245).any(axis=2)
        nw = int(nonwhite.sum())
        ratio = round(nw / (h * w), 4)
        # dominant non-white color bucket
        px = a[nonwhite]
        if len(px):
            med = np.median(px, axis=0).astype(int).tolist()
        else:
            med = None
        uniq = len(np.unique(px // 32, axis=0)) if len(px) else 0
        if nw == 0:
            face = "WHITE"
        elif ratio < 0.01:
            face = "SPARSE"
        else:
            face = f"RENDERED"
        faces[label] = {
            "face": face, "nonwhite_px": nw, "ratio": ratio,
            "median_rgb": med, "color_buckets": int(uniq),
            "size": [w, h],
            "log_lines": sum(1 for _ in open(os.path.join(d, "run.log"), errors="ignore")),
        }
    except Exception as e:
        faces[label] = {"face": "ERR", "err": str(e)}

with open(os.path.join(OUT, "..", "faces.json"), "w") as f:
    json.dump(faces, f, indent=1)

# summary
import collections
cc = collections.Counter(v["face"] for v in faces.values())
print("FACE CENSUS:", dict(cc))
print()
for label, v in sorted(faces.items(), key=lambda kv: (kv[1].get("face",""), -kv[1].get("nonwhite_px",0))):
    if v.get("face") in ("RENDERED","SPARSE"):
        print(f"  {label:36s} {v['face']:9s} px={v['nonwhite_px']:7d} ratio={v['ratio']:.4f} rgb={v['median_rgb']} uniq32={v['color_buckets']}")
print()
for label, v in sorted(faces.items()):
    if v.get("face") in ("WHITE","NO-SHOT","ERR"):
        print(f"  {label:36s} {v['face']}")
