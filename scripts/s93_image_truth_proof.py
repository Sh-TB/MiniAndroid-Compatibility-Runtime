#!/usr/bin/env python3
"""S93 image-truth law proof — synthetic adversarial fixtures (S93 §23 subset).

Proves L-S93-IMG-1..6 with ORACLE expectations before the module may be
committed as a law. Every weak metric must fail at least one fixture.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

REPO = "/home/z/my-project"
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))
sys.path.insert(0, os.path.join(REPO, "tools"))

from probes.semantic_image import image_truth, region_partition  # noqa: E402

OUT = "/tmp/s93_fixtures"
os.makedirs(OUT, exist_ok=True)
S, C = 96, 96


def blue_circle_asset():
    im = Image.new("RGBA", (S, C), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([8, 8, S - 8, C - 8], fill=(30, 90, 220, 255))
    d.ellipse([32, 32, S - 32, C - 32], fill=(120, 180, 255, 255))
    return im


def photo_asset():
    im = Image.new("RGB", (S, C))
    px = im.load()
    for y in range(C):
        for x in range(S):
            px[x, y] = (x * 2 % 256, y * 2 % 256, (x + y) % 256)
    d = ImageDraw.Draw(im)
    d.polygon([(10, 80), (40, 30), (70, 80)], fill=(200, 40, 40))
    d.ellipse([55, 10, 88, 43], fill=(250, 220, 60))
    return im.convert("RGBA")


def render_on(bgcolor, asset, box=None, opaque=False):
    """Flatten asset onto a white 320x240 screenshot at box (or center)."""
    canvas = Image.new("RGB", (320, 240), bgcolor)
    a = asset
    if opaque:
        a = asset.copy()
        solid = Image.new("RGBA", a.size, tuple(
            list(a.getpixel((a.width // 2, a.height // 2))[:3]) + [255]))
        a = solid
    if box is None:
        box = ((320 - a.width) // 2, (240 - a.height) // 2,
               a.width, a.height)
    canvas.paste(a, (box[0], box[1]), a if not opaque else None)
    return canvas


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p)
    return p


ASSET_CIRCLE = blue_circle_asset()
ASSET_PHOTO = photo_asset()
PA_PHOTO = save(ASSET_PHOTO, "a_photo.png")   # path saved up-front
CB = (240, 244, 248)  # screenshot background
CENTER = ((320 - S) // 2, (240 - C) // 2, S, C)

fixtures = []

# 1 correct render -> PASS / VISUALLY_VERIFIED
p_asset = save(ASSET_CIRCLE, "a_circle.png")
p_shot = save(render_on(CB, ASSET_CIRCLE), "f1_correct.png")
fixtures.append(("correct_circle", p_shot, p_asset, CENTER,
                 {"verdict": "VISUALLY_VERIFIED", "content": "PASS",
                  "geometry": "PASS"}))

# 2 solid-color replacement -> PLACEHOLDER
canvas = Image.new("RGB", (320, 240), CB)
ImageDraw.Draw(canvas).rectangle(
    [CENTER[0], CENTER[1], CENTER[0] + S, CENTER[1] + C],
    fill=(30, 90, 220))
p_shot = save(canvas, "f2_solid.png")
fixtures.append(("solid_replacement", p_shot, p_asset, CENTER,
                 {"verdict": "PLACEHOLDER", "content": "FAIL"}))

# 3 two-color photo replacement -> WRONG_CONTENT
canvas = Image.new("RGB", (320, 240), CB)
d = ImageDraw.Draw(canvas)
d.rectangle([CENTER[0], CENTER[1], CENTER[0] + S, CENTER[1] + C // 2],
            fill=(90, 200, 90))
d.rectangle([CENTER[0], CENTER[1] + C // 2, CENTER[0] + S,
             CENTER[1] + C], fill=(40, 60, 90))
p_shot = save(canvas, "f3_twocolor.png")
fixtures.append(("two_color_photo_fake", p_shot, PA_PHOTO, CENTER,
                 {"verdict": "WRONG_CONTENT", "content": "FAIL"}))

# 4 opaque replacement of transparent asset -> OPAQUE_REPLACEMENT
# (structure-preserving: alpha forced to 255, transparent zones show the
#  asset's underlying RGB — the classic premultiplication/alpha-drop bug)
_op = np.array(ASSET_CIRCLE)
_op[..., 3] = 255
p_shot = save(render_on(CB, Image.fromarray(_op)), "f4_opaque.png")
fixtures.append(("opaque_replacement", p_shot, p_asset, CENTER,
                 {"verdict": "OPAQUE_REPLACEMENT", "alpha": "FAIL"}))

# 5 wrong position (100px off) -> WRONG_POSITION (blank expected box, asset
# provably rendered elsewhere on screen)
box = (CENTER[0] + 100, CENTER[1], S, C)
p_shot = save(render_on(CB, ASSET_CIRCLE, box=box), "f5_pos.png")
fixtures.append(("wrong_position", p_shot, p_asset, CENTER,
                 {"verdict": "WRONG_POSITION", "content": "FAIL",
                  "geometry": "FAIL"}))

# 6 wrong scale (0.6x) -> WRONG_SCALE
small = ASSET_CIRCLE.resize((int(S * 0.6), int(C * 0.6)), Image.NEAREST)
box = (CENTER[0] + S // 2 - small.width // 2,
       CENTER[1] + C // 2 - small.height // 2, small.width, small.height)
p_shot = save(render_on(CB, small, box=box), "f6_scale.png")
fixtures.append(("wrong_scale", p_shot, p_asset, CENTER,
                 {"verdict": "WRONG_GEOMETRY", "geometry": "FAIL"}))

# 7 clipped (bottom half missing) -> VISUALLY_PARTIAL + geometry FAIL
# (honest class: right content family in the right place, incomplete)
canvas = Image.new("RGB", (320, 240), CB)
canvas.paste(ASSET_CIRCLE, (CENTER[0], CENTER[1]), ASSET_CIRCLE)
d = ImageDraw.Draw(canvas)
d.rectangle([CENTER[0] - 2, CENTER[1] + C // 2, CENTER[0] + S + 2,
             CENTER[1] + C + 2], fill=CB)
p_shot = save(canvas, "f7_clip.png")
fixtures.append(("clipped", p_shot, p_asset, CENTER,
                 {"verdict": "VISUALLY_PARTIAL", "geometry": "FAIL"}))

# 8 missing (blank region, asset rendered nowhere) -> MISSING
canvas = Image.new("RGB", (320, 240), CB)
p_shot = save(canvas, "f8_missing.png")
fixtures.append(("missing", p_shot, p_asset, CENTER,
                 {"verdict": "MISSING", "content": "FAIL"}))

# 9 correct photo render -> PASS (anti over-rejection guard)
p_asset = PA_PHOTO
p_shot = save(render_on(CB, ASSET_PHOTO), "f9_photo.png")
fixtures.append(("correct_photo", p_shot, p_asset, CENTER,
                 {"verdict": "VISUALLY_VERIFIED", "content": "PASS",
                  "geometry": "PASS"}))

# 10 wrong image in place (red triangle vs circle) -> WRONG_CONTENT
tri = Image.new("RGBA", (S, C), (0, 0, 0, 0))
ImageDraw.Draw(tri).polygon([(48, 8), (8, 88), (88, 88)],
                            fill=(200, 30, 30, 255))
p_shot = save(render_on(CB, tri), "f10_wrongimg.png")
fixtures.append(("wrong_image", p_shot, p_asset, CENTER,
                 {"verdict": "WRONG_CONTENT", "content": "FAIL"}))

# --- run + oracle ------------------------------------------------------------
fails = []
for name, shot, asset, region, oracle in fixtures:
    r = image_truth(shot, open(asset, "rb").read(), region=region)
    got = {"verdict": r["verdict"], "content": r["content"]["value"],
           "geometry": r["geometry"]["value"],
           "alpha": r["alpha"]["value"]}
    ok = all(got.get(k) == v for k, v in oracle.items())
    print(f"{'PASS' if ok else 'REJ'} {name:22s} verdict={r['verdict']:20s} "
          f"content={r['content']['value']:4s} geometry="
          f"{r['geometry']['value']:4s} ncc={r.get('ncc')}")
    if not ok:
        fails.append((name, oracle, got))

# region partition law: missing button can't be averaged away
parts = {"background": [0, 0, 320, 200], "button": [140, 210, 40, 20]}
canvas = Image.new("RGB", (320, 240), CB)
p = save(canvas, "f11_partition.png")
rp = region_partition(p, parts)
ok = rp["aggregate"]["value"] == "FAIL" and \
    "button" in rp["aggregate"]["failed_regions"]
print(f"{'PASS' if ok else 'REJ'} region_partition      aggregate="
      f"{rp['aggregate']['value']} failed={rp['aggregate']['failed_regions']}")
if not ok:
    fails.append(("region_partition", "aggregate FAIL w/ button",
                  rp["aggregate"]))

print(f"\nRESULT: {len(fixtures) + 1 - len(fails)} passed, "
      f"{len(fails)} rejected-by-oracle-failures")
sys.exit(1 if fails else 0)
