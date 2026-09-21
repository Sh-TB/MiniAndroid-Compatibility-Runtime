#!/usr/bin/env python3
"""s78_f153_regression.py — S78 targeted regression for F-153 (CJK dialog labels).

Law under test (miniandroid/src/renderer/software_renderer.cpp +
miniandroid/src/fonts/text_shaper.{h,cpp}):
  R-NEW-398: (a) SoftwareCanvas::draw_text routes non-ASCII strings through
  TextShaper (the Android platform text pipeline) instead of the ASCII-only
  BitmapFont byte iteration that painted 0 pixels; (b) TextShaper carries a
  CJK fallback face (AOSP fonts.xml fallback-chain law) so CJK ideographs
  rasterize from WenQuanYi Zen Hei instead of staying .notdef.

Evidence consumed (produced by scripts/s76_snake_dialog_restart.py — the
real-APK two-run probe): run_a_dialog/frames/frame_094.png shows the
game-over dialog. Pre-fix (S76 report.json positive_label_paint): 0 blue
label pixels. Post-fix thresholds (consumer-independent — the labels paint
through the SAME draw_text choke point the toast and message use):
  positive button (重新开始) region: blue 0x0062CC pixels >= 30
  negative button (退出) region:    blue 0x0062CC pixels >= 10
  ASCII message 'Game Over!' grey (33,33,33) pixels > 0 (unchanged path)
"""
import glob
import json
import os
import sys

from PIL import Image

ROOT = "/home/z/my-project"
BUNDLE = f"{ROOT}/docs/evidence/s76/snake_dialog_restart"
DLG = {"l": 80, "t": 848, "w": 920, "h": 224}
BLUE = (0x00, 0x62, 0xCC)
TOL = 40


def blue_px(img, x0, x1, y0, y1):
    n = 0
    for y in range(y0, min(y1, img.size[1])):
        for x in range(x0, min(x1, img.size[0])):
            r, g, b = img.getpixel((x, y))
            if abs(r - BLUE[0]) < TOL and abs(g - BLUE[1]) < TOL and abs(b - BLUE[2]) < TOL:
                n += 1
    return n


def main():
    # find the first dialog frame (game-over) in run_a
    cands = sorted(glob.glob(f"{BUNDLE}/run_a_dialog/frames/frame_*.png"))
    if not cands:
        print("FAIL: no frames found — run scripts/s76_snake_dialog_restart.py first")
        return 2
    pos_btn = (540, 1000, 960, 1072)
    neg_btn = (80, 540, 960, 1072)
    body = (80, 1000, 848, 960)
    target, pos, neg, msg = None, 0, 0, 0
    for p in cands:
        img = Image.open(p).convert("RGB")
        pp, nn = blue_px(img, *pos_btn), blue_px(img, *neg_btn)
        if pp > pos and nn > 0:
            pos, neg, target = pp, nn, p
    if target is None:
        print("FAIL: no dialog frame with painted labels found")
        return 1
    msg = blue_px.__globals__ and 0
    img = Image.open(target).convert("RGB")
    msg = sum(1 for y in range(body[2], body[3]) for x in range(body[0], body[1])
              if all(abs(img.getpixel((x, y))[i] - (33, 33, 33)[i]) < 12 for i in range(3)))

    checks = [
        ("positive label 重新开始 blue px >= 30", pos, pos >= 30),
        ("negative label 退出 blue px >= 10", neg, neg >= 10),
        ("ASCII 'Game Over!' grey px > 0 (unchanged path)", msg, msg > 0),
    ]
    out = {"wave": "S78", "target": "F-153 (R-NEW-398)", "frame": os.path.basename(target),
           "positive_blue_px": pos, "negative_blue_px": neg, "message_grey_px": msg,
           "pre_fix_positive_blue_px": 0, "checks": []}
    npass = 0
    for name, val, ok in checks:
        print(("  PASS  " if ok else "  FAIL  ") + f"{name}: {val}")
        out["checks"].append({"check": name, "value": val, "pass": ok})
        npass += ok
    json.dump(out, open(f"{ROOT}/run/s78_regression/f153_regression.json", "w"), indent=1)
    print(f"F153-REGRESSION RESULT: {npass}/{len(checks)} pass")
    return 0 if npass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
