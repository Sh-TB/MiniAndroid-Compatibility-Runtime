#!/usr/bin/env python3
"""s182_mosaic.py — the user's «کاشی موزاییکی بزرگ از تمامی اجرا برنامه ها».

ONE BIG MOSAIC of every distinct title we have EVER rendered, newest face per
title, labeled with tag + face8 + verdict class. Newest-session-first
priority; older archive shots only fill titles not seen in newer sessions.

Output: evidence/s182_mosaic/S182_MOSAIC.png (+ copy download/S182_MOSAIC.png)
"""
import hashlib
import json
import re
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path("/home/z/my-project")
EVID = BASE / "evidence/s182_mosaic"
EVID.mkdir(parents=True, exist_ok=True)
OUT = EVID / "S182_MOSAIC.png"
DL = BASE / "download/S182_MOSAIC.png"

# ---- newest-first screenshot sources (dir glob, title-mapping mode) ----
SOURCES = [
    # (glob, mode) mode: 'rundir' -> parent dir name; 'file' -> file stem
    ("run_s182_minimal2/*/screenshot.png", "rundir"),
    ("run_s166_trains/s182_tg/screenshot.png", "file"),
    ("run_s166_trains/s182_dz/screenshot.png", "file"),
    ("run_s181_minimal/*/screenshot.png", "rundir"),
    ("run_s180_battery/*/screenshot.png", "rundir"),
    ("evidence/s179_c9/harness/run_*/screenshot.png", "rundir"),
    ("evidence/s175_a17/*/screenshot.png", "rundir"),
    ("evidence/s115_sweep/t*/screenshot.png", "rundir"),
    ("evidence/s121_full_sessions/*.jpg", "file"),
    ("evidence/s120_new_games/*.png", "file"),
    ("evidence/s124_theme_base/*.jpg", "file"),
    ("evidence/s123_themed_apps/*.jpg", "file"),
    ("evidence/s164_trains/*screenshot*.png", "file"),
    ("evidence/s163_runs/*.png", "file"),
    ("evidence/s118_complete/*.jpg", "file"),
    ("evidence/s117_complete_graphics/*/screenshot_small.png", "rundir"),
    ("evidence/s113_fullgui/*/screenshot.png", "rundir"),
    ("evidence/s112_html5_generalization/*/screenshot.png", "rundir"),
    ("evidence/s112_html5_generalization/gates/*/screenshot.png", "rundir"),
    ("evidence/s110_telegram/*/screenshot.png", "rundir"),
    ("evidence/s107_games/*/screenshot.png", "rundir"),
    ("evidence/s106_fresh/*/screenshot.png", "rundir"),
    ("evidence/cont56/*_full.png", "file"),
    ("evidence/cont61/*.png", "file"),
    ("evidence/cont65/*.png", "file"),
    ("evidence/cont41_audit/shots/*.png", "file"),
    ("evidence/cont94/*.jpg", "file"),
]

CLASS_OF = {}   # tag -> (class, face)
for jf, src in [("evidence/s182_minimal2/S182_BATTERY.json", "S182"),
                ("evidence/s181_minimal/S181_MINIMAL.json", "S181"),
                ("evidence/s182_minimal2/S180_RESHOOT.json", "S180R"),
                ("evidence/s180_battery/S180_BATTERY.json", "S180")]:
    p = BASE / jf
    if p.exists():
        for tag, row in json.load(open(p)).items():
            if not isinstance(row, dict):
                continue
            cls = row.get("class") or "?"
            face = (row.get("face") or "")[:8]
            if tag not in CLASS_OF or src in ("S182", "S180R"):
                CLASS_OF[tag] = (cls, face, src)

COLOR = {"REAL_APP_CONTENT": (36, 138, 61), "PIN_MATCH": (36, 138, 61),
         "REAL": (36, 138, 61),
         "PARTIAL": (214, 158, 20), "DEFAULT_BACKGROUND_ONLY": (200, 60, 40),
         "NO_FRAME": (150, 40, 40), "NO_ROOT": (150, 40, 40),
         "INSTALL_FAIL": (90, 90, 90), "ARCHIVE": (70, 90, 140),
         "SYSTEM_CHROME_ONLY": (214, 158, 20)}


def norm(tag):
    t = tag
    t = re.sub(r"^t\d+_", "", t)          # s115 t115_com.foo
    t = re.sub(r"^(s1\d+|cont\d+|fix\d+|run)_", "", t)
    t = re.sub(r"_(run\d+|postfix\d+|tap\d*|gate|seed|settle|deep|baseline|"
               r"longshot|boot|w\d+)$", "", t)
    return t


ALIAS = {"s182_tg": "telegram", "s182_dz": "dooz"}
CLASS_ALIAS = {"telegram": "tg"}


def classify(tag, face8):
    tag = ALIAS.get(tag, tag)
    lookup = CLASS_ALIAS.get(tag, tag)
    if lookup in CLASS_OF:
        cls, f8, src = CLASS_OF[lookup]
        return (cls, f8 or face8, src)
    for known, (cls, f8, _src) in CLASS_OF.items():
        if face8 and f8 and face8 == f8:
            return (cls, f8, "face-match")
    return ("ARCHIVE", face8, None)


