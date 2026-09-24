#!/usr/bin/env python3
"""S93 font/text truth proof — adversarial fixtures (S93 §5/§6, §23 11-16).

Correct render must PASS; tofu, fallback(wrong font), missing glyph, wrong
glyph, broken font bytes, clipped text, missing text must each be rejected.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = "/home/z/my-project"
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))
sys.path.insert(0, os.path.join(REPO, "tools"))

from probes.semantic_font import (glyph_truth, font_object_truth,  # noqa
                                  text_truth, render_reference)

OUT = "/tmp/s93_font"
os.makedirs(OUT, exist_ok=True)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
TXT = "PLAY 2048"

ok_all = True


def check(name, got, oracle):
    global ok_all
    ok = all(got.get(k) == v for k, v in oracle.items())
    print(f"{'PASS' if ok else 'REJ'} {name:24s} verdict={got['verdict']:22s} "
          f"detections={got.get('detections', [])[:3]}")
    if not ok:
        print(f"     oracle={oracle}")
        ok_all = False


def render(text, font_path, size=32, tofu=False):
    font = ImageFont.truetype(font_path, size)
    tmp = Image.new("L", (10, 10))
    d = ImageDraw.Draw(tmp)
    box = d.textbbox((0, 0), text, font=font)
    W = box[2] - box[0] + 16
    H = box[3] - box[1] + 16
    if tofu:
        n = len([c for c in text if c != " "])
        W = max(W, 16 + n * (int(size * 0.62) + 6) + 8)
    im = Image.new("L", (W, H), 250)
    dd = ImageDraw.Draw(im)
    if tofu:
        # every glyph rendered as the classic hollow .notdef box
        x = 8
        for ch in text:
            if ch == " ":
                x += size // 3
                continue
            dd.rectangle([x, 8, x + int(size * 0.62), 8 + size],
                         outline=20, width=max(2, size // 14))
            x += int(size * 0.62) + 6
    else:
        dd.text((8 - box[0], 8 - box[1]), text, font=font, fill=15)
    return im.convert("RGB")


# 1 correct render -> FONT_VISUALLY_VERIFIED
p = render(TXT, SANS)
r = glyph_truth(p, TXT, reference_font_path=SANS)
check("correct_render", r, {"verdict": "FONT_VISUALLY_VERIFIED",
                            "GLYPH_CORRECTNESS": "PASS"})

# 2 tofu boxes -> UNREADABLE
p = render(TXT, SANS, tofu=True)
r = glyph_truth(p, TXT, reference_font_path=SANS)
check("tofu_glyphs", r, {"verdict": "UNREADABLE"})

# 3 fallback/wrong font: expected SERIF, observed SANS -> WRONG_FONT
p = render(TXT, SANS)                     # observed rendered with sans
r = glyph_truth(p, TXT, reference_font_path=SERIF)
check("fallback_font", r, {"GLYPH_CORRECTNESS": "FAIL"})

# 3b same-family control: mono observed vs sans reference -> also rejected
p = render(TXT, MONO)
r = glyph_truth(p, TXT, reference_font_path=SANS)
check("wrong_family_control", r, {"GLYPH_CORRECTNESS": "FAIL"})

# 4 missing glyph: "ABCD" rendered, expected "ABCDE" -> MISSING_GLYPH
p = render("ABCD", SANS)
r = glyph_truth(p, "ABCDE", reference_font_path=SANS)
check("missing_glyph", r, {"detections": ["MISSING_GLYPH"],
                           "GLYPH_CORRECTNESS": "FAIL"})

# 5 wrong glyph: expected PLAY, observed PL4Y -> WRONG_GLYPH
p = render("PL4Y", SANS)
r = glyph_truth(p, "PLAY", reference_font_path=SANS)
check("wrong_glyph", r, {"GLYPH_CORRECTNESS": "FAIL"})

# 6 broken font bytes -> BROKEN_FONT
corrupt = bytearray(open(SANS, "rb").read()[:4096])
corrupt[0:4] = b"XXXX"
cb = bytes(corrupt) + open(SANS, "rb").read()[4096:]
p = os.path.join(OUT, "broken.ttf")
open(p, "wb").write(cb)
r = font_object_truth(p)
check("broken_font", r, {"verdict": "BROKEN_FONT"})

# 7 text region: correct -> TEXT_VISUALLY_VERIFIED
shot = Image.new("RGB", (320, 240), (245, 246, 248))
shot.paste(render("SCORE 42", SANS, size=24), (40, 100))
node = {"x": 40, "y": 100, "width": 240, "height": 48,
        "text": "SCORE 42"}
r = text_truth(shot, node=node)
check("text_region_ok", r, {"verdict": "TEXT_VISUALLY_VERIFIED"})

# 8 text region: ViewTree says text but pixels blank -> MISSING_TEXT
shot = Image.new("RGB", (320, 240), (245, 246, 248))
node = {"x": 40, "y": 100, "width": 240, "height": 48,
        "text": "SCORE 42"}
r = text_truth(shot, node=node)
check("text_missing", r, {"verdict": "MISSING_TEXT"})

# 9 text region: glyph ink extends above the node top -> CLIPPED_TEXT
full = render("SCORE 42", SANS, size=24)
shot = Image.new("RGB", (320, 240), (245, 246, 248))
shot.paste(full, (40, 92))
node = {"x": 40, "y": 100, "width": 240, "height": 40,
        "text": "SCORE 42"}
r = text_truth(shot, node=node)
check("text_clipped", r, {"verdict": "CLIPPED_TEXT"})

print(f"\nRESULT: {'ALL PASS' if ok_all else 'FAILURES PRESENT'}")
sys.exit(0 if ok_all else 1)
