#!/usr/bin/env python3
"""cont73_census.py — pixel census + frame verdict for the 10 triage rows.
Reuses the user_golden_gate pixel_metrics law (same thresholds) + the
F-NEW-233 trace_summary frame_analysis verdict."""
import hashlib
import json
import math
import os
import sys

OUT = "/home/z/my-project/run/cont73/triage"
ROWS = ["eu.quelltext.memory", "com.chessclock.android",
        "com.simondalvai.ball2box", "org.opensurge2d.surgeengine",
        "page.codeberg.lanticy.guandan", "org.secuso.privacyfriendlysudoku",
        "org.secuso.privacyfriendlymemory", "org.secuso.privacyfriendlydame",
        "org.secuso.privacyfriendlysolitaire", "org.andstatus.game2048"]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def pixel_metrics(png):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    w, h = im.size
    px = list(im.resize((min(w, 270), min(h, 480))).getdata())
    total = len(px)
    colors = {}
    for p in px:
        colors[p] = colors.get(p, 0) + 1
    bg = max(colors.values())
    nonbg = total - bg
    ent = (-sum((c / total) * math.log2(c / total) for c in colors.values())
           if total else 0.0)
    m = {"unique_colors": len(colors),
         "nonbg_ratio": round(nonbg / total, 4),
         "entropy": round(ent, 3)}
    if m["nonbg_ratio"] >= 0.02 and m["unique_colors"] >= 64:
        m["pixclass"] = "REAL_APP_UI"
    elif m["nonbg_ratio"] >= 0.002 or m["unique_colors"] >= 24:
        m["pixclass"] = "PARTIAL_MARGINAL"
    else:
        m["pixclass"] = "WHITE_BLANK"
    return m


def frame_verdict(outdir):
    ts = os.path.join(outdir, "trace_summary.json")
    if os.path.exists(ts):
        try:
            fa = json.load(open(ts)).get("frame_analysis") or {}
            return fa.get("verdict"), fa.get("app_owned_pixels"), fa.get(
                "app_draw_ops")
        except Exception:
            pass
    return None, None, None


def main():
    result = {}
    for pkg in ROWS:
        d = os.path.join(OUT, pkg)
        shot = os.path.join(d, "screenshot.png")
        row = {}
        if os.path.exists(shot):
            row["screenshot_sha16"] = sha16(shot)
            row.update(pixel_metrics(shot))
        v, owned, ops = frame_verdict(d)
        row["frame_verdict"] = v
        row["app_owned_px"] = owned
        row["app_draw_ops"] = ops
        result[pkg] = row
        print(f"{pkg:38s} {str(row.get('pixclass','-')):16s} nonbg="
              f"{str(row.get('nonbg_ratio','-')):7s} colors="
              f"{str(row.get('unique_colors','-')):4s} frame={v} owned={owned} "
              f"ops={ops} shot={str(row.get('screenshot_sha16','-'))}")
    json.dump(result, open(os.path.join(OUT, "..", "triage_census.json"),
                           "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
