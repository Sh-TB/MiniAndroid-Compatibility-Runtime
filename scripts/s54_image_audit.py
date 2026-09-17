#!/usr/bin/env python3
"""S54 generic image audit — same gate law as S53 (scripts/s53_frame_gate.py).

Gate law (S53 law 1, unchanged):
- near-white >= 97% or near-black >= 97%  -> BLANK (do not store as evidence)
- colors <= 8                              -> BLANK (renderer artifact class)
- otherwise                                -> MEANINGFUL candidate

Usage: python3 scripts/s54_image_audit.py <image> [<image>...]
Prints one CSV-ish line per image: verdict,near_white,near_black,colors,sha256,path
"""
import hashlib
import sys

from PIL import Image


def gate(path):
    im = Image.open(path)
    g = im.convert("L")
    h = g.histogram()
    total = im.size[0] * im.size[1]
    near_white = sum(h[245:]) / total * 100
    near_black = sum(h[:12]) / total * 100
    rgb = im.convert("RGB")
    colors = rgb.getcolors(maxcolors=1 << 24)
    ncolors = len(colors) if colors else -1
    verdict = "MEANINGFUL"
    if near_white >= 97 or near_black >= 97 or 0 < ncolors <= 8:
        verdict = "BLANK"
    return dict(near_white=round(near_white, 1), near_black=round(near_black, 1),
                colors=ncolors, verdict=verdict, size=im.size)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for p in sys.argv[1:]:
        try:
            m = gate(p)
            sha = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
            print(f"{m['verdict']}\t{m['near_white']}\t{m['near_black']}\t"
                  f"{m['colors']}\t{m['size'][0]}x{m['size'][1]}\t{sha}\t{p}")
        except Exception as e:  # noqa: BLE001
            print(f"ERROR\t{e}\t{p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
