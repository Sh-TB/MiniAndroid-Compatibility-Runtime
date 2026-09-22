#!/usr/bin/env python3
"""s83b_ladder.py — S83-B2 foundation ladder: l4e_layerlist + l4f_codelayer.

Pixel pins (device 1080x1920, density 1.0 → px == dp):

l4e_layerlist (XML law — layer-list + ring + line + dash):
  root bg #202020; three full-width views stacked: y[0,200) layer_bg,
  y[200,400) ring_bg, y[400,520) line_bg.
  L1 center (540,100)   = D32F2F red   (inset shape solid; AOSP
                        LayerDrawable item 1 paints OVER the color item)
  L1 rim    (540,10)    = 1B5E20 green (outside top inset → color item)
  L1 dash   (104,42)    = 64B5F6 blue  (x mod 26 == 0 → dash ON)
  L1 gap    (100,42)    = D32F2F red   (x mod 26 == 22 → gap → fill shows)
  RING hole (540,300)   = 202020 dark  (innerRadius = 200/4 = 50)
  RING band (602,300)   = FFEB3B yellow (d = 62 ∈ [50, 50+20])
  LINE dash (544,460)   = 4CAF50 green (x mod 32 == 0 → dash ON)
  LINE gap  (540,460)   = 202020 dark  (x mod 32 == 28 ≥ 20 → gap)

l4f_codelayer (code law — LayerDrawable/GradientDrawable capture):
  root bg rgb(18,18,18); v1 y[0,300) code LayerDrawable{pad indigo,
  ring inset(100,50,100,50)}, v2 y[300,600) rounded green rect w/ red stroke.
  L1 hole  (540,150)  = 303F9F indigo (innerRadius 50 px override;
                       Color.rgb(48,63,159))
  L1 band  (602,150)  = FF7043 orange (d = 62 ∈ [50, 75])
  L1 pad   (200,20)   = 303F9F indigo (outside ring inset → pad layer)
  RECT mid (540,450)  = 00C853 green  (GradientDrawable.setColor)
  RECT str (540,595)  = E53935 red    (setStroke band, centered inset;
                       Color.rgb(229,57,53))
  RECT arc (10,310)   = E53935 red    (stroke FOLLOWS the radius-30 corner:
                       d((30,330)→(10,310)) = 28.3 ∈ [20,30])
  RECT out (2,302)    = 121212 dark   (d = 39.6 > 30 → outside the rounded
                       corner → root shows)
"""
import glob
import json
import os
import subprocess
import sys
from collections import Counter
from PIL import Image

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
FIX = "/tmp/my-project/gfx_fixtures"
OUT = "/home/z/my-project/run/s83b"
TOL = 6


def run_fixture(name):
    apk = f"{FIX}/{name}.apk"
    outdir = f"{OUT}/{name}"
    os.makedirs(outdir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = f"{outdir}/provenance.json"
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "6", "--frame-delay", "300", "-o", outdir, apk]
    with open(f"{outdir}.log", "w") as lf:
        rc = subprocess.call(cmd, stdout=lf, stderr=lf,
                             timeout=420, env=env)
    frames = sorted(glob.glob(f"{outdir}/frames/frame_*.png"))
    return rc, frames


def px(im, x, y):
    p = im.load()[x, y]
    return (p[0], p[1], p[2])


def check(name, pins, min_nonwhite=0):
    rc, frames = run_fixture(name)
    res = {"fixture": name, "rc": rc, "frames": len(frames), "pins": {},
           "PASS": False}
    if not frames:
        res["error"] = "no frames"
        return res
    im = Image.open(frames[-1]).convert("RGBA")
    nonwhite = 0
    w, h = im.size
    pix = im.load()
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            p = pix[x, y]
            if not (p[0] > 245 and p[1] > 245 and p[2] > 245):
                nonwhite += 1
    res["nonwhite"] = nonwhite
    all_ok = nonwhite >= min_nonwhite
    for label, (x, y), want in pins:
        got = px(im, x, y)
        ok = all(abs(got[i] - want[i]) <= TOL for i in range(3))
        res["pins"][label] = {"at": [x, y], "want": list(want),
                              "got": list(got), "ok": ok}
        all_ok = all_ok and ok
    res["PASS"] = bool(all_ok and rc == 0)
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {
        "l4e_layerlist": check("l4e_layerlist", [
            ("L1_shape_center", (540, 100), (0xD3, 0x2F, 0x2F)),
            ("L1_color_rim", (540, 10), (0x1B, 0x5E, 0x20)),
            ("L1_dash_on", (104, 42), (0x64, 0xB5, 0xF6)),
            ("L1_dash_gap", (100, 42), (0xD3, 0x2F, 0x2F)),
            ("RING_hole", (540, 300), (0x20, 0x20, 0x20)),
            ("RING_band", (602, 300), (0xFF, 0xEB, 0x3B)),
            ("LINE_dash_on", (544, 460), (0x4C, 0xAF, 0x50)),
            ("LINE_dash_gap", (540, 460), (0x20, 0x20, 0x20)),
        ], min_nonwhite=50000),
        "l4f_codelayer": check("l4f_codelayer", [
            ("L1_hole_indigo", (540, 150), (0x30, 0x3F, 0x9F)),
            ("RING_band_orange", (602, 150), (0xFF, 0x70, 0x43)),
            ("L1_pad_indigo", (200, 20), (0x30, 0x3F, 0x9F)),
            ("RECT_mid_green", (540, 450), (0x00, 0xC8, 0x53)),
            ("RECT_stroke_red", (540, 595), (0xE5, 0x39, 0x35)),
            ("RECT_corner_arc_red", (10, 310), (0xE5, 0x39, 0x35)),
            ("RECT_outside_dark", (2, 302), (0x12, 0x12, 0x12)),
        ], min_nonwhite=100000),
    }
    npass = sum(1 for r in results.values() if r["PASS"])
    with open(f"{OUT}/S83B_LADDER.json", "w") as f:
        json.dump(results, f, indent=1)
    for k, r in results.items():
        print(k, "PASS" if r["PASS"] else "FAIL", "nonwhite=", r.get("nonwhite"))
        if not r["PASS"]:
            for pl, pv in r["pins"].items():
                if not pv.get("ok"):
                    print("   PIN-FAIL", pl, pv)
    print(f"S83-B2 LADDER: {npass}/{len(results)}")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
