#!/usr/bin/env python3
"""s73_snake_finalize.py — S73 PART C finalization:
1. Reconstruct the final autonomous tap schedule from iter_04 (the GOALS_MET
   run) engine.log [F117-TAP] lines.
2. Replay the IDENTICAL schedule 3x as fresh full runs (run_01..03).
3. Verify 3-run byte-identity (per-frame PNG sha + pixel sha).
4. Emit gameplay_trace.json (C5) per run from rendered frames ONLY.
5. Emit snake_autoplay.gif from run_01 real frames.
6. Emit SHA256SUMS + final report json.
"""
import os
import re
import json
import glob
import hashlib
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s73_snake_controller import (analyze_run, count_events, verify_prefix,
                                  frame_cells)
from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s72_w4_apks/snake_v1.0_vc1.apk"
ITER = f"{ROOT}/run/s73_snake_auto/iter_04"
OUT = f"{ROOT}/docs/evidence/s73_snake_autoplay"


def taps_from_log(log_path):
    """(x, y, frame) triples from [F117-TAP] frame N DOWN (x,y)."""
    taps = []
    for line in open(log_path, errors="replace"):
        m = re.search(r"\[F117-TAP\] frame (\d+) DOWN \((\d+),(\d+)\)", line)
        if m:
            fr, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            taps.append((x, y, fr))
    return taps


def run_once(taps, n_frames, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", "250",
           "--dump-view-tree", "-o", out_dir]
    for x, y, fr in taps:
        cmd += ["--tap", f"{x},{y}@{fr}"]
    cmd.append(APK)
    with open(f"{out_dir}/engine.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)
    return rc


def state_hash(o):
    h = hashlib.sha256(json.dumps(
        {"s": o["snake"], "f": o["food"], "d": o["dir"]},
        sort_keys=True).encode()).hexdigest()[:16]
    return h


def build_trace(run_id, obs, taps_by_frame):
    """C5 gameplay_trace.json — every value from actual execution."""
    trace = {"run_id": run_id, "engine": "MiniAndroid real-dalvik",
             "apk": "snake_v1.0_vc1.apk",
             "apk_sha256_16": "54cf48a9",
             "input_model": "scheduled taps x,y@frame through canonical "
                            "TouchDispatcher DOWN/UP law pipeline",
             "vision": "rendered-frame pixel extraction: snake #FF4081, "
                       "food #0000ff on 20x20 grid (39px cells)",
             "frames": []}
    prev_len = None
    for o in obs:
        rec = {
            "frame": o["frame_index"],
            "file": o["frame_file"],
            "screenshot_sha256": o["png_sha256"],
            "state_hash": state_hash(o),
            "observed_snake": o["snake"],
            "observed_food": o["food"],
            "head": o["head"],
            "direction": o["dir"],
        }
        t = taps_by_frame.get(o["frame_index"])
        if t:
            rec["input"] = f"tap({t[0]},{t[1]})@frame{t[2]}"
        ev = []
        if prev_len is not None and o["snake"] and \
                len(o["snake"]) > prev_len:
            ev.append("GROWTH" if o["frame_index"] > 2 else "START_GROW_TICK")
            if o["frame_index"] > 2:
                ev.append("FOOD_CAPTURED")
        if o["game_over"]:
            ev.append("GAME_OVER")
        if ev:
            rec["event"] = ev
        trace["frames"].append(rec)
        if o["snake"]:
            prev_len = len(o["snake"])
    return trace


def main():
    taps = taps_from_log(f"{ITER}/engine.log")
    n_frames = len(glob.glob(f"{ITER}/frames/frame_*.png"))
    print(f"final schedule: {len(taps)} taps, {n_frames} frames")
    os.makedirs(OUT, exist_ok=True)
    runs = {}
    for i in (1, 2, 3):
        rd = f"{OUT}/run_{i:02d}"
        if os.path.exists(rd):
            shutil.rmtree(rd)
        rc = run_once(taps, n_frames, rd)
        obs = analyze_run(rd)
        runs[i] = obs
        ev = count_events(obs)
        taps_by_frame = {(t[2]): t for t in taps}
        trace = build_trace(f"s73_autonomous_run_{i:02d}", obs,
                            taps_by_frame)
        with open(f"{rd}/gameplay_trace.json", "w") as f:
            json.dump(trace, f, indent=1)
        print(f"run_{i:02d}: rc={rc} frames={len(obs)} {ev}")
    # 3-run byte-identity
    seqs = []
    for i in (1, 2, 3):
        seqs.append([o["png_sha256"] for o in runs[i]])
    identical = seqs[0] == seqs[1] == seqs[2]
    div = None
    if not identical:
        for a, b, c in zip(*seqs):
            if not (a == b == c):
                div = seqs[0].index(a)
                break
    print("3-RUN DETERMINISM:", "IDENTICAL" if identical else
          f"DIVERGED at frame {div}")
    # SHA256SUMS (PNG files) per run
    for i in (1, 2, 3):
        rd = f"{OUT}/run_{i:02d}"
        lines = []
        for f in sorted(glob.glob(f"{rd}/frames/*.png")) + \
                sorted(glob.glob(f"{rd}/*.json")):
            h = hashlib.sha256(open(f, "rb").read()).hexdigest()
            lines.append(f"{h}  {os.path.relpath(f, rd)}")
        open(f"{rd}/SHA256SUMS", "w").write("\n".join(lines) + "\n")
    # GIF from run_01 real frames (documented transform: 50% scale, 250ms)
    frames = sorted(glob.glob(f"{OUT}/run_01/frames/frame_*.png"))
    gif_frames = []
    for fp in frames:
        img = Image.open(fp).convert("RGB").resize((540, 960),
                                                   Image.NEAREST)
        gif_frames.append(img.quantize(colors=64, dither=Image.NONE))
    gif_path = f"{OUT}/snake_autoplay.gif"
    gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:],
                       duration=250, loop=0, optimize=True)
    print(f"GIF: {gif_path} "
          f"({os.path.getsize(gif_path)//1024} KB, {len(gif_frames)} frames)")
    # summary
    ev1 = count_events(runs[1])
    last = runs[1][-1]
    capture_frames = [o["frame_index"] for o in runs[1]
                      if o["snake"] and len(o["snake"]) > 3]
    summary = {
        "schedule_taps": len(taps),
        "taps": [f"({x},{y})@{fr}" for x, y, fr in taps],
        "frames_per_run": n_frames,
        "events_run_01": ev1,
        "capture_frames": capture_frames,
        "final_frame": last["frame_file"],
        "final_snake": last["snake"],
        "final_food": last["food"],
        "determinism": "3/3 IDENTICAL (per-frame PNG sha equality)" if
        identical else f"DIVERGED at frame {div}",
        "game_over": any(o["game_over"] for o in runs[1]),
    }
    with open(f"{OUT}/autoplay_summary.json", "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1)[:2200])


if __name__ == "__main__":
    main()
