#!/usr/bin/env python3
"""scripts/verify/f030_pixel_golden.py — F-030 zero-is-null-at-reference-use law fixture
visual oracle.

The fixture (miniandroid/tests/fixtures/f030_zero_law) renders SEVEN
150px verdict bands on a white 1080x1920 framebuffer (top = 100 + i*250):
    L1 y=100  const/4 #0 as Object arg -> AtomicReferenceArray CAS(null)
              succeeds on a fresh cell (the dooz LY1/b;.D -> LY1/j;.j shape)
    L2 y=350  isNull(Object) called with literal null returns true
    L3 y=600  null returned through move-result-object stays null
    L4 y=850  int 0 in a PRIMITIVE param stays int 0 (law scope guard)
    L5 y=1100 F-028h identity preserved: boxed Integer(0) CAS on fresh
              cell FAILS, getAndSet(null) clears it (null != boxed 0)
    L6 y=1350 queue reserve/publish/consume pattern (LockFreeTaskQueueCore
              shape): CAS null->token, set(published), get==published
    L7 y=1600 null survives sput/sget + aput/aget storage round-trips
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, y=1870) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: scripts/verify/f030_pixel_golden.py <screenshot.ppm>
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
    print("F-030 ZERO LAW GOLDEN: 7/7 bands GREEN, gutters white — ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
