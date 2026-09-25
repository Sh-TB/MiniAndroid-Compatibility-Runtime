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


def standard_run(title, apk, frames, taps, compare=(0, -1), out_root=None):
    """Full standard protocol for one title; returns the record dict."""
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
    write_record(rundir, rec)
    return rec
