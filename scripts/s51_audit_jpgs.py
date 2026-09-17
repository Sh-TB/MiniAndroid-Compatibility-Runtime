#!/usr/bin/env python3
# s51_audit_jpgs.py — S51 all-front status audit: curated JPG evidence set.
# Policy: JPG <=100KB, 540x960, q72 (S38 deterministic recipe).
# Source runs: /tmp/s51_audit/<app>/screenshot.png (fresh at HEAD 1b37afd1, 2026-09-17).
import os, hashlib, json
from PIL import Image

SRC = "/tmp/s51_audit"
DST = "/home/z/my-project/docs/evidence/s51_audit"
os.makedirs(DST, exist_ok=True)

APPS = [
    "dooz18", "dooz23", "chessclock", "unote", "tictactoe_corpus", "bouncy",
    "headingcalculator", "notesbillthefarmer", "stopwatchmuellerma", "bgclock",
    "microtimer", "simplekeyboard", "rttt", "itsfrz", "secuso_dicer",
    "openlauncher", "flashlight",
]

rows = []
for app in APPS:
    src = os.path.join(SRC, app, "screenshot.png")
    if not os.path.exists(src):
        print(f"SKIP {app}: no screenshot")
        continue
    dst = os.path.join(DST, f"{app}.jpg")
    im = Image.open(src).convert("RGB")
    im = im.resize((540, 960), Image.LANCZOS)
    im.save(dst, "JPEG", quality=72, optimize=True)
    size = os.path.getsize(dst)
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
    rows.append((app, size, sha))
    print(f"{app}.jpg  {size}B  sha16={sha}")

# Deterministic checksums file (full sha256)
with open(os.path.join(DST, "SHA256SUMS"), "w") as f:
    for app in APPS:
        p = os.path.join(DST, f"{app}.jpg")
        if os.path.exists(p):
            f.write(hashlib.sha256(open(p, "rb").read()).hexdigest() + f"  {app}.jpg\n")

print(json.dumps([(a, s) for a, _, s in rows]))
