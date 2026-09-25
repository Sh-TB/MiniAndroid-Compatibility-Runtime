#!/usr/bin/env python3
"""s99_fish_gif.py — build the canonical Fish Rings interactive GIF.

User finding (S99): the README Fish Rings demo embedded a static JPG, not a
GIF — the only demo without real-motion evidence. This script assembles the
canonical multi-frame GIF from the measured tap-sequence run
(run/s99/fish_gif/fish_tapseq, 3 real taps at frames 30/40/50):

  splash -> timer transition (2,073,600 px) -> empty board -> TAP board
  appears (4,304 px) -> TAP ring rotation (4,320 px) -> TAP (4,308 px)

Output: docs/evidence/canonical/eu.veldsoft.fish.rings.gif (400px wide,
GIF89a multi-frame, dwell-padded so every state is readable).
"""
from PIL import Image
import os

ROOT = "/home/z/my-project"
SRC = f"{ROOT}/run/s99/fish_gif/fish_tapseq/frames"
OUT = f"{ROOT}/docs/evidence/canonical/eu.veldsoft.fish.rings.gif"
WIDTH = 400

# (frame file, dwell ticks) — dwell = ~500ms per tick at the recorded cadence
SEQUENCE = [
    ("frame_000.png", 3),   # splash
    ("frame_005.png", 1),
    ("frame_010.png", 1),
    ("frame_015.png", 1),   # still splash (timer pending)
    ("frame_017.png", 1),   # transition begins
    ("frame_021.png", 4),   # GameActivity, empty board (post-transition)
    ("frame_025.png", 1),
    ("frame_029.png", 1),   # pre-tap
    ("frame_031.png", 4),   # TAP 1: board painted (4,304 px)
    ("frame_035.png", 1),
    ("frame_039.png", 1),   # pre-tap
    ("frame_041.png", 4),   # TAP 2: ring rotation (4,320 px)
    ("frame_045.png", 1),
    ("frame_049.png", 1),   # pre-tap
    ("frame_051.png", 4),   # TAP 3: ring rotation (4,308 px)
    ("frame_056.png", 2),
    ("frame_059.png", 3),   # final state
]


def main():
    frames = []
    for name, dwell in SEQUENCE:
        p = os.path.join(SRC, name)
        im = Image.open(p).convert("RGB")
        w, h = im.size
        nh = int(h * WIDTH / w)
        im = im.resize((WIDTH, nh), Image.LANCZOS)
        frames.append((im, dwell))
    h0 = frames[0][0].size[1]
    frames = [(im.crop((0, 0, WIDTH, min(im.size[1], h0))), d) for im, d in frames]

    out_frames = []
    durations = []
    for im, dwell in frames:
        for t in range(dwell):
            out_frames.append(im)
            durations.append(500 if t == 0 else 120)
    # per-frame adaptive palette (GIF89a local palettes, dither off = deterministic)
    pal_frames = [im.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
                  for im in out_frames]
    pal_frames[0].save(
        OUT, save_all=True, append_images=pal_frames[1:],
        duration=durations, loop=0, optimize=False, disposal=1)
    print("WROTE", OUT, os.path.getsize(OUT), "bytes,", len(pal_frames), "frames")


if __name__ == "__main__":
    main()
