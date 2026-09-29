#!/usr/bin/env python3
"""s121_fishrings_autoplay.py — fishrings (ebinqo) ring-rotation gameplay (S121).

The board renders 30 balls in 4 rings (10 red / 8 pink / 6 blue / 6 green)
with red rotation arrows. Tap a ball -> its ring rotates one step -> balls
shift along the ring. Measured ball centers (vision, S121 calibration):
  red ring:   (365,229) (472,228) (270,281) (567,281) (215,376) (622,375)
              (215,486) (621,486) (270,580) (567,580)
  pink ring:  (424,431) (329,376) (516,377) (369,525) (476,524) (369,633)
              (476,632) (420,727)
  blue arc:   (120,430) (66,524) (66,632) (119,725) (213,781) (324,781)
  green arc:  (717,432) (769,526) (769,634) (716,728) (622,782) (513,783)
Protocol: probe (no taps) -> tap a red-ring ball @40 -> vision-diff the ball
positions before/after (state_change_px + per-ball occupancy) -> tap again
-> 2 rotations captured. Determinism: same schedule 2x byte-compare.
"""
import glob
import os
import subprocess

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s65_apks/fishrings_v1.23_vc6.apk"
OUT = f"{ROOT}/run/s121_fishrings"

RED_RING = [(365, 229), (472, 228), (270, 281), (567, 281), (215, 376),
            (622, 375), (215, 486), (621, 486), (270, 580), (567, 580)]


def run_engine(taps, n_frames, out_dir, frame_delay=250):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=600)
    return rc


def occupancy(png):
    """Which red-ring slots hold a red ball (sample 5x5 ink at centers)."""
    img = Image.open(png).convert("RGB")
    px = img.load()
    occ = []
    for (cx, cy) in RED_RING:
        n = sum(1 for dx in range(-12, 13, 4) for dy in range(-12, 13, 4)
                if 0 <= cx + dx < 1080 and 0 <= cy + dy < 1920
                and px[cx + dx, cy + dy][0] > 200
                and 80 < px[cx + dx, cy + dy][1] < 190
                and 80 < px[cx + dx, cy + dy][2] < 190)
        occ.append(n >= 6)
    return occ


def state_change_px(rundir, fr_a, fr_b):
    a = Image.open(f"{rundir}/frames/frame_{fr_a:03d}.png").convert("L")
    b = Image.open(f"{rundir}/frames/frame_{fr_b:03d}.png").convert("L")
    pa, pb = a.load(), b.load()
    w, h = a.size
    n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if abs(pa[x, y] - pb[x, y]) > 12:
                n += 1
    return n * 4


def main():
    # probe
    pd = f"{OUT}/probe"
    run_engine([], 36, pd)
    base_occ = occupancy(f"{pd}/frames/frame_030.png")
    print("probe red-ring occupancy:", base_occ)

    # rotate: tap a red ball twice (two taps 10 frames apart)
    d = f"{OUT}/rot1"
    bx, by = RED_RING[0]
    rc = run_engine([(bx, by, 40), (bx, by, 50)], 66, d)
    pre = f"{d}/frames/frame_038.png"
    mid = f"{d}/frames/frame_048.png"
    post = f"{d}/frames/frame_064.png"
    o_pre = occupancy(pre)
    o_mid = occupancy(mid)
    o_post = occupancy(post)
    sc1 = state_change_px(d, 38, 48)
    sc2 = state_change_px(d, 48, 64)
    print(f"tap@({bx},{by})@40 rc={rc}")
    print("occ pre :", o_pre)
    print("occ mid :", o_mid)
    print("occ post:", o_post)
    print(f"state_change_px 38->48: {sc1}  48->64: {sc2}")

    # determinism: rerun byte-compare frames 46..52
    d2 = f"{OUT}/rot1_r2"
    run_engine([(bx, by, 40), (bx, by, 50)], 66, d2)
    same = all(
        Image.open(f"{d}/frames/frame_{i:03d}.png").tobytes()
        == Image.open(f"{d2}/frames/frame_{i:03d}.png").tobytes()
        for i in range(46, 53))
    print("repeatability 2x (frames 46-52):",
          "IDENTICAL" if same else "VARIANCE")

    with open(f"{OUT}/record.txt", "w") as f:
        f.write(f"pre {o_pre}\nmid {o_mid}\npost {o_post}\n"
                f"sc1 {sc1}\nsc2 {sc2}\nsame {same}\n")


if __name__ == "__main__":
    main()
