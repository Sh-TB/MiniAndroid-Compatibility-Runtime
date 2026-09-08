#!/usr/bin/env python3
"""f020_pixel_golden.py — F-020 snapshot-law fixture visual oracle.

The fixture (miniandroid/tests/fixtures/f020_snapshot) renders FIVE 200px
verdict bands on a white 1080x1920 framebuffer:
    law1  y=200  AtomicReference ctor-value identity (dooz global-snapshot law)
    law2  y=500  AtomicInteger prefix/postfix arithmetic
    law3  y=800  Enum.compareTo ordinal sign (isAtLeast shape)
    law4  y=1100 AtomicBoolean compareAndSet value law
    law5  y=1400 Activity.getLayoutInflater() window-singleton law
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=0 and y=1500, x=540) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: f020_pixel_golden.py <screenshot.ppm>
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
    for i in range(5):
        y = 200 + i * 300
        r, g, b = px(540, y)
        if not (g > 120 and r < 100 and b < 120):
            failures.append(f"law{i+1} band y={y}: rgb({r},{g},{b}) NOT green")
        # second probe per band (left side) — band must be full-width
        r2, g2, b2 = px(200, y)
        if not (g2 > 120 and r2 < 100):
            failures.append(f"law{i+1} band left probe y={y}: rgb({r2},{g2},{b2}) NOT green")
    # white gutters: above the block (bands span y=100..1500) and below
    for (gx, gy) in [(540, 50), (540, 1550), (540, 1800)]:
        r, g, b = px(gx, gy)
        if (r, g, b) != (255, 255, 255):
            failures.append(f"gutter ({gx},{gy}): rgb({r},{g},{b}) NOT white")

    if failures:
        print("F-020 PIXEL GOLDEN: FAIL")
        for f_ in failures:
            print("  " + f_)
        return 1
    print("F-020 PIXEL GOLDEN: ALL 5 LAWS GREEN (snapshot-family laws verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
