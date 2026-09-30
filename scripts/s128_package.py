#!/usr/bin/env python3
"""s128_package.py — S128 evidence JPGs (460px, English-only, <=100KB each).
Standing directive: no gameplay GIFs; small images with English captions only."""
import glob, os
from PIL import Image

R = "/home/z/my-project"
OUT = f"{R}/evidence/s128_input_law"
os.makedirs(OUT, exist_ok=True)

def jpg(src, dst, caption_px=460):
    if not src or not os.path.exists(src):
        print("MISS", dst); return
    img = Image.open(src).convert("RGB")
    w, h = img.size
    scale = 460 / w
    img = img.resize((460, int(h * scale)), Image.LANCZOS)
    q = 85
    p = f"{OUT}/{dst}"
    while True:
        img.save(p, "JPEG", quality=q, optimize=True)
        if os.path.getsize(p) <= 100_000 or q <= 40: break
        q -= 8
    print("OK ", dst, os.path.getsize(p) // 1024, "KB")

def frame(d, i):
    fs = sorted(glob.glob(f"{R}/run/s128/{d}/frames/frame_*.png"))
    return fs[i] if i < len(fs) else (fs[-1] if fs else None)

S = f"{R}/run/s128"
# 1. calc TouchTarget chain: pre-tap vs post-tap (3 keys 1-2-3)
jpg(frame("calc_taps", 18), "s128_calc1_before_taps.jpg")
jpg(frame("calc_taps", -1), "s128_calc2_after_taps_123.jpg")
# golden reference (S127 a169346e)
jpg(f"{S}/calc_r1/frames/frame_047.png" if os.path.exists(f"{S}/calc_r1/frames/frame_047.png") else frame("calc_r1", -1),
    "s128_calc3_golden_reference.jpg")
# 2. flappy TouchTarget chain + menu golden + Game activity
jpg(frame("flappy_r1", 16), "s128_flappy1_menu_golden_13cf4746.jpg")
jpg(frame("flappy_r1", -1), "s128_flappy2_after_tap_chain.jpg")
# 3. honest frontiers unchanged
jpg(frame("telegram", -1), "s128_telegram_grey_notarender.jpg")
jpg(frame("whatsapp", -1), "s128_whatsapp_bw_notarender.jpg")
# 4. coherence
jpg(frame("unote", -1), "s128_unote_boot_order_77.jpg")
print("done ->", OUT)
