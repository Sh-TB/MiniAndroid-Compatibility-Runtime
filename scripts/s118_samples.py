#!/usr/bin/env python3
"""S118 — generate sample images for the Telegram state + knowledge-transfer pack.

Outputs (to /home/z/my-project/download/s118_samples/):
  1. telegram_current_frame.png   — the latest official-Telegram render (honest state)
  2. telegram_login_geomap.png   — annotated view-tree geometry map (view_tree.json)
                                    showing the login UI now ON-SCREEN with real
                                    text/positions/colors from the run
  3. telegram_baseline_vs_now.png — S117 placeholder frame vs S118 frame
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path('/home/z/my-project')
OUT = BASE / 'download/s118_samples'
OUT.mkdir(parents=True, exist_ok=True)
FONT_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
]

def font(sz):
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

W, H = 1080, 1920

# ── 1. current frame ─────────────────────────────────────────────────────
src = Path('/tmp/s118/fix25/screenshot.png')
if src.exists():
    img = Image.open(src).convert('RGB')
    img.save(OUT / 'telegram_current_frame.png')
    print('saved telegram_current_frame.png', img.size)

# ── 2. geometry map from view_tree.json ──────────────────────────────────
vt = None
for cand in [Path('/tmp/s118/fix20/view_tree.json'),
             Path('/tmp/s118/fix25/view_tree.json'),
             BASE / 'tmp/s118/fix20/view_tree.json']:
    if cand.exists():
        vt = cand
        break
assert vt, 'no view_tree.json found'
d = json.load(open(vt))
nodes = {n['object_id']: n for n in d['nodes']}

map_img = Image.new('RGB', (W, H), (250, 250, 250))
dr = ImageDraw.Draw(map_img, 'RGBA')
f_small = font(16)
f_tiny = font(13)

# draw only the login-chain subtree (from the LinearLayout that holds the phone screen)
def find_text_nodes():
    out = []
    for n in nodes.values():
        t = n.get('text') or ''
        if any(k in t for k in ('YourNumber', 'StartText', 'StartMessaging',
                                'Disable', 'LowPower')):
            out.append(n)
    return out

def draw_box(n, color, label):
    x, y, w, h = n['x'], n['y'], n['width'], n['height']
    x, y = max(0, x), max(0, y)
    w, h = max(2, min(w, W - x)), max(2, min(h, H - y))
    dr.rectangle([x, y, x + w - 1, y + h - 1], outline=color, width=3)
    if label:
        dr.text((x + 6, y + 4), label[:48], fill=color, font=f_tiny)

LOGIN_KEYS = ['YourNumber', 'StartText', 'StartMessaging', 'Country', 'Code', 'Disable']
cont_count = 0
# container boxes (subtle)
for n in nodes.values():
    if n['width'] >= 400 and n['height'] >= 120 and n['y'] < H:
        cont_count += 1
        if cont_count > 60:
            break
        dr.rectangle([n['x'], n['y'], n['x'] + min(n['width'], W) - 1,
                      n['y'] + min(n['height'], H) - 1],
                     outline=(180, 200, 230, 90), width=2)

# login text nodes (prominent)
for n in find_text_nodes():
    if n['y'] < H + 400:  # near-screen
        t = (n.get('text') or '')[:40]
        draw_box(n, (200, 30, 30, 255), t)

dr.text((24, 16), 'S118 — official Telegram: login/phone view-tree geometry (post ROOT-068)',
        fill=(20, 20, 20), font=font(22))
dr.text((24, 48), 'red = text views with resolved theme colors (e.g. YourNumber #1a1d21, Telegram-blue #85caff)',
        fill=(90, 90, 90), font=font(17))
map_img.save(OUT / 'telegram_login_geomap.png')
print('saved telegram_login_geomap.png')

# ── 3. baseline vs now side-by-side ───────────────────────────────────────
base_shot = Path('/tmp/s118/base_official/screenshot.png')
cur_shot = Path('/tmp/s118/fix25/screenshot.png')
if base_shot.exists() and cur_shot.exists():
    a = Image.open(base_shot).convert('RGB')
    b = Image.open(cur_shot).convert('RGB')
    scale = 0.5
    a = a.resize((int(W * scale), int(H * scale)))
    b = b.resize((int(W * scale), int(H * scale)))
    combo = Image.new('RGB', (a.width * 2 + 30, a.height + 70), (255, 255, 255))
    combo.paste(a, (10, 60))
    combo.paste(b, (a.width + 20, 60))
    dr2 = ImageDraw.Draw(combo)
    dr2.text((10, 12), 'S117 baseline (login tree measured, off-screen)',
             fill=(0, 0, 0), font=font(20))
    dr2.text((a.width + 20, 12), 'S118 (ROOT-068: tree on-screen, theme colors live)',
             fill=(0, 0, 0), font=font(20))
    combo.save(OUT / 'telegram_baseline_vs_now.png')
    print('saved telegram_baseline_vs_now.png')

# ── 4. gate proof montage ────────────────────────────────────────────────
gates = []
for name in ('breakout', 'ballbreak', 'dooz'):
    p = BASE / f'tmp/s117_baseline/gates/{name}/screenshot.png'
    if p.exists():
        im = Image.open(p).convert('RGB')
        im.thumbnail((320, 560))
        gates.append((name, im))
if gates:
    cw = max(im.width for _, im in gates) + 20
    combo = Image.new('RGB', (cw * len(gates), 640), (255, 255, 255))
    dr3 = ImageDraw.Draw(combo)
    for i, (name, im) in enumerate(gates):
        combo.paste(im, (i * cw + 10, 50))
        dr3.text((i * cw + 10, 14), name, fill=(0, 0, 0), font=font(20))
    combo.save(OUT / 'regression_gates_s118.png')
    print('saved regression_gates_s118.png')

print('DONE ->', OUT)

