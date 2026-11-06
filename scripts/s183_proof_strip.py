#!/usr/bin/env python3
"""s183_proof_strip.py — honest visual: what our 'REAL_APP_CONTENT' labels actually look like.
Left→right rows:
  1. #11 TicTacToe: FIXTURE win frame (what DONE showed) vs REAL APK face (1 flat color)
  2. The 5 C_TEXT_ON_FLAT faces called REAL today (textpad/terminightor/pfdicer/tg/forkgram)
  3. Contrast: 3 A_RICH faces (tetris, g2048, snake_deluxe)
  4. Contrast: 3 B_STRUCTURED faces (opencalc, microtimer, tripeaks)
Each tile gets an honest caption band."""
from PIL import Image, ImageDraw

B = "/home/z/my-project"
TILE_W, TILE_H, CAP = 300, 533, 46

rows = [
    ("#11 TicTacToe: fixture 'DONE' vs real APK today", [
        (f"{B}/docs/evidence/visual_forensics/tictactoe/run1/win_full.png", "FIXTURE (self-built) win frame\n97.7% flat blue + X/O glyphs"),
        (f"{B}/run_s182_minimal2/emmanuelttt/screenshot.png", "REAL APK (com.emmanuelmess)\n1 color, 0 app px, GdxRuntimeException"),
    ]),
    ("The 5 faces we labeled REAL that are 'one text line on white'", [
        (f"{B}/run_s182_minimal2/textpad/screenshot.png", "textpad 1.13% nonbg 13 colors"),
        (f"{B}/run_s181_minimal/terminightor/screenshot.png", "terminightor 0.62% nonbg 22 colors"),
        (f"{B}/run_s182_minimal2/pfdicer/screenshot.png", "pfdicer 0.16% nonbg 121 colors"),
        (f"{B}/run_s166_trains/s182_tg/screenshot.png", "telegram 0.15% nonbg (white frontier)"),
        (f"{B}/run_s180_battery/forkgram/screenshot.png", "forkgram 0.15% nonbg (white frontier)"),
    ]),
    ("A_RICH: genuine multi-color graphics (10 titles like these)", [
        (f"{B}/run_s180_battery/tetris/screenshot.png", "tetris 60% nonbg"),
        (f"{B}/run_s180_battery/g2048/screenshot.png", "g2048 60% nonbg"),
        (f"{B}/run_s180_battery/snake_deluxe/screenshot.png", "snake_deluxe 74% nonbg"),
    ]),
    ("B_STRUCTURED: real UI, flat fills, ~0 image assets", [
        (f"{B}/run_s180_battery/opencalc/screenshot.png", "opencalc 46% nonbg flat"),
        (f"{B}/run_s180_battery/microtimer/screenshot.png", "microtimer 44% nonbg flat"),
        (f"{B}/run_s181_minimal/tripeaks/screenshot.png", "tripeaks 29% nonbg flat"),
    ]),
]

pad = 8
label_h = 34
W = max(len(t) for _, t in rows) * (TILE_W + pad) + pad
H = pad + sum(label_h + CAP + TILE_H + pad for _ in rows)
canvas = Image.new("RGB", (W, H), (16, 18, 24))
d = ImageDraw.Draw(canvas)
try:
    from PIL import ImageFont
    f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    f_cap = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except Exception:
    f_title = f_cap = None

y = pad
for title, tiles in rows:
    d.rectangle([0, y, W, y + label_h - 4], fill=(28, 32, 44))
    d.text((pad + 4, y + 7), title, fill=(255, 220, 120), font=f_title)
    y += label_h
    x = pad
    for path, cap in tiles:
        try:
            im = Image.open(path).convert("RGB")
            im.thumbnail((TILE_W, TILE_H))
            canvas.paste(im, (x, y))
        except Exception as e:
            d.rectangle([x, y, x + TILE_W, y + TILE_H], fill=(60, 20, 20))
            d.text((x + 6, y + TILE_H // 2), f"missing: {e.__class__.__name__}", fill=(255, 120, 120), font=f_cap)
        d.rectangle([x, y, x + TILE_W - 1, y + TILE_H + CAP - 1], outline=(90, 96, 120))
        for i, line in enumerate(cap.split("\n")):
            d.text((x + 4, y + TILE_H + 4 + i * 15), line, fill=(210, 214, 228), font=f_cap)
        x += TILE_W + pad
    y += TILE_H + CAP + pad

out = f"{B}/evidence/s183_audit1112/S183_PROOF_STRIP.png"
canvas.save(out)
print(out, canvas.size)
