#!/usr/bin/env python3
"""CAMPAIGN 010 R1 — revived+extended a4 fixture generator.
Creates known PNGs via PIL (the original oracle) + expected RGBA files +
manifest.json for tests/exp088_a4_png_decoder_test.cpp.
Extended beyond the original EXP-088 set: tRNS, palette 4-bit, interlaced,
16-bit, 1-bit gray, color_type 3 with tRNS."""
import os, json
from PIL import Image

OUT = "/tmp/uc010_a4"
os.makedirs(OUT, exist_ok=True)
cases = []

def add(name, pil_img, color_type, save_kwargs=None):
    png_path = os.path.join(OUT, name + ".png")
    rgba_path = os.path.join(OUT, name + ".rgba")
    kw = dict(save_kwargs or {})
    if "pnginfo" not in kw:
        pil_img.save(png_path, "PNG", **kw)
    else:
        pil_img.save(png_path, "PNG", **kw)
    expected = pil_img.convert("RGBA").tobytes()
    with open(rgba_path, "wb") as f:
        f.write(expected)
    cases.append({"name": name, "color_type": color_type,
                  "width": pil_img.width, "height": pil_img.height,
                  "png_path": png_path, "expected_rgba_path": rgba_path})

# color_type 0 gray
add("gray8", Image.new("L", (5, 3), 128), 0)
# color_type 2 rgb
add("rgb8", Image.new("RGB", (4, 4), (10, 200, 30)), 2)
# color_type 4 gray+alpha
add("ga8", Image.frombytes("LA", (3, 5), bytes([64, 255, 128, 128, 200, 0] * 5)), 4)
# color_type 6 rgba
add("rgba8", Image.new("RGBA", (6, 2), (1, 2, 3, 255)), 6)
# palette (auto color_type 3)
pal = Image.new("P", (7, 3))
pal.putpalette([255, 0, 0, 0, 255, 0, 0, 0, 255] + [0, 0, 0] * 253)
for x in range(7):
    for y in range(3):
        pal.putpixel((x, y), (x + y) % 3)
add("palette8", pal, 3)
# tRNS on RGB — NOTE: PIL convert("RGBA") does NOT apply tRNS colorkeys on
# RGB/L images and PIL DROPS the transparency kwarg entirely when saving RGB/L
# PNGs (verified: no tRNS chunk in the file). The expected bytes are computed
# manually with the colorkey applied, and the tRNS chunk is injected by hand.
def add_manual(name, w, h, rgba_bytes, color_type, save_img):
    png_path = os.path.join(OUT, name + ".png")
    rgba_path = os.path.join(OUT, name + ".rgba")
    save_img.save(png_path, "PNG")
    with open(rgba_path, "wb") as f:
        f.write(bytes(rgba_bytes))
    cases.append({"name": name, "color_type": color_type, "width": w, "height": h,
                  "png_path": png_path, "expected_rgba_path": rgba_path})

key = (12, 34, 56)
rgbtns = Image.new("RGB", (4, 4), key)
graytns = Image.new("L", (5, 5), 77)
g16img = Image.new("I;16", (3, 3), 40000)
buf = bytearray()
for i in range(4 * 4):
    buf += bytes(key) + b"\x00"  # every pixel IS the key color → alpha 0

import zlib as _zlib, struct as _struct
def inject_trns(png_path, payload):
    """Insert a tRNS chunk after IHDR (PIL silently drops RGB/L transparency)."""
    data = open(png_path, "rb").read()
    trns = b"tRNS" + payload
    chunk = _struct.pack(">I", len(payload)) + trns + _struct.pack(">I", _zlib.crc32(trns) & 0xFFFFFFFF)
    ihdr_end = 8 + 12 + 13  # sig + IHDR chunk (len+type+data+crc)
    open(png_path, "wb").write(data[:ihdr_end] + chunk + data[ihdr_end:])

add_manual("rgb_trns", 4, 4, buf, 2, rgbtns)
inject_trns(os.path.join(OUT, "rgb_trns.png"), _struct.pack(">HHH", 12, 34, 56))

gbuf = bytearray()
for i in range(5 * 5):
    gbuf += bytes([77, 77, 77, 0])  # gray 77 == key → alpha 0
add_manual("gray_trns", 5, 5, gbuf, 0, graytns)
inject_trns(os.path.join(OUT, "gray_trns.png"), _struct.pack(">H", 77))

# 16-bit gray: decoder strips per libpng png_set_strip_16 (value >> 8).
v = 40000
b8 = v >> 8
g16 = bytearray()
for i in range(3 * 3):
    g16 += bytes([b8, b8, b8, 255])
add_manual("gray16", 3, 3, g16, 0, g16img)
# palette + tRNS
palt = Image.new("P", (4, 4))
palt.putpalette([9, 99, 9, 5, 5, 55] + [0, 0, 0] * 254)
for x in range(4):
    for y in range(4):
        palt.putpixel((x, y), (x + y) % 2)
palt.save(os.path.join(OUT, "palette_trns.png"), "PNG", transparency=bytes([0, 255]))
with open(os.path.join(OUT, "palette_trns.rgba"), "wb") as f:
    im = Image.open(os.path.join(OUT, "palette_trns.png")).convert("RGBA")
    f.write(im.tobytes())
cases.append({"name": "palette_trns", "color_type": 3, "width": 4, "height": 4,
              "png_path": os.path.join(OUT, "palette_trns.png"),
              "expected_rgba_path": os.path.join(OUT, "palette_trns.rgba")})
# 1-bit gray
onebit = Image.new("1", (8, 2), 1)
onebit.putpixel((0, 0), 0)
add("gray1", onebit, 0)
# 4-bit palette
pal4 = Image.new("P", (6, 2))
pal4.putpalette([c for i in range(16) for c in (i * 16, 0, i * 15)])
for x in range(6):
    for y in range(2):
        pal4.putpixel((x, y), x)
add("palette4", pal4, 3)
# interlaced RGBA (Adam7)
add("interlaced", Image.new("RGBA", (9, 9), (7, 8, 9, 200)), 6, {"interlace": 1})

with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(cases, f, indent=1)
print(f"wrote {len(cases)} fixtures to {OUT}")
