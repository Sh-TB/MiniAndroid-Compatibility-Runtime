#!/usr/bin/env python3
"""s100_browser_gif.py — build the canonical Mini Browser interactive GIF.

The browser (com.miniandroid.browser) loads a REAL website over HTTPS
through the runtime's new NET-001 stack (java.net.URL →
HttpURLConnection → OpenSSL TLS → BufferedReader → TextView render).
Evidence run: run/s100/browser_run5 (tap Go at frame 8):

  pre-tap  : "Mini Browser ready." hint + URL field + Go button
  frame 8  : TAP Go (dispatched, listener BrowserActivity$1)
  post-tap : "Loading https://example.com ..." (12,087 px measured state
             change by final frame vs pre-tap; HTTP 200, 559 bytes via
             real TLS — EXP091-SETTEXT + [STR] evidence in stderr.log)

Output: docs/evidence/canonical/com.miniandroid.browser.gif (400px wide,
GIF89a multi-frame, dwell-padded, deterministic palette).
"""
from PIL import Image
import os

ROOT = "/home/z/my-project"
SRC = f"{ROOT}/run/s100/browser_run5/frames"
OUT = f"{ROOT}/docs/evidence/canonical/com.miniandroid.browser.gif"
WIDTH = 400

SEQUENCE = [
    ("frame_000.png", 4),   # ready state (hint text, URL, Go)
    ("frame_004.png", 1),
    ("frame_007.png", 3),   # pre-tap
    ("frame_009.png", 1),   # TAP Go dispatched
    ("frame_011.png", 3),   # "Loading https://example.com ..." state
    ("frame_016.png", 1),
    ("frame_020.png", 1),
    ("frame_024.png", 1),
    ("frame_029.png", 5),   # final state: HTTP 200 (559 bytes) + page text
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
    pal_frames = [im.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
                  for im in out_frames]
    pal_frames[0].save(
        OUT, save_all=True, append_images=pal_frames[1:],
        duration=durations, loop=0, optimize=False, disposal=1)
    print("WROTE", OUT, os.path.getsize(OUT), "bytes,", len(pal_frames), "frames")


if __name__ == "__main__":
    main()
