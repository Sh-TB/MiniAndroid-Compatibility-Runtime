#!/usr/bin/env python3
"""s95_capture.py — S95 P0 BEFORE/AFTER capture harness.

Executes one P0 target or control APK through the MiniAndroid runtime with
the EXACT S92/S93 per-title protocol (frames, taps, resolution, mode), then
collects a machine-readable capture record:

  run/s95/captures/<case>/<phase>/
      ...runtime outputs (screenshot.png, frames/, view_tree.json,
          gfx_provenance.json, click_audit.jsonl)...
  run/s95/captures/<case>/<phase>_capture.json

Capture record contains: APK identity + SHA256, runtime rc + command,
screenshot SHA256/dims/graphics metrics (entropy, luminance, unique colors,
channel means), per-frame SHA256 list, ViewTree summary, provenance record
count, and (optionally) the S93 semantic classification computed by
importing scripts/s93_run_semantic.analyze_case UNCHANGED (zero analysis
drift from the S93 baseline).

Usage:
  python3 scripts/s95_capture.py --phase before [--case bouncy] [--semantic]
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))
MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
DL = os.path.join(REPO, "miniandroid", "download")
CAP = os.path.join(REPO, "run", "s95", "captures")

# S92/S93-identical protocol per case:
# (apk_relpath, package, title, stratum, frames, taps, role, waves)
# taps=None | (x, y, at_frame)
CASES = {
    # ---- P0 WRONG_COLOR targets ----
    "bouncy": ("miniandroid/download/com.dozingcatsoftware.bouncy_43.apk",
               "com.dozingcatsoftware.bouncy", "Vector Pinball", "game-gl",
               10, None, "target", ["WRONG_COLOR"]),
    "hotdeath": ("miniandroid/download/com.smorgasbork.hotdeath_11.apk",
                 "com.smorgasbork.hotdeath", "Hot Death Uno", "image-heavy",
                 10, None, "target", ["WRONG_COLOR"]),
    "urlchecker": ("miniandroid/download/com.trianguloy.urlchecker_28.apk",
                   "com.trianguloy.urlchecker", "URL Checker", "app",
                   10, None, "target", ["WRONG_COLOR", "WRONG_CLIP"]),
    "simplestopwatch": (
        "miniandroid/download/omegacentauri.mobi.simplestopwatch_26.apk",
        "omegacentauri.mobi.simplestopwatch", "Simple Stopwatch", "app",
        6, None, "target", ["WRONG_COLOR", "UNREADABLE_TEXT"]),
    # ---- P0 WRONG_CLIP targets ----
    "bobball": ("miniandroid/download/org.bobstuff.bobball_26.apk",
                "org.bobstuff.bobball", "Bobball", "game-surfaceview",
                10, None, "target", ["WRONG_CLIP"]),
    "dodge": ("miniandroid/download/com.dozingcatsoftware.dodge_10.apk",
              "com.dozingcatsoftware.dodge", "Dodge", "game-canvas",
              10, None, "target", ["WRONG_CLIP"]),
    # ---- P0 ANIMATION_FROZEN targets (S92 tap protocol) ----
    "mini-tetris": (
        "upload/s80_games/build_tetris/tetris_v1.0_vc1.apk",
        "com.miniandroid.tetris", "Mini Tetris", "game-canvas",
        24, (540, 1500, 16), "target", ["ANIMATION_FROZEN"]),
    "minicraft": (
        "upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
        "com.miniandroid.minicraft", "Minicraft", "game-canvas",
        24, (540, 1500, 16), "target", ["ANIMATION_FROZEN"]),
    # ---- CONTROLS (S93 SEMANTIC_PASS) ----
    "nounours": ("miniandroid/download/ca.rmen.nounours_358.apk",
                 "ca.rmen.nounours", "ca.rmen.nounours", "image-heavy",
                 8, None, "control", []),
    "unote": ("miniandroid/download/app.varlorg.unote_30.apk",
              "app.varlorg.unote", "uNote", "app",
              10, None, "control", []),
    "gmdice": ("miniandroid/download/de.duenndns.gmdice_8.apk",
               "de.duenndns.gmdice", "GM Dice", "app-image-heavy",
               10, None, "control", []),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def image_metrics(path):
    """Deterministic graphics metrics for one PNG (PIL, no caches)."""
    from PIL import Image
    img = Image.open(path)
    w, h = img.size
    rgb = img.convert("RGB")
    px = list(rgb.getdata())
    n = len(px)
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    mean_lum = sum(lum) / n
    var = sum((v - mean_lum) ** 2 for v in lum) / n
    # luminance entropy (64-bin)
    hist = [0] * 64
    for v in lum:
        hist[min(63, int(v) * 64 // 256)] += 1
    ent = 0.0
    for c in hist:
        if c:
            p = c / n
            ent -= p * math.log2(p)
    rs = gs = bs = 0
    colors = set()
    step = max(1, n // 200000)  # cap work for color stats
    cnt = 0
    for i in range(0, n, step):
        r, g, b = px[i]
        rs += r; gs += g; bs += b; cnt += 1
        colors.add((r >> 3, g >> 3, b >> 3))
    return {
        "width": w, "height": h,
        "sha256": sha256(path),
        "luminance_mean": round(mean_lum, 3),
        "luminance_std": round(math.sqrt(var), 3),
        "luminance_entropy_bits": round(ent, 4),
        "unique_colors_5bit": len(colors),
        "channel_mean_rgb": [round(rs / cnt, 2), round(gs / cnt, 2),
                             round(bs / cnt, 2)],
    }


def find_apk(rel):
    p = os.path.join(REPO, rel)
    return p if os.path.isfile(p) else None


def run_case(case, phase, with_semantic=False):
    if case not in CASES:
        print(f"unknown case {case}"); sys.exit(2)
    apk_rel, pkg, title, stratum, frames, taps, role, waves = CASES[case]
    apk = find_apk(apk_rel)
    if not apk:
        print(f"APK MISSING {apk_rel}"); sys.exit(2)
    rundir = os.path.join(CAP, case, phase)
    os.makedirs(rundir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(rundir,
                                                     "gfx_provenance.json")
    env["MINIANDROID_CLICK_AUDIT"] = os.path.join(rundir, "click_audit.jsonl")
    tap = f" --tap {taps[0]},{taps[1]}@{taps[2]}" if taps else ""
    cmd = (f"{MA_BIN} run -o {rundir} --execution-mode real-dalvik "
           f"--frames {frames} --width 1080 --height 1920 "
           f"--dump-view-tree --data-root {rundir}/data{tap} --apk {apk}")
    r = subprocess.run(cmd, shell=True, env=env, capture_output=True,
                       text=True, timeout=900)
    shot = os.path.join(rundir, "screenshot.png")
    rec = {
        "schema": "s95.capture.v1",
        "case": case, "phase": phase, "role": role,
        "expected_waves": waves,
        "package": pkg, "title": title, "stratum": stratum,
        "apk_path": apk_rel, "apk_sha256": sha256(apk),
        "protocol": {"frames": frames, "tap": taps, "width": 1080,
                     "height": 1920, "execution_mode": "real-dalvik",
                     "dump_view_tree": True},
        "runtime_rc": r.returncode,
        "runtime_cmd": cmd,
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                      time.gmtime()),
    }
    if os.path.isfile(shot):
        m = image_metrics(shot)
        rec["screenshot"] = m
    fdir = os.path.join(rundir, "frames")
    if os.path.isdir(fdir):
        frs = sorted(f for f in os.listdir(fdir)
                     if f.startswith("frame_") and f.endswith(".png"))
        rec["frame_shas"] = {f: sha256(os.path.join(fdir, f))
                             for f in frs}
        rec["frame_count"] = len(frs)
    vt = os.path.join(rundir, "view_tree.json")
    if os.path.isfile(vt):
        v = json.load(open(vt))
        nodes = v.get("nodes", [])
        rec["view_tree_summary"] = {
            "nodes": len(nodes),
            "text_nodes": sum(1 for n in nodes if str(n.get("text", "")).strip()),
            "image_nodes": sum(1 for n in nodes
                               if n.get("image_resource_id") or
                               "ImageView" in str(n.get("class", ""))),
        }
    prov = os.path.join(rundir, "gfx_provenance.json")
    if os.path.isfile(prov):
        p = json.load(open(prov))
        events = p.get("events", [])
        rec["provenance_summary"] = {
            "events": len(events),
            "drawn_records": sum(1 for e in events if e.get("DRAW_CALLED")),
            "decoded_records": sum(1 for e in events if e.get("DECODED")),
        }
    out_path = os.path.join(CAP, case, f"{phase}_capture.json")
    with open(out_path, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"{case:16s} {phase:6s} rc={r.returncode} "
          f"shot={'Y' if os.path.isfile(shot) else 'N'} "
          f"frames={rec.get('frame_count', 0)} -> {out_path}")

    if with_semantic:
        sem = semantic(case, rundir, apk, pkg, title, stratum)
        sp = os.path.join(CAP, case, f"{phase}_semantic.json")
        with open(sp, "w") as f:
            json.dump(sem, f, indent=1, default=str)
        print(f"{case:16s} {phase:6s} semantic: "
              f"{sem.get('s93_verdict')} "
              f"fails={[c['category'] for c in sem.get('failure_categories', [])][:5]}")


def semantic(case, rundir, apk, pkg, title, stratum):
    """S93-identical semantic analysis (imported UNCHANGED — zero drift)."""
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    from s93_run_semantic import analyze_case  # noqa: E402
    is_game = stratum.startswith("game")
    out = analyze_case(case, rundir, apk, pkg, title, stratum, is_game)
    out["apk_sha256"] = sha256(apk)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True,
                    choices=["before", "after"])
    ap.add_argument("--case", action="append",
                    help="repeatable; default = all cases")
    ap.add_argument("--semantic", action="store_true",
                    help="also run the S93 semantic analysis (imported "
                         "unchanged from scripts/s93_run_semantic.py)")
    a = ap.parse_args()
    os.makedirs(CAP, exist_ok=True)
    for case in (a.case or sorted(CASES)):
        run_case(case, a.phase, with_semantic=a.semantic)


if __name__ == "__main__":
    main()
