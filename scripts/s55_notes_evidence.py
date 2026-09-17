#!/usr/bin/env python3
# S55 Notes evidence audit — §19 screenshot quality gate + §20 determinism.
# Consumes the click-test output dir of the Notes run: baseline screenshot +
# click frames; emits per-frame census (size/colors/dominant/nonbg bbox),
# SHA256, and frame-vs-baseline pixel delta with changed bbox.
import hashlib
import json
import sys
from collections import Counter
from PIL import Image


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def census(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    data = list(im.getdata())
    c = Counter(data)
    total = w * h
    top = c.most_common(3)
    dominant = top[0][1] / total
    colors = len(c)
    # non-background bbox: pixels differing from the dominant color
    bg = top[0][0]
    minx, miny, maxx, maxy, nonbg = w, h, -1, -1, 0
    px = im.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if px[x, y] != bg:
                nonbg += 1
                if x < minx: minx = x
                if y < miny: miny = y
                if x > maxx: maxx = x
                if y > maxy: maxy = y
    return {
        'path': path, 'width': w, 'height': h, 'unique_colors': colors,
        'dominant_ratio': round(dominant, 4),
        'dominant_color': list(bg),
        'nonbg_sampled': nonbg * 4,
        'nonbg_bbox': [minx, miny, maxx, maxy] if maxx >= 0 else None,
        'sha256': sha256(path),
    }


def delta(path_a, path_b):
    a = Image.open(path_a).convert('RGB')
    b = Image.open(path_b).convert('RGB')
    if a.size != b.size:
        return {'error': f'size mismatch {a.size} vs {b.size}'}
    pa, pb = a.load(), b.load()
    w, h = a.size
    diff = 0
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if pa[x, y] != pb[x, y]:
                diff += 1
                if x < minx: minx = x
                if y < miny: miny = y
                if x > maxx: maxx = x
                if y > maxy: maxy = y
    return {
        'a': path_a, 'b': path_b, 'changed_px': diff,
        'changed_ratio': round(diff / (w * h), 4),
        'changed_bbox': [minx, miny, maxx, maxy] if maxx >= 0 else None,
    }


if __name__ == '__main__':
    d = sys.argv[1]
    out = {
        'baseline': census(f'{d}/screenshot.png'),
        'click_frames': [],
        'deltas': [],
    }
    import os
    for name in sorted(os.listdir(d)):
        if name.startswith('click_frame_') and name.endswith('.png'):
            cf = f'{d}/{name}'
            out['click_frames'].append(census(cf))
            out['deltas'].append(delta(f'{d}/screenshot.png', cf))
    print(json.dumps(out, indent=1))
