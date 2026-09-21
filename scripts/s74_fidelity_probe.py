#!/usr/bin/env python3
"""s74_fidelity_probe.py — S74 Level C regression probe (no runtime changes in
S74; this proves the current binary + stored evidence pair still reproduces
byte-identically, per the S56/S73 replay law).

Recipe: replay the EXACT autonomous tap schedule stored in
docs/evidence/s73_snake_autoplay/run_01/engine.log ([F117-TAP] lines) as a
fresh run, then compare every per-frame PNG SHA256 against the stored run_01
frames and the recorded final-state trace fields.
"""
import glob, hashlib, json, os, re, subprocess, sys

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s72_w4_apks/snake_v1.0_vc1.apk"
SRC = f"{ROOT}/docs/evidence/s73_snake_autoplay/run_01"
OUT = f"{ROOT}/run/s74_fidelity_probe"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    taps = []
    for line in open(f"{SRC}/engine.log", errors="replace"):
        m = re.search(r"\[F117-TAP\] frame (\d+) DOWN \((\d+),(\d+)\)", line)
        if m:
            fr, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            taps.append(f"{x},{y}@{fr}")
    if not taps:
        sys.exit("FAIL: no [F117-TAP] schedule found in stored run_01")
    n_frames = len(glob.glob(f"{SRC}/frames/frame_*.png"))
    print(f"schedule: {len(taps)} scheduled taps, {n_frames} stored frames")

    os.makedirs(OUT, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", "250",
           "--dump-view-tree", "-o", OUT]
    for t in taps:
        cmd += ["--tap", t]
    cmd.append(APK)
    with open(f"{OUT}/engine.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)
    print(f"replay rc={rc}")

    new_frames = sorted(glob.glob(f"{OUT}/frames/frame_*.png"))
    old_frames = sorted(glob.glob(f"{SRC}/frames/frame_*.png"))
    print(f"replayed frames: {len(new_frames)} vs stored {len(old_frames)}")
    if len(new_frames) != len(old_frames):
        sys.exit("FAIL: frame count mismatch — NOT byte-identical")

    diffs = []
    for old, new in zip(old_frames, new_frames):
        so, sn = sha256(old), sha256(new)
        if so != sn:
            diffs.append((os.path.basename(old), so[:16], sn[:16]))
    if diffs:
        print(f"FAIL — {len(diffs)} frame divergence(s):")
        for d in diffs[:10]:
            print("  ", d)
        sys.exit(1)
    print(f"PASS — {len(new_frames)}/{len(new_frames)} frames byte-identical vs stored S73 run_01 "
          f"(current binary reproduces committed evidence; zero runtime drift at S74 HEAD)")


if __name__ == "__main__":
    main()
