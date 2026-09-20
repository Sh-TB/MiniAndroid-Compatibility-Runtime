#!/usr/bin/env python3
"""s72_w4_measure.py — per-app frame_008 nonwhite + SHA for W4 vs W3 corpus runs."""
import os, sys, glob, hashlib
from PIL import Image

ROOT = "/home/z/my-project"
APPS = [
    "app.varlorg.unote_30", "bouncy", "com.emmanuelmess.tictactoe_3",
    "com.github.muellerma.stopwatch_6", "de.duenndns.gmdice_8",
    "dooz_23_toplevel", "dubrowgn.microtimer_8", "fishrings_v1.23_vc6",
    "opmt_v0.1.2_vc1", "tripeaks_v1.2.1_vc4",
]

def last_frame(d):
    fr = os.path.join(d, "frames")
    if not os.path.isdir(fr):
        return None
    fs = [f for f in sorted(os.listdir(fr)) if f.endswith((".ppm", ".png"))]
    return os.path.join(fr, fs[-1]) if fs else None

def stats(d):
    f = last_frame(d)
    if not f:
        return None
    img = Image.open(f).convert("RGB")
    px = sum(1 for p in img.getdata() if p != (255, 255, 255))
    sha = hashlib.sha256(img.tobytes()).hexdigest()[:16]
    return px, sha

rows = []
for a in APPS:
    w4 = stats(os.path.join(ROOT, "run", "s72_w4_corpus", a))
    w3 = stats(os.path.join(ROOT, "run", "s72_w3_corpus", a))
    rel = "?"
    if w4 and w3:
        rel = "SAME" if w4[1] == w3[1] else ("UP" if w4[0] > w3[0] else "DOWN")
    rows.append((a, w3, w4, rel))

for a, w3, w4, rel in rows:
    print(f"{a:38s} W3={w3}  W4={w4}  {rel}")

# dooz determinism
shas = []
for i in (1, 2, 3):
    s = stats(os.path.join(ROOT, "run", "s72_w4_corpus", f"dooz_det{i}"))
    shas.append(s)
print("dooz_det:", shas, "UNIQUE:", len(set(x[1] for x in shas if x)))
