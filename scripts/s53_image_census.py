#!/usr/bin/env python3
"""S53 tracked-image census: blank-class + duplicate detection over git-tracked images."""
import hashlib
import subprocess
from collections import Counter
from PIL import Image

files = subprocess.check_output(
    ["git", "ls-files"], text=True).splitlines()
imgs = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]

blank, dup, ok = [], [], 0
hashes = {}
for f in imgs:
    try:
        data = open(f, "rb").read()
    except OSError:
        continue
    dg = hashlib.sha256(data).hexdigest()
    if dg in hashes:
        dup.append((f, hashes[dg], len(data)))
    else:
        hashes[dg] = f
    try:
        im = Image.open(f)
        g = im.convert("L")
        h = g.histogram()
        total = im.size[0] * im.size[1] or 1
        nw = sum(h[245:]) / total * 100
        nb = sum(h[:12]) / total * 100
        rgb = im.convert("RGB")
        c = rgb.getcolors(maxcolors=1 << 24)
        ncol = len(c) if c else -1
        if nw >= 97 or nb >= 97 or 0 < ncol <= 8:
            blank.append((f, round(nw, 1), round(nb, 1), ncol, len(data)))
        else:
            ok += 1
    except Exception as e:
        blank.append((f, "ERR", str(e)[:40], "", 0))

print(f"tracked images: {len(imgs)}  unique: {len(hashes)}  meaningful: {ok}")
print(f"\n== BLANK-CLASS ({len(blank)}) ==")
for f, nw, nb, nc, sz in sorted(blank, key=lambda x: -x[4]):
    print(f"  {sz:>9}B  w={nw}% b={nb}% colors={nc}  {f}")
print(f"\n== BYTE-IDENTICAL DUPLICATES ({len(dup)}) ==")
for f, orig, sz in sorted(dup, key=lambda x: -x[2]):
    print(f"  {sz:>9}B  {f}  == {orig}")
