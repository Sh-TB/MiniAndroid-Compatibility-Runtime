#!/usr/bin/env python3
"""s68_gen_fixture_images.py — generate the f48/f50 fixture drawable corpus.
Every image is built from KNOWN solid pixels so the verifier can assert
exact decoded colors through the full pipeline:
  source pixels → decode → Bitmap/ImageView → framebuffer → PNG → PIL check.
Formats: RGBA PNG, palette PNG (indexed), grayscale PNG, 1x1 PNG, odd-dims
PNG, JPEG, WebP, GIF (explicit-unsupported probe).
"""
from PIL import Image
import os

BASE = "/home/z/my-project/miniandroid/tests/fixtures_foundation"

def solid(w, h, rgb):
    im = Image.new("RGB", (w, h), rgb)
    return im.convert("RGBA")

def put(path, img, fmt=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, fmt) if fmt else img.save(path)
    print("wrote", path)

# ── f48: single red 60x40 PNG for BitmapFactory.decodeResource ──────────
d48 = f"{BASE}/f48_bitmap/res/drawable"
put(f"{d48}/ic_red.png", solid(60, 40, (255, 0, 0)))

# ── f50: format corpus (all 100x60 solids unless noted) ─────────────────
d50 = f"{BASE}/f50_imagefmt/res/drawable"
put(f"{d50}/img_jpg.jpg",   solid(100, 60, (255, 0, 255)).convert("RGB"), "JPEG")
put(f"{d50}/img_webp.webp", solid(100, 60, (0, 255, 255)), "WEBP")
put(f"{d50}/img_gray.png",  solid(100, 60, (128, 128, 128)).convert("L").convert("RGBA"))
pal = solid(100, 60, (255, 128, 0)).convert("P")   # palette/indexed
put(f"{d50}/img_palette.png", pal)
put(f"{d50}/img_odd.png",   solid(37, 23, (0, 0, 255)))   # odd dimensions
put(f"{d50}/one.png",       solid(1, 1, (255, 0, 0)))     # 1x1
put(f"{d50}/gif_test.gif",  solid(100, 60, (0, 180, 0)), "GIF")  # EXPLICIT-UNSUPPORTED probe
print("fixture image corpus complete")
