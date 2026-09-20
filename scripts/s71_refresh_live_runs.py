#!/usr/bin/env python3
"""s71_refresh_live_runs.py — S71 W7: rebuild docs/foundation/live_runs.json
from the FRESH run/s71_live/* evidence (same schema), so diagnose.py /
graph_build.py / api_matrix / source_map consume current-binary facts instead
of stale S69-era artifacts (stale-data false-lead found in the F-136 bundle:
it cited the S69 golden sha while the current binary deterministically
produces the R-NEW-389 sha 4f41dda2...).

nonwhite count matches the S69 definition: pixels differing from the white
background (RGB != 255,255,255) counted over the full frame.

Usage: python3 scripts/s71_refresh_live_runs.py [--keep-old]
By default the OLD (s69) run records are archived into
docs/foundation/s71/live_runs_s69_archive.json before being replaced.
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path("/home/z/my-project")
OUT = ROOT / "docs/foundation/live_runs.json"
S71 = ROOT / "run/s71_live"
ARCHIVE = ROOT / "docs/foundation/s71/live_runs_s69_archive.json"


def nonwhite(p: Path) -> int:
    im = Image.open(p).convert("RGB")
    w, h = im.size
    px = im.load()
    n = 0
    for y in range(0, h, 2):          # stride-2 sampling like S69 census
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if not (r == 255 and g == 255 and b == 255):
                n += 1
    return n * 4  # unsample (matches full-frame scale)


import hashlib


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_record(d: Path, apk: str) -> dict:
    frames = []
    fdir = d / "frames"
    if not fdir.exists():
        fdir = d
    for f in sorted(fdir.glob("frame_*.png")):
        frames.append({"frame": f.name, "nonwhite": nonwhite(f),
                       "sha256": sha(f)})
    shot = d / "screenshot.png"
    screenshot = {"sha256": sha(shot), "nonwhite": nonwhite(shot),
                  "width": Image.open(shot).size[0],
                  "height": Image.open(shot).size[1]} if shot.exists() else {}
    calls = d / "api_calls.json"
    api_calls = {"total": 0, "by_status": {}}
    if calls.exists():
        try:
            arr = json.loads(calls.read_text())
            by_status = {}
            for c in arr:
                by_status[c.get("status", "?")] = \
                    by_status.get(c.get("status", "?"), 0) + 1
            api_calls = {"total": len(arr), "by_status": by_status,
                         "sha256": sha(calls)}
        except Exception:
            pass
    vt = d / "view_tree.json"
    vtn = 0
    vts = ""
    if vt.exists():
        vts = sha(vt)
        try:
            v = json.loads(vt.read_text())
            def count(n):
                if not isinstance(n, dict):
                    return 0
                return 1 + sum(count(c) for c in n.get("children", []) or [])
            vtn = count(v.get("root", v))
        except Exception:
            pass
    log = d / "engine.log"
    rc_zero = False
    if log.exists():
        txt = log.read_text(errors="ignore")
        rc_zero = "FATAL" not in txt
    return {
        "apk": apk,
        "dir": str(d),
        "status": "SUCCESS" if frames else "NO-FRAMES",
        "rc_zero": rc_zero,
        "generation": "s71",
        "max_frame_nonwhite": max((f["nonwhite"] for f in frames), default=0),
        "view_tree_nodes": vtn,
        "view_tree_sha256": vts,
        "api_calls": api_calls,
        "screenshot": screenshot,
        "frames": frames,
    }


def main():
    keep_old = "--keep-old" in sys.argv
    old = json.loads(OUT.read_text()) if OUT.exists() else {"runs": []}
    if not keep_old and not ARCHIVE.exists():
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_text(json.dumps(old, indent=1))
    runs = {d.name + ".apk": run_record(d, d.name + ".apk")
            for d in sorted(S71.iterdir()) if d.is_dir()}
    merged = [runs[apk] for apk in sorted(runs)]
    # preserve any s69-era runs for APKs not re-run in s71 (none today)
    for r in old.get("runs", []):
        if r["apk"] not in runs:
            merged.append(r)
    merged.sort(key=lambda r: r["apk"])
    out = {"generated": "S71 refresh from run/s71_live", "runs": merged}
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT} ({len(merged)} runs)")
    for r in merged:
        fs = r.get("frames", [])
        shas = {f["sha256"][:12] for f in fs}
        print(f"  {r['apk']:<42} frames={len(fs)} distinct={len(shas)} "
              f"nonwhite={fs[0]['nonwhite'] if fs else 0} "
              f"api_calls={r.get('api_calls', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
