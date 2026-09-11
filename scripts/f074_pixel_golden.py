#!/usr/bin/env python3
"""f074 pixel golden — 6-band visual verdict for the F-074/F-075 fixture.

The fixture (miniandroid/tests/fixtures/f074_super_run) renders SIX 180px
verdict bands on a white background. Each band is GREEN (0,160,0) when the
law holds and RED (208,0,0) when violated.

  L1  engine-level super-run walk     (F-074)
  L2  receiver identity preservation  (F-074)
  L3  two-hop superclass walk         (F-074)
  L4  most-derived override wins      (F-074/ART)
  L5  polymorphic zero vs object if-ne (F-075)
  L6  non-null identity round-trip    (F-070/F-073 protected)

Usage: f074_pixel_golden.py <screenshot.ppm>
"""
import sys

with open(sys.argv[1], 'rb') as f:
    data = f.read()

magic = data[:2]
if magic != b'P6':
    print('F074-GOLDEN: not a P6 PPM')
    sys.exit(1)

parts = data.split(b'\n', 3)
w, h = map(int, parts[1].split())
px = parts[3]

failures = []

for i, name in enumerate(('L1-super-run', 'L2-receiver-identity',
                          'L3-two-hop-walk', 'L4-override-wins',
                          'L5-poly-zero-if-ne', 'L6-identity-roundtrip')):
    top = 100 + i * 280 + 90  # middle of the band
    samples = []
    for x in (300, 500, 700):
        idx = (top * w + x) * 3
        samples.append((px[idx], px[idx + 1], px[idx + 2]))
    ok = all(g > 120 and r < 120 for (r, g, b) in samples)
    if not ok:
        failures.append(name)
    print(f'{name} band@y={top}: rgb={samples[0]} {"GREEN" if ok else "RED"}')

if failures:
    print(f'F074-GOLDEN: {len(failures)} FAILURES')
    sys.exit(1)
print('F074-GOLDEN: 6/6 BANDS GREEN')
