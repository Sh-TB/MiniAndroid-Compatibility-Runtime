#!/usr/bin/env python3
# UNIFIED_011.3 — SCREENSHOT ORACLE (§22/§23)
# Second-frame visual correctness: before/after diff with mismatch bbox.
#
# A changed screenshot is NOT automatically a correct screenshot. This tool
# quantifies the delta between two MiniAndroid frames (before vs after a real
# interaction) and reports: dimensions, changed-pixel count, mismatch
# percentage, and the bounding box of the changed region — the numbers the
# campaign contract requires for visual-oracle evidence.
#
# Usage: oracle_diff.py <before.png> <after.png> <out.json> [diff.png]
import json
import sys

from PIL import Image, ImageChops
import numpy as np


def load_rgba(path):
    img = Image.open(path).convert("RGBA")
    return img, np.asarray(img, dtype=np.int16)


def main():
    if len(sys.argv) < 4:
        print("usage: oracle_diff.py <before.png> <after.png> <out.json> [diff.png]")
        return 2
    before_path, after_path, out_path = sys.argv[1:4]
    diff_path = sys.argv[4] if len(sys.argv) > 4 else None

    img_b, arr_b = load_rgba(before_path)
    img_a, arr_a = load_rgba(after_path)

    report = {
        "before": {"path": before_path, "size": list(img_b.size)},
        "after": {"path": after_path, "size": list(img_a.size)},
    }
    if img_b.size != img_a.size:
        report["error"] = "dimension mismatch"
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))
        return 1

    diff = np.abs(arr_b - arr_a)
    # a pixel counts as changed if ANY channel differs by more than 8/255
    changed_mask = np.any(diff > 8, axis=2)
    changed_px = int(changed_mask.sum())
    total_px = int(changed_mask.size)
    ys, xs = np.nonzero(changed_mask)

    bbox = None
    if changed_px:
        bbox = {
            "x0": int(xs.min()), "y0": int(ys.min()),
            "x1": int(xs.max()), "y1": int(ys.max()),
            "w": int(xs.max() - xs.min() + 1),
            "h": int(ys.max() - ys.min() + 1),
        }

    report["diff"] = {
        "changed_px": changed_px,
        "total_px": total_px,
        "changed_pct": round(100.0 * changed_px / total_px, 3),
        "bbox": bbox,
        "max_channel_delta": int(diff.max()),
        "mean_channel_delta": round(float(diff.mean()), 4),
    }

    # where did it change — coarse row/col profiles for interpretation
    if changed_px:
        row_hist = changed_mask.sum(axis=1)
        col_hist = changed_mask.sum(axis=0)
        thirds = {"top": 0, "middle": 0, "bottom": 0}
        h = changed_mask.shape[0]
        for name, sl in (("top", slice(0, h // 3)),
                         ("middle", slice(h // 3, 2 * h // 3)),
                         ("bottom", slice(2 * h // 3, h))):
            thirds[name] = int(row_hist[sl].sum())
        report["diff"]["row_distribution"] = thirds

    if diff_path:
        # amplified diff visualization
        vis = (diff[:, :, :3].astype(np.uint8) * 8).clip(0, 255)
        vis[changed_mask] |= np.array([255, 0, 0], dtype=np.uint8) * 0  # keep raw amp
        Image.fromarray(vis).save(diff_path)
        report["diff_png"] = diff_path

    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
