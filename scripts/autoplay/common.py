#!/usr/bin/env python3
"""autoplay/common.py — the STANDARD MiniAndroid autoplay structure.

One place for every autonomous-play driver (scripts/autoplay/). A standard
autoplay is:

  1. LAUNCH   run_mini(): real-dalvik run of an APK with a fixed
              frame budget and deterministic virtual clock.
  2. INTERACT --tap x,y@frame (the runtime tap schedule): taps are REAL
              dispatches through TouchDispatcher (G06 token evidence).
  3. MEASURE  state_change_px(): exact differing-pixel count between a
              pre-interaction frame and a post frame — "tap dispatched" is
              NEVER the proof (S99 §24 state-change law).
  4. EVIDENCE write_record(): JSON run record (SHA of APK + screenshot +
              px deltas + repeatability) under run/autoplay/<title>/.

Repeatability law: an autoplay MUST be run 3x; determinism is preferred
and variance is recorded honestly (S100 §25).

Tick law (timing-scheduled games): one game tick == two captured frames
(1-move=2-frames law, snake-neon); never sleep-hack the host (S100 §27).
"""
import hashlib
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
OUT_ROOT = os.path.join(REPO, "run", "autoplay")


def sha16(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def run_mini(rundir, apk, frames, taps=(), width=1080, height=1920,
             dump_view_tree=False, timeout=300):
    """LAUNCH + INTERACT. taps = [(x, y, frame), ...] in execution order."""
    os.makedirs(rundir, exist_ok=True)
    cmd = [MA_BIN, "run", "-o", rundir,
           "--execution-mode", "real-dalvik",
           "--frames", str(frames),
           "--width", str(width), "--height", str(height),
           "--data-root", os.path.join(rundir, "data"),
           "--apk", apk]
    for (x, y, fr) in taps:
        cmd += ["--tap", f"{x},{y}@{fr}"]
    if dump_view_tree:
        cmd += ["--dump-view-tree"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    with open(os.path.join(rundir, "stdout.log"), "w") as f:
        f.write(r.stdout)
    with open(os.path.join(rundir, "stderr.log"), "w") as f:
        f.write(r.stderr)
    return r.returncode


def state_change_px(rundir, frame_a, frame_b):
    """MEASURE: exact differing-pixel count between two captured frames."""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(os.path.join(rundir, "frames", frame_a))
                   .convert("L"), dtype=np.int16)
    b = np.asarray(Image.open(os.path.join(rundir, "frames", frame_b))
                   .convert("L"), dtype=np.int16)
    return int((a != b).sum())


def write_record(rundir, record):
    """EVIDENCE: canonical run record for the wave report / registry."""
    with open(os.path.join(rundir, "autoplay_record.json"), "w") as f:
        json.dump(record, f, indent=2)
    return os.path.join(rundir, "autoplay_record.json")


def compact_preview(src_png, out_jpg, max_dim=640, budget_kb=250):
    """C-tier preview derivative (#587 forensic addendum §7): max 640 px,
    byte-budget ~150-250 KB, explicitly labeled DERIVATIVE / NOT
    PIXEL-EXACT in the sidecar manifest. Canonical/pixel-gate images are
    exempt (they never go through this function)."""
    from PIL import Image
    img = Image.open(src_png)
    img.thumbnail((max_dim, max_dim))
    q = 85
    while True:
        img.convert("RGB").save(out_jpg, format="JPEG", quality=q,
                                optimize=True)
        if os.path.getsize(out_jpg) <= budget_kb * 1024 or q <= 70:
            break
        q -= 5
    with open(out_jpg + ".manifest.json", "w") as f:
        json.dump({
            "derivative": "DERIVATIVE / NOT PIXEL-EXACT",
            "source": os.path.relpath(src_png, REPO),
            "source_sha256": hashlib.sha256(
                open(src_png, "rb").read()).hexdigest(),
            "dimensions": list(img.size),
            "encoder": f"PIL JPEG q={q} optimize",
            "bytes": os.path.getsize(out_jpg),
        }, f, indent=1)
    return out_jpg


def standard_run(title, apk, frames, taps, compare=(0, -1), out_root=None,
                 retain_full_screenshot=False):
    """Full standard protocol for one title; returns the record dict.

    §7 default: run artifacts are compact — the full-resolution screenshot
    is retained only behind retain_full_screenshot=True (canonical-evidence
    opt-in); otherwise a 640-px JPEG preview + the per-run SHA row stand in
    for the full PNG (which still lives in the ignored local run tree for
    the session but is NOT promoted)."""
    rundir = os.path.join(out_root or OUT_ROOT, title)
    rc = run_mini(rundir, apk, frames, taps)
    frames_dir = os.path.join(rundir, "frames")
    shot = os.path.join(rundir, "screenshot.png")
    rec = {
        "title": title,
        "apk": apk,
        "apk_sha16": sha16(apk) if os.path.exists(apk) else None,
        "rc": rc,
        "frames": frames,
        "taps": list(taps),
        "screenshot_sha16": sha16(shot) if os.path.exists(shot) else None,
    }
    if compare and os.path.isdir(frames_dir):
        names = sorted(os.listdir(frames_dir))
        if len(names) >= 2:
            fa = names[compare[0]]
            fb = names[compare[1]]
            rec["state_change_px"] = state_change_px(rundir, fa, fb)
            rec["state_change_frames"] = [fa, fb]
    if os.path.exists(shot) and not retain_full_screenshot:
        prev = compact_preview(shot, os.path.join(rundir, "screenshot_preview.jpg"))
        rec["preview"] = os.path.relpath(prev, REPO)
        rec["preview_law"] = "DERIVATIVE / NOT PIXEL-EXACT (C-tier)"
        rec["full_screenshot_retained"] = False
    else:
        rec["full_screenshot_retained"] = bool(os.path.exists(shot))
    # report-honesty gate (#587 §7): reject a contradictory report at the
    # moment it is produced, not at review time.
    rpt = os.path.join(rundir, "report.md")
    if os.path.exists(rpt):
        sys.path.insert(0, os.path.join(REPO, "tools"))
        try:
            import report_sanity
            rec["report_sanity_violations"] = [
                c for c, _ in report_sanity.check_report(rpt)]
        except Exception as e:  # never crash a run on gate failure
            rec["report_sanity_violations"] = [f"GATE_ERROR {e}"]
    write_record(rundir, rec)
    return rec
