#!/usr/bin/env python3
"""
m3_style_geometry_check.py — battery gate for the M3 style/layout law fixture.

Parses the U007_LAYOUT_DEBUG=2 trace of the m3_style_weight fixture run and
asserts the AOSP laws the fixture exercises (no pixel playback, pure trace
law checks on measured geometry):

  [1] header TextView = 64dp → 168px at density 2.625 (fixed child wins)
  [2] row LinearLayout measures 1920-168 = 1752 (FIX-M3-004: match-parent
      child re-measured against the REMAINING height, not the full parent)
  [3] style-only buttons carry lp=0/-1 weight=1000 — geometry delivered by
      the style= bag THROUGH THE PARENT CHAIN (child style M3KeypadDigit
      holds only textSize)
  [4] weighted shares: weight-1 buttons ≈ (1080 - 6*margin - slack)/4
  [5] direct override: btn_direct has weight=2000 (direct 2.0 beats style 1.0)
      and measures ≈ double a weight-1 share
  [6] buttons fill the row height (match_height from the bag → 1752 minus
      vertical margins)
"""
import re
import sys

DENSITY = 2.625
SCREEN_W, SCREEN_H = 1080, 1920


def fail(msg):
    print(f"  FAIL: {msg}")
    sys.exit(1)


def main(path):
    log = open(path, errors="replace").read()
    rows = {}
    for m in re.finditer(
            r"\[U007-LAYOUT\]([ ]*)view (\d+) (\S+); id_name=(\S*) "
            r"lp=(-?\d+)/(-?\d+) weight=(-?\d+) orient=(-?\d+) "
            r"measured=(\d+)x(\d+) at=\((-?\d+),(-?\d+)\)", log):
        depth, vid, cls, idname, lpw, lph, weight, orient, mw, mh, l, t = m.groups()
        rows[int(vid)] = dict(cls=cls, idname=idname, lpw=int(lpw), lph=int(lph),
                              weight=int(weight), mw=int(mw), mh=int(mh),
                              left=int(l), top=int(t), depth=(len(depth) - 1) // 2)

    header = [v for v in rows.values() if v["cls"].startswith("Landroid/widget/TextView")]
    if not header:
        fail("header TextView not found")
    h = header[0]
    if h["mh"] != round(64 * DENSITY):  # 64dp -> 168px
        fail(f"header height {h['mh']} != 168 (64dp law)")
    print("  PASS: header 64dp -> 168px")

    row = [v for v in rows.values()
           if v["cls"].startswith("Landroid/widget/LinearLayout") and v["depth"] == 2]
    if not row:
        fail("inner row LinearLayout not found")
    r = row[0]
    if r["mh"] != SCREEN_H - h["mh"]:
        fail(f"row height {r['mh']} != {SCREEN_H - h['mh']} "
             f"(match-parent remeasure law FIX-M3-004)")
    print("  PASS: row = remaining height after header (FIX-M3-004)")

    digits = sorted((v for v in rows.values() if v["idname"].startswith("btn_digit")), key=lambda v: v["mw"])
    direct = [v for v in rows.values() if v["idname"] == "btn_direct"]
    if len(digits) != 2 or not direct:
        fail(f"fixture buttons missing (digits={len(digits)}, direct={len(direct)})")
    d = digits[0]
    if (d["lpw"], d["lph"], d["weight"]) != (0, -1, 1000):
        fail(f"style-only digit lp={d['lpw']}/{d['lph']} weight={d['weight']} "
             f"!= 0/-1/1000 (style-bag layout params law)")
    print("  PASS: style-only buttons carry lp=0/-1 weight=1000 (bag + parent chain)")

    margin = round(4 * DENSITY)  # 4dp layout_margin from the bag
    avail = SCREEN_W - 6 * margin  # 3 buttons x 2 side margins
    expect_w1 = round(avail / 4.0)
    if abs(d["mw"] - expect_w1) > 2:
        fail(f"weight-1 share {d['mw']} != ~{expect_w1}")
    print(f"  PASS: weight-1 share {d['mw']} ~= {expect_w1} (sequential law)")

    dx = direct[0]
    if dx["weight"] != 2000:
        fail(f"direct override weight {dx['weight']} != 2000 "
             f"(AOSP precedence: direct beats style bag)")
    if abs(dx["mw"] - 2 * d["mw"]) > 4:
        fail(f"weight-2 share {dx['mw']} != ~2x {d['mw']} (sequential law)")
    print("  PASS: direct layout_weight=2 beats style bag; share ~2x weight-1")

    if abs(dx["mh"] - (r["mh"] - 2 * margin)) > 2:
        fail(f"button height {dx['mh']} != row {r['mh']} - 2*margin "
             f"(match_height from bag)")
    print("  PASS: buttons fill row height minus bag margins")
    print("M3 style geometry: 6/6 PASS")


if __name__ == "__main__":
    main(sys.argv[1])
