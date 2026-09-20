#!/usr/bin/env python3
"""S72-W3 corpus pixel measurement — frame_008 nonwhite count + screenshot sha
per APK, compared against the S72-W2 baseline (S72_WAVE2.md §5)."""
import hashlib
import os
import sys
from PIL import Image

OUT = "/home/z/my-project/run/s72_w3_corpus"
W2 = {
    "app.varlorg.unote_30": 236520,
    "bouncy": 2073600,
    "com.emmanuelmess.tictactoe_3": 0,
    "com.github.muellerma.stopwatch_6": 23472,
    "de.duenndns.gmdice_8": 182095,
    "dooz_23_toplevel": 197,
    "dubrowgn.microtimer_8": 1041073,
    "fishrings_v1.23_vc6": 2072819,
    "opmt_v0.1.2_vc1": 213286,
    "tripeaks_v1.2.1_vc4": 205273,
}
WHITE = (255, 255, 255)

def nonwhite(img):
    g = img.convert("RGB")
    return sum(1 for p in g.getdata() if p != WHITE)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

rows = []
for name in sorted(W2):
    d = os.path.join(OUT, name)
    frames = sorted(fn for fn in (os.listdir(os.path.join(d, "frames")) if os.path.isdir(os.path.join(d, "frames")) else []) if fn.endswith((".ppm", ".png")))
    f8 = os.path.join(d, "frames", frames[-1]) if frames else None
    nw = nonwhite(Image.open(f8)) if f8 else -1
    ss = os.path.join(d, "screenshot.png")
    sh = sha256(ss) if os.path.exists(ss) else "-"
    base = W2[name]
    delta = "SAME" if nw == base else ("UP" if nw > base else "DOWN")
    rows.append((name, base, nw, delta, sh[:12]))

print(f"{'app':34s} {'W2 px':>9s} {'W3 px':>9s} {'delta':5s} screenshot_sha")
for (n, b, w, dl, sh) in rows:
    print(f"{n:34s} {b:9d} {w:9d} {dl:5s} {sh}")

# dooz determinism x3
print("\ndooz determinism x3 (screenshot sha):")
shs = []
for i in (1, 2, 3):
    ss = os.path.join(OUT, f"dooz_det{i}", "screenshot.png")
    s = sha256(ss) if os.path.exists(ss) else "MISSING"
    shs.append(s)
    print(f"  run{i}: {s}")
print("  BYTE-IDENTICAL" if len(set(shs)) == 1 and shs[0] != "MISSING" else "  NOT-IDENTICAL")
