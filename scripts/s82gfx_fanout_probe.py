#!/usr/bin/env python3
"""S82-GFX-REVOLUTION P5 — fanout probe.

F-NEW-158 (programmatic background family) was root-caused + fixed via the
fixture ladder. Mission law §19: "How many titles does this fix unlock?"
— re-run a representative subset of the EXECUTED corpus at the new binary
with pixel provenance, and diff each title's screenshot palette against the
frozen S82 COMPARISON.MINIANDROID_PALETTE. Honest deltas only.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter

sys.path.insert(0, "/home/z/my-project/scripts")
from PIL import Image

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
APK_CACHE = "/tmp/my-project/apk_cache/s82"
OUT = "/home/z/my-project/run/s82gfx/fanout"
INDEX = "/home/z/my-project/docs/corpus/s82/compatibility_index.json"

TITLES = ["GAME-001", "GAME-004", "APP-001", "APP-002", "APP-006", "MAND-002"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def palette_of(png, sample=2):
    im = Image.open(png).convert("RGB")
    c = Counter()
    for y in range(0, im.size[1], sample):
        for x in range(0, im.size[0], sample):
            c[im.getpixel((x, y))] += 1
    total = sum(c.values()) or 1
    dom = [{"rgb": list(col), "ratio": round(n / total, 3)}
           for col, n in c.most_common(5)]
    return {"UNIQUE_COLORS": len(c), "DOMINANT": dom}


def main():
    os.makedirs(OUT, exist_ok=True)
    index = json.load(open(INDEX))
    by_tid = {t["TITLE_ID"]: t for t in index["TITLES"]}
    results = {}
    for tid in TITLES:
        rec = by_tid.get(tid)
        if not rec:
            continue
        pkg = rec["PACKAGE"]
        apks = sorted(glob.glob(f"{APK_CACHE}/{pkg}_*.apk"))
        if not apks:
            results[tid] = {"APK": "MISSING"}
            continue
        apk = apks[0]
        outdir = f"{OUT}/{tid}"
        os.makedirs(outdir, exist_ok=True)
        env = dict(os.environ)
        env["MINIANDROID_GFX_PROVENANCE"] = f"{outdir}/provenance.json"
        log = f"{outdir}.log"
        cmd = [ENG, "run", "--execution-mode", "real-dalvik",
               "--frames", "8", "--frame-delay", "300", "-o", outdir, apk]
        with open(log, "w") as lf:
            try:
                rc = subprocess.call(cmd, stdout=lf, stderr=lf,
                                     timeout=420, env=env)
            except subprocess.TimeoutExpired:
                rc = -1
        frames = sorted(glob.glob(f"{outdir}/frames/frame_*.png"))
        shot = f"{outdir}/screenshot.png"
        newest = frames[-1] if frames else None
        now_palette = palette_of(newest) if newest else None
        old_palette = (rec.get("COMPARISON") or {}).get("MINIANDROID_PALETTE")
        new_chain = None
        prov = f"{outdir}/provenance.json"
        if os.path.exists(prov):
            p = json.load(open(prov))
            events = p.get("events", [])
            new_chain = {
                "events": len(events),
                "drawn": sum(1 for e in events if e.get("DRAW_CALLED")),
                "not_drawn": [
                    {"origin": e.get("origin"), "path": e.get("path"),
                     "FAILURE": e.get("FAILURE")}
                    for e in events if not e.get("DRAW_CALLED")][:8],
                "shot_nonwhite": (p.get("screenshot") or {}).get("nonwhite_px"),
                "shot_unique": (p.get("screenshot") or {}).get("unique_colors"),
            }
        results[tid] = {
            "PACKAGE": pkg,
            "APK": os.path.basename(apk),
            "APK_SHA256": sha256_file(apk)[:16],
            "RC": rc,
            "FRAME": newest,
            "SCREENSHOT_SHA256": sha256_file(newest)[:16] if newest else None,
            "PALETTE_BEFORE_FROZEN": {
                "UNIQUE_COLORS": (old_palette or {}).get("UNIQUE_COLORS"),
                "DOMINANT_TOP1": (old_palette or {}).get("DOMINANT", [{}])[0],
            },
            "PALETTE_AFTER_FIX": now_palette,
            "CHAIN": new_chain,
        }
        print(tid, pkg, "rc=", rc,
              "before_unique=", (old_palette or {}).get("UNIQUE_COLORS"),
              "after_unique=", now_palette and now_palette["UNIQUE_COLORS"])
    json.dump(results, open(f"{OUT}/FANOUT_RESULT.json", "w"), indent=1)
    print("written", f"{OUT}/FANOUT_RESULT.json")


if __name__ == "__main__":
    main()
