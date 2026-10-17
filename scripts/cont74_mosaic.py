#!/usr/bin/env python3
"""cont74_mosaic.py — build the CONT-74 pre/post log-evidence mosaic.

Left panel: PRE-FIX stderr rows (VOL-ESC LEAK len=13 x2) at binary
1ecb1949e5fa59cf. Right panel: POST-FIX rows (all DENIED + PATH-LAW +
positive control intact) at binary 2b3bf0bab3770c50, x3.
"""
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
W, H = 1180, 760
img = Image.new("RGB", (W, H), (16, 18, 24))
d = ImageDraw.Draw(img)
f = ImageFont.truetype(FONT, 15)
fs = ImageFont.truetype(FONT, 19)
fb = ImageFont.truetype(FONT, 22)

pre = """PRE-FIX  binary 1ecb1949e5fa59cf  (esc_pre3)
[C74-VERSION] code=V1-ESC pkg=com.probe.c74esc
[C74-SELF] OK wrote own.txt marker
[C74-VOL-ESC] LEAK ESCAPE read own marker via
  /storage/emulated/0/../../../data/data/
  com.probe.c74esc/files/own.txt len=13
[C74-VOL-ESC2] LEAK ESCAPE read own marker via
  /storage/emulated/0/../0/../../../data/data/
  com.probe.c74esc/files/own.txt len=13
[C74-FONT-ESC] OK denied/absent ... -> FileNotFound
  (resolve-ALLOWED: NO PATH-LAW DENIED line)
[C74-VOL-OK] OK volume round-trip
[PATH-LAW] DENIED FileInputStream "/etc/passwd"
[C74-NEG-ETC] OK denied/absent /etc/passwd

  -> runtime-proven tail-join escape: the volume
     backing EXISTS, three .. exit it, own sandbox
     bytes read back through the escape spelling."""

post = """POST-FIX  binary 2b3bf0bab3770c50  (esc_post_1..3, x3)
[C74-VERSION] code=V1-ESC pkg=com.probe.c74esc
[C74-SELF] OK wrote own.txt marker
[C74-VOL-ESC] OK denied/absent ... -> FileNotFound
[C74-VOL-ESC2] OK denied/absent ... -> FileNotFound
[C74-FONT-ESC] OK denied/absent ... -> FileNotFound
[C74-VOL-OK] OK volume round-trip
[PATH-LAW] DENIED FileInputStream
  "/storage/emulated/0/../../../data/data/..."
[PATH-LAW] DENIED FileInputStream
  "/system/fonts/../../data/data/..."
[PATH-LAW] DENIED FileInputStream "/etc/passwd"
[C74-NEG-ETC] OK denied/absent /etc/passwd

  -> F-NEW-377 tail-join containment (same
     path_contained law as F-NEW-375); positive
     control intact; c72priv fence 13/13;
     negatives 19/19; reinstall 8/8; goldens 4/4;
     wall dooz/opencalc/unote 9/9 MATCH."""

def panel(x0, title, body, color):
    d.rectangle([x0+8, 8, x0+566, H-12], outline=color, width=2)
    d.text((x0+24, 20), title, font=fb, fill=color)
    y = 58
    for line in body.splitlines():
        fill = (232, 240, 248)
        if "LEAK" in line: fill = (255, 96, 96)
        elif "PATH-LAW" in line or "DENIED" in line: fill = (120, 220, 140)
        elif line.strip().startswith("->"): fill = (255, 210, 90)
        d.text((x0+24, y), line, font=f, fill=fill)
        y += 21

d.text((24, H-42), "CONT-74 — issue #364 FOUNDATION-7 residual: volume + font tail-join path containment (F-NEW-377) — registry 682->683",
       font=fs, fill=(160, 170, 190))
panel(0,   "PROOF OF LEAK  (before fix)",  pre,  (255, 110, 110))
panel(600, "PROOF OF FIX  (after fix x3)", post, (110, 220, 140))
img.save("/home/z/my-project/evidence/cont74/cont74_mosaic.png")
print("mosaic saved")
