#!/usr/bin/env python3
"""S53 screenshot quality gate + JPG emit.

Policy (S53 law 1):
- near-white >= 97% or near-black >= 97%  -> BLANK (do not store)
- colors <= 8                              -> BLANK (renderer artifact class)
- otherwise                                -> meaningful candidate; store as JPG <= 100 KB
Deterministic output names: <app>_<phase>.jpg (phase = base | after)
SHA256SUMS + quality report written alongside.
"""
import hashlib
import os
import sys
from PIL import Image, ImageChops

OUT_DIR = "/home/z/my-project/docs/evidence/s53_frames"
MAX_BYTES = 100 * 1024

# (app, phase, src_png) — only frames that passed the visual + state-change audit
FRAMES = [
    ("gmdice", "base", "/tmp/s53_gmdice_click/screenshot.png"),
    ("gmdice", "after", "/tmp/s53_gmdice_click/click_frame_2.png"),
    ("microtimer", "base", "/tmp/s53_mt_click/screenshot.png"),
    ("microtimer", "after", "/tmp/s53_mt_click/click_frame_1.png"),
    ("simplestopwatch", "base", "/tmp/s53_simplestopwatch_click/screenshot.png"),
    ("simplestopwatch", "after", "/tmp/s53_simplestopwatch_click/click_frame_1.png"),
    ("headingcalculator", "base", "/tmp/s53_headingcalculator_click/screenshot.png"),
    ("headingcalculator", "after", "/tmp/s53_headingcalculator_click/click_frame_9.png"),
    ("unote", "base", "/tmp/s53_unote_click/screenshot.png"),
]

REJECTED = [
    ("chessclock", "base", "/tmp/s53_chessclock/screenshot.png",
     "BLANK dark class: 99.3% near-black, 2 colors, 0/8 click state changes"),
    ("notes", "base", "/tmp/s53_notes_click/screenshot.png",
     "BLANK near-white class: 99.1% near-white, 5 colors, 0/3 click state changes"),
]


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
                colors=ncolors, verdict=verdict)


def emit_jpg(src, dst):
    im = Image.open(src).convert("RGB")
    q = 88
    im.save(dst, "JPEG", quality=q, optimize=True)
    while os.path.getsize(dst) > MAX_BYTES and q >= 40:
        q -= 8
        im.save(dst, "JPEG", quality=q, optimize=True)
    return q


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    lines = ["# S53 frame quality gate + SHA256\n"]
    kept = 0
    for app, phase, src in FRAMES:
        if not os.path.exists(src):
            print(f"MISSING {src}", file=sys.stderr)
            continue
        g = gate(src)
        if g["verdict"] != "MEANINGFUL":
            print(f"REJECT {app}/{phase}: {g}")
            continue
        dst = os.path.join(OUT_DIR, f"{app}_{phase}.jpg")
        q = emit_jpg(src, dst)
        sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
        size = os.path.getsize(dst)
        kept += 1
        lines.append(f"{sha}  {app}_{phase}.jpg  {size}B  q{q}  "
                     f"nearWhite={g['near_white']}% nearBlack={g['near_black']}% colors={g['colors']}")
        print(f"KEEP {app}_{phase}.jpg {size}B q{q} {g}")
    print("\n-- rejected (blank class, recorded as text only) --")
    for app, phase, src, why in REJECTED:
        if os.path.exists(src):
            g = gate(src)
            lines.append(f"REJECTED {app}_{phase}: {why} [gate: {g}]")
            print(f"REJECT {app}: {why} [gate: {g}]")
    with open(os.path.join(OUT_DIR, "SHA256SUMS"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nkept={kept}")


if __name__ == "__main__":
    main()
