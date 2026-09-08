#!/usr/bin/env python3
"""f024_pixel_golden.py — F-024 InputStream EOF-law fixture visual oracle.

The fixture (miniandroid/tests/fixtures/f024_eof_law) renders SEVEN 150px
verdict bands on a white 1080x1920 framebuffer (top = 100 + i*250):
    L1 y=100  empty stream: first read() == -1
    L2 y=350  single-byte stream: 0x41 then -1
    L3 y=600  0xFF is DATA (255, unsigned law)
    L4 y=850  EOF is sticky (3 further reads == -1)
    L5 y=1100 bulk read: count 11, bytes land, then -1
    L6 y=1350 drain loop terminates with count == 11
    L7 y=1600 available() 11→0; read-after-close sees EOF
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, x=540) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: f024_pixel_golden.py <screenshot.ppm>
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
        if (r, g, b) != (255, 255, 255):
            failures.append(f"gutter ({gx},{gy}): rgb({r},{g},{b}) NOT white")

    if failures:
        print("F-024 PIXEL GOLDEN: FAIL")
        for f_ in failures:
            print("  " + f_)
        return 1
    print("F-024 PIXEL GOLDEN: ALL 7 LAWS GREEN (InputStream EOF family verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
