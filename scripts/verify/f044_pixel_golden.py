#!/usr/bin/env python3
"""scripts/verify/f044_pixel_golden.py — F-044 per-frame return-descriptor law fixture
visual oracle.

The fixture (miniandroid/tests/fixtures/f044_return_descriptor_law) renders
SEVEN 150px verdict bands on a white 1080x1920 framebuffer (top=100+i*250):
    L1 y=100   int return after a boolean callee: versionHash() returns
               6729 (the dooz DerivedSnapshotState hash), not bool-1
    L2 y=350   int return after an Object callee: 6729 preserved
    L3 y=600   int return after a void callee: -5 preserved (all 32 bits)
    L4 y=850   boolean return after an int callee: boolean semantics intact
    L5 y=1100  dooz nested .c -> .d -> contains() shape: outer I-method
               still returns its own 6729 after Z and I callees
    L6 y=1350  dependency-change detection: scanned version 6729 -> 6731
               when the record id moves 2 -> 4 (pre-F-044 both collapsed
               to boolean 1 — a dependency write was permanently invisible)
    L7 y=1600  Object return after a boolean callee: reference identity
               preserved (== token, non-null)
GREEN band (g>120, r<100) = law holds; RED = violated; anything else at a
band center = render defect. Gutters (y=50, y=1800, y=1870) must be white.

Exit 0 iff every band is green and every gutter is white.

Usage: scripts/verify/f044_pixel_golden.py <screenshot.ppm>
"""
import sys


def read_ppm(path):
    with open(path, "rb") as f:
        data = f.read()
    # P6 header: magic, width height, maxval — whitespace separated.
    parts = data.split(b"\n", 3)
    magic = parts[0].strip()
    if magic != b"P6":
        raise SystemExit(f"not a P6 ppm: {magic!r}")
    dims = parts[1].split()
    w, h = int(dims[0]), int(dims[1])
    maxval = int(parts[2].split()[0])
    pix = parts[3]
    return w, h, maxval, pix


def pixel(pix, w, x, y):
    o = (y * w + x) * 3
    return pix[o], pix[o + 1], pix[o + 2]


def classify(rgb):
    r, g, b = rgb
    if g > 120 and r < 100:
        return "GREEN"
    if r > 150 and g < 100:
        return "RED"
    return "OTHER"


def main() -> int:
    ppm_path = sys.argv[1]
    w, h, maxval, pix = read_ppm(ppm_path)
    if (w, h) != (1080, 1920):
        print(f"FAIL: unexpected framebuffer {w}x{h}")
        return 1

    bands = [(100, "L1 int-after-bool"), (350, "L2 int-after-object"),
             (600, "L3 int-after-void neg"), (850, "L4 bool-after-int"),
             (1100, "L5 dooz nested shape"), (1350, "L6 version-change law"),
             (1600, "L7 object-after-bool")]
    ok = True
    for top, name in bands:
        cy = top + 75
        rgb = pixel(pix, w, 540, cy)
        verdict = classify(rgb)
        print(f"{name:28s} center={rgb} -> {verdict}")
        if verdict != "GREEN":
            ok = False

    gutters = [(540, 50), (540, 1800), (540, 1870)]
    for x, y in gutters:
        rgb = pixel(pix, w, x, y)
        if classify(rgb) != "OTHER" or rgb != (255, 255, 255):
            # gutters must be pure white
            print(f"gutter ({x},{y}) = {rgb} (expected white)")
            ok = ok and rgb == (255, 255, 255)

    print("F044 GOLDEN:", "ALL GREEN (7/7)" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
