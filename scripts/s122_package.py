#!/usr/bin/env python3
"""s122_package.py — package the S122 harder-games evidence (460px smalls).

Sources (best frames, honest labels):
  chess      : full load, 0 errors, toolbar painted, content render pending
               the adapter->relayout traversal (documented frontier).
  klondike   : menu -> New Game click -> GameActivity -> deck tap -> deal.
"""
import os

from PIL import Image

R = "/home/z/my-project"
OUT = f"{R}/evidence/s122_harder_games"
os.makedirs(OUT, exist_ok=True)

JOBS = [
    # (source frame, output name)
    (f"{R}/run/s122_harder/chess/frames/frame_059.png",
     "chess_full_load_0err_toolbar.jpg"),
    (f"{R}/run/s122_harder/klondike/frames/frame_059.png",
     "klondike1_menu_rendered.jpg"),
    (f"{R}/run/s122_klondike_session/new_game2/frames/frame_119.png",
     "klondike2_new_game_table_deck.jpg"),
    (f"{R}/run/s122_klondike_session/deal3/frames/frame_149.png",
     "klondike3_after_deck_tap_aces_up.jpg"),
]

for src, name in JOBS:
    img = Image.open(src).convert("RGB")
    img.thumbnail((460, 820))
    dst = f"{OUT}/{name}"
    img.save(dst, quality=70)
    kb = os.path.getsize(dst) // 1024
    print(f"{name}: {img.size[0]}x{img.size[1]} {kb}KB")
