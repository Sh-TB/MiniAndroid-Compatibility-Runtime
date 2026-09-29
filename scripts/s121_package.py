#!/usr/bin/env python3
"""s121_package.py — small English-only evidence PNGs for the S121 wave."""
import os
from PIL import Image

R = "/home/z/my-project"
OUT = f"{R}/evidence/s121_full_sessions"
os.makedirs(OUT, exist_ok=True)

PICKS = [
    # TriPeaks: deal + the full-loop HUD ledger (draw/capture/streak/draw)
    ("tripeaks1_deal.jpg", f"{R}/run/s120_new_games/tripeaks_game3/frames/frame_040.png", 800),
    ("tripeaks2_full_session_hud.jpg", f"{R}/run/s121_tripeaks/fullloop/hud_sheet.png", 900),
    # gmdice: 3D20 rendered three dice values
    ("gmdice_3d20_three_dice.jpg", f"{R}/run/s121_gmdice/frames/frame_040.png", 800),
    # bouncy: menu (start-game root cause: Box2D .so frontier — textual report)
    ("bouncy_menu.jpg", f"{R}/run/s120_new_games/bouncy/frames/frame_029.png", 800),
    # opmt: live board — white piece selected (blue ring), law-fixed layout
    ("opmt_board_selection.jpg", f"{R}/run/s121_opmt/game_fixed_render/frames/frame_095.png", 800),
    # fishrings: after two agent taps (ring rotated vs S120 board)
    ("fishrings_after_two_taps.jpg", f"{R}/run/s121_fishrings/rot1/frames/frame_064.png", 800),
    # dooz-compose: honest FAIL evidence (blank, Compose unwind chain in report)
    ("dooz_compose_blank_fail.jpg", f"{R}/run/s120_new_games/dooz_compose/frames/frame_029.png", 300),
]

for name, src, maxh in PICKS:
    if not os.path.exists(src):
        print("MISSING", src)
        continue
    img = Image.open(src).convert("RGB")
    w, h = img.size
    tw = 460
    th = int(h * tw / w)
    if th > maxh:                       # tall sheets: cap the height instead
        th = maxh
        tw = int(w * th / h)
    img = img.resize((tw, th), Image.LANCZOS)
    dst = f"{OUT}/{name}"
    img.save(dst, quality=82, optimize=True)
    kb = os.path.getsize(dst) // 1024
    print(f"{name}: {img.size[0]}x{img.size[1]} {kb}KB")
