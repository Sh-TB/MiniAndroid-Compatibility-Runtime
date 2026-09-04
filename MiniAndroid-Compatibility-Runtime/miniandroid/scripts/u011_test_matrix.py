#!/usr/bin/env python3
"""UNIFIED_011 clean-clone test matrix runner.

Runs the canonical regression set against a built miniandroid binary and
emits a machine-readable summary (JSON) + human table.

Usage:
    python3 scripts/u011_test_matrix.py [--binary build/miniandroid] [--apk-dir DIR]

APK location policy (CAMPAIGN 011 §20/§21): APKs are NEVER stored in the
repository. They are fetched by scripts/download_test_apks.py into an
external cache directory (default: <repo>/../apk_cache or $MINIANDROID_APK_CACHE).
Each run reports APK FOUND / APK MISSING / SHA256 MATCH / MISMATCH.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent          # .../miniandroid
DEFAULT_CACHE = Path(os.environ.get("MINIANDROID_APK_CACHE", REPO.parent.parent / "apk_cache"))

# name -> (relative cache path, expected sha256 or None, timeout_s)
MATRIX = [
    ("gmdice",        "corpus/gmdice.apk",        "1621eda11b5dbc0c232b54c652d27aeab2f8a3c95be2c1f0632d6233b12d8a85", 120),
    ("telegram_v12",  "exp038_telegram/Telegram.apk", "f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6", 280),
    ("microtimer",    "corpus/microtimer.apk",    None, 120),
    ("stopwatch",     "corpus/stopwatch.apk",     None, 120),
    ("simplestopwatch","corpus/simplestopwatch.apk", None, 120),
    ("tictactoe",     "corpus/tictactoe.apk",     None, 120),
    ("unote",         "corpus/unote.apk",         None, 120),
    ("dooz",          "corpus/dooz.apk",          None, 200),
]

# canonical baselines (see MASTER docs + status_011_1.json).
# UNIFIED_011.1: 088ea640... = libpng-encoder baseline (pixel-identical to the
# UNIFIED_002-era 06fb40da... lineage; PNG file hash changed by design, R1).
# UNIFIED_011.2 IMAGE-RES-RENDER: simplestopwatch anchors move from
# d495e3cb2ccf6c11 (blank ImageButtons) to 2a12587a0acf196c — the
# android:src icons (lock/settings/menu) now decode and render for real.
# 2026-09-04 FIX-1..6 (real text pipeline + AOSP measure/layout): the anchor
# moves 2a12587a0acf196c -> 97933dbcb993ba09. This is an INTENTIONAL,
# documented rendering-contract change:
#   * text is now shaped by the REAL FriBidi/HarfBuzz/FreeType pipeline at
#     the view's real textSize (was: fixed 8x16 BitmapFont, microscopic on
#     density-scaled screens);
#   * measure/layout follows AOSP MeasureSpec modes (EXACTLY/AT_MOST/
#     UNSPECIFIED) + LinearLayout weights + RelativeLayout dependency rules;
#   * the toolbar moved to its XML-true position and buttons carry real
#     label text ("Start"/"Reset");
#   * the custom BigTextView surface shows an honest labeled placeholder
#     until its onDraw DEX chain (setText(String[])->drawText) lands.
# The old anchor's pixels are preserved in git history at 2a12587a.
BASELINE_SHA = {
    "telegram_v12": "088ea640587ec0d28fc7cd16b0097f2529ff7da2d594c3c2663c67531d770f6a",
    "simplestopwatch": "97933dbcb993ba0975c93a8dce7924f0cd5cd6b0fd802564391bb95387a6a71f",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(binary: Path, name: str, apk: Path, out_root: Path, timeout: int):
    outdir = out_root / name
    outdir.mkdir(parents=True, exist_ok=True)
    log = outdir / "run.log"
    t0 = time.time()
    try:
        with open(log, "w") as f:
            rc = subprocess.run(
                [str(binary), "run", str(apk), "-o", str(outdir), "-v"],
                cwd=str(REPO), stdout=f, stderr=subprocess.STDOUT,
                timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        rc = -99
    dt = round(time.time() - t0, 1)
    shot = outdir / "screenshot.png"
    entry = {
        "name": name, "apk": str(apk), "exit": rc, "seconds": dt,
        "screenshot_sha256": sha256(shot) if shot.exists() else None,
    }
    if name in BASELINE_SHA and entry["screenshot_sha256"]:
        entry["baseline_match"] = entry["screenshot_sha256"] == BASELINE_SHA[name]
    try:
        from PIL import Image
        im = Image.open(shot).convert("RGB")
        entry["nonwhite_px"] = sum(1 for p in im.getdata() if p != (255, 255, 255))
    except Exception:
        entry["nonwhite_px"] = None
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default=str(REPO / "build/miniandroid"))
    ap.add_argument("--apk-dir", default=str(DEFAULT_CACHE))
    ap.add_argument("--out", default=str(REPO / "run/u011/matrix"))
    ap.add_argument("--runs", type=int, default=1, help="repeat count for determinism check")
    args = ap.parse_args()

    binary, apk_dir, out_root = Path(args.binary), Path(args.apk_dir), Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    results = []
    for name, rel, expect_sha, timeout in MATRIX:
        apk = Path(args.apk_dir) / rel
        if not apk.exists():
            # fall back to legacy in-repo download dir if present (dev machines)
            legacy = REPO / "download" / rel
            apk = legacy if legacy.exists() else apk
        if not apk.exists():
            results.append({"name": name, "status": "APK MISSING", "apk": str(apk)})
            continue
        apk_ok = True
        if expect_sha:
            apk_ok = sha256(apk) == expect_sha
        for i in range(args.runs):
            r = run_one(binary, name if args.runs == 1 else f"{name}_r{i+1}",
                        apk, out_root, timeout)
            r["apk_sha_match"] = apk_ok if expect_sha else "unchecked"
            results.append(r)
    summary = {
        "binary": str(binary), "binary_sha256": sha256(binary),
        "results": results,
    }
    out_json = out_root / "matrix_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"{'name':<20} {'exit':<5} {'sec':<7} {'nonwhite':<9} screenshot/baseline")
    for r in results:
        if r.get("status") == "APK MISSING":
            print(f"{r['name']:<20} APK MISSING: {r['apk']}")
            continue
        base = ""
        if "baseline_match" in r:
            base = " BASELINE_MATCH" if r["baseline_match"] else " BASELINE_DIFF"
        print(f"{r['name']:<20} {r['exit']:<5} {r['seconds']:<7} "
              f"{str(r['nonwhite_px']):<9} {(r['screenshot_sha256'] or '')[:16]}{base}")
    print(f"\nsummary: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
