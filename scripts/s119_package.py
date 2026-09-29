#!/usr/bin/env python3
"""s119_package.py — small English-only evidence PNGs for the S119 games wave."""
import os
from PIL import Image

R = "/home/z/my-project"
OUT = f"{R}/evidence/s119_games"
os.makedirs(OUT, exist_ok=True)

PICKS = [
    ("ttt1_opening_x_o.png",   f"{R}/run/s83_ttt_autoplay/leg00/frames/frame_007.png"),
    ("ttt2_win_and_dialog.png", f"{R}/run/s83_ttt_autoplay/leg04/frames/frame_015.png"),
    ("ttt3_round2_score_kept.png", f"{R}/run/s83_ttt_autoplay/final/frames/frame_027.png"),
    ("g2048_real_score84.png", f"{R}/run/s80_2048_autoplay/cycle_30/frames/frame_075.png"),
    ("snake_real_score2.png",  f"{R}/run/s80_sd_autoplay/final_run/frames/frame_020.png"),
    ("tetris_stack_7locks.png", f"{R}/run/s80_tet_autoplay/cycle_04/frames/frame_202.png"),
    ("minicraft_cottage.png",  f"{R}/run/s98_minicraft_autoplay/build_run/frames/frame_049.png"),
    ("snakeneon_capture.png",  f"{R}/run/s98_snakeneon_autoplay/final/frames/frame_124.png"),
]

for name, src in PICKS:
    if not os.path.exists(src):
        print("MISSING", src)
        continue
    img = Image.open(src).convert("RGB")
    w, h = img.size
    tw = 460
    img = img.resize((tw, int(h * tw / w)), Image.LANCZOS)
    dst = f"{OUT}/{name}"
    img.save(dst, optimize=True)
    kb = os.path.getsize(dst) // 1024
    print(f"{name}: {tw}x{img.size[1]} {kb}KB")
