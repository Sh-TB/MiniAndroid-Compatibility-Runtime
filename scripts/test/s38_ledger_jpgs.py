#!/usr/bin/env python3
"""S38: convert wave-4 fixture evidence screenshots to JPG <=100KB into
the ledger folder, print SHA-256 + sizes for the ledger rows."""
import os, io, hashlib
from PIL import Image

JOBS = [
    ("hello_widgets.jpg", "/tmp/s38_runs/wave4/hw_fixed/screenshot.png"),
    ("hello_smoke.jpg",   "/tmp/s38_runs/wave4/hs_fixed/screenshot.png"),
    ("scroll_min.jpg",    "/tmp/s38_runs/wave4/sm_fixed/screenshot.png"),
]
OUT = "/home/z/my-project/miniandroid/docs/evidence/apps_ledger"
LIMIT = 100 * 1024

for name, src in JOBS:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    half = im.resize((w // 2, h // 2), Image.LANCZOS)  # 540x960 archive law
    q = 72
    while q >= 30:
        buf = io.BytesIO()
        half.save(buf, "JPEG", quality=q)
        if buf.tell() <= LIMIT:
            break
        q -= 6
    data = buf.getvalue()
    dst = os.path.join(OUT, name)
    with open(dst, "wb") as f:
        f.write(data)
    sha = hashlib.sha256(data).hexdigest()
    print(f"{name}: {len(data)}B q={q} sha256={sha}")
