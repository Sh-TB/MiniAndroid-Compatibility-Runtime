#!/usr/bin/env python3
"""s93_aggregate.py — S93 §26/§28 aggregates: metrics.json, failure_map.json,
asset_truth.json, animation_truth.json, font_truth.json from run/s93/verdicts.
"""
import glob
import json
import os
from collections import Counter

REPO = "/home/z/my-project"
V93 = os.path.join(REPO, "run", "s93", "verdicts")

IMAGE_FIELDS = ("discovered", "resolved", "decoded", "rendered",
                "geometrically_verified", "content_verified",
                "visually_verified", "partial", "failed", "unknown")


def main():
    verdicts = {}
    for p in sorted(glob.glob(os.path.join(V93, "*.json"))):
        name = os.path.basename(p)[:-5]
        verdicts[name] = json.load(open(p))

    # --- §26 image truth aggregates ---------------------------------------
    img = Counter()
    asset_truth = {}
    for name, v in verdicts.items():
        for path, it in (v.get("image_truths") or {}).items():
            key = f"{name}:{path}"
            verd = it.get("verdict")
            asset_truth[key] = verd
            img["discovered"] += 1
            if verd == "NOT_APPLICABLE":
                img["decoded"] += 1  # provenance proved decode, no dst
                continue
            g = (it.get("geometry") or {}).get("value")
            c = (it.get("content") or {}).get("value")
            if g == "PASS":
                img["geometrically_verified"] += 1
            if c == "PASS":
                img["content_verified"] += 1
            if verd == "VISUALLY_VERIFIED":
                img["visually_verified"] += 1
            elif verd == "VISUALLY_PARTIAL":
                img["partial"] += 1
            elif verd in ("WRONG_CONTENT", "WRONG_GEOMETRY", "WRONG_POSITION",
                          "PLACEHOLDER", "OPAQUE_REPLACEMENT", "MISSING"):
                img["failed"] += 1
            elif verd in ("UNKNOWN", "UNANCHORED"):
                img["unknown"] += 1
    metrics = {
        "schema": "s93.metrics.v1",
        "titles": len(verdicts),
        "title_verdicts": dict(Counter(
            v.get("s93_verdict") for v in verdicts.values())),
        "images": dict(img),
        "s92_pilot_crosscheck": {
            name: s92_overall(v.get("package"))
            for name, v in verdicts.items() if name in PILOT_NAMES},
    }

    # --- §26 animation + font aggregates ----------------------------------
    anim = Counter()
    animation_truth = {}
    fonts = Counter()
    font_truth = {}
    text_stats = Counter()
    for name, v in verdicts.items():
        a = v.get("animation_truth")
        if a and a.get("verdict"):
            animation_truth[name] = a.get("verdict")
            verd = a.get("verdict")
            if verd in ("ANIMATION_GEOMETRY_VERIFIED",
                        "ANIMATION_CONTENT_VERIFIED"):
                anim["frame_correct"] += 1
            elif verd in ("ANIMATION_DECODED", "ANIMATION_RENDERED",
                          "SINGLE_FRAME"):
                anim["decoded_or_rendered"] += 1
            elif verd == "NOT_APPLICABLE":
                anim["no_contract"] += 1
            else:
                anim["failed"] += 1
        for fp, ft in (v.get("font_truths") or {}).items():
            font_truth[f"{name}:{fp}"] = ft.get("verdict")
            fonts["resolved"] += 1
            if ft.get("verdict") == "BROKEN_FONT":
                fonts["failed"] += 1
            else:
                fonts["glyph_object_ok"] += 1
        for tp, tt in (v.get("text_truths") or {}).items():
            text_stats[tt.get("verdict", "UNKNOWN")] += 1

    # --- §19 failure map ---------------------------------------------------
    failure_map = {}
    for name, v in verdicts.items():
        cats = [c.get("category") for c in
                (v.get("failure_categories") or [])]
        if cats:
            failure_map[name] = cats

    os.makedirs(os.path.join(REPO, "run", "s93"), exist_ok=True)
    for fname, data in (
            ("metrics.json", metrics),
            ("failure_map.json", failure_map),
            ("asset_truth.json", asset_truth),
            ("animation_truth.json", {"per_title": animation_truth,
                                      "totals": dict(anim)}),
            ("font_truth.json", {"per_object": font_truth,
                                 "text_verdicts": dict(text_stats),
                                 "totals": dict(fonts)})):
        with open(os.path.join(REPO, "run", "s93", fname), "w") as f:
            json.dump(data, f, indent=1, default=str)
        print("wrote", fname)
    print(json.dumps(metrics["title_verdicts"], indent=1))
    print("images:", dict(img))
    print("animation:", dict(anim))


PILOT_NAMES = set()
try:
    import sys
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    from s93_run_semantic import PILOT_CASES
    PILOT_NAMES = set(PILOT_CASES.keys())
except Exception:
    pass


def s92_overall(package):
    """S92 machine verdict for the same package (tolerant filename match)."""
    if not package:
        return None
    for p in glob.glob(os.path.join(REPO, "registry", "graphics_verdicts",
                                    f"{package}*.json")):
        try:
            return json.load(open(p)).get("overall")
        except Exception:
            continue
    return None


if __name__ == "__main__":
    main()
