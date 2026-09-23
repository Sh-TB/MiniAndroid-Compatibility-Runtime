#!/usr/bin/env python3
"""s83_evidence_package.py — package the S83 campaign evidence.

Law: JPG ≤100KB (S38 image law), SHA256SUMS manifest, honest naming
(<apk>__L<level>_<levelname>.jpg). Gameplay stage captures included for
TicTacToe Deluxe + Snake Deluxe (the user-mandated TicTacToe/Snake completion).
"""
import glob
import hashlib
import json
import os
import shutil

from PIL import Image

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/docs/evidence/s83"
os.makedirs(OUT, exist_ok=True)
campaign = json.load(open(f"{ROOT}/run/s83_campaign/report.json"))


def to_jpg(src_png, dst_jpg, max_side=540, q=72):
    img = Image.open(src_png).convert("RGB")
    w, h = img.size
    scale = max_side / max(w, h)
    if scale < 1:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img.save(dst_jpg, "JPEG", quality=q)
    # enforce ≤100KB: degrade quality if needed
    while os.path.getsize(dst_jpg) > 100 * 1024 and q > 30:
        q -= 6
        img.save(dst_jpg, "JPEG", quality=q)
    return os.path.getsize(dst_jpg)


manifest = []
count = 0

for group in ("games", "apps", "high"):
    for item in campaign["results"][group]:
        if not item.get("final_frame"):
            continue
        v = item.get("visual", {})
        tag = item["apk"].replace(".apk", "")[:44]
        dst = f"{OUT}/{group}__{tag}__L{v.get('LEVEL','-')}_{v.get('LEVEL_NAME','NOFRAME')}.jpg"
        try:
            sz = to_jpg(item["final_frame"], dst)
            manifest.append((os.path.basename(dst), sz))
            count += 1
        except Exception as e:
            print("SKIP", tag, e)

# gameplay stage captures — TicTacToe Deluxe
tt_stages = [
    ("run/s83_ttt_autoplay/leg00/frames/frame_007.png",
     "gameplay__tictactoe_deluxe__stage1_X_center.jpg"),
    ("run/s83_ttt_autoplay/leg02/frames/frame_011.png",
     "gameplay__tictactoe_deluxe__stage2_midgame.jpg"),
    ("run/s83_ttt_autoplay/leg04/frames/frame_015.png",
     "gameplay__tictactoe_deluxe__stage3_O_win_strike.jpg"),
    ("run/s83_ttt_autoplay/leg05/frames/frame_017.png",
     "gameplay__tictactoe_deluxe__stage4_roundover_dialog.jpg"),
    ("run/s83_ttt_autoplay/final/frames/frame_027.png",
     "gameplay__tictactoe_deluxe__stage5_round2_fresh_board.jpg"),
]
# snake lifecycle
sn_stages = [
    ("run/s83_snake_proof/frames/frame_003.png",
     "gameplay__snake_deluxe__stage1_board_ready.jpg"),
    ("run/s83_snake_proof/frames/frame_010.png",
     "gameplay__snake_deluxe__stage2_snake_chasing_apple.jpg"),
    ("run/s83_snake_proof/frames/frame_022.png",
     "gameplay__snake_deluxe__stage3_late_game.jpg"),
    ("run/s83_snake_proof/frames/frame_025.png",
     "gameplay__snake_deluxe__stage4_gameover_dialog.jpg"),
]
for src, name in tt_stages + sn_stages:
    if os.path.exists(src):
        sz = to_jpg(src, f"{OUT}/{name}")
        manifest.append((name, sz))
        count += 1
    else:
        print("MISSING stage", src)

with open(f"{OUT}/SHA256SUMS", "w") as f:
    for name, _ in sorted(manifest):
        h = hashlib.sha256(open(f"{OUT}/{name}", "rb").read()).hexdigest()
        f.write(f"{h}  {name}\n")

sizes = [s for _, s in manifest]
print(f"packaged {count} JPGs, max={max(sizes)//1024}KB total="
      f"{sum(sizes)//1024}KB -> {OUT}")
