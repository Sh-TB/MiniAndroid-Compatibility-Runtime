#!/usr/bin/env python3
"""cont66_bmi_boxes.py — measure the exact pixel boxes in the BMI face:
EditText frames (153-grey), the blue Calculate button, spinner text glyph
columns. Compare with the XML ground truth geometry."""
from PIL import Image

im = Image.open('/home/z/my-project/run/cont66/survey/bmi/screenshot.png').convert('RGB')
W, H = im.size
px = im.load()

# 1) EditText frames: grey ~ (153,153,153)? scan for greyish pixels
grey_cols = {}
grey_rows = {}
for y in range(0, H, 2):
    for x in range(0, W, 2):
        r, g, b = px[x, y]
        if 130 <= r <= 190 and 130 <= g <= 190 and 130 <= b <= 190 and abs(r-g) < 12 and abs(g-b) < 12:
            grey_cols[x] = grey_cols.get(x, 0) + 1
            grey_rows[y] = grey_rows.get(y, 0) + 1
gcols = sorted([x for x, c in grey_cols.items() if c >= 8])
grows = sorted([y for y, c in grey_rows.items() if c >= 8])
def runs(vals):
    out = []
    for v in vals:
        if out and v - out[-1][1] <= 3: out[-1][1] = v
        else: out.append([v, v])
    return out
print('grey frame col-runs:', runs(gcols))
print('grey frame row-runs:', runs(grows))

# 2) Blue button: Material blue ~ (colorAccent). Find blue-ish region
bcols, brows = {}, {}
for y in range(0, H, 2):
    for x in range(0, W, 2):
        r, g, b = px[x, y]
        if b > 140 and b > r + 40 and g > r and g < b:
            bcols[x] = bcols.get(x, 0) + 1
            brows[y] = brows.get(y, 0) + 1
bcr = runs(sorted([x for x, c in bcols.items() if c >= 6]))
brr = runs(sorted([y for y, c in brows.items() if c >= 6]))
print('blue col-runs:', bcr)
print('blue row-runs:', brr)

# 3) spinner text columns: white glyphs on dark bg, left region
wcols = {}
for y in range(0, 500, 2):
    for x in range(0, 700, 2):
        r, g, b = px[x, y]
        if r > 200 and g > 200 and b > 200:
            wcols[x] = wcols.get(x, 0) + 1
print('white glyph col-runs (top 500px, left 700):', runs(sorted([x for x, c in wcols.items() if c >= 3]))[:12])

# 4) right-edge content check: how close does non-bg content reach x=W?
bg = px[2, 2]
rightmost = 0
for x in range(W - 1, 0, -1):
    n = 0
    for y in range(0, H, 6):
        r, g, b = px[x, y]
        if abs(r-bg[0]) + abs(g-bg[1]) + abs(b-bg[2]) > 30: n += 1
    if n >= 3: rightmost = x; break
print('rightmost non-bg column:', rightmost, 'of', W)
