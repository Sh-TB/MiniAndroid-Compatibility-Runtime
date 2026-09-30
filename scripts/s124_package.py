#!/usr/bin/env python3
"""s124_package.py — S124 THEME-BASE evidence pack (460px JPG <=100KB, English)."""
import glob
import os
import subprocess

from PIL import Image

R = "/home/z/my-project"
OUT = f"{R}/evidence/s124_theme_base"
os.makedirs(OUT, exist_ok=True)

PICKS = [
    ("run/s124/calcF1/frames/frame_023.png", "s124_calc1_themed_render.jpg",
     "Heading Calculator final render — 3-run deterministic a169346e, framework-res base active"),
    ("run/s124/flappyF1/frames/frame_016.png", "s124_flappy1_start_screen_golden.jpg",
     "FlappyCow start screen — byte-identical to S123 golden 13cf4746 x3 (no regression)"),
    ("run/s124/reg_gmdice/frames/frame_023.png", "s124_gmdice1_themed_menu.jpg",
     "gmdice menu — app theme now resolves through real framework chain"),
    ("run/s124/reg_unote/frames/frame_023.png", "s124_unote1_menu.jpg",
     "unote menu — window background + action bar from lawful theme values"),
    ("run/s124/reg_microtimer/frames/frame_023.png", "s124_microtimer1_keypad.jpg",
     "microtimer keypad render"),
    ("run/s124/doozF/frames/frame_015.png", "s124_dooz1_blank_frontier.jpg",
     "dooz last frame — theme base 355 keys loaded; first frame still blank (Compose frontier R-NEW-344)"),
    ("run/s124/tgF/frames/frame_047.png", "s124_telegram1_grey_frontier.jpg",
     "Telegram last frame — 3 grey colors: NOT A RENDER; SvgHelper themed-icon parsing runs; 8 uncaught"),
    ("run/s124/waF/frames/frame_023.png", "s124_whatsapp1_blackwhite_frontier.jpg",
     "WhatsApp last frame — 2 colors black/white: NOT A RENDER; AppContext.set frontier unchanged"),
    ("run/s124/notesF/frames/frame_023.png", "s124_notes1_defstyle.jpg",
     "notes — defStyleAttr tier active (2 widget template bags applied)"),
]

for src, name, desc in PICKS:
    if not os.path.exists(src):
        print("MISSING", src)
        continue
    dst = os.path.join(OUT, name)
    img = Image.open(src).convert("RGB")
    w, h = img.size
    nh = 460
    nw = int(w * nh / h)
    img = img.resize((nw, nh), Image.LANCZOS)
    q = 72
    img.save(dst, "JPEG", quality=q)
    while os.path.getsize(dst) > 100 * 1024 and q > 30:
        q -= 6
        img.save(dst, "JPEG", quality=q)
    print(f"{name}: {os.path.getsize(dst)} bytes q={q}")

# manifest
with open(os.path.join(OUT, "MANIFEST.txt"), "w") as f:
    f.write("S124 THEME/TEMPLATE BASE evidence — English-only, 460px, <=100KB\n")
    f.write("Engine: AOSP-law theme engine (Theme overlay stack + GetAttribute hops\n")
    f.write("+ defStyleAttr tier + android:theme subtree overlays + framework-res\n")
    f.write("package 0x01 router with staged-package skip + SPARSE/OFFSET16 type laws).\n\n")
    for _, name, desc in PICKS:
        f.write(f"{name}: {desc}\n")
print("manifest written")
