#!/usr/bin/env python3
"""S38-A: convert all ledger evidence PNGs to JPG (quality tuned, <=100KB), report
compression, update ledger references. Re-created after container reset."""
import os, hashlib
from PIL import Image

LEDGER_DIR = "/home/z/my-project/miniandroid/docs/evidence/apps_ledger"
MAX_BYTES = 100 * 1024

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

results = []
for name in sorted(os.listdir(LEDGER_DIR)):
    if not name.endswith(".png"):
        continue
    png_path = os.path.join(LEDGER_DIR, name)
    jpg_name = name[:-4] + ".jpg"
    jpg_path = os.path.join(LEDGER_DIR, jpg_name)
    img = Image.open(png_path)
    orig_bytes = os.path.getsize(png_path)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    q = 72
    while True:
        img.save(jpg_path, "JPEG", quality=q, optimize=True)
        if os.path.getsize(jpg_path) <= MAX_BYTES or q <= 40:
            break
        q -= 8
    results.append((name, jpg_name, orig_bytes, os.path.getsize(jpg_path), q, sha256(jpg_path)))
    os.remove(png_path)

tot_old = tot_new = 0
print(f"{'old':38s} {'new':38s} {'old':>7s} {'new':>7s} {'Q':>3s}")
for name, jpg_name, ob, jb, q, h in results:
    tot_old += ob; tot_new += jb
    print(f"{name:38s} {jpg_name:38s} {ob:7d} {jb:7d} {q:3d}  sha={h[:12]}")
print(f"\nTOTAL: {tot_old} -> {tot_new} ({100.0*(tot_old-tot_new)/max(tot_old,1):.1f}%), {len(results)} imgs")
