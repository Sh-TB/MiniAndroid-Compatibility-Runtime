#!/usr/bin/env python3
"""cont66_pixel.py — column-band + row-band census of the 4 compose-lane faces.
For each face: background, per-column-band ink share (find compression/clipping),
dark glyph count, button-like regions."""
import json, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from PIL import Image
from cont56_pixel_analysis import analyze  # reuse canonical tool

def band_census(path, bands=10):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    px = im.load()
    # background = corner color
    bg = px[2, 2]
    def nonbg_count(x0, y0, x1, y1):
        n = 0
        for y in range(y0, y1, 4):
            for x in range(x0, x1, 4):
                r, g, b = px[x, y]
                if abs(r-bg[0])+abs(g-bg[1])+abs(b-bg[2]) > 30:
                    n += 1
        return n
    colbands = []
    step = W // bands
    for i in range(bands):
        cnt = nonbg_count(i*step, 0, (i+1)*step, H)
        total = ((step)//4) * (H//4)
        colbands.append(round(cnt/total, 3))
    rowbands = []
    rstep = H // bands
    for i in range(bands):
        cnt = nonbg_count(0, i*rstep, W, (i+1)*rstep)
        total = (W//4) * (rstep//4)
        rowbands.append(round(cnt/total, 3))
    return bg, colbands, rowbands

faces = {
  'simplecalc': 'run/cont66/survey/simplecalc/screenshot.png',
  'opencalc':   'run/cont66/survey/opencalc/screenshot.png',
  'tanana':     'run/cont66/survey/tanana/screenshot.png',
  'bmi':        'run/cont66/survey/bmi/screenshot.png',
  'alex':       'run/cont66/survey/alex/screenshot.png',
}
out = {}
for name, path in faces.items():
    a = analyze(path)[0] if isinstance(analyze(path), tuple) else analyze(path)
    bg, colbands, rowbands = band_census(path)
    out[name] = {
        'bg': bg,
        'nonbg_share': a['nonbg_share'],
        'dark_glyph_samples': a['dark_glyph_samples'],
        'button_like_count': a['button_like_count'],
        'col_ink_bands_L2R': colbands,
        'row_ink_bands_T2B': rowbands,
    }
    print(f"== {name} == bg={bg} nonbg={a['nonbg_share']} glyphs={a['dark_glyph_samples']} buttons={a['button_like_count']}")
    print('  col:', colbands)
    print('  row:', rowbands)
json.dump(out, open('/home/z/my-project/run/cont66/survey/pixel_census.json', 'w'), indent=1)
