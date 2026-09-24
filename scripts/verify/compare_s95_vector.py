#!/usr/bin/env python3
"""compare_s95_vector.py — F-S95-VEC-1 golden comparator (L-S95-VECTOR-1).

Verifies, from the RUN-DIR evidence of the s95_vector fixture APK:
  Case 1 (iv_tri)   — the anydpi-v21 VECTOR (green triangle) won the resource
                      selection over the mdpi RED / hdpi BLUE PNG variants:
                      green ink fraction >= 0.04, red ink == 0, blue ink == 0,
                      0xCCCCCC "IMG?" placeholder == 0.
  Case 2 (iv_curve) — cubic-bezier pathData renders (blue ink fraction >=
                      0.04, placeholder == 0).
  Case 3 (iv_rot)   — group rotation 45 renders a DIAGONAL bar (purple ink
                      fraction >= 0.02 AND corner-quadrant ink present where
                      an unrotated bar would show none, placeholder == 0).

Exit 0 = ALL PASS. Machine JSON via --json.
"""
import argparse
import collections
import json
import os
import sys

from PIL import Image


def ink_fraction(img, box, predicate):
    region = img.crop(box)
    px = list(region.convert("RGB").getdata())
    if not px:
        return 0.0, {}
    counts = collections.Counter(px)
    hits = sum(1 for p in px if predicate(p))
    return hits / len(px), counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out")
    ap.add_argument("--json", dest="json_path")
    a = ap.parse_args()

    shot = os.path.join(a.run_dir, "screenshot.png")
    vt = os.path.join(a.run_dir, "view_tree.json")
    checks = []
    failed = 0

    def check(name, ok, detail):
        nonlocal failed
        if not ok:
            failed += 1
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    if not os.path.isfile(shot) or not os.path.isfile(vt):
        print("S95-VECTOR GOLDEN: FAIL (missing evidence)")
        sys.exit(1)

    img = Image.open(shot).convert("RGB")
    vtj = json.load(open(vt))
    views = {}
    for n in vtj.get("nodes", []):
        cls = str(n.get("class", ""))
        if "ImageView" in cls and n.get("visibility", 0) == 0:
            views[len(views)] = (int(n["x"]), int(n["y"]),
                                 int(n["width"]), int(n["height"]))
    if len(views) < 3:
        print("S95-VECTOR GOLDEN: FAIL (fewer than 3 ImageViews)")
        sys.exit(1)

    def box(i):
        x, y, w, h = views[i]
        return (x, y, x + w, y + h)

    green = lambda p: p[1] > 120 and p[0] < 100 and p[2] < 100
    blue = lambda p: p[2] > 120 and p[0] < 100 and p[1] < 100
    purple = lambda p: p[0] > 120 and p[2] > 120 and p[1] < 100
    red = lambda p: p[0] > 150 and p[1] < 100 and p[2] < 100
    placeholder = lambda p: abs(p[0] - 204) < 12 and abs(p[1] - 204) < 12 \
        and abs(p[2] - 204) < 12

    # Case 1 — differential selection oracle
    g, _ = ink_fraction(img, box(0), green)
    r, _ = ink_fraction(img, box(0), red)
    b, _ = ink_fraction(img, box(0), blue)
    ph, _ = ink_fraction(img, box(0), placeholder)
    check("case1 vector wins selection (green ink)", g >= 0.04, f"green={g:.4f}")
    check("case1 mdpi red variant NOT rendered", r < 0.001, f"red={r:.4f}")
    check("case1 hdpi blue variant NOT rendered", b < 0.001, f"blue={b:.4f}")
    check("case1 no IMG? placeholder", ph < 0.01, f"placeholder={ph:.4f}")

    # Case 2 — bezier flattening
    b2, _ = ink_fraction(img, box(1), blue)
    ph2, _ = ink_fraction(img, box(1), placeholder)
    check("case2 cubic pathData renders (blue ink)", b2 >= 0.04, f"blue={b2:.4f}")
    check("case2 no IMG? placeholder", ph2 < 0.01, f"placeholder={ph2:.4f}")

    # Case 3 — group rotation: ink + diagonal evidence (corner quadrant)
    p3, _ = ink_fraction(img, box(2), purple)
    ph3, _ = ink_fraction(img, box(2), placeholder)
    x, y, w, h = views[2]
    # top-left quadrant inside the view: a horizontal un-rotated bar at
    # mid-height has NO ink here; the 45° rotated bar MUST.
    tl_box = (x, y, x + w // 3, y + h // 3)
    tl, _ = ink_fraction(img, tl_box, purple)
    check("case3 rotated bar renders (purple ink)", p3 >= 0.02, f"purple={p3:.4f}")
    check("case3 diagonal evidence (top-left quadrant ink)", tl >= 0.02,
          f"tl={tl:.4f}")
    check("case3 no IMG? placeholder", ph3 < 0.01, f"placeholder={ph3:.4f}")

    result = {
        "golden": "F-S95-VEC-1",
        "law": "L-S95-VECTOR-1",
        "checks": checks,
        "failures": failed,
        "all_pass": failed == 0,
    }
    if a.json_path:
        with open(a.json_path, "w") as f:
            json.dump(result, f, indent=1)
    for c in checks:
        print(f"  [{'PASS' if c['ok'] else 'FAIL'}] {c['name']} ({c['detail']})")
    print("S95-VECTOR GOLDEN:", "ALL PASS (8 checks)"
          if failed == 0 else f"FAIL ({failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
