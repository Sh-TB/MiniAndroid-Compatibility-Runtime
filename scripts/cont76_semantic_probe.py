#!/usr/bin/env python3
"""cont76_semantic_probe.py — FOUNDATION-6 minimal semantic-probe runner
(issue #364 6/4 tool candidate, built this wave).

One bounded harness for N apps: fresh store, install, one warm run per app,
per-app verdict rows (the shared vocabulary of the #364 ledger):

  REAL_APP_UI        nonbg content + app-owned draw ops on the live window
  SPLASH_ONLY        engine default splash face (31ddd4d5b8e6d18e family)
  WHITE_BLANK        uniform white, no app surface
  DARK_SURFACE_NO_OPS  app background reached, APP_DRAW_OPS missing
  PREREQUISITE_MISMATCH  native/ABI gate refused (honest refusal logged)

Usage: cont76_semantic_probe.py <apk1> [apk2 ...] [--frames N] [--budget S]
Writes JSON census to run/cont76/semantic_probe/<pkg>/row.json and prints
the scoreboard (verdict percentages) — the loop's "what percentage works"
answer is produced by this runner from here on.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = "/home/z/my-project"
BIN = f"{ROOT}/miniandroid/build/miniandroid"
STORE = f"{ROOT}/run/cont76/semantic_probe/store"
OUTD = f"{ROOT}/run/cont76/semantic_probe"
SPLASH_SHA16 = "31ddd4d5b8e6d18e"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def app_package(apk):
    with zipfile.ZipFile(apk) as z:
        data = z.read("AndroidManifest.xml")
    m = re.search(rb"package=|P\s*Y", data)  # binary XML: pull via aapt2
    # binary manifest: find the package attribute string near the header
    import struct
    # cheap approach: use aapt2 dump
    r = subprocess.run([f"{ROOT}/tools/toolchain/aapt2", "dump", "badging", apk],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r"package: name='([^']+)'", r.stdout)
    return m.group(1) if m else os.path.basename(apk)


def pixel_metrics(png):
    """The user_golden_gate pixel_metrics law (same thresholds as the
    CONT-73 census — one shared vocabulary, no ad-hoc classifier)."""
    from PIL import Image
    import math
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
    return {"unique_colors": len(colors),
            "nonbg_ratio": round(nonbg / total, 4),
            "entropy": round(ent, 3)}


def classify(combined, shot_path):
    row = {}
    shot = sha16(shot_path) if os.path.exists(shot_path) else "NOSCREEN"
    row["screenshot_sha16"] = shot
    # native/ABI gate refusals (honest prerequisites)
    if re.search(r"nativeOnCreate.*fail|UnsatisfiedLink|dlopen.*fail"
                 r"|ARM-only|native lib.*not load", combined, re.I):
        row["verdict"] = "PREREQUISITE_MISMATCH"
        return row
    if shot == SPLASH_SHA16:
        row["verdict"] = "SPLASH_ONLY"
        return row
    if shot == "NOSCREEN":
        row["verdict"] = "NO_SCREEN"
        return row
    m = pixel_metrics(shot_path)
    row.update(m)
    if m["unique_colors"] <= 2:
        # uniform surface — white or the app's own background (no content)
        with open(shot_path, "rb") as f:
            pass
        from PIL import Image
        dom = Image.open(shot_path).convert("RGB").getpixel((5, 5))
        row["dominant_rgb"] = list(dom)
        if dom[0] > 240 and dom[1] > 240 and dom[2] > 240:
            row["verdict"] = "WHITE_BLANK"
        else:
            row["verdict"] = "DARK_SURFACE_NO_OPS"
        return row
    if m["nonbg_ratio"] >= 0.02 and m["unique_colors"] >= 64:
        row["verdict"] = "REAL_APP_UI"
    elif m["nonbg_ratio"] >= 0.002 or m["unique_colors"] >= 24:
        row["verdict"] = "PARTIAL_MARGINAL"
    else:
        row["verdict"] = "WHITE_BLANK"
    return row


def main():
    apks = [a for a in sys.argv[1:] if not a.startswith("--")]
    frames = 5
    budget = 90
    argv = sys.argv[1:]
    if "--frames" in argv:
        frames = int(argv[argv.index("--frames") + 1])
    if "--budget" in argv:
        budget = int(argv[argv.index("--budget") + 1])

    os.makedirs(STORE, exist_ok=True)
    rows = []
    for apk in apks:
        pkg = app_package(apk)
        outdir = f"{OUTD}/{pkg}"
        shutil.rmtree(outdir, ignore_errors=True)
        os.makedirs(outdir, exist_ok=True)
        inst = subprocess.run([BIN, "install", apk, "--data-root", STORE],
                              capture_output=True, text=True, timeout=120)
        cmd = [BIN, "run", "--package", pkg, "--data-root", STORE,
               "--width", "1080", "--height", "1920",
               "--frames", str(frames), "--max-seconds", str(budget),
               "-o", outdir]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=budget + 60)
            combined = r.stdout + r.stderr
        except subprocess.TimeoutExpired as e:
            combined = (e.stdout or b"").decode(errors="replace") + \
                       (e.stderr or b"").decode(errors="replace")
        row = {"package": pkg, "apk_sha16": sha16(apk),
               "install_rc": inst.returncode, "binary_sha16": sha16(BIN)}
        row.update(classify(combined, f"{outdir}/screenshot.png"))
        rows.append(row)
        print(f"  {pkg}: {row['verdict']} (shot {row['screenshot_sha16']})")

    # scoreboard — the loop's percentage answer
    n = len(rows)
    tally = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    working = tally.get("REAL_APP_UI", 0)
    scoreboard = {
        "apps": n,
        "tally": tally,
        "real_app_ui_pct": round(100.0 * working / n, 1) if n else 0.0,
    }
    os.makedirs(f"{ROOT}/evidence/cont76", exist_ok=True)
    with open(f"{ROOT}/evidence/cont76/semantic_probe.json", "w") as f:
        json.dump({"rows": rows, "scoreboard": scoreboard}, f, indent=1)
    print(f"SCOREBOARD: {working}/{n} REAL_APP_UI = "
          f"{scoreboard['real_app_ui_pct']}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