tiles = []          # (title, path, class, face8, src_session)
seen = set()
order = ["s182_tg", "s182_dz", "run_s182", "run_s181",
         "run_s180_battery", "s180r", "s179", "s175", "s115", "s121",
         "s120", "s124", "s123", "s164", "s163", "s118", "s117", "s113",
         "s112", "s110", "s107", "s106", "cont56", "cont61", "cont65",
         "cont41", "cont94"]


def src_rank(p):
    s = str(p).lower()
    for i, k in enumerate(order):
        if k in s:
            return i
    return len(order)


files = []
for pat, mode in SOURCES:
    for p in sorted(BASE.glob(pat)):
        files.append((p, mode))
files.sort(key=lambda x: (src_rank(x[0]), str(x[0])))

FIXED_TAG = {
    "run_s166_trains/s182_tg/screenshot.png": "telegram",
    "run_s166_trains/s182_dz/screenshot.png": "dooz",
}

for p, mode in files:
    raw = p.parent.name if mode == "rundir" else p.stem
    key = str(p.relative_to(BASE))
    tag = FIXED_TAG.get(key) or ALIAS.get(norm(raw), norm(raw))
    if not tag or tag in seen:
        continue
    try:
        im = Image.open(p)
        im.load()
    except Exception:
        continue
    digest = hashlib.sha256(p.read_bytes()).hexdigest()[:8]
    seen.add(tag)
    tiles.append((tag, p, digest, src_rank(p)))

rows = []
for tag, p, face8, rank in tiles:
    cls, f8, src = classify(tag, face8)
    rows.append((tag, p, cls, f8, rank))

print(f"distinct titles: {len(rows)}")
from collections import Counter
cnt = Counter(c for _, _, c, _, _ in rows)
print(cnt)

# ---- render ----
TW, TH, LBL, HDR, COLS = 208, 440, 40, 150, 8
font_l = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/"
                            "DejaVuSansMono.ttf", 12)
font_h = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
nrows = (len(rows) + COLS - 1) // COLS
W, H = COLS * (TW + 6) + 12, HDR + nrows * (TH + LBL + 6) + 12
canvas = Image.new("RGB", (W, H), (24, 26, 32))
d = ImageDraw.Draw(canvas)
real = cnt.get("REAL_APP_CONTENT", 0) + cnt.get("PIN_MATCH", 0) + \
    cnt.get("REAL", 0)
d.text((16, 14), f"MiniAndroid Compatibility Runtime — ALL-RUNS MOSAIC "
       f"({len(rows)} titles, newest face per title, binary main "
       f"5d7edcdb34b1502c C9+C7)", font=font_h, fill=(235, 235, 240))
d.text((16, 56), f"REAL_APP_CONTENT/PIN_MATCH: {real}    PARTIAL: "
       f"{cnt.get('PARTIAL', 0) + cnt.get('SYSTEM_CHROME_ONLY', 0)}    "
       f"NO_FRAME/NO_ROOT: {cnt.get('NO_FRAME', 0) + cnt.get('NO_ROOT', 0)}"
       f"    DEFAULT_BACKGROUND_ONLY: {cnt.get('DEFAULT_BACKGROUND_ONLY', 0)}"
       f"    INSTALL_FAIL: {cnt.get('INSTALL_FAIL', 0)}    "
       f"ARCHIVE(older session): {cnt.get('ARCHIVE', 0)}",
       font=font_l, fill=(200, 205, 215))
d.text((16, 84), "green=app content renders   amber=partial chrome   "
       "red=no root frame / background only   blue=archived older-session "
       "face (pre-S180)", font=font_s, fill=(160, 165, 175))
d.text((16, 106), "S182 battery (this session): 10 tiny games + 10 simple "
       "apps -> 9/20 REAL_APP_CONTENT; census total now 49 measured titles",
       font=font_l, fill=(140, 200, 150))

for i, (tag, p, cls, f8, rank) in enumerate(rows):
    cx = 12 + (i % COLS) * (TW + 6)
    cy = HDR + (i // COLS) * (TH + LBL + 6)
    try:
        im = Image.open(p).convert("RGB")
        im.thumbnail((TW, TH))
        canvas.paste(im, (cx + (TW - im.width) // 2, cy))
    except Exception:
        pass
    band = COLOR.get(cls, (70, 90, 140))
    d.rectangle([cx, cy + TH, cx + TW, cy + TH + LBL], fill=band)
    d.text((cx + 5, cy + TH + 2), tag[:24], font=font_l,
           fill=(255, 255, 255))
    d.text((cx + 5, cy + TH + 21), f"{cls[:12]} {f8}", font=font_s,
           fill=(255, 255, 255))

canvas.save(OUT, optimize=True)
DL.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(OUT, DL)
print(f"saved {OUT} ({OUT.stat().st_size/1e6:.1f} MB) {W}x{H}")
print(f"copy  {DL}")
