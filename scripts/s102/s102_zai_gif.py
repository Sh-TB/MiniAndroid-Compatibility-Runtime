#!/usr/bin/env python3
"""s102_zai_gif.py — build the canonical Mini Browser z.ai interactive GIF.

Owner mandate (S102): "see if you can load the browser and open the
z.ai website — if you can, put its GIF on the front page next to the 4
important games."

Evidence run: /tmp/zai_run2 (tap Go, 8 frames):

  frame 0     : "Mini Browser ready." hint + URL field pre-filled z.ai
  frame 1     : TAP Go dispatched (CLICK-TEST probed=1)
  frames 2-3  : "Loading https://z.ai ..." state
  frames 4-7  : "HTTP 200 (15727 bytes)" — REAL TLS page text of
                https://chat.z.ai/ rendered (redirect z.ai 307 →
                chat.z.ai 200 followed through the S102 HEADER-OWS-TRIM
                law; measured state change vs pre-tap frame)

Output: docs/evidence/canonical/com.miniandroid.browser.zai.gif
        (400px wide, GIF89a multi-frame, dwell-padded).
"""
from PIL import Image
import os
import hashlib

ROOT = "/home/z/my-project"
SRC = "/tmp/zai_run2/frames"
OUT = f"{ROOT}/docs/evidence/canonical/com.miniandroid.browser.zai.gif"
WIDTH = 400

SEQUENCE = [
    ("frame_000.png", 5),  # ready state (z.ai pre-filled)
    ("frame_001.png", 1),  # TAP Go
    ("frame_002.png", 2),  # "Loading https://z.ai ..."
    ("frame_003.png", 2),
    ("frame_004.png", 1),
    ("frame_005.png", 2),  # HTTP 200 (15727 bytes) page text
    ("frame_006.png", 1),
    ("frame_007.png", 6),  # final: chat.z.ai content rendered
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

    pal_frames = []
    for im, dwell in frames:
        p = im.convert("P", palette=Image.ADAPTIVE, colors=64)
        pal_frames.append((p, dwell))
    pal_frames[0][0].save(
        OUT, save_all=True, append_images=[f for f, _ in pal_frames[1:]],
        duration=[d * 180 for _, d in pal_frames], loop=0, optimize=False)

    h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"GIF: {OUT}")
    print(f"SHA256: {h}")
    print(f"frames: {len(pal_frames)} size: {pal_frames[0][0].size}")


if __name__ == "__main__":
    main()
