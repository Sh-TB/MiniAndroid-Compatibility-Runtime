#!/usr/bin/env python3
"""f026_pixel_golden.py — F-026 Room/SQLite persistence-law visual oracle.

The fixture (miniandroid/tests/fixtures/f026_room_sql_law) renders SEVEN
150px verdict bands on a white 1080x1920 framebuffer (top = 100 + i*250):
    L1 y=100  INSERT×3 + SELECT ORDER BY id → A,B,C (deterministic order)
    L2 y=350  UPDATE affected + persisted qty==11
    L3 y=600  DELETE → count==2
    L4 y=850  txn commit → count==4
    L5 y=1100 txn rollback (no setSuccessful) → count stays 4
    L6 y=1350 cursor typed reads + isNull NULL/non-NULL + 4-row walk
    L7 y=1600 reopen (close + fresh helper) → 4 rows, updated qty survives
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, x=540) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: f026_pixel_golden.py <screenshot.ppm>
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
        y = 100 + i * 250 + 75
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
        print("F-026 PIXEL GOLDEN: FAIL")
        for f_ in failures:
            print("  " + f_)
        return 1
    print("F-026 PIXEL GOLDEN: ALL 7 LAWS GREEN (SQLite/Cursor/txn family verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
