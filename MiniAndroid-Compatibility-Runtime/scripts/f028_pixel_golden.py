#!/usr/bin/env python3
"""f028_pixel_golden.py — F-028 untyped-register conversion-law fixture
visual oracle.

The fixture (miniandroid/tests/fixtures/f028_float_law) renders SEVEN
150px verdict bands on a white 1080x1920 framebuffer (top = 100 + i*250):
    L1 y=100  const/high16 float bits -> float-to-int == 115 (dooz pattern)
    L2 y=350  int-to-float of real int == 180.0f
    L3 y=600  dooz arithmetic chain 200/100.0f-0.02f > 1.0f
    L4 y=850  round-toward-zero: -2.5f->-2, 0.9f->0, 1.9f->1
    L5 y=1100 NaN->0 and f2i saturation to MAX_VALUE
    L6 y=1350 float identity via static/virtual/interface-default calls
    L7 y=1600 float bits preserved through sput/sget + aput/aget
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, x=1870? left/right)
must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: f028_pixel_golden.py <screenshot.ppm>
"""
import sys


def main() -> int:
    ppm_path = sys.argv[1]
    with open(ppm_path, "rb") as f:
        raw = f.read()
    parts = raw.split(b"\n", 3)
    w, h = map(int, parts[1].split())
    data = parts[3]

    def px(x: int, y: int):
        i = (y * w + x) * 3
        return (data[i], data[i + 1], data[i + 2])

    failures = []
    for i in range(7):
        y = 100 + i * 250 + 75  # band vertical center
        r, g, b = px(540, y)
        if not (g > 120 and r < 100 and b < 120):
            failures.append(f"L{i+1} band y={y}: rgb({r},{g},{b}) NOT green")
        r2, g2, b2 = px(200, y)
        if not (g2 > 120 and r2 < 100):
            failures.append(f"L{i+1} band left probe y={y}: rgb({r2},{g2},{b2}) NOT green")
    for (gx, gy) in [(540, 50), (540, 1800), (540, 1870)]:
        r, g, b = px(gx, gy)
        if not (r > 230 and g > 230 and b > 230):
            failures.append(f"gutter ({gx},{gy}): rgb({r},{g},{b}) NOT white")

    if failures:
        for msg in failures:
            print("FAIL:", msg)
        return 1
    print("F-028 FLOAT LAW GOLDEN: 7/7 bands GREEN, gutters white — ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
