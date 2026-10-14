#!/usr/bin/env python3
"""cont65_gen_assets.py — CAPAUDIT probe assets (CONT-65 capability audit).
Generates deterministic test images in fixtures/capaudit_probe/assets/:
  png_rgba.png   64x64 RGBA gradient disc with alpha (curved shape + transparency)
  png_palette.png 64x64 palette-mode 4 exact quadrants
  img.jpg        64x64 JPEG horizontal gradient
  img.webp       64x64 WebP magenta disc on cyan
  anim.gif       48x48 3-frame GIF (red/green/blue discs, 200ms/frame)
  bg.png         128x128 diagonal stripes (background-image quality probe)
  tone.wav       16-bit PCM sine ( MediaPlayer / SoundPool decode probe )
"""
import os, math, struct, wave
from PIL import Image

BASE = "/home/z/my-project/fixtures/capaudit_probe"
A = os.path.join(BASE, "assets")
os.makedirs(A, exist_ok=True)

# ---- 1. png_rgba.png: RGBA disc, horizontal gradient, alpha outside disc ----
W = H = 64
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
px = im.load()
for y in range(H):
    for x in range(W):
        # gradient blue->red across x, green across y
        r = int(255 * x / (W - 1))
        g = int(255 * y / (H - 1))
        b = 128
        # curved disc mask (radius 30, center 32,32)
        if (x - 32) ** 2 + (y - 32) ** 2 <= 30 * 30:
            px[x, y] = (r, g, b, 255)
        else:
            px[x, y] = (0, 0, 0, 0)
im.save(os.path.join(A, "png_rgba.png"))

# ---- 2. png_palette.png: palette (P) mode, 4 exact quadrants ----
im = Image.new("P", (W, H), 0)
px = im.load()
cols = [(0, (255, 0, 0)), (1, (0, 255, 0)), (2, (0, 0, 255)), (3, (255, 255, 0))]
for y in range(H):
    for x in range(W):
        idx = (1 if y >= H // 2 else 0) | (2 if x >= W // 2 else 0)
        px[x, y] = idx
im.putpalette([c for _, c in cols for c in c] + [0] * (768 - 12))
im.save(os.path.join(A, "png_palette.png"))

# ---- 3. img.jpg: horizontal gradient red->blue ----
im = Image.new("RGB", (W, H))
px = im.load()
for y in range(H):
    for x in range(W):
        px[x, y] = (int(255 * x / (W - 1)), 64, int(255 * (W - 1 - x) / (W - 1)))
im.save(os.path.join(A, "img.jpg"), quality=90)

# ---- 4. img.webp: magenta disc on cyan ----
im = Image.new("RGBA", (W, H), (0, 255, 255, 255))
px = im.load()
for y in range(H):
    for x in range(W):
        if (x - 32) ** 2 + (y - 32) ** 2 <= 24 * 24:
            px[x, y] = (255, 0, 255, 255)
im.save(os.path.join(A, "img.webp"))

# ---- 5. anim.gif: 3 frames red/green/blue discs, 200 ms each ----
frames = []
for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
    f = Image.new("RGB", (48, 48), (20, 20, 20))
    fp = f.load()
    for y in range(48):
        for x in range(48):
            if (x - 24) ** 2 + (y - 24) ** 2 <= 18 * 18:
                fp[x, y] = color
    frames.append(f)
frames[0].save(os.path.join(A, "anim.gif"), save_all=True,
               append_images=frames[1:], duration=200, loop=0)

# ---- 6. bg.png: diagonal stripes (bg quality probe) ----
im = Image.new("RGB", (128, 128))
px = im.load()
for y in range(128):
    for x in range(128):
        px[x, y] = (200, 200, 200) if (x + y) // 8 % 2 == 0 else (40, 40, 40)
im.save(os.path.join(A, "bg.png"))

# ---- 7. tone.wav: 0.5s 440Hz sine 16-bit mono 8kHz ----
path = os.path.join(A, "tone.wav")
with wave.open(path, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
    samples = b"".join(
        struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / 8000)))
        for i in range(4000))
    w.writeframes(samples)

for f in sorted(os.listdir(A)):
    print(f, os.path.getsize(os.path.join(A, f)))
