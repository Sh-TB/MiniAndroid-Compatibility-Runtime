#!/usr/bin/env python3
"""f050_pixel_golden.py — F-050 Choreographer frame-pump law fixture
visual oracle.

The fixture (miniandroid/tests/fixtures/f050_frame_pump) renders SEVEN
150px verdict bands on a white 1080x1920 framebuffer (top = 100 + i*250):
    L1 y=100  getAndIncrement +1/OLD-return law (F-050c root: the
              prefix-match bug decremented; dooz sendersAndCloseStatus)
    L2 y=350  getAndDecrement/decrementAndGet/incrementAndGet epochs
    L3 y=600  Boolean.TRUE/FALSE non-null + value + identity (F-050d root)
    L4 y=850  Boolean identity storage round-trip
    L5 y=1100 Throwable message law getMessage() (F-050b)
    L6 y=1350 Choreographer.getInstance singleton identity (F-050a)
    L7 y=1600 the frame pump: postFrameCallback -> doFrame(J) fired with
              a monotonic frame time (the withFrameNanos resume path)
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, y=1870) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: f050_pixel_golden.py <screenshot.ppm>
"""
import sys


def rgb(px, w, x, y):
    i = (y * w + x) * 3
    return px[i], px[i + 1], px[i + 2]


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()
    # Plain PPM (P6) header: P6\n<w> <h>\n255\n
    parts = data.split(b"\n", 3)
    w, h = map(int, parts[1].split())
    px = parts[3]

    failures = 0
    for i in range(7):
        y = 160 + i * 250  # band center
        x = 540
        r, g, b = rgb(px, w, x, y)
        ok = g > 120 and r < 100
        print(f"L{i+1} band@y={y}: rgb=({r},{g},{b}) {'GREEN' if ok else 'RED'}")
        if not ok:
            failures += 1
    for y in (50, 1800, 1870):
        r, g, b = rgb(px, w, 540, y)
        white = r > 240 and g > 240 and b > 240
        if not white:
            print(f"gutter y={y} not white: ({r},{g},{b})")
            failures += 1

    if failures:
        print(f"F050-GOLDEN: {failures} FAILURES")
        return 1
    print("F050-GOLDEN: ALL PASS (7 bands + gutters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
