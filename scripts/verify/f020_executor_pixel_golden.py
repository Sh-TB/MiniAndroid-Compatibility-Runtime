#!/usr/bin/env python3
"""scripts/verify/f020_executor_pixel_golden.py — §4 Executor fixture visual oracle.

The fixture (miniandroid/tests/fixtures/f020_executor) renders FOUR 200px
verdict bands on a white 1080x1920 framebuffer (top = 100 + i*300):
    law1 y=200  Executors.newFixedThreadPool product identity (non-null)
    law2 y=500  all 3 submitted tasks ran exactly once (count == 3 —
                catches the double-run defect class: 6 or 9 executions)
    law3 y=800  FIFO submit-order law (1+2+4 = 7 at the drain point)
    law4 y=1100 run() executed at the drain point (after onCreate)
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1300, x=540) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: scripts/verify/f020_executor_pixel_golden.py <screenshot.ppm>
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
    for i in range(4):
        y = 200 + i * 300
        r, g, b = px(540, y)
        if not (g > 120 and r < 100 and b < 120):
            failures.append(f"law{i+1} band y={y}: rgb({r},{g},{b}) NOT green")
        r2, g2, b2 = px(200, y)
        if not (g2 > 120 and r2 < 100):
            failures.append(f"law{i+1} band left probe y={y}: rgb({r2},{g2},{b2}) NOT green")
    for (gx, gy) in [(540, 50), (540, 1350), (540, 1800)]:
        r, g, b = px(gx, gy)
        if (r, g, b) != (255, 255, 255):
            failures.append(f"gutter ({gx},{gy}): rgb({r},{g},{b}) NOT white")

    if failures:
        print("EXECUTOR PIXEL GOLDEN: FAIL")
        for f_ in failures:
            print("  " + f_)
        return 1
    print("EXECUTOR PIXEL GOLDEN: ALL 4 LAWS GREEN (submit/queue/drain/FIFO verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
