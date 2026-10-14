#!/usr/bin/env python3
"""cont64_verify_f352.py — the F-NEW-352 tint-law pixel verifier.

Reads the probe screenshot and asserts each patch's expected color.
Rows (patch 120x120; x=80 left, x=300 right; y per row):
  R1 T1 SRC_IN red/white->RED        T2 SRC_IN over transparent->BACKGROUND
  R2 T3 SRC_ATOP green/half-alpha    T4 MULTIPLY red x BLUE->black rgb
  R3 T5 no-filter control UNCHANGED  T6 BlendModeColorFilter SRC_IN green
  R4 T7 per-paint state red | blue   T8 getColorFilter round-trip GREEN
"""
import sys
from PIL import Image

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/run/cont64/f352_det/screenshot.png"

BG = (24, 24, 28)
ROWS = [
    # (label, x, y, expected_rgb, tolerance)
    ("T1 SRC_IN red over white",        140, 140, (255, 0, 0),   12),
    ("T2 SRC_IN over transparent",      360, 140, BG,            12),
    ("T3 SRC_ATOP opaque half",         140, 290, (0, 255, 0),   12),
    ("T4 MULTIPLY red x blue",          360, 290, (0, 0, 0),     24),
    ("T5 no-filter control",            140, 440, (0, 68, 136),  12),
    ("T6 BlendModeColorFilter green",   360, 440, (0, 204, 68),  12),
    ("T7a per-paint red",               140, 590, (255, 0, 0),   12),
    ("T7b per-paint blue",              360, 590, (0, 0, 255),   12),
    ("T8 round-trip green",             140, 740, (17, 170, 102), 12),
]

im = Image.open(PATH).convert("RGB")
passed = failed = 0
for label, x, y, want, tol in ROWS:
    # majority color in a 40x40 window at the patch center (anti-alias safe)
    from collections import Counter
    c = Counter()
    for yy in range(y - 20, y + 20):
        for xx in range(x - 20, x + 20):
            c[im.getpixel((xx, yy))] += 1
    got = c.most_common(1)[0][0]
    ok = all(abs(a - b) <= tol for a, b in zip(got, want))
    print(f"{'PASS' if ok else 'FAIL'} {label}: got={got} want={want}")
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
print(f"== {passed}/{passed + failed} pixel rows")
sys.exit(0 if failed == 0 else 1)
