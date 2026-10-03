#!/usr/bin/env python3
"""CLOSED-ISSUE FORENSIC PROGRAM (#367/#368/#369) — current-HEAD re-run wave.

Re-runs every batch issue title whose APK is (re)buildable at the current
binary, x1 run each with pixel metrics + state-change check where applicable
(games: post-tap frame delta). Saves per-title evidence to
evidence/batch367_rerun/<title>/ + wave_summary.json.
Applies F-NEW-233 frame-truth metrics (unique colors, nonbg ratio, draw ops).
"""
import hashlib, json, os, shutil, subprocess, time
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "evidence/batch367_rerun"
OUT.mkdir(parents=True, exist_ok=True)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE, capture_output=True, text=True).stdout.strip()[:8]

# title -> (apk path or builder, taps for interaction)
WAVE = {
    "de.duenndns.gmdice": (BASE / "upload/canonical_apks/de.duenndns.gmdice_8.apk", [(540, 960)]),
    "com.miniandroid.snakeneon": (BASE / "upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk", [(540, 960)]),
    "com.dozingcatsoftware.bouncy": (BASE / "upload/canonical_apks/bouncy.apk", [(540, 300)]),
    "com.miniandroid.tictactoedeluxe": ("BUILD_TTDELUXE", [(540, 960)]),
}

def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

def png_metrics(p):
    """Decode PNG via python (no PIL dependency assumption — use zlib/struct)."""
    try:
        from PIL import Image
        im = Image.open(p).convert("RGB")
        im = im.resize((im.width // 2, im.height // 2))  # speed
        colors = im.getcolors(maxcolors=1 << 24)
        ncolors = len(colors) if colors else -1
        total = im.width * im.height
        # background = most common color
        colors.sort(reverse=True)
        dom = colors[0][0] / total if colors else 1.0
        return {"unique_colors": ncolors, "dominant_ratio": round(dom, 4),
                "nonbg_ratio": round(1 - dom, 4)}
    except Exception as e:
        return {"metrics_error": str(e)}

def run_title(name, apk, taps):
    d = OUT / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cmd = [str(BIN), "run", str(apk), "-o", str(d/"out"), "--frames", "3"]
    for t in taps:
        cmd += ["--tap", f"{t[0]},{t[1]}"]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=BASE/"miniandroid", capture_output=True, text=True, timeout=180)
    wall = round(time.time() - t0, 1)
    log = (d/"run.log")
    log.write_text(r.stdout[-20000:] + "\n=== STDERR ===\n" + r.stderr[-20000:])
    status = "UNKNOWN"
    for line in (r.stdout + r.stderr).splitlines():
        if "Status:" in line:
            status = line.split("Status:")[-1].strip()
            break
    shot = d/"out/screenshot.png"
    metrics = png_metrics(shot) if shot.exists() else {}
    shot_sha = sha16(shot) if shot.exists() else None
    # frame delta (state change): frames 1 vs 3
    f1, f3 = d/"out/frames/frame_000.png", d/"out/frames/frame_002.png"
    delta = None
    if f1.exists() and f3.exists():
        delta = (sha16(f1) != sha16(f3))
    rec = {
        "title": name, "apk": str(apk), "apk_sha16": sha16(apk),
        "rc": r.returncode, "status": status, "wall_s": wall,
        "screenshot_sha16": shot_sha, "pixels": metrics,
        "frame_delta_tap": delta,
        "runtime_head": HEAD,
    }
    (d/"record.json").write_text(json.dumps(rec, indent=1))
    return rec

results = {}
for name, (apk, taps) in WAVE.items():
    if apk == "BUILD_TTDELUXE":
        b = BASE/"upload/batch367_build/tictactoedeluxe.apk"
        b.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["bash", "scripts/build/build_fixture_apk.sh",
                            "games/tictactoe-deluxe", str(b)],
                           cwd=BASE, capture_output=True, text=True, timeout=240)
        if r.returncode != 0 or not b.exists():
            results[name] = {"title": name, "build": "FAILED", "log": r.stderr[-800:]}
            continue
        apk = b
    try:
        results[name] = run_title(name, apk, taps)
        print(name, "->", results[name]["status"], "| colors:", results[name].get("pixels", {}).get("unique_colors"), "| delta:", results[name].get("frame_delta_tap"))
    except Exception as e:
        results[name] = {"title": name, "error": str(e)}
        print(name, "ERROR", e)

summary = {"wave": "closed-issue-forensic-batch367-rerun", "head": HEAD,
           "generated": time.strftime("%Y-%m-%d"), "results": results}
(OUT/"wave_summary.json").write_text(json.dumps(summary, indent=1))
print("\nWAVE COMPLETE ->", OUT/"wave_summary.json")
