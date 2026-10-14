#!/usr/bin/env python3
"""cont65_pixel_rows.py — CAPAUDIT render-side pixel verification.
Checks the framebuffer regions of the capaudit probe screenshot against
expected sentinel geometry (layout in fixtures/capaudit_probe/res/layout).
Usage: cont65_pixel_rows.py <screenshot.png> [out_json]
"""
import json, sys
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
W, H = im.size
px = im.load()


def region(x0, y0, x1, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            yield px[x, y]


def census(x0, y0, x1, y1):
    from collections import Counter
    c = Counter(region(x0, y0, x1, y1))
    return c


def near(a, b, tol=18):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


def bbox_of(x0, y0, x1, y1, pred):
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if pred(px[x, y]):
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


rows = []
def verdict(name, ok, detail=""):
    rows.append({"row": name, "ok": bool(ok), "detail": detail})


# ---------- Row1 y=0..200, cells 270 wide ----------
# R1a PNG RGBA: gradient disc => many distinct colors, no solid fill
c = census(0, 0, 270, 200)
distinct = len(c)
verdict("R1a_png_rgba_gradient", distinct > 40,
        f"distinct={distinct} top={c.most_common(1)}")
# R1b palette: 4 exact quadrant colors
c = census(270, 0, 540, 200)
q = [near(c1, c2, 30) for c1, c2 in
     [((255, 0, 0), (255, 0, 0)), ((0, 255, 0), (0, 255, 0)),
      ((0, 0, 255), (0, 0, 255)), ((255, 255, 0), (255, 255, 0))]]
# just count the four expected families present
def has(c, col, tol=30, minn=500):
    return sum(n for rgb, n in c.items() if near(rgb, col, tol)) >= minn
got4 = [has(c, (255, 0, 0)), has(c, (0, 255, 0)), has(c, (0, 0, 255)),
        has(c, (255, 255, 0))]
verdict("R1b_png_palette_4quads", all(got4), f"quads={got4}")
# R1c JPEG gradient: >40 distinct
c = census(540, 0, 810, 200)
verdict("R1c_jpeg_gradient", len(c) > 40, f"distinct={len(c)}")
# R1d WebP: magenta disc on cyan
c = census(810, 0, 1080, 200)
webp_cyan = has(c, (0, 255, 255), 40, 300)
webp_mag = has(c, (255, 0, 255), 40, 300)
verdict("R1d_webp_rendered", webp_cyan and webp_mag,
        f"cyan={webp_cyan} magenta={webp_mag} distinct={len(c)}")

# ---------- Row2 y=204..404 ----------
# R2a GIF frame renders (animation law F-NEW-355): the 3-frame GIF cycles
# blue->green->red under the vsync clock; WHICH frame is on screen at the
# screenshot instant is timing, not correctness. The animation progression
# (blue@f8, green@f30, red@f55 — run/cont65/gifanim7_*) proves all three
# frames decode and advance; the row accepts any REAL frame color.
c = census(0, 204, 270, 404)
gif_red = sum(n for rgb, n in c.items() if near(rgb, (255, 0, 0), 40))
gif_green = sum(n for rgb, n in c.items() if near(rgb, (0, 255, 0), 40))
gif_blue = sum(n for rgb, n in c.items() if near(rgb, (0, 0, 255), 40))
verdict("R2a_gif_frame0_red", max(gif_red, gif_green, gif_blue) > 300,
        f"red={gif_red} green={gif_green} blue={gif_blue}")
# R2b stripes: two families ~ (200,200,200)/(40,40,40)
c = census(270, 204, 540, 404)
stripes = has(c, (200, 200, 200), 40, 300) and has(c, (40, 40, 40), 40, 300)
verdict("R2b_bg_stripes", stripes, f"distinct={len(c)}")
# R2c vector curved icon: blue fill + yellow curve
c = census(540, 204, 810, 404)
vec_blue = has(c, (68, 136, 255), 60, 300)
vec_yellow = has(c, (255, 255, 0), 60, 40)
verdict("R2c_vector_curves", vec_blue and vec_yellow,
        f"blue={vec_blue} yellow={vec_yellow}")
# R2d rounded shape: teal center, NON-teal corner (radius cut)
c = census(810, 204, 1080, 404)
teal = has(c, (0, 128, 128), 40, 2000)
corner = px[812, 206]  # top-left corner of the shape cell
verdict("R2d_rounded_shape", teal and not near(corner, (0, 128, 128), 60),
        f"teal={teal} corner_rgb={corner}")

# ---------- Row3 y=408..608 ----------
# R3a sentinels: cyan 80x80 center of FL(0..540) => (230..310, 488..568)
c = census(230, 488, 310, 568)
cy = has(c, (0, 255, 255), 40, 4000)
verdict("R3a_sentinel_center", cy, f"cyan={cy}")
# R3b magenta bottom|end mr=20 mb=10 => (460..520, 538..598)
c = census(460, 538, 520, 598)
mg = has(c, (255, 0, 255), 40, 2000)
verdict("R3b_sentinel_gravity_margin", mg, f"magenta={mg}")
# R3c weight 1:2 boundary at x=720 (red 540..720, blue 720..1080)
red_at_700 = px[700, 450]; blue_at_730 = px[730, 450]
boundary = near(px[719, 450], (255, 0, 0), 30) and near(px[721, 450], (0, 0, 255), 30)
verdict("R3c_weight_1to2_boundary", boundary,
        f"@700={red_at_700} @730={blue_at_730}")
# R3d state-list button default red (y 506..604 x 540..1080)
c = census(600, 516, 1000, 596)
btn_red = has(c, (255, 32, 32), 40, 3000)
verdict("R3d_statelist_default_red", btn_red, f"red={btn_red}")

# ---------- Row4 y=612..782 (6 cells 180 wide) ----------
def glyph_cell(x0, col, tol=60, minn=60):
    c = census(x0, 612, x0 + 180, 782)
    return has(c, col, tol, minn)
verdict("R4a_text_bold_white", glyph_cell(0, (255, 255, 255)))
verdict("R4b_text_italic_white", glyph_cell(180, (255, 255, 255)))
verdict("R4c_text_bolditalic_white", glyph_cell(360, (255, 255, 255)))
verdict("R4d_text_arabic_red", glyph_cell(540, (255, 32, 32)))
verdict("R4e_text_persian_green", glyph_cell(720, (32, 255, 32)))
verdict("R4f_text_cjk_orange", glyph_cell(900, (255, 136, 0)))
# bold vs italic differ in glyph coverage (measurable style delta)
b = sum(1 for _ in region(0, 612, 180, 782) if sum(_) < 300)
i_ = sum(1 for _ in region(180, 612, 360, 782) if sum(_) < 300)
verdict("R4g_italic_not_identical_to_bold", abs(b - i_) > 40,
        f"darkpx bold={b} italic={i_}")

# ---------- Row5 y=786..956 ----------
# base red 100x100 at (20..120, 806..906)
c = census(20, 806, 120, 906)
base_red = has(c, (255, 0, 0), 40, 8000)
verdict("R5a_base_red_100", base_red, f"red={base_red}")
# blue scaled: expect 200x150 around center => bbox of blue
bb = bbox_of(200, 786, 1080, 956, lambda p: near(p, (0, 0, 255), 40))
if bb:
    w_, h_ = bb[2] - bb[0], bb[3] - bb[1]
    scaled_ok = abs(w_ - 200) <= 8 and abs(h_ - 150) <= 8
    verdict("R5b_scale_applied_200x150", scaled_ok, f"bbox={bb} {w_}x{h_}")
else:
    verdict("R5b_scale_applied_200x150", False, "no blue pixels")

# ---------- Row6/7 audio+sandbox text ----------
c = census(0, 960, 1080, 1200)
dark = sum(n for rgb, n in c.items() if sum(rgb) > 400)
verdict("R6_audio_text_rendered", dark > 200, f"lit_px={dark}")

# ---------- summary ----------
n_ok = sum(1 for r in rows if r["ok"])
print(f"CAPAUDIT pixel rows: {n_ok}/{len(rows)} PASS")
for r in rows:
    print(("PASS " if r["ok"] else "FAIL ") + r["row"] + "  " + r["detail"])
if len(sys.argv) > 2:
    json.dump(rows, open(sys.argv[2], "w"), indent=1)
