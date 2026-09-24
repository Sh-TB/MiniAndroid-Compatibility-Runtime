#!/usr/bin/env python3
"""S93 animation-truth law proof — adversarial fixtures (S93 §10/§23 17-20).

Fixture set: correct motion, frozen, repeated frames, wrong order (teleport),
placeholder alternation, random noise, moving-background/stationary-object,
object-lost. ORACLE expectations per fixture.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

REPO = "/home/z/my-project"
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))
sys.path.insert(0, os.path.join(REPO, "tools"))

from probes.semantic_animation import animation_truth  # noqa: E402

OUT = "/tmp/s93_anim"
os.makedirs(OUT, exist_ok=True)
W, H = 160, 120


def frame(sprites, bg_shift=0, noise=False, fill=None):
    """sprites: list of (cx, cy, r, color). bg_shift slides a bg stripe.
    Stripes live at y 4-24 and y 96-116 (outside the sprite lane region)."""
    if fill is not None:
        return Image.new("RGB", (W, H), fill)
    im = Image.new("RGB", (W, H), (238, 242, 246))
    d = ImageDraw.Draw(im)
    d.rectangle([40 + bg_shift, 4, 120 + bg_shift, 24], fill=(200, 208, 216))
    d.rectangle([40 + bg_shift, 96, 120 + bg_shift, 116],
                fill=(200, 208, 216))
    for cx, cy, r, color in sprites:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        d.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2],
                  fill=(250, 250, 250))
    if noise:
        a = np.array(im)
        rng = np.random.default_rng()  # unseeded: every frame differs
        a = rng.integers(0, 256, size=a.shape, dtype=np.uint8)
        return Image.fromarray(a)
    return im


paths = []


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p)
    return p


def run(name, imgs, oracle, region=None, expect_motion=True,
        expected_direction="any"):
    ps = [save(im, f"{name}_{i}.png") for i, im in enumerate(imgs)]
    r = animation_truth(ps, object_region=region,
                        expect_motion=expect_motion,
                        expected_direction=expected_direction)
    got = {k: r.get(k) for k in oracle}
    ok = all(got.get(k) == v for k, v in oracle.items())
    print(f"{'PASS' if ok else 'REJ'} {name:26s} verdict={r['verdict']:26s} "
          f"decoded={r.get('ANIMATION_DECODED'):4s} rendered="
          f"{r.get('ANIMATION_RENDERED'):4s} content="
          f"{r.get('ANIMATION_CONTENT_VERIFIED'):4s} geom="
          f"{r.get('ANIMATION_GEOMETRY_VERIFIED'):4s} travel="
          f"{r.get('object_travel_px')}")
    if not ok:
        print(f"     oracle={oracle} got={got} detections={r['detections']}")
    return ok


results = []
REGION = (20, 36, 120, 56)  # sprite lane y36..92, stripes outside

# 1 correct: ball moves right, background stripes also shift slightly
imgs = [frame([(40 + i * 8, 70, 10, (30, 90, 220))], bg_shift=i * 2)
        for i in range(6)]
results.append(run("correct_motion", imgs,
                   {"verdict": "ANIMATION_GEOMETRY_VERIFIED",
                    "ANIMATION_CONTENT_VERIFIED": "PASS",
                    "ANIMATION_GEOMETRY_VERIFIED": "PASS"}, region=REGION))

# 2 frozen: identical frames
imgs = [frame([(60, 70, 10, (30, 90, 220))]) for _ in range(6)]
results.append(run("frozen", imgs,
                   {"verdict": "FROZEN",
                    "ANIMATION_CONTENT_VERIFIED": "FAIL"}, region=REGION))

# 3 repeated frames: A A A B B B
imgs = [frame([(60, 70, 10, (30, 90, 220))])] * 3 + \
    [frame([(90, 70, 10, (30, 90, 220))])] * 3
results.append(run("repeated_frames", imgs,
                   {"verdict": "ANIMATION_RENDERED"}, region=REGION))

# 4 wrong order / teleport: 1,2,3 -> back to 1 under a monotonic contract
xs = [40, 48, 56, 40, 48, 56]
imgs = [frame([(x, 70, 10, (30, 90, 220))]) for x in xs]
results.append(run("suspected_wrong_order", imgs,
                   {"ANIMATION_GEOMETRY_VERIFIED": "FAIL",
                    "ANIMATION_CONTENT_VERIFIED": "PASS"}, region=REGION,
                   expected_direction="monotonic"))

# 5 placeholder animation: solid red / solid blue alternation
imgs = [frame(None, fill=(220, 40, 40)), frame(None, fill=(40, 60, 220))] * 3
results.append(run("placeholder_animation", imgs,
                   {"verdict": "PLACEHOLDER_ANIMATION",
                    "ANIMATION_RENDERED": "FAIL"}))

# 6 random noise
imgs = [frame([], noise=True) for _ in range(6)]
results.append(run("noise", imgs,
                   {"verdict": "NOISE",
                    "ANIMATION_CONTENT_VERIFIED": "FAIL"}, region=REGION))

# 7 moving background, stationary object (S93 §10: object must move)
imgs = [frame([(60, 70, 10, (30, 90, 220))], bg_shift=i * 6)
        for i in range(6)]
results.append(run("bg_moves_object_static", imgs,
                   {"ANIMATION_GEOMETRY_VERIFIED": "FAIL"},
                   region=REGION))

# 8 object lost: sprite present frames 0-2, gone 3-5
imgs = [frame([(60, 70, 10, (30, 90, 220))]) for _ in range(3)] + \
    [frame([]) for _ in range(3)]
results.append(run("object_lost", imgs,
                   {"ANIMATION_CONTENT_VERIFIED": "FAIL"},
                   region=REGION))

n_pass = sum(results)
print(f"\nRESULT: {n_pass}/{len(results)} fixtures matched oracle")
sys.exit(0 if n_pass == len(results) else 1)
