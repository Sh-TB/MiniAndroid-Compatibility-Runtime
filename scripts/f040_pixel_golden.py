#!/usr/bin/env python3
"""f040_pixel_golden.py — F-040 java.util.Arrays.fill family law fixture
visual oracle.

The fixture (miniandroid/tests/fixtures/f040_arrays_fill) renders SEVEN
150px verdict bands on a white 1080x1920 framebuffer (top = 100 + i*250):
    L1 y=100   dooz metadata init: fill(long[], 0, len, 0x8080...80) —
               every window equals the ScatterMap EMPTY marker
    L2 y=350   range fill + OpenJDK rangeCheck (IAE from>to, AIOOBE to>len)
    L3 y=600   int[] whole (2-arg) + range (4-arg) fills
    L4 y=850   Object[] null fill reads null; token fill preserves
               reference identity at every slot
    L5 y=1100  byte/short/char/boolean fill family
    L6 y=1350  float/double fill; double bits round-trip exactly
               (0x4018000000000000 == raw bits of 6.0)
    L7 y=1600  probe-readback simulation: all 64 control bytes 0x80 after
               EMPTY fill; tag write at slot 5 reads 0x3F with slot 0
               still 0x80 (the law whose absence made Lh/u;.a spin)
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, y=1870) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: f040_pixel_golden.py <screenshot.ppm>
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
    print("F-040 ARRAYS FILL LAW GOLDEN: 7/7 bands GREEN, gutters white — ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
