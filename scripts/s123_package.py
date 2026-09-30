#!/usr/bin/env python3
"""S123 evidence packaging: 460px JPGs, English-only, size-bounded 26-66KB."""
import os
from PIL import Image

OUT = "/home/z/my-project/evidence/s123_themed_apps"
os.makedirs(OUT, exist_ok=True)

JOBS = [
    # (src, dst)
    ("/tmp/s123_fc_r1/frames/frame_000.png", "flappycow1_start_screen_full.jpg"),
    ("/tmp/s123_fc_r1/frames/frame_001.png", "flappycow2_game_activity_after_play_tap.jpg"),
    ("/tmp/s123_calc_r1/frames/frame_000.png", "calc1_themed_keypad_initial.jpg"),
    ("/tmp/s123_calc_r1/frames/frame_002.png", "calc2_display_after_keypad_input.jpg"),
    ("/tmp/s123_tg1/frames/frame_002.png", "telegram1_launch_activity_frame.jpg"),
    ("/tmp/s123_wa1/frames/frame_001.png", "whatsapp1_main_launch_frame.jpg"),
]

def pack(src, dst):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    nw = 460
    nh = max(1, round(h * nw / w))
    im = im.resize((nw, nh), Image.LANCZOS)
    q = 88
    while q >= 40:
        im.save(f"{OUT}/{dst}", "JPEG", quality=q, optimize=True)
        sz = os.path.getsize(f"{OUT}/{dst}")
        if sz <= 66 * 1024:
            break
        q -= 6
    sz = os.path.getsize(f"{OUT}/{dst}")
    lo = 26 * 1024
    if sz < lo and q > 40:
        # bump quality up to reach the floor honestly (detail-rich frames)
        im.save(f"{OUT}/{dst}", "JPEG", quality=95, optimize=True)
        sz = os.path.getsize(f"{OUT}/{dst}")
    print(f"{dst}: {sz} bytes ({nw}x{nh}) q~{q}")

for src, dst in JOBS:
    if os.path.exists(src):
        pack(src, dst)
    else:
        print(f"MISSING: {src}")
print("done")
