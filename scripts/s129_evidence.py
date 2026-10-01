#!/usr/bin/env python3
"""s129_evidence.py — S129 evidence JPGs (460px, English-only captions)."""
import glob, json, os, shutil
from PIL import Image

R = "/home/z/my-project"
SRC = f"{R}/run/s129"
OUT = f"{R}/evidence/s129_input_law"
os.makedirs(OUT, exist_ok=True)


def save_jpg(src, dst, label=None):
    if not src or not os.path.exists(src):
        print("MISS", src)
        return
    img = Image.open(src).convert("RGB")
    w, h = img.size
    scale = 460.0 / w
    img = img.resize((460, int(h * scale)), Image.LANCZOS)
    img.save(f"{OUT}/{dst}", "JPEG", quality=82)
    print("OK  ", dst)


def last_frame(d):
    fs = sorted(glob.glob(f"{SRC}/{d}/frames/frame_*.png"))
    return fs[-1] if fs else None


save_jpg(last_frame("fixture_tap"),
         "s129_delegate_tap_real_dex_DELEGATE_CLICK.jpg")
save_jpg(last_frame("fixture_swipe"),
         "s129_velocity_real_dex_VY999.jpg")
save_jpg(last_frame("unote_swipe"),
         "s129_unote_swipe_move_delivery.jpg")
save_jpg(last_frame("calc_r1"),
         "s129_calc_golden_preserved_a169346e.jpg")
save_jpg(last_frame("flappy_r1"),
         "s129_flappy_menu_golden_preserved_13cf4746.jpg")
save_jpg(last_frame("ttt_taps"),
         "s129_ttt_byte_identical_b5a7a35d.jpg")
save_jpg(last_frame("telegram"),
         "s129_telegram_honest_not_a_render_3colors.jpg")
save_jpg(last_frame("whatsapp"),
         "s129_whatsapp_honest_not_a_render_2colors.jpg")

rep = json.load(open(f"{SRC}/s129_report.json"))
shutil.copy(f"{SRC}/s129_report.json", f"{OUT}/s129_input_wave_report.json")
print("wave gates: fixture texts:",
      "DELEGATE-CLICK" in rep["fixture_tap"]["texts"],
      "VY=999;VX=0" in rep["fixture_swipe"]["texts"])
