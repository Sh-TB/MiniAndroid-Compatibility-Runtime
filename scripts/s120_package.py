#!/usr/bin/env python3
"""s120_package.py — small English-only evidence PNGs for the S120 new-games wave."""
import os
from PIL import Image

R = "/home/z/my-project"
OUT = f"{R}/evidence/s120_new_games"
os.makedirs(OUT, exist_ok=True)

PICKS = [
    ("tripeaks1_new_game_deal.png", f"{R}/run/s120_new_games/tripeaks_game3/frames/frame_059.png"),
    ("tripeaks2_agent_move_state_change.png", f"{R}/run/s120_new_games/tripeaks_move1/frames/frame_059.png"),
    ("gmdice_agent_roll_result6.png", f"{R}/run/s120_new_games/gmdice_roll/frames/frame_029.png"),
    ("opmt_full_menu.png", f"{R}/run/s120_new_games/opmt/frames/frame_029.png"),
    ("fishrings_puzzle_board.png", f"{R}/run/s120_new_games/fishrings/frames/frame_029.png"),
    ("bouncy_menu.png", f"{R}/run/s120_new_games/bouncy/frames/frame_029.png"),
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
