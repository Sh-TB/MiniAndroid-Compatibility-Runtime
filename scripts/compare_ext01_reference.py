#!/usr/bin/env python3
"""
compare_ext01_reference.py — GOLDEN-01 structural pixel comparison.

The trusted reference (upstream author's real-phone screenshot) contains
DEVICE-SPECIFIC strings (its ANDROID_ID / Android version / API level) and a
system gesture bar, so byte-equality with MiniAndroid is neither possible nor
required by the campaign (recorded in EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md).
Byte-equality IS enforced between MiniAndroid runs (Rule 12 — verified separately).

This script quantifies STRUCTURAL equivalence:
  1. background color (modal pixel)
  2. text ink bounding box + centering
  3. per-line ink bands (count, order, centers)
"""
from PIL import Image

REF = "/home/z/corpus/external_hello/helloworldselfaware-android-phone-screenshot.png"
MINI = "/home/z/corpus/external_hello/g49_run2/screenshot.png"

def analyze(path, label):
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    # Modal background = most common value
    hist = {}
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            v = px[x, y]
            hist[v] = hist.get(v, 0) + 1
    bg = max(hist, key=hist.get)
    # Ink pixels = far from background
    ink = [(x, y) for y in range(h) for x in range(w)
           if abs(px[x, y] - bg) > 60]
    if not ink:
        return dict(label=label, w=w, h=h, bg=bg, ink=0)
    xs = [p[0] for p in ink]; ys = [p[1] for p in ink]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # Row profile → line bands (rows containing ink, clustered)
    # EXCLUDE the bottom system-UI strip (gesture bar) from BOTH bands and
    # bbox: it belongs to the platform, not the app (recorded in the fixture
    # doc; reference bottom 7% only — MiniAndroid has no system bar at all).
    sysbar_top = int(h * 0.93)
    rows = sorted({y for _, y in ink if y < sysbar_top})
    ink_app = [(x, y) for (x, y) in ink if y < sysbar_top]
    bands = []
    start = prev = rows[0]
    for y in rows[1:]:
        if y - prev > 12:
            bands.append((start, prev)); start = y
        prev = y
    bands.append((start, prev))
    # App-content bbox from app ink only (system bar excluded)
    if not ink_app:
        return dict(label=label, w=w, h=h, bg=bg, ink=len(ink), bands=[])
    axs = [p[0] for p in ink_app]; ays = [p[1] for p in ink_app]
    ax0, ax1, ay0, ay1 = min(axs), max(axs), min(ays), max(ays)
    return dict(label=label, w=w, h=h, bg=bg, ink=len(ink),
                bbox=(ax0, ay0, ax1, ay1),
                cx=(ax0 + ax1) / 2, cy=(ay0 + ay1) / 2,
                bands=bands)

ref = analyze(REF, "reference(phone)")
mini = analyze(MINI, "miniandroid")

print("== reference ==", {k: v for k, v in ref.items() if k != 'bands'})
print("   text bands:", ref.get('bands'))
print("== miniandroid ==", {k: v for k, v in mini.items() if k != 'bands'})
print("   text bands:", mini.get('bands'))

checks = []
checks.append(("background identical (black)", ref['bg'] == mini['bg'] == 0))
checks.append(("background match", ref['bg'] == mini['bg']))
checks.append(("ink present", ref['ink'] > 1000 and mini['ink'] > 1000))
checks.append(("4-line band structure", len(ref.get('bands', [])) == len(mini.get('bands', [])) == 4))
if ref.get('bands') and mini.get('bands'):
    checks.append(("horizontal centering within 3%",
                   abs(ref['cx'] / ref['w'] - 0.5) < 0.03 and
                   abs(mini['cx'] / mini['w'] - 0.5) < 0.03))
    checks.append(("vertical centering within 6%",
                   abs(ref['cy'] / ref['h'] - 0.5) < 0.06 and
                   abs(mini['cy'] / mini['h'] - 0.5) < 0.06))
    checks.append(("text block width ratio within 25%",
                   abs(((mini['bbox'][2] - mini['bbox'][0]) / mini['w']) -
                       ((ref['bbox'][2] - ref['bbox'][0]) / ref['w'])) < 0.25))

print()
ok = True
for name, passed in checks:
    print(("PASS  " if passed else "FAIL  ") + name)
    ok &= passed
print()
print("GOLDEN-01 STRUCTURAL COMPARISON:", "PASS" if ok else "FAIL",
      f"({sum(1 for _, p in checks if p)}/{len(checks)} checks)")
